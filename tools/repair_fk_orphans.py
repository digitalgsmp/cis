#!/usr/bin/env python3.12
"""Clear the 24 orphaned rows left after the workflow_runs_old constraint repair.

Runs after tools/repair_fk_definitions.py, which fixed the stale constraint text
and took foreign_key_check from 80 down to 24. What remains is genuine orphan
data, in two kinds:

  15 eric_gate_approvals with goal_reference_id = 0
      Approvals recorded 8-11 July, before goal_references existed (its first row
      is 11 July 18:22). Zero was used as a stand-in in a NOT NULL column. These
      are real decisions, so they are backfilled, not deleted: each gets a
      goal_references row built from its run's topic, marked authored_by
      'BACKFILL_20260830' so it stays distinguishable from a goal Eric set at the
      gate. A sentinel row with id 0 was rejected as the fix — goal_references
      .workflow_run_id is NOT NULL and every lookup in the code reads
      "WHERE workflow_run_id = ? LIMIT 1", so a sentinel would have to attach to
      some real run and would then shadow that run's own goal trace.

   9 rows of June debris
      2 workflow_run_artifacts (git_head, 15 June) and 7 dispatch_events
      (17 June) whose parent rows no longer exist. Nothing references them.
      Deleted.

The point of reaching zero is that foreign_key_check only works as a signal from
a clean baseline: at 24 it says nothing, at 0 any future violation is a new
defect. (UNIFIED BUILD LIST 0.1, 2026-08-30)

Read-only by default. Pass --apply to write.
"""

import argparse
import os
import sqlite3
import sys

DEFAULT_DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
BACKFILL_TAG = "BACKFILL_20260830"


def zero_goal_approvals(conn):
    # Keyed on rowid, not id: eric_gate_approvals.id is a TEXT PRIMARY KEY, which
    # SQLite does not make implicitly NOT NULL (only INTEGER PRIMARY KEY, the
    # rowid alias, gets that). All 15 of these rows were written with a NULL id,
    # so "WHERE id = ?" matches nothing — NULL equals nothing, including itself.
    return conn.execute(
        "SELECT a.rowid, a.workflow_run_id, a.decided_at, w.topic "
        "FROM eric_gate_approvals a "
        "JOIN workflow_runs w ON a.workflow_run_id = w.id "
        "WHERE a.goal_reference_id = 0 "
        "ORDER BY a.decided_at"
    ).fetchall()


def orphan_artifacts(conn):
    return conn.execute(
        "SELECT a.id, a.artifact_type, a.run_id FROM workflow_run_artifacts a "
        "LEFT JOIN workflow_runs w ON a.run_id = w.id WHERE w.id IS NULL"
    ).fetchall()


def orphan_dispatch_events(conn):
    return conn.execute(
        "SELECT e.id, e.event_type, e.dispatch_id FROM dispatch_events e "
        "LEFT JOIN dispatch_log d ON e.dispatch_id = d.dispatch_id "
        "WHERE d.dispatch_id IS NULL"
    ).fetchall()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--apply", action="store_true", help="write the change (default is a dry run)")
    args = ap.parse_args()

    mode = "" if args.apply else "?mode=ro"
    conn = sqlite3.connect(f"file:{args.db}{mode}", uri=True)
    conn.execute("PRAGMA foreign_keys = ON")

    before = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    approvals = zero_goal_approvals(conn)
    artifacts = orphan_artifacts(conn)
    events = orphan_dispatch_events(conn)

    print(f"database: {args.db}")
    print(f"foreign_key_check violations before: {before}\n")

    print(f"BACKFILL — {len(approvals)} approvals need a goal_references row:")
    for _aid, run_id, decided_at, topic in approvals:
        print(f"  {decided_at[:19]}  {run_id[:30]}")
        print(f"      {(topic or '(no topic)')[:96]}")

    print(f"\nDELETE — {len(artifacts)} orphaned workflow_run_artifacts:")
    for rid, atype, run_id in artifacts:
        print(f"  id={rid} {atype} -> missing run {run_id[:30]}")

    print(f"\nDELETE — {len(events)} orphaned dispatch_events:")
    for rid, etype, dispatch_id in events:
        print(f"  id={rid} {etype} -> missing dispatch {dispatch_id[:30]}")

    if not args.apply:
        print("\nDry run. Nothing written. Re-run with --apply to make the change.")
        return 0

    print()
    try:
        conn.execute("BEGIN")
        for approval_rowid, run_id, decided_at, topic in approvals:
            # One goal per run: reuse an existing row if this run already has one.
            row = conn.execute(
                "SELECT id FROM goal_references WHERE workflow_run_id = ? "
                "ORDER BY id LIMIT 1",
                (run_id,),
            ).fetchone()
            if row:
                goal_id = row[0]
            else:
                cur = conn.execute(
                    "INSERT INTO goal_references "
                    "(workflow_run_id, goal_label, dependency_node, tier_advanced, "
                    " advancement_type, authored_by, created_at) "
                    "VALUES (?,?,'','','PIPELINE_RUN',?,?)",
                    (run_id, topic or "(no topic recorded)", BACKFILL_TAG, decided_at),
                )
                goal_id = cur.lastrowid
            conn.execute(
                "UPDATE eric_gate_approvals SET goal_reference_id = ? WHERE rowid = ?",
                (goal_id, approval_rowid),
            )

        conn.executemany(
            "DELETE FROM workflow_run_artifacts WHERE id = ?",
            [(r[0],) for r in artifacts],
        )
        conn.executemany(
            "DELETE FROM dispatch_events WHERE id = ?",
            [(r[0],) for r in events],
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"ABORT — rolled back, nothing written: {type(e).__name__}: {e}")
        return 1
    conn.close()

    check = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
    after = len(check.execute("PRAGMA foreign_key_check").fetchall())
    still_zero = check.execute(
        "SELECT COUNT(*) FROM eric_gate_approvals WHERE goal_reference_id = 0"
    ).fetchone()[0]
    backfilled = check.execute(
        "SELECT COUNT(*) FROM goal_references WHERE authored_by = ?", (BACKFILL_TAG,)
    ).fetchone()[0]
    approvals_total = check.execute(
        "SELECT COUNT(*) FROM eric_gate_approvals"
    ).fetchone()[0]
    check.close()

    print(f"integrity_check: {integrity}")
    print(f"goal_references rows created: {backfilled}")
    print(f"approvals still pointing at goal 0: {still_zero}")
    print(f"eric_gate_approvals total: {approvals_total} (unchanged, none deleted)")
    print(f"foreign_key_check violations after: {after} (was {before})")
    return 0 if integrity == "ok" and after == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
