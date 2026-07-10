CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE project_decisions (
    id          TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    decision    TEXT NOT NULL,
    reason      TEXT,
    status      TEXT NOT NULL DEFAULT 'DECIDED'
                    CHECK (status IN ('DECIDED', 'OPEN', 'SUPERSEDED')),
    decided_at  TEXT NOT NULL,
    superseded_by TEXT
);
CREATE TABLE open_questions (
    id          TEXT PRIMARY KEY,
    question    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'OPEN'
                    CHECK (status IN ('OPEN', 'RESOLVED', 'DEFERRED')),
    resolution  TEXT,
    opened_at   TEXT NOT NULL,
    resolved_at TEXT
, priority INTEGER NOT NULL DEFAULT 0, session_id TEXT NOT NULL DEFAULT 'current');
CREATE TABLE next_actions (
    id          TEXT PRIMARY KEY,
    tier        TEXT,
    description TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETE', 'BLOCKED', 'DEFERRED')),
    depends_on  TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT
);
CREATE TABLE active_blockers (
    id          TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'ACTIVE'
                    CHECK (status IN ('ACTIVE', 'RESOLVED')),
    resolution  TEXT,
    created_at  TEXT NOT NULL,
    resolved_at TEXT
);
CREATE TABLE project_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key             TEXT NOT NULL,
    value           TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('git', 'gate', 'manual')),
    evidence_hash   TEXT,
    evidence_run_id TEXT,
    created_at      TEXT NOT NULL,
    superseded_at   TEXT,
    superseded_by   INTEGER REFERENCES project_state(id)
);
CREATE INDEX idx_project_state_key_created
    ON project_state(key, created_at);
CREATE TABLE dam_assets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path       TEXT NOT NULL,
    file_hash       TEXT NOT NULL,           -- SHA256 of file contents
    file_size       INTEGER NOT NULL,        -- bytes
    source_profile  TEXT NOT NULL,           -- 'prime', 'v4impl', 'r1', 'v4pro'
    session_id      TEXT,                    -- extracted from file, may be NULL for edge cases
    session_start   TEXT,                    -- ISO timestamp from file
    message_count   INTEGER NOT NULL,
    imported_at     TEXT NOT NULL            -- ISO timestamp of import
);
CREATE UNIQUE INDEX idx_dam_assets_hash ON dam_assets(file_hash);
CREATE TABLE dam_extracted_text (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id        INTEGER NOT NULL REFERENCES dam_assets(id) ON DELETE CASCADE,
    segment_index   INTEGER NOT NULL,        -- 0-based position within the file's messages
    speaker_role    TEXT NOT NULL,           -- 'user', 'assistant', 'tool', 'system'
    content_text    TEXT NOT NULL,            -- verbatim message content
    created_at      TEXT NOT NULL            -- ISO timestamp from the message (or file session_start)
);
CREATE INDEX idx_dam_ext_asset ON dam_extracted_text(asset_id);
CREATE INDEX idx_dam_ext_role ON dam_extracted_text(speaker_role);
CREATE VIRTUAL TABLE dam_extracted_text_fts USING fts5(
    content_text,
    content='dam_extracted_text',
    content_rowid='id'
)
/* dam_extracted_text_fts(content_text) */;
CREATE TABLE IF NOT EXISTS 'dam_extracted_text_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'dam_extracted_text_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'dam_extracted_text_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'dam_extracted_text_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER dam_ext_ai AFTER INSERT ON dam_extracted_text BEGIN
    INSERT INTO dam_extracted_text_fts(rowid, content_text) VALUES (new.id, new.content_text);
END;
CREATE TRIGGER dam_ext_ad AFTER DELETE ON dam_extracted_text BEGIN
    INSERT INTO dam_extracted_text_fts(dam_extracted_text_fts, rowid, content_text) VALUES ('delete', old.id, old.content_text);
END;
CREATE TRIGGER dam_ext_au AFTER UPDATE ON dam_extracted_text BEGIN
    INSERT INTO dam_extracted_text_fts(dam_extracted_text_fts, rowid, content_text) VALUES ('delete', old.id, old.content_text);
    INSERT INTO dam_extracted_text_fts(rowid, content_text) VALUES (new.id, new.content_text);
END;
CREATE TABLE workflow_run_legacy_links (
    id             TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL,
    kanban_card_id TEXT NOT NULL,
    kanban_board   TEXT,
    retired_at     TEXT NOT NULL DEFAULT (datetime('now')),
    note           TEXT
);
CREATE TABLE workflow_run_artifacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES "workflow_runs_old"(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE session_closeouts (
    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at                   TEXT NOT NULL,
    completed_at                 TEXT,
    status                       TEXT NOT NULL CHECK (status IN ('PASS', 'FAIL', 'BLOCKED')),
    start_head                   TEXT,
    end_head                     TEXT,
    dirty_before_json            TEXT,
    dirty_after_json             TEXT,
    generated_context            INTEGER NOT NULL DEFAULT 0,
    export_agreement_status      TEXT,
    build_state_coherence_status TEXT,
    commit_hash                  TEXT,
    log_path                     TEXT,
    failure_step                 TEXT,
    failure_summary              TEXT,
    created_by                   TEXT NOT NULL DEFAULT 'operator_command'
, push_status TEXT);
CREATE TABLE goal_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id     TEXT NOT NULL REFERENCES "workflow_runs_old"(id),

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
CREATE INDEX idx_goal_references_run
    ON goal_references(workflow_run_id);
CREATE INDEX idx_goal_references_node
    ON goal_references(dependency_node);
CREATE TABLE drift_indicators (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,

    workflow_run_id     TEXT REFERENCES "workflow_runs_old"(id),
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

    raised_by_run_id        TEXT REFERENCES "workflow_runs_old"(id)
);
CREATE INDEX idx_drift_indicators_status
    ON drift_indicators(status);
CREATE INDEX idx_drift_indicators_run
    ON drift_indicators(workflow_run_id);
CREATE INDEX idx_drift_indicators_type
    ON drift_indicators(indicator_type);
CREATE TRIGGER trg_drift_indicators_status_updated_at
    AFTER UPDATE OF status ON drift_indicators
    FOR EACH ROW
    BEGIN
        UPDATE drift_indicators SET status_updated_at = datetime('now') WHERE id = OLD.id;
    END;
CREATE TABLE rejection_rationale (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,

    decision_trail_id       INTEGER NOT NULL REFERENCES decision_trails(id),
    workflow_run_id         TEXT NOT NULL REFERENCES "workflow_runs_old"(id),
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
CREATE INDEX idx_rejection_rationale_trail
    ON rejection_rationale(decision_trail_id);
CREATE INDEX idx_rejection_rationale_run
    ON rejection_rationale(workflow_run_id);
CREATE TABLE decision_trails (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id         TEXT NOT NULL REFERENCES "workflow_runs_old"(id),

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
CREATE INDEX idx_decision_trails_run
    ON decision_trails(workflow_run_id);
CREATE TRIGGER trg_decision_trails_updated_at
    AFTER UPDATE ON decision_trails
    FOR EACH ROW
    BEGIN
        UPDATE decision_trails SET updated_at = datetime('now') WHERE id = OLD.id;
    END;
CREATE TABLE advisor_escalations (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,

    workflow_run_id             TEXT REFERENCES "workflow_runs_old"(id),
    -- Nullable for phase-level questions not tied to a run.

    trigger_class               TEXT NOT NULL CHECK (trigger_class IN (
                                    'DISCRETIONARY',
                                    'MANDATORY'
                                )),

    trigger_reason              TEXT NOT NULL,
    -- Plain-language reason. E.g., 'ERIC_REQUEST', 'OPEN_DRIFT_INDICATOR',
    -- 'DELIBERATION_EXHAUSTION', 'VERIFICATION_FAILURE_2X', etc.

    escalation_scope            TEXT NOT NULL,
    -- What component, tier, or decision the escalation covers.

    status                      TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN (
                                    'OPEN',
                                    'PACKET_BUILT',
                                    'TRANSMITTED',
                                    'RESPONSES_COMPLETE',
                                    'RECONCILED',
                                    'ABANDONED',
                                    'SUPERSEDED',
                                    'CANCELLED_BY_ERIC'
                                )),

    reconciliation_disposition  TEXT CHECK (reconciliation_disposition IN (
                                    'ACCEPT',
                                    'ACCEPT_WITH_MODIFICATION',
                                    'REJECT',
                                    'RETURN_TO_DRAFT',
                                    'ESCALATE_FURTHER',
                                    NULL
                                )),

    reconciliation_note         TEXT,
    -- Eric's plain-language reconciliation note.

    advisor_divergence_summary  TEXT,
    -- Plain-language statement of where advisors disagreed (BOTH-advisor escalations).

    advisor_positions_json      TEXT,
    -- Minimal structured capture of each advisor's position on contested points.

    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),

    reconciled_at               TEXT,
    -- Set when reconciliation is recorded.

    abandoned_at                TEXT,
    -- Set when escalation enters a terminal state.

    abandoned_reason            TEXT,
    -- Mandatory for ABANDONED, SUPERSEDED, CANCELLED_BY_ERIC.

    superseded_by               INTEGER REFERENCES advisor_escalations(id)
    -- Self-FK for SUPERSEDED terminal state. Mirrors project_state.superseded_by.
);
CREATE INDEX idx_advisor_escalations_run
    ON advisor_escalations(workflow_run_id);
CREATE INDEX idx_advisor_escalations_status
    ON advisor_escalations(status);
CREATE TABLE advisor_escalation_packets (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,

    escalation_id               INTEGER NOT NULL REFERENCES advisor_escalations(id),

    packet_version              INTEGER NOT NULL DEFAULT 1,
    -- Starts at 1. Incremented per new version under the same escalation_id.

    packet_raw                  TEXT NOT NULL,
    -- Full verbatim packet text. The immutable evidence artifact.

    packet_hash                 TEXT NOT NULL,
    -- SHA256 over sections P1-P6. Binds responses to this exact version.

    git_head                    TEXT NOT NULL,
    -- Git commit hash at packet build time.

    advisor_target              TEXT NOT NULL CHECK (advisor_target IN (
                                    'CLAUDE',
                                    'CHATGPT',
                                    'BOTH'
                                )),

    requested_response_type     TEXT NOT NULL CHECK (requested_response_type IN (
                                    'AUDIT',
                                    'PROPOSAL_REVIEW',
                                    'RISK_ASSESSMENT',
                                    'DESIGN_INPUT'
                                )),

    packet_status               TEXT NOT NULL DEFAULT 'PACKET_BUILT' CHECK (packet_status IN (
                                    'PACKET_BUILT',
                                    'TRANSMITTED'
                                )),

    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),

    transmitted_at              TEXT
    -- Records first transmission of this version.
);
CREATE INDEX idx_advisor_escalation_packets_esc
    ON advisor_escalation_packets(escalation_id);
CREATE UNIQUE INDEX idx_advisor_escalation_packets_ver
    ON advisor_escalation_packets(escalation_id, packet_version);
CREATE TABLE advisor_responses (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,

    escalation_id               INTEGER NOT NULL REFERENCES advisor_escalations(id),

    packet_id                   INTEGER NOT NULL REFERENCES advisor_escalation_packets(id),

    advisor                     TEXT NOT NULL CHECK (advisor IN (
                                    'CLAUDE',
                                    'CHATGPT'
                                )),

    transmission_mode           TEXT NOT NULL DEFAULT 'MANUAL_PASTE' CHECK (transmission_mode IN (
                                    'MANUAL_PASTE',
                                    'API'
                                )),

    response_raw                TEXT,
    -- Verbatim advisor response text. Null until RECEIVED.

    responded_packet_hash       TEXT,
    -- The hash the advisor was responding to. Set at ingestion.

    hash_match_status           TEXT CHECK (hash_match_status IN (
                                    'MATCH',
                                    'MISMATCH',
                                    NULL
                                )),
    -- NULL until response ingested.

    primary_type                TEXT CHECK (primary_type IN (
                                    'AUDIT_PASS',
                                    'AUDIT_OBJECTION',
                                    'PROPOSAL',
                                    'CLARIFICATION_REQUEST',
                                    'RISK_FLAG',
                                    'RECOMMENDATION',
                                    NULL
                                )),

    secondary_flags             TEXT,
    -- Optional comma-separated flags.

    classification_source       TEXT CHECK (classification_source IN (
                                    'ERIC',
                                    'TOOL',
                                    'HERMES_ASSISTED',
                                    NULL
                                )),

    classification_status       TEXT CHECK (classification_status IN (
                                    'PROPOSED',
                                    'CONFIRMED',
                                    'CORRECTED',
                                    NULL
                                )),

    response_status             TEXT NOT NULL DEFAULT 'EXPECTED' CHECK (response_status IN (
                                    'EXPECTED',
                                    'TRANSMITTED',
                                    'RECEIVED',
                                    'INGESTED',
                                    'CLASSIFIED'
                                )),

    received_at                 TEXT,
    ingested_at                 TEXT
);
CREATE INDEX idx_advisor_responses_esc
    ON advisor_responses(escalation_id);
CREATE INDEX idx_advisor_responses_pkt
    ON advisor_responses(packet_id);
CREATE INDEX idx_advisor_responses_status
    ON advisor_responses(response_status);
CREATE TABLE eric_gate_approvals (
    id TEXT PRIMARY KEY,

    workflow_run_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (
        decision IN ('APPROVE', 'VETO', 'RETURN_TO_DRAFT')
    ),

    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL DEFAULT 'Eric',

    goal_reference_id INTEGER NOT NULL,

    briefing_hash TEXT NOT NULL,
    briefing_json TEXT NOT NULL,

    drift_snapshot_json TEXT NOT NULL,
    decision_trail_snapshot_json TEXT NOT NULL,

    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    supersedes_approval_id TEXT,

    rationale TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY (workflow_run_id)
        REFERENCES "workflow_runs_old"(id),

    FOREIGN KEY (goal_reference_id)
        REFERENCES goal_references(id),

    FOREIGN KEY (supersedes_approval_id)
        REFERENCES eric_gate_approvals(id)
);
CREATE INDEX idx_eric_gate_approvals_workflow_run_id
    ON eric_gate_approvals(workflow_run_id);
CREATE INDEX idx_eric_gate_approvals_goal_reference_id
    ON eric_gate_approvals(goal_reference_id);
CREATE UNIQUE INDEX idx_eric_gate_one_current_decision
    ON eric_gate_approvals(workflow_run_id)
    WHERE is_current = 1;
CREATE TABLE build_plan_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'CIS',
    node_label      TEXT NOT NULL,
    tier            TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN (
                        'PENDING', 'IN_PROGRESS', 'COMPLETE',
                        'BLOCKED', 'DEFERRED', 'PROPOSED'
                    )),
    blocked_reason  TEXT,
    required_role   TEXT,
    allowed_mode    TEXT,
    workflow_run_id TEXT REFERENCES "workflow_runs_old"(id),
    evidence_path   TEXT,
    commit_hash     TEXT,
    completed_at    TEXT,
    approved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, node_label)
);
CREATE TABLE build_plan_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         INTEGER NOT NULL REFERENCES build_plan_nodes(id) ON DELETE CASCADE,
    depends_on_id   INTEGER NOT NULL REFERENCES build_plan_nodes(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL DEFAULT 'HARD'
                    CHECK (dependency_type IN ('HARD', 'SOFT')),
    UNIQUE(node_id, depends_on_id),
    CHECK(node_id != depends_on_id)
);
CREATE INDEX idx_bpn_project_status
    ON build_plan_nodes(project_id, status);
CREATE INDEX idx_bpn_project_sequence
    ON build_plan_nodes(project_id, sequence);
CREATE INDEX idx_bpd_node
    ON build_plan_dependencies(node_id);
CREATE INDEX idx_bpd_depends
    ON build_plan_dependencies(depends_on_id);
CREATE VIRTUAL TABLE session_closeouts_fts USING fts5(
    failure_summary,
    failure_step,
    log_path,
    created_by,
    content='session_closeouts',
    content_rowid='id'
)
/* session_closeouts_fts(failure_summary,failure_step,log_path,created_by) */;
CREATE TABLE IF NOT EXISTS 'session_closeouts_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'session_closeouts_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'session_closeouts_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'session_closeouts_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER session_closeouts_fts_insert AFTER INSERT ON session_closeouts BEGIN
    INSERT INTO session_closeouts_fts(rowid, failure_summary, failure_step, log_path, created_by)
    VALUES (new.id, new.failure_summary, new.failure_step, new.log_path, new.created_by);
END;
CREATE TRIGGER session_closeouts_fts_delete AFTER DELETE ON session_closeouts BEGIN
    INSERT INTO session_closeouts_fts(session_closeouts_fts, rowid, failure_summary, failure_step, log_path, created_by)
    VALUES ('delete', old.id, old.failure_summary, old.failure_step, old.log_path, old.created_by);
END;
CREATE TRIGGER session_closeouts_fts_update AFTER UPDATE ON session_closeouts BEGIN
    INSERT INTO session_closeouts_fts(session_closeouts_fts, rowid, failure_summary, failure_step, log_path, created_by)
    VALUES ('delete', old.id, old.failure_summary, old.failure_step, old.log_path, old.created_by);
    INSERT INTO session_closeouts_fts(rowid, failure_summary, failure_step, log_path, created_by)
    VALUES (new.id, new.failure_summary, new.failure_step, new.log_path, new.created_by);
END;
CREATE TABLE lifecycle_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id         TEXT NOT NULL,
    session_id          TEXT,
    from_state          TEXT NOT NULL,
    to_state            TEXT NOT NULL,
    gate_type           TEXT,
    initiated_by        TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    dispatch_ref        TEXT,
    evidence_ref        TEXT,
    reviewer_message_id TEXT,
    directive_hash      TEXT,
    eric_approved       INTEGER NOT NULL DEFAULT 0,
    eric_bypass         INTEGER NOT NULL DEFAULT 0,
    revision_count      INTEGER NOT NULL DEFAULT 0,
    notes               TEXT
, workflow_run_id TEXT);
CREATE INDEX idx_lifecycle_proposal
    ON lifecycle_events(proposal_id, timestamp);
CREATE TABLE dispatch_log (
    dispatch_id         TEXT PRIMARY KEY,
    proposal_id         TEXT NOT NULL,
    source_actor        TEXT NOT NULL,
    target_agent        TEXT NOT NULL,
    target_endpoint     TEXT NOT NULL,
    lifecycle_state_at  TEXT NOT NULL,
    payload_hash        TEXT NOT NULL,
    payload_summary     TEXT NOT NULL,
    initiated_by        TEXT NOT NULL,
    eric_approved       INTEGER NOT NULL DEFAULT 0,
    timestamp_initiated TEXT NOT NULL,
    current_status      TEXT NOT NULL DEFAULT 'PENDING',
    directive_hash      TEXT,
    timestamp_completed TEXT,
    http_status_code    INTEGER,
    response_message_id TEXT,
    response_summary    TEXT,
    error_message       TEXT
, workflow_run_id TEXT);
CREATE INDEX idx_dispatch_proposal
    ON dispatch_log(proposal_id);
CREATE TABLE dispatch_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dispatch_id         TEXT NOT NULL REFERENCES dispatch_log(dispatch_id),
    event_type          TEXT NOT NULL,
    timestamp           TEXT NOT NULL,
    http_status_code    INTEGER,
    response_message_id TEXT,
    error_message       TEXT
);
CREATE INDEX idx_dispatch_events_dispatch
    ON dispatch_events(dispatch_id);
CREATE INDEX idx_lifecycle_workflow_run
    ON lifecycle_events(workflow_run_id);
CREATE INDEX idx_dispatch_workflow_run
    ON dispatch_log(workflow_run_id);
CREATE TABLE intent_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_text TEXT NOT NULL,
    model_interpretation TEXT,
    mapped_layer TEXT,
    mapped_component TEXT,
    source_file TEXT NOT NULL,
    source_line INTEGER,
    source_timestamp TEXT,
    voice TEXT NOT NULL DEFAULT 'eric-verbatim',
    categories TEXT,
    review_decision TEXT NOT NULL DEFAULT 'CONFIRMED',
    revision_note TEXT,
    eric_confirmed_at TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_intent_map_layer ON intent_map(mapped_layer);
CREATE INDEX idx_intent_map_component ON intent_map(mapped_component);
CREATE INDEX idx_intent_map_voice ON intent_map(voice);
CREATE TABLE anti_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eric_asked TEXT,
    model_produced TEXT,
    friction_type TEXT,
    guardrail_mechanism TEXT,
    source_file TEXT NOT NULL,
    source_line INTEGER,
    failure_flag TEXT,
    review_decision TEXT NOT NULL DEFAULT 'CONFIRMED',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_anti_patterns_flag ON anti_patterns(failure_flag);
CREATE INDEX idx_anti_patterns_friction ON anti_patterns(friction_type);
CREATE TABLE functional_spec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,
    layer TEXT NOT NULL,
    description TEXT,
    wiasw_origin TEXT,
    intent_source_ids TEXT,
    build_status TEXT DEFAULT 'unspecified',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_functional_spec_layer ON functional_spec(layer);
CREATE INDEX idx_functional_spec_component ON functional_spec(component_name);
CREATE TABLE reviewer_brief (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion TEXT NOT NULL,
    category TEXT NOT NULL,
    detail TEXT,
    source_file TEXT,
    source_line INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_reviewer_brief_category ON reviewer_brief(category);
CREATE TABLE knowledge_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    source_key TEXT,
    timestamp TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_km_source ON knowledge_messages(source);
CREATE INDEX idx_km_role ON knowledge_messages(role);
CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(
    content,
    source,
    role,
    content='knowledge_messages',
    content_rowid='id'
)
/* knowledge_messages_fts(content,source,role) */;
CREATE TABLE IF NOT EXISTS 'knowledge_messages_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'knowledge_messages_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'knowledge_messages_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'knowledge_messages_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER km_ai AFTER INSERT ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(rowid, content, source, role)
    VALUES (new.id, new.content, new.source, new.role);
END;
CREATE TRIGGER km_ad AFTER DELETE ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(knowledge_messages_fts, rowid, content, source, role)
    VALUES ('delete', old.id, old.content, old.source, old.role);
END;
CREATE TRIGGER km_au AFTER UPDATE ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(knowledge_messages_fts, rowid, content, source, role)
    VALUES ('delete', old.id, old.content, old.source, old.role);
    INSERT INTO knowledge_messages_fts(rowid, content, source, role)
    VALUES (new.id, new.content, new.source, new.role);
END;
CREATE TABLE session_handoffs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT NOT NULL,               -- "2026-06-29"
    title           TEXT NOT NULL,               -- "June 27-29: Front Door + Reconciliation"
    summary         TEXT NOT NULL,               -- What was built/done
    decisions       TEXT,                        -- Key decisions made this session
    next_actions    TEXT,                        -- What's next (priority order)
    claude_context  TEXT,                        -- Working context for external advisor
    eric_feedback   TEXT,                        -- Eric's verbatim feedback
    gateway_status  TEXT,                        -- Verified port status at handoff time
    git_head        TEXT,                        -- Commit SHA at time of handoff
    is_current      INTEGER NOT NULL DEFAULT 0,  -- 1 = latest active handoff
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_session_handoffs_current
    ON session_handoffs(is_current, created_at DESC);
CREATE TABLE dev_pivot_status (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id          TEXT NOT NULL UNIQUE,              -- 'DEV-PIVOT-01'
    title           TEXT NOT NULL,                      -- 'Governance Reset Proposal'
    category        TEXT NOT NULL CHECK (category IN (
                        'governance', 'enforcement', 'architecture',
                        'pipeline', 'data', 'operations'
                    )),
    status          TEXT NOT NULL DEFAULT 'LIVE' CHECK (status IN (
                        'LIVE', 'INVALIDATED', 'PARTIALLY_INVALIDATED', 'SUPERSEDED'
                    )),
    invalidation_reason TEXT,                           -- what changed to invalidate it
    invalidated_by   TEXT,                              -- capability or change that caused it
    depends_on       TEXT,                              -- what capability this doc's resolution depends on
    capability_gap   TEXT,                              -- what's missing that keeps this LIVE
    affected_sections TEXT,                             -- which sections are stale (comma-separated)
    last_reviewed_at TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_dps_status ON dev_pivot_status(status);
CREATE INDEX idx_dps_category ON dev_pivot_status(category);
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('message','decision','status_change','completion','ingestion','verification','reasoning_stream','gate_decision','spec','review','build_event')),
    source TEXT NOT NULL,
    role TEXT,
    content TEXT NOT NULL,
    entity_id INTEGER,
    intention_id INTEGER,
    evidence_cmd TEXT,
    evidence_output TEXT,
    evidence_verified INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    workflow_run_id TEXT
);
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('gateway','tier','tool','document','decision','project','profile','model')),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE VIEW verification_queue AS
    SELECT id, type, source, content, evidence_cmd, evidence_output, created_at
    FROM observations
    WHERE evidence_cmd IS NOT NULL AND evidence_verified = 0
    ORDER BY created_at DESC
/* verification_queue(id,type,source,content,evidence_cmd,evidence_output,created_at) */;
CREATE INDEX idx_observations_type ON observations(type);
CREATE INDEX idx_observations_source ON observations(source);
CREATE INDEX idx_observations_entity ON observations(entity_id);
CREATE INDEX idx_observations_intention ON observations(intention_id);
CREATE INDEX idx_observations_created ON observations(created_at);
CREATE TABLE intentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    source_session TEXT,
    source_text TEXT NOT NULL,
    paraphrase TEXT,
    category TEXT DEFAULT 'CIS',
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK(status IN ('pending','confirmed','fulfilled','diverged','retired')),
    fulfilled_by TEXT,
    depends_on TEXT,
    notes TEXT
, detail TEXT);
CREATE TABLE agent_trajectories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    role TEXT NOT NULL,
    phase TEXT NOT NULL,
    input_text TEXT NOT NULL,
    output_text TEXT NOT NULL,
    feedback_text TEXT,
    round_number INTEGER,
    outcome TEXT DEFAULT 'pending',
    consensus_reached INTEGER DEFAULT 0,
    config_version TEXT,
    marginal_utility REAL,
    created_at TEXT DEFAULT (datetime('now'))
, tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0);
CREATE INDEX idx_trajectories_run
    ON agent_trajectories(run_id);
CREATE INDEX idx_trajectories_role_phase
    ON agent_trajectories(role, phase);
CREATE INDEX idx_trajectories_outcome
    ON agent_trajectories(outcome);
CREATE VIRTUAL TABLE agent_trajectories_fts USING fts5(
    input_text, output_text, role, phase,
    content='agent_trajectories',
    content_rowid='id'
)
/* agent_trajectories_fts(input_text,output_text,role,phase) */;
CREATE TABLE IF NOT EXISTS 'agent_trajectories_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'agent_trajectories_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'agent_trajectories_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'agent_trajectories_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER trajectories_ai AFTER INSERT ON agent_trajectories BEGIN
    INSERT INTO agent_trajectories_fts(rowid, input_text, output_text, role, phase)
    VALUES (new.id, new.input_text, new.output_text, new.role, new.phase);
END;
CREATE TRIGGER trajectories_ad AFTER DELETE ON agent_trajectories BEGIN
    INSERT INTO agent_trajectories_fts(agent_trajectories_fts, rowid, input_text, output_text, role, phase)
    VALUES ('delete', old.id, old.input_text, old.output_text, old.role, old.phase);
END;
CREATE TRIGGER trajectories_au AFTER UPDATE ON agent_trajectories BEGIN
    INSERT INTO agent_trajectories_fts(agent_trajectories_fts, rowid, input_text, output_text, role, phase)
    VALUES ('delete', old.id, old.input_text, old.output_text, old.role, old.phase);
    INSERT INTO agent_trajectories_fts(rowid, input_text, output_text, role, phase)
    VALUES (new.id, new.input_text, new.output_text, new.role, new.phase);
END;
CREATE TABLE circuit_breaker_state (
    role TEXT PRIMARY KEY,
    failures INTEGER NOT NULL DEFAULT 0,
    last_failure_ts REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE code_review_chunks (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    diff_text TEXT DEFAULT '',
    l1_results TEXT DEFAULT '',
    review_a_pass1 TEXT DEFAULT '',
    review_b_pass2 TEXT DEFAULT '',
    review_a_consensus TEXT DEFAULT '',
    final_verdict TEXT DEFAULT 'PENDING',
    revision_directive TEXT DEFAULT '',
    revision_number INTEGER DEFAULT 1,
    incorporated INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(run_id, chunk_number, revision_number)
);
CREATE TABLE workflow_runs (
    id                        TEXT PRIMARY KEY,
    topic                     TEXT NOT NULL,
    result                    TEXT NOT NULL DEFAULT 'PENDING'
                              CHECK (result IN
                              ('PENDING', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR', 'VERIFY_FAILED')),
    requires_eric_review      INTEGER NOT NULL DEFAULT 1
                              CHECK (requires_eric_review IN (0, 1)),
    max_rounds                INTEGER NOT NULL,
    max_consecutive_revisions INTEGER NOT NULL DEFAULT 3,
    rounds_completed          INTEGER NOT NULL DEFAULT 0,
    final_objections_json     TEXT,
    created_at                TEXT NOT NULL,
    completed_at              TEXT,
    status                    TEXT NOT NULL DEFAULT 'INTAKE',
    route                     TEXT,
    updated_at                TEXT,
    eric_approved_at          TEXT,
    intent                    TEXT,
    directive_hash            TEXT
, project_id TEXT DEFAULT 'cis', parent_run_id TEXT REFERENCES workflow_runs(id));
CREATE TABLE deliberation_rounds (
    id                  INTEGER PRIMARY KEY,
    run_id              TEXT NOT NULL,
    round_number        INTEGER NOT NULL,
    drafter_role        TEXT NOT NULL,
    drafter_output      TEXT NOT NULL DEFAULT '',
    reviewer_role       TEXT NOT NULL DEFAULT '',
    reviewer_signal     TEXT NOT NULL DEFAULT 'PENDING'
                        CHECK (reviewer_signal IN
                        ('PENDING', 'OBJECTIONS', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    objections_json     TEXT,
    revision_number     INTEGER NOT NULL DEFAULT 1,
    requires_eric_review INTEGER NOT NULL DEFAULT 1
                        CHECK (requires_eric_review IN (0, 1)),
    created_at          TEXT NOT NULL,
    reviewer1_output    TEXT DEFAULT '',
    reviewer2_output    TEXT DEFAULT '',
    brain_output        TEXT DEFAULT '',
    verify_output       TEXT DEFAULT '',
    human_question      TEXT DEFAULT '',
    human_answer        TEXT DEFAULT '',
    menter_output       TEXT DEFAULT '',
    UNIQUE(run_id, round_number)
);
CREATE TABLE corpus_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_root TEXT NOT NULL,          -- 'session_closeouts', 'agent_trajectories', 'deliberation_rounds', 'archive'
    source_file TEXT,                   -- original file path or table row reference
    line_number INTEGER,
    timestamp TEXT,
    content_text TEXT NOT NULL,
    project_tag TEXT DEFAULT 'CIS',     -- CIS, SWA, WIAS
    extraction_pass INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_corpus_project ON corpus_entries(project_tag);
CREATE INDEX idx_corpus_source ON corpus_entries(source_root);
CREATE VIRTUAL TABLE corpus_entries_fts USING fts5(
    content_text, source_root, project_tag,
    content='corpus_entries', content_rowid='id'
)
/* corpus_entries_fts(content_text,source_root,project_tag) */;
CREATE TABLE IF NOT EXISTS 'corpus_entries_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'corpus_entries_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'corpus_entries_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'corpus_entries_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER corpus_entries_ai AFTER INSERT ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(rowid, content_text, source_root, project_tag)
    VALUES (new.id, new.content_text, new.source_root, new.project_tag);
END;
CREATE TRIGGER corpus_entries_ad AFTER DELETE ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(corpus_entries_fts, rowid, content_text, source_root, project_tag)
    VALUES ('delete', old.id, old.content_text, old.source_root, old.project_tag);
END;
CREATE TRIGGER corpus_entries_au AFTER UPDATE ON corpus_entries BEGIN
    INSERT INTO corpus_entries_fts(corpus_entries_fts, rowid, content_text, source_root, project_tag)
    VALUES ('delete', old.id, old.content_text, old.source_root, old.project_tag);
    INSERT INTO corpus_entries_fts(rowid, content_text, source_root, project_tag)
    VALUES (new.id, new.content_text, new.source_root, new.project_tag);
END;
CREATE TABLE projects (
    id TEXT PRIMARY KEY,                -- 'cis', 'swa', 'wias'
    name TEXT NOT NULL,
    repo_path TEXT NOT NULL,
    spine_path TEXT NOT NULL,           -- path to cis_memory.db for this project
    agents_md_path TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE run_dependencies (
    run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    depends_on_run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    dependency_type TEXT NOT NULL DEFAULT 'sequential',
    PRIMARY KEY (run_id, depends_on_run_id)
);
CREATE TABLE dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES workflow_runs(id),
    failed_at TEXT DEFAULT (datetime('now')),
    error_message TEXT,
    agent_role TEXT,
    phase TEXT,
    input_text TEXT,
    retry_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending'  -- pending, retried, resolved, abandoned
);
CREATE INDEX idx_dlq_status ON dead_letter_queue(status);
CREATE INDEX idx_dlq_run ON dead_letter_queue(run_id);
