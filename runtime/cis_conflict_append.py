#!/usr/bin/env python3
"""
cis_conflict_append.py — Append a conflict entry to CIS_CONFLICT_REGISTER.md

Usage:
    python3 cis_conflict_append.py \
        --title "Short conflict title" \
        --severity "HIGH|MEDIUM|LOW" \
        --category "Filesystem|Naming|Governance|Documentation|Runtime|Schema" \
        --conflict "What the conflict is" \
        --risk "What breaks if unresolved" \
        --observed "Where/when it was found" \
        --action "Immediate action taken or required" \
        --resolution "What ADR or step resolves it" \
        --notes "Optional additional notes"

All fields except --notes are required.
"""

import argparse
from pathlib import Path
from datetime import datetime

REGISTER_PATH = Path("/mnt/projects/cis/docs/CIS_CONFLICT_REGISTER.md")

HEADER = """# CIS Conflict Register
# Updated automatically — do not edit header manually
# Canonical path: /mnt/projects/cis/docs/CIS_CONFLICT_REGISTER.md

Purpose:
Track discovered contradictions, filesystem conflicts, naming collisions,
stale documentation, deferred bugs, and governance/runtime mismatches.
Any conflict not resolved immediately must be entered before session close.

Status values:
  OPEN       — identified, not yet resolved
  DEFERRED   — acknowledged, resolution scheduled
  RESOLVED   — fix confirmed and verified
  SUPERSEDED — made irrelevant by other architectural change

---

"""

def ensure_register():
    REGISTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not REGISTER_PATH.exists():
        REGISTER_PATH.write_text(HEADER, encoding="utf-8")
        print(f"Created {REGISTER_PATH}")

def append_conflict(args):
    ensure_register()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    notes_block = f"\nNotes:\n{args.notes}\n" if args.notes else ""

    entry = f"""
## {timestamp} — {args.title}

Status:    OPEN
Severity:  {args.severity}
Category:  {args.category}

Conflict:
{args.conflict}

Risk:
{args.risk}

Observed During:
{args.observed}

Immediate Action:
{args.action}

Required Resolution:
{args.resolution}
{notes_block}
---
"""

    with REGISTER_PATH.open("a", encoding="utf-8") as f:
        f.write(entry)

    print(f"PASS — Conflict appended to {REGISTER_PATH}")
    print(f"Title: {args.title}")
    print(f"Severity: {args.severity}")

def main():
    parser = argparse.ArgumentParser(description="Append a conflict to CIS_CONFLICT_REGISTER.md")
    parser.add_argument("--title",      required=True)
    parser.add_argument("--severity",   required=True, choices=["HIGH", "MEDIUM", "LOW"])
    parser.add_argument("--category",   required=True)
    parser.add_argument("--conflict",   required=True)
    parser.add_argument("--risk",       required=True)
    parser.add_argument("--observed",   required=True)
    parser.add_argument("--action",     required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--notes",      default="")
    args = parser.parse_args()
    append_conflict(args)

if __name__ == "__main__":
    main()
