-- Migration 0037: Card runner dispatch ledger (queue item WB.1B-2)
--
-- One row per dispatch attempt (implement or review) of a gated card to a
-- CLI target (claude or codex). Additive only, staged like 0035/0036 — NOT
-- applied to the live spine (data/cis_memory.db) by this card; applying it
-- is an activation step.
--
-- `active_lock` implements the one-run-at-a-time-per-repo rule as a DB-level
-- partial unique index rather than an app-level check, matching the
-- request_id/pending-lock pattern already used by 0036's
-- card_factory_cards: set to 1 while a run is queued/running/stopping (or
-- stop_failed, where the process may still be alive and uncontrolled), and
-- cleared to NULL only once a run is confirmed in a terminal, safe state.
--
-- `card_fingerprint` is the sha256 of the card file's content at dispatch
-- time, binding a dispatch to the exact revision it was authorized against
-- (per the bounded-control addendum: "gate PASS is not user approval").
--
-- Token/turn/cost fields are nullable = unknown, never estimated — codex's
-- --json usage reporting was never verified live (FACTS.md §4), so codex
-- rows are expected to leave most of these NULL with usage_unknown=1.
--
-- Corrected 2026-09-17 by card WB.1B-2A (dispatch corrections). Edited in
-- place — like 0036's own addendum, this migration has never been applied
-- to any database, so there is nothing to migrate away from. Added:
--   card_factory_card_id — dispatch is now validated against the live
--     card_factory_cards/card_factory_asks row (current revision, PASS
--     verdict, matching ask revision, matching card_text), not just trusted
--     because a file happened to sit in cards/inbox/ ("an inbox pathname is
--     not proof of validity"). NOT NULL: every dispatch must name one.
--   review_of_run_id — a review run must name the specific prior implement
--     run (same card_factory_card_id) it is reviewing, so a review's
--     evidence folder can coexist with the implementation's without either
--     overwriting the other.
--   run_dir — each run gets its own unique evidence folder
--     (data/agent_handoffs/<card_id>/run-<id>-<mode>/), linked to the card
--     via the shared <card_id> parent, rather than one folder per card that
--     implementation and review would collide over.
--   error — setup/process-launch failures (folder creation, spawning the
--     child) are recorded here and release active_lock, rather than
--     leaving a run stuck at status='queued' forever with no explanation.
--   model is now nullable (codex has no named default model in FACTS.md).

CREATE TABLE IF NOT EXISTS card_runner_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    card_factory_card_id INTEGER NOT NULL,
    review_of_run_id INTEGER REFERENCES card_runner_runs(id),
    run_dir TEXT,
    card_path TEXT NOT NULL,
    card_fingerprint TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('implement', 'review')),
    target TEXT NOT NULL CHECK (target IN ('claude', 'codex')),
    model TEXT,  -- NULL means "target's own configured default" (codex has none named in FACTS.md)
    project TEXT,
    limits_json TEXT NOT NULL,
    permitted_files_json TEXT,
    permitted_commands_json TEXT,
    authorized_by TEXT NOT NULL,
    permission_mode TEXT NOT NULL,
    permission_risk TEXT,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'stopping', 'completed',
                           'failed', 'timeout', 'stopped', 'stop_failed')),
    active_lock INTEGER CHECK (active_lock IN (1)),
    pid INTEGER,
    pgid INTEGER,
    session_id TEXT,
    log_path TEXT,
    started_at TEXT,
    finished_at TEXT,
    exit_code INTEGER,
    wall_seconds REAL,
    num_turns INTEGER,
    input_tokens INTEGER,
    cached_input_tokens INTEGER,
    output_tokens INTEGER,
    reasoning_tokens INTEGER,
    cost_usd REAL,
    usage_unknown INTEGER NOT NULL DEFAULT 0 CHECK (usage_unknown IN (0, 1)),
    final_message TEXT,
    error TEXT,
    out_of_scope_json TEXT,
    cancel_requested INTEGER NOT NULL DEFAULT 0 CHECK (cancel_requested IN (0, 1)),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Reusing a request_id must not start a second run: a repeat dispatch call
-- looks up and returns the existing row instead of inserting a new one.
CREATE UNIQUE INDEX IF NOT EXISTS idx_cr_runs_request ON card_runner_runs(request_id);

-- One run at a time per repo, enforced atomically at INSERT time (not by an
-- app-level check-then-act, which would race).
CREATE UNIQUE INDEX IF NOT EXISTS idx_cr_runs_active_lock ON card_runner_runs(active_lock);

CREATE INDEX IF NOT EXISTS idx_cr_runs_card_path ON card_runner_runs(card_path, id);
CREATE INDEX IF NOT EXISTS idx_cr_runs_project ON card_runner_runs(project);
CREATE INDEX IF NOT EXISTS idx_cr_runs_card_factory_card ON card_runner_runs(card_factory_card_id, id);
CREATE INDEX IF NOT EXISTS idx_cr_runs_review_of ON card_runner_runs(review_of_run_id);
