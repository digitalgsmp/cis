#!/usr/bin/env python3.12
"""Retrieval proof, through the EXACT path a cold developer uses.

Replicates tools/ask_history.py: same embedding, same n_results = max(k*10,50),
same MIN_CHARS=200 and PER_SOURCE=2 ranking rules. Then reports whether the
preserved handoff is among what that path actually returns.

Also records a measurement worth keeping: Chroma's HNSW search is approximate,
so recall depends on n_results. The same probe can miss at 30 and rank first at
400. Both numbers are printed, because the one that matters for a cold start is
the one ask_history asks for.
"""
import sys
from collections import Counter
sys.path.insert(0, "/mnt/projects/cis/runtime")
from mcp_bridge.chroma_index import ChromaClient
from mcp_bridge.chroma_lock import chroma_read

TARGET = "CIS-ARCH-RECONSTRUCTION-PHASE-HANDOFF-2026-10-07/"
MIN_CHARS, PER_SOURCE, K = 200, 2, 5

PROBES = [
    "Hermes is an implementation, not the permanent definition of the backend",
    "record once derive everywhere",
    "cards are projections of structured Execution Contracts",
    "DeepSeek Harness replaceability test",
    "dependency architecture versus trust deployment topology",
    "WIASW destination extensibility test",
    "revision 127 precedes reconstruction",
]


def ask_history_rank(coll, emb, q):
    """What tools/ask_history.py returns for this question, in order."""
    r = coll.query(query_embeddings=[emb], n_results=max(K * 10, 50),
                   include=["documents", "metadatas"])
    picked, seen = [], {}
    for d, m in zip(r["documents"][0], r["metadatas"][0]):
        if not d or len(d) < MIN_CHARS:
            continue
        src = (m or {}).get("source", "?")
        if seen.get(src, 0) >= PER_SOURCE:
            continue
        seen[src] = seen.get(src, 0) + 1
        picked.append((src, (m or {}).get("source_key") or "", d))
        if len(picked) >= K:
            break
    return picked, r["metadatas"][0]


c = ChromaClient()
with chroma_read() as got:
    if not got:
        print("LOCK UNAVAILABLE"); sys.exit(2)
    coll = c._client.get_collection("knowledge_messages")

    print("RETRIEVAL PROOF — preserved phase handoff")
    print("store: knowledge_messages (Chroma) · model: all-MiniLM-L6-v2 · "
          "path: tools/ask_history.py semantics (n_results=50, k=5, "
          "MIN_CHARS=200, PER_SOURCE=2)")
    print()
    returned = 0
    deep = 0
    for q in PROBES:
        emb = c._embedding.embed_single(q)
        picked, metas50 = ask_history_rank(coll, emb, q)
        hit = next((i for i, (_s, key, _d) in enumerate(picked, 1)
                    if TARGET in key), None)
        # Deep recall, for the HNSW-recall note.
        r400 = coll.query(query_embeddings=[emb], n_results=400,
                          include=["metadatas"])
        deep_rank = next((i for i, m in enumerate(r400["metadatas"][0], 1)
                          if TARGET in ((m or {}).get("source_key") or "")), None)
        if hit:
            returned += 1
        if deep_rank:
            deep += 1
        print(f"PROBE  {q}")
        print(f"  ask_history result slot for the handoff : "
              f"{hit if hit else 'not in the 5 returned'}")
        print(f"  deep raw rank (n_results=400)           : {deep_rank}")
        print(f"  sources ask_history returned            : "
              f"{dict(Counter(s for s, _k, _d in picked))}")
        for i, (s, key, d) in enumerate(picked, 1):
            mark = "<<<" if TARGET in key else "   "
            print(f"    {i}. {mark} [{s}] {key[:64]}")
            print(f"            {d[:110].replace(chr(10), ' ')}")
        print()

    print(f"SUMMARY: handoff among ask_history's 5 results for "
          f"{returned}/{len(PROBES)} probes; "
          f"present in deep recall for {deep}/{len(PROBES)}.")
