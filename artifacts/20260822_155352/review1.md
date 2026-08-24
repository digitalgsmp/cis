Line 80: "reuse it, do not invent a new one" is not implementable — pipeline_run.py line 47 calls main() at module level with no __main__ guard, so importing it from container_app.py crashes with IndexError on sys.argv[1].

Line 47: timeout default 1800 contradicts pipeline_relay.py line 42 (AGENT_TIMEOUTS["draft"] = 300) and the authority spec §6.3 (180s per agent call) with no justification for the 6x divergence.

Lines 82-87: raw prompt sent directly to the Draft gateway — SPEC_PRODUCTION_PIPELINE_RELAY.md §3.0 lines 74-79 mandate pre-discovery before ANY agent dispatch; this endpoint silently bypasses that rule without acknowledging the deviation.

Line 106: hard-coded "/workspace/cis/artifacts" violates the codebase convention (pipeline_relay.py line 34, api/relay.py line 186 use CIS_PROJECT_ROOT env with fallback) and ADR-SEED-010 multi-project isolation.

Line 49: generated run_id format "run-<hash16>" diverges from pipeline_relay.py line 346 format "run-<hash16>-<unix_ts>"; if Open Question 1 resolves to writing workflow_runs, the hash-only ids collide with relay_start's idempotency query (api/relay.py line 229: WHERE id LIKE 'run-<hash>%').