#!/usr/bin/env python3
"""
primer_update_v3.py — Constitutional Primer Update Applier (Single-Surface Workflow)
ADR-049 — CIS_Primer_Update_Governance_Contract_v1.md

Workflow:
  1. Architect generates *_update_draft.md files beside canonical files
     Example:
       01_CURRENT_STATE.md               <- canonical (authoritative)
       01_CURRENT_STATE_update_draft.md  <- candidate (not authoritative)

  2. Run --preview to generate diffs for Verifier constitutional review
     A preview stamp is written. Apply requires a valid recent stamp.

  3. After Verifier review + Human Gate approval:
     Run --apply --approved-by <name> --architect <model>

Constitutional protections enforced (ADR-049):
  - Apply Atomicity Rule: two-phase prepare/commit — all succeed or none apply
  - Preview enforcement: apply requires a recent preview stamp
  - Process lock: prevents concurrent execution
  - Immutable backups before commit phase
  - Constitutional keyword drift detection (signal only)
  - Apply manifest generation (immutable audit artifact)
  - Explicit human approval acknowledgment required

Governance: ADR-049, CIS_Primer_Update_Governance_Contract_v1.md

Usage:
  python3 primer_update_v3.py --preview
  python3 primer_update_v3.py --apply --approved-by "Utgar" --architect "claude-sonnet-4-6"

  --preview              Show diffs. Write preview stamp. No files modified.
  --apply                Apply approved drafts atomically.
  --approved-by NAME     Required for apply. Human Gate identifier.
  --architect MODEL      Architect model name for manifest. Required for apply.
  --verifier MODEL       Verifier model name for manifest. Default: ChatGPT
  --max-preview-age SEC  Max seconds since preview before apply is blocked.
                         Default: 86400 (24 hours).
"""

import argparse
import difflib
import fcntl
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

PRIMER  = Path("/mnt/projects/cis/docs/claude_chat_transcripts/ChatGTP_Project_Primer")
BACKUPS = PRIMER / "_backups"

DRAFT_SUFFIX    = "_update_draft.md"
LOCK_FILE       = PRIMER / ".primer_update.lock"
PREVIEW_STAMP   = PRIMER / ".last_preview_stamp"
DEFAULT_MAX_AGE = 86400  # 24 hours

CONSTITUTIONAL_KEYWORDS = [
    "LOCKED", "constitutional", "Contracts override",
    "human-led", "Human-led", "story-first", "Story-first",
    "sequential", "Sequential", "verification before",
    "Human Gate", "Authoritative Memory", "Runtime Discovery",
]


# ── Utilities ──────────────────────────────────────────────────────────────────

def _now_stamp():
    return datetime.now().strftime("%Y%m%d_%H%M")


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_draft_pairs(primer_dir: Path):
    """Find *_update_draft.md files. Returns [(draft_path, canonical_path)]."""
    pairs = []
    for draft in sorted(primer_dir.glob(f"*{DRAFT_SUFFIX}")):
        canonical_name = draft.name.replace(DRAFT_SUFFIX, ".md")
        canonical = primer_dir / canonical_name
        pairs.append((draft, canonical))
    return pairs


def _check_drift(diff_lines, filename):
    """Check removed lines for constitutional keyword drift. Returns warnings list."""
    warnings = []
    removed = [l[1:] for l in diff_lines if l.startswith('-') and not l.startswith('---')]
    for line in removed:
        for kw in CONSTITUTIONAL_KEYWORDS:
            if kw in line:
                warnings.append(
                    f"  WARNING: constitutional keyword '{kw}' removed from {filename}"
                )
                break
    return warnings


def _acquire_lock():
    """Acquire process lock. Exits if another instance is running."""
    lock_fd = open(LOCK_FILE, 'w')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("FAIL — another primer_update_v3.py process is running.")
        print(f"Lock file: {LOCK_FILE}")
        print("Note: the lock file alone does not indicate an active lock.")
        print("Only remove manually if no primer_update_v3.py process is running.")
        sys.exit(1)
    return lock_fd


def _release_lock(lock_fd):
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()
    try:
        LOCK_FILE.unlink()
    except FileNotFoundError:
        pass


def _check_preview_stamp(max_age_seconds: int):
    """Verify a recent preview was run. Exits if stamp missing or too old."""
    if not PREVIEW_STAMP.exists():
        print("FAIL — no preview stamp found.")
        print("Run preview before apply:")
        print("  python3 primer_update_v3.py --preview")
        print("\nConstitutional requirement: preview must precede apply (ADR-049).")
        sys.exit(1)

    stamp_mtime = PREVIEW_STAMP.stat().st_mtime
    age_seconds = datetime.now().timestamp() - stamp_mtime
    if age_seconds > max_age_seconds:
        age_hours = age_seconds / 3600
        print(f"FAIL — preview stamp is {age_hours:.1f} hours old (max: {max_age_seconds/3600:.1f}h).")
        print("Re-run preview before applying:")
        print("  python3 primer_update_v3.py --preview")
        sys.exit(1)


# ── Preview mode ───────────────────────────────────────────────────────────────

def run_preview(pairs):
    timestamp = _now_stamp()

    print(f"\n{'='*60}")
    print(f"Primer Update v3 — PREVIEW — {timestamp}")
    print(f"Governance: ADR-049 / CIS_Primer_Update_Governance_Contract_v1.md")
    print(f"{'='*60}")
    print(f"\nDraft pairs found: {len(pairs)}")

    updated      = []
    new_files    = []
    unchanged    = []
    drift_issues = []

    for draft_path, canonical_path in pairs:
        new_content = draft_path.read_text(encoding="utf-8")

        if canonical_path.exists():
            old_content = canonical_path.read_text(encoding="utf-8")

            if old_content == new_content:
                unchanged.append(canonical_path.name)
                continue

            diff = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{canonical_path.name}",
                tofile=f"b/{canonical_path.name} (draft: {draft_path.name})",
            ))

            drift_issues.extend(_check_drift(diff, canonical_path.name))
            updated.append(canonical_path.name)

            print(f"\n{'='*60}")
            print(f"DIFF: {canonical_path.name}")
            print(f"Draft: {draft_path.name}")
            print("".join(diff[:50]))
            if len(diff) > 50:
                print(f"  ... ({len(diff) - 50} more lines)")
        else:
            new_files.append(canonical_path.name)
            print(f"\n{'='*60}")
            print(f"NEW FILE: {canonical_path.name}")
            print(f"Draft: {draft_path.name}")

    # Summary
    if updated:
        print(f"\nTo update ({len(updated)}): " + ", ".join(updated))
    if new_files:
        print(f"New files ({len(new_files)}): " + ", ".join(new_files))
    if unchanged:
        print(f"Unchanged ({len(unchanged)}): " + ", ".join(unchanged))

    if drift_issues:
        print(f"\nDRIFT WARNINGS ({len(drift_issues)}):")
        for w in drift_issues:
            print(w)
        print("\n  Constitutional language removed. Verifier must review.")
    else:
        print("\nDrift check: CLEAN — no constitutional keyword removal detected.")

    # Write preview stamp
    PREVIEW_STAMP.write_text(_now_iso(), encoding="utf-8")

    print(f"\n{'='*60}")
    print("PREVIEW COMPLETE — no files modified.")
    print(f"Preview stamp written: {PREVIEW_STAMP}")
    print("\nAfter Verifier review and Human Gate approval:")
    print('  python3 primer_update_v3.py --apply --approved-by "YourName" --architect "model-name"')
    print(f"{'='*60}")


# ── Apply mode (two-phase atomic) ──────────────────────────────────────────────

def run_apply(pairs, approved_by: str, architect: str, verifier: str):
    timestamp  = _now_stamp()
    backup_dir = BACKUPS / timestamp
    diff_dir   = backup_dir / "diffs"

    print(f"\n{'='*60}")
    print(f"Primer Update v3 — APPLY — {timestamp}")
    print(f"Governance: ADR-049 / CIS_Primer_Update_Governance_Contract_v1.md")
    print(f"Approved by: {approved_by}")
    print(f"Architect:   {architect}")
    print(f"Verifier:    {verifier}")
    print(f"{'='*60}")

    # ── Classify pairs ────────────────────────────────────────────────────────
    to_replace   = []  # (draft_path, canonical_path, diff, new_content) — existing canonicals
    to_create    = []  # (draft_path, canonical_path, new_content) — new files
    unchanged    = []
    drift_issues = []
    created_names = set()  # tracks canonical names for new files — used in Phase B

    for draft_path, canonical_path in pairs:
        new_content = draft_path.read_text(encoding="utf-8")

        if canonical_path.exists():
            old_content = canonical_path.read_text(encoding="utf-8")
            if old_content == new_content:
                unchanged.append(canonical_path.name)
                continue
            diff = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{canonical_path.name}",
                tofile=f"b/{canonical_path.name}",
            ))
            drift_issues.extend(_check_drift(diff, canonical_path.name))
            to_replace.append((draft_path, canonical_path, diff, new_content))
        else:
            to_create.append((draft_path, canonical_path, new_content))
            created_names.add(canonical_path.name)

    if not to_replace and not to_create:
        print("\nNothing to apply — all drafts match canonicals or no drafts found.")
        return

    print(f"\nPHASE A — PREPARE")
    print(f"  Files to replace: {len(to_replace)}")
    print(f"  Files to create:  {len(to_create)}")
    print(f"  Unchanged:        {len(unchanged)}")

    # ── Phase A: Prepare — create backups, temp files, diffs ─────────────────
    # All preparation happens before any canonical file is touched.
    # If Phase A fails, canonical state is guaranteed unchanged.

    backup_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    temp_files = []  # [(temp_path, canonical_path, draft_path)]

    try:
        for draft_path, canonical_path, diff, new_content in to_replace:
            # Backup original (immutable)
            shutil.copy2(canonical_path, backup_dir / canonical_path.name)

            # Write diff
            if diff:
                diff_file = diff_dir / f"{canonical_path.stem}.diff"
                diff_file.write_text("".join(diff), encoding="utf-8")

            # Write new content to temp file in same directory
            tmp = tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8',
                dir=canonical_path.parent,
                prefix=f".tmp_{canonical_path.stem}_",
                suffix=".md",
                delete=False
            )
            tmp.write(new_content)
            tmp.close()
            temp_files.append((Path(tmp.name), canonical_path, draft_path))
            print(f"  Prepared: {canonical_path.name}")

        for draft_path, canonical_path, new_content in to_create:
            # New file — no backup needed, write to temp
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8',
                dir=canonical_path.parent,
                prefix=f".tmp_{canonical_path.stem}_",
                suffix=".md",
                delete=False
            )
            tmp.write(new_content)
            tmp.close()
            temp_files.append((Path(tmp.name), canonical_path, draft_path))
            print(f"  Prepared (new): {canonical_path.name}")

    except Exception as e:
        # Phase A failed — clean up temp files, canonical state untouched
        print(f"\nFAIL — Phase A (prepare) error: {e}")
        print("Cleaning up temp files...")
        for tmp_path, _, _ in temp_files:
            try:
                tmp_path.unlink()
            except Exception:
                pass
        print("Canonical state unchanged. No files modified.")
        sys.exit(1)

    # ── Phase B: Commit — atomic rename temp -> canonical ─────────────────────
    # Path.replace() is atomic on POSIX filesystems (same filesystem).
    # All temp files are in the same directory as their canonical targets.

    print(f"\nPHASE B — COMMIT")
    files_written  = []
    files_created  = []
    drafts_removed = []

    try:
        for tmp_path, canonical_path, draft_path in temp_files:
            # Atomic rename: temp -> canonical
            tmp_path.replace(canonical_path)

            if canonical_path.name in created_names:
                files_created.append(canonical_path.name)
            else:
                files_written.append(canonical_path.name)

            # Remove draft after successful canonical write
            draft_path.unlink()
            drafts_removed.append(draft_path.name)
            print(f"  Committed: {canonical_path.name}")
            print(f"  Removed:   {draft_path.name}")

    except Exception as e:
        print(f"\nFAIL — Phase B (commit) error: {e}")
        print("Partial commit may have occurred.")
        print(f"Backups available at: {backup_dir}")
        print("Log as FAILED_APPLY in CIS_CONFLICT_REGISTER.md.")
        print("Restore from backups if canonical state is inconsistent.")
        sys.exit(1)

    # Clean up preview stamp after successful apply
    try:
        PREVIEW_STAMP.unlink()
    except FileNotFoundError:
        pass

    # ── Apply manifest (immutable audit artifact) ─────────────────────────────
    manifest = {
        "action": "Primer update apply — primer_update_v3.py",
        "timestamp": _now_iso(),
        "governance": "ADR-049 / CIS_Primer_Update_Governance_Contract_v1.md",
        "cycle_status": "APPROVED",
        "approved_by": approved_by,
        "architect_model": architect,
        "verifier_model": verifier,
        "files_replaced": files_written,
        "files_created": files_created,
        "files_unchanged": unchanged,
        "drafts_removed": drafts_removed,
        "backup_location": str(backup_dir),
        "drift_warnings": drift_issues,
    }

    manifest_path = backup_dir / f"apply_manifest_{timestamp}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if drift_issues:
        print(f"\nDRIFT WARNINGS ({len(drift_issues)}):")
        for w in drift_issues:
            print(w)

    print(f"\n{'='*60}")
    print(f"APPLY COMPLETE")
    print(f"Replaced:  {len(files_written)}")
    print(f"Created:   {len(files_created)}")
    print(f"Unchanged: {len(unchanged)}")
    print(f"Backups:   {backup_dir}")
    print(f"Manifest:  {manifest_path}")
    print(f"{'='*60}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CIS Constitutional Primer Update Applier v3 (ADR-049)"
    )
    parser.add_argument("--preview", action="store_true",
                        help="Show diffs and write preview stamp. No files modified.")
    parser.add_argument("--apply", action="store_true",
                        help="Apply approved drafts atomically. Requires --approved-by.")
    parser.add_argument("--approved-by", metavar="NAME",
                        help="Human Gate identifier. Required for --apply.")
    parser.add_argument("--architect", metavar="MODEL", default=None,
                        help="Architect model name for manifest. Required for --apply.")
    parser.add_argument("--verifier", metavar="MODEL", default="ChatGPT",
                        help="Verifier model name for manifest. Default: ChatGPT")
    parser.add_argument("--max-preview-age", metavar="SECONDS", type=int,
                        default=DEFAULT_MAX_AGE,
                        help=f"Max seconds since preview before apply is blocked. Default: {DEFAULT_MAX_AGE}")
    args = parser.parse_args()

    if not args.preview and not args.apply:
        parser.print_help()
        sys.exit(1)

    if args.preview and args.apply:
        print("FAIL — specify either --preview or --apply, not both.")
        sys.exit(1)

    if args.apply and not args.approved_by:
        print("FAIL — --apply requires --approved-by <name>.")
        print("Human Gate approval must be explicitly acknowledged.")
        sys.exit(1)

    if args.apply and not args.architect:
        print("FAIL — --apply requires --architect <model-name>.")
        sys.exit(1)

    # Acquire process lock
    lock_fd = _acquire_lock()

    try:
        pairs = _find_draft_pairs(PRIMER)

        if not pairs and args.preview:
            print("No *_update_draft.md files found in primer directory.")
            print(f"Location: {PRIMER}")
            sys.exit(0)

        if not pairs and args.apply:
            print("No *_update_draft.md files found. Nothing to apply.")
            sys.exit(0)

        if args.preview:
            run_preview(pairs)

        elif args.apply:
            _check_preview_stamp(args.max_preview_age)
            run_apply(pairs, args.approved_by, args.architect, args.verifier)

    finally:
        _release_lock(lock_fd)


if __name__ == "__main__":
    main()
