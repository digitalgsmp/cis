#!/usr/bin/env python3
"""
Append new knowledge_messages to existing ChromaDB collection.
Only embeds messages not already in ChromaDB (checked by source_key or content hash).
"""
import sqlite3, chromadb, sys, os
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
CHROMA_PATH = "/mnt/projects/cis/data/chroma_data"
COLLECTION_NAME = "knowledge_messages"
BATCH_SIZE = 500

print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Get all existing ChromaDB IDs
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(COLLECTION_NAME)
existing_ids = set()
# ChromaDB get() can be slow for large collections — use a range query
offset = 0
while True:
    batch = collection.get(offset=offset, limit=10000, include=[])
    ids = batch.get('ids', [])
    if not ids:
        break
    existing_ids.update(ids)
    offset += len(ids)
print(f"Existing ChromaDB IDs: {len(existing_ids)}")

# Get all knowledge_messages
conn = sqlite3.connect(DB_PATH)
rows = conn.execute(
    "SELECT id, content, source, role, source_key FROM knowledge_messages ORDER BY id"
).fetchall()
conn.close()
print(f"Knowledge messages: {len(rows)} total")

# Filter to new only
class STEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model):
        self.model = model
    def __call__(self, input):
        return self.model.encode(input, show_progress_bar=True).tolist()

ef = STEmbeddingFunction(model)

new_rows = []
for row in rows:
    chroma_id = f"km_{row[0]}"
    if chroma_id not in existing_ids:
        new_rows.append(row)

print(f"New to embed: {len(new_rows)}")

if not new_rows:
    print("Nothing new to embed. Done.")
    sys.exit(0)

# Embed in batches
total = len(new_rows)
embedded = 0
for i in range(0, total, BATCH_SIZE):
    batch = new_rows[i:i+BATCH_SIZE]
    ids = [f"km_{r[0]}" for r in batch]
    documents = [r[1] for r in batch if r[1]]
    metadatas = [{"source": r[2], "role": r[3], "source_key": r[4] or ""} for r in batch]

    valid = [(j, d, m) for j, (idx, d, m) in enumerate(zip(ids, documents, metadatas)) if d]
    if not valid:
        continue
    valid_ids = [ids[v[0]] for v in valid]
    valid_docs = [v[1] for v in valid]
    valid_meta = [v[2] for v in valid]

    collection.add(ids=valid_ids, documents=valid_docs, metadatas=valid_meta)
    embedded += len(batch)
    if (i // BATCH_SIZE) % 5 == 0:
        print(f"  {embedded}/{total}")

print(f"DONE: {embedded} new messages embedded")
print(f"Collection total: {collection.count()}")
