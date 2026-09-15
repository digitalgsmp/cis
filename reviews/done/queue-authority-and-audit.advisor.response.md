# Advisor review — queue-authority-and-audit

- packet: `reviews/pending/queue-authority-and-audit.md`
- advisor: advisor on port 8649, no tools
- run tag: queue-authority-and-audit @ 2026-09-10T00:21:45-05:00
- at: 2026-09-10T00:22:13
- prompt_tokens: 2883
- completion_tokens: 2400
- total_tokens: 5283
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The project's organizing artifact is a 120-item queue whose status fields are prose typed a month ago, with 56 items carrying no status at all and nothing derived from code. Working from that list — or continuing to add to it — would be guessing. This card makes the database the authority so that assessments persist, then assesses every item against actual command output. That is the right work because you cannot prioritize or execute a work list you cannot trust. The time is right because the queue is already being used (items reference it, a pre-commit hook regenerates related files) and every day of work on top of unverified status compounds the problem. The one thing that would change my mind: if the project has a hard external deadline imminent enough that stopping to fix the queue costs more than working blind. Nothing in the packet indicates that, so I proceed.

Now the review.

PHASE 1 — Design

Step 1 (read-only survey) is correct and complete. It asks for the five facts that matter: row count, markdown readers, table readers, git-ignore status of the spine, and the existing 32-check verifier. Reporting before acting is right. The instruction to continue past an untracked spine (d) is the correct call — Step 3D is the structural answer to git tracking, and stopping would just delay the decision.

Step 2 (backup) covers the right three things: the markdown (true rollback), the table dump, and the extractor source. Stating all three paths before proceeding is what makes a rollback possible under pressure.

Step 3A — making the extractor refuse without --force after one final run is the correctStep 3A — making the extractor refuse without --force after one final run is the correct way to handle the transition. It does not delete the tool, so nobody is stranded, but it makes the overwriting behavior opt-in and loud. One concern: the phrase "one final time" needs a witness. Step 4 check 1 diffs the rendered output against the backup, which proves the table captured the content, but nothing records that the final extraction was the run that populated the table. If the table already had rows from a prior extraction, the "final" run could silently no-op and the check would still pass because the old rows reproduce the file. Fix: after the final extraction, confirm the row count equals 120 and that every item_num in the markdown appears in the table before locking the extractor. One line in Step 3A, one expectation in Step 4 check 1.

Step 3B — the migration adds two columns to queue_items and one new append-only table. No existing columns touched, no data loss. The schema of queue_item_events is right: item_num, field, old_value, new_value, changed_at, changed_by, evidence, note. Putting evidence in the event row rather than the item row is the correct call because an item's status can change multiple times and each change needs its own evidence. The one gap: there is no explicit constraint or index. For 120 rows it does not matter functionally, but a CHECK constraint on the new status values in queue_items would make the tool's refusal logic enforced at the database too, not just at the CLI. Not blocking — the tool is the gate — but cheap insurance.

Step 3C — queue_set.py as the sole write path, refusing unknown items and unknown statuses, writing the change and event row in one transaction, printing before and after. This is the structural enforcement of "the database is authority." Correct. Two things to verify in implementation that the card does not state: that it rejects an empty --evidence for any status other than NEEDS_ERIC or NO_CHECK_WRITTEN, and that it rejects --evidence longer than some reasonable bound (command output can be large; the card does not say whether to truncate or cap). These are implementation details the card can leave to the builder, but the first one matters because the entire premise is "no mark without evidence." If the tool accepts an empty evidence string for DONE, the rule is unenforced. Add: evidence must be non-empty for DONE, OPEN, PARTLY, and PRESENT_UNPROVEN. NEEDS_ERIC and NO_CHECK_WRITTEN may carry a note instead.

Step 3D — rendering the markdown from the table with a DO NOT EDIT banner, wired into the existing pre-commit hook. This is the strongest part of the design. The spine is a binary nobody can diff; the rendered markdown is the readable history committed on every change. The analogy to AGENTS.md is apt and apparently already precedented in the repo. This is what keeps the queue in version control without making git track the sqlite file as the source of truth. Correct.

Step 4 — the verification checks are well ordered. Check 1 (render-diff against backup) is load-bearing and the card says so. Check 2 (one change round-trips through table, event, and render) proves the write path works end to end. Check 3 (second render is a no-op) proves idempotency. Check 4 (old extractor with --force does not destroy events) proves the migration survived a re-extraction. Check 5 (all 32 existing checks pass) proves no regression. The gate between phase 1 and phase 2 is check 1 alone, which is correct — check 1 is the one that proves authority transferred. Checks 2-5 are necessary but do not gate phase 2 because they test the write path, which phase 2 exercises constantly. One addition: check 2 should also confirm that the event row's old_value matches the status that was there before the change, not just that an event row exists. The card says "with old and new values" which implies it, but the verifier should check old_value specifically because a null or wrong old_value means the history is already lying.

PHASE 2 — Design

Step 5 (classify before assessing) is the most important structural decision in phase 2, and the card is right to make it a hard report gate. Sorting 120 items into RUNNABLE, JUDGMENT, and NO_CHECK before touching any of them lets Eric see the shape of the audit before it runs. The card explicitly says that if most items are JUDGMENT or NO_CHECK, Eric should be told before Step 6 runs because the audit is worth less than it costs. This is the correct escape valve and it is stated honestly.

The one thing Step 5 does not specify is the classification of items that have multiple checks or a check that is partly runnable. An item might say "the config exists and the port is open" — file existence is runnable, port check is runnable, but if it also says "and it handles the case correctly" that is judgment. Recommend: classify by the hardest-to-settle check the item names. If any check is JUDGMENT, the item is JUDGMENT, because you cannot mark it DONE with a command if part of what it asks is a decision. State this in Step 5 so the builder does not have to guess.

Step 6 — assess RUNNABLE items one at a time, run the stated check, capture actual output, mark from output only. The rule "an item may only be marked from command output" is the core of the card and it is correct. The PRESENT_UNPROVEN carve-out for the container pipeline path is the right call given 1.23 (no end-to-end run) and 3.28 (no pytest). Marking code as PRESENT_UNPROVEN rather than DONE is honest and prevents the audit from laundering untested code into "done." Two concerns:

First, the card says "if the check runs and the result is ambiguous, mark it UNCLEAR." It does not say what to do if the check itself errors — the command fails to run, not because the thing is absent but because the environment is broken (missing tool, permission denied, path wrong). An errored check is not the same as an ambiguous result. Recommend: if the check command errors, mark UNCLEAR and record the error output, but flag it separately from ambiguous-output UNCLEAR items so Eric can distinguish "the item is unclear" from "the check broke." This matters because a broken check is fixable and should not be left as a permanent UNCLEAR.

Second, the card does not state whether a single item can have multiple checks that disagree — one says DONE, one says OPEN. If the item names two checks and one passes and one fails, the honest mark is PARTLY with evidence from both. The card should say this explicitly rather than leaving it to the builder's judgment, because the whole point of the card is to remove judgment from the marking step.

Step 7 — JUDGMENT items get NEEDS_ERIC with the question recorded. NO_CHECK items get NO_CHECK_WRITTEN. Both are correct and both are explicitly not assessed. The card is clear that naming these is a deliverable, not a failure. This is right.

Step 8 — the report covers the right six things: classification counts, changed statuses with evidence, UNCLEAR items with reasons, NEEDS_ERIC as questions, NO_CHECK_WRITTEN list, and the final render diff. The render diff at the end is the proof that the file still reproduces from the table after all marking. Correct.

The DONE WHEN clause is precise and testable: byte-faithful render, status change writes row and evidence, every item has a mark backed by output or an explicit non-mark, nothing on Claude Code's word alone. The IF ANY CHECK FAILS clause (stop, restore, report, do not repair forward) is the right discipline and matches phase 1's check 1 failure handling.

NOT IN THIS CARD — the scope fence is explicit and correct. Not deleting the markdown, not changing item text, not writing checks for NO_CHECK items, not answering NEEDS_ERIC questions, not 1.22 or retrieval or closeout. This is the right boundary because this card is about establishing authority and assessing, not about redesigning the queue or starting new work.

One scope question the card does not address: supersedes. It says this card supersedes queue-db-authority, which was phase 1 alone. If queue-db-authority was already partially executed, this card needs to say what state the system is in when it starts. If queue-db-authority never ran, fine. If it ran phase 1 partially, the backup and migration steps could collide with prior work. The card should state the starting assumption: either "queue-db-authority was not executed" or "if queue-db-authority was partially executed, Step 1 must report which of its steps completed before Step 2 begins." This is a real gap because a superseded card that was partially run leaves the system in an undefined state relative to the new card's Step 1.

Summary of findings, in priority order:

1. Step 3A: add a row-count and item-num coverage check after the final extraction, before locking the extractor, to prove the "final run" actually populated the table and was not a silent no-op over existing rows.

2. Step 3C: state that evidence must be non-empty for DONE, OPEN, PARTLY, and PRESENT_UNPROVEN. NEEDS_ERIC and NO_CHECK_WRITTEN may use note instead. Without this the "no mark without evidence" rule is unenforced at the tool level.

3. Supersedes: state the starting assumption about whether queue-db-authority was executed. If it may have been partially run, Step 1 must detect and report that state before Step 2.

4. Step 5: specify that an item with any JUDGMENT check is classified JUDGMENT, classifying by the hardest-to-settle check. Prevents the builder from splitting an item and marking parts of it.

5. Step 6: distinguish errored checks from ambiguous results. Both are UNCLEAR, but errored checks should be flagged so Eric can fix the check rather than live with a permanent unknown.

6. Step 6: state that if an item names multiple checks and they disagree, mark PARTLY with evidence from all. Do not leave this to builder judgment.

7. Step 4 check 2: verify that the event row's old_value matches the prior status, not just that an event row exists.

8. Step 3B: optional, non-blocking — a CHECK constraint on status values in queue_items would enforce the tool's status validation at the database level. Cheap insurance for 120 rows.

None of these are design failures. The card is sound, the phases are correctly ordered, the gate is correctly placed, the scope fence is explicit, and the "assess from command output only" rule is the right rule for a queue that currently has 56 silent items and 11 unknowns. The findings above are sharpening the enforcement of rules the card already states, not changing the design.
