-- Migration 0024: Dead Letter Queue
-- Component 11 — Error Recovery
-- Stores runs that need human intervention (ESCALATED or ERROR status).

CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    failed_at TEXT DEFAULT (datetime('now')),
    error_message TEXT,
    agent_role TEXT,
    phase TEXT,
    input_text TEXT,
    retry_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'  -- pending, retried, resolved, abandoned
);

CREATE INDEX IF NOT EXISTS idx_dlq_status ON dead_letter_queue(status);
CREATE INDEX IF NOT EXISTS idx_dlq_run ON dead_letter_queue(run_id);
