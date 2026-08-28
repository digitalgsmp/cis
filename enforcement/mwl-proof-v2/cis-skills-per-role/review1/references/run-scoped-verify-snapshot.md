# Run-Scoped Verify Evidence via Working-Tree Snapshot

## Problem

The verify phase cannot tell which changes a run made. `_run_l1_checks` diffs against git HEAD, so pre-existing dirty state is attributed to the run. After resume, `_pre_exec_head` (in-memory instance attribute) is lost, and isolation silently degrades to the no-isolation fallback.

## Verified Code Anchors (pipeline_relay.py, 3577 lines)

| Function | Line(s) | Role |
|---|---|---|
| `_execution()` | 3196-3211 | Captures HEAD only (in-memory `self._pre_exec_head`) |
| `_code_review_gate()` (chunked path) | 2862-2871 | Same HEAD-only capture; `project_dir` computed at line 2822 (local var, NOT function param); calls `_verification` directly at line 2896 |
| `_verification()` | 3346-3397 | Reads `getattr(self, "_pre_exec_head", "")` at 3375 |
| `_run_isolated_l1()` | 1662-1771 | Creates clean worktree at pre_exec_head, applies full `git diff`, runs L1 checks. **Only caller**: line 3376 in `_verification` |
| `_run_l1_checks()` | 1595-1659 | All diffs against HEAD/index — `git diff --stat`, `git diff`, `git diff --name-only`, `git ls-files --others` |
| `resume()` | 2106-2141 | Dispatches VERIFICATION straight to `_verification` (line 2141) — instance attrs lost |
| Compensation | 3506-3522 | `git stash push` with no path scoping |

## Two Paths to Verification (verified)

Both must persist the snapshot before `_verification` runs:
1. **`_execution` path**: `_execution` (3196) → sets status VERIFICATION (3343) → calls `_verification` (3344)
2. **`_code_review_gate` path**: `_code_review_gate` (2809) → captures pre_head (2862-2871) → sets status VERIFICATION (2895) → calls `_verification` (2896)

The draft's edit 5b (patching lines 2862-2871) is correct, but `_code_review_gate` is a separate pipeline method, NOT a second entry point into `_execution`. It does its own Menter builds per chunk, then calls `_verification` directly.

## Persistence Precedent

- `workflow_run_artifacts` table (spine_schema.sql line 103): `(id, run_id, artifact_type, content, created_at)`
- `drafter_start.py` `record_git_head()` (lines 97-105): INSERTs `git_head` artifact type
- `workflow_runs.directive_hash` (frozen at lines 3221-3226): column-based persistence precedent
- No unique index on `(run_id, artifact_type)` — idempotency must be enforced in code

## Design Pattern

1. **Snapshot helper** (`_capture_git_snapshot`): HEAD + `git status --porcelain` + `git diff` (capped), parsed into dirty_files/untracked_files lists.
2. **Idempotent persist** (`_ensure_exec_snapshot`): load-or-capture so resume re-entering EXECUTION reuses the original snapshot.
3. **Run-scoped delta** (`_compute_run_scoped_delta`): `git diff --name-only snap["head"]` minus `snap["dirty_files"]` = run-scoped files. PRE-DIRTY label for files dirty both before and after.
4. **Extended `_run_isolated_l1`**: optional `snapshot` kwarg; applies run-scoped patch instead of full diff.

## Pitfalls Discovered in Review

1. **`git diff` against snapshot HEAD does NOT immunize against mid-run commits by other processes.** If another process commits between snapshot and verify, those files appear in `git diff --name-only snap["head"]` but NOT in `snap["dirty_files"]`, so they'd be falsely attributed to the run. CIS is single-actor in practice, but spec text must be honest about this limitation.

2. **DB write failures must not crash execution.** `_save_exec_snapshot` needs try/except wrapping. Snapshot is non-critical for the same-process path (in-memory fallback exists). A DB lock error should log a warning, not propagate.

3. **Untracked new files can't be represented in `git apply` patches.** They must be copied directly into the clean worktree (e.g., `shutil.copy2` or `cp`). The draft must specify this explicitly — "identical limitation to today's code" is not sufficient guidance for the implementer.

4. **`_code_review_gate`'s `project_dir` is computed at line 2822 via `DB_PATH.rsplit("/", 1)[0]`, not a function parameter.** The variable IS in scope by line 2862, but spec text claiming it's "a function parameter" is factually wrong.

5. **`subprocess` is NOT imported at module top.** It is imported locally inside each function that needs it (lines 1601, 1673, 1782, 1915, 1996, 2863, 2903, 3202, 3510). The new module-level helpers (`_capture_git_snapshot`, `_compute_run_scoped_delta`) must each add `import subprocess` at function scope, matching the file's convention. Do NOT add a module-level `import subprocess` — it would break the established pattern.

6. **Dangling FK: `workflow_run_artifacts.run_id` references `workflow_runs_old`(id), which does NOT exist in the live DB.** `PRAGMA foreign_keys` returns 0 and `_db_connect()` (line 176-186) does not enable FK enforcement, so INSERTs succeed. But if anyone ever enables FK enforcement, the artifacts table becomes unwritable. The implementer must know this is consciously accepted existing rot, not an oversight. No fix needed for this spec — just don't be surprised by it.

7. **`DB_PATH.rsplit("/", 1)[0]` yields `/workspace/cis/data`, NOT `/workspace/cis`.** With `DB_PATH = /workspace/cis/data/cis_memory.db` (confirmed from `CIS_SPINE_PATH` env), the split produces the `data/` subdirectory. Git commands still work because they walk up to find `.git`, but `PROJECT_ROOT` (line 34: `os.path.dirname(os.path.dirname(DB_PATH))`) is the correct module-level constant yielding `/workspace/cis`. New code should use `PROJECT_ROOT` directly instead of re-deriving.

8. **`_compute_run_scoped_delta` return type must be `Tuple[str, List[str]]`, not bare `str`.** The draft's section 5d needs the run-scoped file list to construct the scoped patch inside `_run_isolated_l1`, but the function as specified in section 4e only returns an evidence string. The implementer will hit this gap immediately. Fix: return `(evidence_str, run_scoped_files)` so callers thread the file list through without recomputation.

## Guardrails Integration

- `guardrail_claim_action` (guardrails.py:175): takes `pre_exec_head: str`, runs `git diff --name-only pre_exec_head` at line 221
- `guardrail_evidence_hash_chain` (guardrails.py:2428): takes `pre_exec_head: str`, checks HEAD movement
- Fix: pass persisted HEAD from snapshot into `run_guardrails()` at line 3416 instead of `getattr(self, "_pre_exec_head", "")` — no guardrails.py edits needed

## Module Imports Already Available

- Line 20: `import json`
- Line 25: `from datetime import datetime, timezone`
- Line 26: `from typing import Any, Dict, List, Optional, Tuple`
