# Flask + Async Pipeline Integration

## Problem

`pipeline_relay.py` is an async state machine using `asyncio` + `httpx`.
Flask is synchronous. How do you expose the async pipeline behind Flask
endpoints without blocking the request thread?

## Solution: start_sync() + Background Thread

### 1. Add a sync run-creation method to PipelineRelay

```python
def start_sync(self, intent_text: str) -> str:
    """Create a new pipeline run (sync, non-async). Does NOT start processing."""
    run_id = _create_run(self.conn, intent_text)
    _set_run_status(self.conn, run_id, "BRAIN_PHASE")
    return run_id
```

This creates the `workflow_runs` row and sets status to `BRAIN_PHASE`
without calling any async methods. The API endpoint returns the `run_id`
immediately.

### 2. Launch the async pipeline in a daemon thread

```python
_active_runs: Dict[str, dict] = {}  # run_id -> {thread, error, started_at}

def _run_pipeline_background(run_id: str, intent: str) -> None:
    from pipeline_relay import PipelineRelay
    relay = PipelineRelay()
    try:
        asyncio.run(relay.resume(run_id))
    except Exception as e:
        _active_runs[run_id] = {**_active_runs.get(run_id, {}), "error": str(e)}
    finally:
        relay.close()
        _active_runs[run_id] = {**_active_runs.get(run_id, {}), "finished_at": time.time()}
```

### 3. Flask endpoint creates run + launches thread

```python
@relay_bp.route("/api/relay/start", methods=["POST"])
def relay_start():
    data = request.get_json(silent=True) or {}
    intent = (data.get("intent") or "").strip()

    # Create run synchronously
    relay = PipelineRelay()
    run_id = relay.start_sync(intent)
    relay.close()

    # Launch async pipeline in background
    thread = threading.Thread(target=_run_pipeline_background, args=(run_id, intent), daemon=True)
    _active_runs[run_id] = {"thread": thread, "started_at": time.time()}
    thread.start()

    return jsonify({"run_id": run_id, "status": "BRAIN_PHASE"})
```

### 4. Resume after Eric Gate approval

Same pattern — launch `resume()` in a background thread:

```python
if decision == "APPROVE":
    thread = threading.Thread(target=_run_pipeline_background, args=(run_id, run["topic"]), daemon=True)
    thread.start()
```

`resume()` reads status from `workflow_runs` and dispatches to the right phase.

## Cross-Round Output Aggregation

`deliberation_rounds` stores each phase's output in a separate column
(`brain_output`, `drafter_output`, `reviewer1_output`, etc.). Each round
only fills its own column — the rest are empty strings.

The status endpoint searches backward through rounds for the latest
non-empty value for each field:

```python
def _latest_nonempty(field: str) -> Optional[str]:
    for r in reversed(rounds):
        val = r.get(field)
        if val and val.strip():
            return val
    return None
```

## Flask Python Version

CIS Flask app runs on `python3.12`, NOT the system `python3` (no Flask installed).
Always use: `python3.12 /mnt/projects/cis/runtime/app.py`

## /api/relay/run: Lean Endpoint in container_app.py

`POST /api/relay/run` (defined in `container_app.py:39-77`, not in the
relay blueprint) is the lean counterpart to `POST /api/relay/start`:

- No mwl-proof-v2 pre-flight check
- No 1-hour idempotency window — every call creates a fresh run
- Reuses `_check_auth`, `_run_pipeline_background`, and `_active_runs`
  from `api.relay` (imported directly)
- Same daemon-thread pattern: `start_sync()` creates the run, then
  `threading.Thread(target=_run_pipeline_background, daemon=True).start()`

When both endpoints exist, prefer `/api/relay/run` for smoke checks
(no idempotency dedup, no pre-flight overhead).

## CRITICAL PITFALL: Uncommitted Code Changes Are Not Live in Running Flask

Flask loads all routes at import time. If you add or modify an endpoint
in `container_app.py` and the running server process predates the
change, the new route returns 405 Method Not Allowed — even though
`app.url_map` shows it when you import the module fresh in a separate
process.

Verification:
```bash
ps -p $(pgrep -f container_app) -o lstart --no-headers
stat -c '%y' runtime/container_app.py
# If file mtime > process start time, the server has stale code
```

Fix: restart the server (or `docker restart cis-pipeline`) after code
changes to Flask route definitions.

## Key Files

- `runtime/container_app.py` — Flask app (container entry point, registers `relay_bp` + own routes like `/api/relay/run`)
- `runtime/api/relay.py` — Flask blueprint (relay endpoints: /start, /<run_id>, /<run_id>/answer, /health, etc.)
- `runtime/abstraction/pipeline_relay.py` — async state machine + start_sync() + resume()
- `runtime/app.py` — legacy Flask app (superseded by container_app.py in container context)

## Idempotency

`POST /api/relay/start` checks for existing non-terminal runs with same
intent hash within 1 hour. Returns existing `run_id` if found.

## Per-Role Agent Timeouts

The default `AGENT_TIMEOUT=180s` is too short for tool-using agents. The
background thread pattern means a timeout will silently set the run to
ERROR — the Flask request already returned, so there's no user-visible
error until they poll status.

`pipeline_relay.py` defines per-role overrides:

```python
AGENT_TIMEOUTS = {
    "verify": 600,   # 10 min — runs evidence commands (git diff, tests)
    "menter": 600,   # 10 min — builds code
    "brain": 300,    # 5 min — xhigh reasoning
    "draft": 300,    # 5 min — xhigh reasoning
}
# Default: 180s for reviewers (parallel, shorter responses)
```

When a phase fails with `reviewer_signal=ERROR` and no output, check
whether the timeout was too short before investigating the gateway.

## Gate Endpoint Directive Hash

The gate endpoint must filter `drafter_output != ''` when computing the
directive hash — proposal_review rounds have `drafter_output=''` (default
empty string, not NULL). Without this filter, the hash is SHA256 of empty
string (`e3b0c44298fc1c14...`) and Menter receives an empty directive.
