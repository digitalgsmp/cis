-- Migration 0026: gate_outcomes table
-- Part 6 of DETERMINISTIC_GUARDRAIL_SPECIFICATION.md — Self-Evolving Harness
-- Stores every guardrail pass/fail alongside run results for adaptive threshold tuning.

CREATE TABLE IF NOT EXISTS gate_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,          -- brain, intent_review, draft, proposal_review, execution, verification
    role TEXT NOT NULL,           -- brain, draft, review1, review2, menter, verify
    guardrail_name TEXT NOT NULL, -- claim_action_verifier, sycophancy_detector, etc.
    verdict TEXT NOT NULL,        -- PASS, FAIL, SKIP
    mode TEXT DEFAULT 'ADVISORY',-- BLOCK or ADVISORY
    summary TEXT,
    evidence TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES workflow_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_gate_outcomes_run ON gate_outcomes(run_id);
CREATE INDEX IF NOT EXISTS idx_gate_outcomes_guardrail ON gate_outcomes(guardrail_name);
CREATE INDEX IF NOT EXISTS idx_gate_outcomes_verdict ON gate_outcomes(verdict);
