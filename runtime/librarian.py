#!/usr/bin/env python3
"""
librarian.py — CIS Kernel Librarian Agent

Reads every source file in the project, extracts its durable essence,
and registers it in the kernel workspace. Does NOT move or modify originals.

Outputs:
  - cis_kernel/source/ — symlinks to source material organized by type
  - cis_kernel/source/MANIFEST.md — index of what was registered
  - cis_kernel/source/SESSION_LOG.md — record of what was processed each run

Usage:
  python3 librarian.py --create        # create directory structure only
  python3 librarian.py --register      # register all known sources (topology-based)
  python3 librarian.py --scan          # scan project dir for all files (catch-all)
  python3 librarian.py --all           # full build: create + register
"""

import os, sys, json, shutil, time
from pathlib import Path
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/mnt/projects/cis")
KERNEL_DIR    = PROJECT_ROOT / "cis_kernel"
ARCHIVE_DIRS  = [
    PROJECT_ROOT / "docs/_archive/CIS_Creative_Intelligence_System_LegacyBuildFiles",
    PROJECT_ROOT / "docs/_archive/CIS_Canonical_Build_Sequence",
]
DOCS_DIR      = PROJECT_ROOT / "docs"
RUNTIME_DIR   = PROJECT_ROOT / "runtime"
LOGS_DIR      = PROJECT_ROOT / "logs"

# ── Source topology (from cis_kernel_source_topology.md) ──────────────────────
# Every file in the project has value. These groups organize by type.
# The catch-all scan (--scan) picks up anything missed.
SOURCE_GROUPS = {
    "vision": {
        "base_path": ARCHIVE_DIRS[0],
        "globs": ["X_*.md", "x_*.md", "_CIS_*.md", "Hand-offs/*.md"],
        "priority": "HIGH",
        "desc": "LegacyBuildFiles — ground truth, written WITH Eric"
    },
    "transcripts_claude": {
        "base_path": DOCS_DIR / "claude_chat_transcripts",
        "globs": ["2026-04-*.md", "2026-05-*.md", "captures/*.md",
                   "insights/*.md", "ChatGTP_Project_Primer/**/*.md"],
        "priority": "MEDIUM",
        "desc": "Claude & ChatGPT transcripts — raw exploration"
    },
    "transcripts_original": {
        "base_path": DOCS_DIR / "architecture_atlas/original_CISChats",
        "globs": ["CIS_Chat_*.md", "architecture_atlas_prompt*.md"],
        "priority": "MEDIUM",
        "desc": "Original CIS chats — early development"
    },
    "extraction_analyses": {
        "base_path": DOCS_DIR / "architecture_atlas",
        "globs": ["*extraction_analysis*.md"],
        "priority": "MEDIUM",
        "desc": "Model-written extraction summaries of chat sessions"
    },
    "architecture_maps": {
        "base_path": DOCS_DIR,
        "globs": ["CIS_FILE_MAP.md", "YOUR_DOCUMENT_MAP.md",
                   "CIS_CONFLICT_REGISTER.md",
                   "claude_chat_transcripts/insights/*.md",
                   "claude_chat_transcripts/ChatGTP_Project_Primer/13_RUNTIME_TOPOLOGY.md",
                   "architecture_atlas/original_CISChats/architecture_atlas_prompt.md"],
        "priority": "HIGH",
        "desc": "Architecture maps, cross-references, topology documents"
    },
    "build_plans": {
        "base_path": ARCHIVE_DIRS[1],
        "globs": ["*.md", "*.txt", "*.svg", "*.html"],
        "priority": "HIGH",
        "desc": "Build sequences and roadmaps"
    },
    "handoffs": {
        "base_path": ARCHIVE_DIRS[0] / "Hand-offs",
        "globs": ["*.md"],
        "priority": "SITUATIONAL",
        "desc": "Session handoff documents"
    },
    "adrs": {
        "base_path": DOCS_DIR / "ADRs",
        "globs": ["ADR-*.md"],
        "priority": "LOW",
        "desc": "Architecture Decision Records — governance artifacts"
    },
    "runtime_code": {
        "base_path": RUNTIME_DIR,
        "globs": ["**/*.py", "**/*.html", "**/*.css", "**/*.js", "**/*.json"],
        "priority": "REFERENCE",
        "desc": "Running application code and UI"
    },
    "obsidian_vault": {
        "base_path": DOCS_DIR / "CIS_Creative_Intelligence_System_v1",
        "globs": ["**/*.md"],
        "priority": "REFERENCE",
        "desc": "Obsidian vault — git mirrored CIS documentation"
    },
    "session_logs": {
        "base_path": LOGS_DIR,
        "globs": ["*.md", "session_records/*.md", "session_records/*.json"],
        "priority": "SITUATIONAL",
        "desc": "Session logs and minutes records"
    },
    "other_docs": {
        "base_path": DOCS_DIR,
        "globs": ["**/*.md", "**/*.txt", "**/*.json", "**/*.yaml", "**/*.yml",
                   "**/*.svg", "**/*.png", "**/*.jpg", "**/*.xlsx"],
        "priority": "SITUATIONAL",
        "desc": "Other documents throughout the docs folder"
    },
}

# ── Directory structure ────────────────────────────────────────────────────────
KERNEL_TREE = {
    "identity": ["concept.md", "intent.md", "domain.cfg"],
    "source": {
        "vision": [],
        "transcripts": [],
        "references": [],
        "captures": [],
    },
    "extraction": {
        "functional_intents": [],
        "patterns": [],
        "conflicts": [],
        "gaps": [],
    },
    "research": {
        "references": [],
        "solutions": [],
        "experiments": [],
    },
    "design": {
        "mockups": [],
        "architecture": [],
        "decisions": [],
    },
    "build": {
        "plan": [],
        "code": [],
        "tests": [],
        "progress": [],
    },
    "polish": {
        "issues": [],
        "feedback": [],
    },
    "release": {
        "builds": [],
        "docs": [],
        "notes": [],
    },
}

# ── Exclusions (directories to skip in catch-all scan) ────────────────────────
EXCLUDE_DIRS = {"node_modules", "__pycache__", ".git", ".obsidian",
                ".venv", "venv", ".git"}

def create_structure(base: Path, tree: dict, dry_run=False):
    """Recursively create directory structure from tree spec."""
    created = []
    for name, contents in tree.items():
        dir_path = base / name
        if not dry_run:
            dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
        if isinstance(contents, dict):
            created += create_structure(dir_path, contents, dry_run)
        elif isinstance(contents, list):
            for fname in contents:
                fpath = dir_path / fname
                if not dry_run and not fpath.exists():
                    if "." in str(fname):
                        fpath.write_text(f"# {fname}\n\n")
                    else:
                        fpath.mkdir(parents=True, exist_ok=True)
                created.append(str(fpath))
    return created

def find_sources():
    """Find all source files matching the defined groups."""
    results = {}
    for group_name, group in SOURCE_GROUPS.items():
        matches = []
        base = group["base_path"]
        if not base.exists():
            continue
        for pattern in group["globs"]:
            found = list(base.rglob(pattern))
            matches.extend([str(f) for f in found if f.is_file()])
        results[group_name] = {
            "files": sorted(set(matches)),
            "priority": group["priority"],
            "desc": group["desc"],
            "count": len(set(matches)),
        }
    return results

def register_sources(sources, base_dir: Path, symlink=True):
    """Create symlinks to source files organized by group in source/."""
    source_dir = base_dir / "source"
    registered = []
    for group_name, info in sources.items():
        target_dir = source_dir / group_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for src_path in info["files"]:
            src = Path(src_path)
            link = target_dir / src.name
            if link.exists():
                link = target_dir / f"{src.parent.name}_{src.name}"
            if link.exists():
                stamp = src.stat().st_mtime_ns
                link = target_dir / f"{stamp}_{src.name}"
            try:
                if symlink:
                    os.symlink(str(src.resolve()), str(link))
                else:
                    shutil.copy2(str(src), str(link))
                registered.append(str(link))
            except FileExistsError:
                registered.append(f"{link} (already exists)")
            except Exception as e:
                registered.append(f"{src} — ERROR: {e}")
    return registered

def write_manifest(sources, registered, base_dir: Path):
    """Write a detailed manifest of all registered source material."""
    lines = [
        "# CIS Kernel v1 — Source Manifest\n",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"Kernel root: {base_dir}\n\n",
        "## Summary\n\n",
        "| Group | Count | Priority | Description |\n",
        "|-------|-------|----------|-------------|\n",
    ]
    total = sum(s["count"] for s in sources.values())
    for name, info in sorted(sources.items()):
        lines.append(f"| {name} | {info['count']} | {info['priority']} | {info['desc']} |\n")
    lines.append(f"\n**Total: {total} source files registered**\n\n")
    lines.append("## Files by Group\n\n")
    for name, info in sorted(sources.items()):
        if info["count"] == 0:
            continue
        lines.append(f"### {name} ({info['count']} files, priority: {info['priority']})\n\n")
        for f in sorted(info["files"]):
            status = "✓" if any(f in r for r in registered) else "?"
            lines.append(f"- [{status}] {f}\n")
        lines.append("\n")
    manifest_path = base_dir / "source" / "MANIFEST.md"
    manifest_path.write_text("".join(lines))
    return str(manifest_path)

def write_session_log(base_dir: Path, action: str, detail: str):
    """Append to the running session log."""
    log_path = base_dir / "source" / "SESSION_LOG.md"
    entry = f"\n## {time.strftime('%Y-%m-%d %H:%M:%S')} — {action}\n\n{detail}\n"
    mode = "a" if log_path.exists() else "w"
    header = "# CIS Kernel — Librarian Session Log\n\n" if mode == "w" else ""
    with open(log_path, mode) as f:
        f.write(header + entry)

def scan_all_files():
    """Catch-all scan: find EVERY file in the project with known extensions."""
    known_extensions = {'.md', '.py', '.html', '.js', '.css', '.json', 
                        '.yaml', '.yml', '.txt', '.svg', '.png', '.jpg',
                        '.jpeg', '.gif', '.xlsx', '.xls', '.cfg', '.ini',
                        '.toml', '.csv', '.xml', '.diff', '.sh', '.envrc'}
    all_files = []
    for root, dirs, files in os.walk(str(PROJECT_ROOT)):
        # Skip exclusions
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        # Skip hermes home, vendor dirs
        if '.hermes' in root or 'node_modules' in root or '.git' in root:
            dirs.clear()
            continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in known_extensions:
                all_files.append(os.path.join(root, f))
    return sorted(all_files)

# ── CLI ─────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="CIS Kernel Librarian Agent")
    parser.add_argument("--create", action="store_true", help="Create kernel directory structure")
    parser.add_argument("--register", action="store_true", help="Register source files (symlink into source/)")
    parser.add_argument("--scan", action="store_true", help="Scan project root for all files (catch-all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    parser.add_argument("--copy", action="store_true", help="Copy files instead of symlinking")
    parser.add_argument("--all", action="store_true", help="Full build: create + register")
    args = parser.parse_args()

    if not any([args.create, args.register, args.scan, args.all]):
        parser.print_help()
        sys.exit(0)

    if args.all:
        args.create = True
        args.register = True

    base = KERNEL_DIR
    detail_lines = []

    # ── Create structure ──
    if args.create:
        print(f"  Creating kernel structure at {base}...")
        created = create_structure(base, KERNEL_TREE, dry_run=args.dry_run)
        for p in sorted(created):
            print(f"    {p}")
        detail_lines.append(f"Created {len(created)} directories/files")
        if not args.dry_run:
            write_session_log(base, "CREATE STRUCTURE", f"Created {len(created)} items")

    # ── Register sources ──
    if args.register:
        print(f"\n  Finding source files...")
        sources = find_sources()
        for name, info in sorted(sources.items()):
            if info["count"] > 0:
                print(f"    {name}: {info['count']} files ({info['priority']})")

        total = sum(s["count"] for s in sources.values())
        print(f"\n  Total: {total} source files found")

        if not args.dry_run:
            print(f"\n  Registering sources...")
            registered = register_sources(sources, base, symlink=not args.copy)
            print(f"  Creating manifest...")
            manifest = write_manifest(sources, registered, base)
            print(f"  Manifest written to: {manifest}")
            summary = f"Registered {total} files across {len([s for s in sources.values() if s['count'] > 0])} groups. Manifest: {manifest}"
            write_session_log(base, "REGISTER SOURCES", summary)
            detail_lines.append(summary)
        else:
            print(f"\n  (dry-run — no files registered)")

    # ── Scan for all files (catch-all) ──
    if args.scan:
        print(f"\n  Scanning project root for ALL files ({PROJECT_ROOT})...")
        all_files = scan_all_files()
        print(f"  Found {len(all_files)} files with known extensions")
        ext_counts = Counter(os.path.splitext(f)[1].lower() for f in all_files)
        for ext, count in sorted(ext_counts.items()):
            print(f"    {ext}: {count}")

        if not args.dry_run:
            scan_path = base / "source" / "FULL_SCAN.md"
            lines = [
                f"# Full Project Scan — {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                f"**Total files found:** {len(all_files)}\n\n",
                "## File Counts by Extension\n\n",
            ]
            for ext, count in sorted(ext_counts.items()):
                lines.append(f"- `{ext}`: {count}\n")
            lines.append("\n## All Files\n\n")
            for f in all_files:
                lines.append(f"- {f}\n")
            scan_path.write_text("".join(lines))
            print(f"\n  Full scan written to: {scan_path}")

    print(f"\n  Done.")

if __name__ == "__main__":
    main()
