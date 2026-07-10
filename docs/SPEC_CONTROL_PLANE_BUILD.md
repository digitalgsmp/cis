# CIS Control Plane and SWA Development Infrastructure
## Build Specification for Menter

**Status:** APPROVED by Eric — bypass pipeline, deliver directly to Menter
**Source:** Pipeline run `run-12d5aa6946666b73-1783649571` — 6 rounds (2 draft, 2 review, consensus reached)
**Verification:** GLM Verifier (this document) — codebase facts verified against live source
**Date:** 2026-07-10

---

## 0. Verified Codebase State

All facts below were verified by the GLM Verifier against live source files on 2026-07-10. Menter should treat these as ground truth, not re-derive them.

### Files
- `runtime/api/relay.py` — 540 lines, 7 routes: `/api/relay/health`, `/start`, `/<run_id>`, `/<run_id>/answer`, `/<run_id>/gate`, `/<run_id>/verify`, `/<run_id>/trace`
- `runtime/abstraction/pipeline_relay.py` — 2,447 lines. Contains `PipelineRelay` class, `_pre_discovery()`, `MAX_DRAFT_ROUNDS=3`, circuit breaker, `AGENT_TIMEOUTS`
- `runtime/mcp_bridge/` — 5 files: `server.py`, `tools.py`, `spine.py`, `chroma_index.py`, `__init__.py`
- `runtime/ui/src/pages/` — 19 JSX pages including `PipelinePage.jsx`, `EricGatePage.jsx`, `DashboardPage.jsx`
- `runtime/schema/spine_schema.sql` — 9 base tables (stale — does not reflect migrations 0011-0020)
- `runtime/schema/migrations/` — 22 migration files, latest: `0020_deliberation_rounds_signal_check.sql`

### Schema (Live DB — `/mnt/projects/cis/data/cis_memory.db`)
- `deliberation_rounds` has ALL output columns: `drafter_output`, `reviewer1_output`, `reviewer2_output`, `brain_output`, `verify_output`, `menter_output`, `human_question`, `human_answer`. OQ-SEED-006 is RESOLVED.
- `workflow_runs` has: `eric_approved_at`, `intent`, `directive_hash`, `status`, `route`
- `agent_trajectories` has FTS5 index, columns: `input_text`, `output_text`, `feedback_text`, `outcome`, `consensus_reached`, `config_version`, `marginal_utility`. Does NOT have `tokens_in`/`tokens_out`.
- `circuit_breaker_state` table exists and is persisted
- `goal_references` table EXISTS — the eric_gate_approvals FK is valid
- `eric_gate_approvals` table exists with `is_current` partial unique index

### Existing Mechanisms (DO NOT REBUILD)
- `_pre_discovery()` at line 471 — called 7 times before each agent dispatch. Does FTS5 search on `knowledge_messages_fts`, prior agent trajectories, and optional web search. Injects results into agent prompt. Component 2 extends this, does NOT replace it.
- `MAX_DRAFT_ROUNDS = 3` at line 49 — escalation to ESCALATED at lines 1712-1713. Component 11's consensus failure escalation ALREADY EXISTS.
- REVISE flow: `relay.py` line 440 handles `REVISE` decision, sets status to `DRAFT_PHASE`. The pipeline resumes with feedback. Component 8's iterative loop ALREADY EXISTS for the basic case.
- Circuit breaker: 3 failures → 5 min cooldown, persisted to `circuit_breaker_state` table
- `AGENT_TIMEOUTS` dict — per-role timeouts 180-600s
- Telegram notifications via `_notify_terminal_failure` on terminal failures
- 17 MCP bridge tools providing FTS5 + ChromaDB search

### Known Bug
- `PipelineRelay.__init__(self, db_path=DB_PATH)` stores `self.db_path` at line 1346, but `self.conn = _db_connect()` at line 1347 calls the module-level `_db_connect()` which uses module-level `DB_PATH` at line 177 — NOT `self.db_path`. This means multi-project DB switching is broken. The connection always points at the default DB regardless of what's passed to the constructor.

---

## 1. Component Specifications

### COMPONENT 1 — Control Plane UI

**Goal:** Browser-based interface wrapping the relay API. Replaces curl commands as Eric's primary interface.

**What exists:** 19 React pages. `PipelinePage.jsx` shows build plan status + run list. `EricGatePage.jsx` shows approvals. Neither talks to the relay API directly — they use the older app.py endpoints.

**What to build:**

New `RelayPage.jsx` — split-pane layout:
- Left: intent submission form (textarea + submit button → `POST /api/relay/start`)
- Right: live run view (polls `GET /api/relay/<run_id>` every 2 seconds)
- When status=`ERIC_GATE`: show three buttons (Approve, Reject, Refine) + rationale textarea → `POST /api/relay/<run_id>/gate`
- Show deliberation rounds (Brain output, Drafter proposal, Review1+Review2 outputs with signals) in expandable sections
- Mobile-responsive: stack vertically on viewport < 768px, gate panel buttons full-width

New `RunHistoryPage.jsx` — or extend `PipelinePage.jsx`:
- Query `GET /api/relay/runs?limit=50` for run list
- Click a run → expand to show trace via `GET /api/relay/<run_id>/trace`
- Search/filter by status

New API endpoint in `relay.py`:
```python
GET /api/relay/runs?limit=50
# Returns: [{id, topic, status, created_at, rounds_completed, result}]
# Query: SELECT id, topic, status, created_at, rounds_completed, result
#        FROM workflow_runs ORDER BY created_at DESC LIMIT ?
```

New methods in `ui/src/api.js`:
- `relayStart(intent)`, `relayStatus(runId)`, `relayGate(runId, decision, rationale)`, `relayAnswer(runId, answer)`, `relayVerify(runId)`, `relayTrace(runId)`, `relayListRuns(limit)`

Add route in `App.jsx` for `/relay` → `RelayPage`

**Files:**
- `runtime/ui/src/pages/RelayPage.jsx` (new)
- `runtime/ui/src/api.js` (modify — add relay methods)
- `runtime/ui/src/App.jsx` (modify — add route)
- `runtime/api/relay.py` (modify — add `GET /api/relay/runs`)

### COMPONENT 2 — Knowledge Base Runtime Access (DELTA only)

**Goal:** Fix the known bug and add a relay-accessible KB search endpoint.

**What exists:** `_pre_discovery()` already queries KB before dispatching agents. 17 MCP tools. FTS5 across 287K messages. ChromaDB with 3125 docs.

**Bug fix:** In `runtime/mcp_bridge/spine.py`, the `cis_get_run_detail` query references `workflow_run_id` but the `workflow_run_artifacts` table uses `run_id`. Fix the SQL query.

**New relay endpoints:**
```python
GET /api/relay/kb/search?q=<query>&top_k=10
# Proxies to cis_search_knowledge via MCP bridge
# Returns: [{content, source, score, timestamp}]

GET /api/relay/kb/decisions
# Returns open decisions from project_decisions table
# Query: SELECT label, decision, reason, status FROM project_decisions WHERE status='active'
```

**Files:**
- `runtime/mcp_bridge/spine.py` (modify — fix `workflow_run_id` → `run_id`)
- `runtime/api/relay.py` (modify — add 2 endpoints)

### COMPONENT 3 — Corpus Extraction Pass 1

**Goal:** Systematic extraction of Eric's verbatim words from all source roots, stored in spine with provenance.

**What to build:**

New migration `0021_corpus_entries.sql`:
```sql
CREATE TABLE IF NOT EXISTS corpus_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_root TEXT NOT NULL,      -- 'session_closeouts', 'agent_trajectories', 'deliberation_rounds', 'archive'
    source_file TEXT,
    line_number INTEGER,
    timestamp TEXT,
    content_text TEXT NOT NULL,
    project_tag TEXT DEFAULT 'CIS', -- CIS, SWA, WIAS
    extraction_pass INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE IF NOT EXISTS corpus_entries_fts USING fts5(
    content_text, source_root, project_tag,
    content='corpus_entries', content_rowid='id'
);
CREATE TRIGGER corpus_entries_ai AFTER INSERT ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(rowid, content_text, source_root, project_tag)
    VALUES (new.id, new.content_text, new.source_root, new.project_tag);
END;
CREATE TRIGGER corpus_entries_ad AFTER DELETE ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(corpus_entries_fts, rowid, content_text, source_root, project_tag)
    VALUES ('delete', old.id, old.content_text, old.source_root, old.project_tag);
END;
CREATE TRIGGER corpus_entries_au AFTER UPDATE ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(corpus_entries_fts, rowid, content_text, source_root, project_tag)
    VALUES ('delete', old.id, old.content_text, old.source_root, old.project_tag);
    INSERT INTO corpus_entries_fts(rowid, content_text, source_root, project_tag)
    VALUES (new.id, new.content_text, new.source_root, new.project_tag);
END;
```

New script `tools/extract_corpus.py`:
- Source roots:
  1. `session_closeouts` table — `failure_summary`, `log_path` fields
  2. `agent_trajectories` table — `input_text` where role='user'
  3. `deliberation_rounds` table — `drafter_output` (Eric's intent text from Brain phase)
  4. `/mnt/archive/` session JSON files (if mounted — check first, skip if not)
- For each source: extract messages where role='user' (Eric's words), tag with project based on topic keyword matching (CIS/SWA/WIAS)
- Re-runnable: skip sources already extracted (check `source_root` + `source_file` + `line_number` uniqueness)
- Output: row count per source root, per project tag

**Files:**
- `runtime/schema/migrations/0021_corpus_entries.sql` (new)
- `tools/extract_corpus.py` (new)

### COMPONENT 4 — Multi-Project Support

**Goal:** Project registration and project-aware pipeline routing per ADR-SEED-010 (filesystem isolation model).

**Critical bug to fix first:** `PipelineRelay.__init__` stores `self.db_path` but `_db_connect()` uses module-level `DB_PATH`. Fix: make `_db_connect()` accept a `db_path` parameter, or make `self.conn = sqlite3.connect(self.db_path, timeout=10)` directly in `__init__`.

**What to build:**

New migration `0022_projects_table.sql`:
```sql
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,            -- 'cis', 'swa', 'wias'
    name TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    spine_path TEXT NOT NULL,       -- path to cis_memory.db for this project
    agents_md_path TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);
INSERT OR IGNORE INTO projects (id, name, repo_path, spine_path, agents_md_path)
VALUES ('cis', 'CIS', '/mnt/projects/cis', '/mnt/projects/cis/data/cis_memory.db', '/mnt/projects/cis/AGENTS.md');
```

Add `project_id TEXT` column to `workflow_runs` (ALTER TABLE in same migration).

Modify `relay.py`:
- `POST /api/relay/start` — accept optional `project` field in JSON body
- When `project` is provided: look up `projects` table for `spine_path`, instantiate `PipelineRelay(db_path=spine_path)`
- When not provided: use default CIS DB

Modify `pipeline_relay.py`:
- Fix `_db_connect()` to accept `db_path` parameter: `def _db_connect(db_path=DB_PATH): return sqlite3.connect(db_path, timeout=10)`
- Fix `PipelineRelay.__init__`: `self.conn = _db_connect(self.db_path)`
- `PROJECT_ROOT` should derive from `self.db_path` parent, not module-level `DB_PATH`

New relay endpoints:
```python
POST /api/projects   # Register a new project
GET /api/projects    # List all projects
```

**Concurrency note:** `relay.py` creates new `PipelineRelay()` instances per request (lines 122, 209). After the `_db_connect` fix, each instance can point at a different DB. Two concurrent runs for different projects will have separate `PipelineRelay` instances with separate connections. This is safe — no shared state between instances except the module-level `DB_PATH` constant (used only as a default).

**Files:**
- `runtime/schema/migrations/0022_projects_table.sql` (new)
- `runtime/abstraction/pipeline_relay.py` (modify — fix `_db_connect` + `__init__`)
- `runtime/api/relay.py` (modify — project parameter + project endpoints)

### COMPONENT 5 — SWA Project Bootstrap

**Goal:** Initialize SWA as a new project with its own repo, spine, and AGENTS.md.

**Prerequisites:** Component 3 (corpus extraction — to find SWA-tagged sessions), Component 4 (multi-project support — to register SWA)

**What to build:**
- Create directory: `/mnt/projects/swa/`
- `git init /mnt/projects/swa/`
- Copy CIS toolchain: `runtime/schema/spine_schema.sql`, `runtime/schema/migrations/` (base schema only — SWA starts fresh), `tools/gates/` (the gate scripts), `tools/export/generate_hcp.py`
- Create SWA spine: `sqlite3 /mnt/projects/swa/data/cis_memory.db < spine_schema.sql`
- Run corpus extraction for SWA-tagged sessions only: `python3 tools/extract_corpus.py --project SWA`
- Generate SWA AGENTS.md from extracted corpus (manual or pipeline-assisted)
- Register SWA: `POST /api/projects {id: 'swa', name: 'SWA', repo_path: '/mnt/projects/swa', spine_path: '/mnt/projects/swa/data/cis_memory.db'}`

**Note:** Eric explicitly overrides AGENTS.md §2 "Do Not Start" for SWA bootstrap. This override is logged in this spec.

**Files:**
- `/mnt/projects/swa/` (new directory tree)
- `AGENTS.md` for SWA (new — generated from corpus)

### COMPONENT 6 — Agent Soul/Briefing Injection

**Goal:** At pipeline run start, inject a structured briefing document into each agent's context.

**What exists:** `_pre_discovery()` already injects KB search results and prior trajectories. This component ADDS a structured soul document wrapper around that.

**What to build:**

New config file `runtime/config/role_overlays.yaml`:
```yaml
brain:
  role: "You are the Brain. Analyze Eric's intent. Identify what exists vs what needs building. Ground every claim in codebase facts."
  bias_overlay: "Resist enterprise patterns. Eric builds creative tools, not enterprise software. Flag any drift toward governance committees, stakeholder approvals, multi-tenant architecture."
draft:
  role: "You are the Drafter. Write detailed build specifications. Specify exact file paths, function names, schema changes. Acknowledge what exists before specifying what's new."
review1:
  role: "You are Reviewer 1. Adversarial critique. Verify every claim against the actual codebase. Flag assumptions. You are the first line of defense against fabrications."
review2:
  role: "You are Reviewer 2. Independent analysis. You MUST produce your own reasoning, not restate Reviewer 1. If you agree, explain WHY with different evidence."
menter:
  role: "You are the Implementer. Build exactly what the spec says. No shortcuts, no stubs, no hardcoded values. Every file you claim to create must actually exist."
verify:
  role: "You are the Verifier. Do not trust Menter's self-report. Run deterministic checks. File exists? Code compiles? Tests pass? Git diff shows claimed changes?"
```

Modify `pipeline_relay.py` `_pre_discovery()` (or add a wrapper `_build_soul_document`):
- Prepend to agent prompt, structured as:
  ```
  [PROJECT_BRIEF]
  {AGENTS.md content, truncated to 4000 chars}
  
  [ROLE_OVERLAY]
  {role_overlays.yaml[role]}
  
  [KB_CONTEXT]
  {top 3 KB hits for this topic — already from _pre_discovery}
  
  [RECENT_RUNS]
  {last 3 runs for this project with their outcomes}
  
  [ERICS_WORKING_METHODS]
  Verification-hardening rule: self-report is not truth.
  Evidence-backed response rule: every claim needs raw evidence.
  READ_ONLY_STANDING_BY: do not modify until explicitly directed.
  
  [TASK]
  {original prompt from pipeline}
  ```

- Token budget: total soul document must not exceed 8000 chars (~2000 tokens). Truncate sections if needed. Priority: ROLE_OVERLAY > TASK > KB_CONTEXT > RECENT_RUNS > PROJECT_BRIEF > ERICS_WORKING_METHODS.

**Files:**
- `runtime/config/role_overlays.yaml` (new)
- `runtime/abstraction/pipeline_relay.py` (modify — add soul document builder, call before `_pre_discovery` or wrap it)

### COMPONENT 7 — Eric Gate as Real Interface

**Goal:** Gate view in control plane UI with mobile-responsive design.

**What exists:** Backend is complete — `POST /api/relay/<run_id>/gate` handles APPROVE/REJECT/REVISE. REVISE loops back to DRAFT_PHASE.

**What to build:** This is UI work only, covered by Component 1's Eric Gate panel in `RelayPage.jsx`.

**Specific mobile requirements:**
- Gate panel: 3 action buttons (Approve/Reject/Refine) full-width on mobile, inline on desktop
- Rationale textarea: min 200px height on mobile
- Deliberation viewer: collapse by default on mobile, expandable sections
- Responsive breakpoint: 768px

**Files:** Covered by Component 1's `RelayPage.jsx`

### COMPONENT 8 — Iterative Development (DELTA only)

**What exists:** REVISE at Eric Gate loops back to DRAFT_PHASE. `MAX_DRAFT_ROUNDS=3` with escalation.

**What to add (genuinely new):**
- Task decomposition: `POST /api/relay/<run_id>/decompose` — takes a large directive, splits into sub-tasks, creates child runs
- Child run tracking: add `parent_run_id TEXT` column to `workflow_runs`
- Dependency tracking: new table `run_dependencies`

New migration `0023_run_decomposition.sql`:
```sql
ALTER TABLE workflow_runs ADD COLUMN parent_run_id TEXT REFERENCES workflow_runs(id);
CREATE TABLE IF NOT EXISTS run_dependencies (
    run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    depends_on_run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    dependency_type TEXT NOT NULL DEFAULT 'sequential',
    PRIMARY KEY (run_id, depends_on_run_id)
);
```

New relay endpoints:
```python
POST /api/relay/<run_id>/decompose   # Split directive into child runs
GET /api/relay/<run_id>/children     # List child runs
```

**Files:**
- `runtime/schema/migrations/0023_run_decomposition.sql` (new)
- `runtime/api/relay.py` (modify — add decompose + children endpoints)

### COMPONENT 9 — Git Workflow

**Goal:** Automated git operations integrated into pipeline phases.

**What to build:**

Add to `pipeline_relay.py`:
- `_git_create_branch(run_id, project_root)`: On EXECUTION phase start, create branch `cis/run-{run_id}` (or `swa/run-{run_id}`)
- `_git_commit(run_id, project_root, topic)`: After Menter completes, commit all changes with message `run-{run_id}: {topic[:80]}`
- `_git_rollback(run_id, project_root)`: On VERIFY_FAILED, `git checkout` back to branch point
- `_git_create_pr(run_id, project_root)`: On CONSENSUS_REACHED, output `gh pr create` command (or auto-create if `gh` is available)

**Design constraint:** These methods take `project_root` as parameter (supports multi-project). They use `subprocess.run(['git', '-C', project_root, ...])`.

**Files:**
- `runtime/abstraction/pipeline_relay.py` (modify — add git methods, call at appropriate phase transitions)

### COMPONENT 10 — Verification Depth

**What exists:** Verify agent reviews text output. `_run_automated_checks()` does syntax checking, secret scanning, test collection. L1 verification runs git diff.

**What to add:**

- Test execution: After test collection, run `pytest` if tests exist. Add to `_run_automated_checks()` in `pipeline_relay.py`
- Regression detection: `git stash` → run tests on pre-change state → `git stash pop` → compare results
- Directive scope verification: Parse the FINAL_DIRECTIVE from Eric Gate approval, extract claimed file paths, verify each path exists via `os.path.exists()`
- Browser/UI verification: For UI changes, use `curl` against the running container app to verify pages load (200 status), or use Playwright for headless browser checks if available

**Files:**
- `runtime/abstraction/pipeline_relay.py` (modify — extend `_run_automated_checks()`)

### COMPONENT 11 — Error Recovery (DELTA only)

**What exists:** Circuit breaker (3 failures → 5 min cooldown). Agent timeouts (180-600s). Telegram notifications on terminal failures. `MAX_DRAFT_ROUNDS=3` → ESCALATED.

**What to add (genuinely new):**

- Auto-retry for transient failures: In agent dispatch, if HTTP call fails with connection refused or timeout, retry once after 5 seconds before tripping circuit breaker
- Dead letter queue: New table for runs in ESCALATED or ERROR status

New migration `0024_dead_letter_queue.sql`:
```sql
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    failed_at TEXT DEFAULT (datetime('now')),
    error_message TEXT,
    agent_role TEXT,
    phase TEXT,
    input_text TEXT,
    retry_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'  -- pending, retried, resolved, abandoned
);
```

- Timeout enforcement: Ensure `httpx.AsyncClient(timeout=...)` is set at the HTTP call level in agent dispatch (verify, don't assume)
- Telegram notification on ERIC_GATE: Extend `_notify_terminal_failure` or add `_notify_eric_gate` to send a Telegram message when a run reaches ERIC_GATE status

**Files:**
- `runtime/schema/migrations/0024_dead_letter_queue.sql` (new)
- `runtime/abstraction/pipeline_relay.py` (modify — add retry logic, dead letter insertion, Eric Gate notification)

### COMPONENT 12 — Monitoring and Observability

**What to build:**

New relay endpoint:
```python
GET /api/relay/metrics
# Returns: {
#   total_runs, runs_by_status: {PENDING: N, CONSENSUS_REACHED: N, ...},
#   avg_rounds, avg_duration_seconds,
#   agent_success_rates: {brain: {success: N, failure: N}, ...},
#   total_tokens_estimated
# }
```

Token tracking: Add `tokens_in INTEGER` and `tokens_out INTEGER` columns to `agent_trajectories`. Capture from gateway response headers or response body if available.

New migration `0025_agent_token_tracking.sql`:
```sql
ALTER TABLE agent_trajectories ADD COLUMN tokens_in INTEGER DEFAULT 0;
ALTER TABLE agent_trajectories ADD COLUMN tokens_out INTEGER DEFAULT 0;
```

SSE endpoint (optional, simple polling works for Phase B):
```python
GET /api/relay/events?run_id=X
# Server-Sent Events: sends status changes as they happen
```

Error log endpoint:
```python
GET /api/relay/<run_id>/errors
# Returns only error-level entries from agent_trajectories where outcome='failure'
```

**Files:**
- `runtime/schema/migrations/0025_agent_token_tracking.sql` (new)
- `runtime/api/relay.py` (modify — add metrics + errors endpoints)
- `runtime/abstraction/pipeline_relay.py` (modify — capture token counts in agent dispatch)

### COMPONENT 13 — Remote Access

**What exists:** Bearer token auth on relay API. Container runs on `127.0.0.1:5000`. Existing auth system has `/api/app/auth/login` and `/api/app/auth/register`.

**What to build:**
- Extend relay endpoints to check session cookie (not just Bearer token)
- Document nginx reverse proxy + Let's Encrypt setup for HTTPS
- Document Tailscale Serve configuration for remote access
- Create `docs/REMOTE_ACCESS_SETUP.md` with step-by-step instructions

**Files:**
- `runtime/api/relay.py` (modify — session auth)
- `docs/REMOTE_ACCESS_SETUP.md` (new — documentation)

### COMPONENT 14 — Persistent State and Handoff

**What exists:** `workflow_runs`, `deliberation_rounds`, `agent_trajectories`, `eric_gate_approvals`, `session_closeouts`, `session_handoffs` tables. MCP bridge can query all.

**What to add:**
- Schema fix: `spine_schema.sql` is stale — update it to reflect migrations 0011-0020. This is a documentation fix, not a schema change (the live DB already has everything)
- "What did we do last time?": Extend `_pre_discovery()` to query last 3 CONSENSUS_REACHED runs for the current project and include their drafter_output summaries
- Per-project decision log: `project_decisions` table already exists. For SWA, ADRs are stored in SWA's own spine (separate DB per ADR-SEED-010)
- Session handoff: Load most recent `session_closeouts` row for the project and include it in the soul document (Component 6)

**Files:**
- `runtime/schema/spine_schema.sql` (modify — sync with live DB state)
- `runtime/abstraction/pipeline_relay.py` (modify — extend `_pre_discovery()` with recent run summaries)

---

## 2. Build Phases

### Phase A — Foundation (order matters)
| Step | Component | What | Key Files |
|------|-----------|------|-----------|
| A1 | Bug fix | Fix `_db_connect()` to accept db_path parameter | `pipeline_relay.py` |
| A2 | Component 2 | Fix `cis_get_run_detail` bug + add KB search endpoints | `mcp_bridge/spine.py`, `relay.py` |
| A3 | Component 3 | Corpus extraction (migration 0021 + script) | `0021_corpus_entries.sql`, `tools/extract_corpus.py` |
| A4 | Component 4 | Multi-project support (migration 0022 + routing) | `0022_projects_table.sql`, `pipeline_relay.py`, `relay.py` |

### Phase B — Interface & Bootstrap
| Step | Component | What | Key Files |
|------|-----------|------|-----------|
| B1 | Component 1 | Control Plane UI (RelayPage + run list endpoint) | `RelayPage.jsx`, `api.js`, `App.jsx`, `relay.py` |
| B2 | Component 7 | Eric Gate UI (mobile-responsive, in RelayPage) | Covered by B1 |
| B3 | Component 6 | Agent soul/briefing injection | `role_overlays.yaml`, `pipeline_relay.py` |
| B4 | Component 5 | SWA project bootstrap | `/mnt/projects/swa/` tree |

### Phase C — Pipeline Hardening
| Step | Component | What | Key Files |
|------|-----------|------|-----------|
| C1 | Component 8 | Task decomposition + child runs | `0023_run_decomposition.sql`, `relay.py` |
| C2 | Component 9 | Git workflow (branch/commit/rollback) | `pipeline_relay.py` |
| C3 | Component 10 | Verification depth (test execution + scope check) | `pipeline_relay.py` |
| C4 | Component 11 | Error recovery (retry + dead letter + notifications) | `0024_dead_letter_queue.sql`, `pipeline_relay.py` |

### Phase D — Production Readiness
| Step | Component | What | Key Files |
|------|-----------|------|-----------|
| D1 | Component 12 | Monitoring and observability | `0025_agent_token_tracking.sql`, `relay.py`, `pipeline_relay.py` |
| D2 | Component 13 | Remote access (auth + docs) | `relay.py`, `docs/REMOTE_ACCESS_SETUP.md` |
| D3 | Component 14 | Persistent state hardening (schema sync + handoff) | `spine_schema.sql`, `pipeline_relay.py` |

---

## 3. Schema Migrations Summary

| Migration | Table(s) | Purpose |
|-----------|----------|---------|
| 0021 | corpus_entries + FTS | Corpus extraction storage |
| 0022 | projects + workflow_runs.project_id | Multi-project support |
| 0023 | workflow_runs.parent_run_id + run_dependencies | Task decomposition |
| 0024 | dead_letter_queue | Error recovery |
| 0025 | agent_trajectories.tokens_in/out | Token tracking |

No migration conflicts. Next available number is 0021 (verified — last migration file is `0020_deliberation_rounds_signal_check.sql`).

---

## 4. Architecture Decisions

- **ADR-SEED-010** governs: `--project-root` model (filesystem isolation). Each project gets own spine DB. Shared toolchain, isolated state. No database-level multi-tenancy.
- **ADR-SEED-002** governs: Verification-hardening. Menter self-report is not truth. Verify agent must produce deterministic evidence.
- **ADR-SEED-012** governs: FINAL_JSON blocks for state transitions. Already implemented in `_parse_final_json`. Maintain this pattern.
- **New:** Control plane UI is read-heavy and polling-based (2-second intervals). No WebSocket complexity in Phase B. Add SSE in Phase D if polling proves insufficient.
- **New:** Soul injection happens at dispatch time in `pipeline_relay.py`, not at profile configuration time. This allows per-run context (KB hits, recent runs) that static profile configs can't provide.
- **New:** Multi-project concurrency is safe because `relay.py` creates new `PipelineRelay()` instances per request. After the `_db_connect` fix, each instance uses its own DB path. No shared mutable state between instances.

---

## 5. Verification Plan

After each phase, the Verifier checks:

**Phase A:**
- `GET /api/relay/kb/search?q=control+plane` returns results
- `python3 tools/extract_corpus.py` produces row counts per source root and project tag
- `POST /api/relay/start` with `project=swa` creates a run in SWA's spine (verify: run appears in SWA's DB, not CIS's)
- `PipelineRelay(db_path='/tmp/test.db')` actually connects to `/tmp/test.db` (unit test)

**Phase B:**
- Browser at `/relay` shows intent submission form
- Submitting intent starts a real pipeline run, live view updates
- Eric Gate panel appears at ERIC_GATE status with 3 buttons
- Gate panel is usable on mobile viewport (375px width)
- Agent prompts contain `[PROJECT_BRIEF]`, `[ROLE_OVERLAY]`, `[KB_CONTEXT]` sections (verify in `agent_trajectories.input_text`)
- SWA project exists at `/mnt/projects/swa/` with its own spine DB and AGENTS.md

**Phase C:**
- `POST /api/relay/<run_id>/decompose` creates child runs with `parent_run_id` set
- Git branch created on EXECUTION phase start
- Git commit created after Menter completes
- Failed verification triggers git rollback
- `pytest` runs during verification phase if tests exist
- Dead letter queue has rows for ESCALATED/ERROR runs

**Phase D:**
- `GET /api/relay/metrics` returns run counts and agent success rates
- `agent_trajectories` has non-zero `tokens_in`/`tokens_out` for recent runs
- `spine_schema.sql` matches live DB schema (all tables/columns present)
- `_pre_discovery()` includes last 3 CONSENSUS_REACHED run summaries in agent prompts

---

## 6. Menter Directives

Build in phase order (A → B → C → D). Within each phase, build in step order (A1 before A2, etc.).

For each step:
1. Create/modify the files listed
2. Run `python3 -m py_compile` on any Python file you touch
3. Run the migration against the spine DB if one is specified
4. Verify the change works (curl the endpoint, run the script, check the file)
5. Report what you did with evidence (file paths, command output, git diff)

**Do NOT:**
- Rebuild mechanisms that already exist (see §0 "Existing Mechanisms")
- Create stubs or placeholder code
- Hardcode values that should be config
- Skip the `_db_connect` fix — it blocks Component 4
- Create migration numbers below 0021

**Do:**
- Read the actual source files before modifying them
- Test each change before reporting completion
- Include file paths and line numbers in your reports
- Ask for clarification via the answer endpoint if something is ambiguous
