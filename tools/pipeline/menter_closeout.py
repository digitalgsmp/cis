#!/usr/bin/env python3
"""
menter_closeout.py — R2: the sandbox completion hook.

Transitions MENTER_BUILDING -> MENTER_COMPLETE -> IMPL_REVIEW_PENDING, stores the
build evidence (patch handle, output dir, exit code) into workflow_run_artifacts,
and creates the two implementation-review dispatches (review1 8643 + review2 8647).

Invoked by run_claude_sandbox.sh after the sandbox exits (not by cron/manual).

Usage:
  python3 tools/pipeline/menter_closeout.py --run-id <id> --output-dir <path> --exit-code <n>
"""

import argparse
import hashlib
import json
import os
import sqlite3
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


def patch_hash(output_dir):
    """Hash the coder's changes.patch if present — the evidence handle the
    reviewers and apply gate will re-check."""
    p = os.path.join(output_dir, "changes.patch")
    if os.path.isfile(p):
        return hashlib.sha256(open(p, "rb").read()).hexdigest()
    return ""


def main():
    parser = argparse.ArgumentParser(description="Menter closeout (completion hook)")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--exit-code", type=int, default=0)
    args = parser.parse_args()

    db = get_db()
    run = db.execute("SELECT * FROM workflow_runs WHERE id = ?", (args.run_id,)).fetchone()
    if run is None:
        # Standalone/manual sandbox run with no matching workflow_run — no spine writes.
        print(f"NOTE: no workflow_runs row for {args.run_id} — no spine writes")
        db.close()
        sys.exit(0)

    proposal_id = resolve_proposal_id(args.run_id, db)
    if not proposal_id:
        print(f"REFUSED: no proposal_id for run {args.run_id}", file=sys.stderr)
        db.close()
        sys.exit(1)

    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import get_current_state, transition_state, create_dispatch

    current = get_current_state(proposal_id, db)
    if current != "MENTER_BUILDING":
        print(f"NOTE: current state '{current}', expected MENTER_BUILDING — "
              f"closeout already applied or out of order; no duplicate transition")
        db.close()
        sys.exit(0)

    session_id = resolve_session_id(args.run_id, db)
    ph = patch_hash(args.output_dir)

    # Build evidence (Menter self-report is NOT truth — store the HANDLE only).
    evidence = json.dumps({
        "output_dir": args.output_dir,
        "exit_code": args.exit_code,
        "patch_hash": ph,
        "card_scope": run["card_scope"],
    })
    db.execute(
        "INSERT INTO workflow_run_artifacts (run_id, artifact_type, content) "
        "VALUES (?, 'menter_build_evidence', ?)",
        (args.run_id, evidence))
    db.commit()

    # MENTER_BUILDING -> MENTER_COMPLETE
    r1 = transition_state(
        proposal_id, session_id, "MENTER_BUILDING", "MENTER_COMPLETE",
        "menter_closeout.py", db=db,
        evidence_ref=ph, notes=f"exit_code={args.exit_code}")
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, r1))
    db.commit()

    # MENTER_COMPLETE -> IMPL_REVIEW_PENDING
    r2 = transition_state(
        proposal_id, session_id, "MENTER_COMPLETE", "IMPL_REVIEW_PENDING",
        "menter_closeout.py", db=db,
        evidence_ref=ph)
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? "
        "WHERE id = ? AND workflow_run_id IS NULL",
        (args.run_id, r2))
    db.commit()

    # Two implementation-review dispatches (review1 + review2), carrying the
    # evidence handle, NOT the proposal text (R3).
    review_payload = json.dumps({
        "run_id": args.run_id,
        "patch_hash": ph,
        "output_dir": args.output_dir,
        "evidence_handle": f"workflow_run_artifacts:menter_build_evidence:{args.run_id}",
    })
    for agent, endpoint in (("review1", "http://127.0.0.1:8643"),
                            ("review2", "http://127.0.0.1:8647")):
        did = create_dispatch(
            proposal_id=proposal_id,
            source_actor="menter",
            target_agent=agent,
            target_endpoint=endpoint,
            lifecycle_state_at="IMPL_REVIEW_PENDING",
            payload=review_payload,
            initiated_by="menter_closeout.py",
            eric_approved=1,
            db=db)
        db.execute(
            "UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?",
            (args.run_id, did))
        db.commit()

    print("MENTER CLOSEOUT COMPLETE")
    print(f"workflow_run_id: {args.run_id}")
    print(f"patch_hash: {ph}")
    print("lifecycle: MENTER_BUILDING -> MENTER_COMPLETE -> IMPL_REVIEW_PENDING")

    db.close()


if __name__ == "__main__":
    main()
