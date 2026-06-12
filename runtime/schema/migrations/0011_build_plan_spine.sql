-- Migration 0011: Build-Plan Spine Authority
-- Component 3.5 Phase 1 — Schema only. No data.
-- Design: docs/CIS_FOUNDATION_HARDENING_COMPONENT_3_5_DESIGN.md (Revision 2)

CREATE TABLE IF NOT EXISTS build_plan_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'CIS',
    node_label      TEXT NOT NULL,
    tier            TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN (
                        'PENDING', 'IN_PROGRESS', 'COMPLETE',
                        'BLOCKED', 'DEFERRED', 'PROPOSED'
                    )),
    blocked_reason  TEXT,
    required_role   TEXT,
    allowed_mode    TEXT,
    workflow_run_id TEXT REFERENCES workflow_runs(id),
    evidence_path   TEXT,
    commit_hash     TEXT,
    completed_at    TEXT,
    approved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, node_label)
);

CREATE TABLE IF NOT EXISTS build_plan_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         INTEGER NOT NULL REFERENCES build_plan_nodes(id) ON DELETE CASCADE,
    depends_on_id   INTEGER NOT NULL REFERENCES build_plan_nodes(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL DEFAULT 'HARD'
                    CHECK (dependency_type IN ('HARD', 'SOFT')),
    UNIQUE(node_id, depends_on_id),
    CHECK(node_id != depends_on_id)
);

CREATE INDEX IF NOT EXISTS idx_bpn_project_status
    ON build_plan_nodes(project_id, status);
CREATE INDEX IF NOT EXISTS idx_bpn_project_sequence
    ON build_plan_nodes(project_id, sequence);
CREATE INDEX IF NOT EXISTS idx_bpd_node
    ON build_plan_dependencies(node_id);
CREATE INDEX IF NOT EXISTS idx_bpd_depends
    ON build_plan_dependencies(depends_on_id);
