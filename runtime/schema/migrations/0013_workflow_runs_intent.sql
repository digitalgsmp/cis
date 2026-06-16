-- Migration 0013: Add intent column to workflow_runs
-- Eric's stated intent preserved separately from topic summary.
-- Intent = the underlying need/goal (why). Topic = what to build (what).
-- Reviewer uses intent to check proposals against purpose, not just structure.
ALTER TABLE workflow_runs ADD COLUMN intent TEXT;
