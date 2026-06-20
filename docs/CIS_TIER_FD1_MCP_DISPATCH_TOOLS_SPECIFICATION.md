# Tier FD.1 — MCP Dispatch Tools
## Specification Document v1.2 (Revised — B1, M1–M5, N1 applied)

## Eric Gate Status: DRAFT — Awaiting Reviewer Re-Audit

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-20
**Source:** DEV-PIVOT-09 §FD.1 + Baseline Verification (raw grep 2026-06-20T04:15Z)
**Reviewer edits incorporated:** B1 (authoritative count from raw grep), M1 (file count label), M2 (relative symlink), M3 (Eric Gate query specified), M5 (mock-only tests)
**Gating dependency:** MCP Bridge (Tier 8) COMPLETE — 11 tools functional, stdio transport verified
**Baseline evidence:** /mnt/cache/catalog/fd1_baseline_20260620_041229.log

---

## 1. Purpose

### 1.1 What FD.1 solves

1. **No dispatch capability in MCP bridge.** The existing 11 MCP tools (cis_get_*, cis_search_*) are read-only spine queries. There is no MCP tool that initiates a CIS pipeline operation — Drafter, Reviewer, or Implementer dispatch requires manual terminal invocation.
2. **Front-door pipeline has no entry point.** DEV-PIVOT-09's front-door architecture assumes MCP tools can start pipeline workflows. FD.1 provides those tools.
3. **ADR-SEED-014 home-resolution risk retired.** Baseline confirmed `drafter_start.py` hardcodes `/mnt/projects/cis` and does not use `expanduser`, `~`, or `HERMES_HOME`. The subprocess call from dispatch handlers cannot propagate a bug that doesn't exist in the called script.

### 1.2 Core capability

> Add 3 MCP dispatch tools (cis_dispatch_drafter, cis_dispatch_reviewer, cis_dispatch_implementer) and a `runtime/mcp/` symlink to the existing MCP bridge, enabling pipeline operations from MCP clients. Total tools: 11 existing + 3 new = 14.

### 1.3 What changes for the operator (Eric)

| Before | After |
|--------|-------|
| Start Drafter: manually run `python3 tools/pipeline/drafter_start.py "topic" --intent "reason"` in terminal | MCP tool `cis_dispatch_drafter` with topic + intent, returns run_id |
| Start Reviewer: manually run `python3 tools/pipeline/reviewer_reconcile.py --run-id <id>` | MCP tool `cis_dispatch_reviewer` with run_id, returns deliberation status |
| Start Implementer: manually route FINAL_DIRECTIVE to v4impl gateway | MCP tool `cis_dispatch_implementer` with run_id, returns evidence |
| MCP path: `runtime/mcp_bridge/` | Also accessible at `runtime/mcp/` (relative symlink) |

### 1.4 What FD.1 does NOT change

- No existing 11 MCP tools modified
- No MCP transport changes (stdio remains)
- No new Python dependencies
- No database schema changes
- No new services or daemons
- No Hermes config changes
- No gateway or router changes
- No orchestrator changes
- No UI changes
- No enforcement, hooks, Docker, or /opt/cis-control changes

---

## 2. Architecture

### 2.1 Existing stack

| Layer | Existing | FD.1 Change |
|-------|----------|-------------|
| MCP transport | stdio via Hermes MCP config | None |
| Tool definitions | 11 read-only tools in tools.py TOOLS list | Add 3 dispatch tool definitions |
| Tool handlers | handle_get_current_phase, …, handle_get_similar | Add 3 dispatch handlers |
| Spine helpers | spine.py (existing query functions) | Add 1 helper: `check_eric_gate_approval(run_id)` |
| Pipeline scripts | drafter_start.py, reviewer_reconcile.py | Called via subprocess (unchanged) |
| Symlink | runtime/mcp_bridge/ only | Add relative symlink `runtime/mcp → mcp_bridge` |

### 2.2 Files to create (2 new)

| File | Purpose |
|------|---------|
| `runtime/mcp/` | Relative symlink to `mcp_bridge/` for spec path compliance |
| `tests/test_mcp_dispatch.py` | 12 tests verifying dispatch tools (all mocked, per M5) |

### 2.3 Files to modify (1)

| File | Change |
|------|--------|
| `runtime/mcp_bridge/tools.py` | Add 3 tool definitions + 3 handler functions + 3 HANDLERS entries |
| `runtime/mcp_bridge/spine.py` | Add `check_eric_gate_approval(run_id)` helper (per M3 — implementer gate query) |

### 2.4 Files unchanged

- `runtime/mcp_bridge/server.py` — stdio server, no change
- `runtime/mcp_bridge/chroma_index.py` — chroma index, no change
- `runtime/mcp_bridge/__init__.py` — package init, no change
- `tools/pipeline/drafter_start.py` — called via subprocess, no change
- `tools/pipeline/reviewer_reconcile.py` — called via subprocess, no change
- All 11 existing MCP tool definitions — unmodified
- All 11 existing handler functions — unmodified
- `runtime/api/router.py` — no change
- Hermes MCP config files — no change

### 2.5 No new dependencies, no new services

---

## 3. Dispatch Tool Specifications

### 3.1 cis_dispatch_drafter

| Field | Value |
|-------|-------|
| Name | `cis_dispatch_drafter` |
| Description | Start the CIS Drafter pipeline for a crystallized topic. Creates a workflow_run and dispatches the Drafter to produce a specification. Returns the workflow_run_id for tracking. |
| Required inputs | `topic` (string), `intent` (string) |
| Optional inputs | `session_id` (string) |
| Handler action | Calls `python3 tools/pipeline/drafter_start.py <topic> --intent <intent> [--session-id <id>]` via subprocess |
| Returns | `{ "workflow_run_id": "run-<hex>", "status": "DISPATCHED" }` |
| Error returns | `{ "error": "<message>" }` if topic/intent missing or subprocess fails |

### 3.2 cis_dispatch_reviewer

| Field | Value |
|-------|-------|
| Name | `cis_dispatch_reviewer` |
| Description | Dispatch the CIS Reviewer (R1 + Qwen dual-review) for a Drafter proposal. Requires an existing workflow_run_id from cis_dispatch_drafter. |
| Required inputs | `run_id` (string) |
| Handler action | Calls `python3 tools/pipeline/reviewer_reconcile.py --run-id <run_id>` via subprocess |
| Returns | `{ "run_id": "<id>", "status": "<CONSENSUS_REACHED|OBJECTIONS|ESCALATE>", "rounds_completed": <int> }` |
| Error returns | `{ "error": "<message>" }` if run_id missing, not found, or reviewer script fails |

### 3.3 cis_dispatch_implementer

| Field | Value |
|-------|-------|
| Name | `cis_dispatch_implementer` |
| Description | Dispatch the CIS Implementer to execute an Eric-approved FINAL_DIRECTIVE. Requires a workflow_run_id with Eric Gate approval. |
| Required inputs | `run_id` (string) |
| Handler action | Calls `check_eric_gate_approval(run_id)` from spine.py (see §3.4), then dispatches implementer via pipeline only if approved. |
| Returns | `{ "run_id": "<id>", "status": "DISPATCHED", "gate_status": "APPROVED" }` |
| Error returns | `{ "error": "<message>" }` if run_id missing, not Eric-approved, or dispatch fails |
| Gate query | See §3.4 below |

### 3.4 Eric Gate approval query (M3 — specified)

The `check_eric_gate_approval(run_id)` helper in `runtime/mcp_bridge/spine.py` runs:

```sql
SELECT eric_approved_at IS NOT NULL AND eric_approved_at != '' AS approved
FROM workflow_runs
WHERE id = ?
```

Returns `True` if the run has a non-null, non-empty `eric_approved_at` timestamp. Returns `False` otherwise (including when `run_id` does not exist). The `cis_dispatch_implementer` handler refuses dispatch with `{"error": "Eric Gate approval required", "gate_status": "UNAPPROVED"}` when this returns `False`.

This query reads from the existing `workflow_runs` table (schema unchanged since Tier 7). No schema migration required. The `eric_approved_at` column is populated by the Eric Gate APPROVE endpoint (Tier 11B).

**Why spine.py is now modified (was previously "unchanged"):** The helper function `check_eric_gate_approval` is a new addition to spine.py. It is a read-only query against existing schema — no writes, no schema changes. spine.py's existing 11 query functions are unmodified.

---

## 4. Deterministic Acceptance Criteria

### 4.1 Functional acceptance tests (all mocked per M5)

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| A1 | 3 dispatch tools registered in TOOLS list | Inspect TOOLS list | 14 total tools (11 existing + 3 new), new names present | `grep -c '"name": "cis_dispatch_' tools.py` returns 3 |
| A2 | No name collisions — 14 unique cis_* names | Compare all 14 names | 14 unique names, no duplicates | `grep -c '"name": "cis_' tools.py` returns 14 |
| A3 | Final tool count = 14 | Count all cis_* tool definitions | 14 | `grep -c '"name": "cis_' tools.py` returns 14 |
| A4 | cis_dispatch_drafter handler exists | Call with mocked subprocess | Returns dict with workflow_run_id, status=DISPATCHED | Handler returns correct keys, subprocess NOT called |
| A5 | cis_dispatch_reviewer handler exists | Call with mocked subprocess | Returns dict with run_id, status, rounds_completed | Handler returns correct keys, subprocess NOT called |
| A6 | cis_dispatch_implementer handler exists | Call with mocked gate check | Returns dict with status=DISPATCHED, gate_status=APPROVED | Handler returns correct keys, subprocess NOT called |
| A7 | runtime/mcp/ symlink resolves (relative) | `ls runtime/mcp/tools.py` | File listing succeeds | `test -f runtime/mcp/tools.py && echo EXISTS` |
| A8 | Symlink is relative, not absolute | `readlink runtime/mcp` | `mcp_bridge` (no leading /) | `test "$(readlink runtime/mcp)" = "mcp_bridge"` |
| A9 | Missing required field returns error dict | cis_dispatch_drafter with empty topic | Returns dict with error key, no crash | Check error key present, no traceback |
| A10 | Missing required field returns error dict | cis_dispatch_reviewer with no run_id | Returns dict with error key | Check error key present |
| A11 | Implementer refuses unapproved run_id | cis_dispatch_implementer with run_id lacking eric_approved_at | Returns `{"error": "...", "gate_status": "UNAPPROVED"}` | Gate query returns False, handler returns error |
| A12 | check_eric_gate_approval in spine.py | Call helper with four cases: (a) approved run_id with non-empty eric_approved_at → True; (b) run_id with eric_approved_at IS NULL → False; (c) run_id with eric_approved_at = '' → False; (d) missing run_id / no row → False | Direct helper test with controlled rows or patched DB cursor; verify boolean return for each case |

### 4.2 Security acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| S1 | No secrets in new tool definitions | grep api_key/secret/token on added lines | Zero matches | `grep -cE 'api_key|secret|password|token'` on git diff added lines returns 0 |
| S2 | Dispatch tools do not bypass Eric Gate | cis_dispatch_implementer without Eric approval | Returns error, not dispatched | A11 covers this — gate query verified in handler |

### 4.3 Mock/dry-run enforcement (M5)

All dispatch handler tests use Python `unittest.mock.patch` to replace `subprocess.run` and `spine.check_eric_gate_approval` with controlled mocks. No test invokes a real subprocess, writes to the spine, or launches a live pipeline run. Test isolation:

| Mock target | Replacement |
|-------------|-------------|
| `subprocess.run` | `MagicMock` returning success stub (for handler-exists tests) |
| `spine.check_eric_gate_approval` | `MagicMock` returning True (approved) or False (unapproved) per test case |
| Pipeline scripts | Never called — `subprocess.run` is patched before handler invocation |

For `cis_dispatch_implementer` unapproved-run tests, the test must assert that the dispatch path is not invoked. Use `subprocess.run.assert_not_called()` or an equivalent `assert not mock.called` check on the mocked dispatch/API call. Returning an error key is not sufficient if the dispatch path was still called.

---

## 5. Required Tests and Gates

### 5.1 Pre-implementation gates

| Gate | Command | Expected |
|------|---------|----------|
| No secrets in tools.py | `bash tools/gates/gate_no_secrets.sh` | PASS |
| MCP bridge server reachable | Verify server.py responds | PASS (existing infra) |
| Build state coherence | `python3 tools/gates/gate_build_state_coherence.py` | PASS |

### 5.2 Post-implementation verification gates

| Gate | Command | Expected |
|------|---------|----------|
| Dispatch tests pass (mocked) | `python3 -m pytest tests/test_mcp_dispatch.py -v` | 12 passed |
| Authoritative tool count | `grep -c '"name": "cis_' runtime/mcp_bridge/tools.py` | 14 |
| Dispatch count = 3 | `grep -c '"name": "cis_dispatch_' runtime/mcp_bridge/tools.py` | 3 |
| Symlink resolves + relative | `test -f runtime/mcp/tools.py && test "$(readlink runtime/mcp)" = "mcp_bridge" && echo PASS` | PASS |
| Build state coherence | `python3 tools/gates/gate_build_state_coherence.py` | PASS |
| Export agreement | `bash tools/gates/gate_export_agreement.sh` | PASS |

---

## 6. Phased Build Plan

### 6.1 Build nodes

| Node | Label | Depends On | Scope |
|------|-------|------------|-------|
| FD.1.1 | Create relative symlink | None | `cd runtime && ln -s mcp_bridge mcp`, verify relative |
| FD.1.2 | Add Eric Gate helper to spine.py | None | `check_eric_gate_approval(run_id)` function (read-only query) |
| FD.1.3 | Add dispatch tool definitions + handlers | FD.1.1, FD.1.2 | 3 tool defs + 3 handlers + 3 HANDLERS entries in tools.py |
| FD.1.4 | Write mocked dispatch tests | FD.1.1 | 12 tests in tests/test_mcp_dispatch.py (all mocked per M5) |
| FD.1.5 | Run tests + gates | FD.1.3, FD.1.4 | pytest + gate scripts |
| FD.1.6 | Commit and verify | FD.1.5 | git commit, verify clean tree |

### 6.2 What each node does NOT include

- FD.1.1: No tool changes, no tests
- FD.1.2: No schema changes (read-only query on existing workflow_runs table), no writes
- FD.1.3: No live pipeline dispatch (subprocess called by handler, not by the tool definition itself)
- FD.1.4: No live subprocess calls, no spine writes, no workflow_run creation (all mocked)
- FD.1.5: No new gates, use existing gate scripts
- FD.1.6: No push to GitHub unless closeout procedure runs

---

## 7. Out of Scope / Non-Goals

| Item | Reason |
|------|--------|
| Intent bridge / crystallization | FD.2+ scope, not FD.1 |
| Router integration with dispatch tools | FD.3 scope, dispatch tools are callable standalone |
| Gateway-to-gateway dispatch handoff | Separate orchestrator concern |
| MCP transport changes (HTTP, SSE) | stdio remains, per existing architecture |
| New MCP configuration | Hermes MCP config already points to mcp_bridge/; symlink provides alternative path |
| Pipeline orchestration chaining | Dispatch tools call one script each; chaining is orchestrator scope |
| Front-door integration tests | FD.4 scope, not FD.1 |
| Enforcement primitive, /opt/cis-control, Docker, hooks | Phase 0 complete; deferred per current_direction pivot |
| Live pipeline runs from tests | M5 prohibits — all tests mock subprocess |

---

## 8. Eric Gate Approval Required Before Implementation

### 8.1 Gating conditions

1. Baseline verification log reviewed: `/mnt/cache/catalog/fd1_baseline_20260620_041229.log`
2. ADR-SEED-014 caveat retired: confirmed `drafter_start.py` has no home-resolution code
3. Tool name collisions ruled out: `cis_dispatch_*` does not conflict with any of the 11 existing `cis_get_*`/`cis_search_*` names
4. Authoritative existing tool count confirmed by raw grep: 11
5. Authoritative post-implementation count: 11 + 3 = 14
6. Eric Gate approval query specified (§3.4) and scoped to read-only on existing schema
7. All dispatch tests mocked per M5 — no live pipeline runs from tests

### 8.2 What happens after approval

- FD.1.1–FD.1.6 execute in sequence
- Implementer (v4impl) executes, gates verify
- NA-SEED-017 marked COMPLETE

### 8.3 What happens if approval is withheld

- Spec returns to Drafter for revision per Reviewer OBJECTIONS
- No symlink created, no tools added, no spine.py modified

---

## Appendix A: Baseline Verification — Raw Evidence

**Evidence log:** `/mnt/cache/catalog/fd1_baseline_20260620_041229.log`

### A.1 Authoritative tool count (raw grep — B1 source of truth)

```
COMMAND: grep -c '"name": "cis_' runtime/mcp_bridge/tools.py
OUTPUT:  11
EXIT:    0
```

### A.2 Authoritative tool names (raw grep — collision check)

```
COMMAND: grep -oP '"name":\s*"\K[^"]+' runtime/mcp_bridge/tools.py
OUTPUT:  cis_get_current_phase
         cis_get_build_status
         cis_get_next_actions
         cis_get_recent_runs
         cis_get_run_detail
         cis_get_open_decisions
         cis_get_open_questions
         cis_get_eric_gate_status
         cis_search_sessions
         cis_search_semantic
         cis_get_similar
EXIT:    0
```

### A.3 Core files present

```
COMMAND: ls -la runtime/api/router.py tools/pipeline/pipeline_dispatch.sh tools/pipeline/drafter_start.py
OUTPUT:  All three files present (8639, 6791, 9729 bytes respectively)
EXIT:    0
```

### A.4 MCP bridge directory

```
COMMAND: ls -la runtime/mcp_bridge/
OUTPUT:  5 .py files (chroma_index.py, __init__.py, server.py, spine.py, tools.py)
EXIT:    0
```

### A.5 Dependency versions

```
COMMAND: pip3 show chromadb | grep Version && pip3 show sentence-transformers | grep Version
OUTPUT:  Version: 1.5.9
         Version: 5.5.0
EXIT:    0
```

### A.6 Symlink target clear

```
COMMAND: ls -la runtime/mcp
OUTPUT:  ls: cannot access 'runtime/mcp': No such file or directory
EXIT:    2 (expected — symlink target clear)
```

### A.7 ADR-SEED-014 caveat check

```
COMMAND: grep -nE "HERMES_HOME|expanduser|realpath|~|home" tools/pipeline/drafter_start.py
OUTPUT:  (empty — no matches)
EXIT:    1 (zero matches — ADR-SEED-014 caveat RETIRED for FD.1)
```

---

**Authorship rule:** This specification was drafted by Hermes (v4pro Drafter). It is a PROPOSAL ONLY. No implementation until Eric Gate approval per §8. Revision v1.1 incorporates B1 (raw-grep authoritative count), M1–M5 from consolidated Reviewer reconciliation.
