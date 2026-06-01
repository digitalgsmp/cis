#!/usr/bin/env python3
"""
api/operator.py — CIS Operator Abstraction Layer (ADR-044)

Wraps high-friction execution tasks so the human never manually
generates manifests, computes hashes, constructs JSON, or routes
terminal output.

Routes:
    POST /api/operator/verify-contract   — Enqueue L1 + L2 for a contract file (ADR-045)
    POST /api/operator/slot1-start       — Start vLLM Slot 1
    GET  /api/operator/slot1-health      — Check Slot 1 health
    POST /api/operator/run-l2            — Enqueue L2 on last manifest (ADR-045)
    GET  /api/operator/next-action       — Return next required build action
    GET  /api/operator/flask-status      — Confirm Flask is running
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Blueprint, jsonify, request

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import PROJECTS_ROOT, RUNTIME_DIR
except ImportError:
    PROJECTS_ROOT = Path("/mnt/projects/cis")
    RUNTIME_DIR   = Path("/mnt/projects/cis/runtime")

from db.connection import db_connect

operator_bp = Blueprint("operator", __name__)

# ── Constants ──────────────────────────────────────────────────────────────────

CONTRACTS_DIR     = Path(PROJECTS_ROOT) / "docs" / "contracts"
LOGS_DIR          = Path(PROJECTS_ROOT) / "logs"
MANIFEST_PATH     = Path("/tmp/last_manifest.json")
VERIFY_SCRIPT     = Path(RUNTIME_DIR) / "cis_verify.py"
VERIFY_SEM_SCRIPT = Path(RUNTIME_DIR) / "cis_verify_semantic.py"
SLOT1_SCRIPT      = Path(RUNTIME_DIR) / "cis_vllm_slot1.sh"
SLOT1_URL         = "http://127.0.0.1:8001/v1/models"
VLLM_ENV          = Path("/mnt/models/vllm-env/bin/python3")

# ── Utilities ──────────────────────────────────────────────────────────────────

def ts_iso():
    return datetime.now(timezone.utc).isoformat()

def ts_session():
    return datetime.now(timezone.utc).strftime("%Y%m%d")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def slot1_is_healthy() -> bool:
    try:
        r = requests.get(SLOT1_URL, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def _enqueue(job_type: str, payload: dict, source: str) -> dict:
    """
    Insert a job into execution_jobs and return {success, job_id}.
    Internal helper — operator routes call this instead of run_script().
    """
    conn = db_connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO execution_jobs
                (job_type, status, payload, source, priority, created_at)
            VALUES (?, 'queued', ?, ?, 5, datetime('now'))
            """,
            (job_type, json.dumps(payload), source)
        )
        conn.commit()
        return {"success": True, "job_id": cursor.lastrowid}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def run_script(cmd: list, timeout: int = 120) -> dict:
    """Retained for slot1-start and any non-queue operations."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout":     result.stdout,
            "stderr":     result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -1, "stdout": "", "stderr": "Timeout expired."}
    except Exception as e:
        return {"returncode": -1, "stdout": "", "stderr": str(e)}

# ── Routes ─────────────────────────────────────────────────────────────────────

@operator_bp.route("/api/operator/verify-contract", methods=["POST"])
def verify_contract():
    """
    Enqueue a verify_contract job for a contract file.
    ADR-045: no longer executes directly — enqueues to execution_jobs.

    Body (JSON):
        { "file_path": "/mnt/projects/cis/docs/contracts/SomeContract.md" }

    Returns:
        { queued: true, job_id: N, file: "...", poll: "/api/queue/job/<N>" }
    """
    data      = request.get_json(force=True) or {}
    file_path = data.get("file_path", "").strip()

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    path = Path(file_path)
    if not path.exists():
        return jsonify({"error": f"File not found: {file_path}"}), 404

    result = _enqueue(
        job_type="verify_contract",
        payload={"contract_path": str(path)},
        source="api/operator/verify-contract"
    )

    if not result["success"]:
        return jsonify({"error": result["error"]}), 500

    job_id = result["job_id"]
    return jsonify({
        "queued":  True,
        "job_id":  job_id,
        "file":    str(path),
        "status":  "queued",
        "poll":    f"/api/queue/job/{job_id}",
        "message": "Job enqueued. Poll /api/queue/job/{} for result.".format(job_id)
    })


@operator_bp.route("/api/operator/slot1-health", methods=["GET"])
def slot1_health():
    up = slot1_is_healthy()
    return jsonify({"slot1_running": up, "status": "UP" if up else "DOWN"})


@operator_bp.route("/api/operator/slot1-start", methods=["POST"])
def slot1_start():
    """
    Attempts to start Slot 1 in the background.
    Returns immediately — client should poll /slot1-health.
    """
    if slot1_is_healthy():
        return jsonify({"status": "already_running", "message": "Slot 1 is already up."})
    try:
        subprocess.Popen(
            ["bash", str(SLOT1_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return jsonify({"status": "starting",
                        "message": "Slot 1 start initiated. Poll /api/operator/slot1-health."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@operator_bp.route("/api/operator/run-l2", methods=["POST"])
def run_l2():
    """
    Enqueue an L2 semantic verification job.
    ADR-045: no longer executes directly — enqueues to execution_jobs.

    Body (JSON):
        { "manifest_path": "/absolute/path/to/manifest.json" }

    Returns:
        { queued: true, job_id: N, poll: "/api/queue/job/<N>" }
    """
    data          = request.get_json(force=True) or {}
    manifest_path = data.get("manifest_path", "").strip()

    # Fall back to last_manifest.json if no path provided
    if not manifest_path:
        manifest_path = str(MANIFEST_PATH)

    if not Path(manifest_path).exists():
        return jsonify({"error": f"Manifest not found: {manifest_path}"}), 400

    if not slot1_is_healthy():
        return jsonify({
            "verdict": "BLOCKED",
            "message": "Slot 1 is not running. Start it first."
        }), 503

    result = _enqueue(
        job_type="run_l2",
        payload={"manifest_path": manifest_path},
        source="api/operator/run-l2"
    )

    if not result["success"]:
        return jsonify({"error": result["error"]}), 500

    job_id = result["job_id"]
    return jsonify({
        "queued":        True,
        "job_id":        job_id,
        "manifest_path": manifest_path,
        "status":        "queued",
        "poll":          f"/api/queue/job/{job_id}",
        "message":       "L2 job enqueued. Poll /api/queue/job/{} for result.".format(job_id)
    })


@operator_bp.route("/api/operator/next-action", methods=["GET"])
def next_action():
    """
    Returns the next required build action based on current system state.
    Reads the reorientation file for Next Steps.
    """
    reorientation = Path(PROJECTS_ROOT) / "handoff" / "2_CIS_REORIENTATION.md"
    if reorientation.exists():
        lines = reorientation.read_text().splitlines()
        in_next = False
        steps = []
        for line in lines:
            if "## Next Steps" in line or "Next Steps" in line:
                in_next = True
                continue
            if in_next:
                if line.startswith("##"):
                    break
                if line.strip():
                    steps.append(line.strip())
        return jsonify({"next_steps": steps[:5]})
    return jsonify({"next_steps": [
        "Reorientation file not found — drag handoff files to start session."
    ]})


@operator_bp.route("/api/operator/flask-status", methods=["GET"])
def flask_status():
    """
    Returns Flask runtime status.
    If this route responds, Flask is up.
    """
    import flask
    return jsonify({
        "status":        "UP",
        "flask_version": flask.__version__,
        "timestamp":     ts_iso(),
    })
