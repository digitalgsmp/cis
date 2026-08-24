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

from flask import Flask, jsonify, send_from_directory, make_response, redirect, request
import os, sys

# Ensure runtime dir is in path
RUNTIME_DIR = os.path.dirname(os.path.abspath(__file__))
if RUNTIME_DIR not in sys.path:
    sys.path.insert(0, RUNTIME_DIR)

app = Flask(__name__, static_folder=None)

# ── Register only the pipeline relay blueprint ─────────────────────────────────
from api.relay import relay_bp
app.register_blueprint(relay_bp)

# ── Run start (lean, unconditional) ──────────────────────────────────────────
# Lean counterpart to POST /api/relay/start (api/relay.py:167): no mwl-proof-v2
# pre-flight, no 1-hour idempotency window. Every call creates a fresh
# workflow_runs row via PipelineRelay.start_sync and spawns the async pipeline
# in a background thread. Reuses api.relay's auth check, background runner,
# and _active_runs tracking — no duplication of those primitives.
import threading as _thread_mod
import time as _time_mod
from api.relay import _check_auth, _run_pipeline_background, _active_runs

@app.route("/api/relay/run", methods=["POST"])
def relay_run_start():
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    intent = (data.get("intent") or "").strip()
    if not intent:
        return jsonify({"error": "intent required"}), 400

    abstraction_dir = os.path.join(RUNTIME_DIR, "abstraction")
    if abstraction_dir not in sys.path:
        sys.path.insert(0, abstraction_dir)
    from pipeline_relay import PipelineRelay

    relay = PipelineRelay()
    try:
        run_id = relay.start_sync(intent)
        if not isinstance(run_id, str) or not run_id:
            raise RuntimeError(f"start_sync returned invalid run_id: {run_id!r}")
    except Exception as e:
        return jsonify({"error": f"Failed to create run: {e}"}), 500
    finally:
        relay.close()

    thread = _thread_mod.Thread(
        target=_run_pipeline_background,
        args=(run_id, intent),
        daemon=True,
    )
    _active_runs[run_id] = {"thread": thread, "started_at": _time_mod.time()}
    thread.start()

    return jsonify({
        "run_id": run_id,
        "status": "BRAIN_PHASE",
        "message": "Pipeline started. Poll GET /api/relay/<run_id> for status.",
    })

@app.route("/api/relay/ping", methods=["GET"])
def relay_ping():
    """Liveness probe: no auth, no DB, no gateway sweep. Returns exactly {"status": "ok"}."""
    return jsonify({"status": "ok"})

# ── React SPA (built to ui/dist/) ───────────────────────────────────────────────
UI_DIR = os.path.join(RUNTIME_DIR, "ui", "dist")

@app.route("/dashboard/")
def container_dashboard():
    """CIS Container Architecture Dashboard — standalone HTML page."""
    dash_path = os.path.join(RUNTIME_DIR, "ui", "public", "cis-container-dashboard.html")
    if os.path.isfile(dash_path):
        with open(dash_path, encoding="utf-8") as f:
            return f.read(), 200, {"Content-Type": "text/html; charset=utf-8"}
    return jsonify({"error": "Dashboard not found"}), 404

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
    """Get health of internal gateways and key services.
    Docker container management is NOT available from inside the contained worker
    — that would require docker socket access, which breaks the enforcement model.
    Container status is available via the host-side API at port 8642/system/health."""
    containers = []
    gateways = []
    services = []
    try:
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
    """Docker restart is NOT available from inside the contained worker.
    Container restart must be performed from the host side."""
    return jsonify({"error": "Docker restart not available from contained worker. Use host-side: sg docker -c 'docker restart <name>'"}), 403


@app.route("/api/relay/system/restart-all", methods=["POST"])
def _system_restart_all():
    """Docker restart is NOT available from inside the contained worker."""
    return jsonify({"error": "Docker restart not available from contained worker. Use host-side: sg docker -c 'docker restart <name>'"}), 403


@app.route("/api/relay/system/logs/<container>")
def _system_logs(container):
    """Docker logs are NOT available from inside the contained worker.
    Gateway logs are available at /tmp/cis-logs/<profile>.log inside the container."""
    # Gateway logs ARE accessible — they're local files, not docker commands
    log_map = {
        "cis-brainstorm": "/tmp/cis-logs/brain.log",
        "cis-drafter": "/tmp/cis-logs/draft.log",
        "cis-qwen-reviewer": "/tmp/cis-logs/review1.log",
        "cis-glm-reviewer": "/tmp/cis-logs/review2.log",
        "cis-implementer": "/tmp/cis-logs/menter.log",
        "cis-verifier": "/tmp/cis-logs/verify.log",
        "cis-pipeline": "/tmp/cis-logs/pipeline_api.log",
    }
    log_path = log_map.get(container)
    if not log_path:
        return jsonify({"error": f"Unknown container '{container}'. Available: {list(log_map.keys())}"}), 404
    try:
        with open(log_path, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()][-50:]
        return jsonify({"container": container, "lines": lines, "source": log_path})
    except FileNotFoundError:
        return jsonify({"error": f"Log file not found: {log_path}"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Enforcement Security Audit ────────────────────────────────────────────────
# Proves the containment model is intact by checking actual filesystem state.
# Every check is deterministic — no self-report, no trust, raw evidence only.

import stat as _stat_mod
import pwd as _pwd_mod
import grp as _grp_mod

def _check_file_owner(path):
    """Return (uid, gid, mode) for a path, or None if not found."""
    try:
        st = os.stat(path)
        return (st.st_uid, st.st_gid, st.st_mode)
    except OSError:
        return None

def _check_writable(path):
    """Check if the current process (worker) can write to this path."""
    return os.access(path, os.W_OK)

@app.route("/api/relay/system/security")
def _system_security():
    """Deterministic enforcement audit. Checks actual filesystem state to prove
    the container is secure and agents are guardrailed. No self-report — raw evidence."""
    checks = []
    all_pass = True

    def _add(name, passed, detail):
        nonlocal all_pass
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            all_pass = False

    # 1. Worker is non-root (UID must be 1000, not 0)
    uid = os.getuid()
    _add("Worker is non-root", uid != 0, f"UID={uid} ({_pwd_mod.getpwuid(uid).pw_name})")

    # 2. No docker socket accessible
    sock_exists = os.path.exists("/var/run/docker.sock")
    _add("No docker socket mounted", not sock_exists,
         "/var/run/docker.sock NOT present" if not sock_exists else "⚠ docker socket IS mounted — containment BROKEN")

    # 3. Worker not in docker group
    docker_groups = [g for g in os.getgroups()]
    docker_gids = [_grp_mod.getgrgid(g).gr_name for g in docker_groups if _grp_mod.getgrgid(g).gr_name == "docker"]
    _add("Worker not in docker group", len(docker_gids) == 0,
         f"Groups: {[_grp_mod.getgrgid(g).gr_name for g in docker_groups]}" if docker_groups else "No supplementary groups")

    # 4. Managed config is root-owned and worker can't write
    managed_cfg = "/etc/hermes/config.yaml"
    info = _check_file_owner(managed_cfg)
    if info:
        owner_uid, owner_gid, mode = info
        worker_writable = _check_writable(managed_cfg)
        _add("Managed config sealed (root-owned, worker RO)",
             owner_uid == 0 and not worker_writable,
             f"owner=uid:{owner_uid} mode:{oct(mode)} worker_writable={worker_writable}")
    else:
        _add("Managed config sealed", False, f"{managed_cfg} not found")

    # 5. Enforcement plugin is root-owned and worker can't write
    for profile in ["brain", "draft", "review1", "review2", "menter", "verify"]:
        plugin_path = f"/home/worker/.hermes-{profile}/plugins/mwl-proof"
        info = _check_file_owner(plugin_path)
        if info:
            owner_uid, _, mode = info
            worker_writable = _check_writable(plugin_path)
            _add(f"Plugin sealed: {profile}", owner_uid == 0 and not worker_writable,
                 f"owner=uid:{owner_uid} worker_writable={worker_writable}")
        else:
            _add(f"Plugin sealed: {profile}", False, f"{plugin_path} not found")

    # 6. Gate scripts are root-owned and worker can't write
    gates_dir = "/opt/cis-gates"
    if os.path.isdir(gates_dir):
        info = _check_file_owner(gates_dir)
        if info:
            owner_uid, _, mode = info
            worker_writable = _check_writable(gates_dir)
            _add("Gate scripts sealed (root-owned, worker RO)",
                 owner_uid == 0 and not worker_writable,
                 f"owner=uid:{owner_uid} mode:{oct(mode)} worker_writable={worker_writable}")
        else:
            _add("Gate scripts sealed", False, f"stat failed on {gates_dir}")
    else:
        _add("Gate scripts sealed", False, f"{gates_dir} not found")

    # 7. Hook consent baked into image env
    hooks_enabled = os.environ.get("HERMES_ACCEPT_HOOKS") == "1"
    managed_dir = os.environ.get("HERMES_MANAGED_DIR") == "/etc/hermes"
    _add("Hook consent baked (HERMES_ACCEPT_HOOKS=1)", hooks_enabled,
         f"HERMES_ACCEPT_HOOKS={os.environ.get('HERMES_ACCEPT_HOOKS', '<unset>')}")
    _add("Managed scope baked (HERMES_MANAGED_DIR=/etc/hermes)", managed_dir,
         f"HERMES_MANAGED_DIR={os.environ.get('HERMES_MANAGED_DIR', '<unset>')}")

    # 8. Entry point script is read-only (bind-mounted RO from host or root-owned in image)
    entrypoint = "/opt/cis-control/entrypoint.sh"
    info = _check_file_owner(entrypoint)
    if info:
        owner_uid, _, mode = info
        worker_writable = _check_writable(entrypoint)
        # Pass if worker can't write to it — either root-owned OR bind-mounted RO
        _add("Entrypoint sealed (worker cannot modify)",
             not worker_writable,
             f"owner=uid:{owner_uid} mode:{oct(mode)} worker_writable={worker_writable}")
    else:
        _add("Entrypoint sealed", False, f"{entrypoint} not found")

    return jsonify({
        "enforcement_intact": all_pass,
        "checks": checks,
        "passed": sum(1 for c in checks if c["passed"]),
        "failed": sum(1 for c in checks if not c["passed"]),
        "total": len(checks),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)