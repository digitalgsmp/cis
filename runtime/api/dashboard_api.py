"""
api/dashboard_api.py — Tier 11A read-only dashboard API.

Exposes a single GET endpoint that aggregates pipeline status, blockers,
recent runs, build capabilities, and system overview descriptions.
No writes. No pipeline module imports.
"""

import yaml
import os
from flask import Blueprint, jsonify

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


@dashboard_bp.route("/api/dashboard/full")
def dashboard_full():
    """Aggregated dashboard data: phase, blockers, runs, capabilities, overview.

    Pulls from the existing Tier 10 pipeline endpoints and the spine directly.
    No writes. All data is read-only.
    """
    overview = _load_overview()

    # --- Phase / status (from pipeline_views in-process) ---
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
        rows = conn.execute(
            "SELECT id, description FROM active_blockers WHERE status = 'ACTIVE'"
        ).fetchall()
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

    # --- Completed capabilities (from build_plan_nodes, sourced live per E6) ---
    capabilities = []
    try:
        from mcp_bridge.tools import handle_get_build_status
        # get all nodes — the tool accepts an empty params dict
        conn = _connect_readonly()
        rows = conn.execute(
            "SELECT node_label, status, tier, completed_at FROM build_plan_nodes "
            "WHERE status = 'COMPLETE' AND project_id = 'CIS' "
            "ORDER BY sequence"
        ).fetchall()
        conn.close()
        for r in rows:
            entry = {
                "node_label": r["node_label"],
                "status": r["status"],
                "tier": r["tier"],
                "completed_at": r["completed_at"],
            }
            # Attach operator description from overview YAML if available
            ov = overview.get(r["node_label"], {})
            if ov.get("operator_description"):
                entry["operator_description"] = ov["operator_description"]
            if ov.get("capability_area"):
                entry["capability_area"] = ov["capability_area"]
            capabilities.append(entry)
    except Exception:
        pass

    # --- System overview sections by capability_area ---
    overview_areas = {}
    for node_label, ov in overview.items():
        area = ov.get("capability_area", "Other")
        if area not in overview_areas:
            overview_areas[area] = []
        overview_areas[area].append({
            "node_label": node_label,
            "description": ov.get("operator_description", ""),
        })

    # --- Quick links ---
    quick_links = [
        {"path": "/pipeline", "label": "Pipeline", "desc": "Build plan status"},
        {"path": "/eric-gate", "label": "Eric Gate", "desc": "Pending approvals"},
        {"path": "/archive/search", "label": "Archive", "desc": "Search sessions"},
        {"path": "/archive/sessions", "label": "Sessions", "desc": "Browse history"},
        {"path": "/decisions", "label": "Decisions", "desc": "ADR trail"},
    ]

    return jsonify({
        "phase": phase,
        "blockers": blockers,
        "runs": runs,
        "capabilities": capabilities,
        "overview_areas": overview_areas,
        "quick_links": quick_links,
    })
