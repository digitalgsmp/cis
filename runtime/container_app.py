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

@app.route("/health")
def health_alias():
    """Alias for gate_service_health.sh which checks /health on the port."""
    return health()

@app.route("/api/ping")
def ping():
    return jsonify({"status": "pong"})

# ── System Dashboard ───────────────────────────────────────────────────────────
import subprocess as _subproc
import re as _re_mod

# Internal gateway ports (inside this container) — the actual pipeline gateways
_GATEWAY_PORTS = {
    "Brain":        (8644, "deepseek-v4-pro"),
    "Draft":        (8645, "deepseek-v4-pro"),
    "Review1":      (8643, "qwen3.7-max"),
    "Review2":      (8647, "glm-5.2"),
    "Menter":       (8646, "deepseek-v4-pro"),
    "Verify":       (8648, "glm-5.2"),
}

@app.route("/api/relay/system/health")
def _system_health():
    """Get health of Docker containers, internal gateways, and key services."""
    containers = []
    gateways = []
    services = []
    try:
        # ── Docker container overview (via docker ps) ───────────────────────
        result = _subproc.run(
            ["docker", "ps", "-a", "--format",
             "{{.Names}}\t{{.Status}}\t{{.Image}}\t{{.Ports}}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                name = parts[0] if len(parts) > 0 else ""
                status_raw = parts[1] if len(parts) > 1 else ""
                image = parts[2] if len(parts) > 2 else ""
                ports = parts[3] if len(parts) > 3 else ""
                is_running = status_raw.startswith("Up")
                health = ""
                healthy = True
                if "unhealthy" in status_raw.lower():
                    health = "unhealthy"
                    healthy = False
                elif "healthy" in status_raw.lower():
                    health = "healthy"
                uptime = ""
                if is_running:
                    uptime = status_raw.replace("Up ", "").split(" (")[0]
                containers.append({
                    "name": name,
                    "status": "running" if is_running else "stopped",
                    "health": health,
                    "healthy": healthy if is_running else False,
                    "image": image[:60],
                    "uptime": uptime,
                    "ports": ports[:80] if ports else "",
                })

        # ── Internal gateway health (127.0.0.1:864x — the real gateways) ──
        for label, (port, model) in _GATEWAY_PORTS.items():
            try:
                hresult = _subproc.run(
                    ["curl", "-s", "--max-time", "3", f"http://127.0.0.1:{port}/health"],
                    capture_output=True, text=True, timeout=5
                )
                ok = hresult.returncode == 0 and "ok" in hresult.stdout.lower()
                gateways.append({
                    "name": label,
                    "port": port,
                    "model": model,
                    "healthy": ok,
                })
            except Exception:
                gateways.append({"name": label, "port": port, "model": model, "healthy": False})

        # ── SQLite spine ────────────────────────────────────────────────────
        try:
            import sqlite3 as _sq3
            db_path = os.environ.get("CIS_DB_PATH", "/workspace/cis/data/cis_memory.db")
            if not os.path.exists(db_path):
                db_path = "/mnt/projects/cis/data/cis_memory.db"
            _conn = _sq3.connect(db_path, timeout=2)
            _conn.execute("SELECT 1")
            _conn.close()
            services.append({"name": "SQLite Spine", "healthy": True, "detail": db_path})
        except Exception as e:
            services.append({"name": "SQLite Spine", "healthy": False, "detail": str(e)})

        # ── GLM/Qwen llama-servers ──────────────────────────────────────────
        for label, port in [("GLM llama-server", 8001), ("Qwen llama-server", 8002)]:
            try:
                hresult = _subproc.run(
                    ["curl", "-s", "--max-time", "3", f"http://localhost:{port}/health"],
                    capture_output=True, text=True, timeout=5
                )
                services.append({"name": label, "healthy": hresult.returncode == 0, "url": f"localhost:{port}"})
            except Exception:
                services.append({"name": label, "healthy": False, "url": f"localhost:{port}"})

        # ── ChromaDB ────────────────────────────────────────────────────────
        try:
            hresult = _subproc.run(
                ["curl", "-s", "--max-time", "3", "http://localhost:8000/api/v1/heartbeat"],
                capture_output=True, text=True, timeout=5
            )
            services.append({"name": "ChromaDB", "healthy": hresult.returncode == 0 and "nanosecond" in hresult.stdout.lower(), "url": "localhost:8000"})
        except Exception:
            services.append({"name": "ChromaDB", "healthy": False, "url": "localhost:8000"})

    except Exception as e:
        return jsonify({"error": str(e), "containers": containers, "gateways": gateways, "services": services}), 500
    return jsonify({"containers": containers, "gateways": gateways, "services": services})


@app.route("/api/relay/system/restart", methods=["POST"])
def _system_restart():
    from flask import request as _req
    data = _req.get_json(silent=True) or {}
    container = data.get("container", "")
    if not container:
        return jsonify({"error": "container name required"}), 400
    allowed = ["cis-pipeline", "cis-hermes", "cis-brainstorm", "cis-drafter",
               "cis-qwen-reviewer", "cis-glm-reviewer", "cis-implementer", "cis-verifier"]
    if container not in allowed:
        return jsonify({"error": f"container '{container}' not in whitelist"}), 403
    # Self-restart: return success first, then restart asynchronously
    if container == "cis-pipeline":
        import threading
        def _delayed_restart():
            import time as _time
            _time.sleep(0.5)
            _subproc.run(["docker", "restart", container], capture_output=True, text=True, timeout=60)
        threading.Thread(target=_delayed_restart, daemon=True).start()
        return jsonify({"status": "ok", "container": container, "note": "self-restart scheduled"})
    try:
        result = _subproc.run(["docker", "restart", container], capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return jsonify({"status": "ok", "container": container})
        return jsonify({"error": result.stderr.strip()}), 500
    except _subproc.TimeoutExpired:
        return jsonify({"error": "restart timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/relay/system/restart-all", methods=["POST"])
def _system_restart_all():
    order = ["cis-hermes", "cis-brainstorm", "cis-drafter",
             "cis-qwen-reviewer", "cis-glm-reviewer", "cis-implementer",
             "cis-verifier", "cis-pipeline"]
    results = []
    for name in order:
        try:
            result = _subproc.run(["docker", "restart", name], capture_output=True, text=True, timeout=60)
            results.append({"container": name, "status": "ok" if result.returncode == 0 else "error"})
        except Exception as e:
            results.append({"container": name, "status": "error", "error": str(e)})
    return jsonify({"results": results})


@app.route("/api/relay/system/logs/<container>")
def _system_logs(container):
    allowed = ["cis-pipeline", "cis-hermes", "cis-brainstorm", "cis-drafter",
               "cis-qwen-reviewer", "cis-glm-reviewer", "cis-implementer", "cis-verifier"]
    if container not in allowed:
        return jsonify({"error": "container not in whitelist"}), 403
    try:
        result = _subproc.run(
            ["docker", "logs", "--tail", "50", container],
            capture_output=True, text=True, timeout=10
        )
        lines = [l for l in (result.stdout + result.stderr).strip().split("\n") if l.strip()][-50:]
        return jsonify({"container": container, "lines": lines})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
