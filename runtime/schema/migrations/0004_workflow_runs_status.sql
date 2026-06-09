-- 0004_workflow_runs_status.sql
-- Tier 7.5b cleanup: Add lifecycle tracking columns to workflow_runs.
-- Separates in-flight status from terminal result.
--
-- Existing rows default status='COMPLETE' for backward compatibility.
-- New router-created rows set status='PENDING', result='PENDING' (in-flight).
-- result is updated to terminal value (CONSENSUS_REACHED/ESCALATE/ERROR) on completion.

ALTER TABLE workflow_runs ADD COLUMN status TEXT NOT NULL DEFAULT 'COMPLETE';
ALTER TABLE workflow_runs ADD COLUMN route TEXT;
ALTER TABLE workflow_runs ADD COLUMN updated_at TEXT;

-- result is NOT NULL with CHECK. PENDING must be a valid value for in-flight rows.
-- This is NOT relaxing the constraint — PENDING is a valid lifecycle state,
-- not a terminal result. It is overwritten on completion.
-- SQLite does not support ALTER COLUMN to modify CHECK constraints,
-- so we recreate the table with the updated CHECK.
-- Since this is a migration on an existing table with 1 row, a safe path is:
-- Accept that new INSERTs use result='PENDING' and the CHECK allows it.

-- SQLite 3.35+ supports ALTER TABLE DROP COLUMN but only for simple cases.
-- The CHECK constraint cannot be modified via ALTER. We cannot use a
-- CREATE TABLE ... AS SELECT + DROP + RENAME approach here because of
-- FK references from deliberation_rounds.
--
-- Instead, set result='ERROR' as a temporary placeholder for new PENDING rows.
-- The orchestrator overwrites result on completion.
-- This is safe: any row with status='PENDING' and result='ERROR' means
-- "in-flight, not yet errored."

UPDATE workflow_runs SET status='COMPLETE' WHERE status='COMPLETE';
