# Spine + baseline discipline — make review evidence durable by construction

VERSION 2 — revised after round-1 review (both lineages FRAME: RIGHT_WORK).

CHANGES (V1 → V2):
- R1: do NOT add `reviewer_output` — `reviewer1_output` / `reviewer2_output`
  already exist (migrations 0015, 0016, 0020). Only `prompt_tokens` and
  `completion_tokens` are genuinely new.
- R2: write output into the existing `reviewer1_output` / `reviewer2_output`
  columns (not a new column); append-only requires a unique run_id per
  invocation.
- NEW R4: also fix `runtime/orchestrator.py:306` INSERT OR REPLACE (same
  lossy-overwrite class in the orchestrator path).
- NEW R5: fix `cis_search_sessions` — live bug `no such column: sc.created_at`
  in spine.py:312 (a reviewer instrument is currently broken).
- Add a numbered migration for the token columns.

GOAL_ALIGNMENT: seed intent 3 — checks and balances. A reviewer that cannot
independently verify a before/after claim is an opinion-giver, not a measurer.

## Problem (observed)

reviewer-fix-tool-trim C3 was NOT_ESTABLISHED: the claim "prompt_tokens rose
5,118 → 303,099" had a durable AFTER but no durable BEFORE — the 5,118 lived
only in the gateway log, and the rerun overwrote the prior response file. Two
structural causes: (1) `advisor_review.sh` overwrites
`reviews/done/<id>.<lineage>.response.md` on rerun; (2) the spine's
`deliberation_rounds` is not populated with the reviewer's output or token
usage by `advisor_review.sh` (it writes only `reviewer_signal`). Output columns
exist (migrations 0015/0016) but the script does not use them.

## Requirement

The spine must be the durable, append-only record of every review round — full
output plus token usage — so any before/after claim is verifiable from the
spine + repo alone, no gateway-log access.

## Changes

R1. Add `prompt_tokens INTEGER`, `completion_tokens INTEGER` to
    `deliberation_rounds` via a new numbered migration. Do NOT add a new output
    column — reuse `reviewer1_output` / `reviewer2_output`.

R2. `advisor_review.sh`: on every round, write the full reviewer output into
    the existing `reviewer1_output` / `reviewer2_output` column for the lineage,
    and record `prompt_tokens` + `completion_tokens`. Append-only: each
    invocation gets a distinct run_id (e.g. timestamp-suffixed) so a rerun
    INSERTs a new row instead of hitting the UNIQUE(run_id, round_number)
    collision that today logs "already exists" and drops the round.

R3. Response files: write run-tagged filenames so a rerun cannot clobber the
    prior response.

R4. Fix `runtime/orchestrator.py:306` INSERT OR REPLACE so the orchestrator
    path is also append-only, not overwrite-in-place.

R5. Fix `cis_search_sessions` (spine.py:312 `no such column: sc.created_at`) —
    a reviewer read-only instrument is broken and must be repaired so the
    archive is searchable during review.

## DONE-WHEN

Running a review twice on the same packet leaves BOTH rounds queryable in
deliberation_rounds with distinct token counts and distinct output, and a
reviewer can confirm a before/after claim using only cis_get_run_detail — no
gateway-log access. cis_search_sessions returns session results, not a
sqlite3.OperationalError.
