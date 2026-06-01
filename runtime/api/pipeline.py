"""
api/pipeline.py — File browser, intake, and pipeline stage endpoints.
Routes:
    GET  /api/browse
    POST /api/intake
    POST /api/pipeline/<action>
    GET  /api/pipeline/status/<source_id>
"""

from pathlib import Path
from flask import Blueprint, jsonify, request
from config import RUNTIME_DIR, INGEST_ROOT, EXTRACT_CMD
from utils.helpers import load_json, run_command

pipeline_bp = Blueprint("pipeline", __name__)


@pipeline_bp.route("/api/browse")
def api_browse():
    path = request.args.get("path", "/mnt/archive").rstrip("/")
    try:
        p = Path(path)
        if not p.exists() or not p.is_dir():
            return jsonify({"error": "Path not found", "path": path}), 404

        entries = []
        for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            entries.append({
                "name":   item.name,
                "path":   str(item),
                "is_dir": item.is_dir(),
                "ext":    item.suffix.lower() if item.is_file() else None
            })

        parent = str(p.parent) if str(p) != "/" else None
        return jsonify({"path": str(p), "parent": parent, "entries": entries})

    except PermissionError:
        return jsonify({"error": "Permission denied", "path": path}), 403
    except Exception as e:
        return jsonify({"error": str(e), "path": path}), 500


@pipeline_bp.route("/api/intake", methods=["POST"])
def api_intake():
    data       = request.get_json()
    file_path  = data.get("path", "").strip()
    project_id = data.get("project_id", "").strip() or None

    if not file_path:
        return jsonify({"success": False, "error": "No path provided"}), 400

    cmd = f"python3 {RUNTIME_DIR}/cis_intake.py '{file_path}'"
    if project_id:
        cmd += f" --project '{project_id}'"

    result = run_command(cmd)
    return jsonify(result)


@pipeline_bp.route("/api/pipeline/<action>", methods=["POST"])
def api_pipeline(action):
    data      = request.get_json()
    source_id = data.get("source_id", "").strip()

    if not source_id:
        return jsonify({"success": False, "error": "No source_id provided"}), 400

    commands = {
        "classify":   f"python3 {RUNTIME_DIR}/cis_classify.py '{source_id}'",
        "preprocess": f"python3 {RUNTIME_DIR}/cis_preprocess.py '{source_id}'",
        "extract":    f"{EXTRACT_CMD} '{source_id}'",
        "normalize":  f"python3 {RUNTIME_DIR}/cis_normalize.py '{source_id}'",
    }

    if action not in commands:
        return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400

    result = run_command(commands[action])

    # Attach current manifest status if available
    manifest_path = INGEST_ROOT / source_id.lower() / "manifest.json"
    if manifest_path.exists():
        try:
            manifest = load_json(manifest_path)
            result["manifest_status"] = manifest.get("status", "unknown")
        except Exception:
            pass

    return jsonify(result)


@pipeline_bp.route("/api/pipeline/status/<source_id>")
def api_pipeline_status(source_id):
    manifest_path = INGEST_ROOT / source_id.lower() / "manifest.json"
    if not manifest_path.exists():
        return jsonify({"found": False}), 404

    try:
        manifest = load_json(manifest_path)
        return jsonify({
            "found":       True,
            "source_id":   source_id,
            "status":      manifest.get("status"),
            "source_name": manifest.get("source_name"),
            "history":     manifest.get("history", [])
        })
    except Exception as e:
        return jsonify({"found": False, "error": str(e)}), 500
