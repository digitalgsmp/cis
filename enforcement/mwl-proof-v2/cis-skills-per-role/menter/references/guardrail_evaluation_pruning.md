# Guardrail Evaluation and Pruning

## When to Evaluate

After wiring guardrails and running 20+ pipeline runs with gate_outcomes recorded,
evaluate which guardrails are:
1. **Working** — PASS/FAIL on real data, catching real issues
2. **Broken** — always FAIL/SKIP due to bugs (wrong DB table, wrong column, missing row_factory)
3. **Irrelevant** — always SKIP because the condition they check doesn't apply to this pipeline

## Methodology

### Step 1: Query gate_outcomes for aggregate stats

```sql
SELECT guardrail_name, verdict, COUNT(*) as count
FROM gate_outcomes
GROUP BY guardrail_name, verdict
ORDER BY guardrail_name, verdict;
```

### Step 2: Classify each guardrail

**Always SKIP** → Check if the condition applies to the pipeline at all:
- Does the pipeline produce the input the guardrail checks? (e.g., no multi-option prompts → position_randomizer irrelevant)
- Is the condition already enforced at a different layer? (e.g., different gateways/ports = different models → model_diversity redundant)
- Does the guardrail require inputs the pipeline never provides? (e.g., --proposal-file → staleness gate always skips)

**Always FAIL** → Check if the guardrail is querying the right data at the right time:
- Is the DB table populated BEFORE or AFTER the guardrail runs? (e.g., deliberation_rounds populated by _complete_round() AFTER guardrails → query agent_trajectories instead)
- Is the row_factory set? (sqlite3 returns tuples by default, need `conn.row_factory = sqlite3.Row` for named access)
- Are the column names correct? (spec ≠ actual schema — always PRAGMA table_info)

**PASS only** → Working correctly. Don't touch.

**Mixed PASS/FAIL** → Working correctly. The FAILs are catching real issues.

### Step 3: Delete irrelevant guardrails

For each irrelevant guardrail:
1. Delete the function definition from `guardrails.py`
2. Remove the call from `run_guardrails()`
3. Update docstrings that reference it
4. Delete any external gate script file (`tools/gates/gate_*.sh` or `.py`)
5. Delete from `SECURITY_GATES` list if present
6. Delete from `PHASE_GATE_MAP` if present

### Step 4: Fix broken guardrails

For each broken guardrail:
1. Diagnose the root cause (DB timing, row_factory, wrong column name)
2. Fix the query or add the missing setup
3. Test with real DB data:
```python
import sqlite3, sys
sys.path.insert(0, 'runtime/abstraction')
from guardrails import guardrail_raw_source_preservation
conn = sqlite3.connect('data/cis_memory.db')
r = guardrail_raw_source_preservation(conn, 'run-XXXXX')
print(f'{r.verdict} - {r.summary}')
```
4. Verify syntax: `python3 -m py_compile runtime/abstraction/guardrails.py`

## Guards Deleted (2026-07-10, commit c4ce0d8)

| Guardrail | Reason | Was |
|-----------|--------|-----|
| honesty_reporter | Old gate_runner.sh that produced aggregate banners is deleted. gate_outcomes records every outcome individually — nothing to lie about. | Always SKIP |
| model_diversity | Diversity enforced at architecture level: Review1=port 8643=qwen3.7-max, Review2=port 8647=glm-5.2. Different gateways = different models. | Always SKIP |
| example_diversifier | Pipeline prompts don't contain static examples. No anchoring risk. | Always SKIP |
| position_randomizer | Pipeline prompts don't have multi-option choices. No positional bias risk. | Always SKIP |
| gate_staleness.sh | Required --proposal-file arg never provided. Pipeline stores everything in SQLite spine, not proposal files. | Always SKIP |
| gate_mcp_no_network | Redundant with Docker container isolation. Container network is already restricted. | Always FAIL |

## Guards Fixed (2026-07-10, commit c4ce0d8)

### raw_source_preservation

**Bug**: Queried `deliberation_rounds` table, but that table is populated by `_complete_round()` which runs AFTER guardrails. So it always found 0 chars.

**Fix**: Switched to querying `agent_trajectories` table, which is populated by `_record_trajectory()` BEFORE guardrails fire.

**Pipeline execution order** (critical for understanding which tables are available):
```
_record_trajectory()     → writes to agent_trajectories (BEFORE guardrails)
run_guardrails()         → guardrails can query agent_trajectories
_complete_round()        → writes to deliberation_rounds (AFTER guardrails)
run_external_gates()     → external gates can query deliberation_rounds
```

**Test result**: PASS — 17,876 chars across 4 trajectory entries (was 0 chars before fix).

### trajectory_monitor

**Bug**: Crashed with `'tuple' object has no attribute 'keys'` because `conn.row_factory` wasn't set to `sqlite3.Row`.

**Fix**: Added `conn.row_factory = sqlite3.Row` before querying.

**Test result**: PASS — trajectory healthy (2 entries, no repetition).

## Key Lesson

Not all guardrails from the spec are relevant to every pipeline implementation. The spec lists 34 failure modes, but some are already handled by architectural decisions (different gateways = model diversity, container isolation = network restriction, individual gate_outcomes recording = no aggregate banners). Evaluating relevance AFTER wiring and running the pipeline is more effective than trying to predict relevance before building — the gate_outcomes data tells you which guards actually fire and which are dead code.
