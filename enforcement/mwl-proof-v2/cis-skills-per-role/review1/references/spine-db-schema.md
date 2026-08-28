# CIS Spine DB Schema — Reviewer Reference

Spine DB path: `data/cis_memory.db` (env override: `CIS_SPINE_PATH`)
Pipeline relay default: `/workspace/cis/data/cis_memory.db` (env override: `CIS_DB_PATH`)

## workflow_runs table

Columns: `id, topic, result, requires_eric_review, max_rounds, max_consecutive_revisions, rounds_completed, final_objections_json, created_at, completed_at, status, route, updated_at, eric_approved_at, intent, directive_hash, project_id, parent_run_id`

- `status` holds the current phase: `INTAKE`, `BRAIN_PHASE`, `INTENT_REVIEW`, `DRAFT_PHASE`, `PROPOSAL_REVIEW`, `ERIC_GATE`, `CLOSED_EXPIRED`, `COMPLETED`, etc.
- `result` defaults to `'PENDING'`
- Use `ORDER BY created_at DESC LIMIT N` to find recent runs
- `requires_eric_review` (integer 0/1) flags whether Eric Gate was triggered

## deliberation_rounds table

Columns: `id, run_id, round_number, drafter_role, drafter_output, reviewer_role, reviewer_signal, objections_json, revision_number, requires_eric_review, created_at, reviewer1_output, reviewer2_output, brain_output, verify_output, human_question, human_answer, menter_output`

**CRITICAL: There is NO `status` column and NO `phase` column.** Common mistakes from live sessions:

- ❌ `SELECT ... WHERE status='OPEN'` — column does not exist
- ❌ `SELECT phase FROM deliberation_rounds` — column does not exist
- ✅ Use `drafter_role` to identify the phase: 'brain', 'intent_review', 'draft', 'proposal_review'
- ✅ Use `reviewer_signal` for round outcome: `PENDING`, `CONSENSUS_REACHED`, `OBJECTIONS`
- ✅ Use `revision_number` to track which revision of a round
- ✅ Use `requires_eric_review` (integer 0/1) to check if Eric Gate was flagged

## Run status vs round status

- `workflow_runs.status` = pipeline's current phase (machine state)
- `deliberation_rounds.reviewer_signal` = individual round consensus outcome
- A run at `INTENT_REVIEW` with round 4 `reviewer_signal=PENDING` means the reviewer hasn't responded yet
- A completed run with all rounds `CONSENSUS_REACHED` and final round `requires_eric_review=1` means it passed all reviews but may expire waiting for Eric

## Example queries

```sql
-- Recent runs
SELECT id, topic, status, created_at, completed_at
FROM workflow_runs ORDER BY created_at DESC LIMIT 10;

-- Round history for a specific run (use drafter_role as phase proxy)
SELECT id, round_number, drafter_role, reviewer_signal,
       requires_eric_review, created_at
FROM deliberation_rounds
WHERE run_id='run-XXXX' ORDER BY id;

-- Find expired runs (passed all reviews but Eric didn't approve)
SELECT id, topic, status, completed_at
FROM workflow_runs
WHERE status='CLOSED_EXPIRED' ORDER BY created_at DESC;

-- Current run state
SELECT id, topic, status, rounds_completed, requires_eric_review
FROM workflow_runs
WHERE status NOT IN ('COMPLETED','CLOSED_EXPIRED')
ORDER BY created_at DESC;
```

## Pitfall: multiple .db files exist

Many stale/empty `.db` files exist in the repo (runtime/pipeline.db, cis_spine.db, runtime/cis_live.db are all empty). The authoritative spine is `data/cis_memory.db`. Always verify with `sqlite3 <path> ".tables"` before querying — empty files return no error but have no tables.
