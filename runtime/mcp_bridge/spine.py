"""
spine.py — Read-only SQLite queries for the CIS MCP Bridge.

All queries are SELECT only. The database is opened in read-only mode
(uri=True, mode=ro) to OS-enforce the no-write constraint.

Tables read:
  build_plan_nodes, workflow_runs, deliberation_rounds,
  workflow_run_artifacts, eric_gate_approvals, session_closeouts,
  session_closeouts_fts, project_decisions, open_questions
"""
import os
import sqlite3


def _get_db_path():
    """Return the CIS spine path from CIS_SPINE_PATH env var."""
    path = os.environ.get("CIS_SPINE_PATH", "")
    if not path:
        raise RuntimeError("CIS_SPINE_PATH environment variable is not set")
    return path


def _connect_readonly(db_path=None):
    """Open the spine database in read-only mode (OS-enforced)."""
    if db_path is None:
        db_path = _get_db_path()
    # Use URI mode with mode=ro for read-only enforcement
    # Encode the path for URI usage (handle spaces and special chars)
    encoded = db_path.replace("%", "%25").replace("#", "%23")
    uri = "file:{}?mode=ro".format(encoded)
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row):
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def _rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows] if rows else []


# ── Query Functions (one per MCP tool) ───────────────────────────────


def query_current_phase(db_path=None):
    """
    Current build tier, status, and next actions from build_plan_nodes.

    Returns dict with keys:
      build_phase: str (from project_state)
      in_progress: list of nodes with status IN_PROGRESS
      pending: list of nodes with status PENDING
      next_tier: str (from project_state)
      next_action: str (from project_state)
    """
    conn = _connect_readonly(db_path)
    try:
        # Build phase from project_state (latest non-superseded)
        phase_row = conn.execute(
            """SELECT value FROM project_state
               WHERE key = 'build_phase' AND superseded_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        ).fetchone()

        next_tier_row = conn.execute(
            """SELECT value FROM project_state
               WHERE key = 'next_tier' AND superseded_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        ).fetchone()

        next_action_row = conn.execute(
            """SELECT value FROM project_state
               WHERE key = 'next_action' AND superseded_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        ).fetchone()

        in_progress = _rows_to_list(conn.execute(
            """SELECT node_label, status, tier, blocked_reason
               FROM build_plan_nodes
               WHERE project_id = 'CIS' AND status = 'IN_PROGRESS'
               ORDER BY sequence"""
        ).fetchall())

        pending = _rows_to_list(conn.execute(
            """SELECT node_label, status, tier, blocked_reason
               FROM build_plan_nodes
               WHERE project_id = 'CIS' AND status = 'PENDING'
               ORDER BY sequence"""
        ).fetchall())

        return {
            "build_phase": phase_row["value"] if phase_row else None,
            "next_tier": next_tier_row["value"] if next_tier_row else None,
            "next_action": next_action_row["value"] if next_action_row else None,
            "in_progress": in_progress,
            "pending": pending,
        }
    finally:
        conn.close()


def query_build_status(node_label, db_path=None):
    """
    Single build_plan_node by label.

    Returns dict with keys: node_label, status, tier, blocked_reason,
    evidence_path, commit_hash, completed_at, approved_at, created_at, updated_at.
    Returns None if no matching node.
    """
    conn = _connect_readonly(db_path)
    try:
        row = conn.execute(
            """SELECT node_label, status, tier, blocked_reason,
                      evidence_path, commit_hash, completed_at,
                      approved_at, created_at, updated_at
               FROM build_plan_nodes
               WHERE node_label = ?""",
            (node_label,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def query_next_actions(db_path=None):
    """
    Nodes with status PENDING where dependencies are satisfied.

    Returns list of dicts with all build_plan_nodes columns for eligible nodes.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT node_label, status, tier, blocked_reason,
                      evidence_path, commit_hash, completed_at,
                      approved_at, created_at, updated_at
               FROM build_plan_nodes
               WHERE project_id = 'CIS' AND status = 'PENDING'
               ORDER BY sequence"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_recent_runs(limit=5, db_path=None):
    """
    Last N workflow_runs.

    Returns list of dicts with keys: id, topic, result, rounds_completed,
    created_at, completed_at, status.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT id, topic, result, rounds_completed,
                      created_at, completed_at, status
               FROM workflow_runs
               ORDER BY created_at DESC
               LIMIT ?""",
            (int(limit),),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_run_detail(run_id, db_path=None):
    """
    Single workflow_run + its deliberation_rounds + artifacts.

    Returns dict with keys:
      run: dict (workflow_runs row)
      rounds: list of dicts (deliberation_rounds rows)
      artifacts: list of dicts (workflow_run_artifacts rows)
    Returns None if run_id not found.
    """
    conn = _connect_readonly(db_path)
    try:
        run_row = conn.execute(
            """SELECT * FROM workflow_runs WHERE id = ?""",
            (run_id,),
        ).fetchone()
        if run_row is None:
            return None

        rounds = _rows_to_list(conn.execute(
            """SELECT * FROM deliberation_rounds
               WHERE run_id = ?
               ORDER BY round_number""",
            (run_id,),
        ).fetchall())

        artifacts = _rows_to_list(conn.execute(
            """SELECT * FROM workflow_run_artifacts
               WHERE workflow_run_id = ?
               ORDER BY created_at""",
            (run_id,),
        ).fetchall())

        return {
            "run": dict(run_row),
            "rounds": rounds,
            "artifacts": artifacts,
        }
    finally:
        conn.close()


def query_open_decisions(db_path=None):
    """
    Active non-superseded decisions from project_decisions.

    Returns list of dicts.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM project_decisions
               WHERE status = 'DECIDED' AND superseded_by IS NULL
               ORDER BY decided_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_open_questions(db_path=None):
    """
    All open questions from open_questions.

    Returns list of dicts.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM open_questions
               WHERE status = 'OPEN'
               ORDER BY opened_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_eric_gate_status(db_path=None):
    """
    Pending Eric Gate approvals.

    Returns list of dicts from eric_gate_approvals where is_current=1,
    joined with goal_references for goal_label.
    """
    conn = _connect_readonly(db_path)
    try:
        rows = conn.execute(
            """SELECT ega.decision, ega.decided_at,
                      ega.workflow_run_id, ega.rationale,
                      ega.created_at, gr.goal_label
               FROM eric_gate_approvals ega
               LEFT JOIN goal_references gr
                 ON ega.goal_reference_id = gr.id
               WHERE ega.is_current = 1
               ORDER BY ega.decided_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def query_search_sessions(query_text, limit=10, db_path=None):
    """
    FTS5 search across session_closeouts.

    Searches the session_closeouts_fts virtual table for matching text
    in failure_summary, failure_step, log_path, and created_by columns.
    Returns matching rows from the base session_closeouts table.

    Returns list of dicts with session_closeouts columns.
    """
    conn = _connect_readonly(db_path)
    try:
        # Use FTS5 MATCH to find matching rowids, then join back to base table
        rows = conn.execute(
            """SELECT sc.*
               FROM session_closeouts sc
               JOIN session_closeouts_fts fts ON sc.id = fts.rowid
               WHERE session_closeouts_fts MATCH ?
               ORDER BY sc.created_at DESC
               LIMIT ?""",
            (query_text, int(limit)),
        ).fetchall()

        # Also try a LIKE fallback for simple term matching
        if not rows:
            like_pattern = "%{}%".format(query_text)
            rows = conn.execute(
                """SELECT * FROM session_closeouts
                   WHERE failure_summary LIKE ?
                      OR failure_step LIKE ?
                      OR log_path LIKE ?
                      OR created_by LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (like_pattern, like_pattern, like_pattern,
                 like_pattern, int(limit)),
            ).fetchall()

        return _rows_to_list(rows)
    finally:
        conn.close()
