-- Migration 0023: Task Decomposition
-- Component 8 — Iterative Development
-- Allows breaking large directives into child runs with dependency tracking.

ALTER TABLE workflow_runs ADD COLUMN parent_run_id TEXT REFERENCES workflow_runs(id);

CREATE TABLE IF NOT EXISTS run_dependencies (
    run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    depends_on_run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    dependency_type TEXT NOT NULL DEFAULT 'sequential',
    PRIMARY KEY (run_id, depends_on_run_id)
);
