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
ALLOWED_DECISION_STATUSES = {"DECIDED", "OPEN", "SUPERSEDED"}
ALLOWED_QUESTION_STATUSES = {"OPEN", "RESOLVED", "DEFERRED"}
ALLOWED_ACTION_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETE", "BLOCKED", "DEFERRED"}
ALLOWED_BLOCKER_STATUSES = {"ACTIVE", "RESOLVED"}
ALLOWED_STATE_SOURCES = {"git", "gate", "manual"}


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
    # Apply Tier 4.4 migration if not yet applied
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='project_decisions'"
    )
    if cursor.fetchone() is None:
        migration_path = Path(SCHEMA_PATH).parent / "migrations" / "0001_context_export_state.sql"
        conn.executescript(migration_path.read_text())
    # Apply Tier 6.5 remediation migration if not yet applied (project_state table)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='project_state'"
    )
    if cursor.fetchone() is None:
        migration_path = Path(SCHEMA_PATH).parent / "migrations" / "0002_project_state.sql"
        conn.executescript(migration_path.read_text())
    # Apply Tier 7.5b DAM migration if not yet applied (dam_assets + FTS5)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='dam_assets'"
    )
    if cursor.fetchone() is None:
        migration_path = Path(SCHEMA_PATH).parent / "migrations" / "0003_dam.sql"
        conn.executescript(migration_path.read_text())
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
           (id, topic, result, requires_eric_review,
            max_rounds, max_consecutive_revisions, rounds_completed,
            final_objections_json, created_at, completed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            id,
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


def insert_project_decision(conn, id, label, decision, reason=None, status="DECIDED", decided_at=None, superseded_by=None):
    if status not in ALLOWED_DECISION_STATUSES:
        raise ValueError(f"Invalid status '{status}'.")
    from datetime import datetime, timezone
    conn.execute(
        """INSERT INTO project_decisions
           (id, label, decision, reason, status, decided_at, superseded_by)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (id, label, decision, reason, status, decided_at or datetime.now(timezone.utc).isoformat(), superseded_by),
    )


def insert_open_question(conn, id, question, status="OPEN", resolution=None, opened_at=None, resolved_at=None):
    if status not in ALLOWED_QUESTION_STATUSES:
        raise ValueError(f"Invalid status '{status}'.")
    from datetime import datetime, timezone
    conn.execute(
        """INSERT INTO open_questions
           (id, question, status, resolution, opened_at, resolved_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (id, question, status, resolution, opened_at or datetime.now(timezone.utc).isoformat(), resolved_at),
    )


def insert_next_action(conn, id, description, tier=None, status="PENDING", depends_on=None, created_at=None, updated_at=None):
    if status not in ALLOWED_ACTION_STATUSES:
        raise ValueError(f"Invalid status '{status}'.")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO next_actions
           (id, tier, description, status, depends_on, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (id, tier, description, status, depends_on, created_at or now, updated_at or now),
    )


def insert_active_blocker(conn, id, description, status="ACTIVE", resolution=None, created_at=None, resolved_at=None):
    if status not in ALLOWED_BLOCKER_STATUSES:
        raise ValueError(f"Invalid status '{status}'.")
    from datetime import datetime, timezone
    conn.execute(
        """INSERT INTO active_blockers
           (id, description, status, resolution, created_at, resolved_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (id, description, status, resolution, created_at or datetime.now(timezone.utc).isoformat(), resolved_at),
    )


def insert_project_state(conn, key, value, source, evidence_hash=None, evidence_run_id=None, created_at=None):
    """Insert one row into project_state (append-only)."""
    if source not in ALLOWED_STATE_SOURCES:
        raise ValueError(f"Invalid source '{source}'. Allowed: {', '.join(sorted(ALLOWED_STATE_SOURCES))}")
    from datetime import datetime, timezone
    conn.execute(
        """INSERT INTO project_state
           (key, value, source, evidence_hash, evidence_run_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (key, value, source, evidence_hash, evidence_run_id,
         created_at or datetime.now(timezone.utc).isoformat()),
    )


def get_project_state(conn):
    """Return current project state as {key: value} dict. Only newest unsuperseded row per key."""
    rows = conn.execute(
        """SELECT key, value FROM project_state
           WHERE superseded_at IS NULL
           AND id = (
               SELECT MAX(id) FROM project_state ps2
               WHERE ps2.key = project_state.key AND ps2.superseded_at IS NULL
           )"""
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def supersede_project_state(conn, key, superseded_by_id):
    """Mark all current rows for a key as superseded."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE project_state SET superseded_at = ?, superseded_by = ?
           WHERE key = ? AND superseded_at IS NULL""",
        (now, superseded_by_id, key),
    )
