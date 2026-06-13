-- CIS Spine Migration 009: FTS5 index on session_closeouts
-- Purpose: Enables cis_search_sessions MCP tool via full-text search
-- Tier: 8 (MCP Bridge)
-- Created: 2026-06-12
-- Dependencies: session_closeouts table (created in Tier 4 spine)
--
-- Creates an external content FTS5 virtual table that indexes
-- the searchable text columns of session_closeouts. The base
-- table is not altered.

CREATE VIRTUAL TABLE IF NOT EXISTS session_closeouts_fts USING fts5(
    failure_summary,
    failure_step,
    log_path,
    created_by,
    content='session_closeouts',
    content_rowid='id'
);

-- Triggers to keep FTS5 index in sync with base table
CREATE TRIGGER IF NOT EXISTS session_closeouts_fts_insert AFTER INSERT ON session_closeouts BEGIN
    INSERT INTO session_closeouts_fts(rowid, failure_summary, failure_step, log_path, created_by)
    VALUES (new.id, new.failure_summary, new.failure_step, new.log_path, new.created_by);
END;

CREATE TRIGGER IF NOT EXISTS session_closeouts_fts_delete AFTER DELETE ON session_closeouts BEGIN
    INSERT INTO session_closeouts_fts(session_closeouts_fts, rowid, failure_summary, failure_step, log_path, created_by)
    VALUES ('delete', old.id, old.failure_summary, old.failure_step, old.log_path, old.created_by);
END;

CREATE TRIGGER IF NOT EXISTS session_closeouts_fts_update AFTER UPDATE ON session_closeouts BEGIN
    INSERT INTO session_closeouts_fts(session_closeouts_fts, rowid, failure_summary, failure_step, log_path, created_by)
    VALUES ('delete', old.id, old.failure_summary, old.failure_step, old.log_path, old.created_by);
    INSERT INTO session_closeouts_fts(rowid, failure_summary, failure_step, log_path, created_by)
    VALUES (new.id, new.failure_summary, new.failure_step, new.log_path, new.created_by);
END;
