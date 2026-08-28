# L1 Verification and Working-Tree Snapshots

## How L1 Checks Work

`_run_l1_checks` (pipeline_relay.py line 1595) runs:
- `git diff --stat`
- `git diff` (bare — unstaged only)
- `git diff --name-only`
- `git ls-files --others --exclude-standard`

All diff against HEAD/index. Pre-existing dirty state is attributed to the run.

`_run_isolated_l1` (line 1662) creates a detached worktree at `pre_exec_head`, captures `git diff` (the whole working-tree diff), applies it in the clean worktree, then runs `_run_l1_checks` inside. Falls back to in-place with "NO ISOLATION" warning at line 1764 if `pre_exec_head` is empty.

`_execution` captures `self._pre_exec_head` at:
- Lines 3201-3211 (regular execution path)
- Lines 2862-2871 (chunked execution path)

Instance attribute only — not persisted to DB. Lost on process restart.

`_verification` (line 3346) reads it via `getattr(self, "_pre_exec_head", "")` at line 3375.

## Three Failure Modes

1. **Resume loss**: `resume()` at line 2140 dispatches to `_verification`, but `_pre_exec_head` is empty after restart. Isolation silently degrades to the no-isolation fallback.
2. **Committed changes invisible**: If Menter commits, bare `git diff` returns empty. The isolated worktree gets nothing applied. L1 sees a clean tree and may PASS incorrectly. This is the worst failure mode.
3. **Whole-tree attribution**: The diff applied is the entire working tree, not run-scoped. Pre-existing dirt gets attributed to the run.

## Snapshot Design (Build Target)

- Record HEAD + `git diff HEAD` (not bare `git diff`) to capture staged+unstaged
- Persist to DB via `workflow_run_artifacts` table, artifact_type `git_snapshot_exec_start`
  - Precedent: `tools/pipeline/drafter_start.py` lines 98-101 inserts `git_head` artifact
- Idempotent on resume re-entering EXECUTION: capture only if no snapshot exists for the run
- Run-scoped delta computation: post-execution tree minus snapshot
  - Unified approach: `git stash create` makes a tree object, then `git diff <snapshot_tree> <current_tree>`
  - Handles both committed and uncommitted changes in one command
- Inject run-scoped delta into verify prompt as primary L1 evidence

## Compensation Scope Risk

Verify-FAIL compensation (~line 3511) runs `git stash push` over the entire dirty tree. Pre-existing untracked/modified files unrelated to the run get stashed too — data-loss risk for the developer. A persisted run-start snapshot would let compensation scope its stash to only the run's changes. Not optional — this is a correctness issue.

## Guardrails Blind Spot

`guardrail_claim_action` (guardrails.py line 175) runs `git diff --name-only pre_exec_head` — also keyed on the in-memory HEAD. `guardrail_evidence_hash_chain` (line 2428) checks HEAD movement. Both share the same resume-loss failure mode. The snapshot fix in pipeline_relay.py should also update guardrails to load the persisted snapshot.
