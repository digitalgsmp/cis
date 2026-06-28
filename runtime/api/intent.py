"""
api/intent.py — Intent Alignment API.

Fast-track Phase E: Measure proposals against Eric's verbatim intentions
using the existing knowledge_messages ChromaDB collection + SQLite FTS5.

Endpoints:
    GET /api/intent/alignment?proposal=<text>&top_k=10
        Returns combined semantic (ChromaDB) + keyword (FTS5) matches
        from Eric's verbatim words across all knowledge sources.

Blueprint: intent_bp — register in app.py
"""
import sqlite3
from flask import Blueprint, jsonify, request

# DB path — hardcoded to match MCP bridge (config.py's DB_PATH points elsewhere)
DB_PATH = "/mnt/projects/cis/data/cis_memory.db"

intent_bp = Blueprint("intent", __name__)

CHROMA_PATH = "/mnt/projects/cis/data/chroma_data"
COLLECTION_NAME = "knowledge_messages"


def _get_chroma():
    """Lazy-load ChromaDB client."""
    import chromadb
    return chromadb.PersistentClient(path=CHROMA_PATH)


def _get_db():
    """Open CIS spine read-only."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def measure_intent(proposal_text: str, top_k: int = 10) -> dict:
    """
    Measure a proposal against Eric's verbatim intentions.

    Returns:
        {
            "proposal": <text>,
            "semantic": [{id, content, source, role, score, source_key}, ...],
            "keyword":  [{id, content, source, role, source_key}, ...],
            "total_matches": N
        }
    """
    results = {"proposal": proposal_text, "semantic": [], "keyword": [], "total_matches": 0}

    # ── Semantic search via ChromaDB ──
    try:
        client = _get_chroma()
        collection = client.get_collection(COLLECTION_NAME)
        chroma_results = collection.query(
            query_texts=[proposal_text],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        if chroma_results.get("ids") and chroma_results["ids"][0]:
            for i, doc_id in enumerate(chroma_results["ids"][0]):
                content = (chroma_results["documents"][0][i] or "")[:500]
                meta = chroma_results["metadatas"][0][i]
                dist = chroma_results["distances"][0][i]
                results["semantic"].append({
                    "id": doc_id,
                    "content": content,
                    "source": meta.get("source", ""),
                    "role": meta.get("role", ""),
                    "source_key": meta.get("source_key", ""),
                    "score": round(1.0 - float(dist), 4),
                })
    except Exception as e:
        results["semantic_error"] = str(e)

    # ── Keyword search via SQLite FTS5 ──
    try:
        conn = _get_db()
        safe_query = proposal_text.replace('"', '').replace("'", "")[:200]
        rows = conn.execute(
            """SELECT km.id, km.content, km.source, km.role, km.source_key
               FROM knowledge_messages km
               JOIN knowledge_messages_fts fts ON km.id = fts.rowid
               WHERE knowledge_messages_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (safe_query, top_k),
        ).fetchall()

        if not rows:
            like = f"%{safe_query}%"
            rows = conn.execute(
                """SELECT id, content, source, role, source_key
                   FROM knowledge_messages
                   WHERE content LIKE ?
                   ORDER BY id DESC
                   LIMIT ?""",
                (like, top_k),
            ).fetchall()

        for row in rows:
            results["keyword"].append({
                "id": row["id"],
                "content": (row["content"] or "")[:500],
                "source": row["source"] or "",
                "role": row["role"] or "",
                "source_key": row["source_key"] or "",
            })
        conn.close()
    except Exception as e:
        results["keyword_error"] = str(e)

    results["total_matches"] = len(results["semantic"]) + len(results["keyword"])
    return results


# ── Flask endpoint ──────────────────────────────────────────

@intent_bp.route("/api/intent/alignment", methods=["GET"])
def api_intent_alignment():
    """
    GET /api/intent/alignment?proposal=<text>&top_k=10

    Measure a proposal against Eric's verbatim intentions.
    Returns combined semantic + keyword matches with provenance.
    """
    proposal = request.args.get("proposal", "").strip()
    if not proposal:
        return jsonify({"error": "proposal parameter is required"}), 400

    try:
        top_k = int(request.args.get("top_k", 10))
        top_k = max(1, min(top_k, 50))
    except ValueError:
        top_k = 10

    result = measure_intent(proposal, top_k=top_k)
    return jsonify(result)
