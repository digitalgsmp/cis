# ADR-041 — Artifact Registry: Canonical SHA Binding Schema

**Status:** PROPOSED — pending Layer 3 audit  
**Date:** 2026-04-26  
**Supersedes:** None  
**Required by:** ADR-040 (Layer 3 Audit Mandatory Gate)

---

## Decision

A `manifests` table in `cis_memory.db` is the canonical artifact registry for CIS.

Every build action that produces a manifest writes a record to this table at Layer 1 verification time (`cis_verify.py --manifest`). This table is the authoritative source for SHA binding in all audit validation — including `--session-close-check` and dependency validation.

Extracting SHA from audit rounds is permanently rejected. The canonical SHA must always come from the `manifests` table.

---

## Schema

### Table: `manifests`

```sql
CREATE TABLE IF NOT EXISTS manifests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id     TEXT NOT NULL,
    sha256          TEXT NOT NULL,
    artifact_type   TEXT NOT NULL,
    artifact_name   TEXT NOT NULL,
    artifact_path   TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    action          TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    builder_model_id TEXT NOT NULL DEFAULT '',
    manifest_path   TEXT,
    raw_manifest    TEXT,
    UNIQUE(artifact_id) ON CONFLICT REPLACE
);

CREATE INDEX IF NOT EXISTS idx_manifests_artifact_id ON manifests(artifact_id);
CREATE INDEX IF NOT EXISTS idx_manifests_session_id  ON manifests(session_id);
```

**Field definitions:**

| Field | Type | Required | Description |
|---|---|---|---|
| `artifact_id` | TEXT UNIQUE | YES | Canonical ID: `{type}__{name}__{session}__{seq:03d}` |
| `sha256` | TEXT | YES | Full 64-char hex SHA-256 of the artifact file at write time |
| `artifact_type` | TEXT | YES | `script`, `contract`, `schema`, `record`, `config`, `doc` |
| `artifact_name` | TEXT | YES | Short name component of artifact_id |
| `artifact_path` | TEXT | YES | Absolute path to the artifact file |
| `session_id` | TEXT | YES | CIS session ID string |
| `sequence` | INTEGER | YES | 1-based sequence within session and artifact name |
| `action` | TEXT | YES | Human-readable description of the build action |
| `timestamp` | TEXT | YES | ISO 8601 UTC timestamp of manifest write |
| `builder_model_id` | TEXT | YES | ID of the model that produced this artifact — required for role separation (ADR-040) |
| `manifest_path` | TEXT | NO | Path to the JSON manifest file, if written to disk |
| `raw_manifest` | TEXT | NO | Full JSON manifest content, stored for audit trail |

---

### Table: `live_rounds` — added column

The `live_rounds` table is a **hard dependency** for ADR-041. If `live_rounds` does not exist when the migration runs, the migration fails. ADR-040 enforcement (verdict, model_name, prompt, response) cannot operate without these columns. There is no deferred mode.

```sql
ALTER TABLE live_rounds ADD COLUMN verdict TEXT DEFAULT NULL;
ALTER TABLE live_rounds ADD COLUMN model_name TEXT DEFAULT NULL;
ALTER TABLE live_rounds ADD COLUMN prompt TEXT DEFAULT NULL;
ALTER TABLE live_rounds ADD COLUMN response TEXT DEFAULT NULL;
```

**New fields:**

| Field | Type | Description |
|---|---|---|
| `verdict` | TEXT | Explicit verdict stored at round resolution: `PASS`, `FAIL`, or `CONDITIONAL` |
| `model_name` | TEXT | Name of the external model used for this audit round |
| `prompt` | TEXT | Full prompt sent to the external model — logged verbatim |
| `response` | TEXT | Full response received from the external model — logged verbatim |

**Why:** Strict verdict parsing against free text is unreliable. A dedicated `verdict` field written at round resolution is the only reliable source of truth. `model_name`, `prompt`, and `response` as dedicated fields prevent content-field pollution and enable isolated validation.

---

## Write protocol

`cis_verify.py --manifest <path>` writes to the `manifests` table immediately after Layer 1 PASS. The manifest JSON must contain a complete `artifact_identity` block. On FAIL, no record is written — failed artifacts are not registered.

Write is atomic: if the DB write fails, the verification is marked FAIL and the build action does not advance.

`artifact_id` is UNIQUE — a second write with the same artifact_id updates the existing record (upsert). This handles the case where a file is rebuilt and re-verified in the same session.

---

## SHA binding guarantee

With this schema in place, the SHA binding chain is:

```
Build action writes file
  → cis_verify.py computes sha256 from actual file
  → Layer 1 PASS
  → sha256 written to manifests table (canonical record)
  → Auditor runs Layer 3 and logs full sha256 in audit round
  → validate_audit_round() fetches sha from manifests table
  → Compares manifests.sha256 against sha256 found in audit round content
  → Match = binding confirmed
  → Mismatch = audit is for a different file version — FAIL
```

This chain cannot be bypassed by extracting SHA from the audit round because the expected value always comes from an independent source (the manifests table written before the audit occurred).

---

## Rationale

ADR-040 requires artifact-to-audit binding. The only way to guarantee this non-circularly is an independent SHA registry written before the audit occurs. Extracting expected SHA from the audit round itself means the auditor can include any SHA and pass the check — this defeats the binding guarantee entirely.

SQLite in `cis_memory.db` (ADR-004) is the correct location. No new database or dependency is introduced.

---

## Impact on existing code

- `cis_verify.py`: `run_manifest()` gains a DB write step after PASS. `artifact_identity` block must include `builder_model_id`. Role separation check reads `builder_model_id` from the `manifests` table as the canonical source. `run_session_close_check()` and `check_dependencies_with_audit_status()` query `manifests` table for canonical SHA.
- `live_rounds` table: four new columns added via migration. Existing rows default to NULL — backward compatible.
- Dashboard (`cis_dashboard.html`): CIS Live round creation form needs `verdict`, `model_name`, `prompt`, `response` fields. This is a frontend task deferred to the next session after schema is live.
- `api/live.py`: round creation endpoint needs to accept and store the four new fields.

---

## Exit criteria

ADR-041 is implemented when:
- [ ] Migration script runs without error on `cis_memory.db`
- [ ] `cis_verify.py --manifest` writes a record to `manifests` table on PASS
- [ ] `cis_verify.py --session-close-check` reads SHA from `manifests` table
- [ ] `cis_verify.py --self-check` passes with synthetic registry tests
- [ ] Layer 3 audit of migration + cis_verify.py returns PASS from two independent auditor models (selected from the active model roster per ADR-040 — not restricted to specific external providers)

---

## Status: PROPOSED — pending Layer 3 audit before locking
