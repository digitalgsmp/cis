"""
api/decisions.py — Architecture Decision Record endpoints.
Routes:
    GET  /api/decisions
    POST /api/decisions
"""

from flask import Blueprint, jsonify, request
from db.connection import db_connect

decisions_bp = Blueprint("decisions", __name__)


@decisions_bp.route("/api/decisions")
def api_decisions():
    conn = db_connect()
    try:
        rows = conn.execute(
            "SELECT decision_number, title, description, rationale, status, created_at "
            "FROM decisions ORDER BY id ASC"
        ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])
    finally:
        conn.close()


@decisions_bp.route("/api/decisions", methods=["POST"])
def api_decisions_add():
    data   = request.get_json()
    number = data.get("decision_number", "").strip()
    title  = data.get("title", "").strip()
    desc   = data.get("description", "").strip()
    rat    = data.get("rationale", "").strip()
    status = data.get("status", "locked").strip()

    if not number or not title or not desc or not rat:
        return jsonify({
            "success": False,
            "error": "decision_number, title, description and rationale are required"
        }), 400

    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO decisions "
            "(decision_number, title, description, rationale, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (number, title, desc, rat, status)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
