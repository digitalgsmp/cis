-- Migration 0029: Intent provenance and drift tracking
-- Links the full chain: original intent → enriched intent → phase outputs → final result
-- Drift scores at each phase boundary detect when the pipeline diverges from intent

CREATE TABLE IF NOT EXISTS intent_provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    -- The anchor: what Eric actually asked for
    original_intent TEXT NOT NULL,
    -- Brain's enriched understanding (structured)
    enriched_intent TEXT,
    -- KB context that informed the enrichment
    kb_context_hash TEXT,
    -- Conversation session that produced this intent (if from brain chat)
    brain_session_id TEXT,
    -- When the intent was locked
    locked_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS phase_drift (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,              -- brain, intent_review, draft, proposal_review, menter, verify
    round INTEGER NOT NULL,
    -- The intent anchor at time of this phase
    intent_snapshot TEXT NOT NULL,    -- enriched intent (copied for immutability)
    -- What this phase produced
    phase_output TEXT,
    -- Drift score: 0.0 = perfectly aligned, 1.0 = completely diverged
    drift_score REAL,
    -- Drift reasons (JSON array of detected misalignments)
    drift_reasons TEXT,
    -- Verdict: ALIGNED, MINOR_DRIFT, SIGNIFICANT_DRIFT, DIVERGED
    verdict TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_provenance_run ON intent_provenance(run_id);
CREATE INDEX IF NOT EXISTS idx_drift_run ON phase_drift(run_id);
CREATE INDEX IF NOT EXISTS idx_drift_phase ON phase_drift(run_id, phase);
