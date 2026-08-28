# Control Plane Build — Complete Evidence (2026-07-10)

All 14 components built directly by GLM Verifier. Phases A-D complete.
Phase A evidence: see [phase_a_build_evidence.md](phase_a_build_evidence.md).

## Phase B — Interface & Bootstrap

### B1: Control Plane UI
- **New file**: `runtime/ui/src/pages/RelayPage.jsx` (21.7KB)
  - Split-pane layout: left = intent form, right = live run view
  - Phase progress bar (11 phases, color-coded)
  - Deliberation rounds viewer (expandable, shows Brain/Draft/Reviewer1/Reviewer2/Menter outputs)
  - Run history page (polls `GET /api/relay/runs`)
  - Human question panel (inline answer input)
  - 2-second polling, stops on terminal states
- **Modified**: `runtime/ui/src/api.js` — 9 relay methods added (relayStart, relayStatus, relayGate, relayAnswer, relayVerify, relayTrace, relayListRuns, relayKbSearch, relayKbDecisions)
- **Modified**: `runtime/ui/src/App.jsx` — import, route (`/relay`), nav item ("Relay" in Monitor group)

### B2: Eric Gate UI (mobile-responsive)
- Embedded in RelayPage.jsx (not a separate file)
- Three action buttons: Approve (green), Reject (red), Refine (yellow)
- Mobile-responsive: full-width stacked buttons <768px, inline on desktop
- Rationale textarea (min 200px height on mobile)
- Shows Brain output, Reviewer1 output, Reviewer2 output (truncated to 2000 chars)

### B3: Agent Soul/Briefing Injection
- **New file**: `runtime/config/role_overlays.yaml` — 6 role overlays (brain, draft, review1, review2, menter, verify)
  - Each has `role` (identity) and `bias_overlay` (anti-enterprise-bias instructions)
- **Modified**: `runtime/abstraction/pipeline_relay.py` — added `_build_soul_document()` function (lines 558-665)
  - Structured sections: ROLE_OVERLAY > BIAS_OVERLAY > TASK > KB_CONTEXT > RECENT_RUNS > PROJECT_BRIEF > ERICS_WORKING_METHODS
  - 8000 char budget (truncates with priority order)
  - KB_CONTEXT: top 3 FTS5 hits for the topic
  - RECENT_RUNS: last 3 CONSENSUS_REACHED runs with topics
  - PROJECT_BRIEF: AGENTS.md content (truncated to 3000 chars)
- **Wiring**: `_pre_discovery()` return statement prepends soul document before pre-discovery results
- **Verified**: soul document for "brain" role = 4060 chars, all sections populated

### B4: SWA Project Bootstrap
- **New directory tree**: `/mnt/projects/swa/` with `data/`, `runtime/schema/migrations/`, `tools/gates/`, `docs/`
- **SWA spine**: `/mnt/projects/swa/data/cis_memory.db` — created from `spine_schema.sql` + migrations 0010, 0015, 0017, 0020, 0021, 0022
- **SWA AGENTS.md**: `/mnt/projects/swa/AGENTS.md` — bootstrap document with seed intent, architecture, verification rules
- **Git**: initialized, initial commit `dd367b8`
- **Registered**: in CIS `projects` table (id=swa, spine_path, agents_md_path)
- **Verified**: `sqlite3 /mnt/projects/swa/data/cis_memory.db ".tables"` — all tables present, 0 runs (fresh)

## Phase C — Pipeline Hardening

### C1: Task Decomposition
- **Migration 0023**: `workflow_runs.parent_run_id` + `run_dependencies` table
- **New endpoints in relay.py**:
  - `POST /api/relay/<run_id>/decompose` — creates child runs from subtask array, sets parent_run_id, tracks dependencies
  - `GET /api/relay/<run_id>/children` — lists child runs

### C2: Git Workflow
- **Added to `PipelineRelay` class** in `pipeline_relay.py`:
  - `_git(*args)` — subprocess wrapper, uses `self.db_path` to derive project root
  - `_git_create_branch(run_id)` — creates `cis/run-{run_id[:20]}` branch
  - `_git_commit(run_id, topic)` — `git add -A && git commit -m "run-{id}: {topic}"`
  - `_git_rollback(run_id)` — `git checkout -- . && git checkout master && git branch -D {branch}`
  - `_git_pr_command(run_id, topic)` — generates `gh pr create` command (does not auto-execute)

### C3: Verification Depth
- **Extended `_run_automated_checks()`** in `pipeline_relay.py`:
  - 7b: Actual `pytest` execution (was collection-only `--co`). Runs `pytest -x -q --tb=short`, 120s timeout
  - 7c: Directive scope verification — regex-extracts claimed file paths from agent output, checks `os.path.exists()` for each

### C4: Error Recovery
- **Migration 0024**: `dead_letter_queue` table (run_id, error_message, agent_role, phase, retry_count, status)
- **Retry logic** in `_call_agent()`: retries once on `httpx.ConnectError`/`httpx.TimeoutException` after 5s delay, before tripping circuit breaker
- **DLQ insertion**: `_set_run_status()` inserts into `dead_letter_queue` on ESCALATED/ERROR/VERIFY_FAILED
- **Eric Gate notification**: new `_notify_eric_gate()` function — sends Telegram message when run reaches ERIC_GATE status. Includes run ID, intent preview, and curl command for approval.
- **Verified**: all py_compile checks pass

## Phase D — Production Readiness

### D1: Monitoring and Observability
- **Migration 0025**: `agent_trajectories.tokens_in` + `tokens_out` columns
- **New endpoints in relay.py**:
  - `GET /api/relay/metrics` — total runs, runs by status, avg rounds, agent success rates, token totals, DLQ pending count
  - `GET /api/relay/<run_id>/errors` — error-level trajectories for a run
  - `GET /api/relay/dlq` — pending dead letter queue entries

### D2: Remote Access
- **New file**: `docs/REMOTE_ACCESS_SETUP.md` — 3 options documented:
  - Tailscale (recommended — `tailscale serve --bg 5000`)
  - Nginx reverse proxy + Let's Encrypt
  - SSH tunnel (quick, no setup)

### D3: Persistent State
- **Synced**: `runtime/schema/spine_schema.sql` — dumped from live DB (166 lines → 1075 lines). Backup saved as `spine_schema.sql.bak`.
- **RECENT_RUNS** capability: already implemented in B3's soul document builder — queries last 3 CONSENSUS_REACHED runs and includes topic summaries in agent prompts. This is the "what did we do last time?" capability.

## Summary

| Phase | Components | Files Created | Files Modified | Migrations |
|-------|-----------|----------------|-----------------|------------|
| A | 4 (bug fix, KB, corpus, multi-project) | 3 (migration, script) | 3 (pipeline_relay, relay, spine) | 0021, 0022 |
| B | 4 (UI, gate UI, soul, SWA) | 3 (RelayPage, overlays, SWA tree) | 3 (api.js, App.jsx, pipeline_relay) | — |
| C | 4 (decompose, git, verify, recovery) | 1 (migration 0024) | 2 (pipeline_relay, relay) | 0023, 0024 |
| D | 3 (monitoring, remote, state) | 2 (migration 0025, docs) | 2 (spine_schema, relay) | 0025 |
| **Total** | **14** | **10** | **5** | **5** |

All files compile. All migrations applied. All endpoints tested against live DB.
