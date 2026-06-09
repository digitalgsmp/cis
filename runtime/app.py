#!/usr/bin/env python3
"""
app.py — CIS Dashboard entry point.
Initialises Flask, registers all API blueprints, serves the frontend.

Usage:
    python3 /mnt/projects/cis/runtime/app.py

Access:
    http://localhost:5000
"""

from flask import Flask, jsonify, send_from_directory, request
import os
import sys
from config import RUNTIME_DIR

# Ensure runtime dir is in path for API blueprints
sys.path.insert(0, str(RUNTIME_DIR))

# ── Blueprint imports ──────────────────────────────────────────────────────────
from api.system          import system_bp
from api.projects        import projects_bp
from api.session         import session_bp
from api.tasks           import tasks_bp
from api.pipeline        import pipeline_bp
from api.records         import records_bp
from api.captures        import captures_bp
from api.decisions       import decisions_bp
from api.extraction_runs import extraction_runs_bp
from api.live            import live_bp
from api.models          import models_bp
from api.operator        import operator_bp          # ADR-044
from api.queue           import queue_bp             # ADR-045
from api.drafts import drafts_bp
from api.gpt import gpt_bp
from api.spines_api import spines_bp
from api.ingest_spines import ingest_spines_bp
from api.idea_uploads import idea_uploads_bp
from api.app_api import app_bp
from api.lms_api import lms_bp
from api.collab import collab_bp
from api.collab_rounds import collab_rounds_bp
from api.advisor import advisor_bp
from api.reconciliation import reconciliation_bp
from api.idea_drafts import idea_drafts_bp
from api.advisor_external import advisor_external_bp
from api.dam import dam_bp
from cis_ingest import create_api_blueprint


# ── Worker import ──────────────────────────────────────────────────────────────
from queue_worker import start_worker, worker_status  # ADR-045

# ── Memory system ─────────────────────────────────────────────────────────────
from memory.memory_store import MemoryStore
memory_store = MemoryStore()
memory_store.ensure_tables()

# ── Initialize app database ────────────────────────────────────────────────────
from cis_db import init_db
init_db()


# ── App init ───────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder=None)

CIS_API_KEY = os.environ.get("CIS_API_KEY", "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")

@app.before_request
def check_api_key():
    if request.path.startswith("/api/"):
        if request.remote_addr in ("127.0.0.1", "::1"):
            return None
        key = request.headers.get("X-CIS-API-Key")
        if key == CIS_API_KEY:
            return None
        return jsonify({"error": "Unauthorized"}), 401
    return None

# ── Register blueprints ────────────────────────────────────────────────────────
app.register_blueprint(system_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(session_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(pipeline_bp)
app.register_blueprint(records_bp)
app.register_blueprint(captures_bp)
app.register_blueprint(decisions_bp)
app.register_blueprint(extraction_runs_bp)
app.register_blueprint(live_bp)
app.register_blueprint(models_bp)
app.register_blueprint(operator_bp)                 # ADR-044
app.register_blueprint(queue_bp)                    # ADR-045
app.register_blueprint(drafts_bp)
app.register_blueprint(gpt_bp)
app.register_blueprint(spines_bp)
app.register_blueprint(ingest_spines_bp)
app.register_blueprint(idea_uploads_bp)
app.register_blueprint(app_bp)
app.register_blueprint(lms_bp)
app.register_blueprint(collab_bp)
app.register_blueprint(collab_rounds_bp)

# ── Ingestion API ─────────────────────────────────────────────────────────
ingest_bp = create_api_blueprint()
app.register_blueprint(ingest_bp)
app.register_blueprint(advisor_bp)
app.register_blueprint(reconciliation_bp)
app.register_blueprint(idea_drafts_bp)
app.register_blueprint(advisor_external_bp)
app.register_blueprint(dam_bp)

# ── Worker status route ────────────────────────────────────────────────────────

@app.route("/api/queue/worker-status")
def api_worker_status():
    """Return current queue worker state. Used by dashboard polling."""
    return jsonify(worker_status())

# ── Archive file server (before SPA catch-all) ─────────────────────────────────

import mimetypes as _mime
import os as _os
from flask import send_file as _send_file

ARCHIVE_ROOTS = ["/mnt/archive", "/mnt/projects"]

@app.route("/api/archive-file")
def serve_archive_file():
    file_path = request.args.get("path", "")
    if not file_path:
        return jsonify({"error": "path required"}), 400
    resolved = _os.path.abspath(file_path)
    allowed = any(resolved.startswith(_os.path.abspath(r)) for r in ARCHIVE_ROOTS)
    if not allowed:
        return jsonify({"error": "Access denied"}), 403
    if not _os.path.isfile(resolved):
        return jsonify({"error": "Not found"}), 404
    mtype, _ = _mime.guess_type(resolved)
    return _send_file(resolved, mimetype=mtype or "application/octet-stream")

# ── SPA catch-all — must be before more specific frontend routes ──────────

@app.route("/")
@app.route("/<path:path>")
def index(path=""):
    # Always inject basename script for root-level SPA serving
    ui_dist = RUNTIME_DIR / "ui" / "dist"
    target = ui_dist / path if path else None
    if target and target.exists() and target.is_file():
        return send_from_directory(str(ui_dist), path)
    # SPA fallback: read index.html and inject basename (empty for root serving)
    index_html = (ui_dist / "index.html").read_text(encoding="utf-8")
    index_html = index_html.replace(
        '<div id="root"></div>',
        '<script>window.__CIS_BASENAME__="";</script><div id="root"></div>'
    )
    from flask import make_response
    resp = make_response(index_html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


# ── Legacy frontend routes ─────────────────────────────────────────────────

@app.route("/project/<project_id>")
@app.route("/project/<project_id>/<panel>")
def project_view(project_id, panel="overview"):
    return send_from_directory(str(RUNTIME_DIR), "cis_dashboard.html")

# ── Kernel UI routes ──────────────────────────────────────────────────────

@app.route("/kernel")
def kernel_ui():
    return send_from_directory(str(RUNTIME_DIR / "ui_mockups"), "cis_kernel_v3.html")

@app.route("/kernel/components/<path:filename>")
def kernel_components(filename):
    return send_from_directory(str(RUNTIME_DIR / "ui_components"), filename)

@app.route("/workbench")
def workbench_ui():
    return send_from_directory(str(RUNTIME_DIR / "ui_mockups"), "cis_kernel_v3.html")

# ── React Flow UI routes ─────────────────────────────────────────────────

UI_DIR = RUNTIME_DIR / "ui" / "dist"

@app.route("/ui/")
@app.route("/ui/<path:filename>")
def reactflow_ui(filename="index.html"):
    # For client-side routing: if the file doesn't exist on disk, serve index.html
    ui_file = UI_DIR / filename
    if ui_file.exists() and ui_file.is_file():
        return send_from_directory(str(UI_DIR), filename)
    # SPA fallback with /ui basename
    index_html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    index_html = index_html.replace(
        '<div id="root"></div>',
        '<script>window.__CIS_BASENAME__="/ui";</script><div id="root"></div>'
    )
    from flask import make_response
    resp = make_response(index_html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 60)
    print("  CIS Dashboard — Modular Backend")
    print("  http://localhost:5000")
    print("═" * 60)
    start_worker()                                   # ADR-045 — queue worker
    app.run(host="0.0.0.0", port=5000, debug=False)
