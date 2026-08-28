# POST /api/relay/run — Verified Wiring Map & Smoke-Check Flags

Verified read-only by a Brain session, 2026-08-22. Ground truth = the code, not docs.

## Wiring chain (implemented, runtime/container_app.py:39)

1. Route: `@app.route("/api/relay/run", methods=["POST"])` registered directly on the
   Flask app in `runtime/container_app.py` — NOT on the relay blueprint. `relay_bp`
   (registered at line 27) owns the rest of `/api/relay/*`.
2. Auth: `from api.relay import _check_auth` (`api/relay.py:43`) — same optional
   bearer-token rule as the relay family (`CIS_PIPELINE_API_KEY`).
3. Body: `{"intent": str}`. Missing/empty intent → 400 `{"error": "intent required"}`.
4. Run creation: `PipelineRelay.start_sync(intent)` (`abstraction/pipeline_relay.py:2095`)
   → `_create_run` inserts a `workflow_runs` row, sets status `BRAIN_PHASE`, returns the
   `run_id` string. `start_sync` does NOT begin processing — by design.
5. Async spawn: daemon thread runs `_run_pipeline_background(run_id, intent)`
   (`api/relay.py:110`) → `asyncio.run(relay.resume(run_id))`; tracked in `_active_runs`
   (`api/relay.py:107`).
6. Response: 200 `{"run_id", "status": "BRAIN_PHASE", "message": "Pipeline started. Poll
   GET /api/relay/<run_id> for status."}`. Non-string run_id or exception → 500.

No route conflict: `relay_bp` has `/api/relay/runs` (plural, GET, `api/relay.py:725`) —
distinct from `/api/relay/run`, so app boot is safe.

## Drift flags to check before trusting any smoke test

- **Stale spec:** `docs/SPEC_RELAY_RUN_ENDPOINT.md` (2026-08-22, DRAFT pre-review)
  specifies a DIFFERENT contract: synchronous Draft-gateway-only call to port 8645,
  `prompt` field, 201 + `artifact_path` + `draft_bytes`, writes
  `artifacts/<run_id>/draft.md`. The implemented endpoint is a lean full-pipeline async
  start with an `intent` field. Verify against implemented code (Commandment 9); flag the
  spec, never use it as acceptance criteria.
- **Spine path gotcha:** `pipeline_relay.py` DB_PATH defaults to
  `/mnt/projects/cis/data/cis_memory.db` (via `CIS_SPINE_PATH`); the in-workspace spine is
  `/workspace/cis/data/cis_memory.db`. Without `CIS_SPINE_PATH` + `CIS_PROJECT_ROOT`
  exported, `start_sync` writes the `workflow_runs` row to the wrong DB and the smoke
  check falsely fails. Exporting these env vars is part of wiring verification, not a code
  change.
- **Side effect:** a happy-path POST genuinely starts a full pipeline run (spawns agent
  calls against the 6 gateways). For a wiring-only check, scope to row creation + thread
  spawn, or accept the side effect explicitly.
- **Runtime reality:** check for a live listener on port 5000 (and 8643–8648) before
  curling; in a fresh environment none may be up and the app must be started first
  (running it is a runtime action, not a build).

## Minimal smoke-check shape (Eric's preferred minimalism)

1. Import check: `python -c` import of `container_app` with the runtime dir on sys.path.
2. POST missing intent → 400.
3. POST with intent → 200, string `run_id`, `workflow_runs` row present in the spine.
4. Auth check only if `CIS_PIPELINE_API_KEY` is configured.

No governance apparatus, no test matrix — Eric builds creative tools and flags
enterprise-pattern drift.

## Git note

As of 2026-08-22 the endpoint is uncommitted: `git log -S 'relay/run'` finds no commit
that ever contained the route, and both `runtime/container_app.py` and
`runtime/abstraction/pipeline_relay.py` sit modified in the working tree. "Committed"
means pushed to GitHub — a local working tree is not a backup.
