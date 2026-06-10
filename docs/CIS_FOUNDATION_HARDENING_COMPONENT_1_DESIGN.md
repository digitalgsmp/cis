# Foundation Hardening — Component 1 Design
## Provenance and Lifecycle Base Schema
**Status: IMPLEMENTED — migration 0008 applied to cis_memory.db**
**Author: Claude (external advisor)**
**Implementer: v4impl (Hermes Agent)**
**Date: 2026-06-10**
**Revision: v4 — implemented with FK type corrections, commit f296a76+**
**Migration path: runtime/schema/migrations/0008_provenance_lifecycle_base.sql**
**Depends on: nothing (foundation layer)**
**Blocks: Components 2, 3, 4, 5**
**Spine: 4 new tables, 8 indexes, 2 triggers created. Zero existing data modified.**

---

## Purpose

This schema extension gives every pipeline action a provenance trail. It is the
foundation that Components 2 through 5 build on. Without it:

- Eric Gate has no structured briefing to surface — it can only record a timestamp
- The Router has no basis for drift detection — it cannot ask "does this action have a goal reference?"
- Dismissed objections leave no trace — the Kanban situation cannot be detected by the system

The four tables defined here are the minimum required to support all five Foundation
Hardening components. They do not replace any existing spine tables. They extend the
spine with governance infrastructure.

---

## Existing Spine (reference — do not modify)

| Table | Rows (current) | Purpose |
|-------|---------------|---------|
| workflow_runs | 5 | Authoritative in-flight work object |
| deliberation_rounds | 4 | Per-round Drafter/Reviewer history |
| project_decisions | 13 | ADR records |
| open_questions | 6 | Tracked questions with status |
| next_actions | 12 | Approved build-order actions |
| active_blockers | 6 | Current blockers with status |
| session_closeouts | (migration 0007) | Session close records with push status |

New tables in this migration do not alter any existing table. Foreign keys reference
`workflow_runs(id)` as the primary linkage point. Secondary foreign keys reference
`decision_trails(id)` and `active_blockers(id)` where noted per table.

---

## Four New Tables

---

### Table 1: `goal_references`

**Purpose:** Every pipeline action must connect to a defined project goal and a
dependency graph node. This table records that connection explicitly, making it
queryable. The Router (Component 4) and Eric Gate (Component 3) both query this
table to surface actions with missing or weak goal traces.

**The Kanban problem in this context:** Kanban became load-bearing because no
record existed of why it was introduced, what goal it served, or when the goal
would be met. Had `goal_references` existed, the Router could have flagged
"this workflow_run has no goal reference" before it reached Eric Gate.

```sql
CREATE TABLE IF NOT EXISTS goal_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id     INTEGER NOT NULL REFERENCES workflow_runs(id),

    goal_label          TEXT NOT NULL,
    -- Plain-language label for the goal this action serves.
    -- Example: "Pipeline stability before Tier 8"
    -- Example: "Eliminate manual scaffolding from execution path"

    dependency_node     TEXT NOT NULL,
    -- The exact node label from CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md that this
    -- action closes or advances. Must be a named node, not a tier label alone.
    -- Convention: values must match node labels exactly as they appear in the
    -- build plan. Free text for now; CHECK constraint deferred until node
    -- vocabulary stabilizes (see OQ-C1-002).
    -- Example: "Tier 6 — Closeout trigger design"
    -- Example: "Foundation Hardening — Component 1"

    tier_advanced       TEXT,
    -- Which tier is advanced by completing this action. Optional but recommended.
    -- Example: "Foundation Hardening"

    advancement_type    TEXT NOT NULL CHECK (advancement_type IN (
                            'CLOSES_NODE',
                            'ADVANCES_TIER',
                            'RESOLVES_BLOCKER',
                            'RESOLVES_OPEN_QUESTION',
                            'ESTABLISHES_PREREQUISITE'
                        )),
    -- CLOSES_NODE: this action directly closes the named dependency_node
    -- ADVANCES_TIER: this action advances but does not close the tier
    -- RESOLVES_BLOCKER: this action resolves an active_blocker record
    -- RESOLVES_OPEN_QUESTION: this action resolves an open_questions record
    -- ESTABLISHES_PREREQUISITE: this action creates a required foundation for a future node

    linked_record_table TEXT CHECK (
                            linked_record_table IS NULL OR linked_record_table IN (
                                'active_blockers',
                                'open_questions',
                                'project_decisions',
                                'next_actions'
                            )
                        ),
    linked_record_id    INTEGER,
    -- Optional. If advancement_type is RESOLVES_BLOCKER or RESOLVES_OPEN_QUESTION,
    -- record which row in active_blockers or open_questions is resolved.
    -- linked_record_table must be one of the four known spine tables above, or NULL.

    authored_by         TEXT NOT NULL CHECK (authored_by IN (
                            'DRAFTER',
                            'REVIEWER',
                            'ERIC_GATE',
                            'ROUTER',
                            'CLOSEOUT'
                        )),

    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_goal_references_run
    ON goal_references(workflow_run_id);

CREATE INDEX IF NOT EXISTS idx_goal_references_node
    ON goal_references(dependency_node);
```

**Gate requirement:** Before Eric Gate approval, a `goal_references` row must exist
for the active `workflow_run_id`. Gate exits non-zero (FAIL) if no row found.
This is the deterministic check that prevents goal-orphaned actions from reaching
Eric.

---

### Table 2: `decision_trails`

**Purpose:** Records the condensed path from problem identification through
deliberation to a proposed action. One `workflow_run` can produce multiple
decision points (e.g., the Drafter proposes three approaches; the Reviewer
objects to two; Eric redirects; a revised proposal emerges). Each is a row.

This table is what surfaces to Eric in plain language at the Gate. It is also
the record that Component 5 (Tier Retrofit Assessment) queries to find gaps
in prior tier completions.

**Authorship rule (resolved — ChatGPT audit, OQ-C1-001):**
The Drafter or Reviewer creates a draft `decision_trails` row when
`CONSENSUS_REACHED` is emitted or when the run is escalated to Eric. This row
must exist before Eric Gate runs — the Gate reads it as the primary briefing.
The Closeout script then finalizes the row: it sets `eric_decision`,
`eric_decision_note`, `eric_decided_at`, and `updated_at` after the session
closes. Closeout-only authorship is not acceptable because Eric Gate requires
the trail to exist before approval.

```sql
CREATE TABLE IF NOT EXISTS decision_trails (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id         INTEGER NOT NULL REFERENCES workflow_runs(id),

    trail_sequence          INTEGER NOT NULL,
    -- 1-indexed sequence within this workflow_run. Multiple decision points
    -- in a single run are numbered in order of occurrence.

    UNIQUE (workflow_run_id, trail_sequence),
    -- Enforces sequence integrity. Without this, sequence numbers are advisory only.

    problem_statement       TEXT NOT NULL,
    -- One to three sentences. What problem or gap triggered this decision point.
    -- Must be plain language. No model jargon.

    research_summary        TEXT,
    -- What the Research profile surfaced, if a research round was run.
    -- Null if no research was performed (e.g., operator command path).

    draft_summary           TEXT,
    -- What the Drafter proposed. Condensed, not the full artifact.

    review_summary          TEXT,
    -- What the Reviewer raised. Objections, consensus signal, and round count.

    external_audit_summary  TEXT,
    -- What Claude and/or ChatGPT returned, if an escalation was performed.
    -- Null if no external audit occurred.

    proposed_action         TEXT NOT NULL,
    -- The action that emerged from deliberation. One paragraph, plain language.
    -- This is what Eric reads at the Gate.

    round_count             INTEGER NOT NULL DEFAULT 1,
    -- Number of Drafter→Reviewer rounds before CONSENSUS_REACHED or ERIC_GATE.

    consensus_signal        TEXT NOT NULL CHECK (consensus_signal IN (
                                'CONSENSUS_REACHED',
                                'ESCALATED_TO_ERIC',
                                'ESCALATED_EXTERNAL',
                                'OPERATOR_COMMAND'
                            )),
    -- CONSENSUS_REACHED: Reviewer issued no material objections
    -- ESCALATED_TO_ERIC: Deliberation did not reach consensus; Eric intervened
    -- ESCALATED_EXTERNAL: Claude or ChatGPT audit was required
    -- OPERATOR_COMMAND: Bypassed deliberation (deterministic path)

    eric_decision           TEXT CHECK (eric_decision IN (
                                'APPROVED',
                                'VETOED',
                                'REDIRECTED',
                                'DEFERRED',
                                NULL
                            )),
    -- Null when the row is first created (pre-Gate). Set by Closeout after Eric decides.

    eric_decision_note      TEXT,
    -- Plain-language note Eric provides at approval or veto.
    -- Required if eric_decision is VETOED or REDIRECTED.

    eric_decided_at         TEXT,
    -- Null until Closeout finalizes. Timestamp of Eric's decision.

    authored_by             TEXT NOT NULL CHECK (authored_by IN (
                                'DRAFTER',
                                'REVIEWER',
                                'CLOSEOUT',
                                'ROUTER'
                            )),
    -- Who created the initial draft row. Closeout updates but does not re-set this.

    created_at              TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_decision_trails_run_seq
    ON decision_trails(workflow_run_id, trail_sequence);

CREATE INDEX IF NOT EXISTS idx_decision_trails_run
    ON decision_trails(workflow_run_id);

CREATE TRIGGER IF NOT EXISTS trg_decision_trails_updated_at
    AFTER UPDATE ON decision_trails
    FOR EACH ROW
    BEGIN
        UPDATE decision_trails SET updated_at = datetime('now') WHERE id = OLD.id;
    END;
```

**Gate requirement:** Eric Gate reads the most recent `decision_trails` row for
the active `workflow_run_id` and surfaces `proposed_action` + `problem_statement`
in plain language. Gate exits non-zero (FAIL) if no trail row exists.

---

### Table 3: `drift_indicators`

**Purpose:** Tracks conditions that indicate the project is drifting from its
dependency graph, accruing ungoverned technical debt, or producing incomplete
governance records. Each indicator has a lifecycle: RAISED → ACKNOWLEDGED →
RESOLVED or ESCALATED.

This is the table that would have surfaced the Kanban situation. A temporary
dependency introduced without a retirement trigger would have generated a
`drift_indicators` row of type `TEMPORARY_DEPENDENCY_NO_RETIREMENT`. That row
would have remained RAISED until a retirement plan was defined — making the
gap visible.

**Promotion to `active_blockers`:** The schema supports automatic promotion of
long-standing RAISED indicators to `active_blockers`. The logic and trigger
conditions for this promotion belong to Component 4 (Router) or a future
closeout hardening pass — not Component 1. This schema provides the fields
necessary to support that behavior when it is built.

```sql
CREATE TABLE IF NOT EXISTS drift_indicators (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    workflow_run_id     INTEGER REFERENCES workflow_runs(id),
    -- Nullable. Some drift indicators are not associated with a specific run
    -- (e.g., a stale tier detected at session start by the Router).

    indicator_type      TEXT NOT NULL CHECK (indicator_type IN (
                            'TEMPORARY_DEPENDENCY_NO_RETIREMENT',
                            -- A component or mechanism was introduced as temporary
                            -- but has no defined retirement trigger.
                            -- Example: Kanban as pipeline transport before ADR-013.

                            'ACTION_DIVERGES_FROM_DEPENDENCY_GRAPH',
                            -- The proposed or executed action does not correspond
                            -- to any node in the approved build order.

                            'OBJECTION_DISMISSED_WITHOUT_RESOLUTION',
                            -- A Reviewer objection was recorded in deliberation_rounds
                            -- but no resolution was documented before CONSENSUS_REACHED.

                            'COMPONENT_PATCHED_WITHOUT_ROOT_CAUSE',
                            -- A component has been patched more than once without a
                            -- root cause diagnosis committed to the spine.

                            'GATE_BYPASSED',
                            -- A pipeline gate was explicitly bypassed or overridden
                            -- without Eric approval recorded in decision_trails.

                            'ERIC_GATE_NO_PROVENANCE'
                            -- An Eric Gate approval was recorded (eric_approved_at)
                            -- without a corresponding decision_trails row.
                        )),

    description         TEXT NOT NULL,
    -- Plain-language description of the specific drift condition detected.
    -- Must be concrete: what component, what session, what gap.

    detected_by         TEXT NOT NULL CHECK (detected_by IN (
                            'ROUTER',
                            'GATE_SCRIPT',
                            'CLOSEOUT',
                            'EXTERNAL_ADVISOR',
                            'ERIC',
                            'MANUAL'
                        )),

    status              TEXT NOT NULL DEFAULT 'RAISED' CHECK (status IN (
                            'RAISED',
                            -- Detected, not yet acknowledged.

                            'ACKNOWLEDGED',
                            -- Eric has seen it. No resolution yet.

                            'RESOLVED',
                            -- Root cause addressed. Resolution documented in
                            -- resolution_note. Linked decision_trails row required.

                            'ESCALATED',
                            -- Routed to external advisor (Claude/ChatGPT) for audit.

                            'ACCEPTED_DEBT',
                            -- Eric explicitly accepted this as known architectural debt.
                            -- Must have resolution_note.

                            'WONT_FIX'
                            -- Explicitly decided not to address. Requires Eric approval
                            -- and resolution_note.
                        )),

    resolution_note     TEXT,
    -- Required when status transitions to RESOLVED, ACCEPTED_DEBT, or WONT_FIX.

    linked_decision_trail_id    INTEGER REFERENCES decision_trails(id),
    -- When RESOLVED: the decision_trails row that documents the fix.

    linked_blocker_id           INTEGER REFERENCES active_blockers(id),
    -- If this indicator was promoted to an active_blocker, record the link.

    raised_at               TEXT NOT NULL DEFAULT (datetime('now')),

    acknowledged_at         TEXT,
    acknowledged_by         TEXT CHECK (acknowledged_by IN (
                                'ERIC',
                                'ROUTER',
                                'CLOSEOUT',
                                'EXTERNAL_ADVISOR',
                                NULL
                            )),
    -- Null until status transitions to ACKNOWLEDGED or beyond.

    resolved_at             TEXT,
    resolved_by             TEXT CHECK (resolved_by IN (
                                'ERIC',
                                'ROUTER',
                                'CLOSEOUT',
                                'EXTERNAL_ADVISOR',
                                'V4_IMPLEMENTER',
                                NULL
                            )),
    -- Null until status transitions to RESOLVED, ACCEPTED_DEBT, or WONT_FIX.

    status_updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    -- Updated on every status transition. Provides an auditable record of
    -- when the indicator last changed state, independent of resolved_at.

    raised_by_run_id        INTEGER REFERENCES workflow_runs(id)
    -- May differ from workflow_run_id if the indicator was raised by the
    -- Router at session start rather than during a specific run.
);

CREATE INDEX IF NOT EXISTS idx_drift_indicators_status
    ON drift_indicators(status);

CREATE INDEX IF NOT EXISTS idx_drift_indicators_run
    ON drift_indicators(workflow_run_id);

CREATE INDEX IF NOT EXISTS idx_drift_indicators_type
    ON drift_indicators(indicator_type);

CREATE TRIGGER IF NOT EXISTS trg_drift_indicators_status_updated_at
    AFTER UPDATE OF status ON drift_indicators
    FOR EACH ROW
    BEGIN
        UPDATE drift_indicators SET status_updated_at = datetime('now') WHERE id = OLD.id;
    END;
```

**Gate requirement:** Eric Gate queries `drift_indicators WHERE status IN ('RAISED',
'ACKNOWLEDGED')` before presenting the approval briefing. Any open indicators for
the active `workflow_run_id` are surfaced in the briefing. Eric must explicitly
acknowledge or resolve each before approving, or veto the action.

---

### Table 4: `rejection_rationale`

**Purpose:** Records what was considered and why it was not chosen. This is
distinct from `decision_trails` (which records what happened) — this table
records what was rejected before the final path was selected.

One `decision_trails` row can have zero or many `rejection_rationale` rows.
The table ensures that future sessions can understand why a path was not taken,
preventing the system from re-evaluating already-rejected approaches without
full context.

```sql
CREATE TABLE IF NOT EXISTS rejection_rationale (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    decision_trail_id       INTEGER NOT NULL REFERENCES decision_trails(id),
    workflow_run_id         INTEGER NOT NULL REFERENCES workflow_runs(id),
    -- Denormalized for query convenience. Must match decision_trail.workflow_run_id.

    rejected_option_label   TEXT NOT NULL,
    -- Short label for the rejected approach.
    -- Example: "Extend workflow_runs with provenance columns"
    -- Example: "Use Kanban as primary pipeline transport indefinitely"

    rejected_option_summary TEXT NOT NULL,
    -- One to three sentences describing the rejected option.

    rejection_reason        TEXT NOT NULL CHECK (rejection_reason IN (
                                'ARCHITECTURAL_MISMATCH',
                                -- Option violates an existing ADR or CIS build principle.

                                'ONE_TO_MANY_VIOLATION',
                                -- Option cannot model the required relationship.

                                'QUERYABILITY_GAP',
                                -- Option makes required queries impractical or impossible.

                                'LIFECYCLE_UNSUPPORTED',
                                -- Option cannot represent the required state machine.

                                'GOVERNANCE_GAP',
                                -- Option would leave a governance requirement unmet.

                                'SCOPE_VIOLATION',
                                -- Option exceeds the defined scope of this component.

                                'DEPENDENCY_ORDER_VIOLATION',
                                -- Option requires a component not yet built.

                                'ERIC_REJECTED',
                                -- Eric explicitly rejected this option at the Gate.

                                'EXTERNAL_ADVISOR_REJECTED'
                                -- Claude or ChatGPT audit rejected this option.
                            )),

    rejection_detail        TEXT NOT NULL,
    -- Plain language. Concrete explanation of why this option was rejected.
    -- Must be specific enough that a future session understands without
    -- re-reading the full deliberation transcript.

    rejected_by             TEXT NOT NULL CHECK (rejected_by IN (
                                'DRAFTER',
                                'REVIEWER',
                                'ERIC',
                                'CLAUDE',
                                'CHATGPT',
                                'ARCHITECTURAL_RULE'
                            )),

    created_at              TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_rejection_rationale_trail
    ON rejection_rationale(decision_trail_id);

CREATE INDEX IF NOT EXISTS idx_rejection_rationale_run
    ON rejection_rationale(workflow_run_id);
```

**Gate requirement:** No gate blocks on `rejection_rationale`. It is populated
as part of normal deliberation. The Eric Gate briefing surfaces any
`rejection_rationale` rows for the active trail — Eric sees what was considered
and rejected before approving the chosen path. An empty table is visible to Eric
as a gap; this creates enforcement through visibility before any technical check.

---

## Relationships to Existing Spine

```
workflow_runs (existing)
    │
    ├── goal_references          (1:many — one run, multiple goal connections)
    │
    ├── decision_trails          (1:many — one run, multiple decision points)
    │       │
    │       └── rejection_rationale  (1:many — one trail, multiple rejected options)
    │
    └── drift_indicators         (1:many — one run, multiple drift conditions)
            │
            ├── → decision_trails(id)    (linked_decision_trail_id — when resolved)
            └── → active_blockers(id)    (linked_blocker_id — when promoted)
```

`drift_indicators.workflow_run_id` is nullable to support Router-detected indicators
that are not tied to a specific run (e.g., detected at session start).

`rejection_rationale` carries a denormalized `workflow_run_id` for query convenience;
it also references `decision_trails(id)` as its primary parent.

---

## Migration File

**Path:** `runtime/schema/migrations/0008_provenance_lifecycle_base.sql`

The migration file contains only `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF
NOT EXISTS`, and `CREATE TRIGGER IF NOT EXISTS` statements. No `ALTER TABLE`,
no data backfill, no destructive operations. Safe to apply to an existing spine
with zero downtime.

Two triggers are defined:
- `trg_decision_trails_updated_at` — fires on any UPDATE to `decision_trails`,
  sets `updated_at` to current timestamp.
- `trg_drift_indicators_status_updated_at` — fires on UPDATE of `status` column
  on `drift_indicators`, sets `status_updated_at` to current timestamp.

`gate_db_state.py` must be extended after implementation to verify:
- All four tables exist
- All required columns are present with correct types
- All indexes exist
- All CHECK constraints are present (verified via `sqlite_master` schema inspection)
- Both triggers exist

This extension is scoped to the implementation phase, not this design document.

---

## Gate Requirements Summary

| Gate | Check | Fail Condition |
|------|-------|----------------|
| Eric Gate (pre-approval) | `goal_references` row exists for active run | No goal reference → FAIL |
| Eric Gate (pre-approval) | `decision_trails` row exists for active run | No trail → FAIL |
| Eric Gate (pre-approval) | Open `drift_indicators` surfaced in briefing | Indicators exist → surface for acknowledgment |
| gate_db_state.py (post-implementation) | All 4 tables, indexes, triggers, CHECK constraints present | Missing any → FAIL |

The drift indicator auto-promotion behavior (RAISED indicators of sufficient age
promoted to `active_blockers`) is **supported by this schema** but is not
implemented in Component 1. That logic belongs to Component 4 (Router) or a
future closeout hardening pass and will be defined there.

---

## Risks

**R1 — Backfill gap.** The four new tables are populated going forward only.
Existing `workflow_runs` records have no corresponding provenance rows. Mitigation:
Eric Gate enforcement applies only to new runs created after migration 0008 is applied.
Component 5 (Tier Retrofit Assessment) handles historical reconstruction.

**R2 — `decision_trails` authoring burden.** Trail records require structured
summaries. Authorship rule is now explicit: Drafter/Reviewer creates the row at
CONSENSUS_REACHED; Closeout finalizes it. This splits the burden and avoids
Closeout-only authorship, which would have made the trail unavailable at Gate time.

**R3 — `drift_indicators` noise at first deployment.** After migration, a one-time
triage pass is needed: Eric reviews any manually seeded RAISED indicators and sets
each to ACKNOWLEDGED, ACCEPTED_DEBT, or RESOLVED. This is not ongoing maintenance.

**R4 — `rejection_rationale` adoption.** The table has value only if populated.
Enforcement mechanism: Eric Gate briefing explicitly surfaces whether
`rejection_rationale` rows exist for the active trail. Empty is visible.

---

## Open Questions for Eric

**OQ-C1-001 — RESOLVED in this revision.** Decision trail authorship: Drafter/Reviewer
creates draft row at CONSENSUS_REACHED; Closeout finalizes after Eric's decision.
This is now the stated rule in the schema section above.

**OQ-C1-002 — `goal_references.dependency_node` vocabulary enforcement.**
Free text for now; convention requires matching the exact node label from
`CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`. A CHECK constraint against a fixed list is
deferred until the node vocabulary stabilizes. Component 5 can validate
retrospectively. Eric decides whether to accept this deferral or require a CHECK
constraint at migration 0008.

**OQ-C1-003 — `drift_indicators` auto-promotion threshold.**
The promotion logic belongs to Component 4, not Component 1. The schema supports
it. The threshold question (session count vs. calendar time) is deferred to the
Component 4 design. No decision required from Eric at this stage.

---

## What This Design Does Not Include

Explicitly out of scope for Component 1:

- Any UI changes (gated on Tier 10)
- Any Router changes (Component 4)
- Any Eric Gate implementation (Component 3)
- Any change to existing spine tables
- Any backfill of prior workflow_runs
- Any VDB or Chroma integration
- `gate_db_state.py` extension (implementation phase only)
- Drift indicator auto-promotion logic (Component 4)

---

## Revision Log

| Version | Date | Changes |
|---------|------|---------|
| v1 | 2026-06-10 | Initial draft |
| v2 | 2026-06-10 | ChatGPT audit incorporated: resolved authorship contradiction; added UNIQUE constraint on decision_trails; corrected migration description to include triggers; added acknowledged_by, resolved_by, status_updated_at to drift_indicators; added CHECK constraints to all enum-like authored_by/detected_by/rejected_by fields; corrected foreign key description; added CHECK constraint on goal_references.linked_record_table; reframed drift promotion as future behavior supported, not Component 1 requirement |
| v3 | 2026-06-10 | Eric approval pre-check: corrected linked_record_table CHECK to SQLite-safe NULL form: field IS NULL OR field IN (...) |
| v4 | 2026-06-10 | v4impl implemented. Fixes: FK columns changed from INTEGER to TEXT to match workflow_runs.id and active_blockers.id (both TEXT PK). Removed redundant explicit UNIQUE INDEX on decision_trails (table-level UNIQUE constraint handles it). Fixed SQLite comma-after-DEFAULT parser quirk. Applied migration 0008 to cis_memory.db — 4 tables, 8 indexes, 2 triggers. |

---

## Protocol Status

1. ✅ Claude drafts (v1)
2. ✅ ChatGPT audits (8 findings — all incorporated in v2)
3. ✅ Eric approves (2026-06-10: "go ahead")
4. ✅ v4impl implements (migration 0008 applied, verified)
5. ⬜ Deterministic gates verify before spine record written
