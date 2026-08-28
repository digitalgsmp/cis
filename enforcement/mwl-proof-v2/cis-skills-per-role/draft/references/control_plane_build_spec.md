# Control Plane Build Spec Reference

## Source
- **Spec document**: `docs/SPEC_CONTROL_PLANE_BUILD.md` in the CIS repo
- **Pipeline run**: `run-12d5aa6946666b73-1783649571` (6 rounds: Brain → Intent Review → Draft → Review (OBJECTIONS) → Revised Draft → Review (CONSENSUS))
- **Author**: GLM Verifier (z-ai/glm-5.2)
- **Date**: 2026-07-10
- **Pattern**: Verifier-as-Spec-Author (see SKILL.md §"Verifier-as-Spec-Author Workflow")

## What This Spec Covers

14-component build plan for CIS Control Plane and SWA Development Infrastructure:

1. **Control Plane UI** — React pages wrapping relay API (RelayPage, run history)
2. **KB Runtime Access** — Fix cis_get_run_detail bug + add KB search relay endpoints
3. **Corpus Extraction Pass 1** — Extract Eric's verbatim words from spine tables + archive
4. **Multi-Project Support** — Projects table, per-project spine DB, fix _db_connect bug
5. **SWA Project Bootstrap** — Initialize SWA repo, spine, AGENTS.md
6. **Agent Soul/Briefing Injection** — Structured briefing document at dispatch time
7. **Eric Gate as Real Interface** — Mobile-responsive gate UI (rides on Component 1)
8. **Iterative Development** — Task decomposition + child runs (DELTA over existing REVISE loop)
9. **Git Workflow** — Branch per run, auto-commit, rollback on verify fail
10. **Verification Depth** — pytest execution, regression detection, directive scope verification
11. **Error Recovery** — Auto-retry, dead letter queue (DELTA over existing circuit breaker)
12. **Monitoring and Observability** — Metrics endpoint, token tracking, SSE
13. **Remote Access** — Session auth, HTTPS, Tailscale docs
14. **Persistent State and Handoff** — Sync spine_schema.sql, recent run summaries in pre-discovery

## Key Codebase Facts (Verified 2026-07-10)

- `relay.py`: 540 lines, 7 routes (health was missed by pipeline draft — spec corrects to 7)
- `pipeline_relay.py`: 2,447 lines at `runtime/abstraction/pipeline_relay.py`
- 22 migration files, next available: 0021 (last: `0020_deliberation_rounds_signal_check.sql`)
- `deliberation_rounds` has ALL output columns (reviewer1_output, reviewer2_output, brain_output, verify_output, menter_output) — OQ-SEED-006 RESOLVED
- `goal_references` table EXISTS in live DB — eric_gate_approvals FK is valid
- `agent_trajectories` does NOT have tokens_in/tokens_out (Component 12 adds them)
- 19 UI pages in `runtime/ui/src/pages/` including PipelinePage.jsx, EricGatePage.jsx
- 5 MCP bridge files: server.py, tools.py, spine.py, chroma_index.py, __init__.py

## Critical Bug Found During Verification

`PipelineRelay.__init__(self, db_path=DB_PATH)` stores `self.db_path` at line 1346, but:
```python
self.conn = _db_connect()  # line 1347 — calls module-level _db_connect()
```
`_db_connect()` at line 177 uses module-level `DB_PATH`, not `self.db_path`:
```python
def _db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)  # module-level DB_PATH
```
Result: `PipelineRelay(db_path='/mnt/projects/swa/data/cis_memory.db')` still connects to CIS DB.
Fix: `def _db_connect(db_path=DB_PATH): return sqlite3.connect(db_path, timeout=10)` + `self.conn = _db_connect(self.db_path)`

## Reviewer Issues Incorporated

### Reviewer 1 (Round 4 — OBJECTIONS, 3 critical):
1. Components 2, 8, 11 propose building features that ALREADY EXIST (_pre_discovery, MAX_DRAFT_ROUNDS, REVISE→DRAFT_PHASE)
2. Wrong migration numbering (proposed 0011, actual 0015/0016/0020 already exist)
3. Scope inflated ~800-1000 lines of duplicate work

### Reviewer 2 (Round 6 — CONSENSUS with 8 concerns):
1. Multi-project DB switching underspecified (module-level connection)
2. Concurrent multi-project race condition
3. SWA corpus keyword tagging is fragile
4. Soul injection prompt length budget missing
5. Component 7 mobile CSS is not free
6. Playwright availability in container unconfirmed
7. eric_gate_approvals FK fix should pick one approach
8. Build order should swap A3/A4 (projects table before corpus tagging)

## Migrations Required
- 0021: corpus_entries + FTS5
- 0022: projects table + workflow_runs.project_id
- 0023: workflow_runs.parent_run_id + run_dependencies
- 0024: dead_letter_queue
- 0025: agent_trajectories.tokens_in/tokens_out

## Build Phases
- **Phase A**: Foundation (bug fix → KB access → corpus extraction → multi-project)
- **Phase B**: Interface & Bootstrap (UI → Eric Gate UI → soul injection → SWA bootstrap)
- **Phase C**: Pipeline Hardening (iterative dev → git workflow → verification depth → error recovery)
- **Phase D**: Production Readiness (monitoring → remote access → persistent state)
