# Relay Endpoint Chunk Verification — Pitfalls (CIS runtime)

Session case study: adding POST /api/relay/run to runtime/container_app.py (Menter chunk, 2026-08-22).
All completion criteria were verified with raw evidence, not self-report.

## Pre-flight checks before touching code

- The chunk may ALREADY be applied in the working tree (a prior attempt or concurrent chunk). read_file the target first; if the edits exist, verify them instead of rewriting.
- Deps for import integrity: the worker python needs `flask` (container_app + api/relay) and `httpx` (pipeline_relay lazy import). `pip3 install flask httpx` if missing.
- Gateways live at 127.0.0.1:8643-8648; check with `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8644/health`. If they are UP, verification POSTs will drive real pipeline phases.

## Live side effects (the big one)

A test POST does TWO real things: INSERTs a workflow_runs row AND spawns a daemon thread running asyncio.run(relay.resume(run_id)) against live gateways — real API tokens. Rules:
- Use a trivial smoke intent ("reply with the single word OK, use no tools").
- Keep poll windows short (~75s max); advancement (status != BRAIN_PHASE, rounds_completed > 0, or background.active flipping false) is enough evidence — do not wait for a full pipeline run.
- When the test process exits, daemon threads die, leaving mid-flight runs. That is the documented /start lifecycle (recoverable via relay.resume) — do not try to delete rows or mark them terminal; leave them and report honestly.

## Auth testing trap

`api.relay._check_auth` reads `API_KEY = os.environ.get("CIS_PIPELINE_API_KEY")` at MODULE IMPORT time. Testing the 401/200 matrix therefore requires a fresh subprocess with the env var exported BEFORE python starts:
`CIS_PIPELINE_API_KEY=testkey python3 -c "from container_app import app; ..."`
In-process os.environ changes after import do nothing.

## Schema drift: verify spec claims against the live DB

The spec claimed workflow_runs.created_by exists. Live schema (PRAGMA table_info) has NO such column. Real columns:
id, topic, result, requires_eric_review, max_rounds, max_consecutive_revisions, rounds_completed,
final_objections_json, created_at, completed_at, status, route, updated_at, eric_approved_at,
intent, directive_hash, project_id, parent_run_id.
Always run PRAGMA table_info before writing evidence SQL — spec claims are claims, not reality.

## Endpoint behavior facts (verified)

- GET /api/relay/<run_id> response: top-level status/rounds_completed plus "background": {"active": bool, "error": ...}. active = run_id in _active_runs AND "finished_at" not in entry. There is NO top-level finished_at.
- GET /api/relay/run resolves through the blueprint dynamic rule to 404 {"error": "Run not found", "run_id": "run"} — a documented GET-only overlap, never a 405.
- POST /api/relay/start with empty body returns 400 {"error": "intent required"} — a cheap, run-free regression probe that proves the guarded path is alive without creating a run or triggering pre-flight.
- run_id format: run-<sha256(intent)[:16]>-<unix_ts>; regex ^run-[0-9a-f]{16}-[0-9]{10}$.

## Shared working tree discipline

Other chunks edit the same repo (and even the same file) concurrently. Before submitting:
- `git diff -- <file> | grep '^@@'` and confirm your hunks are exactly your spec's edits.
- Never revert someone else's hunks that share the file; report them in the FINAL_JSON summary.
- Delta discipline for CIS chunks: the one modified file only, no new files in the repo, no migrations; temp verification scripts live in /tmp and get deleted.
