"""
api/extraction_runs.py — Extraction run log endpoints.
Routes:
    GET  /api/extraction_runs
    POST /api/extraction_runs
"""

from flask import Blueprint, jsonify, request
from db.connection import db_connect

extraction_runs_bp = Blueprint("extraction_runs", __name__)


@extraction_runs_bp.route("/api/extraction_runs")
def api_extraction_runs_get():
    source_id  = request.args.get("source_id")
    project_id = request.args.get("project_id")
    conn = db_connect()
    try:
        if source_id:
            rows = conn.execute(
                "SELECT * FROM extraction_runs WHERE source_id=? ORDER BY id DESC LIMIT 20",
                (source_id,)
            ).fetchall()
        elif project_id:
            rows = conn.execute(
                "SELECT * FROM extraction_runs WHERE project_id=? ORDER BY id DESC LIMIT 50",
                (project_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM extraction_runs ORDER BY id DESC LIMIT 50"
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])
    finally:
        conn.close()


@extraction_runs_bp.route("/api/extraction_runs", methods=["POST"])
def api_extraction_runs_post():
    data             = request.get_json()
    source_id        = data.get("source_id", "").strip()
    record_id        = data.get("record_id", "").strip() or None
    model_used       = data.get("model_used", "").strip() or None
    extraction_type  = data.get("extraction_type", "vision").strip()
    status           = data.get("status", "success").strip()
    duration_seconds = data.get("duration_seconds") or None
    error            = data.get("error", "").strip() or None
    project_id       = data.get("project_id", "").strip() or None
    completed_at     = data.get("completed_at", "").strip() or None

    if not source_id:
        return jsonify({"success": False, "error": "source_id is required"}), 400

    conn = db_connect()
    try:
        conn.execute(
            "INSERT INTO extraction_runs "
            "(source_id, record_id, model_used, extraction_type, status, "
            "duration_seconds, error, project_id, created_at, completed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)",
            (source_id, record_id, model_used, extraction_type, status,
             duration_seconds, error, project_id, completed_at)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
