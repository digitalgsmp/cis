#!/usr/bin/env python3
"""queue_set.py — the sole write path for the queue's status.

BUILD LIST queue-authority-and-audit, step 3C. The database is the authority;
a status change goes through this tool, never raw SQL, so every change carries
an append-only event row with the evidence that justified it. That is the
column that makes the phase-2 audit mean anything: no mark on a belief.

Usage:
    python3 tools/queue/queue_set.py <item_num> --status <VALUE> \
        [--evidence "<command output>"] [--note "<why>"] [--by "<who>"]

Refuses unknown items and unknown statuses. Evidence (command output) is
required for statuses that assert a code fact: DONE, OPEN, PARTLY,
PRESENT_UNPROVEN, UNCLEAR. NEEDS_ERIC and NO_CHECK_WRITTEN carry a note — a
question or explanation — instead, since those are decisions, not measurements.
"""
import argparse
import datetime
import os
import sqlite3
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

KNOWN = {
    "OPEN", "UNASSESSED", "HALF_DONE", "DONE", "UNPARSED",
    "PARTLY", "UNCLEAR", "PRESENT_UNPROVEN", "NEEDS_ERIC", "NO_CHECK_WRITTEN",
}
EVIDENCE_REQUIRED = {"DONE", "OPEN", "PARTLY", "PRESENT_UNPROVEN", "UNCLEAR"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("item_num")
    ap.add_argument("--status", required=True)
    ap.add_argument("--evidence", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--by", default="")
    a = ap.parse_args()

    status = a.status.upper()
    if status not in KNOWN:
        print("unknown status: %r" % a.status)
        print("known: %s" % ", ".join(sorted(KNOWN)))
        return 2

    if status in EVIDENCE_REQUIRED and not a.evidence.strip():
        print("--evidence is required for %s." % status)
        print("The rule is: no mark without the command output that justified it.")
        return 2

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT need_status FROM queue_items WHERE item_num=?", (a.item_num,)
    ).fetchone()
    if row is None:
        conn.close()
        print("unknown item: %r (not in queue_items)" % a.item_num)
        return 2
    old = row[0]

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    who = a.by or os.environ.get("USER", "")

    conn.execute("BEGIN IMMEDIATE")
    cur.execute(
        "UPDATE queue_items SET need_status=?, status_changed_at=?, status_changed_by=? "
        "WHERE item_num=?",
        (status, now, who, a.item_num))
    cur.execute(
        "INSERT INTO queue_item_events "
        "(item_num, field, old_value, new_value, changed_at, changed_by, evidence, note) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (a.item_num, "need_status", old, status, now, who, a.evidence, a.note))
    conn.commit()
    conn.close()

    print("item %s: %r -> %r" % (a.item_num, old, status))
    if a.evidence:
        print("evidence: %s" % a.evidence[:300])
    if a.note:
        print("note: %s" % a.note[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
