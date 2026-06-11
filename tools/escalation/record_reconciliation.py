#!/usr/bin/env python3
"""
record_reconciliation.py — Record Eric's Reconciliation
Component 2: Escalation Advisor Integration Protocol

Records disposition, note, divergence fields. Writes linked decision_trails
entry and, when applicable, rejection_rationale. Requires an explicit
Eric-attribution flag. Refuses to run on escalations in terminal states.

Usage:
    record_reconciliation.py --escalation-id ID \
        --disposition ACCEPT|ACCEPT_WITH_MODIFICATION|REJECT|RETURN_TO_DRAFT|ESCALATE_FURTHER \
        --note "Eric's reconciliation note" \
        --eric-attribution \
        [--divergence-summary "..."] [--positions-json "..."] \
        [--workflow-run-id RUN_ID] [--db PATH]
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "runtime"))
from db.database import (
    init_db, get_escalation, get_escalation_responses,
    record_reconciliation as db_record_reconciliation,
    ALLOWED_RECONCILIATION_DISPOSITIONS,
)

DEFAULT_DB = "/mnt/projects/cis/data/cis_memory.db"

TERMINAL_STATUSES = {"ABANDONED", "SUPERSEDED", "CANCELLED_BY_ERIC", "RECONCILED"}


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Record Eric's reconciliation of an advisor escalation"
    )
    parser.add_argument("--escalation-id", type=int, required=True)
    parser.add_argument("--disposition", required=True,
                        choices=sorted(ALLOWED_RECONCILIATION_DISPOSITIONS))
    parser.add_argument("--note", required=True,
                        help="Eric's plain-language reconciliation note")
    parser.add_argument("--eric-attribution", action="store_true", required=True,
                        help="Required: Eric must explicitly attribute this reconciliation")
    parser.add_argument("--divergence-summary", default=None)
    parser.add_argument("--positions-json", default=None)
    parser.add_argument("--workflow-run-id", default=None,
                        help="Workflow run to link decision_trails entry to")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--reject-advisor", choices=["CLAUDE", "CHATGPT"], default=None,
                        help="If REJECT disposition, which advisor's position is rejected")
    parser.add_argument("--rejection-reason", default=None,
                        help="Rejection rationale detail (required if --reject-advisor set)")
    args = parser.parse_args()

    db_path = args.db
    if not Path(db_path).exists():
        fail(f"Database not found: {db_path}")

    conn = init_db(db_path)

    esc = get_escalation(conn, args.escalation_id)
    if esc is None:
        conn.close()
        fail(f"Escalation {args.escalation_id} not found")

    if esc["status"] in TERMINAL_STATUSES:
        conn.close()
        fail(f"Escalation {args.escalation_id} is in terminal state '{esc['status']}' — cannot reconcile")

    now = datetime.now(timezone.utc).isoformat()

    # Record reconciliation
    db_record_reconciliation(
        conn, args.escalation_id, args.disposition, args.note,
        divergence_summary=args.divergence_summary,
        positions_json=args.positions_json,
        reconciled_at=now,
    )

    # Write decision_trails entry
    workflow_run_id = args.workflow_run_id or esc["workflow_run_id"]
    if workflow_run_id:
        # Get next trail sequence
        cur = conn.execute(
            "SELECT COALESCE(MAX(trail_sequence), 0) FROM decision_trails WHERE workflow_run_id = ?",
            (workflow_run_id,),
        )
        next_seq = cur.fetchone()[0] + 1

        problem = f"Escalation {args.escalation_id}: {esc['trigger_class']} — {esc['trigger_reason']}"
        proposed_action = f"Eric reconciled: {args.disposition}. {args.note}"

        conn.execute(
            """INSERT INTO decision_trails
               (workflow_run_id, trail_sequence, problem_statement, proposed_action,
                consensus_signal, authored_by, external_audit_summary, created_at)
               VALUES (?, ?, ?, ?, 'ESCALATED_EXTERNAL', 'CLOSEOUT', ?, ?)""",
            (workflow_run_id, next_seq, problem, proposed_action,
             f"Escalation {args.escalation_id}: {args.disposition}", now),
        )
        decision_trail_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"Decision trail created: id={decision_trail_id} seq={next_seq} run={workflow_run_id}")

        # Write rejection_rationale if Eric rejected an advisor
        if args.disposition == "REJECT" and args.reject_advisor and args.rejection_reason:
            rejected_label = f"Advisor {args.reject_advisor} position on escalation {args.escalation_id}"
            conn.execute(
                """INSERT INTO rejection_rationale
                   (decision_trail_id, workflow_run_id, rejected_option_label,
                    rejected_option_summary, rejection_reason, rejection_detail, rejected_by, created_at)
                   VALUES (?, ?, ?, ?, 'ERIC_REJECTED', ?, 'ERIC', ?)""",
                (decision_trail_id, workflow_run_id, rejected_label,
                 f"Advisor {args.reject_advisor} recommendation rejected",
                 args.rejection_reason, now),
            )
            print(f"Rejection rationale recorded for advisor {args.reject_advisor}")

    conn.commit()
    conn.close()

    print(f"Escalation {args.escalation_id} reconciled: {args.disposition}")


if __name__ == "__main__":
    main()
