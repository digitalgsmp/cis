# Post-Scrape Intention Alignment Pipeline — Specification

**Document:** SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE.md
**Version:** 1.0.0
**Date:** 2026-06-26
**Author:** V4 Drafter (hermes-v4pro:8645)
**Status:** PROPOSAL_READY — pending adversarial review
**Pipeline:** run-9ed3912fdc3b — Direct Directive Mode (no spine run_id)
**Eric's Request:** June 26, 2026 Telegram session

---

## 1. Objective

Define the end-to-end specification for extracting Eric's verbatim intentions from the full 3,071-file corpus, presenting them for his batch review and confirmation, and ingesting confirmed intentions into a hybrid knowledge base (SQLite fast DB + Chroma VDB) that every pipeline stage measures against — so Drafter proposals, Reviewer challenges, and Implementer actions all align with what Eric actually stated, not what a model guesses.

---

## 2. Architecture Overview

```
PHASE A: SCRAPE ──────────────────────────────────────────────────────────
  Stage A1: File Discovery        → Inventory all 3,071 source files
  Stage A2: Three-Model Tagging   → Claude Opus + DeepSeek V4 Pro + GLM 5.2
                                    independently tag every file using
                                    TAGGING_DIRECTIVE_v3.1.md
  Stage A3: Review Stage A        → R1 (8643) + Prime (8642) audit tags
                                    for VOICE accuracy, blind spots

PHASE B: EXTRACT ─────────────────────────────────────────────────────────
  Stage B1: Drafter Synthesizes   → 5 deliverables from reconciled tags
  Stage B2: Review Stage B        → Two reviewers audit deliverables
  Stage B3: Extract Intention
            Records               → Individual intention items extracted
                                    with full provenance, verbatim text,
                                    categorization, and confidence score

PHASE C: CONFIRM ─────────────────────────────────────────────────────────
  Stage C1: Batch Review Surface  → Portal panel: every intention item
                                    listed with verbatim restatement,
                                    layer/component mapping, domain, score
  Stage C2: Eric Batch Review     → Eric checks APPROVE / REJECT / REVISE
                                    per item, optionally adds comment
  Stage C3: Revised Items Feed    → REVISED items re-presented for
            Back                   confirmation; REJECTED items discarded

PHASE D: INGEST ──────────────────────────────────────────────────────────
  Stage D1: SQLite Ingestion      → confirmed intentions → intent_records
                                    table with full provenance
  Stage D2: VDB Embedding         → verbatim fragments → ChromaDB
                                    collection intent_memory (semantic)
                                    + anti_patterns (fuzzy match)
  Stage D3: Hybrid Query Layer    → API endpoints: exact SQL + fuzzy VDB
                                    search against validated intentions

PHASE E: WIRE ────────────────────────────────────────────────────────────
  Stage E1: Drafter Query         → intent_map lookup before drafting
  Stage E2: Reviewer Measure      → proposal vs. eric-verbatim diff
  Stage E3: Implementer Validate  → artifact vs. functional_spec
  Stage E4: Eric Gate Evidence    → full trail: you said X, we built Y
```

---

## 3. Requested Outputs — Detailed Specification

### 3.1 Extraction Format / Schema — Intention Record

An intention record is the output of Phase B Stage B3. It is produced by the Drafter from reconciled multi-model tags and becomes the unit of Eric's batch review.

```json
{
  "record_id": "int-<12_hex>",
  "source": {
    "file_path": "/home/eric/.hermes-v4pro/sessions/session_20260520_215551_16187f.json",
    "message_index": 14,
    "speaker": "user",
    "timestamp": "2026-05-20T21:55:51Z"
  },
  "verbatim_text": "I don't want summaries, I am trying to build a system that works from the raw files.",
  "tagging": {
    "voice": "eric-verbatim",
    "categories": ["eric-intention", "intent-scrape", "shared-memory"],
    "build_target": "cross-cutting",
    "functionality": ["intent-memory reference standard", "raw-evidence pipeline"],
    "failure_flag": null,
    "wiasw_origin": false,
    "reviewer_measurement": true
  },
  "intent_statement": "Eric wants CIS to work from raw source files, not model summaries.",
  "domain": "intent-scrape",
  "layer_mapping": {
    "application_part": "cross-cutting",
    "component": "intent-memory reference standard",
    "build_tier": "Post-Scrape Intention Alignment"
  },
  "confidence": {
    "score": 0.95,
    "model_agreement": 3,
    "models": ["claude-opus-4.8", "deepseek-v4-pro", "glm-5.2"],
    "disagreement_note": null
  },
  "review_state": "pending",
  "eric_decision": null,
  "eric_comment": null,
  "extracted_at": "2026-06-26T12:00:00Z"
}
```

**Field definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Unique identifier, `int-` prefix + 12 hex chars |
| `source.file_path` | string | Absolute path to the source file |
| `source.message_index` | int | 0-based position within the source file's messages |
| `source.speaker` | string | `user`, `assistant`, `tool`, `system` |
| `source.timestamp` | ISO 8601 | When the message was recorded |
| `verbatim_text` | string | Eric's or the model's exact words, unedited |
| `tagging.voice` | enum | `eric-verbatim`, `model-interpretation`, `technical-spec`, `governance` |
| `tagging.categories` | array | From TAGGING_DIRECTIVE_v3.1 category list |
| `tagging.build_target` | enum | `control-plane`, `abstraction-layer`, `hermes-backend`, `pipeline`, `cross-cutting`, `reviewer-measurement` |
| `tagging.functionality` | array | Specific components informed, e.g. `["panel model dropdown", "dispatch router"]` |
| `tagging.failure_flag` | string? | CIS failure mode if present, or null |
| `tagging.wiasw_origin` | bool | Whether this traces to the WIASW analog framework |
| `tagging.reviewer_measurement` | bool | Whether this informs the Reviewer Measurement Brief |
| `intent_statement` | string | ONE sentence: what Eric is asking for (for eric-verbatim); or "n/a" for model content |
| `domain` | string | Primary domain, from category that best describes this record |
| `layer_mapping.application_part` | enum | Which of the 3 application parts this maps to |
| `layer_mapping.component` | string | The specific component within that part |
| `layer_mapping.build_tier` | string | Which CIS build tier this informs |
| `confidence.score` | float | 0.0–1.0 agreement across models on this record |
| `confidence.model_agreement` | int | How many of the 3 models independently tagged this similarly |
| `confidence.models` | array | Which models tagged this |
| `confidence.disagreement_note` | string? | If models disagreed on category/build_target, note here |
| `review_state` | enum | `pending`, `approved`, `rejected`, `revised` |
| `eric_decision` | string? | Eric's decision when reviewed |
| `eric_comment` | string? | Eric's revision comment if revised |
| `extracted_at` | ISO 8601 | When this record was extracted |

### 3.2 Tagging Taxonomy

The taxonomy is defined by TAGGING_DIRECTIVE_v3.1.md (already written, proven on 3+ documents). No new taxonomy is needed. The spec references the directive as the authoritative source.

**VOICE (primary sort):**
- `eric-verbatim` — Eric's actual words. Feeds Intent Map.
- `model-interpretation` — Model trying to understand Eric. Feeds Anti-Pattern Register when drift detected.
- `technical-spec` — Architecture, build plans, code docs. Measured against eric-verbatim.
- `governance` — ADRs, decisions, rules. Feeds guardrail mechanisms.

**CATEGORIES (20 predefined + model-discovered):**
See TAGGING_DIRECTIVE_v3.1.md §CATEGORIES for the full list. Key: control-plane, enforcement, pipeline, intent-scrape, intent-inference, shared-memory, agent-roles, lane-cis-product, lane-cis-project, eric-intention, failure-pattern, enterprise-friction, decision, open-question, wiasw-origin, guardrail-mechanism, verification-method, profile-character, reviewer-duties, measurement-criteria, reviewer-brief.

**BUILD TARGET:**
- `control-plane` — Portal, panels, chat, Flask endpoints
- `abstraction-layer` — Dispatch boundary, routing, trigger
- `hermes-backend` — Enforced container, pipeline execution
- `pipeline` — Multi-stage deliberation mechanics
- `cross-cutting` — Applies across multiple parts
- `reviewer-measurement` — What reviewers measure against

**FAILURE FLAGS:**
false-proof, shell-surface, amnesia-trigger, enterprise-default, self-attestation, scope-creep, blind-routing, sequential-build-violation

**Category-to-Layer Mapping:**
See enforcement/CATEGORY_TO_LAYER_MAP.md for the authoritative mapping of every category to the three application parts.

### 3.3 Eric Review Workflow — Batch Review Surface

Eric explicitly rejected per-item sequential dialog. He wants a batch review surface — a form list, checklist, or portal panel where he can review all extracted intentions at once and mark each as APPROVE, REJECT, or REVISE (with optional comment).

**Workflow:**

1. Drafter finishes Phase B Stage B3 extraction → produces a JSON file containing all intention records at `/mnt/projects/cis/data/extraction/intent_records_batch_<date>.json`

2. Portal reads this file and renders the **Intent Review Panel** — a new React page at `/intent-review` within the existing CIS UI (port 5000)

3. Each row in the panel shows:
   - Checkbox for select (for batch actions)
   - Verbatim text excerpt (truncated to ~120 chars, expandable)
   - "I understand your intention as: [model's intent_statement]"
   - "This maps to: [application_part] > [component] at [build_tier]"
   - Domain + categories as tag chips
   - Confidence score as a colored badge (green ≥0.9, yellow ≥0.7, red <0.7)
   - Three action buttons: APPROVE / REJECT / REVISE
   - Comment field (appears when REVISE is clicked)

4. Batch operations:
   - "Approve All High Confidence" (score ≥0.9) — one-click
   - "Select All" / "Deselect All"
   - "Apply Decision to Selected" — bulk APPROVE/REJECT

5. On submission:
   - POST to `/api/intent-review/submit` with array of `{record_id, decision, comment}`
   - Backend writes `intent_confirmations` rows
   - Approved records are queued for SQLite + VDB ingestion
   - Rejected records are discarded (write decision_trails row)
   - Revised records are flagged for re-presentation after comment resolution

6. Revised items:
   - If Eric writes a revision comment, the record goes to `review_state=revised`
   - Drafter incorporates the comment and re-extracts, producing a new version
   - Revised records appear in a separate "Revised — Awaiting Re-review" section at the top of the next review batch
   - Eric re-confirms each revised item

**Delivery mechanism recommendation:** React portal panel within existing CIS UI. See §3.6.

### 3.4 Hybrid Knowledge Base Schema

#### 3.4.1 SQLite Tables (fast DB at `/mnt/projects/cis/data/cis_memory.db`)

```sql
-- Core intention records (one per extracted intention)
CREATE TABLE intent_records (
    id              TEXT PRIMARY KEY,          -- int-<12_hex>
    source_path     TEXT NOT NULL,             -- absolute file path
    source_line     INTEGER,                   -- message index in source
    speaker_role    TEXT NOT NULL,             -- user, assistant, tool, system
    source_ts       TEXT,                      -- ISO timestamp
    verbatim_text   TEXT NOT NULL,             -- exact words, unedited
    voice           TEXT NOT NULL CHECK (voice IN
                    ('eric-verbatim', 'model-interpretation', 'technical-spec', 'governance')),
    categories_json TEXT NOT NULL,             -- JSON array of category strings
    build_target    TEXT NOT NULL CHECK (build_target IN
                    ('control-plane', 'abstraction-layer', 'hermes-backend', 'pipeline', 'cross-cutting', 'reviewer-measurement')),
    functionality_json TEXT,                   -- JSON array of specific components
    intent_statement TEXT,                     -- ONE sentence: what Eric is asking for
    failure_flag    TEXT,                      -- CIS failure mode if present, or NULL
    domain          TEXT NOT NULL,             -- primary category domain
    layer_component TEXT,                      -- mapped component name
    build_tier      TEXT,                      -- which build tier this informs
    confidence_score REAL NOT NULL,            -- 0.0-1.0
    model_agreement INTEGER NOT NULL,          -- 1-3
    models_json     TEXT NOT NULL,             -- JSON array of model names
    disagreement_note TEXT,                    -- if models disagreed
    wiasw_origin    INTEGER NOT NULL DEFAULT 0,-- boolean
    reviewer_measurement INTEGER NOT NULL DEFAULT 0, -- boolean
    extracted_at    TEXT NOT NULL,             -- ISO timestamp
    extraction_run  TEXT NOT NULL              -- batch identifier
);

-- Eric's confirmation decisions per record
CREATE TABLE intent_confirmations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT NOT NULL REFERENCES intent_records(id),
    decision        TEXT NOT NULL CHECK (decision IN ('APPROVE', 'REJECT', 'REVISE')),
    comment         TEXT,                      -- Eric's revision comment
    decided_at      TEXT NOT NULL,             -- ISO timestamp
    source          TEXT NOT NULL DEFAULT 'portal'  -- portal, telegram, manual
);

-- Anti-pattern register (built from FAILURE_FLAG entries)
CREATE TABLE anti_patterns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       TEXT REFERENCES intent_records(id),
    failure_mode    TEXT NOT NULL,             -- one of the 8 FAILURE FLAGS
    pattern_text    TEXT NOT NULL,             -- what the model did
    eric_intent     TEXT NOT NULL,             -- what Eric actually asked for
    guardrail       TEXT NOT NULL,             -- what guardrail prevents this
    evidence_source TEXT NOT NULL,             -- source file path
    extracted_at    TEXT NOT NULL
);

-- Reviewer measurement brief (deliverable 5)
CREATE TABLE reviewer_brief (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    section         TEXT NOT NULL,             -- 1-7 per directive v3.1 §WHAT REVIEWERS MEASURE AGAINST
    section_label   TEXT NOT NULL,             -- e.g. "Eric's role", "Two lanes"
    content         TEXT NOT NULL,             -- synthesized from reviewer-measurement tagged blocks
    source_records  TEXT NOT NULL,             -- JSON array of record_ids
    extracted_at    TEXT NOT NULL
);

-- Functional specification by layer
CREATE TABLE functional_spec (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    application_part TEXT NOT NULL CHECK (application_part IN
                    ('control-plane', 'abstraction-layer', 'hermes-backend')),
    component       TEXT NOT NULL,             -- specific component name
    description     TEXT NOT NULL,             -- what this component does
    requirements_json TEXT NOT NULL,           -- JSON array of requirement strings
    wiasw_origin    INTEGER NOT NULL DEFAULT 0,
    source_records  TEXT NOT NULL,             -- JSON array of record_ids
    extracted_at    TEXT NOT NULL
);

-- Indexes for fast pipeline queries
CREATE INDEX idx_intent_records_domain ON intent_records(domain);
CREATE INDEX idx_intent_records_voice ON intent_records(voice);
CREATE INDEX idx_intent_records_build_target ON intent_records(build_target);
CREATE INDEX idx_intent_records_confidence ON intent_records(confidence_score DESC);
CREATE INDEX idx_intent_confirmations_record ON intent_confirmations(record_id);
CREATE INDEX idx_intent_confirmations_decision ON intent_confirmations(decision);
CREATE INDEX idx_anti_patterns_failure ON anti_patterns(failure_mode);
CREATE INDEX idx_functional_spec_part ON functional_spec(application_part);
```

#### 3.4.2 Chroma VDB (at `/mnt/projects/cis/data/chroma_data/`)

Two collections managed by the existing ChromaDB instance (Tier 9 COMPLETE):

**Collection: `intent_memory`**
- Documents: Eric-verbatim text fragments (max 500 chars each)
- Metadata per document: `{record_id, domain, build_target, layer_component, confidence_score, source_path, timestamp}`
- Embedding model: all-MiniLM-L6-v2 (default, already installed)
- Query pattern: "Find Eric's intentions similar to `<current proposal draft>`"
- Use: Semantic similarity search — does this proposal align with something Eric actually asked for?

**Collection: `anti_patterns`**
- Documents: Anti-pattern descriptions (failure mode + pattern text + eric_intent)
- Metadata per document: `{record_id, failure_mode, guardrail}`
- Query pattern: "Does this proposal match any known failure pattern?"
- Use: Fuzzy similarity matching against historical enterprise-default drift

#### 3.4.3 Hybrid Query Pattern

```python
def measure_proposal_against_intent(proposal_text: str) -> dict:
    """
    Pipeline function called by Drafter, Reviewer, and Implementer.
    Returns: exact SQL matches + fuzzy VDB matches.
    """
    # Exact matches: SQLite FTS5 on verbatim_text
    exact = sqlite_query("""
        SELECT id, verbatim_text, intent_statement, domain, confidence_score
        FROM intent_records
        WHERE voice = 'eric-verbatim'
          AND verbatim_text MATCH ?
        ORDER BY confidence_score DESC
        LIMIT 10
    """, proposal_text)

    # Fuzzy matches: ChromaDB semantic search
    fuzzy = chroma_collection("intent_memory").query(
        query_texts=[proposal_text],
        n_results=10
    )

    # Anti-pattern check
    patterns = chroma_collection("anti_patterns").query(
        query_texts=[proposal_text],
        n_results=5
    )

    return {"exact": exact, "fuzzy": fuzzy, "anti_patterns": patterns}
```

### 3.5 Pipeline Integration

#### 3.5.1 Drafter Stage (8645)

Before drafting any proposal, the Drafter queries intent memory:

```
QUERY: "SELECT intent_statement, layer_component, build_tier
        FROM intent_records WHERE voice='eric-verbatim'
        AND confidence_score >= 0.7"
→ Returns: list of Eric's confirmed intentions, mapped to components.

QUERY: ChromaDB intent_memory.query(query_texts=[draft_topic])
→ Returns: semantically similar Eric intentions to the draft topic.
```

Output requirement: Every Drafter proposal must include an "Intent Alignment" section listing which Eric intentions the proposal addresses, with record IDs. The Reviewer then measures the proposal against those exact intentions.

#### 3.5.2 Reviewer Stage (8643)

The Reviewer measures each proposal against:

1. The Reviewer Measurement Brief (from reviewer_brief table) — Eric's core intentions, profile duties, two-lane model, confirmation gate, 7-stage sequence
2. The Anti-Pattern Register — is this proposal repeating a known failure pattern?
3. The verbatim intentions the Drafter claimed to address

Reviewer output format: For each objection, cite the specific Eric intention (record_id + verbatim text) that contradicts the proposal.

#### 3.5.3 Implementer Stage (8646)

Before building, the Implementer queries:

```
QUERY: functional_spec WHERE application_part=<target> AND component=<target>
→ Returns: what this component must do, per Eric's confirmed intentions.

QUERY: anti_patterns WHERE failure_mode IN ('self-attestation', 'scope-creep', 'sequential-build-violation')
→ Returns: guardrails to enforce.
```

Output requirement: Every Implementer completion must include a verification section showing the artifact matches the functional_spec requirements.

#### 3.5.4 Eric Gate

The Eric Gate approval panel shows the full evidence trail:

```
Eric said:      [verbatim_text] (source: file, line, timestamp)
Drafter proposed: [proposal summary] aligned with [record_ids]
Reviewer flagged: [objections if any]
Implementer built: [artifact evidence]
```

#### 3.5.5 API Endpoints (New)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/intent/records?domain=X&confidence_min=0.7` | Query intention records |
| GET | `/api/intent/record/<id>` | Single record with full provenance |
| GET | `/api/intent/review/batch/<batch_id>` | Get batch for Eric review panel |
| POST | `/api/intent/review/submit` | Submit Eric's batch decisions |
| GET | `/api/intent/search?q=<text>` | Hybrid search (SQL + VDB) |
| GET | `/api/intent/anti-patterns?mode=<failure_mode>` | Query anti-pattern register |
| GET | `/api/intent/functional-spec?part=<application_part>` | Query functional spec |
| GET | `/api/intent/reviewer-brief` | Get Reviewer Measurement Brief |
| GET | `/api/intent/alignment?proposal=<text>` | Measure proposal against intent (returns exact + fuzzy + anti-pattern matches) |

Implementation: New Flask blueprint `intent_bp` in `runtime/api/intent.py`, registered in `runtime/app.py`.

### 3.6 Delivery Mechanism for Batch Review Surface

**Recommendation: React portal panel within the existing CIS UI.**

Rationale:
- Eric explicitly listed "portal panel" as an option in his requirements
- The CIS portal at `http://127.0.0.1:5000` already serves a React app with 25+ pages via Flask
- A new page `IntentReviewPage.jsx` routes to `/intent-review`, served by the existing Vite build
- Zero new infrastructure — same Flask app, same React app, same port
- The existing pages (PipelinePage, EricGatePage, ReviewQueue) establish the pattern: read-only query panels with action buttons
- Checklist file (.md) is inferior: no filtering, no batch operations, no sorting by confidence, requires Eric to manually edit a file

**Alternative (rejected):** Flat markdown checklist file.
- Eric would have to edit a markdown file manually
- No filtering by confidence score, domain, or category
- No batch approve/reject
- No structured output for automated ingestion

**Implementation:**
1. New React component: `runtime/ui/src/pages/IntentReviewPage.jsx`
2. New API blueprint: `runtime/api/intent.py` (endpoints listed in §3.5.5)
3. Flask route registration in `runtime/app.py`
4. Vite route in `runtime/ui/src/App.jsx`

The component renders:
- Summary bar: "X of Y items reviewed, Z approved, W rejected, V revised"
- Filter bar: by domain, confidence range, voice, build target
- Batch action bar: "Approve All High Confidence", "Select All / Deselect All"
- Item rows: verbatim excerpt + model understanding + layer mapping + confidence badge + action buttons
- Submit button: POST to `/api/intent/review/submit`

---

## 4. AGENTS.md 'Do Not Start' Override

Per Eric's directive (June 26, 2026 Telegram session), the following AGENTS.md entries are OVERRIDDEN for this work:

| Blocked Item | Reason Override Applies |
|---|---|
| VDB pipeline rebuild | Intention alignment REQUIRES VDB for semantic search; the existing ChromaDB instance (Tier 9) is operational and will be extended, not rebuilt |
| Unified memory build | The hybrid KB schema in §3.4 is a new set of tables + collections, not a unified memory build — it's scoped to intention records only |

What remains blocked (NOT overridden):
- Pass 5 implementation (project promotion, schema migration)
- Wiring V4-Pro through NeMo
- Briefing Center UI redesign
- Notes/Open Items database implementation
- Discord/Telegram gateway
- Schedule field-use work (SWA)
- CIS Foundation Build Plan Phases 1-3
- Snapshot trigger work (CIS-INFRA-STORAGE-002)

---

## 5. Build Order — Phased Implementation

### Phase A: Scrape (prerequisite: none, partially proven)

| Stage | Description | Deliverable |
|-------|-------------|-------------|
| A1 | Run full file discovery across all 3,071 sources | Inventory JSON |
| A2 | Execute three-model tagging on all files using TAGGING_DIRECTIVE_v3.1.md | `enforcement/mwl-proof-v2/tagging_results/` (all files) |
| A3 | Run Review Stage A (R1:8643 + Prime:8642) on all tagged output | Review A audit report |

**Already proven:** Stages A2 and A3 demonstrated on 3-4 test documents (June 25-26).

### Phase B: Extract (prerequisite: Phase A complete)

| Stage | Description | Deliverable |
|-------|-------------|-------------|
| B1 | Drafter synthesizes 5 deliverables from reconciled tags | 5 deliverable documents in `docs/` |
| B2 | Review Stage B on deliverables | Review B audit report |
| B3 | Extract individual intention records (JSON) | `data/extraction/intent_records_batch_<date>.json` |

### Phase C: Confirm (prerequisite: Phase B complete)

| Stage | Description | Deliverable |
|-------|-------------|-------------|
| C1 | Build IntentReviewPage.jsx + intent_bp Flask blueprint | `/intent-review` panel |
| C2 | Eric reviews batch via portal | Approved/rejected/revised decisions |
| C3 | Handle revised items, re-present for confirmation | Revised item re-review |

### Phase D: Ingest (prerequisite: Phase C approved records exist)

| Stage | Description | Deliverable |
|-------|-------------|-------------|
| D1 | Create SQLite tables (§3.4.1) + import confirmed records | `intent_records` table populated |
| D2 | Embed verbatim fragments into ChromaDB collections | `intent_memory` + `anti_patterns` collections populated |
| D3 | Test hybrid queries (exact SQL + fuzzy VDB) | Verified query results |

### Phase E: Wire (prerequisite: Phase D complete)

| Stage | Description | Deliverable |
|-------|-------------|-------------|
| E1 | Drafter queries intent memory before drafting | Pipeline integration verified |
| E2 | Reviewer measures against intent | Reviewer workflow updated |
| E3 | Implementer validates against functional spec | Implementer workflow updated |
| E4 | Eric Gate shows evidence trail | Gate panel updated |

---

## 6. Acceptance Criteria

### AC-1: Full Corpus Coverage
ALL 3,071 available files are tagged by at least 2 of 3 models. Coverage report shows file count, tagged count, and any files that failed (with reason).

### AC-2: Multi-Model Agreement
Each intention record shows confidence score computed from 2-3 model agreement. Records with score <0.5 are flagged for manual review.

### AC-3: Batch Review Surface
The `/intent-review` portal panel renders all extracted intention records. Eric can filter, sort (by confidence, domain, date), bulk-select, and submit APPROVE/REJECT/REVISE decisions for all items.

### AC-4: Confirmation Gate
Only APPROVED records progress to SQLite + VDB ingestion. REJECTED records are discarded with a decision_trails entry. REVISED records block ingestion until re-confirmed.

### AC-5: Hybrid Knowledge Base
SQLite intent_records table contains all confirmed records with full provenance. ChromaDB intent_memory collection supports semantic search. ChromaDB anti_patterns collection supports fuzzy failure-pattern matching.

### AC-6: Pipeline Integration
The `/api/intent/alignment` endpoint returns exact SQL matches + fuzzy VDB matches + anti-pattern flags. Every pipeline stage (Drafter, Reviewer, Implementer) can query this before acting.

### AC-7: Evidence Trail
The Eric Gate approval panel shows: Eric's verbatim words → Drafter's proposal → Reviewer's challenges → Implementer's artifact → verification evidence.

---

## 7. Risks and Unknowns

| # | Risk | Mitigation |
|---|------|------------|
| R1 | 3,071 files × 3 models = ~9,213 tagging runs. At ~30s each, that's ~77 hours of compute. Claude Opus costs ~$15/M tokens — tagging the full corpus could cost $200-500+. | Phase by phase. Start with 50-file batch to validate pipeline end-to-end. Scale to full corpus after Eric confirms the pipeline works. Use DeepSeek/GLM for the bulk (cheaper); Claude for critical/ambiguous files. |
| R2 | Tagging quality degrades with file size — very large session files (1.8MB+) may produce noisy tags. | The TAGGING_DIRECTIVE_v3.1 says "Group every 5-15 lines into a tagged block." Large files should be chunked into manageable segments before tagging. |
| R3 | The ChromaDB instance at `/mnt/projects/cis/data/chroma_data/` is nearly empty (188KB). Embedding 3,071 files' worth of verbatim fragments could produce a multi-GB database. | Embed only eric-verbatim fragments, not full documents. A typical session file has ~10-20 eric-verbatim messages at ~100 chars each = ~2KB per file. 3,071 files × 2KB = ~6MB of text → manageable. |
| R4 | Eric's batch review may be overwhelming if 3,071 files produce thousands of intention records. | Filtering by confidence score reduces the volume. High-confidence records can be bulk-approved. Only low-confidence and ambiguous records need individual attention. |
| R5 | This spec assumes the tagging pipeline can scale to 3,071 files. The tagging has only been proven on 3-4 test documents. | Phase A should include a 50-file scalability test before committing to full corpus. |
| R6 | The IntentReviewPage is a new React component in an existing app — existing build pipeline, routing, and API patterns must be followed. | Build from existing patterns: PipelinePage, EricGatePage, ReviewQueue. No new framework, no new dependencies. |

---

## 8. Verification Plan

### V1: Tagging Coverage
```bash
# After Phase A: count tagged files
ls enforcement/mwl-proof-v2/tagging_results/ | wc -l
# Expected: ≥ 3,071 tagged files (one per source)
```

### V2: Extraction Completeness
```bash
# After Phase B3: count extracted records
python3 -c "import json; data=json.load(open('data/extraction/intent_records_batch_<date>.json')); print(len(data))"
# Expected: thousands of records with all required fields
```

### V3: Batch Review Surface
```bash
curl -s http://127.0.0.1:5000/api/intent/review/batch/<batch_id> | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['records']))"
# Expected: records returned, each with verbatim_text, intent_statement, layer_mapping
```

### V4: SQLite Ingestion
```bash
sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM intent_records WHERE review_state='approved'"
sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM intent_confirmations WHERE decision='APPROVE'"
# Expected: matching counts, both > 0
```

### V5: ChromaDB Ingestion
```python
# After Phase D2: verify collections exist and have documents
import chromadb
client = chromadb.PersistentClient(path="/mnt/projects/cis/data/chroma_data")
collection = client.get_collection("intent_memory")
print(f"Documents: {collection.count()}")
# Expected: count > 0
```

### V6: Hybrid Query
```python
# Test exact + fuzzy search
curl -s "http://127.0.0.1:5000/api/intent/alignment?proposal=build+dark+mode+toggle" | python3 -m json.tool
# Expected: {"exact": [...], "fuzzy": [...], "anti_patterns": [...]}
```

---

## 9. References

| Document | Path | Purpose |
|----------|------|---------|
| Tagging directive v3.1 | `enforcement/TAGGING_DIRECTIVE_v3.md` | Tagging taxonomy and format |
| Category-to-layer map | `enforcement/CATEGORY_TO_LAYER_MAP.md` | Category → application part mapping |
| Intent recovery pipeline | `cis-drafter-workflow` skill, `references/intent-recovery-pipeline.md` | End-to-end pipeline overview |
| Session handoff 2026-06-25 | `docs/SESSION_HANDOFF_2026-06-25.md` | Current pipeline state and next actions |
| Corpus audit | `docs/audits/corpus_audit_2026-06-08.md` | 3,105 files catalogued, 3,071 importable |
| MWL proof reproduction | `docs/MWL_PROOF_REPRODUCTION.md` | Enforcement container proof |
| CIS 16 failure modes | `docs/CIS_16_FAILURE_MODES.md` | What guardrails prevent |
| Build plan v2 | `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` | Build order authority |
| Tagging results | `enforcement/mwl-proof-v2/tagging_results/` | Proven 3-model tagging on 3-4 docs |
| Anthropic export | `docs/Anthropic_Data_Export_260625/conversations.json` | 138 Claude conversations |

---

## 10. Next Actions

1. This spec → Review Stage A: dispatch to r1 (hermes-r1:8643) for adversarial review
2. r1 review → Review Stage B: dispatch to Prime (hermes-prime:8642) for blind-spot catch
3. Revised spec → Eric Gate approval
4. Approved → Implementer (8646) builds Phase A Stage A1 (file discovery) → scales to A2 (tagging)

---

## 11. FINAL_JSON

```json
{
  "role": "drafter",
  "status": "PROPOSAL_READY",
  "summary": "Post-Scrape Intention Alignment Pipeline specification defining 5 phases (Scrape → Extract → Confirm → Ingest → Wire) across 15 stages. Covers: extraction record schema with full provenance, tagging taxonomy referencing TAGGING_DIRECTIVE_v3.1, Eric batch review via React portal panel, hybrid KB schema (SQLite intent_records + ChromaDB intent_memory/anti_patterns collections), pipeline integration API endpoints for Drafter/Reviewer/Implementer/Eric Gate, and a phased build order with acceptance criteria and verification plan.",
  "recommendation": "Proceed to adversarial review (r1:8643 first, then Prime:8642 for blind-spot catch). Before full corpus execution, run a 50-file scalability test to validate the tagging pipeline at scale. The batch review portal panel should be built against the existing CIS UI patterns (React + Flask, same port 5000, following PipelinePage/ReviewQueue patterns).",
  "next_action": "REVIEW_PENDING"
}
```
