"""
api/ingest_spines.py — Extraction file ingestion endpoints for the CIS UI.
Routes:
    GET  /api/ingest-spines/status        — current counts and last run info
    POST /api/ingest-spines/run           — trigger ingestion (background)
    GET  /api/ingest-spines/files         — list source files with parse status
    GET  /api/ingest-spines/files/:file   — detailed parse result for one file
"""

import subprocess
import json
import threading
import time
import mimetypes
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file
from db.connection import db_connect

ingest_spines_bp = Blueprint("ingest_spines", __name__, url_prefix="/api/ingest-spines")

SCRIPT_PATH = Path("/mnt/projects/cis/runtime/scripts/ingest_extractions.py")
CIS_EXT_DIR = Path("/mnt/projects/cis/cis_kernel/extraction/functional_intents")
SWA_EXT_DIR = Path("/mnt/projects/social_work_ai/swa_kernel/extraction/functional_intents")

# ── Background run state ────────────────────────────────────────────────────
_run_state = {"running": False, "output": "", "progress": "", "started_at": None, "finished_at": None}


@ingest_spines_bp.route("/status")
def status():
    """Return current ingestion state and DB counts."""
    conn = db_connect()
    try:
        cis_spines = conn.execute(
            "SELECT COUNT(*) FROM knowledge_spines WHERE domain='CIS'"
        ).fetchone()[0]
        swa_spines = conn.execute(
            "SELECT COUNT(*) FROM knowledge_spines WHERE domain='SWA'"
        ).fetchone()[0]
        cis_nodes = conn.execute(
            "SELECT COALESCE(SUM(node_count), 0) FROM knowledge_spines WHERE domain='CIS'"
        ).fetchone()[0]
        swa_nodes = conn.execute(
            "SELECT COALESCE(SUM(node_count), 0) FROM knowledge_spines WHERE domain='SWA'"
        ).fetchone()[0]
        total_spines = cis_spines + swa_spines
        total_nodes = cis_nodes + swa_nodes

        # Source file counts
        cis_files = len(list(CIS_EXT_DIR.glob("*.md"))) if CIS_EXT_DIR.exists() else 0
        swa_files = len(list(SWA_EXT_DIR.glob("*.md"))) if SWA_EXT_DIR.exists() else 0

        return jsonify({
            "db": {
                "cis_spines": cis_spines,
                "swa_spines": swa_spines,
                "cis_nodes": cis_nodes,
                "swa_nodes": swa_nodes,
                "total_spines": total_spines,
                "total_nodes": total_nodes,
            },
            "source": {
                "cis_files": cis_files,
                "swa_files": swa_files,
                "total_source": cis_files + swa_files,
            },
            "run": {
                "running": _run_state["running"],
                "started_at": _run_state["started_at"],
                "finished_at": _run_state["finished_at"],
                "last_output": _run_state["output"][-2000:] if _run_state["output"] else "",
                "last_progress": _run_state["progress"],
            }
        })
    finally:
        conn.close()


@ingest_spines_bp.route("/run", methods=["POST"])
def run_ingestion():
    """Trigger extraction ingestion in background."""
    if _run_state["running"]:
        return jsonify({"error": "Already running"}), 409

    project = request.json.get("project", "") if request.json else ""

    def _run():
        _run_state["running"] = True
        _run_state["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        _run_state["output"] = ""
        _run_state["progress"] = "starting..."

        cmd = ["python3", str(SCRIPT_PATH)]
        if project == "cis":
            cmd.append("--project")
            cmd.append("cis")
        elif project == "swa":
            cmd.append("--project")
            cmd.append("swa")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            output = result.stdout + result.stderr
            _run_state["output"] = output
            # Extract summary line
            for line in output.split("\n"):
                if line.startswith("Summary:") or "Spines created" in line or "Files processed" in line:
                    _run_state["progress"] = line
            _run_state["progress"] = _run_state.get("progress", "completed")
        except subprocess.TimeoutExpired:
            _run_state["output"] = "TIMEOUT: Ingestion exceeded 10 minutes"
            _run_state["progress"] = "timed out"
        except Exception as e:
            _run_state["output"] = f"ERROR: {e}"
            _run_state["progress"] = f"error: {e}"
        finally:
            _run_state["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            _run_state["running"] = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"started": True, "project": project or "all"})


@ingest_spines_bp.route("/files")
def list_source_files():
    """List all extraction source files with their ingestion status."""
    conn = db_connect()
    try:
        files = []

        # CIS files
        if CIS_EXT_DIR.exists():
            for f in sorted(CIS_EXT_DIR.iterdir()):
                if f.suffix != ".md":
                    continue
                spine = conn.execute(
                    "SELECT spine_id, node_count, status, ingested_at FROM knowledge_spines WHERE file_path=?",
                    (str(f),)
                ).fetchone()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "project": "cis",
                    "ingested": spine is not None,
                    "spine_id": spine["spine_id"] if spine else None,
                    "node_count": spine["node_count"] if spine else 0,
                    "ingested_at": spine["ingested_at"] if spine else None,
                })

        # SWA files
        if SWA_EXT_DIR.exists():
            for f in sorted(SWA_EXT_DIR.iterdir()):
                if f.suffix != ".md":
                    continue
                spine = conn.execute(
                    "SELECT spine_id, node_count, status, ingested_at FROM knowledge_spines WHERE file_path=?",
                    (str(f),)
                ).fetchone()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "project": "swa",
                    "ingested": spine is not None,
                    "spine_id": spine["spine_id"] if spine else None,
                    "node_count": spine["node_count"] if spine else 0,
                    "ingested_at": spine["ingested_at"] if spine else None,
                })

        return jsonify({"files": files, "total": len(files)})
    finally:
        conn.close()


@ingest_spines_bp.route("/raw-file/<path:filename>")
def serve_raw_file(filename):
    """Serve the raw extraction file content."""
    project = request.args.get("project", "")
    if project == "cis":
        target = CIS_EXT_DIR / filename
        if target.exists() and target.is_file():
            mime, _ = mimetypes.guess_type(str(target))
            return send_file(str(target), mimetype=mime or "text/markdown")
    elif project == "swa":
        target = SWA_EXT_DIR / filename
        if target.exists() and target.is_file():
            mime, _ = mimetypes.guess_type(str(target))
            return send_file(str(target), mimetype=mime or "text/markdown")
    # Fallback: search both directories
    for d in [CIS_EXT_DIR, SWA_EXT_DIR]:
        target = d / filename
        if target.exists() and target.is_file():
            mime, _ = mimetypes.guess_type(str(target))
            return send_file(str(target), mimetype=mime or "text/markdown")
    return jsonify({"error": "File not found"}), 404


@ingest_spines_bp.route("/files/<path:filepath>")
def file_detail(filepath):
    """Return detailed parse info for a single extraction file."""
    # Resolve the file path
    candidates = [
        CIS_EXT_DIR / filepath,
        SWA_EXT_DIR / filepath,
        Path(filepath),
    ]
    target = None
    for c in candidates:
        if c.exists() and c.suffix == ".md":
            target = c
            break

    if not target:
        return jsonify({"error": "File not found"}), 404

    # Get the spine from DB
    conn = db_connect()
    try:
        spine = conn.execute(
            "SELECT * FROM knowledge_spines WHERE file_path=?", (str(target),)
        ).fetchone()
        if spine:
            nodes = conn.execute(
                "SELECT * FROM spine_nodes WHERE spine_id=? ORDER BY node_id",
                (spine["spine_id"],)
            ).fetchall()
            return jsonify({
                "file": target.name,
                "path": str(target),
                "project": "cis" if "/cis/" in str(target) else "swa",
                "spine": dict(spine),
                "nodes": [dict(n) for n in nodes],
            })
        else:
            return jsonify({
                "file": target.name,
                "path": str(target),
                "project": "cis" if "/cis/" in str(target) else "swa",
                "spine": None,
                "nodes": [],
            })
    finally:
        conn.close()
