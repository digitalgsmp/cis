CARD: QUEUE-DB-AUTHORITY
INTENT: The database becomes the queue's authority. The markdown becomes a
generated view of it. Eric's decision, 2026-09-10. This REVERSES the direction
shipped on 2026-09-09 and reviewed three times.
Back up first, state the paths. No commit until the reversal is proven.

--- WHY THE PREVIOUS DECISION WAS WRONG ---
The design shipped yesterday made `docs/UNIFIED_BUILD_LIST.md` authoritative and
`queue_items` a projection regenerated from it. The argument was: Eric authors
the queue in prose and cannot write SQL, so making the table authoritative puts
a coder between him and his own list.

**That premise is false. He does not edit the file — Claude Code does.** Every
build-list edit on 2026-09-08 and 2026-09-09 was made by a script. He states
intent; the writes are already code. The constraint the design was built around
does not exist.

**What the wrong direction cost, all observed within 24 hours:**
  * The queue has no history. Every extraction deletes 120 rows and rewrites
    them, so nothing records when an item changed status or why.
  * Nothing can be stored with an item that is not in the markdown. The
    current-item pointer had to go into a different table to survive.
  * State the loop produces is therefore scattered across four stores, which is
    2.12 generalised.
  * The projection went stale three times in one day; each was caught by hand.

--- STEP 1 (read-only): confirm what would be lost or broken ---
Report each:
  a. sqlite3 data/cis_memory.db "select count(*), count(need_status) from queue_items"
  b. every reader of the markdown:
     grep -rln "UNIFIED_BUILD_LIST" --include=*.py --include=*.sh tools/ runtime/ config/
  c. every reader of the table:
     grep -rln "queue_items" --include=*.py --include=*.sh tools/ runtime/
  d. is the spine in git?  git check-ignore -v data/cis_memory.db
  e. tools/queue/verify_queue_items.py — all 32 checks, current pass/fail
If (d) says the spine is untracked, STOP and report. It changes the card:
authority moving to an untracked file takes the queue out of version control,
and Step 3D exists to answer that.

--- STEP 2: backup ---
cp docs/UNIFIED_BUILD_LIST.md data/backups/UNIFIED_BUILD_LIST_$(date -u +%Y%m%dT%H%M%SZ).md
sqlite3 data/cis_memory.db ".dump queue_items" > data/backups/queue_items_$(date -u +%Y%m%dT%H%M%SZ).sql
cp tools/queue/extract_queue_items.py data/backups/
State all three paths. The markdown backup is the true rollback: if the reversal
is wrong, the file is still the whole queue.

--- STEP 3: THE BUILD ---

A. ONE-TIME MIGRATION, THEN THE DIRECTION FLIPS.
   The current extractor runs one final time. From that moment
   `tools/queue/extract_queue_items.py` is renamed to make its new status
   obvious and refuses to run without an explicit --force, because after the
   flip it would overwrite authority with a copy.

B. THE TABLE GAINS WHAT A FILE CANNOT HOLD.
   Migration 0032 adds to queue_items — no data loss, existing columns unchanged:
     status_changed_at   when need_status last changed
     status_changed_by   what changed it (a tool name, a run id, or 'operator')
   and a new table queue_item_events, one row per change:
     item_num, field, old_value, new_value, changed_at, changed_by, note
   This is the history the file never had. It is append-only.

C. WRITES GO THROUGH A TOOL, NEVER RAW SQL.
   tools/queue/queue_set.py <item_num> --status <VALUE> --note "<why>"
   It refuses an unknown item, refuses an unknown status, writes the change and
   the event row in one transaction, and prints the before and after.
   Adding or editing item text uses the same tool, not an editor.

D. THE MARKDOWN IS REGENERATED FROM THE TABLE AND STAYS IN GIT.
   tools/queue/render_build_list.py writes docs/UNIFIED_BUILD_LIST.md from
   queue_items, with a DO NOT EDIT banner naming the tool.
   **This is what keeps the queue in version control.** The spine is a binary
   nobody can diff; the rendered markdown is committed on every change, so git
   still holds a readable, diffable history of the queue — generated from the
   authority rather than being it. Same relationship AGENTS.md already has.
   Wired into the pre-commit hook that already regenerates six files.

E. THE ROUND-TRIP IS WHAT MAKES THIS SAFE.
   body_md is already stored verbatim per item, and the existing verification
   proves the partition is lossless — every row's text matches the file at its
   own lines, no overlaps, no gaps, no markers outside a row. That check is what
   makes rendering back out of the table trustworthy. Run it before and after.

--- STEP 4: verify by output ---
1. Render the markdown from the table and diff it against the backup taken in
   Step 2. EXPECT: no differences other than the DO NOT EDIT banner.
   This is the load-bearing check. If the render is not byte-faithful, the table
   is not yet capable of being the authority and the card STOPS here.
2. Change one item's status with the tool. Confirm: the table changed, an event
   row exists with old and new values, and the rendered markdown reflects it.
3. Re-render twice. The second render produces no diff.
4. Confirm the history survives what destroyed it before: run the OLD extractor
   with --force, then confirm queue_item_events still holds its rows.
5. All 32 existing checks still pass.
6. Ask the reader for an item and confirm it answers from the table.

--- STEP 5: report ---
The Step 1 findings, the Step 4 diff result in full, one event row printed
whole, and which of the 32 checks changed meaning now that the table is source.

DONE WHEN: the markdown renders byte-faithfully from the table, a status change
writes both the row and its history, re-rendering is stable, and the old
extractor cannot silently overwrite authority.

IF CHECK 1 FAILS: stop, restore the markdown from backup, report. Do not repair
forward. A table that cannot reproduce the file is not the authority yet.

NOT IN THIS CARD:
  * Deleting the markdown. It stays, generated and committed.
  * Any change to what the 120 items say.
  * The advisor loop's own record (1.22), retrieval, the reply path, closeout.
  * Backfilling history for changes made before this card. The event log starts
    empty and truthful rather than invented.
