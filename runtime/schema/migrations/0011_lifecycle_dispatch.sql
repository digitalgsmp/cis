-- Migration 0011: lifecycle_events + dispatch_log + dispatch_events
-- Prerequisite for Tier 11C Drafter→Reviewer handoff
-- Derived from all INSERT/SELECT/UPDATE usage in runtime/api/orchestration.py
-- FK decisions (explicit):
--   dispatch_events.dispatch_id → FK REFERENCES dispatch_log(dispatch_id)
--   lifecycle_events.proposal_id → bare TEXT (no proposals table exists yet)
--   dispatch_log.proposal_id → bare TEXT

-- 1. lifecycle_events — state machine transition log
CREATE TABLE IF NOT EXISTS lifecycle_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id         TEXT NOT NULL,
    session_id          TEXT,
    from_state          TEXT NOT NULL,
    to_state            TEXT NOT NULL,
    gate_type           TEXT,
    initiated_by        TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    dispatch_ref        TEXT,
    evidence_ref        TEXT,
    reviewer_message_id TEXT,
    directive_hash      TEXT,
    eric_approved       INTEGER NOT NULL DEFAULT 0,
    eric_bypass         INTEGER NOT NULL DEFAULT 0,
    revision_count      INTEGER NOT NULL DEFAULT 0,
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_proposal
    ON lifecycle_events(proposal_id, timestamp);

-- 2. dispatch_log — agent dispatch records
CREATE TABLE IF NOT EXISTS dispatch_log (
    dispatch_id         TEXT PRIMARY KEY,
    proposal_id         TEXT NOT NULL,
    source_actor        TEXT NOT NULL,
    target_agent        TEXT NOT NULL,
    target_endpoint     TEXT NOT NULL,
    lifecycle_state_at  TEXT NOT NULL,
    payload_hash        TEXT NOT NULL,
    payload_summary     TEXT NOT NULL,
    initiated_by        TEXT NOT NULL,
    eric_approved       INTEGER NOT NULL DEFAULT 0,
    timestamp_initiated TEXT NOT NULL,
    current_status      TEXT NOT NULL DEFAULT 'PENDING',
    directive_hash      TEXT,
    timestamp_completed TEXT,
    http_status_code    INTEGER,
    response_message_id TEXT,
    response_summary    TEXT,
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_dispatch_proposal
    ON dispatch_log(proposal_id);

-- 3. dispatch_events — per-dispatch event log (FK to dispatch_log)
CREATE TABLE IF NOT EXISTS dispatch_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dispatch_id         TEXT NOT NULL REFERENCES dispatch_log(dispatch_id),
    event_type          TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    http_status_code    INTEGER,
    response_message_id TEXT,
    error_message       TEXT
);

CREATE INDEX IF NOT EXISTS idx_dispatch_events_dispatch
    ON dispatch_events(dispatch_id);
