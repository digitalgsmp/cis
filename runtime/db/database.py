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

# Component 2 — Escalation Advisor Integration Protocol allowlists
ALLOWED_TRIGGER_CLASSES = {"DISCRETIONARY", "MANDATORY"}
ALLOWED_ESCALATION_STATUSES = {
    "OPEN", "PACKET_BUILT", "TRANSMITTED", "RESPONSES_COMPLETE",
    "RECONCILED", "ABANDONED", "SUPERSEDED", "CANCELLED_BY_ERIC"
}
ALLOWED_RECONCILIATION_DISPOSITIONS = {
    "ACCEPT", "ACCEPT_WITH_MODIFICATION", "REJECT",
    "RETURN_TO_DRAFT", "ESCALATE_FURTHER"
}
ALLOWED_ADVISOR_TARGETS = {"CLAUDE", "CHATGPT", "BOTH"}
ALLOWED_RESPONSE_TYPES = {"AUDIT", "PROPOSAL_REVIEW", "RISK_ASSESSMENT", "DESIGN_INPUT"}
ALLOWED_PACKET_STATUSES = {"PACKET_BUILT", "TRANSMITTED"}
ALLOWED_ADVISORS = {"CLAUDE", "CHATGPT"}
ALLOWED_TRANSMISSION_MODES = {"MANUAL_PASTE", "API"}
ALLOWED_PRIMARY_TYPES = {
    "AUDIT_PASS", "AUDIT_OBJECTION", "PROPOSAL",
    "CLARIFICATION_REQUEST", "RISK_FLAG", "RECOMMENDATION"
}
ALLOWED_CLASSIFICATION_SOURCES = {"ERIC", "TOOL", "HERMES_ASSISTED"}
ALLOWED_CLASSIFICATION_STATUSES = {"PROPOSED", "CONFIRMED", "CORRECTED"}
ALLOWED_RESPONSE_STATUSES = {"EXPECTED", "TRANSMITTED", "RECEIVED", "INGESTED", "CLASSIFIED"}
ALLOWED_HASH_MATCH_STATUSES = {"MATCH", "MISMATCH"}


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
    # Apply Foundation Hardening Component 1 migration if not yet applied (provenance lifecycle schema)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='goal_references'"
    )
    if cursor.fetchone() is None:
        migration_path = Path(SCHEMA_PATH).parent / "migrations" / "0008_provenance_lifecycle_base.sql"
        conn.executescript(migration_path.read_text())
    # Apply Foundation Hardening Component 2 migration if not yet applied (advisor escalation protocol)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='advisor_escalations'"
    )
    if cursor.fetchone() is None:
        migration_path = Path(SCHEMA_PATH).parent / "migrations" / "0009_advisor_escalation_protocol.sql"
        conn.executescript(migration_path.read_text())
    # Apply Foundation Hardening Component 3.5 migration if not yet applied (build plan spine)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='build_plan_nodes'"
    )
    if cursor.fetchone() is None:
        migration_path = Path(SCHEMA_PATH).parent / "migrations" / "0011_build_plan_spine.sql"
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


# ── Component 2 — Advisor Escalation Protocol helpers ──────────────

def insert_advisor_escalation(conn, trigger_class, trigger_reason, escalation_scope,
                              workflow_run_id=None, created_at=None):
    """Insert one row into advisor_escalations. Returns the new row id."""
    if trigger_class not in ALLOWED_TRIGGER_CLASSES:
        raise ValueError(
            f"Invalid trigger_class '{trigger_class}'. Allowed: {sorted(ALLOWED_TRIGGER_CLASSES)}")
    from datetime import datetime, timezone
    cur = conn.execute(
        """INSERT INTO advisor_escalations
           (workflow_run_id, trigger_class, trigger_reason, escalation_scope, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (workflow_run_id, trigger_class, trigger_reason, escalation_scope,
         created_at or datetime.now(timezone.utc).isoformat()),
    )
    return cur.lastrowid


def update_escalation_status(conn, escalation_id, new_status):
    """Update escalation status with validation."""
    if new_status not in ALLOWED_ESCALATION_STATUSES:
        raise ValueError(
            f"Invalid escalation status '{new_status}'. Allowed: {sorted(ALLOWED_ESCALATION_STATUSES)}")
    conn.execute(
        "UPDATE advisor_escalations SET status = ? WHERE id = ?",
        (new_status, escalation_id),
    )


def get_escalation(conn, escalation_id):
    """Return one advisor_escalation row as dict, or None."""
    row = conn.execute(
        "SELECT * FROM advisor_escalations WHERE id = ?", (escalation_id,)
    ).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM advisor_escalations LIMIT 0").description]
    return dict(zip(cols, row))


def insert_escalation_packet(conn, escalation_id, packet_version, packet_raw,
                              packet_hash, git_head, advisor_target,
                              requested_response_type, packet_status="PACKET_BUILT",
                              created_at=None, transmitted_at=None):
    """Insert one row into advisor_escalation_packets. Returns the new row id."""
    if advisor_target not in ALLOWED_ADVISOR_TARGETS:
        raise ValueError(
            f"Invalid advisor_target '{advisor_target}'. Allowed: {sorted(ALLOWED_ADVISOR_TARGETS)}")
    if requested_response_type not in ALLOWED_RESPONSE_TYPES:
        raise ValueError(
            f"Invalid requested_response_type '{requested_response_type}'. Allowed: {sorted(ALLOWED_RESPONSE_TYPES)}")
    if packet_status not in ALLOWED_PACKET_STATUSES:
        raise ValueError(
            f"Invalid packet_status '{packet_status}'. Allowed: {sorted(ALLOWED_PACKET_STATUSES)}")
    from datetime import datetime, timezone
    cur = conn.execute(
        """INSERT INTO advisor_escalation_packets
           (escalation_id, packet_version, packet_raw, packet_hash, git_head,
            advisor_target, requested_response_type, packet_status, created_at, transmitted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (escalation_id, packet_version, packet_raw, packet_hash, git_head,
         advisor_target, requested_response_type, packet_status,
         created_at or datetime.now(timezone.utc).isoformat(), transmitted_at),
    )
    return cur.lastrowid


def get_packet(conn, packet_id):
    """Return one advisor_escalation_packets row as dict, or None."""
    row = conn.execute(
        "SELECT * FROM advisor_escalation_packets WHERE id = ?", (packet_id,)
    ).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM advisor_escalation_packets LIMIT 0").description]
    return dict(zip(cols, row))


def get_latest_packet_version(conn, escalation_id):
    """Return the highest packet_version for an escalation, or 0."""
    row = conn.execute(
        "SELECT COALESCE(MAX(packet_version), 0) FROM advisor_escalation_packets WHERE escalation_id = ?",
        (escalation_id,),
    ).fetchone()
    return row[0]


def insert_advisor_response(conn, escalation_id, packet_id, advisor,
                             response_raw=None, responded_packet_hash=None,
                             hash_match_status=None,
                             primary_type=None, secondary_flags=None,
                             classification_source=None, classification_status=None,
                             response_status="EXPECTED",
                             transmission_mode="MANUAL_PASTE",
                             received_at=None, ingested_at=None):
    """Insert one row into advisor_responses. Returns the new row id."""
    if advisor not in ALLOWED_ADVISORS:
        raise ValueError(
            f"Invalid advisor '{advisor}'. Allowed: {sorted(ALLOWED_ADVISORS)}")
    if transmission_mode not in ALLOWED_TRANSMISSION_MODES:
        raise ValueError(
            f"Invalid transmission_mode '{transmission_mode}'. Allowed: {sorted(ALLOWED_TRANSMISSION_MODES)}")
    if response_status not in ALLOWED_RESPONSE_STATUSES:
        raise ValueError(
            f"Invalid response_status '{response_status}'. Allowed: {sorted(ALLOWED_RESPONSE_STATUSES)}")
    if primary_type is not None and primary_type not in ALLOWED_PRIMARY_TYPES:
        raise ValueError(
            f"Invalid primary_type '{primary_type}'. Allowed: {sorted(ALLOWED_PRIMARY_TYPES)}")
    if classification_source is not None and classification_source not in ALLOWED_CLASSIFICATION_SOURCES:
        raise ValueError(
            f"Invalid classification_source '{classification_source}'. Allowed: {sorted(ALLOWED_CLASSIFICATION_SOURCES)}")
    if classification_status is not None and classification_status not in ALLOWED_CLASSIFICATION_STATUSES:
        raise ValueError(
            f"Invalid classification_status '{classification_status}'. Allowed: {sorted(ALLOWED_CLASSIFICATION_STATUSES)}")
    if hash_match_status is not None and hash_match_status not in ALLOWED_HASH_MATCH_STATUSES:
        raise ValueError(
            f"Invalid hash_match_status '{hash_match_status}'. Allowed: {sorted(ALLOWED_HASH_MATCH_STATUSES)}")
    cur = conn.execute(
        """INSERT INTO advisor_responses
           (escalation_id, packet_id, advisor, transmission_mode,
            response_raw, responded_packet_hash, hash_match_status,
            primary_type, secondary_flags,
            classification_source, classification_status,
            response_status, received_at, ingested_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (escalation_id, packet_id, advisor, transmission_mode,
         response_raw, responded_packet_hash, hash_match_status,
         primary_type, secondary_flags,
         classification_source, classification_status,
         response_status, received_at, ingested_at),
    )
    return cur.lastrowid


def update_response_status(conn, response_id, new_status, extra_fields=None):
    """Update response_status. Optionally set additional fields via dict."""
    if new_status not in ALLOWED_RESPONSE_STATUSES:
        raise ValueError(
            f"Invalid response_status '{new_status}'. Allowed: {sorted(ALLOWED_RESPONSE_STATUSES)}")
    sets = ["response_status = ?"]
    params = [new_status]
    if extra_fields:
        for col, val in extra_fields.items():
            sets.append(f"{col} = ?")
            params.append(val)
    params.append(response_id)
    conn.execute(
        f"UPDATE advisor_responses SET {', '.join(sets)} WHERE id = ?",
        params,
    )


def get_response(conn, response_id):
    """Return one advisor_responses row as dict, or None."""
    row = conn.execute(
        "SELECT * FROM advisor_responses WHERE id = ?", (response_id,)
    ).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM advisor_responses LIMIT 0").description]
    return dict(zip(cols, row))


def get_escalation_responses(conn, escalation_id):
    """Return all advisor_responses rows for an escalation as list of dicts."""
    rows = conn.execute(
        "SELECT * FROM advisor_responses WHERE escalation_id = ? ORDER BY id",
        (escalation_id,),
    ).fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM advisor_responses LIMIT 0").description]
    return [dict(zip(cols, r)) for r in rows]


def record_reconciliation(conn, escalation_id, disposition, note,
                           divergence_summary=None, positions_json=None,
                           reconciled_at=None):
    """Record Eric's reconciliation on an escalation."""
    if disposition not in ALLOWED_RECONCILIATION_DISPOSITIONS:
        raise ValueError(
            f"Invalid reconciliation_disposition '{disposition}'. Allowed: {sorted(ALLOWED_RECONCILIATION_DISPOSITIONS)}")
    from datetime import datetime, timezone
    conn.execute(
        """UPDATE advisor_escalations SET
               status = 'RECONCILED',
               reconciliation_disposition = ?,
               reconciliation_note = ?,
               advisor_divergence_summary = ?,
               advisor_positions_json = ?,
               reconciled_at = ?
           WHERE id = ?""",
        (disposition, note, divergence_summary, positions_json,
         reconciled_at or datetime.now(timezone.utc).isoformat(), escalation_id),
    )


def cancel_escalation(conn, escalation_id, reason):
    """Cancel an escalation (CANCELLED_BY_ERIC terminal state)."""
    from datetime import datetime, timezone
    conn.execute(
        """UPDATE advisor_escalations SET
               status = 'CANCELLED_BY_ERIC',
               abandoned_reason = ?,
               abandoned_at = ?
           WHERE id = ? AND status NOT IN ('ABANDONED', 'SUPERSEDED', 'CANCELLED_BY_ERIC', 'RECONCILED')""",
        (reason, datetime.now(timezone.utc).isoformat(), escalation_id),
    )


def confirm_response_classification(conn, response_id, confirmed=True):
    """Advance a response to CLASSIFIED when Eric confirms or corrects.

    Sets classification_status to CONFIRMED (or CORRECTED if confirmed=False),
    classification_source to ERIC, and response_status to CLASSIFIED.
    """
    status = 'CONFIRMED' if confirmed else 'CORRECTED'
    conn.execute(
        """UPDATE advisor_responses SET
               classification_status = ?,
               classification_source = 'ERIC',
               response_status = 'CLASSIFIED'
           WHERE id = ?""",
        (status, response_id),
    )


# ── Component 3 — Eric Gate Approval helpers ──────────────────────

ALLOWED_ERIC_GATE_DECISIONS = {'APPROVE', 'VETO', 'RETURN_TO_DRAFT'}


def insert_eric_gate_approval(conn, approval_id, workflow_run_id, decision,
                               goal_reference_id, briefing_hash, briefing_json,
                               drift_snapshot_json, decision_trail_snapshot_json,
                               decided_by='Eric', is_current=1, rationale=None,
                               supersedes_approval_id=None, created_at=None,
                               decided_at=None):
    """Insert one row into eric_gate_approvals. Returns the new row id."""
    if decision not in ALLOWED_ERIC_GATE_DECISIONS:
        raise ValueError(
            f"Invalid decision '{decision}'. Allowed: {sorted(ALLOWED_ERIC_GATE_DECISIONS)}")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO eric_gate_approvals
           (id, workflow_run_id, decision, decided_at, decided_by,
            goal_reference_id, briefing_hash, briefing_json,
            drift_snapshot_json, decision_trail_snapshot_json,
            is_current, supersedes_approval_id, rationale, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (approval_id, workflow_run_id, decision,
         decided_at or now, decided_by,
         goal_reference_id, briefing_hash, briefing_json,
         drift_snapshot_json, decision_trail_snapshot_json,
         is_current, supersedes_approval_id, rationale,
         created_at or now),
    )
    return approval_id


def supersede_current_approval(conn, workflow_run_id):
    """Set is_current=0 for all current approval rows on a workflow run.

    Must be called inside a transaction before inserting a new current row.
    """
    conn.execute(
        """UPDATE eric_gate_approvals SET is_current = 0
           WHERE workflow_run_id = ? AND is_current = 1""",
        (workflow_run_id,),
    )


def get_current_eric_gate_approval(conn, workflow_run_id):
    """Return the current eric_gate_approvals row as dict, or None."""
    row = conn.execute(
        """SELECT * FROM eric_gate_approvals
           WHERE workflow_run_id = ? AND is_current = 1
           ORDER BY decided_at DESC, created_at DESC, id DESC
           LIMIT 1""",
        (workflow_run_id,),
    ).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in conn.execute(
        "SELECT * FROM eric_gate_approvals LIMIT 0").description]
    return dict(zip(cols, row))


def get_eric_gate_approval_history(conn, workflow_run_id):
    """Return all eric_gate_approvals rows for a run as list of dicts, newest first."""
    rows = conn.execute(
        """SELECT * FROM eric_gate_approvals
           WHERE workflow_run_id = ?
           ORDER BY decided_at DESC, created_at DESC, id DESC""",
        (workflow_run_id,),
    ).fetchall()
    cols = [d[0] for d in conn.execute(
        "SELECT * FROM eric_gate_approvals LIMIT 0").description]
    return [dict(zip(cols, r)) for r in rows]


def set_workflow_run_approved_at(conn, workflow_run_id, approved_at):
    """Set workflow_runs.eric_approved_at and update updated_at."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE workflow_runs SET
               eric_approved_at = ?,
               updated_at = ?
           WHERE id = ?""",
        (approved_at, now, workflow_run_id),
    )


def get_escalation_blockers(conn, workflow_run_id):
    """Return count of unreconciled mandatory escalations for a workflow run.

    Terminal states (RECONCILED, CANCELLED_BY_ERIC, ABANDONED, SUPERSEDED)
    are not blocking.
    """
    row = conn.execute(
        """SELECT COUNT(*) FROM advisor_escalations
           WHERE workflow_run_id = ?
             AND trigger_class = 'MANDATORY'
             AND status NOT IN ('RECONCILED', 'CANCELLED_BY_ERIC',
                                'ABANDONED', 'SUPERSEDED')""",
        (workflow_run_id,),
    ).fetchone()
    return row[0]
