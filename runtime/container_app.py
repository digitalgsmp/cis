#!/usr/bin/env python3
# Pipeline fixed and operational
# CIS pipeline container entry point — it works
"""
container_app.py — Minimal Flask app for the CIS pipeline container.
Only imports the relay blueprint (pipeline API). No legacy UI endpoints.

This avoids importing 30+ legacy blueprints with hardcoded host paths
that don't exist in the container filesystem.

Usage (inside container):
    python -c "from runtime.container_app import app; app.run(host='0.0.0.0', port=5000)"
"""

from flask import Flask, jsonify, send_from_directory, make_response, redirect
import os, sys

# Ensure runtime dir is in path
RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if RUNTIME_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_DIR)

app = Flask(__name__, static_folder=None)

# ── Register only the pipeline relay blueprint ─────────────────────────────────
from api.relay import relay_bp
app.register_blueprint(relay_bp)

# ── React SPA (built to ui/dist/) ───────────────────────────────────────────────
UI_DIR = os.path.join(RUNTIME_DIR, "ui", "dist")

@app.route("/ui/")
@app.route("/ui/<path:filename>")
def reactflow_ui(filename="index.html"):
    ui_file = os.path.join(UI_DIR, filename)
    if os.path.isfile(ui_file):
        return send_from_directory(UI_DIR, filename)
    # SPA fallback — serve index.html for client-side routes
    index_path = os.path.join(UI_DIR, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as f:
            index_html = f.read()
        index_html = index_html.replace(
            '<div id="root"></div>',
            '<script>window.__CIS_BASENAME__="/ui";</script><div id="root"></div>'
        )
        resp = make_response(index_html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        return resp
    return jsonify({"error": "UI not built. Run: cd runtime/ui && npm run build"}), 404

@app.route("/")
def root_redirect():
    return redirect("/ui/")

# ── Health check ────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    from datetime import datetime, timezone
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container": True
    })

@app.route("/api/ping")
def ping():
    return jsonify({"status": "pong"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
