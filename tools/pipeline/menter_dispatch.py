#!/usr/bin/env python3
"""
menter_dispatch.py — R1: dispatch Menter (sandboxed Claude Code) on Eric approval.

Transitions ERIC_APPROVAL_GATE -> MENTER_BUILDING, persists card_scope on the
workflow_run at first dispatch, writes the dispatch_log row, and launches
tools/run_claude_sandbox.sh in the background with the approved directive.

The completion hook (menter_closeout.py) is invoked by run_claude_sandbox.sh
itself after the sandbox exits — this script only starts the build.

Usage:
  python3 tools/pipeline/menter_dispatch.py --run-id <id> --card-scope '["a.py", "b/*.py"]'
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
REPO_ROOT = os.environ.get("CIS_REPO_ROOT", "/mnt/projects/cis")


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def resolve_proposal_id(run_id, db):
    row = db.execute(
        "SELECT DISTINCT proposal_id FROM lifecycle_events "
        "WHERE workflow_run_id = ? ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    return row["proposal_id"] if row else None


def resolve_session_id(run_id, db):
    row = db.execute(
        "SELECT session_id FROM lifecycle_events "
        "WHERE workflow_run_id = ? AND session_id IS NOT NULL "
        "ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    if row and row["session_id"]:
        return row["session_id"]
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description="Dispatch Menter (sandboxed Claude Code)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--card-scope", required=True,
                        help="JSON list of repo-relative path globs")
    args = parser.parse_args()

    try:
        card_scope = json.loads(args.card_scope)
        if not isinstance(card_scope, list) or not card_scope:
            raise ValueError("card_scope must be a non-empty JSON list")
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"REFUSED: bad --card-scope: {exc}", file=sys.stderr)
        sys.exit(1)

    db = get_db()
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (args.run_id,)).fetchone()
    if run is None:
        print(f"REFUSED: workflow_run not found: {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    proposal_id = resolve_proposal_id(args.run_id, db)
    if not proposal_id:
        print(f"REFUSED: no proposal_id for run {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import get_current_state, transition_state, create_dispatch

    current = get_current_state(proposal_id, db)
    if current != "ERIC_APPROVAL_GATE":
        print(f"REFUSED: current state '{current}', expected ERIC_APPROVAL_GATE",
              file=sys.stderr)
        db.close()
        sys.exit(1)

    session_id = resolve_session_id(args.run_id, db)

    # Persist card_scope at dispatch time (R6 item 7) — before the build starts.
    scope_json = json.dumps(card_scope)
    db.execute(
        "UPDATE workflow_runs SET card_scope = ? WHERE id = ?",
        (scope_json, args.run_id),
    )
    db.commit()

    # Lifecycle: ERIC_APPROVAL_GATE -> MENTER_BUILDING
    row_id = transition_state(
        proposal_id, session_id, "ERIC_APPROVAL_GATE", "MENTER_BUILDING",
        "menter_dispatch.py", db=db,
        notes=f"card_scope={scope_json}")
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, row_id))
    db.commit()

    # Dispatch log row
    payload = json.dumps({"run_id": args.run_id, "card_scope": card_scope})
    dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor="orchestrator",
        target_agent="menter",
        target_endpoint="sandbox:tools/run_claude_sandbox.sh",
        lifecycle_state_at="MENTER_BUILDING",
        payload=payload,
        initiated_by="menter_dispatch.py",
        eric_approved=1,
        db=db)
    db.execute(
        "UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?",
        (args.run_id, dispatch_id))
    db.commit()

    # Launch the sandboxed coder in the background. The sandbox script's own
    # completion hook fires menter_closeout.py when it exits (R2).
    topic = run["topic"] if run["topic"] else ""
    sandbox_cmd = [
        "bash", os.path.join(REPO_ROOT, "tools", "run_claude_sandbox.sh"),
        "--run-id", args.run_id,
        "--card-scope", scope_json,
        json.dumps({"run_id": args.run_id, "topic": topic, "card_scope": card_scope}),
    ]
    subprocess.Popen(
        sandbox_cmd,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True, cwd=REPO_ROOT)

    print("MENTER DISPATCHED")
    print(f"workflow_run_id: {args.run_id}")
    print(f"dispatch_id: {dispatch_id}")
    print(f"lifecycle: ERIC_APPROVAL_GATE -> MENTER_BUILDING")

    db.close()


if __name__ == "__main__":
    main()
