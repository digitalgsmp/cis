"""
api/dashboard_api.py — Tier 11A read-only dashboard API + Tier 11B Eric Gate approval.

11A: GET /api/dashboard/full — aggregates pipeline status, blockers, runs, capabilities.
11B: POST /api/dashboard/approve — controlled Eric Gate APPROVE write.
No pipeline module imports. No new tables. No VETO/RETURN_TO_DRAFT.
"""

import yaml
import os
import uuid
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

dashboard_bp = Blueprint("dashboard", __name__)

# Load system overview descriptions at module init (cached in memory)
_OVERVIEW_PATH = os.path.join(os.path.dirname(__file__), "system_overview.yaml")
_overview_cache = None


def _load_overview():
    global _overview_cache
    if _overview_cache is not None:
        return _overview_cache
    try:
        with open(_OVERVIEW_PATH, "r") as f:
            raw = yaml.safe_load(f) or []
        _overview_cache = {entry["node_label"]: entry for entry in raw if entry.get("node_label")}
    except Exception:
        _overview_cache = {}
    return _overview_cache


# ── 11A: GET /api/dashboard/full ──────────────────────────────────────────

@dashboard_bp.route("/api/dashboard/full")
def dashboard_full():
    """Aggregated dashboard data: phase, blockers, runs, capabilities, overview."""
    overview = _load_overview()

    # --- Phase / status ---
    try:
        from mcp_bridge.tools import handle_get_current_phase
        phase = handle_get_current_phase({})
    except Exception:
        phase = {"build_phase": "unknown", "next_tier": "unknown", "next_action": "", "pending": [], "in_progress": []}

    # --- Active blockers ---
    blockers = []
    try:
        from mcp_bridge.spine import _connect_readonly
        conn = _connect_readonly()
        rows = conn.execute("SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'").fetchall()
        conn.close()
        blockers = [{"id": r["id"], "description": r["description"]} for r in rows]
    except Exception:
        pass

    # --- Recent runs ---
    runs = []
    try:
        from mcp_bridge.tools import handle_get_recent_runs
        result = handle_get_recent_runs({"limit": 5})
        runs = result.get("runs", [])
    except Exception:
        pass

    # --- Completed capabilities ---
    capabilities = []
    try:
        conn = _connect_readonly()
        rows = conn.execute(
            "SELECT node_label, status, tier, completed_at FROM build_plan_nodes "
            "WHERE status = 'COMPLETE' AND project_id = 'cis' ORDER BY sequence"
        ).fetchall()
        conn.close()
        for r in rows:
            entry = {"node_label": r["node_label"], "status": r["status"], "tier": r["tier"], "completed_at": r["completed_at"]}
            ov = overview.get(r["node_label"], {})
            if ov.get("operator_description"):
                entry["operator_description"] = ov["operator_description"]
            if ov.get("capability_area"):
                entry["capability_area"] = ov["capability_area"]
            capabilities.append(entry)
    except Exception:
        pass

    # --- System overview sections ---
    overview_areas = {}
    for node_label, ov in overview.items():
        area = ov.get("capability_area", "Other")
        overview_areas.setdefault(area, []).append({"node_label": node_label, "description": ov.get("operator_description", "")})

    # --- Quick links ---
    quick_links = [
        {"path": "/pipeline", "label": "Pipeline", "desc": "Build plan status"},
        {"path": "/eric-gate", "label": "Eric Gate", "desc": "Pending approvals"},
        {"path": "/archive/search", "label": "Archive", "desc": "Search sessions"},
        {"path": "/archive/sessions", "label": "Sessions", "desc": "Browse history"},
        {"path": "/decisions", "label": "Decisions", "desc": "ADR trail"},
    ]

    return jsonify({
        "phase": phase, "blockers": blockers, "runs": runs,
        "capabilities": capabilities, "overview_areas": overview_areas, "quick_links": quick_links,
    })


# ── 11B: POST /api/dashboard/approve ──────────────────────────────────────

def _get_db_path():
    path = os.environ.get("CIS_SPINE_PATH", "")
    if not path:
        raise RuntimeError("CIS_SPINE_PATH environment variable is not set")
    return path


def _get_git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd="/mnt/projects/cis").strip()
    except Exception:
        return "unknown"


@dashboard_bp.route("/api/dashboard/approve", methods=["POST"])
def dashboard_approve():
    """Record Eric Gate APPROVE for a workflow run. Controlled write.

    Uses existing eric_gate_approvals table (Component 3 schema). No new tables.
    Only APPROVE is supported — VETO and RETURN_TO_DRAFT return 400.
    Idempotent: duplicate approval returns existing record.
    Requires goal_reference_id from goal_references — 409 if none exists.
    """
    import sqlite3
    data = request.get_json(silent=True) or {}
    run_id = data.get("run_id", "").strip()
    rationale = data.get("rationale", "").strip()

    if not run_id:
        return jsonify({"status": "rejected", "error": "run_id is required"}), 400

    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # --- Validate run exists ---
        row = cur.execute("SELECT id, status FROM workflow_runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return jsonify({"status": "rejected", "error": f"Workflow run {run_id} not found"}), 404

        # --- Idempotency: check existing current approval ---
        existing = cur.execute(
            "SELECT id, decided_at FROM eric_gate_approvals WHERE workflow_run_id = ? AND is_current = 1 AND decision = 'APPROVE'",
            (run_id,)
        ).fetchone()
        if existing:
            return jsonify({
                "status": "already_approved",
                "approval_id": existing["id"],
                "run_id": run_id,
                "message": f"This run was already approved at {existing['decided_at']}.",
            }), 200

        # --- Find goal_reference_id ---
        goal = cur.execute(
            "SELECT id, goal_label FROM goal_references WHERE workflow_run_id = ? ORDER BY id LIMIT 1",
            (run_id,)
        ).fetchone()
        if not goal:
            return jsonify({
                "status": "rejected",
                "error": "No goal reference exists for this run. Approval cannot proceed — upstream goal formation did not run.",
            }), 409

        # --- Build approval record ---
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        approval_id = str(uuid.uuid4())

        # briefing_json: pull Drafter output from deliberation_rounds if available
        rounds = cur.execute(
            "SELECT round_number, role, content FROM deliberation_rounds WHERE workflow_run_id = ? ORDER BY round_number",
            (run_id,)
        ).fetchall()
        briefing_obj = {
            "workflow_run_id": run_id,
            "goal_label": goal["goal_label"],
            "rounds": [{"round": r["round_number"], "role": r["role"], "content": r["content"][:500]} for r in rounds],
        }
        briefing_json = json.dumps(briefing_obj, ensure_ascii=False)
        briefing_hash = hashlib.sha256(briefing_json.encode("utf-8")).hexdigest()

        # drift_snapshot_json
        git_head = _get_git_head()
        drift_obj = {"git_head": git_head, "dirty_files": [], "captured_at": now_utc}
        drift_json = json.dumps(drift_obj, ensure_ascii=False)

        # decision_trail_snapshot_json
        trail_obj = [{"round": r["round_number"], "role": r["role"]} for r in rounds]
        trail_json = json.dumps(trail_obj, ensure_ascii=False)

        # Handle supersedes: set prior is_current to 0
        prior = cur.execute(
            "SELECT id FROM eric_gate_approvals WHERE workflow_run_id = ? AND is_current = 1",
            (run_id,)
        ).fetchone()

        if prior:
            cur.execute("UPDATE eric_gate_approvals SET is_current = 0 WHERE id = ?", (prior["id"],))
            supersedes_id = prior["id"]
        else:
            supersedes_id = None

        # Insert
        cur.execute("""
            INSERT INTO eric_gate_approvals
            (id, workflow_run_id, decision, decided_at, decided_by,
             goal_reference_id, briefing_hash, briefing_json,
             drift_snapshot_json, decision_trail_snapshot_json,
             is_current, supersedes_approval_id, rationale, created_at)
            VALUES (?, ?, 'APPROVE', ?, 'Eric', ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            approval_id, run_id, now_utc, goal["id"],
            briefing_hash, briefing_json,
            drift_json, trail_json,
            supersedes_id, rationale or None, now_utc,
        ))

        conn.commit()

        return jsonify({
            "status": "approved",
            "approval_id": approval_id,
            "run_id": run_id,
            "decision": "APPROVE",
            "recorded_at": now_utc,
            "next_action": f"Orchestrator can now proceed with --run-id {run_id} for Drafter→Reviewer handoff.",
        }), 200

    except sqlite3.IntegrityError as e:
        # UNIQUE constraint hit — concurrent approval, return existing
        existing = cur.execute(
            "SELECT id, decided_at FROM eric_gate_approvals WHERE workflow_run_id = ? AND is_current = 1",
            (run_id,)
        ).fetchone()
        if existing:
            return jsonify({
                "status": "already_approved",
                "approval_id": existing["id"],
                "run_id": run_id,
                "message": "Concurrent approval detected. This run is already approved.",
            }), 200
        return jsonify({"status": "rejected", "error": str(e)}), 500

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

    finally:
        conn.close()
