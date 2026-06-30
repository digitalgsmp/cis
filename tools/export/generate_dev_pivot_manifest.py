#!/usr/bin/env python3
"""
generate_dev_pivot_manifest.py — Tier 5.6
Reads dev_pivot_status from SQLite spine.
Writes docs/DEV-PIVOT_STATUS.md — a categorized manifest for agents and external advisors.

Usage: python3 tools/export/generate_dev_pivot_manifest.py [--db PATH] [--out PATH] [--run-id ID]
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data" / "cis_memory.db"
DEFAULT_OUT = REPO_ROOT / "docs" / "DEV-PIVOT_STATUS.md"


def query_dev_pivot(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM dev_pivot_status ORDER BY doc_id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def render(rows, run_id=None):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rid = run_id or "manual"

    lines = [
        "# DEV-PIVOT Status Report",
        f"Generated: {now} | Run: {rid}",
        "Source: SQLite spine (dev_pivot_status table)",
        "DO NOT MANUALLY EDIT — regenerate with tools/export/generate_dev_pivot_manifest.py",
        "",
        "Each DEV-PIVOT document represents a problem important enough to spec.",
        "INVALIDATED = progress solved it. LIVE = problem still unsolved.",
        "",
        "---",
        "",
    ]

    categories = {
        "INVALIDATED": [],
        "PARTIALLY_INVALIDATED": [],
        "LIVE": [],
    }

    for r in rows:
        status = r["status"]
        if status in categories:
            categories[status].append(r)

    # ── INVALIDATED ──
    lines.append("## INVALIDATED — Capability progress made these obsolete")
    lines.append("")
    for r in categories["INVALIDATED"]:
        lines.append(f"### {r['doc_id']}: {r['title']}")
        lines.append(f"**Invalidated by:** `{r['invalidated_by'] or 'time_passed'}`")
        lines.append(f"**Reason:** {r['invalidation_reason']}")
        if r.get("affected_sections"):
            lines.append(f"**Affected sections:** {r['affected_sections']}")
        lines.append("")

    # ── PARTIALLY INVALIDATED ──
    lines.append("## PARTIALLY INVALIDATED — Assumptions changed under them")
    lines.append("")
    for r in categories["PARTIALLY_INVALIDATED"]:
        lines.append(f"### {r['doc_id']}: {r['title']}")
        lines.append(f"**Changed by:** `{r['invalidated_by'] or 'unknown'}`")
        lines.append(f"**What changed:** {r['invalidation_reason']}")
        if r.get("capability_gap"):
            lines.append(f"**Remaining gap:** {r['capability_gap']}")
        if r.get("affected_sections"):
            lines.append(f"**Affected sections:** {r['affected_sections']}")
        lines.append("")

    # ── LIVE (by category) ──
    lines.append("## STILL LIVE — Unsolved problems ({} docs)".format(len(categories["LIVE"])))
    lines.append("")

    # Group by category
    by_cat = {}
    for r in categories["LIVE"]:
        cat = r["category"]
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(r)

    cat_labels = {
        "governance": "Governance",
        "enforcement": "Enforcement",
        "architecture": "Architecture & Direction",
        "pipeline": "Pipeline",
        "data": "Data & Cataloging",
        "operations": "Operations",
    }

    for cat_key in ["governance", "enforcement", "architecture", "pipeline", "data", "operations"]:
        items = by_cat.get(cat_key, [])
        if not items:
            continue
        lines.append(f"### {cat_labels[cat_key]}")
        lines.append("")
        for r in items:
            dep = r.get("depends_on")
            gap = r.get("capability_gap")
            lines.append(f"- **{r['doc_id']}**: {r['title']}")
            if dep:
                lines.append(f"  - Depends on: `{dep}`")
            if gap:
                lines.append(f"  - Gap: {gap}")
        lines.append("")

    # ── Summary ──
    lines.append("---")
    lines.append("")
    total = len(rows)
    invalidated = len(categories["INVALIDATED"])
    partial = len(categories["PARTIALLY_INVALIDATED"])
    live = len(categories["LIVE"])
    lines.append(f"**Summary:** {invalidated} invalidated, {partial} partially invalidated, {live} live — {total} total")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate DEV-PIVOT status manifest from spine")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--run-id", default=None, help="Pipeline run ID for stamp")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"ERROR: DB not found: {args.db}", file=sys.stderr)
        sys.exit(2)

    rows = query_dev_pivot(args.db)
    if not rows:
        print("WARNING: dev_pivot_status table is empty. Run seed first.", file=sys.stderr)

    output = render(rows, run_id=args.run_id)
    Path(args.out).write_text(output)
    print(f"PASS: DEV-PIVOT manifest written to {args.out} ({len(output)} chars, {len(rows)} docs)")


if __name__ == "__main__":
    main()
