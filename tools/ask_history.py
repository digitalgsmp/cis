#!/usr/bin/env python3.12
# Semantic search over Eric conversation history.
# MUST run as python3.12 (chromadb is in /home/eric/.local/lib/python3.12).
# Usage: python3.12 tools/ask_history.py "your question" [top_k]
import sys, os
sys.path.insert(0, "/mnt/projects/cis/runtime")
from mcp_bridge.chroma_index import ChromaClient, redact_secrets
from mcp_bridge.chroma_lock import chroma_read
q = sys.argv[1]
k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
c = ChromaClient()
# Embedding the question touches only the local model, not the store, so it
# happens outside the lock — no reason to hold the store while the GPU works.
e = c._embedding.embed_single(q)
# No source filter. The old filter reached 4.7% of the KB (14,011 of 299,514):
# it hid the archive, cis_docs, swa_project, every pipeline run and agent session,
# and one of its four names ("hermes_session") was a source_key prefix that matched
# nothing. gate_research_before_conclusion checks claims against the whole corpus,
# so this searches the whole corpus too.
# Over-fetch, then rank. Raw cosine order is dominated by cis_docs, which holds
# 75,794 chunks averaging 168 chars — a bare heading like "### FTS5 query syntax"
# embeds tighter to a short question than 2,600 chars of the reasoning that
# answers it. Unranked, every query returned headings. Two deterministic rules:
# drop fragments too short to be an answer, and let no single source take the
# whole page.
MIN_CHARS = 200      # below this it is a heading or a stub, not an answer
PER_SOURCE = 2       # so one source cannot crowd out the rest

# Shared lock: an ingest writing the store while this reads it corrupts the read.
# Reporting nothing beats reporting garbage, and unlike the pipeline this has no
# keyword fallback to degrade to. (UNIFIED BUILD LIST 0.3)
with chroma_read() as got_lock:
    if not got_lock:
        print("KB ingest in progress — the store is being written.")
        print("Search would read a half-written index. Retry when it finishes.")
        sys.exit(2)
    # Opening the collection reads the store too, so it belongs inside the lock,
    # not just the query.
    coll = c._client.get_collection("knowledge_messages")
    r = coll.query(query_embeddings=[e], n_results=max(k * 10, 50),
                   include=["documents", "metadatas"])

picked, seen = [], {}
for d, m in zip(r["documents"][0], r["metadatas"][0]):
    if not d or len(d) < MIN_CHARS:
        continue
    src = (m or {}).get("source", "?")
    if seen.get(src, 0) >= PER_SOURCE:
        continue
    seen[src] = seen.get(src, 0) + 1
    picked.append((src, d))
    if len(picked) >= k:
        break

# If the filters were too strict for a narrow corpus, fall back to raw order
# rather than reporting nothing.
if not picked:
    picked = [((m or {}).get("source", "?"), d)
              for d, m in zip(r["documents"][0], r["metadatas"][0])][:k]

# Mask secrets on the way out. The index-time filter never ran over most of this
# corpus — the ingest tools bypass it — so the only reliable place to catch a
# secret is here, between the store and a reader. (UNIFIED BUILD LIST 0.2)
for src, d in picked:
    print(f"[{src}]")
    print(redact_secrets(d)[:900]); print("===")
