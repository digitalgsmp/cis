-- Migration 0028: Brain chat sessions and pipeline interjections
-- Supports conversational Brain interface and mid-pipeline backchannel

-- Pre-pipeline brain conversations (before a run starts)
CREATE TABLE IF NOT EXISTS brain_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,       -- groups messages in one conversation
    role TEXT NOT NULL,             -- 'user' or 'brain'
    content TEXT NOT NULL,
    kb_context TEXT,                -- KB context that was injected (for audit)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Mid-pipeline interjections (backchannel during active run)
CREATE TABLE IF NOT EXISTS pipeline_interjections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    consumed_by_phase TEXT,         -- which phase consumed it
    consumed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_brain_chats_session ON brain_chats(session_id);
CREATE INDEX IF NOT EXISTS idx_interjections_run ON pipeline_interjections(run_id);
