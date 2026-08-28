# Verify Isolation Architecture — Known Gaps (2026-08-25)

## Current State

### Execution Phase: HEAD-only, in-memory
- `_execution()` line 3196: captures `git rev-parse HEAD` → `self._pre_exec_head` (lines 3201-3211)
- Chunked path lines 2862-2871: identical capture
- Nothing persisted to DB

### Verify Phase: consumes in-memory attribute
- `_verification()` line 3375: `pre_head = getattr(self, "_pre_exec_head", "")`
- Passes to `_run_isolated_l1(project_dir, pre_head)`

### Isolation Mechanism: `_run_isolated_l1` (line 1662)
1. Captures full working-tree diff via bare `git diff` (line 1687)
2. Creates detached worktree at `pre_exec_head` (line 1696)
3. Applies the diff to the clean worktree (line 1714)
4. Runs `_run_l1_checks(worktree_path)` inside it (line 1735)
5. Falls back to in-place checks with "NO ISOLATION" warning if pre_exec_head empty (lines 1764-1769)

### Evidence Source: `_run_l1_checks` (line 1595)
- `git diff --stat` (line 1608) — bare, working tree vs index
- `git diff` (line 1617) — bare, capped at 2000 chars
- `git diff --name-only` (line 1630) — bare
- `git ls-files --others --exclude-standard` (line 1651) — untracked files

### Resume Breaks It
- `resume()` line 2106 dispatches `status == VERIFICATION` → `_verification` (line 2140)
- `_pre_exec_head` is instance attribute — after resume it's empty
- Isolation silently degrades to no-isolation fallback

### Guardrails Share the Blind Spot
- `guardrail_claim_action` (guardrails.py line 219): `git diff --name-only pre_exec_head`
- `guardrail_evidence_hash_chain` (guardrails.py line 2428): checks HEAD movement
- Both keyed on in-memory HEAD, not persisted

### Persistence Precedent Exists
- `workflow_run_artifacts` table: `run_id TEXT, artifact_type TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT`
- `drafter_start.py` (line 97): `INSERT INTO workflow_run_artifacts (run_id, artifact_type, content, created_at) VALUES (?, 'git_head', ?, ?)`
- Column name is `run_id` (NOT `workflow_run_id` — the test fixture uses the latter, but live DB uses `run_id`)
- `directive_hash` column on `workflow_runs` (lines 3221-3226): another persistence precedent

## Known Gaps (Identified in Adversarial Review)

### GAP 1 — Committed changes invisible (MEDIUM)
Bare `git diff` compares working tree to index, not HEAD. If Menter commits during execution:
- `git diff` returns empty → worktree gets nothing applied → verify sees clean tree
- Run-scoped delta MUST include `git diff pre_exec_head..HEAD` (committed changes)

### GAP 2 — Resume re-enters EXECUTION without idempotency guard (MEDIUM)
`resume()` → `_execution()` re-runs snapshot capture. If a run crashes during EXECUTION and resumes, a NEW pre-execution state is captured — different from original. Implementer must add: "if snapshot artifact exists for run_id, reuse it."

### GAP 3 — Snapshot format underspecified (LOW)
Brain proposes "HEAD + git status --porcelain + pre-existing git diff" but doesn't specify:
- Which git commands exactly
- Serialization format (JSON? concatenated text?)
- How verify computes the run-scoped delta from it

### GAP 4 — Snapshot size unaddressed (LOW)
Large working trees → large `git diff` output → DB bloat and prompt token overflow. No truncation or size policy.

### GAP 5 — Guardrails not in build plan (LOW)
Eric's intent scopes to "verify in pipeline_relay.py." Guardrails may be intentionally out of scope, but this should be explicit.

## Verify-FAIL Compensation (line 3512)
`git stash push -m "CIS compensation: {run_id} verify FAIL"` — stashes the ENTIRE dirty tree, not just run-scoped changes. A persisted run-start snapshot would let compensation scope itself.

## Schema Quick Reference
```sql
-- Live DB (migration 0005, spine_schema.sql)
CREATE TABLE workflow_run_artifacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES workflow_runs(id),
    artifact_type TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
```
