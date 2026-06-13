# Tier 9 — Chroma/VDB Specification
## Specification Document v1.0

## Eric Gate Status: PENDING_APPROVAL

This document defines the architectural direction for Tier 9. It is **NOT** an
implementation directive. No code shall be written, no spine rows modified, and no
files staged under this document alone. Implementation proceeds only after Eric
Gate approval is recorded.

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-13
**Status:** DRAFT — awaiting Eric Gate review
**Gating dependency:** Tier 8 (MCP Bridge) must be COMPLETE per dependency graph

---

## 1. Purpose

### 1.1 What Tier 9 solves

Eric's long-term goal, stated in his own words: "build a knowledge base in the
sqlite db that will vectorized and saved to a vdb." The CIS project has already
imported 3,071 Hermes session files into the SQLite spine with FTS5 full-text
search (Tier 7.5b). But FTS5 is lexical only — it matches words, not meaning.

Current limitations of FTS5-only search:

- **Lexical, not semantic.** Searching for "how did we handle client intake forms"
  finds only exact word matches. Sessions that discuss "admission paperwork" or
  "new client registration" are missed even though they discuss the same concept.
- **No relevance ranking.** FTS5 returns matches in insertion order. There is no
  way to say "show me the most relevant results first."
- **No cross-document similarity.** FTS5 cannot answer "find sessions similar to
  this proposal" or "what else is related to this decision."

Tier 9 adds a Chroma vector database that indexes the existing DAM content
(session messages, research artifacts, proposals, review rounds) as embeddings.
This enables semantic search — finding sessions by meaning, not just by keyword.

### 1.2 Core capability

> **A local Chroma vector database that indexes existing CIS content (session
> archives, deliberation rounds, project decisions) as embeddings, exposed via a
> read-only MCP retrieval tool. Semantic search complements FTS5 lexical search —
> both are available. Retrieval results flow through the existing WorkIntent →
> Process Manager → Human Approval Gate pipeline. No write access to spine.**

### 1.3 What changes for the operator (Eric)

| Before Tier 9 | After Tier 9 |
|---------------|--------------|
| Search sessions by keyword only (FTS5) | Search sessions by meaning (semantic + keyword) |
| "What did I say about client intake?" returns only exact phrase matches | Returns sessions about admission, registration, intake forms — same concept, different words |
| No relevance ranking — results in insertion order | Results ranked by semantic relevance |
| Can't find "sessions similar to this one" | Similarity search: "find me more like this" |
| FTS5 only | Both FTS5 (lexical) and Chroma (semantic) available via MCP Bridge |

---

## 2. Data Scope

### 2.1 What data SHALL be embedded/indexed

| Source | Table(s) | Content to embed | Purpose |
|--------|----------|-----------------|---------|
| DAM session messages | `dam_extracted_text` | User messages from Hermes session archives (already imported, 3,071 sessions) | Recover Eric's own words about app logic, client schedules, assessments, recovery plans |
| Deliberation rounds | `deliberation_rounds` | Drafter proposals and Reviewer feedback text | Find prior design reasoning and decisions |
| Project decisions | `project_decisions` | ADR-SEED-* decision text and labels | Trace architectural decision lineage |
| Session closeouts | `session_closeouts` | Failure summaries and log paths | Find prior failure patterns and resolutions |

### 2.2 What data SHALL NOT be embedded/indexed

| Excluded | Reason |
|----------|--------|
| API keys, tokens, secrets, .env values | Privacy/security — never leave the local filesystem in plaintext |
| Raw SQLite spine tables (build_plan_nodes structure, workflow_runs metadata) | These are queried directly via MCP Bridge (Tier 8). Embedding structural metadata adds no value. |
| Full deliberation round bodies (only summaries/indexable text) | The full JSON bodies are available via `cis_get_run_detail` (Tier 8). Embedding the full JSON would be noisy. |
| Binary files, images, PDF attachments | Out of scope for Tier 9. Text-only embedding. |
| SWA project data | Tier 9 serves CIS only per the per-project isolation model (ADR-SEED-010). SWA gets its own VDB later. |
| Git history, commit messages, diff contents | These are queried via git, not Chroma. |

### 2.3 Privacy and secret constraints

- Embedding is performed **locally** using an on-device embedding model (e.g.,
  `all-MiniLM-L6-v2` via `sentence-transformers`). No text leaves the machine.
- No API keys, tokens, or external service credentials are used.
- Chroma stores vectors on the local filesystem at a configurable path
  (`CIS_CHROMA_PATH` environment variable, default
  `/mnt/projects/cis/data/chroma_data`).
- The embedding model is downloaded once and cached locally. No runtime network
  calls.
- No secret-bearing fields (`API_KEY`, `TOKEN`, `PASSWORD`) are included in the
  embedding pipeline or indexed content.

---

## 3. Out of Scope

### 3.1 Explicitly not part of Tier 9

| Item | Reason |
|------|--------|
| Write operations to spine | Mutations go through Process Manager → Eric Gate. Chroma is read-only retrieval. |
| Real-time indexing | Indexing is a batch operation run at closeout or on demand. Not continuous. |
| SWA project data | Per ADR-SEED-010, projects are isolated. SWA gets its own VDB later. |
| Multi-modal embeddings (images, audio) | Text-only for Tier 9. |
| Hybrid search fusion (combining FTS5 + Chroma scores) | Tier 9 provides both tools separately. Fusion logic is a future enhancement. |
| Chroma as a shared service | Chroma runs embedded in the same process as the MCP Bridge. No separate server process. |
| External API-based embeddings (OpenAI, Cohere) | All embedding is local. No external API calls. |
| Auto-indexing on state change | Index rebuild is manual/closeout-triggered. Not event-driven. |
| Tier 10 CIS UI | Gated on Tier 9. Not built here. |
| Tier 8 MCP Bridge modification | Tier 9 adds a new MCP tool to the existing bridge. Does not change existing tools. |

---

## 4. Relationship to Tier 8 MCP Bridge

### 4.1 Where Chroma sits in the architecture

```
┌──────────────────────────────────────────────────────┐
│  Hermes Profile (e.g., V4 Drafter on port 8645)      │
│                                                      │
│  MCP Tools available:                                │
│    mcp_cis_get_current_phase()    (Tier 8)           │
│    mcp_cis_get_build_status()     (Tier 8)           │
│    mcp_cis_search_sessions()      (Tier 8 — FTS5)    │
│    mcp_cis_search_semantic()      (Tier 9 — NEW)     │
│    mcp_cis_get_similar()          (Tier 9 — NEW)     │
└──────────────────────┬───────────────────────────────┘
                       │ stdio (MCP protocol)
                       │
┌──────────────────────▼───────────────────────────────┐
│  cis_mcp_bridge/                                     │
│  ├── server.py          MCP server (Tier 8)           │
│  ├── tools.py           + 2 new tools (Tier 9)       │
│  ├── spine.py           SQLite queries (Tier 8)      │
│  └── chroma_index.py    Chroma queries (Tier 9 NEW)  │
│                                                      │
│  Reads from:                                         │
│    ┌──────────────────┐    ┌──────────────────────┐  │
│    │ SQLite Spine     │    │ Chroma Vector DB     │  │
│    │ cis_memory.db    │    │ chroma_data/         │  │
│    └──────────────────┘    └──────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 4.2 Flow relationship

The Chroma layer is a **passive retrieval layer** — same architectural role as
the MCP Bridge queries:

1. **Before a workflow run**: Drafter calls `cis_search_semantic("client intake
   forms")` to find prior discussions about the same concept across different
   wordings.
2. **During deliberation**: Reviewer calls `cis_get_similar(run_id)` to find
   prior proposals similar to the current one, surfacing related decisions.
3. **After a workflow run**: Implementer calls `cis_search_semantic("build_plan
   migration")` to find prior migration patterns before implementing.
4. **Between sessions**: Eric or any profile searches the archive by meaning
   without needing the exact keywords.

### 4.3 What Chroma must NOT do in relation to the flow

- Must not classify intents, route work, or create WorkIntent objects
- Must not stage candidates, request approvals, or dispatch agents
- Must not participate in deliberation rounds
- Must not enforce state transition rules (that's the Process Manager)
- Must not gate on Eric approval (that's the Eric Gate)
- Must not generate FINAL_DIRECTIVE or FINAL_JSON blocks
- Must not write to the SQLite spine

### 4.4 New MCP tools (added to existing Tier 8 bridge)

| Tool Name | Returns | Purpose |
|-----------|---------|---------|
| `cis_search_semantic` | Top-K semantically relevant documents from the indexed corpus, with relevance scores | Find sessions by meaning, not keyword |
| `cis_get_similar` | Documents similar to a given document (by ID), with similarity scores | "Find me more like this" |

These are added to the existing 9 MCP tools from Tier 8. The bridge total
becomes 11 tools.

### 4.5 Existing MCP tools are unchanged

All 9 Tier 8 tools (`cis_get_current_phase`, `cis_get_build_status`,
`cis_get_next_actions`, `cis_get_recent_runs`, `cis_get_run_detail`,
`cis_get_open_decisions`, `cis_get_open_questions`, `cis_get_eric_gate_status`,
`cis_search_sessions`) continue to function identically. `cis_search_sessions`
remains the FTS5 lexical search tool. `cis_search_semantic` is the new semantic
search tool. Both are available — they serve different query types.

---

## 5. Retrieval Results Flow Through CIS Pipeline

### 5.1 How retrieval results are used

Retrieval results from Chroma are **context only** — they are injected into the
profile's session context (like AGENTS.md is today) but do not trigger actions:

1. Profile calls `cis_search_semantic("social worker intake process")`
2. Chroma returns top-10 relevant document excerpts with source references
3. Profile reads the results as context for the current task
4. If the profile wants to act on a result (e.g., "open the session where I
   described the intake form logic"), it creates a WorkIntent through the
   normal pipeline

### 5.2 Retrieval does NOT bypass the pipeline

```
Profile calls cis_search_semantic("...")
  │
  ▼
Chroma returns results → injected as context into session
  │
  ▼
Profile reads context, decides to act
  │
  ▼
WorkIntent created (normal Process Manager flow)
  → Content-Based Router
  → Domain Adapter
  → Process Manager (state machine)
  → Human Approval Gate
  → Dispatch / Dead Letter
```

- Chroma retrieval is a **context operation**, not a pipeline trigger
- The Process Manager, Human Approval Gate, and Dead Letter handling are **never
  bypassed** by retrieval
- Retrieval results are evidence, not directives
- The Eric Gate is required for any mutation that follows from retrieval

### 5.3 Truth authority

Per the dependency graph: "Truth flows from verified pipeline runs, not semantic
search." Chroma is a discovery tool. The authoritative source of truth is:

1. The SQLite spine (build_plan_nodes, project_decisions, workflow_runs)
2. Git history (commits, diffs)
3. Verified pipeline run outputs

Chroma search results are suggestions, not determinations. They help find
relevant context but do not replace verified state.

---

## 6. Minimum Architecture

### 6.1 Component diagram

```
┌──────────────────────────────────────────────────────┐
│  cis_mcp_bridge/chroma_index.py     (NEW — Tier 9)   │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  EmbeddingPipeline                             │  │
│  │  - Loads sentence-transformers model           │  │
│  │  - Embeds text from dam_extracted_text,        │  │
│  │    deliberation_rounds, project_decisions,     │  │
│  │    session_closeouts                           │  │
│  │  - Batched, incremental (skip already-indexed) │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │                              │
│  ┌────────────────────▼───────────────────────────┐  │
│  │  ChromaClient                                  │  │
│  │  - Persistent Chroma collection at             │  │
│  │    CIS_CHROMA_PATH                             │  │
│  │  - Query by text (embed query → search)        │  │
│  │  - Query by ID (get similar documents)         │  │
│  │  - Returns (id, text, metadata, score) tuples  │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │                              │
│  ┌────────────────────▼───────────────────────────┐  │
│  │  Tool Handlers (added to tools.py)             │  │
│  │  - cis_search_semantic(query, top_k)           │  │
│  │  - cis_get_similar(document_id, top_k)         │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 6.2 Technology choices

| Choice | Rationale |
|--------|-----------|
| **Chroma** | Python-native, local, open-source vector database. No server process — runs embedded. Persistent storage on disk. |
| **sentence-transformers / all-MiniLM-L6-v2** | Lightweight (80MB), fast, runs on CPU. No GPU required. Proven for semantic search. Available via `pip install sentence-transformers`. |
| **Embedded mode** | Chroma runs in-process with the MCP Bridge. No separate Chroma server to manage. |
| **Incremental indexing** | Documents are indexed once and tracked by source row ID. Re-indexing only adds new or changed documents. |
| **CIS_CHROMA_PATH env var** | Configurable storage path. Default: `/mnt/projects/cis/data/chroma_data`. |

### 6.3 Files to create

| File | Purpose |
|------|---------|
| `runtime/mcp_bridge/chroma_index.py` | Embedding pipeline + Chroma client + query functions |
| `runtime/mcp_bridge/py.typed` | PEP 561 marker (optional, for type checkers) |

### 6.4 Files to modify

| File | Change |
|------|--------|
| `runtime/mcp_bridge/tools.py` | Add 2 tool definitions + 2 handler functions |
| `runtime/mcp_bridge/server.py` | No changes — tools are auto-registered from TOOLS list |

### 6.5 New Python dependency

| Package | Version | Purpose |
|---------|---------|---------|
| `chromadb` | >=0.4.0 | Vector database |
| `sentence-transformers` | >=2.2.0 | Local embedding model |

These are installed in the Hermes Agent venv:
```
~/.hermes/hermes-agent/venv/bin/pip install chromadb sentence-transformers
```

### 6.6 No new database tables

Tier 9 does not add tables to the SQLite spine. It reads existing tables and
writes vectors to Chroma's own persistent storage on disk (separate from SQLite).

---

## 7. Required Schemas, Files, and Services

### 7.1 No new SQLite tables

| Data Source | Existing Table | Read by Chroma |
|-------------|---------------|----------------|
| Session messages | `dam_extracted_text` | Yes — embed user messages |
| Deliberation rounds | `deliberation_rounds` | Yes — embed drafter proposals |
| Project decisions | `project_decisions` | Yes — embed decision text |
| Session closeouts | `session_closeouts` | Yes — embed failure summaries |

### 7.2 Chroma collection schema

One Chroma collection per data source:

| Collection Name | Source Table | Embedding Content | Metadata |
|-----------------|-------------|-------------------|----------|
| `cis_sessions` | `dam_extracted_text` | `content` field (user messages) | `source_table`, `source_id`, `speaker`, `session_file` |
| `cis_deliberations` | `deliberation_rounds` | `drafter_output` field | `source_table`, `source_id`, `run_id`, `round_number` |
| `cis_decisions` | `project_decisions` | `decision` + `label` fields | `source_table`, `source_id`, `decision_id` |
| `cis_closeouts` | `session_closeouts` | `failure_summary` field | `source_table`, `source_id`, `log_path` |

### 7.3 Directory structure

```
/mnt/projects/cis/
├── data/
│   ├── cis_memory.db          (SQLite spine — Tier 4)
│   └── chroma_data/           (NEW — Tier 9)
│       └── chroma.sqlite3     (Chroma's internal SQLite)
└── runtime/
    └── mcp_bridge/
        ├── __init__.py
        ├── server.py           (Tier 8)
        ├── tools.py            (Tier 8 + 2 new tools)
        ├── spine.py            (Tier 8 — unchanged)
        └── chroma_index.py     (NEW — Tier 9)
```

### 7.4 No new services

Chroma runs embedded in the MCP Bridge process. No separate Chroma server, no
systemd service, no network listener.

---

## 8. Security and Approval Boundaries

### 8.1 Environment isolation

Same as Tier 8 (§6.1). The MCP Bridge subprocess inherits only safe baseline
variables. `CIS_CHROMA_PATH` is explicitly added via `mcp_servers.cis.env`.

### 8.2 Database access

- SQLite spine remains read-only (Tier 8 enforcement unchanged)
- Chroma data is read/write within the bridge process (for index building), but
  exposed through readonly MCP tools (query only)
- No SQLite write operations from Tier 9 code

### 8.3 Embedding model security

- `sentence-transformers` loads the model from local cache after first download
- The model download is a one-time operation. After that, no network access is
  needed for embedding
- Model files are stored in the standard HuggingFace cache (`~/.cache/huggingface`)
- The model is open-source and auditable (all-MiniLM-L6-v2, MIT license)

### 8.4 No network access for embedding or search

- Embedding: local model, no API calls
- Indexing: reads local SQLite, writes local Chroma storage
- Search: queries local Chroma, returns local results
- Zero outbound connections for runtime operations

### 8.5 No secrets, no credentials

- No API keys in embedding pipeline code
- No authentication tokens for Chroma (embedded mode, localhost only)
- No environment variable leakage (same MCP env filtering as Tier 8)

### 8.6 Approval boundaries

- Chroma tools are **read-only retrieval** — they do not trigger Eric Gate review
- Retrieval results are **context**, not directives
- Any mutation following from retrieval requires full WorkIntent → Process
  Manager → Eric Gate pipeline
- Chroma does not bypass the Eric Gate

---

## 9. Deterministic Acceptance Criteria

### 9.1 Functional acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| A1 | Semantic search returns results | `cis_search_semantic("client intake")` | Returns top-K documents with relevance scores > 0 | Compare against known corpus content |
| A2 | Semantic search relevance | Search for "admission paperwork" | Finds sessions about "client intake", "registration", "new client" — related concepts | Manual relevance spot-check |
| A3 | Get similar documents | `cis_get_similar(document_id)` | Returns documents with similarity scores, excluding the query document itself | Verify query doc not in results |
| A4 | FTS5 still works | `cis_search_sessions("client intake")` | Returns exact keyword matches (unchanged from Tier 8) | Regression test |
| A5 | All 9 Tier 8 tools still work | Call each existing MCP tool | All return correct results, no regressions | Full regression suite |
| A6 | Empty query handled | `cis_search_semantic("")` | Returns graceful error, not crash | Error handling test |
| A7 | Index is idempotent | Run index build twice | Second run reports 0 new documents indexed | Idempotency test |
| A8 | Metadata preserved | Search returns document with metadata | Result includes `source_table`, `source_id`, `session_file` or equivalent | Metadata verification |
| A9 | Collection exists after index | Query Chroma directly | All 4 collections exist with document counts matching source rows | Chroma native query |

### 9.2 Security acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| S1 | No write to SQLite spine | Search and index operations | Zero INSERT/UPDATE/DELETE on cis_memory.db | Audit via gate_mcp_readonly.py |
| S2 | No network imports in chroma_index.py | Scan source | No `socket`, `http`, `urllib.request`, `requests`, `httpx`, `aiohttp` | gate_mcp_no_network.py |
| S3 | No secrets in embedding pipeline | Scan source | No `API_KEY`, `TOKEN`, `SECRET`, `PASSWORD` | Security grep |
| S4 | Chroma path configurable | Set `CIS_CHROMA_PATH=/tmp/test_chroma` | Index and search use the configured path | Env var test |
| S5 | Search does not return raw secrets | Index includes a test doc with fake key | Search result excludes or redacts `sk-...` patterns | Secret filtering test |

### 9.3 Integration acceptance tests

| # | Test | Input | Expected Output | Verification |
|---|------|-------|-----------------|--------------|
| I1 | Embedded Chroma starts without server | Import chroma_index | No separate Chroma process running | `ps aux | grep chroma` returns only the bridge |
| I2 | Index builds from live data | Run index on production cis_memory.db | Collections created with document count > 0 | Chroma native count query |
| I3 | MCP tools discoverable | Start Hermes with cis MCP config | `mcp_cis_search_semantic` appears in tool list | MCP tool registration log |
| I4 | Concurrent read safety | Two profiles query simultaneously | Both get correct results, no locking errors | Concurrent Chroma read test |
| I5 | Incremental index add | Add new document, re-index | Only the new document is indexed, existing docs unchanged | Diff collection count |

---

## 10. Required Tests and Gates Before Implementation

### 10.1 Pre-implementation gates (must pass before code is written)

| Gate | Type | Purpose |
|------|------|---------|
| Tier 8 COMPLETE | Dependency | MCP Bridge must be verified complete |
| Chroma package installed | Dependency | `~/.hermes/hermes-agent/venv/bin/python -c "import chromadb"` succeeds |
| sentence-transformers installed | Dependency | `~/.hermes/hermes-agent/venv/bin/python -c "import sentence_transformers"` succeeds |
| DAM data exists | DB state | `SELECT COUNT(*) FROM dam_extracted_text` > 0 |
| Chroma storage dir writable | Filesystem | `CIS_CHROMA_PATH` directory exists and is writable |

### 10.2 Post-implementation verification gates

| Gate | Type | Purpose |
|------|------|---------|
| `gate_mcp_readonly.py` | Security | Verify no write SQL in Tier 9 code (reuse Tier 8 gate) |
| `gate_mcp_no_network.py` | Security | Verify no network imports in chroma_index.py (reuse Tier 8 gate) |
| `gate_chroma_tool_a1.sh` through `gate_chroma_tool_a9.sh` | Functional | One gate per acceptance test A1-A9 |
| `gate_chroma_security_s1.sh` through `gate_chroma_security_s5.sh` | Security | One gate per security test S1-S5 |
| `gate_chroma_tools_registered.sh` | Functional | Confirm 11 tools total (9 Tier 8 + 2 Tier 9) appear at startup |
| `gate_chroma_index_healthy.py` | Functional | Confirm Chroma collections exist and are queryable |

### 10.3 Test file structure

```
/mnt/projects/cis/
├── tests/
│   └── mcp_bridge/
│       ├── test_chroma_index.py      # Unit tests for Chroma queries
│       ├── test_chroma_security.py   # Security boundary tests
│       └── test_chroma_integration.py # Integration tests
└── tools/
    └── gates/
        ├── gate_chroma_index_healthy.py
        ├── gate_chroma_tool_a1.sh through gate_chroma_tool_a9.sh
        ├── gate_chroma_security_s1.sh through gate_chroma_security_s5.sh
        └── gate_chroma_tools_registered.sh
```

---

## 11. Eric Gate Approval Required Before Implementation

### 11.1 Gating conditions

Tier 9 implementation shall not begin until ALL of:

| # | Condition | Verification |
|---|-----------|-------------|
| 1 | Tier 8 (MCP Bridge) status = COMPLETE | `SELECT status FROM build_plan_nodes WHERE node_label = 'Tier 8 — MCP Bridge'` |
| 2 | Eric Gate approval recorded for **this specification** | This document approved by Eric |
| 3 | Chroma and sentence-transformers packages installed in Hermes venv | `pip list | grep chromadb` and `pip list | grep sentence-transformers` |
| 4 | DAM data exists and is accessible | `SELECT COUNT(*) FROM dam_extracted_text` >= 1000 |
| 5 | Eric explicitly issues PROCEED or IMPLEMENT for Tier 9 | Not automatic |

### 11.2 What happens after approval

1. Tier 9 status moves from PENDING → IN_PROGRESS
2. Chroma packages installed (if not already)
3. Implementation follows the build plan in §12
4. Verification gates (§10.2) run after implementation
5. Tier 9 status moves to COMPLETE only after all gates pass AND Eric approves
   the completion closeout

### 11.3 What happens if approval is withheld

- Tier 9 remains PENDING
- This specification document is revised per Eric's direction
- Resubmitted for Eric Gate review
- Tier 10 (CIS UI) remains BLOCKED

---

## 12. Phased Build Plan

### 12.1 Build nodes

| Node | Label | Depends On | Scope |
|------|-------|-----------|-------|
| Tier 9.1 | Chroma — dependency installation | Eric Gate on this spec | Install `chromadb` and `sentence-transformers` in Hermes venv. Verify imports. |
| Tier 9.2 | Chroma — embedding pipeline | Tier 9.1 | Implement `chroma_index.py`: embedding pipeline, Chroma client, index-from-spine function. Unit tests with small test corpus. |
| Tier 9.3 | Chroma — MCP tool integration | Tier 9.2 | Add `cis_search_semantic` and `cis_get_similar` to `tools.py`. Wire to chroma_index query functions. |
| Tier 9.4 | Chroma — index build | Tier 9.3 | Run full index build against production `cis_memory.db`. Verify collections created. |
| Tier 9.5 | Chroma — security gates | Tier 9.4 | Run all security gates: no write SQL, no network, no secrets. |
| Tier 9.6 | Chroma — acceptance test suite | Tier 9.5 | Run all functional and integration acceptance tests (A1-A9, I1-I5). |
| Tier 9.7 | Chroma — closeout | Tier 9.6 | Verify all gates pass. Record evidence. Regenerate exports. Request Eric Gate closeout. |

### 12.2 What each node does NOT include

| Node | Exclusions |
|------|------------|
| 9.1 | No code written. Dependency check only. |
| 9.2 | No MCP tool integration. No profile config changes. |
| 9.3 | No full index build. No security scanning. |
| 9.4 | No new features. Index build only. |
| 9.5 | No new features. Security scanning only. |
| 9.6 | No new features. Acceptance testing only. |
| 9.7 | No new features. Verification + documentation only. |

---

## 13. Recommendation

**Approve this specification as the architecture basis for Tier 9.**

Tier 9 is the natural next step after the MCP Bridge: it adds semantic search
on top of the existing archive infrastructure. It is read-only, local,
secrets-free, and does not bypass the Eric Gate or Process Manager. It uses
Chroma (open-source, embedded, Python-native) with a lightweight local embedding
model (all-MiniLM-L6-v2, 80MB, CPU-only).

The build is phased into 7 small, gated nodes, each independently verifiable
before the next begins. The existing FTS5 search (`cis_search_sessions`) remains
unchanged — semantic search is additive, not replacement.

---

## Appendix A: Evidence References

### A.1 Current build state

```
COMMAND: sqlite3 data/cis_memory.db "SELECT node_label, status FROM build_plan_nodes WHERE node_label IN ('Tier 8 — MCP Bridge', 'Tier 9 — Chroma/VDB', 'Tier 10 — CIS UI / Custom Display Views') ORDER BY id;"
OUTPUT:
Tier 8 — MCP Bridge|COMPLETE
Tier 9 — Chroma/VDB|PENDING
Tier 10 — CIS UI / Custom Display Views|BLOCKED
```

### A.2 DAM data availability

```
COMMAND: sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM dam_assets;"
OUTPUT: 3082
```

### A.3 Eric's seed intent (verbatim)

```
Source: session_20260520_215551_16187f.json
> I then was to build a knowledge base in the sqlite db that will vectorized
> and saved to a vdb.
```

### A.4 Dependency graph (Tier 9)

```
From docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md §Tier 9:
Chroma indexes collab session messages, research artifacts, proposals, and
review rounds. Retrieval only — never writes to spine. Truth flows from
verified pipeline runs, not semantic search.
```

---

*End of Tier 9 Chroma/VDB Specification v1.0*
*Status: DRAFT — awaiting Eric Gate review*
*Next step: Eric reads → approves specification → Tier 9 IN_PROGRESS → IMPLEMENT*
