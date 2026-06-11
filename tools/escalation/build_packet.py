#!/usr/bin/env python3
"""
build_packet.py — Deterministic Escalation Packet Builder
Component 2: Escalation Advisor Integration Protocol

Assembles P0-P3 and P6 from spine + git queries.
Accepts P4/P5 content from file or stdin.
Fails loudly (non-zero exit) if project_state is absent or any mandatory
section is missing. Computes SHA256 over P1-P6. Writes escalation + packet
rows to the spine. Prints full packet to stdout for Eric to copy.

Usage:
    build_packet.py --trigger-class DISCRETIONARY|MANDATORY \
        --trigger-reason "..." --scope "..." \
        --target CLAUDE|CHATGPT|BOTH \
        --response-type AUDIT|PROPOSAL_REVIEW|RISK_ASSESSMENT|DESIGN_INPUT \
        [--workflow-run-id RUN_ID] \
        [--p4-file FILE] [--p5-file FILE] \
        [--db PATH]
"""

import sys
import hashlib
import subprocess
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

# Add parent dir for database import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "runtime"))
from db.database import (
    init_db, get_project_state, insert_advisor_escalation,
    insert_escalation_packet, update_escalation_status,
    ALLOWED_TRIGGER_CLASSES, ALLOWED_ADVISOR_TARGETS,
    ALLOWED_RESPONSE_TYPES,
)

DEFAULT_DB = "/mnt/projects/cis/data/cis_memory.db"
PROJECT_ROOT = "/mnt/projects/cis"

SECTION_HEADERS = ["P0 — Header", "P1 — Project position", "P2 — Spine state excerpt",
                   "P3 — Provenance and lifecycle records", "P4 — The exact question",
                   "P5 — Constraints and authority limits", "P6 — Evidence appendix"]


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def get_git_head():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=5)
        if result.returncode != 0:
            fail(f"git rev-parse HEAD failed: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        fail(f"git command failed: {e}")


def build_p0(escalation_id, packet_version, workflow_run_id, advisor_target,
             trigger_class, trigger_reason, packet_hash):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    git_head = get_git_head()
    lines = [
        "P0 — Header",
        "=" * 60,
        f"escalation_id: {escalation_id}",
        f"packet_version: {packet_version}",
        f"date: {now}",
        f"git_head: {git_head}",
        f"workflow_run_id: {workflow_run_id or '(none — phase-level question)'}",
        f"advisor_target: {advisor_target}",
        f"trigger_class: {trigger_class}",
        f"trigger_reason: {trigger_reason}",
        f"packet_hash: {packet_hash}",
        "",
    ]
    return "\n".join(lines), git_head


def build_p1(conn):
    state = get_project_state(conn)
    if not state:
        fail("project_state is absent from the spine — cannot build P1")
    build_phase = state.get("build_phase", "unknown")
    completed_tier = state.get("completed_tier", "unknown")
    next_tier = state.get("next_tier", "unknown")
    next_action = state.get("next_action", "none")

    lines = [
        "P1 — Project position",
        "=" * 60,
        f"Current phase: {build_phase}",
        f"Completed tier: {completed_tier}",
        f"Next tier: {next_tier}",
        f"Next action: {next_action}",
        "",
    ]
    return "\n".join(lines)


def build_p2(conn, workflow_run_id):
    lines = [
        "P2 — Spine state excerpt",
        "=" * 60,
    ]
    if workflow_run_id:
        row = conn.execute(
            "SELECT id, topic, result, status, created_at, completed_at FROM workflow_runs WHERE id = ?",
            (workflow_run_id,),
        ).fetchone()
        if row:
            lines.append(f"Workflow run: {row[0]} | topic: {row[1]} | result: {row[2]} | status: {row[3]} | created: {row[4]}")
        else:
            lines.append(f"Workflow run: {workflow_run_id} (not found in spine)")
    else:
        lines.append("Workflow run: (none — phase-level question)")

    rounds = conn.execute(
        "SELECT round_number, reviewer_signal FROM deliberation_rounds WHERE run_id = ? ORDER BY round_number",
        (workflow_run_id,),
    ).fetchall() if workflow_run_id else []
    if rounds:
        lines.append("Deliberation rounds:")
        for rn, sig in rounds:
            lines.append(f"  Round {rn}: {sig}")
    else:
        lines.append("Deliberation rounds: none")

    blockers = conn.execute(
        "SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'"
    ).fetchall()
    if blockers:
        lines.append("Open active_blockers:")
        for bid, bdesc in blockers:
            lines.append(f"  {bid}: {bdesc[:120]}")
    else:
        lines.append("Open active_blockers: none")

    closeout = conn.execute(
        "SELECT id, end_head, completed_at FROM session_closeouts WHERE status = 'PASS' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if closeout:
        lines.append(f"Last verified closeout: id={closeout[0]} head={closeout[1]} at={closeout[2]}")
    else:
        lines.append("Last verified closeout: none")

    lines.append("")
    return "\n".join(lines)


def build_p3(conn, workflow_run_id):
    lines = [
        "P3 — Provenance and lifecycle records",
        "=" * 60,
    ]
    # goal_references
    goals = conn.execute(
        "SELECT goal_label, dependency_node, advancement_type FROM goal_references WHERE workflow_run_id = ?",
        (workflow_run_id,),
    ).fetchall() if workflow_run_id else []
    if goals:
        lines.append("Goal references:")
        for gl, dn, at in goals:
            lines.append(f"  {gl} → {dn} ({at})")
    else:
        lines.append("Goal references: none")

    # decision_trails
    trails = conn.execute(
        "SELECT trail_sequence, problem_statement, proposed_action, consensus_signal FROM decision_trails WHERE workflow_run_id = ? ORDER BY trail_sequence",
        (workflow_run_id,),
    ).fetchall() if workflow_run_id else []
    if trails:
        lines.append("Decision trails:")
        for ts, ps, pa, cs in trails:
            lines.append(f"  [{ts}] {ps[:100]} → {pa[:100]} ({cs})")
    else:
        lines.append("Decision trails: none")

    # drift_indicators (open, relevant)
    drift = conn.execute(
        "SELECT id, indicator_type, description FROM drift_indicators WHERE status = 'RAISED'"
    ).fetchall()
    if drift:
        lines.append("Open drift indicators:")
        for did, it, desc in drift:
            lines.append(f"  {did}: {it} — {desc[:120]}")
    else:
        lines.append("Open drift indicators: none")

    # rejection_rationale
    rejects = conn.execute(
        "SELECT rejected_option_label, rejection_reason FROM rejection_rationale WHERE workflow_run_id = ?",
        (workflow_run_id,),
    ).fetchall() if workflow_run_id else []
    if rejects:
        lines.append("Rejection rationale:")
        for rol, rr in rejects:
            lines.append(f"  {rol}: {rr}")
    else:
        lines.append("Rejection rationale: none")

    lines.append("")
    return "\n".join(lines)


def build_p6(workflow_run_id):
    lines = [
        "P6 — Evidence appendix",
        "=" * 60,
    ]
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-5"], capture_output=True, text=True,
            cwd=PROJECT_ROOT, timeout=5)
        if result.returncode == 0:
            lines.append("Recent commits:")
            lines.append(result.stdout.strip())
    except Exception:
        lines.append("(git log unavailable)")

    lines.append("")
    return "\n".join(lines)


def extract_sections(packet_text):
    """Extract P1-P6 section text from a packet. Returns dict P1..P6 -> text."""
    sections = {}
    current = None
    buf = []
    for line in packet_text.split("\n"):
        for i, hdr in enumerate(SECTION_HEADERS):
            if line.strip() == hdr:
                if current:
                    sections[current] = "\n".join(buf).strip()
                current = f"P{i}"
                buf = [line]
                break
        else:
            if current:
                buf.append(line)
    if current:
        sections[current] = "\n".join(buf).strip()
    return sections


def compute_packet_hash(p1_p6_text):
    """SHA256 over the concatenated P1-P6 text blocks."""
    return hashlib.sha256(p1_p6_text.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Build an escalation packet for Claude/ChatGPT advisor review"
    )
    parser.add_argument("--trigger-class", required=True,
                        choices=sorted(ALLOWED_TRIGGER_CLASSES))
    parser.add_argument("--trigger-reason", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--target", required=True,
                        choices=sorted(ALLOWED_ADVISOR_TARGETS))
    parser.add_argument("--response-type", required=True,
                        choices=sorted(ALLOWED_RESPONSE_TYPES))
    parser.add_argument("--workflow-run-id", default=None)
    parser.add_argument("--p4-file", default=None,
                        help="File containing P4 section text")
    parser.add_argument("--p5-file", default=None,
                        help="File containing P5 section text")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--escalation-id", type=int, default=None,
                        help="Existing escalation_id for new packet version")
    args = parser.parse_args()

    db_path = args.db
    if not Path(db_path).exists():
        fail(f"Database not found: {db_path}")

    conn = init_db(db_path)

    # P4 content
    if args.p4_file:
        p4_text = Path(args.p4_file).read_text().strip()
    else:
        p4_text = sys.stdin.read().strip()
        if len(sys.argv) > 1 and not sys.stdin.isatty():
            pass  # piped input
        else:
            print("Enter P4 — The exact question (end with Ctrl+D):", file=sys.stderr)
            p4_text = sys.stdin.read().strip()

    if not p4_text:
        fail("P4 content is empty")

    # P5 content (default or from file)
    default_p5 = textwrap.dedent("""\
    P5 — Constraints and authority limits
    ============================================================
    Advisor has review/consult authority only. No execution authority.
    Output is advisory input to Eric's reconciliation, not a directive.

    The Exact-Format Instruction Rule applies: use COMMAND + OUTPUT + FINAL format.
    Verification-Hardening and Evidence-Backed Response rules govern all claims.

    Scope fence: do not expand into Component 3 (Eric Gate redesign),
    Component 4 (Router expansion), or Tier 8 (API transport).
    """)
    if args.p5_file:
        p5_text = Path(args.p5_file).read_text().strip()
    else:
        p5_text = default_p5

    # Build escalation row first to get escalation_id
    escalation_id = args.escalation_id
    if escalation_id is None:
        escalation_id = insert_advisor_escalation(
            conn, trigger_class=args.trigger_class,
            trigger_reason=args.trigger_reason,
            escalation_scope=args.scope,
            workflow_run_id=args.workflow_run_id,
        )
        update_escalation_status(conn, escalation_id, "PACKET_BUILT")
    else:
        # Verify escalation exists
        esc = conn.execute(
            "SELECT id FROM advisor_escalations WHERE id = ?", (escalation_id,)
        ).fetchone()
        if esc is None:
            conn.close()
            fail(f"Escalation {escalation_id} not found")

    # Determine packet version
    cur = conn.execute(
        "SELECT COALESCE(MAX(packet_version), 0) FROM advisor_escalation_packets WHERE escalation_id = ?",
        (escalation_id,),
    )
    packet_version = cur.fetchone()[0] + 1

    # Build P0-P3 and P6 from spine + git
    p1_text = build_p1(conn)
    p2_text = build_p2(conn, args.workflow_run_id)
    p3_text = build_p3(conn, args.workflow_run_id)
    p6_text = build_p6(args.workflow_run_id)

    # Build full packet text with placeholder for hash
    # (hash computed over P1-P6 only, then inserted into P0)
    p1_p6_text = "\n\n".join([p1_text, p2_text, p3_text, p4_text, p5_text, p6_text])
    packet_hash = compute_packet_hash(p1_p6_text)

    p0_text, git_head = build_p0(
        escalation_id, packet_version, args.workflow_run_id,
        args.target, args.trigger_class, args.trigger_reason, packet_hash,
    )

    full_packet = "\n\n".join([p0_text, p1_text, p2_text, p3_text, p4_text, p5_text, p6_text])

    # Verify all mandatory sections present
    required = {f"P{i}" for i in range(7)}
    present = set(extract_sections(full_packet).keys())
    missing = required - present
    if missing:
        conn.close()
        fail(f"Missing mandatory sections: {sorted(missing)}")

    # Write packet row
    packet_id = insert_escalation_packet(
        conn, escalation_id=escalation_id,
        packet_version=packet_version,
        packet_raw=full_packet,
        packet_hash=packet_hash,
        git_head=git_head,
        advisor_target=args.target,
        requested_response_type=args.response_type,
        packet_status="PACKET_BUILT",
    )

    conn.commit()
    conn.close()

    # Print packet to stdout
    print(full_packet)
    print(f"\n--- Packet built: escalation_id={escalation_id} packet_id={packet_id} version={packet_version} ---",
          file=sys.stderr)


if __name__ == "__main__":
    import textwrap
    main()
