# Knowledge Base Schema Gaps

Discovered 2026-07-08 during a Verify session. The pre-discovery
search in pipeline_relay.py failed with "no such column: source_key".

## The Bug

`pipeline_relay.py` line 230 queries the FTS5 virtual table directly:

```python
# WRONG — source_key is not a column in the FTS5 virtual table
cur = conn.execute(
    "SELECT content, source, source_key FROM knowledge_messages_fts "
    "WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT 5",
    (keywords,)
)
```

FTS5 virtual tables only expose columns declared in the
`CREATE VIRTUAL TABLE` statement. The `source_key` column lives on
the base `knowledge_messages` table, not on `knowledge_messages_fts`.

The correct pattern (already used in `spine.py` line 348 and
`intent.py` line 83) is to JOIN the FTS5 table to the base table:

```python
# CORRECT — join FTS5 results back to base table for non-indexed columns
rows = conn.execute(
    """SELECT km.id, km.content, km.source, km.role, km.source_key
       FROM knowledge_messages km
       JOIN knowledge_messages_fts fts ON km.id = fts.rowid
       WHERE knowledge_messages_fts MATCH ?
       ORDER BY rank
       LIMIT ?""",
    (safe_query, limit)
).fetchall()
```

## Root Cause: Missing Table DDL

The `knowledge_messages` table and `knowledge_messages_fts` FTS5
virtual table have **no CREATE TABLE statement anywhere in the repo**.

Searched:
- `runtime/schema/spine_schema.sql` — no knowledge_messages
- `runtime/schema/migrations/` (16 migration files) — none reference it
- `tools/catalog/*.py` — all INSERT into it, none CREATE it
- `tools/catalog/convert_to_knowledge.py` — INSERTs and queries but no CREATE
- `tools/catalog/ingest_legacy.py` — same pattern

The table was created ad-hoc (likely by a deleted script or manual
sqlite3 command). This means:
1. The schema is not version-controlled
2. The FTS5 virtual table column list is unknown without introspecting the live DB
3. Any column could be missing without detection until query time

## How to Introspect the Live Schema

```bash
# Base table columns
sqlite3 /mnt/projects/cis/data/cis_memory.db "PRAGMA table_info(knowledge_messages);"

# FTS5 virtual table columns (look at the CREATE statement)
sqlite3 /mnt/projects/cis/data/cis_memory.db ".schema knowledge_messages_fts"

# Row counts
sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT COUNT(*) FROM knowledge_messages;"
sqlite3 /mnt/projects/cis/data/cis_memory.db "SELECT COUNT(*) FROM knowledge_messages_fts;"
```

## Code Files That Reference source_key

All of these expect `source_key` to exist on the base table:

- `runtime/mcp_bridge/spine.py` — lines 348, 360 (SELECT with JOIN — correct)
- `runtime/abstraction/pipeline_relay.py` — line 230 (SELECT from FTS5 — BUG)
- `runtime/api/intent.py` — lines 83, 95, 109 (SELECT with JOIN — correct)
- `tools/catalog/ingest_legacy.py` — lines 59, 156, 166, 238, 248 (INSERT — correct)
- `tools/catalog/ingest_chatgpt_only.py` — lines 66, 75 (INSERT — correct)
- `tools/catalog/convert_to_knowledge.py` — lines 18, 20 (INSERT — correct)
- `tools/catalog/ingest_sessions.py` — line 66 (SELECT DISTINCT — correct)
- `tools/catalog/build_embeddings.py` — line 38 (SELECT — correct)
- `tools/catalog/append_embeddings.py` — line 36 (SELECT — correct)

**Only `pipeline_relay.py` has the bug** — it queries source_key
directly from the FTS5 virtual table instead of joining to the base table.

## Fix

Change `pipeline_relay.py` line 230 from:

```python
"SELECT content, source, source_key FROM knowledge_messages_fts "
"WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT 5",
```

To:

```python
"SELECT km.content, km.source, km.source_key "
"FROM knowledge_messages km "
"JOIN knowledge_messages_fts fts ON km.id = fts.rowid "
"WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT 5",
```

## Gateway Health Check False Positive

The CIS adapter status (`cis_adapter_status`) reports all 6 gateway
profiles as `"healthy": true` even when they return `HTTP 401: Invalid API key`.

The health check only tests whether the port responds, not whether
authentication works. A gateway with expired/rotated keys will show
green while every actual API call fails with 401.

### How to Detect Auth Failures

Check the `error` field in the adapter status output, not just `healthy`:

```python
# All 6 profiles showed this pattern:
"healthy": true,
"error": "HTTP 401: {\"error\":{\"message\":\"Invalid API key\"}}"
```

When the `error` field is non-empty, the gateway port is up but auth
is broken. Check the `.env` files for valid `API_SERVER_KEY` values
(see `references/gateway_api_key_discovery.md` for key locations).
