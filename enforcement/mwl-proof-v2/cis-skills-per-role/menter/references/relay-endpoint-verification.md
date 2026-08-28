# Verifying Relay Endpoint Changes (container_app / api.relay)

Proven workflow from the POST /api/relay/run Menter chunk (2026-08-22). Applies to any endpoint delta in runtime/container_app.py or runtime/api/relay.py, and to Verify-stage re-checks of those deltas.

## Environment facts

- System python3 (3.11) has NO flask. The Verify-stage venv is /tmp/cis_verify_venv (flask 3.1.3, httpx, PyYAML). Use its bin/python for every test-client run and the import-integrity check. If it is missing: `python3 -m venv /tmp/cis_verify_venv && /tmp/cis_verify_venv/bin/pip install flask httpx`.
- CIS_SPINE_PATH=/workspace/cis/data/cis_memory.db — the PRODUCTION spine (~4.8GB, WAL). Test POSTs write REAL rows here. Do not point tests at it casually; do not DELETE rows afterwards (non-destructive rule). Document the smoke run IDs in the chunk summary instead — non-terminal runs are resumable by design.
- CIS_PIPELINE_API_KEY is unset by default → auth disabled. To test the 401/200 matrix, export it in a separate subprocess (module reads it at import time), e.g. `CIS_PIPELINE_API_KEY=testkey <venv python> auth_probe.py`.
- Gateways are LIVE on this host at 127.0.0.1:8643-8648 (Brain 8644, Draft 8645, Review1 8643, Review2 8647, Menter 8646, Verify 8648). Any POST that spawns the pipeline thread WILL call them and burn real tokens. Use trivial intents that end with "do not build anything".

## Verification battery (maps to spec completion criteria)

1. Import integrity: `cd runtime && <venv python> -c "from container_app import app"` → exit 0.
2. test_client happy path → 200, run_id matching `^run-[0-9a-f]{16}-[0-9]{10}$`, status BRAIN_PHASE.
3. Missing intent → 400 `{"error": "intent required"}`.
4. Auth matrix (separate env): no header → 401, wrong key → 401, correct Bearer → 200 + DB row.
5. DB evidence: raw sqlite3 SELECT on workflow_runs for the returned run_id → one row, BRAIN_PHASE.
6. Thread evidence: `_active_runs[run_id]` entry with `thread.is_alive()`; GET /api/relay/<run_id> → `background.active` true; then PROGRESSION: status advances past BRAIN_PHASE.
7. No regression: /api/health and /api/ping 200; GET on the literal route path still resolves via the blueprint dynamic rule (404 Run not found, not 405); /start still 400 on empty intent; url_map contains the new POST rule.

## Pitfalls

- Daemon threads die with the test process. In-process waits cannot observe progression — run a POLLER as a long-lived separate process: POST once, then loop checking DB status every ~20s until status != BRAIN_PHASE or error/finished_at appears in _active_runs. The Brain gateway can take up to 300s (xhigh reasoning); a 90s budget is too short. Hard cap ~12 min, then report timeout honestly.
- Flask url_map: str(rule) omits HTTP methods. Assert on rule.rule + rule.methods, e.g. `[r.methods for r in app.url_map.iter_rules() if r.rule == "/api/relay/run"]` contains "POST".
- search_files (ripgrep) can return 0 hits for regex alternation patterns (`def (a|b)`) in this repo while the symbols exist. Before concluding a route/symbol does not exist, cross-check with terminal `grep -n`. Never report "not present" off a single tool.
- The working tree carries other agents' uncommitted work (e.g. an unrelated /dashboard/ route in container_app.py). Run `git status` FIRST, scope your edits to the spec, leave others' work untouched, and report your delta as the chunk-attributable diff — not the whole file diff.
- The /run endpoint's lean design is intentional: no pre-flight (mwl-proof-v2), no idempotency window — every POST creates a fresh run. Full /start parity is a one-line delegation to relay_start() if ever wanted; do not copy the pre-flight machinery.
