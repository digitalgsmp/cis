#!/usr/bin/env python3.12
"""Is the 3/7 shortfall a ranking problem or an approximate-recall problem?

If the handoff chunk has the SMALLEST distance at depth 400 but is absent from a
depth-50 query, then the top-50 window is not the true top 50 — the HNSW search
is missing it, and no reranking change can recover what the search never
returned. Measured, not assumed.
"""
import sys
sys.path.insert(0, "/mnt/projects/cis/runtime")
from mcp_bridge.chroma_index import ChromaClient
from mcp_bridge.chroma_lock import chroma_read

TARGET = "CIS-ARCH-RECONSTRUCTION-PHASE-HANDOFF-2026-10-07/"
PROBES = [
    "dependency architecture versus trust deployment topology",
    "WIASW destination extensibility test",
    "record once derive everywhere",
    "cards are projections of structured Execution Contracts",
]
DEPTHS = [50, 100, 200, 400, 800]

c = ChromaClient()
with chroma_read() as got:
    coll = c._client.get_collection("knowledge_messages")
    print(f"collection count: {coll.count():,}")
    print()
    for q in PROBES:
        emb = c._embedding.embed_single(q)
        print(f"PROBE: {q}")
        for n in DEPTHS:
            r = coll.query(query_embeddings=[emb], n_results=n,
                           include=["metadatas", "distances"])
            metas, dists = r["metadatas"][0], r["distances"][0]
            rank = next((i for i, m in enumerate(metas, 1)
                         if TARGET in ((m or {}).get("source_key") or "")), None)
            best = dists[0]
            hd = (dists[rank - 1] if rank else None)
            print(f"  n_results={n:4d}  handoff_rank={str(rank):>5s}  "
                  f"best_distance={best:.4f}  "
                  f"handoff_distance={('%.4f' % hd) if hd is not None else '—':>7s}")
        print()
