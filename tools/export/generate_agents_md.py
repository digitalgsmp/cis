#!/usr/bin/env python3
"""
generate_agents_md.py — Tier 5.1
Reads SQLite spine + config/agents_static.yaml.
Writes /mnt/projects/cis/AGENTS.md.
Output must stay under 20,000 characters; every run reports the size it
produced, that limit and the margin between them (WB1-D18).

Usage: python3 tools/export/generate_agents_md.py [--db PATH] [--config PATH] [--out PATH] [--run-id ID] [--dry-run]
"""

import argparse
import re
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

# ── size observability (WB1-D18) ───────────────────────────────────────────
#
# CHAR_LIMIT above is a hard, fail-closed guard and stays one. What WB1-D18
# recorded was not a defect in the guard but the absence of any warning
# before it fires: section 1 of this projection is nothing but the two spine
# values project_state.build_phase and current_direction, a correction to
# them is routinely longer than the prose it replaces, and the first visible
# symptom of crossing 20,000 characters was a seeding assertion failing in
# an apparently unrelated test suite rather than "your state text is too
# long".
#
# So: every successful generation now states size, limit and remaining
# margin; a generation that is under the limit but close to it says so; and
# a generation over the limit still writes nothing and now names both the
# overage and the sections that account for it. None of this changes what
# is generated — the numbers are read off the finished projection, never fed
# back into it, so authoritative content is never shortened to satisfy the
# guard.

# Margin at or below which a successful generation also warns. Advisory
# only: nothing fails under CHAR_LIMIT, and raising CHAR_LIMIT is not the
# response to either signal — shortening the two spine values is.
MARGIN_WARN_CHARS = 1500

SECTION_HEADING_RE = re.compile(r"^## .*$", re.MULTILINE)


def section_sizes(output):
    """Characters attributable to each '## ' section of `output`, largest
    first. A pure function of the rendered text — the same projection always
    yields the same breakdown — so it can be reported without making
    generation any less deterministic."""
    starts = [m.start() for m in SECTION_HEADING_RE.finditer(output)]
    sizes = []
    if starts:
        sizes.append(("(file header)", starts[0]))
    for start, end in zip(starts, starts[1:] + [len(output)]):
        heading = output[start:end].split("\n", 1)[0][len("## "):].strip()
        sizes.append((heading, end - start))
    return sorted(sizes, key=lambda item: -item[1])


def size_report(output):
    """Size, limit and remaining margin for a rendered projection, plus the
    per-section breakdown. `char_margin` is negative exactly when the hard
    guard must refuse the write."""
    char_count = len(output)
    return {
        "char_count": char_count,
        "char_limit": CHAR_LIMIT,
        "char_margin": CHAR_LIMIT - char_count,
        "sections": section_sizes(output),
    }


def format_sections(sections, top=3):
    return "; ".join(f"{name} {count} chars" for name, count in sections[:top])


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
           WHERE project_id='cis' AND status IN ('PENDING','IN_PROGRESS')
           ORDER BY sequence"""
    ).fetchall()

    # Fallback: if no PENDING/IN_PROGRESS build nodes, pull from next_actions
    if not actions:
        actions = conn.execute(
            """SELECT id, tier, description, status
               FROM next_actions
               WHERE status IN ('PENDING','IN_PROGRESS')
               ORDER BY created_at"""
        ).fetchall()

    # Section 7 — Active Blockers: authoritative source is BLOCKED build_plan_nodes,
    # supplemented by ACTIVE infrastructure blockers from active_blockers
    bp_blockers = conn.execute(
        """SELECT node_label AS id, blocked_reason AS description, 'BLOCKED' AS status
           FROM build_plan_nodes
           WHERE project_id='cis' AND status='BLOCKED'
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

    # Session handoff — latest active handoff from spine
    handoff = conn.execute(
        """SELECT date, title, summary, decisions, next_actions,
                  claude_context, eric_feedback, gateway_status, git_head
           FROM session_handoffs
           WHERE is_current = 1
           ORDER BY created_at DESC
           LIMIT 1"""
    ).fetchone()

    conn.close()
    return runs, decisions, questions, actions, blockers, build_state, eric_gate, handoff


def render(static, runs, decisions, questions, actions, blockers, build_state,
           eric_gate=None, handoff=None, run_id=None):
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
    direction = build_state.get("current_direction", "")
    if direction:
        lines.append(f"Direction: {direction}")
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
    lines.append(
        "Full text/reasoning of any decision: `project_decisions` table in "
        "the spine DB — `sqlite3 data/cis_memory.db \"SELECT * FROM "
        "project_decisions WHERE id='<ID>'\"`. This table is the canonical "
        "source; the list below is an index, not a summary."
    )
    for d in decisions:
        lines.append(f"- [{d['id']}] {d['label']}")
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

    advisor = static.get("external_advisor_role", "").strip()
    if advisor:
        lines.append("## 11.6. External Advisor Role")
        lines.append(advisor)
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

    lines.append("## 13. Session Handoff (from spine)")
    if handoff:
        lines.append(f"**{handoff['title']}** — {handoff['date']}")
        lines.append(f"Git HEAD: `{handoff['git_head']}`")
        lines.append("")
        lines.append(f"**Built:** {handoff['summary']}")
        if handoff['decisions']:
            lines.append(f"**Decisions:** {handoff['decisions']}")
        if handoff['eric_feedback']:
            lines.append(f"**Eric:** {handoff['eric_feedback']}")
        if handoff['gateway_status']:
            lines.append(f"**Gateway:** {handoff['gateway_status']}")
        if handoff['next_actions']:
            lines.append(f"**Next:** {handoff['next_actions']}")
        if handoff['claude_context']:
            lines.append(f"**Claude context:** {handoff['claude_context']}")
    else:
        lines.append("- No session handoff recorded (session_handoffs table empty)")
    lines.append("")

    lines.append("## 14. Evidence-Backed Response Rule")
    lines.append(static.get("evidence_rule", "").strip())
    lines.append("")

    dev_phase = static.get("development_phase_rule", "").strip()
    if dev_phase:
        lines.append("## 15. Development Phase Rule — Functionality First, "
                     "Refactor Deliberately")
        lines.append(dev_phase)
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
    runs, decisions, questions, actions, blockers, build_state, eric_gate, handoff = \
        query_spine(args.db)
    output = render(static, runs, decisions, questions, actions, blockers,
                    build_state, eric_gate=eric_gate, handoff=handoff,
                    run_id=args.run_id)

    report = size_report(output)
    char_count = report["char_count"]
    margin = report["char_margin"]
    sections = format_sections(report["sections"])

    if margin < 0:
        print(f"ERROR: Output is {char_count} chars, exceeds {CHAR_LIMIT} limit "
              f"by {-margin} chars. Nothing was written to {args.out}.")
        print(f"ERROR: largest sections: {sections}.")
        print("ERROR: section '1. Current Build Phase' is exactly "
              "project_state.build_phase + current_direction. Shorten those "
              "two spine values — do not raise the limit and do not truncate "
              "authoritative state.")
        sys.exit(1)

    if args.dry_run:
        print(output)
        print(f"\n--- {char_count} chars (limit {CHAR_LIMIT}, "
              f"margin {margin} chars) ---")
        sys.exit(0)

    Path(args.out).write_text(output)
    if margin <= MARGIN_WARN_CHARS:
        print(f"WARN: only {margin} chars of margin remain under the "
              f"{CHAR_LIMIT} limit. Largest sections: {sections}.")
    print(f"PASS: AGENTS.md written to {args.out} ({char_count} chars, "
          f"limit {CHAR_LIMIT}, margin {margin} chars)")


if __name__ == "__main__":
    main()
