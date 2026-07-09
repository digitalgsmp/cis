-- Migration 0019: Expand workflow_runs.result CHECK to include PENDING
-- The result column was constrained to only terminal states.
-- Fixing bug 4 (default to PENDING) requires PENDING to be a valid value.

-- SQLite cannot ALTER CHECK constraints in place, so we rebuild the table.
-- This preserves all existing data.

-- Step 1: Rename old table
ALTER TABLE workflow_runs RENAME TO workflow_runs_old;

-- Step 2: Create new table with expanded CHECK
CREATE TABLE workflow_runs (
    id                        TEXT PRIMARY KEY,
    topic                     TEXT NOT NULL,
    result                    TEXT NOT NULL DEFAULT 'PENDING'
                              CHECK (result IN
                              ('PENDING', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR', 'VERIFY_FAILED')),
    requires_eric_review      INTEGER NOT NULL DEFAULT 1
                              CHECK (requires_eric_review IN (0, 1)),
    max_rounds                INTEGER NOT NULL,
    max_consecutive_revisions INTEGER NOT NULL DEFAULT 3,
    rounds_completed          INTEGER NOT NULL DEFAULT 0,
    final_objections_json     TEXT,
    created_at                TEXT NOT NULL,
    completed_at              TEXT,
    status                    TEXT NOT NULL DEFAULT 'INTAKE',
    route                     TEXT,
    updated_at                TEXT,
    eric_approved_at          TEXT,
    intent                    TEXT,
    directive_hash            TEXT
);

-- Step 3: Copy data from old table
INSERT INTO workflow_runs
SELECT id, topic, result, requires_eric_review, max_rounds,
       max_consecutive_revisions, rounds_completed, final_objections_json,
       created_at, completed_at, status, route, updated_at, eric_approved_at,
       intent, directive_hash
FROM workflow_runs_old;

-- Step 4: Drop old table
DROP TABLE workflow_runs_old;
