-- Migration 0005: Retire kanban_card_id and kanban_board from workflow_runs.
-- Add eric_approved_at as placeholder Eric Gate mechanism.
-- Add workflow_run_artifacts for explicit implementation evidence.
-- Add workflow_run_legacy_links to preserve historical Kanban references.
-- ADR-013: Kanban retired as pipeline transport.
--
-- eric_approved_at: placeholder pending provenance schema design in
-- Foundation Hardening Phase. Setter (UI/API/CLI) not yet implemented.
-- gate_eric_approval_present.sh will correctly fail until setter is built.
--
-- workflow_run_artifacts: required by gate_implementation_artifact_present.sh.
-- Implementer must INSERT an artifact_type='implementation' row containing
-- commit hash or file change evidence. Completion status alone is not evidence.

BEGIN TRANSACTION;

-- Step 1: Create legacy links table
CREATE TABLE IF NOT EXISTS workflow_run_legacy_links (
    id             TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL,
    kanban_card_id TEXT NOT NULL,
    kanban_board   TEXT,
    retired_at     TEXT NOT NULL DEFAULT (datetime('now')),
    note           TEXT
);

-- Step 2: Preserve non-null kanban_card_id rows before removal
INSERT INTO workflow_run_legacy_links
    (id, run_id, kanban_card_id, kanban_board, note)
SELECT
    id || '-kanban-link',
    id,
    kanban_card_id,
    kanban_board,
    'Retired per ADR-013 migration 0005'
FROM workflow_runs
WHERE kanban_card_id IS NOT NULL AND kanban_card_id != '';

-- Step 3: Create artifacts table
CREATE TABLE IF NOT EXISTS workflow_run_artifacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Step 4: Recreate workflow_runs without kanban columns, with eric_approved_at
CREATE TABLE workflow_runs_new (
    id                        TEXT PRIMARY KEY,
    topic                     TEXT NOT NULL,
    result                    TEXT NOT NULL CHECK (result IN
                              ('CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    requires_eric_review      INTEGER NOT NULL DEFAULT 1
                              CHECK (requires_eric_review IN (0, 1)),
    max_rounds                INTEGER NOT NULL,
    max_consecutive_revisions INTEGER NOT NULL DEFAULT 3,
    rounds_completed          INTEGER NOT NULL DEFAULT 0,
    final_objections_json     TEXT,
    created_at                TEXT NOT NULL,
    completed_at              TEXT,
    status                    TEXT NOT NULL DEFAULT 'COMPLETE',
    route                     TEXT,
    updated_at                TEXT,
    eric_approved_at          TEXT
);

-- Step 5: Copy all active columns
INSERT INTO workflow_runs_new
    (id, topic, result, requires_eric_review, max_rounds,
     max_consecutive_revisions, rounds_completed, final_objections_json,
     created_at, completed_at, status, route, updated_at)
SELECT
    id, topic, result, requires_eric_review, max_rounds,
    max_consecutive_revisions, rounds_completed, final_objections_json,
    created_at, completed_at, status, route, updated_at
FROM workflow_runs;

-- Step 6: Swap tables
DROP TABLE workflow_runs;
ALTER TABLE workflow_runs_new RENAME TO workflow_runs;

COMMIT;
