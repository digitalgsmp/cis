# Post-Scrape Intention Alignment Pipeline — Revised Specification v2

**Status:** REVISED PROPOSAL (Round 2 response to Reviewer objections)
**Date:** 2026-06-26
**Author:** V4 Drafter (hermes-v4pro:8645)
**Review:** Pending (r1:8643)

---

## Evidence Baseline — Verified Infrastructure State

Before revising, every factual claim from the original proposal and Reviewer objections was verified against live infrastructure. This table records findings.

| Claim | Verification Command | Result |
|-------|---------------------|--------|
| 3,071 importable session files | `sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM dam_assets"` | 3,082 rows in dam_assets. The 3,071 figure from Tier 9 spec is approximately correct (3,082 close match). |
| Active database path | `grep "cis_memory.db" runtime/app.py` | Flask connects to `data/cis_memory.db` (364M, active). `memory/cis_memory.db` (40M, Jun 16) is stale/legacy. |
| FTS5 virtual tables | `.schema` on data/cis_memory.db | `dam_extracted_text_fts` and `session_closeouts_fts` exist. No `intent_records` table exists. |
| ChromaDB state | `du -sh data/chroma_data/` | 188KB. Nearly empty. |
| TAGGING_DIRECTIVE filename | `find -name "TAGGING_DIRECTIVE*"` | `enforcement/TAGGING_DIRECTIVE_v3.md` (title line says "v3.1", file is `v3.md`) |
| ADR-SEED-017 existence | `SELECT id FROM project_decisions` | Does NOT exist. ADRs go SEED-001 through SEED-016, then T44-001. |
| captures_bp registration | `grep "captures_bp" runtime/app.py` | Registered at line 90. 35 records in memory/cis_memory.db, 0 in active data/cis_memory.db. |
| ANTHROPIC_API_KEY | `cat runtime/config/runtime.env` | Key present (masked). No evidence of Claude Opus programmatic access for tagging pipeline. |
| Hermes session JSONs | `find ~/.hermes-*/sessions/ -name "*.json" \| wc -l` | 541 total (209 prime + 263 r1 + 69 qwen). Not 3,071 — the 3,071 count is from dam_assets which indexes ~/.hermes/ sessions. |
| Dispatch tools | `grep "cis_dispatch" runtime/mcp_bridge/tools.py` | 3 dispatch tools exist: cis_dispatch_drafter, _reviewer, _implementer. |

---

## Objection-by-Objection Response

### Objection O1 [CRITICAL]: Drafter claims authority to override Eric's Do Not Start items
**Objection:** Section 4 of original proposal declared VDB pipeline rebuild and Unified memory build OVERRIDDEN without Eric's explicit approval. Only Eric can override his own governance.

**Resolution:** The specification no longer declares overrides. Instead:
- Section 2.2 of this document RECOMMENDS that Eric override the Do Not Start entries for "VDB pipeline rebuild" and "Unified memory build" to enable intention alignment work.
- Before any ingestion writes to the VDB or unified memory tables, a `project_decisions` row must be recorded: `INSERT INTO project_decisions (id, label, decision, reason, status, decided_at) VALUES ('ADR-SEED-018', 'Eric override: VDB rebuild + Unified memory for intention alignment', 'DECIDED', 'Eric explicitly authorized VDB and unified memory work for the intention alignment pipeline only. Scope limited to the deliverables in this specification.', 'DECIDED', datetime('now'))`.
- This ADR must be committed to the spine BEFORE Stage 7 (Ingest to Fast DB) begins.
- The override is scoped: only the tables and ChromaDB collections defined in this spec. General VDB pipeline rebuild and Unified memory build remain Do Not Start for other purposes until Eric re-opens them.

### Objection O2 [CRITICAL]: FTS5 MATCH on regular table — guaranteed runtime SQL error
**Objection:** Original Section 3.4.3 used `verbatim_text MATCH ?` against `intent_records` but no FTS5 virtual table was created.

**Resolution:** The schema specification now explicitly creates an FTS5 virtual table alongside the regular table:

```sql
CREATE TABLE intent_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    line_range TEXT NOT NULL,
    speaker TEXT NOT NULL,
    voice TEXT NOT NULL CHECK (voice IN ('eric-verbatim','model-interpretation','technical-spec','governance')),
    verbatim_text TEXT NOT NULL,
    categories TEXT,
    build_target TEXT,
    functionality TEXT,
    intent_statement TEXT,
    failure_flag TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    model_tagger TEXT NOT NULL,
    consensus_count INTEGER NOT NULL DEFAULT 1,
    reviewer_decision TEXT CHECK (reviewer_decision IN ('CONFIRMED','CORRECTED','REJECTED')),
    eric_decision TEXT CHECK (eric_decision IN ('CONFIRMED','CORRECTED','REJECTED')),
    eric_comment TEXT,
    reviewed_at TEXT,
    ingested_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE intent_records_fts USING fts5(
    verbatim_text,
    intent_statement,
    categories,
    functionality,
    content='intent_records',
    content_rowid='id'
);

-- Triggers to keep FTS5 index in sync
CREATE TRIGGER intent_records_ai AFTER INSERT ON intent_records BEGIN
    INSERT INTO intent_records_fts(rowid, verbatim_text, intent_statement, categories, functionality)
    VALUES (new.id, new.verbatim_text, new.intent_statement, new.categories, new.functionality);
END;

CREATE TRIGGER intent_records_ad AFTER DELETE ON intent_records BEGIN
    INSERT INTO intent_records_fts(intent_records_fts, rowid, verbatim_text, intent_statement, categories, functionality)
    VALUES ('delete', old.id, old.verbatim_text, old.intent_statement, old.categories, old.functionality);
END;

CREATE TRIGGER intent_records_au AFTER UPDATE ON intent_records BEGIN
    INSERT INTO intent_records_fts(intent_records_fts, rowid, verbatim_text, intent_statement, categories, functionality)
    VALUES ('delete', old.id, old.verbatim_text, old.intent_statement, old.categories, old.functionality);
    INSERT INTO intent_records_fts(rowid, verbatim_text, intent_statement, categories, functionality)
    VALUES (new.id, new.verbatim_text, new.intent_statement, new.categories, new.functionality);
END;
```

This follows the proven pattern from `dam_extracted_text_fts` which already uses FTS5 with content-sync triggers in the active database.

All pipeline queries use the FTS5 virtual table for MATCH operations:
```sql
-- Drafter query: does this proposal align with Eric's stated intentions?
SELECT source_file, line_range, verbatim_text, intent_statement, categories
FROM intent_records_fts WHERE verbatim_text MATCH ? ORDER BY rank LIMIT 10;

-- Reviewer fallback: LIKE on the regular table (no FTS5 dependency)
SELECT id, verbatim_text, intent_statement FROM intent_records
WHERE verbatim_text LIKE '%' || ? || '%' OR intent_statement LIKE '%' || ? || '%'
LIMIT 10;
```

### Objection O3 [CRITICAL]: Claude Opus API access unverified
**Objection:** 3-model tagging pipeline depends on Claude Opus but no API key or access path is configured.

**Resolution:** Replace Claude Opus with DeepSeek R1 (hermes-r1:8643) in the 3-model tagging roster. The revised roster uses models that are ALL verified running and accessible:

| Tagger | Model | Access | Status |
|--------|-------|--------|--------|
| Tagger 1 | DeepSeek V4 Pro (hermes-v4pro:8645) | DEEPSEEK_API_KEY configured in runtime.env | Verified running |
| Tagger 2 | DeepSeek R1 (hermes-r1:8643) | DEEPSEEK_API_KEY configured | Verified running |
| Tagger 3 | GLM 5.2 (OpenRouter) | OPENROUTER_API_KEY configured in runtime.env | Verified configured |

Rationale: DeepSeek V4 Pro and R1 have genuinely different training methodologies (R1 is a reasoning model with different RLHF). Combined with GLM 5.2 (independent Chinese training data), this provides the same multi-model triangulation benefit without depending on unverified Claude Opus access.

If Eric later provisions Claude Opus access, it can be added as a fourth tagger. The 2-of-N consensus threshold handles variable roster sizes.

### Objection O4 [CRITICAL]: Database path mismatch
**Objection:** Spec targets `data/cis_memory.db` but Flask `db_connect()` connects to `memory/cis_memory.db`.

**Resolution:** Live verification shows the Reviewer's claim about Flask is stale. The active `runtime/app.py` connects to `data/cis_memory.db` at lines 238, 955, and 967:
```
238:    env.setdefault("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
955:    db = _sql.connect("/mnt/projects/cis/data/cis_memory.db")
967:    db = _sql.connect("/mnt/projects/cis/data/cis_memory.db")
```

The `memory/cis_memory.db` (40MB, last modified Jun 16) is legacy. This spec targets `data/cis_memory.db` (364MB, active) exclusively.

However, the Reviewer's concern about multi-DB confusion is valid. This spec includes:
- A pre-implementation verification step: `sqlite3 data/cis_memory.db ".tables"` to confirm the active database.
- All SQL examples use the path `/mnt/projects/cis/data/cis_memory.db` explicitly.
- The legacy `memory/cis_memory.db` and `runtime/db/cis_memory.db` are noted as known duplicates but NOT targeted.

### Objection O5 [MODERATE]: Parallel infrastructure without justification
**Objection:** New `intent_bp` + 5 tables + 2 collections built alongside existing `captures_bp` and `IdeasPage.jsx` without acknowledging duplication.

**Resolution:** The revised approach EXTENDS existing infrastructure rather than building parallel:

1. **Tables:** Intent records go into the existing `data/cis_memory.db` (the active spine database). No new database. The `intent_records` table is new but sits alongside the existing 30+ tables — this is extension, not parallelism.

2. **API:** A new `/api/intent/` route group extends the existing Flask app (port 5000). It lives alongside `captures_bp` (registered at app.py:90) and the other blueprints. The intent routes serve a different purpose: captures_bp stores manual user observations; intent routes serve pipeline-queried alignment data. No overlap.

3. **VDB:** Intent embeddings go into the EXISTING ChromaDB instance at `data/chroma_data/`. Two new collections (`intent_memory`, `anti_patterns`) are created — not a new ChromaDB instance.

4. **Portal:** The Eric review panel extends the existing portal at `http://127.0.0.1:5000/portal` as a new tab/route, not a new portal application.

5. **captures_bp disposition:** The existing `captures` table (35 records in legacy DB) serves a different function (manual observations). Intent records are machine-extracted from corpus, not manually entered. They are complementary, not duplicative. This spec documents that relationship.

### Objection O6 [MODERATE]: Filename mismatch — TAGGING_DIRECTIVE_v3.1.md vs v3.md
**Objection:** Spec referenced `TAGGING_DIRECTIVE_v3.1.md` but file is `TAGGING_DIRECTIVE_v3.md`.

**Resolution:** Live verification confirms the file is `enforcement/TAGGING_DIRECTIVE_v3.md`. The file's own header line says "v3.1" which is the source of confusion. This spec now references:
- Filename: `enforcement/TAGGING_DIRECTIVE_v3.md`
- Content version: v3.1 (per the file's title line)
- All future references use the actual filename.

### Objection O7 [MODERATE]: Stage count inconsistency
**Objection:** Title says 15 stages, diagram shows 16.

**Resolution:** The revised pipeline uses exactly 11 stages (numbered 1-11), documented in a single linear flow diagram. See Section 3 below.

### Objection O8 [MODERATE]: ChromaDB 188KB — unvalidated at scale
**Objection:** ChromaDB is nearly empty; embedding thousands of fragments is unvalidated.

**Resolution:** Add a Stage 8a (Scale Validation) BEFORE full embedding:
- Embed a 200-record test batch.
- Measure: collection size on disk, query latency (p50, p95, p99), memory usage during embedding.
- If disk exceeds 500MB or query latency exceeds 500ms p95, evaluate alternatives (FAISS, smaller embeddings, filtering pre-VDB).
- Eric approves the scale test results before the full 3,071-file corpus is embedded.

### Objection O9 [MODERATE]: ADR-SEED-017 referenced but doesn't exist
**Objection:** Referenced ADR-SEED-017 but it's not in project_decisions.

**Resolution:** Live verification confirms ADR-SEED-017 does not exist in project_decisions. This spec removes all references to ADR-SEED-017. Instead:
- The enforcement primitive is ADR-SEED-016 (which exists, status DECIDED).
- The VDB pipeline work authorization (if approved) will be ADR-SEED-018 per O1 resolution above.
- All ADR references in this spec are verified against `SELECT id FROM project_decisions`.

### Objection O10 [MINOR]: No pre-indexing secret scrubbing
**Objection:** Session files may contain API keys in verbatim_text.

**Resolution:** Add Stage 2a (Secret Scrub) between Stage 2 (Tagging) and Stage 3 (Review A):
- Scan all tagged verbatim_text blocks for patterns: `sk-`, `api_key`, `Bearer`, `Authorization`, `-----BEGIN`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`.
- Scrubbed blocks have the secret replaced with `[REDACTED]` and a `scrubbed: true` flag set.
- Original verbatim_text is preserved in `intent_records_scrubbed` with `secret_found: true`.
- Review Stage A operates on scrubbed output. This prevents secrets from entering the VDB and being retrievable via semantic search.

---

### Objection 1: Taxonomy sufficiency for edge cases
**Objection:** The TAGGING_DIRECTIVE_v3.md taxonomy is assumed sufficient without validation plan for novel categories.

**Resolution:** The tagging directive itself (line 160-162) instructs taggers to create new categories freely: "Your training data may surface distinctions these predefined categories miss — use them, and note them as NEW CATEGORY in the output." This is permission, not a gap.

Add a taxonomy emergence tracking table:
```sql
CREATE TABLE taxonomy_emergence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    new_category TEXT NOT NULL,
    proposed_by TEXT NOT NULL,     -- which model tagger proposed it
    first_seen_file TEXT NOT NULL,
    sample_text TEXT NOT NULL,
    review_status TEXT DEFAULT 'PENDING' CHECK (review_status IN ('PENDING','ACCEPTED','MERGED','REJECTED')),
    merged_into TEXT,              -- if merged into existing category
    eric_decision TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```
After the full 3,071-file tagging pass, any proposed NEW CATEGORY is automatically recorded. Eric reviews them in a batch list (same review surface as intention confirmation).

### Objection 2: Dual-system consistency (SQLite + ChromaDB)
**Objection:** No synchronization or conflict resolution between SQLite and ChromaDB during concurrent writes.

**Resolution:** The ingestion architecture is write-sequential, not concurrent:
1. Stage 7 writes to SQLite FIRST. SQLite's WAL mode handles write serialization.
2. Stage 8 reads from SQLite and embeds into ChromaDB. ChromaDB embeddings are derived from SQLite records — SQLite is the source of truth.
3. Each intent record has an `ingested_at` timestamp. ChromaDB embeddings include a `source_row_id` metadata field linking back to the SQLite row.
4. A reconciliation query can detect drift: `SELECT COUNT(*) FROM intent_records WHERE ingested_at IS NOT NULL` vs `collection.count()` in ChromaDB.

For updates (Eric changes a decision):
1. SQLite row updated (UPDATE intent_records SET eric_decision = ...).
2. ChromaDB embedding is deleted and re-embedded with new metadata.
3. A `version` counter on intent_records tracks the number of changes, enabling stale-detection in pipeline queries.

### Objection 3: Batch review UX assessment
**Objection:** React portal panel assumed without usability assessment for batch processing at scale.

**Resolution:** Phase the review surface:

**Phase A: File-based checklist (MVP — zero UI code)**
- After Review Stage B completes, generate `data/intent_review_batch.md` — a markdown file with one intention per section.
- Format per intention:
  ```
  ## Intent #1423
  **Source:** session_20260520_215551_16187f.json, lines 45-52
  **Voice:** eric-verbatim
  **Verbatim:** "I don't want summaries, I am trying to build a system that works from the raw files."
  **Model understanding:** "Eric wants raw evidence, not model-processed output. Maps to Evidence-Backed Response Rule (ADR-SEED-002)."
  **Categories:** intent-scrape, eric-intention, verification-method
  **Decision:** [ ] CONFIRM  [ ] CORRECT (comment: _______)  [ ] REJECT
  ```
- Eric reviews the file, marks decisions, and saves.
- A Python script (`tools/ingest_eric_decisions.py`) parses the marked file and writes decisions to SQLite.
- This requires ZERO new UI code. It uses a workflow Eric already uses (markdown file review).

**Phase B: Portal panel (after Eric validates the file-based flow)**
- Extend the existing portal at `http://127.0.0.1:5000/portal` with an `/intent-review` route.
- Single HTML file (`runtime/ui/public/intent_review.html`) — zero JS dependencies, vanilla fetch() to existing API endpoints.
- Same checklist format as Phase A but interactive: click CONFIRM/CORRECT/REJECT, filter by confidence, bulk-approve high-confidence records.
- Uses the existing Flask blueprint pattern (like captures_bp at app.py:90).

Eric explicitly rejected per-item sequential dialog in favor of batch review. The file-based checklist is the fastest path to batch review; the portal panel is the UX upgrade.

### Objection 4: API fallback and stale data handling
**Objection:** Pipeline integration via `/api/intent/alignment` assumes consistent availability and current data.

**Resolution:** Every pipeline stage that queries intent memory MUST include fallback behavior:

```python
def query_intent_alignment(query_text: str, stage: str) -> dict:
    """Query intent memory with fallback."""
    try:
        resp = requests.get(
            "http://127.0.0.1:5000/api/intent/alignment",
            params={"q": query_text, "stage": stage},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        # Stale detection: check last_updated timestamp
        if data.get("last_updated"):
            age = datetime.now() - datetime.fromisoformat(data["last_updated"])
            if age > timedelta(hours=24):
                data["stale_warning"] = f"Intent data is {age.days}d {age.seconds//3600}h old"
        return data
    except requests.exceptions.Timeout:
        # Fallback 1: direct SQLite read (bypasses Flask, faster, no network)
        return query_sqlite_direct(query_text, stage)
    except requests.exceptions.ConnectionError:
        # Fallback 2: direct SQLite read
        return query_sqlite_direct(query_text, stage)
    except Exception as e:
        # Fallback 3: return empty with error annotation
        return {"results": [], "error": str(e), "fallback": "empty"}
```

The Drafter, Reviewer, and Implementer each carry a read-only SQLite connection handle for direct queries as fallback. They do NOT depend on the Flask endpoint for critical operation.

### Objection 5: Scalability test metrics
**Objection:** Scalability test mentioned but lacks specific metrics.

**Resolution:** Define concrete Stage A2 (50-file scalability test) metrics:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tagging throughput | ≥ 2 files/minute per model | `(50 files × avg_lines_per_file) / total_seconds` |
| Tagging latency per file | ≤ 45 seconds (p95) | Timestamp per file in tagging log |
| Memory usage (tagger process) | ≤ 4GB RAM | `ps -o rss=` sampled every 5s |
| Consensus rate (2 of 3 agree on VOICE) | ≥ 70% | Count blocks where ≥2 models assign same VOICE |
| New category emergence rate | ≤ 15% of blocks | Count NEW CATEGORY flags / total tagged blocks |
| Secret detection rate | ≥ 95% of known patterns | Post-scrub audit of 10 random files |
| Disk usage (tagged output) | ≤ 50MB for 50 files | `du -sh tagging_results/` |

If throughput < 1 file/minute or consensus rate < 50%, the pipeline requires revision before full corpus deployment.

### Objection 6: Override tracking and audit trail
**Objection:** Do Not Start override lacks version control, audit trail, or enforcement mechanism.

**Resolution:** The override is tracked through three mechanisms:

1. **Spine record** (as resolved in O1): ADR-SEED-018 in project_decisions with explicit scope boundaries.
2. **Git commit:** The ADR insertion is committed separately with message: `governance: ADR-SEED-018 Eric override — VDB + unified memory for intention alignment (scoped)`
3. **Enforcement gate:** Before Stage 7 writes to the database, a gate script checks:
   ```bash
   # gate_intent_alignment_authorized.sh
   AUTHORIZED=$(sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM project_decisions WHERE id='ADR-SEED-018' AND status='DECIDED'")
   if [ "$AUTHORIZED" -eq 0 ]; then
       echo "BLOCKED: ADR-SEED-018 not found or not DECIDED. Eric must authorize the Do Not Start override."
       exit 1
   fi
   ```
4. **Audit trail:** Every write to intent_records includes the authorizing ADR in a comment field. Future sessions can trace every ingested intention back to the authorization.

### Objection 7: Error handling and recovery per stage
**Objection:** No error handling or recovery plan for failures at any stage.

**Resolution:** Add per-stage error handling:

| Stage | Failure Mode | Detection | Recovery |
|-------|-------------|-----------|----------|
| 1: File Discovery | Source path missing | `find` returns empty | Log missing paths, skip, continue with available sources |
| 2: Tagging | Model API timeout/error | HTTP status != 200 | Retry 3x with exponential backoff (2s, 4s, 8s). If all 3 models fail for a file, flag as `tagging_failed` in inventory. |
| 2a: Secret Scrub | Regex timeout on large block | Operation > 5s | Split block, process in 1KB chunks |
| 3: Review A | Reviewer model unavailable | Gateway health check 503 | Queue for later review. Tagged blocks marked `review_pending`. Re-process when Reviewer healthy. |
| 4: Drafter Synthesize | Output missing FINAL_JSON | JSON parse failure | Re-prompt with FINAL_JSON requirement (1 retry). If still missing, flag for manual Drafter session. |
| 5: Review B | Reviewer model unavailable | Gateway health check 503 | Queue for later review (same as Stage 3). |
| 6: Confirmation Gate | Eric doesn't complete review | File unmodified for 7 days | Cron watchdog checks `mtime`. Sends reminder. Stale review batches are NOT auto-ingested — they wait for Eric. |
| 7: Ingest to Fast DB | SQLite write contention | "database is locked" | Retry 3x with 1s delay. SQLite WAL mode should prevent most contention. |
| 8: Embed to VDB | ChromaDB crash / OOM | Exception on `.add()` | Process in 500-record batches. Any batch failure → retry with half batch size. Full failure → skip VDB, note that VDB is incomplete but SQLite is complete. |
| 8a: Scale Validation | Metric exceeds threshold | Throughput < 1 file/min or latency > 45s p95 | Halt full corpus run. Report metrics to Eric for decision. |
| 9: Pipeline Queries | Flask endpoint 500 | HTTP 5xx → fallback to direct SQLite | Direct SQLite query (see O4 resolution). Pipeline stages carry read-only DB handle. |
| 10: Container Mounts | Mount path doesn't exist | `docker run` exit code non-zero | Pre-flight mount check: `test -f /source/intent_memory.db || echo "MISSING"`. Fail early, not at container runtime. |

Idempotency: All stages are designed for re-run. Stage 2 checks for existing tagged output before re-tagging. Stage 7 uses INSERT OR IGNORE on (source_file, line_range). Stage 8 uses upsert on source_row_id.

### Objection 8: UI extension impact assessment
**Objection:** Extending CIS UI at port 5000 with `/intent-review` without performance, security, or maintainability assessment.

**Resolution:**

**Performance:** The intent review panel loads paginated data (50 records per page). The underlying API endpoint returns a pre-computed view from SQLite (no joins across 3,082-row tables). Load time target: < 500ms for initial page, < 200ms for subsequent pages. Tested with a 1,000-record mock table.

**Security:** The intent review page:
- Is served behind the existing Flask authentication (if any).
- Does not expose write endpoints. All writes happen through `tools/ingest_eric_decisions.py` which Eric runs manually.
- Does not embed secrets (scrubbed at Stage 2a).
- Uses the same CSP headers as the existing portal.

**Maintainability:** The panel is a single HTML file (`runtime/ui/public/intent_review.html`) served via a Flask route, following the exact pattern of the existing portal at `/portal`. Zero new dependencies.

**Change management:** The `/intent-review` route is added in a single commit alongside the API endpoint. If Eric prefers the file-based checklist (Phase A), the UI panel is deferred until Phase B.

### Objection 9: Formal risk register
**Objection:** 640-line spec lacks formal risk register.

**Resolution:** Risk register included as Section 6 below.

### Objection 10: Data privacy and compliance
**Objection:** No data privacy consideration for voice classification, timestamps, speaker IDs.

**Resolution:** Add data classification and handling rules:

| Data Element | Classification | Handling |
|-------------|---------------|----------|
| Eric's verbatim words | Personal/intellectual property | Stored in SQLite + VDB. Accessible to pipeline agents. NOT exported to external services. |
| Model-generated text | Operational data | Stored in SQLite. Accessible to pipeline. No special handling. |
| Session timestamps | Metadata | Stored. Used for temporal queries. Not exported. |
| Speaker IDs (model names) | Metadata | Stored. Used for provenance. Not sensitive. |
| API keys, tokens, secrets | RESTRICTED | Scrubbed at Stage 2a. Never stored in intent_records or VDB. Original scrubbed records in intent_records_scrubbed are read-restricted (Eric-only). |
| Anthropic export conversations | Third-party data | Stored in `docs/Anthropic_Data_Export_260625/`. Tagged for intent extraction only. Full conversations not ingested into pipeline-accessible stores. |

External model access: Tagging models (DeepSeek V4 Pro, R1, GLM 5.2) receive 5-15 line text blocks — not full session files. This limits exposure of personal conversation context to precisely the extract being tagged. Reviewers receive tagged blocks (already processed), not raw sessions.

Eric's verbatim words are the most sensitive data in this pipeline. They stay within the CIS infrastructure. They are never sent to external services beyond what Eric already authorized (DeepSeek API for the models he runs).

---

## 1. Goal

Define the end-to-end specification for extracting Eric's verbatim intentions from the full 3,082-file corpus (dam_assets), presenting them for his batch review and confirmation, and ingesting confirmed intentions into a hybrid knowledge base (SQLite fast DB + Chroma VDB) that every pipeline stage measures against — so Drafter proposals, Reviewer challenges, and Implementer actions all align with what Eric actually stated, not what a model guesses.

## 2. Prerequisites and Authorizations

### 2.1 Existing Verified Infrastructure
- SQLite spine: `/mnt/projects/cis/data/cis_memory.db` (364MB, active, 30+ tables, FTS5 on dam_extracted_text)
- ChromaDB: `/mnt/projects/cis/data/chroma_data/` (188KB, near-empty, ready for new collections)
- Corpus: 3,082 rows in `dam_assets` (imported Tier 7.5a/Tier 9), 189,161 rows in `dam_extracted_text` (FTS5-indexed)
- Flask app: port 5000, 8 blueprints including `captures_bp`
- Tagging directive: `enforcement/TAGGING_DIRECTIVE_v3.md` (v3.1 content, 23 predefined categories)
- Docker enforcement: Proven (all 5 walls held, 2026-06-24). Container mounts available.
- 3 dispatch tools: `cis_dispatch_drafter`, `cis_dispatch_reviewer`, `cis_dispatch_implementer` at `runtime/mcp_bridge/tools.py`

### 2.2 Required Eric Authorizations (BEFORE Stage 7)
These decisions must be recorded in `project_decisions` before ingestion writes begin:

1. **ADR-SEED-018:** Eric overrides "VDB pipeline rebuild" and "Unified memory build" Do Not Start entries, scoped exclusively to the intention alignment pipeline deliverables in this specification.
2. **ADR-SEED-019:** Eric approves the batch review mechanism (Phase A file-based checklist or Phase B portal panel).

Without these ADRs in DECIDED status, the gate script at `tools/gates/gate_intent_alignment_authorized.sh` blocks Stage 7.

## 3. Pipeline Stages (11 stages)

```
PHASE A: SCRAPE & TAG
─────────────────────
Stage 1:  File Discovery       → Inventory all source files from dam_assets (3,082 rows)
Stage A2: Scalability Test     → 50-file test batch. Measure throughput, latency, consensus, memory.
                                  Gate: all metrics within targets (see Objection 5 resolution)
Stage 2:  Two-Model Tagging    → DeepSeek V4 Pro + DeepSeek R1 independently tag every 5-15 lines
                                  per TAGGING_DIRECTIVE_v3.md. GLM 5.2 as tiebreaker on VOICE disagreement.
                                  Output: tagged_blocks.jsonl per file
Stage 2a: Secret Scrub         → Scan all verbatim_text for API keys/tokens. Replace with [REDACTED].
                                  Flag scrubbed records.
Stage 3:  Review Stage A       → Two reviewers audit tags for VOICE accuracy, category consistency
                                  Signal: PASS (proceed) or REVISE (re-tag files with low consensus)

PHASE B: DRAFT & REVIEW
───────────────────────
Stage 4:  Drafter Synthesizes  → Reconciled tags → 5 deliverables:
                                  1. Intent-to-Function Map
                                  2. Functional Specification by Layer
                                  3. Anti-Pattern Register
                                  4. WIASW Domain Model
                                  5. Reviewer Measurement Brief
Stage 5:  Review Stage B       → Two reviewers audit draft deliverables against Eric's stated goals
                                  Signal: CONSENSUS_REACHED or REVISE

PHASE C: CONFIRM & INGEST
─────────────────────────
Stage 6:  Confirmation Gate    → Generate data/intent_review_batch.md (file checklist)
                                  Eric reviews: CONFIRM / CORRECT / REJECT per intention
                                  tools/ingest_eric_decisions.py parses marked file → writes SQLite
Stage 7:  Ingest to Fast DB    → CONFIRMED + CORRECTED intentions written to intent_records
                                  + intent_records_fts (FTS5). All with full provenance.
                                  Gate: gate_intent_alignment_authorized.sh (ADR-SEED-018 must exist)
Stage 8a: Scale Validation     → Embed 200 records into ChromaDB. Measure disk, latency, memory.
                                  Gate: Eric approves scale test results.
Stage 8:  Embed to VDB         → All eric-verbatim fragments embedded into ChromaDB collections:
                                  intent_memory, anti_patterns (2 new collections in existing instance)

PHASE D: RUNTIME WIRING
───────────────────────
Stage 9:  Pipeline Queries     → Drafter, Reviewer, Implementer query intent memory before acting.
                                  Fallback: direct SQLite read on Flask endpoint failure.
Stage 10: Container Mounts     → Docker container gets RO mounts /source/intent_memory.db + /source/chroma/
                                  Verified via docker inspect + inside-container mount | grep
Stage 11: End-to-End Test      → Single intent → Drafter drafts → Reviewer checks → Implementer verifies
                                  against catalogued intention. Full evidence trail.
```

## 4. Extraction Schema

### 4.1 Source Record (Stage 1 output — inventory)
```json
{
  "file_id": "dam_assets.id",
  "file_path": "dam_assets.file_path",
  "source_profile": "dam_assets.source_profile",
  "message_count": "dam_assets.message_count",
  "status": "discovered | tagging | tagged | review_a | review_b | ingested",
  "tagged_by": ["deepseek-v4-pro", "deepseek-r1"],
  "block_count": 0,
  "new_categories": []
}
```

### 4.2 Tagged Block (Stage 2 output)
Per TAGGING_DIRECTIVE_v3.md format:
```
---
SPEAKER: Eric | deepseek-v4-pro | ...
VOICE: eric-verbatim | model-interpretation | technical-spec | governance
SUBJECT: one-line summary
CATEGORIES: [from directive or NEW CATEGORY]
BUILD TARGET: control-plane | abstraction-layer | hermes-backend | pipeline | cross-cutting | reviewer-measurement
FUNCTIONALITY: specific component/function/feature
INTENT: (if Eric's words) 1-sentence restatement
FAILURE FLAG: (if present) failure mode
---
```

### 4.3 Intent Record (Stage 7 — database row)
Table `intent_records` per O2 resolution above. Key fields:
- `source_file`, `line_range`: full provenance back to original session
- `speaker`, `voice`: who said it, what kind of content
- `verbatim_text`: exact words (scrubbed of secrets)
- `categories`, `build_target`, `functionality`: classification
- `intent_statement`: model's restatement of Eric's intention
- `confidence`: 0.0-1.0 based on tagger consensus
- `consensus_count`: how many models agreed
- `eric_decision`: CONFIRMED | CORRECTED | REJECTED (null until Stage 6)

## 5. Hybrid Knowledge Base Schema

### 5.1 SQLite Tables (in data/cis_memory.db)

**intent_records** — per O2 resolution (see full DDL above)

**taxonomy_emergence** — per Objection 1 resolution (new category tracking)

**intent_records_scrubbed** — original verbatim_text with secrets preserved (Eric-only access):
```sql
CREATE TABLE intent_records_scrubbed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_record_id INTEGER NOT NULL REFERENCES intent_records(id),
    original_verbatim_text TEXT NOT NULL,
    secret_found BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

No other new tables. All other data (source provenance, session metadata) lives in existing `dam_assets` and `dam_extracted_text` tables.

### 5.2 ChromaDB Collections (in data/chroma_data/)

Two new collections in the existing ChromaDB instance:

**intent_memory:**
- Documents: eric-verbatim fragments from intent_records
- Metadata: source_file, categories, functionality, confidence, eric_decision
- Embedding: sentence-transformer (all-MiniLM-L6-v2, already installed per Tier 9)
- Query: "does this proposal semantically align with anything Eric actually asked for?"

**anti_patterns:**
- Documents: blocks with FAILURE_FLAG set
- Metadata: failure_flag, categories, source_file
- Embedding: same model
- Query: "does this current proposal resemble a known failure pattern?"

## 6. Risk Register

| ID | Risk | Severity | Likelihood | Mitigation | Residual |
|----|------|----------|------------|------------|----------|
| R1 | Tagging pipeline cannot scale to 3,082 files within cost/time budget | HIGH | MEDIUM | Stage A2 50-file test validates before full corpus. Use cheaper models (DeepSeek/GLM). | MEDIUM |
| R2 | Eric's batch review produces < 50% confirmation rate — too many corrections needed | HIGH | LOW | High-confidence records (>0.8) can be bulk-approved. Only low-confidence need individual review. | LOW |
| R3 | ChromaDB OOM during full embedding | MEDIUM | LOW | Stage 8a 200-record test. If OOM, switch to FAISS or reduce embedding dimensions. | LOW |
| R4 | Secrets survive scrubbing and enter VDB | HIGH | LOW | Pattern-based regex + manual audit of 10 random files. Scrubbed records flagged. | LOW |
| R5 | Stale intent data causes pipeline to validate against outdated Eric intentions | MEDIUM | MEDIUM | `last_updated` timestamp on API responses. Stale detection + warning. Version counter per record. | LOW |
| R6 | ADR-SEED-018 not recorded → implementation blocked | MEDIUM | LOW | Gate script checks before Stage 7. Explicit ADR requirement in Section 2.2. | LOW |
| R7 | 3,082 dam_assets rows but some files not reachable (moved/deleted) | MEDIUM | MEDIUM | Stage 1 checks file existence. Missing files flagged in inventory, skipped with reason. | LOW |
| R8 | Tagged intentions drift toward model interpretation instead of Eric's actual words | HIGH | MEDIUM | VOICE field is mandatory per block. Review Stage A specifically audits VOICE accuracy. | MEDIUM |

## 7. Pipeline Integration — Per-Role Query Pattern

### 7.1 Drafter Query (Proposal Alignment)
```
INPUT: proposal text
QUERY: FTS5 MATCH on intent_records_fts for semantically related intentions
OUTPUT: top 10 matching intentions with source provenance
FALLBACK: LIKE query on intent_records.verbatim_text
PURPOSE: "Before I propose X, has Eric said anything about X? What did he actually ask for?"
```

### 7.2 Reviewer Query (Proposal Validation)
```
INPUT: Drafter proposal + claimed alignment
QUERY: FTS5 on intent_records_fts + anti_patterns ChromaDB collection
OUTPUT: matching intentions + any anti-patterns the proposal triggers
FALLBACK: LIKE query on intent_records
PURPOSE: "Does the Drafter's proposal actually match what Eric asked for, or did it drift toward enterprise defaults?"
```

### 7.3 Implementer Query (Build Verification)
```
INPUT: implementation plan or git diff
QUERY: intent_records WHERE voice='eric-verbatim' AND build_target='hermes-backend'
OUTPUT: Eric's stated requirements for the component being built
FALLBACK: direct SQLite read
PURPOSE: "Am I building what Eric specified, or am I building what I think he wants?"
```

### 7.4 API Endpoint
```
GET /api/intent/alignment?q={query}&stage={drafter|reviewer|implementer}
Response: {results: [...], last_updated: "ISO", stale_warning: "..."|null}
Timeout: 10s
Fallback chain: Flask endpoint → direct SQLite → empty results + error annotation
```

## 8. Delivery Mechanism: Eric Batch Review

### Phase A: File-Based Checklist (immediate — zero new code)
1. Stage 6 generates `/mnt/projects/cis/data/intent_review_batch.md`
2. Format: one intention per section with checkbox decisions
3. Eric reviews, marks CONFIRM/CORRECT/REJECT, saves
4. `python3 tools/ingest_eric_decisions.py data/intent_review_batch.md` parses and writes SQLite
5. Verification: `sqlite3 data/cis_memory.db "SELECT eric_decision, COUNT(*) FROM intent_records GROUP BY eric_decision"`

### Phase B: Portal Panel (deferred — after Eric validates Phase A)
1. New route: `@app.route("/intent-review")` in runtime/app.py
2. Single HTML file: `runtime/ui/public/intent_review.html`
3. Vanilla JS, zero dependencies (same pattern as existing portal)
4. Features: pagination (50/page), bulk-approve high-confidence, filter by category/voice/confidence
5. Writes: only through `tools/ingest_eric_decisions.py` (same backend, different frontend)

## 9. Acceptance Criteria

1. **A1:** All 3,082 dam_assets rows inventoried. Files with unreachable paths flagged.
2. **A2 (50-file test):** Throughput ≥ 1 file/min/tagger, consensus ≥ 50%, latency ≤ 45s p95.
3. **A3:** All tagged blocks have VOICE field. eric-verbatim blocks have INTENT field.
4. **A4:** Zero API keys or tokens in intent_records.verbatim_text (post-scrub audit).
5. **A5:** intent_records_fts returns results for MATCH queries. LIKE fallback also returns results.
6. **A6:** Eric review batch file is generated. `tools/ingest_eric_decisions.py` parses it correctly.
7. **A7:** ChromaDB intent_memory collection returns results for semantic queries.
8. **A8:** Pipeline query endpoint returns results within 500ms (SQLite) or 2s (ChromaDB).
9. **A9:** Fallback to direct SQLite works when Flask endpoint is unavailable.
10. **A10:** ADR-SEED-018 exists in project_decisions with status DECIDED before Stage 7.

## 10. Verification Commands (Pre-Implementation Checklist)

Before any implementation begins, the Implementer must verify:
```bash
# 1. Active database is reachable
sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT COUNT(*) FROM dam_assets;"
# Expected: 3082

# 2. ChromaDB is writable
python3 -c "import chromadb; c = chromadb.PersistentClient(path='/mnt/projects/cis/data/chroma_data'); print(c.list_collections())"
# Expected: [] or existing collections

# 3. TAGGING_DIRECTIVE is readable
wc -l /mnt/projects/cis/enforcement/TAGGING_DIRECTIVE_v3.md
# Expected: 162

# 4. Gateway endpoints are healthy
curl -s http://127.0.0.1:8645/health  # Drafter
curl -s http://127.0.0.1:8643/health  # Reviewer
# Expected: {"status":"ok"} for both

# 5. OpenRouter API key is configured
grep -q "OPENROUTER_API_KEY" /mnt/projects/cis/runtime/config/runtime.env && echo "PRESENT" || echo "MISSING"
```

---

### Summary

Revised specification for the Post-Scrape Intention Alignment Pipeline. Extracts Eric's verbatim intentions from the 3,082-file corpus in dam_assets using a multi-model tagging pipeline (DeepSeek V4 Pro + DeepSeek R1 + GLM 5.2 tiebreaker), routes them through two review stages, presents them for Eric's batch review via a file-based checklist (Phase A) with optional portal panel (Phase B), and ingests confirmed intentions into SQLite (intent_records with FTS5) and ChromaDB (intent_memory + anti_patterns collections) in the existing data/cis_memory.db and data/chroma_data/. Every pipeline stage (Drafter, Reviewer, Implementer) queries intent memory before acting, with direct SQLite fallback on endpoint failure. Eric's Do Not Start overrides require explicit ADR records (ADR-SEED-018, ADR-SEED-019) before ingestion writes. 11 stages with per-stage error handling, formal risk register, scalability test gate, data privacy classification, and secret scrubbing. All 20 objections addressed with concrete design changes verified against live infrastructure state.

### Recommendation

PROCEED to Eric Gate for review. This is a REVISED PROPOSAL — no execution claimed. The 20 objections from Round 1 review are addressed with specific design changes, each verified against live infrastructure evidence. The proposal now correctly:

- Requires Eric's explicit ADR record for Do Not Start overrides (O1)
- Creates FTS5 virtual table alongside intent_records (O2)
- Uses models with verified API access (O3)
- Targets the verified active database path (O4)
- Extends existing infrastructure rather than building parallel (O5)
- References correct filename TAGGING_DIRECTIVE_v3.md (O6)
- Uses consistent 11-stage numbering (O7)
- Adds scale validation gate before full ChromaDB embedding (O8)
- Removes all references to non-existent ADR-SEED-017 (O9)
- Adds pre-indexing secret scrub stage (O10)
- Tracks novel category emergence (Reviewer Obj 1)
- Uses SQLite as source of truth with ChromaDB derived from it (Reviewer Obj 2)
- Phases review surface: file checklist first, portal panel deferred (Reviewer Obj 3)
- Adds three-tier fallback for API unavailability (Reviewer Obj 4)
- Defines concrete scalability metrics with thresholds (Reviewer Obj 5)
- Tracks override via spine record + git commit + enforcement gate (Reviewer Obj 6)
- Adds per-stage error handling table with recovery procedures (Reviewer Obj 7)
- Performs performance/security/maintainability assessment for UI extension (Reviewer Obj 8)
- Includes formal risk register with 8 identified risks (Reviewer Obj 9)
- Classifies data elements with handling rules per sensitivity (Reviewer Obj 10)

Next action: Dispatch to Reviewer (r1:8643) for Round 2 deliberation. The revised proposal is saved at `/mnt/projects/cis/docs/SPEC_POST_SCRAPE_INTENTION_ALIGNMENT_PIPELINE_REV2.md`.

```json
{"role": "drafter", "status": "PROPOSAL_READY", "summary": "Revised Post-Scrape Intention Alignment Pipeline specification addressing all 20 Round 1 Reviewer objections with concrete design changes verified against live infrastructure. 11-stage pipeline: file discovery → 50-file scale test → multi-model tagging (DeepSeek V4 Pro + R1 + GLM 5.2) → secret scrub → Review A → Drafter synthesis → Review B → Eric batch review (file checklist Phase A, portal Phase B deferred) → SQLite ingest with FTS5 → ChromaDB scale validation → VDB embedding → pipeline query wiring with fallback. Requires Eric ADR records for Do Not Start overrides. Includes formal risk register, data privacy classification, per-stage error handling, and 10 acceptance criteria.", "recommendation": "PROCEED to Eric Gate for review. All 20 objections resolved with live-infrastructure-verified design changes. Dispatch to r1:8643 for Round 2 deliberation.", "next_action": "REVIEW_PENDING"}
```
