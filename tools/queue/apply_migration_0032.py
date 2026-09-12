#!/usr/bin/env python3
"""apply_migration_0032.py — apply (or verify) the queue-authority schema.

BUILD LIST queue-authority-and-audit, phase 1. The ALTER TABLE ADD COLUMN
statements in 0032_queue_authority.sql are NOT idempotent in SQLite (no
`IF NOT EXISTS` for columns), so a blind re-run fails. This guard checks column
existence first, then applies only what is missing.

Usage:
    python3 tools/queue/apply_migration_0032.py           # apply
    python3 tools/queue/apply_migration_0032.py --verify  # exit 0 if applied
"""
import argparse
import os
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")


def columns(conn, table):
    return {r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)}


def apply(conn):
    changed = []
    existing = columns(conn, "queue_items")
    for name, ddl in (
        ("status_changed_at", "TEXT"),
        ("status_changed_by", "TEXT"),
    ):
        if name not in existing:
            conn.execute("ALTER TABLE queue_items ADD COLUMN %s %s" % (name, ddl))
            changed.append("queue_items." + name)

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS queue_item_events (
            id          INTEGER PRIMARY KEY,
            item_num    TEXT NOT NULL,
            field       TEXT NOT NULL,
            old_value   TEXT,
            new_value   TEXT,
            changed_at  TEXT NOT NULL DEFAULT (datetime('now')),
            changed_by  TEXT,
            evidence    TEXT,
            note        TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_queue_item_events_item
            ON queue_item_events(item_num);
        CREATE TABLE IF NOT EXISTS queue_sections (
            seq         INTEGER PRIMARY KEY,
            kind        TEXT NOT NULL CHECK (kind IN ('preamble','tier_header')),
            content     TEXT NOT NULL,
            tier        INTEGER,
            source_line INTEGER,
            source_sha  TEXT NOT NULL
        );
        """
    )
    return changed


def verify(conn):
    ok = True
    cols = columns(conn, "queue_items")
    for name in ("status_changed_at", "status_changed_by"):
        present = name in cols
        print("%s queue_items.%s" % ("PASS" if present else "FAIL", name))
        ok = ok and present
    for table in ("queue_item_events", "queue_sections"):
        present = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone() is not None
        print("%s %s exists" % ("PASS" if present else "FAIL", table))
        ok = ok and present
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()

    conn = sqlite3.connect(DB)
    if a.verify:
        ok = verify(conn)
        conn.close()
        print("Result: %s" % ("PASS" if ok else "FAIL"))
        return 0 if ok else 1

    changed = apply(conn)
    conn.commit()
    conn.close()
    if changed:
        print("applied: %s" % ", ".join(changed))
    else:
        print("already applied — no changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
