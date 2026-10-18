-- Migration 0041: semantic-transaction continuity ledger.
--
-- Additive only. Not yet applied to the live spine (data/cis_memory.db).
--
-- A row binds one lifecycle evaluation of a meaningful
-- Input -> Process -> Output transition to the exact hashes of its input,
-- output, and evidence set, plus the contract version that produced it.
-- Domain state writers insert their mutation and a ledger row in one SQLite
-- transaction. The analysis call itself occurs before BEGIN/COMMIT so no
-- model or network latency is ever held inside a database write lock.
--
-- The ledger is append-only: a transaction_id's lifecycle (EVALUATED ->
-- COMMITTED / FAILED / INVALIDATED / SUPERSEDED) is a sequence of appended
-- rows, never an UPDATE of a prior row. transaction_id is therefore NOT
-- unique here -- the current state of a transaction_id is "whichever row
-- for it has the highest id", not "the only row for it". A request_id may
-- legitimately carry more than one transaction of the same kind (e.g. two
-- PLAN transactions prepared in the same request), so (request_id, kind) is
-- not unique either.
--
-- envelope_json and check_json carry metadata and hashes only -- never the
-- raw input_payload/proposed_output content, a retrieved excerpt, a secret,
-- or generated code. Callers that need the original content keep it outside
-- the ledger and rely on input_hash/output_hash/evidence_set_hash to detect
-- drift.

CREATE TABLE IF NOT EXISTS continuity_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Optional caller-supplied idempotency key for one ledger row (distinct
    -- from transaction_id, which identifies the lifecycle, not one row).
    -- Auto-generated when a writer does not supply one, so either calling
    -- convention inserts cleanly.
    ledger_event_id TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    transaction_id TEXT NOT NULL,
    request_id TEXT,
    project_id TEXT,
    kind TEXT NOT NULL CHECK (kind IN (
        'INGEST', 'RETRIEVAL', 'INTERPRETATION', 'MODEL_OUTPUT',
        'KNOWLEDGE_FORMATION', 'PLAN', 'APPROVAL', 'EXECUTION',
        'VERIFICATION', 'PROMOTION', 'REUSE'
    )),
    criticality TEXT NOT NULL CHECK (criticality IN (
        'OBSERVE', 'CANDIDATE', 'AUTHORITATIVE'
    )),
    actor TEXT NOT NULL,
    operation TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    evidence_set_hash TEXT NOT NULL,
    contract_version TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN (
        'ALIGNED', 'ANTECEDENT_FOUND', 'MISMATCH',
        'INSUFFICIENT_EVIDENCE', 'UNAVAILABLE'
    )),
    decision TEXT NOT NULL CHECK (decision IN ('ALLOW', 'ANNOTATE', 'HOLD')),
    check_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'EVALUATED'
        CHECK (status IN (
            'EVALUATED', 'COMMITTED', 'FAILED', 'INVALIDATED', 'SUPERSEDED'
        )),
    checked_at TEXT NOT NULL,
    committed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_continuity_transaction_lifecycle
    ON continuity_transactions(transaction_id, id);

CREATE INDEX IF NOT EXISTS idx_continuity_project_time
    ON continuity_transactions(project_id, created_at);

CREATE INDEX IF NOT EXISTS idx_continuity_decision_status
    ON continuity_transactions(decision, status, created_at);

CREATE INDEX IF NOT EXISTS idx_continuity_request_kind
    ON continuity_transactions(request_id, kind);
