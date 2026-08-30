#!/usr/bin/env python3.12
"""rebuild_vector_index.py — rebuild the Chroma collection from the spine.

The vector store is DERIVED data. Every embedding in it was generated from
knowledge_messages in SQLite, so the collection can be thrown away and rebuilt
at any time. That is why a Chroma backup matters far less than a spine backup,
and why "repair the index" is the wrong frame — the right frame is "decide what
belongs in it, then rebuild".

Why this exists (2026-08-29): the archive was embedded wholesale. It became
2.19M of 2.64M vectors — 82% of the index — and 53% of it was source code and a
third-party drive dump. "Why was the orchestrator set aside" started returning
Blender addon source. Filtering it out at QUERY time was tried and is not
viable: a metadata filter makes Chroma scan all 2.6M vectors and the query never
returned. Deleting in place leaves tombstones and keeps the file at 20GB. So:
rebuild, excluding what does not belong.

Exclusions are deliberate and visible, not a hidden filter. The excluded text
stays in SQLite and remains fully searchable by FTS5 keyword — only the semantic
index is scoped.

Usage:
  python3.12 tools/rebuild_vector_index.py --dry-run
  python3.12 tools/rebuild_vector_index.py --exclude archive
  python3.12 tools/rebuild_vector_index.py --exclude archive --include-like 'archive/_2 Word%'
"""
import argparse
import os
import sqlite3
import sys
import time

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
COLLECTION = "knowledge_messages"
ADD_MAX = 2000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_PATH)
    ap.add_argument("--exclude", action="append", default=[],
                    help="source name to leave OUT of the vector index")
    ap.add_argument("--include-like", action="append", default=[],
                    help="source_key LIKE pattern to keep even if its source is excluded")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)

    where, params = "1=1", []
    if args.exclude:
        marks = ",".join("?" * len(args.exclude))
        keep = ""
        if args.include_like:
            keep = " OR " + " OR ".join(
                ["source_key LIKE ?"] * len(args.include_like))
        where = f"(source NOT IN ({marks}){keep})"
        params = list(args.exclude) + list(args.include_like)

    total = conn.execute(
        f"SELECT count(*) FROM knowledge_messages WHERE {where}", params
    ).fetchone()[0]
    grand = conn.execute("SELECT count(*) FROM knowledge_messages").fetchone()[0]

    print(f"spine rows          : {grand:,}")
    print(f"to index            : {total:,}")
    print(f"left out of vectors : {grand - total:,} "
          f"(still keyword-searchable via FTS5)")
    if args.exclude:
        print(f"excluded sources    : {', '.join(args.exclude)}")
    if args.include_like:
        print(f"kept back in        : {', '.join(args.include_like)}")

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return 0

    sys.path.insert(0, "/mnt/projects/cis/runtime")
    from mcp_bridge.chroma_index import ChromaClient, filter_for_index
    client = ChromaClient()

    print("\ndropping the old collection...")
    try:
        client._client.delete_collection(COLLECTION)
    except Exception as e:
        print(f"  (delete_collection: {e})")
    coll = client._client.create_collection(COLLECTION)

    print("rebuilding...")
    started = time.time()
    done = 0
    ids, docs, metas = [], [], []

    def flush():
        nonlocal ids, docs, metas, done
        if not ids:
            return
        # Secrets never enter the store. (UNIFIED BUILD LIST 0.2)
        ids, docs, metas, _dropped = filter_for_index(ids, docs, metas)
        if not ids:
            return
        coll.add(ids=ids, documents=docs, metadatas=metas,
                 embeddings=client._embedding.embed(docs))
        done += len(ids)
        rate = done / max(time.time() - started, 1)
        eta = (total - done) / rate / 60 if rate else 0
        print(f"  {done:,}/{total:,}  ({rate:.0f}/s, ~{eta:.1f} min left)",
              flush=True)
        ids, docs, metas = [], [], []

    for rid, content, source, role, skey in conn.execute(
        f"SELECT id, content, source, role, source_key FROM knowledge_messages "
        f"WHERE {where} ORDER BY id", params
    ):
        if not content:
            continue
        ids.append(f"km_{rid}")
        docs.append(content)
        metas.append({"source": source or "", "role": role or "",
                      "source_key": skey or ""})
        if len(ids) >= ADD_MAX:
            flush()
    flush()

    print(f"\nDone. {done:,} vectors in '{COLLECTION}'.")
    print("The chroma.sqlite3 file will NOT shrink on its own — SQLite keeps the")
    print("freed pages. Run VACUUM to reclaim the disk if you want it back.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
