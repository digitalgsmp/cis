"""
api/dam.py — DAM Search API endpoint (Tier 7.5b)
Route: GET /api/dam/search
"""

from flask import Blueprint, jsonify, request
import sqlite3
from db.dam_db import ensure_dam_schema, search_fts, count_fts

dam_bp = Blueprint("dam", __name__)

# DAM data lives in the spine database, not the Flask operational DB
DAM_DB_PATH = "/mnt/projects/cis/data/cis_memory.db"


def _dam_connect():
    """Open a read-only connection to the DAM spine database."""
    conn = sqlite3.connect(DAM_DB_PATH)
    return conn


@dam_bp.route("/api/dam/search")
def api_dam_search():
    """Full-text search over imported Hermes session messages.
    Query params:
        q              — FTS5 search query (required)
        speaker_filter — 'user', 'assistant', 'tool', or 'system' (optional)
        limit          — max results (default 20, max 200)
        offset         — pagination offset (default 0)
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing required parameter: q"}), 400

    speaker_filter = request.args.get("speaker_filter", "").strip() or None
    try:
        limit = min(int(request.args.get("limit", 20)), 200)
    except (ValueError, TypeError):
        limit = 20
    try:
        offset = max(int(request.args.get("offset", 0)), 0)
    except (ValueError, TypeError):
        offset = 0

    conn = _dam_connect()
    try:
        ensure_dam_schema(conn)
        total = count_fts(conn, q, speaker_filter)
        rows = search_fts(conn, q, speaker_filter, limit=limit, offset=offset)
    finally:
        conn.close()

    return jsonify({
        "query": q,
        "speaker_filter": speaker_filter,
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": rows,
    })
