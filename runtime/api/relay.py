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


def _db(db_path: str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, timeout=10)
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


def _run_pipeline_background(run_id: str, intent: str, db_path: str = None) -> None:
    """Run pipeline_relay.py in a background thread (non-blocking).

    Accepts db_path for multi-project support (ADR-SEED-010).
    """
    import sys

    abstraction_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "abstraction",
    )
    if abstraction_dir not in sys.path:
        sys.path.insert(0, abstraction_dir)

    from pipeline_relay import PipelineRelay

    relay = PipelineRelay(db_path=db_path) if db_path else PipelineRelay()
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


@relay_bp.route("/api/relay/health", methods=["GET"])
def relay_health():
    """Health check — no auth required, used by container entrypoint."""
    from abstraction.dispatch import PROFILES, check_gateway
    gateways = {}
    for role, profile in PROFILES.items():
        healthy, error, latency = check_gateway(profile["port"])
        gateways[role] = {
            "port": profile["port"],
            "healthy": healthy,
            "latency_ms": round(latency * 1000) if latency else None,
            "error": error,
        }
    healthy_count = sum(1 for g in gateways.values() if g["healthy"])
    return jsonify({
        "status": "ok",
        "gateways": gateways,
        "gateways_healthy": healthy_count,
        "gateways_total": len(gateways),
    })


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

    # Multi-project support: look up project spine_path if project specified
    project_id = (data.get("project") or "").strip()
    project_db_path = None
    if project_id:
        conn = _db()
        try:
            row = conn.execute(
                "SELECT spine_path FROM projects WHERE id = ? AND status = 'active'",
                (project_id,),
            ).fetchone()
            if row:
                project_db_path = row["spine_path"]
            else:
                return jsonify({"error": f"Unknown project: {project_id}"}), 400
        finally:
            conn.close()

    # Idempotency: check for existing non-terminal run with same intent
    intent_hash = hashlib.sha256(intent.encode()).hexdigest()[:16]
    conn = _db(project_db_path) if project_db_path else _db()
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

    relay = PipelineRelay(db_path=project_db_path) if project_db_path else PipelineRelay()
    try:
        run_id = relay.start_sync(intent)
    finally:
        relay.close()

    # Start the async pipeline in a background thread
    thread = threading.Thread(
        target=_run_pipeline_background,
        args=(run_id, intent, project_db_path),
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
            "AND drafter_output != '' "
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
                "UPDATE workflow_runs SET status = 'PATTERN_CATALOG' WHERE id = ?",
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

        # If approved, trigger pattern catalog + code review in background
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
            "new_status": "PATTERN_CATALOG" if decision == "APPROVE" else
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


# ── Run List Endpoint ────────────────────────────────────────────────────


@relay_bp.route("/api/relay/runs", methods=["GET"])
def relay_list_runs():
    """List recent pipeline runs."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    limit = request.args.get("limit", 50, type=int)
    conn = _db()
    try:
        rows = conn.execute(
            """SELECT id, topic, status, created_at, rounds_completed, result
               FROM workflow_runs
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        runs = [
            {
                "id": r["id"],
                "topic": r["topic"][:200] if r["topic"] else "",
                "status": r["status"],
                "created_at": r["created_at"],
                "rounds_completed": r["rounds_completed"],
                "result": r["result"],
            }
            for r in rows
        ]
        return jsonify({"runs": runs, "count": len(runs)})
    finally:
        conn.close()


# ── KB Search Endpoints ──────────────────────────────────────────────────


@relay_bp.route("/api/relay/kb/search", methods=["GET"])
def relay_kb_search():
    """Search the knowledge base (FTS5 across 287K messages)."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    top_k = request.args.get("top_k", 10, type=int)
    conn = _db()
    try:
        rows = conn.execute(
            """SELECT content, source, role
               FROM knowledge_messages_fts
               WHERE knowledge_messages_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, top_k),
        ).fetchall()
        results = [
            {
                "content": r["content"][:500] if r["content"] else "",
                "source": r["source"],
                "role": r["role"],
            }
            for r in rows
        ]
        return jsonify({"query": query, "results": results, "count": len(results)})
    except sqlite3.OperationalError as e:
        return jsonify({"query": query, "results": [], "error": str(e)}), 200
    finally:
        conn.close()


@relay_bp.route("/api/relay/kb/decisions", methods=["GET"])
def relay_kb_decisions():
    """Return open project decisions (ADRs)."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            """SELECT label, decision, reason, status
               FROM project_decisions
               WHERE status IN ('DECIDED', 'OPEN')
               ORDER BY label"""
        ).fetchall()
        decisions = [dict(r) for r in rows]
        return jsonify({"decisions": decisions, "count": len(decisions)})
    finally:
        conn.close()


# ── Project Management Endpoints ─────────────────────────────────────────


@relay_bp.route("/api/projects", methods=["GET"])
def list_projects():
    """List all registered projects."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, name, repo_path, spine_path, agents_md_path, status, created_at "
            "FROM projects ORDER BY created_at"
        ).fetchall()
        projects = [dict(r) for r in rows]
        return jsonify({"projects": projects, "count": len(projects)})
    finally:
        conn.close()


@relay_bp.route("/api/projects", methods=["POST"])
def register_project():
    """Register a new project.

    Body: {id, name, repo_path, spine_path, agents_md_path?}
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    project_id = (data.get("id") or "").strip()
    name = (data.get("name") or "").strip()
    repo_path = (data.get("repo_path") or "").strip()
    spine_path = (data.get("spine_path") or "").strip()
    agents_md_path = (data.get("agents_md_path") or "").strip() or None

    if not all([project_id, name, repo_path, spine_path]):
        return jsonify({"error": "id, name, repo_path, spine_path are required"}), 400

    conn = _db()
    try:
        conn.execute(
            """INSERT OR REPLACE INTO projects (id, name, repo_path, spine_path, agents_md_path, status)
               VALUES (?, ?, ?, ?, ?, 'active')""",
            (project_id, name, repo_path, spine_path, agents_md_path),
        )
        conn.commit()
        return jsonify({
            "id": project_id,
            "name": name,
            "repo_path": repo_path,
            "spine_path": spine_path,
            "agents_md_path": agents_md_path,
            "status": "active",
        }), 201
    finally:
        conn.close()


# ── Task Decomposition Endpoints (Component 8) ──────────────────────────


@relay_bp.route("/api/relay/<run_id>/decompose", methods=["POST"])
def relay_decompose(run_id: str):
    """Split a run's directive into child runs.

    Body: {subtasks: [{intent: "...", depends_on: "child_id"?}, ...]}
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    subtasks = data.get("subtasks", [])
    if not subtasks:
        return jsonify({"error": "subtasks array required"}), 400

    conn = _db()
    try:
        parent = _get_run(conn, run_id)
        if not parent:
            return jsonify({"error": "Parent run not found"}), 404

        import sys as _sys
        sys_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "abstraction",
        )
        if sys_path not in _sys.path:
            _sys.path.insert(0, sys_path)
        from pipeline_relay import PipelineRelay

        relay = PipelineRelay()
        children = []
        try:
            for subtask in subtasks:
                sub_intent = subtask.get("intent", "").strip()
                if not sub_intent:
                    continue
                child_id = relay.start_sync(sub_intent)
                # Set parent_run_id
                conn.execute(
                    "UPDATE workflow_runs SET parent_run_id = ? WHERE id = ?",
                    (run_id, child_id),
                )
                # Set dependency if specified
                depends_on = subtask.get("depends_on")
                if depends_on:
                    conn.execute(
                        "INSERT OR IGNORE INTO run_dependencies (run_id, depends_on_run_id, dependency_type) VALUES (?, ?, 'sequential')",
                        (child_id, depends_on),
                    )
                children.append({"run_id": child_id, "intent": sub_intent[:100]})
            conn.commit()
        finally:
            relay.close()

        return jsonify({"parent_run_id": run_id, "children": children, "count": len(children)})
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/children", methods=["GET"])
def relay_children(run_id: str):
    """List child runs of a parent run."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            """SELECT id, topic, status, result, rounds_completed, created_at
               FROM workflow_runs
               WHERE parent_run_id = ?
               ORDER BY created_at""",
            (run_id,),
        ).fetchall()
        children = [dict(r) for r in rows]
        return jsonify({"parent_run_id": run_id, "children": children, "count": len(children)})
    finally:
        conn.close()


# ── Monitoring Endpoints (Component 12) ─────────────────────────────────


@relay_bp.route("/api/relay/metrics", methods=["GET"])
def relay_metrics():
    """Return pipeline metrics summary."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        # Total runs by status
        status_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM workflow_runs GROUP BY status"
        ).fetchall()
        runs_by_status = {r["status"]: r["cnt"] for r in status_rows}
        total_runs = sum(runs_by_status.values())

        # Average rounds
        avg_row = conn.execute(
            "SELECT AVG(rounds_completed) as avg FROM workflow_runs WHERE rounds_completed > 0"
        ).fetchone()
        avg_rounds = round(avg_row["avg"], 1) if avg_row and avg_row["avg"] else 0

        # Agent success rates
        agent_rows = conn.execute(
            "SELECT role, "
            "SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) as success, "
            "COUNT(*) as total "
            "FROM agent_trajectories GROUP BY role"
        ).fetchall()
        agent_rates = {}
        for r in agent_rows:
            total = r["total"] or 0
            success = r["success"] or 0
            agent_rates[r["role"]] = {
                "success": success,
                "total": total,
                "rate": round(success / total * 100, 1) if total > 0 else 0,
            }

        # Token totals
        token_row = conn.execute(
            "SELECT SUM(tokens_in) as tin, SUM(tokens_out) as tout FROM agent_trajectories"
        ).fetchone()
        total_tokens_in = token_row["tin"] or 0 if token_row else 0
        total_tokens_out = token_row["tout"] or 0 if token_row else 0

        # Dead letter queue count
        try:
            dlq_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM dead_letter_queue WHERE status='pending'"
            ).fetchone()
            dlq_pending = dlq_row["cnt"] if dlq_row else 0
        except Exception:
            dlq_pending = 0

        return jsonify({
            "total_runs": total_runs,
            "runs_by_status": runs_by_status,
            "avg_rounds": avg_rounds,
            "agent_success_rates": agent_rates,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "dlq_pending": dlq_pending,
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/errors", methods=["GET"])
def relay_errors(run_id: str):
    """Return error-level entries from agent trajectories."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, role, phase, substr(output_text, 1, 500) as output_preview, created_at "
            "FROM agent_trajectories WHERE run_id = ? AND outcome != 'success' "
            "ORDER BY id",
            (run_id,),
        ).fetchall()
        errors = [dict(r) for r in rows]
        return jsonify({"run_id": run_id, "errors": errors, "count": len(errors)})
    finally:
        conn.close()


@relay_bp.route("/api/relay/dlq", methods=["GET"])
def relay_dlq():
    """List pending dead letter queue entries."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, run_id, failed_at, error_message, phase, retry_count, status "
            "FROM dead_letter_queue WHERE status = 'pending' ORDER BY failed_at DESC"
        ).fetchall()
        entries = [dict(r) for r in rows]
        return jsonify({"dlq": entries, "count": len(entries)})
    except Exception:
        return jsonify({"dlq": [], "count": 0})
    finally:
        conn.close()


@relay_bp.route("/api/relay/guardrails", methods=["GET"])
def relay_guardrails():
    """Get guardrail outcomes for a run (or all recent)."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    run_id = request.args.get("run_id", "").strip()
    conn = _db()
    try:
        if run_id:
            rows = conn.execute(
                "SELECT id, run_id, phase, role, guardrail_name, verdict, mode, summary, timestamp "
                "FROM gate_outcomes WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, run_id, phase, role, guardrail_name, verdict, mode, summary, timestamp "
                "FROM gate_outcomes ORDER BY id DESC LIMIT 200",
            ).fetchall()
        outcomes = [dict(r) for r in rows]
        # Summary stats
        stats = {}
        for o in outcomes:
            key = o["guardrail_name"]
            if key not in stats:
                stats[key] = {"PASS": 0, "FAIL": 0, "SKIP": 0}
            verdict = o.get("verdict", "SKIP")
            if verdict in stats[key]:
                stats[key][verdict] += 1
        return jsonify({
            "outcomes": outcomes,
            "count": len(outcomes),
            "stats": stats,
            "gate_types": {
                "native": "Tier 1-4 Python guardrails (34 checks)",
                "external": "Tier 5 external gate scripts (ext_ prefix)",
            },
        })
    except Exception as e:
        return jsonify({"outcomes": [], "count": 0, "error": str(e)})
    finally:
        conn.close()
