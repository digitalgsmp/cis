# Advisor review — spine-baseline-discipline

- packet: `reviews/pending/spine-baseline-discipline.md`
- advisor: advisor on port 8649
- run tag: spine-baseline-discipline @ 2026-09-12T14:50:15-05:00
- at: 2026-09-12T14:52:27
- prompt_tokens: 928794
- completion_tokens: 3267
- total_tokens: 932061
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

Now I have all the evidence I need. Let me compile my review.

FRAME: RIGHT_WORK

This proposal targets a real, observed gap that directly undermines the project's seed intent of "checks and balances." A reviewer that cannot independently verify a before/after claim is an opinion-giver, not a measurer — and the C3 NOT_ESTABLISHED verdict from the evaluator on reviewer-fix-tool-trim proves the gap was hit in practice, not in theory. The proposal is the right item at the right time.

Now the claim-by-claim review.

---

VERDICT ON THE PROBLEM DESCRIPTION: ESTABLISHED

The proposal makes four factual claims about the current state. I verified each:

1. "advisor_review.sh overwrites reviews/done/<id>.<lineage>.response.md on rerun, destroying the prior state." — VERIFIED. The header comment at tools/advisor_review.sh line 18 documents the write path as `reviews/done/<id>.<profile>.response.md` for round 1, with no versioning or run-tag component in the filename. The variable `OUT` is set to `$OUTDIR/$ID.response.md` (line ~197 of the first 200 lines). The filename is deterministic — a rerun with the same ID and profile produces the same path and overwrites. The directory listing of reviews/done/ confirms exactly one `reviewer-fix-tool-trim.advisor.response.md` and one `reviewer-fix-tool-trim.evaluator.response.md`, despite the card being reviewed today — no prior version files exist.

2. "A rerun even logs 'NOT recorded: already exists' instead of appending." — VERIFIED. cis_search_files found two matches in advisor_review.sh:
   - Line 598: `NOT recorded: {run_id} already exists (duplicate round for this run_id)`
   - Line 1058: `NOT recorded: {run_id} round {rnd} already exists — a duplicate`
   These are skip-and-log paths, not append paths. A rerun that hits the same run_id+round_number is silently dropped from the spine.

3. "The spine's deliberation_rounds stores only reviewer_signal, not the reviewer's output or token usage — OQ-SEED-006, still open." — PARTIALLY ACCURATE, with an important correction. OQ-SEED-006 is confirmed OPEN (cis_get_open_questions). The original OQ-SEED-006 text says "no reviewer_output column exists, only reviewer_signal." But migration 0015 (cis_read_file of runtime/schema/migrations/0015_production_pipeline.sql) added `reviewer1_output TEXT`, `reviewer2_output TEXT`, `brain_output TEXT`, `verify_output TEXT` to deliberation_rounds, and migration 0020 rebuilt the table with those columns included. So reviewer output columns DO exist in the schema. However, the proposal's deeper claim is correct in practice: cis_search_files for `reviewer1_output|reviewer2_output` in tools/advisor_review.sh returned "git grep failed" (no matches), meaning advisor_review.sh does not populate those columns when it INSERTs into deliberation_rounds. The columns exist in the schema but are unused by the advisor review script. The gap is real; the framing as "no column exists" is stale.

4. "The claim 'prompt_tokens rose 5,118 → 303,099' had a durable AFTER but no durable BEFORE." — VERIFIED. The evaluator's own response (cis_read_file of reviews/done/reviewer-fix-tool-trim.evaluator.response.md) states: "C3 is NOT_ESTABLISHED — the 303,099 token count exists in UNIFIED_BUILD_LIST.md:3221, but I cannot verify the 5,118 baseline." The response file header records `prompt_tokens: 194992` for the evaluator and `prompt_tokens: 525830` for the advisor, but these are the CURRENT run's tokens, not the prior run's. The prior run's token count was overwritten when the response file was rewritten.

---

VERDICT ON R1 (schema: add reviewer_output TEXT, prompt_tokens INTEGER, completion_tokens INTEGER): PARTIALLY REDUNDANT, PARTIALLY CORRECT

The `reviewer_output TEXT` column already exists in two forms: `reviewer1_output` and `reviewer2_output` (migration 0015, migration 0020). The proposal should use the existing columns rather than adding a new `reviewer_output`. The token columns (`prompt_tokens INTEGER`, `completion_tokens INTEGER`) genuinely do not exist on `deliberation_rounds` — I confirmed this by reading the complete migration 0020 table definition, which has no token columns. Migration 0025 added `tokens_in`/`tokens_out` to `agent_trajectories`, a different table, so that does not help.

The proposal should be amended: do not add `reviewer_output TEXT` (it exists as `reviewer1_output`/`reviewer2_output`); do add `prompt_tokens INTEGER` and `completion_tokens INTEGER` to `deliberation_rounds`.

---

VERDICT ON R2 (advisor_review.sh: INSERT full output + token counts on every round, append-only): CORRECT AND NEEDED

The three INSERT sites are at lines 250, 588, and 1030 (cis_search_files). The "NOT recorded: already exists" skip at lines 598 and 1058 confirms the non-append behavior. The proposal's requirement that a rerun create a NEW row with its own run tag, rather than skipping, is the right fix. The current UNIQUE(run_id, round_number) constraint means a rerun with the same run_id hits a collision — the fix must either use a distinct run_id per invocation (e.g., timestamp-suffixed) or change the uniqueness constraint.

One concern: the proposal says "INSERT a new deliberation_rounds row carrying the full reviewer output + token counts." The output should go into the existing `reviewer1_output`/`reviewer2_output` columns (or whichever corresponds to the lineage), not a new column.

---

VERDICT ON R3 (run-tagged filenames so reruns cannot clobber): CORRECT AND NEEDED

The current filename pattern is `<id>.<profile>.response.md` — no run tag. A rerun overwrites. The directory listing confirms only one file per id+profile+round-type exists. Adding a run tag (timestamp or sequence) to the filename is the minimal fix.

---

VERDICT ON R4 (claim discipline becomes automatic): CORRECT IN PRINCIPLE

If R1+R2+R3 are implemented, then every review round's output and token counts are queryable from the spine via `cis_get_run_detail` (or equivalent). A before/after claim citing two run_id+round rows would be verifiable. This is the right structural goal.

---

VERDICT ON DONE-WHEN: CORRECT AND TESTABLE

The done-when is: "Running a review twice on the same packet leaves BOTH rounds queryable in deliberation_rounds with distinct token counts anddistinct reviewer_output, and a reviewer can confirm a before/after claim using only cis_get_run_detail — no gateway-log access." This is precise, behavioral, and testable. It directly closes the gap that caused C3's NOT_ESTABLISHED.

---

ONE ADDITIONAL FINDING: cis_search_sessions is broken.

While investigating, I attempted cis_search_sessions to find prior session closeouts about "reviewer-fix-tool-trim" or "prompt_tokens baseline." The tool returned an error: `sqlite3.OperationalError: no such column: sc.created_at` (traceback in runtime/mcp_bridge/spine.py line 312). This is a live bug in the MCP bridge — the session_closeouts FTS query references a column that does not exist on the table. This does not block the proposal, but it means one of the reviewer's read-only instruments is currently broken, which is itself a measurement gap. The proposal should note this as a pre-existing defect that prevents reviewers from searching the session archive.

---

SUMMARY

FRAME: RIGHT_WORK. The proposal identifies a real structural gap that has already caused a NOT_ESTABLISHED verdict in practice. The fix is correctly targeted at making the pipeline durably persist what reviewers need, rather than relying on Drafter discipline.

Three corrections to the proposal before implementation:

1. R1 should not add `reviewer_output TEXT` — `reviewer1_output` and `reviewer2_output` already exist (migration 0015, migration 0020). Only `prompt_tokens INTEGER` and `completion_tokens INTEGER` are genuinely new columns needed on `deliberation_rounds`.

2. R2 should specify that reviewer output goes into the existing `reviewer1_output`/`reviewer2_output` columns, not a new column. The append-only requirement means the run_id must be unique per invocation (timestamp-suffixed or similar), since the current UNIQUE(run_id, round_number) constraint is what causes the "NOT recorded: already exists" skip.

3. The proposal should note that `cis_search_sessions` is currently broken (`no such column: sc.created_at` in spine.py:312), which is a separate but related measurement gap — reviewers cannot search the session archive until it is fixed.

With those three amendments, the proposal is ready for implementation.
