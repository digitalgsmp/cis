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
import sys
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

    # ── Pre-flight intent validation ──────────────────────────────────
    # Expert pushback: check intent against containment rules and project goals
    # BEFORE spending any API tokens. Blocks critical violations, warns on risky ones.
    import subprocess as _pf_subproc
    pf_script = os.path.join(os.environ.get("CIS_PROJECT_ROOT", "/workspace/cis"),
                             "enforcement", "mwl-proof-v2", "pre_flight_check.py")
    if os.path.isfile(pf_script):
        try:
            pf_result = _pf_subproc.run(
                [sys.executable, pf_script, intent],
                capture_output=True, text=True, timeout=10
            )
            if pf_result.returncode == 2:
                # Blocked — critical violation
                return jsonify({
                    "error": "Intent blocked by pre-flight check",
                    "details": pf_result.stdout.strip(),
                    "blocked": True,
                }), 403
            # returncode 1 = warnings (allow but include them)
            # returncode 0 = clean approve
        except Exception:
            pass  # If pre-flight fails, don't block the run — fail open

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


def _get_stop_reason(conn: sqlite3.Connection, run_id: str) -> Optional[dict]:
    """The phase that halted the run and why. None if it did not halt."""
    try:
        row = conn.execute(
            "SELECT phase, error_message, failed_at FROM dead_letter_queue "
            "WHERE run_id = ? ORDER BY id DESC LIMIT 1", (run_id,)).fetchone()
    except sqlite3.OperationalError:
        return None
    if not row:
        return None
    return {"phase": row["phase"], "reason": row["error_message"],
            "at": row["failed_at"]}


def _get_failed_checks(conn: sqlite3.Connection, run_id: str) -> list:
    """Checks that failed, blocking ones first — the answer to 'why did it stop'.

    `blocking` is what actually halts a run; an advisory failure is a warning
    the run continued past. Evidence is included because a summary alone
    ("1 claimed file does not exist") does not say which file.
    """
    try:
        rows = conn.execute(
            "SELECT guardrail_name, mode, summary, evidence, phase, role "
            "FROM gate_outcomes WHERE run_id = ? AND verdict = 'FAIL' "
            "ORDER BY CASE mode WHEN 'BLOCK' THEN 0 ELSE 1 END, id",
            (run_id,)).fetchall()
    except sqlite3.OperationalError:
        return []
    return [{
        "check": r["guardrail_name"],
        "blocking": r["mode"] == "BLOCK",
        "phase": r["phase"],
        "role": r["role"],
        "summary": r["summary"],
        "evidence": (r["evidence"] or "")[:1200],
    } for r in rows]


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
        stopped_by = _get_stop_reason(conn, run_id)
        failed_checks = _get_failed_checks(conn, run_id)

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
            # Why a run stopped, and which check stopped it. Both were already
            # recorded in the spine and neither was reachable without querying
            # SQLite by hand, so a non-coder had no way to see why work halted.
            "stopped_by": stopped_by,
            "failed_checks": failed_checks,
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

        # ── Build provenance data for this approval ────────────────────────
        # Provenance = audit trail that links Eric's approval to the run's
        # deliberation history, goal context, and drift state at approval time.
        # This data feeds the knowledge base and gate_eric_approval.py checks.

        # 1. Create or find goal_reference for this run
        existing_goal = conn.execute(
            "SELECT id FROM goal_references WHERE workflow_run_id = ? LIMIT 1",
            (run_id,),
        ).fetchone()
        if existing_goal:
            goal_ref_id = existing_goal[0]
        else:
            # Create goal reference from the run's topic/intent
            topic = run["topic"] if "topic" in run.keys() else ""
            cur = conn.execute(
                "INSERT INTO goal_references "
                "(workflow_run_id, goal_label, dependency_node, tier_advanced, "
                "advancement_type, authored_by) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, topic[:200], "", "", "PIPELINE_RUN", "ERIC_GATE"),
            )
            goal_ref_id = cur.lastrowid

        # 2. Create decision_trail from deliberation rounds
        rounds = conn.execute(
            "SELECT round_number, drafter_role, reviewer_signal "
            "FROM deliberation_rounds WHERE run_id = ? ORDER BY round_number",
            (run_id,),
        ).fetchall()
        round_count = len(rounds)
        round_summaries = [
            f"Round {r[0]} ({r[1]}): {r[2]}" for r in rounds
        ]
        consensus_signal = rounds[-1][2] if rounds else "PENDING"

        # Get summaries from key phases
        brain_row = conn.execute(
            "SELECT brain_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_role = 'brain' "
            "ORDER BY id DESC LIMIT 1", (run_id,),
        ).fetchone()
        draft_row = conn.execute(
            "SELECT drafter_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_role = 'draft' "
            "ORDER BY id DESC LIMIT 1", (run_id,),
        ).fetchone()
        review_row = conn.execute(
            "SELECT reviewer1_output FROM deliberation_rounds "
            "WHERE run_id = ? AND drafter_role = 'proposal_review' "
            "ORDER BY id DESC LIMIT 1", (run_id,),
        ).fetchone()

        brain_summary = (brain_row[0][:500] if brain_row and brain_row[0] else "")[:500]
        draft_summary = (draft_row[0][:500] if draft_row and draft_row[0] else "")[:500]
        review_summary = (review_row[0][:500] if review_row and review_row[0] else "")[:500]

        cur = conn.execute(
            "INSERT INTO decision_trails "
            "(workflow_run_id, trail_sequence, problem_statement, "
            "research_summary, draft_summary, review_summary, "
            "proposed_action, round_count, consensus_signal, "
            "eric_decision, eric_decision_note, eric_decided_at, authored_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, 1, run["topic"] if "topic" in run.keys() else "",
             brain_summary, draft_summary, review_summary,
             directive[:500], round_count, consensus_signal,
             decision, rationale, now, "ROUTER"),
        )
        trail_id = cur.lastrowid

        # 3. Capture drift snapshot
        drift_rows = conn.execute(
            "SELECT id, indicator_type, description, status, detected_by "
            "FROM drift_indicators WHERE workflow_run_id = ?",
            (run_id,),
        ).fetchall()
        open_drift = [d for d in drift_rows if d[3] in ("RAISED", "ACKNOWLEDGED", "ESCALATED")]
        drift_snapshot = {
            "open_drift_count": len(open_drift),
            "blocking_drift": [
                {"type": d[1], "description": d[2], "status": d[3]}
                for d in open_drift
            ],
            "all_drift_count": len(drift_rows),
        }
        drift_snapshot_json = json.dumps(drift_snapshot)

        # 4. Build briefing JSON (4 required sections)
        goal_label = run["topic"][:200] if "topic" in run.keys() else ""
        briefing = {
            "briefing": {
                "action_summary": f"Eric {decision.lower()}d run {run_id} "
                                  f"with rationale: {rationale or '(none given)'}",
                "goal_trace": {
                    "goal_reference_id": goal_ref_id,
                    "goal_label": goal_label,
                    "dependency_node": "",
                    "tier_advanced": "",
                },
                "decision_trail": {
                    "trail_id": trail_id,
                    "round_count": round_count,
                    "consensus_signal": consensus_signal,
                    "rounds": round_summaries,
                },
                "drift_indicators": drift_snapshot,
            },
            "generated_at": now,
            "rationale": rationale,
        }

        # 5. Compute briefing hash (excluding generated_at, rationale, briefing_hash)
        import unicodedata
        hash_payload = {
            k: v for k, v in briefing.items()
            if k not in ("generated_at", "rationale", "briefing_hash")
        }
        canonical = unicodedata.normalize("NFC", json.dumps(
            hash_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ))
        briefing_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        briefing["briefing_hash"] = briefing_hash
        briefing_json = json.dumps(briefing, ensure_ascii=False)

        # 6. Store decision trail snapshot
        trail_snapshot = {
            "trail_id": trail_id,
            "round_count": round_count,
            "rounds": round_summaries,
            "consensus_signal": consensus_signal,
        }
        trail_snapshot_json = json.dumps(trail_snapshot)

        # Write immutable audit record with full provenance
        # Mark all previous approvals for this run as non-current
        conn.execute(
            "UPDATE eric_gate_approvals SET is_current = 0 "
            "WHERE workflow_run_id = ?",
            (run_id,),
        )
        conn.execute(
            "INSERT INTO eric_gate_approvals "
            "(workflow_run_id, decision, rationale, decided_at, "
            "goal_reference_id, briefing_hash, briefing_json, "
            "drift_snapshot_json, decision_trail_snapshot_json, "
            "is_current, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
            (run_id, decision, rationale, now,
             goal_ref_id, briefing_hash, briefing_json,
             drift_snapshot_json, trail_snapshot_json, now),
        )

        # Update run status based on decision
        if decision == "APPROVE":
            conn.execute(
                "UPDATE workflow_runs SET status = 'PATTERN_CATALOG', "
                "eric_approved_at = ? WHERE id = ?",
                (now, run_id),
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


# ── Project Overview Endpoints ──────────────────────────────────────────

@relay_bp.route("/api/relay/project/<project_id>/overview", methods=["GET"])
def project_overview(project_id: str):
    """Get a project overview: build plan, recent runs, decisions, stats."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        # Build plan nodes
        nodes = conn.execute(
            "SELECT node_label, tier, sequence, status, blocked_reason, "
            "completed_at, commit_hash FROM build_plan_nodes "
            "WHERE project_id = ? COLLATE NOCASE ORDER BY sequence",
            (project_id,)
        ).fetchall()
        build_plan = [dict(r) for r in nodes]
        complete = sum(1 for n in build_plan if n["status"] == "COMPLETE")
        deferred = sum(1 for n in build_plan if n["status"] == "DEFERRED")
        pending = sum(1 for n in build_plan if n["status"] == "PENDING")

        # Recent runs
        runs = conn.execute(
            "SELECT id, topic, status, created_at, rounds_completed, result "
            "FROM workflow_runs WHERE project_id = ? COLLATE NOCASE "
            "ORDER BY created_at DESC LIMIT 10",
            (project_id,)
        ).fetchall()
        recent_runs = [dict(r) for r in runs]

        # Project decisions (ADRs)
        decisions = conn.execute(
            "SELECT label, substr(decision, 1, 200) as decision, status, decided_at "
            "FROM project_decisions ORDER BY decided_at DESC LIMIT 20"
        ).fetchall()
        adr_list = [dict(r) for r in decisions]

        # Stats
        total_runs = conn.execute(
            "SELECT count(*) FROM workflow_runs WHERE project_id = ?",
            (project_id,)
        ).fetchone()[0]
        consensus_runs = conn.execute(
            "SELECT count(*) FROM workflow_runs WHERE project_id = ? AND result = 'CONSENSUS_REACHED'",
            (project_id,)
        ).fetchone()[0]
        escalated_runs = conn.execute(
            "SELECT count(*) FROM workflow_runs WHERE project_id = ? AND result = 'ESCALATED'",
            (project_id,)
        ).fetchone()[0]
        eric_gate_runs = conn.execute(
            "SELECT count(*) FROM workflow_runs WHERE project_id = ? AND status = 'ERIC_GATE'",
            (project_id,)
        ).fetchone()[0]

        # Active blockers
        blockers = conn.execute(
            "SELECT id, description, status FROM active_blockers WHERE status != 'RESOLVED' LIMIT 5"
        ).fetchall()
        active_blockers = [{"blocker_id": r["id"], "title": r["description"], "status": r["status"]} for r in blockers]

        # Dev pivots — the real governance tracking (not just ADRs)
        pivots = conn.execute(
            "SELECT doc_id, title, status, category, invalidation_reason, capability_gap "
            "FROM dev_pivot_status ORDER BY id"
        ).fetchall()
        dev_pivots = [dict(r) for r in pivots]

        # Session closeout stats — real development activity
        closeout_stats = conn.execute(
            "SELECT count(*) as total, "
            "sum(CASE WHEN status='PASS' THEN 1 ELSE 0 END) as passed, "
            "sum(CASE WHEN status='FAIL' THEN 1 ELSE 0 END) as failed, "
            "sum(CASE WHEN status='BLOCKED' THEN 1 ELSE 0 END) as blocked "
            "FROM session_closeouts"
        ).fetchone()
        closeout_summary = dict(closeout_stats) if closeout_stats else {"total": 0, "passed": 0, "failed": 0, "blocked": 0}

        return jsonify({
            "project_id": project_id,
            "build_plan": build_plan,
            "build_plan_stats": {
                "total": len(build_plan),
                "complete": complete,
                "deferred": deferred,
                "pending": pending,
            },
            "recent_runs": recent_runs,
            "decisions": adr_list,
            "dev_pivots": dev_pivots,
            "closeout_stats": closeout_summary,
            "stats": {
                "total_runs": total_runs,
                "consensus_reached": consensus_runs,
                "escalated": escalated_runs,
                "at_eric_gate": eric_gate_runs,
            },
            "active_blockers": active_blockers,
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/project/<project_id>/build-plan", methods=["GET"])
def project_build_plan(project_id: str):
    """Get detailed build plan for a project."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT node_label, tier, sequence, status, blocked_reason, "
            "required_role, allowed_mode, workflow_run_id, evidence_path, "
            "commit_hash, completed_at, approved_at "
            "FROM build_plan_nodes WHERE project_id = ? COLLATE NOCASE ORDER BY sequence",
            (project_id,)
        ).fetchall()
        return jsonify({"nodes": [dict(r) for r in rows]})
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


# ═══════════════════════════════════════════════════════════════════════════
#  BRAIN CHAT — pre-pipeline conversational interface
# ═══════════════════════════════════════════════════════════════════════════

import uuid as _uuid
import httpx as _httpx


def _kb_search(conn: sqlite3.Connection, query: str, limit: int = 5) -> list:
    """Search the knowledge base FTS5 for context relevant to the query."""
    import re as _re
    keywords = _re.sub(r'[."*(){}:^+\-]', ' ', query)
    keywords = keywords.strip() or "CIS pipeline"
    try:
        rows = conn.execute(
            "SELECT content, source FROM knowledge_messages_fts "
            "WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT ?",
            (keywords, limit),
        ).fetchall()
        return [{"content": r[0][:500], "source": r[1]} for r in rows]
    except Exception:
        return []


@relay_bp.route("/api/relay/brain/chat", methods=["POST"])
def brain_chat():
    """Conversational Brain interface — pre-pipeline.

    Eric talks with Brain. Brain searches the KB for context.
    Returns Brain's response + KB context used.
    Does NOT start a pipeline run — this is exploration.
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    session_id = (data.get("session_id") or "").strip()
    if not message:
        return jsonify({"error": "message required"}), 400
    if not session_id:
        session_id = f"brain-{_uuid.uuid4().hex[:12]}"

    conn = _db()
    try:
        # 1. Store user message
        conn.execute(
            "INSERT INTO brain_chats (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, "user", message),
        )
        conn.commit()

        # 2. Search KB for context
        kb_results = _kb_search(conn, message)

        # 3. Build conversation history
        history_rows = conn.execute(
            "SELECT role, content FROM brain_chats "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        history = [dict(r) for r in history_rows]

        # 4. Build messages for Brain gateway
        system_prompt = (
            "You are Brain, the lateral exploration engine of the CIS pipeline. "
            "Your role is to understand Eric's intent deeply by exploring it from "
            "multiple angles, surfacing assumptions, and connecting it to the "
            "knowledge base. Be conversational. Ask questions when something is "
            "ambiguous. When you have enough understanding, say 'READY TO PROCEED' "
            "and summarize the intent.\n\n"
            "Knowledge base context for this message:\n"
        )
        if kb_results:
            for hit in kb_results:
                system_prompt += f"- [{hit['source']}] {hit['content'][:200]}\n"
        else:
            system_prompt += "(No KB results found for this query)\n"

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            else:
                messages.append({"role": "assistant", "content": msg["content"]})

        # 5. Call Brain gateway (port 8644)
        brain_url = "http://127.0.0.1:8644/v1/chat/completions"
        brain_key = os.environ.get("CIS_BRAIN_API_KEY", "")
        payload = {
            "model": "agent",
            "messages": messages,
            "max_tokens": 4096,
        }
        headers = {"Content-Type": "application/json"}
        if brain_key:
            headers["Authorization"] = f"Bearer {brain_key}"

        try:
            resp = _httpx.post(brain_url, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            brain_data = resp.json()
            brain_output = brain_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            brain_output = f"[Brain gateway error: {e}]"

        # 6. Store Brain response
        conn.execute(
            "INSERT INTO brain_chats (session_id, role, content, kb_context) "
            "VALUES (?, ?, ?, ?)",
            (session_id, "brain", brain_output,
             json.dumps(kb_results) if kb_results else None),
        )
        conn.commit()

        return jsonify({
            "session_id": session_id,
            "brain_response": brain_output,
            "kb_context": kb_results,
            "ready": "READY TO PROCEED" in brain_output,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@relay_bp.route("/api/relay/brain/history/<session_id>", methods=["GET"])
def brain_history(session_id: str):
    """Get conversation history for a brain chat session."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM brain_chats "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        return jsonify({
            "session_id": session_id,
            "messages": [dict(r) for r in rows],
        })
    finally:
        conn.close()


@relay_bp.route("/api/relay/brain/start", methods=["POST"])
def brain_start_pipeline():
    """Start a pipeline run from a Brain chat session.

    Takes the conversation history and builds an enriched intent,
    then starts the pipeline.
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    conn = _db()
    try:
        rows = conn.execute(
            "SELECT role, content FROM brain_chats "
            "WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
        if not rows:
            return jsonify({"error": "No conversation found for session"}), 404

        # Build enriched intent from conversation
        conversation = [dict(r) for r in rows]
        enriched_intent = "## Enriched Intent (from Brain conversation)\n\n"
        enriched_intent += "### Conversation History\n"
        for msg in conversation:
            speaker = "Eric" if msg["role"] == "user" else "Brain"
            enriched_intent += f"**{speaker}:** {msg['content']}\n\n"
        enriched_intent += (
            "### Pipeline Directive\n"
            "Use the conversation above as the full intent context. "
            "Brain has explored this with Eric. Honor the nuances discussed."
        )

        # Start pipeline with enriched intent
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
            run_id = relay.start_sync(enriched_intent)
        finally:
            relay.close()

        # Start the async pipeline in a background thread
        thread = threading.Thread(
            target=_run_pipeline_background,
            args=(run_id, enriched_intent, None),
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
            "message": "Pipeline started with enriched intent from Brain chat.",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  PIPELINE INTERJECTIONS — mid-pipeline backchannel
# ═══════════════════════════════════════════════════════════════════════════

@relay_bp.route("/api/relay/<run_id>/interject", methods=["POST"])
def relay_interject(run_id: str):
    """Add a mid-pipeline interjection (backchannel).

    Does NOT stop the pipeline. The interjection is stored and will be
    consumed by the next phase that runs.
    """
    auth_err = _check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message required"}), 400

    conn = _db()
    try:
        # Verify run exists
        run = _get_run(conn, run_id)
        if not run:
            return jsonify({"error": "Run not found"}), 404

        conn.execute(
            "INSERT INTO pipeline_interjections (run_id, message) VALUES (?, ?)",
            (run_id, message),
        )
        conn.commit()

        return jsonify({
            "run_id": run_id,
            "message": "Interjection recorded. Will be consumed by the next phase.",
            "run_status": run["status"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@relay_bp.route("/api/relay/<run_id>/interjections", methods=["GET"])
def relay_get_interjections(run_id: str):
    """Get all interjections for a run."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT id, run_id, message, created_at, consumed_by_phase, consumed_at "
            "FROM pipeline_interjections WHERE run_id = ? ORDER BY id ASC",
            (run_id,),
        ).fetchall()
        return jsonify({
            "run_id": run_id,
            "interjections": [dict(r) for r in rows],
        })
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
#  LIVE FEED — phase-by-phase output for observation
# ═══════════════════════════════════════════════════════════════════════════

@relay_bp.route("/api/relay/<run_id>/feed", methods=["GET"])
def relay_feed(run_id: str):
    """Live pipeline feed — all phase outputs, gate results, interjections.

    Returns everything needed to observe a running pipeline in real-time.
    """
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

        # Get gate outcomes
        gate_rows = conn.execute(
            "SELECT phase, role, guardrail_name, verdict, mode, summary, timestamp "
            "FROM gate_outcomes WHERE run_id = ? ORDER BY id ASC",
            (run_id,),
        ).fetchall()
        gates = [dict(r) for r in gate_rows]

        # Get interjections
        interj_rows = conn.execute(
            "SELECT id, message, created_at, consumed_by_phase "
            "FROM pipeline_interjections WHERE run_id = ? ORDER BY id ASC",
            (run_id,),
        ).fetchall()
        interjections = [dict(r) for r in interj_rows]

        # Build phase timeline
        phases = []
        for r in rounds:
            phase = {
                "round": r["round_number"],
                "phase": r["drafter_role"],
                "signal": r["reviewer_signal"],
                "created_at": r["created_at"],
            }
            # Include full outputs for observation
            if r.get("brain_output"):
                phase["brain_output"] = r["brain_output"]
            if r.get("drafter_output"):
                phase["drafter_output"] = r["drafter_output"]
            if r.get("reviewer1_output"):
                phase["reviewer1_output"] = r["reviewer1_output"]
            if r.get("reviewer2_output"):
                phase["reviewer2_output"] = r["reviewer2_output"]
            if r.get("verify_output"):
                phase["verify_output"] = r["verify_output"]
            if r.get("menter_output"):
                phase["menter_output"] = r["menter_output"]
            if r.get("human_question"):
                phase["human_question"] = r["human_question"]
            phases.append(phase)

        # Get provenance + drift data
        prov_row = conn.execute(
            "SELECT original_intent, enriched_intent, kb_context_hash, "
            "brain_session_id, locked_at "
            "FROM intent_provenance WHERE run_id = ? ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        provenance = dict(prov_row) if prov_row else None

        drift_rows = conn.execute(
            "SELECT phase, round, drift_score, drift_reasons, verdict, created_at "
            "FROM phase_drift WHERE run_id = ? ORDER BY id ASC",
            (run_id,),
        ).fetchall()
        drift_data = [dict(r) for r in drift_rows]

        return jsonify({
            "run_id": run["id"],
            "topic": run["topic"],
            "status": run["status"],
            "result": run.get("result"),
            "created_at": run["created_at"],
            "phases": phases,
            "gates": gates,
            "interjections": interjections,
            "trajectories": trajectories,
            "provenance": provenance,
            "drift": drift_data,
            "background": {
                "active": run_id in _active_runs
                and "finished_at" not in _active_runs.get(run_id, {}),
                "error": _active_runs.get(run_id, {}).get("error"),
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ── System Dashboard Endpoints ──────────────────────────────────────────────

import subprocess
import re as _re


@relay_bp.route("/system/health", methods=["GET"])
def system_health():
    """Get health of all Docker containers and key services."""
    containers = []
    services = []

    try:
        # Get docker container list
        result = subprocess.run(
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

                # Parse status
                is_running = status_raw.startswith("Up")
                health = ""
                healthy = True
                if "unhealthy" in status_raw.lower():
                    health = "unhealthy"
                    healthy = False
                elif "healthy" in status_raw.lower():
                    health = "healthy"
                elif "health: starting" in status_raw.lower():
                    health = "starting"
                    healthy = False

                # Extract uptime
                uptime = ""
                if is_running:
                    uptime = status_raw.replace("Up ", "").split(" (")[0]

                # Determine model from container name
                model = ""
                name_lower = name.lower()
                if "brainstorm" in name_lower or name_lower == "cis-brain":
                    model = "deepseek-v4-pro"
                elif "drafter" in name_lower:
                    model = "deepseek-v4-pro"
                elif "qwen" in name_lower or ("reviewer" in name_lower and "glm" not in name_lower):
                    model = "qwen3.7-max"
                elif "glm" in name_lower:
                    model = "glm-5.2"
                elif "implementer" in name_lower:
                    model = "deepseek-v4-pro"
                elif "verifier" in name_lower:
                    model = "glm-5.2"
                elif "pipeline" in name_lower:
                    model = "control-plane"
                elif "hermes" in name_lower:
                    model = "prime"

                # Check gateway health if running
                if is_running and model and model not in ("control-plane", "prime"):
                    try:
                        port_match = _re.search(r"0\.0\.0\.0:(\d+)->", ports)
                        if port_match:
                            port = port_match.group(1)
                            hresult = subprocess.run(
                                ["curl", "-s", "--max-time", "3", f"http://localhost:{port}/api/health"],
                                capture_output=True, text=True, timeout=5
                            )
                            if hresult.returncode == 0 and "ok" in hresult.stdout.lower():
                                healthy = True
                            else:
                                healthy = False
                                health = health or "gateway-down"
                    except Exception:
                        pass

                containers.append({
                    "name": name,
                    "status": "running" if is_running else "stopped",
                    "health": health,
                    "healthy": healthy if is_running else False,
                    "image": image[:60],
                    "uptime": uptime,
                    "ports": ports[:80] if ports else "",
                    "model": model,
                })

        # Check non-Docker services
        # SQLite DB
        try:
            db_path = os.environ.get("CIS_DB_PATH", "/workspace/cis/data/cis_memory.db")
            if not os.path.exists(db_path):
                db_path = "/mnt/projects/cis/data/cis_memory.db"
            conn = sqlite3.connect(db_path, timeout=2)
            conn.execute("SELECT 1")
            conn.close()
            services.append({"name": "SQLite Spine", "healthy": True, "detail": db_path})
        except Exception as e:
            services.append({"name": "SQLite Spine", "healthy": False, "detail": str(e)})

        # GLM llama-server (port 8001 or 8002)
        for port_label, port in [("GLM llama-server", 8001), ("Qwen llama-server", 8002)]:
            try:
                hresult = subprocess.run(
                    ["curl", "-s", "--max-time", "3", f"http://localhost:{port}/health"],
                    capture_output=True, text=True, timeout=5
                )
                if hresult.returncode == 0:
                    services.append({"name": port_label, "healthy": True, "url": f"localhost:{port}"})
                else:
                    services.append({"name": port_label, "healthy": False, "url": f"localhost:{port}"})
            except Exception:
                services.append({"name": port_label, "healthy": False, "url": f"localhost:{port}"})

        # ChromaDB
        try:
            hresult = subprocess.run(
                ["curl", "-s", "--max-time", "3", "http://localhost:8000/api/v1/heartbeat"],
                capture_output=True, text=True, timeout=5
            )
            if hresult.returncode == 0 and "nanosecond" in hresult.stdout.lower():
                services.append({"name": "ChromaDB", "healthy": True, "url": "localhost:8000"})
            else:
                services.append({"name": "ChromaDB", "healthy": False, "url": "localhost:8000"})
        except Exception:
            services.append({"name": "ChromaDB", "healthy": False, "url": "localhost:8000"})

    except Exception as e:
        return jsonify({"error": str(e), "containers": containers, "services": services}), 500

    return jsonify({"containers": containers, "services": services})


@relay_bp.route("/system/restart", methods=["POST"])
def system_restart():
    """Restart a single Docker container."""
    data = request.get_json(silent=True) or {}
    container = data.get("container", "")
    if not container:
        return jsonify({"error": "container name required"}), 400

    allowed = ["cis-pipeline", "cis-hermes", "cis-brainstorm", "cis-drafter",
               "cis-qwen-reviewer", "cis-glm-reviewer", "cis-implementer",
               "cis-verifier"]
    if container not in allowed:
        return jsonify({"error": f"container '{container}' not in whitelist"}), 403

    try:
        result = subprocess.run(
            ["docker", "restart", container],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return jsonify({"status": "ok", "container": container, "message": "restarted"})
        else:
            return jsonify({"error": result.stderr.strip()}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "restart timed out (60s)"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@relay_bp.route("/system/restart-all", methods=["POST"])
def system_restart_all():
    """Restart all CIS containers in dependency order."""
    order = ["cis-hermes", "cis-brainstorm", "cis-drafter",
             "cis-qwen-reviewer", "cis-glm-reviewer", "cis-implementer",
             "cis-verifier", "cis-pipeline"]
    results = []
    for name in order:
        try:
            result = subprocess.run(
                ["docker", "restart", name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                results.append({"container": name, "status": "ok"})
            else:
                results.append({"container": name, "status": "error", "error": result.stderr.strip()})
        except Exception as e:
            results.append({"container": name, "status": "error", "error": str(e)})

    return jsonify({"results": results})


@relay_bp.route("/system/logs/<container>", methods=["GET"])
def system_logs(container):
    """Get last 50 lines of container logs."""
    allowed = ["cis-pipeline", "cis-hermes", "cis-brainstorm", "cis-drafter",
               "cis-qwen-reviewer", "cis-glm-reviewer", "cis-implementer",
               "cis-verifier"]
    if container not in allowed:
        return jsonify({"error": "container not in whitelist"}), 403

    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "50", "--no-log-prefix", container],
            capture_output=True, text=True, timeout=10
        )
        lines = (result.stdout + result.stderr).strip().split("\n")
        lines = [l for l in lines if l.strip()][-50:]
        return jsonify({"container": container, "lines": lines})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
