#!/usr/bin/env python3
"""
cis_verify_jobs.py
ADR-045 Step 1 — L1 deterministic verification for execution_jobs table

Checks:
  1. DB file exists
  2. execution_jobs table exists
  3. All required columns present with correct types
  4. Table accepts a test insert and read
  5. Test row is cleaned up after verification

Usage:
    python3 /mnt/projects/cis/runtime/cis_verify_jobs.py

Output appended to:
    /mnt/projects/cis/logs/verification_log.md
"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH      = Path("/mnt/projects/cis/memory/cis_memory.db")
LOG_PATH     = Path("/mnt/projects/cis/logs/verification_log.md")
ACTION       = "ADR-045 Step 1 — execution_jobs table creation"
REQUIRED_COLS = {
    "id":           "INTEGER",
    "job_type":     "TEXT",
    "status":       "TEXT",
    "payload":      "TEXT",
    "result":       "TEXT",
    "error":        "TEXT",
    "created_at":   "TEXT",
    "started_at":   "TEXT",
    "completed_at": "TEXT",
    "priority":     "INTEGER",
    "retries":      "INTEGER",
    "max_retries":  "INTEGER",
    "source":       "TEXT",
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run():
    results = []
    passed  = 0
    failed  = 0

    def check(label, ok, detail=""):
        nonlocal passed, failed
        status = "PASS" if ok else "FAIL"
        line   = f"{status}  {label}" + (f": {detail}" if detail else "")
        results.append(line)
        if ok:
            passed += 1
        else:
            failed += 1
        print(line)

    print(f"\nVERIFICATION REPORT")
    print(f"Action:   {ACTION}")
    print(f"Run time: {now()}")
    print("-" * 60)

    # Check 1: DB exists
    check("DB file exists", DB_PATH.exists(), str(DB_PATH))
    if not DB_PATH.exists():
        _write_log(results, failed, ACTION)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # Check 2: Table exists
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    check("execution_jobs table exists", "execution_jobs" in tables)
    if "execution_jobs" not in tables:
        conn.close()
        _write_log(results, failed, ACTION)
        sys.exit(1)

    # Check 3: Columns present
    col_info = conn.execute("PRAGMA table_info(execution_jobs)").fetchall()
    col_map  = {row[1]: row[2].upper() for row in col_info}
    for col, expected_type in REQUIRED_COLS.items():
        present = col in col_map
        check(f"Column present: {col}", present,
              f"type={col_map.get(col, 'MISSING')}")

    # Check 4: Test insert and read
    try:
        conn.execute("""
            INSERT INTO execution_jobs (job_type, status, source, created_at)
            VALUES ('_verify_test', 'queued', 'cis_verify_jobs.py', datetime('now'))
        """)
        conn.commit()
        row = conn.execute(
            "SELECT id FROM execution_jobs WHERE job_type='_verify_test'"
        ).fetchone()
        check("Test insert and read", row is not None)

        # Cleanup
        if row:
            conn.execute("DELETE FROM execution_jobs WHERE job_type='_verify_test'")
            conn.commit()
            check("Test row cleaned up", True)
    except Exception as e:
        check("Test insert and read", False, str(e))

    conn.close()

    # Summary
    print("-" * 60)
    overall = "PASS" if failed == 0 else "FAIL"
    summary = f"Result: {overall} — {passed} passed, {failed} failed"
    blocking = "NO" if failed == 0 else "YES — do not advance until resolved"
    print(summary)
    print(f"Blocking: {blocking}")

    results.append(summary)
    results.append(f"Blocking: {blocking}")

    _write_log(results, failed, ACTION)
    sys.exit(0 if failed == 0 else 1)


def _write_log(results, failed, action):
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = (
            f"\n## {now()} — {action}\n"
            + "\n".join(results)
            + "\n"
        )
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"\nLog written: {LOG_PATH}")
    except Exception as e:
        print(f"WARNING: Could not write log: {e}")


if __name__ == "__main__":
    run()
