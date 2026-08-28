# pipeline_relay.py — Verify Flow Map & Run-Scoped Snapshot Design

Grounded map of `runtime/abstraction/pipeline_relay.py` (3577 lines) as of 2026-08.
Line numbers drift; treat as anchors, re-grep before citing.

## Key locations

- `_execution()` ~3196 — regular Menter path. Captures ONLY `git rev-parse HEAD`
  into `self._pre_exec_head` (~3201-3211). NOT persisted. Freezes `directive_hash`
  into workflow_runs (~3221-3226) — precedent for a small column addition.
- Chunked execution path ~2862-2871 — same in-memory pre_head capture, second copy.
- `_verification()` ~3346 — verify phase. Loads `getattr(self, "_pre_exec_head", "")`
  (~3375), calls `_run_isolated_l1(project_dir, pre_head)`, composes prompt
  (~3384-3397) from: discovery + intent anchor + L1 evidence + FINAL_DIRECTIVE +
  Menter self-report. Guardrails get pre_exec_head at ~3416.
- `resume()` ~2106 — status == "VERIFICATION" → `_verification` directly (~2140).
  `_pre_exec_head` is a fresh instance attr → EMPTY after resume. This is the
  "doesn't survive resume" gap.
- Verify-FAIL compensation ~3505-3533 — `git stash push` of the ENTIRE dirty tree,
  not run-scoped; stash_ref stored in deliberation_rounds.objections_json.

## L1 evidence chain (the actual bug surface)

- `_run_l1_checks(cwd)` ~1595 — evidence = `git diff --stat`, `git diff` (capped
  2000 chars), `git diff --name-only` + existence/size, `git ls-files --others`.
  EVERY check diffs against HEAD/index → any pre-existing dirty state is
  attributed to the run. Root of "verify cannot tell which changes a run made".
- `_run_isolated_l1(cwd, pre_exec_head)` ~1662 — detached worktree at pre_exec_head,
  applies `git diff` (whole-tree diff, not run-scoped), runs _run_l1_checks inside.
  Falls back to in-place checks with "NO ISOLATION" warning if pre_exec_head empty.
- Guardrails have the same blind spot: guardrails.py `guardrail_claim_action` (~219,
  `git diff --name-only pre_exec_head`) and `guardrail_evidence_hash_chain` (~2429).

## Spine DB facts (CIS_SPINE_PATH env; default /mnt/projects/cis/data/cis_memory.db)

- workflow_runs columns: id, topic, result, requires_eric_review, max_rounds,
  rounds_completed, final_objections_json, created_at, completed_at, status, route,
  updated_at, eric_approved_at, intent, directive_hash, project_id, parent_run_id.
  No pre-exec/snapshot column.
- workflow_run_artifacts (run_id, artifact_type, content, created_at) EXISTS —
  `tools/pipeline/drafter_start.py` (~98-101) already INSERTs git HEAD into it.
  Use this as the persistence home for a run-start snapshot: no schema migration.
- deliberation_rounds: has verify_output, menter_output, objections_json,
  reviewer1/2_output, brain_output, drafter_output; UNIQUE(run_id, round_number).

## Run-scoped snapshot design (approved direction)

1. Snapshot helper at execution start: HEAD + `git status --porcelain` +
   pre-existing `git diff` (deterministic string). Call from BOTH execution paths.
2. Persist via workflow_run_artifacts, artifact_type like `git_snapshot_exec_start`.
   Idempotent on resume: capture only if absent for run_id.
3. `_verification`: load snapshot from DB (fallback to in-memory attr for the
   same-process path); compute run-scoped delta = post-exec tree minus snapshot;
   inject into l1_evidence + verify prompt. Keep pre_exec_head only for clean
   worktree checkout.
4. Optional: scope the FAIL compensation stash to the run-scoped delta.

## Brain-role workflow that produced this

Evidence-backed INTENT_UNDERSTANDING: map the code paths (grep line numbers first),
read the relevant sections in full, check the DB schema, THEN write claims with
file:line citations. End with FINAL_JSON {"role":"brain","status":"READY","summary":...}.
Pitfall: if search_files returns 0 matches where the pattern obviously exists,
verify with `grep -c` in terminal before concluding absence (tool glitch seen once
on this repo). Line numbers cited in output must come from actual reads, not memory.
