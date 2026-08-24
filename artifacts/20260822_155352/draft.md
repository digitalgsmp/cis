Review complete. I verified every claim in the spec against the actual codebase (pipeline_run.py, container_app.py, api/relay.py, abstraction/dispatch.py, abstraction/pipeline_relay.py, SPEC_PRODUCTION_PIPELINE_RELAY.md) and the house spec conventions.

Overall verdict: solid, well-formed spec. It follows the house format exactly (header block, numbered sections, error matrix, JSON examples, open questions), and the core contract is implementable. But there are three issues that should be fixed before review, and a handful of completeness gaps.

BLOCKING / MUST FIX

1. "Reuse pipeline_run.py call()" is not directly implementable. pipeline_run.py has no __main__ guard — main() executes at module level on line 47 — so importing it from container_app.py would run main() and crash with IndexError on sys.argv[1]. The spec says "reuse it, do not invent a new one" but gives no mechanism. Pick one and state it: (a) copy the ~10-line call() pattern into container_app.py (contradicts "reuse", but is the zero-risk option), or (b) refactor pipeline_run.py to extract call() into a shared module and add a __main__ guard (touches the CLI the spec says stays as-is). As written, an implementer following the spec literally hits a crash.

2. Timeout default of 1800s is inconsistent with the pipeline's own draft timeout. pipeline_relay.py sets AGENT_TIMEOUTS["draft"] = 300s (line 42), and the authority spec §6.3 says 180s per agent call. 1800 comes from pipeline_run.py, which is the declared pattern authority, so it's defensible — but the spec should explicitly acknowledge the divergence from the pipeline's 300s draft timeout and justify why a bare draft gets 6x more time than a draft inside a run. Also, 30 minutes of synchronous blocking means one worker thread pinned per request; if this ever runs under gunicorn with N sync workers, N slow drafts exhaust the server. The v2 note covers this partially, but the timeout choice itself deserves a sentence.

3. The endpoint silently bypasses the mandatory pre-discovery rule. Authority spec §3.0 says "Before ANY agent is dispatched" a mandatory discovery query runs. /run sends the raw prompt straight to the Draft gateway with zero discovery. That may be a fine design choice for a raw single-shot path, but the spec should state the deviation explicitly and justify it, not leave it implicit — reviewers in this codebase will flag it.

COMPLETENESS GAPS

4. No pre-flight check. /api/relay/start runs enforcement/mwl-proof-v2/pre_flight_check.py and returns 403 on critical violations before spending tokens. /run has no mention of it. The gateway-side mwl-proof plugin still applies at Layer 3, so enforcement isn't fully bypassed, but the spec should state explicitly whether pre-flight applies to /run (recommendation: yes, same 403 semantics — it's cheap and prevents token burn on blocked intents).

5. run_id format coupling risk. Generated "run-<hash16>" matches the prefix convention, but real workflow_runs ids are "run-<hash16>-<unix_ts>" (pipeline_relay.py line 346). Fine for v1 since /run writes no DB rows, but if Open Question 1 flips to "yes, write to workflow_runs", hash-only ids will be swept up by relay_start's idempotency query (WHERE id LIKE 'run-<hash>%' AND status NOT IN terminal...). Note this coupling in the open questions now.

6. Misleading GET. GET /api/relay/run will match the blueprint's GET /api/relay/<run_id> with run_id="run" and return 404 "Run not found" — confusing for anyone who typos the method. Also note GET /api/relay/runs (plural) already exists in relay.py, so the two names are close enough to cause typos. Suggest documenting this or adding an explicit 405.

7. No max_tokens. pipeline_relay.py caps draft calls at max_tokens 8192 (line 1380); pipeline_run.py doesn't set it. The spec follows pipeline_run.py, which is fine, but output size is then whatever the gateway defaults to — one line in §5 noting the cap is intentionally absent (or adding it) prevents truncation surprises.

8. Hard-coded /workspace/cis path. pipeline_run.py hard-codes it, but the codebase convention is CIS_PROJECT_ROOT env with fallback (pipeline_relay.py line 34, api/relay.py line 186), and ADR-SEED-010 is multi-project filesystem isolation. Use os.environ.get("CIS_PROJECT_ROOT", "/workspace/cis") + "/artifacts".

9. 502 vs 500 for malformed gateway responses. The matrix maps "unexpected exception" to 500, but a gateway returning 200 with invalid JSON or missing choices is arguably a 502 (gateway misbehaving). Define it so the acceptance tests can assert deterministically.

10. Observability. With no spine writes, the only record of a /run is the file. One log line (run_id, duration, bytes) to /tmp/cis-logs/pipeline_api.log would make failures debuggable — worth a bullet in §7.

VERIFIED CORRECT

- Authority chain holds: §6.4 exists in SPEC_PRODUCTION_PIPELINE_RELAY.md and covers the API family and auth. One nuance: §6.4 specifies /api/pipeline/* paths while the implementation drifted to /api/relay/* (api/relay.py cites §6.4 anyway). The new endpoint correctly follows the implemented convention, but a one-line acknowledgment of the path drift keeps the authority chain honest.
- Gateway pattern matches pipeline_run.py call() exactly: URL, Bearer CIS_DRAFT_API_KEY, body shape, choices[0].message.content extraction, 1800s timeout.
- dispatch.py PROFILES["draft"]["port"] = 8645 and the DEV-PIVOT-05 §5 single-source-of-truth claim check out. Physical path is runtime/abstraction/dispatch.py, importable as abstraction.dispatch from container_app.py — the spec's wording is fine.
- _GATEWAY_PORTS["Draft"] = (8645, "deepseek-v4-pro") exists in container_app.py for the fallback.
- CIS_DRAFT_API_KEY is the right env var (also matches pipeline_relay's CIS_{ROLE}_API_KEY convention, line 1299-1305).
- _check_auth exists with the exact 401 shape and disabled-when-unset rule.
- No existing POST /api/relay/run route anywhere; no Flask route conflict with the blueprint's GET /api/relay/<run_id> (static beats dynamic, methods differ).
- The run_id regex is the right path-traversal guard — matches the known pitfall for client-supplied path components.
- Error matrix and response contract are consistent with codebase practices.

Bottom line: fix items 1-3 before sending to review (1 and 3 are the ones a reviewer will definitely catch), fold 4-10 in as they're cheap. The structure, format, and verification section are already at the standard this codebase expects.