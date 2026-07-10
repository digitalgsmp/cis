-- Migration 0021: Corpus Entries
-- Systematic extraction of Eric's verbatim words from all source roots.
-- Per-project provenance tagging (CIS, SWA, WIAS).
-- Part of Component 3 — Corpus Extraction Pass 1.

CREATE TABLE IF NOT EXISTS corpus_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_root TEXT NOT NULL,          -- 'session_closeouts', 'agent_trajectories', 'deliberation_rounds', 'archive'
    source_file TEXT,                   -- original file path or table row reference
    line_number INTEGER,
    timestamp TEXT,
    content_text TEXT NOT NULL,
    project_tag TEXT DEFAULT 'CIS',     -- CIS, SWA, WIAS
    extraction_pass INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_corpus_project ON corpus_entries(project_tag);
CREATE INDEX IF NOT EXISTS idx_corpus_source ON corpus_entries(source_root);

-- FTS5 virtual table for full-text search across corpus
CREATE VIRTUAL TABLE IF NOT EXISTS corpus_entries_fts USING fts5(
    content_text, source_root, project_tag,
    content='corpus_entries', content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS corpus_entries_ai AFTER INSERT ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(rowid, content_text, source_root, project_tag)
    VALUES (new.id, new.content_text, new.source_root, new.project_tag);
END;

CREATE TRIGGER IF NOT EXISTS corpus_entries_ad AFTER DELETE ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(corpus_entries_fts, rowid, content_text, source_root, project_tag)
    VALUES ('delete', old.id, old.content_text, old.source_root, old.project_tag);
END;

CREATE TRIGGER IF NOT EXISTS corpus_entries_au AFTER UPDATE ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(corpus_entries_fts, rowid, content_text, source_root, project_tag)
    VALUES ('delete', old.id, old.content_text, old.source_root, old.project_tag);
    INSERT INTO corpus_entries_fts(rowid, content_text, source_root, project_tag)
    VALUES (new.id, new.content_text, new.source_root, new.project_tag);
END;
