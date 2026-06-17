#!/usr/bin/env python3
"""
reviewer_closeout.py — Tier 11D: Validate Reviewer FINAL_JSON, write
REVIEWING → REVIEW_COMPLETE, route to REVISE_REQUESTED or ERIC_APPROVAL_GATE.

ADR-SEED-012 (Orchestrator Validation Contract — Reviewer contract).
ADR-SEED-014 Clause 6.

Usage:
  python3 tools/pipeline/reviewer_closeout.py --run-id <id> < review_output.txt
  python3 tools/pipeline/reviewer_closeout.py --run-id <id> --reviewer-output-file output.txt
  python3 tools/pipeline/reviewer_closeout.py --run-id <id> --proposal-id <uuid> < output.txt
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone


DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
REPO_ROOT = "/mnt/projects/cis"

VALID_REVIEWER_STATUSES = {"CONSENSUS_REACHED", "OBJECTIONS", "ESCALATE"}
VALID_NEXT_ACTIONS = {"ERIC_APPROVAL_GATE", "REVISE_REQUESTED", "IDLE"}
TERMINAL_STATUSES = {"COMPLETE", "ERROR", "ESCALATE"}


def get_db():
    """Open CIS spine database with row factory."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


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


def extract_final_json(text):
    """Extract FINAL_JSON block from Reviewer output.

    Strategy 1: Markdown code fence with ```json ... ``` containing valid JSON.
    Strategy 2: Raw JSON object at end of text (last { ... } on own lines).
    """
    # Strategy 1: fenced JSON block
    fence_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 2: raw JSON object at end
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped.startswith("{"):
            candidate = "\n".join(lines[i:])
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
            break

    return None


def check_review_complete_exists(proposal_id, db):
    """Check if REVIEW_COMPLETE already recorded for this proposal."""
    row = db.execute(
        "SELECT COUNT(*) as cnt FROM lifecycle_events "
        "WHERE proposal_id = ? AND to_state = 'REVIEW_COMPLETE'",
        (proposal_id,)
    ).fetchone()
    return row["cnt"] > 0


def get_drafter_dispatch(run_id, db):
    """Get the drafter→reviewer dispatch for this run."""
    return db.execute(
        "SELECT * FROM dispatch_log "
        "WHERE workflow_run_id = ? AND source_actor = 'drafter' "
        "ORDER BY timestamp_initiated DESC LIMIT 1",
        (run_id,)
    ).fetchone()


def main():
    parser = argparse.ArgumentParser(
        description="CIS Tier 11D — Reviewer closeout"
    )
    parser.add_argument("--run-id", required=True, help="Workflow run ID")
    parser.add_argument("--proposal-id", default=None, help="Proposal ID (resolved if omitted)")
    parser.add_argument("--reviewer-output-file", default=None,
                        help="File with Reviewer output")
    parser.add_argument("--session-id", default=None, help="Session identifier")
    args = parser.parse_args()

    # --- Read Reviewer output ---
    if args.reviewer_output_file:
        with open(args.reviewer_output_file) as f:
            reviewer_output = f.read()
    else:
        reviewer_output = sys.stdin.read()

    if not reviewer_output.strip():
        print("REFUSED: Empty Reviewer output.", file=sys.stderr)
        sys.exit(1)

    db = get_db()
    run_id = args.run_id

    # --- Load workflow_run ---
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
    if run is None:
        print(f"REFUSED: Workflow run not found: {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    if run["status"] in TERMINAL_STATUSES:
        print(f"REFUSED: Workflow run is in terminal status: {run['status']}",
              file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Resolve proposal_id ---
    proposal_id = args.proposal_id or resolve_proposal_id(run_id, db)
    if not proposal_id:
        print(f"REFUSED: No proposal_id found for run {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Verify current lifecycle state is REVIEWING ---
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import (
        get_current_state, transition_state,
        create_dispatch, update_dispatch_inflight, complete_dispatch
    )

    current_state = get_current_state(proposal_id, db)
    if current_state != "REVIEWING":
        print(f"REFUSED: Current lifecycle state is '{current_state}', "
              f"expected 'REVIEWING'.", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Idempotency check ---
    if check_review_complete_exists(proposal_id, db):
        print("REFUSED: REVIEW_COMPLETE already recorded. Closeout is idempotent.",
              file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Git-state enforcement ---
    porcelain = git_status_porcelain()
    untracked = [l for l in porcelain.split("\n") if l.startswith("??")]
    dirty_tracked = [l for l in porcelain.split("\n")
                     if l.startswith(" M") or l.startswith("M ")]

    if untracked:
        print("REFUSED: Untracked files exist. Closeout requires clean working tree.",
              file=sys.stderr)
        for f in untracked:
            if f.strip():
                print(f"  {f}", file=sys.stderr)
        db.close()
        sys.exit(1)

    if dirty_tracked:
        print("WARNING: Dirty tracked files exist.", file=sys.stderr)
        for f in dirty_tracked:
            if f.strip():
                print(f"  {f}", file=sys.stderr)

    # --- Extract and validate FINAL_JSON ---
    final_json = extract_final_json(reviewer_output)
    if final_json is None:
        print("REFUSED: No valid FINAL_JSON block found in Reviewer output.",
              file=sys.stderr)
        db.close()
        sys.exit(1)

    role = final_json.get("role", "")
    status = final_json.get("status", "")

    if role != "reviewer" or status not in VALID_REVIEWER_STATUSES:
        print(f"REFUSED: FINAL_JSON role must be \"reviewer\", "
              f"status must be CONSENSUS_REACHED|OBJECTIONS|ESCALATE. "
              f"Got role={role!r}, status={status!r}.",
              file=sys.stderr)
        db.close()
        sys.exit(1)

    # Optional field validation
    summary = final_json.get("summary", "")
    if summary and len(summary) > 500:
        summary = summary[:500]

    recommendation = final_json.get("recommendation", "")
    if recommendation and len(recommendation) > 500:
        recommendation = recommendation[:500]

    next_action = final_json.get("next_action")
    if next_action and next_action not in VALID_NEXT_ACTIONS:
        print(f"WARNING: next_action '{next_action}' not in {VALID_NEXT_ACTIONS}. Ignoring.",
              file=sys.stderr)

    # Warn if next_action conflicts with status (status is authoritative)
    if next_action and status == "CONSENSUS_REACHED" and next_action != "ERIC_APPROVAL_GATE":
        print(f"WARNING: next_action '{next_action}' conflicts with CONSENSUS_REACHED status. "
              f"Status is authoritative.", file=sys.stderr)
    if next_action and status == "ESCALATE" and next_action != "ERIC_APPROVAL_GATE":
        print(f"WARNING: next_action '{next_action}' conflicts with ESCALATE status. "
              f"Status is authoritative.", file=sys.stderr)

    # --- Hash Reviewer output ---
    reviewer_output_hash = hashlib.sha256(reviewer_output.encode("utf-8")).hexdigest()

    # --- Resolve session_id ---
    session_id = resolve_session_id(run_id, args.session_id, db)

    # --- Determine verdict routing ---
    escalation_forced = False

    if status == "OBJECTIONS":
        # Check if max revision rounds reached
        rounds_completed = run["rounds_completed"] or 0
        max_revisions = run["max_consecutive_revisions"] or 3
        if rounds_completed >= max_revisions:
            print(f"WARNING: Max revision rounds reached "
                  f"({rounds_completed}/{max_revisions}). Forcing ESCALATE routing.",
                  file=sys.stderr)
            escalation_forced = True
            routing = "ERIC_APPROVAL_GATE"
        else:
            routing = "REVISE_REQUESTED"
    elif status == "CONSENSUS_REACHED":
        routing = "ERIC_APPROVAL_GATE"
    elif status == "ESCALATE":
        routing = "ERIC_APPROVAL_GATE"
    else:
        # Should never reach here due to earlier validation
        print(f"REFUSED: Unknown status: {status}", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Write lifecycle event: REVIEWING → REVIEW_COMPLETE ---
    review_complete_row_id = transition_state(
        proposal_id, session_id,
        "REVIEWING", "REVIEW_COMPLETE",
        "reviewer_closeout.py", db=db,
        notes=f"Reviewer output hash: {reviewer_output_hash}")
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (run_id, review_complete_row_id))
    db.commit()

    # --- Record deliberation round ---
    # Get drafter output hash from the drafter dispatch
    drafter_dispatch = get_drafter_dispatch(run_id, db)
    drafter_output_hash = drafter_dispatch["payload_hash"] if drafter_dispatch else ""

    new_round_number = (run["rounds_completed"] or 0) + 1
    objections_json = None
    if status == "OBJECTIONS":
        objections_list = final_json.get("objections", [])
        if objections_list:
            objections_json = json.dumps(objections_list)

    db.execute(
        """INSERT INTO deliberation_rounds
           (run_id, round_number, drafter_role, drafter_output,
            reviewer_role, reviewer_signal, objections_json,
            revision_number, requires_eric_review, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, new_round_number, "drafter", drafter_output_hash,
         "reviewer", status, objections_json,
         new_round_number, 1 if status == "ESCALATE" else 0,
         datetime.now(timezone.utc).isoformat()))

    # --- Write verdict routing lifecycle event ---
    verdict_notes = f"Reviewer verdict: {status}"
    if escalation_forced:
        verdict_notes += " (MAX_ROUNDS_EXCEEDED — forced escalation)"

    verdict_row_id = transition_state(
        proposal_id, session_id,
        "REVIEW_COMPLETE", routing,
        "reviewer_closeout.py", db=db,
        notes=verdict_notes)
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (run_id, verdict_row_id))
    db.commit()

    # --- Update workflow_runs ---
    now = datetime.now(timezone.utc).isoformat()
    new_rounds_completed = (run["rounds_completed"] or 0) + 1

    # Determine status for workflow_runs
    if routing == "REVISE_REQUESTED":
        wf_status = "REVISE_REQUESTED"
    elif status == "CONSENSUS_REACHED":
        wf_status = "CONSENSUS_REACHED"
    else:  # ESCALATE
        wf_status = "ESCALATE"

    # M1: result field — only updated for terminal verdicts.
    # REVISE_REQUESTED (OBJECTIONS with rounds remaining) is not terminal;
    # the existing result stays unchanged until a final verdict is reached.
    # CHECK constraint on result: IN ('CONSENSUS_REACHED', 'ESCALATE', 'ERROR')
    if status == "CONSENSUS_REACHED":
        db.execute(
            """UPDATE workflow_runs
               SET status = ?, result = 'CONSENSUS_REACHED', rounds_completed = ?,
                   updated_at = ?
               WHERE id = ?""",
            (wf_status, new_rounds_completed, now, run_id))
    elif status == "ESCALATE" or escalation_forced:
        db.execute(
            """UPDATE workflow_runs
               SET status = ?, result = 'ESCALATE', rounds_completed = ?,
                   updated_at = ?
               WHERE id = ?""",
            (wf_status, new_rounds_completed, now, run_id))
    else:  # OBJECTIONS with rounds remaining — result is NOT final, leave unchanged
        db.execute(
            """UPDATE workflow_runs
               SET status = ?, rounds_completed = ?,
                   updated_at = ?
               WHERE id = ?""",
            (wf_status, new_rounds_completed, now, run_id))
    db.commit()

    # --- Update dispatch log: mark drafter dispatch as SUCCESS ---
    drafter_dispatch = get_drafter_dispatch(run_id, db)
    if drafter_dispatch:
        complete_dispatch(
            drafter_dispatch["dispatch_id"],
            http_status_code=0,
            response_body=reviewer_output,
            db=db)

    # --- If REVISE_REQUESTED, create return dispatch to Drafter ---
    return_dispatch_id = None
    if routing == "REVISE_REQUESTED":
        return_dispatch_id = create_dispatch(
            proposal_id=proposal_id,
            source_actor="reviewer",
            target_agent="hermes-v4pro",
            target_endpoint="http://127.0.0.1:8645",
            lifecycle_state_at="REVISE_REQUESTED",
            payload=reviewer_output,
            initiated_by="reviewer_closeout.py",
            eric_approved=0,
            db=db)
        db.execute(
            "UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?",
            (run_id, return_dispatch_id))
        db.commit()

    # --- Output ---
    print("REVIEWER CLOSEOUT COMPLETE")
    print(f"workflow_run_id: {run_id}")
    print(f"proposal_id: {proposal_id}")
    print(f"verdict: {status}")
    print(f"routing: {routing}")
    print(f"reviewer_output_hash: {reviewer_output_hash}")
    if routing == "REVISE_REQUESTED" and return_dispatch_id:
        print(f"return_dispatch_id: {return_dispatch_id}")
        print("next_action: Drafter (hermes-v4pro:8645) should pick up revision dispatch")

    db.close()


if __name__ == "__main__":
    main()
