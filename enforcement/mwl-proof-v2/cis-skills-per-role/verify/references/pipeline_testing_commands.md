# Pipeline Testing Commands

Reference for starting, monitoring, approving, and resuming CIS pipeline runs.
All commands assume `cd /mnt/projects/cis` as working directory.

## Container Lifecycle

### Start the container (production)

The correct Docker image is `cis-hermes:pipeline` (NOT `cis-hermes:pinned`).
The `pinned` image has a bare `sleep infinity` CMD and lacks the entrypoint
and profile configs. The `pipeline` image has the full entrypoint baked in.

```bash
sg docker -c "docker run -d \
  --name cis-pipeline \
  -p 5000:5000 \
  -v /mnt/projects/cis:/workspace/cis \
  -v /tmp/cis-secrets.env:/workspace/secrets.env:ro \
  cis-hermes:pipeline"
```

### Restart the container

```bash
sg docker -c "docker restart cis-pipeline"
```

**Note**: `entrypoint.sh` now cleans stale pidfiles on startup. Previously,
`docker restart` preserved `/tmp`, causing old pidfiles to skip gateway startup
("already running (pid 33)") — only 4/6 gateways would come up. The fix
removes all role pidfiles at the top of entrypoint.sh before launching.

### Check gateway health

```bash
curl -s http://localhost:5000/api/relay/health | python3 -m json.tool
```

Expected: `gateways_healthy: 6, gateways_total: 6`. Gateways returning HTTP 401
are healthy (auth required = process alive). "Connection refused" = gateway
not yet started or crashed.

### View container logs

```bash
sg docker -c "docker logs cis-pipeline 2>&1 | tail -30"
```

### Per-gateway logs (inside container)

```bash
sg docker -c "docker exec cis-pipeline cat /tmp/cis-logs/brain.log"
# Also: draft.log, review1.log, review2.log, menter.log, verify.log
```

## Start a Pipeline Run

### Container API (production)

```bash
curl -s -X POST http://localhost:5000/api/relay/start \
  -H "Content-Type: application/json" \
  -d '{"intent": "Add a /api/ping endpoint to runtime/container_app.py"}' \
  | python3 -m json.tool
```

Returns: `{"run_id": "run-<hash>-<timestamp>", "status": "BRAIN_PHASE"}`

### Direct Python (development)

```python
import asyncio
from runtime.abstraction.pipeline_relay import PipelineRelay
r = PipelineRelay()
run_id = asyncio.run(r.start('Your task description here'))
print(f'COMPLETED: {run_id}')
```

## Resume a Pipeline Run

After Eric Gate approval or after any interruption:

```python
import asyncio
from runtime.abstraction.pipeline_relay import PipelineRelay
r = PipelineRelay()
asyncio.run(r.resume('<run_id>'))
print('PIPELINE DONE')
```

## Monitor Pipeline Progress

### Run status

```sql
SELECT status, result, rounds_completed
FROM workflow_runs WHERE id = '<run_id>';
```

### Round-by-round progress

```sql
SELECT id, round_number, drafter_role, reviewer_signal
FROM deliberation_rounds WHERE run_id = '<run_id>' ORDER BY id;
```

### Agent trajectories

```sql
SELECT id, role, phase, outcome, substr(output_text, 1, 80)
FROM agent_trajectories WHERE run_id = '<run_id>'
ORDER BY id;
```

### Verify intent was not truncated

```sql
SELECT length(topic) FROM workflow_runs WHERE id = '<run_id>';
```

### Gateway health (container)

```bash
curl -s http://localhost:5000/api/relay/health | python3 -m json.tool
```

## Eric Gate Approval

### Via container API

```bash
curl -s -X POST http://localhost:5000/api/relay/<run_id>/gate \
  -H "Content-Type: application/json" \
  -d '{"decision": "APPROVE", "rationale": "proceed"}' | python3 -m json.tool
```

### Direct sqlite3 (when API unavailable)

```python
import sqlite3, hashlib
from datetime import datetime, timezone

conn = sqlite3.connect('data/cis_memory.db')
conn.row_factory = sqlite3.Row
run_id = '<run_id>'

# Verify current status
run = conn.execute('SELECT status FROM workflow_runs WHERE id = ?', (run_id,)).fetchone()
assert run['status'] == 'ERIC_GATE', f"Expected ERIC_GATE, got {run['status']}"

# Get directive hash
latest = conn.execute(
    'SELECT drafter_output FROM deliberation_rounds '
    'WHERE run_id = ? AND drafter_output != "" '
    'ORDER BY id DESC LIMIT 1', (run_id,)).fetchone()
directive_hash = hashlib.sha256(latest['drafter_output'].encode()).hexdigest()
now = datetime.now(timezone.utc).isoformat()

# Mark previous approvals as non-current
conn.execute('UPDATE eric_gate_approvals SET is_current = 0 WHERE workflow_run_id = ?', (run_id,))

# Write immutable audit record
conn.execute(
    'INSERT INTO eric_gate_approvals '
    '(workflow_run_id, decision, rationale, decided_at, '
    'goal_reference_id, briefing_hash, briefing_json, '
    'drift_snapshot_json, decision_trail_snapshot_json, '
    'is_current, created_at) '
    'VALUES (?, ?, ?, ?, 0, ?, "{}", "{}", "{}", 1, ?)',
    (run_id, 'APPROVE', 'rationale here', now, directive_hash, now))

# Update run status to PATTERN_CATALOG
conn.execute(
    'UPDATE workflow_runs SET status = "PATTERN_CATALOG", '
    'directive_hash = ?, eric_approved_at = ? WHERE id = ?',
    (directive_hash, now, run_id))
conn.commit()
print(f'Approved. Status set to PATTERN_CATALOG')
```

Then resume the pipeline with `r.resume('<run_id>')`.

## Key State Transitions

```
BRAIN_PHASE -> INTENT_REVIEW -> DRAFT_PHASE -> PROPOSAL_REVIEW
  -> ERIC_GATE -> PATTERN_CATALOG -> CODE_REVIEW_GATE
  -> EXECUTION -> VERIFICATION -> terminal (CONSENSUS_REACHED / VERIFY_FAILED / ESCALATE)
```

OBJECTIONS in intent review send back to BRAIN_PHASE (max 2 rounds).
OBJECTIONS in proposal review send back to DRAFT_PHASE (max 3 rounds).
OBJECTIONS in code review send back to chunk revision (max 3 per chunk).

## Pitfalls

- **`start_sync()` does NOT process** — it only creates the run. The API
  calls `start_sync()` then launches `resume()` in a background thread.
- **Code committed after a run can't be tested by that run** — start
  a new run after committing pipeline code changes.
- **Pipeline runs take 5-15+ minutes** — use background mode with
  `notify_on_complete=true` for long runs.
- **Code review gate is the longest phase** — 3-pass sequential review
  (Menter -> Review1 -> Review2 -> Consensus) per chunk, with up to 3
  revision cycles per chunk.
- **Use `sg docker -c` for all docker commands** — the `eric` user is
  not in the `docker` group. Use `sg docker -c "docker ..."` to execute
  docker commands with the docker group's privileges.
