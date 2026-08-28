# Spine Schema Constraints — pipeline_relay.py

Discovered 2026-07-08 while building pipeline_relay.py.
The spec (SPEC_PRODUCTION_PIPELINE_RELAY.md) describes ideal columns,
but the actual spine has CHECK constraints and naming differences.

## How to Verify Before Writing

```bash
sqlite3 /mnt/projects/cis/data/cis_memory.db "PRAGMA table_info(workflow_runs);"
sqlite3 /mnt/projects/cis/data/cis_memory.db ".schema workflow_runs"
sqlite3 /mnt/projects/cis/data/cis_memory.db "PRAGMA table_info(deliberation_rounds);"
sqlite3 /mnt/projects/cis/data/cis_memory.db ".schema deliberation_rounds"
```

## workflow_runs — Actual Constraints

| Column | Type | NOT NULL | Default | CHECK |
|--------|------|----------|---------|-------|
| id | TEXT | yes (PK) | — | — |
| topic | TEXT | yes | — | — |
| result | TEXT | yes | — | IN ('CONSENSUS_REACHED', 'ESCALATE', 'ERROR') |
| requires_eric_review | INTEGER | yes | 1 | — |
| max_rounds | INTEGER | yes | — | — |
| max_consecutive_revisions | INTEGER | yes | 3 | — |
| rounds_completed | INTEGER | yes | 0 | — |
| final_objections_json | TEXT | no | — | — |
| created_at | TEXT | yes | — | — |
| completed_at | TEXT | no | — | — |
| status | TEXT | yes | 'COMPLETE' | — |
| route | TEXT | no | — | — |
| updated_at | TEXT | no | — | — |
| eric_approved_at | TEXT | no | — | — |
| intent | TEXT | no | — | — |
| directive_hash | TEXT | no | — | — |

**Gotchas:**
- NO `created_by` column — don't include it in INSERT
- `result` has CHECK constraint — must be `CONSENSUS_REACHED`, `ESCALATE`, or `ERROR`. NOT `PENDING`.
- `status` is free-text (no CHECK) — use state machine values like `INTAKE`, `BRAIN_PHASE`, etc.

### Correct INSERT for a new run

```sql
INSERT INTO workflow_runs
    (id, topic, result, status, created_at, max_rounds, rounds_completed)
VALUES (?, ?, 'CONSENSUS_REACHED', 'INTAKE', ?, 3, 0)
```

## deliberation_rounds — Actual Constraints

| Column | Type | NOT NULL | Default | CHECK |
|--------|------|----------|---------|-------|
| id | INTEGER PK | yes | — | — |
| run_id | TEXT | yes | — | FK → workflow_runs(id) |
| round_number | INTEGER | yes | — | UNIQUE(run_id, round_number) |
| drafter_role | TEXT | yes | — | — |
| drafter_output | TEXT | yes | — | — |
| reviewer_role | TEXT | yes | — | — |
| reviewer_signal | TEXT | yes | — | IN ('OBJECTIONS', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR') |
| objections_json | TEXT | no | — | — |
| revision_number | INTEGER | yes | 1 | — |
| requires_eric_review | INTEGER | yes | 1 | IN (0, 1) |
| created_at | TEXT | yes | — | — |
| reviewer1_output | TEXT | no | — | — |
| reviewer2_output | TEXT | no | — | — |
| brain_output | TEXT | no | — | — |
| verify_output | TEXT | no | — | — |
| human_question | TEXT | no | — | — |
| human_answer | TEXT | no | — | — |

**Gotchas:**
- Column is `run_id`, NOT `workflow_run_id` (spec says workflow_run_id)
- NO `status` column — the reviewer_signal column serves as status
- NO `completed_at` column
- NO `phase` column — phase info goes in `drafter_role` field
- `reviewer_signal` has CHECK constraint — must be one of the 4 enum values
- `drafter_output` and `drafter_role` are NOT NULL — must have values even for non-drafter rounds
- **`UNIQUE(run_id, round_number)` — round numbers must be globally unique per run.** The pipeline relay calls `_start_round()` with phase-specific round numbers (brain round 1, intent_review round 1, draft round 1) — all reuse `round_num=1`, causing a UNIQUE constraint crash on the second call. Fix: `_start_round()` auto-increments `round_number` via `SELECT COALESCE(MAX(round_number), 0) + 1 FROM deliberation_rounds WHERE run_id = ?` instead of trusting the caller's value. The caller's `round_num` is stored in `revision_number` as a hint.

### Correct INSERT for a new round

```sql
INSERT INTO deliberation_rounds
    (run_id, round_number, drafter_role, drafter_output,
     reviewer_role, reviewer_signal, revision_number,
     requires_eric_review, created_at)
VALUES (?, ?, '<phase>', '', '', 'CONSENSUS_REACHED', ?, 0, ?)
```

### Correct UPDATE to complete a round

```sql
-- Update reviewer_signal + output columns, NOT status
UPDATE deliberation_rounds
SET reviewer_signal = ?,
    brain_output = ?,
    reviewer1_output = ?,
    reviewer2_output = ?
WHERE id = ?
```

## agent_trajectories — No Surprises

Schema matches the spec/migration. No CHECK constraints beyond the standard ones.
Safe to INSERT directly.

## The `IS NOT NULL` vs `!= ''` Trap (2026-07-08)

**Bug**: `_execution()` and `_verification()` query `WHERE drafter_output IS NOT NULL`
to find the latest draft output. But `_start_round()` INSERTs rows with
`drafter_output = ''` (empty string, the DEFAULT). SQLite treats `''` as
NOT NULL, so `IS NOT NULL` returns rows with empty strings. Menter received
an empty directive and reported: "that's the SHA-256 of an empty string.
There is no directive body."

**Fix**: All queries that retrieve phase outputs must filter both:
```sql
WHERE drafter_output IS NOT NULL AND drafter_output != ''
ORDER BY id DESC LIMIT 1
```

This applies to `brain_output`, `drafter_output`, `reviewer1_output`,
`reviewer2_output`, and `verify_output` — all use `''` as the default
in `_start_round()`. The `IS NOT NULL` check alone is insufficient.

The same pattern applies to the Flask status endpoint: use a
`_latest_nonempty(field)` helper that searches backward through rounds
for the first non-empty value, rather than reading from the latest round
(which may have empty columns for phases that didn't produce output).

## Pattern for Future Schema Changes

1. Run `PRAGMA table_info()` on the target table
2. Run `.schema <table>` to see CHECK constraints
3. Write a test INSERT with dummy data first
4. Only then code the production INSERT
5. **Test with `!= ''` not just `IS NOT NULL`** when querying columns with DEFAULT ''

## goal_references — CHECK Constraints (2026-07-11)

Discovered while building the Eric Gate provenance system. The table has
strict CHECK constraints on enum-like columns:

| Column | Type | NOT NULL | CHECK values |
|--------|------|----------|-------------|
| advancement_type | TEXT | yes | CLOSES_NODE, ADVANCES_TIER, RESOLVES_BLOCKER, RESOLVES_OPEN_QUESTION, ESTABLISHES_PREREQUISITE, **PIPELINE_RUN** (added by migration 0027) |
| authored_by | TEXT | yes | DRAFTER, REVIEWER, ERIC_GATE, ROUTER, CLOSEOUT |
| dependency_node | TEXT | yes | (no CHECK, but NOT NULL — use empty string) |
| linked_record_table | TEXT | no | NULL or one of: active_blockers, open_questions, project_decisions, next_actions |

**Gotcha:** SQLite doesn't support `ALTER TABLE ... ALTER CHECK`. To add a
new enum value, the migration must recreate the table:
backup → drop → recreate with new CHECK → restore → drop backup.
See `runtime/schema/migrations/0027_add_pipeline_run_advancement_type.sql`.

## decision_trails — CHECK Constraints (2026-07-11)

| Column | Type | NOT NULL | CHECK values |
|--------|------|----------|-------------|
| authored_by | TEXT | yes | DRAFTER, REVIEWER, CLOSEOUT, ROUTER (NOTE: no ERIC_GATE here, unlike goal_references) |
| trail_sequence | INTEGER | yes | UNIQUE(workflow_run_id, trail_sequence) |

**Gotcha:** `authored_by` allowed values differ between tables. goal_references
allows ERIC_GATE but not CLOSEOUT-only; decision_trails allows CLOSEOUT but not
ERIC_GATE. When inserting into both in one transaction, use ERIC_GATE for
goal_references and ROUTER for decision_trails.
