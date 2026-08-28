# Intent Submission Guidelines

How to craft and submit intents to the CIS pipeline relay.
Covers both the container API (port 5000) and direct Python calls.

## What Is an Intent?

An intent is the text Eric (or an operator) submits to the pipeline to
start a workflow run. It becomes the `workflow_runs.topic` value in the
spine DB and is the primary input Brain uses to understand the task.

## Submission Methods

### Container API (production)

```bash
curl -s -X POST http://localhost:5000/api/relay/start \
  -H "Content-Type: application/json" \
  -d '{"intent": "Add a /api/ping endpoint to runtime/container_app.py that returns JSON with status and timestamp"}' \
  | python3 -m json.tool
```

Returns: `{"run_id": "run-<hash>-<timestamp>", "status": "BRAIN_PHASE"}`

### Direct Python (development)

```python
import asyncio
from runtime.abstraction.pipeline_relay import PipelineRelay
r = PipelineRelay()
run_id = asyncio.run(r.start('Your task description here'))
```

## Intent Length — No Truncation (Fixed 2026-07-09)

**Previously**: intents were truncated to 500 chars by `intent_text[:500]`
in `_create_run()`. This silently cut multi-component plans — only the first
component was visible to Brain and downstream agents.

**Fixed**: the `[:500]` truncation was removed. SQLite TEXT has no length
limit. Full intents (tested up to 4220 chars) are stored and visible to all
agents. Brain confirmed seeing all 14 components of a multi-paragraph intent.

**Verify after submission**:
```sql
SELECT length(topic), substr(topic, 1, 80), substr(topic, -80)
FROM workflow_runs WHERE id = '<run_id>';
```
`length(topic)` should match your submitted intent length.

**Best practice**: Even though truncation is fixed, keep intents focused.
For multi-component plans, either submit separate runs per component (the
pipeline is designed for single-task units), or write a spec to disk and
reference its path in a short intent:

```json
{"intent": "Read docs/BUILD_PLAN.md and implement Component 1: Control Plane UI. The spec has full details."}
```

Brain's pre-discovery will find the file, and the intent stays clean.

## Good Intent Patterns

**Single focused task:**
```
Add a /api/ping endpoint to runtime/container_app.py that returns
JSON with status and timestamp fields.
```

**Reference a spec:**
```
Read docs/SPEC_CODE_REVIEW_GATE.md and implement the chunk-based
review pattern described in §4. Start with the _review_single_chunk
function.
```

**Build on prior work:**
```
The previous run (run-abc123) added the /api/health endpoint.
Now add a /api/health/detailed endpoint that returns per-gateway
status with response times.
```

## Bad Intent Patterns

**Vague intent with no file paths:**
```
Make the pipeline better.
```
Brain's pre-discovery can't find what "better" means. Always include
specific file paths, function names, or spec references.

**Intent that duplicates an existing spec:**
```
Design a code review gate with sequential three-pass review...
```
A spec for this already exists at `docs/SPEC_CODE_REVIEW_GATE.md`.
Reference the spec instead of re-describing it in the intent.

## Monitoring a Submitted Run

```bash
# Status via container API
curl -s http://localhost:5000/api/relay/<run_id> | python3 -m json.tool

# Spine DB status
sqlite3 data/cis_memory.db \
  "SELECT status, result, rounds_completed FROM workflow_runs WHERE id = '<run_id>';"

# Round details
sqlite3 data/cis_memory.db \
  "SELECT id, round_number, drafter_role, reviewer_signal
   FROM deliberation_rounds WHERE run_id = '<run_id>' ORDER BY id;"

# Verify intent was not truncated
sqlite3 data/cis_memory.db \
  "SELECT length(topic) FROM workflow_runs WHERE id = '<run_id>';"
```
