-- 0002_project_state.sql
-- Tier 6.5 Remediation: append-only canonical build-state table
-- Applied: 2026-06-08
-- Evidence: git log shows Tier 5.1 through 6.5 complete

CREATE TABLE IF NOT EXISTS project_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('git', 'gate', 'manual')),
    evidence_hash   TEXT,
    evidence_run_id TEXT,
    created_at      TEXT NOT NULL,
    superseded_at   TEXT,
    superseded_by   INTEGER REFERENCES project_state(id)
);

CREATE INDEX IF NOT EXISTS idx_project_state_key_created
    ON project_state(key, created_at);
