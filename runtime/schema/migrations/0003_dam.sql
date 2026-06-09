-- 0003_dam.sql — Digital Asset Management Foundation Schema
-- Tier 7.5b — Clean Subset Import + FTS5
-- Depends on: spine_schema.sql (workflow_runs, deliberation_rounds)
--              0001_context_export_state.sql (project_decisions, open_questions, next_actions, active_blockers)
--              0002_project_state.sql (project_state)

PRAGMA foreign_keys = ON;

-- One row per imported session file
CREATE TABLE IF NOT EXISTS dam_assets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,
    file_hash       TEXT NOT NULL,           -- SHA256 of file contents
    file_size       INTEGER NOT NULL,        -- bytes
    source_profile  TEXT NOT NULL,           -- 'prime', 'v4impl', 'r1', 'v4pro'
    session_id      TEXT,                    -- extracted from file, may be NULL for edge cases
    session_start   TEXT,                    -- ISO timestamp from file
    message_count   INTEGER NOT NULL,
    imported_at     TEXT NOT NULL            -- ISO timestamp of import
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dam_assets_hash ON dam_assets(file_hash);

-- One row per message extracted from a session file
CREATE TABLE IF NOT EXISTS dam_extracted_text (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL REFERENCES dam_assets(id) ON DELETE CASCADE,
    segment_index   INTEGER NOT NULL,        -- 0-based position within the file's messages
    speaker_role    TEXT NOT NULL,           -- 'user', 'assistant', 'tool', 'system'
    content_text    TEXT NOT NULL,            -- verbatim message content
    created_at      TEXT NOT NULL            -- ISO timestamp from the message (or file session_start)
);

CREATE INDEX IF NOT EXISTS idx_dam_ext_asset ON dam_extracted_text(asset_id);
CREATE INDEX IF NOT EXISTS idx_dam_ext_role ON dam_extracted_text(speaker_role);

-- FTS5 virtual table for full-text search over extracted text
CREATE VIRTUAL TABLE IF NOT EXISTS dam_extracted_text_fts USING fts5(
    content_text,
    content='dam_extracted_text',
    content_rowid='id'
);

-- Triggers to keep FTS5 index in sync
CREATE TRIGGER IF NOT EXISTS dam_ext_ai AFTER INSERT ON dam_extracted_text BEGIN
    INSERT INTO dam_extracted_text_fts(rowid, content_text) VALUES (new.id, new.content_text);
END;

CREATE TRIGGER IF NOT EXISTS dam_ext_ad AFTER DELETE ON dam_extracted_text BEGIN
    INSERT INTO dam_extracted_text_fts(dam_extracted_text_fts, rowid, content_text) VALUES ('delete', old.id, old.content_text);
END;

CREATE TRIGGER IF NOT EXISTS dam_ext_au AFTER UPDATE ON dam_extracted_text BEGIN
    INSERT INTO dam_extracted_text_fts(dam_extracted_text_fts, rowid, content_text) VALUES ('delete', old.id, old.content_text);
    INSERT INTO dam_extracted_text_fts(rowid, content_text) VALUES (new.id, new.content_text);
END;
