#!/usr/bin/env python3
"""
generate_agents_md.py — Tier 5.1
Reads SQLite spine + config/agents_static.yaml.
Writes /mnt/projects/cis/AGENTS.md.
Output must stay under 20,000 characters.

Usage: python3 tools/export/generate_agents_md.py [--db PATH] [--config PATH] [--out PATH] [--run-id ID] [--dry-run]
"""

import argparse
import sqlite3
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data" / "cis_memory.db"
DEFAULT_CONFIG = REPO_ROOT / "config" / "agents_static.yaml"
DEFAULT_OUT = REPO_ROOT / "AGENTS.md"
CHAR_LIMIT = 20000


def load_static(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)


def query_spine(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    runs = conn.execute(
        "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    decisions = conn.execute(
        """SELECT * FROM project_decisions
           WHERE status != 'SUPERSEDED' AND id LIKE 'ADR-SEED-%'
           ORDER BY decided_at DESC"""
    ).fetchall()

    questions = conn.execute(
        """SELECT * FROM open_questions
           WHERE status = 'OPEN' AND id LIKE 'OQ-SEED-%'
           ORDER BY opened_at DESC"""
    ).fetchall()

    actions = conn.execute(
        """SELECT * FROM next_actions
           WHERE status IN ('PENDING','IN_PROGRESS') AND id LIKE 'NA-SEED-%'
           ORDER BY tier, id"""
    ).fetchall()

    blockers = conn.execute(
        """SELECT * FROM active_blockers
           WHERE status = 'ACTIVE' AND id LIKE 'BLK-SEED-%'
           ORDER BY created_at DESC"""
    ).fetchall()

    conn.close()
    return runs, decisions, questions, actions, blockers


def render(static, runs, decisions, questions, actions, blockers, run_id=None):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    latest_run_id = runs[0]["id"] if runs else "none"
    rid = run_id or "none"

    lines = []
    lines.append("# CIS — AGENTS.md")
    lines.append(f"Generated: {now} | Run: {rid} | Latest pipeline: {latest_run_id}")
    lines.append("Source: SQLite spine + config/agents_static.yaml")
    lines.append("DO NOT MANUALLY EDIT — regenerate with tools/export/generate_agents_md.py")
    lines.append("")

    lines.append("## 1. Current Build Phase")
    lines.append("Tier 4.4 COMPLETE. Tier 5 Context Export Pipeline — IN PROGRESS.")
    lines.append("Build order authority: docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md")
    lines.append("")

    lines.append("## 2. Do Not Start")
    for item in static.get("do_not_start", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## 3. Active Architecture")
    lines.append("")
    lines.append("### Infrastructure")
    for k, v in static.get("infrastructure", {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("### Gateways")
    lines.append("| Label | Profile | Port | Model | Reasoning | NeMo | Status |")
    lines.append("|-------|---------|------|-------|-----------|------|--------|")
    for gw in static.get("gateways", []):
        nemo = "Yes" if gw.get("nemo") else "No"
        lines.append(
            f"| {gw['label']} | {gw['profile']} | {gw['port']} "
            f"| {gw['model']} | {gw['reasoning']} | {nemo} | {gw['status']} |"
        )
    lines.append("")
    lines.append("### Hermes Source Patches")
    patches = static.get("hermes_patches", {})
    base = patches.get("base_path", "")
    for p in patches.get("patches", []):
        loc = f":{p['line']}" if p.get("line") else ""
        lines.append(f"- {base}{p['file']}{loc} — {p['description']}")
    lines.append("")

    lines.append("## 4. Active Decisions")
    for d in decisions:
        lines.append(f"- [{d['id']}] {d['label']}: {d['decision']}")
    lines.append("")

    lines.append("## 5. Open Questions")
    for q in questions:
        lines.append(f"- [{q['id']}] {q['question']}")
    lines.append("")

    lines.append("## 6. Next Actions")
    for a in actions:
        tier = f"Tier {a['tier']}" if a["tier"] else "—"
        lines.append(f"- [{a['id']}] ({tier}) {a['description']}")
    lines.append("")

    lines.append("## 7. Active Blockers")
    for b in blockers:
        lines.append(f"- [{b['id']}] {b['description']}")
    lines.append("")

    lines.append("## 8. Recent Pipeline Runs (last 5)")
    if runs:
        for r in runs:
            lines.append(
                f"- [{r['id']}] {r['topic'][:80]} — {r['result']} "
                f"({r['rounds_completed']} rounds, {r['completed_at'] or 'incomplete'})"
            )
    else:
        lines.append("- No completed runs yet.")
    lines.append("")

    lines.append("## 9. Verification Hardening Rule")
    lines.append(static.get("verification_hardening_rule", "").strip())
    lines.append("")

    lines.append("## 10. Role Identity Rule")
    lines.append(static.get("role_identity_rule", "").strip())
    lines.append("")

    lines.append("## 11. Seed Intent — Eric's Own Words")
    si = static.get("seed_intent", {})
    lines.append(si.get("instruction", ""))
    lines.append("")
    for excerpt in si.get("excerpts", []):
        lines.append(f"Source: {excerpt['source']}")
        for line in excerpt["text"].strip().splitlines():
            lines.append(f"> {line}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate AGENTS.md from spine")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output instead of writing file")
    parser.add_argument("--run-id", default=None, help="Pipeline run ID for stamp")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"ERROR: DB not found: {args.db}")
        sys.exit(2)
    if not Path(args.config).exists():
        print(f"ERROR: Config not found: {args.config}")
        sys.exit(2)

    static = load_static(args.config)
    runs, decisions, questions, actions, blockers = query_spine(args.db)
    output = render(static, runs, decisions, questions, actions, blockers, run_id=args.run_id)

    char_count = len(output)
    if char_count > CHAR_LIMIT:
        print(f"ERROR: Output is {char_count} chars, exceeds {CHAR_LIMIT} limit.")
        sys.exit(1)

    if args.dry_run:
        print(output)
        print(f"\n--- {char_count} chars (limit {CHAR_LIMIT}) ---")
        sys.exit(0)

    Path(args.out).write_text(output)
    print(f"PASS: AGENTS.md written to {args.out} ({char_count} chars)")


if __name__ == "__main__":
    main()
