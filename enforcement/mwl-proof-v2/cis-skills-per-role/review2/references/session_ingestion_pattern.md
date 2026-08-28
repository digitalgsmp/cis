# Session Ingestion Pattern

## What It Does
Ingests Hermes session transcripts from all profile directories into the CIS knowledge base (`knowledge_messages` table + FTS5 index).

## Script Location
`tools/catalog/ingest_sessions.py`

## How It Works

1. **Scan all profile session directories**:
   - `~/.hermes/sessions/` (prime)
   - `~/.hermes-v4pro/sessions/` (draft)
   - `~/.hermes-v4impl/sessions/` (menter)
   - `~/.hermes-r1/sessions/` (review1)
   - `~/.hermes-glm-reviewer/sessions/` (review2)
   - `~/.hermes-brainstorm/sessions/` (brain)
   - `~/.hermes-qwen/sessions/` (qwen — legacy)
   - `~/.hermes-glm-verifier/sessions/` (verify)

2. **Filter by recency** — default 30 days via `DAYS_BACK` constant

3. **Extract messages** — only `user` and `assistant` roles, skip tool output. Content >10 chars only.

4. **Chunk at 4000 chars** — split at newlines when possible, not mid-word

5. **Deduplicate by source_key** — format: `hermes_session/<profile>/<session_id>/<chunk_index>`. If first chunk (`/0`) already exists, skip the entire session.

6. **Batch insert** — 500 messages per batch into `knowledge_messages` table

7. **Rebuild FTS5 index** — `INSERT INTO knowledge_messages_fts(knowledge_messages_fts) VALUES('rebuild')`

## Running

```bash
cd /mnt/projects/cis
python3 tools/catalog/ingest_sessions.py
```

## Re-running
Safe to re-run. Deduplication by source_key means already-ingested sessions are skipped. Only new sessions since last run get ingested.

## Stats (2026-07-08 run)
- 1,514 sessions processed across 7 profiles
- 10,650 new messages inserted
- KB total: 298,298 messages
- FTS5 index rebuilt successfully

## Schema

```sql
-- knowledge_messages (existing table)
CREATE TABLE knowledge_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,          -- "session" for ingested sessions
    content TEXT NOT NULL,       -- chunked session text
    source TEXT NOT NULL,        -- "hermes_<profile>" e.g. "hermes_prime"
    source_key TEXT,             -- "hermes_session/<profile>/<session_id>/<chunk>"
    timestamp TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

## Extending to ChromaDB
The existing `tools/catalog/build_embeddings.py` script can be run after ingestion to build ChromaDB embeddings for the new messages. It reads all `knowledge_messages` rows and embeds them. Note: it currently deletes and recreates the entire collection, which is slow for 298K messages. For incremental updates, a targeted embedding script would be needed.
