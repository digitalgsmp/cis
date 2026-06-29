# ADR-SEED-014 — Temporary Draft Initiation Contract Before Router/Tier 7R

**Status:** REVIEWED (r1 objections resolved, pending Eric Gate approval)
**ADR ID:** ADR-SEED-014
**Date proposed:** 2026-06-14
**Date reviewed:** 2026-06-15
**Reviewed by:** V4 Reviewer (r1, port 8643) — 5 objections raised, all resolved
**Proposed by:** V4 Reviewer (r1, port 8643) — see Provenance Note below
**Supersedes:** None
**Superseded by:** None (temporary bridge, superseded by Tier 7R Router when built)

---

## Provenance Note

This ADR was initially drafted during a Reviewer-profile session (r1, port 8643)
while the operator was diagnosing a role-boundary failure (BLK-SEED-005: gateway
service auto-overwrite causing profile misbinding). The ADR's architecture emerged
through iterative discovery against live schema evidence, with external advisor
audit (ChatGPT, Claude) across multiple rounds.

Eric explicitly waives the Drafter/Reviewer provenance defect for ADR-SEED-014 only.
Reason: the ADR was challenged by the same r1 instance after role identity was
confirmed, material defects were caught (false "transition demonstrated" claim,
incorrect FK direction, missing idempotency, missing git-state policy), and all
objections were resolved. Restarting from scratch on port 8645 would add friction
without improving the underlying decision.

This waiver does not create precedent. Future ADR/spec drafting must originate from
V4 Drafter (port 8645) and be independently challenged by r1 (port 8643) before
Eric Gate approval, per the established Drafter→Reviewer→Eric Gate pipeline.

---

## Decision

Until the Router / Tier 7R initiation path is fully built, CIS will use a temporary
manual TRIAGE contract for how a Drafter session begins:

1. **Eric states the initiating intent** in plain language. Eric's stated intent is
   sufficient authorization to open the temporary manual TRIAGE workflow_run. No
   separate pre-draft approval step is required. The recorded intent text is
   authoritative and must be preserved for Reviewer comparison against the Drafter
   proposal. Eric Gate remains later in the pipeline for implementation approval.

2. **A minimal initiation shim creates both identities.** A script
   (`tools/pipeline/drafter_start.py`) accepts Eric's intent as input and creates:
   - A `workflow_run_id` following the existing `run-<hex>` convention
   - A `proposal_id` following the existing UUID convention
   - The link between them (via `workflow_run_id` columns on `lifecycle_events`
     and `dispatch_log` — see Design Choice 1 below)
   - Idempotency: if Eric's intent text hashes to an already-active workflow_run,
     returns the existing IDs instead of creating duplicates

   This is the only path for creating a Drafter workflow run until Tier 7R Router exists.
   `drafter_start.py` does not classify, route, or interpret the intent.

3. **The Drafter receives both IDs plus a spine-derived session briefing** (via
   `drafter_session_init.py`, defined in the Tier 11C specification). The Drafter
   may draft the proposal from Eric's intent, current spine state, active decisions,
   active blockers, and the approved build order.

4. **The Drafter may not invent or materially alter the initiating goal.** If the
   Drafter identifies a gap in the intent, it may flag it for Eric but must not
   rewrite the goal to fill the gap.

5. **External advisors may frame options, critique, or analyze**, but they may not:
   - Author the authoritative proposal content
   - Create the initiating intent
   - Create the workflow_run or proposal
   - Write FINAL_JSON blocks
   - Insert lifecycle_events or dispatch records

   The advisor-framing-not-authoring boundary is primarily a governance convention.
   It is not fully technically enforceable — a motivated Drafter could paste
   advisor-authored text verbatim and no automated gate would catch it. The
   following minimum mechanisms provide partial enforcement:

   - `drafter_start.py` records Eric's exact intent text in `workflow_runs.topic`
     as the authoritative initiating source.
   - `drafter_closeout.py` logs a hash of the Drafter output.
   - The Reviewer is instructed to compare the Drafter proposal against Eric's
     recorded intent and challenge material drift.
   - Eric Gate remains as the final human reconciliation point.

   Full automated "advisor similarity detection" is not required for Tier 11C.
   Clause 5's primary enforcement is the existing triangulated review model:
   Drafter authors, Reviewer challenges, Eric reconciles.

6. **Reviewer challenge begins only after Drafter emits a valid FINAL_JSON** with
   `role: "drafter"` and `status: "PROPOSAL_READY"`.

---

## Deliberated Design Choices

### Choice 1: Proposal identity vs. workflow identity

**Fact:** The existing code (`runtime/api/orchestration.py:119`, `runtime/api/advisor.py:1250`)
already uses separate namespaces:
- `proposal_id` = UUID, used in `lifecycle_events`, `dispatch_log`, `dispatch_events`
- `workflow_run_id` = `run-<hex>`, used in `workflow_runs`

There is currently no column joining them. The Flask API creates both in the same
call but the link exists only in the HTTP response, not in the database.

**Options considered:**

- Option A: Collapse them (`proposal_id = workflow_run_id`).
  Rejected. Would create semantic collision — `run-<hex>` values in columns designed
  for UUIDs. Creates future migration cleanup when the Flask API resumes writing UUIDs.

- Option B: Separate identities with no recorded link.
  Rejected. Session-coincidence is not a link — `drafter_session_init.py` and
  `drafter_closeout.py` cannot answer "what workflow_run does this lifecycle belong to?"

- **Option C (chosen): Separate identities with explicit recorded links on the many side.**
  One workflow run produces many lifecycle events and many dispatches. The link
  belongs on the many side: `workflow_run_id` on `lifecycle_events` and `dispatch_log`.
  Two nullable TEXT columns. No FK required (proposals table doesn't exist yet per
  migration 0011 comment, and `proposal_id` remains the lifecycle primary key).

**Decision:** Honor the existing separate-identity architecture. Add nullable
`workflow_run_id` columns to the two many-side tables. The migration is:
```sql
ALTER TABLE lifecycle_events ADD COLUMN workflow_run_id TEXT;
ALTER TABLE dispatch_log ADD COLUMN workflow_run_id TEXT;
```

`drafter_start.py` creates the workflow_run_id and proposal_id, then writes
`workflow_run_id` into each lifecycle event and dispatch row it creates.
Downstream scripts query lifecycle directly by workflow_run_id, or join:
`SELECT * FROM lifecycle_events WHERE workflow_run_id = ?`.
`proposal_id` remains the lifecycle primary identifier — `workflow_run_id`
is a denormalized join key for convenience.

### Choice 2: Lifecycle events as canonical state machine (no new column on workflow_runs)

**Fact:** `lifecycle_events` exists (migration 0011) but contains zero rows. The state
machine is enforced in code by `transition_state()` which validates against
`ALLOWED_TRANSITIONS` before writing. The table has never been operationally exercised.

**Decision:** `lifecycle_events` is the canonical draft/review state machine.
`workflow_runs.status` remains coarse-grained (COMPLETE/PENDING/ERROR) and is not
used for intermediate draft/review transitions. No `draft_status` column is added.

**Required states (from the existing ALLOWED_TRANSITIONS in orchestration.py):**

| Transition | Meaning |
|---|---|
| IDLE → ROUTING | Intent received, routing begins |
| ROUTING → DRAFTING | Drafter session active |
| DRAFTING → DRAFT_READY | Proposal complete, FINAL_JSON validated |
| DRAFT_READY → REVIEW_PENDING | Dispatch created, awaiting Reviewer |

These state names are not invented — they are the existing constants from
`runtime/api/orchestration.py` lines 21-71.

### Choice 3: Write through the existing state machine, not raw SQL

**Decision:** `drafter_start.py` and `drafter_closeout.py` must write lifecycle
events through `transition_state()` (or a validated CLI-safe wrapper) rather than
inserting rows directly. This ensures the ALLOWED_TRANSITIONS validator is the
single enforcement point, preventing the state machine from forking into two writers
with different rules.

**Verification required before Tier 11C implementation:** Tier 11C must verify
whether `transition_state()` (`runtime/api/orchestration.py:138`) is safely
callable from a terminal script without importing the full Flask application
context. If it requires Flask context, Tier 11C must provide one of:
- A small CLI-safe wrapper that exposes the same validation
- A shared validation helper extracted from `orchestration.py` into a standalone module
- Explicit replication of the validation logic (least preferred)

State-transition rules must not be duplicated in two places. One validator, one
source of truth, callable from both Flask and terminal contexts.

The existing `transition_state()` function (`orchestration.py:138`) accepts:
```python
transition_state(proposal_id, session_id, from_state, to_state,
                 initiated_by, gate_type=None, dispatch_ref=None,
                 evidence_ref=None, reviewer_message_id=None,
                 directive_hash=None, eric_approved=0,
                 eric_bypass=0, revision_count=0, notes=None, db=None)
```

### Choice 4: Eric's stated intent as sufficient authorization

**Decision:** Eric stating the intent is sufficient to open the temporary manual
TRIAGE workflow_run. No separate pre-draft approval step is required. Adding one
would recreate the friction Tier 11C is designed to remove.

The authority boundary is preserved by:
- `drafter_start.py` recording Eric's exact intent text as the authoritative source
- The Drafter being prohibited from materially altering it (clause 4)
- The Reviewer challenging any drift between intent and proposal (clause 6)
- Eric Gate remaining as the later implementation approval gate (not collapsed into initiation)

### Choice 5: Git-state policy for session init and closeout

**Decision:** Three-phase git-state handling:

| Phase | Script | Policy |
|---|---|---|
| Initiation | `drafter_start.py` | Warns on dirty tracked files and untracked files. Does not refuse. Records git HEAD for provenance. |
| Session start | `drafter_session_init.py` | Warns on dirty/untracked state. Does not refuse. Reports git HEAD and dirty file list in briefing. |
| Closeout | `drafter_closeout.py` | **Refuses** closeout if untracked files exist. Warns on dirty tracked files. Closeout is the enforcement point. |

This keeps initiation permissive (the operator may have intentionally open work)
while making closeout strict (no uncommitted artifacts escape the session).
Human cleanup of untracked files is required before closeout can proceed.

---

## Rationale

### Why this is needed now

The designed CIS pipeline (TRIAGE → Router → Orchestrator → Drafter) assumes Router
creates workflow_runs. But Tier 7 (Router) is deferred. The current operational path
is Eric opening terminal sessions manually. Without this contract:

- Drafter sessions begin through implicit context and manual paste.
- No authoritative record exists for how a draft began.
- The `lifecycle_events` table exists but has never been exercised — the state machine
  is structural, not operational.
- External advisors have no explicit boundary.
- `proposal_id` and `workflow_run_id` are created in the Flask API but not joinable
  in the database.

### Why the boundary clause matters

Evidence from this session: External advisors (ChatGPT, Claude) provided substantive
framing before the Drafter began drafting this ADR. Clause 5 codifies: advisors
critique and frame, but the Drafter authors. Without this clause, the line between
"advisor framed options" and "advisor authored the proposal skeleton" is invisible.

### Why separate identities with a recorded link

The existing code already chose separate namespaces. Collapsing them for the
temporary bridge would create semantic collision (mixed ID formats in lifecycle_events)
that becomes cleanup debt when the Flask API resumes. Adding nullable
`workflow_run_id` columns to the two many-side tables is the least invasive way to
make the link queryable without forking from the intended architecture.

### Why temporary

This contract is a bridge to Tier 7R Router. When the Router is built, it replaces
`drafter_start.py`. This ADR will be superseded. It must not expand into full router
implementation, intent classification, project promotion, or generalized workflow
automation.

---

## Schema Change Required

Migration for Tier 11C prerequisite (new file: `runtime/schema/migrations/0012_workflow_run_link.sql`):

```sql
-- Migration 0012: Add workflow_run_id to lifecycle and dispatch tables
-- Prerequisite for ADR-SEED-014 (Temporary Draft Initiation Contract)
-- Links the lifecycle state machine back to the durable workflow run.
-- One workflow_run → many lifecycle_events, many dispatch_log rows.
-- FK deferred — proposals and dispatches are independent namespaces per
-- migration 0011 comment ("no proposals table exists yet").

ALTER TABLE lifecycle_events ADD COLUMN workflow_run_id TEXT;
ALTER TABLE dispatch_log ADD COLUMN workflow_run_id TEXT;
```

This is additive only. No existing rows modified. No existing queries break.
`proposal_id` remains the primary lifecycle identifier. `workflow_run_id` is
a denormalized join key for query convenience.

---

## Implementation Consequence for Tier 11C

1. Tier 11C must include migration 0012 as a prerequisite (add `workflow_run_id`
   to `lifecycle_events` and `dispatch_log`).

2. Tier 11C must verify `transition_state()` terminal callability and provide a
   CLI-safe wrapper if needed (see Choice 3).

3. The Tier 11C state sequence becomes:

   ```
   Eric states intent
        ↓
   drafter_start.py:
     - Hashes Eric's intent text for idempotency check
     - If existing active run found, returns existing IDs (no duplicate)
     - Creates workflow_run_id (run-<hex>)
     - Creates proposal_id (UUID)
     - Writes lifecycle events via transition_state(): IDLE → ROUTING → DRAFTING
       (each with workflow_run_id set)
     - Records Eric's exact intent in workflow_runs.topic
     - Records git HEAD
     - Warns on dirty/untracked git state
        ↓
   drafter_session_init.py briefs from workflow_run (spine + git state)
   Warns on dirty/untracked state
        ↓
   Drafter produces proposal + FINAL_JSON
        ↓
   drafter_closeout.py:
     - Refuses if untracked files exist
     - Validates FINAL_JSON (role=drafter, status=PROPOSAL_READY)
     - Logs hash of Drafter output
     - Writes lifecycle event: DRAFTING → DRAFT_READY
     - Creates dispatch_log row (REVIEW_PENDING → r1, port 8643)
     - Writes lifecycle event: DRAFT_READY → REVIEW_PENDING
        ↓
   Reviewer receives dispatch (r1, port 8643)
   Reviewer compares proposal against Eric's recorded intent
   ```

4. Idempotency: `drafter_start.py` hashes Eric's intent text and checks for an
   existing workflow_run with the same topic. If found and still active (not
   COMPLETE/ERROR/ESCALATE), returns the existing `workflow_run_id` and
   `proposal_id` instead of creating duplicates.

5. All lifecycle writes go through `transition_state()` (or its CLI-safe wrapper)
   using existing ALLOWED_TRANSITIONS state names.

6. The phrase "workflow run is in a Drafter-closeable state" is redefined as:
   the most recent `lifecycle_events.to_state` for this `workflow_run_id` is
   `DRAFTING`, and no `DRAFT_READY` event already exists (idempotency protection).

7. Git-state enforcement: `drafter_start.py` warns, `drafter_session_init.py`
   warns, `drafter_closeout.py` refuses if untracked files exist.

---

## Evidence

### Fact 1: No ADR covers draft initiation
13 ADRs exist (SEED-001 through SEED-013, plus T44-001). None define how a Drafter
workflow_run is created.

### Fact 2: Workflow_run creation exists only in Flask API layer
`runtime/api/advisor.py:1250` — `_create_workflow_run()` is API-bound. Terminal
Drafter sessions have no equivalent path.

### Fact 3: proposal_id and workflow_run_id are separate identities in existing code
`orchestration.py:119`: `generate_proposal_id()` returns `str(uuid.uuid4())`
`advisor.py:1250`: `_create_workflow_run()` returns `f"run-{uuid.uuid4().hex[:13]}"`
No column in any Tier 11B table stores the link between them.

### Fact 4: Lifecycle events table exists but is empty (0 rows)
`migration 0011_lifecycle_dispatch.sql` created the schema. The state machine
(`ALLOWED_TRANSITIONS` in `orchestration.py:21-71`) is enforced in code but has
never been exercised with real data. No demonstration of DRAFT_READY → REVIEW_PENDING
has occurred.

### Fact 5: ALLOWED_TRANSITIONS already defines the needed states
All required states exist in the code: ROUTING, DRAFTING, DRAFT_READY, REVIEW_PENDING.
No new state names need to be invented.

### Fact 6: No column exists to join proposal_id to workflow_run_id (on either side)
Full schema audit of lifecycle_events, dispatch_log, dispatch_events, workflow_runs,
workflow_run_artifacts, and workflow_run_legacy_links confirmed zero columns
bridging the two identities. The Flask API creates both IDs in the same call but
the link exists only in the HTTP response, not in the database.

Migration 0012 adds `workflow_run_id` to the many-side tables (`lifecycle_events`,
`dispatch_log`) so downstream queries can filter lifecycle and dispatch state by
workflow run without a join through proposal_id.

---

## Boundary

This is a temporary bridge, not the final Router/Tier 7R design. It must not expand into:
- Full router implementation
- Intent classification or topic routing
- Project promotion (Pass 5)
- Generalized workflow automation
- Multi-project initiation
- Schedule/field-use work (SWA)

When Tier 7R Router is built, `drafter_start.py` is retired, the `workflow_run_id`
link columns become the standard join path, and this ADR is marked SUPERSEDED.

---

## Resolved Reviewer Objections

The following objections were raised by V4 Reviewer (r1, port 8643) on 2026-06-15
and resolved in this revision:

| # | Objection | Resolution |
|---|---|---|
| 1 | ADR authored by Reviewer profile, not Drafter | Eric waived for ADR-SEED-014 only (see Provenance Note). Future ADRs: Drafter authors first. |
| 2 | Advisor boundary clause has no enforcement mechanism | Stated as governance convention with minimum mechanisms: intent recording, output hashing, Reviewer comparison. No overbuilt similarity detection. |
| 3 | `transition_state()` import chain unspecified for terminal scripts | Tier 11C must verify terminal callability. Provide CLI-safe wrapper if Flask context required. One validator, callable from both contexts. |
| 4 | No idempotency protection for `drafter_start.py` | Added topic-hash dedup. Duplicate intents return existing IDs instead of creating duplicates. |
| 5 | Missing git-state policy for session init vs closeout | Three-phase policy added (Choice 5): start warns, session init warns, closeout refuses untracked files. |

Risk assessment: **LOW** after revisions. Architecture is sound. All structural
decisions are resolved. Implementation risks are limited to `transition_state()`
terminal callability (verification gated before Tier 11C build) and the advisor
boundary (governance convention, not technical enforcement).

---

## Session Update — 2026-06-27

This document's topic (ADR-SEED-014 contract) was not directly advanced this session.
The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
abstraction layer (5 endpoints including human-readable status), intent alignment
pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
Commit: 70e73bd.
