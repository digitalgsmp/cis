-- Migration 0022: Projects Table + Multi-Project Support
-- Per ADR-SEED-010: --project-root model (filesystem isolation).
-- Each project gets own spine DB. Shared toolchain, isolated state.

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,                -- 'cis', 'swa', 'wias'
    name TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    spine_path TEXT NOT NULL,           -- path to cis_memory.db for this project
    agents_md_path TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Register CIS as the default project
INSERT OR IGNORE INTO projects (id, name, repo_path, spine_path, agents_md_path)
VALUES ('cis', 'CIS', '/mnt/projects/cis', '/mnt/projects/cis/data/cis_memory.db', '/mnt/projects/cis/AGENTS.md');

-- Add project_id to workflow_runs for per-project run tracking
ALTER TABLE workflow_runs ADD COLUMN project_id TEXT DEFAULT 'cis';
