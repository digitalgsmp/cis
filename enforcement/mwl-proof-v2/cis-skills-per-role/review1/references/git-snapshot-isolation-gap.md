# Git Snapshot Isolation Gap — Verify Phase Cannot Attribute Changes to a Run

**Discovered:** 2026-08-25 (Reviewer 1 adversarial review)
**File:** `runtime/abstraction/pipeline_relay.py`
**Status:** Known gap, not yet built

## The Problem

The verify phase cannot tell which changes a run made vs pre-existing dirty state or changes by other processes mid-run.

### Root Cause Chain

1. **Execution captures only HEAD hash, in memory** (lines 3201-3211, 2862-2871)
   - `git rev-parse HEAD` → `self._pre_exec_head`
   - Nothing written to DB

2. **Verify consumes in-memory attribute** (line 3375)
   - `pre_head = getattr(self, "_pre_exec_head", "")`
   - After resume: empty → isolation silently degrades to "NO ISOLATION" fallback (line 1764-1769)

3. **`_run_l1_checks` diffs against HEAD/index** (line 1595)
   - `git diff --stat`, `git diff`, `git diff --name-only`, `git ls-files --others`
   - ALL diff against HEAD — pre-existing dirt attributed to the run

4. **`_run_isolated_l1` captures only unstaged changes** (line 1687)
   - `menter_diff = _run(["git", "diff"]).stdout` — `git diff` with no args = working tree vs index
   - If Menter commits changes, `git diff` returns empty → isolated worktree shows "no changes" = FALSE NEGATIVE
   - Should use `git diff HEAD` to capture committed + staged + unstaged

5. **Guardrails have same blind spot** (`guardrails.py` line 219, 2429)
   - `guardrail_claim_action` runs `git diff --name-only pre_exec_head`
   - `guardrail_evidence_hash_chain` checks HEAD movement
   - Both keyed on in-memory HEAD, not persisted snapshot

## What Needs Building

### 1. Snapshot Helper (shared by both execution paths)

Capture at execution start:
- HEAD hash
- `git status --porcelain`
- Pre-existing `git diff HEAD` (committed + staged + unstaged)

Return: deterministic string (JSON or porcelain text) + HEAD

Call from:
- Line 2862 (chunked execution)
- Line 3201 (regular execution)

### 2. Persistence Write (idempotent)

**Table:** `workflow_run_artifacts`
- Schema: `(id, run_id, artifact_type, content, created_at)`
- artifact_type: `git_snapshot_exec_start`
- content: the snapshot string

**Precedent:** `tools/pipeline/drafter_start.py` lines 98-101 inserts `git_head` into same table

**Caveat:** `pipeline_relay.py` has NEVER written to this table (0 INSERTs). The drafter_start.py precedent is from external CLI tool, separate process. Relay's first write needs connection-pattern awareness.

**Idempotency:** On resume re-entering EXECUTION (line 2139 dispatches to full `_execution()`), check if snapshot exists for run_id before capturing. Otherwise reuse existing.

### 3. Reload + Run-Scoped Diff in `_verification`

Load persisted snapshot from run record (fall back to in-memory attribute for same-process path).

Compute run-scoped delta: post-execution tree minus snapshot.

Inject into:
- `l1_evidence` (replace current diff-against-HEAD as primary evidence)
- Verify prompt (add run-start reference)

**Isolated-worktree path:** Can keep `pre_exec_head` for clean checkout, but applied diff must be run-scoped delta, not whole working-tree diff.

## Known Issues to Flag for Drafter

### Broken FK on `workflow_run_artifacts`

Schema shows:
```sql
run_id TEXT NOT NULL REFERENCES "workflow_runs_old"(id) ON DELETE CASCADE
```

Live table is `workflow_runs`, not `workflow_runs_old`. FK is dangling.

**Why it works today:** SQLite ships with `PRAGMA foreign_keys = OFF` by default. 20 existing rows prove inserts succeed.

**Risk:** If anyone enables FK enforcement, ON DELETE CASCADE silently deletes nothing (broken ref). Flag in spec, not a blocker.

### Resume Re-enters `_execution()` Fully

Line 2139: `elif status == "EXECUTION": await self._execution(run_id, intent)`

Entire method runs from top — including git rev-parse and snapshot capture. Idempotency guard must be FIRST thing inside `_execution`, before any capture code.

### Compensation Scope (Optional)

Verify-FAIL compensation (line 3512) runs `git stash push` over entire dirty tree — also stashes changes unrelated to the run. A persisted run-start snapshot would let compensation scope itself. Optional enhancement.

## Minimal Build Scope

- One snapshot helper function
- One idempotent DB write
- One reload + run-scoped diff in `_verification`
- One prompt paragraph

**Constraints:**
- No new pipeline stages
- No schema ceremony (use existing `workflow_run_artifacts` table)
- No generic "artifact store service" — existing table is right-sized
- Small, backward-compatible addition like `directive_hash` was

## Verification Commands

```bash
# Check _pre_exec_head is in-memory only
grep -n "_pre_exec_head" runtime/abstraction/pipeline_relay.py

# Check pipeline_relay has never written to workflow_run_artifacts
grep -rn "INSERT INTO workflow_run_artifacts" runtime/abstraction/pipeline_relay.py

# Check broken FK
sqlite3 data/cis_memory.db "SELECT sql FROM sqlite_master WHERE name='workflow_run_artifacts';"

# Check _run_isolated_l1 captures only unstaged
sed -n '1687p' runtime/abstraction/pipeline_relay.py
```

## References

- Eric's intent: "Capture a snapshot of the working tree at the start of the execution phase, persist it on the run record so it survives a resume, and give the verify prompt that reference so it diffs against the run start instead of git HEAD."
- Reviewer 1 verdict: CONSENSUS_REACHED with 4 annotations for drafter
