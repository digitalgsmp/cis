"""build_plan.py — Build-Plan Spine access layer. Component 3.5."""

import sqlite3
from pathlib import Path

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
ALLOWED_STATUSES = {'PENDING', 'IN_PROGRESS', 'COMPLETE', 'BLOCKED', 'DEFERRED', 'PROPOSED'}
ALLOWED_DEPENDENCY_TYPES = {'HARD', 'SOFT'}


def create_node(conn, project_id, node_label, tier, sequence,
                status='PENDING', blocked_reason=None,
                required_role=None, allowed_mode=None):
    """Insert a build_plan_nodes row. Returns (node_id, is_new).
    is_new=True if row was inserted, False if already existed."""
    before = conn.total_changes
    conn.execute(
        """INSERT OR IGNORE INTO build_plan_nodes
           (project_id, node_label, tier, sequence, status, blocked_reason,
            required_role, allowed_mode)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (project_id, node_label, tier, sequence, status, blocked_reason,
         required_role, allowed_mode)
    )
    is_new = (conn.total_changes > before)
    row = conn.execute(
        "SELECT id FROM build_plan_nodes WHERE project_id=? AND node_label=?",
        (project_id, node_label)
    ).fetchone()
    return (row[0], is_new) if row else (None, False)


def create_dependency(conn, node_id, depends_on_id, dependency_type='HARD'):
    """Insert a dependency row. Returns True if inserted, False if skipped."""
    before = conn.total_changes
    conn.execute(
        """INSERT OR IGNORE INTO build_plan_dependencies
           (node_id, depends_on_id, dependency_type)
           VALUES (?, ?, ?)""",
        (node_id, depends_on_id, dependency_type)
    )
    return conn.total_changes > before


def promote_unblocked(conn, project_id='CIS'):
    """Promote BLOCKED nodes whose HARD deps are all COMPLETE to PENDING.
    Returns list of promoted node_labels. DEFERRED nodes are never promoted."""
    promoted = []
    blocked = conn.execute(
        """SELECT id, node_label FROM build_plan_nodes
           WHERE project_id=? AND status='BLOCKED'""",
        (project_id,)
    ).fetchall()
    for node in blocked:
        nid = node[0]
        nlabel = node[1]
        unmet = conn.execute(
            """SELECT COUNT(*) FROM build_plan_dependencies bpd
               JOIN build_plan_nodes dep ON bpd.depends_on_id = dep.id
               WHERE bpd.node_id=? AND bpd.dependency_type='HARD'
                 AND dep.status != 'COMPLETE'""",
            (nid,)
        ).fetchone()[0]
        if unmet == 0:
            conn.execute(
                "UPDATE build_plan_nodes SET status='PENDING', updated_at=datetime('now') WHERE id=?",
                (nid,)
            )
            promoted.append(nlabel)
    return promoted


def complete_node(conn, node_id, evidence_path=None, commit_hash=None, workflow_run_id=None):
    """Mark node COMPLETE (from IN_PROGRESS only). Then auto-promote unblocked dependents."""
    conn.execute(
        """UPDATE build_plan_nodes
           SET status='COMPLETE', evidence_path=?, commit_hash=?,
               workflow_run_id=?, completed_at=datetime('now'), updated_at=datetime('now')
           WHERE id=? AND status='IN_PROGRESS'""",
        (evidence_path, commit_hash, workflow_run_id, node_id)
    )
    return promote_unblocked(conn)
