"""build_plan.py — Build-Plan Spine access layer. Component 3.5."""

import sqlite3
from pathlib import Path
from datetime import datetime, timezone

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


def sync_project_state_from_build_plan(conn, project_id='CIS'):
    """Write project_state cache from build_plan_nodes.
    Source label: 'build_plan_spine' (not 'gate' — this is a cache sync, not a gate result).
    Supersedes prior next_tier/next_action/build_phase rows."""
    now = datetime.now(timezone.utc).isoformat()

    completed = conn.execute(
        """SELECT node_label, tier, sequence FROM build_plan_nodes
           WHERE project_id=? AND status='COMPLETE'
           ORDER BY sequence DESC LIMIT 1""",
        (project_id,)
    ).fetchone()

    next_node = conn.execute(
        """SELECT node_label, tier, sequence FROM build_plan_nodes
           WHERE project_id=? AND status='IN_PROGRESS'
           ORDER BY sequence LIMIT 1""",
        (project_id,)
    ).fetchone()

    if not next_node:
        next_node = conn.execute(
            """SELECT bpn.node_label, bpn.tier
               FROM build_plan_nodes bpn
               WHERE bpn.project_id=?
                 AND bpn.status='PENDING'
                 AND bpn.id NOT IN (
                     SELECT bpd.node_id FROM build_plan_dependencies bpd
                     JOIN build_plan_nodes dep ON bpd.depends_on_id = dep.id
                     WHERE bpd.dependency_type='HARD'
                       AND dep.status != 'COMPLETE'
                 )
               ORDER BY bpn.sequence LIMIT 1""",
            (project_id,)
        ).fetchone()

    conn.execute(
        """UPDATE project_state SET superseded_at=?
           WHERE key IN ('next_tier','next_action','build_phase')
             AND superseded_at IS NULL""",
        (now,)
    )

    completed_label = completed[0] if completed else "(none)"

    if next_node:
        next_label = next_node[0]
        next_tier_val = next_node[1]
        source = "gate"
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
            ("next_tier", next_tier_val, source, now)
        )
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
            ("next_action", next_label, source, now)
        )
        phase = f"{completed_label}. {next_label}."
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
            ("build_phase", phase, source, now)
        )
    else:
        # No IN_PROGRESS or unblocked PENDING node — all work complete or blocked
        source = "gate"
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
            ("next_tier", "—", source, now)
        )
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
            ("next_action", "(none — all nodes COMPLETE, BLOCKED, or DEFERRED)", source, now)
        )
        phase = f"{completed_label}. No active work — all remaining nodes BLOCKED or DEFERRED."
        conn.execute(
            "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
            ("build_phase", phase, source, now)
        )
