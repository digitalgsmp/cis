"""
api/captures.py — Capture (insight, note, solution) endpoints.
Routes:
    GET  /api/captures
    POST /api/captures
"""

from flask import Blueprint, jsonify, request
from db.connection import db_connect, ensure_tables
from utils.helpers import ts

captures_bp = Blueprint("captures", __name__)


@captures_bp.route("/api/captures", methods=["GET"])
def api_captures_get():
    project_id = request.args.get("project_id")
    conn = db_connect()
    ensure_tables(conn)
    try:
        if project_id:
            rows = conn.execute(
                "SELECT * FROM captures WHERE project_id=? ORDER BY id DESC LIMIT 50",
                (project_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM captures ORDER BY id DESC LIMIT 50"
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@captures_bp.route("/api/captures", methods=["POST"])
def api_captures_post():
    data         = request.get_json()
    capture_type = data.get("capture_type", "insight").strip()
    title        = data.get("title", "").strip()
    observation  = data.get("observation", "").strip()
    source       = data.get("source_record_id", "").strip() or None
    project_id   = data.get("project_id", "").strip() or None

    if not title or not observation:
        return jsonify({"success": False, "error": "title and observation are required"}), 400

    conn = db_connect()
    ensure_tables(conn)
    try:
        conn.execute(
            "INSERT INTO captures (capture_type, title, observation, source_record_id, project_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (capture_type, title, observation, source, project_id, ts())
        )
        # Mirror insights into dedicated table
        if capture_type == "insight":
            conn.execute(
                "INSERT INTO insights (category, title, observation, source_record_id, project_id, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("workflow", title, observation, source, project_id, ts())
            )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
