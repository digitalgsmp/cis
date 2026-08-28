# POST /api/relay/run — daemon thread → resume() chain

Verified against the codebase on 2026-08-22 (Brain session, "pipeline smoke check 2").
All line numbers are from that checkout; re-verify if the files move.

## The chain (endpoint → thread → state machine)

1. `runtime/container_app.py:39-77` — `POST /api/relay/run` (lean endpoint).
   - Reuses `_check_auth`, `_run_pipeline_background`, `_active_runs` from `api.relay`
     (imported at container_app.py:37). No mwl-proof pre-flight, no 1-hour idempotency
     window — every call creates a fresh run (contrast with `POST /api/relay/start`).
   - `PipelineRelay().start_sync(intent)` at line 57 → creates the workflow_runs row
     synchronously and sets status BRAIN_PHASE.
   - run_id validated as non-empty string (lines 58-59), else 500.
   - Lines 65-71: `threading.Thread(target=_run_pipeline_background, args=(run_id, intent), daemon=True)`,
     registered in `_active_runs[run_id]`, started.
   - Returns `{run_id, status: "BRAIN_PHASE", message}` (lines 73-77).

2. `runtime/api/relay.py:110-139` — `_run_pipeline_background(run_id, intent, db_path=None)`.
   - Inserts `runtime/abstraction` into sys.path (117-122), imports PipelineRelay (124),
     calls `asyncio.run(relay.resume(run_id))` at line 128 — THE call the smoke check proves.
   - Exceptions land in `_active_runs[run_id]["error"]` (129-133); finally sets
     `finished_at` and closes the relay (134-139).

3. `runtime/abstraction/pipeline_relay.py:2095-2104` — `start_sync` docstring states the
   contract under test: "The API layer calls this to create the run, then launches
   resume() in a background thread."
   `resume()` (2106-2141) is NOT a stub: loads the run, bails on TERMINAL_STATES, then
   dispatches on current status to _brain_phase / _intent_review / _draft_phase /
   _proposal_review / _pattern_catalog / _code_review_gate / _execution / _verification.

## Smoke-check procedure (verify only — build nothing)

1. Pre-flight: `curl -s http://127.0.0.1:5000/api/ping` (expect pong) and
   `curl -s http://127.0.0.1:5000/api/relay/health` (gateways 8644-8648; a 401 with
   "gateway alive" counts as healthy). Quick per-port check:
   `for p in 8644 8645 8643 8647 8646 8648; do curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$p/health; done`
   — expect 200s.
2. POST a trivial intent (matches recent test-run pattern, e.g. greet.py-style):
   `curl -s -X POST http://127.0.0.1:5000/api/relay/run -H 'Content-Type: application/json' -d '{"intent":"..."}'`
   → capture run_id.
3. Poll `GET /api/relay/<run_id>`. THE evidence is the run's `status` advancing off the
   synchronously-set BRAIN_PHASE into later phases (INTENT_REVIEW → DRAFT_PHASE → ...):
   raw DB state only the background thread's resume() call can produce. Self-report is
   not truth — polled transitions are the proof.
4. Failure signals: `background.active` false while status is stuck at BRAIN_PHASE,
   or non-empty `background.error` in the status payload (relay.py:335-339).
   Both read from `_active_runs` bookkeeping.

## Design facts worth remembering

- One thread per /run call, each with its own `asyncio.run()` event loop — safe because
  a thread never handles two runs.
- `daemon=True`: the thread dies if the container process exits, but the run row survives
  in SQLite and resume() re-dispatching from its stored status is the crash-recovery design.
- The smoke run consumes real gateway tokens; keep the intent minimal.
- Side effect: the test creates a real workflow_runs row — that is the mechanism under
  test, not new build work, so it does not trip the Do Not Start list.
