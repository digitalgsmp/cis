# CIS Intention Alignment Pipeline — Specification v1.0

**Author:** Hermes R1 Reviewer (deepseek-v4-pro)
**Date:** 2026-06-26
**Status:** DRAFT — awaiting Eric Gate review
**Purpose:** Define the end-to-end pipeline that extracts Eric's verbatim intentions from all available source files, presents them for clarity validation, and feeds confirmed intentions into the CIS build pipeline as the measuring tool for all downstream work.

---

## 1. Problem Statement

The CIS pipeline (Drafter → Reviewer → Implementer → Eric Gate) exists but has no source of truth to measure against. Eric's intentions — the definitions of what CIS, SWA, and WIAS are supposed to be — live across spreadsheets, plain-language roadmaps, archived notes, and chat transcripts. Without a catalog of these intentions, the pipeline cannot:
- Verify that a Drafter proposal aligns with Eric's original intent
- Detect when an Implementer output diverges from what was specified
- Present Eric with a clear "this is what I thought you meant — is it correct?" checkpoint

## 2. Target End State

A five-stage pipeline that:

1. Extracts every verbatim Eric statement from all available files into a searchable catalog
2. Presents each intention to Eric for clarity validation (confirm/reject/edit/comment)
3. Feeds confirmed intentions into the build-priority decision process
4. Generates workflow documents from validated intentions
5. Provides the measuring tool the pipeline uses to verify alignment at every stage

```
ALL source files → Extract → Eric-filter → Domain-tag → SQLite+FTS5 catalog
                                     ↓
                           Eric clarity validation (batch review form)
                                     ↓
                           Confirmed intentions → build priority decisions
                                     ↓
                           Drafter specs ← measured against intentions
                                     ↓
                           Reviewer verifies ← measured against intentions
                                     ↓
                           Implementer builds ← measured against intentions
```

## 3. Five Stages

### Stage 1: Full Corpus Extraction (READ-ONLY)

**Input:** All parseable files across:
- `/mnt/archive/WIAS/` — WIAS spreadsheets, production pipeline docs
- `/mnt/projects/cis/` — CIS docs, specs, code, spine
- `/mnt/projects/swa/` — SWA project files, transcripts, kernel
- `/mnt/archive/_2 Word/` — Idea Bank, creative notes
- `/home/eric/.hermes*/sessions/` — All Hermes chat sessions across profiles

**Output:** 
- `file_inventory.json` — Every file with path, size, type, project tag
- `extracted_text/` — Raw text from every parseable file
- `eric_catalog.db` — SQLite database with FTS5 full-text search

**Catalog schema:**
```sql
CREATE TABLE eric_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    project TEXT NOT NULL,        -- CIS, SWA, WIAS, ARCHIVE, SESSIONS
    speaker TEXT NOT NULL,        -- eric_verbatim, eric_framing, system_generated, unknown
    domain TEXT NOT NULL,         -- cis, swa, wias, shared (comma-separated)
    raw_text TEXT NOT NULL,
    timestamp TEXT,
    char_length INTEGER,
    status TEXT DEFAULT 'unevaluated',  -- unevaluated, confirmed, rejected, revised, duplicate
    eric_comment TEXT,
    revised_text TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE eric_catalog_fts USING fts5(raw_text, content=eric_catalog, content_rowid=id);
```

**Scope:** 77,128 files discovered → ~18,700 parseable → ~71,000 text fragments → ~2,900 Eric-verbatim/framing fragments.

### Stage 2: Eric Clarity Validation (BATCH REVIEW)

**Problem:** Per-item sequential review (one-at-a-time in Telegram) does not scale to 2,900 fragments.

**Solution:** A single-page HTML review form, loadable in any browser on desktop or tablet.

**Review form features:**
- Table/list view of all Eric-verbatim fragments
- Four actions per item:
  - ✓ **Confirm** — "Yes, this is what I meant"
  - ✗ **Reject** — "This is not my intention / not relevant"
  - ✏ **Revise** — Edit the text to clarify what was actually intended
  - 💬 **Comment** — Add a note without changing status
- **Filters:** by project (CIS/SWA/WIAS/Shared), domain, source file, status
- **Sort:** by source, domain, timestamp, text length
- **Batch actions:** "Confirm all from [source]", "Reject all system-generated"
- **Pagination:** 50 items per page, keyboard navigation
- **Persistence:** Saves to `eric_catalog.db` via embedded SQLite (or writes JSON that a script ingests)

**Output:** Every fragment tagged: confirmed / rejected / revised + eric_comment + revised_text.

**Delivery:** Single HTML file at `/mnt/cache/catalog/review.html`. Eric opens it locally. No server required. All data embedded in the page (or loaded from a companion JSON file).

### Stage 3: Build Priority from Confirmed Intentions

**Input:** Confirmed intentions from Stage 2.

**Process:**
- Query catalog: `SELECT * FROM eric_catalog WHERE speaker IN ('eric_verbatim','eric_framing') AND status='confirmed'`
- Group by domain (CIS, SWA, WIAS, Shared)
- Agents in this chat deliberate: what must be built next based on confirmed intentions?
- Eric decides priority

**Output:** Prioritized build targets, each traced to source intentions.

### Stage 4: Drafter Workflow Documents

**Input:** Confirmed intentions + build priority decisions from Stage 3.

**Process:**
- Drafter produces specification documents for the next build target
- Every requirement in the spec is traceable to a source intention (by catalog ID)
- Reviewer verifies: does this spec satisfy the referenced intentions?
- Eric Gate approves

### Stage 5: Implementer Build & Verify

**Input:** Approved Drafter spec from Stage 4.

**Process:**
- Implementer builds to spec
- Verification: does the output match the spec, which matches the source intentions?
- Measuring tool: query `eric_catalog.db` to confirm alignment
- Evidence required (Verification Hardening Rule): git diff, test output, endpoint response

## 4. Pipeline Integration

### How the catalog measures alignment

At every pipeline stage, the catalog serves as the source of truth:

| Stage | Catalog query | Purpose |
|-------|--------------|---------|
| Drafter | `WHERE domain='cis' AND status='confirmed'` | Author spec from confirmed intentions |
| Reviewer | Cross-reference spec claims against source intentions | Verify no intention is missed or distorted |
| Implementer | Every module traced to a spec requirement → traced to an intention | Build what was intended |
| Eric Gate | "Here are the intentions this work addresses. Confirm?" | Visibility into what's being built and why |

### How this feeds the existing CIS pipeline

The intention catalog does not replace the pipeline — it feeds it. The existing Drafter→Reviewer→Implementer flow gains a measuring tool:
- **Before:** Drafter authors from memory/training data → no way to verify alignment
- **After:** Drafter authors against confirmed intentions → Reviewer verifies against same source → Implementer builds traceably

## 5. Implementation Scope

### What SHALL be built

| Component | Description | Location |
|-----------|-------------|----------|
| `discover_files.py` | Walk all source roots, produce file_inventory.json | `tools/catalog/` |
| `extract_text.py` | Parse each file type, produce extracted_text/ | `tools/catalog/` |
| `filter_eric.py` | Tag speaker (eric_verbatim, etc.), produce eric_corpus.jsonl | `tools/catalog/` |
| `build_catalog_db.py` | Populate eric_catalog.db with FTS5 | `tools/catalog/` |
| `review.html` | Single-page batch review form | `/mnt/cache/catalog/` |
| `apply_review.py` | Read review form output, update catalog statuses | `tools/catalog/` |
| `search_catalog.py` | CLI: FTS5 search + domain/speaker/status filter | `tools/catalog/` |

### What SHALL NOT be built (this tier)

- UI dashboard for catalog browsing (deferred — review form is sufficient)
- Automated intention-to-spec generation (Drafter handles this per-spec)
- VDB/Chroma indexing of intentions (separate tier — catalog is SQLite+FTS5)
- Telegram bot for intention review (batch form replaces chat-based review)
- Live catalog refresh on file change (run tools again to regenerate)

### Storage

- Catalog root: `/mnt/cache/catalog/` (existing, SSD, 111.8 GB available)
- Catalog DB: `/mnt/cache/catalog/eric_catalog.db` (standalone, not in CIS spine)
- Extracted text: `/mnt/cache/catalog/extracted_text/` (derived, reproducible)
- Review form: `/mnt/cache/catalog/review.html`

## 6. Out of Scope

- Crawling or scraping external websites/APIs
- Extracting text from images (OCR) or audio (transcription)
- Password-protected or encrypted files
- Real-time sync with source files (regenerate catalog to refresh)
- Integration with Chroma/VDB vector search (separate tier)
- Multi-user review (Eric-only)

## 7. Current State (as of 2026-06-26)

| Stage | Status | Output |
|-------|--------|--------|
| Stage 1 — Extraction | **COMPLETE** | `eric_catalog.db` (39.7 MB, 71,466 fragments, 2,820 Eric-verbatim) |
| Stage 2 — Review Form | **NOT BUILT** | Spec this document |
| Stage 3 — Build Priority | **NOT STARTED** | Depends on Stage 2 |
| Stage 4 — Drafter Docs | **NOT STARTED** | Depends on Stage 3 |
| Stage 5 — Build & Verify | **NOT STARTED** | Depends on Stage 4 |

## 8. Acceptance Criteria

### A1: Catalog Integrity
- [ ] `eric_catalog.db` contains all Eric-verbatim fragments from all source roots
- [ ] FTS5 search returns relevant results for queries like "pipeline", "Eric Gate", "WIAS"
- [ ] Every fragment has: source_file, project, speaker, domain, raw_text

### A2: Review Form
- [ ] `review.html` loads in browser without server
- [ ] All Eric-verbatim fragments are displayed
- [ ] Confirm/Reject/Revise/Comment actions work per item
- [ ] Batch actions work (confirm all from one source)
- [ ] Filter by domain and project works
- [ ] Review decisions are persisted (to JSON file or directly to SQLite)

### A3: Pipeline Integration
- [ ] `search_catalog.py` can be called from pipeline scripts
- [ ] Drafter can query confirmed intentions as context for spec authoring
- [ ] Reviewer can cross-reference spec claims against catalog

---

## FINAL_JSON

```json
{
  "role": "Reviewer",
  "status": "PROPOSAL_READY",
  "summary": "Five-stage intention alignment pipeline specified. Stage 1 complete (catalog built, 2,820 Eric-verbatim fragments). Stage 2 (batch review form) is the next build target — a single HTML page for Eric to confirm/reject/revise intentions at scale. Stages 3-5 depend on Stage 2 completion. All work traces back to confirmed intentions, giving the CIS pipeline a measuring tool at every stage.",
  "recommendation": "Eric review and approve Stage 2 review form design before build. The form replaces one-at-a-time Telegram review with batch operation Eric controls on his own time.",
  "next_action": "If approved, build review.html. If design changes needed, revise §Stage 2 before build."
}
```
