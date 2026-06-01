"""
api/queue.py — Execution Queue Ownership Layer
ADR-045 Step 2

Routes:
    POST /api/queue/enqueue       — Add a job to the execution queue
    GET  /api/queue/status        — List all jobs (optionally filtered by status)
    GET  /api/queue/job/<job_id>  — Get detail for a single job
    POST /api/queue/cancel/<job_id> — Cancel a queued job

Job lifecycle: queued → running → complete | failed | cancelled

Valid job_types (Step 2): verify_contract | run_l2
Additional types added via future ADR only.

Governance: ADR-045, CIS_Execution_Layer_Contract_v1.md
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from db.connection import db_connect

queue_bp = Blueprint("queue", __name__)

VALID_JOB_TYPES = {"verify_contract", "run_l2"}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── POST /api/queue/enqueue ────────────────────────────────────────────────────

@queue_bp.route("/api/queue/enqueue", methods=["POST"])
def api_queue_enqueue():
    """
    Enqueue a new execution job.

    Required fields:
        job_type  — one of VALID_JOB_TYPES
        source    — identifying string for the originating route or operator

    Optional fields:
        payload   — JSON string of job-specific parameters
        priority  — integer, lower = higher priority (default 5)
    """
    data     = request.get_json() or {}
    job_type = data.get("job_type", "").strip()
    source   = data.get("source", "").strip()
    payload  = data.get("payload", None)
    priority = data.get("priority", 5)

    if not job_type:
        return jsonify({"success": False, "error": "job_type is required"}), 400
    if job_type not in VALID_JOB_TYPES:
        return jsonify({
            "success": False,
            "error": f"Unknown job_type '{job_type}'. Valid types: {sorted(VALID_JOB_TYPES)}"
        }), 400
    if not source:
        return jsonify({"success": False, "error": "source is required"}), 400

    conn = db_connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO execution_jobs
                (job_type, status, payload, source, priority, created_at)
            VALUES (?, 'queued', ?, ?, ?, ?)
            """,
            (job_type, payload, source, priority, _now())
        )
        conn.commit()
        job_id = cursor.lastrowid
        return jsonify({
            "success": True,
            "job_id":  job_id,
            "job_type": job_type,
            "status":  "queued",
            "created_at": _now()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── GET /api/queue/status ──────────────────────────────────────────────────────

@queue_bp.route("/api/queue/status")
def api_queue_status():
    """
    Return all jobs, optionally filtered by status.
    Query param: ?status=queued|running|complete|failed|cancelled
    Returns newest-first.
    """
    status_filter = request.args.get("status", None)

    conn = db_connect()
    try:
        if status_filter:
            rows = conn.execute(
                """
                SELECT id, job_type, status, source, priority,
                       created_at, started_at, completed_at, error
                FROM execution_jobs
                WHERE status = ?
                ORDER BY id DESC
                """,
                (status_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, job_type, status, source, priority,
                       created_at, started_at, completed_at, error
                FROM execution_jobs
                ORDER BY id DESC
                """
            ).fetchall()

        return jsonify({
            "count": len(rows),
            "filter": status_filter,
            "jobs": [dict(r) for r in rows]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── GET /api/queue/job/<job_id> ────────────────────────────────────────────────

@queue_bp.route("/api/queue/job/<int:job_id>")
def api_queue_job_detail(job_id):
    """
    Return full detail for a single job including payload and result.
    """
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT * FROM execution_jobs WHERE id = ?",
            (job_id,)
        ).fetchone()

        if not row:
            return jsonify({"found": False, "job_id": job_id}), 404

        return jsonify({"found": True, "job": dict(row)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


# ── POST /api/queue/cancel/<job_id> ───────────────────────────────────────────

@queue_bp.route("/api/queue/cancel/<int:job_id>", methods=["POST"])
def api_queue_cancel(job_id):
    """
    Cancel a job that is currently queued.
    Only queued jobs may be cancelled — running, complete, failed jobs are immutable.
    """
    conn = db_connect()
    try:
        row = conn.execute(
            "SELECT id, status FROM execution_jobs WHERE id = ?",
            (job_id,)
        ).fetchone()

        if not row:
            return jsonify({"success": False, "error": f"Job {job_id} not found"}), 404

        if row["status"] != "queued":
            return jsonify({
                "success": False,
                "error": f"Job {job_id} is '{row['status']}' — only queued jobs can be cancelled"
            }), 409

        conn.execute(
            "UPDATE execution_jobs SET status='cancelled', completed_at=? WHERE id=?",
            (_now(), job_id)
        )
        conn.commit()
        return jsonify({
            "success":  True,
            "job_id":   job_id,
            "status":   "cancelled",
            "completed_at": _now()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
