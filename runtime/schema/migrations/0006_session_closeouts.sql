-- Migration 0006: Add session_closeouts table.
-- Records every closeout attempt as a lifecycle event.
-- Used by router at session start to surface last verified state.
-- Written by tools/closeout.sh on every closeout run.

CREATE TABLE IF NOT EXISTS session_closeouts (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at                   TEXT NOT NULL,
    completed_at                 TEXT,
    status                       TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'BLOCKED')),
    start_head                   TEXT,
    end_head                     TEXT,
    dirty_before_json            TEXT,
    dirty_after_json             TEXT,
    generated_context            INTEGER NOT NULL DEFAULT 0,
    export_agreement_status      TEXT,
    build_state_coherence_status TEXT,
    commit_hash                  TEXT,
    log_path                     TEXT,
    failure_step                 TEXT,
    failure_summary              TEXT,
    created_by                   TEXT NOT NULL DEFAULT 'operator_command'
);
