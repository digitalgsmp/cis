#!/usr/bin/env python3
"""
Build ChromaDB embeddings for knowledge_messages.
Reads from knowledge_messages table, embeds content, stores in ChromaDB.

Uses sentence-transformers for embeddings (local, free, no API calls).
"""
import sqlite3
import os
import sys

DB_PATH = "/mnt/projects/cis/data/cis_memory.db"
CHROMA_PATH = "/mnt/projects/cis/data/chroma_data"
COLLECTION_NAME = "knowledge_messages"


def main():
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        print("ERROR: chromadb not installed. Run: pip install chromadb")
        sys.exit(1)

    # Check for sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        use_st = True
        print(f"Using sentence-transformers: all-MiniLM-L6-v2")
    except ImportError:
        use_st = False
        print("sentence-transformers not available, using chromadb default embedding function")

    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, content, source, role, source_key FROM knowledge_messages"
    ).fetchall()
    conn.close()

    print(f"Embedding {len(rows)} messages...")

    # ChromaDB client
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing collection if any
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        pass

    if use_st:
        # Use local sentence-transformers embedding function
        class STEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __init__(self, model):
                self.model = model

            def __call__(self, input):
                return self.model.encode(input, show_progress_bar=True).tolist()

        ef = STEmbeddingFunction(model)
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
        )
    else:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        )

    # Batch insert
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        ids = [f"km_{r[0]}" for r in batch]
        documents = [r[1] for r in batch if r[1]]
        metadatas = [
            {"source": r[2], "role": r[3], "source_key": r[4] or ""}
            for r in batch
        ]

        # Filter empty documents
        valid = [(i, d, m) for i, (idx, d, m) in enumerate(zip(ids, documents, metadatas)) if d]
        if not valid:
            continue

        valid_ids = [ids[v[0]] for v in valid]
        valid_docs = [v[1] for v in valid]
        valid_meta = [v[2] for v in valid]

        collection.add(
            ids=valid_ids,
            documents=valid_docs,
            metadatas=valid_meta,
        )

        if (i // batch_size) % 10 == 0:
            print(f"  Embedded {min(i + batch_size, len(rows))}/{len(rows)}")

    print(f"DONE: {len(rows)} messages embedded in collection '{COLLECTION_NAME}'")
    print(f"ChromaDB path: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
