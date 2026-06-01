# ADR-048 — Staged Draft Intake Layer
# Status: LOCKED
# Created: 2026-05-04
# Depends on: ADR-043 (Execution Layer), ADR-044 (Operator Abstraction),
#             ADR-045 (Execution Queue Ownership), ADR-046 (Automation Reduction),
#             ADR-049 (Constitutional Memory Governance)
# Canonical path: /mnt/projects/cis/docs/ADRs/ADR-048_Staged_Draft_Intake_Layer.md

---

## 1. Problem

The human operator is currently the transport layer between AI-generated
structured content and canonical CIS records. This manifests as:

- Copy-pasting AI-generated session fields into dashboard forms
- Manually moving files from Downloads into runtime directories
- Bridging AI output to governance records by hand
- No quarantine zone between untrusted external artifacts and canonical state
- No structured classification of proposed content before human review
- No audit trail for what was proposed, by whom, and what happened to it

This is the "human is still the API" problem named in the constitutional
record. ADR-046 (Automation Reduction) requires that every significant
build action eliminate at least one manual operator action. ADR-048 is
the structural response to that requirement at the intake layer.

---

## 2. Decision

Introduce a Staged Draft Intake Layer between external artifact sources
and canonical CIS records.

This layer owns:
- classification of incoming artifacts by draft type
- quarantine of untrusted material before human review
- structured staging of AI-proposed content into the intake buffer
- human-gated promotion through trust zones
- provenance recording for all intake events
- filesystem watch automation for operator drop zones

This layer does NOT own:
- canonical record mutation (human-gated, separate commit step)
- verification of content correctness (ADR-033/034/040)
- execution scheduling (ADR-045)
- operator UI controls beyond the Draft Intake Panel (ADR-044)
- raw creative material ingestion (separate pipeline: /mnt/projects/cis/ingest/)

---

## 3. Trust Zone Model

Four trust zones define the intake pipeline. Material may only move
forward through zones, never backward, except via explicit rejection.

```
Downloads / External Sources  (untrusted)
        ↓
    inbox                     (quarantine — filesystem + DB)
        ↓
    staging                   (reviewed candidate — human promoted)
        ↓
    canonical                 (approved truth — human committed)
```

**Zone definitions:**

| Zone | Filesystem Path | DB zone value | Trust Level |
|---|---|---|---|
| Operator drop zone | /home/eric/Downloads/CIS_intake/ | — | untrusted |
| Inbox | /mnt/projects/cis/drafts/inbox/ | inbox | quarantine |
| Staging | /mnt/projects/cis/drafts/staging/ | staging | reviewed candidate |
| Canonical | DB / runtime files | canonical | approved truth |

**Zone transition rules:**
- Inbox → Staging: requires human Approve action in dashboard
- Staging → Canonical: requires human Commit action (Phase 3 scope)
- Any zone → Rejected: human Reject action; draft marked rejected in DB
- Any zone → Archived: human Archive action; draft removed from active view
- No zone transition may be automated without explicit human approval
- Backward zone movement is prohibited

---

## 4. Draft Types

Seven draft types are defined. No other type is legal.

| draft_type | Description |
|---|---|
| adr | Architectural Decision Record draft |
| session_field | Session open/close field block |
| conflict | Conflict register entry |
| primer_update | Primer file update draft |
| knowledge_record | Knowledge base record |
| manifest | Verification or processing manifest |
| config_patch | Runtime configuration change |

**Type inference rules (cis_download_watcher.py):**
- Filename contains "adr" → adr
- Filename contains "session" or "handoff" → session_field
- Filename contains "conflict" → conflict
- Filename contains "primer" or "_update_draft" → primer_update
- Filename contains "contract" → config_patch
- Filename contains "knowledge" or "record" → knowledge_record
- No match → file is skipped; not staged; operator must rename intentionally

---

## 5. Drafts Table Schema

```sql
CREATE TABLE IF NOT EXISTS drafts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_type          TEXT NOT NULL CHECK(draft_type IN (
                            'adr', 'knowledge_record', 'session_field',
                            'conflict', 'manifest', 'primer_update', 'config_patch'
                        )),
    payload_format      TEXT NOT NULL DEFAULT 'json' CHECK(payload_format IN (
                            'json', 'markdown', 'text', 'structured'
                        )),
    schema_version      TEXT NOT NULL DEFAULT '1.0',
    zone                TEXT NOT NULL DEFAULT 'inbox' CHECK(zone IN (
                            'downloads', 'inbox', 'staging', 'canonical'
                        )),
    status              TEXT NOT NULL DEFAULT 'inbox' CHECK(status IN (
                            'inbox', 'staged', 'pending_review',
                            'approved', 'rejected', 'committed',
                            'superseded', 'archived'
                        )),
    source_model        TEXT CHECK(source_model IN (
                            'claude', 'chatgpt', 'gemini', 'local', 'human'
                        )),
    source_session      TEXT,
    filename            TEXT,
    imported_by         TEXT,
    checksum            TEXT UNIQUE,
    payload             TEXT NOT NULL,
    proposed_target     TEXT,
    supersedes_id       INTEGER REFERENCES drafts(id),
    superseded_by       INTEGER REFERENCES drafts(id),
    approved_by         TEXT,
    approved_at         TEXT,
    rejected_by         TEXT,
    rejected_at         TEXT,
    rejection_reason    TEXT,
    committed_by        TEXT,
    committed_at        TEXT,
    commit_result       TEXT,
    canonical_record_id TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
```

**Constraints:**
- checksum is UNIQUE — identical content cannot be staged twice
- payload must be a non-empty string
- draft_type must be one of the seven defined types
- source_model must be one of the five defined values
- No rows may be deleted from drafts — use status transitions only
- updated_at must be set on every status change

---

## 6. Lifecycle Status Values

| Status | Meaning |
|---|---|
| inbox | Newly staged, in quarantine, awaiting human review |
| staged | Acknowledged by operator, moved to staging zone |
| pending_review | Flagged for explicit review before action |
| approved | Human approved, ready for commit |
| rejected | Human rejected, no further action |
| committed | Committed to canonical record |
| superseded | Replaced by a newer draft of the same content |
| archived | Removed from active view, retained for audit |

---

## 7. API Routes

```
POST /api/drafts/stage           — Stage an AI-proposed or operator-supplied draft
GET  /api/drafts/list            — List drafts (filterable by zone, status, type)
GET  /api/drafts/<id>            — Get a single draft record
POST /api/drafts/<id>/action     — Perform a lifecycle action on a draft
```

**Stage endpoint payload:**
```json
{
  "draft_type":     "session_field",
  "payload_format": "markdown",
  "schema_version": "1.0",
  "source_model":   "claude",
  "source_session": "optional session id",
  "filename":       "optional original filename",
  "payload":        "the proposed content as a string",
  "notes":          "optional provenance note"
}
```

**Action endpoint payload:**
```json
{
  "action":   "approve",
  "operator": "eric"
}
```

Valid actions: `approve`, `reject`, `archive`, `supersede`

---

## 8. Filesystem Watcher (cis_download_watcher.py)

The watcher automates the Downloads → inbox transport step.

**Behavior:**
- Watches /home/eric/Downloads/CIS_intake/ every 5 seconds
- On new file detection: moves file to /mnt/projects/cis/drafts/inbox/
- Infers draft_type from filename (Section 4 rules)
- If type cannot be inferred: file is skipped, logged, not moved
- Calls POST /api/drafts/stage with file content and inferred type
- On success: writes .cis_staged marker file in inbox
- On failure: writes .cis_stage_failed marker file; file retained in inbox
- Duplicate detection via SHA-256 checksum — identical files are skipped
- Runs as systemd service cis-watcher, auto-starts on boot

**Watcher scope:**
- Watched extensions: .md .txt .json .py .html .csv .yaml .yml
- Ignored: hidden files, directories, files with .cis_staged or .cis_stage_failed suffix
- Source model attribution: all watcher-staged files are attributed to 'human'

**Watcher does NOT:**
- Stage files to staging or canonical zones
- Approve any draft
- Modify any canonical record
- Watch any directory other than CIS_intake

---

## 9. Separation from Raw Ingest Pipeline

The draft intake layer and the raw creative material ingest pipeline
are separate systems. They must not be conflated.

| Dimension | Draft Intake (ADR-048) | Raw Ingest |
|---|---|---|
| Root path | /mnt/projects/cis/drafts/ | /mnt/projects/cis/ingest/ |
| Config constant | DRAFT_INBOX_DIR | INGEST_ROOT |
| Purpose | AI-proposed structured governance content | Raw creative source material |
| Content types | ADRs, session fields, primer updates, etc. | Scripts, audio, video, images, documents |
| Processing target | Canonical DB records and governance files | Knowledge records via extraction pipeline |
| Automation | cis_download_watcher.py | pipeline.py / cis_extract.py |

No file may be moved from the draft intake pipeline into the raw ingest
pipeline or vice versa without explicit operator action.

---

## 10. Prohibited Behaviors

The following behaviors are prohibited and constitute governance violations:

- Autonomous promotion of any draft beyond inbox without human approval
- Direct mutation of canonical DB records or files from the intake layer
- Deletion of any draft record from the drafts table
- Backward zone movement (staging → inbox, canonical → staging, etc.)
- Staging a draft with an unrecognized draft_type
- Use of the ingest/ pipeline for governance content
- Use of the drafts/ pipeline for raw creative material
- Bypassing checksum deduplication
- Watcher staging files to any zone other than inbox

---

## 11. Dashboard Integration

The Draft Intake Panel is the human approval surface for this layer.

Location: Right sidebar StreamDeck, below Operator panel
Component: DraftIntakePanel (React, cis_dashboard.html)

**Operator workflow:**
1. File appears in CIS_intake (operator places it or Claude generates it)
2. Watcher moves file to inbox and stages to DB automatically
3. Operator opens dashboard, clicks Refresh in Draft Intake Panel
4. Draft appears with type, source, zone, and timestamp
5. Operator selects draft and chooses Approve, Reject, or Archive
6. Approved drafts move to staging zone in DB
7. Commit step (Phase 3) promotes staging → canonical

**Known issue (conflict register):**
The rounds form session dropdown does not refresh after a new session
is opened without a browser refresh. LOW severity. DEFERRED.

---

## 12. Implementation Phases

### Phase 1 — Manual Draft Intake (COMPLETE)
- drafts table schema deployed to cis_memory.db
- /api/drafts/stage endpoint operational
- /api/drafts/list and /api/drafts/<id>/action routes operational
- DraftIntakePanel React component integrated into dashboard
- End-to-end governance flow verified: AI proposes → staged → human approves → zone promoted

### Phase 2 — Filesystem Watcher Automation (COMPLETE)
- cis_download_watcher.py deployed to /mnt/projects/cis/runtime/
- /home/eric/Downloads/CIS_intake/ established as operator drop zone
- /mnt/projects/cis/drafts/inbox/ and staging/ directories created
- config.py updated with DOWNLOADS_WATCH_DIR, DRAFT_INBOX_DIR, DRAFT_STAGING_DIR
- cis-watcher.service deployed as systemd unit, enabled on boot
- End-to-end verified: file dropped → auto-moved → API staged → DB record → dashboard visible

### Phase 3 — Commit Layer (NOT YET BUILT)
- /api/drafts/<id>/commit endpoint
- Type-specific commit handlers per draft_type
- Canonical record mutation from approved staging drafts
- Commit provenance recording

---

## 13. Governance Boundary

The intake layer stages and presents. It does not decide.

- ADR-043 remains authoritative execution law
- ADR-033/034/040 remain authoritative verification requirements
- ADR-046 requires automation reduction — intake automation satisfies this requirement
- ADR-049 governs primer file mutation — primer_update drafts must pass through
  the ADR-049 governed update cycle before canonical promotion
- No intake action may bypass a human approval gate
- No intake action may bypass verification requirements on canonical mutation

---

## 14. What This Does Not Solve

- Commit layer (Phase 3 — future session)
- Type-specific commit handlers per draft_type
- Automated L1/L2 verification of draft content before staging
- Multi-file draft batching
- Draft versioning beyond supersession
- Visual orchestration and build navigation (future ADR — build plan rewrite)
- Unified intake routing between draft intake and raw ingest pipelines (future ADR)
- Governed state registry and drift detection (future ADR — build plan rewrite)

---

## LOCKED
