# CIS Spec Review Checklist + Verified Codebase Facts

Use when asked to review a CIS spec (docs/SPEC_*.md) for correctness/completeness,
or before implementing one. Facts verified against the codebase 2026-08-22 —
re-verify before citing (the codebase moves fast).

## Review methodology — verify EVERY claim against code

1. Authority chain: does the cited spec section actually exist and say what is
   claimed? Known drift: SPEC_PRODUCTION_PIPELINE_RELAY.md §6.4 lists
   /api/pipeline/* paths, but the implementation moved to /api/relay/*
   (api/relay.py cites §6.4 anyway). New endpoints follow the implemented
   convention; flag the drift explicitly so the authority chain stays honest.
2. Every code reference: function names, env vars, constants, file paths, ports.
3. Route collisions: grep *.py for the new route; check static-vs-dynamic
   shadowing (e.g. GET /api/relay/run falls into GET /api/relay/<run_id> with
   run_id="run" → misleading 404 "Run not found"). Also check near-miss names
   (GET /api/relay/runs plural exists).
4. Cross-layer consistency: timeouts, run_id formats, idempotency prefixes,
   max_tokens caps, path conventions (CIS_PROJECT_ROOT vs hard-coded
   /workspace/cis). A new endpoint that picks values from one file but lives
   next to another often contradicts the pipeline's own numbers.
5. Mandatory architecture rules the endpoint might silently bypass — the spec
   must state and justify each deviation:
   - Pre-discovery (§3.0 of SPEC_PRODUCTION_PIPELINE_RELAY.md: "before ANY agent
     is dispatched"). Raw single-shot endpoints skip it by design.
   - Pre-flight check: /api/relay/start runs
     enforcement/mwl-proof-v2/pre_flight_check.py (403 on returncode 2, warns on
     1, clean on 0) BEFORE spending tokens. Decide whether new endpoints apply
     it too; gateway-side mwl-proof still applies at Layer 3 regardless.
6. Importability of "reuse X.py's function" claims: check for a __main__ guard.
   pipeline_run.py has NONE — main() runs at module level, so importing it
   crashes (IndexError on sys.argv[1]). Any spec saying "reuse call()" must
   choose: copy the pattern inline, or refactor + add a guard.
7. Error mapping determinism: 502 vs 500 for malformed gateway responses
   (200 with invalid JSON / missing choices) must be pinned so acceptance
   tests can assert exact behavior.

## Verified codebase facts

- pipeline_run.py: no __main__ guard (see above). call() hard-codes
  timeout=1800 and omits max_tokens. Writes /workspace/cis/artifacts/
  <run_id>/{draft,review1,review2}.md; run_id is a timestamp, not a hash.
- pipeline_relay.py gateway calls: httpx AsyncClient with per-role
  AGENT_TIMEOUTS = {verify: 600, menter: 600, brain: 300, draft: 300},
  default 180s; payload sets max_tokens=8192. API key resolution (~line 1297):
  1) CIS_{ROLE}_API_KEY env, 2) gateway .env API_SERVER_KEY,
  3) config.yaml api_server section. So CIS_DRAFT_API_KEY is the right name.
- workflow_runs id format: "run-" + sha256(intent)[:16] + "-" + unix_ts
  (pipeline_relay.py _create_run). api/relay.py idempotency matches
  id LIKE 'run-<hash16>%' AND status NOT IN (terminal...) — any other path
  generating hash-only ids can be swept up by that query if it later writes
  workflow_runs rows. Flag this coupling when specs defer DB writes to v2.
- dispatch.py PROFILES (runtime/abstraction/dispatch.py, importable as
  abstraction.dispatch when runtime/ is on sys.path): brain 8644, draft 8645,
  review1 8643, review2 8647, menter 8646, verify 8648. PROFILES has NO
  "model" field — models live in container_app.py _GATEWAY_PORTS as
  (port, model) tuples.
- api/relay.py: GET /api/relay/runs (plural) exists. _check_auth returns None
  when CIS_PIPELINE_API_KEY unset (auth disabled, not required). 401 body is
  {"error": "Unauthorized", "detail": "Invalid or missing API key"}.
- Multi-project convention (ADR-SEED-010): use
  os.environ.get("CIS_PROJECT_ROOT", "/workspace/cis") instead of hard-coded
  paths; per-project spine via the `project` field on /api/relay/start.

## Review output shape that landed well

Plain-text report: verdict up front, then BLOCKING issues (numbered, with
file:line evidence), then COMPLETENESS GAPS (suggestions with rationale), then
a VERIFIED CORRECT section confirming which spec claims check out. This mirrors
the dual-review (R1+R2) style of the pipeline itself.
