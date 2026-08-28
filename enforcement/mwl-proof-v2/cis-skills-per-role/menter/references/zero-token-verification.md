# Zero-Token Deterministic Verification of Pipeline/API Changes

How to verify changes to runtime code (container_app.py, api/relay.py,
pipeline_relay.py) without spending a single gateway token and without
touching the production spine. Proven on the POST /api/relay/run chunk.

## Core principle

All 6 gateways are LIVE (ports 8643-8648, /health returns 200). Any real
POST to /api/relay/run or /api/relay/start triggers a full pipeline run
with token spend. Never fire a live gateway call during verification.
Instead: pre-trip the DB-backed circuit breaker so the pipeline fails
deterministically BEFORE any HTTP.

## Pre-tripping the circuit breaker

`_breaker_is_tripped` (pipeline_relay.py ~line 157) reads the
`circuit_breaker_state` table: failures >= 3 with a recent last_failure_ts
raises ConnectionError before `check_gateway`/HTTP. Pre-trip in the
throwaway DB:

    INSERT OR REPLACE INTO circuit_breaker_state
      (role, failures, last_failure_ts, updated_at)
      VALUES ('brain', 3, <time.time()>, <iso-now>);

Evidence after a run: failures count incremented (3→4), thread logs
"Circuit breaker tripped for brain", and no gateway call was made.

## Throwaway spine DB from production schema (read-only)

    src = sqlite3.connect(f"file:/workspace/cis/data/cis_memory.db?mode=ro", uri=True)
    ddl = {r[0]: (r[1], r[2]) for r in src.execute(
        "SELECT name, type, sql FROM sqlite_master WHERE sql IS NOT NULL")}

PITFALL: sqlite_master also lists sqlite_autoindex_* rows whose `sql` IS
NULL — iterating names broadly and indexing into ddl raises KeyError.
Filter on `sql IS NOT NULL` first, then create objects in dependency
order:
  1. base tables: workflow_runs, deliberation_rounds, circuit_breaker_state, agent_trajectories
  2. FTS virtual table: agent_trajectories_fts (external-content FTS5)
  3. triggers: trajectories_ai/ad/au (reference the FTS table)
Indexes are performance-only — skip them for verification DBs.
Missing the FTS table breaks every trajectory INSERT via its trigger.

## Env caching: fresh subprocess for different env

pipeline_relay computes DB_PATH from CIS_SPINE_PATH at MODULE IMPORT
time and caches it. In-process os.environ mutation after import has no
effect. Any test needing a different spine path, auth key set/unset,
or a schemaless DB must run in a fresh subprocess:

    subprocess.run([sys.executable, "-c", code], env={...}, timeout=60)

Auth is enabled by CIS_PIPELINE_API_KEY being set (checked at import).
Unset it for auth-disabled checks, set it for the 401/200 matrix.

## Dependencies

pipeline_relay imports httpx AND yaml (pyyaml) at module level;
api.relay needs Flask. A /tmp verification venv needs all three:
`pip install flask httpx pyyaml`. System python usually lacks Flask.
Delta discipline: keep the venv in /tmp, never touch repo requirements.

## Constructing the route's OWN error branch (explicit 500)

- Works: zero-byte schemaless DB. Connect succeeds (SQLite accepts empty
  file), the INSERT inside start_sync fails inside the route's try block,
  route returns its explicit 500 {"error": "Failed to create run: ..."}.
- Does NOT work: locked DB. pipeline_relay connects in its CONSTRUCTOR,
  outside the route's try block → Flask generic 500, not the route's
  error path. Also _db_connect sets busy_timeout=5000, so lock tests
  block ~5s anyway.

## GET status semantics (for assertions)

GET /api/relay/<run_id> → background.active True = run in _active_runs,
no finished_at. On breaker-driven failure the resume thread records the
error + finished_at, so status advances INTAKE → BRAIN_PHASE → ERROR.
Assert "advanced" as: status left {INTAKE, BRAIN_PHASE} OR finished_at
present — the thread can finish in <1s, don't require active=True to
still hold.
Route-collision check: GET /api/relay/run must hit the blueprint dynamic
rule and return 404 (proves the app-level POST /run doesn't shadow it).

## Harness conventions (ad-hoc verification)

- Script under /tmp with hermes-verify- prefix; DBs via
  tempfile.mkdtemp(prefix="hermes-verify-"); cleanup with rmtree.
- Assert raw sqlite3 evidence (rows, breaker counts, trajectory counts),
  never self-reported status. Status fields: workflow_runs.result must
  stay PENDING unless the pipeline actually reached consensus.
- Counter pitfall: when result lines append detail after "PASS", count
  with `": PASS" in line`, not line.endswith("PASS").
- rmtree can silently fail (ignore_errors) if a daemon thread still
  holds the DB open; do a shell-level `rm -rf /tmp/hermes-verify-*`
  sweep after the run.
- Post-run hygiene: confirm production spine untouched — mtime predates
  the test window AND zero rows with test topics
  (topic LIKE '%hermes-verify%' OR topic LIKE '%smoke%').

## Noise to expect (not failures)

- `[pipeline] ...` prints from pipeline_relay are pre-existing, not ours.
- "KB ingest failed ... no such table: knowledge_messages" — swallowed by
  _pre_discovery; knowledge_messages isn't copied into throwaway DBs.
- "Run ... → ERROR (no Telegram notification configured)" — the error
  recording itself works; that's the expected breaker-driven path.

## Universal-rules checklist applied to every chunk

1. No default success: report the state start_sync actually set
   (e.g. BRAIN_PHASE), never fabricate consensus/success.
2. Explicit errors: 401/400/500 tuples with error strings; no bare
   except; relay.close() in finally.
3. No secrets in code or responses.
4. No prints/TODOs in committed code.
5. Claims backed by test_client + raw sqlite evidence, not narration.
6. All test artifacts in /tmp; only the target repo file modified.
7. Run state persists in the workflow_runs SQLite row (_active_runs is
   transient bookkeeping, same as /start).
8. Validate inputs before use (run_id type/emptiness before thread
   registration).
