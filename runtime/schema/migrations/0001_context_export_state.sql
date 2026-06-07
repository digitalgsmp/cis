-- 0001_context_export_state.sql
-- Tier 4.4 — Context Export State Tables
-- Extends the Tier 4.1 minimum spine (workflow_runs + deliberation_rounds).
-- Required by Tier 5 generate_agents_md.py and generate_hcp.py.
-- Apply with: sqlite3 data/cis_memory.db < runtime/schema/migrations/0001_context_export_state.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS project_decisions (
    id          TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    decision    TEXT NOT NULL,
    reason      TEXT,
    status      TEXT NOT NULL DEFAULT 'DECIDED'
                    CHECK (status IN ('DECIDED', 'OPEN', 'SUPERSEDED')),
    decided_at  TEXT NOT NULL,
    superseded_by TEXT
);

CREATE TABLE IF NOT EXISTS open_questions (
    id          TEXT PRIMARY KEY,
    question    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK (status IN ('OPEN', 'RESOLVED', 'DEFERRED')),
    resolution  TEXT,
    opened_at   TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS next_actions (
    id          TEXT PRIMARY KEY,
    tier        TEXT,
    description TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETE', 'BLOCKED', 'DEFERRED')),
    depends_on  TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS active_blockers (
    id          TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE', 'RESOLVED')),
    resolution  TEXT,
    created_at  TEXT NOT NULL,
    resolved_at TEXT
);
