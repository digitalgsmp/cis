#!/usr/bin/env python3
"""
drafter_closeout.py — Tier 11C: Validate FINAL_JSON, write DRAFT_READY→REVIEW_PENDING,
create dispatch to Reviewer.
ADR-SEED-014 Clause 6 / Implementation Consequence.

Usage:
  python3 tools/pipeline/drafter_closeout.py --run-id <id> < proposal_output.txt
  python3 tools/pipeline/drafter_closeout.py --run-id <id> --drafter-output-file proposal.txt
  python3 tools/pipeline/drafter_closeout.py --run-id <id> --proposal-id <uuid> < proposal.txt
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

VALID_NEXT_ACTIONS = {"REVIEW_PENDING", "REVISION_READY", "IDLE"}
TERMINAL_STATUSES = {"COMPLETE", "ERROR", "ESCALATE"}


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


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
    """Extract FINAL_JSON block from Drafter output.

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
    # Find the last { that starts a line and matching }
    lines = text.split("\n")
    # Walk backwards to find a line that is just "{" or starts with "{" at end
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if stripped.startswith("{"):
            # Take from here to end
            candidate = "\n".join(lines[i:])
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
            break

    return None


def check_draft_ready_exists(proposal_id, db):
    row = db.execute(
        "SELECT COUNT(*) as cnt FROM lifecycle_events "
        "WHERE proposal_id = ? AND to_state = 'DRAFT_READY'",
        (proposal_id,)
    ).fetchone()
    return row["cnt"] > 0


def main():
    parser = argparse.ArgumentParser(
        description="CIS Tier 11C — Drafter closeout"
    )
    parser.add_argument("--run-id", required=True, help="Workflow run ID")
    parser.add_argument("--proposal-id", default=None, help="Proposal ID (resolved if omitted)")
    parser.add_argument("--drafter-output-file", default=None, help="File with Drafter output")
    parser.add_argument("--session-id", default=None, help="Session identifier")
    args = parser.parse_args()

    # --- Read Drafter output ---
    if args.drafter_output_file:
        with open(args.drafter_output_file) as f:
            drafter_output = f.read()
    else:
        drafter_output = sys.stdin.read()

    if not drafter_output.strip():
        print("REFUSED: Empty Drafter output.", file=sys.stderr)
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
        print(f"REFUSED: Workflow run is in terminal status: {run['status']}", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Resolve proposal_id ---
    proposal_id = args.proposal_id or resolve_proposal_id(run_id, db)
    if not proposal_id:
        print(f"REFUSED: No proposal_id found for run {run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Git-state enforcement (ADR-014 Choice 5) ---
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
    final_json = extract_final_json(drafter_output)
    if final_json is None:
        print("REFUSED: No valid FINAL_JSON block found in Drafter output.",
              file=sys.stderr)
        db.close()
        sys.exit(1)

    role = final_json.get("role", "")
    status = final_json.get("status", "")

    if role != "drafter" or status != "PROPOSAL_READY":
        print(f"REFUSED: FINAL_JSON role must be 'drafter', status must be "
              f"'PROPOSAL_READY'. Got role={role!r}, status={status!r}.",
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
        print(f"REFUSED: next_action must be one of {VALID_NEXT_ACTIONS}, "
              f"got {next_action!r}.", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Verify state machine position ---
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import get_current_state, transition_state, create_dispatch

    current_state = get_current_state(proposal_id, db)
    if current_state != "DRAFTING":
        print(f"REFUSED: Current lifecycle state is '{current_state}', "
              f"expected 'DRAFTING'.", file=sys.stderr)
        db.close()
        sys.exit(1)

    # Idempotency check
    if check_draft_ready_exists(proposal_id, db):
        print("REFUSED: DRAFT_READY already recorded for this proposal. "
              "Closeout is idempotent — cannot close twice.", file=sys.stderr)
        db.close()
        sys.exit(1)

    # --- Hash Drafter output ---
    output_hash = hashlib.sha256(drafter_output.encode("utf-8")).hexdigest()

    # --- Resolve session_id ---
    session_id = resolve_session_id(run_id, args.session_id, db)

    # --- Write DRAFTING → DRAFT_READY ---
    draft_ready_row_id = transition_state(
        proposal_id, session_id, "DRAFTING", "DRAFT_READY",
        "drafter_closeout.py", db=db,
        notes="Drafter output hash: " + output_hash
    )
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (run_id, draft_ready_row_id)
    )

    # --- Create dispatch to Reviewer ---
    dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor="drafter",
        target_agent="hermes-r1",
        target_endpoint="http://127.0.0.1:8643",
        lifecycle_state_at="DRAFT_READY",
        payload=drafter_output,
        initiated_by="drafter_closeout.py",
        eric_approved=0,
        db=db
    )
    db.execute(
        "UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?",
        (run_id, dispatch_id)
    )

    # --- Write DRAFT_READY → REVIEW_PENDING ---
    review_pending_row_id = transition_state(
        proposal_id, session_id, "DRAFT_READY", "REVIEW_PENDING",
        "drafter_closeout.py", db=db, dispatch_ref=dispatch_id
    )
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (run_id, review_pending_row_id)
    )

    # --- Update workflow_runs status ---
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        "UPDATE workflow_runs SET status = 'REVIEW_PENDING', updated_at = ? WHERE id = ?",
        (now, run_id)
    )
    db.commit()

    # --- Output ---
    print("CLOSEOUT COMPLETE")
    print(f"workflow_run_id: {run_id}")
    print(f"proposal_id: {proposal_id}")
    print(f"dispatch_id: {dispatch_id}")
    print(f"drafter_output_hash: {output_hash}")
    print("lifecycle_state: REVIEW_PENDING")
    print("target: hermes-r1 (port 8643)")

    db.close()


if __name__ == "__main__":
    main()
