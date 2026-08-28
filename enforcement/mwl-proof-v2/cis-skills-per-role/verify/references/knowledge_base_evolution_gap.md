# Knowledge Base Self-Evolution Gap

Session: 2026-07-09
Identified after full end-to-end test of Code Review Gate (commit b11af59)

## The Problem

The pipeline produces rich narrative content every run — Brain's
understanding, reviewer objections, consensus reasoning, pattern
catalogs, code review findings, Menter's build output, verify evidence.
This content is stored in three SQLite tables:

- `agent_trajectories` (58 rows) — full input + output per agent call
- `deliberation_rounds` (48+ rows) — reviewer outputs, signals, objections
- `code_review_chunks` (1+ rows) — 3-pass review content, diffs, L1 evidence

**NONE of this content is in the FTS5 knowledge base (`knowledge_messages`).**

Empirical proof from 2026-07-09:

```
SELECT count(*) FROM agent_trajectories;           -- 58
SELECT count(*) FROM knowledge_messages;           -- 298,298
SELECT count(*) FROM knowledge_messages
  WHERE source = 'agent_trajectories';             -- 0
```

The knowledge base has 298,298 documents — all historical exports
(Claude transcripts, ChatGPT sessions, Hermes session logs, docs).
They were ingested once and never updated. The pipeline produces new
knowledge every run, and none of it flows back.

## Why This Matters

### No Self-Evolution

Each pipeline run is an island. The pre-discovery search in
`_pre_discovery()` does two things:

1. Searches `knowledge_messages_fts` (the knowledge base) — finds
   historical session exports, not pipeline findings
2. Searches `agent_trajectories` via direct SQL — finds prior
   trajectories, but ONLY if `outcome = 'success'`

So pre-discovery has two separate search paths that don't overlap.
Pipeline findings are invisible to the FTS5 search. And trajectory
search has its own bugs (see below).

### Trajectory Outcome Bug

Code review trajectories have `outcome = 'pending'`, not `'success'`:

```
trajectories 56-58 (review1, review2, review1_consensus):
  outcome = 'pending'  ← NOT 'success'
```

The code review path doesn't call `_update_trajectory_outcome()` for
the reviewer passes. So pre-discovery's `WHERE outcome = 'success'`
filter skips all reviewer outputs from code review — the most valuable
findings are invisible to future runs.

### Objections Don't Become Lessons

When proposal review round 4 returned OBJECTIONS, the objection text
is in `deliberation_rounds.reviewer1_output`. But it's not extracted,
indexed, or made discoverable. The next run's Brain or Draft won't find
the objection that was raised last time. The same class of issue could
be repeated because nobody remembers the last objection.

### Pattern Catalog Not Reusable

The pattern catalog Brain produced (6,683 chars) is in
`deliberation_rounds.brain_output` and saved to disk at
`runtime/catalogs/PATTERN_CATALOG.md`. But it's not in the FTS5
knowledge base. A future run on the same project would regenerate the
catalog from scratch rather than finding the existing one.

## What Needs to Happen

After every pipeline run (or after each round), the narrative content
needs to flow into `knowledge_messages` so the FTS5 trigger indexes it.

Proposed sources for the knowledge_messages table:

| Source Name | Content | Table of Origin |
|-------------|---------|-----------------|
| `pipeline_brain` | Brain's understanding output | deliberation_rounds.brain_output |
| `pipeline_objections` | Reviewer objection text | deliberation_rounds.reviewer1/2_output WHERE signal=OBJECTIONS |
| `pipeline_consensus` | Reviewer consensus reasoning | deliberation_rounds.reviewer1/2_output WHERE signal=CONSENSUS |
| `pipeline_catalog` | Pattern catalog | deliberation_rounds.brain_output WHERE drafter_role='pattern_catalog' |
| `pipeline_code_review` | All 3 review passes | code_review_chunks.review_a_pass1, review_b_pass2, review_a_consensus |
| `pipeline_menter` | Menter's build output | code_review_chunks / deliberation_rounds.menter_output |
| `pipeline_verify` | Verify evidence report | deliberation_rounds.verify_output |

The `knowledge_messages` table has a trigger that auto-inserts into
`knowledge_messages_fts` on INSERT. So inserting into
`knowledge_messages` is all that's needed — the FTS5 index updates
automatically.

### Fix 1: Trajectory Outcome for Code Review

`_review_single_chunk()` must call `_update_trajectory_outcome()` for
all three review passes:
- Reviewer A pass 1 → `outcome = 'success'` if completed
- Reviewer B pass 2 → `outcome = 'success'` if completed
- Reviewer A consensus → `outcome = 'success'` if verdict delivered

Without this, pre-discovery's `WHERE outcome = 'success'` filter
skips all code review findings.

### Fix 2: Post-Run Ingestion

After a run completes (CONSENSUS_REACHED, VERIFY_FAILED, ESCALATED),
the pipeline should insert key outputs into `knowledge_messages` with
appropriate source labels. This makes them FTS5-searchable by future
runs' pre-discovery.

### Fix 3: Objection Extraction

When a round has `reviewer_signal = 'OBJECTIONS'`, the objection text
should be extracted and ingested with `source = 'pipeline_objections'`
so future runs can search "what did reviewers object to in similar
situations?"

## The Connection: Pipeline → Trajectories → Knowledge Base → Pre-Discovery

```
Pipeline Run
    ↓
┌─────────────────────────────────────┐
│  deliberation_rounds (SQLite)       │
│  - signals, objections, consensus   │
│  - reviewer/brain/menter/verify out │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  agent_trajectories (SQLite)        │
│  - full input + output per agent    │
│  - outcome: success/failed/pending  │
│  - config_version (git hash)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  code_review_chunks (SQLite)        │
│  - 3-pass review content            │
│  - diffs, L1 evidence, verdicts     │
└──────────────┬──────────────────────┘
               │
    ═══════════╧═══════════════════════
    ║   GAP: nothing crosses here   ║
    ║   No ingestion into KB FTS5  ║
    ═══════════╤═══════════════════════
               │
┌──────────────▼──────────────────────┐
│  knowledge_messages (FTS5)          │
│  - 298,298 docs, all historical     │
│  - Claude/ChatGPT transcripts       │
│  - Hermes session exports           │
│  - ZERO pipeline run content        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  pre_discovery (next run)           │
│  - searches FTS5 (finds old stuff)  │
│  - searches trajectories (if bug-   │
│    free, finds prior agent output)  │
│  - MISSES: objections, code review  │
│    findings, pattern catalogs       │
└─────────────────────────────────────┘
```

## Status

**FIXED (commit ffd3c1c, 2026-07-09).** The self-evolution bridge is
implemented and the gap is closed.

### What Was Built

**`_ingest_to_kb()`** — Ingests any content string into `knowledge_messages`
with source tags (`pipeline_{phase}`), run_id, role, signal, and context.
Best-effort: failures don't crash the pipeline.

**`_ingest_round_to_kb()`** — Extracts all narrative content from a
deliberation round (brain_output, drafter_output, reviewer1/2_output,
menter_output, verify_output, human_question) and ingests each piece
with appropriate source tags.

**`_complete_round()` now auto-triggers ingestion** — Every call to
`_complete_round()` (28 call sites across all phases) automatically
ingests the round's narrative into the knowledge base. No manual wiring
needed at each call site — the bridge is in the function itself.

**Code review chunk ingestion** — `_review_single_chunk()` explicitly
ingests all 3 review passes on both APPROVED and CHANGES_REQUESTED
outcomes. The revision directive (actionable feedback to Menter) is
also ingested — objections become searchable lessons.

**Trajectory outcomes fixed** — All three review passes now call
`_update_trajectory_outcome(..., "success")`:
- `review1` / `code_review` — first pass
- `review2` / `code_review` — second pass (builds on A)
- `review1` / `code_review_consensus` — consensus pass

### The Closed Loop

```
Pipeline Run
    ↓
┌─────────────────────────────────────┐
│  deliberation_rounds (SQLite)       │
│  - signals, objections, consensus   │
└──────────────┬──────────────────────┘
               │ _complete_round() triggers
┌──────────────▼──────────────────────┐
│  _ingest_round_to_kb()              │
│  - extracts all outputs per round   │
│  - ingests with source=phase tags   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  knowledge_messages (FTS5)          │
│  - pipeline_brain, pipeline_draft,  │
│    pipeline_code_review, etc.       │
│  - AFTER INSERT trigger → FTS5      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  pre_discovery (next run)           │
│  - FTS5 search finds pipeline       │
│    findings from prior runs         │
│  - trajectory search finds prior    │
│    agent outputs (now all 'success')│
└─────────────────────────────────────┘
```

Each run produces knowledge → KB indexes it → next run's pre-discovery
finds it. This IS the self-evolution loop.

## End-to-End Verification (2026-07-09)

The bridge was committed in `ffd3c1c` but never exercised — the
previous pipeline run occurred *before* the code existed. A new run
was required to test it. **Pitfall: code committed after a run cannot
be tested by that run. Always start a new pipeline run after committing
pipeline code changes.**

### Verification Procedure

1. **Start a pipeline run:**
   ```python
   import asyncio
   from runtime.abstraction.pipeline_relay import PipelineRelay
   r = PipelineRelay()
   run_id = asyncio.run(r.start('Your task description'))
   print(f'COMPLETED: {run_id}')
   ```

2. **Monitor KB ingestion during the run:**
   ```sql
   SELECT source, COUNT(*) FROM knowledge_messages
   WHERE source LIKE 'pipeline%' GROUP BY source;
   ```
   Expected: entries appear as each round completes (pipeline_brain,
   pipeline_intent_review, pipeline_draft, pipeline_proposal_review,
   pipeline_pattern_catalog, pipeline_code_review).

3. **Verify FTS5 indexing:**
   ```sql
   SELECT content, source FROM knowledge_messages_fts
   WHERE knowledge_messages_fts MATCH 'pipeline docstring'
   ORDER BY rank LIMIT 5;
   ```
   Pipeline entries must appear in FTS5 search results — the AFTER
   INSERT trigger on knowledge_messages auto-indexes them.

4. **Simulate next run's pre-discovery:**
   ```python
   import sqlite3
   conn = sqlite3.connect('data/cis_memory.db')
   keywords = ' '.join(intent.split()[:10])
   cur = conn.execute(
       'SELECT content, source FROM knowledge_messages_fts '
       'WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT 5',
       (keywords,))
   for content, source in cur.fetchall():
       is_pipeline = source.startswith('pipeline_')
       print(f'[{source}] {"<- PIPELINE" if is_pipeline else ""}')
   ```
   If pipeline entries appear at the top, the self-evolution loop is
   confirmed: run -> KB -> FTS5 -> next run's pre-discovery finds it.

### Verified Results (run-e4aac6f86dc70fd4-1783600639)

- 22 KB entries ingested across 6 phases (brain, draft, intent_review,
  proposal_review, pattern_catalog, code_review)
- FTS5 search successfully found pipeline narratives at top of results
- Both CONSENSUS_REACHED and OBJECTIONS signals preserved in KB
- Pre-discovery simulation confirmed pipeline entries appear at top of
  FTS5 results — the loop is closed
- Full pipeline flow: Brain → Intent Review → Draft → Proposal Review (with
  revision) → Eric Gate → Pattern Catalog → Code Review Gate (3 revision
  cycles, escalated on Reviewer B transient failure — led to retry fix)

### Monitoring Pipeline Progress

```sql
-- Run status
SELECT status, result FROM workflow_runs WHERE id = '<run_id>';

-- Round-by-round progress
SELECT id, round_number, drafter_role, reviewer_signal
FROM deliberation_rounds WHERE run_id = '<run_id>' ORDER BY id;

-- Trajectory recording (code review has 3+ per cycle)
SELECT id, role, outcome FROM agent_trajectories
WHERE run_id = '<run_id>' AND phase = 'code_review' ORDER BY id;

-- KB entries by source
SELECT source, COUNT(*) FROM knowledge_messages
WHERE source LIKE 'pipeline%' GROUP BY source;
```

### Eric Gate Direct Approval (when Flask API is unavailable)

When `runtime/app.py` can't start (import errors, etc), approve
directly via sqlite3 — see `references/pipeline_testing_commands.md`
for the full procedure.
