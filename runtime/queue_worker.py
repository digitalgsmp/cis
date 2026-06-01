"""
queue_worker.py — CIS Execution Queue Worker
ADR-045 Step 3

Single-threaded FIFO background worker. Started automatically by Flask on
app startup. Polls execution_jobs table for queued work. Executes one job
at a time. Hardware constraint intentional — ADR-045.

Job types handled:
    verify_contract — run cis_verify.py against a contract file
    run_l2          — run cis_verify_semantic.py against a manifest

Worker lifecycle:
    - Started via start_worker() called from app.py after blueprint registration
    - Runs as a daemon thread — stops automatically when Flask exits
    - Restarts itself after each job (poll loop continues)
    - On cold start: any 'running' jobs from prior crash are reset to 'queued'

Governance: ADR-045, CIS_Execution_Layer_Contract_v1.md,
            CIS_Automation_Reduction_Contract_v1.md
"""

import json
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import sqlite3
from config import DB_PATH, RUNTIME_DIR

POLL_INTERVAL  = 3      # seconds between polls when queue is empty
JOB_TIMEOUT    = 120    # seconds before a running job is considered hung

_worker_thread  = None
_worker_running = False
_worker_status  = {
    "state":       "stopped",   # stopped | idle | running
    "current_job": None,
    "last_poll":   None,
    "last_job_id": None,
    "last_result": None,
    "started_at":  None,
}


# ── Public API ─────────────────────────────────────────────────────────────────

def start_worker():
    """
    Start the background worker thread. Called once from app.py on startup.
    Idempotent — safe to call multiple times.
    """
    global _worker_thread, _worker_running

    if _worker_thread and _worker_thread.is_alive():
        return  # Already running

    _worker_running = True
    _worker_thread  = threading.Thread(
        target=_worker_loop,
        name="cis-queue-worker",
        daemon=True
    )
    _worker_thread.start()
    _worker_status["state"]      = "idle"
    _worker_status["started_at"] = _now()
    print(f"[CIS Worker] Started at {_worker_status['started_at']}")


def stop_worker():
    """Signal the worker to stop after the current job completes."""
    global _worker_running
    _worker_running = False
    _worker_status["state"] = "stopped"


def worker_status():
    """Return current worker status dict. Used by /api/queue/worker-status route."""
    return {
        **_worker_status,
        "thread_alive": _worker_thread.is_alive() if _worker_thread else False,
    }


# ── Internal worker loop ───────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _db():
    """Open a fresh DB connection for worker use."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _recover_crashed_jobs():
    """
    On startup, reset any jobs stuck in 'running' state from a prior crash.
    Prevents permanent job blockage after unexpected Flask exit.
    """
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id FROM execution_jobs WHERE status='running'"
        ).fetchall()
        if rows:
            conn.execute(
                "UPDATE execution_jobs SET status='queued', started_at=NULL "
                "WHERE status='running'"
            )
            conn.commit()
            print(f"[CIS Worker] Cold-start recovery: reset {len(rows)} stuck job(s) to queued")
    finally:
        conn.close()


def _claim_next_job():
    """
    Claim the next queued job atomically. Returns the job row or None.
    Uses priority ASC, id ASC ordering — lower priority number runs first,
    FIFO within same priority.
    """
    conn = _db()
    try:
        row = conn.execute(
            """
            SELECT * FROM execution_jobs
            WHERE status = 'queued'
            ORDER BY priority ASC, id ASC
            LIMIT 1
            """
        ).fetchone()

        if not row:
            return None, conn

        conn.execute(
            "UPDATE execution_jobs SET status='running', started_at=? WHERE id=?",
            (_now(), row["id"])
        )
        conn.commit()
        return dict(row), conn
    except Exception:
        conn.close()
        return None, None


def _complete_job(conn, job_id, result):
    try:
        conn.execute(
            "UPDATE execution_jobs SET status='complete', result=?, completed_at=? WHERE id=?",
            (json.dumps(result), _now(), job_id)
        )
        conn.commit()
    finally:
        conn.close()


def _fail_job(conn, job_id, error):
    try:
        conn.execute(
            "UPDATE execution_jobs SET status='failed', error=?, completed_at=? WHERE id=?",
            (str(error), _now(), job_id)
        )
        conn.commit()
    finally:
        conn.close()


def _worker_loop():
    """Main poll loop. Runs until stop_worker() is called."""
    print("[CIS Worker] Loop started — recovering crashed jobs")
    _recover_crashed_jobs()

    while _worker_running:
        _worker_status["last_poll"] = _now()

        job, conn = _claim_next_job()

        if not job:
            _worker_status["state"]       = "idle"
            _worker_status["current_job"] = None
            time.sleep(POLL_INTERVAL)
            continue

        job_id   = job["id"]
        job_type = job["job_type"]
        payload  = json.loads(job["payload"]) if job.get("payload") else {}

        _worker_status["state"]       = "running"
        _worker_status["current_job"] = job_id
        _worker_status["last_job_id"] = job_id
        print(f"[CIS Worker] Starting job {job_id} type={job_type}")

        try:
            result = _dispatch(job_type, payload)
            _complete_job(conn, job_id, result)
            _worker_status["last_result"] = "complete"
            print(f"[CIS Worker] Job {job_id} complete")
        except Exception as e:
            _fail_job(conn, job_id, str(e))
            _worker_status["last_result"] = f"failed: {e}"
            print(f"[CIS Worker] Job {job_id} failed: {e}")

        _worker_status["state"]       = "idle"
        _worker_status["current_job"] = None


# ── Job dispatcher ─────────────────────────────────────────────────────────────

def _dispatch(job_type, payload):
    """Route job_type to its handler. Returns result dict."""
    if job_type == "verify_contract":
        return _run_verify_contract(payload)
    elif job_type == "run_l2":
        return _run_l2(payload)
    else:
        raise ValueError(f"Unknown job_type: {job_type}")


def _run_verify_contract(payload):
    """
    Run cis_verify.py against a contract file.
    Payload: { "contract_path": "/absolute/path/to/contract.md" }
    """
    import hashlib
    contract_path = payload.get("contract_path", "")
    if not contract_path:
        raise ValueError("verify_contract requires contract_path in payload")

    path = Path(contract_path)
    if not path.exists():
        raise ValueError(f"Contract file not found: {contract_path}")

    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    session_id  = datetime.now(timezone.utc).strftime("%Y%m%d")
    artifact_id = f"contract__{path.stem}__{session_id}__001"
    manifest = {
        "action": f"Verify {path.name} — Queue worker (ADR-045)",
        "timestamp": _now(),
        "artifact_identity": {
            "artifact_id": artifact_id, "artifact_type": "contract",
            "artifact_name": path.stem, "artifact_path": str(path),
            "sha256": sha, "timestamp": _now(),
            "session_id": session_id, "sequence": 1,
            "builder_model_id": "claude-sonnet-4-6",
        },
        "dependencies": [],
        "files_written": [{"path": str(path), "min_size": 50,
            "min_size_unit": "lines", "sha256": sha, "key_markers": ["LOCKED"]}],
    }
    manifest_path = Path("/tmp") / f"manifest_{artifact_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    verify_script = RUNTIME_DIR / "cis_verify.py"
    cmd = ["python3", str(verify_script), "--manifest", str(manifest_path), "--log"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=JOB_TIMEOUT
    )
    return {
        "exit_code": result.returncode,
        "stdout":    result.stdout[-4000:] if result.stdout else "",
        "stderr":    result.stderr[-2000:] if result.stderr else "",
        "passed":    result.returncode == 0
    }


def _run_l2(payload):
    """
    Run cis_verify_semantic.py against a manifest file.
    Payload: { "manifest_path": "/absolute/path/to/manifest.json" }
    File path is extracted from manifest files_written[0].path
    """
    manifest_path = payload.get("manifest_path", "")
    if not manifest_path:
        raise ValueError("run_l2 requires manifest_path in payload")

    # Extract file path from manifest
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        files_written = manifest.get("files_written", [])
        if not files_written:
            raise ValueError("Manifest has no files_written entries")
        first = files_written[0]
        file_path = first if isinstance(first, str) else first.get("path", "")
        if not file_path:
            raise ValueError("Could not extract file path from manifest files_written")
    except Exception as e:
        raise ValueError(f"Failed to read manifest: {e}")

    verify_script = RUNTIME_DIR / "cis_verify_semantic.py"
    cmd = ["python3", str(verify_script),
           "--manifest", manifest_path,
           "--file", file_path,
           "--log"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=JOB_TIMEOUT
    )
    return {
        "exit_code": result.returncode,
        "stdout":    result.stdout[-4000:] if result.stdout else "",
        "stderr":    result.stderr[-2000:] if result.stderr else "",
        "passed":    result.returncode == 0
    }