# Tier 8 — MCP Bridge Specification
## Specification Document v1.0

## Eric Gate Status: PENDING_APPROVAL

This document defines the architectural direction for Tier 8. It is **NOT** an
implementation directive. No code shall be written, no spine rows modified, and no
files staged under this document alone. Implementation proceeds only after Eric
Gate approval is recorded.

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-12
**Revised:** 2026-06-13 — Adversarial review by V4 Reviewer (deepseek-v4-pro). Corrections: O1 (mcp venv path), O2 (decisions→project_decisions), O3 (FTS5 migration added), O4 (CLOSED→DECIDED filter), R5 (Appendix A.5 verified).
**Status:** REVISED_DRAFT — corrections applied, awaiting Eric Gate review
**Gating dependency:** Tier 7R.4 (Process Manager) must be COMPLETE per §11.5 of Tier 7R spec

---

## 1. Purpose

### 1.1 What Tier 8 solves

Currently, Hermes Agent profiles (Drafter, Reviewer, Implementer, Research) cannot
programmatically query the CIS spine. Every session must load the full AGENTS.md
context (~400 lines) before it knows the current build phase, next actions, recent
pipeline runs, and open decisions. This is wasteful and fragile:

- AGENTS.md is a static snapshot generated at closeout. Between closeouts, it
  becomes stale — profile sessions operate on outdated context.
- The full AGENTS.md must be regenerated for any state change, consuming tokens
  and adding latency.
- Profiles cannot ask targeted questions like "what is the status of build_plan_node
  X" or "what are the open questions about Y" without loading the entire document.

Tier 8 builds an MCP (Model Context Protocol) bridge that exposes the CIS spine as
query-only MCP tools. Hermes profiles connect to the MCP bridge at session start and
gain query access to current state without full AGENTS.md regeneration. The bridge
is read-only and approval-gated — it never writes to the spine and never bypasses
the Eric Gate.

### 1.2 Core capability

> **A local MCP server that exposes read-only spine queries to authorized Hermes
> profiles, feeding targeted context on demand instead of requiring full AGENTS.md
> regeneration on every state change.**

### 1.3 What changes for the operator (Eric)

| Before Tier 8 | After Tier 8 |
|---------------|--------------|
| AGENTS.md regenerated at every closeout (~400 lines, full snapshot) | AGENTS.md remains the startup context. Between closeouts, profiles query the spine directly for current state. |
| Profile asks "what is the next action?" — model guesses from stale AGENTS.md | Profile calls mcp_cis_get_next_actions() — returns live spine rows |
| Profile needs to know if a node is COMPLETE — reads old AGENTS.md | Profile calls mcp_cis_get_build_status(node_label) — returns current spine row |
| Cross-session context limited to what AGENTS.md captured | Profiles can query prior workflow_runs, deliberation_rounds, and decisions on demand |

---

## 2. Access Boundaries

### 2.1 What MCP tools SHALL expose (read-only)

| Tool Name | Returns | Purpose |
|-----------|---------|---------|
| `cis_get_current_phase` | Current build tier, status, next actions from build_plan_nodes | Fast startup orientation |
| `cis_get_build_status` | Single node by label: status, evidence_path, commit_hash, completed_at | Targeted build phase query |
| `cis_get_next_actions` | All nodes where status = PENDING and dependencies are COMPLETE | What to work on next |
| `cis_get_recent_runs` | Last N workflow_runs with result, rounds_completed, created_at | Recent pipeline activity |
| `cis_get_run_detail` | Single workflow_run + its deliberation_rounds | Deep inspection of a pipeline run |
| `cis_get_open_decisions` | All rows from project_decisions table where status = 'DECIDED' AND superseded_by IS NULL | Active, non-superseded decisions (ADR-SEED-*) |
| `cis_get_open_questions` | All rows from open_questions table | Outstanding unknowns |
| `cis_get_eric_gate_status` | Pending approvals from eric_gate_approvals | What's waiting for Eric |
| `cis_search_sessions` | FTS5 search across session_closeouts (requires schema migration — see §5.3) | Archive discovery — "have we solved this before" |

### 2.2 What MCP tools SHALL NOT expose

| Prohibited | Reason |
|------------|--------|
| Any INSERT, UPDATE, or DELETE on spine tables | MCP bridge is read-only. Mutations go through Process Manager → Eric Gate → approved workflow only. |
| Raw SQL execution | No arbitrary queries. Every tool is a predefined, parameterized read. |
| Credential or .env access | MCP subprocess environment is filtered (see §6.1). No API keys, tokens, or secrets. |
| Filesystem write access | MCP bridge process has no write permission to the CIS repo or data directory. |
| Agent dispatch or orchestrator trigger | MCP bridge does not initiate pipeline runs. It is a query surface only. |
| External network access | MCP bridge does not call out to external APIs. It reads the local SQLite spine only. |
| AGENTS.md generation or export | Export generation remains a closeout gate function (Tier 5), not an MCP tool. |
| Kanban board access | Kanban is retired as pipeline transport (ADR-SEED-013). MCP does not revive it. |

### 2.3 Access control

- MCP bridge binds to localhost only (127.0.0.1). Zero external network exposure.
- MCP bridge runs as a stdio MCP server, not an HTTP server, so it is only accessible
  to processes that explicitly spawn it.
- Hermes profiles connect via the native MCP client (native-mcp skill). The MCP config
  is per-profile — only profiles Eric explicitly configures can access the bridge.
- No authentication token required (localhost + stdio transport is the security boundary).

---

## 3. Relationship to the WorkIntent → Process Manager Flow

### 3.1 Where MCP sits in the architecture

```
Incoming prompt / file / archive hit / workflow event
                    │
          ┌─────────▼──────────┐
          │  Normalizer         │
          │  → WorkIntent       │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  Domain Classifier  │
          │  + Adapters         │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  Process Manager    │  ←── MCP BRIDGE sits alongside,
          │  (State Machine)    │      not inside, this flow.
          └─────────┬──────────┘      It reads the spine that the
                    │                  Process Manager writes to.
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼─────┐  ┌────▼─────┐  ┌─────▼────┐
│Stage     │  │Human     │  │Dispatch  │
│Candidate │  │Approval  │  │Action    │
│          │  │Gate      │  │          │
└──────────┘  └──────────┘  └──────────┘
                    │
          ┌─────────▼──────────┐
          │  Dead Letter        │
          └────────────────────┘


          ┌─────────────────────────┐
          │  MCP Bridge (Tier 8)    │  ← Read-only query surface
          │  ┌───────────────────┐  │
          │  │ cis_get_current_  │  │
          │  │ phase()           │  │
          │  │ cis_get_build_    │  │
          │  │ status()          │  │
          │  │ cis_get_next_     │  │
          │  │ actions()         │  │
          │  │ cis_search_       │  │
          │  │ sessions()        │  │
          │  └───────┬───────────┘  │
          └──────────┼──────────────┘
                     │
                     │ reads from
                     ▼
          ┌─────────────────────────┐
          │  SQLite Spine           │
          │  (cis_memory.db)        │
          └─────────────────────────┘
```

### 3.2 Flow relationship

The MCP bridge is a **passive query layer** — it does not participate in the
WorkIntent → Process Manager → Approval flow. It provides context to the profiles
that DO participate:

1. **Before a workflow run**: Drafter calls `cis_get_current_phase()` and
   `cis_get_next_actions()` to understand what needs work. Reviewer calls
   `cis_get_recent_runs()` to see what was recently decided.

2. **During a workflow run**: Research profile calls `cis_search_sessions()` to
   check if a topic has been previously examined. Drafter calls
   `cis_get_open_questions()` to ensure the proposal addresses outstanding unknowns.

3. **After a workflow run**: Eric or Implementer calls `cis_get_build_status()` to
   verify a node is COMPLETE. Implementer calls `cis_get_run_detail()` to review
   the deliberation that produced the directive.

4. **Between sessions**: Any profile calls any MCP tool to get current state without
   regenerating AGENTS.md. This eliminates the stale-context gap between closeouts.

### 3.3 What MCP must NOT do in relation to the flow

- Must not classify intents, route work, or create WorkIntent objects
- Must not stage candidates, request approvals, or dispatch agents
- Must not participate in deliberation rounds
- Must not enforce state transition rules (that's the Process Manager)
- Must not gate on Eric approval (that's the Eric Gate)
- Must not generate FINAL_DIRECTIVE or FINAL_JSON blocks

---

## 4. Minimum Bridge Architecture

### 4.1 Component diagram

```
┌──────────────────────────────────────────────────────┐
│  Hermes Profile (e.g., V4 Drafter on port 8645)      │
│                                                      │
│  ~/.hermes/config.yaml:                               │
│    mcp_servers:                                       │
│      cis:                                             │
│        command: "/home/eric/.hermes/hermes-agent/     │
│                   venv/bin/python"                     │
│        args: ["-m", "cis_mcp_bridge.server"]          │
│        env:                                           │
│          CIS_SPINE_PATH: "/mnt/projects/cis/data/     │
│                           cis_memory.db"              │
│        timeout: 30                                    │
│                                                      │
│  Tools available: mcp_cis_get_current_phase(),        │
│    mcp_cis_get_build_status(...), etc.                │
└──────────────────────┬───────────────────────────────┘
                       │ stdio (MCP protocol)
                       │
┌──────────────────────▼───────────────────────────────┐
│  cis_mcp_bridge/                                     │
│  ├── server.py          MCP server entry point        │
│  ├── tools.py           Tool definitions + handlers   │
│  ├── spine.py           SQLite read-only queries      │
│  └── __init__.py                                      │
│                                                      │
│  Runs as a subprocess spawned by Hermes native MCP    │
│  client. Connects to CIS_SPINE_PATH (env var).        │
│  All queries are SELECT only. No write operations.    │
│  Binds to stdio transport — no network socket.        │
└──────────────────────┬───────────────────────────────┘
                       │ sqlite3 (read-only)
                       │
┌──────────────────────▼───────────────────────────────┐
│  /mnt/projects/cis/data/cis_memory.db                 │
│  (SQLite spine — Tier 4)                              │
│                                                      │
│  Tables read: build_plan_nodes, workflow_runs,        │
│    deliberation_rounds, workflow_run_artifacts,       │
│    eric_gate_approvals, session_closeouts,            │
│    project_decisions, open_questions, next_actions    │
└──────────────────────────────────────────────────────┘
```

### 4.2 Files to create

| File | Purpose |
|------|---------|
| `runtime/mcp_bridge/__init__.py` | Package marker |
| `runtime/mcp_bridge/server.py` | MCP stdio server entry point. Uses the `mcp` Python package (same SDK Hermes uses for its native MCP client). Registers tools, handles stdio transport. |
| `runtime/mcp_bridge/tools.py` | Tool definitions: name, description, JSON Schema parameters, handler functions. |
| `runtime/mcp_bridge/spine.py` | Read-only SQLite queries. All queries are SELECT. Database opened in read-only mode (`sqlite3_open_v2` with `SQLITE_OPEN_READONLY`). Query results returned as JSON-serializable dicts/lists. |

### 4.3 Technology choices

| Choice | Rationale |
|--------|-----------|
| Python `mcp` package | Same SDK Hermes uses for native MCP client. Battle-tested. Supports stdio transport natively. |
| stdio transport | No network exposure. Process boundary is the security boundary. Hermes spawns the subprocess with filtered env. |
| SQLite read-only mode | OS-level guarantee that the bridge cannot write, even if code is buggy or compromised. |
| CIS_SPINE_PATH env var | Path injected by Hermes MCP config. Bridge does not hardcode paths. |
| No external dependencies beyond `mcp` and Python stdlib | Minimum surface area. `mcp` is installed in the Hermes Agent venv (`~/.hermes/hermes-agent/venv`). The MCP bridge uses this venv's Python. |

### 4.4 Hermes MCP configuration (per profile)

Each profile that needs CIS spine access adds to its `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  cis:
    command: "/home/eric/.hermes/hermes-agent/venv/bin/python"
    args: ["-m", "cis_mcp_bridge.server"]
    env:
      CIS_SPINE_PATH: "/mnt/projects/cis/data/cis_memory.db"
    timeout: 30
```

The `PYTHONPATH` must include `/mnt/projects/cis/runtime` so the `cis_mcp_bridge`
package is importable. This is set in the profile's shell environment or `.env`.

Profiles that do NOT need spine access (e.g., external advisor profiles) omit the
`cis` MCP server entry — they get no spine tools.

---

## 5. Required Tables, Files, and Schemas

### 5.1 No new database tables

Tier 8 does not add tables to the SQLite spine. It reads existing tables:

| Table | Read by tool(s) | Purpose |
|-------|-----------------|---------|
| `build_plan_nodes` | `cis_get_current_phase`, `cis_get_build_status`, `cis_get_next_actions` | Build phase tracking |
| `workflow_runs` | `cis_get_recent_runs`, `cis_get_run_detail` | Pipeline activity |
| `deliberation_rounds` | `cis_get_run_detail` | Round-by-round history |
| `workflow_run_artifacts` | `cis_get_run_detail` | Associated artifacts |
| `eric_gate_approvals` | `cis_get_eric_gate_status` | Pending approvals |
| `session_closeouts` | `cis_search_sessions` | Archive search (FTS5) |
| `project_decisions` | `cis_get_open_decisions` | Active decisions (ADR-SEED-*) |
| `open_questions` | `cis_get_open_questions` | Outstanding unknowns (OQ-SEED-*) |

### 5.2 No new configuration files

The MCP bridge requires no config file. Configuration is via:
- `CIS_SPINE_PATH` environment variable (path to `cis_memory.db`)
- Hermes `config.yaml` `mcp_servers.cis` block (transport + env)

### 5.3 Schema migration required

One schema migration is required for Tier 8:

| Migration | Purpose |
|-----------|---------|
| `runtime/schema/migrations/009_fts_session_closeouts.sql` | Create FTS5 virtual table `session_closeouts_fts` over `session_closeouts(failure_summary, failure_step, log_path, created_by)` to support `cis_search_sessions` full-text search |

The migration creates an external content FTS5 index — the `session_closeouts` base table is not altered. The bridge queries the FTS5 virtual table for text search; the base table for row retrieval.

This migration must be applied and verified before `cis_search_sessions` can be used. All other bridge tables already exist in the spine (Tier 4).

### 5.4 Directory structure

```
/mnt/projects/cis/
└── runtime/
    └── mcp_bridge/           ← NEW (Tier 8)
        ├── __init__.py
        ├── server.py
        ├── tools.py
        └── spine.py
```

---

## 6. Security and Approval Boundaries

### 6.1 Environment isolation

The MCP bridge subprocess inherits Hermes' filtered MCP environment. Per the
native-mcp skill, only safe baseline variables are passed:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables
- `CIS_SPINE_PATH` (explicitly added in `mcp_servers.cis.env`)

No API keys, tokens, or secrets are passed. The bridge has no access to
`~/.hermes/.env`, AWS credentials, GitHub tokens, or any other credential store.

### 6.2 Database access

- The spine database is opened in **SQLite read-only mode** (`uri=True` with
  `mode=ro` query parameter, or `sqlite3_open_v2` with `SQLITE_OPEN_READONLY`).
- The bridge code contains **zero** INSERT, UPDATE, DELETE, CREATE, DROP, or
  ALTER statements. This is verified by automated scanning (gate_mcp_readonly.py,
  see §7.2).
- The database file is owned by the `eric` user. The MCP bridge process runs as
  the same user (spawned by Hermes), so file permissions do not block read access.

### 6.3 Filesystem access

- The MCP bridge process has no reason to touch the filesystem beyond opening
  the spine database.
- The `CIS_SPINE_PATH` is the only path the bridge knows about.
- No write_file, mkdir, or any filesystem manipulation code exists in the bridge.

### 6.4 Network access

- The bridge uses stdio transport — no TCP socket, no HTTP listener.
- The bridge code contains no `socket`, `http`, `urllib`, or `requests` imports.
  This is verified by automated scanning (gate_mcp_no_network.py, see §7.2).
- No external API calls. No outbound connections.

### 6.5 Approval boundaries

- MCP bridge operations are **read-only** — they do not trigger Eric Gate review.
  Read operations (retrieving current state, searching sessions) are pre-approved
  by architectural design, consistent with Tier 7R §7.2.
- MCP bridge **does not bypass** the Eric Gate. It cannot create WorkIntent
  objects, stage candidates, or dispatch agents. Mutations still require the full
  approval pipeline.
- If a profile tries to use MCP query results to justify a mutation without Eric
  Gate approval, the Process Manager (Tier 7R.4) blocks the dispatch. MCP queries
  do not constitute approval.

### 6.6 Audit trail

- MCP tool calls are logged at Hermes' MCP client layer (stdout/stderr of the
  subprocess). No additional audit logging is required within the bridge itself.
- The bridge does NOT write an audit trail to the spine (that would be a write
  operation).

---

## 7. Deterministic Acceptance Criteria

### 7.1 Functional acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| A1 | Phase query | `mcp_cis_get_current_phase()` | Returns current tier label, status, and next actions matching spine | Compare against `SELECT * FROM build_plan_nodes WHERE status IN ('IN_PROGRESS', 'PENDING')` |
| A2 | Build status | `mcp_cis_get_build_status("Tier 7R.4")` | Returns status=COMPLETE (or current actual status) with evidence_path | Compare against direct SQLite query |
| A3 | Next actions | `mcp_cis_get_next_actions()` | Returns only nodes where status=PENDING AND all dependency nodes are COMPLETE | Verify no orphaned or out-of-order nodes |
| A4 | Recent runs | `mcp_cis_get_recent_runs(limit=5)` | Returns up to 5 most recent workflow_runs, ordered by created_at DESC | Compare row count and order |
| A5 | Run detail | `mcp_cis_get_run_detail("run-xxx")` | Returns the run + its deliberation_rounds + artifacts | Verify round count matches spine |
| A6 | Eric Gate status | `mcp_cis_get_eric_gate_status()` | Returns pending approvals with workflow_run_id, decision, created_at | Compare against `SELECT * FROM eric_gate_approvals WHERE decision = 'APPROVE' AND is_current = 1` |
| A7 | Session search | `mcp_cis_search_sessions("social worker")` | Returns matching session_closeouts with snippets | FTS5 match test |
| A8 | Open decisions | `mcp_cis_get_open_decisions()` | Returns decisions from project_decisions where status = 'DECIDED' AND superseded_by IS NULL | Compare against project_decisions table |
| A9 | Open questions | `mcp_cis_get_open_questions()` | Returns all open questions | Compare against open_questions table |

### 7.2 Security acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| S1 | Read-only enforcement | Attempt INSERT/UPDATE/DELETE via any code path | SQLite returns SQLITE_READONLY error | Database opened with `mode=ro` — OS-enforced |
| S2 | No network imports | Scan bridge source files | No `socket`, `http`, `urllib`, `requests`, `httpx`, `aiohttp` imports | `grep -r` on bridge directory |
| S3 | No write statements | Scan bridge source files | No INSERT, UPDATE, DELETE, CREATE, DROP, ALTER keywords in SQL strings | `grep -ri` on bridge directory |
| S4 | No filesystem writes | Scan bridge source files | No `open(..., 'w')`, `write()`, `os.remove()`, `shutil` imports | `grep -r` on bridge directory |
| S5 | Localhost binding only | If bridge ever adds optional HTTP transport | Must bind to 127.0.0.1 only, reject 0.0.0.0 | Test with netstat/ss |
| S6 | Filtered environment | Check env vars visible to bridge subprocess | No API_KEY, TOKEN, SECRET, or PASSWORD vars present | Compare against Hermes MCP env filter |

### 7.3 Integration acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| I1 | Profile loads MCP tools | Start Hermes Drafter with cis MCP config | `mcp_cis_get_current_phase` appears in tool list | Check Hermes startup logs for MCP tool registration |
| I2 | Cross-profile access | All 4 active profiles configured | Each profile can call cis_get_current_phase independently | Sequential test from each profile |
| I3 | Concurrent access | Two profiles query simultaneously | Both get correct results, no locking errors | SQLite concurrent read test |
| I4 | Stale data handling | Spine updated between queries | Subsequent queries return updated data (no caching beyond SQLite's page cache) | Timestamp-based verification |
| I5 | Error on missing DB | CIS_SPINE_PATH points to nonexistent file | MCP tool returns clear error, does not crash Hermes | Graceful error test |

---

## 8. Required Tests and Gates Before Implementation

### 8.1 Pre-implementation gates (must pass before code is written)

| Gate | Type | Purpose |
|------|------|---------|
| Tier 7R.4 COMPLETE | Dependency | Process Manager must be verified complete with acceptance tests passing |
| spine_mcp_tables_exist.sql | DB state | Confirm all tables the bridge will read exist in cis_memory.db |
| spine_row_count.sql | DB state | Confirm build_plan_nodes has rows (spine is not empty) |
| `mcp_package_installed.sh` | Dependency | Confirm `~/.hermes/hermes-agent/venv/bin/python -c "import mcp"` succeeds |
| python_version.sh | Dependency | Confirm Python 3.9+ is available |

### 8.2 Post-implementation verification gates (must pass before COMPLETE)

| Gate | Type | Purpose | Implementation |
|------|------|---------|----------------|
| `gate_mcp_readonly.py` | Security | Scan bridge source for write SQL statements | `grep` for INSERT/UPDATE/DELETE/CREATE/DROP/ALTER |
| `gate_mcp_no_network.py` | Security | Scan bridge source for network imports | `grep` for socket/http/urllib/requests/httpx/aiohttp |
| `gate_mcp_no_filesystem_write.py` | Security | Scan bridge source for filesystem write operations | `grep` for `open.*'w'`/write/remove/shutil |
| `gate_mcp_tools_registered.sh` | Functional | Confirm all 9 tools appear in Hermes tool list after startup | Parse Hermes startup log |
| `gate_mcp_tool_a1.sh` through `gate_mcp_tool_a9.sh` | Functional | One gate per acceptance test A1-A9 | Each gate calls the MCP tool and validates output shape |
| `gate_mcp_cross_profile.sh` | Integration | Confirm tools work from at least 2 different profiles | Sequential curl/CLI test |

### 8.3 Test file structure

```
/mnt/projects/cis/
├── tests/
│   └── mcp_bridge/
│       ├── test_tools.py          # Unit tests per tool handler
│       ├── test_spine.py          # Unit tests for read-only queries
│       ├── test_security.py       # Security boundary tests (S1-S6)
│       └── test_integration.py    # Integration tests (I1-I5)
└── tools/
    └── gates/
        ├── gate_mcp_readonly.py
        ├── gate_mcp_no_network.py
        ├── gate_mcp_no_filesystem_write.py
        ├── gate_mcp_tools_registered.sh
        ├── gate_mcp_tool_a1.sh through gate_mcp_tool_a9.sh
        └── gate_mcp_cross_profile.sh
```

---

## 9. Out of Scope

### 9.1 Explicitly not part of Tier 8

| Item | Reason |
|------|--------|
| Write operations to spine | Mutations go through Process Manager → Eric Gate. MCP is read-only. |
| AGENTS.md generation | Export generation is a Tier 5 closeout function. MCP provides live query — the alternative to regeneration. |
| WorkIntent creation or routing | Classification and routing are Tier 7R functions. MCP is a passive query layer. |
| Agent dispatch or orchestrator trigger | MCP cannot initiate pipeline runs. |
| Chroma/VDB integration | Tier 9. MCP reads SQLite spine; VDB reads Chroma. Separate tiers, separate concerns. |
| UI or dashboard | Tier 10. MCP is a backend query surface, not a user-facing interface. |
| External network exposure | MCP binds localhost only. No remote access. |
| Authentication system | Localhost + stdio transport is the security boundary. No auth tokens needed. |
| Multi-project support | CIS_SPINE_PATH points to one database. Project isolation is per the ADR-SEED-010 model. |
| Hot-reload of tools | Adding new tools requires restarting Hermes profiles (native MCP limitation). |
| HTTP/SSE transport | stdio only for Tier 8. HTTP could be added later, but introduces network security surface. |
| Write-audit logging | Read operations do not require audit trails. |
| Tier 9 Chroma/VDB | Gated on Tier 8 per dependency graph. Not built here. |
| Tier 10 CIS UI | Gated on Tier 9. Not built here. |

---

## 10. Eric Gate Approval Required Before Implementation

### 10.1 Gating conditions

Tier 8 implementation shall not begin until ALL of:

| # | Condition | Verification |
|---|-----------|-------------|
| 1 | Tier 7R.4 (Process Manager) status = COMPLETE | `SELECT status FROM build_plan_nodes WHERE node_label = 'Tier 7R.4'` |
| 2 | Eric Gate approval recorded for **this specification** | `eric_gate_approvals` row with `workflow_run_id` referencing this spec approval |
| 3 | All Tier 7R acceptance tests (A1-A6 from Tier 7R §8) passing | Test suite output |
| 4 | Evidence manifest for Tier 7R.4 complete: git diff, test output, spine queries | Evidence directory |
| 5 | Eric explicitly issues PROCEED or IMPLEMENT for Tier 8 | Not automatic — Eric must read this spec and approve |

### 10.2 Approval record format

Eric Gate approval for this specification must include:

```
Decision: APPROVE
Workflow: [Tier 8 MCP Bridge Specification review]
Rationale: [Eric's rationale]
Date: [ISO 8601]
Decided by: Eric
```

The approval must be recorded in the `eric_gate_approvals` table and linked to a
`workflow_run_id` created for this specification review.

### 10.3 What happens after approval

1. A build_plan_node for Tier 8 is created in the spine with status = PROPOSED
2. Eric issues IMPLEMENT → Tier 8 status moves to IN_PROGRESS
3. Implementation follows the phased build plan in §11
4. Verification gates (§8.2) run after each build increment
5. Tier 8 status moves to COMPLETE only after all gates pass AND Eric approves
   the completion closeout

### 10.4 What happens if approval is withheld

- Tier 8 remains BLOCKED
- This specification document is revised per Eric's direction
- Resubmitted for Eric Gate review
- Tier 9 (Chroma/VDB) and Tier 10 (UI) remain BLOCKED

---

## 11. Phased Build Plan

### 11.1 Principle

Tier 8 is built as sequential, independently-gated increments. Each increment
requires its own verification gate pass before the next increment begins. No
increment may start before its dependencies are verified.

### 11.2 Build nodes

| Node | Label | Depends On | Scope |
|------|-------|-----------|-------|
| Tier 8.1 | MCP Bridge — spine query layer | Tier 7R.4 COMPLETE, Eric Gate on this spec | Implement `spine.py`: read-only SQLite queries for all 9 tools. No MCP server yet — just the query functions with unit tests. |
| Tier 8.2 | MCP Bridge — tool definitions | Tier 8.1 | Implement `tools.py`: define tool schemas, wire handler functions to spine queries. Unit test each tool. |
| Tier 8.3 | MCP Bridge — server | Tier 8.2 | Implement `server.py`: stdio MCP server that registers tools. Test with `mcp test` CLI. |
| Tier 8.4 | MCP Bridge — Hermes profile integration | Tier 8.3 | Add `mcp_servers.cis` block to Drafter, Reviewer, Implementer, and Research profile configs. Verify tools appear at startup. |
| Tier 8.5 | MCP Bridge — security gates | Tier 8.4 | Run all security gates (§8.2): read-only, no network, no filesystem write. |
| Tier 8.6 | MCP Bridge — cross-profile integration test | Tier 8.5 | Run cross-profile test (I2). Run concurrent access test (I3). |
| Tier 8.7 | MCP Bridge — acceptance test suite | Tier 8.6 | Run all 9 functional acceptance tests (A1-A9). Record results. |
| Tier 8.8 | MCP Bridge — closeout | Tier 8.7 | Verify all gates pass. Record evidence. Update AGENTS.md. Request Eric Gate closeout approval. |

### 11.3 Node dependency graph

```
Eric Gate on Tier 8 spec
  └── Tier 8.1 (spine.py)
        └── Tier 8.2 (tools.py)
              └── Tier 8.3 (server.py)
                    └── Tier 8.4 (profile integration)
                          └── Tier 8.5 (security gates)
                                └── Tier 8.6 (cross-profile test)
                                      └── Tier 8.7 (acceptance suite)
                                            └── Tier 8.8 (closeout)
```

### 11.4 What each node does NOT include

| Node | Exclusions |
|------|------------|
| 8.1 | No MCP protocol code. No tool definitions. No Hermes config changes. |
| 8.2 | No MCP server. No process management. No Hermes integration. |
| 8.3 | No profile config changes. No cross-profile testing. No security scanning. |
| 8.4 | No new tool implementations. No security gates. No acceptance tests. |
| 8.5 | No new features. Security scanning only. |
| 8.6 | No new features. Integration testing only. |
| 8.7 | No new features. Acceptance testing only. |
| 8.8 | No new features. Verification + documentation only. |

---

## 12. Recommendation

**Approve this specification as the architecture basis for Tier 8.**

Tier 8 is the smallest possible bridge: a read-only MCP server that exposes the
existing SQLite spine to authorized Hermes profiles. It does not add tables,
migrations, network exposure, or write operations. It eliminates the stale-context
gap between AGENTS.md closeouts by allowing profiles to query current state on
demand.

The security boundary is strong: stdio transport (no network), SQLite read-only
mode (OS-enforced no-write), filtered environment (no secrets), and no external
API calls.

The architecture preserves the existing WorkIntent → Process Manager → Human
Approval Gate → Dead Letter flow without interference. MCP is a passive query
surface alongside the flow, not inside it.

The build is phased into 8 small, gated nodes (8.1-8.8), each independently
verifiable before the next begins.

---

## Appendix A: Evidence References

### A.1 Dependency graph (Tier 8 current state)

```
COMMAND: sqlite3 data/cis_memory.db "SELECT node_label, status FROM build_plan_nodes WHERE node_label LIKE '%Tier 8%' OR node_label LIKE '%Tier 7R%'"
OUTPUT:
Tier 7R — Intent-to-Workflow Architecture Specification|COMPLETE
Tier 7R.1 — WorkIntent Schema + Canonical Model|COMPLETE
Tier 7R.2 — DomainAdapter Interface + CISAdapter|COMPLETE
Tier 7R.3 — SWAAdapter (Validation Use Case)|COMPLETE
Tier 7R.4 — Process Manager (State Machine)|COMPLETE
Tier 7R.5 — Human Approval Gate Integration|COMPLETE
Tier 7R.6 — Dead Letter / Blocked Handling|COMPLETE
Tier 7R.7 — Acceptance Test Suite|COMPLETE
Tier 8 — MCP Bridge|BLOCKED
Tier 9 — Chroma/VDB|BLOCKED
Tier 10 — CIS UI / Custom Display Views|BLOCKED
```

### A.2 ADR-013 (Kanban retirement)

```
SOURCE: AGENTS.md §4
ADR-SEED-013: Retire Kanban as required pipeline transport. workflow_runs is the
authoritative in-flight work object. deliberation_rounds stores per-round history.
Router creates workflow_runs row and returns run_id. Orchestrator accepts --run-id
and reads topic from workflow_runs. Gates verify from SQLite. Kanban code paths
are commented out and preserved as legacy.
```

### A.3 Native MCP client capability (already present)

```
SOURCE: native-mcp skill
Hermes Agent has a built-in MCP client that connects to MCP servers at startup,
discovers their tools, and makes them available as first-class tools the agent can
call directly. No bridge CLI needed -- tools from MCP servers appear alongside
built-in tools like terminal, read_file, etc.
```

### A.4 Build Proposal v1.0 Tier 8 original description

```
SOURCE: CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md line 326
From Build Proposal v1.0 §Phase H. MCP server at localhost:8888 exposes query tools
for current state, next actions, decisions, and prior proposals. The bidirectional
query tool that feeds Drafter context without full AGENTS.md regeneration.
```

### A.5 MCP Python package availability (verified 2026-06-12)

```
COMMAND: ~/.hermes/hermes-agent/venv/bin/python -c "import mcp; print('mcp imported OK'); print(hasattr(mcp, 'ClientSession')); print(mcp.ClientSession)"
OUTPUT:
mcp imported OK
True
<class 'mcp.client.session.ClientSession'>
```

The `mcp` Python package is available in the Hermes Agent venv at
`~/.hermes/hermes-agent/venv`. This is the Python environment the MCP bridge
uses (see §4.4 `command:` path). The system `python3` does NOT have `mcp`
installed — the venv Python path must be used.

---

*End of Tier 8 MCP Bridge Specification v1.0*
*Status: DRAFT — awaiting Eric Gate review*
*Next step: Eric reads → approves specification → Tier 8 build_plan_nodes created → IMPLEMENT*
