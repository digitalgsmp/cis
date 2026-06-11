-- Migration 0009: Advisor Escalation Protocol Schema
-- Foundation Hardening Phase — Component 2
-- Design: Claude (Revision 2), audited by ChatGPT, approved by Eric
-- Section 11 resolved: project_state confirmed present
-- Implemented by v4impl 2026-06-10
--
-- Three new tables:
--   advisor_escalations         — one row per escalation lifecycle
--   advisor_escalation_packets  — one row per immutable packet version
--   advisor_responses           — one row per expected advisor per packet exchange
--
-- Lifecycle pattern mirrors project_state: append-only with superseded_by
-- for packet versioning and escalation supersession.

---------------------------------------------------------------------
-- Table 1: advisor_escalations
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS advisor_escalations (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,

    workflow_run_id             TEXT REFERENCES workflow_runs(id),
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

CREATE INDEX IF NOT EXISTS idx_advisor_escalations_run
    ON advisor_escalations(workflow_run_id);

CREATE INDEX IF NOT EXISTS idx_advisor_escalations_status
    ON advisor_escalations(status);


---------------------------------------------------------------------
-- Table 2: advisor_escalation_packets
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS advisor_escalation_packets (
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

CREATE INDEX IF NOT EXISTS idx_advisor_escalation_packets_esc
    ON advisor_escalation_packets(escalation_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_advisor_escalation_packets_ver
    ON advisor_escalation_packets(escalation_id, packet_version);


---------------------------------------------------------------------
-- Table 3: advisor_responses
---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS advisor_responses (
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

CREATE INDEX IF NOT EXISTS idx_advisor_responses_esc
    ON advisor_responses(escalation_id);

CREATE INDEX IF NOT EXISTS idx_advisor_responses_pkt
    ON advisor_responses(packet_id);

CREATE INDEX IF NOT EXISTS idx_advisor_responses_status
    ON advisor_responses(response_status);
