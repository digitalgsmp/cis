# CIS Tier 11D — Reviewer-Side Handoff Specification

**Status:** REVISED_DRAFT — revisions applied per Reviewer #1 (r1:8643) feedback, awaiting re-review
**Author:** V4 Drafter (hermes-v4pro, port 8645)
**Date:** 2026-06-16
**Revision:** 1 (2026-06-16 — R1-R9 applied)
**Binding foundation:** ADR-SEED-014 (Temporary Draft Initiation Contract), ADR-SEED-012 (Orchestrator Validation Contract)
**Supersedes:** None (first Tier 11D specification)
**Prerequisite tiers:** 11C (Drafter-side handoff)

---

## 1. Binding Authority

Tier 11D is the Reviewer-side counterpart to Tier 11C. Where 11C handles the Drafter's
side of the handoff (IDLE → ROUTING → DRAFTING → DRAFT_READY → REVIEW_PENDING), 11D
handles the Reviewer's side (REVIEW_PENDING → REVIEWING → REVIEW_COMPLETE → verdict routing).

ADR-SEED-012 (Orchestrator Validation Contract) defines the Reviewer's FINAL_JSON contract:
- Role-scoped status values: `CONSENSUS_REACHED`, `OBJECTIONS`, or `ESCALATE`
- FINAL_JSON is the authoritative signal; markdown headings are documentation

ADR-SEED-014 (Temporary Draft Initiation Contract) defines the overall pipeline structure
that 11D completes. Specifically:
- Clause 6: "Reviewer challenge begins only after Drafter emits a valid FINAL_JSON"
- The dispatch created by `drafter_closeout.py` is PENDING; 11D picks it up
- The pipeline diagram in ADR-014 §Implementation Consequence #3 ends with "Reviewer receives dispatch"

Tier 11C states in its §11 Boundary:
> "Tier 11C is the Drafter-side handoff only. Reviewer initiation (`REVIEW_PENDING → REVIEWING`)
> is out of scope. Reviewer closeout (`REVIEWING → REVIEW_COMPLETE`) is out of scope."

Tier 11D fills exactly these two gaps.

Key citations:

| Source | What It Requires |
|---|---|
| ADR-012 (Orchestrator Validation Contract) | Reviewer FINAL_JSON: role=reviewer, status=CONSENSUS_REACHED\|OBJECTIONS\|ESCALATE |
| ADR-014 Clause 6 | Reviewer challenge begins after valid Drafter FINAL_JSON; Reviewer compares proposal against Eric's recorded intent |
| ADR-014 Implementation Consequence #3 | Pipeline: DRAFT_READY → REVIEW_PENDING → (11D fills: REVIEWING → REVIEW_COMPLETE → verdict) |
| Tier 11C §11 Boundary | "Reviewer initiation (REVIEW_PENDING → REVIEWING) is out of scope. Reviewer closeout is out of scope." |
| ADR-013 | Kanban retired — no Kanban cards, no Kanban integration |
| orchestration.py ALLOWED_TRANSITIONS | REVIEW_PENDING→REVIEWING, REVIEWING→REVIEW_COMPLETE, REVIEW_COMPLETE→REVISE_REQUESTED, REVIEW_COMPLETE→ERIC_APPROVAL_GATE already exist |
| Tier 11B Eric Gate endpoint | `/api/pipeline/eric-gate` (runtime/api/pipeline_views.py:70) |

---

## 2. Prerequisites

No new migrations required. Migration 0012 (applied in Tier 11C) already added
`workflow_run_id` to `lifecycle_events` and `dispatch_log`. All state names are
already in `ALLOWED_TRANSITIONS`.

**Verification before 11D implementation:**
```bash
# Confirm required transitions exist in orchestration.py:
grep -E "REVIEW_PENDING.*REVIEWING|REVIEWING.*REVIEW_COMPLETE|REVIEW_COMPLETE.*REVISE_REQUESTED|REVIEW_COMPLETE.*ERIC_APPROVAL_GATE" runtime/api/orchestration.py
# Confirm migration 0012 applied:
sqlite3 data/cis_memory.db "PRAGMA table_info(lifecycle_events);" | grep workflow_run_id
sqlite3 data/cis_memory.db "PRAGMA table_info(dispatch_log);" | grep workflow_run_id
# Confirm 11C drafter scripts exist:
ls tools/pipeline/drafter_start.py tools/pipeline/drafter_session_init.py tools/pipeline/drafter_closeout.py
```

---

## 3. Script Inventory

Three scripts + one gate. All live under `tools/pipeline/`.

| Script | Purpose | Key State Transitions |
|---|---|---|
| `reviewer_pickup.py` | Finds next PENDING dispatch for hermes-r1, marks IN_FLIGHT, transitions REVIEW_PENDING → REVIEWING | REVIEW_PENDING → REVIEWING |
| `reviewer_session_init.py` | Produces spine-derived briefing for the Reviewer (Drafter proposal, Eric's intent, active ADRs, lifecycle trail) | Read-only |
| `reviewer_closeout.py` | Validates Reviewer FINAL_JSON, writes REVIEWING → REVIEW_COMPLETE, routes to REVISE_REQUESTED or ERIC_APPROVAL_GATE | REVIEWING → REVIEW_COMPLETE → (REVISE_REQUESTED \| ERIC_APPROVAL_GATE) |
| `gate_reviewer_closeout.sh` | Verifies closeout invariants | Read-only gate |

---

## 4. Script: reviewer_pickup.py

### 4.1 CLI Contract

```
Usage: python3 tools/pipeline/reviewer_pickup.py [--run-id WORKFLOW_RUN_ID | --dispatch-id DISPATCH_ID]
       [--session-id SESSION_ID]

Arguments:
  --run-id         Optional. Pick up the PENDING dispatch for this workflow_run.
                   Mutually exclusive with --dispatch-id.
  --dispatch-id    Optional. Pick up a specific dispatch by ID.
                   Mutually exclusive with --run-id.
  --session-id     Optional. Session identifier for lifecycle_events.session_id.

Exit codes:
  0 — Success (dispatch claimed, REVIEW_PENDING → REVIEWING)
  1 — No PENDING dispatch found, already claimed, transition error, or DB failure
```

If neither `--run-id` nor `--dispatch-id` is provided, `reviewer_pickup.py` lists
all PENDING dispatches for `target_agent = 'hermes-r1'` and exits 0, printing each
dispatch with its workflow_run_id and proposal_id. This is the "show queue" mode.

### 4.2 Behavior (Claim Mode)

When `--run-id` or `--dispatch-id` is provided:

1. **Validate input.** One and only one of `--run-id` or `--dispatch-id` must be
   provided. Refuse if both or neither are given (when claiming, not listing).

2. **Open database.** Connect to `data/cis_memory.db`.
   Use `sys.path.insert` pattern to import from `runtime.api.orchestration`:
   ```python
   import sys, os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'runtime'))
   from api.orchestration import transition_state, get_current_state, update_dispatch_inflight
   ```

3. **Find the dispatch.** If `--dispatch-id`, query directly.
   If `--run-id`, query PENDING dispatches for that workflow_run:
   ```sql
   SELECT * FROM dispatch_log
   WHERE workflow_run_id = ? AND current_status = 'PENDING'
   ORDER BY timestamp_initiated ASC LIMIT 1
   ```
   Refuse if no PENDING dispatch found. Refuse if `current_status != 'PENDING'`
   (already claimed/completed/failed).

4. **Resolve proposal_id and session_id.** From the dispatch row:
   - `proposal_id` = dispatch row's `proposal_id`
   - `session_id` resolution order (matching 11C's `resolve_session_id`):
     1. `--session-id` if provided
     2. Most recent `session_id` from `lifecycle_events` for this `workflow_run_id`
     3. ISO timestamp default

5. **Verify current lifecycle state.** Call `get_current_state(proposal_id, db)`.
   Must be exactly `'REVIEW_PENDING'`. If not:
   - Print: `REFUSED: Current lifecycle state is '<state>', expected 'REVIEW_PENDING'.`
   - Exit 1.

6. **Mark dispatch IN_FLIGHT.** Call `update_dispatch_inflight(dispatch_id, db)`.
   This updates `dispatch_log.current_status = 'IN_FLIGHT'` and writes a
   `dispatch_events` row with `event_type = 'IN_FLIGHT'`.

7. **Transition state: REVIEW_PENDING → REVIEWING.**
   ```python
   reviewing_row_id = transition_state(
       proposal_id, session_id,
       'REVIEW_PENDING', 'REVIEWING',
       'reviewer_pickup.py', db=db,
       dispatch_ref=dispatch_id)
   ```
   Then backfill `workflow_run_id`:
   ```sql
   UPDATE lifecycle_events SET workflow_run_id = ?
   WHERE id = ? AND workflow_run_id IS NULL
   ```

8. **Update workflow_runs status.**
   ```sql
   UPDATE workflow_runs SET status = 'REVIEWING', updated_at = ?
   WHERE id = ?
   ```

9. **Output.** Print to stdout:
   ```
   CLAIMED
   dispatch_id: <id>
   workflow_run_id: <id>
   proposal_id: <id>
   target_endpoint: http://127.0.0.1:8643
   lifecycle_state: REVIEWING
   ```

### 4.3 Behavior (List Mode)

When neither `--run-id` nor `--dispatch-id` is provided:

1. Query all PENDING dispatches for `hermes-r1`:
   ```sql
   SELECT d.dispatch_id, d.workflow_run_id, d.proposal_id,
          d.timestamp_initiated, d.payload_summary,
          w.topic
   FROM dispatch_log d
   LEFT JOIN workflow_runs w ON d.workflow_run_id = w.id
   WHERE d.target_agent = 'hermes-r1' AND d.current_status = 'PENDING'
   ORDER BY d.timestamp_initiated ASC
   ```

2. Print each dispatch with its summary. If none found, print "No PENDING dispatches."

### 4.4 What reviewer_pickup.py Must NOT Do

- Send HTTP to port 8643 (claim only — does not invoke the Reviewer)
- Auto-start the Reviewer agent process
- Interpret or classify the proposal
- Create Kanban cards (ADR-013)
- Create Router/Tier 7R records

---

## 5. Script: reviewer_session_init.py

### 5.1 CLI Contract

```
Usage: python3 tools/pipeline/reviewer_session_init.py --run-id WORKFLOW_RUN_ID [--brief]

Arguments:
  --run-id         Required. The workflow_run_id.
  --brief          If set, produce condensed briefing.

Exit codes:
  0 — Success
  1 — Run not found, dispatch not found, or DB failure
```

### 5.2 Behavior

1. **Validate input.** `--run-id` is required.

2. **Open database.** Same pattern.

3. **Load workflow_run.** Query `SELECT * FROM workflow_runs WHERE id = ?`.
   Refuse if not found.

4. **Load the dispatch.** Query the IN_FLIGHT or PENDING dispatch for this run:
   ```sql
   SELECT * FROM dispatch_log
   WHERE workflow_run_id = ? AND current_status IN ('PENDING', 'IN_FLIGHT')
   ORDER BY timestamp_initiated DESC LIMIT 1
   ```

5. **Extract the Drafter's proposal.** The dispatch's `payload_summary` (first 500 chars)
   is displayed. The full proposal text is the `payload` — but this was set by
   `drafter_closeout.py` as the full Drafter output text. Since `dispatch_log`
   stores `payload_hash` and `payload_summary` but NOT the full payload body
   (per the existing `create_dispatch()` function), the full proposal is retrieved
   from the lifecycle trail context:
   - The Drafter output hash is stored in the `DRAFTING → DRAFT_READY` lifecycle
     event's `notes` field (format: "Drafter output hash: <sha256>").
   - The full proposal text is what was piped to `drafter_closeout.py`.
   - For the Reviewer briefing, the proposal summary (first 500 chars) is sufficient
     context. The Reviewer accesses the full proposal by reading the Drafter's
     original output from the session or from stdin during the review session.

   **Design note:** Full payload persistence is a known gap. The current `dispatch_log`
   schema stores `payload_hash` and `payload_summary` (500 chars max) but not the full
   body. This is sufficient for the briefing — the Reviewer receives the full proposal
   as a separate artifact. A future tier (likely Unified Memory) should add
   `payload_full` or a separate table for full dispatch bodies.

6. **Load spine context.** Execute queries:
   a. **Eric's original intent:** `SELECT topic FROM workflow_runs WHERE id = ?`
   b. **Active decisions (ADRs):**
      ```sql
      SELECT id, label, decision FROM project_decisions
      WHERE status = 'DECIDED' ORDER BY decided_at DESC
      ```
   c. **Active blockers:**
      ```sql
      SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'
      ```
   d. **Build tier status:**
      ```sql
      SELECT node_label, tier, status FROM build_plan_nodes
      WHERE status = 'PENDING' ORDER BY sequence LIMIT 5
      ```
   e. **Lifecycle trail for this run:**
      ```sql
      SELECT from_state, to_state, timestamp, initiated_by, notes
      FROM lifecycle_events WHERE workflow_run_id = ? ORDER BY id ASC
      ```
   f. **Current lifecycle state:** via `get_current_state(proposal_id, db)`
   g. **Prior deliberation rounds (if any):**
      ```sql
      SELECT round_number, drafter_role, reviewer_role,
             reviewer_signal, created_at
      FROM deliberation_rounds WHERE run_id = ? ORDER BY round_number ASC
      ```

7. **Load git state.** Run `git rev-parse HEAD` and `git status --porcelain`.

8. **Git-state warning.** Same format as 11C: warn on dirty/untracked, do not refuse.

9. **Assemble and print briefing:**
   ```
   ═══ Reviewer Session Briefing ═══
   Workflow Run: <workflow_run_id>
   Proposal: <proposal_id>
   Dispatch: <dispatch_id>
   Git HEAD: <sha>

   ─── Eric's Original Intent ───
   <workflow_runs.topic>

   ─── Drafter Proposal Summary ───
   <dispatch_log.payload_summary>

   ─── Current Lifecycle State ───
   REVIEWING

   ─── Lifecycle Trail ───
   <each event: from_state → to_state (timestamp) by initiated_by>

   ─── Prior Deliberation Rounds ───
   Round <N>: status=<status> | <brief>
   (or "None — initial review")

   ─── Active Decisions ───
   <ADR-ID: label — decision summary>

   ─── Active Blockers ───
   <list or "None">

   ─── Build Tier Status ───
   Pending: <list>

   ─── Git State ───
   Clean / Dirty with file list
   ```

### 5.3 What reviewer_session_init.py Must NOT Do

- Modify any database rows (read-only)
- Interpret or classify the proposal
- Pre-judge the review outcome
- Start any agent process

---

## 6. Script: reviewer_closeout.py

### 6.1 CLI Contract

```
Usage: python3 tools/pipeline/reviewer_closeout.py --run-id WORKFLOW_RUN_ID
       [--proposal-id PROPOSAL_ID] [--reviewer-output-file PATH] [--session-id SESSION_ID]

Arguments:
  --run-id                Required. The workflow_run_id.
  --proposal-id           Optional. Resolved from lifecycle_events if omitted.
  --reviewer-output-file  Optional. Path to Reviewer's full output (proposal + findings + FINAL_JSON).
                          If omitted, reads from stdin.
  --session-id            Optional. Resolution order: explicit → most recent lifecycle → ISO default.

Exit codes:
  0 — Success (REVIEWING → REVIEW_COMPLETE → verdict routing complete)
  1 — Validation failure (missing FINAL_JSON, wrong role/status, DB error)
```

### 6.2 Behavior

1. **Validate input.** `--run-id` is required. Read Reviewer output from file or stdin.

2. **Open database.** Same pattern.

3. **Load workflow_run.** Verify it exists.

4. **Resolve proposal_id.** From `--proposal-id` or lifecycle_events.

5. **Verify current lifecycle state.** Must be `'REVIEWING'`. If not:
   - Print: `REFUSED: Current lifecycle state is '<state>', expected 'REVIEWING'.`
   - Exit 1.

6. **Idempotency check.** Verify no `REVIEW_COMPLETE` event already exists:
   ```sql
   SELECT COUNT(*) FROM lifecycle_events
   WHERE proposal_id = ? AND to_state = 'REVIEW_COMPLETE'
   ```
   If count > 0:
   - Print: `REFUSED: REVIEW_COMPLETE already recorded. Closeout is idempotent.`
   - Exit 1.

7. **Git-state enforcement (same policy as 11C).** Run `git status --porcelain`.
   - Untracked files (`??`): REFUSE, exit 1.
   - Dirty tracked files (` M` or `M `): WARN, continue.

8. **Validate Reviewer output contains FINAL_JSON.** Search for a FINAL_JSON block
   (markdown code fence with `json` tag, or raw JSON at end of output).
   Must parse via `json.loads()`.

   If no parseable JSON block found:
   - Print: `REFUSED: No valid FINAL_JSON block found in Reviewer output.`
   - Exit 1.

9. **Validate FINAL_JSON fields (ADR-SEED-012 Reviewer contract).**
   The parsed JSON must contain:
   - `"role"` = `"reviewer"` (string, case-sensitive)
   - `"status"` = one of `"CONSENSUS_REACHED"`, `"OBJECTIONS"`, `"ESCALATE"` (string, case-sensitive)

   Optional fields (validated if present):
   - `"summary"`: string, max 500 chars
   - `"recommendation"`: string, max 500 chars
   - `"next_action"`: string, must be one of `"REVISE_REQUESTED"`, `"ERIC_APPROVAL_GATE"`, `"IDLE"`

   If role or status is wrong:
   - Print: `REFUSED: FINAL_JSON role must be "reviewer", status must be CONSENSUS_REACHED|OBJECTIONS|ESCALATE. Got role=<value>, status=<value>.`
   - Exit 1.

10. **Hash the Reviewer output.** Compute SHA-256 of full output text.

11. **Determine verdict routing.** Based on FINAL_JSON status:
    - `CONSENSUS_REACHED` → route to `ERIC_APPROVAL_GATE`
    - `OBJECTIONS` → route to `REVISE_REQUESTED` (back to Drafter for revision)
    - `ESCALATE` → route to `ERIC_APPROVAL_GATE` (with escalation flag)

12. **Verify verdict routing is allowed.** If `OBJECTIONS`, check that a revision
    loop would not exceed `max_consecutive_revisions` (default 3 from workflow_runs).
    ```sql
    SELECT rounds_completed, max_consecutive_revisions FROM workflow_runs WHERE id = ?
    ```
    If `rounds_completed >= max_consecutive_revisions` and status is `OBJECTIONS`:
    - Print: `WARNING: Max revision rounds reached. Forcing ESCALATE routing.`
    - Override the routing variable: `routing = 'ERIC_APPROVAL_GATE'`
    - Set `escalation_forced = True` (used in step 15 notes and step 16 result)
    - Do NOT create a return dispatch (step 18 will be skipped)

    If revision rounds remain, set `routing` based on status:
    ```python
    if escalation_forced:
        routing = 'ERIC_APPROVAL_GATE'
    elif status == 'CONSENSUS_REACHED':
        routing = 'ERIC_APPROVAL_GATE'
    elif status == 'ESCALATE':
        routing = 'ERIC_APPROVAL_GATE'
    else:  # OBJECTIONS with rounds remaining
        routing = 'REVISE_REQUESTED'
    ```

13. **Write lifecycle event: REVIEWING → REVIEW_COMPLETE.**
    ```python
    review_complete_row_id = transition_state(
        proposal_id, session_id,
        'REVIEWING', 'REVIEW_COMPLETE',
        'reviewer_closeout.py', db=db,
        notes=f'Reviewer output hash: {reviewer_output_hash}')
    # Backfill workflow_run_id
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? WHERE id = ?",
        (run_id, review_complete_row_id))
    db.commit()
    ```

14. **Record deliberation round.** The `deliberation_rounds` schema is:
    ```sql
    CREATE TABLE deliberation_rounds (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id          TEXT NOT NULL REFERENCES workflow_runs(id),
        round_number    INTEGER NOT NULL,
        drafter_role    TEXT NOT NULL,
        drafter_output  TEXT NOT NULL,
        reviewer_role   TEXT NOT NULL,
        reviewer_signal TEXT NOT NULL CHECK (reviewer_signal IN
                          ('OBJECTIONS','CONSENSUS_REACHED','ESCALATE','ERROR')),
        objections_json TEXT,
        revision_number INTEGER NOT NULL DEFAULT 1,
        requires_eric_review INTEGER NOT NULL DEFAULT 1,
        created_at      TEXT NOT NULL,
        UNIQUE(run_id, round_number)
    );
    ```
    Since `reviewer_signal` is NOT NULL, there is no "open round" concept —
    each round row is complete when written. The Reviewer always INSERTs a new
    round with `round_number = rounds_completed + 1`. The `UNIQUE(run_id, round_number)`
    constraint prevents duplicate round writes.

    ```sql
    INSERT INTO deliberation_rounds
      (run_id, round_number, drafter_role, drafter_output,
       reviewer_role, reviewer_signal, objections_json,
       revision_number, requires_eric_review, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ```
    Where:
    - `run_id` = workflow_run_id
    - `round_number` = workflow_runs.rounds_completed + 1
    - `drafter_role` = `'drafter'`
    - `drafter_output` = Drafter proposal hash (from dispatch_log.payload_hash for this run)
    - `reviewer_role` = `'reviewer'`
    - `reviewer_signal` = FINAL_JSON status (CONSENSUS_REACHED|OBJECTIONS|ESCALATE)
    - `objections_json` = JSON array of objection strings (if any)
    - `revision_number` = revision count (round_number)
    - `requires_eric_review` = 1 if ESCALATE, else 0
    - `created_at` = UTC ISO timestamp

15. **Write verdict routing lifecycle event.**
    ```python
    verdict_row_id = transition_state(
        proposal_id, session_id,
        'REVIEW_COMPLETE', routing,
        'reviewer_closeout.py', db=db,
        notes=f'Reviewer verdict: {status}' +
              (' (MAX_ROUNDS_EXCEEDED — forced escalation)' if escalation_forced else ''))
    # Backfill workflow_run_id
    db.execute(
        "UPDATE lifecycle_events SET workflow_run_id = ? WHERE id = ?",
        (run_id, verdict_row_id))
    db.commit()
    ```

16. **Update workflow_runs.**
    ```sql
    UPDATE workflow_runs
    SET status = ?, result = ?, rounds_completed = rounds_completed + 1,
        updated_at = ?
    WHERE id = ?
    ```
    Where `status`:
    - `'REVISE_REQUESTED'` if OBJECTIONS
    - `'CONSENSUS_REACHED'` if CONSENSUS_REACHED
    - `'ESCALATE'` if ESCALATE
    And `result`:
    - `'CONSENSUS_REACHED'` if CONSENSUS_REACHED
    - `'ESCALATE'` if ESCALATE or OBJECTIONS-with-max-rounds

17. **Update dispatch log.** Mark the dispatch as SUCCESS via `complete_dispatch()`,
    which updates `dispatch_log` and inserts a `dispatch_events` row:
    ```python
    from api.orchestration import complete_dispatch
    complete_dispatch(
        dispatch_id, 
        http_status_code=0,  # No HTTP involved in reviewer closeout
        response_body=reviewer_output_text,
        db=db)
    ```

18. **If REVISE_REQUESTED, create return dispatch to Drafter.**
    When the verdict is `REVISE_REQUESTED` (OBJECTIONS with rounds remaining):
    ```python
    return_dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor='reviewer',
        target_agent='hermes-v4pro',
        target_endpoint='http://127.0.0.1:8645',
        lifecycle_state_at='REVISE_REQUESTED',
        payload=reviewer_output_text,
        initiated_by='reviewer_closeout.py',
        eric_approved=0,
        db=db
    )
    ```
    Then set `workflow_run_id` on the return dispatch:
    ```sql
    UPDATE dispatch_log SET workflow_run_id = ? WHERE dispatch_id = ?
    ```

19. **Output.** Print to stdout:
    ```
    REVIEWER CLOSEOUT COMPLETE
    workflow_run_id: <id>
    proposal_id: <id>
    verdict: <CONSENSUS_REACHED|OBJECTIONS|ESCALATE>
    routing: <ERIC_APPROVAL_GATE|REVISE_REQUESTED>
    reviewer_output_hash: <sha256-hex>
    ```
    If REVISE_REQUESTED, also print:
    ```
    return_dispatch_id: <id>
    next_action: Drafter (hermes-v4pro:8645) should pick up revision dispatch
    ```

### 6.3 What reviewer_closeout.py Must NOT Do

- Auto-run the Drafter for revision loops (dispatch record only, per 11C convention)
- Auto-advance past ERIC_APPROVAL_GATE (Eric must manually approve)
- Send HTTP to any gateway endpoint
- Modify the Reviewer's output text
- Create Kanban cards (ADR-013)
- Implement the Eric Gate approval flow (that's 11B's domain, and the gate itself)

---

## 7. Gate: gate_reviewer_closeout.sh

### 7.1 Location

`tools/gates/gate_reviewer_closeout.sh`

### 7.2 CLI Contract

```
Usage: bash tools/gates/gate_reviewer_closeout.sh --run-id WORKFLOW_RUN_ID

Exit codes:
  0 — All checks pass
  1 — One or more checks fail
```

### 7.3 Checks

1. **Migration 0012 applied.** `workflow_run_id` exists on lifecycle_events + dispatch_log.

2. **Full lifecycle trail present.** Verify ≥7 events (happy path):
   IDLE→ROUTING, ROUTING→DRAFTING, DRAFTING→DRAFT_READY, DRAFT_READY→REVIEW_PENDING,
   REVIEW_PENDING→REVIEWING, REVIEWING→REVIEW_COMPLETE, REVIEW_COMPLETE→(REVISE_REQUESTED|ERIC_APPROVAL_GATE)

3. **Correct state sequence.** to_state trail must include the subsequence:
   ROUTING, DRAFTING, DRAFT_READY, REVIEW_PENDING, REVIEWING, REVIEW_COMPLETE

4. **Dispatch consumed.** Original drafter→reviewer dispatch must be SUCCESS:
   ```sql
   SELECT current_status FROM dispatch_log
   WHERE workflow_run_id = ? AND source_actor = 'drafter'
   ```
   Must return `SUCCESS`.

5. **Verdict routing valid.** Last lifecycle to_state must be REVISE_REQUESTED or ERIC_APPROVAL_GATE.

6. **If REVISE_REQUESTED: return dispatch exists.** Verify a PENDING dispatch from reviewer→v4pro exists.

7. **Deliberation round recorded.** Verify a deliberation_rounds row with reviewer_status not null exists.

8. **No scope creep.** Verify no Tier 7R/Router imports in reviewer scripts:
   ```bash
   ! grep -qE 'from.*tier7r|import.*tier7r|from.*router|import.*router|process_manager|classifier|WorkIntent' tools/pipeline/reviewer_*.py
   ```

9. **Git clean.** No untracked files.

### 7.4 Output Format

```
=== Tier 11D: Reviewer Closeout Gate ===
Run ID: <id>
1. Migration 0012:                        PASS / FAIL
2. Full lifecycle trail (≥7 events):      PASS / FAIL
3. State sequence correct:                 PASS / FAIL
4. Drafter dispatch SUCCESS:              PASS / FAIL
5. Verdict routing valid:                 PASS / FAIL
6. Return dispatch (if REVISE_REQUESTED): PASS / FAIL / N/A
7. Deliberation round recorded:           PASS / FAIL
8. No scope creep:                         PASS / FAIL
9. Git clean:                              PASS / FAIL
```

---

## 8. State Sequence (Normative)

```
11C (Drafter side):
  Eric states intent
       │
       ▼
  drafter_start.py: IDLE → ROUTING → DRAFTING
       │
       ▼
  Drafter (v4pro:8645) produces proposal + FINAL_JSON
       │
       ▼
  drafter_closeout.py: DRAFTING → DRAFT_READY → REVIEW_PENDING
  Creates dispatch → hermes-r1:8643 (PENDING)
       │
       ▼
  ═══════════════ Tier 11C / 11D boundary ═══════════════
       │
       ▼
11D (Reviewer side — THIS SPEC):
  reviewer_pickup.py:
    Finds PENDING dispatch for hermes-r1
    Marks dispatch IN_FLIGHT
    REVIEW_PENDING → REVIEWING
       │
       ▼
  reviewer_session_init.py:
    Briefing: Eric's intent, Drafter proposal summary,
    active ADRs, lifecycle trail, git state
       │
       ▼
  Reviewer (r1:8643) produces findings + FINAL_JSON:
    { "role": "reviewer", "status": "CONSENSUS_REACHED"|"OBJECTIONS"|"ESCALATE", ... }
       │
       ▼
  reviewer_closeout.py:
    Validates FINAL_JSON
    REVIEWING → REVIEW_COMPLETE
       │
       ├─ CONSENSUS_REACHED → ERIC_APPROVAL_GATE
       │       │
       │       ▼
       │     Eric Gate (11B endpoint) → DIRECTIVE_DRAFTING → ...
       │
       ├─ OBJECTIONS (rounds remain) → REVISE_REQUESTED
       │       │
       │       ▼
       │     Return dispatch → hermes-v4pro:8643 (PENDING)
       │     Drafter picks up → DRAFTING (revision)
       │
       └─ ESCALATE → ERIC_APPROVAL_GATE (with escalation flag)
```

---

## 9. FINAL_JSON (Per ADR-SEED-012 Reviewer Contract)

The Reviewer's output must end with a FINAL_JSON block:

```json
{
  "role": "reviewer",
  "status": "CONSENSUS_REACHED",
  "summary": "<concise summary of review findings>",
  "recommendation": "<the Reviewer's recommendation for next steps>",
  "next_action": "ERIC_APPROVAL_GATE"
}
```

Valid Reviewer status values (ADR-SEED-012 role-scoped):
- `CONSENSUS_REACHED` — Reviewer agrees with Drafter proposal; ready for Eric Gate
- `OBJECTIONS` — Reviewer has specific objections; requires revision
- `ESCALATE` — Irreconcilable disagreement; requires Eric's direct intervention

The `next_action` field is optional. When present, valid values are:
`"ERIC_APPROVAL_GATE"`, `"REVISE_REQUESTED"`, `"IDLE"`.

If `next_action` is present and conflicts with `status` (e.g., status=CONSENSUS_REACHED but
next_action=REVISE_REQUESTED), `reviewer_closeout.py` validates and warns but does not refuse
— the `status` field is authoritative for routing.

---

## 10. File Manifest

| File | Path | Type |
|---|---|---|
| reviewer_pickup.py | `tools/pipeline/reviewer_pickup.py` | New |
| reviewer_session_init.py | `tools/pipeline/reviewer_session_init.py` | New |
| reviewer_closeout.py | `tools/pipeline/reviewer_closeout.py` | New |
| gate_reviewer_closeout.sh | `tools/gates/gate_reviewer_closeout.sh` | New |
| Tier 11D spec | `docs/CIS_TIER_11D_REVIEWER_SIDE_HANDOFF_SPECIFICATION.md` | This document |

No existing files modified. `runtime/api/orchestration.py` is imported (not patched).

---

## 11. Boundary (What Tier 11D Must NOT Include)

- Eric Gate approval flow implementation (11B owns `/api/pipeline/eric-gate`)
- Drafter revision session initiation (handled by re-running drafter_start.py with the return dispatch)
- Full orchestrator loop automation (REVISE_REQUESTED → DRAFTING → ... is manual for now)
- Multi-round auto-cycling (each round is initiated by Eric or a future Orchestrator tier)
- AGENTS.md regeneration (separate export step)
- Automatic git commit
- Router / Tier 7R imports or dependencies
- Kanban integration (ADR-013)
- Intent classification or topic routing

Tier 11D handles the Reviewer's receipt of a dispatch, review session, and closeout with
verdict routing. The Drafter revision pickup (REVISE_REQUESTED → DRAFTING) reuses the existing
11C drafter_start.py with a new intent derived from the return dispatch — no new 11D script
handles that transition.

---

## 12. Acceptance Tests

### 12.1 Happy Path (CONSENSUS_REACHED)

```
Given:  Drafter closeout completed (11C), dispatch PENDING for hermes-r1
When:   reviewer_pickup.py --run-id <id>
Then:   Exit 0, CLAIMED, lifecycle_state=REVIEWING
When:   reviewer_session_init.py --run-id <id>
Then:   Briefing includes Eric's intent, proposal summary, active ADRs
When:   Reviewer produces findings + {"role":"reviewer","status":"CONSENSUS_REACHED"}
And:    reviewer_closeout.py --run-id <id> < review_output.txt
Then:   Exit 0, "REVIEWER CLOSEOUT COMPLETE", verdict=CONSENSUS_REACHED, routing=ERIC_APPROVAL_GATE
And:    lifecycle_events has: REVIEWING → REVIEW_COMPLETE → ERIC_APPROVAL_GATE
And:    dispatch_log shows drafter dispatch = SUCCESS
And:    workflow_runs.status = 'CONSENSUS_REACHED'
And:    gate_reviewer_closeout.sh --run-id <id> exits 0, all 9 checks PASS
```

### 12.2 Objections Path (REVISE_REQUESTED)

```
Given:  Reviewer finds issues, emits {"role":"reviewer","status":"OBJECTIONS"}
When:   reviewer_closeout.py --run-id <id> < review_output.txt
Then:   Exit 0, verdict=OBJECTIONS, routing=REVISE_REQUESTED
And:    Return dispatch created: target_agent=hermes-v4pro, target_endpoint=http://127.0.0.1:8645
And:    workflow_runs.rounds_completed incremented
And:    workflow_runs.status = 'REVISE_REQUESTED'
```

### 12.3 Max Rounds Forced Escalation

```
Given:  workflow_runs.rounds_completed = 3, max_consecutive_revisions = 3
And:    Reviewer emits {"role":"reviewer","status":"OBJECTIONS"}
When:   reviewer_closeout.py --run-id <id> < review_output.txt
Then:   WARNING printed, routing forced to ERIC_APPROVAL_GATE
And:    No return dispatch to Drafter created
And:    lifecycle_events notes include "MAX_ROUNDS_EXCEEDED"
```

### 12.4 Missing FINAL_JSON

```
Given:  Reviewer output has no JSON block
When:   reviewer_closeout.py --run-id <id> < output.txt
Then:   Exit 1, "REFUSED: No valid FINAL_JSON block found"
And:    No lifecycle events written
```

### 12.5 Wrong Role

```
Given:  Reviewer output has {"role":"drafter","status":"CONSENSUS_REACHED"}
When:   reviewer_closeout.py --run-id <id> < output.txt
Then:   Exit 1, "REFUSED: FINAL_JSON role must be 'reviewer'"
```

### 12.6 Double Closeout Refused

```
Given:  reviewer_closeout.py already ran successfully
When:   Same command runs again
Then:   Exit 1, "REFUSED: REVIEW_COMPLETE already recorded"
```

### 12.7 Pickup Queue (List Mode)

```
Given:  2 PENDING dispatches exist for hermes-r1
When:   reviewer_pickup.py (no arguments)
Then:   Both dispatches listed with workflow_run_id, proposal_id, summary
```

---

## 13. Interaction with Existing Tier 11B (Eric Gate)

When the verdict routes to `ERIC_APPROVAL_GATE`, the existing Tier 11B endpoint
(`/api/pipeline/eric-gate`) is the next step. Tier 11D does not implement or call
the Eric Gate — it only transitions the lifecycle state to `ERIC_APPROVAL_GATE`.
The Eric Gate approval and subsequent DIRECTIVE_DRAFTING → DIRECTIVE_READY → EXECUTING
pipeline is existing infrastructure (11B + orchestration.py state machine).

---

*End of Tier 11D Specification.*
*Next step: V4 Reviewer (r1, port 8643) independent challenge.*
