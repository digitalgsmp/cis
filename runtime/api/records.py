"""
api/records.py — Knowledge record read endpoints.
Routes:
    GET /api/records
    GET /api/records/<record_id>
"""

from flask import Blueprint, jsonify, request
from config import RECORDS_ROOT
from utils.helpers import load_json

records_bp = Blueprint("records", __name__)


@records_bp.route("/api/records")
def api_records():
    project_id    = request.args.get("project_id")
    status_filter = request.args.get("status")
    records = []

    if not RECORDS_ROOT.exists():
        return jsonify([])

    for record_dir in sorted(RECORDS_ROOT.iterdir()):
        if not record_dir.is_dir():
            continue
        for record_file in sorted(record_dir.glob("*.json")):
            try:
                record = load_json(record_file)
                if project_id and record.get("project_id") != project_id:
                    continue
                if status_filter and record.get("status") != status_filter:
                    continue
                records.append({
                    "record_id":          record.get("record_id", record_file.stem),
                    "title":              record.get("title", ""),
                    "status":             record.get("status", ""),
                    "knowledge_category": record.get("knowledge_category", ""),
                    "project_id":         record.get("project_id"),
                    "active_stages":      record.get("active_stages", []),
                    "created_at":         record.get("created_at", ""),
                    "updated_at":         record.get("updated_at", ""),
                })
            except Exception:
                pass

    return jsonify(records)


@records_bp.route("/api/records/<path:record_id>")
def api_record_detail(record_id):
    for record_dir in RECORDS_ROOT.iterdir():
        if not record_dir.is_dir():
            continue
        for record_file in record_dir.glob("*.json"):
            try:
                record = load_json(record_file)
                if record.get("record_id") == record_id:
                    return jsonify(record)
            except Exception:
                pass
    return jsonify({"error": "Record not found"}), 404
