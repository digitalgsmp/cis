# Execution Snapshot Gap

**Status:** Verified architectural gap, not yet implemented  
**File:** `runtime/abstraction/pipeline_relay.py` (3577 lines)  
**Discovered:** 2026-08-25

## Problem

The verify phase cannot attribute changes to a specific run. It diffs against git HEAD, not the execution-start state, so pre-existing dirty state gets attributed to the run.

## Root Cause

1. **In-memory only:** `_execution()` at line 3196 captures HEAD via `git rev-parse HEAD` and stores it in `self._pre_exec_head` (lines 3201-3211). The chunked execution path does the same at lines 2863-2871. Nothing is persisted to the database.

2. **Resume loses it:** `resume()` at line 2106 dispatches `status == VERIFICATION` straight to `self._verification` (line 2140), but `_pre_exec_head` is an instance attribute from the prior process. After resume, line 3375 does `pre_head = getattr(self, "_pre_exec_head", "")` which returns empty, and isolation falls back with an explicit "NO ISOLATION" warning (lines 1764-1769 in `_run_isolated_l1`).

3. **L1 checks diff against HEAD:** `_run_l1_checks` (line 1595) runs `git diff --stat`, `git diff`, `git diff --name-only`, `git ls-files --others` — all against HEAD/index. Any pre-existing dirty state in the worktree is attributed to the run.

4. **Guardrails have the same blind spot:** `guardrails.py` `guardrail_claim_action` (line 219) runs `git diff --name-only pre_exec_head` and `guardrail_evidence_hash_chain` (line 2429) checks HEAD movement — both keyed on the in-memory HEAD.

## Solution Architecture (minimal, in existing style)

### 1. Snapshot Helper
Capture at execution start:
- HEAD hash
- `git status --porcelain` output
- Full `git diff` at execution start

Return deterministic string (JSON or porcelain text) plus HEAD.

### 2. Persistence Write
Insert into `workflow_run_artifacts` with `artifact_type = 'git_snapshot_exec_start'`. Precedent: `tools/pipeline/drafter_start.py` lines 98-101 already inserts git HEAD into this table — no schema migration needed.

**Idempotency:** On resume re-entering EXECUTION, capture only if no snapshot exists for the run, otherwise reuse it.

### 3. Reload + Run-Scoped Diff in _verification
- Load persisted snapshot from run record (fall back to in-memory attribute for same-process path)
- Compute run-scoped delta: post-execution tree minus snapshot
- Inject into `l1_evidence` and verify prompt as the reference, replacing current diff-against-HEAD

The isolated-worktree path can keep `pre_exec_head` for clean checkout, but the applied diff must be the run-scoped delta, not the whole working-tree diff.

### 4. Secondary: Compensation Scoping
Verify-FAIL compensation (line 3506) runs `git stash push` over the entire dirty tree, stashing changes unrelated to the run. A persisted run-start snapshot would let compensation scope itself. Optional but worth noting in the spec.

## Build Scope

Two functions + one DB write/read + one prompt paragraph. No new pipeline stages, no schema ceremony. Use existing `workflow_run_artifacts` table (or a `directive_hash`-style column if drafter decides it's cleaner).

## Flags

- No governance, no multi-tenant abstractions
- Do not invent a generic "artifact store service"
- Backward-compatible addition like `directive_hash` was (frozen in `_execution` lines 3221-3226)
