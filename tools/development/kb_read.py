#!/usr/bin/env python3
"""kb_read.py — bounded, read-only original-KB evidence for WB.1C packets.

Reuses the existing FTS5 index (knowledge_messages / knowledge_messages_fts)
and the existing secret-redaction filter (mcp_bridge.chroma_index.redact_secrets),
the same pattern runtime/workbench_app.py._kb_search already uses — but
additionally returns the stable id/source_key/role that helper drops, because
a packet must be able to name exactly which record it cites and re-fetch it
later for a freshness check.

No embedding model, no Chroma, no network: this is FTS keyword search only,
matching the task's "no remote model calls needed to prepare" requirement.
"""
import os
import re
import sqlite3
import sys

MIN_CHARS_DEFAULT = 0     # kb_read does not filter short rows; the caller
                           # decides relevance, this module reports coverage
BOUND_CHARS = 900          # per-result content bound, matches the ingest
                           # tools' MAX_CHARS so an excerpt is never
                           # arbitrarily longer than what was ever embedded

_RUNTIME_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "runtime",
)

# Small, fixed stopword list — enough to keep an OR-query from being
# dominated by function words, not a linguistics project.
_STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "is",
    "are", "was", "were", "be", "been", "this", "that", "with", "without",
    "it", "its", "at", "by", "from", "as", "into",
}


def _redact(text):
    if _RUNTIME_DIR not in sys.path:
        sys.path.insert(0, _RUNTIME_DIR)
    try:
        from mcp_bridge.chroma_index import redact_secrets
    except Exception as e:
        return f"(KB content withheld — secret filter unavailable: {type(e).__name__})"
    return redact_secrets(text)


def _keywords(query):
    """Turn a free-text concept query into an FTS5 OR-of-terms expression.

    FTS5's bareword sequence is an implicit AND — a multi-word natural
    query like "remote access without opening firewall ports" would then
    require EVERY word to appear in the same row, which real prose rarely
    does. OR ranked by bm25 (ORDER BY rank) surfaces the closest matches
    first while still returning something for a loosely-worded concept
    query, which is what a bounded developer-supplied search needs here.
    """
    cleaned = re.sub(r'[."*(){}:^+\-]', ' ', query)
    terms = [w for w in cleaned.split() if len(w) > 2 and w.lower() not in _STOPWORDS]
    return " OR ".join(terms)


def search_knowledge(conn, query, limit=8):
    """Run one bounded FTS5 search. Returns a dict that distinguishes:
      - ok=False: the query itself failed (bad FTS syntax, missing table, etc)
      - ok=True, results=[]: the query ran and matched nothing
      - ok=True, results=[...], truncated=True: more matched than `limit`
        returned; `total_matches` and the omitted rows' ids are still
        discoverable via a second call with a higher limit or fetch_by_ids.
    """
    keywords = _keywords(query)
    if not keywords:
        return {
            "ok": False, "query": query, "keywords": keywords,
            "error": "empty query after stripping FTS special characters",
            "results": [],
        }
    try:
        # FTS5 external-content tables reject `MATCH` against an aliased
        # table name ("no such column: f") on this sqlite3 build — the
        # match must name knowledge_messages_fts directly.
        rows = conn.execute(
            "SELECT km.id, km.source, km.source_key, km.role, km.content, km.timestamp "
            "FROM knowledge_messages_fts "
            "JOIN knowledge_messages km ON km.id = knowledge_messages_fts.rowid "
            "WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT ?",
            (keywords, limit),
        ).fetchall()
        total = conn.execute(
            "SELECT count(*) FROM knowledge_messages_fts WHERE knowledge_messages_fts MATCH ?",
            (keywords,),
        ).fetchone()[0]
    except sqlite3.OperationalError as e:
        return {
            "ok": False, "query": query, "keywords": keywords,
            "error": f"{type(e).__name__}: {e}", "results": [],
        }

    results = [
        {
            "id": r[0], "source": r[1], "source_key": r[2], "role": r[3],
            "content": _redact(r[4])[:BOUND_CHARS], "timestamp": r[5],
        }
        for r in rows
    ]
    return {
        "ok": True, "query": query, "keywords": keywords,
        "results": results, "returned": len(results),
        "total_matches": total, "truncated": total > len(results),
    }


def fetch_by_ids(conn, ids):
    """Direct lookup by stable knowledge_messages.id — used to pull a record
    named by the developer (e.g. 'KB 750756') rather than found by search,
    and to re-check a previously-cited record's content for freshness."""
    if not ids:
        return {"ok": True, "results": [], "missing": []}
    placeholders = ",".join("?" for _ in ids)
    try:
        rows = conn.execute(
            f"SELECT id, source, source_key, role, content, timestamp "
            f"FROM knowledge_messages WHERE id IN ({placeholders})",
            list(ids),
        ).fetchall()
    except sqlite3.OperationalError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "results": [], "missing": list(ids)}
    found_ids = {r[0] for r in rows}
    results = [
        {
            "id": r[0], "source": r[1], "source_key": r[2], "role": r[3],
            "content": _redact(r[4])[:BOUND_CHARS], "timestamp": r[5],
        }
        for r in rows
    ]
    missing = [i for i in ids if i not in found_ids]
    return {"ok": True, "results": results, "missing": missing}
