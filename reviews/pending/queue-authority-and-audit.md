CARD: QUEUE-AUTHORITY-AND-AUDIT
INTENT: Two phases. First the database becomes the queue's authority and gains a
history. Then every item is assessed against the code and marked, with the
evidence recorded beside the mark. Eric's decision, 2026-09-10.
SUPERSEDES the card queue-db-authority, which was phase 1 alone.
Back up first, state the paths. Phase 2 does not begin until phase 1's check 1
passes. No commit until both phases report.

--- WHY ---
The queue currently carries status as prose someone typed, mostly on 2026-08-29.
8 items say done, 3 partly, 42 say the need stands, 11 say nobody could tell, and
**56 say nothing at all**. Nothing derives any of it from the code. The list's
own rule is to re-check an item before working it, and nothing enforces that —
that is item 2.39.

The two phases are one job because **the audit is only worth doing if its result
persists.** Under the current design every extraction deletes 120 rows and
rewrites them from the markdown, so an assessment would be erased by the next
edit. Authority has to move first or the audit evaporates.

═══════════ PHASE 1 — THE DATABASE BECOMES THE AUTHORITY ═══════════

--- STEP 1 (read-only): confirm what breaks ---
Report each:
  a. sqlite3 data/cis_memory.db "select count(*), count(need_status) from queue_items"
  b. readers of the markdown:
     grep -rln "UNIFIED_BUILD_LIST" --include=*.py --include=*.sh tools/ runtime/ config/
  c. readers of the table:
     grep -rln "queue_items" --include=*.py --include=*.sh tools/ runtime/
  d. IS THE SPINE IN GIT?  git check-ignore -v data/cis_memory.db
  e. tools/queue/verify_queue_items.py — all 32 checks, pass/fail
If (d) shows the spine is untracked, do NOT stop — Step 3D is the answer to it —
but report it before continuing, because it is the fact that decides whether the
queue stays in version control.

--- STEP 2: backup ---
cp docs/UNIFIED_BUILD_LIST.md data/backups/UNIFIED_BUILD_LIST_$(date -u +%Y%m%dT%H%M%SZ).md
sqlite3 data/cis_memory.db ".dump queue_items" > data/backups/queue_items_$(date -u +%Y%m%dT%H%M%SZ).sql
cp tools/queue/extract_queue_items.py data/backups/
State all three. The markdown backup is the true rollback: if this is wrong, the
file is still the entire queue.

--- STEP 3: the build ---
A. The current extractor runs one final time, then refuses to run without
   --force. After the flip it would overwrite authority with a copy.

B. Migration 0032 — no data loss, existing columns untouched:
     queue_items      + status_changed_at, status_changed_by
     queue_item_events  item_num, field, old_value, new_value,
                        changed_at, changed_by, evidence, note
   Append-only. `evidence` is the column that makes phase 2 mean anything: it
   holds the command output that justified the change, not a claim that one
   exists.

C. Writes go through a tool, never raw SQL:
     tools/queue/queue_set.py <item_num> --status <VALUE>
                              --evidence "<command output>" --note "<why>"
   Refuses unknown items and unknown statuses. Writes the change and its event
   row in one transaction. Prints before and after.

D. tools/queue/render_build_list.py writes the markdown FROM the table with a
   DO NOT EDIT banner, wired into the pre-commit hook that already regenerates
   six files. **This is what keeps the queue in version control** — the spine is
   a binary nobody can diff; the rendered file is committed on every change, so
   git holds a readable history generated from the authority rather than being
   it. Same relationship AGENTS.md already has.

--- STEP 4: verify phase 1 ---
1. Render the markdown from the table, diff against the Step 2 backup.
   EXPECT: no differences except the banner. **LOAD-BEARING.** A table that
   cannot reproduce the file is not the authority. If this fails: restore, stop,
   report. Do not repair forward and do not start phase 2.
2. Change one item's status with the tool; confirm the row changed, an event row
   exists with old and new values, and the render reflects it.
3. Render twice — the second produces no diff.
4. Run the old extractor with --force, then confirm queue_item_events survived.
5. All 32 existing checks still pass.

═══════════ PHASE 2 — ASSESS ALL 120 ITEMS ═══════════

**Gate: phase 2 does not begin unless check 1 above passed.**

--- STEP 5: classify every item, do not assess yet ---
For each of the 120, find its "The one check that settles it" line and sort into:
  RUNNABLE   the check names something a command settles — a file, a table, a
             column, a grep, a count, a port
  JUDGMENT   the check asks whether something is still wanted, worth doing, or
             right. No command settles it.
  NO_CHECK   no check is written
Report the three counts and the item numbers in each. **Report before assessing.**
The ratio decides whether this audit is mostly measurement or mostly opinion,
and Eric should see it before the work runs.

--- STEP 6: assess the RUNNABLE ones, one at a time ---
For each: run its stated check. Capture the actual output. Then mark:
  DONE          the check proves the thing exists and does what the item asked
  OPEN          the check proves it does not
  PARTLY        the check proves some of it
Record via queue_set.py with the command output in --evidence.

**THE RULE THAT MAKES THIS DIFFERENT FROM WHAT IS THERE NOW: an item may only be
marked from command output. No item is marked because Claude Code believes it.**
If the check runs and the result is ambiguous, mark it UNCLEAR and record why —
an honest unknown beats a confident wrong mark, and 56 items already say nothing
because nobody wanted to write one down.

**Do not mark "works as intended" for anything in the container pipeline path.**
A code run has never completed end to end (1.23) and pytest is installed on no
interpreter here (3.28). For those, the strongest honest mark is
PRESENT_UNPROVEN: the code exists, its behaviour is untested.

--- STEP 7: the other two buckets ---
JUDGMENT items: do not guess. Mark NEEDS_ERIC and record the question the item
asks, so they arrive as a list of decisions rather than 40 unread items.
NO_CHECK items: mark NO_CHECK_WRITTEN. These cannot be assessed by anyone until
someone states what evidence would settle them. That list is itself a finding.

--- STEP 8: report ---
  * the three classification counts
  * every status that CHANGED, with the command output that changed it
  * every item marked UNCLEAR and why
  * the NEEDS_ERIC list as questions, in plain language
  * the NO_CHECK_WRITTEN list
  * the render diff after all the marking, proving the file still reproduces

DONE WHEN: the markdown renders byte-faithfully from the table; a status change
writes both the row and its evidence; every one of the 120 items carries either a
mark backed by command output, or an explicit NEEDS_ERIC / NO_CHECK_WRITTEN /
PRESENT_UNPROVEN; and nothing is marked on Claude Code's word alone.

IF ANY CHECK FAILS: stop, restore, report. Do not repair forward.

NOT IN THIS CARD:
  * Deleting the markdown. It stays, generated and committed.
  * Changing what any item SAYS. This card changes status and evidence only.
  * Writing checks for the NO_CHECK items. Naming them is the deliverable.
  * Answering the NEEDS_ERIC questions.
  * 1.22, retrieval, the reply path, closeout.

SCALE, STATED HONESTLY: phase 2 is 120 items assessed individually. This is a
long card. It should report progress in batches rather than going silent, and if
the classification in Step 5 shows most items are JUDGMENT or NO_CHECK, the
audit is worth less than it costs and Eric should be told that before Step 6
runs rather than after.
