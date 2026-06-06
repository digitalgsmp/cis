-- spine_schema.sql — CIS Deterministic State Spine
-- Tier 4.1: Minimum schema (workflow_runs + deliberation_rounds)
-- Remaining tables deferred to Tier 4.2+

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS workflow_runs (
    id              TEXT PRIMARY KEY,
    kanban_card_id  TEXT,
    kanban_board    TEXT NOT NULL DEFAULT 'cis-pipeline',
    topic           TEXT NOT NULL,
    result          TEXT NOT NULL CHECK (result IN ('CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    requires_eric_review INTEGER NOT NULL DEFAULT 1 CHECK (requires_eric_review IN (0, 1)),
    max_rounds      INTEGER NOT NULL,
    max_consecutive_revisions INTEGER NOT NULL DEFAULT 3,
    rounds_completed INTEGER NOT NULL DEFAULT 0,
    final_objections_json TEXT,
    created_at      TEXT NOT NULL,
    completed_at    TEXT
);

CREATE TABLE IF NOT EXISTS deliberation_rounds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    round_number    INTEGER NOT NULL,
    drafter_role    TEXT NOT NULL,
    drafter_output  TEXT NOT NULL,
    reviewer_role   TEXT NOT NULL,
    reviewer_signal TEXT NOT NULL CHECK (reviewer_signal IN ('OBJECTIONS', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    objections_json TEXT,
    revision_number INTEGER NOT NULL DEFAULT 1,
    requires_eric_review INTEGER NOT NULL DEFAULT 1 CHECK (requires_eric_review IN (0, 1)),
    created_at      TEXT NOT NULL,
    UNIQUE(run_id, round_number)
);
