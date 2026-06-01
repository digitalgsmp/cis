"""
api/system.py — System status endpoint.
Route: GET /api/status
"""

from flask import Blueprint, jsonify
from config import RECORDS_ROOT
from db.connection import db_connect, ensure_tables, ensure_phase1_tables
from utils.helpers import ts
from utils.project_helpers import get_all_projects

system_bp = Blueprint("system", __name__)


@system_bp.route("/api/status")
def api_status():
    record_count  = sum(1 for _ in RECORDS_ROOT.rglob("*.json")) if RECORDS_ROOT.exists() else 0
    project_count = len(get_all_projects())

    conn = db_connect()
    ensure_tables(conn)
    ensure_phase1_tables(conn)
    open_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0]
    conn.close()

    return jsonify({
        "status":    "online",
        "timestamp": ts(),
        "counts": {
            "records":    record_count,
            "projects":   project_count,
            "open_tasks": open_tasks
        }
    })


@system_bp.route("/api/system/health")
def api_system_health():
    conn = db_connect()
    try:
        conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    finally:
        conn.close()
    return jsonify({"status": "ok", "database": db_ok})


@system_bp.route("/api/system/extraction-stats")
def api_extraction_stats():
    import os
    cis_dir = "/mnt/projects/cis/cis_kernel/extraction/functional_intents"
    swa_dir = "/mnt/projects/social_work_ai/swa_kernel/extraction/functional_intents"
    cis_count = len(os.listdir(cis_dir)) if os.path.isdir(cis_dir) else 0
    swa_count = len(os.listdir(swa_dir)) if os.path.isdir(swa_dir) else 0
    return jsonify({
        "cis": cis_count,
        "swa": swa_count,
        "indexed": False,
        "total": cis_count + swa_count
    })


@system_bp.route("/api/system/scratchpad")
def api_scratchpad():
    import re
    scratch_path = "/mnt/projects/cis/cis_kernel/build/CIS_SCRATCHPAD.md"
    ideas = []
    decisions = []
    todos = []
    try:
        with open(scratch_path) as f:
            text = f.read()
        current_section = None
        for line in text.split("\n"):
            if line.startswith("## Ideas"):
                current_section = "ideas"
            elif line.startswith("## Decisions"):
                current_section = "decisions"
            elif line.startswith("## Things To Build"):
                current_section = "todos"
            elif line.startswith("## "):
                current_section = None
            elif current_section == "ideas" and line.strip().startswith("- "):
                ideas.append(line.strip()[2:])
            elif current_section == "decisions" and line.strip().startswith("- "):
                decisions.append(line.strip()[2:])
            elif current_section == "todos" and line.strip().startswith("- "):
                todos.append(line.strip()[2:])
    except FileNotFoundError:
        pass
    return jsonify({"ideas": ideas, "decisions": decisions, "todos": todos})
