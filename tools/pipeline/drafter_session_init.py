#!/usr/bin/env python3
"""
drafter_session_init.py — Tier 11C: Produce spine-derived briefing for the Drafter.
ADR-SEED-014 Clause 3.

Read-only. Queries spine + git state for workflow_run_id. Produces structured
briefing to stdout so the Drafter knows what to draft.

Usage:
  python3 tools/pipeline/drafter_session_init.py --run-id <workflow_run_id>
  python3 tools/pipeline/drafter_session_init.py --run-id <id> --brief
"""

import argparse
import os
import sqlite3
import subprocess
import sys


DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
REPO_ROOT = "/mnt/projects/cis"


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def git_head():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def git_status_porcelain():
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def resolve_proposal_id(run_id, db):
    row = db.execute(
        """SELECT DISTINCT proposal_id FROM lifecycle_events
           WHERE workflow_run_id = ? ORDER BY id DESC LIMIT 1""",
        (run_id,)
    ).fetchone()
    return row["proposal_id"] if row else None


def get_current_lifecycle_state(proposal_id):
    """Call get_current_state from orchestration module."""
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import get_current_state
    db2 = sqlite3.connect(DB_PATH)
    db2.row_factory = sqlite3.Row
    state = get_current_state(proposal_id, db2)
    db2.close()
    return state


def brief_mode(run_id, proposal_id, topic, state, pending_count, blocker_count, dirty):
    print(f"Run: {run_id} | State: {state} | Intent: {topic[:120]}{'...' if len(topic)>120 else ''}")
    print(f"Pending tiers: {pending_count} | Blockers: {blocker_count} | Git: {'dirty' if dirty else 'clean'}")


def full_briefing(run_id, proposal_id, run, head, state, lifecycle_trail,
                  pending, completed, blockers, decisions, questions, dirty_files):
    print("═══ Drafter Session Briefing ═══")
    print(f"Workflow Run: {run_id}")
    print(f"Proposal: {proposal_id}")
    print(f"Git HEAD: {head}")
    print()

    print("─── Eric's Intent ───")
    print(run["topic"])
    print()

    print("─── Current Lifecycle State ───")
    print(state)
    print()

    print("─── Lifecycle Trail ───")
    for ev in lifecycle_trail:
        print(f"  {ev['from_state']} → {ev['to_state']} ({ev['timestamp']}) by {ev['initiated_by']}")
    print()

    print("─── Build Tier Status ───")
    if pending:
        print("Pending:")
        for p in pending:
            print(f"  {p['node_label']} (tier {p['tier']}) — {p['status']}")
    else:
        print("Pending: None")
    if completed:
        print("Recently completed:")
        for c in completed:
            print(f"  {c['node_label']} (tier {c['tier']}) — {c['completed_at']}")
    print()

    print("─── Active Blockers ───")
    if blockers:
        for b in blockers:
            print(f"  {b['id']}: {b['description']}")
    else:
        print("  None")
    print()

    print("─── Active Decisions ───")
    if decisions:
        for d in decisions:
            label = d["label"] or ""
            decision_text = (d["decision"] or "")[:120]
            print(f"  {d['id']}: {label} — {decision_text}{'...' if len(d['decision'] or '') > 120 else ''}")
    else:
        print("  None")
    print()

    print("─── Open Questions ───")
    if questions:
        for q in questions:
            print(f"  {q['id']}: {q['question'][:200]}")
    else:
        print("  None")
    print()

    print("─── Git State ───")
    if dirty_files:
        print("Dirty/untracked files:")
        for f in dirty_files:
            print(f"  {f}")
    else:
        print("Clean")


def main():
    parser = argparse.ArgumentParser(
        description="CIS Tier 11C — Drafter session briefing"
    )
    parser.add_argument("--run-id", required=True, help="Workflow run ID")
    parser.add_argument("--brief", action="store_true", help="Condensed briefing")
    args = parser.parse_args()

    run_id = args.run_id
    db = get_db()

    # Load workflow_run
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
    if run is None:
        print(f"ERROR: Workflow run not found: {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)
    if not run["topic"]:
        print(f"ERROR: Workflow run has empty topic: {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    proposal_id = resolve_proposal_id(run_id, db)
    if not proposal_id:
        print(f"ERROR: No proposal_id found for run {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    # Spine context
    pending = db.execute(
        "SELECT node_label, tier, status FROM build_plan_nodes "
        "WHERE status = 'PENDING' ORDER BY sequence LIMIT 5"
    ).fetchall()

    completed = db.execute(
        "SELECT node_label, tier, completed_at FROM build_plan_nodes "
        "WHERE status = 'COMPLETE' ORDER BY completed_at DESC LIMIT 3"
    ).fetchall()

    blockers = db.execute(
        "SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'"
    ).fetchall()

    decisions = db.execute(
        "SELECT id, label, decision FROM project_decisions "
        "WHERE status = 'DECIDED' AND id LIKE 'ADR-SEED-%' "
        "ORDER BY decided_at DESC"
    ).fetchall()

    questions = db.execute(
        "SELECT id, question FROM open_questions WHERE status = 'OPEN'"
    ).fetchall()

    lifecycle_trail = db.execute(
        "SELECT from_state, to_state, timestamp, initiated_by FROM lifecycle_events "
        "WHERE workflow_run_id = ? ORDER BY id ASC",
        (run_id,)
    ).fetchall()

    db.close()

    # Git state
    head = git_head()
    porcelain = git_status_porcelain()
    dirty_files = porcelain.strip().split("\n") if porcelain.strip() else []
    is_dirty = bool(dirty_files and dirty_files[0])

    # Git warning (stderr)
    if is_dirty:
        print("WARNING: Git working tree is not clean.", file=sys.stderr)
        for f in dirty_files:
            print(f"  {f}", file=sys.stderr)

    # Lifecycle state
    state = get_current_lifecycle_state(proposal_id)

    if args.brief:
        brief_mode(run_id, proposal_id, run["topic"], state,
                   len(pending), len(blockers), is_dirty)
    else:
        full_briefing(run_id, proposal_id, run, head, state,
                      lifecycle_trail, pending, completed,
                      blockers, decisions, questions, dirty_files)


if __name__ == "__main__":
    main()
