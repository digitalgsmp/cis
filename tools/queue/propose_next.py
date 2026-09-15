#!/usr/bin/env python3
"""propose_next.py — answer 'what's next?' in the operator's plain language.

BUILD LIST 4.1 + the queue-authority classifier. This is the deterministic
answer to 'what's next / what else should we do / what's left'. It reads the
queue (queue_items + check_class) and the current-item pointer, and says, in
Eric's shape, not the machinery's:

  * the ONE next thing to work on and why it is next
  * the few after it, in order
  * the decisions only Eric can make (JUDGMENT), as questions

No component names, no file names, no card names, no assumption he remembers a
previous session. The queue order is the dependency order (TIER 0 before TIER 1
...); RUNNABLE items surface ahead of JUDGMENT items within a tier because a
runnable item can be advanced without Eric.

This does NOT advance the pointer by itself. It only says what is next. The
pointer advances when a piece of work actually finishes (set_current_item.py),
or when Eric directs it — never on its own.

Usage:
    python3 tools/queue/propose_next.py [--top N] [--ingest]
      --top N    how many of the ordered next-items to show (default 5)
      --ingest   fire session ingest first (the 4.1 trigger, off by default)
"""
import argparse
import os
import sqlite3
import subprocess
import sys

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
INGEST = os.environ.get(
    "CIS_INGEST_TOOL", "/mnt/projects/cis/tools/ingest_hermes_sessions_v2.py")

# check_class -> sort key within a tier: runnable before judgment before the
# (rare) unclassifiable, because runnable is advanceable without Eric.
_CLASS_RANK = {"RUNNABLE": 0, "JUDGMENT": 1, "NO_CHECK": 2}


def fire_ingest():
    print("ingesting sessions ...", file=sys.stderr, flush=True)
    r = subprocess.run([sys.executable, INGEST], capture_output=True, text=True)
    if r.returncode != 0:
        print("ingest failed:\n%s" % r.stderr[-2000:], file=sys.stderr)
        return False
    print("ingest done.", file=sys.stderr)
    return True


def current_item(conn):
    row = conn.execute(
        "SELECT value FROM project_state WHERE key='current_queue_item' "
        "AND superseded_at IS NULL").fetchone()
    return row[0] if row else None


def status_plain(status):
    return {
        "HALF_DONE": "half done",
        "OPEN": "not started",
        "UNASSESSED": "not checked yet",
        "DONE": "done",
    }.get(status, "no status written")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--ingest", action="store_true")
    a = ap.parse_args()

    if a.ingest:
        if not fire_ingest():
            return 1

    conn = sqlite3.connect(DB)

    # non-DONE items, in dependency order (tier), runnable first within a tier
    rows = conn.execute(
        "SELECT item_num, tier, title, need_status, check_class "
        "FROM queue_items "
        "WHERE need_status IS NULL OR need_status != 'DONE' "
        "ORDER BY tier, item_num").fetchall()
    # stable sort: within the tier order, put RUNNABLE ahead of JUDGMENT
    rows.sort(key=lambda r: (_CLASS_RANK.get(r[4], 2)))

    cur = current_item(conn)

    L = ["", "WHAT'S NEXT", "=" * 60, ""]

    if cur:
        cur_row = conn.execute(
            "SELECT title, need_status FROM queue_items WHERE item_num=?", (cur,)
        ).fetchone()
        if cur_row and (cur_row[1] is None or cur_row[1] != "DONE"):
            L.append("YOU WERE ON: %s — %s" % (cur, (cur_row[0] or "")[:70]))
            L.append("")

    runnable = [r for r in rows if r[4] == "RUNNABLE"]
    judgment = [r for r in rows if r[4] == "JUDGMENT"]

    if runnable:
        n, tier, title, status, _ = runnable[0]
        L.append("NEXT: %s — %s" % (n, (title or "")[:70]))
        if status:
            L.append("      (%s)" % status_plain(status))
        L.append("")
        if len(runnable) > 1:
            L.append("THEN, IN ORDER:")
            for n, tier, title, status, _ in runnable[1:a.top]:
                L.append("  %s. %s — %s" % (n, (title or "")[:62],
                                            status_plain(status) if status else ""))
            L.append("")

    if judgment:
        L.append("NEEDS YOUR DECISION (%d):" % len(judgment))
        for n, tier, title, status, _ in judgment:
            L.append("  %s. %s" % (n, (title or "")[:66]))
        L.append("")

    if not runnable and not judgment:
        L.append("Nothing is left to work on that is not already done.")

    L.append("-" * 60)
    L.append("%d items still open; %d need a decision only you can make."
             % (len(rows), len(judgment)))
    L.append("")
    print("\n".join(L))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
