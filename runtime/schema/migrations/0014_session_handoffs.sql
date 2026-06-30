-- CIS Spine Migration 0014
-- session_handoffs: durable record of session-to-session handoff narrative.
-- Fills the gap between auto-generated spine data and manual DEV-PIVOT prose.
-- The AGENTS.md generator reads the latest row and includes it as a
-- "Session Handoff" section, eliminating manual DEV-PIVOT section drift.
--
-- Run: sqlite3 data/cis_memory.db < runtime/schema/migrations/0014_session_handoffs.sql

CREATE TABLE IF NOT EXISTS session_handoffs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT NOT NULL,               -- "2026-06-29"
    title           TEXT NOT NULL,               -- "June 27-29: Front Door + Reconciliation"
    summary         TEXT NOT NULL,               -- What was built/done
    decisions       TEXT,                        -- Key decisions made this session
    next_actions    TEXT,                        -- What's next (priority order)
    claude_context  TEXT,                        -- Working context for external advisor
    eric_feedback   TEXT,                        -- Eric's verbatim feedback
    gateway_status  TEXT,                        -- Verified port status at handoff time
    git_head        TEXT,                        -- Commit SHA at time of handoff
    is_current      INTEGER NOT NULL DEFAULT 0,  -- 1 = latest active handoff
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Index for fetching latest
CREATE INDEX IF NOT EXISTS idx_session_handoffs_current
    ON session_handoffs(is_current, created_at DESC);
