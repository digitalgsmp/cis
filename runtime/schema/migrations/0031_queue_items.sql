-- Migration 0031: queue_items — the unified build list as a table
--
-- BUILD LIST 3.21, serving 2.30 (the spine as the stateless agents' source of
-- truth). Reviewed by two lineages across three packets (queue-3.21-preflight,
-- queue-3.21-r2, queue-3.21-r3); the objections and what changed are in
-- reviews/done/.
--
-- WHAT THIS ANSWERS. 2.30 asks four questions. This table answers ONE outright:
-- "what was just done" (the 10 completion-bearing items). "What is the current
-- item" and "what does it depend on" require regenerated edges and are NOT
-- delivered here — see the queue-edges-disposition card. "Did it succeed" is
-- deliberately absent; see ADR-3.21-001 below.
--
-- DELIBERATELY ABSENT: any column linking an item to the run that advanced it,
-- or to whether that run succeeded. Proposed 2026-09-08 as
-- workflow_runs.queue_item_num and WITHDRAWN 2026-09-09 on dual-lineage review:
-- the join would inherit build list item 1.24 (phase rows marked 'success' on
-- runs that failed downstream) and would answer 2.30's fourth question WRONGLY
-- rather than not at all. Item 2.13 is the prerequisite for answering it
-- properly. This is a decision, not an oversight.
--
-- THE DECISION IS RECORDED IN project_decisions AS ADR-3.21-001, NOT ONLY HERE.
-- GLM raised, and Qwen independently agreed, that a DDL comment does not survive
-- a table rebuild: migration 0030 silently dropped two indexes on 2026-09-07
-- exactly that way, caught only because one lineage looked for it. This comment
-- is the copy a developer running `.schema queue_items` will see; the durable
-- copy is the project_decisions row, and this migration file is itself
-- version-controlled. Do not add a run-linking column without reading
-- ADR-3.21-001, build list 1.24, and 2.13 first.

CREATE TABLE IF NOT EXISTS queue_items (
    item_num        TEXT PRIMARY KEY,          -- '1.12', '3.21' — the identity
    tier            INTEGER NOT NULL,          -- from the item NUMBER, never the header
    title           TEXT NOT NULL,
    body_md         TEXT NOT NULL,             -- the item's prose, verbatim
    form            TEXT NOT NULL CHECK (form IN ('heading','bullet')),
    scope           TEXT,
    need_status     TEXT CHECK (need_status IS NULL OR need_status IN
                        ('OPEN','UNASSESSED','HALF_DONE','DONE','UNPARSED')),
    need_raw        TEXT,                      -- the literal prose the status came from
    source_line     INTEGER NOT NULL,          -- position at extraction, NOT an identity
    source_sha      TEXT NOT NULL,             -- sha256 of the whole markdown file
    extracted_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_queue_items_tier   ON queue_items(tier, item_num);
CREATE INDEX IF NOT EXISTS idx_queue_items_status ON queue_items(need_status);

-- The decision record. project_decisions is the repo's existing ADR form
-- (CLAUDE.md), it is not touched by a queue_items rebuild, and its status
-- vocabulary already carries SUPERSEDED for the day this is revisited.
INSERT OR REPLACE INTO project_decisions
    (id, label, decision, reason, status, decided_at)
VALUES (
    'ADR-3.21-001',
    'queue_items carries no run link and no success field',
    'queue_items answers what an item is and what its stated status is. It does '
    || 'not link an item to a workflow_run and does not record whether work on '
    || 'it succeeded. The proposed workflow_runs.queue_item_num column was '
    || 'withdrawn before implementation.',
    'Dual-lineage advisor review 2026-09-09 (queue-3.21-r2). The join would '
    || 'inherit build list item 1.24 — phase rows marked success on runs that '
    || 'failed downstream — so it would answer 2.30''s fourth question wrongly '
    || 'rather than not at all. GLM: "a join that returns a false positive is '
    || 'worse than no join at all." Item 2.13 is the prerequisite for answering '
    || 'it properly. Revisit only after 1.24 and 2.13.',
    'DECIDED',
    datetime('now')
);
