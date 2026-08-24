pipeline_run.py has no `__main__` guard — `main()` executes at module level (line 47) — so the spec's "reuse `pipeline_run.py call()`, do not invent a new one" is not directly importable without either copying the pattern or refactoring the CLI.

Spec's 1800s timeout default diverges from `pipeline_relay.py` line 42 (`AGENT_TIMEOUTS["draft"] = 300s`) and authority spec §6.3 (180s per agent call) with no stated justification for the 6x multiplier.

Spec's `/run` endpoint sends the raw prompt straight to the Draft gateway with zero discovery, silently bypassing authority spec §3.0's mandatory pre-discovery rule ("Before ANY agent is dispatched") with no stated deviation.