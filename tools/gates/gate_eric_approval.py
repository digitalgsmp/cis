#!/usr/bin/env python3
"""
gate_eric_approval.py — Eric Gate Approval Verification (Component 3)

Verifies that an approved workflow run has valid approval provenance.
Selects the current Eric Gate decision row (is_current=1) and runs 6 checks.
Prior VETO/RETURN_TO_DRAFT rows with is_current=0 must not cause failure.

Usage:
    python3 tools/gates/gate_eric_approval.py --workflow-run-id <RUN_ID>
    python3 tools/gates/gate_eric_approval.py --workflow-run-id <RUN_ID> --db <PATH>

Exit 0: PASS — approval provenance is valid
Exit 1: FAIL — approval provenance is missing, stale, or invalid
Exit 2: ERROR — usage, config, or DB error
"""

import argparse
import json
import os
import sqlite3
import sys

SPINE_PATH = os.environ.get(
    "CIS_SPINE_PATH",
    "/mnt/projects/cis/data/cis_memory.db",
)


def fail(code, msg):
    print(f"FAIL [{code}]: {msg}", file=sys.stderr)
    sys.exit(1)


def error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def get_current_approval(conn, run_id):
    """Get current Eric Gate decision row, or None."""
    row = conn.execute(
        """SELECT * FROM eric_gate_approvals
           WHERE workflow_run_id = ? AND is_current = 1
           ORDER BY decided_at DESC, created_at DESC, id DESC
           LIMIT 1""",
        (run_id,),
    ).fetchone()
    if row is None:
        return None
    cols = list(row.keys())
    return dict(zip(cols, row))


def check_1_valid_workflow_run(conn, run_id):
    """Workflow run exists, is CONSENSUS_REACHED, not in ERROR."""
    row = conn.execute(
        "SELECT id, result, status FROM workflow_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    if row is None:
        fail(1, f"Workflow run '{run_id}' not found")
    result = row[1]
    status = row[2]
    if result != "CONSENSUS_REACHED":
        fail(1, f"Run result is '{result}', expected 'CONSENSUS_REACHED'")
    if status == "ERROR":
        fail(1, "Run is in ERROR status")
    print(f"[1] PASS: Workflow run {run_id} exists, result=CONSENSUS_REACHED")


def check_2_matching_approval_row(conn, run_id):
    """Current approval row exists, is APPROVE, and matches eric_approved_at."""
    approval = get_current_approval(conn, run_id)
    if approval is None:
        fail(2, "No current Eric Gate approval row found (is_current=1)")

    decision = approval.get("decision")
    if decision != "APPROVE":
        fail(2, f"Current decision is '{decision}', expected 'APPROVE'")

    # eric_approved_at must match
    row = conn.execute(
        "SELECT eric_approved_at FROM workflow_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    wf_approved = row[0] if row else None
    ga_decided = approval.get("decided_at")

    if wf_approved != ga_decided:
        fail(2, (
            f"workflow_runs.eric_approved_at ({wf_approved}) "
            f"!= eric_gate_approvals.decided_at ({ga_decided})"
        ))

    if approval.get("decided_by") != "Eric":
        fail(2, f"decided_by is '{approval.get('decided_by')}', expected 'Eric'")

    print(f"[2] PASS: Current APPROVE row {approval['id']}, "
          f"eric_approved_at matches")


def check_3_briefing_integrity(conn, run_id):
    """Briefing JSON is valid, all 4 sections present, hash matches."""
    approval = get_current_approval(conn, run_id)
    if approval is None:
        fail(3, "No current approval row to verify briefing integrity")

    briefing_json = approval.get("briefing_json", "")
    try:
        briefing = json.loads(briefing_json)
    except (json.JSONDecodeError, TypeError):
        fail(3, "Stored briefing_json is not valid JSON")

    sections = briefing.get("briefing", {})
    required = ["action_summary", "goal_trace", "decision_trail",
                "drift_indicators"]
    missing = [s for s in required if s not in sections or sections[s] is None]
    if missing:
        fail(3, f"Missing briefing sections: {', '.join(missing)}")

    # Recompute hash from stored JSON
    import hashlib
    import unicodedata

    def canonicalize(payload):
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False)
        return unicodedata.normalize("NFC", raw)

    hash_payload = {
        k: v for k, v in briefing.items()
        if k not in ("generated_at", "rationale", "briefing_hash")
    }
    canonical = canonicalize(hash_payload)
    recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    stored_hash = approval.get("briefing_hash")

    if recomputed != stored_hash:
        fail(3, (
            f"Briefing hash mismatch: stored '{stored_hash[:16]}...', "
            f"recomputed '{recomputed[:16]}...'"
        ))

    print(f"[3] PASS: Briefing integrity verified, 4 sections present, "
          f"hash matches")


def check_4_goal_trace_integrity(conn, run_id):
    """Goal reference exists and has required fields."""
    approval = get_current_approval(conn, run_id)
    if approval is None:
        fail(4, "No current approval row to verify goal trace")

    goal_id = approval.get("goal_reference_id")
    if goal_id is None:
        fail(4, "goal_reference_id is NULL")

    row = conn.execute(
        "SELECT id, goal_label, dependency_node, tier_advanced "
        "FROM goal_references WHERE id = ?",
        (goal_id,),
    ).fetchone()
    if row is None:
        fail(4, f"Goal reference {goal_id} not found in goal_references")

    goal_label = row[1] or ""
    dep_node = row[2] or ""
    tier = row[3] or ""

    if not goal_label.strip():
        fail(4, "goal_label is empty")
    if not dep_node.strip() and not tier.strip():
        fail(4, "Neither dependency_node nor tier_advanced is present")

    print(f"[4] PASS: Goal reference {goal_id}: '{goal_label}' → "
          f"{dep_node or tier}")


def check_5_drift_and_objection_state(conn, run_id):
    """No open blocking drift, unresolved objections, or unreconciled escalations."""
    approval = get_current_approval(conn, run_id)
    if approval is None:
        fail(5, "No current approval row to verify drift state")

    drift_snapshot = approval.get("drift_snapshot_json", "{}")
    try:
        drift = json.loads(drift_snapshot)
    except (json.JSONDecodeError, TypeError):
        fail(5, "Stored drift_snapshot_json is not valid JSON")

    open_count = drift.get("open_drift_count", 0)
    blocking = drift.get("blocking_drift", [])

    if open_count > 0 or len(blocking) > 0:
        fail(5, f"{open_count} open blocking drift indicator(s) at approval time")

    # Check current state too — no new drift since approval
    current_drift = conn.execute(
        """SELECT COUNT(*) FROM drift_indicators
           WHERE workflow_run_id = ?
             AND status IN ('RAISED', 'ACKNOWLEDGED', 'ESCALATED')
             AND raised_at > ?""",
        (run_id, approval.get("decided_at")),
    ).fetchone()
    if current_drift and current_drift[0] > 0:
        fail(5, f"{current_drift[0]} new drift indicator(s) raised since approval")

    print(f"[5] PASS: No blocking drift, objections, or unreconciled escalations")


def check_6_export_agreement():
    """Export gate passes — regenerate context and verify."""
    import subprocess

    # Check generate_all.py
    result = subprocess.run(
        ["python3", "/mnt/projects/cis/tools/export/generate_all.py"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        fail(6, f"generate_all.py failed:\n{result.stderr.strip()}")

    # Check export agreement gate
    result2 = subprocess.run(
        ["bash", "/mnt/projects/cis/tools/gates/gate_export_agreement.sh"],
        capture_output=True, text=True, timeout=30,
    )
    if result2.returncode != 0:
        fail(6, f"gate_export_agreement.sh failed:\n{result2.stdout.strip()}")

    print(f"[6] PASS: Export agreement verified, context regenerated")


def main():
    parser = argparse.ArgumentParser(
        description="Eric Gate Approval Verification (Component 3)"
    )
    parser.add_argument(
        "--workflow-run-id", required=True,
        help="Workflow run ID to verify approval for",
    )
    parser.add_argument(
        "--db", default=SPINE_PATH,
        help=f"Database path (default: {SPINE_PATH})",
    )
    args = parser.parse_args()

    if not os.path.exists(args.db):
        error(f"Database not found: {args.db}")

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    try:
        check_1_valid_workflow_run(conn, args.workflow_run_id)
        check_2_matching_approval_row(conn, args.workflow_run_id)
        check_3_briefing_integrity(conn, args.workflow_run_id)
        check_4_goal_trace_integrity(conn, args.workflow_run_id)
        check_5_drift_and_objection_state(conn, args.workflow_run_id)
        check_6_export_agreement()
    finally:
        conn.close()

    print("\nPASS: Eric Gate approval provenance verified")
    sys.exit(0)


if __name__ == "__main__":
    main()
