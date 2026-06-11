-- Migration 0010: Eric Gate Approvals
-- Component: 3 — Eric Gate Redesign
-- Design: docs/CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md Revision 2
-- Date: 2026-06-11
-- Dependencies: Migration 0008 (provenance tables), Migration 0009 (escalation tables)
-- Idempotent: uses IF NOT EXISTS

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS eric_gate_approvals (
    id TEXT PRIMARY KEY,

    workflow_run_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (
        decision IN ('APPROVE', 'VETO', 'RETURN_TO_DRAFT')
    ),

    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL DEFAULT 'Eric',

    goal_reference_id INTEGER NOT NULL,

    briefing_hash TEXT NOT NULL,
    briefing_json TEXT NOT NULL,

    drift_snapshot_json TEXT NOT NULL,
    decision_trail_snapshot_json TEXT NOT NULL,

    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    supersedes_approval_id TEXT,

    rationale TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY (workflow_run_id)
        REFERENCES workflow_runs(id),

    FOREIGN KEY (goal_reference_id)
        REFERENCES goal_references(id),

    FOREIGN KEY (supersedes_approval_id)
        REFERENCES eric_gate_approvals(id)
);

CREATE INDEX IF NOT EXISTS idx_eric_gate_approvals_workflow_run_id
    ON eric_gate_approvals(workflow_run_id);

CREATE INDEX IF NOT EXISTS idx_eric_gate_approvals_goal_reference_id
    ON eric_gate_approvals(goal_reference_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_eric_gate_one_current_decision
    ON eric_gate_approvals(workflow_run_id)
    WHERE is_current = 1;
