# CIS Pipeline Build — Session Handoff

**Last updated:** 2026-07-08  
**Branch:** main  
**Latest commit:** `ffd3c1c` — self-evolution bridge

---

## What's Built

A multi-agent deliberation pipeline (CIS Pipeline Relay) that routes work through:

```
Brain → Intent Review → Draft (multi-round) → Proposal Review → Eric Gate →
Pattern Catalog → Code Review Gate (3-pass sequential) → Menter (chunked) → Verify
```

### Key properties
- **No default-to-success** — rounds start PENDING, Verify escalates on no verdict, all phases validate FINAL_JSON
- **3-pass sequential code review** — Reviewer A (less competent) → Reviewer B (more competent, sees A) → A consensus (sees B, delivers one voice to Menter)
- **Self-evolution** — every round's narrative auto-ingested into `knowledge_messages` → FTS5 auto-indexes → next run's pre-discovery searches it
- **Circuit breaker** — persisted to DB, trips after 3 consecutive broken agent responses
- **Health check** — validates JSON structure + content, catches zombie processes (port open but empty response)
- **Isolated verification** — `git worktree`-based isolation, Menter's diff applied to clean pre-Menter HEAD
- **Pattern catalog** — Brain reads codebase, generates per-project pattern catalog, reviewers validate it

## Files

| File | Purpose |
|------|---------|
| `runtime/abstraction/pipeline_relay.py` | Main state machine (~2,100 lines) |
| `runtime/api/relay.py` | Flask API endpoints (6 routes) |
| `runtime/app.py` | Flask app, registers relay blueprint |
| `docs/SPEC_CODE_REVIEW_GATE.md` | Code Review Gate spec (REV-2) |
| `docs/SPEC_PRODUCTION_PIPELINE_RELAY.md` | Pipeline spec (REV-2) |
| `data/cis_memory.db` | SQLite spine (migrations through 0020) |

## Commits This Session

```
ffd3c1c — self-evolution bridge (pipeline → knowledge_messages → FTS5)
b11af59 — end-to-end test verified (full 10-round pass)
44cfd1c — FINAL_JSON parser fix + migrations 0019/0020
e44268f — Code Review Gate implementation
7682ad1 — Code Review Gate spec REV-2
1ad844d — 10 bug fixes (default-to-success elimination)
6c2207d — 4 data integrity bugs fixed
b888d5f — API + query fixes, first full end-to-end pass
a6f88a1 — Flask API endpoints + gateway auth fix
```

## Gateways

| Role | Port | Model | Profile |
|------|------|-------|---------|
| Brain | 8644 | deepseek-v4-pro | hermes-brainstorm |
| Draft | 8645 | deepseek-v4-pro | hermes-v4pro |
| Review1 | 8643 | qwen3.7-max | hermes-r1 |
| Review2 | 8647 | glm-5.2 | hermes-glm-reviewer |
| Menter | 8646 | deepseek-v4-pro | hermes-v4impl |
| Verify | 8648 | glm-5.2 | hermes-glm-verifier |

API keys are auto-discovered from each gateway's `.env` file (`API_SERVER_KEY`).

## What's Done

- ✅ Full pipeline state machine (all phases)
- ✅ Flask API (start, status, gate, trace, resume, health)
- ✅ Eric Gate (human approval via API)
- ✅ Code Review Gate (3-pass sequential, pattern catalog)
- ✅ Isolated verification (git worktree)
- ✅ Circuit breaker (persisted to DB)
- ✅ Health check (content validation, not just port)
- ✅ Self-evolution bridge (pipeline → knowledge_messages → FTS5)
- ✅ End-to-end test passed (10 rounds, full pipeline)

## What's Next

1. **✅ Test self-evolution** — DONE (2026-07-09). Run `run-e4aac6f86dc70fd4` confirmed: 22 KB entries ingested across 6 phases, FTS5 search finds pipeline narratives, pre-discovery returns them. Self-evolution bridge verified end-to-end.
2. **✅ Code review retry fix** — DONE (commit `8e620ec`). Added `_call_agent_with_retry` helper: retries once with 2s backoff before escalating. Fixes empty `str(e)` with `repr(e)` fallback. Root cause: Reviewer B threw empty exception on revision 3, escalating the run.
3. **Container transition** — move pipeline into Docker containers (production target). Host is dev only.
4. **Systemd fix** — add `KillMode=control-group` to service files to prevent stale processes
5. **UI** — display pipeline runs, trajectories, code review results in the CIS UI

## How to Resume After Reset

1. **Read this file:** `docs/HANDOFF_PIPELINE_BUILD.md`
2. **Check git log:** `git log --oneline -10`
3. **Check DB state:** `sqlite3 data/cis_memory.db "SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 5;"`
4. **Start a pipeline run:**
   ```bash
   cd /mnt/projects/cis
   python3.12 -c "
   from runtime.abstraction.pipeline_relay import PipelineRelay
   r = PipelineRelay()
   r.start_sync('Your task description here')
   "
   ```
5. **Check status:** `curl localhost:5000/api/relay/status/<run_id>`

## Known Blockers

- **DeepSeek API balance** — Brain/Draft/Menter depend on it. HTTP 402 if depleted.
- **Systemd stale processes** — `systemctl restart` doesn't always kill children. Workaround: manually kill PID on the port before restart.
- **~~Self-evolution untested end-to-end~~** — RESOLVED 2026-07-09. Verified working: 22 KB entries, FTS5 indexed, pre-discovery returns results.
