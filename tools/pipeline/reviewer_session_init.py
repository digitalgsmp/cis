#!/usr/bin/env python3
"""
reviewer_session_init.py — Tier 11D: Produce spine-derived briefing for the Reviewer.

ADR-SEED-014 Clause 6. Read-only. Queries spine + git state for workflow_run_id.
Produces structured briefing to stdout so the Reviewer knows what to review.

Usage:
  python3 tools/pipeline/reviewer_session_init.py --run-id <workflow_run_id>
  python3 tools/pipeline/reviewer_session_init.py --run-id <id> --brief
"""

import argparse
import os
import sqlite3
import subprocess
import sys


DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
REPO_ROOT = "/mnt/projects/cis"


def get_db():
    """Open CIS spine database with row factory."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def git_head():
    """Return current git HEAD SHA from repo root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def git_status_porcelain():
    """Return git status --porcelain output."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def resolve_proposal_id(run_id, db):
    """Resolve proposal_id from lifecycle_events for this workflow_run."""
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


def brief_mode(run_id, proposal_id, topic, state, dispatch_summary,
               pending_count, blocker_count, dirty):
    """Condensed briefing output."""
    print(f"Run: {run_id} | State: {state} | "
          f"Intent: {topic[:120]}{'...' if len(topic) > 120 else ''}")
    print(f"Proposal summary: {(dispatch_summary or '')[:200]}")
    print(f"Pending tiers: {pending_count} | Blockers: {blocker_count} | "
          f"Git: {'dirty' if dirty else 'clean'}")


def full_briefing(run_id, proposal_id, dispatch_id, dispatch_summary,
                  run, head, state, lifecycle_trail, deliberation_rounds,
                  pending, blockers, decisions, dirty_files):
    """Full briefing output."""
    print("═══ Reviewer Session Briefing ═══")
    print(f"Workflow Run: {run_id}")
    print(f"Proposal: {proposal_id}")
    print(f"Dispatch: {dispatch_id}")
    print(f"Git HEAD: {head}")
    print()

    print("─── Eric's Original Intent ───")
    print(run["topic"])
    print()

    print("─── Drafter Proposal Summary ───")
    print(dispatch_summary or "(no summary available)")
    print()

    print("─── Current Lifecycle State ───")
    print(state)
    print()

    print("─── Lifecycle Trail ───")
    for ev in lifecycle_trail:
        print(f"  {ev['from_state']} → {ev['to_state']} "
              f"({ev['timestamp']}) by {ev['initiated_by']}")
    print()

    print("─── Prior Deliberation Rounds ───")
    if deliberation_rounds:
        for dr in deliberation_rounds:
            signal = dr["reviewer_signal"] or "pending"
            print(f"  Round {dr['round_number']}: "
                  f"signal={signal} | "
                  f"drafter={dr['drafter_role']} | "
                  f"reviewer={dr['reviewer_role']} | "
                  f"created={dr['created_at']}")
    else:
        print("  None — initial review")
    print()

    print("─── Active Decisions ───")
    if decisions:
        for d in decisions:
            label = d["label"] or ""
            decision_text = (d["decision"] or "")[:120]
            print(f"  {d['id']}: {label} — {decision_text}"
                  f"{'...' if len(d['decision'] or '') > 120 else ''}")
    else:
        print("  None")
    print()

    print("─── Active Blockers ───")
    if blockers:
        for b in blockers:
            print(f"  {b['id']}: {b['description']}")
    else:
        print("  None")
    print()

    print("─── Build Tier Status ───")
    if pending:
        print("Pending:")
        for p in pending:
            print(f"  {p['node_label']} (tier {p['tier']}) — {p['status']}")
    else:
        print("Pending: None")
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
        description="CIS Tier 11D — Reviewer session briefing"
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

    proposal_id = resolve_proposal_id(run_id, db)
    if not proposal_id:
        print(f"ERROR: No proposal_id found for run {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    # Load the dispatch (IN_FLIGHT or PENDING)
    dispatch = db.execute(
        """SELECT * FROM dispatch_log
           WHERE workflow_run_id = ? AND current_status IN ('PENDING', 'IN_FLIGHT')
           ORDER BY timestamp_initiated DESC LIMIT 1""",
        (run_id,)
    ).fetchone()
    dispatch_id = dispatch["dispatch_id"] if dispatch else "N/A"
    dispatch_summary = dispatch["payload_summary"] if dispatch else None

    # Spine context queries
    pending_tiers = db.execute(
        "SELECT node_label, tier, status FROM build_plan_nodes "
        "WHERE status = 'PENDING' ORDER BY sequence LIMIT 5"
    ).fetchall()

    blockers = db.execute(
        "SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'"
    ).fetchall()

    decisions = db.execute(
        "SELECT id, label, decision FROM project_decisions "
        "WHERE status = 'DECIDED' ORDER BY decided_at DESC"
    ).fetchall()

    lifecycle_trail = db.execute(
        "SELECT from_state, to_state, timestamp, initiated_by, notes "
        "FROM lifecycle_events WHERE workflow_run_id = ? ORDER BY id ASC",
        (run_id,)
    ).fetchall()

    deliberation_rounds = db.execute(
        """SELECT round_number, drafter_role, reviewer_role,
                  reviewer_signal, created_at
           FROM deliberation_rounds WHERE run_id = ? ORDER BY round_number ASC""",
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
                   dispatch_summary, len(pending_tiers), len(blockers), is_dirty)
    else:
        full_briefing(run_id, proposal_id, dispatch_id, dispatch_summary,
                      run, head, state, lifecycle_trail, deliberation_rounds,
                      pending_tiers, blockers, decisions, dirty_files)


if __name__ == "__main__":
    main()
