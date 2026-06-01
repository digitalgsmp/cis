#!/usr/bin/env python3
"""
cis_migrate_041.py — DB Migration for ADR-041: Artifact Registry Schema

Creates the `manifests` table and adds required columns to `live_rounds`.
Safe to run multiple times — uses IF NOT EXISTS and checks before ALTER.

Usage:
    python3 /mnt/projects/cis/runtime/cis_migrate_041.py
    python3 /mnt/projects/cis/runtime/cis_migrate_041.py --dry-run
    python3 /mnt/projects/cis/runtime/cis_migrate_041.py --verify

Exit codes:
    0 = success / already applied
    1 = migration failed
    2 = error
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import PROJECTS_ROOT
    DB_PATH = Path(PROJECTS_ROOT) / "memory" / "cis_memory.db"
except ImportError:
    DB_PATH = Path(__file__).resolve().parent.parent / "memory" / "cis_memory.db"

MIGRATION_ID = "ADR-041"
MIGRATION_DESC = "Artifact registry: manifests table (with builder_model_id) + live_rounds verdict fields"


def ts_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

CREATE_MANIFESTS = """
CREATE TABLE IF NOT EXISTS manifests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id     TEXT NOT NULL,
    sha256          TEXT NOT NULL,
    artifact_type   TEXT NOT NULL,
    artifact_name   TEXT NOT NULL,
    artifact_path   TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    action          TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    builder_model_id TEXT NOT NULL DEFAULT '',
    manifest_path   TEXT,
    raw_manifest    TEXT,
    UNIQUE(artifact_id) ON CONFLICT REPLACE
);
"""

CREATE_MANIFESTS_IDX_ARTIFACT = """
CREATE INDEX IF NOT EXISTS idx_manifests_artifact_id ON manifests(artifact_id);
"""

CREATE_MANIFESTS_IDX_SESSION = """
CREATE INDEX IF NOT EXISTS idx_manifests_session_id ON manifests(session_id);
"""

# Columns to add to live_rounds — checked before adding (ALTER TABLE is not idempotent)
LIVE_ROUNDS_NEW_COLUMNS = [
    ("verdict",    "TEXT DEFAULT NULL",
     "Explicit resolved verdict: PASS, FAIL, or CONDITIONAL"),
    ("model_name", "TEXT DEFAULT NULL",
     "Name of the external model used for this audit round"),
    ("prompt",     "TEXT DEFAULT NULL",
     "Full prompt sent to the external model, logged verbatim"),
    ("response",   "TEXT DEFAULT NULL",
     "Full response received from the external model, logged verbatim"),
]

# Migration log table — tracks which migrations have been applied
CREATE_MIGRATION_LOG = """
CREATE TABLE IF NOT EXISTS migration_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    migration   TEXT NOT NULL,
    description TEXT,
    applied_at  TEXT NOT NULL,
    status      TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_existing_columns(cur: sqlite3.Cursor, table: str) -> set:
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def migration_already_applied(cur: sqlite3.Cursor, migration_id: str) -> bool:
    if not table_exists(cur, "migration_log"):
        return False
    cur.execute(
        "SELECT id FROM migration_log WHERE migration=? AND status='applied'",
        (migration_id,)
    )
    return cur.fetchone() is not None


def log_migration(cur: sqlite3.Cursor, migration_id: str, desc: str, status: str):
    cur.execute("""
        INSERT INTO migration_log (migration, description, applied_at, status)
        VALUES (?, ?, ?, ?)
    """, (migration_id, desc, ts_utc(), status))


# ---------------------------------------------------------------------------
# Migration steps
# ---------------------------------------------------------------------------

def step_migration_log(cur: sqlite3.Cursor, dry_run: bool) -> bool:
    print("  [1] Create migration_log table if not exists")
    if not dry_run:
        cur.execute(CREATE_MIGRATION_LOG)
    print("      OK")
    return True


def step_manifests_table(cur: sqlite3.Cursor, dry_run: bool) -> bool:
    print("  [2] Create manifests table")
    if table_exists(cur, "manifests"):
        print("      Already exists — checking for missing columns")
        existing_cols = get_existing_columns(cur, "manifests")

        # Fix 1 (ChatGPT v8): ALTER existing table to add builder_model_id if missing.
        # CREATE TABLE is skipped when table exists, so missing columns must be added here.
        cols_to_add = [
            ("builder_model_id", "TEXT NOT NULL DEFAULT ''",
             "Model that produced the artifact — required for role separation (ADR-040)"),
        ]
        for col_name, col_def, col_desc in cols_to_add:
            if col_name not in existing_cols:
                print(f"      Adding missing column '{col_name}': {col_desc}")
                if not dry_run:
                    cur.execute(
                        f"ALTER TABLE manifests ADD COLUMN {col_name} {col_def}"
                    )
                print(f"        Added")
            else:
                print(f"      Column '{col_name}' already present")
    else:
        if not dry_run:
            cur.execute(CREATE_MANIFESTS)
        print("      Created")

    print("  [3] Create manifests indexes")
    if not dry_run:
        cur.execute(CREATE_MANIFESTS_IDX_ARTIFACT)
        cur.execute(CREATE_MANIFESTS_IDX_SESSION)
    print("      OK")
    return True


def step_live_rounds_columns(cur: sqlite3.Cursor, dry_run: bool) -> bool:
    print("  [4] Add columns to live_rounds")

    if not table_exists(cur, "live_rounds"):
        print("      FAIL: live_rounds table does not exist.")
        print("           ADR-040 enforcement depends on verdict, model_name, prompt,")
        print("           and response columns in live_rounds. The table must exist")
        print("           before this migration can complete (ADR-041).")
        return False

    existing = get_existing_columns(cur, "live_rounds")

    for col_name, col_def, col_desc in LIVE_ROUNDS_NEW_COLUMNS:
        if col_name in existing:
            print(f"      Column '{col_name}' already exists — skipping")
        else:
            print(f"      Adding column '{col_name}': {col_desc}")
            if not dry_run:
                cur.execute(f"ALTER TABLE live_rounds ADD COLUMN {col_name} {col_def}")
            print(f"        Added")

    return True


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def run_verify() -> int:
    print(f"\n{'=' * 60}")
    print("CIS MIGRATION VERIFY — ADR-041")
    print(f"DB: {DB_PATH}")
    print(f"{'=' * 60}\n")

    if not DB_PATH.exists():
        print(f"FAIL  DB not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    failures = 0

    # Check manifests table exists
    exists = table_exists(cur, "manifests")
    print(f"{'PASS' if exists else 'FAIL'}  manifests table exists")
    if not exists:
        failures += 1

    if exists:
        cols = get_existing_columns(cur, "manifests")
        required = {"artifact_id", "sha256", "artifact_type", "artifact_name",
                    "artifact_path", "session_id", "sequence", "action", "timestamp",
                    "builder_model_id"}
        for col in required:
            present = col in cols
            print(f"{'PASS' if present else 'FAIL'}  manifests.{col} column present")
            if not present:
                failures += 1

        # Check UNIQUE constraint via index
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND tbl_name='manifests' AND name='idx_manifests_artifact_id'"
        )
        idx = cur.fetchone()
        print(f"{'PASS' if idx else 'FAIL'}  idx_manifests_artifact_id index exists")
        if not idx:
            failures += 1

    # Check live_rounds columns
    if table_exists(cur, "live_rounds"):
        lr_cols = get_existing_columns(cur, "live_rounds")
        for col_name, _, col_desc in LIVE_ROUNDS_NEW_COLUMNS:
            present = col_name in lr_cols
            print(f"{'PASS' if present else 'FAIL'}  live_rounds.{col_name} column present")
            if not present:
                failures += 1
    else:
        print("FAIL  live_rounds table does not exist — ADR-040 enforcement cannot operate")
        failures += 1

    # Check migration log entry
    if table_exists(cur, "migration_log"):
        applied = migration_already_applied(cur, MIGRATION_ID)
        print(f"{'PASS' if applied else 'FAIL'}  migration_log records {MIGRATION_ID} as applied")
        if not applied:
            failures += 1

    conn.close()

    print()
    if failures == 0:
        print(f"Result: PASS — ADR-041 migration verified ({'' if failures == 0 else failures})")
        return 0
    else:
        print(f"Result: FAIL — {failures} check(s) failed")
        return 1


# ---------------------------------------------------------------------------
# Main migration
# ---------------------------------------------------------------------------

def run_migration(dry_run: bool = False) -> int:
    print(f"\n{'=' * 60}")
    print(f"CIS MIGRATION — {MIGRATION_ID}")
    print(f"{'[DRY RUN] ' if dry_run else ''}DB: {DB_PATH}")
    print(f"{'=' * 60}\n")

    if not DB_PATH.exists():
        print(f"ERROR: DB not found: {DB_PATH}")
        print("       Run from the VM where cis_memory.db exists.")
        return 2

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Fix 1 (ChatGPT v10): Create migration_log table FIRST before any read/write.
    # On a fresh DB, migration_log does not exist yet — must be created before
    # migration_already_applied() queries it or log_migration() writes to it.
    step_migration_log(cur, dry_run)
    if not dry_run:
        conn.commit()

    # Now safe to check whether this migration was previously applied.
    # Do NOT return early — schema steps are idempotent and must always run
    # to apply any columns added after initial deployment (ADR-041 Fix 2).
    already_applied = not dry_run and migration_already_applied(cur, MIGRATION_ID)
    if already_applied:
        print(f"Note: {MIGRATION_ID} previously logged as applied.")
        print(f"      Running schema steps anyway to apply any missing columns.\n")

    print(f"\nApplying migration: {MIGRATION_DESC}\n")

    try:
        ok = True
        ok = ok and step_manifests_table(cur, dry_run)
        ok = ok and step_live_rounds_columns(cur, dry_run)

        if not ok:
            print("\nMigration FAILED — rolling back")
            conn.rollback()
            conn.close()
            return 1

        if not dry_run:
            if already_applied:
                # Update timestamp to record re-run
                cur.execute("""
                    UPDATE migration_log SET applied_at = ?, description = ?
                    WHERE migration = ? AND status = 'applied'
                """, (ts_utc(), MIGRATION_DESC + " (re-run)", MIGRATION_ID))
            else:
                log_migration(cur, MIGRATION_ID, MIGRATION_DESC, "applied")
            conn.commit()
            print(f"\nMigration {MIGRATION_ID} applied successfully at {ts_utc()}")
        else:
            print(f"\n[DRY RUN] No changes written. Remove --dry-run to apply.")

        conn.close()
        return 0

    except Exception as e:
        print(f"\nERROR during migration: {e}")
        conn.rollback()
        conn.close()
        return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=f"CIS DB Migration: {MIGRATION_ID} — {MIGRATION_DESC}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cis_migrate_041.py                  # Apply migration
  python3 cis_migrate_041.py --dry-run        # Preview without writing
  python3 cis_migrate_041.py --verify         # Verify migration is applied
        """
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview migration steps without writing to DB")
    parser.add_argument("--verify", action="store_true",
                        help="Verify the migration has been applied correctly")
    args = parser.parse_args()

    if args.verify:
        sys.exit(run_verify())
    else:
        sys.exit(run_migration(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
