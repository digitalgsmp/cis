#!/usr/bin/env python3
"""
Append new knowledge_messages to existing ChromaDB collection.
Only embeds messages not already in ChromaDB (checked by source_key or content hash).

2026-09-05 — this tool was a sixth Chroma writer that BOTH 0.2 and 0.3 missed:

  * No chroma_write lock (0.3). It opened a bare chromadb.PersistentClient on
    /mnt/projects/cis/data/chroma_data — the same store 0.3 wired five other
    writers to protect — so running it while the container held a read could
    corrupt that read. 0.3 is marked DONE and this was a live hole in it.
  * No filter_for_index (0.2). Raw knowledge_messages content went straight to
    collection.add(), so any secret in a row was embedded verbatim. The
    docstring on filter_for_index says "Every ingest tool must call this before
    coll.add()" and names five tools; this was not one of them.

Both are fixed below. The lock is held for the WHOLE Chroma phase, not per
batch, because this tool scans existing ids first and then adds against that
scan — a writer admitted in between would make the scan stale and produce
duplicate embeddings.

The model load and the SQLite read stay OUTSIDE the lock deliberately: neither
touches Chroma, and holding an exclusive lock through a multi-second model load
blocks the container's semantic search for no reason.
"""
import sqlite3, sys, os

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
CHROMA_PATH = "/mnt/projects/cis/data/chroma_data"
COLLECTION_NAME = "knowledge_messages"
BATCH_SIZE = 500

sys.path.insert(0, "/mnt/projects/cis/runtime")
from mcp_bridge.chroma_index import filter_for_index          # noqa: E402
from mcp_bridge.chroma_lock import chroma_write               # noqa: E402

import chromadb                                               # noqa: E402
from sentence_transformers import SentenceTransformer         # noqa: E402
from chromadb.utils import embedding_functions                # noqa: E402


class STEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model):
        self.model = model

    def __call__(self, input):
        return self.model.encode(input, show_progress_bar=True).tolist()


# ── Outside the lock: model load and SQLite read touch no Chroma state ────────
print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
ef = STEmbeddingFunction(model)

conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    "SELECT id, content, source, role, source_key FROM knowledge_messages ORDER BY id"
).fetchall()
conn.close()
print(f"Knowledge messages: {len(rows)} total")

# ── Exclusive for the whole Chroma phase. (UNIFIED BUILD LIST 0.3) ────────────
with chroma_write(what="append_embeddings"):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)

    existing_ids = set()
    offset = 0
    while True:
        batch = collection.get(offset=offset, limit=10000, include=[])
        ids = batch.get('ids', [])
        if not ids:
            break
        existing_ids.update(ids)
        offset += len(ids)
    print(f"Existing ChromaDB IDs: {len(existing_ids)}")

    new_rows = [r for r in rows if f"km_{r[0]}" not in existing_ids]
    print(f"New to embed: {len(new_rows)}")

    if not new_rows:
        print("Nothing new to embed. Done.")
        sys.exit(0)

    total = len(new_rows)
    embedded = 0
    dropped_total = 0
    for i in range(0, total, BATCH_SIZE):
        batch = new_rows[i:i + BATCH_SIZE]

        ids, documents, metadatas = [], [], []
        for r in batch:
            if not r[1]:
                continue
            ids.append(f"km_{r[0]}")
            documents.append(r[1])
            metadatas.append({"source": r[2], "role": r[3], "source_key": r[4] or ""})
        if not ids:
            continue

        # Index-time secret filter. (UNIFIED BUILD LIST 0.2) Excluded rows are
        # DROPPED, not masked — a private key has no business in the store in
        # any form. Redact rows are kept with the secret masked.
        ids, documents, metadatas, dropped = filter_for_index(ids, documents, metadatas)
        dropped_total += dropped
        if not ids:
            continue

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        embedded += len(ids)
        if (i // BATCH_SIZE) % 5 == 0:
            print(f"  {embedded}/{total}")

    print(f"DONE: {embedded} new messages embedded")
    if dropped_total:
        print(f"Dropped by the secret filter: {dropped_total}")
    print(f"Collection total: {collection.count()}")
