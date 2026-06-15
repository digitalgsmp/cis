# Tier 11 — Operator Control Layer
## Specification Document v2.0 — Reconciled

## Status: REVISED_DRAFT — Reviewer R1-R4 applied (v2.1)

This document is the reconciled Tier 11 specification incorporating:
- V4 Drafter original spec (v1.0, 2026-06-14)
- Claude Opus 4.8 review of the Reviewer
- ChatGPT 5.5 reconciliation directive
- V4 Reviewer adversarial review (O1-O5, R1-R5)
- **V4 Reviewer re-review (R1-R4, 2026-06-14):** page count corrected (18 not 25), goal_references fill strategy completed, ALLOWED_TRANSITIONS appendix fixed, dispatch_events → dispatch_log resolved

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-14 (revised)
**Supersedes:** `docs/CIS_TIER_11_UI_USABILITY_SPECIFICATION.md` v1.0 (archived)
**Reviewer edits (v1.0) preserved:** E1-E6
**New reviewer findings incorporated:** O1/R1 (schema collision), O4/R2 (import boundary), O2 (build plan gap), O3 (system overview source), R3-R5
**Claude additions:** auto-loop guard, runtime evidence requirement for 11C

---

## 0. Structure: Three Sub-Tiers

Tier 11 is broken into three ordered, independently closeable sub-tiers:

| Sub-Tier | Name | Dependencies | Write Authority | Readiness |
|----------|------|-------------|-----------------|-----------|
| **11A** | Dashboard / Navigation / System Overview | Tier 10 COMPLETE | Read-mostly (no writes) | READY |
| **11B** | Eric Gate Approval Record | 11A complete | Controlled approval write (1 POST endpoint) | READY — gated on R1 resolution |
| **11C** | Drafter→Reviewer Handoff | 11B complete, 7R runtime verified | Controlled orchestration call (1 import boundary) | BLOCKED — see §0.3 |

Each sub-tier closes out independently. 11B must not begin until 11A is COMPLETE.
11C must not begin until 11B is COMPLETE AND the 11C runtime evidence requirement
is satisfied.

### 0.1 Dependency Graph

```
Tier 10 (COMPLETE)
    │
    ▼
┌───────────┐
│   11A     │  Dashboard + Nav + System Overview
│  READY    │  Read-mostly. No writes.
└─────┬─────┘
      │ close 11A
      ▼
┌───────────┐
│   11B     │  Eric Gate Approval Record
│  READY*   │  Controlled write. Uses existing eric_gate_approvals.
└─────┬─────┘  *Gated on R1 resolution
      │ close 11B
      ▼
┌───────────┐
│   11C     │  Drafter→Reviewer Handoff
│  BLOCKED  │  Controlled orchestration import.
└───────────┘  Blocked until 7R runtime evidence + lifecycle tables exist.
```

### 0.2 What each sub-tier does NOT include

| Sub-Tier | Excluded |
|----------|----------|
| 11A | No writes. No approval. No handoff. No layout engine rewrite. |
| 11B | No orchestrator invocation. No agent dispatch. No VETO/RETURN_TO_DRAFT. No pipeline module imports. |
| 11C | No Implementer dispatch. No FINAL_DIRECTIVE execution. No state-write beyond handoff log. No multi-hop automation. |

### 0.3 11C Blocking Finding

**11C is BLOCKED** pending two conditions:

1. **Runtime evidence requirement:** The `orchestration.py` state machine defines ALLOWED_TRANSITIONS
   including DRAFT_READY → REVIEW_PENDING but the supporting tables (`lifecycle_events`, `dispatch_log`)
   do not exist in `cis_memory.db`. The state machine has never logged a transition. Before 11C
   can wire a UI button to the state machine, at least one logged DRAFT_READY → REVIEW_PENDING
   transition must be demonstrated end-to-end.

   ```
   EVIDENCE: sqlite3 data/cis_memory.db ".schema lifecycle_events"
   OUTPUT: (no table — does not exist)
   
   EVIDENCE: sqlite3 data/cis_memory.db ".schema dispatch_log"
   OUTPUT: (no table — does not exist)
   ```

2. **Table creation prerequisite:** `lifecycle_events` and `dispatch_log` tables must be created
   in `cis_memory.db` per the `orchestration.py` INSERT statements. This is a prerequisite, not
   part of Tier 11. It may be handled as a pre-11C infrastructure task or a Tier 7R implementation
   step, at Eric's discretion.

**Do not implement 11C until these conditions are resolved.**

---

## 1. Purpose

### 1.1 What Tier 11 solves

CIS has 18 routed React pages (plus 7 infra sub-components), 23 build-plan nodes (22 COMPLETE), 8 gateway endpoints,
and a working deliberation pipeline — but the operator (Eric) has no coherent
interface to understand or control any of it.

**Readability problems:**
- The HomePage shows stale aggregate counts unrelated to pipeline state.
- The 16-entry flat nav bar has no grouping. "Map," "Chat," "Ingestion" are
  meaningless labels.
- There is no system overview. Eric cannot see what CIS can do in plain language.
- Browser layout has accumulated organic cruft — overlapping elements, flat
  hierarchy, no visual distinction between functional areas.

**Control problems:**
- Every pipeline step requires Eric to manually ferry work between agents on
  separate terminal sessions. The Drafter doesn't know the Reviewer exists.
  Eric is the transport layer — copying output, opening terminals, pasting text
  between gateway profiles (ports 8642-8646).
- To approve a Drafter proposal, Eric must open a terminal, run the Reviewer
  manually, read the response, decide, then manually record the decision.
  There is no button. No spine record is written by a UI action.
- The `eric_gate_approvals` table exists with a full Component 3 schema but
  has zero rows. The approval mechanism was designed but never wired to the UI.

Tier 11 addresses these in three ordered phases: visibility first (11A),
approval recording second (11B), and the single safest handoff third (11C).

### 1.2 Core capability

> **An operator control layer that provides: (A) a live dashboard with
> functional nav groups, system overview in operator language, and layout
> repair; (B) a controlled Eric Gate APPROVE action that writes to the
> existing approval table with idempotency protection; and (C) a single
> safe non-execution handoff from Drafter to Reviewer using the existing
> spine transport, with auto-loop guard and git-HEAD consistency check.**

### 1.3 What changes for the operator (Eric)

| Before Tier 11 | After 11A | After 11B | After 11C |
|----------------|-----------|-----------|-----------|
| Stale HomePage with static counts | Live dashboard with pipeline phase, blockers, capabilities | Same + Eric Gate action area with APPROVE button | Same + handoff status |
| 16 flat nav entries | 4-group nav: Monitor, Work, Knowledge, Infra | Same | Same |
| No system understanding | System Overview in operator language | Same | Same |
| Browser layout cruft | Modest repair: spacing, hierarchy, non-overlap | Same | Same |
| Must open terminal to approve | Must open terminal | Click APPROVE on dashboard; spine record written | Click APPROVE; handoff queued |
| Copy Drafter output to Reviewer terminal | Same manual process | Same manual process | Click triggers Drafter→Reviewer handoff |

### 1.4 Scope boundaries

**In scope (three sub-tiers):**
- 11A: Dashboard, nav groups, system overview, modest layout repair
- 11B: Single APPROVE/PASS endpoint using existing `eric_gate_approvals` schema
- 11C: Drafter→Reviewer handoff via existing spine transport

**Out of scope (entire Tier 11):**
- Implementer dispatch
- FINAL_DIRECTIVE generation or execution
- VETO, RETURN_TO_DRAFT (deferred to full Component 3)
- Automated orchestrator chain beyond Drafter→Reviewer
- Multi-hop automation
- Gateway-to-gateway handoff beyond Drafter→Reviewer
- Tier 12 Unified Memory (explicitly deferred until 11A/11B/11C complete or paused by Eric)

---

## 2. 11A — Dashboard, Navigation, System Overview

### 2.1 What 11A delivers

11A replaces the stale HomePage with a live dashboard, restructures the nav bar
into functional groups, adds a System Overview page, and applies modest layout
repair. It is read-mostly — no writes, no approval, no handoff.

#### 2.1.1 Dashboard sections

| Section | Data Source | Description |
|---------|-------------|-------------|
| Current Phase | `GET /api/pipeline/status` (Tier 10) | Current build phase, next tier, next action |
| Active Blockers | SQLite `active_blockers` (column `description`, per E2) | Blocker ID and description |
| Recent Pipeline Runs | `GET /api/pipeline/runs?limit=5` (Tier 10) | Last 5 workflow_runs with status |
| Completed Capabilities | `build_plan_nodes` WHERE status='COMPLETE' (per E6) | Live tier labels and statuses from spine |
| Quick Links | Static | Links to Monitor group pages |

#### 2.1.2 System Overview

A new section or page that explains CIS in operator language. Capabilities are
sourced live from `build_plan_nodes` (status from spine). Operator-facing
descriptions are sourced from a static config file:

**Source of truth:** `runtime/api/system_overview.yaml`
- Keyed by `node_label` (matching `build_plan_nodes.node_label`)
- Contains: `operator_description` (1-2 sentences in plain language),
  `capability_area` (Monitor/Work/Knowledge/Infra), `depends_on` (list)
- Loaded by `dashboard_api.py` at startup, cached in memory
- If a node_label has no entry, the dashboard shows the raw node_label
- Maintained by hand; updated when new tiers are added

Example:

```yaml
- node_label: "Tier 0 — Deliberation Engine"
  operator_description: "Multi-model debate system. Drafter writes proposals, Reviewer checks them. Both run on separate AI models with different training data so they catch each other's blind spots."
  capability_area: "Monitor"

- node_label: "Tier 10 — CIS UI / Custom Display Views"
  operator_description: "Pipeline visibility pages. Shows build plan status, recent runs, Eric Gate approvals, and archive search — all in the browser instead of terminal commands."
  capability_area: "Monitor"
```

This is pragmatic per Reviewer R3: static config avoids spine schema changes
while keeping descriptions maintainable.

#### 2.1.3 Layout repair — modest scope

11A includes modest layout repair for readability. This is NOT a CSS redesign.
Existing dark theme and Share Tech Mono typography are preserved.

Scope of repair:
- Ensure nav groups render without horizontal overflow at standard desktop width
- Add spacing between dashboard sections (cards should not touch)
- Ensure the top bar, content area, and status bar form a clear visual hierarchy
- Fix any known overlapping elements in the existing 18 routed pages
- Add section headers with consistent styling to the dashboard

Not in scope:
- CSS framework replacement
- Responsive/mobile design
- Dark/light theme toggle
- Font changes
- Rewriting existing page CSS

#### 2.1.4 Navigation restructuring (from v1.0, unchanged)

Four nav groups replace the flat 16-entry nav bar:

| Group | Pages | Count |
|-------|-------|-------|
| Monitor | Pipeline, Eric Gate, Archive, Sessions, Decisions | 5 |
| Work | Ideas, Projects, Schedule, DAM, Advisor Chat | 5 |
| Knowledge | Learn, Review | 2 |
| Infra | Infra (with sub-tabs) | 1 |

Pages removed from nav but accessible via direct URL (per E5):

| Page | Route | Access |
|------|-------|--------|
| SpineGraph (Map) | `/spines` | Direct URL |
| ChatConsole (Chat) | `/chat` | Direct URL |
| Ingestion | `/ingest` | Direct URL |
| InfraPage CollabTracker | `/infra?tab=collab` | Direct URL |

Advisor Chat promoted from Infra sub-pages to Work nav (D4).

#### 2.1.5 Files for 11A

Created (3):
- `runtime/ui/src/pages/DashboardPage.jsx`
- `runtime/ui/src/components/NavGroup.jsx`
- `runtime/api/dashboard_api.py` (GET endpoint only)
- `runtime/api/system_overview.yaml` (static config)

Modified (3):
- `runtime/ui/src/App.jsx` — nav restructure, DashboardPage route
- `runtime/ui/src/api.js` — add dashboardFull()
- `runtime/app.py` — register dashboard_api blueprint

Archived (1):
- `runtime/ui/src/pages/HomePage.jsx` → `runtime/ui_archive/HomePage.jsx`

No new database tables in 11A.

---

## 3. 11B — Eric Gate Approval Record

### 3.1 Schema collision resolution (R1)

**Finding (Reviewer O1):** The `eric_gate_approvals` table already exists in
`cis_memory.db` with the full Component 3 schema:

```
EVIDENCE: sqlite3 data/cis_memory.db ".schema eric_gate_approvals"
OUTPUT:
CREATE TABLE eric_gate_approvals (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('APPROVE', 'VETO', 'RETURN_TO_DRAFT')),
    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL DEFAULT 'Eric',
    goal_reference_id INTEGER NOT NULL,
    briefing_hash TEXT NOT NULL,
    briefing_json TEXT NOT NULL,
    drift_snapshot_json TEXT NOT NULL,
    decision_trail_snapshot_json TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    supersedes_approval_id TEXT,
    rationale TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id),
    FOREIGN KEY (goal_reference_id) REFERENCES goal_references(id),
    FOREIGN KEY (supersedes_approval_id) REFERENCES eric_gate_approvals(id)
);
```

The table has 0 rows. It has never been used.

**Resolution:** 11B must INSERT into this existing schema. The Tier 11 spec's
proposed `CREATE TABLE IF NOT EXISTS` approach is withdrawn. No new table is
created. No migration is performed. The existing table is the target.

### 3.2 Required fields — fill strategy

The existing schema has 14 columns. The 11B APPROVE endpoint must populate all
NOT NULL columns. Strategy for each:

| Column | Source | Strategy |
|--------|--------|----------|
| `id` | Generated | `uuid.uuid4()` |
| `workflow_run_id` | Request body | Provided by UI from the run being approved |
| `decision` | Fixed | `'APPROVE'` (only allowed value for 11B) |
| `decided_at` | Generated | `datetime.utcnow().isoformat()` |
| `decided_by` | Default | `'Eric'` (column default) |
| `goal_reference_id` | Spine lookup | Query `goal_references` for the row matching `workflow_run_id` from the deliberation that produced the Drafter output. **If none exists, reject with HTTP 409 and message: "No goal reference exists for this run. Approval cannot proceed — upstream goal formation did not run." Zero rows written to either table.** This is a deterministic gate: the NOT NULL foreign key on `eric_gate_approvals.goal_reference_id` asserts that no approval may advance a goal that was never established. Manufacturing a placeholder defeats the gate and writes a provenance-free governance object into the spine — prohibited. |
| `briefing_hash` | Generated | SHA-256 of `briefing_json` |
| `briefing_json` | Request or generated | If the Drafter output includes a FINAL_JSON block, serialize it. Otherwise `"{}"` with a note. |
| `drift_snapshot_json` | Generated | `{"git_head": "<HEAD hash>", "dirty_files": [...], "captured_at": "<ISO timestamp>"}` |
| `decision_trail_snapshot_json` | Spine read | Serialize the `deliberation_rounds` rows for this `workflow_run_id`. Read-only query. |
| `is_current` | Fixed | `1`. If a prior approval exists for this `workflow_run_id`, set the prior row's `is_current` to `0` before inserting. |
| `supersedes_approval_id` | Computed | If a prior approval exists, set to that row's `id`. Otherwise NULL. |
| `rationale` | Request body | Optional comment from Eric (e.g., "Spec looks good, pass to Implementer") |
| `created_at` | Generated | `datetime.utcnow().isoformat()` |

### 3.3 Idempotency and concurrency

**Duplicate protection:** If an approval already exists for `workflow_run_id`
with `is_current = 1` and `decision = 'APPROVE'`, the endpoint returns the
existing approval record with HTTP 200 and a `"status": "already_approved"`
field. No duplicate row is inserted.

**Concurrency protection:** Two rapid clicks produce one approval. This is
enforced by the existing UNIQUE partial index on `eric_gate_approvals`:

```sql
CREATE UNIQUE INDEX idx_eric_gate_one_current_decision
    ON eric_gate_approvals(workflow_run_id)
    WHERE is_current = 1;
```

A second INSERT with the same `workflow_run_id` and `is_current = 1` will
fail with a UNIQUE constraint violation. The endpoint catches this and returns
the existing approval.

If Eric re-approves a previously approved run (e.g., after revisions), the
endpoint sets the prior row's `is_current = 0`, sets `supersedes_approval_id`
on the new row, and inserts with `is_current = 1`. This maintains a full
approval history while ensuring only one current approval per run.

### 3.4 Endpoint specification

| Field | Value |
|-------|-------|
| Method | POST |
| Path | `/api/dashboard/approve` |
| Auth | CIS_API_KEY (existing before_request hook) |

**Request body:**

```json
{
  "run_id": "run-88032ce506724",
  "comment": "Spec looks good, pass to Implementer"
}
```

**Response (200, success):**

```json
{
  "status": "approved",
  "approval_id": "b4f3c9e1-...",
  "run_id": "run-88032ce506724",
  "decision": "APPROVE",
  "recorded_at": "2026-06-14T18:00:00Z",
  "next_action": "Orchestrator can now proceed with --run-id run-88032ce506724 for Drafter→Reviewer handoff."
}
```

**Response (200, already approved):**

```json
{
  "status": "already_approved",
  "approval_id": "b4f3c9e1-...",
  "run_id": "run-88032ce506724",
  "message": "This run was already approved at 2026-06-14T17:55:00Z."
}
```

**Response (400, invalid):**

```json
{
  "status": "rejected",
  "error": "Only APPROVE is supported in Tier 11B. VETO and RETURN_TO_DRAFT are not implemented."
}
```

**Response (409, no goal reference):**

```json
{
  "status": "rejected",
  "error": "No goal reference exists for this run. Approval cannot proceed — upstream goal formation did not run."
}
```

### 3.5 What 11B does NOT do

Per the controlled write boundary:
- No orchestrator invocation. Approval writes a record. It does not call
  `orchestrator.py` or `orchestration.py`.
- No agent dispatch. No HTTP call to any gateway.
- No VETO or RETURN_TO_DRAFT. Server-side validation rejects non-APPROVE values.
- No pipeline module imports. `dashboard_api.py` does not import
  `process_manager`, `approval_gate`, `dispatch`, or `classifier`.
- No new tables. Uses existing `eric_gate_approvals`.

### 3.6 Security boundary (11B)

| Layer | Mechanism |
|-------|-----------|
| Endpoint | Single POST `/api/dashboard/approve`. All other routes GET. |
| Imports | No `orchestration`, `orchestrator`, `process_manager`, `approval_gate`, `dispatch`, `classifier` |
| SQLite | INSERT only into `eric_gate_approvals`. UPDATE only on `is_current` for idempotency. SELECT on `goal_references`, `deliberation_rounds`, `workflow_runs` for field population. **No INSERT into `goal_references` — the goal must already exist.** |
| Validation | `decision` must be `'APPROVE'`. `run_id` must exist in `workflow_runs`. |

---

## 4. 11C — Drafter→Reviewer Handoff

### 4.1 What 11C delivers

A single safe handoff: when Eric clicks APPROVE in 11B, the UI offers a
"Pass to Reviewer" action that transitions the workflow from DRAFT_READY
to REVIEW_PENDING and invokes the Reviewer gateway with the Drafter's output.

**11C is BLOCKED** until the conditions in §0.3 are resolved.

### 4.2 Controlled import boundary (R2/R4)

11C crosses the "no pipeline module imports" boundary that 11A and 11B enforce.
This crossing is allowed ONLY for the specific Drafter→Reviewer handoff.

**Allowed imports in 11C:**

```python
# Allowed: orchestration state machine (transition logging)
from api.orchestration import transition_state, create_dispatch, complete_dispatch

# Allowed: HTTP client for Reviewer gateway invocation
import requests

# Allowed: git HEAD capture
import subprocess  # for `git rev-parse HEAD`
```

**Prohibited imports in 11C:**

```python
# PROHIBITED: process manager, dispatch to execution lanes
from tier7r.process_manager import ...   # BLOCKED
from tier7r.approval_gate import ...      # BLOCKED

# PROHIBITED: FINAL_DIRECTIVE execution
from api.orchestration import freeze_directive  # BLOCKED — directive preparation only
```

### 4.3 Handoff mechanism

The handoff uses the existing spine transport and `orchestrator.py`. It does
NOT create a new parallel workflow system.

**Handoff flow:**

1. Eric clicks "Pass to Reviewer" on the dashboard (only visible after 11B APPROVE).
2. UI sends POST to `/api/dashboard/handoff` with `{"run_id": "..."}`.
3. Backend captures `git rev-parse HEAD` at handoff time.
4. Backend reads the Drafter output from `deliberation_rounds` for this run.
5. Backend validates the state: `workflow_runs` status must allow handoff.
6. Backend calls `transition_state(proposal_id, ..., 'DRAFT_READY', 'REVIEW_PENDING', ...)`
   to log the transition in `lifecycle_events`.
7. Backend calls `create_dispatch(proposal_id, 'DRAFTER', 'REVIEWER', ...)` to log
   the dispatch in `dispatch_log`.
8. Backend invokes the Reviewer gateway via `orchestrator.run_deliberation()` with
   `--run-id` and the Drafter output as context.
9. Backend logs the response via `complete_dispatch()`.
10. Backend returns status to UI: handoff queued/accepted, Reviewer response pending,
    or error with raw evidence.

**Handoff table (R4):** The handoff is tracked through the existing `lifecycle_events`
and `dispatch_log` tables in `cis_memory.db` — no new handoff_queue table is created.
The `workflow_runs` state machine is the handoff mechanism. This follows Reviewer R5:
"the state machine already has DRAFT_READY → REVIEW_PENDING. Handoff may be as simple
as transitioning state in the existing spine rather than creating a new queue table."

### 4.4 Safety predicates (deterministic)

Before executing a handoff, the backend validates ALL of:

1. **Target lane has no execution authority.** Reviewer (`hermes-r1`, port 8643)
   has no implementer role per ADR-SEED-004. This is a static check — the handoff
   endpoint only allows target='REVIEWER'.

2. **Logged transition exists.** `transition_state()` must succeed and return a
   row ID in `lifecycle_events` before the gateway is invoked.

3. **Idempotency check passes.** If a REVIEW_PENDING or REVIEWING transition
   already exists for this run, the handoff is rejected with "already in progress."

4. **Git HEAD matches.** The git HEAD captured at handoff time is logged. If a
   subsequent handoff attempt has a different HEAD than the logged one, it is
   rejected — the codebase changed between approval and handoff. This prevents
   handoff on stale state.

5. **Round/loop guard passes.** The handoff may perform only ONE hop (DRAFT_READY
   → REVIEW_PENDING). It does not auto-advance beyond that. The orchestrator's
   `max_rounds` config controls deliberation rounds within the Reviewer gateway,
   but the handoff endpoint does not loop.

### 4.5 Auto-loop guard (Claude addition)

> Drafter→Reviewer automation may perform only one hop per Eric click.
> OBJECTIONS must not automatically trigger a second Drafter→Reviewer loop.
> Any multi-round loop must require explicit orchestrator max-round
> configuration and visible UI status.

Implementation:
- The handoff endpoint transitions DRAFT_READY → REVIEW_PENDING exactly once.
- If the Reviewer returns OBJECTIONS/REVISE_REQUESTED, the handoff endpoint
  does NOT automatically re-invoke the Drafter. It surfaces the Reviewer's
  response in the UI with status "Reviewer requests revisions. Eric must
  manually decide next action."
- Multi-round deliberation (Drafter↔Reviewer loops) requires the full
  orchestrator (`--run-id`, `--max-rounds`), which is a separate invocation
  and not part of the 11C handoff endpoint.

### 4.6 Error handling

Failed handoff writes raw error evidence and moves to BLOCKED or DEAD_LETTER:

- If `transition_state()` fails: log the error, return 500 with the state
  machine error message. Do not invoke the Reviewer.
- If the Reviewer gateway returns 4xx/5xx: log via `fail_dispatch()`, capture
  the raw HTTP response, return error to UI.
- If the Reviewer gateway times out: log via `fail_dispatch()`, return timeout
  error.
- In all failure cases: write raw error evidence to `dispatch_log` with
  event_type='ERROR'. The UI shows the error and suggests manual intervention.

### 4.7 What 11C does NOT do

- No Implementer dispatch. The handoff stops at Reviewer.
- No FINAL_DIRECTIVE generation or execution.
- No state-write beyond the logged transition and dispatch records.
- No export or verification automation.
- No multi-hop automation (no Drafter→Reviewer→Drafter loops).
- No VETO/RETURN_TO_DRAFT (those are 11B-scope or deferred).

### 4.8 Security boundary (11C)

| Layer | Mechanism |
|-------|-----------|
| Endpoint | Single POST `/api/dashboard/handoff`. Only target='REVIEWER' allowed. |
| Imports | `api.orchestration` (transition_state, create_dispatch, complete_dispatch, fail_dispatch). `requests`. `subprocess` (git). |
| Prohibited imports | `tier7r.process_manager`, `tier7r.approval_gate`, `api.orchestration.freeze_directive` |
| State machine | Only DRAFT_READY → REVIEW_PENDING transition allowed from this endpoint |
| Loop guard | One hop per click. OBJECTIONS do not auto-loop. |
| Git HEAD guard | Handoff rejected if HEAD changed since logged transition |

---

## 5. Tier 7R Dependency Analysis

### 5.1 What exists

```
EVIDENCE: find runtime -iname '*process*manager*' -o -iname '*workintent*' -o -iname '*approval*gate*' -o -iname '*dead*letter*' -o -iname '*orchestrat*'
OUTPUT:
runtime/tier7r/process_manager.py
runtime/tier7r/approval_gate.py
runtime/tier7r/dead_letter.py
runtime/api/orchestration.py
runtime/orchestrator.py
```

```
EVIDENCE: grep -c "ALLOWED_TRANSITIONS" runtime/api/orchestration.py
OUTPUT: 2
```

The state machine is defined. `orchestrator.py` calls gateways via HTTP.
`orchestration.py` defines ALLOWED_TRANSITIONS including the full pipeline:
DRAFT_READY → REVIEW_PENDING → REVIEWING → REVIEW_COMPLETE → ERIC_APPROVAL_GATE
→ DIRECTIVE_DRAFTING → DIRECTIVE_READY → EXECUTING.

### 5.2 What is missing (blocks 11C)

```
EVIDENCE: sqlite3 data/cis_memory.db ".schema lifecycle_events"
OUTPUT: (no output — table does not exist)

EVIDENCE: sqlite3 data/cis_memory.db ".schema dispatch_log"
OUTPUT: (no output — table does not exist)
```

The `lifecycle_events` and `dispatch_log` tables do not exist in the spine.
`orchestration.py` INSERTs into them but they were never created. The state
machine cannot log a transition without these tables.

### 5.3 Assessment

| Component | Status | Evidence |
|-----------|--------|----------|
| State machine (ALLOWED_TRANSITIONS) | Defined | `orchestration.py` lines 21-81 |
| Gateway invocation (call_agent) | Defined | `orchestrator.py` line 78-108 |
| lifecycle_events table | Missing | `.schema` returns no output |
| dispatch_log table | Missing | `.schema` returns no output |
| eric_gate_approvals table | Exists, 0 rows | `.schema` returns full Component 3 schema |
| Test mode (--test) | Defined | `orchestrator.py` line 536-555 |
| End-to-end handoff logged | Not demonstrated | No rows in lifecycle_events or dispatch_log |

**FINAL: 11C is BLOCKED.** The state machine is spec-complete but not runtime-wired.
Before 11C can proceed, the lifecycle_events and dispatch_log tables must be created
AND at least one DRAFT_READY → REVIEW_PENDING transition must be demonstrated
end-to-end with a logged event.

---

## 6. Acceptance Criteria

### 6.1 11A acceptance tests (A1-A10, from v1.0 + new)

| # | Test | Verification |
|---|------|-------------|
| A1 | Dashboard loads as `/` | Browser screenshot vs. spine data |
| A2 | Current phase matches spine | Compare against `/api/pipeline/status` |
| A3 | Active blockers display (column `description`, per E2) | Compare against `SELECT id, description FROM active_blockers` |
| A4 | Recent runs list | Compare against `/api/pipeline/runs?limit=5` |
| A5 | Eric Gate status | Compare against `/api/pipeline/eric-gate` |
| A6 | Capabilities from spine (per E6) | Compare against `SELECT node_label, status FROM build_plan_nodes WHERE status='COMPLETE'` |
| A7 | Nav shows 4 groups | Visual inspection + count per group |
| A8 | Removed-from-nav pages accessible (per E5) | Direct URL: `/spines`, `/chat`, `/ingest`, `/infra?tab=collab` |
| A9 | Advisor Chat in Work nav (D4) | Visual inspection |
| A10 | All 18 routed pages render. 7 infra sub-components tested via InfraPage route. | Browser console regression sweep |
| A11 | System Overview exists | Page or section showing capabilities in operator language |
| A12 | System Overview sourced from system_overview.yaml | Verify descriptions match YAML, not hardcoded |
| A13 | Dashboard layout: no element overlap at 1280px+ width | Browser screenshot at standard desktop |
| A14 | HomePage archived | `! test -f runtime/ui/src/pages/HomePage.jsx` |
| A15 | HomePage in archive | `test -f runtime/ui_archive/HomePage.jsx` |

### 6.2 11B acceptance tests (B1-B11)

| # | Test | Verification |
|---|------|-------------|
| B1 | APPROVE writes to existing eric_gate_approvals schema | `SELECT * FROM eric_gate_approvals WHERE workflow_run_id = ?` returns row with all 14 columns populated |
| B2 | goal_reference_id populated | Column is NOT NULL, value references valid goal_references row |
| B3 | briefing_json contains Drafter FINAL_JSON or fallback | Column is NOT NULL, valid JSON |
| B4 | drift_snapshot_json contains git HEAD | `json_extract(drift_snapshot_json, '$.git_head')` returns 40-char hash |
| B5 | decision_trail_snapshot_json contains deliberation_rounds | Valid JSON array matching `deliberation_rounds` rows |
| B6 | Duplicate approval is idempotent | Second POST with same run_id returns `"status": "already_approved"`, no duplicate row |
| B7 | Concurrent double-click creates one current approval | UNIQUE partial index enforced; second INSERT fails gracefully |
| B8 | APPROVE with no goal reference returns 409 | POST with a run_id that has no goal_references row returns 409. Verify zero rows written to both eric_gate_approvals and goal_references. |
| B9 | VETO and RETURN_TO_DRAFT rejected | POST with `"decision": "VETO"` returns 400 |
| B10 | No pipeline/orchestrator imports in dashboard_api.py | `grep -E 'orchestrat|process_manager|dispatch' runtime/api/dashboard_api.py` returns empty |
| B11 | UI confirms approval and shows next manual action | Response rendered on dashboard with next-action text |

### 6.3 11C acceptance tests (C1-C10)

**Only applicable when 11C is unblocked.**

| # | Test | Verification |
|---|------|-------------|
| C1 | Drafter→Reviewer handoff creates logged transition | `lifecycle_events` row with from_state='DRAFT_READY', to_state='REVIEW_PENDING' |
| C2 | Reviewer gateway receives the packet | `dispatch_log` row with target_agent='REVIEWER', current_status='SUCCESS' |
| C3 | Handoff records git HEAD | `dispatch_log` row or handoff metadata contains git HEAD at handoff time |
| C4 | Handoff rejects stale HEAD | If git HEAD changed since approval, handoff returns error |
| C5 | OBJECTIONS does not auto-loop | Reviewer response with OBJECTIONS → UI shows status, no second Drafter invocation |
| C6 | Failed handoff writes raw evidence | `dispatch_log` row with event_type='ERROR', raw error in evidence field |
| C7 | No Implementer dispatch occurs | No transition beyond REVIEW_PENDING from this endpoint |
| C8 | No FINAL_DIRECTIVE execution occurs | `freeze_directive` not called |
| C9 | No state-write beyond transition/dispatch log | Only lifecycle_events and dispatch_log INSERTs |
| C10 | One hop per click | Only DRAFT_READY → REVIEW_PENDING; no auto-advance to REVIEWING |

---

## 7. Safety Gates

### 7.1 11A gates

| Gate | Type | Purpose |
|------|------|---------|
| `gate_11a_no_writes.sh` | Security | Zero POST/PUT/PATCH/DELETE in 11A endpoints |
| `gate_11a_regression_pages.sh` | Functional | All 18 routed pages render |
| `gate_11a_removed_nav.sh` | Functional | 4 removed-from-nav pages reachable by direct URL |
| `gate_11a_system_overview.sh` | Functional | System Overview renders, descriptions match YAML |
| `gate_11a_layout_no_overlap.sh` | Functional | No element overlap at standard desktop width |
| `gate_11a_nav_groups.sh` | Functional | 4-group nav with correct item counts |

### 7.2 11B gates

| Gate | Type | Purpose |
|------|------|---------|
| `gate_11b_approve_schema.sh` | Functional | INSERT populates all 14 columns of existing eric_gate_approvals |
| `gate_11b_idempotency.sh` | Functional | Duplicate approval returns already_approved |
| `gate_11b_concurrency.sh` | Functional | UNIQUE partial index prevents duplicate current approvals |
| `gate_11b_no_goal_reference_create.sh` | Security | 11B endpoint code contains no INSERT into goal_references. Approval with no goal reference returns 409. |
| `gate_11b_no_veto.sh` | Security | VETO/RETURN_TO_DRAFT rejected with 400 |
| `gate_11b_no_orchestrator_import.sh` | Security | No orchestrator/orchestration imports in 11B code |
| `gate_11b_one_post_only.sh` | Security | Exactly one POST endpoint in dashboard_api.py |

### 7.3 11C gates (when unblocked)

| Gate | Type | Purpose |
|------|------|---------|
| `gate_11c_transition_logged.sh` | Functional | lifecycle_events row for DRAFT_READY → REVIEW_PENDING |
| `gate_11c_git_head.sh` | Functional | git HEAD logged and validated |
| `gate_11c_no_auto_loop.sh` | Safety | OBJECTIONS do not trigger auto-loop |
| `gate_11c_no_dispatch.sh` | Safety | No implementer dispatch from handoff endpoint |
| `gate_11c_no_directive.sh` | Safety | freeze_directive not called |
| `gate_11c_one_hop.sh` | Safety | Only DRAFT_READY → REVIEW_PENDING; no auto-advance |

---

## 8. Out of Scope / Deferred

| Item | Reason |
|------|--------|
| Implementer dispatch | Explicitly deferred. Requires separate Eric approval timestamps: one for packet preparation, one for dispatch. |
| FINAL_DIRECTIVE generation | Deferred. Packet preparation and implementation dispatch are two separate logged events, not in Tier 11. |
| VETO, RETURN_TO_DRAFT | Deferred to full Component 3 implementation. 11B only supports APPROVE. |
| Automated orchestrator chain beyond Drafter→Reviewer | Deferred. 11C is the single safest hop. Full chain requires Tier 7R implementation beyond spec level. |
| Multi-hop deliberation loops | Deferred. Requires explicit orchestrator config. 11C performs one hop only. |
| Tier 12 — Unified Memory | Deferred until 11A/11B/11C are complete or explicitly paused by Eric. |
| Pass 5 — Project Promotion | Deferred per existing blocking list. |

---

## 9. Eric Gate Approval Required

### 9.1 Gating conditions

Implementation of each sub-tier shall not begin until:

| # | Condition | Applies To |
|---|-----------|-----------|
| 1 | Tier 10 COMPLETE | 11A, 11B, 11C |
| 2 | Eric Gate approval of this revised specification | 11A, 11B, 11C |
| 3 | 11A COMPLETE with all A1-A15 gates passing | 11B |
| 4 | 11B COMPLETE with all B1-B10 gates passing | 11C |
| 5 | lifecycle_events and dispatch_log tables created in cis_memory.db | 11C |
| 6 | At least one logged DRAFT_READY → REVIEW_PENDING transition demonstrated | 11C |
| 7 | Eric explicitly issues PROCEED for each sub-tier | 11A, 11B, 11C |

### 9.2 What happens after approval

1. 11A moves to IN_PROGRESS → implemented → gates pass → COMPLETE
2. 11B moves to IN_PROGRESS → implemented → gates pass → COMPLETE
3. 11C preconditions resolved → 11C moves to IN_PROGRESS → implemented → gates pass → COMPLETE
4. Each sub-tier closeout requires Eric Gate approval

---

## Appendix A: Evidence References

### A.1 eric_gate_approvals schema (live)

```
COMMAND: sqlite3 data/cis_memory.db ".schema eric_gate_approvals"
OUTPUT: (full Component 3 schema — 14 columns, UNIQUE partial index on is_current=1)
Rows: 0 (table exists, never used)
```

### A.2 Orchestration state machine (defined)

```
COMMAND: grep -c "^ALLOWED_TRANSITIONS" runtime/api/orchestration.py
OUTPUT: 1

COMMAND: grep -c "ALLOWED_TRANSITIONS" runtime/api/orchestration.py
OUTPUT: 3
  (The dict definition, a docstring reference, and the validation check.)

COMMAND: grep "DRAFT_READY.*REVIEW_PENDING\|REVIEW_COMPLETE.*ERIC_APPROVAL" runtime/api/orchestration.py
OUTPUT:
    ('DRAFT_READY',         'REVIEW_PENDING'),
    ('REVIEW_COMPLETE',     'ERIC_APPROVAL_GATE'),
```

### A.3 Missing tables (blocks 11C)

```
COMMAND: sqlite3 data/cis_memory.db ".schema lifecycle_events"
OUTPUT: (no output — table does not exist)

COMMAND: sqlite3 data/cis_memory.db ".schema dispatch_log"
OUTPUT: (no output — table does not exist)
```

### A.4 Gateway invocation (exists)

```
COMMAND: grep "def call_agent\|requests.post" runtime/orchestrator.py
OUTPUT:
def call_agent(agent_name, content, thread_id, config):
    response = requests.post(
```

### A.5 Test mode (exists)

```
COMMAND: grep "\-\-test" runtime/orchestrator.py
OUTPUT:
        "--test", "-t", action="store_true",
        help="Short test mode: prepends test prefix and enables truncated output"
```

### A.6 Build plan gap

```
COMMAND: grep -c "Tier 11" docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md
OUTPUT: 0
```

Build plan ends at Tier 9. Tiers 10 and 11 are organic additions beyond the plan.
This is acknowledged per Reviewer O2.

---

*End of Tier 11 Operator Control Layer Specification v2.0*
**Status: REVISED_DRAFT v2.1 — Reviewer R1-R4 applied. Awaiting Eric Gate review.**
*Next step: Eric Gate review → Eric approves → 11A IN_PROGRESS*

## FINAL: Proceed / Blocked

| Sub-Tier | Status | Reason |
|----------|--------|--------|
| **11A** | **READY** for Eric Gate review | No blockers. Read-mostly. All design decisions resolved. |
| **11B** | **READY** for Eric Gate review | R1 resolved (existing schema, fill strategy defined). R2 boundary defined (no pipeline imports in 11B). |
| **11C** | **BLOCKED** | `lifecycle_events` and `dispatch_log` tables do not exist in `cis_memory.db`. State machine cannot log transitions. Runtime evidence of end-to-end DRAFT_READY → REVIEW_PENDING required before 11C authorization. |

**Full spec is ready for Eric Gate review of 11A and 11B.** 11C is documented
but blocked pending infrastructure prerequisites.
