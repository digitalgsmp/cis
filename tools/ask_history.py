#!/usr/bin/env python3.12
# Semantic search over Eric conversation history.
# MUST run as python3.12 (chromadb is in /home/eric/.local/lib/python3.12).
# Usage: python3.12 tools/ask_history.py "your question" [top_k]
import sys, os
sys.path.insert(0, "/mnt/projects/cis/runtime")
from mcp_bridge.chroma_index import ChromaClient
q = sys.argv[1]
k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
c = ChromaClient()
e = c._embedding.embed_single(q)
coll = c._client.get_collection("knowledge_messages")
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

for src, d in picked:
    print(f"[{src}]")
    print(d[:900]); print("===")
