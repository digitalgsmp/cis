-- Migration 0027: Add PIPELINE_RUN to advancement_type CHECK constraint
--
-- Pipeline runs that aren't tied to a specific build plan node need a valid
-- advancement_type. The existing 5 values are all build-plan-specific.
-- Add 'PIPELINE_RUN' for standalone pipeline executions.
--
-- SQLite doesn't support ALTER TABLE ... ALTER CHECK, so we recreate the table.

-- 1. Save existing data
CREATE TABLE IF NOT EXISTS goal_references_backup AS
    SELECT * FROM goal_references;

-- 2. Drop the old table (cascades to indexes)
DROP TABLE IF EXISTS goal_references;

-- 3. Recreate with updated CHECK constraint
CREATE TABLE goal_references (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id       TEXT NOT NULL REFERENCES workflow_runs(id),
    goal_label            TEXT NOT NULL,
    dependency_node       TEXT NOT NULL,
    tier_advanced         TEXT,
    advancement_type      TEXT NOT NULL CHECK (advancement_type IN (
                            'CLOSES_NODE',
                            'ADVANCES_TIER',
                            'RESOLVES_BLOCKER',
                            'RESOLVES_OPEN_QUESTION',
                            'ESTABLISHES_PREREQUISITE',
                            'PIPELINE_RUN'
                        )),
    linked_record_table   TEXT CHECK (
                            linked_record_table IS NULL OR linked_record_table IN (
                                'active_blockers',
                                'open_questions',
                                'project_decisions',
                                'next_actions'
                            )
                        ),
    linked_record_id      INTEGER,
    authored_by          TEXT NOT NULL,
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 4. Restore existing data
INSERT INTO goal_references
    (id, workflow_run_id, goal_label, dependency_node, tier_advanced,
     advancement_type, linked_record_table, linked_record_id,
     authored_by, created_at)
    SELECT id, workflow_run_id, goal_label, dependency_node, tier_advanced,
           advancement_type, linked_record_table, linked_record_id,
           authored_by, created_at
    FROM goal_references_backup;

-- 5. Clean up backup
DROP TABLE goal_references_backup;

-- 6. Recreate index
CREATE INDEX IF NOT EXISTS idx_goal_references_run
    ON goal_references(workflow_run_id);
