-- Migration 0036: Card Factory asks + generated cards (queue item WB.1B-1)
--
-- Additive only. Two tables:
--   card_factory_asks  — what Eric typed (project, ask text, done-when text).
--     `revision` increments on every edit so a card generated against an
--     older wording can be told apart from the ask's current text.
--   card_factory_cards — one row per generate attempt or per edit of an
--     existing card. Editing a card does NOT overwrite its row: it inserts a
--     new row in the same lineage (`lineage_id` groups them, `card_revision`
--     counts within the lineage, `supersedes_id` points at the row it
--     replaces) so the prior text and gate verdict stay on the record
--     instead of being lost. `ask_revision` is a snapshot of the ask's
--     revision at the moment this row's text was produced/accepted — a card
--     is "stale" (application-computed, not stored) when this no longer
--     equals the ask's current `revision`. Dispatch columns are nullable
--     placeholders for WB.1B-2 (card execution) — not written or read here.
--
-- Prefixed card_factory_* rather than bare asks/cards to stay unambiguous
-- next to the cards/ directory on disk and the unrelated mined_tasks table.
--
-- This migration has NOT been applied to the live spine (data/cis_memory.db)
-- as part of this card. Applying it to the live, shared, multi-GB database
-- is an activation step (WB.1B Stage 5 / card C4), not something to do
-- inside an implementation pass.
--
-- Superseded 2026-09-17 by the bounded-control correction addendum on
-- card C1: added asks.revision; cards.ask_revision/lineage_id/card_revision/
-- supersedes_id/is_current, request_id + its dedup/lock indexes, and usage
-- columns. This file replaces the original 0036 in place (never applied to
-- any database, so there is nothing to migrate away from).

CREATE TABLE IF NOT EXISTS card_factory_asks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    ask_text TEXT NOT NULL,
    done_when_text TEXT,
    revision INTEGER NOT NULL DEFAULT 1,
    knowledge_message_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS card_factory_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ask_id INTEGER NOT NULL REFERENCES card_factory_asks(id),
    ask_revision INTEGER NOT NULL,
    lineage_id INTEGER,
    card_revision INTEGER NOT NULL DEFAULT 1,
    supersedes_id INTEGER REFERENCES card_factory_cards(id),
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    card_text TEXT,
    gate_exit_code INTEGER,
    gate_output TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'pass', 'fail', 'skip', 'error')),
    saved_path TEXT,
    error TEXT,
    request_id TEXT,
    usage_input_tokens INTEGER,
    usage_output_tokens INTEGER,
    usage_cost_usd REAL,
    dispatch_target TEXT,
    dispatch_status TEXT,
    dispatch_run_id TEXT,
    dispatch_started_at TEXT,
    dispatch_finished_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_cf_cards_ask ON card_factory_cards(ask_id, id);
CREATE INDEX IF NOT EXISTS idx_cf_cards_lineage ON card_factory_cards(lineage_id, card_revision);

-- Dedup: replaying the same client request_id for the same ask must not
-- create a second row / trigger a second model call.
CREATE UNIQUE INDEX IF NOT EXISTS idx_cf_cards_request
    ON card_factory_cards(ask_id, request_id) WHERE request_id IS NOT NULL;

-- Concurrency lock: only one generation may be in flight (status='pending',
-- inserted eagerly with a request_id before the model call) per ask
-- revision at a time. Card edits never insert a request_id'd pending row,
-- so they are not affected by this lock.
CREATE UNIQUE INDEX IF NOT EXISTS idx_cf_cards_pending_lock
    ON card_factory_cards(ask_id, ask_revision)
    WHERE status = 'pending' AND request_id IS NOT NULL;

-- At most one row per lineage may be the current tip. SQLite treats every
-- NULL in a unique index as distinct, so freshly generated rows (lineage_id
-- briefly NULL before being set to their own id in the same commit) never
-- collide here; only two concurrent edits of the same lineage would, and
-- edit_card() demotes the old row to is_current=0 before inserting the new
-- one specifically so that ordering — not this index — is what prevents a
-- row from ever conflicting with itself.
CREATE UNIQUE INDEX IF NOT EXISTS idx_cf_cards_lineage_current
    ON card_factory_cards(lineage_id) WHERE is_current = 1;
