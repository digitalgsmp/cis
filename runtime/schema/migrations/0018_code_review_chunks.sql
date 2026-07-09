-- Migration 0018: Code review chunks table
-- Stores per-chunk code review state for the sequential three-pass review process.
-- Per SPEC_CODE_REVIEW_GATE.md REV-2.

CREATE TABLE IF NOT EXISTS code_review_chunks (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    diff_text TEXT DEFAULT '',
    l1_results TEXT DEFAULT '',
    review_a_pass1 TEXT DEFAULT '',
    review_b_pass2 TEXT DEFAULT '',
    review_a_consensus TEXT DEFAULT '',
    final_verdict TEXT DEFAULT 'PENDING',
    revision_directive TEXT DEFAULT '',
    revision_number INTEGER DEFAULT 1,
    incorporated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(run_id, chunk_number, revision_number)
);
