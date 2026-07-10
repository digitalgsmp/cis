# Session Handoff — 2026-07-10

## What Was Done

### Spec Work
- **docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md** — Added Part 6: Self-Evolving Harness Strategy. Covers adaptive threshold tuning, gate_outcomes table schema, three-phase build order (static → feedback → adaptive), RSI connection, no-LLM-in-tuning-loop constraint.
- **docs/SPEC_CONTROL_PLANE_BUILD.md** — Full 14-component build spec for Menter. Verified codebase facts, reviewer objections incorporated, correct migration numbers, `_db_connect` bug documented.

### 14-Component Build (All Complete)

**Phase A — Foundation:**
- A1: Fixed `_db_connect()` bug in `pipeline_relay.py` — now accepts `db_path` parameter. `PipelineRelay.__init__` uses `self.db_path`.
- A2: Fixed `workflow_run_id` → `run_id` bug in `mcp_bridge/spine.py` (workflow_run_artifacts query). Added 3 relay endpoints: `GET /api/relay/runs`, `GET /api/relay/kb/search`, `GET /api/relay/kb/decisions`.
- A3: Migration 0021 (`corpus_entries` + FTS5). `tools/extract_corpus.py` created and run — 213 entries extracted (165 agent_trajectories, 31 deliberation_rounds, 17 session_closeouts).
- A4: Migration 0022 (`projects` table + `workflow_runs.project_id`). Multi-project routing in `relay.py` — `POST /api/relay/start` accepts `project` field. Added `GET/POST /api/projects`.

**Phase B — Interface & Bootstrap:**
- B1: `RelayPage.jsx` — split-pane UI: intent form, live run view (2s polling), phase progress bar, deliberation rounds viewer (expandable), run history. 9 relay methods added to `api.js`, route + nav item in `App.jsx`.
- B2: Eric Gate panel in RelayPage — mobile-responsive (stacks <768px), 3 buttons (Approve/Reject/Refine), rationale textarea, shows Brain/Reviewer1/Reviewer2 outputs.
- B3: `runtime/config/role_overlays.yaml` — 6 role overlays with bias resistance. `_build_soul_document()` in `pipeline_relay.py` — injects ROLE_OVERLAY, BIAS_OVERLAY, KB_CONTEXT, RECENT_RUNS, PROJECT_BRIEF, ERICS_WORKING_METHODS. 8000 char budget. Verified: 4060 chars, all sections populated.
- B4: SWA project at `/mnt/projects/swa/` — git repo, spine DB (migrations applied), AGENTS.md. Registered in CIS projects table.

**Phase C — Pipeline Hardening:**
- C1: Migration 0023 (`workflow_runs.parent_run_id` + `run_dependencies`). Added `POST /api/relay/<run_id>/decompose` and `GET /api/relay/<run_id>/children`.
- C2: Git workflow methods in `PipelineRelay`: `_git_create_branch()`, `_git_commit()`, `_git_rollback()`, `_git_pr_command()`.
- C3: Extended `_run_automated_checks()`: actual pytest execution, directive scope verification (checks claimed files exist).
- C4: Migration 0024 (`dead_letter_queue`). Retry logic in `_call_agent()` — retries once on transient failure. DLQ insertion on ESCALATED/ERROR. `_notify_eric_gate()` — Telegram notification when run reaches Eric Gate.

**Phase D — Production Readiness:**
- D1: Migration 0025 (`agent_trajectories.tokens_in/out`). Added `GET /api/relay/metrics`, `GET /api/relay/<run_id>/errors`, `GET /api/relay/dlq`.
- D2: `docs/REMOTE_ACCESS_SETUP.md` — Tailscale, nginx, SSH tunnel options.
- D3: `spine_schema.sql` synced from live DB (166 → 1075 lines). Soul document already includes RECENT_RUNS.

### Pipeline Run
- Run `run-12d5aa6946666b73-1783649571` was approved at Eric Gate, progressed to CODE_REVIEW_GATE, Menter produced output, then ESCALATED. Run closed as ESCALATE.

### Docker Image
- No rebuild needed. The CIS repo is mounted as a volume (`/mnt/projects/cis` → `/workspace/cis` read-write). All Python code changes are live in the container without rebuilding. pyyaml was already in the Dockerfile.
- If a rebuild IS needed (e.g., new dependencies or gate scripts): `sg docker -c "docker build -t cis-hermes:pipeline -f /mnt/projects/cis/enforcement/mwl-proof-v2/Dockerfile /mnt/projects/cis/enforcement/mwl-proof-v2/"` (requires sudo/docker group access).

---

## What's NOT Done Yet

### 1. Deterministic Guardrails (docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md)
The spec documents 24 failure modes and 34 guardrail designs. **Zero are wired into the pipeline.** The pipeline still relies 100% on LLM judgment for quality. Tier 1 guardrails (items 1-10) are the next priority:
- Claim-Action Verifier — `os.path.exists`, `grep`, `git diff` after each phase
- Unverified Claim Propagator Block — tag unverified claims in downstream prompts
- Code Quality Pre-Check — `py_compile`, grep for TODO/pass/hardcoded
- Sycophancy Detector — keyword + string similarity on reviewer outputs
- Scope Compliance Checker — noun phrase overlap between intent and output
- Output Schema Validator — hard FAIL on unparseable FINAL_JSON
- Content Specificity Check — keyword matching against project terms
- Honesty Reporter — PASS/SKIP/FAIL counters in all gate scripts
- Path Contract Validator — `os.path` checks before writes
- Tool Result Sandboxing — string wrapping of tool results in prompts

### 2. Self-Evolving Harness (Part 6 of the spec)
- `gate_outcomes` table not created yet
- No threshold tuning logic
- No feedback loop from pipeline outcomes to guardrail thresholds
- Build order: Phase A (static gates) → Phase B (feedback analysis after 20-30 runs) → Phase C (adaptive thresholds)

### 3. Git Commit
- None of today's work has been committed. All changes are on disk but unstaged.

### 4. Container Verification
- The container needs to be restarted (or verified) to pick up the new endpoints and soul injection. The volume mount means the code is there, but the Flask process inside the container may need a restart.

---

## Files Created (10)
- `runtime/schema/migrations/0021_corpus_entries.sql`
- `runtime/schema/migrations/0022_projects_table.sql`
- `runtime/schema/migrations/0023_run_decomposition.sql`
- `runtime/schema/migrations/0024_dead_letter_queue.sql`
- `runtime/schema/migrations/0025_agent_token_tracking.sql`
- `runtime/ui/src/pages/RelayPage.jsx`
- `runtime/config/role_overlays.yaml`
- `tools/extract_corpus.py`
- `docs/REMOTE_ACCESS_SETUP.md`
- `/mnt/projects/swa/` (full project tree: repo, spine DB, AGENTS.md)

## Files Modified (6)
- `runtime/abstraction/pipeline_relay.py` — 8 patches
- `runtime/api/relay.py` — 7 patches
- `runtime/mcp_bridge/spine.py` — 1 bug fix
- `runtime/ui/src/api.js` — 9 relay methods
- `runtime/ui/src/App.jsx` — import, route, nav item
- `runtime/schema/spine_schema.sql` — synced from live DB

## Migrations Applied (5)
0021, 0022, 0023, 0024, 0025 — all applied to CIS spine. 0021 and 0022 also applied to SWA spine.

---

## Next Session Entry Points

1. **Git commit** — `cd /mnt/projects/cis && git add -A && git commit -m "14-component control plane build"`
2. **Wire Tier 1 guardrails** — Start with Claim-Action Verifier (§1.2) and Sycophancy Detector (§2.2) from `docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md`
3. **Create gate_outcomes table** — Part 6.3 of the spec has the schema
4. **Restart container** — `cd /mnt/projects/cis/enforcement/mwl-proof-v2 && ./run_container.sh stop && ./run_container.sh -d` to pick up new endpoints
5. **Test the UI** — Navigate to `http://localhost:5000/relay` in a browser
