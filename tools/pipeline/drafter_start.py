#!/usr/bin/env python3
"""
drafter_start.py — Tier 11C: Create workflow_run + proposal, initiate Drafter lifecycle.
ADR-SEED-014 Clause 2 / Choice 1.

Usage:
  python3 tools/pipeline/drafter_start.py "Eric's intent text"
  python3 tools/pipeline/drafter_start.py "intent" --session-id sess-123

Creates: workflow_run_id (run-<hex>), proposal_id (UUID), lifecycle events
         IDLE→ROUTING→DRAFTING. Idempotent by topic hash.
"""

import argparse
import hashlib
import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone


DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
REPO_ROOT = "/mnt/projects/cis"


def get_db():
    """Open CIS spine database with row factory."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def git_head():
    """Return current git HEAD SHA from repo root, or None on failure."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def git_status_porcelain():
    """Return git status --porcelain output, or '' on failure."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def warn_git_state():
    """Print git-state warning to stderr if working tree is not clean."""
    porcelain = git_status_porcelain()
    if porcelain.strip():
        lines = porcelain.strip().split("\n")
        print("WARNING: Git working tree is not clean. "
              "Untracked/dirty files will block closeout.",
              file=sys.stderr)
        print("Dirty/untracked files:", file=sys.stderr)
        for line in lines:
            print(f"  {line}", file=sys.stderr)


def check_idempotent(intent_text, db):
    """Return (workflow_run_id, proposal_id) if active run exists, else (None, None)."""
    row = db.execute(
        """SELECT id FROM workflow_runs
           WHERE topic = ? AND status NOT IN ('COMPLETE', 'ERROR', 'ESCALATE')
           ORDER BY created_at DESC LIMIT 1""",
        (intent_text,)
    ).fetchone()
    if row is None:
        return None, None
    run_id = row["id"]
    # Resolve proposal_id from lifecycle_events
    prop = db.execute(
        """SELECT DISTINCT proposal_id FROM lifecycle_events
           WHERE workflow_run_id = ? ORDER BY id DESC LIMIT 1""",
        (run_id,)
    ).fetchone()
    prop_id = prop["proposal_id"] if prop else None
    return run_id, prop_id


def record_git_head(run_id, head_sha, db):
    """Insert git HEAD into workflow_run_artifacts."""
    if head_sha:
        db.execute(
            """INSERT INTO workflow_run_artifacts
               (run_id, artifact_type, content, created_at)
               VALUES (?, 'git_head', ?, ?)""",
            (run_id, head_sha, datetime.now(timezone.utc).isoformat())
        )


def main():
    parser = argparse.ArgumentParser(
        description="CIS Tier 11C — Drafter workflow initiation"
    )
    parser.add_argument(
        "intent_text", nargs="?", default=None,
        help="Eric's stated initiating intent (or read from stdin if omitted)"
    )
    parser.add_argument(
        "--session-id", default=None,
        help="Session identifier for lifecycle_events.session_id"
    )
    args = parser.parse_args()

    # Resolve intent text
    if args.intent_text:
        intent = args.intent_text.strip()
    elif not sys.stdin.isatty():
        intent = sys.stdin.read().strip()
    else:
        print("ERROR: No intent text provided.", file=sys.stderr)
        sys.exit(1)

    if not intent:
        print("ERROR: Intent text must be non-empty.", file=sys.stderr)
        sys.exit(1)

    intent_hash = hashlib.sha256(intent.encode("utf-8")).hexdigest()
    session_id = args.session_id or datetime.now(timezone.utc).isoformat()

    db = get_db()

    # --- Idempotency check ---
    existing_run, existing_prop = check_idempotent(intent, db)
    if existing_run:
        print(f"EXISTING workflow_run_id={existing_run} proposal_id={existing_prop}")
        db.close()
        sys.exit(0)

    # --- Create identities ---
    workflow_run_id = f"run-{uuid.uuid4().hex[:13]}"
    proposal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # --- Insert workflow_runs row ---
    db.execute(
        """INSERT INTO workflow_runs
           (id, topic, result, requires_eric_review, max_rounds,
            max_consecutive_revisions, rounds_completed, created_at, status)
           VALUES (?, ?, 'CONSENSUS_REACHED', 1, 3, 3, 0, ?, 'PENDING')""",
        (workflow_run_id, intent, now)
    )

    # --- Import orchestration module ---
    sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
    from api.orchestration import transition_state

    # --- Write lifecycle events ---
    row1_id = transition_state(
        proposal_id, session_id, "IDLE", "ROUTING",
        "drafter_start.py", db=db
    )
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? WHERE id = ? AND workflow_run_id IS NULL",
        (workflow_run_id, row1_id)
    )

    row2_id = transition_state(
        proposal_id, session_id, "ROUTING", "DRAFTING",
        "drafter_start.py", db=db
    )
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? WHERE id = ? AND workflow_run_id IS NULL",
        (workflow_run_id, row2_id)
    )

    # --- Record git HEAD ---
    head = git_head()
    record_git_head(workflow_run_id, head, db)
    # Record intent hash for downstream verification
    db.execute(
        """INSERT INTO workflow_run_artifacts
           (run_id, artifact_type, content, created_at)
           VALUES (?, 'intent_hash', ?, ?)""",
        (workflow_run_id, intent_hash, now)
    )
    db.commit()

    # --- Git-state warning ---
    warn_git_state()

    # --- Output ---
    print(f"workflow_run_id: {workflow_run_id}")
    print(f"proposal_id: {proposal_id}")
    print(f"intent_hash: {intent_hash}")
    print(f"git_head: {head}")

    db.close()


if __name__ == "__main__":
    main()
