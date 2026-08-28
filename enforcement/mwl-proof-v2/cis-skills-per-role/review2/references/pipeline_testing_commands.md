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

## Runtime Smoke Check: Verify Daemon Thread Drives Resume

When you need to verify (read-only) that the background thread actually
executes `resume()` and the state machine progresses.

### Preferred endpoint: /api/relay/run

`/api/relay/run` (container_app.py:39-77) is the lean counterpart to
`/api/relay/start` (api/relay.py:167). Key differences:
- No mwl-proof-v2 pre-flight check
- No 1-hour idempotency window (every call creates a fresh run)
- Defined directly in container_app.py, not in the relay blueprint
- Same `_run_pipeline_background` thread pattern, same `resume()` call

Both endpoints prove the same daemon-thread-drives-resume contract.
Prefer `/api/relay/run` for smoke checks — no pre-flight, no idempotency
window, simpler surface area.

### Pre-step: capture gateway health before the POST

```bash
curl -s http://localhost:5000/api/relay/health | python3 -m json.tool
```

Expected: `gateways_healthy: 6, gateways_total: 6`, all `healthy: true`
with 401 counted as alive. Save this output — it proves gateways were
up at the time of the run, which disambiguates failures later.

### Step 1: POST a minimal intent

```bash
curl -s -X POST http://localhost:5000/api/relay/run \
  -H "Content-Type: application/json" \
  -d '{"intent": "smoke check: verify relay resume works"}' \
  | python3 -m json.tool
```

Expect HTTP 200 with `run_id` (non-empty string) and `status: BRAIN_PHASE`.
Save raw response verbatim. A 500 here means `start_sync` broke, not resume.

### Step 2: Poll every 5 seconds, up to 10 minutes

Brain phase runs pre-discovery with web_search, so the first advance
can take several minutes. Each snapshot: record `status`,
`rounds_completed`, `latest_phase`, `latest_signal`, presence of non-empty
`brain_output`, `background.active`, `background.error`.

```bash
curl -s http://localhost:5000/api/relay/<run_id> | python3 -m json.tool
```

Save at least 3 raw snapshots verbatim: initial (should show
`active: true`), one showing transition off `BRAIN_PHASE`, and final.

### Step 3: Completion check

`background.active` flips `true -> false`, `background.error` is `null`.
That means the daemon thread finished `resume()` without exception.

### Pass criteria (all must hold)

P1. POST returns 200 with non-empty `run_id` and `status: BRAIN_PHASE`.
P2. At least two poll snapshots show a state transition: one with a
    deliberation round of `drafter_role: brain` and non-empty
    `brain_output`, a later one with `status != BRAIN_PHASE`.
P3. `background.active` true in early snapshots, false at completion;
    `background.error` null at every snapshot.
P4. Final status in `{CONSENSUS_REACHED, ESCALATED, VERIFY_FAILED,
    STALE, ERROR, WAITING_FOR_HUMAN, ERIC_GATE}` with
    `rounds_completed >= 1` and non-empty `brain_output`.

### Stop states vs terminal states

`WAITING_FOR_HUMAN` and `ERIC_GATE` are STOP states, not terminal states.
`resume()` returns from them without advancing (prints a message, returns).
`TERMINAL_STATES` (pipeline_relay.py:94) = `{CONSENSUS_REACHED, ESCALATED,
VERIFY_FAILED, STALE, ERROR}` — `resume()` returns immediately for those.

Reaching `ERIC_GATE` or `WAITING_FOR_HUMAN` is a valid pass — the
mechanism drove the run there. Do NOT call `/api/relay/<run_id>/answer`
or `/gate` to advance further — that is acting as Eric.

### Failure disambiguation (keep these hypotheses separate in the report)

F1. POST 500 -> `start_sync` broke, not resume. Report exact error body.
F2. `background.error` non-null -> resume exception. Report the exact
    error string and how far the run advanced before it.
F3. `active` flips false quickly with no rounds row and status still
    `BRAIN_PHASE` -> resume returned without doing work. Report status.
F4. Stuck at `BRAIN_PHASE` past 10 minutes with `active: true`,
    `error: null` -> suspect gateway slowness, NOT resume. Re-run
    `GET /api/relay/health` and report per-gateway latency. Never
    attribute a gateway timeout to resume (Eric's verification-
    hardening rule: self-report is not truth).

### Evidence bar (Eric's rule: self-report is not truth)

The report must contain, verbatim: the POST response, at least three
raw GET snapshots (initial, transition, final), and the pre-POST
`/api/relay/health` output. A prose "it worked" without these raw
payloads is not a pass.

### Auth check: verify /proc/PID/environ

To determine whether auth is required for the smoke check, inspect the
running process's environment:

```bash
# Find the Flask process PID
ps aux | grep 'container_app' | grep -v grep
# Check for API key
cat /proc/<PID>/environ | tr '\0' '\n' | grep CIS_PIPELINE_API_KEY
# If empty/absent, _check_auth is a no-op — no Authorization header needed
# Also check spine path
cat /proc/<PID>/environ | tr '\0' '\n' | grep CIS_SPINE_PATH
```

When `CIS_PIPELINE_API_KEY` is absent from the process environment,
`_check_auth()` (api/relay.py:43-55) returns `None` — auth is disabled
and no `Authorization` header is needed on any API call.

### CRITICAL PITFALL: Uncommitted Code Is Not Live

Flask loads routes at import time. If you add a new endpoint to
`container_app.py` (or any Flask app) and don't restart the server
process, the route returns 405 Method Not Allowed — even though the
code is correct and `app.url_map` shows it when you import the module
fresh in a separate process.

Verification: `ps -p <pid> -o lstart` shows when the server process
started. `stat -c %y <file>` shows when the code was last modified.
If the file is newer than the process, the running server has stale
code.

To make new endpoints live:
```bash
# If running in Docker:
sg docker -c "docker restart cis-pipeline"
# If running as a bare process:
kill <pid> && cd /workspace/cis/runtime && python3 -c \
  "from container_app import app; app.run(host='0.0.0.0', port=5000)"
```

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
