#!/usr/bin/env python3
"""
reviewer_pickup.py — Tier 11D: Pick up PENDING dispatch for hermes-r1, claim it,
transition REVIEW_PENDING → REVIEWING.

ADR-SEED-012 (Orchestrator Validation Contract), ADR-SEED-014 Clause 6.

Usage:
  # List all PENDING dispatches for hermes-r1 (list mode):
  python3 tools/pipeline/reviewer_pickup.py

  # Claim a specific dispatch:
  python3 tools/pipeline/reviewer_pickup.py --dispatch-id <uuid>

  # Claim the dispatch for a specific workflow run:
  python3 tools/pipeline/reviewer_pickup.py --run-id <id>

  # With explicit session ID:
  python3 tools/pipeline/reviewer_pickup.py --run-id <id> --session-id <sid>
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone


DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
REPO_ROOT = "/mnt/projects/cis"


def get_db():
    """Open CIS spine database with row factory."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def resolve_session_id(run_id, explicit, db):
    """Session ID resolution order: explicit arg → most recent lifecycle → ISO timestamp."""
    if explicit:
        return explicit
    row = db.execute(
        """SELECT session_id FROM lifecycle_events
           WHERE workflow_run_id = ? AND session_id IS NOT NULL
           ORDER BY id DESC LIMIT 1""",
        (run_id,)
    ).fetchone()
    if row and row["session_id"]:
        return row["session_id"]
    return datetime.now(timezone.utc).isoformat()


def list_mode(db):
    """List all PENDING dispatches for hermes-r1."""
    rows = db.execute(
        """SELECT d.dispatch_id, d.workflow_run_id, d.proposal_id,
                  d.timestamp_initiated, d.payload_summary,
                  w.topic
           FROM dispatch_log d
           LEFT JOIN workflow_runs w ON d.workflow_run_id = w.id
           WHERE d.target_agent = 'hermes-r1' AND d.current_status = 'PENDING'
           ORDER BY d.timestamp_initiated ASC"""
    ).fetchall()

    if not rows:
        print("No PENDING dispatches.")
        return

    for r in rows:
        print(f"dispatch_id: {r['dispatch_id']}")
        print(f"  workflow_run_id: {r['workflow_run_id']}")
        print(f"  proposal_id: {r['proposal_id']}")
        topic = (r['topic'] or '')[:120]
        print(f"  topic: {topic}")
        summary = (r['payload_summary'] or '')[:200]
        print(f"  summary: {summary}")
        print(f"  initiated: {r['timestamp_initiated']}")
        print()


def claim_mode(args, db):
    """Claim a dispatch and transition REVIEW_PENDING → REVIEWING."""

    # Validate input: one and only one of --run-id or --dispatch-id
    if args.run_id and args.dispatch_id:
        print("REFUSED: Cannot specify both --run-id and --dispatch-id.", file=sys.stderr)
        sys.exit(1)
    if not args.run_id and not args.dispatch_id:
        print("REFUSED: Must specify --run-id or --dispatch-id when claiming (or neither to list).",
              file=sys.stderr)
        sys.exit(1)

    # Import orchestration functions
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import transition_state, get_current_state, update_dispatch_inflight

    # Find the dispatch
    if args.dispatch_id:
        dispatch = db.execute(
            "SELECT * FROM dispatch_log WHERE dispatch_id = ?",
            (args.dispatch_id,)
        ).fetchone()
    else:
        dispatch = db.execute(
            """SELECT * FROM dispatch_log
               WHERE workflow_run_id = ? AND current_status = 'PENDING'
               ORDER BY timestamp_initiated ASC LIMIT 1""",
            (args.run_id,)
        ).fetchone()

    if dispatch is None:
        print("REFUSED: No PENDING dispatch found.", file=sys.stderr)
        sys.exit(1)

    if dispatch["current_status"] != "PENDING":
        print(f"REFUSED: Dispatch already {dispatch['current_status']}.", file=sys.stderr)
        sys.exit(1)

    dispatch_id = dispatch["dispatch_id"]
    run_id = dispatch["workflow_run_id"]
    proposal_id = dispatch["proposal_id"]

    # Resolve session_id
    session_id = resolve_session_id(run_id, args.session_id, db)

    # Verify current lifecycle state is REVIEW_PENDING
    current_state = get_current_state(proposal_id, db)
    if current_state != "REVIEW_PENDING":
        print(f"REFUSED: Current lifecycle state is '{current_state}', "
              f"expected 'REVIEW_PENDING'.", file=sys.stderr)
        sys.exit(1)

    # Mark dispatch IN_FLIGHT
    update_dispatch_inflight(dispatch_id, db)

    # Transition state: REVIEW_PENDING → REVIEWING
    reviewing_row_id = transition_state(
        proposal_id, session_id,
        "REVIEW_PENDING", "REVIEWING",
        "reviewer_pickup.py", db=db,
        dispatch_ref=dispatch_id)

    # Backfill workflow_run_id
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (run_id, reviewing_row_id))
    db.commit()

    # Update workflow_runs status
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE workflow_runs SET status = 'REVIEWING', updated_at = ? WHERE id = ?",
        (now, run_id))
    db.commit()

    # Output
    print("CLAIMED")
    print(f"dispatch_id: {dispatch_id}")
    print(f"workflow_run_id: {run_id}")
    print(f"proposal_id: {proposal_id}")
    print("target_endpoint: http://127.0.0.1:8643")
    print("lifecycle_state: REVIEWING")


def main():
    parser = argparse.ArgumentParser(
        description="CIS Tier 11D — Reviewer dispatch pickup"
    )
    parser.add_argument("--run-id", default=None, help="Workflow run ID")
    parser.add_argument("--dispatch-id", default=None, help="Specific dispatch ID")
    parser.add_argument("--session-id", default=None, help="Session identifier")
    args = parser.parse_args()

    db = get_db()

    # List mode: neither --run-id nor --dispatch-id
    if not args.run_id and not args.dispatch_id:
        list_mode(db)
        db.close()
        sys.exit(0)

    claim_mode(args, db)
    db.close()


if __name__ == "__main__":
    main()
