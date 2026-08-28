# CIS Spec Authoring + Relay API Reference

Condensed from a session writing SPEC_RELAY_RUN_ENDPOINT.md (2026-08-22). Use this
when asked to write a spec for any CIS runtime change, or when touching the relay API.

## House spec format (docs/SPEC_*.md)

Header block after the H1 title:

```
**Date:** YYYY-MM-DD
**Status:** DRAFT (pre-review) | REV-N (post dual-review)
**Authority:** <existing spec or doc that grounds this one>
**Supersedes:** <what this replaces>
```

Body: numbered sections separated by `---`. Standard sections seen in
SPEC_PRODUCTION_PIPELINE_RELAY.md: What This Is → Motivation → Request/Response
contracts (markdown tables) → Layer details → Implementation Notes → Verification
(acceptance tests) → Open Questions (explicitly for reviewers).

Conventions that reviewers expect:
- Error matrix as a table (status | condition | body).
- JSON request/response examples inline.
- Open Questions section at the end — decisions deliberately deferred.

## Relay API family (where endpoints live)

- runtime/container_app.py — minimal Flask app, registers ONLY relay_bp. Houses
  /api/relay/system/* handlers, /api/health, UI fallback routes. New lightweight
  relay endpoints can go here as plain @app.route handlers.
- runtime/api/relay.py — production relay API (POST /api/relay/start,
  GET /api/relay/<run_id>, /answer, /gate, /verify, /trace). Auth via
  _check_auth(): Bearer CIS_PIPELINE_API_KEY; auth disabled when key unset.
  Idempotency: same intent within 1h returns existing non-terminal run.
- Runtime of /start spawns PipelineRelay.resume() in a background daemon thread
  (_run_pipeline_background), keyed in _active_runs dict.

## Drafter pipeline output contract (live DRAFT phase — distinct from persisted SPEC_*.md)

The Drafter gateway returns a plain-text proposal (assume no markdown rendering:
numbered sections, indented code, no asterisks/headers/code fences). It MUST end
with FINAL_JSON — the parser keys off it:

```json
{"role":"draft","status":"PROPOSAL_READY","summary":"one-line delta summary"}
```

Section order that has passed review:
1. Intent Confirmation — restate Eric's intent, one paragraph.
2. What Exists (verified, not assumed) — cite file + line number for every claimed primitive; run the searches yourself before writing.
3. Design Decision (flagged explicitly) — state lean-vs-parity choice when the requested capability overlaps existing code.
4. File Changes (exact) — exact insertion points, anchor line numbers, full code.
5. API Contract — request/response bodies and error matrix.
6. Non-Goals — what was deliberately NOT built.
7. Fallback — the one-line alternative if reviewers demand parity (document it, don't build it).
8. Verification — raw-evidence commands (import check, flask test_client, sqlite SELECT), never self-report.
9. Risks.

Lean-vs-parity pattern: when Eric asks for an endpoint that duplicates existing
capability at a new path/file (e.g. POST /api/relay/run in container_app.py vs
POST /api/relay/start in api/relay.py), do NOT copy the full machinery
(pre-flight, idempotency, project lookup). Either keep the new route lean —
auth + start primitive + background thread, importing api.relay's helpers
(_check_auth, _run_pipeline_background, _active_runs) rather than redefining —
with each omission explicitly flagged, or delegate the whole handler body to the
existing view function: `from api.relay import relay_start; return relay_start()`
works fine inside the same Flask request context. Never duplicate logic across
two start paths.

Verified primitives (line numbers drift; shapes are stable):
- api/relay.py: relay_start:167, _check_auth:43 (returns None = auth disabled when CIS_PIPELINE_API_KEY unset), _run_pipeline_background:110 (asyncio.run(relay.resume(run_id)) in daemon thread), _active_runs:107 (read by status + runs-list for the "active" flag — register new runs in it or they look inactive).
- abstraction/pipeline_relay.py: start_sync:2095 (creates row + sets BRAIN_PHASE, returns run_id, no async processing), _create_run:341 (NO dedupe — idempotency lives only in the /start handler), run_id = run-<sha256(intent)[:16]>-<unix_ts>:346. PipelineRelay(db_path=...) and relay.close() exist.
- container_app.py: imports jsonify but NOT request — add `request` to the flask import line when adding JSON routes. RUNTIME_DIR:19 is already on sys.path; the abstraction/ subdir must be added lazily inside the handler (matches api/relay.py's lazy pipeline_relay import; keeps the minimal app light at startup).

Route-collision check: an app-level POST /api/relay/run coexists with the
blueprint GET /api/relay/<run_id> rule; GET /api/relay/run resolves through the
dynamic rule → 404 "Run not found", not 405. Flask merges blueprint + app rules
into one url_map, so importing api.relay helpers from container_app.py reuses
the same module object (no double-import risk).

## Proven draft-gateway call pattern (pipeline_run.py)

Canonical single-shot call — reuse, don't reinvent:

```
POST http://127.0.0.1:8645/v1/chat/completions
Authorization: Bearer <CIS_DRAFT_API_KEY>
{"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": prompt}]}
```

Extract response: body["choices"][0]["message"]["content"] (OpenAI-compatible).
Artifact write pattern: /workspace/cis/artifacts/<run_id>/draft.md via
pathlib mkdir(parents=True, exist_ok=True) + write_text.

## Port map

- Canonical: abstraction/dispatch.py PROFILES dict (brain 8644, draft 8645,
  review1 8643, review2 8647, menter 8646, verify 8648) + ROLE_ALIASES.
- container_app.py duplicates this as _GATEWAY_PORTS (with model names).
- dispatch.py is the declared single source of truth (DEV-PIVOT-05 §5).

## Pitfalls

1. cis_search_knowledge FTS5 chokes on "." in queries ("fts5: syntax error near
   ".""). Queries like "draft.md" or "port 8645 artifacts" fail. Strip periods
   or use quoted phrases; retry with simplified terms.
2. Any client-supplied run_id/token that lands in a filesystem path is a
   path-traversal vector — enforce ^[A-Za-z0-9_-]{1,64}$ before building the path.
3. cis_adapter_dispatch can 404 when the abstraction layer is down; fall back to
   writing the spec directly and note the routing failure in the report.
4. Prior-trajectory summaries in the pipeline context are NOT ground truth. One
   trajectory claimed a GET /api/relay/system/stats route in container_app.py
   that is absent from the current tree (reverted or never landed). Always
   re-verify "what exists" against the live tree before writing the spec.
5. search_files content patterns are grep regexes — unescaped braces fail
   ("grep: Unmatched {", e.g. pattern run-\{). Search for the literal anchor
   without the brace (def start_sync, "run-") or escape it.
