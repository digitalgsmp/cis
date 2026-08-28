# Verify Snapshot Gap — Execution State Not Persisted

## The Problem

The CIS pipeline's verify phase (`_verification()` in `pipeline_relay.py`)
cannot tell which changes a run made. It diffs the post-execution tree
against git HEAD, not against the run's start state. Pre-existing dirty
state and changes from other processes are all attributed to the run.

The root cause is architectural: execution-start state is captured as an
in-memory instance attribute (`self._pre_exec_head`) that holds only a
HEAD hash (not a working-tree snapshot), and is never persisted to the DB.
On resume, the attribute is empty and isolation silently degrades.

## Verified Code Locations (pipeline_relay.py, 3577 lines, 2026-08-25)

### Execution phase — captures HEAD only, in memory

- **Regular path** `_execution()` line 3196: runs `git rev-parse HEAD`
  at lines 3204-3208, stores on `self._pre_exec_head` at line 3211.
  cwd = `DB_PATH.rsplit("/",1)[0]` (resolves to project data dir).
- **Chunked path** (line 2822 entry): same pattern at lines 2862-2871.
  cwd = `project_dir` where `project_dir = DB_PATH.rsplit("/",1)[0]` (line 2822).
- Neither path writes anything to the DB for pre-exec state.

### Verify phase — consumes in-memory attribute, loses it on resume

- `_verification()` line 3375: `pre_head = getattr(self, "_pre_exec_head", "")`
- Line 3376: passes to `_run_isolated_l1(project_dir, pre_head)`
- `resume()` line 2140: `elif status == "VERIFICATION": await self._verification(...)`
  — new process, attribute never set, `getattr` returns `""`.

### _run_isolated_l1 (line 1662) — isolation fallback

- Line 1687: captures `menter_diff = _run(["git", "diff"]).stdout` —
  this is `git diff` with NO arguments = unstaged tracked-file changes only
  (misses staged changes and untracked files). Pre-existing dirt is included.
- Lines 1692-1696: if `pre_exec_head` is set, creates a detached worktree
  at that HEAD and applies the diff.
- Lines 1764-1769: if `pre_exec_head` is empty OR worktree creation failed,
  falls back to in-place `_run_l1_checks(cwd)` with "NO ISOLATION" warning.
  On resume, this is the path taken — silently, no error raised.

### _run_l1_checks (line 1595) — the actual evidence source

All four checks diff against HEAD/index, not against run-start:
- Line 1607: `git diff --stat`
- Line 1617: `git diff` (full, capped 2000 chars)
- Line 1629: `git diff --name-only`
- Line 1650: `git ls-files --others --exclude-standard`

### Guardrails have the same blind spot (guardrails.py, 3214 lines)

- `guardrail_claim_action` (def line 175): line 219 `if pre_exec_head:`
  → line 221 `git diff --name-only pre_exec_head`. Keyed on in-memory HEAD.
- `guardrail_evidence_hash_chain` (def line 2428): line 2438 `if not pre_exec_head: return SKIP`.
  Lines 2451, 2459, 2467: all diff against `pre_exec_head`.
- Both guardrails called at lines 3272 (execution) and 3416 (verification)
  with `pre_exec_head=getattr(self, "_pre_exec_head", "")` — same resume loss.
- The guardrail calls inside `_review_single_chunk` also use the same
  in-memory attribute (set at 2871 before the chunk loop).

### Verify-FAIL compensation (line 3512)

`git stash push -m "CIS compensation: {run_id} verify FAIL"` with
`cwd=DB_PATH.rsplit("/",1)[0]`. Stashes the ENTIRE dirty tree —
unscoped, includes changes unrelated to the run.

## Persistence Precedent (verified)

### Option A: workflow_run_artifacts table (no schema change)

- Schema (`spine_schema.sql` lines 103-109): `workflow_run_artifacts`
  (id, run_id, artifact_type, content, created_at).
- **WARNING**: FK at line 105 references `"workflow_runs_old"(id)`, not
  `workflow_runs(id)`. This may be stale from a migration. The drafter
  must verify an INSERT actually succeeds before relying on this table.
- Precedent: `tools/pipeline/drafter_start.py` lines 97-105:
  `record_git_head()` inserts `artifact_type='git_head'` into this table.

### Option B: workflow_runs column (small schema addition)

- `directive_hash TEXT` column on `workflow_runs` (schema line 986),
  frozen in `_execution` at lines 3221-3226. Precedent for a small,
  backward-compatible column addition.

## Build Plan (minimal, in existing style)

1. **Snapshot helper**: capture HEAD + `git status --porcelain` +
   pre-existing `git diff` at execution start. Call from BOTH execution
   entry points (line 2862 chunked, line 3201 regular). Return a
   deterministic string + HEAD.

2. **Persistence write** at execution start: INSERT into
   `workflow_run_artifacts` with `artifact_type='git_snapshot_exec_start'`
   (following drafter_start.py precedent). On resume re-entering
   EXECUTION, capture only if no snapshot exists (idempotent).

3. **Read + run-scoped diff** in `_verification`: load persisted snapshot
   from DB (fall back to in-memory attr for same-process path), compute
   post-execution tree minus snapshot, inject into `l1_evidence` and the
   verify prompt (lines 3384-3397) as the primary reference. The
   isolated-worktree path can keep `pre_exec_head` for clean checkout,
   but the applied diff must be the run-scoped delta, not the whole
   working-tree diff.

4. **Secondary**: the verify-FAIL compensation (line 3512) should scope
   its `git stash` to run-scoped changes using the persisted snapshot.

## Key Design Constraints

- No new pipeline stages, no governance, no multi-tenant abstractions.
- Do not invent a generic "artifact store service" — the existing
  `workflow_run_artifacts` table is the right-sized tool.
- Do not touch the DB schema unless a column is cleaner than artifacts;
  either way it must be a small backward-compatible addition like
  `directive_hash`.
- Both execution paths use `DB_PATH.rsplit("/",1)[0]` as cwd (different
  variable names: `pre_head` path uses inline, chunked path uses
  `project_dir`). The snapshot helper must receive the same project root
  from both.

## FK Enforcement Note (verified 2026-08-25)

The schema's FK on `workflow_run_artifacts.run_id` references
`"workflow_runs_old"(id)`, but migration 0019 drops `workflow_runs_old`.
This is safe because `_db_connect()` (line 176) does NOT set
`PRAGMA foreign_keys=ON` — only WAL, busy_timeout, synchronous.
SQLite ignores FKs unless explicitly enabled. `drafter_start.py` already
INSERTs into this table successfully, confirming FKs are unenforced.
The artifacts-table approach requires no schema change and is safe.

## Spec Review Findings (Reviewer 1, 2026-08-25)

When reviewing the drafter's proposal for the snapshot fix, five issues
were found. The proposal was still CONSENSUS_REACHED because none changed
the architecture, but the implementer must resolve them:

1. **"project_dir as a function parameter" is wrong** (Section 5b):
   At the chunked path (line 2862), `project_dir` is a local variable
   set at line 2822 inside `_code_review_gate`, NOT a function parameter.
   The function signature is `(self, run_id, intent)`. The edit works
   because project_dir IS in scope, but the stated reason is factually
   wrong and would mislead an implementer.

2. **_compute_run_scoped_delta defined but never called** (Section 4e):
   The function is specified in detail but no edit (5a-5g) references it.
   `l1_evidence` comes from `_run_isolated_l1` (edit 5c), not from
   `_compute_run_scoped_delta`. The implementer must wire it in or inline
   its logic into `_run_isolated_l1`.

3. **_run_isolated_l1's path to run-scoped file list is unspecified**
   (Edit 5d): Says "same file list as 4e" but doesn't say whether
   `_run_isolated_l1` calls `_compute_run_scoped_delta`, inlines the
   logic, or receives the file list as a parameter. If the former,
   `_compute_run_scoped_delta`'s return type must expose the file list,
   not just an evidence string.

4. **`git diff` (no args) is NOT the "full working-tree diff"**:
   The draft and existing code call `_run(["git", "diff"])` at line 1687.
   `git diff` with no args shows only unstaged changes to tracked files.
   It misses staged changes and untracked files. The proposed
   `git diff snapshot["head"] -- <files>` is more correct but the draft's
   characterization of the current code as "full working-tree diff" is
   inaccurate.

5. **`git diff <old_head>` is NOT HEAD-independent (false claim in spec)**:
   The draft claims `git diff --name-only snap["head"]` is "HEAD-independent"
   so "mid-run commits by other processes cannot contaminate it." This is
   FALSE. `git diff --name-only <commit>` diffs the working tree against that
   commit — it includes BOTH unstaged changes AND changes that have been
   committed since that commit. If another process commits files between
   snapshot and verify, those committed files appear in `total_dirty` and
   won't be caught by set subtraction against `snap["dirty_files"]` if
   they're new files (not in the snapshot's dirty set). The correct
   decomposition would be: `git diff --name-only <old_head> HEAD` (committed
   changes) PLUS `git diff --name-only` (unstaged changes), then subtract
   the snapshot's dirty_files from each. Or accept that mid-run commits
   by other processes are an unhandled edge case and state it as a
   limitation. Low probability in practice (the pipeline runs in a
   single-process model), but the spec's correctness claim is wrong.

### Additional Findings (Reviewer 1, 2026-08-25, second pass)

6. **Missing subprocess import in new helpers** (Section 4a-4e):
   The spec's new helpers (`_capture_git_snapshot`, `_compute_run_scoped_delta`)
   use `subprocess.run()` but the file has NO top-level `import subprocess`.
   All existing functions import it locally (`_run_l1_checks` line 1601,
   `_run_isolated_l1` line 1673, `_execution` line 3202, `_code_review_gate`
   line 2863). The new helpers must follow the same pattern or the code
   will fail with NameError.

7. **guardrail_evidence_hash_chain line number off by 1**:
   Spec claims line 2428, actual is line 2427. Trivial but the
   implementer should verify anchors before editing.

8. **Edit 5f fixes line 3416 (verify) but NOT line 3272 (execution)**:
   Both lines use `pre_exec_head=getattr(self, "_pre_exec_head", "")`.
   The spec patches the verify-phase guardrail (3416) to use
   `snap.get("head", "")` but leaves the execution-phase guardrail (3272)
   on the same broken getattr. After resume into EXECUTION, the execution
   guardrail will silently SKIP.
   
   The draft's INTENT_ANCHOR states both guardrail sites (3416 and 3272)
   as part of the problem. The spec section 5f only patches 3416. This is
   a gap — the implementer must also patch 3272, OR the spec must declare
   it a non-goal with explicit reasoning. The reasoning would be:
   EXECUTION status is set at line 3343 (`_set_run_status(self.conn,
   run_id, "VERIFICATION")`) — wait, that sets VERIFICATION not EXECUTION.
   Looking more carefully: `_execution()` at line 3196 never sets status
   to "EXECUTION" itself — the status was set to "EXECUTION" by the
   caller (line 3272's guardrail runs during _execution, but the method
   was dispatched from resume at line 2138-2139). So resume into
   EXECUTION IS reachable (resume() line 2138 dispatches it), meaning
   3272 IS a live bug on resume-into-EXECUTION, not just latent.

9. **_save_exec_snapshot commits independently**:
   The spec's `_save_exec_snapshot` does `conn.commit()` immediately
   after INSERT, unlike `drafter_start.py` which commits once at the
   end of `main()`. This is actually correct for crash survival (the
   snapshot must persist even if execution fails later), but the
   spec should state this is intentional.

10. **Worktree SHA invariant must be stated**:
    Edit 5d keeps `pre_exec_head` for the clean worktree checkout but
    computes the run-scoped patch via `git diff snapshot["head"] -- <files>`.
    In the normal path `pre_exec_head == snapshot["head"]` (edit 5a sets
    `self._pre_exec_head = snap.get("head", "")`). But in the legacy
    fallback (edit 5c, snap from in-memory attr), they could diverge if
    the old code path set `_pre_exec_head` differently. The spec should
    state the invariant: the worktree checkout SHA must equal the diff
    baseline SHA.

### Finding 11 — Pre-dirty overlap files: 4e and 5d are internally inconsistent (Reviewer 1, 2026-08-25, third pass)

Section 4e step 4 defines `overlap = total_dirty intersect snap["dirty_files"]`
— files dirty both before and after the run — and labels each as
"PRE-DIRTY: run-scoped content delta not computable, full diff shown."

Section 5d says `_run_isolated_l1` should apply
`git diff snapshot["head"] -- <run_scoped_files>` to the clean worktree.
But `run_scoped_files` (from 4e step 3) is `total_dirty minus snap["dirty_files"]`,
which EXCLUDES overlap files. So overlap files are:
- Shown as full diffs in the evidence string (4e)
- NOT included in the worktree patch (5d)

This means the clean worktree will NOT contain the overlap files' changes.
The L1 checks run in the worktree will see those files at their pre-execution
state (the snapshot commit), not at their post-execution state. If Menter
modified a file that was already dirty, the worktree won't reflect Menter's
modification to that file.

The spec must state explicitly: overlap files are excluded from the worktree
patch because their run-scoped delta is not computable from a single
`git diff <commit> -- <file>` (that diff includes both pre-existing and run
changes mixed together). The worktree will show these files at their
pre-execution state only. The PRE-DIRTY full-diff section in the evidence
is the only visibility the verify agent gets for these files.

This is the same root issue as finding #5 (git diff is not HEAD-independent)
but manifests at the application level, not the detection level.

### Finding 12 — _run_isolated_l1 needs a git-apply fallback (Reviewer 1, 2026-08-25, fourth pass)

Edit 5d replaces the full `git diff` capture at line 1687 with a run-scoped
patch: `git diff snapshot["head"] -- <run_scoped_files>`. This patch is
then applied to the clean worktree via `git apply`.

If `git apply` of the run-scoped patch FAILS (e.g. because the file list
is incomplete, or the snapshot HEAD doesn't match the worktree base, or
there are content conflicts), the current code path continues silently
and runs `_run_l1_checks` inside a partially-patched worktree. This
produces false evidence — the worktree is missing files Menter created
or modified, so L1 checks report them as MISSING or unchanged.

**Required fix**: if `git apply` of the run-scoped patch fails, fall back
to the full `git diff` (current behavior) with an explicit warning marker
in the evidence string: "RUN-SCOPED PATCH FAILED — falling back to full
diff, isolation may include pre-existing changes." This prevents silent
incomplete-worktree L1 checks.

This is the same class of risk as Finding 11 (overlap files excluded
from the worktree patch) but for the failure case rather than the design
case. Both result in the worktree not reflecting Menter's actual changes.

### Finding 13 — Run-scoped untracked files are invisible to the clean worktree (Reviewer 1, 2026-08-25)

`git diff <commit> -- <files>` only produces patch output for tracked
files. Files Menter created NEW (untracked) are not representable in a
diff against any commit — they don't exist in the snapshot commit. The
spec acknowledges this ("untracked new files are not representable in a
patch") but the consequence is understated:

The clean worktree will NOT contain Menter's new files. The L1 checks
run in the worktree (including the Flask app import test at ~line 1745)
will fail if the run created new files that the import test depends on.
This is a pre-existing limitation (today's `git diff` also excludes
untracked files), but the spec's move to run-scoped patching makes it
more visible because the PRE-DIRTY section now explicitly lists what was
excluded.

**Recommendation**: for run-scoped untracked files, copy them into the
clean worktree after applying the patch (e.g. `shutil.copy` from the
original workspace). The `_compute_run_scoped_delta` file list
(`run_scoped_untracked`) is the authoritative source for what to copy.
Without this, the clean-worktree import test will fail for any run that
creates new files — which is the majority of CIS runs (greet.py, etc.).

## Reviewer Methodology: How to Vet a Drafter Spec

When reviewing a drafter proposal for the pipeline:

1. **Verify every line number claim** by reading the actual code at that
   offset. Specs often cite line numbers that are close but wrong after
   recent edits. Use `read_file` with offset, not grep, to confirm the
   cited content is at the cited line.

2. **Verify "only caller" / "zero other call sites" claims** with
   `grep -rn '<function_name>'` across runtime/ and tools/. The draft
   claimed `_run_isolated_l1` had one caller — verified true. But don't
   trust it without checking.

3. **Verify "function parameter" vs "local variable" claims** by reading
   the enclosing function's def line. Specs sometimes call local vars
   "parameters" — the distinction matters for scoping analysis.

4. **Verify FK/schema claims** by reading the schema file AND checking
   whether `PRAGMA foreign_keys=ON` is set in the connection function.
   A dangling FK reference in schema.sql is harmless if FKs are off.

5. **Check for defined-but-uncalled functions** in the spec's new-code
   section. If a function is defined in section 4 but no edit in section 5
   references it, flag it — the implementer will be guessing at the
   wiring.

6. **Verify both execution paths are covered**. The pipeline has two
   independent execution entry points (`_code_review_gate` at 2809 and
   `_execution` at 3196) that both set `_pre_exec_head` and both
   transition to `_verification`. Any fix must cover both or one path
   remains broken.

7. **Check for missing imports in new code**. If the spec defines new
   helper functions that use `subprocess`, `sqlite3`, etc., verify
   whether those modules are imported at the top of the file or
   locally inside each function. In `pipeline_relay.py`, `subprocess`
   is NOT a top-level import — every function that uses it does a
   local `import subprocess`. New helpers must follow the same
   pattern or they will fail with `NameError`.

8. **Check that ALL sites with the same bug pattern are fixed**. If
   the spec identifies a bug at one call site (e.g. line 3416), grep
   for all other sites with the same pattern
   (`grep -n 'pre_exec_head=getattr'`). If there are others (e.g.
   line 3272), either patch them too or declare them as non-goals
   with explicit reasoning.

9. **Verify invariant assumptions**. If the spec's fix assumes two
   values are always equal (e.g. worktree checkout SHA == diff
   baseline SHA), trace all code paths to confirm they can never
   diverge. If they can, flag it and ask the spec to state the
   invariant explicitly.

10. **Check for internal consistency between spec sections**. Section 4
    (new code) and section 5 (edits to existing code) are written by
    the same drafter but can contradict each other. In this session,
    section 4e defined a file set (run_scoped = total minus pre-dirty)
    that excluded overlap files, but section 5d referenced "same file
    list as 4e" without acknowledging that overlap files would be
    absent from the worktree patch. Cross-reference every variable name
    and file list between sections 4 and 5 to catch these.

11. **Verify "function parameter" vs "local variable" claims by reading
    the enclosing def line**. Specs sometimes say "already in scope as
    a function parameter" when the variable is actually a local set
    a few lines above. The edit still works (the variable IS in scope)
    but the stated reasoning is wrong and misleads implementers who
    rely on the spec's analysis for related decisions.
