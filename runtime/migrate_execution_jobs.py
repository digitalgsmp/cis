#!/usr/bin/env python3
"""
migrate_execution_jobs.py
ADR-045 Step 1 — Create execution_jobs table in cis_memory.db

Idempotent: safe to run multiple times.
Canonical DB: /mnt/projects/cis/memory/cis_memory.db

Usage:
    python3 /mnt/projects/cis/runtime/migrate_execution_jobs.py
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("/mnt/projects/cis/memory/cis_memory.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type        TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'queued',
    payload         TEXT,
    result          TEXT,
    error           TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    started_at      TEXT,
    completed_at    TEXT,
    priority        INTEGER NOT NULL DEFAULT 5,
    retries         INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 1,
    source          TEXT
)
"""

# Valid status values (for documentation — not enforced by SQLite)
# queued | running | complete | failed | cancelled

COLUMN_DOCS = {
    "id":           "Auto-incrementing primary key",
    "job_type":     "Type of work: verify_contract | run_l2 | (future types)",
    "status":       "queued | running | complete | failed | cancelled",
    "payload":      "JSON string — job-type-specific input parameters",
    "result":       "JSON string — job output on completion",
    "error":        "Error message string if status=failed",
    "created_at":   "UTC datetime when job was enqueued",
    "started_at":   "UTC datetime when worker picked up the job",
    "completed_at": "UTC datetime when job reached terminal state",
    "priority":     "Lower number = higher priority (reserved for future use)",
    "retries":      "Number of retry attempts made",
    "max_retries":  "Maximum retries allowed before marking failed",
    "source":       "Originating route or system that enqueued the job",
}


def run():
    if not DB_PATH.exists():
        print(f"FAIL  DB not found: {DB_PATH}")
        sys.exit(1)

    print(f"Connecting to: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute(SCHEMA)
        conn.commit()
        print("PASS  execution_jobs table created (or already existed)")
    except Exception as e:
        print(f"FAIL  Schema creation error: {e}")
        conn.close()
        sys.exit(1)

    # Verify columns are present
    cursor = conn.execute("PRAGMA table_info(execution_jobs)")
    cols = {row[1] for row in cursor.fetchall()}
    expected = set(COLUMN_DOCS.keys())
    missing = expected - cols

    if missing:
        print(f"FAIL  Missing columns: {missing}")
        conn.close()
        sys.exit(1)

    print(f"PASS  All {len(expected)} columns verified")
    for col in sorted(cols):
        print(f"      ✓ {col}")

    conn.close()
    print("\nMigration complete. Run cis_verify_jobs.py to confirm.")


if __name__ == "__main__":
    run()
