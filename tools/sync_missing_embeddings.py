#!/usr/bin/env python3.12
"""sync_missing_embeddings.py — embed KB rows that have no vector.

The two stores can drift. rechunk_for_embedding.py commits SQLite before adding
to Chroma, so a failed add (2026-08-29: a batch of 7,196 exceeded Chroma's
5,461 record limit) leaves rows with text and no embedding. Those rows are
findable by FTS5 and invisible to semantic search, silently.

This finds rows whose km_<id> is absent from the collection and embeds them.
Idempotent — safe to run any time, and worth running after any interrupted job.

Usage:
  python3.12 tools/sync_missing_embeddings.py --check
  python3.12 tools/sync_missing_embeddings.py --source archive
  python3.12 tools/sync_missing_embeddings.py            # all sources
"""
import argparse
import os
import sqlite3
import sys

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
CHROMA_SQLITE = "/mnt/projects/cis/data/chroma_data/chroma.sqlite3"
ADD_MAX = 2000


def missing_ids(db, source=None):
    """Row ids present in knowledge_messages but absent from the vector store."""
    s = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    c = sqlite3.connect(f"file:{CHROMA_SQLITE}?mode=ro", uri=True)

    have = {r[0] for r in c.execute("SELECT embedding_id FROM embeddings")}
    q = "SELECT id, content, source, role, source_key FROM knowledge_messages"
    params = ()
    if source:
        q += " WHERE source = ?"
        params = (source,)

    out = []
    for rid, content, src, role, skey in s.execute(q, params):
        if f"km_{rid}" not in have:
            out.append((rid, content, src, role, skey))
    s.close()
    c.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--source")
    ap.add_argument("--check", action="store_true", help="report only")
    args = ap.parse_args()

    rows = missing_ids(args.db, args.source)
    if not rows:
        print("no missing embeddings — stores are in sync")
        return 0

    by_source = {}
    for _, _, src, _, _ in rows:
        by_source[src] = by_source.get(src, 0) + 1
    print(f"rows with no embedding: {len(rows):,}")
    for src, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
        print(f"  {src:24} {n:,}")

    if args.check:
        print("\n--check: nothing written.")
        return 0

    sys.path.insert(0, "/mnt/projects/cis/runtime")
    from mcp_bridge.chroma_index import ChromaClient, filter_for_index
    from mcp_bridge.chroma_lock import chroma_write
    client = ChromaClient()

    # Exclusive for the whole sync. (UNIFIED BUILD LIST 0.3)
    with chroma_write(what="sync_missing_embeddings"):
        coll = client._client.get_collection("knowledge_messages")
        done = 0
        for i in range(0, len(rows), ADD_MAX):
            batch = rows[i:i + ADD_MAX]
            docs = [r[1] for r in batch]
            # Secrets never enter the store. (UNIFIED BUILD LIST 0.2)
            _ids, docs, _metas, _dropped = filter_for_index(
                [f"km_{r[0]}" for r in batch], docs,
                [{"source": r[2], "role": r[3] or "",
                  "source_key": r[4] or ""} for r in batch])
            if not _ids:
                continue
            coll.add(
                ids=_ids,
                documents=docs,
                metadatas=_metas,
                embeddings=client._embedding.embed(docs),
            )
            done += len(batch)
            print(f"  {done:,}/{len(rows):,}", flush=True)

    print(f"\nDone. {done:,} embedded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
