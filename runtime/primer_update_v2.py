#!/usr/bin/env python3
"""
primer_update_v2.py — Safe primer update applier.

Reads content from primer_update_content/ folder (one .md per primer file).
For each file:
  1. Creates a timestamped backup in PRIMER/_backups/
  2. Generates a unified diff and writes it to _backups/
  3. Writes the new content
  4. Reports changes

Usage:
  python3 primer_update_v2.py [--preview]

  --preview   Show diffs without writing. No files modified.

Content source:
  /mnt/projects/cis/docs/claude_chat_transcripts/ChatGTP_Project_Primer/_update_staging/

Place updated .md files in _update_staging/ before running.
Any file not present in _update_staging/ is left untouched.
"""

import argparse
import difflib
import shutil
import sys
from datetime import datetime
from pathlib import Path

PRIMER        = Path("/mnt/projects/cis/docs/claude_chat_transcripts/ChatGTP_Project_Primer")
STAGING       = PRIMER / "_update_staging"
BACKUPS       = PRIMER / "_backups"
DISTILLATIONS = PRIMER / "SESSION_DISTILLATIONS"

def run(preview: bool):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_dir = BACKUPS / timestamp
    diff_dir   = backup_dir / "diffs"

    if not STAGING.exists():
        print(f"FAIL — staging folder not found: {STAGING}")
        print("Create it and place updated .md files there before running.")
        sys.exit(1)

    staged_files = sorted(STAGING.glob("*.md"))
    staged_distillations = sorted((STAGING / "SESSION_DISTILLATIONS").glob("*.md")) \
        if (STAGING / "SESSION_DISTILLATIONS").exists() else []

    if not staged_files and not staged_distillations:
        print("No staged files found. Nothing to apply.")
        sys.exit(0)

    if not preview:
        backup_dir.mkdir(parents=True, exist_ok=True)
        diff_dir.mkdir(parents=True, exist_ok=True)
        DISTILLATIONS.mkdir(exist_ok=True)

    updated      = []
    new_files    = []
    unchanged    = []
    drift_issues = []

    all_staged = [(f, PRIMER / f.name) for f in staged_files] + \
                 [(f, DISTILLATIONS / f.name) for f in staged_distillations]

    for staged_path, target_path in all_staged:
        new_content = staged_path.read_text(encoding="utf-8")

        if target_path.exists():
            old_content = target_path.read_text(encoding="utf-8")

            if old_content == new_content:
                unchanged.append(target_path.name)
                continue

            diff = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{target_path.name}",
                tofile=f"b/{target_path.name}",
            ))

            # Drift detection: warn if lines removed that contain constitutional keywords
            constitutional_keywords = [
                "LOCKED", "constitutional", "Contracts override",
                "human-led", "Human-led", "story-first", "Story-first",
                "sequential", "Sequential", "verification before",
            ]
            removed_lines = [l[1:] for l in diff if l.startswith('-') and not l.startswith('---')]
            for line in removed_lines:
                for kw in constitutional_keywords:
                    if kw in line:
                        drift_issues.append(
                            f"  WARNING: constitutional keyword '{kw}' removed from {target_path.name}"
                        )
                        break

            if not preview:
                # Backup original
                shutil.copy2(target_path, backup_dir / target_path.name)
                # Write diff
                diff_file = diff_dir / f"{target_path.stem}.diff"
                diff_file.write_text("".join(diff), encoding="utf-8")
                # Write new content
                target_path.write_text(new_content, encoding="utf-8")

            updated.append(target_path.name)

            if preview:
                print(f"\n{'='*60}")
                print(f"DIFF: {target_path.name}")
                print("".join(diff[:40]))
                if len(diff) > 40:
                    print(f"  ... ({len(diff)-40} more lines)")
        else:
            if not preview:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(new_content, encoding="utf-8")
            new_files.append(target_path.name)

    # ── Report ────────────────────────────────────────────────────────────────
    mode = "PREVIEW" if preview else "APPLIED"
    print(f"\n{'='*60}")
    print(f"Primer Update — {mode} — {timestamp}")
    print(f"{'='*60}")

    if updated:
        print(f"\nUpdated ({len(updated)}):")
        for f in updated:
            print(f"  ✓ {f}")

    if new_files:
        print(f"\nNew files ({len(new_files)}):")
        for f in new_files:
            print(f"  + {f}")

    if unchanged:
        print(f"\nUnchanged ({len(unchanged)}):")
        for f in unchanged:
            print(f"  — {f}")

    if drift_issues:
        print(f"\nDRIFT WARNINGS ({len(drift_issues)}):")
        for w in drift_issues:
            print(w)
        print("\n  Review diffs before confirming. Constitutional language may have been removed.")

    if not preview and (updated or new_files):
        print(f"\nBackups written to: {backup_dir}")
        print(f"Diffs written to:   {diff_dir}")

    if not drift_issues:
        print("\nPRIMER UPDATE: CLEAN — no constitutional drift detected.")
    else:
        print(f"\nPRIMER UPDATE: REVIEW REQUIRED — {len(drift_issues)} drift warning(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safe CIS primer update applier")
    parser.add_argument("--preview", action="store_true",
                        help="Show diffs without writing any files")
    args = parser.parse_args()
    run(preview=args.preview)
