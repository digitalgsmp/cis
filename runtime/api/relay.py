"""
api/relay.py — CIS Pipeline Relay API (production).

Per SPEC_PRODUCTION_PIPELINE_RELAY.md §6.4.
Wraps pipeline_relay.py (async state machine) behind Flask endpoints.

Endpoints:
    POST /api/relay/start              — submit intent, returns run_id
    GET  /api/relay/<run_id>           — current state, latest outputs
    POST /api/relay/<run_id>/answer    — Eric answers HUMAN_QUESTION
    POST /api/relay/<run_id>/gate      — Eric approves/rejects (immutable audit)
    GET  /api/relay/<run_id>/verify    — Verify's evidence report
    GET  /api/relay/<run_id>/trace     — full trajectory trace

Authentication: Bearer token via CIS_PIPELINE_API_KEY env var.
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

relay_bp = Blueprint("relay", __name__)

# ── Config ─────────────────────────────────────────────────────────────

DB_PATH = os.environ.get(
    "CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db"
)
API_KEY = os.environ.get("CIS_PIPELINE_API_KEY", "")

# ── Auth ────────────────────────────────────────────────────────────────


def _check_auth() -> Optional[tuple]:
    """Returns (error_response, status_code) if auth fails, None if OK."""
    if not API_KEY:
        return None  # Auth disabled when no key configured
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token == API_KEY:
            return None
    return (
        jsonify({"error": "Unauthorized", "detail": "Invalid or missing API key"}),
        401,
    )


# ── DB Helper ────────────────────────────────────────────────────────────


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def _get_run(conn: sqlite3.Connection, run_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT id, topic, status, created_at, directive_hash, "
        "rounds_completed, result "
        "FROM workflow_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    if not row:
        return None
    return dict(row)


def _get_rounds(conn: sqlite3.Connection, run_id: str) -> list:
    rows = conn.execute(
        "SELECT id, run_id, round_number, drafter_role, drafter_output, "
        "reviewer_role, reviewer_signal, reviewer1_output, reviewer2_output, "
        "brain_output, verify_output, human_question, human_answer, "
        "created_at "
        "FROM deliberation_rounds WHERE run_id = ? ORDER BY id",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _get_trajectories(conn: sqlite3.Connection, run_id: str) -> list:
    rows = conn.execute(
        "SELECT id, role, phase, round_number, outcome, "
        "substr(input_text, 1, 500) as input_preview, "
        "substr(output_text, 1, 500) as output_preview, "
        "created_at "
        "FROM agent_trajectories WHERE run_id = ? ORDER BY id",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ── Background Pipeline Runner ──────────────────────────────────────────

_active_runs: Dict[str, dict] = {}  # run_id → {thread, error, started_at}


def _run_pipeline_background(run_id: str, intent: str) -> None:
    """Run pipeline_relay.py in a background thread (non-blocking)."""
    import sys

    abstraction_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "abstraction",
    )
    if abstraction_dir not in sys.path:
        sys.path.insert(0, abstraction_dir)

    from pipeline_relay import PipelineRelay

    relay = PipelineRelay()
    try:
        asyncio.run(relay.resume(run_id))
    except Exception as e:
        _active_runs[run_id] = {
            **_active_runs.get(run_id, {}),
            "error": str(e),
        }
    finally:
        relay.close()
        _active_runs[run_id] = {
            **_active_runs.get(run_id, {}),
            "finished_at": time.time(),
        }


# ── Endpoints ───────────────────────────────────────────────────────────


@relay_bp.route("/api/relay/start", methods=["POST"])
def relay_start():
    """Submit intent to the pipeline relay. Returns run_id.

    Idempotent: same intent text within 1 hour returns existing non-terminal run.
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    intent = (data.get("intent") or "").strip()
    if not intent:
        return jsonify({"error": "intent required"}), 400

    # Idempotency: check for existing non-terminal run with same intent
    intent_hash = hashlib.sha256(intent.encode()).hexdigest()[:16]
    conn = _db()
    try:
        existing = conn.execute(
            "SELECT id, status FROM workflow_runs "
            "WHERE id LIKE ? AND status NOT IN "
            "('CONSENSUS_REACHED','ESCALATED','VERIFY_FAILED','STALE','ERROR') "
            "AND created_at > datetime('now', '-1 hour') "
            "ORDER BY created_at DESC LIMIT 1",
            (f"run-{intent_hash}%",),
        ).fetchone()
        if existing:
            return jsonify({
                "run_id": existing["id"],
                "status": existing["status"],
                "message": "Existing non-terminal run found for this intent",
            })
    finally:
        conn.close()

    # Create run via pipeline_relay
    sys_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "abstraction",
    )
    import sys as _sys
    if sys_path not in _sys.path:
        _sys.path.insert(0, sys_path)
    from pipeline_relay import PipelineRelay

    relay = PipelineRelay()
    try:
        run_id = relay.start_sync(intent)
    finally:
        relay.close()

    # Start the async pipeline in a background thread
    thread = threading.Thread(
        target=_run_pipeline_background,
        args=(run_id, intent),
        daemon=True,
    )
    _active_runs[run_id] = {
        "thread": thread,
        "started_at": time.time(),
    }
    thread.start()

    return jsonify({
        "run_id": run_id,
        "status": "BRAIN_PHASE",
        "message": "Pipeline started. Poll GET /api/relay/<run_id> for status.",
    })


@relay_bp.route("/api/relay/<run_id>", methods=["GET"])
def relay_status(run_id: str):
    """Get current state, latest outputs, and trajectory history."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    conn = _db()
    try:
        run = _get_run(conn, run_id)
        if not run:
            return jsonify({"error": "Run not found", "run_id": run_id}), 404

        rounds = _get_rounds(conn, run_id)
        trajectories = _get_trajectories(conn, run_id)

        # Build latest outputs — search across all rounds for latest non-empty value
        latest = rounds[-1] if rounds else {}
        active = _active_runs.get(run_id, {})

        def _latest_nonempty(field: str) -> Optional[str]:
            """Find the latest non-empty value for a field across all rounds."""
            for r in reversed(rounds):
                val = r.get(field)
                if val and val.strip():
                    return val
            return None

        return jsonify({
            "run_id": run["id"],
            "topic": run["topic"],
            "status": run["status"],
            "created_at": run["created_at"],
            "directive_hash": run.get("directive_hash"),
            "rounds_completed": run.get("rounds_completed", 0),
            "result": run.get("result"),
            "latest_phase": latest.get("drafter_role", ""),
            "latest_signal": latest.get("reviewer_signal", ""),
            "brain_output": _latest_nonempty("brain_output"),
            "drafter_output": _latest_nonempty("drafter_output"),
            "reviewer1_output": _latest_nonempty("reviewer1_output"),
            "reviewer2_output": _latest_nonempty("reviewer2_output"),
            "verify_output": _latest_nonempty("verify_output"),
            "human_question": _latest_nonempty("human_question"),
            "human_answer": _latest_nonempty("human_answer"),
            "rounds": [
                {
                    "id": r["id"],
                    "round": r["round_number"],
                    "phase": r["drafter_role"],
                    "signal": r["reviewer_signal"],
                    "created_at": r["created_at"],
                }
                for r in rounds
            ],
            "trajectories": trajectories,
            "background": {
                "active": run_id in _active_runs
                and "finished_at" not in active,
                "error": active.get("error"),
            },
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/answer", methods=["POST"])
def relay_answer(run_id: str):
    """Eric answers a HUMAN_QUESTION from Brain.

    Requires the run to be in WAITING_FOR_HUMAN state.
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip()
    if not answer:
        return jsonify({"error": "answer required"}), 400

    conn = _db()
    try:
        run = _get_run(conn, run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404

        # Store the answer
        conn.execute(
            "UPDATE deliberation_rounds SET human_answer = ? "
            "WHERE run_id = ? AND human_question IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (answer, run_id),
        )
        conn.execute(
            "UPDATE workflow_runs SET status = 'BRAIN_PHASE' "
            "WHERE id = ? AND status = 'WAITING_FOR_HUMAN'",
            (run_id,),
        )
        conn.commit()

        # Re-trigger Brain with the answer
        thread = threading.Thread(
            target=_run_pipeline_background,
            args=(run_id, run["topic"]),
            daemon=True,
        )
        _active_runs[run_id] = {
            "thread": thread,
            "started_at": time.time(),
        }
        thread.start()

        return jsonify({
            "run_id": run_id,
            "status": "BRAIN_PHASE",
            "message": "Answer injected, Brain re-dispatched",
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/gate", methods=["POST"])
def relay_gate(run_id: str):
    """Eric approves or rejects at the ERIC GATE.

    Immutable audit record: writes to eric_gate_approvals table.
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    decision = (data.get("decision") or "").strip().upper()
    rationale = (data.get("rationale") or "").strip()

    if decision not in ("APPROVE", "REJECT", "REVISE"):
        return jsonify({
            "error": "decision must be APPROVE, REJECT, or REVISE"
        }), 400

    conn = _db()
    try:
        run = _get_run(conn, run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404

        if run["status"] != "ERIC_GATE":
            return jsonify({
                "error": f"Run is not at ERIC_GATE (current: {run['status']})",
            }), 409

        now = datetime.now(timezone.utc).isoformat()

        # Get the directive (drafter_output from latest round)
        latest_round = conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_output IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        directive = latest_round["drafter_output"] if latest_round else ""

        # Freeze directive hash on approval
        directive_hash = None
        if decision == "APPROVE":
            directive_hash = hashlib.sha256(
                directive.encode()
            ).hexdigest()
            conn.execute(
                "UPDATE workflow_runs SET directive_hash = ? WHERE id = ?",
                (directive_hash, run_id),
            )

        # Write immutable audit record
        # Mark all previous approvals for this run as non-current
        conn.execute(
            "UPDATE eric_gate_approvals SET is_current = 0 "
            "WHERE workflow_run_id = ?",
            (run_id,),
        )
        # eric_gate_approvals requires goal_reference_id (NOT NULL)
        # and briefing_hash (NOT NULL) — use 0 and empty string as defaults
        conn.execute(
            "INSERT INTO eric_gate_approvals "
            "(workflow_run_id, decision, rationale, decided_at, "
            "goal_reference_id, briefing_hash, briefing_json, "
            "drift_snapshot_json, decision_trail_snapshot_json, "
            "is_current, created_at) "
            "VALUES (?, ?, ?, ?, 0, ?, '{}', '{}', '{}', 1, ?)",
            (run_id, decision, rationale, now,
             directive_hash or "", now),
        )

        # Update run status based on decision
        if decision == "APPROVE":
            conn.execute(
                "UPDATE workflow_runs SET status = 'EXECUTION' WHERE id = ?",
                (run_id,),
            )
        elif decision == "REJECT":
            conn.execute(
                "UPDATE workflow_runs SET status = 'ESCALATED' WHERE id = ?",
                (run_id,),
            )
        elif decision == "REVISE":
            conn.execute(
                "UPDATE workflow_runs SET status = 'DRAFT_PHASE' WHERE id = ?",
                (run_id,),
            )

        conn.commit()

        # If approved, trigger execution in background
        if decision == "APPROVE":
            thread = threading.Thread(
                target=_run_pipeline_background,
                args=(run_id, run["topic"]),
                daemon=True,
            )
            _active_runs[run_id] = {
                "thread": thread,
                "started_at": time.time(),
            }
            thread.start()

        return jsonify({
            "run_id": run_id,
            "decision": decision,
            "rationale": rationale,
            "decided_at": now,
            "directive_hash": directive_hash[:16] + "..." if directive_hash else None,
            "new_status": "EXECUTION" if decision == "APPROVE" else
                          "ESCALATED" if decision == "REJECT" else "DRAFT_PHASE",
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/verify", methods=["GET"])
def relay_verify(run_id: str):
    """Get Verify's evidence report."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    conn = _db()
    try:
        run = _get_run(conn, run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404

        # Get verify output from deliberation rounds
        row = conn.execute(
            "SELECT verify_output FROM deliberation_rounds "
            "WHERE run_id = ? AND verify_output IS NOT NULL "
            "ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()

        # Get verify trajectory
        traj = conn.execute(
            "SELECT output_text, outcome FROM agent_trajectories "
            "WHERE run_id = ? AND role = 'verify' "
            "ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()

        return jsonify({
            "run_id": run_id,
            "run_status": run["status"],
            "verify_output": row["verify_output"] if row else None,
            "verify_trajectory": dict(traj) if traj else None,
            "directive_hash": run.get("directive_hash"),
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/trace", methods=["GET"])
def relay_trace(run_id: str):
    """Full trajectory trace for debugging."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    conn = _db()
    try:
        run = _get_run(conn, run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404

        rounds = _get_rounds(conn, run_id)
        trajectories = _get_trajectories(conn, run_id)

        return jsonify({
            "run_id": run["id"],
            "topic": run["topic"],
            "status": run["status"],
            "created_at": run["created_at"],
            "directive_hash": run.get("directive_hash"),
            "rounds": rounds,
            "trajectories": trajectories,
        })
    finally:
        conn.close()
