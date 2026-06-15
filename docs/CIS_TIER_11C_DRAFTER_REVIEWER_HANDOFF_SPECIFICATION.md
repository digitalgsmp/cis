# CIS Tier 11C — Drafter-to-Reviewer Handoff Specification

**Status:** REVISED — r1 objections addressed, pending re-review
**Author:** V4 Drafter (hermes-v4pro, port 8645)
**Date:** 2026-06-15
**Revision:** R1 — 7 Reviewer objections resolved
**Binding foundation:** ADR-SEED-014 (Temporary Draft Initiation Contract)
**Supersedes:** None (first Tier 11C specification)
**Prerequisite tiers:** 11A, 11B

---

## 1. Binding Authority

ADR-SEED-014 is the binding foundation. This specification implements ADR-014's
design choices, state sequence, and boundaries. Where ADR-014 states a requirement,
this specification provides the exact implementation contract. No design decisions
in this specification contradict ADR-014.

Key citations from ADR-014 that this specification implements:

| ADR-014 Reference | What It Requires |
|---|---|
| Clause 2 + Choice 1 | `drafter_start.py` creates both `workflow_run_id` and `proposal_id`, links them |
| Choice 1 (Option C) | Separate identities, `workflow_run_id` on `lifecycle_events` + `dispatch_log` |
| Choice 3 | Lifecycle writes through `transition_state()`, not raw SQL |
| Clause 2 | Topic-hash idempotency for `drafter_start.py` |
| Choice 5 | Three-phase git-state policy: start warns, session warns, closeout refuses |
| Clause 6 | FINAL_JSON validation: role=drafter, status=PROPOSAL_READY |
| Implementation Consequence #3 | State sequence: IDLE→ROUTING→DRAFTING→DRAFT_READY→REVIEW_PENDING |
| Boundary clause | No Router, no Tier 7R, no intent classification |
| Choice 3 verification gate | `transition_state()` terminal callability must be verified before implementation |

---

## 2. Prerequisite: Migration 0012

**File:** `runtime/schema/migrations/0012_workflow_run_link.sql`

ADR-014 Choice 1 mandates `workflow_run_id` columns on the two many-side tables.
This migration is additive — no existing rows, no breaking changes, no FK required.

```sql
-- Migration 0012: Add workflow_run_id to lifecycle and dispatch tables
-- Prerequisite for ADR-SEED-014 (Temporary Draft Initiation Contract)
-- Links the lifecycle state machine back to the durable workflow run.
-- One workflow_run → many lifecycle_events, many dispatch_log rows.
-- FK deferred — proposals and dispatches are independent namespaces per
-- migration 0011 comment ("no proposals table exists yet").

ALTER TABLE lifecycle_events ADD COLUMN workflow_run_id TEXT;
ALTER TABLE dispatch_log ADD COLUMN workflow_run_id TEXT;

CREATE INDEX IF NOT EXISTS idx_lifecycle_workflow_run
    ON lifecycle_events(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_dispatch_workflow_run
    ON dispatch_log(workflow_run_id);
```

**Verification after applying:**
```bash
sqlite3 data/cis_memory.db "PRAGMA table_info(lifecycle_events);" | grep workflow_run_id
sqlite3 data/cis_memory.db "PRAGMA table_info(dispatch_log);" | grep workflow_run_id
```

Both must return one row each showing `workflow_run_id` with type `TEXT`.

---

## 3. Script Inventory

Three scripts. All live under `tools/pipeline/` (new directory). One gate script
lives under `tools/gates/`.

| Script | Purpose | ADR-014 Source |
|---|---|---|
| `drafter_start.py` | Creates workflow_run + proposal, writes IDLE→ROUTING→DRAFTING | Clause 2, Choice 1 |
| `drafter_session_init.py` | Produces spine-derived briefing for the Drafter | Clause 3 |
| `drafter_closeout.py` | Validates FINAL_JSON, writes DRAFT_READY→REVIEW_PENDING, creates dispatch | Clause 6, Implementation Consequence |
| `gate_drafter_closeout.sh` | Verifies closeout invariants | Per Tier convention |

---

## 4. Script: drafter_start.py

### 4.1 CLI Contract

```
Usage: python3 tools/pipeline/drafter_start.py <intent-text> [--session-id SESSION_ID]

Arguments:
  intent-text     Eric's stated initiating intent. Recorded verbatim.
                  Must be non-empty, non-whitespace.

Options:
  --session-id    Optional session identifier for lifecycle_events.session_id.
                  Defaults to ISO timestamp if omitted.

Exit codes:
  0 — Success (new or existing run returned)
  1 — Input error (empty intent, DB failure)
```

### 4.2 Behavior

1. **Validate input.** Refuse if `intent_text.strip()` is empty.

2. **Open database.** Connect to `data/cis_memory.db` with `row_factory = sqlite3.Row`.
   Use the same DB_PATH convention as `runtime/db/database.py` (`/mnt/projects/cis/data/cis_memory.db`).

3. **Idempotency check.** Hash `intent_text.strip()` with SHA-256.
   Query `workflow_runs` for a row with matching `topic` where `status`
   is NOT in (`'COMPLETE'`, `'ERROR'`, `'ESCALATE'`).
   If found:
   - Query the most recent `lifecycle_events` row for that workflow_run
     to get the `proposal_id`.
   - Print: `EXISTING workflow_run_id=<id> proposal_id=<id>`
   - Exit 0 with the existing IDs. Do not create duplicates.

4. **Create identities.**
   - `workflow_run_id = f"run-{uuid.uuid4().hex[:13]}"` (matches existing convention in `runtime/api/advisor.py:1250`)
   - `proposal_id = str(uuid.uuid4())` (matches existing convention in `runtime/api/orchestration.py:119`)

5. **Insert workflow_runs row.** Use the schema from migration 0004:
   ```sql
   INSERT INTO workflow_runs
     (id, topic, result, requires_eric_review, max_rounds,
      max_consecutive_revisions, rounds_completed, created_at, status)
   VALUES (?, ?, 'CONSENSUS_REACHED', 1, 3, 3, 0, ?, 'PENDING')
   ```
   `topic` = Eric's exact intent text (strip trailing whitespace, preserve internal whitespace).
   `created_at` = `datetime.now(timezone.utc).isoformat()`.
   `status` = `'PENDING'` (not `'IN_PROGRESS'` — the state machine owns progress,
   `workflow_runs.status` is coarse-grained terminal status per ADR-014 Choice 2).

   **Schema constraint note:** `result` is set to `'CONSENSUS_REACHED'` at
   creation because the existing CHECK constraint on `workflow_runs.result`
   only permits `'CONSENSUS_REACHED'`, `'ESCALATE'`, or `'ERROR'`.
   `'PENDING'` is not a valid result value. This is a temporary workaround:
   a freshly initiated run carries `result = 'CONSENSUS_REACHED'` semantically
   before any consensus has occurred. Future schema cleanup should allow a
   non-terminal initial result value (e.g., `'PENDING'` or `'IN_PROGRESS'`)
   but Tier 11C does not modify the CHECK constraint. Any query that filters on
   `result = 'CONSENSUS_REACHED'` should also check `status != 'PENDING'` to
   exclude newly-initiated runs.

6. **Write lifecycle events via transition_state().**
   Import from `runtime.api.orchestration` using the pattern verified in §8:
   ```python
   import sys, os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'runtime'))
   from api.orchestration import transition_state
   ```

   Execute exactly 2 transitions:
   ```python
   row1_id = transition_state(proposal_id, session_id, 'IDLE',    'ROUTING',  'drafter_start.py', db=db)
   row2_id = transition_state(proposal_id, session_id, 'ROUTING',  'DRAFTING', 'drafter_start.py', db=db)
   ```

   **Cold-start precondition:** The first transition (`IDLE→ROUTING`) succeeds
   because `get_current_state()` returns `None` when no prior lifecycle events
   exist, and the state machine treats no-existing-state as equivalent to
   `'IDLE'` (`orchestration.py:154`: `effective_current = current if current
   is not None else 'IDLE'`). All subsequent transitions must use the actual
   current lifecycle state.

   **Capturing return values:** `transition_state()` returns `cursor.lastrowid`
   (verified: `orchestration.py:185`). The return value must be captured and
   used for the `workflow_run_id` backfill:
   ```sql
   UPDATE lifecycle_events SET workflow_run_id = ?
   WHERE id = ? AND workflow_run_id IS NULL
   -- id = row1_id (or row2_id) from transition_state() return value
   ```
   This pattern applies to all `transition_state()` call sites throughout this
   specification.

7. **Record git HEAD.** Run `git rev-parse HEAD` from the CIS repo root.
   Store in a manner observable by `drafter_session_init.py`.
   Implementation: append a row to `workflow_run_artifacts`:
   ```sql
   INSERT INTO workflow_run_artifacts
     (run_id, artifact_type, content, created_at)
   VALUES (?, 'git_head', ?, ?)
   ```
   Where `content` = the git SHA. Column names reflect the live schema
   (`run_id` not `workflow_run_id`; `content` is the single text payload
   column — no `artifact_path` or `artifact_hash` columns exist).

8. **Git-state warning.** Run `git status --porcelain` from the CIS repo root.
   If any lines exist (dirty tracked or untracked), print to stderr:
   ```
   WARNING: Git working tree is not clean. Untracked/dirty files will block closeout.
   Dirty/untracked files:
   <git status --porcelain output, each line indented>
   ```
   Do not refuse. Per ADR-014 Choice 5, initiation only warns.

9. **Output.** Print to stdout:
   ```
   workflow_run_id: <id>
   proposal_id: <id>
   intent_hash: <sha256-hex>
   git_head: <sha>
   ```

### 4.3 What drafter_start.py Must NOT Do

- Classify, route, or interpret the intent (ADR-014 Boundary)
- Create Kanban cards (ADR-013: Kanban retired)
- Create Router/Tier 7R records
- Auto-start the Drafter or Reviewer (ADR-014: dispatch only, no auto-run)
- Write FINAL_JSON (that belongs to the Drafter, not the start script)

---

## 5. Script: drafter_session_init.py

### 5.1 CLI Contract

```
Usage: python3 tools/pipeline/drafter_session_init.py --run-id WORKFLOW_RUN_ID [--brief]

Arguments:
  --run-id        Required. The workflow_run_id from drafter_start.py output.

Options:
  --brief         If set, produce a condensed one-paragraph briefing.
                  Default: full briefing (all sections).

Exit codes:
  0 — Success
  1 — Run not found, DB failure, or empty topic
```

### 5.2 Behavior

1. **Validate input.** `--run-id` is required. Refuse if missing.

2. **Open database.** Same pattern as `drafter_start.py`.

3. **Load workflow_run.** Query `SELECT * FROM workflow_runs WHERE id = ?`.
   Refuse with error if not found. Refuse if `topic` is NULL or empty.

4. **Load spine context.** Execute the following queries:

   a. **Current build tier state:**
      ```sql
      SELECT node_label, tier, status FROM build_plan_nodes
      WHERE status = 'PENDING' ORDER BY sequence LIMIT 5
      ```

   b. **Most recent completed tiers:**
      ```sql
      SELECT node_label, tier, completed_at FROM build_plan_nodes
      WHERE status = 'COMPLETE' ORDER BY completed_at DESC LIMIT 3
      ```

   c. **Active blockers:**
      ```sql
      SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'
      ```

   d. **Active decisions (ADRs):**
      ```sql
      SELECT id, label, decision FROM project_decisions
      WHERE status = 'DECIDED' AND id LIKE 'ADR-SEED-%'
      ORDER BY decided_at DESC
      ```

   e. **Open questions:**
      ```sql
      SELECT id, question FROM open_questions WHERE status = 'OPEN'
      ```

   f. **Current lifecycle state:**
      Use `get_current_state(proposal_id, db)` from `orchestration.py`.
      (The `proposal_id` is resolved from `lifecycle_events`:
      `SELECT DISTINCT proposal_id FROM lifecycle_events WHERE workflow_run_id = ?`)

   g. **Prior lifecycle events for this run:**
      ```sql
      SELECT from_state, to_state, timestamp, initiated_by FROM lifecycle_events
      WHERE workflow_run_id = ? ORDER BY id ASC
      ```

5. **Load git state.** Run `git rev-parse HEAD` and `git status --porcelain`
   from the CIS repo root.

6. **Git-state warning.** If `git status --porcelain` produces any output, print
   the same warning format as `drafter_start.py` §4.2.8.

7. **Assemble and print briefing.** The output is plain text, structured as:

   ```
   ═══ Drafter Session Briefing ═══
   Workflow Run: <workflow_run_id>
   Proposal: <proposal_id>
   Git HEAD: <sha>

   ─── Eric's Intent ───
   <workflow_runs.topic — full text>

   ─── Current Lifecycle State ───
   <current state from get_current_state()>

   ─── Lifecycle Trail ───
   <each event: from_state → to_state (timestamp) by initiated_by>

   ─── Build Tier Status ───
   Pending: <list of pending tiers with node_label>
   Recently completed: <list of completed tiers>

   ─── Active Blockers ───
   <list or "None">

   ─── Active Decisions ───
   <ADR-ID: label — decision summary>

   ─── Open Questions ───
   <list or "None">

   ─── Git State ───
   Clean / Dirty with file list
   ```

8. **Exit 0.**

### 5.3 --brief Mode

When `--brief` is set, output only:
```
Run: <workflow_run_id> | State: <lifecycle_state> | Intent: <first 120 chars of topic>
Pending tiers: <count> | Blockers: <count> | Git: clean/dirty
```

### 5.4 What drafter_session_init.py Must NOT Do

- Modify any database rows (read-only)
- Create or modify files
- Interpret or classify the intent
- Start any agent process
- Generate proposals or recommendations

---

## 6. Script: drafter_closeout.py

### 6.1 CLI Contract

```
Usage: python3 tools/pipeline/drafter_closeout.py --run-id WORKFLOW_RUN_ID [--proposal-id PROPOSAL_ID]
       [--drafter-output-file PATH] [--session-id SESSION_ID]

Arguments:
  --run-id              Required. The workflow_run_id.
  --proposal-id         Optional. The proposal_id. If omitted, resolved from lifecycle_events
                        WHERE workflow_run_id = <run_id>.
  --drafter-output-file Optional. Path to a file containing the Drafter's full output.
                        If omitted, reads from stdin.
  --session-id          Optional. Session identifier for lifecycle_events.session_id.
                        Resolution order (first available wins):
                          1. Explicit --session-id argument
                          2. Most recent lifecycle_events.session_id for this run
                          3. ISO timestamp default
```
Exit codes:
  0 — Success (DRAFT_READY → REVIEW_PENDING complete, dispatch created)
  1 — Validation failure (missing FINAL_JSON, wrong role/status, untracked files, DB error)
```

### 6.2 Behavior

1. **Validate input.** `--run-id` is required. If `--drafter-output-file` is set,
   read the file. Otherwise read from stdin until EOF.

2. **Open database.** Same pattern as `drafter_start.py`.

3. **Load workflow_run.** Verify it exists and `status` is not in a terminal state
   (`'COMPLETE'`, `'ERROR'`, `'ESCALATE'`). Refuse if already terminal.

4. **Resolve proposal_id.** If `--proposal-id` provided, use it. Otherwise:
   ```sql
   SELECT DISTINCT proposal_id FROM lifecycle_events
   WHERE workflow_run_id = ? ORDER BY id DESC LIMIT 1
   ```
   Refuse if no proposal_id found.

5. **Git-state enforcement (ADR-014 Choice 5).** Run `git status --porcelain`.
   If any untracked files exist (lines starting with `??`):
   - Print to stderr: `REFUSED: Untracked files exist. Closeout requires clean working tree.`
   - List the untracked files.
   - Exit 1.
   If dirty tracked files exist (lines starting with ` M` or `M `):
   - Print to stderr: `WARNING: Dirty tracked files exist.`
   - List the dirty files.
   - Continue (warn, do not refuse — per Choice 5, closeout refuses untracked only).

6. **Validate Drafter output contains FINAL_JSON.** Parse the Drafter output
   (from file or stdin). Search for a FINAL_JSON block. The block is defined as:
   - A markdown code fence with `json` language tag containing a valid JSON object
   - OR a raw JSON object on its own line(s) at the end of the output
   - The JSON must parse successfully via `json.loads()`.

   If no parseable JSON block is found:
   - Print: `REFUSED: No valid FINAL_JSON block found in Drafter output.`
   - Exit 1.

7. **Validate FINAL_JSON fields (ADR-014 Clause 6).**
   The parsed JSON object must contain:
   - `"role"` with value exactly `"drafter"` (string, case-sensitive)
   - `"status"` with value exactly `"PROPOSAL_READY"` (string, case-sensitive)

   Optional fields (validated if present, ignored if absent):
   - `"summary"`: string, max 500 chars
   - `"recommendation"`: string, max 500 chars
   - `"next_action"`: string, must be one of `"REVIEW_PENDING"`, `"REVISION_READY"`, `"IDLE"`

   If `"role"` != `"drafter"` or `"status"` != `"PROPOSAL_READY"`:
   - Print: `REFUSED: FINAL_JSON role must be "drafter", status must be "PROPOSAL_READY". Got role=<value>, status=<value>.`
   - Exit 1.

8. **Verify state machine position.** Call `get_current_state(proposal_id, db)`.
   Current state must be `'DRAFTING'`. If not:
   - Print: `REFUSED: Current lifecycle state is '<state>', expected 'DRAFTING'. Closeout requires an active DRAFTING session.`
   - Exit 1.

   Also check that no `DRAFT_READY` event already exists for this proposal
   (idempotency protection per ADR-014 Implementation Consequence #6):
   ```sql
   SELECT COUNT(*) FROM lifecycle_events
   WHERE proposal_id = ? AND to_state = 'DRAFT_READY'
   ```
   If count > 0:
   - Print: `REFUSED: DRAFT_READY already recorded for this proposal. Closeout is idempotent — cannot close twice.`
   - Exit 1.

9. **Hash the Drafter output.** Compute SHA-256 of the full Drafter output text.

10. **Write lifecycle event: DRAFTING → DRAFT_READY.**
    ```python
    draft_ready_row_id = transition_state(
        proposal_id, session_id, 'DRAFTING', 'DRAFT_READY',
        'drafter_closeout.py', db=db,
        notes='Drafter output hash: ' + output_hash)
    ```
    Then set `workflow_run_id` using the captured row ID:
    ```sql
    UPDATE lifecycle_events SET workflow_run_id = ?
    WHERE id = ? AND workflow_run_id IS NULL
    -- id = draft_ready_row_id
    ```

11. **Create dispatch to Reviewer (ADR-014 Implementation Consequence).**
    Use `create_dispatch()` from `runtime/api/orchestration`:
    ```python
    dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor='drafter',
        target_agent='hermes-r1',
        target_endpoint='http://127.0.0.1:8643',
        lifecycle_state_at='DRAFT_READY',
        payload=drafter_output_text,
        initiated_by='drafter_closeout.py',
        eric_approved=0,
        db=db
    )
    ```
    `create_dispatch()` returns the new `dispatch_id` (verified: `orchestration.py:225`).
    Then set `workflow_run_id` on the dispatch:
    ```sql
    UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?
    ```
    Per ADR-014: "without auto-running Reviewer" — the dispatch record is created
    but `drafter_closeout.py` does NOT send the HTTP request to port 8643.
    The dispatch exists as a pending record for the Reviewer to pick up.

12. **Write lifecycle event: DRAFT_READY → REVIEW_PENDING.**
    ```python
    review_pending_row_id = transition_state(
        proposal_id, session_id, 'DRAFT_READY', 'REVIEW_PENDING',
        'drafter_closeout.py', db=db, dispatch_ref=dispatch_id)
    ```
    Then set `workflow_run_id` using `review_pending_row_id` as above.

13. **Update workflow_runs status.** Set `status = 'REVIEW_PENDING'` and
    `updated_at = <now>`:
    ```sql
    UPDATE workflow_runs SET status = 'REVIEW_PENDING', updated_at = ?
    WHERE id = ?
    ```

14. **Output.** Print to stdout:
    ```
    CLOSEOUT COMPLETE
    workflow_run_id: <id>
    proposal_id: <id>
    dispatch_id: <id>
    drafter_output_hash: <sha256-hex>
    lifecycle_state: REVIEW_PENDING
    target: hermes-r1 (port 8643)
    ```

### 6.3 What drafter_closeout.py Must NOT Do

- Auto-run the Reviewer or send HTTP to port 8643 (dispatch record only)
- Auto-commit to git (closeout is a state-machine event, git commit is separate)
- Regenerate AGENTS.md (that is a separate export step, not lifecycle state)
- Run gate scripts (the gate runs separately against closeout evidence)
- Modify the Drafter's output text
- Create Kanban cards (ADR-013)

---

## 7. Gate: gate_drafter_closeout.sh

### 7.1 Location

`tools/gates/gate_drafter_closeout.sh`

### 7.2 Behavior

Runs after `drafter_closeout.py` completes successfully. Verifies:

1. **Migration 0012 applied.** `workflow_run_id` column exists on both tables.
   ```bash
   sqlite3 data/cis_memory.db "PRAGMA table_info(lifecycle_events);" | grep -q workflow_run_id
   sqlite3 data/cis_memory.db "PRAGMA table_info(dispatch_log);" | grep -q workflow_run_id
   ```

2. **Lifecycle trail exists.** Verify the correct number of events.
   The happy-path sequence produces exactly 4 lifecycle events:
   IDLE→ROUTING, ROUTING→DRAFTING (from drafter_start.py)
   DRAFTING→DRAFT_READY, DRAFT_READY→REVIEW_PENDING (from drafter_closeout.py)
   Tested by: `sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM lifecycle_events WHERE workflow_run_id = '<run_id>';"`
   Must return 4.

3. **Correct state transition sequence.** Verify the to_state trail:
   ```bash
   sqlite3 data/cis_memory.db "SELECT to_state FROM lifecycle_events WHERE workflow_run_id = '<run_id>' ORDER BY id ASC;"
   ```
   Must include the subsequence: ROUTING, DRAFTING, DRAFT_READY, REVIEW_PENDING (in order).

4. **Dispatch exists and is PENDING.** Verify:
   ```bash
   sqlite3 data/cis_memory.db "SELECT current_status FROM dispatch_log WHERE workflow_run_id = '<run_id>';"
   ```
   Must return `PENDING`.

5. **Dispatch targets Reviewer (port 8643).** Verify:
   ```bash
   sqlite3 data/cis_memory.db "SELECT target_agent, target_endpoint FROM dispatch_log WHERE workflow_run_id = '<run_id>';"
   ```
   Must return `hermes-r1` and `http://127.0.0.1:8643`.

6. **No scope creep.** Verify no Router/Tier 7R imports in any of the three scripts:
   ```bash
   ! grep -qE 'from.*tier7r|import.*tier7r|from.*router|import.*router|process_manager|classifier|WorkIntent' tools/pipeline/drafter_*.py
   ```

7. **Git state clean.** Verify no untracked files:
   ```bash
   [ -z "$(git status --porcelain | grep '^??')" ]
   ```

### 7.3 CLI Contract

```
Usage: bash tools/gates/gate_drafter_closeout.sh --run-id WORKFLOW_RUN_ID

Exit codes:
  0 — All checks pass
  1 — One or more checks fail
```

### 7.4 Output Format

```
=== Tier 11C: Drafter Closeout Gate ===
Run ID: <id>
1. Migration 0012: PASS / FAIL
2. Lifecycle trail ≥ 5 events: PASS / FAIL
3. State sequence (ROUTING→DRAFTING→DRAFT_READY→REVIEW_PENDING): PASS / FAIL
4. Dispatch PENDING: PASS / FAIL
5. Dispatch target (hermes-r1:8643): PASS / FAIL
6. No scope creep: PASS / FAIL
7. Git clean (no untracked files): PASS / FAIL
```

---

## 8. Verification Gate (Pre-Implementation)

Before Tier 11C implementation begins, verify:

### 8.1 transition_state() terminal callability

**Status:** VERIFIED 2026-06-15.

```python
import sys, os
sys.path.insert(0, '/mnt/projects/cis/runtime')
from api.orchestration import transition_state, get_current_state, generate_proposal_id
# Works without Flask context. No flask imports in transition_state source.
# ALLOWED_TRANSITIONS count: 49 state pairs.
# Successfully executed: IDLE → ROUTING, verified current_state = 'ROUTING'.
# Cleanup: test row deleted.
```

Evidence file for Reviewer: `/mnt/projects/cis/runtime/tests/test_transition_state_terminal.py`
(to be written as part of Tier 11C implementation, exercising the full
IDLE→ROUTING→DRAFTING→DRAFT_READY→REVIEW_PENDING chain from a terminal script).

---

## 9. State Sequence (Normative)

```
Eric states intent
     │
     ▼
drafter_start.py:
  [IDLE → ROUTING]  workflow_run_id + proposal_id created
  [ROUTING → DRAFTING]  Drafter session active
     │
     ▼
drafter_session_init.py:
  Briefing from spine + git state
     │
     ▼
Drafter (V4-Pro, port 8645) produces proposal + FINAL_JSON:
  { "role": "drafter", "status": "PROPOSAL_READY", ... }
     │
     ▼
drafter_closeout.py:
  [DRAFTING → DRAFT_READY]   Proposal complete, hash logged
  Create dispatch → hermes-r1:8643 (PENDING, no HTTP call)
  [DRAFT_READY → REVIEW_PENDING]  Awaiting Reviewer
     │
     ▼
gate_drafter_closeout.sh:
  Verify migration, lifecycle trail, dispatch, no scope creep, git clean
     │
     ▼
Reviewer (r1, port 8643) picks up dispatch
  (Reviewer initiation is out of Tier 11C scope)
```

---

## 10. File Manifest

| File | Path | Type |
|---|---|---|
| Migration 0012 | `runtime/schema/migrations/0012_workflow_run_link.sql` | New |
| drafter_start.py | `tools/pipeline/drafter_start.py` | New |
| drafter_session_init.py | `tools/pipeline/drafter_session_init.py` | New |
| drafter_closeout.py | `tools/pipeline/drafter_closeout.py` | New |
| gate_drafter_closeout.sh | `tools/gates/gate_drafter_closeout.sh` | New |
| Tier 11C spec | `docs/CIS_TIER_11C_DRAFTER_REVIEWER_HANDOFF_SPECIFICATION.md` | This document |

No existing files are modified. `runtime/api/orchestration.py` is imported by
the three scripts but not patched. The `sys.path.insert` import pattern is
tested and verified.

---

## 11. Boundary (What Tier 11C Must NOT Include)

Per ADR-014 Boundary clause:

- No Router implementation
- No intent classification or topic routing
- No project promotion (Pass 5)
- No generalized workflow automation
- No multi-project initiation
- No Schedule/field-use work (SWA)
- No Tier 7R imports or dependencies
- No Kanban integration (ADR-013: Kanban retired)
- No auto-running of Reviewer (dispatch record only)
- No automatic git commit (closeout is state-machine event, commit is separate)
- No AGENTS.md regeneration (separate export pipeline step)

Tier 11C is the Drafter-side handoff only. Reviewer initiation (`REVIEW_PENDING → REVIEWING`)
is out of scope. Reviewer closeout (`REVIEWING → REVIEW_COMPLETE`) is out of scope.
The implementation loop (DRAFTING revision after OBJECTIONS) is out of scope —
ADR-014 defines the initial DRAFT_READY→REVIEW_PENDING handoff only; revision
loops are deferred to future Reviewer-side or Orchestrator integration work.

---

## 12. Acceptance Tests

### 12.1 Happy Path

```
Given:  Eric runs: drafter_start.py "Draft a proposal for Tier 11C specification"
When:   drafter_session_init.py --run-id <id> produces briefing
And:    Drafter produces proposal ending with {"role":"drafter","status":"PROPOSAL_READY"}
And:    drafter_closeout.py --run-id <id> < proposal_output.txt
Then:   Exit 0, CLOSEOUT COMPLETE printed
And:    lifecycle_events has trail: ROUTING → DRAFTING → DRAFT_READY → REVIEW_PENDING
And:    dispatch_log has one row: target_agent=hermes-r1, target_endpoint=http://127.0.0.1:8643, current_status=PENDING
And:    gate_drafter_closeout.sh --run-id <id> returns 0 with all 7 checks PASS
```

### 12.2 Idempotency

```
Given:  drafter_start.py "Draft a proposal for Tier 11C specification" has already run
When:   Same command runs again with identical intent text
Then:   Exit 0, "EXISTING workflow_run_id=<id> proposal_id=<id>" printed
And:    No new rows in workflow_runs or lifecycle_events
```

### 12.3 Missing FINAL_JSON

```
Given:  Drafter output has no JSON block
When:   drafter_closeout.py --run-id <id> < output.txt
Then:   Exit 1, "REFUSED: No valid FINAL_JSON block found"
And:    No lifecycle events written
```

### 12.4 Wrong FINAL_JSON Role

```
Given:  Drafter output has {"role":"reviewer","status":"PROPOSAL_READY"}
When:   drafter_closeout.py --run-id <id> < output.txt
Then:   Exit 1, "REFUSED: FINAL_JSON role must be 'drafter', status must be 'PROPOSAL_READY'"
```

### 12.5 Untracked Files Block Closeout

```
Given:  Untracked files exist (git status --porcelain shows ??)
When:   drafter_closeout.py --run-id <id> < output.txt
Then:   Exit 1, "REFUSED: Untracked files exist"
```

### 12.6 Double Closeout Refused

```
Given:  drafter_closeout.py has successfully run once
When:   Same command runs again with same run-id
Then:   Exit 1, "REFUSED: DRAFT_READY already recorded"
```

---

## 13. FINAL_JSON (Per ADR-SEED-012 Contract)

The Drafter's output must end with a FINAL_JSON block. This specification
re-states the ADR-SEED-012 (Orchestrator Validation Contract) requirements as
they apply to the Drafter role:

```json
{
  "role": "drafter",
  "status": "PROPOSAL_READY",
  "summary": "<concise summary of the proposal>",
  "recommendation": "<the Drafter's recommendation>",
  "next_action": "REVIEW_PENDING"
}
```

Valid status values for Drafter (ADR-SEED-012 role-scoped):
- `PROPOSAL_READY` — Initial proposal ready for Reviewer challenge
- `REVISION_READY` — Revised proposal after addressing Reviewer objections

The `next_action` field is optional but when present must be one of:
`"REVIEW_PENDING"`, `"REVISION_READY"`, `"IDLE"`.

The orchestrator validates only the FINAL_JSON block, not freeform body text (ADR-SEED-012).
Markdown heading presence (### Summary, ### Recommendation) must not cause validation failure.

---

*End of Tier 11C Specification.*
*Next step: V4 Reviewer (r1, port 8643) independent challenge.*
