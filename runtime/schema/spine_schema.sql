-- spine_schema.sql — CIS Deterministic State Spine
-- Tier 4.1: Minimum schema (workflow_runs + deliberation_rounds)
-- Updated: Migration 0005 — Kanban retired per ADR-013.
-- Updated: Migration 0006 — session_closeouts table added.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS workflow_runs (
    id                        TEXT PRIMARY KEY,
    topic                     TEXT NOT NULL,
    result                    TEXT NOT NULL CHECK (result IN
                              ('CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    requires_eric_review      INTEGER NOT NULL DEFAULT 1
                              CHECK (requires_eric_review IN (0, 1)),
    max_rounds                INTEGER NOT NULL,
    max_consecutive_revisions INTEGER NOT NULL DEFAULT 3,
    rounds_completed          INTEGER NOT NULL DEFAULT 0,
    final_objections_json     TEXT,
    created_at                TEXT NOT NULL,
    completed_at              TEXT,
    status                    TEXT NOT NULL DEFAULT 'COMPLETE',
    route                     TEXT,
    updated_at                TEXT,
    eric_approved_at          TEXT
);

CREATE TABLE IF NOT EXISTS deliberation_rounds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    round_number    INTEGER NOT NULL,
    drafter_role    TEXT NOT NULL,
    drafter_output  TEXT NOT NULL,
    reviewer_role   TEXT NOT NULL,
    reviewer_signal TEXT NOT NULL CHECK (reviewer_signal IN ('OBJECTIONS', 'CONSENSUS_REACHED', 'ESCALATE', 'ERROR')),
    objections_json TEXT,
    revision_number INTEGER NOT NULL DEFAULT 1,
    requires_eric_review INTEGER NOT NULL DEFAULT 1 CHECK (requires_eric_review IN (0, 1)),
    created_at      TEXT NOT NULL,
    UNIQUE(run_id, round_number)
);

CREATE TABLE IF NOT EXISTS workflow_run_artifacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workflow_run_legacy_links (
    id             TEXT PRIMARY KEY,
    run_id         TEXT NOT NULL,
    kanban_card_id TEXT NOT NULL,
    kanban_board   TEXT,
    retired_at     TEXT NOT NULL DEFAULT (datetime('now')),
    note           TEXT
);


CREATE TABLE IF NOT EXISTS session_closeouts (
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
    created_by                   TEXT NOT NULL DEFAULT 'operator_command',
    push_status                  TEXT
);

-- ── Component 2: Advisor Escalation Protocol Tables ──────────────
-- Mirror of migration 0009. Keep in sync.

CREATE TABLE IF NOT EXISTS advisor_escalations (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_run_id             TEXT REFERENCES workflow_runs(id),
    trigger_class               TEXT NOT NULL CHECK (trigger_class IN ('DISCRETIONARY','MANDATORY')),
    trigger_reason              TEXT NOT NULL,
    escalation_scope            TEXT NOT NULL,
    status                      TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','PACKET_BUILT','TRANSMITTED','RESPONSES_COMPLETE','RECONCILED','ABANDONED','SUPERSEDED','CANCELLED_BY_ERIC')),
    reconciliation_disposition  TEXT CHECK (reconciliation_disposition IN ('ACCEPT','ACCEPT_WITH_MODIFICATION','REJECT','RETURN_TO_DRAFT','ESCALATE_FURTHER',NULL)),
    reconciliation_note         TEXT,
    advisor_divergence_summary  TEXT,
    advisor_positions_json      TEXT,
    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),
    reconciled_at               TEXT,
    abandoned_at                TEXT,
    abandoned_reason            TEXT,
    superseded_by               INTEGER REFERENCES advisor_escalations(id)
);
CREATE INDEX IF NOT EXISTS idx_advisor_escalations_run ON advisor_escalations(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_advisor_escalations_status ON advisor_escalations(status);

CREATE TABLE IF NOT EXISTS advisor_escalation_packets (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    escalation_id               INTEGER NOT NULL REFERENCES advisor_escalations(id),
    packet_version              INTEGER NOT NULL DEFAULT 1,
    packet_raw                  TEXT NOT NULL,
    packet_hash                 TEXT NOT NULL,
    git_head                    TEXT NOT NULL,
    advisor_target              TEXT NOT NULL CHECK (advisor_target IN ('CLAUDE','CHATGPT','BOTH')),
    requested_response_type     TEXT NOT NULL CHECK (requested_response_type IN ('AUDIT','PROPOSAL_REVIEW','RISK_ASSESSMENT','DESIGN_INPUT')),
    packet_status               TEXT NOT NULL DEFAULT 'PACKET_BUILT' CHECK (packet_status IN ('PACKET_BUILT','TRANSMITTED')),
    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),
    transmitted_at              TEXT
);
CREATE INDEX IF NOT EXISTS idx_advisor_escalation_packets_esc ON advisor_escalation_packets(escalation_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_advisor_escalation_packets_ver ON advisor_escalation_packets(escalation_id, packet_version);

CREATE TABLE IF NOT EXISTS advisor_responses (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    escalation_id               INTEGER NOT NULL REFERENCES advisor_escalations(id),
    packet_id                   INTEGER NOT NULL REFERENCES advisor_escalation_packets(id),
    advisor                     TEXT NOT NULL CHECK (advisor IN ('CLAUDE','CHATGPT')),
    transmission_mode           TEXT NOT NULL DEFAULT 'MANUAL_PASTE' CHECK (transmission_mode IN ('MANUAL_PASTE','API')),
    response_raw                TEXT,
    responded_packet_hash       TEXT,
    hash_match_status           TEXT CHECK (hash_match_status IN ('MATCH','MISMATCH',NULL)),
    primary_type                TEXT CHECK (primary_type IN ('AUDIT_PASS','AUDIT_OBJECTION','PROPOSAL','CLARIFICATION_REQUEST','RISK_FLAG','RECOMMENDATION',NULL)),
    secondary_flags             TEXT,
    classification_source       TEXT CHECK (classification_source IN ('ERIC','TOOL','HERMES_ASSISTED',NULL)),
    classification_status       TEXT CHECK (classification_status IN ('PROPOSED','CONFIRMED','CORRECTED',NULL)),
    response_status             TEXT NOT NULL DEFAULT 'EXPECTED' CHECK (response_status IN ('EXPECTED','TRANSMITTED','RECEIVED','INGESTED','CLASSIFIED')),
    received_at                 TEXT,
    ingested_at                 TEXT
);
CREATE INDEX IF NOT EXISTS idx_advisor_responses_esc ON advisor_responses(escalation_id);
CREATE INDEX IF NOT EXISTS idx_advisor_responses_pkt ON advisor_responses(packet_id);
CREATE INDEX IF NOT EXISTS idx_advisor_responses_status ON advisor_responses(response_status);

-- Migration 0010: Eric Gate Approvals (Component 3)
CREATE TABLE IF NOT EXISTS eric_gate_approvals (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('APPROVE', 'VETO', 'RETURN_TO_DRAFT')),
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
    FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(id),
    FOREIGN KEY (goal_reference_id) REFERENCES goal_references(id),
    FOREIGN KEY (supersedes_approval_id) REFERENCES eric_gate_approvals(id)
);
CREATE INDEX IF NOT EXISTS idx_eric_gate_approvals_workflow_run_id
    ON eric_gate_approvals(workflow_run_id);
CREATE INDEX IF NOT EXISTS idx_eric_gate_approvals_goal_reference_id
    ON eric_gate_approvals(goal_reference_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_eric_gate_one_current_decision
    ON eric_gate_approvals(workflow_run_id)
    WHERE is_current = 1;
