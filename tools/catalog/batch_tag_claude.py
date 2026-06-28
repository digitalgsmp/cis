#!/usr/bin/env python3
"""
Batch Tag Pipeline: Claude Export → Local-First Tagging → Tagged Output

MODEL POLICY (hardwired):
  PRIMARY:  qwen (local GPU, llama-server port 8002, FREE — 124 files)
  SECONDARY: ds-reasoner (DeepSeek API, cheapest at ~$5 for 124 files)
  CODING ONLY: claude-opus (Anthropic API — NOT for bulk tagging)
  API-BASED: glm-5.2, glm (OpenRouter — skip for bulk to save cost)

Reads pre-processed conversation files, sends each to the configured models
with the v3.1 tagging directive, and saves tagged output to a results directory.

Usage:
    python3 tools/catalog/batch_tag_claude.py --start 0 --end 10
    python3 tools/catalog/batch_tag_claude.py --all
    python3 tools/catalog/batch_tag_claude.py --all --models qwen ds-reasoner
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

PORTAL_URL = "http://localhost:5000/api/portal/chat-direct"
INPUT_DIR = "/mnt/projects/cis/enforcement/mwl-proof-v2/tagging_input/claude_export"
OUTPUT_DIR = "/mnt/projects/cis/enforcement/mwl-proof-v2/tagging_results/claude_export"
DIRECTIVE_PATH = "/mnt/projects/cis/enforcement/TAGGING_DIRECTIVE_v3.md"

# HARDWIRED: local-first for bulk inference. Only add paid models when
# explicitly requested via --models flag. Claude is coding-only.
DEFAULT_MODELS = ["ds-reasoner"]
ALL_KNOWN_MODELS = {
    "qwen":         {"label": "Qwen 30B (local GPU)",        "cost": "FREE"},
    "ds-reasoner":  {"label": "DeepSeek Reasoner (API)",     "cost": "~$5/124"},
    "glm-5.2":      {"label": "GLM 5.2 (OpenRouter API)",    "cost": "~$20/124"},
    "claude-opus":  {"label": "Claude Opus 4.8 (API)",       "cost": "~$168/124 — CODING ONLY"},
}
RETRY_DELAY = 30  # seconds between retries
MAX_RETRIES = 3


def load_directive():
    """Load the tagging directive."""
    with open(DIRECTIVE_PATH) as f:
        directive = f.read()
    return directive


def call_model(model, message, timeout=180):
    """Call a direct model via the portal API."""
    payload = json.dumps({
        "model": model,
        "message": message
    }).encode('utf-8')
    
    req = urllib.request.Request(
        PORTAL_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.fp else str(e)
        return {"error": f"HTTP {e.code}", "body": body[:500]}
    except Exception as e:
        return {"error": str(e)}


def tag_file(filepath, filename, model, directive):
    """Tag a single file with a single model."""
    # Read the conversation
    with open(filepath) as f:
        content = f.read()
    
    # Build the tagging prompt
    prompt = f"""{directive}

═══════════════════════════════════════════════════════════
DOCUMENT TO TAG
═══════════════════════════════════════════════════════════

{content}

═══════════════════════════════════════════════════════════
Tag the ENTIRE document above. Every 5-15 lines gets a tagged block with metadata.
Create new categories freely.
═══════════════════════════════════════════════════════════"""
    
    # Call the model
    for attempt in range(MAX_RETRIES):
        result = call_model(model, prompt)
        
        if "error" not in result:
            return result
        
        print(f"    Attempt {attempt+1} failed: {result['error']}", file=sys.stderr)
        if attempt < MAX_RETRIES - 1:
            print(f"    Retrying in {RETRY_DELAY}s...", file=sys.stderr)
            time.sleep(RETRY_DELAY)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Batch tag Claude export conversations")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Process all files")
    group.add_argument("--start", type=int, help="Start index")
    parser.add_argument("--end", type=int, help="End index (exclusive)")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                        help=f"Models to use (default: {' '.join(DEFAULT_MODELS)})")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()
    
    # Load directive
    directive = load_directive()
    print(f"Loaded directive: {len(directive)} chars")
    
    # Get file list
    files = sorted(os.listdir(INPUT_DIR))
    files = [f for f in files if f.endswith('.txt')]
    total_files = len(files)
    print(f"Found {total_files} files in {INPUT_DIR}")
    
    # Determine range
    if args.all:
        start, end = 0, total_files
    else:
        start = args.start
        end = min(args.end or total_files, total_files)
    
    batch = files[start:end]
    print(f"Processing files [{start}:{end}] ({len(batch)} files)")
    print(f"Models: {', '.join(args.models)}")
    print(f"Total API calls: {len(batch)} × {len(args.models)} = {len(batch) * len(args.models)}")
    
    if args.dry_run:
        print("\nDRY RUN — would process:")
        for f in batch[:5]:
            print(f"  {f}")
        if len(batch) > 5:
            print(f"  ... and {len(batch)-5} more")
        
        # Cost estimate
        print(f"\nCOST ESTIMATE:")
        avg_chars = sum(os.path.getsize(os.path.join(INPUT_DIR, f)) for f in batch) / len(batch)
        avg_tokens_in = (avg_chars / 4) + (len(directive) / 4)
        avg_tokens_out = avg_tokens_in * 0.77  # output ratio from test
        
        for model in args.models:
            info = ALL_KNOWN_MODELS.get(model, {})
            label = info.get("label", model)
            cost_str = info.get("cost", "?")
            print(f"  {label}: {cost_str}")
        
        return
    
    # Create output dirs
    for model in args.models:
        os.makedirs(os.path.join(OUTPUT_DIR, model), exist_ok=True)
    
    # Process files
    completed = 0
    errors = 0
    start_time = time.time()
    
    for i, filename in enumerate(batch):
        filepath = os.path.join(INPUT_DIR, filename)
        file_num = start + i + 1
        elapsed = time.time() - start_time
        
        print(f"\n[{file_num}/{end}] {filename} ({elapsed:.0f}s elapsed)")
        
        for model in args.models:
            model_label = ALL_KNOWN_MODELS.get(model, {}).get("label", model)
            out_path = os.path.join(OUTPUT_DIR, model, f"{filename}__{model}.txt")
            
            # Skip if already done
            if os.path.exists(out_path):
                print(f"  {model_label}: SKIP (already exists)")
                completed += 1
                continue
            
            print(f"  {model_label}: tagging...", end='', flush=True)
            result = tag_file(filepath, filename, model, directive)
            
            if "error" in result:
                print(f" FAILED: {result['error'][:100]}")
                errors += 1
                # Save error
                with open(out_path, 'w') as f:
                    f.write(f"ERROR: {json.dumps(result, indent=2)}\n")
            else:
                response = result.get('response', '')
                reasoning = result.get('reasoning', '')
                print(f" OK ({len(response)} chars response, {len(reasoning)} reasoning)")
                completed += 1
                
                # Save tagged output
                with open(out_path, 'w') as f:
                    if reasoning:
                        f.write(f"# MODEL REASONING\n{reasoning}\n\n")
                    f.write(f"# TAGGED OUTPUT\n{response}\n")
            
            # Small delay between calls to avoid rate limits
            time.sleep(2)
    
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"DONE: {completed} completed, {errors} errors")
    print(f"Time: {total_time:.0f}s ({total_time/3600:.1f}h)")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
