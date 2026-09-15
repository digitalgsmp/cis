# Advisor review — kb-near-real-time-ingest

- packet: `reviews/pending/kb-near-real-time-ingest.md`
- advisor: evaluator on port 8650
- run tag: kb-near-real-time-ingest @ 2026-09-13T12:28:00-05:00
- at: 2026-09-13T12:34:13
- prompt_tokens: 337830
- completion_tokens: 3854
- total_tokens: 341684
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

Eric directed this in the current session (2026-09-13), verbatim in the proposal. A live operator directive supersedes queue ordering regardless of what the build list says is next. The problem is real and immediately verifiable: reviewers querying `knowledge_messages` cannot see current-session content because ingestion only runs at closeout.

---

**Verified claims:**

1. **`ingest_sessions.py` writes `knowledge_messages`, no Chroma** — Confirmed. The tool at `tools/catalog/ingest_sessions.py` (153 lines) does `INSERT INTO knowledge_messages` and `INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')`. No Chroma import anywhere in the file.

2. **`sweep.py` writes `memory_records`, NOT `knowledge_messages`** — Confirmed. `runtime/memory/sweep.py` (57 lines) calls `session_sweep` from `memory_store.py` and reports `memory_records` and `chroma_vectors` counts. It never touches `knowledge_messages`.

3. **`sync_missing_embeddings.py` holds `chroma_write` lock** — Confirmed. Line: `with chroma_write(what="sync_missing_embeddings"):` wraps the entire batch loop. This is the ~15-minute blocker the proposal correctly identifies.

4. **`knowledge_messages` schema** — Confirmed via `PRAGMA table_info`: id, role, content, source, source_key, timestamp, created_at. Dedup is by `source_key` (the ingest tool checks `if source_key in existing`).

5. **Idempotency** — Confirmed. `ingest_sessions.py` builds an `existing` set from `SELECT DISTINCT source_key FROM knowledge_messages` and skips any chunk whose key is already present.

**Unverified claim:**

- `tools/closeout.sh:212` as the sole invocation site — I could not read past line ~60 of the 394-line file (output truncation). The claim is plausible given the tool directory structure, but I did not confirm the exact line.

---

**Technical gaps the proposal must resolve before implementation:**

**G1. FTS5 rebuild is not incremental.** The ingest tool executes `INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')` — a full index rebuild on every invocation, not an append. On a table with tens of thousands of rows, this is not "seconds." The proposal claims the FTS side takes seconds; that claim holds only if the rebuild is replaced with row-level FTS5 triggers or an incremental update path. The proposal must specify whether the pre-dispatch ingest uses the existing tool as-is (---

**REVIEW COMPLETE**

**FRAME: RIGHT_WORK** — Eric directed this live in the current session (2026-09-13). The problem is real and immediately blocks reviewer verification.

**Verified:**
- `ingest_sessions.py` writes `knowledge_messages` + FTS5, no Chroma (tools/catalog/ingest_sessions.py:153 lines)
- `sweep.py` writes `memory_records`, NOT `knowledge_messages` (runtime/memory/sweep.py:57 lines)
- `sync_missing_embeddings.py` holds `chroma_write` lock for entire batch (tools/sync_missing_embeddings.py:line ~68)
- `cis_search_knowledge` queries both `knowledge_messages` FTS5 AND Chroma vectors (runtime/mcp_bridge/spine.py:344-386 FTS, 450+ semantic)
- Reviewers in readonly mode get `cis_search_knowledge` tool (runtime/mcp_bridge/tools.py:42 in READONLY_TOOL_NAMES)
- Dedup by `source_key` is implemented (ingest_sessions.py:lines ~70-75)

**Critical gap the proposal must resolve:**

The existing `ingest_sessions.py` executes a **full FTS5 rebuild** on every invocation (line 139: `INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')`). This is not incremental. On a table with tens of thousands of rows, this is not "seconds" — it's minutes. The proposal's constraint 5 ("ingest should be fast, seconds for the FTS side") cannot be met by calling the existing tool as-is.

**The implementation must either:**
1. Replace the full rebuild with FTS5 triggers (automatic incremental updates on INSERT), OR
2. Write a new delta-only ingest path that uses `INSERT INTO knowledge_messages_fts(rowid, content)` for each new row instead of rebuild, OR
3. Skip FTS5 update at pre-dispatch and rely only on the LIKE fallback in spine.py:374 for immediate freshness, rebuilding FTS5 at closeout only.

The proposal does not specify which path. This must be decided before implementation begins, because option 3 changes the contract (FTS5 stale but LIKE fresh) while options 1-2 require schema or tool changes.

**Open questions O1-O3 are correctly identified.** O1 answer: `cis_search_knowledge` reads BOTH stores (FTS5 + Chroma), so both need updating for full coverage. O2 answer: reviewers need both for verification (FTS for exact directive text, vectors for semantic recall). O3 answer is sound (proceed with stale row, second-chance at verdict).

**Recommendation:** Approve the work item with one amendment — the implementation spec must specify the FTS5 incremental strategy before code begins, because the existing tool's full-rebuild approach violates constraint 5.
