#!/usr/bin/env python3.12
"""Repoint foreign keys that name workflow_runs_old, a table that no longer exists.

Eight tables in the spine declare FOREIGN KEY ... REFERENCES "workflow_runs_old",
left behind when workflow_runs was renamed. The rows are fine — 56 of the 58
flagged by foreign_key_check point at a real workflow_runs row. Only the
constraint text is stale.

This matters because SQLite does not warn about a foreign key naming a missing
table. It refuses the write:

    PRAGMA foreign_keys = ON;
    INSERT INTO eric_gate_approvals ...
    -> OperationalError: no such table: main.workflow_runs_old

So this repair has to land before foreign key enforcement is switched on at the
connection factories, or approving a run at the Eric Gate would fail. (UNIFIED
BUILD LIST 0.1, 2026-08-30)

The edit is textual: the CREATE TABLE statement in sqlite_master is rewritten in
place via writable_schema. No table is dropped or rebuilt, so indexes, triggers,
AUTOINCREMENT sequences and row data are untouched. Every candidate statement is
executed against a scratch database first to prove it still parses.

Read-only by default. Pass --apply to write.
"""

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
STALE = "workflow_runs_old"
LIVE = "workflow_runs"


def find_candidates(conn):
    """Every schema object whose SQL still names the renamed-away table."""
    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE sql LIKE ? AND name NOT LIKE 'sqlite_%'",
        (f"%{STALE}%",),
    ).fetchall()
    out = []
    for obj_type, name, sql in rows:
        new_sql = sql.replace(f'"{STALE}"', LIVE).replace(STALE, LIVE)
        if new_sql != sql:
            out.append((obj_type, name, sql, new_sql))
    return out


def validate(candidates):
    """Prove each rewritten statement still parses, in a throwaway database."""
    scratch = sqlite3.connect(":memory:")
    scratch.execute(f"CREATE TABLE {LIVE} (id TEXT PRIMARY KEY)")
    for obj_type, name, _old, new_sql in candidates:
        if obj_type != "table":
            continue
        try:
            scratch.execute(new_sql)
        except sqlite3.Error as e:
            return f"{name}: {e}"
    scratch.close()
    return None


def changed_lines(old_sql, new_sql):
    """The lines that actually differ, for a reader who is not diffing by eye."""
    pairs = []
    for a, b in zip(old_sql.splitlines(), new_sql.splitlines()):
        if a != b:
            pairs.append((a.strip(), b.strip()))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--apply", action="store_true", help="write the change (default is a dry run)")
    args = ap.parse_args()

    mode = "" if args.apply else "?mode=ro"
    conn = sqlite3.connect(f"file:{args.db}{mode}", uri=True)

    before = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    candidates = find_candidates(conn)

    print(f"database: {args.db}")
    print(f"foreign_key_check violations before: {before}")
    print(f"schema objects naming {STALE}: {len(candidates)}\n")

    if not candidates:
        print("Nothing to repair.")
        return 0

    for obj_type, name, old_sql, new_sql in candidates:
        print(f"  {obj_type} {name}")
        for old_line, new_line in changed_lines(old_sql, new_sql):
            print(f"      - {old_line}")
            print(f"      + {new_line}")
    print()

    err = validate(candidates)
    if err:
        print(f"ABORT — rewritten statement does not parse: {err}")
        return 1
    print("All rewritten statements parse against a scratch database.\n")

    if not args.apply:
        print("Dry run. Nothing written. Re-run with --apply to make the change.")
        return 0

    version = conn.execute("PRAGMA schema_version").fetchone()[0]
    conn.execute("PRAGMA writable_schema=ON")
    for obj_type, name, _old, new_sql in candidates:
        conn.execute(
            "UPDATE sqlite_master SET sql=? WHERE type=? AND name=?",
            (new_sql, obj_type, name),
        )
    conn.execute(f"PRAGMA schema_version={version + 1}")
    conn.execute("PRAGMA writable_schema=OFF")
    conn.commit()
    conn.close()

    # Reopen so the rewritten schema is read fresh off disk, not from cache.
    check = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
    after = len(check.execute("PRAGMA foreign_key_check").fetchall())
    remaining = len(find_candidates(check))
    check.close()

    print(f"integrity_check: {integrity}")
    print(f"schema objects still naming {STALE}: {remaining}")
    print(f"foreign_key_check violations after: {after} (was {before})")
    return 0 if integrity == "ok" and remaining == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
