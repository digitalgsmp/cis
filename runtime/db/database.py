"""
database.py — CIS SQLite Spine Write/Read Layer
Tier 4.2 — Minimal functions for workflow_runs + deliberation_rounds
"""

import sqlite3
import os
from pathlib import Path


DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
SCHEMA_PATH = "/mnt/projects/cis/runtime/schema/spine_schema.sql"

ALLOWED_RESULTS = {"CONSENSUS_REACHED", "ESCALATE", "ERROR"}
ALLOWED_SIGNALS = {"OBJECTIONS", "CONSENSUS_REACHED", "ESCALATE", "ERROR"}


def init_db(db_path=None):
    """Open (or create) the SQLite database, enable foreign keys, and apply schema if needed."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    # Check if schema already applied
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_runs'"
    )
    if cursor.fetchone() is None:
        schema_sql = Path(SCHEMA_PATH).read_text()
        conn.executescript(schema_sql)
    return conn


def _validate_result(result):
    if result not in ALLOWED_RESULTS:
        raise ValueError(
            f"Invalid result '{result}'. Allowed: {', '.join(sorted(ALLOWED_RESULTS))}"
        )


def _validate_signal(signal):
    if signal not in ALLOWED_SIGNALS:
        raise ValueError(
            f"Invalid signal '{signal}'. Allowed: {', '.join(sorted(ALLOWED_SIGNALS))}"
        )


def _validate_positive_int(value, name):
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer, got {value}")


def _validate_boolean(value, name):
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1, got {value}")


def insert_workflow_run(
    conn,
    id,
    topic,
    result,
    requires_eric_review=1,
    max_rounds=3,
    kanban_card_id=None,
    kanban_board="cis-pipeline",
    max_consecutive_revisions=3,
    rounds_completed=0,
    final_objections_json=None,
    created_at=None,
    completed_at=None,
):
    """Insert one row into workflow_runs."""
    _validate_result(result)
    _validate_positive_int(max_rounds, "max_rounds")
    _validate_positive_int(max_consecutive_revisions, "max_consecutive_revisions")
    _validate_boolean(requires_eric_review, "requires_eric_review")

    from datetime import datetime, timezone

    conn.execute(
        """INSERT INTO workflow_runs
           (id, kanban_card_id, kanban_board, topic, result, requires_eric_review,
            max_rounds, max_consecutive_revisions, rounds_completed,
            final_objections_json, created_at, completed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            id,
            kanban_card_id,
            kanban_board,
            topic,
            result,
            requires_eric_review,
            max_rounds,
            max_consecutive_revisions,
            rounds_completed,
            final_objections_json,
            created_at or datetime.now(timezone.utc).isoformat(),
            completed_at,
        ),
    )


def insert_deliberation_round(
    conn,
    run_id,
    round_number,
    drafter_role,
    drafter_output,
    reviewer_role,
    reviewer_signal,
    objections_json=None,
    revision_number=1,
    requires_eric_review=1,
    created_at=None,
):
    """Insert one row into deliberation_rounds."""
    _validate_signal(reviewer_signal)
    _validate_positive_int(round_number, "round_number")
    _validate_positive_int(revision_number, "revision_number")
    _validate_boolean(requires_eric_review, "requires_eric_review")

    from datetime import datetime, timezone

    conn.execute(
        """INSERT INTO deliberation_rounds
           (run_id, round_number, drafter_role, drafter_output,
            reviewer_role, reviewer_signal, objections_json,
            revision_number, requires_eric_review, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id,
            round_number,
            drafter_role,
            drafter_output,
            reviewer_role,
            reviewer_signal,
            objections_json,
            revision_number,
            requires_eric_review,
            created_at or datetime.now(timezone.utc).isoformat(),
        ),
    )


def get_workflow_run(conn, run_id):
    """Return one workflow_run as a dict, or None."""
    row = conn.execute(
        "SELECT * FROM workflow_runs WHERE id = ?", (run_id,)
    ).fetchone()
    if row is None:
        return None
    cols = [desc[0] for desc in conn.execute("SELECT * FROM workflow_runs LIMIT 0").description]
    return dict(zip(cols, row))


def count_rounds(conn, run_id):
    """Return number of deliberation_rounds for a run_id."""
    row = conn.execute(
        "SELECT COUNT(*) FROM deliberation_rounds WHERE run_id = ?", (run_id,)
    ).fetchone()
    return row[0]
