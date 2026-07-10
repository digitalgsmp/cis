-- Migration 0025: Agent Token Tracking
-- Component 12 — Monitoring and Observability
-- Tracks token usage per agent dispatch for cost analysis.

ALTER TABLE agent_trajectories ADD COLUMN tokens_in INTEGER DEFAULT 0;
ALTER TABLE agent_trajectories ADD COLUMN tokens_out INTEGER DEFAULT 0;
