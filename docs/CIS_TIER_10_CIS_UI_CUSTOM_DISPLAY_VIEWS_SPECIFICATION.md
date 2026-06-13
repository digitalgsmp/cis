# Tier 10 — CIS UI / Custom Display Views Specification
## Specification Document v1.0

## Eric Gate Status: PENDING_APPROVAL

This document defines the architectural direction for Tier 10. It is **NOT** an
implementation directive. No code shall be written, no spine rows modified, and no
files staged under this document alone. Implementation proceeds only after Eric
Gate approval is recorded.

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-13
**Revised:** 2026-06-13 — Reviewer corrections: R1 (11→20 page count, separated top-level/infra), R2 (Appendix A.2: complete JSX + HTML inventory), R3 (Appendix A.3: corrected grep command).
**Status:** REVISED_DRAFT — corrections applied, awaiting Reviewer re-review
**Gating dependency:** Tier 9 (Chroma/VDB) must be COMPLETE per dependency graph

---

## 1. Purpose

### 1.1 What Tier 10 solves

CIS has a working React/Flask UI (`runtime/app.py`, `runtime/ui/`) with pages for
Ideas, Projects, Schedule, DAM, Review Queue, Learning, Ingestion, Spine Map,
Infrastructure, Chat, and Advisor Chat. But these pages were built before Tier 8
(MCP Bridge) and Tier 9 (Chroma/VDB) existed.

Current limitations:

- **No live pipeline visibility.** The HomePage shows dashboard stats from
  static API endpoints. It cannot show current build_plan_nodes status, recent
  workflow_runs, or pending Eric Gate approvals without regenerating AGENTS.md.
- **No semantic archive search in the UI.** The DAM page shows extracted text
  assets but cannot answer "find sessions about client intake" — only keyword
  search. Chroma semantic search (Tier 9) has no UI surface.
- **No decision trail browser.** The 13 ADR-SEED decisions live in
  `project_decisions` but have no UI for browsing, filtering, or tracing
  superseded chains.
- **No session archive browser.** The 12 session_closeouts and 3,082 DAM
  sessions have no dedicated browse/search UI component.
- **No Eric Gate dashboard.** Pending approvals, escalation status, and gate
  history are queryable via MCP tools but invisible in the UI.

Tier 10 adds **custom display views** — read-only UI components that consume
Tier 8 MCP Bridge tools and Tier 9 Chroma/VDB semantic search, surfacing live
pipeline state and archive search in the existing CIS dashboard.

### 1.2 Core capability

> **A set of read-only display views in the existing CIS UI that consume Tier 8
> MCP Bridge tools (live spine state) and Tier 9 Chroma/VDB tools (semantic
> archive search), providing the operator with live pipeline visibility, archive
> discovery, and decision lineage tracing — without adding write endpoints or
> bypassing the WorkIntent → Process Manager → Eric Gate pipeline.**

### 1.3 What changes for the operator (Eric)

| Before Tier 10 | After Tier 10 |
|----------------|---------------|
| Must query SQLite or MCP CLI to see build plan status | View live build plan node status, dependencies, and blockers in the UI |
| Must run `cis_search_sessions` via CLI to find past sessions | Semantic search the archive from the UI with relevance-ranked results |
| Must query `project_decisions` table directly to see ADR lineage | Browse decisions with filter/search, see superseded chains |
| Eric Gate approval status invisible unless queried manually | Eric Gate dashboard shows pending approvals, escalation state |
| No way to browse session closeout history | Session archive browser with FTS5 + semantic dual search |

### 1.4 What Tier 10 does NOT change

- The existing UI (HomePage, Ideas, Projects, DAM, etc.) remains fully functional.
  Tier 10 views are **additive** — new pages or new sections on existing pages.
- No existing API endpoints are modified or removed.
- No existing React components are rewritten.
- The Flask backend (`app.py`) gains only read-only proxy endpoints if needed
  to expose MCP/Chroma results to the frontend. It does not gain write endpoints.
- This is NOT a "broad UI redesign." It is targeted custom display views for
  specific pipeline-state and archive-search use cases.

---

## 2. Display Views — What Is Needed

### 2.1 View inventory

| # | View Name | Consumes | Purpose |
|---|-----------|----------|---------|
| V1 | **Build Plan Status** | Tier 8 MCP: `cis_get_current_phase`, `cis_get_build_status`, `cis_get_next_actions` | Live display of build_plan_nodes: tier labels, statuses, dependencies, blockers. Replaces static AGENTS.md §1 snapshot with live query. |
| V2 | **Recent Pipeline Runs** | Tier 8 MCP: `cis_get_recent_runs`, `cis_get_run_detail` | Browse recent workflow_runs with deliberation round counts, results, timestamps. Click into a run to see its deliberation_rounds. |
| V3 | **Eric Gate Dashboard** | Tier 8 MCP: `cis_get_eric_gate_status`, `cis_get_open_decisions` | Pending approvals, escalation status, decision trail summary. "What needs Eric's attention right now." |
| V4 | **Semantic Archive Search** | Tier 9 MCP: `cis_search_semantic` | Meaning-based search across DAM sessions, deliberation rounds, decisions, and closeouts. Relevance-ranked results with source metadata. |
| V5 | **Session Archive Browser** | Tier 8 MCP: `cis_search_sessions` (FTS5) + Tier 9 MCP: `cis_search_semantic` | Browse session_closeouts and DAM sessions. Dual search: keyword (FTS5) + meaning (semantic). Toggle between modes. |
| V6 | **Decision Trail Viewer** | Tier 8 MCP: `cis_get_open_decisions` | Browse ADR-SEED decisions: filter by status, see superseded chains, view decision text. |

### 2.2 View descriptions

#### V1: Build Plan Status

- **Layout:** Table or card grid showing all build_plan_nodes.
- **Columns:** Node label, status (color-coded: COMPLETE=green, IN_PROGRESS=blue, PENDING=yellow, BLOCKED=red), dependencies, completed_at.
- **Data source:** `cis_get_current_phase()` for summary + `cis_get_build_status(node_label)` for details.
- **Update:** Query on page load. Manual refresh button. No polling (read-only MCP bridge, no server push).
- **Navigation target:** New route `/pipeline` or section on existing HomePage.

#### V2: Recent Pipeline Runs

- **Layout:** Table with expandable rows. Click a row to see deliberation_rounds for that run.
- **Columns:** run_id, topic, result, rounds_completed, created_at.
- **Data source:** `cis_get_recent_runs(limit=20)` for list, `cis_get_run_detail(run_id)` for detail.
- **Update:** Query on page load. Detail on click.
- **Navigation target:** New route `/pipeline/runs` or section under `/pipeline`.

#### V3: Eric Gate Dashboard

- **Layout:** Card-based dashboard showing:
  - Pending approvals (count + list)
  - Open decisions requiring attention
  - Escalation status
- **Data source:** `cis_get_eric_gate_status()`, `cis_get_open_decisions()`.
- **Update:** Query on page load. Manual refresh.
- **Navigation target:** New route `/eric-gate` or sidebar widget.

#### V4: Semantic Archive Search

- **Layout:** Search bar + result list. Each result shows:
  - Relevance score
  - Source table (dam_extracted_text, deliberation_rounds, project_decisions, session_closeouts)
  - Text snippet (first 200 chars)
  - Link to source (DAM asset, run detail, etc.)
- **Data source:** `cis_search_semantic(query, top_k=20)`.
- **Navigation target:** New route `/archive/search` or search bar on DAM page.

#### V5: Session Archive Browser

- **Layout:** Combined search + browse. Toggle between FTS5 (keyword) and semantic (meaning) search modes.
  - FTS5 mode: calls `cis_search_sessions(query)`.
  - Semantic mode: calls `cis_search_semantic(query)`.
- **Browse:** Paginated list of all session_closeouts with filter by status (PASS/FAIL/BLOCKED).
- **Data source:** `cis_search_sessions(query)` (FTS5) + `cis_search_semantic(query)` (semantic) + direct SQLite for browse (via existing API).
- **Navigation target:** New route `/archive/sessions` or section under DAM.

#### V6: Decision Trail Viewer

- **Layout:** Filterable list of project_decisions. Each card shows:
  - Decision ID (ADR-SEED-xxx)
  - Label
  - Status (DECIDED, with superseded_by chain if any)
  - Decision text (truncated, expandable)
- **Filters:** By status, by keyword in label/decision text.
- **Data source:** `cis_get_open_decisions()`.
- **Navigation target:** New route `/decisions` or nested under `/pipeline`.

---

## 3. How the UI Consumes Tier 8 MCP and Tier 9 Outputs

### 3.1 Data flow

```
┌──────────────────────────────────────────────────────┐
│  CIS React Frontend (runtime/ui/)                    │
│                                                      │
│  New Display Views (V1-V6):                          │
│    BuildPlanStatus.jsx                               │
│    PipelineRuns.jsx                                  │
│    EricGateDashboard.jsx                             │
│    SemanticSearch.jsx                                │
│    SessionArchive.jsx                                │
│    DecisionTrail.jsx                                 │
│                                                      │
│  All read-only. No write buttons, no mutation forms. │
└──────────────────────┬───────────────────────────────┘
                       │ HTTP GET (read-only endpoints)
                       │
┌──────────────────────▼───────────────────────────────┐
│  CIS Flask Backend (runtime/app.py)                  │
│                                                      │
│  NEW read-only proxy endpoints (blueprint):          │
│    GET /api/pipeline/status                          │
│    GET /api/pipeline/runs                            │
│    GET /api/pipeline/runs/<run_id>                   │
│    GET /api/pipeline/eric-gate                       │
│    GET /api/archive/search/semantic?q=...            │
│    GET /api/archive/search/fts?q=...                 │
│    GET /api/decisions                                │
│                                                      │
│  These endpoints call MCP tools. They do NOT:        │
│    - Call INSERT/UPDATE/DELETE on any DB             │
│    - Trigger pipeline runs                           │
│    - Bypass Process Manager or Eric Gate             │
│    - Expose credentials or secrets                   │
└──────────────────────┬───────────────────────────────┘
                       │ MCP stdio protocol
                       │
┌──────────────────────▼───────────────────────────────┐
│  cis_mcp_bridge/           (Tier 8 + Tier 9)         │
│  ├── server.py                                        │
│  ├── tools.py          (11 tools total)               │
│  ├── spine.py          (SQLite read-only)             │
│  └── chroma_index.py   (Chroma queries)               │
│                                                      │
│  All queries are read-only SELECT against             │
│  cis_memory.db or Chroma query against                │
│  chroma_data/.                                        │
└──────────────────────┬───────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ SQLite   │ │ Chroma   │ │ Session  │
   │ Spine    │ │ VDB      │ │ Transcripts
   │          │ │          │ │ (Hermes) │
   └──────────┘ └──────────┘ └──────────┘
```

### 3.2 How the Flask backend calls MCP tools

The Flask backend does NOT spawn the MCP bridge directly. Instead, it calls the
MCP bridge Python module in-process (since both run in the Hermes venv):

```python
# In a new blueprint file: runtime/api/pipeline_views.py
from cis_mcp_bridge.tools import (
    cis_get_current_phase,
    cis_get_build_status,
    cis_get_next_actions,
    cis_get_recent_runs,
    cis_get_run_detail,
    cis_get_eric_gate_status,
    cis_get_open_decisions,
    cis_search_sessions,
    cis_search_semantic,
)
```

Each endpoint handler calls the corresponding function directly. No subprocess
spawn, no HTTP to MCP bridge, no network hop. The MCP bridge functions are
imported as Python modules and return Python dicts/lists — the Flask endpoints
serialize to JSON.

This is the simplest integration path and avoids:
- Spawning a separate MCP server process per request
- HTTP overhead between Flask and MCP
- Authentication complexity (same process, same user)

### 3.3 No new write endpoints

The new Flask blueprint (`pipeline_views.py`) contains ONLY `GET` endpoints.
No `POST`, `PUT`, `PATCH`, or `DELETE`. Verified by automated gate
(`gate_ui_no_write_endpoints.sh`, see §10.2).

---

## 4. Read-Only Enforcement

### 4.1 UI level

- All new display views are **display only**. No forms, no input fields beyond
  search queries, no "approve," "reject," "create," "edit," or "delete" buttons.
- Search bars and filter dropdowns are the only interactive elements.
- Existing UI pages (Ideas, Projects, etc.) are not modified to add write
  capabilities through these new views.

### 4.2 Backend level

- All new API endpoints are `GET` methods only.
- No endpoint accepts a request body.
- Endpoints do not call any function that writes to `cis_memory.db` or Chroma.
- The `gate_ui_no_write_endpoints.sh` gate verifies this at implementation time.

### 4.3 Pipeline level

- Display views cannot trigger WorkIntent creation, Process Manager state
  transitions, or Eric Gate approvals.
- The only path to mutation remains: WorkIntent → Process Manager → Human
  Approval Gate → Dispatch / Dead Letter (Tier 7R).
- Display views are consumers of pipeline state, not participants in the
  pipeline.

---

## 5. No Pipeline Bypass

### 5.1 What the UI display views must NOT do

| Prohibited | Enforcement |
|------------|-------------|
| Create WorkIntent objects | No POST endpoints, no write functions in UI code |
| Trigger Process Manager transitions | UI has no import of process_manager.py |
| Record Eric Gate approvals | UI has no import of eric_gate modules |
| Dispatch agents | UI has no import of dispatch or agent modules |
| Write to SQLite spine | No INSERT/UPDATE/DELETE in UI backend code |
| Write to Chroma | No index-build functions called from UI backend |
| Modify existing API blueprints | New blueprint only; existing blueprints unchanged |
| Expose MCP tools as public HTTP POST | All new endpoints are GET; no tool-call-by-HTTP |

### 5.2 Verification

- `gate_ui_no_pipeline_bypass.py` scans the new blueprint for imports of
  pipeline modules (process_manager, approval_gate, classifier, work_intent,
  dispatch, dead_letter) and fails if any are found.
- `gate_ui_no_write_endpoints.sh` scans for POST/PUT/PATCH/DELETE decorators.
- `gate_mcp_readonly.py` (existing Tier 8 gate) covers the MCP bridge layer.

---

## 6. Minimum Architecture

### 6.1 Architecture constraint: use existing stack

Tier 10 does NOT introduce a new frontend framework, new backend server, or new
database. It extends the existing CIS stack:

| Layer | Existing | Tier 10 Change |
|-------|----------|----------------|
| Frontend | React (runtime/ui/) with react-router, reactflow | 6 new page components, 1-2 new routes |
| Backend | Flask (runtime/app.py) with ~30 blueprints | 1 new read-only blueprint (pipeline_views.py) |
| Database | SQLite (cis_memory.db) | No new tables. Reads only. |
| Vector DB | Chroma (chroma_data/) | Read queries only. No writes from UI. |
| MCP Bridge | cis_mcp_bridge/ (Tier 8+9) | No changes. Imported as Python modules. |

### 6.2 New files to create

| File | Purpose |
|------|---------|
| `runtime/api/pipeline_views.py` | Flask blueprint: read-only endpoints that import MCP tool functions and return JSON |
| `runtime/api/__init__.py` | May already exist; update if needed |
| `runtime/ui/src/pages/PipelinePage.jsx` | Build Plan Status + Recent Runs (V1+V2) |
| `runtime/ui/src/pages/EricGatePage.jsx` | Eric Gate Dashboard (V3) |
| `runtime/ui/src/pages/ArchiveSearchPage.jsx` | Semantic Archive Search (V4) |
| `runtime/ui/src/pages/SessionArchivePage.jsx` | Session Archive Browser (V5) |
| `runtime/ui/src/pages/DecisionsPage.jsx` | Decision Trail Viewer (V6) |

### 6.3 Files to modify

| File | Change |
|------|--------|
| `runtime/app.py` | Register new `pipeline_views` blueprint |
| `runtime/ui/src/App.jsx` | Add new routes and nav entries for V1-V6 |
| `runtime/ui/src/api.js` | Add API call functions for new endpoints (if needed) |

### 6.4 No new dependencies

Tier 10 uses the existing stack:
- React 18+ (already in `runtime/ui/`)
- Flask (already in `runtime/app.py`)
- `cis_mcp_bridge` tools (Tier 8+9, already importable)
- No new npm packages, no new pip packages

### 6.5 No new services

- No new systemd services
- No new ports
- No new processes
- The existing Flask server (`runtime/app.py`) serves the new endpoints on the
  existing port (5000)

---

## 7. Required Endpoints and Schemas

### 7.1 New Flask blueprint endpoints (all GET, all read-only)

| Endpoint | Calls MCP Tool | Returns |
|----------|---------------|---------|
| `GET /api/pipeline/status` | `cis_get_current_phase()` | Build plan summary: current tier, status, next actions |
| `GET /api/pipeline/status/<node_label>` | `cis_get_build_status(node_label)` | Single node detail |
| `GET /api/pipeline/runs?limit=20` | `cis_get_recent_runs(limit)` | Recent workflow_runs list |
| `GET /api/pipeline/runs/<run_id>` | `cis_get_run_detail(run_id)` | Run detail + deliberation_rounds |
| `GET /api/pipeline/eric-gate` | `cis_get_eric_gate_status()` | Pending approvals |
| `GET /api/decisions` | `cis_get_open_decisions()` | Active decisions list |
| `GET /api/archive/search/semantic?q=<query>&top_k=20` | `cis_search_semantic(query, top_k)` | Semantic search results |
| `GET /api/archive/search/fts?q=<query>` | `cis_search_sessions(query)` | FTS5 search results |

### 7.2 No new database tables

Tier 10 does not add tables to `cis_memory.db`. All data is read from existing
tables via MCP bridge tools.

### 7.3 No new Chroma collections

Tier 10 queries existing Tier 9 collections. No new embeddings, no new
collections, no index modifications.

### 7.4 No new configuration files

- The existing Flask config (`runtime/config.py`) is sufficient.
- The existing React build setup (`runtime/ui/vite.config.js` or equivalent) is
  sufficient.
- No new environment variables are required.

---

## 8. Security and Constraints

### 8.1 Read-only enforcement (layered)

| Layer | Mechanism |
|-------|-----------|
| Flask endpoint | `@app.route(..., methods=['GET'])` — only GET |
| MCP bridge | SQLite read-only mode + SELECT-only queries (Tier 8) |
| Chroma | Query-only methods; no `add()`, `upsert()`, `delete()` from UI code |
| UI components | No mutation buttons, no forms with POST actions |

### 8.2 No secrets exposure

- The Flask backend already requires `CIS_API_KEY` for non-localhost API access
  (existing `app.py` `before_request` hook).
- The new endpoints inherit this authentication.
- No API keys, tokens, or secrets are embedded in React component code.
- Search queries are user-entered text — no credential injection vector.

### 8.3 No unapproved writes

- The UI display views have zero write code paths.
- The Flask blueprint has zero write endpoints.
- The MCP bridge (Tier 8) is read-only by design.
- Chroma queries (Tier 9) are query-only from the UI path.

### 8.4 Network exposure

- The Flask server already binds to `localhost:5000` (existing behavior).
- No new ports are opened.
- No external network access is introduced.
- The new React components make fetch calls to the same origin
  (`/api/pipeline/...`) — no cross-origin requests.

### 8.5 No secrets in search queries

- Semantic search queries and FTS5 queries are user-entered text passed as URL
  query parameters.
- No secret-like patterns are required or expected in search queries.
- The MCP bridge's existing security gates (no network, no write SQL) cover the
  backend path.

---

## 9. Deterministic Acceptance Criteria

### 9.1 Functional acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| A1 | Build plan status loads | Navigate to `/pipeline` | All build_plan_nodes displayed with correct status colors | Compare against `SELECT * FROM build_plan_nodes` |
| A2 | Build plan status updates | Tier 8 node status changes | `/pipeline` shows updated status after refresh | Spine query before/after |
| A3 | Pipeline runs list | Navigate to `/pipeline/runs` | Up to 20 most recent workflow_runs displayed | Compare against `SELECT * FROM workflow_runs ORDER BY created_at DESC LIMIT 20` |
| A4 | Run detail expands | Click a run row | Deliberation rounds for that run displayed with correct round numbers | Compare against `SELECT * FROM deliberation_rounds WHERE run_id = ?` |
| A5 | Eric Gate dashboard loads | Navigate to `/eric-gate` | Pending approvals count and list displayed | Compare against `eric_gate_approvals` table |
| A6 | Semantic search returns results | Search "client intake" on archive page | Relevance-ranked results with scores > 0, spanning multiple source tables | Manual spot-check + Chroma native query |
| A7 | FTS5 search returns results | Search "closeout" on session archive | Matching session_closeouts displayed | Compare against `cis_search_sessions("closeout")` |
| A8 | Decision trail loads | Navigate to `/decisions` | All 13 ADR-SEED decisions displayed with status and labels | Compare against `project_decisions` table |
| A9 | No write endpoints | Scan `pipeline_views.py` | Zero POST/PUT/PATCH/DELETE decorators | `grep -E '@(route|app\.route).*methods.*POST\|PUT\|PATCH\|DELETE'` |
| A10 | Existing UI pages unchanged | Navigate to `/ideas`, `/projects`, `/dam`, etc. | All existing pages load and function identically | Manual navigation regression |

### 9.2 Security acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| S1 | No write endpoints | Scan `pipeline_views.py` | Zero POST/PUT/PATCH/DELETE | `gate_ui_no_write_endpoints.sh` |
| S2 | No pipeline bypass imports | Scan `pipeline_views.py` | No imports from process_manager, approval_gate, classifier, work_intent, dispatch, dead_letter | `gate_ui_no_pipeline_bypass.py` |
| S3 | No secrets in frontend code | Scan new JSX files | No hardcoded API keys, tokens, or passwords | `grep -rE 'sk-|gh[pousr]_|AKIA|Bearer|eyJ'` |
| S4 | All endpoints are GET | Curl each endpoint with POST | All return 405 Method Not Allowed | `gate_ui_method_allowlist.sh` |
| S5 | Authentication required for non-localhost | Curl from external IP (simulated) | 401 Unauthorized | Existing CIS_API_KEY check |

### 9.3 Integration acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| I1 | Flask serves new endpoints | Start Flask, curl `/api/pipeline/status` | Returns JSON with build_plan_nodes | Curl + jq validation |
| I2 | React builds with new pages | `npm run build` in `runtime/ui/` | Build succeeds, new routes in bundle | Build output |
| I3 | New nav links appear | Navigate to CIS dashboard | New nav entries for Pipeline, Eric Gate, Archive, Decisions visible | Browser screenshot |
| I4 | Existing UI regression | Navigate to all 20 existing JSX page files (13 top-level + 7 infra sub-pages) | All load correctly, no JS errors | Browser console check |
| I5 | MCP bridge functions importable | `python -c "from cis_mcp_bridge.tools import cis_get_current_phase; print(type(cis_get_current_phase))"` | Prints `<class 'function'>` | Import test |

---

## 10. Required Tests and Gates Before Implementation

### 10.1 Pre-implementation gates

| Gate | Type | Purpose |
|------|------|---------|
| Tier 9 COMPLETE | Dependency | Chroma/VDB must be verified complete with acceptance tests passing |
| Existing UI operational | Functional | Flask server starts, React app builds, all 20 existing JSX page files (13 top-level + 7 infra sub-pages) load |
| MCP tools importable in Flask context | Dependency | `from cis_mcp_bridge.tools import cis_get_current_phase` succeeds from `runtime/` |
| No `pipeline_views.py` exists yet | State | Confirm no prior Tier 10 implementation artifacts |

### 10.2 Post-implementation verification gates

| Gate | Type | Purpose |
|------|------|---------|
| `gate_ui_no_write_endpoints.sh` | Security | Scan `pipeline_views.py` for POST/PUT/PATCH/DELETE |
| `gate_ui_no_pipeline_bypass.py` | Security | Scan for pipeline module imports |
| `gate_ui_method_allowlist.sh` | Security | Confirm all new endpoints reject non-GET methods |
| `gate_ui_tool_a1.sh` through `gate_ui_tool_a10.sh` | Functional | One gate per acceptance test A1-A10 |
| `gate_ui_regression.sh` | Functional | Navigate all 20 existing JSX page files (13 top-level + 7 infra sub-pages), confirm zero JS errors |
| `gate_ui_build.sh` | Functional | `npm run build` succeeds with new components |
| `gate_ui_no_secrets_in_jsx.sh` | Security | Scan JSX files for secret patterns |

### 10.3 Test file structure

```
/mnt/projects/cis/
├── tests/
│   └── ui/
│       ├── test_pipeline_views.py       # Unit tests for Flask blueprint endpoints
│       ├── test_ui_security.py          # Security boundary tests (S1-S5)
│       └── test_ui_integration.py       # Integration tests (I1-I5)
└── tools/
    └── gates/
        ├── gate_ui_no_write_endpoints.sh
        ├── gate_ui_no_pipeline_bypass.py
        ├── gate_ui_method_allowlist.sh
        ├── gate_ui_tool_a1.sh through gate_ui_tool_a10.sh
        ├── gate_ui_regression.sh
        ├── gate_ui_build.sh
        └── gate_ui_no_secrets_in_jsx.sh
```

---

## 11. Phased Build Plan

### 11.1 Build nodes

| Node | Label | Depends On | Scope |
|------|-------|-----------|-------|
| Tier 10.1 | UI — Flask blueprint | Eric Gate on this spec, Tier 9 COMPLETE | Implement `runtime/api/pipeline_views.py`: 8 read-only GET endpoints. Unit tests. |
| Tier 10.2 | UI — React components (pipeline views) | Tier 10.1 | Implement `PipelinePage.jsx`, `EricGatePage.jsx`, `DecisionsPage.jsx` (V1, V2, V3, V6). Wire to new endpoints. |
| Tier 10.3 | UI — React components (archive views) | Tier 10.2 | Implement `ArchiveSearchPage.jsx`, `SessionArchivePage.jsx` (V4, V5). Wire to search endpoints. |
| Tier 10.4 | UI — App integration | Tier 10.3 | Add new routes and nav entries to `App.jsx`. Update `api.js` if needed. |
| Tier 10.5 | UI — security gates | Tier 10.4 | Run all security gates: no write endpoints, no pipeline bypass, no secrets. |
| Tier 10.6 | UI — regression test | Tier 10.5 | Run existing UI regression: all 20 existing JSX page files (13 top-level + 7 infra sub-pages) load, zero JS errors. |
| Tier 10.7 | UI — acceptance test suite | Tier 10.6 | Run all 10 functional acceptance tests (A1-A10). Record results. |
| Tier 10.8 | UI — closeout | Tier 10.7 | Verify all gates pass. Record evidence. Regenerate exports. Request Eric Gate closeout. |

### 11.2 What each node does NOT include

| Node | Exclusions |
|------|------------|
| 10.1 | No React code. No UI components. Backend only. |
| 10.2 | No archive search UI. Pipeline views only. |
| 10.3 | No new endpoints. Archive UI components only. |
| 10.4 | No new features. Navigation + wiring only. |
| 10.5 | No new features. Security scanning only. |
| 10.6 | No new features. Regression testing only. |
| 10.7 | No new features. Acceptance testing only. |
| 10.8 | No new features. Verification + documentation only. |

---

## 12. Out of Scope

### 12.1 Explicitly not part of Tier 10

| Item | Reason |
|------|--------|
| UI redesign or restyle | Tier 10 adds new display views. Does not change existing layout, colors, or design system. |
| Write capabilities from UI | All mutations go through WorkIntent → Process Manager → Eric Gate. UI is display-only. |
| Real-time updates (WebSocket, polling) | MCP bridge is request/response. UI queries on page load + manual refresh. |
| Mobile or responsive redesign | Existing desktop layout is preserved. |
| New authentication system | Existing CIS_API_KEY check is sufficient. |
| Dashboard widgets or home page redesign | HomePage may gain a "Pipeline Status" summary card, but is not redesigned. |
| Multi-project UI | CIS only per ADR-SEED-010. |
| Admin panel or configuration UI | Configuration is via config files and Eric Gate, not UI. |
| Dark/light theme toggle | Existing single-theme (dark) is preserved. |

---

## 13. Eric Gate Approval Required Before Implementation

### 13.1 Gating conditions

Tier 10 implementation shall not begin until ALL of:

| # | Condition | Verification |
|---|-----------|-------------|
| 1 | Tier 9 (Chroma/VDB) status = COMPLETE | `SELECT status FROM build_plan_nodes WHERE node_label = 'Tier 9 — Chroma/VDB'` |
| 2 | Eric Gate approval recorded for **this specification** | This document approved by Eric |
| 3 | Tier 8 MCP Bridge operational | MCP tools importable and returning correct data |
| 4 | Existing CIS UI operational | Flask server starts, React app builds and loads all 20 existing JSX page files (13 top-level + 7 infra sub-pages) |
| 5 | Eric explicitly issues PROCEED or IMPLEMENT for Tier 10 | Not automatic |

### 13.2 What happens after approval

1. Tier 10 status moves from PENDING → IN_PROGRESS
2. Implementation follows the build plan in §11
3. Verification gates (§10.2) run after implementation
4. Tier 10 status moves to COMPLETE only after all gates pass AND Eric approves
   the completion closeout

### 13.3 What happens if approval is withheld

- Tier 10 remains PENDING
- This specification document is revised per Eric's direction
- Resubmitted for Eric Gate review

---

## 14. Recommendation

**Approve this specification as the architecture basis for Tier 10.**

Tier 10 is the minimum viable UI surface for the capabilities built in Tier 8
(MCP Bridge) and Tier 9 (Chroma/VDB). It adds 6 read-only display views to the
existing CIS dashboard without modifying existing functionality, introducing
write capabilities, or bypassing the pipeline.

The architecture is simple: 1 new Flask blueprint (8 GET endpoints), 6 new React
page components, and 2-3 small modifications to existing wiring files. No new
dependencies, no new services, no new database tables.

The security boundary is strong: all new endpoints are GET-only, the MCP bridge
is read-only by design (Tier 8 enforcement), and the UI has zero mutation paths.
The existing WorkIntent → Process Manager → Eric Gate pipeline is not bypassed.

The build is phased into 8 small, gated nodes, each independently verifiable
before the next begins.

---

## Appendix A: Evidence References

### A.1 Current build state

```
COMMAND: sqlite3 data/cis_memory.db "SELECT node_label, status FROM build_plan_nodes WHERE node_label IN ('Tier 8 — MCP Bridge', 'Tier 9 — Chroma/VDB', 'Tier 10 — CIS UI / Custom Display Views') ORDER BY id;"
OUTPUT:
Tier 8 — MCP Bridge|COMPLETE
Tier 9 — Chroma/VDB|COMPLETE
Tier 10 — CIS UI / Custom Display Views|PENDING
```

### A.2 Existing UI inventory

**Top-level JSX page files (14 files):**

```
COMMAND: find runtime/ui/src/pages -maxdepth 1 -name "*.jsx" | sort
OUTPUT:
runtime/ui/src/pages/AssetDetail.jsx
runtime/ui/src/pages/ChatConsole.jsx
runtime/ui/src/pages/DamPage.jsx
runtime/ui/src/pages/HomePage.jsx
runtime/ui/src/pages/IdeasPage.jsx
runtime/ui/src/pages/InfraPage.jsx
runtime/ui/src/pages/IngestionPage.jsx
runtime/ui/src/pages/LearningPage.jsx
runtime/ui/src/pages/ProjectDetail.jsx
runtime/ui/src/pages/ProjectsPage.jsx
runtime/ui/src/pages/ReviewQueue.jsx
runtime/ui/src/pages/SchedulePage.jsx
runtime/ui/src/pages/SpineGraphPage.jsx
```

**Infra sub-pages (6 files):**

```
COMMAND: find runtime/ui/src/pages/infra -name "*.jsx" | sort
OUTPUT:
runtime/ui/src/pages/infra/AdvisorChat.jsx
runtime/ui/src/pages/infra/CollabTracker.jsx
runtime/ui/src/pages/infra/Hardware.jsx
runtime/ui/src/pages/infra/Models.jsx
runtime/ui/src/pages/infra/Services.jsx
runtime/ui/src/pages/infra/Software.jsx
runtime/ui/src/pages/infra/Storage.jsx
```

Total JSX page files: 20 (13 top-level + 7 infra sub-pages).

App.jsx nav routes: 11 top-level routes (Ideas, Projects, Schedule, DAM, Learn, Review, Ingestion, Map, Infra, Chat, Advisor Chat).

**HTML component files (14 files):**

```
COMMAND: find runtime/ui_components -name "*.html" | sort
OUTPUT:
runtime/ui_components/mod_agents.html
runtime/ui_components/mod_buildplan.html
runtime/ui_components/mod_dam.html
runtime/ui_components/mod_files.html
runtime/ui_components/mod_flowchart.html
runtime/ui_components/mod_ideas.html
runtime/ui_components/mod_infrastructure.html
runtime/ui_components/mod_knowledge.html
runtime/ui_components/mod_management.html
runtime/ui_components/mod_project.html
runtime/ui_components/mod_projects.html
runtime/ui_components/mod_research.html
runtime/ui_components/mod_schedule.html
runtime/ui_components/mod_session.html
```

### A.3 Existing MCP tool inventory (Tier 8 + Tier 9)

```
COMMAND: grep -c '"name": "cis_' runtime/mcp_bridge/tools.py
OUTPUT: 11
```

(9 Tier 8 tools + 2 Tier 9 tools. The `grep` pattern `"name": "cis_` matches the JSON
tool definition names, which is the authoritative count. Counting `def cis_` function
definitions is incorrect — MCP tools are registered as dict entries with `name` keys.)

### A.4 Dependency graph reference

```
From docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md:
Tier 10 — CIS UI / Custom Display Views: Gated on Tier 9 Chroma/VDB.
Custom lane displays originally proposed in Tier 2 (Kanban) were deferred
to SQLite spine (Tier 4) + CIS UI views (Tier 10).
```

---

*End of Tier 10 CIS UI / Custom Display Views Specification v1.0*
*Status: DRAFT — awaiting Eric Gate review*
*Next step: Eric reads → approves specification → Tier 10 IN_PROGRESS → IMPLEMENT*
