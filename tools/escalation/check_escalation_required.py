#!/usr/bin/env python3
"""
check_escalation_required.py — Deterministic Mandatory Escalation Check
Component 2: Escalation Advisor Integration Protocol

Pure SQL evaluation: given a workflow_run_id, determines whether mandatory
escalation is required and, if required, whether it is satisfied (RECONCILED
or Eric-cancelled). Zero model reasoning at runtime.

Exit 0: ESCALATION_NOT_REQUIRED or ESCALATION_SATISFIED
Exit 1: ESCALATION_REQUIRED_UNSATISFIED
Exit 2: Error

Usage:
    check_escalation_required.py --workflow-run-id RUN_ID [--db PATH]
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "runtime"))
from db.database import init_db

DEFAULT_DB = "/mnt/projects/cis/data/cis_memory.db"


def fail(msg):
    print(f"ESCALATION_REQUIRED_UNSATISFIED: {msg}")
    sys.exit(1)


def error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def check_drift_indicators(conn, workflow_run_id):
    """Check for open drift indicators referencing this run."""
    rows = conn.execute(
        """SELECT COUNT(*) FROM drift_indicators
           WHERE status = 'RAISED'
           AND (workflow_run_id = ? OR workflow_run_id IS NULL)""",
        (workflow_run_id,),
    ).fetchone()
    return rows[0] > 0


def check_deliberation_exhaustion(conn, workflow_run_id):
    """Check if max rounds reached without CONSENSUS_REACHED."""
    run = conn.execute(
        "SELECT result, rounds_completed, max_rounds FROM workflow_runs WHERE id = ?",
        (workflow_run_id,),
    ).fetchone()
    if run is None:
        return None  # Run doesn't exist — can't determine
    result, completed, max_rounds = run
    if result == "ESCALATE" and completed >= max_rounds:
        return True
    return False


def check_verification_failure_2x(conn, workflow_run_id):
    """Check if VERIFY has failed twice on this run."""
    # Count verification failures via workflow_run_artifacts or gate results.
    # For now, check if there are multiple ERROR result deliberation rounds
    # indicating repeated failures.
    rows = conn.execute(
        """SELECT COUNT(*) FROM deliberation_rounds
           WHERE run_id = ? AND reviewer_signal IN ('ERROR', 'ESCALATE')""",
        (workflow_run_id,),
    ).fetchone()
    return rows[0] >= 2


def check_unresolved_objection(conn, workflow_run_id):
    """Check for unresolved or dismissed objections."""
    # Objections marked resolved without decision_trails
    rows = conn.execute(
        """SELECT COUNT(*) FROM deliberation_rounds d
           WHERE d.run_id = ?
           AND d.reviewer_signal = 'OBJECTIONS'
           AND d.objections_json IS NOT NULL""",
        (workflow_run_id,),
    ).fetchone()
    return rows[0] > 0


def check_governance_tier(conn, workflow_run_id):
    """Check if the project is at Tier 6+ governance scope.
    
    Reads project_state.next_tier. Returns True when next_tier >= 6.
    Note: this checks global project state, not per-run scope.
    Per-run governance detection deferred to future refinement.
    """
    state = conn.execute(
        "SELECT value FROM project_state WHERE key = 'next_tier' AND superseded_at IS NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if state:
        try:
            tier = int(state[0])
            return tier >= 6
        except ValueError:
            pass
    return False


def is_escalation_satisfied(conn, workflow_run_id):
    """Check if a mandatory escalation for this run is RECONCILED or Eric-cancelled.
    
    Returns True only if at least one mandatory escalation exists for this run
    and all mandatory escalations are in a satisfying terminal state.
    Returns False if mandatory triggers exist but no mandatory escalation
    records exist at all.
    """
    # Count total mandatory escalations for this run
    total = conn.execute(
        """SELECT COUNT(*) FROM advisor_escalations
           WHERE workflow_run_id = ?
           AND trigger_class = 'MANDATORY'""",
        (workflow_run_id,),
    ).fetchone()[0]

    # Count satisfying escalations (RECONCILED or CANCELLED_BY_ERIC)
    satisfied = conn.execute(
        """SELECT COUNT(*) FROM advisor_escalations
           WHERE workflow_run_id = ?
           AND trigger_class = 'MANDATORY'
           AND status IN ('RECONCILED', 'CANCELLED_BY_ERIC')""",
        (workflow_run_id,),
    ).fetchone()[0]

    # Satisfied only if at least one exists and none are still open
    return total > 0 and satisfied == total


def main():
    parser = argparse.ArgumentParser(
        description="Check if mandatory escalation is required for a workflow run"
    )
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    db_path = args.db
    if not Path(db_path).exists():
        error(f"Database not found: {db_path}")

    conn = init_db(db_path)

    workflow_run_id = args.workflow_run_id

    # Check if run exists
    run = conn.execute(
        "SELECT id FROM workflow_runs WHERE id = ?", (workflow_run_id,)
    ).fetchone()
    if run is None:
        conn.close()
        error(f"Workflow run '{workflow_run_id}' not found")

    # Evaluate mandatory triggers
    triggers = []
    if check_drift_indicators(conn, workflow_run_id):
        triggers.append("open_drift_indicator")
    if check_deliberation_exhaustion(conn, workflow_run_id):
        triggers.append("deliberation_exhaustion")
    if check_verification_failure_2x(conn, workflow_run_id):
        triggers.append("verification_failure_2x")
    if check_unresolved_objection(conn, workflow_run_id):
        triggers.append("unresolved_objection")
    if check_governance_tier(conn, workflow_run_id):
        triggers.append("governance_tier_work")

    conn.close()

    if not triggers:
        print(f"ESCALATION_NOT_REQUIRED for {workflow_run_id}")
        sys.exit(0)

    # Check satisfaction
    conn2 = init_db(db_path)
    satisfied = is_escalation_satisfied(conn2, workflow_run_id)
    conn2.close()

    if satisfied:
        print(f"ESCALATION_SATISFIED for {workflow_run_id}: triggers={triggers}")
        sys.exit(0)
    else:
        fail(f"ESCALATION_REQUIRED for {workflow_run_id}: triggers={triggers}")


if __name__ == "__main__":
    main()
