# Advisor review — kb-1.22-loop-record

- packet: `reviews/pending/kb-1.22-loop-record.md`
- advisor: advisor on port 8649, no tools
- run tag: kb-1.22-loop-record @ 2026-09-10T00:04:20-05:00
- at: 2026-09-10T00:05:00
- prompt_tokens: 2016
- completion_tokens: 1211
- total_tokens: 3227
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This is the right item at the right time. The card's own intent states the load-bearing problem: advisor exchanges only survive in the knowledge base if a Claude Code transcript happens to capture them — check 4 confirms that as of 2026-09-07, all 29 hits came from transcripts, zero from the loop itself. Capture is a strict prerequisite for the retrieval work that 1.22's other half (and 1.18-1.21 downstream) depends on; you cannot retrieve what was never written. The 26 existing rounds in deliberation_rounds are actively at risk of being the last generation lost, and the backfill addresses that directly. The card correctly scopes itself to the open half and explicitly defers retrieval, schema changes, and everything else. Necessary, urgent, correctly sequenced.

---

Now the review of the card itself.

STEP 1 — GATE CHECKS

The card asks for three read-only checks before any work. The expected values are 0, ~26, 0.
The first check is the critical one — if knowledge_messages already contains advisor-sourced rows, the premise (no one writes the loop's record) is false and the card is stale. The ~26 on deliberation_rounds confirms the rounds exist but aren't being captured, which is the exact gap. The third check (grep count 0 in advisor_review.sh) confirms no knowledge_messages write exists yet. All three are the right gates. The "STOP if non-zero" instruction on check 1 is correct and should be honored literally.

STEP 2 — BACKUP

Backing up advisor_review.sh is right. The decision to NOT dump knowledge_messages (2.65M rows) is correct — recording row count before/after is the reversible fact. I'd add: record the exact count from Step 1's first query as the baseline, not just "before and after backfill," so you have three timestamps (pre-build, post-backfill, post-live-round) rather than two. Minor.

STEP 3 — THE BUILD

3A: Writing at round time, not closeout, is correct. The argument that closeout-only writing leaves readers between closeouts seeing nothing is sound. Four lines in the existing connection block is cleaner than a new invocation point. Good.

3B: One row per round, not per objection. Agree. The reasoning is correct — a round is one lineage's answer to one packet, and splitting 4,000-character answers into findings requires prose parsing that would be guessing.

3C: Self-describing row. The header format is good:
[advisor <card> round <n> <lineage>] frame=<FRAME> verdict=<VERDICT>

source 'advisor_loop', source_key 'advisor/<card>/<lineage>/<round>', role 'assistant', timestamp from round's created_at. All correct. The source_key format is clean and unique per round. One question: what happens if two lineages share the same card and round number? The source_key includes lineage, so it's unique. Fine.

3D: Idempotent on source_key. Delete-then-insert. This is correct and standard. A re-run replaces rather than duplicates.

3E: Backfill the 26 existing rounds. This is the most important step — without it, the card explicitly names the failure (today's exchanges are the last generation lost) and then commits it. The backfill script path tools/queue/ingest_advisor_rounds.py is reasonable. One concern: the backfill needs to reconstruct the header (card, round, lineage, frame verdict, result verdict) from deliberation_rounds. The card doesn't specify whether deliberation_rounds has all these fields. If the frame verdict or result verdict isn't stored per-round in deliberation_rounds, the backfill can't produce self-describing rows for the 26 and will need to either leave those fields blank or pull them from elsewhere. This is the one place the card may be optimistic about data availability. Flag this: before writing the backfill, confirm deliberation_rounds has run_id, reviewer_role (lineage), round number, frame verdict, and result verdict. If any are missing, the backfill rows will be malformed per 3C's own standard.

STEP 4 — VERIFICATION

1. 0 -> 26+: correct baseline and expectation.
2. Live round, +2 (one per lineage), no closeout: correct, proves write-at-round-time.
3. Backfill twice, no change on second run: proves idempotency.
4. The "lying" check — search for an advisor-only phrase and confirm source='advisor_loop': this is the strongest check and the card is right to call it out. The 2026-09-07 finding (29 hits all from claude_code) is exactly the failure mode this card exists to fix. Without this check, a count going up could be transcripts again.
5. Print one row in full, confirm a reader can identify card and lineage: correct readability check.

All five checks are the right checks. No gaps in verification.

STEP 5 — REPORT

The report spec is adequate: row counts at each step, full text of one ingested row, check 4's result. I'd add: include the three Step 1 check values in the report, not just the build-step counts, so the full chain is auditable.

DONE WHEN / FAILURE HANDLING

Done-when criteria are precise and testable. The "IF ANY CHECK FAILS: stop, restore from backup, report. Do not repair forward." instruction is correct — it prevents the most common failure mode (patching forward and ending up in an unknown state).

NOT IN THIS CARD — EXCLUSIONS

The exclusions are the most important part of the card and they're correct. Retrieval is explicitly deferred. No schema change. No real-time queue, reply path, closeout, or commit. The card correctly identifies that capture without retrieval means the next reviewer is still cold-started, and that this is what 1.22 is blocking 1.18-1.21 on. That framing is honest and prevents the card from silently expanding scope.

SUMMARY

The card is well-scoped, correctly sequenced, and its verification is designed to catch the specific failure it exists to fix. The one substantive risk is Step 3E: the backfill assumes deliberation_rows contains all fields needed for self-describing rows (3C). If frame_verdict or result_verdict aren't per-round in that table, the 26 backfilled rows will violate the card's own standard. Before writing the backfill, confirm those fields are present. Everything else is sound. Proceed.
