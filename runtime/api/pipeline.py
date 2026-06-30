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


@pipeline_bp.route("/api/pipeline/roadmap")
def api_pipeline_roadmap():
    """Serve roadmap data from the CIS spine — single source of truth."""
    import sqlite3
    import yaml

    CIS_SPINE = "/mnt/projects/cis/data/cis_memory.db"
    CIS_STATIC = "/mnt/projects/cis/config/agents_static.yaml"

    result = {
        "built": [],
        "specified": [],
        "theorized": [],
        "phases": [],
        "adrs": [],
        "eric_vision": [],
        "current_phase": "",
    }

    try:
        conn = sqlite3.connect(CIS_SPINE)
        conn.row_factory = sqlite3.Row

        phase_row = conn.execute(
            "SELECT value FROM project_state WHERE key='build_phase'"
            " AND superseded_at IS NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if phase_row:
            result["current_phase"] = phase_row["value"]

        built = conn.execute(
            "SELECT node_label, tier FROM build_plan_nodes"
            " WHERE project_id='CIS' AND status='COMPLETE' ORDER BY sequence"
        ).fetchall()
        for b in built:
            result["built"].append({
                "title": b["node_label"],
                "desc": "",
                "date": b["tier"] or "",
            })

        specified = conn.execute(
            "SELECT node_label, tier, status FROM build_plan_nodes"
            " WHERE project_id='CIS' AND status IN ('PENDING','IN_PROGRESS')"
            " ORDER BY sequence"
        ).fetchall()
        for s in specified:
            result["specified"].append({
                "title": s["node_label"],
                "desc": "",
                "date": s["tier"] or "",
                "status": s["status"],
            })

        handoffs = conn.execute(
            "SELECT date, title, summary FROM session_handoffs"
            " WHERE is_current=1 ORDER BY created_at DESC LIMIT 3"
        ).fetchall()
        for h in handoffs:
            result["theorized"].append({
                "title": h["title"],
                "desc": h["summary"] or "",
                "date": h["date"] or "",
                "phase": "Handoff",
            })

        adrs = conn.execute(
            "SELECT id, label, decision FROM project_decisions"
            " WHERE id LIKE 'ADR-SEED-%' AND status != 'SUPERSEDED' ORDER BY id"
        ).fetchall()
        for a in adrs:
            result["adrs"].append({
                "id": a["id"].replace("ADR-SEED-", ""),
                "title": a["label"] or a["id"],
                "summary": a["decision"] or "",
            })

        conn.close()
    except Exception as e:
        result["error"] = str(e)

    try:
        with open(CIS_STATIC) as f:
            static = yaml.safe_load(f)
        seed = static.get("seed_intent", {})
        for excerpt in seed.get("excerpts", []):
            text = excerpt.get("text", "").strip()
            if text:
                first_line = text.split("\n")[0].strip()
                if first_line:
                    result["eric_vision"].append(first_line)
    except Exception:
        pass

    result["phases"] = [
        {"name": "Foundation", "range": "May 31 - Jun 6", "color": "#6b7280"},
        {"name": "Spine & Export", "range": "Jun 6 - 8", "color": "#3b82f6"},
        {"name": "MCP, VDB & UI", "range": "Jun 13", "color": "#8b5cf6"},
        {"name": "Pipeline Oversight", "range": "Jun 14 - 17", "color": "#10b981"},
        {"name": "Enforcement & Portal", "range": "Jun 18 - 23", "color": "#f59e0b"},
        {"name": "Pipeline Operations", "range": "Jun 27 - 29", "color": "#06b6d4"},
    ]

    return jsonify(result)
