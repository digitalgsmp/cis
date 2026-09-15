# Advisor review — spine-baseline-discipline

- packet: `reviews/pending/spine-baseline-discipline.md`
- advisor: evaluator on port 8650
- run tag: spine-baseline-discipline @ 2026-09-12T14:50:15-05:00
- at: 2026-09-12T14:54:35
- prompt_tokens: 437579
- completion_tokens: 2307
- total_tokens: 439886
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

I've completed verification. Here's the review:

---

**FRAME: RIGHT_WORK**

This is foundational infrastructure for the project's stated purpose. Seed intent 3 (checks and balances) requires verifiable review, and reviewers who cannot independently confirm before/after claims are opinion-givers, not measurers. The proposal addresses a structural gap that blocks evidence durability.

---

## Verification of Claims

**Claim 1: Response files are overwritten on rerun**

PARTIALLY VERIFIED. The script header (tools/advisor_review.sh:16-22) documents it writes `reviews/done/<id>.<profile>.response.md` (round 1), `.reconcile.md`, `.reply.md`, and `.result.md`. The script uses `>` (overwrite mode) when writing response files.

However, the "already exists" logic I found (lines 427-428) applies to the RECONCILE file specifically, not the response file. The response file is unconditionally overwritten with `>` at line 268. So the claim is accurate for response files but the specific "already exists" error message is for reconcile files.

**Claim 2: deliberation_rounds doesn't store reviewer output or token counts**

NUANCED. The schema DOES have output columns:
- runtime/schema/migrations/0015_production_pipeline.sql:9-14 adds `reviewer1_output`, `reviewer2_output`, `brain_output`, `verify_output`, `human_question`, `human_answer`
- runtime/schema/migrations/0016_menter_output_column.sql:6 adds `menter_output`

So the schema supports storing reviewer output. The gap is that `advisor_review.sh` doesn't USE these columns—it only writes `reviewer_signal` (the verdict like OBJECTIONS or CONSENSUS_REACHED). The actual reviewer reasoning and objections are not stored in the spine for advisor reviews.

For token counts: VERIFIED. I found no `prompt_tokens` or `completion_tokens` columns in deliberation_rounds. The script extracts these from the API response (tools/advisor_review.sh:220-222, 545, 750, 906) and writes them to the response file, but they are NOT stored in the spine.

**Claim 3: OQ-SEED-006 is still open**

VERIFIED. AGENTS.md:70 and docs/MASTER_GOAL_INVENTORY.md:22 both list it as an open question requiring a `reviewer_output TEXT` column.

---

## Assessment

The proposal correctly identifies structural gaps, but one claim needs refinement:

1. **The schema already supports reviewer output** (migrations 0015-0016). The gap is that `advisor_review.sh doesn't write to those columns — it writes response files instead. So R1 (add `reviewer_output TEXT`) is partially already done for the orchestrator pipeline but NOT for the advisor_review.sh path.

2. **Token counts are genuinely absent from the spine.** No migration adds prompt_tokens or completion_tokens to deliberation_rounds. The token data exists only in the response file headers and in gateway logs. This confirms the core claim.

3. **R3 (versioned response files) is the highest-value change.** The current script writes to a fixed filename per lineage per round. A rerun clobbers the prior state. This is the most actionable and lowest-risk change.

4. **The "already exists" skip behavior** the card describes is for reconcile files (line 427-428), not response files. Response files are silently overwritten. The card conflates two slightly different failure modes but both produce the same outcome: prior state is lost.

**What's missing from the proposal:**

- It doesn't acknowledge that migration 0015 already added output columns to deliberation_rounds. R1 should be scoped as "add token columns + wire advisor_review.sh to use existing output columns" rather than "add reviewer_output TEXT" which already exists.
- It doesn't address the INSERT OR REPLACE pattern in runtime/orchestrator.py:306, which also destroys prior round state for the orchestrator pipeline (not just advisor_review.sh). This is the same class of bug in a different code path.
- No migration file is proposed. The DONE-WHEN is testable but the path from current schema to target schema isn't specified.

**Recommendation:** The work is right and the timing is right — this blocks verifiable review across the entire project. But the card should be revised to (a) acknowledge the existing output columns and scope R1 to token columns only, (b) fix INSERT OR REPLACE in orchestrator.py alongside advisor_review.sh, and (c) include a numbered migration file.
