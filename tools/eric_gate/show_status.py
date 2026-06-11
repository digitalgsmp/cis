#!/usr/bin/env python3
"""
show_status.py — Eric Gate Approval Status Reader (Component 3)

Read-only inspection tool. Shows current approval state and full decision
history for a workflow run. Does not write to the database.

Usage:
    python3 tools/eric_gate/show_status.py --workflow-run-id <RUN_ID>
    python3 tools/eric_gate/show_status.py --workflow-run-id <RUN_ID> --db <PATH>
"""

import argparse
import os
import sqlite3
import sys

SPINE_PATH = os.environ.get(
    "CIS_SPINE_PATH",
    "/mnt/projects/cis/data/cis_memory.db",
)


def dict_from_row(conn, query, params=()):
    """Execute query and return first row as dict."""
    row = conn.execute(query, params).fetchone()
    if row is None:
        return None
    cols = list(row.keys())
    return dict(zip(cols, row))


def main():
    parser = argparse.ArgumentParser(
        description="Eric Gate Approval Status Reader (Component 3)"
    )
    parser.add_argument(
        "--workflow-run-id", required=True,
        help="Workflow run ID to show status for",
    )
    parser.add_argument(
        "--db", default=SPINE_PATH,
        help=f"Database path (default: {SPINE_PATH})",
    )
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"ERROR: Database not found: {args.db}", file=sys.stderr)
        sys.exit(2)

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    try:
        # Workflow run info
        run = dict_from_row(
            conn,
            "SELECT id, topic, result, status, eric_approved_at, "
            "requires_eric_review FROM workflow_runs WHERE id = ?",
            (args.workflow_run_id,),
        )
        if run is None:
            print(f"Workflow run '{args.workflow_run_id}' not found")
            sys.exit(1)

        print(f"Workflow Run: {run['id']}")
        print(f"Topic:        {run['topic']}")
        print(f"Result:       {run['result']}")
        print(f"Status:       {run['status']}")
        print(f"Eric Approved At: {run['eric_approved_at'] or 'NOT APPROVED'}")
        print()

        # Current decision
        current = dict_from_row(
            conn,
            """SELECT id, decision, decided_at, decided_by, goal_reference_id,
                      is_current, rationale
               FROM eric_gate_approvals
               WHERE workflow_run_id = ? AND is_current = 1
               ORDER BY decided_at DESC LIMIT 1""",
            (args.workflow_run_id,),
        )

        if current:
            print(f"Current Decision: {current['decision']}")
            print(f"  Approval ID:   {current['id']}")
            print(f"  Decided At:    {current['decided_at']}")
            print(f"  Decided By:    {current['decided_by']}")
            print(f"  Goal Ref ID:   {current['goal_reference_id']}")
            if current['rationale']:
                print(f"  Rationale:     {current['rationale']}")

            # Closeout validity
            if current['decision'] == 'APPROVE':
                wf_approved = run['eric_approved_at']
                ga_decided = current['decided_at']
                if wf_approved == ga_decided:
                    print()
                    print("Closeout: VALID — approval timestamp matches")
                else:
                    print()
                    print("Closeout: MISMATCH — workflow_runs.eric_approved_at "
                          f"({wf_approved}) != eric_gate_approvals.decided_at "
                          f"({ga_decided})")
            else:
                print()
                print(f"Closeout: BLOCKED — current decision is {current['decision']}, "
                      "not APPROVE")
        else:
            print("Current Decision: NONE — no Eric Gate decision recorded")

        # Full history
        rows = conn.execute(
            """SELECT id, decision, decided_at, decided_by, is_current,
                      supersedes_approval_id, rationale
               FROM eric_gate_approvals
               WHERE workflow_run_id = ?
               ORDER BY decided_at""",
            (args.workflow_run_id,),
        ).fetchall()

        if rows:
            print()
            print("Decision History:")
            print(f"  {'ID':<18} {'Decision':<18} {'Is Current':<12} {'Decided At'}")
            print(f"  {'-'*18} {'-'*18} {'-'*12} {'-'*20}")
            for r in rows:
                current_marker = "YES" if r["is_current"] else "no"
                superseded = ""
                if r["supersedes_approval_id"]:
                    superseded = f" (superseded {r['supersedes_approval_id'][:12]}...)"
                print(f"  {r['id']:<18} {r['decision']:<18} "
                      f"{current_marker:<12} {r['decided_at']}{superseded}")
                if r["rationale"]:
                    print(f"    Rationale: {r['rationale']}")
        else:
            print()
            print("Decision History: (none)")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
