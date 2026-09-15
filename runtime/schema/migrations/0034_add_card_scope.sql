-- Add workflow_runs.card_scope
--
-- CARD: Connect Menter to its pipeline reviewers (implementation review stage)
-- Required by the deterministic apply gate (R6): condition (b) — "the diff
-- touches ONLY files declared in the card's scope" — is unenforceable without a
-- place to declare that scope. card_scope is a JSON array of repo-relative path
-- globs, e.g. ["runtime/mcp_bridge/spine.py", "tools/pipeline/*.py"], populated
-- by tools/pipeline/menter_dispatch.py at the point Menter is first dispatched.

ALTER TABLE workflow_runs ADD COLUMN card_scope TEXT;

-- Backfill: existing rows predate scope enforcement. An empty JSON array is the
-- safe default — it means the apply gate refuses to auto-apply anything for
-- these runs (condition (b) fails closed), never that everything is in scope.
UPDATE workflow_runs SET card_scope = '[]' WHERE card_scope IS NULL;
