-- Migration 0039: Development continuity (WB.1C) — host mechanism for the
-- EXTERNAL Claude Code / ChatGPT-Codex developers building CIS.
--
-- This is NOT a second task queue. queue_items/queue_item_events (0031/0032)
-- remain the sole task authority. These tables hold the DURING-WORK record
-- the queue does not: discoveries, proposals, decisions, verified results,
-- unfinished work, contradictions and user instructions surfaced while a
-- queue item is open, plus explicit transcript import — scoped to a task
-- (queue item_num) but never itself a task list.
--
-- THIS MIGRATION HAS NOT BEEN APPLIED TO THE LIVE SPINE (data/cis_memory.db)
-- as part of this card. Additive only; applying it to the live spine is a
-- staged activation step for later review, not performed here. Tests in
-- tools/development/tests/ apply it to temporary SQLite files only.

CREATE TABLE IF NOT EXISTS dev_continuity_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    task                TEXT NOT NULL,          -- queue item_num, e.g. 'WB.1'
    revision            INTEGER NOT NULL,       -- monotonic per-task sequence, assigned at publish
    kind                TEXT NOT NULL CHECK (kind IN (
                            'proposal', 'decision', 'verified_result',
                            'unfinished_work', 'contradiction',
                            'user_instruction', 'reconciliation'
                        )),
    status              TEXT NOT NULL,          -- kind-specific free text (open/resolved/superseded/
                                                 -- the reconciliation disposition/etc.)
    actor               TEXT NOT NULL,          -- 'claude_code' | 'codex' | 'eric' | ...
    summary             TEXT NOT NULL,
    body                TEXT,
    evidence_refs_json  TEXT NOT NULL DEFAULT '[]',
    source_refs_json    TEXT NOT NULL DEFAULT '[]',
    against_revision    INTEGER,                -- kind='reconciliation' only: the revision being
                                                 -- reconciled against
    request_id          TEXT,                   -- caller-supplied idempotency key
    request_hash        TEXT,                   -- hash of (task,kind,status,summary,body) for the
                                                 -- same request_id, to detect a changed retry
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dce_task_revision
    ON dev_continuity_events(task, revision);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dce_task_request
    ON dev_continuity_events(task, request_id)
    WHERE request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dce_task ON dev_continuity_events(task, id);

-- Explicit transcript import — kept separate from knowledge_messages (the
-- generated/production KB) per WB.1C scope: this task does not write to
-- production KB. source_key is the stable identity: source/task/session
-- file/exchange.part, mirroring tools/ingest_claude_code_sessions.py's
-- convention so the two are reconcilable later without renaming anything.
CREATE TABLE IF NOT EXISTS dev_continuity_transcripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task            TEXT NOT NULL,
    source          TEXT NOT NULL,          -- 'claude_code' | 'codex' | ...
    source_key      TEXT NOT NULL UNIQUE,
    session_file    TEXT NOT NULL,
    exchange_index  INTEGER NOT NULL,
    part            INTEGER NOT NULL,
    content         TEXT NOT NULL,          -- verbatim rendered exchange, role-tagged
    imported_by     TEXT NOT NULL,
    imported_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_dct_task
    ON dev_continuity_transcripts(task, exchange_index, part);
