#!/usr/bin/env python3
"""
record_decision.py — Eric Gate Approval Setter (Component 3)

Records Eric's decision (APPROVE, VETO, RETURN_TO_DRAFT) on a workflow run
after verifying all 13 setter preconditions. All writes execute in a single
SQLite transaction. If any precondition fails, exits non-zero and writes nothing.

Usage:
    python3 tools/eric_gate/record_decision.py \
      --workflow-run-id <RUN_ID> \
      --decision APPROVE \
      --briefing-hash <HASH> \
      --goal-reference-id <GOAL_REFERENCE_ID> \
      --rationale "<ERIC_NOTE>"

    # Supersede a prior current row:
    python3 tools/eric_gate/record_decision.py \
      --workflow-run-id <RUN_ID> \
      --decision APPROVE \
      --briefing-hash <HASH> \
      --goal-reference-id <GOAL_REFERENCE_ID> \
      --rationale "<ERIC_NOTE>" \
      --supersede
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone

# ── Constants ──────────────────────────────────────────────────────

SPINE_PATH = os.environ.get(
    "CIS_SPINE_PATH",
    "/mnt/projects/cis/data/cis_memory.db",
)
BUILD_BRIEFING_SCRIPT = os.path.join(
    os.path.dirname(__file__), "build_briefing.py"
)

ALLOWED_DECISIONS = {"APPROVE", "VETO", "RETURN_TO_DRAFT"}


# ── Helpers ────────────────────────────────────────────────────────

def get_git_head():
    """Return full 40-char git HEAD or 'UNKNOWN'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd="/mnt/projects/cis",
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def dict_from_row(conn, query, params=()):
    """Execute query and return first row as dict."""
    row = conn.execute(query, params).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in row.keys()]
    return dict(zip(cols, row))


def rebuild_briefing(run_id, db_path=None):
    """Rebuild briefing from current spine state. Returns (payload, error)."""
    try:
        cmd = [sys.executable, BUILD_BRIEFING_SCRIPT,
               "--workflow-run-id", run_id, "--json"]
        if db_path:
            cmd.extend(["--db", db_path])
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return None, f"Briefing rebuild failed: {result.stderr.strip()}"
        payload = json.loads(result.stdout)
        return payload, None
    except json.JSONDecodeError as e:
        return None, f"Briefing rebuild produced invalid JSON: {e}"
    except Exception as e:
        return None, f"Briefing rebuild error: {e}"


# ── Precondition Checks ────────────────────────────────────────────

def check_1_workflow_run_exists(conn, run_id):
    """Workflow run exists."""
    row = conn.execute(
        "SELECT id FROM workflow_runs WHERE id = ?", (run_id,)
    ).fetchone()
    if row is None:
        return False, f"Workflow run '{run_id}' not found"
    return True, None


def check_2_consensus_reached(conn, run_id):
    """The DELIBERATION reached consensus — not that the whole run finished.

    This checked workflow_runs.result == 'CONSENSUS_REACHED' until 2026-08-30,
    which was a deadlock. That field is written in exactly one place —
    _verification() in pipeline_relay.py, the LAST phase — and verification only
    runs after the Eric Gate approves. So the gate demanded an outcome that only
    exists once the gate has already been passed, and no run could ever be
    approved through this tool. It is the same circular shape as the briefing
    bug fixed on 2026-08-28, where the gate read decision_trails and
    goal_references that only the approval handler created.

    What the gate actually needs to know is whether the agents agreed BEFORE it
    is asked to decide, and that is recorded per round in
    deliberation_rounds.reviewer_signal. The post-verification value is still
    accepted so a completed run can be re-decided. (UNIFIED BUILD LIST 1.9)
    """
    row = conn.execute(
        "SELECT result FROM workflow_runs WHERE id = ?", (run_id,)
    ).fetchone()
    if row is None:
        return False, "Workflow run not found"
    if row[0] == "CONSENSUS_REACHED":
        return True, None

    last = conn.execute(
        "SELECT reviewer_signal FROM deliberation_rounds "
        "WHERE run_id = ? ORDER BY id DESC LIMIT 1",
        (run_id,),
    ).fetchone()
    if last is None:
        return False, (
            f"Workflow run result is '{row[0]}' and no deliberation rounds "
            f"were recorded — nothing reached consensus"
        )
    if last[0] != "CONSENSUS_REACHED":
        return False, (
            f"Last deliberation round signalled '{last[0]}', "
            f"expected 'CONSENSUS_REACHED' (run result is '{row[0]}')"
        )
    return True, None


def check_3_requires_eric_review(conn, run_id):
    """Workflow run requires Eric review unless explicitly exempted."""
    row = conn.execute(
        "SELECT requires_eric_review FROM workflow_runs WHERE id = ?", (run_id,)
    ).fetchone()
    if row is None:
        return False, "Workflow run not found"
    if row[0] != 1:
        return False, (
            "Workflow run does not require Eric review "
            "(requires_eric_review != 1)"
        )
    return True, None


def check_4_briefing_rebuildable(run_id, db_path=None):
    """Briefing can be rebuilt from current spine state."""
    payload, err = rebuild_briefing(run_id, db_path)
    if err:
        return False, err
    return True, payload


def check_5_briefing_hash_matches(payload, supplied_hash):
    """Rebuilt briefing hash equals supplied briefing hash."""
    rebuilt_hash = payload.get("briefing_hash", "")
    if rebuilt_hash != supplied_hash:
        return False, (
            f"Briefing hash mismatch: supplied '{supplied_hash}', "
            f"rebuilt '{rebuilt_hash}'"
        )
    return True, None


def check_6_goal_reference_valid(conn, run_id, goal_reference_id):
    """Supplied goal reference exists and is valid."""
    row = conn.execute(
        """SELECT id, workflow_run_id, goal_label
           FROM goal_references WHERE id = ?""",
        (goal_reference_id,),
    ).fetchone()
    if row is None:
        return False, f"Goal reference '{goal_reference_id}' not found"

    # Goal reference must belong to this run or be a project-level reference
    goal_run = row[1]
    if goal_run is not None and goal_run != run_id:
        return False, (
            f"Goal reference '{goal_reference_id}' belongs to "
            f"workflow run '{goal_run}', not '{run_id}'"
        )
    return True, None


def check_7_all_sections_present(payload):
    """All four briefing sections are present."""
    briefing = payload.get("briefing", {})
    required = ["action_summary", "goal_trace", "decision_trail",
                "drift_indicators"]
    missing = [s for s in required if s not in briefing or briefing[s] is None]
    if missing:
        return False, f"Missing briefing sections: {', '.join(missing)}"
    return True, None


def check_8_no_blocking_drift(conn, run_id):
    """No open blocking drift indicator exists."""
    row = conn.execute(
        """SELECT COUNT(*) FROM drift_indicators
           WHERE workflow_run_id = ?
             AND status IN ('RAISED', 'ACKNOWLEDGED', 'ESCALATED')""",
        (run_id,),
    ).fetchone()
    count = row[0]
    if count > 0:
        # List them for the error message
        drift = conn.execute(
            """SELECT id, indicator_type, description FROM drift_indicators
               WHERE workflow_run_id = ?
                 AND status IN ('RAISED', 'ACKNOWLEDGED', 'ESCALATED')
               ORDER BY id""",
            (run_id,),
        ).fetchall()
        ids = [f"#{d[0]} ({d[1]}): {d[2][:60]}" for d in drift]
        return False, (
            f"{count} open blocking drift indicator(s): {'; '.join(ids)}"
        )
    return True, None


def check_9_no_unresolved_objections(conn, run_id):
    """No unresolved final objections exist."""
    row = conn.execute(
        "SELECT final_objections_json FROM workflow_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    if row is None:
        return False, "Workflow run not found"

    objections_json = row[0]
    if not objections_json:
        return True, None  # No objections = no problem

    try:
        objections = json.loads(objections_json)
    except (json.JSONDecodeError, TypeError):
        return True, None  # Can't parse = don't block

    if isinstance(objections, list) and len(objections) > 0:
        # Check if any objection is explicitly unresolved
        unresolved = [
            o for o in objections
            if isinstance(o, dict) and o.get("resolved") is False
        ]
        if unresolved:
            return False, (
                f"{len(unresolved)} unresolved final objection(s) "
                f"in final_objections_json"
            )
    return True, None


def check_10_no_unreconciled_escalation(conn, run_id):
    """No mandatory escalation remains unreconciled."""
    # Check if advisor_escalations table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='advisor_escalations'"
    ).fetchone()
    if table_check is None:
        # Component 2 tables not yet present — no-op with warning
        return True, "WARNING: advisor_escalations table not found — check skipped"

    row = conn.execute(
        """SELECT COUNT(*) FROM advisor_escalations
           WHERE workflow_run_id = ?
             AND trigger_class = 'MANDATORY'
             AND status NOT IN ('RECONCILED', 'CANCELLED_BY_ERIC',
                                'ABANDONED', 'SUPERSEDED')""",
        (run_id,),
    ).fetchone()
    count = row[0]
    if count > 0:
        return False, (
            f"{count} unreconciled mandatory escalation(s) for this run"
        )
    return True, None


def check_11_no_prior_current_approval(conn, run_id, supersede):
    """No prior current approval exists unless --supersede is passed."""
    row = conn.execute(
        """SELECT id, decision FROM eric_gate_approvals
           WHERE workflow_run_id = ? AND is_current = 1""",
        (run_id,),
    ).fetchone()
    if row is None:
        return True, None  # No prior row = fine

    if supersede:
        return True, f"Will supersede current decision: {row[0]} ({row[1]})"

    return False, (
        f"Prior current Eric Gate decision exists: {row[0]} ({row[1]}). "
        f"Use --supersede to replace it."
    )


def check_12_git_head_matches(payload):
    """Git HEAD matches briefing source fingerprint."""
    current_head = get_git_head()
    briefing_head = (
        payload.get("source_fingerprint", {}).get("git_head", "")
    )
    if current_head == "UNKNOWN" or briefing_head == "UNKNOWN":
        return True, "WARNING: could not verify git HEAD"
    if current_head != briefing_head:
        return False, (
            f"Git HEAD mismatch: briefing has '{briefing_head[:8]}...', "
            f"current HEAD is '{current_head[:8]}...'"
        )
    return True, None


def check_13_valid_decision(decision):
    """Decision is one of APPROVE, VETO, or RETURN_TO_DRAFT."""
    if decision not in ALLOWED_DECISIONS:
        return False, (
            f"Invalid decision '{decision}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_DECISIONS))}"
        )
    return True, None


# ── Main Setter ────────────────────────────────────────────────────

def record_decision(run_id, decision, briefing_hash, goal_reference_id,
                    rationale, supersede, conn, db_path=None):
    """Run all preconditions, then write decision in a transaction."""

    checks = [
        ("Workflow run exists", check_1_workflow_run_exists(conn, run_id)),
        ("Requires Eric review", check_3_requires_eric_review(conn, run_id)),
    ]

    # Consensus is a precondition for APPROVING, not for refusing. Approving
    # work the deliberation never agreed on is exactly what this gate exists to
    # stop. But applying the same bar to VETO made a malformed run immortal:
    # two 2026-08-22 smoke tests reached ERIC_GATE with result 'PENDING' and
    # could then be neither approved nor closed, so they sat in the queue for
    # eight days making it look like real work awaited a decision. A gate that
    # cannot dispose of what it cannot pass is not a gate, it is a trap.
    # (UNIFIED BUILD LIST 1.9)
    if decision == "APPROVE":
        checks.insert(1, ("CONSENSUS_REACHED",
                          check_2_consensus_reached(conn, run_id)))

    # Check 4: briefing rebuildable
    ok, payload_or_err = check_4_briefing_rebuildable(run_id, db_path)
    checks.append(("Briefing rebuildable", (ok, payload_or_err if not ok else None)))
    if not ok:
        payload = None
    else:
        payload = payload_or_err

    if payload is None:
        for label, (ok, err) in checks:
            if not ok:
                print(f"FAIL [{label}]: {err}", file=sys.stderr)
        return 1

    checks.extend([
        ("Briefing hash matches",
         check_5_briefing_hash_matches(payload, briefing_hash)),
        ("Goal reference valid",
         check_6_goal_reference_valid(conn, run_id, goal_reference_id)),
        ("All sections present",
         check_7_all_sections_present(payload)),
        ("No blocking drift",
         check_8_no_blocking_drift(conn, run_id)),
        ("No unresolved objections",
         check_9_no_unresolved_objections(conn, run_id)),
        ("No unreconciled escalation",
         check_10_no_unreconciled_escalation(conn, run_id)),
        ("No prior current approval",
         check_11_no_prior_current_approval(conn, run_id, supersede)),
        ("Git HEAD matches",
         check_12_git_head_matches(payload)),
        ("Valid decision",
         check_13_valid_decision(decision)),
    ])

    # Run remaining checks
    all_ok = True
    for label, (ok, err) in checks:
        if not ok:
            print(f"FAIL [{label}]: {err}", file=sys.stderr)
            all_ok = False

    if not all_ok:
        return 1

    # All preconditions passed — write in a single transaction
    approval_id = f"ega-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    briefing_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    drift_snapshot = json.dumps(
        payload["briefing"]["drift_indicators"],
        sort_keys=True, separators=(",", ":"),
    )
    decision_trail_snapshot = json.dumps(
        payload["briefing"]["decision_trail"],
        sort_keys=True, separators=(",", ":"),
    )

    try:
        # Begin transaction
        conn.execute("BEGIN")

        # Supersede prior current row
        conn.execute(
            """UPDATE eric_gate_approvals SET is_current = 0
               WHERE workflow_run_id = ? AND is_current = 1""",
            (run_id,),
        )
        prior_current = conn.execute(
            """SELECT id FROM eric_gate_approvals
               WHERE workflow_run_id = ? AND is_current = 0
               ORDER BY decided_at DESC LIMIT 1""",
            (run_id,),
        ).fetchone()
        supersedes_id = prior_current[0] if prior_current else None

        # Insert new row
        conn.execute(
            """INSERT INTO eric_gate_approvals
               (id, workflow_run_id, decision, decided_at, decided_by,
                goal_reference_id, briefing_hash, briefing_json,
                drift_snapshot_json, decision_trail_snapshot_json,
                is_current, supersedes_approval_id, rationale, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (approval_id, run_id, decision, now, "Eric",
             goal_reference_id, briefing_hash, briefing_json,
             drift_snapshot, decision_trail_snapshot,
             1, supersedes_id, rationale, now),
        )

        # For APPROVE: set workflow_runs.eric_approved_at
        # For VETO/RETURN_TO_DRAFT: clear it (supersedes prior APPROVE)
        if decision == "APPROVE":
            # status must advance, not just eric_approved_at. Until 2026-08-30
            # this set the timestamp and left status at ERIC_GATE, and
            # PipelineRelay.resume() on an ERIC_GATE run prints "waiting at
            # ERIC_GATE" and returns — so approving through this path, the one
            # the session notes documented, parked the run forever while
            # printing "Decision recorded: APPROVE". Failure mode 11, inside the
            # gate. PATTERN_CATALOG is the next phase, matching what the API
            # approval handler in runtime/api/relay.py sets.
            # (UNIFIED BUILD LIST 1.9)
            conn.execute(
                """UPDATE workflow_runs SET
                       status = 'PATTERN_CATALOG',
                       eric_approved_at = ?,
                       updated_at = ?
                   WHERE id = ?""",
                (now, now, run_id),
            )
        else:
            # Same defect as the APPROVE branch: this cleared the timestamp and
            # left status at ERIC_GATE, so a vetoed run stayed in the gate queue
            # looking like it still needed a decision. Mapped to match the API
            # handler — VETO is its REJECT (ESCALATED), RETURN_TO_DRAFT is its
            # REVISE (DRAFT_PHASE). (UNIFIED BUILD LIST 1.9)
            new_status = ("ESCALATED" if decision == "VETO"
                          else "DRAFT_PHASE")
            conn.execute(
                """UPDATE workflow_runs SET
                       status = ?,
                       eric_approved_at = NULL,
                       updated_at = ?
                   WHERE id = ?""",
                (new_status, now, run_id),
            )

        conn.execute("COMMIT")

        print(f"Decision recorded: {decision}")
        print(f"Approval ID: {approval_id}")
        print(f"Workflow run: {run_id}")
        print(f"Decided at: {now}")
        print(f"Briefing hash: {briefing_hash}")
        if supersedes_id:
            print(f"Superseded: {supersedes_id}")
        if rationale:
            print(f"Rationale: {rationale}")
        if decision == "APPROVE":
            # Print the next command rather than spawning a background thread.
            # The API handler starts one; a one-shot CLI should not, and work
            # the operator can watch beats work that disappears into a daemon.
            print()
            print("Run advanced to PATTERN_CATALOG. It does NOT continue on its")
            print("own from here — run this to carry it through implement and")
            print("verify, and watch the output:")
            print()
            print("  /usr/local/lib/hermes-agent/venv/bin/python \\")
            print("    runtime/abstraction/pipeline_relay.py --resume "
                  f"{run_id}")
        return 0

    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"FAIL [Transaction]: {e}", file=sys.stderr)
        return 1


# ── CLI ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Eric Gate Approval Setter (Component 3)"
    )
    parser.add_argument(
        "--workflow-run-id", required=True,
        help="Workflow run ID to record decision for",
    )
    parser.add_argument(
        "--decision", required=True,
        choices=sorted(ALLOWED_DECISIONS),
        help="Eric's decision",
    )
    parser.add_argument(
        "--briefing-hash", required=True,
        help="SHA256 briefing hash from build_briefing.py",
    )
    parser.add_argument(
        "--goal-reference-id", required=True, type=int,
        help="Goal reference ID from goal_references table",
    )
    parser.add_argument(
        "--rationale", default="",
        help="Eric's plain-language rationale",
    )
    parser.add_argument(
        "--supersede", action="store_true",
        help="Supersede prior current Eric Gate decision",
    )
    parser.add_argument(
        "--db", default=SPINE_PATH,
        help=f"Database path (default: {SPINE_PATH})",
    )

    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    try:
        exit_code = record_decision(
            args.workflow_run_id,
            args.decision,
            args.briefing_hash,
            args.goal_reference_id,
            args.rationale,
            args.supersede,
            conn,
            db_path=args.db,
        )
    finally:
        conn.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
