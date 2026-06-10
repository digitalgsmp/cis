-- spine_schema.sql — CIS Deterministic State Spine
-- Tier 4.1: Minimum schema (workflow_runs + deliberation_rounds)
-- Updated: Migration 0005 — Kanban retired per ADR-013.
-- Updated: Migration 0006 — session_closeouts table added.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS workflow_runs (
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

CREATE TABLE IF NOT EXISTS workflow_run_artifacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workflow_run_legacy_links (
    id             TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL,
    kanban_card_id TEXT NOT NULL,
    kanban_board   TEXT,
    retired_at     TEXT NOT NULL DEFAULT (datetime('now')),
    note           TEXT
);


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
