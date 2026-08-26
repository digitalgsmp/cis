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
SRC = ["claude_export","chatgpt_export","claude_transcripts","hermes_session"]
r = coll.query(query_embeddings=[e], n_results=k, where={"source":{"$in":SRC}}, include=["documents"])
for d in r["documents"][0]:
    print(d[:900]); print("===")
