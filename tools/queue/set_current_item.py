#!/usr/bin/env python3.12
"""Set which build-list item is being worked now.

BUILD LIST 3.21 / 2.30. Nothing anywhere designated a current item; the reader
answered "NOT AVAILABLE - nothing designates one" for that question.

WHY project_state AND NOT A COLUMN ON queue_items. queue_items is regenerated
wholesale from docs/UNIFIED_BUILD_LIST.md on every extraction, so a pointer
stored there is destroyed the next time anyone edits the markdown.
project_state is a different table, already carries keys of this kind
(build_phase, current_direction, next_action), and already has supersession
columns. No schema change.

THIS IS NOT current_direction OR next_action. Those hold prose about the phase
and the next action. This holds one build-list item number, and only that.

THE STALE POINTER IS THE DEFAULT FAILURE, NOT AN EDGE CASE -- GLM, 2026-09-09:
"nothing pushes the pointer forward when an item is done... it is worse than
NOT AVAILABLE because it provides false confidence that the system knows where
it is." Two guards, neither of which needs a trigger:

  * this setter REFUSES an item that is already DONE, so the pointer cannot be
    aimed at finished work in the first place;
  * the READER re-checks on every call and reports STALE rather than the item
    number once that item becomes DONE.

Together they turn the most likely failure from a false assertion into an
honest one. Neither makes the pointer advance by itself -- that is the next
card, and GLM named it.

Usage:
    python3.12 tools/queue/set_current_item.py <item_num>
    python3.12 tools/queue/set_current_item.py --clear
"""
import datetime
import os
import sqlite3
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "runtime"))
from db import state_authority as sa  # noqa: E402

DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
KEY = "current_queue_item"


def main():
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    arg = sys.argv[1]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = sqlite3.connect(DB)

    # Resolved through the one canonical resolver, not by this script's own
    # SELECT. The old query was `... superseded_at IS NULL` with fetchone():
    # with two live pointer rows it would have seen only one of them and
    # superseded only that one, leaving the other live. It now refuses.
    resolution = sa.resolve_current(conn, KEY)
    if resolution["status"] == sa.CONFLICT:
        print("REFUSED: %s" % resolution["note"])
        print("Rows: %s" % ", ".join(str(r.get("id")) for r in resolution["live_rows"]))
        print("Choosing between them is an authority decision, not this setter's.")
        return 1
    live = resolution["row"]

    if arg == "--clear":
        if not live:
            print("no current item set")
            return 0
        conn.execute("UPDATE project_state SET superseded_at=? WHERE id=?",
                     (now, live["id"]))
        conn.commit()
        print("cleared (was %s)" % live["value"])
        return 0

    row = conn.execute(
        "SELECT item_num, need_status, title FROM queue_items WHERE item_num=?",
        (arg,)).fetchone()
    if row is None:
        print("REFUSED: '%s' is not an item in queue_items." % arg)
        print("A pointer at a non-existent item is worse than none.")
        return 1
    if row[1] == "DONE":
        print("REFUSED: item %s is already DONE." % arg)
        print("Pointing at finished work is the stale-pointer failure by hand.")
        return 1

    # One atomic insert-and-supersede through the sanctioned writer. This
    # used to be three separate statements here — insert, then UPDATE
    # superseded_at, then UPDATE superseded_by — which is the "caller must
    # remember the supersession" shape that left next_action with two live
    # rows elsewhere in the repo.
    try:
        result = sa.set_state(conn, KEY, arg, "manual", created_at=now)
    except sa.StateAuthorityError as e:
        print("REFUSED: %s" % e)
        return 1
    print("current item: %s  (%s)" % (arg, (row[2] or "")[:56]))
    if result["superseded_row_ids"]:
        print("superseded:   %s (row %s)" % (live["value"], result["superseded_row_ids"][0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
