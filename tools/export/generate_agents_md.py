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

    # Section 6 — Next Actions: authoritative source is build_plan_nodes
    actions = conn.execute(
        """SELECT node_label AS id, tier, node_label AS description, status
           FROM build_plan_nodes
           WHERE project_id='CIS' AND status IN ('PENDING','IN_PROGRESS')
           ORDER BY sequence"""
    ).fetchall()

    # Section 7 — Active Blockers: authoritative source is BLOCKED build_plan_nodes,
    # supplemented by ACTIVE infrastructure blockers from active_blockers
    bp_blockers = conn.execute(
        """SELECT node_label AS id, blocked_reason AS description, 'BLOCKED' AS status
           FROM build_plan_nodes
           WHERE project_id='CIS' AND status='BLOCKED'
           ORDER BY sequence"""
    ).fetchall()
    ab_blockers = conn.execute(
        """SELECT id, description, status
           FROM active_blockers
           WHERE status='ACTIVE' AND id LIKE 'BLK-SEED-%'
           ORDER BY created_at DESC"""
    ).fetchall()
    blockers = list(bp_blockers) + list(ab_blockers)

    state_rows = conn.execute(
        """SELECT key, value FROM project_state
           WHERE superseded_at IS NULL
           AND id = (
               SELECT MAX(id) FROM project_state ps2
               WHERE ps2.key = project_state.key AND ps2.superseded_at IS NULL
           )"""
    ).fetchall()
    build_state = {row["key"]: row["value"] for row in state_rows}

    # Eric Gate approval status
    eric_gate = conn.execute(
        """SELECT ega.decision, ega.decided_at, ega.goal_reference_id,
                  ega.workflow_run_id, gr.goal_label
           FROM eric_gate_approvals ega
           LEFT JOIN goal_references gr ON ega.goal_reference_id = gr.id
           WHERE ega.is_current = 1
           ORDER BY ega.decided_at DESC
           LIMIT 1"""
    ).fetchone()

    conn.close()
    return runs, decisions, questions, actions, blockers, build_state, eric_gate


def render(static, runs, decisions, questions, actions, blockers, build_state,
           eric_gate=None, run_id=None):
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
    build_phase = build_state.get("build_phase", "(unknown — project_state table missing)")
    lines.append(build_phase)
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

    lines.append("## 9. Eric Gate Status")
    if eric_gate:
        decision = eric_gate["decision"] or "UNKNOWN"
        decided = eric_gate["decided_at"] or "Not yet decided"
        goal = eric_gate["goal_label"] or "No goal label"
        run_id_eg = eric_gate["workflow_run_id"] or "N/A"
        lines.append(f"- Workflow run: {run_id_eg}")
        lines.append(f"- Status: {decision}")
        lines.append(f"- Decided at: {decided}")
        lines.append(f"- Goal: {goal}")
    else:
        eg_static = static.get("eric_gate_status", {})
        if eg_static and eg_static.get("decision"):
            decision = eg_static.get("decision", "UNKNOWN")
            decided = eg_static.get("decided_at", "Not yet decided")
            goal = eg_static.get("goal_label", "No goal label")
            run_id_eg = eg_static.get("workflow_run_id", "N/A")
            scope = eg_static.get("scope", "").strip()
            lines.append(f"- Workflow run: {run_id_eg}")
            lines.append(f"- Status: {decision}")
            lines.append(f"- Decided at: {decided}")
            lines.append(f"- Goal: {goal}")
            if scope:
                lines.append(f"- Scope: {scope}")
        else:
            lines.append("- No Eric Gate decision recorded (pending)")
    lines.append("")

    lines.append("## 10. Verification Hardening Rule")
    lines.append(static.get("verification_hardening_rule", "").strip())
    lines.append("")

    lines.append("## 11. Role Identity Rule")
    lines.append(static.get("role_identity_rule", "").strip())
    lines.append("")

    startup = static.get("startup_protocol", "").strip()
    if startup:
        lines.append("## 11.5. READ_ONLY_STANDING_BY Startup Protocol")
        lines.append(startup)
        lines.append("")

    lines.append("## 12. Seed Intent — Eric's Own Words")
    si = static.get("seed_intent", {})
    lines.append(si.get("instruction", ""))
    lines.append("")
    for excerpt in si.get("excerpts", []):
        lines.append(f"Source: {excerpt['source']}")
        for line in excerpt["text"].strip().splitlines():
            lines.append(f"> {line}")
        lines.append("")

    lines.append("## 13. Evidence-Backed Response Rule")
    lines.append(static.get("evidence_rule", "").strip())
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
    runs, decisions, questions, actions, blockers, build_state, eric_gate = \
        query_spine(args.db)
    output = render(static, runs, decisions, questions, actions, blockers,
                    build_state, eric_gate=eric_gate, run_id=args.run_id)

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
