import time, os
os.environ.setdefault("CIS_REPO_ROOT", "/mnt/projects/cis")
import chromadb
from sentence_transformers import SentenceTransformer

c = chromadb.PersistentClient(path="/mnt/projects/cis/data/chroma_data")
col = c.get_collection("knowledge_messages")
print(f"count = {col.count()}", flush=True)

m = SentenceTransformer("all-MiniLM-L6-v2")

def q(text):
    emb = m.encode([text], show_progress_bar=False).tolist()[0]
    r = col.query(query_embeddings=[emb], n_results=4, include=["metadatas", "documents"])
    srcs = [( (r["metadatas"][0][i] or {}).get("source","?"), ((r["documents"][0][i] or "")[:50]).replace("\n"," ") ) for i in range(len(r["ids"][0]))]
    return srcs

for term in ["AI Saves the World economics", "creative writing screenplay idea", "social work case management client", "container isolation enforcement"]:
    print(f"\nQ: {term!r}", flush=True)
    for s, d in q(term):
        print(f"   src={s:22} :: {d}", flush=True)
