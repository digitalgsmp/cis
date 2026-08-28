# Pipeline Relay Execution Paths — Pre-Exec Snapshot Gap

## The Problem

`pipeline_relay.py` has TWO independent execution paths that both flow into
the verification phase, but only one captures pre-execution state, and
neither persists it. After a crash/resume into VERIFICATION, the in-memory
`_pre_exec_head` attribute is lost, and verification silently degrades
to no-isolation L1 checks.

## The Two Paths to VERIFICATION

### Path 1: Chunked (CODE_REVIEW_GATE)

```
PATTERN_CATALOG → CODE_REVIEW_GATE → (directly) VERIFICATION
```

- `_code_review_gate()` (line 2809) captures `self._pre_exec_head` at line 2871
  via `git rev-parse HEAD` with `cwd=project_dir`.
- On success, sets status to VERIFICATION and calls `self._verification()` directly
  (line 2893: `_set_run_status(..., "VERIFICATION")` then `await self._verification()`).
- Does NOT pass through `_execution()`. Does NOT call guardrails with `pre_exec_head`.
- `_pre_exec_head` is consumed only by `_verification()` at line 3375.

### Path 2: Regular (EXECUTION)

```
ERIC_GATE → EXECUTION → VERIFICATION
```

- `_execution()` (line 3196) captures `self._pre_exec_head` at line 3211 via
  `git rev-parse HEAD` with `cwd=DB_PATH.rsplit("/", 1)[0]`.
- Sets status to VERIFICATION after completion.
- Calls guardrails with `pre_exec_head` at line 3272.
- `_execution()` is only called from `resume()` at line 2139 when status == EXECUTION.

### Common: VERIFICATION

- `_verification()` (line 3370) reads `pre_head = getattr(self, "_pre_exec_head", "")`
  at line 3375 and passes it to `_run_isolated_l1(project_dir, pre_head)`.
- `_run_isolated_l1` (line 1662) creates a detached worktree at `pre_exec_head`,
  applies `git diff` (the ENTIRE working-tree diff, run-scoped or not), and runs
  `_run_l1_checks` inside it.
- If `pre_exec_head` is empty, falls back to in-place checks with "NO ISOLATION"
  warning (lines 1764-1769).
- Guardrails also receive `pre_exec_head` at line 3416.

## The Resume Bug

`resume()` (line 2106):
- `status == EXECUTION` → `self._execution()` (line 2139): RE-RUNS `git rev-parse HEAD`,
  so `_pre_exec_head` is re-captured but STALE (current HEAD, not original exec-start HEAD).
- `status == VERIFICATION` → `self._verification()` (line 2140): does NOT re-capture
  anything. `_pre_exec_head` is empty (instance attribute was in the prior process).
  Isolation silently degrades to no-isolation fallback.

## The Root Cause in _run_l1_checks

`_run_l1_checks` (line 1595) is the actual evidence source. It runs:
- `git diff --stat` (against HEAD/index)
- `git diff` (against HEAD/index)
- `git diff --name-only` (against HEAD/index)
- `git ls-files --others --exclude-standard`

All four diff against HEAD/index. Any pre-existing dirty state in the worktree
is attributed to the run. This is the root of "cannot tell which changes a run made."

## Persistence Precedent

- `workflow_runs.directive_hash` TEXT column: frozen in `_execution` at lines 3221-3226.
  Precedent for a small column addition.
- `workflow_run_artifacts` table: `(id, run_id, artifact_type, content, created_at)`.
  `drafter_start.py` `record_git_head()` (lines 97-105) inserts `artifact_type='git_head'`
  into this table. Precedent for artifact-based persistence with no schema change.
  NOTE: FK references `workflow_runs_old` not `workflow_runs`, but FK enforcement is OFF
  (PRAGMA foreign_keys = 0), so this is cosmetic.

## The Fix (Minimal)

1. One snapshot helper: capture HEAD + `git status --porcelain` + `git diff` at exec start.
   Call from BOTH paths (line 2862 chunked, line 3201 regular).
2. One persistence write: INSERT into `workflow_run_artifacts` with
   `artifact_type='git_snapshot_exec_start'`. Idempotent: only capture if no
   snapshot exists for the run.
3. One read + diff in `_verification`: load persisted snapshot (fall back to in-memory
   attr for same-process path), compute run-scoped delta, inject into `l1_evidence`
   and the verify prompt as the primary reference.
4. Update the verify-phase guardrail call at line 3416 to use the persisted snapshot
   too — otherwise guardrails still use the stale/empty in-memory value.

## Secondary Observation

The verify-FAIL compensation (line 3512) runs `git stash push` over the entire
dirty tree, stashing changes unrelated to the run. A persisted run-start snapshot
would let compensation scope itself too.
