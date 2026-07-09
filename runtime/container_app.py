#!/usr/bin/env python3
"""
container_app.py — Minimal Flask app for the CIS pipeline container.
Only imports the relay blueprint (pipeline API). No legacy UI endpoints.

This avoids importing 30+ legacy blueprints with hardcoded host paths
that don't exist in the container filesystem.

Usage (inside container):
    python -c "from runtime.container_app import app; app.run(host='0.0.0.0', port=5000)"
"""

from flask import Flask, jsonify
import os, sys

# Ensure runtime dir is in path
RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if RUNTIME_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_DIR)

app = Flask(__name__)

# ── Register only the pipeline relay blueprint ─────────────────────────────────
from api.relay import relay_bp
app.register_blueprint(relay_bp)


# ── Health check ────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    from datetime import datetime, timezone
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "container": True
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
