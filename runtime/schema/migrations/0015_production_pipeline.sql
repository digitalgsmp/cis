-- Migration 0015: Production pipeline schema extensions
-- Per SPEC_PRODUCTION_PIPELINE_RELAY.md (REV-2, 2026-07-08)
-- Adds: deliberation_rounds output columns, agent_trajectories table,
--   agent_trajectories_fts, workflow_runs.directive_hash
-- Note: drafter_output already exists on deliberation_rounds — do NOT re-add.
-- Note: intent_map, anti_patterns, functional_spec, reviewer_brief already exist.

-- ── deliberation_rounds: add missing output columns (OQ-SEED-006) ──
ALTER TABLE deliberation_rounds ADD COLUMN reviewer1_output TEXT;
ALTER TABLE deliberation_rounds ADD COLUMN reviewer2_output TEXT;
ALTER TABLE deliberation_rounds ADD COLUMN brain_output TEXT;
ALTER TABLE deliberation_rounds ADD COLUMN verify_output TEXT;
ALTER TABLE deliberation_rounds ADD COLUMN human_question TEXT;
ALTER TABLE deliberation_rounds ADD COLUMN human_answer TEXT;

-- ── workflow_runs: add directive hash for Eric Gate freeze ──
ALTER TABLE workflow_runs ADD COLUMN directive_hash TEXT;

-- ── agent_trajectories: MATM shared memory ──
CREATE TABLE IF NOT EXISTS agent_trajectories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    role TEXT NOT NULL,
    phase TEXT NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    feedback_text TEXT,
    round_number INTEGER,
    outcome TEXT DEFAULT 'pending',
    consensus_reached INTEGER DEFAULT 0,
    config_version TEXT,
    marginal_utility REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trajectories_run
    ON agent_trajectories(run_id);
CREATE INDEX IF NOT EXISTS idx_trajectories_role_phase
    ON agent_trajectories(role, phase);
CREATE INDEX IF NOT EXISTS idx_trajectories_outcome
    ON agent_trajectories(outcome);

-- ── agent_trajectories_fts: full-text search for trajectory retrieval ──
CREATE VIRTUAL TABLE IF NOT EXISTS agent_trajectories_fts USING fts5(
    input_text, output_text, role, phase,
    content='agent_trajectories',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS trajectories_ai AFTER INSERT ON agent_trajectories BEGIN
    INSERT INTO agent_trajectories_fts(rowid, input_text, output_text, role, phase)
    VALUES (new.id, new.input_text, new.output_text, new.role, new.phase);
END;

CREATE TRIGGER IF NOT EXISTS trajectories_ad AFTER DELETE ON agent_trajectories BEGIN
    INSERT INTO agent_trajectories_fts(agent_trajectories_fts, rowid, input_text, output_text, role, phase)
    VALUES ('delete', old.id, old.input_text, old.output_text, old.role, old.phase);
END;

CREATE TRIGGER IF NOT EXISTS trajectories_au AFTER UPDATE ON agent_trajectories BEGIN
    INSERT INTO agent_trajectories_fts(agent_trajectories_fts, rowid, input_text, output_text, role, phase)
    VALUES ('delete', old.id, old.input_text, old.output_text, old.role, old.phase);
    INSERT INTO agent_trajectories_fts(rowid, input_text, output_text, role, phase)
    VALUES (new.id, new.input_text, new.output_text, new.role, new.phase);
END;
