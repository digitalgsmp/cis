-- Migration 0035: Workbench projects + Braingate conversation (queue item WB.1A)
--
-- Additive only. Does NOT touch the existing `projects` table (0022), which
-- requires a filesystem repo_path and is keyed to git-checkout repos, not to
-- Eric's planning work. workbench_projects is a separate, small durable
-- mapping for "start a project and talk to Braingate" that does not require
-- a repository path or any other technical choice up front.
--
-- kind distinguishes a planning project (no repo yet, the only kind this
-- slice creates) from a provisioned application repository (would map to a
-- `projects` row once that workflow exists — not built here, not implied).
--
-- This migration has NOT been applied to the live spine (data/cis_memory.db,
-- ~5.9GB) as part of this card. It is additive and safe to apply, but that is
-- an activation step for Codex/Eric to run deliberately, not something to do
-- to a multi-GB shared production file inside an implementation pass.
--
-- Edited in place 2026-09-18 by card WB.1B-2B (conversation actions) — like
-- 0036/0037's own precedent, this migration has never been applied to any
-- database, so there is nothing to migrate away from. Added: `context_meta`
-- on workbench_messages, a JSON record of which history messages/KB sources
-- were actually sent to the model for that call (budget, included/omitted
-- message ids, overflow flag) — "display which context was used," per the
-- bounded-control requirement on that card.

CREATE TABLE IF NOT EXISTS workbench_projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'planning' CHECK (kind IN ('planning', 'provisioned')),
    repo_path TEXT,
    direction_note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workbench_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES workbench_projects(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'brain')),
    content TEXT,
    status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'interrupted')),
    kb_context TEXT,
    error TEXT,
    context_meta TEXT,
    request_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_workbench_messages_project
    ON workbench_messages(project_id, id);

CREATE INDEX IF NOT EXISTS idx_workbench_messages_request
    ON workbench_messages(project_id, request_id);
