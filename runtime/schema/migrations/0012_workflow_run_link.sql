-- Migration 0012: Add workflow_run_id to lifecycle and dispatch tables
-- Prerequisite for ADR-SEED-014 (Temporary Draft Initiation Contract)
-- Links the lifecycle state machine back to the durable workflow run.
-- One workflow_run → many lifecycle_events, many dispatch_log rows.
-- FK deferred — proposals and dispatches are independent namespaces per
-- migration 0011 comment ("no proposals table exists yet").

ALTER TABLE lifecycle_events ADD COLUMN workflow_run_id TEXT;
ALTER TABLE dispatch_log ADD COLUMN workflow_run_id TEXT;

CREATE INDEX IF NOT EXISTS idx_lifecycle_workflow_run
    ON lifecycle_events(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_dispatch_workflow_run
    ON dispatch_log(workflow_run_id);
