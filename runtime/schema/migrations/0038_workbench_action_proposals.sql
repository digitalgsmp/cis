-- Migration 0038: Workbench action proposals (queue item WB.1B-2B)
--
-- Links a Braingate conversation (workbench_projects/workbench_messages,
-- migration 0035) to the card-factory/card-runner pipeline (migrations
-- 0036/0037) without ever recording a model's paraphrase as Eric's own
-- words, and without ever treating a draft or gate-PASS verdict as
-- execution authorization.
--
-- user_words is copied verbatim from the source workbench_messages row at
-- proposal-creation time and is never edited afterward — it is the only
-- column on this table that is Eric's own text. kind/outcome/action/
-- boundaries/success_criteria/unresolved_decisions are the model's
-- structured interpretation of that request, produced only when Eric
-- explicitly asked for a proposal (workbench_app.py's mode='draft_proposal'
-- on the same, single, existing Brain-gateway call boundary — never an
-- extra hidden model call). Eric can correct these fields (PATCH); doing so
-- bumps `revision` and clears approved_at/approved_by/approved_fingerprint
-- — a correction must never leave a stale approval looking current.
--
-- card_factory_ask_id / card_factory_card_id / card_runner_run_id are
-- filled in as the proposal moves through two separate, explicit actions:
-- "confirm direction" (creates/syncs a card_factory_asks row from
-- user_words/success_criteria and calls the existing bounded generator +
-- gate) and "approve" (calls card_runner.dispatch() directly, reusing its
-- own database validation, fingerprint binding and request_id dedup
-- unchanged). Neither a generated card nor a gate PASS verdict by itself
-- authorizes approve/dispatch — dispatch() re-validates independently.
--
-- request_id on this table is the same client-supplied id used for the
-- workbench_messages send that produced this proposal (draft_proposal
-- mode) — stored here only so a duplicate-resend lookup can find the
-- already-created proposal without a second parse/insert attempt.
--
-- This migration has NOT been applied to the live spine (data/cis_memory.db)
-- as part of this card. Additive only; applying it is an activation step.
--
-- Edited in place 2026-09-18 by card WB.1B-2B's own CORRECTION.md pass —
-- like 0036/0037's precedent, this migration has never been applied to any
-- database, so there is nothing to migrate away from. Added:
-- `confirmed_revision` — the proposal's own `revision` value at the moment
-- confirm-direction last successfully linked a card_factory_card_id.
-- Independent review found that action/boundary-only corrections bumped
-- `revision` but did not stale the linked card (only success_criteria
-- edits reached the ask, whose own revision is what dispatch() checks) —
-- approve() now requires `revision == confirmed_revision` in addition to
-- the caller's own expected_proposal_revision, so ANY material field edit
-- invalidates approval uniformly, not just ones that happen to touch the
-- ask.
--
-- Edited in place again 2026-09-18 by card WB.1B-3's own CORRECTION.md pass
-- — same "never applied to any database" precedent as the edit above, so
-- again nothing to migrate away from. Added `permitted_files_json` /
-- `permitted_commands_json`: the model's own proposed dispatch scope
-- (arrays of repo-relative file paths / shell command prefixes), produced
-- on the SAME single draft_proposal/revise_proposal model call as
-- kind/outcome/action/etc — never a second call. An independent review of
-- the UI card found it was asking Eric to hand-type technical file paths
-- as the normal approval path because no structured scope existed
-- anywhere to show him instead; these columns let the conversation surface
-- "here is what this action would touch" as a plain-language summary, with
-- `approve_proposal`'s existing `permitted_files`/`permitted_commands`
-- request fields populated FROM this stored scope instead of a blank
-- technical form. Default '[]' (empty JSON array), never NULL, so callers
-- can always safely `json.loads()` without a None-check.

CREATE TABLE IF NOT EXISTS workbench_action_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES workbench_projects(id),
    source_message_ids_json TEXT NOT NULL,
    user_words TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('mockup', 'experiment', 'implementation')),
    outcome TEXT,
    action TEXT,
    boundaries TEXT,
    success_criteria TEXT,
    unresolved_decisions TEXT,
    permitted_files_json TEXT NOT NULL DEFAULT '[]',
    permitted_commands_json TEXT NOT NULL DEFAULT '[]',
    revision INTEGER NOT NULL DEFAULT 1,
    confirmed_revision INTEGER,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed', 'approved')),
    approved_at TEXT,
    approved_by TEXT,
    approved_fingerprint TEXT,
    card_factory_ask_id INTEGER REFERENCES card_factory_asks(id),
    card_factory_card_id INTEGER REFERENCES card_factory_cards(id),
    card_runner_run_id INTEGER REFERENCES card_runner_runs(id),
    request_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_wb_proposals_project ON workbench_action_proposals(project_id, id);
CREATE INDEX IF NOT EXISTS idx_wb_proposals_request ON workbench_action_proposals(project_id, request_id);
CREATE INDEX IF NOT EXISTS idx_wb_proposals_card ON workbench_action_proposals(card_factory_card_id);
CREATE INDEX IF NOT EXISTS idx_wb_proposals_run ON workbench_action_proposals(card_runner_run_id);
