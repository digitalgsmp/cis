CARD: QUEUE-AUTHORITY-V2
INTENT: The database becomes the queue's authority — not overwritable, not by a
flag. Status is a label. A label of DONE is LOCKED only after both reviewers
confirm the evidence proves it. Eric's decision, 2026-09-10.
SUPERSEDES queue-authority-and-audit, which was reviewed and found sound in
design but wrong on two points Eric corrected. Neither superseded card has run.
Back up first, state the paths. No commit until the reversal is proven.

--- WHAT V1 GOT WRONG, IN ERIC'S WORDS ---

**"If it is being made authoritative, why can it be over written."**
V1 kept the extractor and gated it behind `--force`. A source a flag can clobber
is not authoritative; it is a default. Authority has to be structural.

**"It should just be labels and after the reviewers prove it's evidence of being
completed it should be locked."**
V1 let Claude Code mark items DONE from its own command output. That is the same
party writing the work and certifying it — build list item 1.18 exactly, in the
one place where the whole queue's trustworthiness lives. A mark is a claim until
someone independent has seen the evidence.

**And a third, which Eric raised separately: nobody needs the markdown
regenerated.** Measured today — grepping `tools/`, `runtime/` and `config/` for
UNIFIED_BUILD_LIST returns one hit, a comment. No script parses it. The container
agents read the spine through MCP. The reviewers cannot read files at all. V1's
commit-time regeneration was a second representation of history nobody consumes,
which is 2.12 pointed a new way. Replaced with an export command.

═══════════ PHASE 1 — AUTHORITY THAT CANNOT BE OVERWRITTEN ═══════════

--- STEP 1 (read-only): report before touching anything ---
  a. sqlite3 data/cis_memory.db "select count(*), count(need_status) from queue_items"
  b. grep -rln "UNIFIED_BUILD_LIST" --include=*.py --include=*.sh tools/ runtime/ config/
  c. grep -rln "queue_items" --include=*.py --include=*.sh tools/ runtime/
  d. git check-ignore -v data/cis_memory.db
  e. tools/queue/verify_queue_items.py — all 32 checks
  f. confirm NEITHER superseded card ran: no queue_item_events table, no
     migration 0032, extractor unmodified. If any partial state exists, STOP and
     report it — a superseded card that was half-run leaves the system in a
     state this card's steps do not assume.

--- STEP 2: backup ---
cp docs/UNIFIED_BUILD_LIST.md data/backups/UNIFIED_BUILD_LIST_$(date -u +%Y%m%dT%H%M%SZ).md
sqlite3 data/cis_memory.db ".dump queue_items" > data/backups/queue_items_$(date -u +%Y%m%dT%H%M%SZ).sql
cp tools/queue/extract_queue_items.py data/backups/
State all three.

--- STEP 3: the build ---

A. THE IMPORT RUNS ONCE AND CANNOT RUN AGAIN. No --force.
   `extract_queue_items.py` becomes `import_build_list_once.py` and begins by
   refusing if `queue_items` already holds rows, or if `queue_item_events` holds
   any row. There is no flag that bypasses this. Overwriting authority is not
   made loud — it is made impossible without deleting rows by hand, which leaves
   its own trace.
   **Before the lock, prove the import actually populated the table:** row count
   equals the count of item markers in the markdown, and every item number in the
   file appears in the table. A silent no-op over pre-existing rows would
   otherwise pass every downstream check. (GLM, finding 1.)

B. MIGRATION 0032 — no data loss, existing columns untouched:
     queue_items      + status_changed_at, status_changed_by
                      + locked           INTEGER NOT NULL DEFAULT 0
                      + locked_at, locked_by, locked_evidence_ref
     queue_item_events  item_num, field, old_value, new_value,
                        changed_at, changed_by, evidence, note
   Append-only. A CHECK constraint on the permitted status values, so the
   vocabulary is enforced by the database and not only by the tool.
   (GLM, finding 8.)

C. STATUS IS A LABEL. THE TOOL IS THE ONLY WRITE PATH.
     tools/queue/queue_set.py <item_num> --status <VALUE>
                              --evidence "<command output>" --note "<why>"
   * refuses unknown items and unknown statuses
   * evidence must be NON-EMPTY for PROPOSED_DONE, OPEN, PARTLY and
     PRESENT_UNPROVEN. NEEDS_ERIC and NO_CHECK_WRITTEN may carry a note instead.
     Without this the no-mark-without-evidence rule is unenforced.
     (GLM, finding 2.)
   * **refuses outright to write DONE.** Nothing may set DONE directly. DONE is
     produced only by Step 3D.
   * refuses ANY change to an item where locked=1, and says so.
   * writes the change and its event row in one transaction, prints before/after.

D. DONE IS EARNED FROM THE REVIEWERS AND THEN LOCKED.
     tools/queue/queue_certify.py <item_num>
   1. Requires the item to be PROPOSED_DONE with non-empty evidence.
   2. Builds a packet: what the item asked for, the evidence, and the command
      output that produced it.
   3. Sends it to BOTH lineages as a result review — the existing round-3 shape,
      which already asks whether the evidence establishes the claim and what
      would look like success while being wrong.
   4. **Both must return ESTABLISHED.** One NOT_ESTABLISHED, one UNPARSED, or a
      failed lineage, and the item stays PROPOSED_DONE with the objection
      recorded against it.
   5. On two ESTABLISHED: status becomes DONE, `locked` becomes 1, and
      `locked_evidence_ref` points at the two deliberation_rounds rows that
      certified it.
   **Claude Code cannot mark an item done. It can only propose one.**

E. UNLOCKING IS POSSIBLE AND EXPENSIVE.
     tools/queue/queue_set.py <item_num> --unlock --reason "<why>"
   Writes an event row, clears the lock, sets status back to OPEN. There is no
   silent path. A locked item that turns out to be wrong is reopened on the
   record, which is what makes the lock honest rather than merely rigid.

F. THE MARKDOWN IS AN EXPORT, ON DEMAND, NOT A COMMITTED ARTIFACT.
     tools/queue/export_build_list.py > <path>
   Run when someone needs a file to hand to another model. Not wired to the
   pre-commit hook. Not regenerated on change. The event log is the history;
   a second copy of it in prose is the two-sources failure again.

--- STEP 4: verify phase 1 ---
1. The export reproduces the Step 2 backup byte-for-byte apart from a generated
   banner. **LOAD-BEARING** — a table that cannot reproduce the file is not the
   authority. If this fails: restore, stop, report, do not repair forward, do
   not start phase 2.
2. Run the import again. It REFUSES. No rows change.
3. queue_set.py --status DONE is REFUSED, with the reason printed.
4. A status change writes an event row whose old_value equals the status that
   was actually there before — not merely that a row exists. A wrong old_value
   means the history is already lying. (GLM, finding 7.)
5. queue_certify.py on an item with no evidence is REFUSED.
6. Take one genuinely finished item — 3.6, closed 2026-09-07 with a migration
   and a verifier — propose it, certify it, and confirm both lineages returned
   ESTABLISHED before the lock was set.
7. Any write to that item afterwards is REFUSED until --unlock.
8. All 32 existing checks still pass.

═══════════ PHASE 2 — ASSESS ALL 120 ITEMS ═══════════
**Gate: phase 2 does not begin unless check 1 passed.**

--- STEP 5: classify, report, and stop ---
Sort all 120 by their stated "one check that settles it":
  RUNNABLE   a command settles it
  JUDGMENT   it asks whether something is still wanted, worth doing, or right
  NO_CHECK   no check is written
**An item with ANY judgment component is JUDGMENT.** Classify by the
hardest-to-settle check it names; do not split an item and mark half of it.
(GLM, finding 4.)
Report the three counts and the item numbers. **Stop and report before Step 6.**
If most of the list is JUDGMENT or NO_CHECK, the audit costs more than it
returns and Eric should hear that before the work runs.

--- STEP 6: assess the RUNNABLE ones ---
Run each stated check. Capture actual output. Then propose a label:
  PROPOSED_DONE      the output shows it exists and does what the item asked
  OPEN               the output shows it does not
  PARTLY             the output shows some of it — including when an item names
                     two checks that disagree, with evidence from both
                     (GLM, finding 6.)
  PRESENT_UNPROVEN   the code exists and its behaviour is untested. The only
                     honest mark for the container pipeline path: no code run has
                     completed end to end (1.23) and pytest is on no interpreter
                     here (3.28).
  UNCLEAR_RESULT     the check ran and the answer is ambiguous
  UNCLEAR_CHECK_BROKE  the check ERRORED — missing tool, bad path, permission.
                     Reported separately, because a broken check is fixable and
                     must not become a permanent unknown. (GLM, finding 5.)

**No item is marked from Claude Code's belief. Only from output.** And no item
reaches DONE in this step — only PROPOSED_DONE. Certification is Step 3D and it
belongs to the reviewers.

--- STEP 7: the other two buckets ---
JUDGMENT → NEEDS_ERIC, with the question recorded in plain language.
NO_CHECK → NO_CHECK_WRITTEN. Nobody can assess these until someone states what
evidence would settle them. That list is a finding, not a failure.

--- STEP 8: report ---
  * the three classification counts
  * every label proposed, with the command output behind it
  * UNCLEAR_RESULT and UNCLEAR_CHECK_BROKE, listed separately
  * NEEDS_ERIC as plain-language questions
  * NO_CHECK_WRITTEN
  * how many PROPOSED_DONE items exist, and the cost of certifying them —
    two reviewer calls each. **Certification is not automatic; Eric decides how
    many to run.**

DONE WHEN: the import cannot run twice; nothing can write DONE directly; DONE
exists only where both lineages returned ESTABLISHED and the row is locked; every
one of the 120 carries a label backed by output or an explicit non-mark; and the
export still reproduces the file.

IF ANY CHECK FAILS: stop, restore, report. Do not repair forward.

NOT IN THIS CARD:
  * Certifying all PROPOSED_DONE items. Step 8 reports the count and cost.
  * Changing what any item SAYS. Labels and evidence only.
  * Writing checks for NO_CHECK items, or answering NEEDS_ERIC questions.
  * 1.22, retrieval, the reply path, closeout, any commit.
