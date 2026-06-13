"""
api/pipeline_views.py — Tier 10 CIS UI pipeline display views.

Read-only Flask blueprint exposing build-plan status, pipeline runs,
Eric Gate approvals, decision trail, and archive search to the React frontend.

All endpoints are GET only. No writes to spine or Chroma.
"""

from flask import Blueprint, jsonify, request

pipeline_views_bp = Blueprint("pipeline_views", __name__)

# ── Import MCP bridge handler functions (in-process, no subprocess) ──────
from mcp_bridge.tools import (
    handle_get_current_phase,
    handle_get_build_status,
    handle_get_next_actions,
    handle_get_recent_runs,
    handle_get_run_detail,
    handle_get_open_decisions,
    handle_get_eric_gate_status,
    handle_search_sessions,
    handle_search_semantic,
)


# ── Pipeline status ─────────────────────────────────────────────────────

@pipeline_views_bp.route("/api/pipeline/status")
def api_pipeline_status():
    """Build plan summary: current tier, status, next actions."""
    phase = handle_get_current_phase({})
    return jsonify(phase)


@pipeline_views_bp.route("/api/pipeline/status/<path:node_label>")
def api_pipeline_node_status(node_label):
    """Single build_plan_node detail by label."""
    result = handle_get_build_status({"node_label": node_label})
    return jsonify(result)


@pipeline_views_bp.route("/api/pipeline/next-actions")
def api_pipeline_next_actions():
    """All PENDING build_plan_nodes."""
    result = handle_get_next_actions({})
    return jsonify(result)


# ── Pipeline runs ───────────────────────────────────────────────────────

@pipeline_views_bp.route("/api/pipeline/runs")
def api_pipeline_runs():
    """Recent workflow_runs list."""
    limit = request.args.get("limit", 20, type=int)
    result = handle_get_recent_runs({"limit": limit})
    return jsonify(result)


@pipeline_views_bp.route("/api/pipeline/runs/<run_id>")
def api_pipeline_run_detail(run_id):
    """Single workflow_run detail with deliberation_rounds."""
    result = handle_get_run_detail({"run_id": run_id})
    return jsonify(result)


# ── Eric Gate dashboard ─────────────────────────────────────────────────

@pipeline_views_bp.route("/api/pipeline/eric-gate")
def api_eric_gate():
    """Pending approvals and escalation status."""
    result = handle_get_eric_gate_status({})
    return jsonify(result)


# ── Decisions ───────────────────────────────────────────────────────────

@pipeline_views_bp.route("/api/decisions")
def api_decisions():
    """Active project_decisions list."""
    result = handle_get_open_decisions({})
    return jsonify(result)


# ── Archive search ──────────────────────────────────────────────────────

@pipeline_views_bp.route("/api/archive/search/semantic")
def api_archive_search_semantic():
    """Semantic archive search via Chroma/VDB."""
    query = request.args.get("q", "")
    top_k = request.args.get("top_k", 20, type=int)
    result = handle_search_semantic({"query": query, "top_k": top_k})
    return jsonify(result)


@pipeline_views_bp.route("/api/archive/search/fts")
def api_archive_search_fts():
    """FTS5 keyword search across sessions."""
    query = request.args.get("q", "")
    limit = request.args.get("limit", 20, type=int)
    result = handle_search_sessions({"query": query, "limit": limit})
    return jsonify(result)
