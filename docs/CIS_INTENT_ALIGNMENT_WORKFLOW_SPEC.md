# CIS Intent Alignment — End-to-End Workflow Specification

**Author:** Hermes V4 Drafter (deepseek-v4-pro)  
**Date:** 2026-06-26  
**Status:** DRAFT — awaiting Eric Gate  
**HERMES_HOME:** /home/eric/.hermes-v4pro  
**Source:** Eric directive via Telegram CIS_Test_Group, 2026-06-26

---

## Purpose

Build the measurement tool that lets the CIS pipeline validate every stage against Eric's actual intentions. Close the gap between the 5-deliverable scrape output and a runtime queryable hybrid memory system (SQLite fast DB + Chroma VDB).

---

## 1. Source Corpus

### 1.1 Session Files (Priority 1 — Eric's verbatim words)

| Profile | Files | Size | Sessions |
|---------|-------|------|----------|
| prime (~/.hermes/sessions) | 4 jsonl | 409 MB | 332 |
| r1 (~/.hermes-r1/sessions) | 3 jsonl | 113 MB | 468 |
| v4pro (~/.hermes-v4pro/sessions) | 5 jsonl | 56 MB | 619 |
| v4impl (~/.hermes-v4impl/sessions) | 5 jsonl | 242 MB | 225 |

Plus Anthropic export: 1 JSON file, 68 MB, 138 Claude conversations.

**Pre-processing required:** Session JSONL files contain full serialized conversation objects per line. Before tagging, each session must be parsed to extract `role: "user"` messages with timestamps. Only user messages proceed to the tagger. Model responses are skipped for intent extraction but preserved for anti-pattern analysis.

### 1.2 CIS Project Documents (Priority 2)

~620 taggable files from `/mnt/projects/cis/docs/`:
- 450 .md files (architecture, specs, build plans, pivot docs, ADRs)
- 150 .docx files (Word documents)
- 22 .txt files (vision statements, conversation transcripts)

### 1.3 WIASW Archive (Priority 3)

21 files, 4.2 MB at `/mnt/archive/WIAS/`:
- 7 .xlsx spreadsheets (extract all cell values)
- 5 .md, 5 .html, 1 .txt

### 1.4 General Archive (Priority 4)

`/mnt/archive/` — deferred. Too large for initial pass. Assess after P1-P3 complete.

### What is NOT tagged

Code files (.py, .js, .jsx, .sh), databases (.db), images (.png, .jpg), and build artifacts. These contain infrastructure, not intent.

---

## 2. Pipeline Stages

```
                    ┌─────────────────────────┐
                    │  PRE-PROCESS SESSIONS    │
                    │  Extract user messages   │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 1: TAG             │
                    │  3 models independently  │
                    │  Directive v3.1          │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 2: REVIEW STAGE A  │
                    │  R1 + Qwen audit tags    │
                    │  VOICE accuracy,         │
                    │  category consistency    │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 3: DRAFTER         │
                    │  Synthesize reconciled   │
                    │  tags into 5 deliverables│
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 4: REVIEW STAGE B  │
                    │  Audit draft deliverables│
                    │  against intent          │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 5: GENERATE        │
                    │  REVIEW FORM             │
                    │  Extract intention items │
                    │  into batch review JSON  │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 6: ERIC GATE       │
                    │  Batch review form in    │
                    │  portal — Confirm/Reject/│
                    │  Revise each intention   │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 7: INGEST          │
                    │  Confirmed → SQLite      │
                    │  Confirmed → VDB embed   │
                    │  Rejected → discard      │
                    │  Revised → back to Draft │
                    └───────────┬─────────────┘
                                ↓
                    ┌─────────────────────────┐
                    │  PASS 8: VERIFY          │
                    │  Query intent memory     │
                    │  Prove pipeline can      │
                    │  measure against it      │
                    └─────────────────────────┘
```

---

## 3. Pass 5/6 Detail: The Batch Review Form

### 3.1 Why a form instead of dialog

A one-at-a-time conversational gate where a model reads each intention and asks "is this correct?" creates a bottleneck. Eric reviews hundreds of intention items — this must be efficient.

### 3.2 Form structure

Generated as JSON after Pass 4 (Review Stage B). Rendered in the portal's EricGatePage component.

Each row in the review form:

```json
{
  "id": "intent-042",
  "text": "I need checks and balance — if I don't trust something one of you says, I paste it for another model to evaluate.",
  "model_interpretation": "Eric wants independent adversarial review between models — he does not trust single-model output without verification.",
  "mapped_layer": "abstraction-layer",
  "mapped_component": "dispatch router / reviewer routing",
  "source": "session_20260518, line 47",
  "voice": "eric-verbatim",
  "categories": ["eric-intention", "agent-roles", "pipeline"],
  "decision": null,
  "revision_note": null
}
```

### 3.3 Portal UI

Each row renders as a card:

```
┌──────────────────────────────────────────────────────────┐
│ INTENT #042                              source: s18 L47  │
│                                                          │
│ "I need checks and balance — if I don't trust something  │
│  one of you says, I paste it for another model to        │
│  evaluate."                                              │
│                                                          │
│ → Maps to: abstraction-layer / dispatch router           │
│ → Model says: Eric wants independent adversarial review  │
│              between models                              │
│                                                          │
│ [✓ Confirm]   [✗ Reject]   [↩ Revise]                   │
│ Revision note: [________________________________]        │
└──────────────────────────────────────────────────────────┘
```

### 3.4 Actions per item

| Action | Result |
|--------|--------|
| **Confirm** | Item enters SQLite + VDB as measurement standard |
| **Reject** | Item discarded — model misinterpreted |
| **Revise** | Eric writes correction — item returns to Drafter for re-interpretation, then re-enters the review form |

### 3.5 Batch submit

Eric reviews the full list (scrollable, filterable by layer, category, source). One submit button processes all decisions. Confirmed items are ingested. Revised items spawn a new Drafter pass. Rejected items are logged but discarded.

### 3.6 States

The review form persists (saved to spine, reloadable). Eric can:
- Save partial progress and return later
- Filter by: layer, category, source, decision status
- See counts: 142 pending, 38 confirmed, 5 rejected, 3 revised

---

## 4. Ingestion Schema (Pass 7)

### 4.1 SQLite — Fast DB (structured reference)

Four tables added to `cis_memory.db`:

#### intent_map

```sql
CREATE TABLE intent_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_text TEXT NOT NULL,              -- Eric's verbatim words
    model_interpretation TEXT NOT NULL,      -- What the model thinks Eric means
    mapped_layer TEXT NOT NULL,             -- control-plane | abstraction-layer | hermes-backend
    mapped_component TEXT NOT NULL,         -- e.g. "dispatch router", "pre_tool_call hook"
    source_file TEXT NOT NULL,              -- Source document path
    source_line INTEGER,                    -- Line number in source
    source_timestamp TEXT,                  -- When Eric said it
    voice TEXT NOT NULL,                    -- eric-verbatim | eric-framing
    categories TEXT,                        -- Comma-separated category labels
    review_decision TEXT NOT NULL,          -- CONFIRMED | REVISED
    revision_note TEXT,                     -- Eric's correction if REVISED
    eric_confirmed_at TEXT,                 -- Timestamp of confirmation
    status TEXT DEFAULT 'active',           -- active | superseded | deprecated
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_intent_map_layer ON intent_map(mapped_layer);
CREATE INDEX idx_intent_map_component ON intent_map(mapped_component);
CREATE INDEX idx_intent_map_voice ON intent_map(voice);
```

#### anti_patterns

```sql
CREATE TABLE anti_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    eric_asked TEXT NOT NULL,               -- What Eric actually wanted
    model_produced TEXT NOT NULL,           -- What the model did instead
    friction_type TEXT NOT NULL,            -- enterprise-default | amnesia | scope-creep | etc.
    guardrail_mechanism TEXT,               -- What prevents this from recurring
    source_file TEXT NOT NULL,
    source_line INTEGER,
    failure_flag TEXT,                      -- From tagging: false-proof, amnesia-trigger, etc.
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### functional_spec

```sql
CREATE TABLE functional_spec (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL,           -- e.g. "pre_tool_call hook"
    layer TEXT NOT NULL,                    -- control-plane | abstraction-layer | hermes-backend
    description TEXT NOT NULL,              -- What it does
    wiasw_origin TEXT,                      -- WIASW lineage if applicable
    intent_source_ids TEXT,                 -- Comma-separated intent_map IDs that informed this
    build_status TEXT DEFAULT 'unspecified',
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### reviewer_brief

```sql
CREATE TABLE reviewer_brief (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterion TEXT NOT NULL,                -- e.g. "Eric's role is approve/disapprove/refine"
    category TEXT NOT NULL,                 -- profile-character | reviewer-duties | measurement-criteria
    detail TEXT NOT NULL,                   -- Full description
    source_file TEXT,
    source_line INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### 4.2 Chroma VDB — Semantic Search

Two collections:

| Collection | Embedded content | Use case |
|-----------|-----------------|----------|
| `intent_memory` | Every CONFIRMED `eric-verbatim` fragment | "Find Eric statements similar to this proposal" |
| `anti_patterns` | Every CONFIRMED anti-pattern entry | "Has this failure happened before?" |

Embedding model: whatever is available and efficient (sentence-transformers already installed). Metadata per chunk: source file, line, mapped layer, mapped component, categories.

### 4.3 Why both

- **SQLite** — exact queries. Reviewer asks: "Show me every confirmed intention about the dispatch router." Returns structured rows.
- **Chroma** — fuzzy queries. Reviewer asks: "Does this Drafter proposal semantically match anything Eric actually asked for?" Returns similarity-ranked results.
- The pipeline uses SQLite for deterministic checks, Chroma for pattern matching.

---

## 5. Runtime Wiring (Pass 8)

### 5.1 How pipeline stages use intent memory

Each pipeline stage receives a context injection at session init. The `drafter_session_init.py` and `reviewer_session_init.py` scripts (already built) are extended to query intent memory and include relevant results.

| Stage | Queries | Context injected |
|-------|---------|-----------------|
| Drafter | `intent_map` WHERE layer, component match topic | Top 10 most relevant intentions |
| Reviewer A | `reviewer_brief` — measurement criteria | What to audit tags against |
| Reviewer B | `intent_map` + `anti_patterns` | Eric's words + known failures |
| Implementer | `functional_spec` + `intent_map` | What to build + what Eric asked for |
| Eric Gate | All tables | Full evidence trail |

### 5.2 Container mounts

The Docker container running the pipeline gets:

```
/source/cis_memory.db    → RO mount (SQLite fast DB)
/source/chroma/          → RO mount (VDB embeddings)
```

The container queries intent memory but cannot modify it. Ingestion scripts run outside the container.

---

## 6. Portal UI Changes

### 6.1 EricGatePage — Batch Review Mode

Extend existing `EricGatePage.jsx` with a new mode: "Intent Review."

- Renders the review form JSON as a scrollable, filterable list
- Per-item: Confirm / Reject / Revise buttons + revision note field
- Batch submit: POST all decisions to `/api/portal/intent-review/submit`
- Save partial progress to localStorage and spine
- Filter by: layer, category, source, decision status
- Progress bar: "142 of 387 confirmed"

### 6.2 New endpoint

```
POST /api/portal/intent-review/generate
  → Drafter produces review form JSON from tagged corpus

GET /api/portal/intent-review/status
  → Returns counts: pending, confirmed, rejected, revised

POST /api/portal/intent-review/submit
  → Body: [{id, decision, revision_note}, ...]
  → Processes all decisions, triggers ingestion
```

---

## 7. Build Order

```
Phase A: Pre-process sessions
  └─ Extract user messages from all 18 session JSONL files
  └─ Output: flat text files, one per session

Phase B: Tag all sources (Pass 1)
  └─ Session extracts + Anthropic export + CIS docs + WIASW
  └─ 3 models per document, directive v3.1
  └─ Output: tagged files in catalog/tagging_results/

Phase C: Review Stage A (Pass 2)
  └─ R1 + Qwen audit tags
  └─ Output: reconciled tags

Phase D: Drafter synthesizes (Pass 3)
  └─ Produce 5 deliverables
  └─ Output: intent_map.json, functional_spec.json, anti_patterns.json, etc.

Phase E: Review Stage B (Pass 4)
  └─ Audit deliverables against intent
  └─ Output: audit report

Phase F: Generate review form (Pass 5)
  └─ Extract intention items into batch review JSON
  └─ Wire to portal endpoint

Phase G: Portal UI — batch review mode (Pass 6)
  └─ Extend EricGatePage with batch review
  └─ POST endpoint for submit

Phase H: Eric reviews and confirms (Pass 6 continued)
  └─ Eric processes review form in portal
  └─ Output: confirmed/rejected/revised decisions

Phase I: Ingestion (Pass 7)
  └─ CONFIRMED items → SQLite intent_map, anti_patterns, functional_spec, reviewer_brief
  └─ CONFIRMED items → Chroma VDB embeddings
  └─ REVISED items → back to Drafter

Phase J: Verification (Pass 8)
  └─ Query intent memory from pipeline stages
  └─ Prove pipeline measures against Eric's words
  └─ Success: Reviewer flags at least one drift that would have passed without intent memory
```

---

## 8. Dependencies

| Phase | Depends on | Blocks |
|-------|-----------|--------|
| A (pre-process) | Nothing | B |
| B (tag) | A | C |
| C (review A) | B | D |
| D (draft) | C | E |
| E (review B) | D | F |
| F (generate form) | E | G |
| G (portal UI) | F | H |
| H (Eric review) | G | I |
| I (ingest) | H | J |
| J (verify) | I | Pipeline runtime |

---

## 9. What Exists vs What's New

| Component | Status |
|-----------|--------|
| Tagging directive v3.1 | EXISTS — tested on 4 docs |
| CATEGORY_TO_LAYER_MAP.md | EXISTS |
| 3-model parallel tagging script | EXISTS — proven |
| Session pre-processing script | NEW |
| Review Stage A/B pipeline | EXISTS (tools/pipeline/) — needs intent memory injection |
| Drafter session init | EXISTS — needs intent memory query |
| EricGatePage.jsx | EXISTS — display only, needs batch review + write path |
| Batch review form endpoint | NEW |
| Intent ingestion scripts | NEW |
| ChromaDB | EXISTS (v1.5.9) — needs new collections |
| cis_memory.db | EXISTS — needs 4 new tables |
| Container RO mounts | EXISTS (proven) — needs new paths |

---

## 10. Risks

1. **Session parsing:** JSONL format may have changed across Hermes versions. Test on one file from each profile before full parse.
2. **Tagging scale:** 700+ documents × 3 models = 2,100+ tagging jobs. Pipeline must handle this without timeout or model exhaustion.
3. **Model hallucination in tagging:** The directive v3.1 reduces this, but Review Stage A must catch false VOICE assignments and category errors.
4. **Eric fatigue:** 300+ intention items to review. Mitigation: filterable form, save progress, batch submit.
5. **VDB rebuild block:** AGENTS.md previously blocked VDB work. Eric explicitly overrode this (2026-06-26). This spec is the authority.
