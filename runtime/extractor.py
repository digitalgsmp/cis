#!/usr/bin/env python3
"""
extractor.py — CIS Kernel Extractor Agent (Track 1)

Reads source files (vision docs + transcripts), sends them through DeepSeek API
using the architecture atlas extraction prompt, and saves extraction analyses
to cis_kernel/extraction/functional_intents/.

Safety:
  - Sequential calls only (no parallelism — no runaway)
  - Hard limit: MAX_FILES files per run
  - Skips files already extracted (check output dir)
  - Budget-aware: estimates cost before starting

Usage:
  export DEEPSEEK_API_KEY="sk-..."
  python3 extractor.py                           # process all unprocessed source files
  python3 extractor.py --file path/to/file.md    # process a single file
  python3 extractor.py --dry-run                 # show what would be processed
  python3 extractor.py --reset                   # reprocess all (delete existing)
"""

import os, sys, time, json, glob, re
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
KERNEL_DIR   = Path("/mnt/projects/cis/cis_kernel")
PROMPT_FILE  = Path("/mnt/projects/cis/docs/architecture_atlas/original_CISChats/architecture_atlas_prompt.md")
OUTPUT_DIR   = KERNEL_DIR / "extraction" / "functional_intents"
SESSION_LOG  = KERNEL_DIR / "source" / "SESSION_LOG.md"

# Safety limits
MAX_FILES       = 150     # hard cap per run
MAX_RETRIES     = 3       # per file
RATE_LIMIT_WAIT = 3       # seconds between calls

# API config
API_URL  = "https://api.deepseek.com/v1"
# Try loading from Hermes credential pool (auth.json) first
_AUTH_PATH = os.path.expanduser("~/.hermes/auth.json")
_API_KEY = ""
if os.path.exists(_AUTH_PATH):
    try:
        import json as _json
        with open(_AUTH_PATH) as _f:
            _auth = _json.load(_f)
        _creds = _auth.get("credential_pool", {}).get("deepseek", [])
        if _creds:
            _API_KEY = _creds[0].get("access_token", "")
    except Exception:
        pass

# Fallback to environment variable
if not _API_KEY:
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.expanduser("~/.hermes/.env"), override=True)
    except ImportError:
        pass
    _API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

API_KEY = _API_KEY
MODEL    = "deepseek-chat"  # DeepSeek V4
MAX_TOKENS = 8192          # generous output window
TEMP     = 0.3             # low temp for extraction precision

# ── Cost estimation (approximate) ─────────────────────────────────────────────
COST_PER_1K_INPUT  = 0.00027   # DeepSeek chat: $0.27/M tokens
COST_PER_1K_OUTPUT = 0.00110  # DeepSeek chat: $1.10/M tokens

# ── Source file groups (in priority order) ────────────────────────────────────
SOURCE_GROUPS = [
    # CIS core docs
    ("cis_adrs",            Path("/mnt/projects/cis/docs/ADRs"),                                           ".md"),
    ("cis_archive",         Path("/mnt/projects/cis/docs/_archive"),                                       ".md"),
    ("cis_architecture",    Path("/mnt/projects/cis/docs/architecture_atlas"),                             ".md"),
    ("cis_cisv1",           Path("/mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1"),            ".md"),
    ("cis_transcripts",     Path("/mnt/projects/cis/docs/claude_chat_transcripts"),                        ".md"),
    ("cis_contracts",       Path("/mnt/projects/cis/docs/contracts"),                                      ".md"),
    ("cis_references",      Path("/mnt/projects/cis/docs/references"),                                     ".md"),
    ("cis_runtime",         Path("/mnt/projects/cis/runtime"),                                             ".py"),
    # Hermes / AI infrastructure
    ("infrastructure",      Path("/mnt/projects/ai_execution_infrastructure"),                             ".md"),
    ("infrastructure_code", Path("/mnt/projects/ai_execution_infrastructure/04_IMPLEMENTATION_WORKSPACES"), ".py"),
    ("infrastructure_dash", Path("/mnt/projects/ai_execution_infrastructure/07_DASHBOARD"),                ".py"),
    # Creative tools (project files & docs only, not engine artifacts)
    ("blender",             Path("/mnt/projects/blender"),                                                 ".blend"),
    ("blender_docs",        Path("/mnt/projects/blender"),                                                 ".md"),
    ("resolve_docs",        Path("/mnt/projects/resolve"),                                                 ".md"),
    ("unreal_proj",         Path("/mnt/projects/unreal"),                                                  ".uproject"),
    ("unreal_docs",         Path("/mnt/projects/unreal"),                                                  ".md"),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def log(msg):
    print(f"  [{time.strftime('%H:%M:%S')}] {msg}")

def write_session_log(entry):
    """Append to the running session log."""
    mode = "a" if SESSION_LOG.exists() else "w"
    header = "# CIS Kernel — Extractor Session Log\n\n" if mode == "w" else ""
    with open(SESSION_LOG, mode) as f:
        if header:
            f.write(header)
        f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n{entry}\n")

def estimate_tokens(text):
    """Rough token count (4 chars per token)."""
    return len(text) // 4

def load_prompt():
    """Load the extraction prompt from the architecture atlas."""
    if not PROMPT_FILE.exists():
        log(f"WARNING: Prompt file not found at {PROMPT_FILE}")
        return None
    return PROMPT_FILE.read_text(encoding="utf-8")

def find_source_files():
    """Find all source files not yet extracted. Returns list of (group, path)."""
    files = []
    EXCLUDE_DIRS = {'.git', '.obsidian', '__pycache__', 'node_modules',
                    'venv', '.venv', '.hermes', '.pytest_cache',
                    'captures', 'insights', 'extraction_analyses',
                    'functional_intents', 'ui_components', 'original_CISChats',
                    '.gallery', 'Saved'}
    for group_name, directory, ext in SOURCE_GROUPS:
        if not directory.exists():
            log(f"  Directory not found: {directory}")
            continue
        for fpath in sorted(directory.rglob(f"*{ext}")):
            parts = set(fpath.relative_to(directory).parts[:-1])
            if parts & EXCLUDE_DIRS:
                continue
            if fpath.is_file() and not fpath.name.startswith("."):
                files.append((group_name, fpath))
    return files

def already_extracted(fpath):
    """Check if this file has already been processed."""
    base = fpath.stem  # filename without extension
    # Normalize for matching extraction output names
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', base).lower()
    safe = re.sub(r'_+', '_', safe).strip('_')
    pattern = f"{safe}_extraction_analysis.md"
    return (OUTPUT_DIR / pattern).exists()

def get_output_path(fpath):
    """Generate the output file path for a source file."""
    base = fpath.stem
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', base).lower()
    safe = re.sub(r'_+', '_', safe).strip('_')
    return OUTPUT_DIR / f"{safe}_extraction_analysis.md"

def estimate_run_cost(files):
    """Estimate total cost for processing files."""
    total_input_tokens = 0
    prompt = load_prompt()
    prompt_tokens = estimate_tokens(prompt) if prompt else 2000

    for _, fpath in files:
        content = fpath.read_text(encoding="utf-8", errors="replace")
        total_input_tokens += prompt_tokens + estimate_tokens(content)

    # Assume output is ~50% of input
    total_output_tokens = total_input_tokens // 2

    cost_input  = (total_input_tokens / 1000) * COST_PER_1K_INPUT
    cost_output = (total_output_tokens / 1000) * COST_PER_1K_OUTPUT
    total_cost  = cost_input + cost_output

    return total_cost, total_input_tokens, total_output_tokens

# ── API Call ───────────────────────────────────────────────────────────────────

def call_deepseek(system_prompt, user_content):
    """Send to DeepSeek API and return the response content."""
    import httpx

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMP,
    }

    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(
                    f"{API_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = RATE_LIMIT_WAIT * (attempt + 1) * 5
                log(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif e.response.status_code == 401:
                log(f"  ERROR: API key rejected (401). Check DEEPSEEK_API_KEY.")
                return None
            else:
                log(f"  HTTP {e.response.status_code}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_WAIT * (attempt + 1))
        except Exception as e:
            log(f"  Error: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RATE_LIMIT_WAIT * (attempt + 1))

    log(f"  FAILED after {MAX_RETRIES} attempts.")
    return None

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIS Kernel Extractor Agent")
    parser.add_argument("--file", type=str, help="Process a single file path")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without doing it")
    parser.add_argument("--reset", action="store_true", help="Delete all existing extractions and reprocess")
    parser.add_argument("--group", type=str, help="Process only one group (vision, transcripts_claude, etc.)")
    args = parser.parse_args()

    # ── Validate API key ──
    if not API_KEY:
        print("\n  ERROR: DEEPSEEK_API_KEY environment variable not set.")
        print("  Set it with: export DEEPSEEK_API_KEY='sk-...'")
        sys.exit(1)

    print(f"\n  ═══ CIS Extractor Agent ═══")
    print(f"  API: DeepSeek ({MODEL})")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Max files: {MAX_FILES}")
    print(f"  Max retries: {MAX_RETRIES}")
    print()

    # ── Create output dir ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Reset if requested ──
    if args.reset:
        log("Resetting: deleting existing extractions...")
        for f in OUTPUT_DIR.glob("*_extraction_analysis.md"):
            f.unlink()
        log(f"  Deleted all extractions from {OUTPUT_DIR}")

    # ── Load prompt ──
    prompt = load_prompt()
    if not prompt:
        sys.exit(1)

    # ── Find files to process ──
    if args.file:
        fpath = Path(args.file)
        if not fpath.exists():
            print(f"  ERROR: File not found: {fpath}")
            sys.exit(1)
        # Determine group from path
        group = "custom"
        for gname, gdir, _ in SOURCE_GROUPS:
            if str(gdir) in str(fpath.parent):
                group = gname
                break
        files = [(group, fpath)]
    else:
        all_files = find_source_files()
        # Filter by group if requested
        if args.group:
            all_files = [(g, p) for g, p in all_files if g == args.group]
        # Exclude already extracted
        files = [(g, p) for g, p in all_files if not already_extracted(p)]

    if not files:
        print("  No files to process. All source files have been extracted.")
        print("  Use --reset to reprocess, or --file to target a single file.")
        sys.exit(0)

    # ── Apply safety cap ──
    if len(files) > MAX_FILES:
        log(f"  WARNING: {len(files)} files exceeds max of {MAX_FILES}. Truncating.")
        files = files[:MAX_FILES]

    # ── Cost estimate ──
    total_cost, input_tok, output_tok = estimate_run_cost(files)
    print(f"  Files to process: {len(files)}")
    print(f"  Estimated input tokens:  ~{input_tok:,}")
    print(f"  Estimated output tokens: ~{output_tok:,}")
    print(f"  Estimated API cost:      ${total_cost:.4f}")
    print()

    if args.dry_run:
        print("  Dry-run mode. Files that would be processed:")
        for group, fpath in files:
            print(f"    [{group}] {fpath.name}")
        print(f"\n  Total: {len(files)} files.")
        sys.exit(0)

    # ── Confirm ──
    if not args.file:
        print(f"  Starting extraction of {len(files)} files...")
        print(f"  Press Ctrl+C to stop at any time.")
        print()

    # ── Process files ──
    processed = 0
    failed = 0
    skipped = 0

    for idx, (group, fpath) in enumerate(files, 1):
        base_name = fpath.name
        log(f"[{idx}/{len(files)}] [{group}] {base_name}")

        # Read file content
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log(f"  ERROR reading file: {e}")
            failed += 1
            continue

        # Prepare the message: prompt + document
        user_message = f"Source file: {base_name}\nGroup: {group}\n\n---\n\n{content}"

        # Call API
        result = call_deepseek(prompt, user_message)

        if result is None:
            failed += 1
            continue

        # Save output
        output_path = get_output_path(fpath)
        output_content = f"# Extraction Analysis: {base_name}\n\n"
        output_content += f"**Source:** `{fpath}`\n"
        output_content += f"**Group:** {group}\n"
        output_content += f"**Extracted:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output_content += f"**Model:** {MODEL}\n\n"
        output_content += "---\n\n"
        output_content += result

        output_path.write_text(output_content, encoding="utf-8")
        processed += 1

        log(f"  ✓ Saved to {output_path.name}")

        # Rate limiting
        if idx < len(files):
            time.sleep(RATE_LIMIT_WAIT)

    # ── Summary ──
    print()
    print(f"  ═══ Complete ═══")
    print(f"  Processed: {processed}")
    print(f"  Failed:    {failed}")
    print(f"  Skipped:   {skipped}")
    print(f"  Output:    {OUTPUT_DIR}")

    # ── Update session log ──
    summary = (
        f"Extractor run complete.\n"
        f"- Files processed: {processed}\n"
        f"- Failed: {failed}\n"
        f"- Source groups: all project folders (cis/, ai_execution_infrastructure/, blender/, resolve/, unreal/)\n"
        f"- Output directory: {OUTPUT_DIR}\n"
        f"- Estimated cost: ${total_cost:.4f}"
    )
    write_session_log(summary)

    # Show remaining
    remaining = [(g, p) for g, p in find_source_files() if not already_extracted(p)]
    if remaining:
        print(f"\n  Files remaining: {len(remaining)}")
        for g, p in remaining[:5]:
            print(f"    [{g}] {p.name}")
        if len(remaining) > 5:
            print(f"    ... and {len(remaining) - 5} more")

if __name__ == "__main__":
    main()
