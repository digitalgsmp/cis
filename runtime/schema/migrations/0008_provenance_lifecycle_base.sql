-- Migration 0008: Provenance and Lifecycle Base Schema
-- Foundation Hardening Phase — Component 1
-- Design: Claude (v3), audited by ChatGPT, approved by Eric
-- Implemented by v4impl 2026-06-10
--
-- Four new tables supporting Components 2-5:
--   goal_references     — connects actions to project goals and dependency graph nodes
--   decision_trails     — condensed path from problem → deliberation → action
--   drift_indicators    — flags for governance gaps, temporary scaffolding, unresolved objections
--   rejection_rationale — records what was considered and why it was not chosen
--
-- FK type corrections (implementer review F1): workflow_runs.id and active_blockers.id
-- are TEXT PRIMARY KEY. All FK columns use TEXT to match.

---------------------------------------------------------------------
-- Table 1: goal_references
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goal_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id     TEXT NOT NULL REFERENCES workflow_runs(id),

    goal_label          TEXT NOT NULL,
    -- Plain-language label for the goal this action serves.
    -- Example: "Pipeline stability before Tier 8"

    dependency_node     TEXT NOT NULL,
    -- Exact node label from CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md that this
    -- action closes or advances.

    tier_advanced       TEXT,
    -- Which tier is advanced by completing this action.

    advancement_type    TEXT NOT NULL CHECK (advancement_type IN (
                            'CLOSES_NODE',
                            'ADVANCES_TIER',
                            'RESOLVES_BLOCKER',
                            'RESOLVES_OPEN_QUESTION',
                            'ESTABLISHES_PREREQUISITE'
                        )),

    linked_record_table TEXT CHECK (
                            linked_record_table IS NULL OR linked_record_table IN (
                                'active_blockers',
                                'open_questions',
                                'project_decisions',
                                'next_actions'
                            )
                        ),
    linked_record_id    INTEGER,

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


---------------------------------------------------------------------
-- Table 2: decision_trails
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decision_trails (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id         TEXT NOT NULL REFERENCES workflow_runs(id),

    trail_sequence          INTEGER NOT NULL,
    -- 1-indexed sequence within this workflow_run.

    problem_statement       TEXT NOT NULL,
    -- One to three sentences. What problem or gap triggered this decision point.

    research_summary        TEXT,
    -- What the Research profile surfaced, if a research round was run.

    draft_summary           TEXT,
    -- What the Drafter proposed. Condensed, not the full artifact.

    review_summary          TEXT,
    -- What the Reviewer raised. Objections, consensus signal, round count.

    external_audit_summary  TEXT,
    -- What Claude and/or ChatGPT returned, if an escalation was performed.

    proposed_action         TEXT NOT NULL,
    -- The action that emerged from deliberation. One paragraph, plain language.

    round_count             INTEGER NOT NULL DEFAULT 1,
    -- Number of Drafter->Reviewer rounds before CONSENSUS_REACHED or escalation.

    consensus_signal        TEXT NOT NULL CHECK (consensus_signal IN (
                                'CONSENSUS_REACHED',
                                'ESCALATED_TO_ERIC',
                                'ESCALATED_EXTERNAL',
                                'OPERATOR_COMMAND'
                            )),

    eric_decision           TEXT CHECK (eric_decision IN (
                                'APPROVED',
                                'VETOED',
                                'REDIRECTED',
                                'DEFERRED',
                                NULL
                            )),
    -- Null when first created (pre-Gate). Set by Closeout after Eric decides.

    eric_decision_note      TEXT,
    -- Required if eric_decision is VETOED or REDIRECTED.

    eric_decided_at         TEXT,
    -- Null until Closeout finalizes.

    authored_by             TEXT NOT NULL CHECK (authored_by IN (
                                'DRAFTER',
                                'REVIEWER',
                                'CLOSEOUT',
                                'ROUTER'
                            )),
    -- Who created the initial draft row. Closeout updates but does not re-set.

    created_at              TEXT NOT NULL DEFAULT (datetime('now')),
    -- updated_at is managed by trg_decision_trails_updated_at trigger.
    -- Closeout should NOT set updated_at explicitly; the trigger handles it.
    updated_at              TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (workflow_run_id, trail_sequence)
);

CREATE INDEX IF NOT EXISTS idx_decision_trails_run
    ON decision_trails(workflow_run_id);

CREATE TRIGGER IF NOT EXISTS trg_decision_trails_updated_at
    AFTER UPDATE ON decision_trails
    FOR EACH ROW
    BEGIN
        UPDATE decision_trails SET updated_at = datetime('now') WHERE id = OLD.id;
    END;


---------------------------------------------------------------------
-- Table 3: drift_indicators
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drift_indicators (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    workflow_run_id     TEXT REFERENCES workflow_runs(id),
    -- Nullable. Some drift indicators are not associated with a specific run
    -- (e.g., a stale tier detected at session start by the Router).

    indicator_type      TEXT NOT NULL CHECK (indicator_type IN (
                            'TEMPORARY_DEPENDENCY_NO_RETIREMENT',
                            'ACTION_DIVERGES_FROM_DEPENDENCY_GRAPH',
                            'OBJECTION_DISMISSED_WITHOUT_RESOLUTION',
                            'COMPONENT_PATCHED_WITHOUT_ROOT_CAUSE',
                            'GATE_BYPASSED',
                            'ERIC_GATE_NO_PROVENANCE'
                        )),

    description         TEXT NOT NULL,
    -- Plain-language description of the specific drift condition detected.

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
                            'ACKNOWLEDGED',
                            'RESOLVED',
                            'ESCALATED',
                            'ACCEPTED_DEBT',
                            'WONT_FIX'
                        )),

    resolution_note     TEXT,
    -- Required when status transitions to RESOLVED, ACCEPTED_DEBT, or WONT_FIX.

    linked_decision_trail_id    INTEGER REFERENCES decision_trails(id),
    linked_blocker_id           TEXT REFERENCES active_blockers(id),

    raised_at               TEXT NOT NULL DEFAULT (datetime('now')),

    acknowledged_at         TEXT,
    acknowledged_by         TEXT CHECK (acknowledged_by IN (
                                'ERIC',
                                'ROUTER',
                                'CLOSEOUT',
                                'EXTERNAL_ADVISOR',
                                NULL
                            )),

    resolved_at             TEXT,
    resolved_by             TEXT CHECK (resolved_by IN (
                                'ERIC',
                                'ROUTER',
                                'CLOSEOUT',
                                'EXTERNAL_ADVISOR',
                                'V4_IMPLEMENTER',
                                NULL
                            )),

    status_updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    -- Updated on every status transition via trigger.

    raised_by_run_id        TEXT REFERENCES workflow_runs(id)
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


---------------------------------------------------------------------
-- Table 4: rejection_rationale
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rejection_rationale (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    decision_trail_id       INTEGER NOT NULL REFERENCES decision_trails(id),
    workflow_run_id         TEXT NOT NULL REFERENCES workflow_runs(id),
    -- Denormalized for query convenience. Must match decision_trail.workflow_run_id.

    rejected_option_label   TEXT NOT NULL,
    -- Short label for the rejected approach.

    rejected_option_summary TEXT NOT NULL,
    -- One to three sentences describing the rejected option.

    rejection_reason        TEXT NOT NULL CHECK (rejection_reason IN (
                                'ARCHITECTURAL_MISMATCH',
                                'ONE_TO_MANY_VIOLATION',
                                'QUERYABILITY_GAP',
                                'LIFECYCLE_UNSUPPORTED',
                                'GOVERNANCE_GAP',
                                'SCOPE_VIOLATION',
                                'DEPENDENCY_ORDER_VIOLATION',
                                'ERIC_REJECTED',
                                'EXTERNAL_ADVISOR_REJECTED'
                            )),

    rejection_detail        TEXT NOT NULL,
    -- Plain language. Concrete explanation of why this option was rejected.

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
