-- Migration 0017: Persist circuit breaker state across process restarts
-- The in-memory dict was lost on crash/restart, allowing repeated attempts
-- at a dead gateway with no memory of prior failures.

CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    role TEXT PRIMARY KEY,
    failures INTEGER NOT NULL DEFAULT 0,
    last_failure_ts REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT ''
);
