#!/usr/bin/env python3
"""
CIS Phase 4A — Deterministic Briefing Freshness Verifier v0.1

Verifies that CURRENT_CONTEXT_BRIEFING.md is fresh relative to its canonical
source files.  This is a standalone, deterministic script: no LLM calls,
no self-reporting, no external dependencies beyond Python stdlib.

Usage:
    python3 /mnt/projects/cis/tools/verify_context_briefing_freshness.py

Standard CIS Verifier Exit-Code Convention (seed standard for Phase 4B+):
    0 = PASS / verified — briefing exists, is fresh, and structurally valid.
    1 = RECOVERABLE FAIL — briefing is stale OR regeneration was attempted
        but the briefing could not be brought fresh.
    2 = HARD FAIL — missing source file, missing output file, malformed
        briefing content, or unsafe state that cannot be auto-recovered.

Auto-regeneration: when the briefing is stale (exit 1 condition) the script
attempts to regenerate it via:
    python3 /mnt/projects/cis/tools/generate_context_briefing.py --write
After regeneration the full validation sequence runs again.  A regenerated
briefing that passes all checks exits 0.  A regenerated briefing that is
still stale or missing structural markers exits 1.

Source files must match the exact set read by generate_context_briefing.py.
If that generator's source list changes, this verifier must be updated to
match.  The generator is the authority; this verifier follows.

Design constraint: this script reads files, compares timestamps, and may
invoke an external regeneration command.  It never writes canonical content
directly — the generator owns all writes to CURRENT_CONTEXT_BRIEFING.md.
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = "/mnt/projects/cis"

# ── Source files — MUST match generate_context_briefing.py SOURCE_FILES ──
# Static sources (always checked)
STATIC_SOURCES: list[str] = [
    os.path.join(PROJECT_ROOT, "docs/CIS_CURRENT_STATE.md"),
    os.path.join(PROJECT_ROOT, "docs/CIS_CONTEXT_CONTRACT.md"),
    os.path.join(PROJECT_ROOT, "docs/CIS_CORE_BOUNDARY.md"),
    os.path.join(PROJECT_ROOT, "seed_intent_corpus/SEED_INTENT_EXCERPTS.md"),
    os.path.join(PROJECT_ROOT, "seed_intent_corpus/SESSION_ORIENTATION_PROMPT.md"),
    os.path.join(PROJECT_ROOT, "cis_kernel/build/CIS_SCRATCHPAD.md"),
    os.path.join(PROJECT_ROOT, "PROJECT_CONTEXT_PACK/05_NEXT_ACTIONS.md"),
]

# Dynamic source: latest handoff (resolved at runtime, same logic as generator)
HANDOFF_DIR = os.path.join(PROJECT_ROOT, "session_handoffs")

# Output file
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "session_handoffs/CURRENT_CONTEXT_BRIEFING.md")

# Regeneration command
REGEN_CMD = [
    sys.executable,
    os.path.join(PROJECT_ROOT, "tools/generate_context_briefing.py"),
    "--write",
]

# Required structural markers in the briefing
REQUIRED_MARKERS = [
    "CIS Context Briefing",
    "Generated:",
    "Current Operational State",
    "Current Objective",
    "Next Safe Action",
]


def _find_latest_handoff() -> str | None:
    """Return path to the newest HANDOFF_*.md, or None."""
    if not os.path.isdir(HANDOFF_DIR):
        return None
    files = sorted(
        [f for f in os.listdir(HANDOFF_DIR)
         if f.startswith("HANDOFF_") and f.endswith(".md")],
        reverse=True,
    )
    return os.path.join(HANDOFF_DIR, files[0]) if files else None


def _resolve_all_sources() -> tuple[list[str], list[str]]:
    """Return (all_source_paths, missing_paths)."""
    sources = list(STATIC_SOURCES)
    handoff = _find_latest_handoff()
    if handoff:
        sources.append(handoff)
    else:
        # No handoff is not a hard fail — the generator tolerates it
        pass

    missing = [s for s in sources if not os.path.isfile(s)]
    return sources, missing


def _max_source_mtime(sources: list[str]) -> float:
    """Return the highest mtime among all source files."""
    return max(os.path.getmtime(s) for s in sources)


def _check_structural_markers(path: str) -> list[str]:
    """Return list of missing marker strings (empty = all present)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return list(REQUIRED_MARKERS)  # can't read = all missing

    return [m for m in REQUIRED_MARKERS if m not in content]


def _regenerate() -> bool:
    """Run the regeneration command. Return True on success (exit 0)."""
    try:
        result = subprocess.run(
            REGEN_CMD,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"[verifier] regeneration command exited {result.returncode}",
                  file=sys.stderr)
            if result.stderr.strip():
                print(f"[verifier] stderr: {result.stderr.strip()[:500]}",
                      file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        print("[verifier] regeneration command timed out after 60s",
              file=sys.stderr)
        return False
    except Exception as e:
        print(f"[verifier] regeneration command failed: {e}", file=sys.stderr)
        return False


def _ts_display(ts: float) -> str:
    """Format a Unix timestamp for human-readable output."""
    from datetime import datetime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def main() -> int:
    # ── Phase 1: Check source files exist ──────────────────────────
    sources, missing_sources = _resolve_all_sources()
    if missing_sources:
        for m in missing_sources:
            print(f"HARD FAIL: missing source file {m}", file=sys.stderr)
        print(f"HARD FAIL: missing source file(s): {', '.join(missing_sources)}")
        return 2

    # ── Phase 2: Check output file exists ──────────────────────────
    if not os.path.isfile(OUTPUT_FILE):
        print(f"HARD FAIL: briefing file missing: {OUTPUT_FILE}", file=sys.stderr)
        # Try regeneration — maybe it was deleted but sources are fine
        print("[verifier] attempting regeneration (briefing file missing)...",
              file=sys.stderr)
        if _regenerate():
            # Fall through to validation
            if not os.path.isfile(OUTPUT_FILE):
                print(f"HARD FAIL: briefing file still missing after regeneration: {OUTPUT_FILE}")
                return 2
        else:
            print(f"HARD FAIL: briefing file missing and regeneration failed: {OUTPUT_FILE}")
            return 2

    # ── Phase 3: Validate (used by both initial check and post-regeneration) ──
    return _validate(sources)


def _validate(sources: list[str]) -> int:
    """Full validation: freshness + structural markers.  Called on initial
    check AND after regeneration so a regenerated briefing must pass all
    checks before exiting 0."""

    # Freshness check
    latest_source_mtime = _max_source_mtime(sources)
    briefing_mtime = os.path.getmtime(OUTPUT_FILE)
    is_fresh = briefing_mtime >= latest_source_mtime

    # Structural marker check (always run — timestamp alone is not enough)
    missing_markers = _check_structural_markers(OUTPUT_FILE)
    is_structurally_valid = len(missing_markers) == 0

    # Both must pass
    if is_fresh and is_structurally_valid:
        print(f"PASS: briefing is fresh (briefing {_ts_display(briefing_mtime)} "
              f">= latest source {_ts_display(latest_source_mtime)})")
        return 0

    # If structurally invalid, that's a hard fail — can't trust the content
    if not is_structurally_valid:
        print(f"HARD FAIL: briefing missing required structural markers: "
              f"{', '.join(missing_markers)}", file=sys.stderr)
        print(f"HARD FAIL: briefing malformed — missing markers: "
              f"{', '.join(missing_markers)}")
        return 2

    # Stale but structurally valid — attempt regeneration
    assert is_structurally_valid and not is_fresh  # invariant

    latest_name = ""
    for s in sources:
        if os.path.getmtime(s) == latest_source_mtime:
            latest_name = os.path.basename(s)
            break

    print(f"STALE: briefing {_ts_display(briefing_mtime)} is older than "
          f"source {_ts_display(latest_source_mtime)} ({latest_name})",
          file=sys.stderr)
    print("[verifier] regenerating...", file=sys.stderr)

    if not _regenerate():
        print("STALE: briefing remains stale — regeneration failed")
        return 1

    # ── Post-regeneration: re-run FULL validation ──
    if not os.path.isfile(OUTPUT_FILE):
        print("STALE: briefing still missing after regeneration")
        return 1

    new_briefing_mtime = os.path.getmtime(OUTPUT_FILE)
    new_is_fresh = new_briefing_mtime >= latest_source_mtime
    new_missing_markers = _check_structural_markers(OUTPUT_FILE)
    new_is_valid = len(new_missing_markers) == 0

    if new_is_fresh and new_is_valid:
        print(f"PASS: briefing regenerated and now fresh "
              f"(briefing {_ts_display(new_briefing_mtime)} "
              f">= latest source {_ts_display(latest_source_mtime)})")
        return 0

    if not new_is_valid:
        print(f"HARD FAIL: regenerated briefing missing structural markers: "
              f"{', '.join(new_missing_markers)}", file=sys.stderr)
        print(f"HARD FAIL: regenerated briefing malformed — missing markers: "
              f"{', '.join(new_missing_markers)}")
        return 2

    # Still stale after regeneration
    print("STALE: briefing remains stale after regeneration")
    return 1


if __name__ == "__main__":
    sys.exit(main())
