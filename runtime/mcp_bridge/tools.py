"""
tools.py — MCP tool definitions and handler functions for the CIS MCP Bridge.

Defines 9 read-only tools per the Tier 8 specification §2.1:
  cis_get_current_phase, cis_get_build_status, cis_get_next_actions,
  cis_get_recent_runs, cis_get_run_detail, cis_get_open_decisions,
  cis_get_open_questions, cis_get_eric_gate_status, cis_search_sessions
"""
from . import spine

# ── Tool definitions ──────────────────────────────────

TOOLS = [
    {
        "name": "cis_get_current_phase",
        "description": (
            "Get the current CIS build phase, in-progress nodes, "
            "pending nodes, next tier, and next action. "
            "Fast startup orientation — no arguments needed."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cis_get_build_status",
        "description": (
            "Get the status of a single build_plan_node by its exact label. "
            "Returns status, tier, evidence_path, commit_hash, completed_at, approved_at. "
            "Example label: 'Tier 8 — MCP Bridge'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_label": {
                    "type": "string",
                    "description": (
                        "Exact node_label from build_plan_nodes. "
                        "Example: 'Tier 7R.4 — Process Manager (State Machine)'"
                    ),
                },
            },
            "required": ["node_label"],
        },
    },
    {
        "name": "cis_get_next_actions",
        "description": (
            "Get all build_plan_nodes with status PENDING, ordered by sequence. "
            "Use to determine what work is eligible to be picked up next."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cis_get_recent_runs",
        "description": (
            "Get the most recent workflow_runs, ordered by created_at DESC. "
            "Returns id, topic, result, rounds_completed, created_at, completed_at, status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of runs to return (default: 5, max: 50)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "cis_get_run_detail",
        "description": (
            "Get a single workflow_run by ID, including its deliberation_rounds "
            "and workflow_run_artifacts. Use for deep inspection of a pipeline run."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": (
                        "The workflow_run ID (e.g., 'run-88032ce506724')"
                    ),
                },
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "cis_get_open_decisions",
        "description": (
            "Get all active, non-superseded project decisions (project_decisions "
            "where status='DECIDED' AND superseded_by IS NULL). "
            "Returns ADR-SEED-* records."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cis_get_open_questions",
        "description": (
            "Get all open questions (open_questions where status='OPEN'). "
            "Returns OQ-SEED-* records. Use to see outstanding unknowns."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cis_get_eric_gate_status",
        "description": (
            "Get pending Eric Gate approvals from eric_gate_approvals "
            "where is_current=1. Returns decision, workflow_run_id, goal_label, "
            "rationale, and timestamps."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cis_search_sessions",
        "description": (
            "Full-text search across session_closeouts using FTS5. "
            "Searches failure_summary, failure_step, log_path, and created_by. "
            "Returns matching session_closeouts rows. "
            "Use for archive discovery: 'have we solved this before?'"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term for FTS5 full-text search",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default: 10, max: 50)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            "required": ["query"],
        },
    },
]


# ── Handler functions ─────────────────────────────────

def handle_get_current_phase(arguments):
    """Handler for cis_get_current_phase."""
    return spine.query_current_phase()


def handle_get_build_status(arguments):
    """Handler for cis_get_build_status."""
    node_label = arguments.get("node_label", "")
    if not node_label:
        return {"error": "node_label is required"}
    result = spine.query_build_status(node_label)
    if result is None:
        return {"error": "No build_plan_node found with label: {}".format(
            node_label)}
    return result


def handle_get_next_actions(arguments):
    """Handler for cis_get_next_actions."""
    return {"actions": spine.query_next_actions()}


def handle_get_recent_runs(arguments):
    """Handler for cis_get_recent_runs."""
    limit = arguments.get("limit", 5)
    return {"runs": spine.query_recent_runs(limit=limit)}


def handle_get_run_detail(arguments):
    """Handler for cis_get_run_detail."""
    run_id = arguments.get("run_id", "")
    if not run_id:
        return {"error": "run_id is required"}
    result = spine.query_run_detail(run_id)
    if result is None:
        return {"error": "No workflow_run found with id: {}".format(run_id)}
    return result


def handle_get_open_decisions(arguments):
    """Handler for cis_get_open_decisions."""
    return {"decisions": spine.query_open_decisions()}


def handle_get_open_questions(arguments):
    """Handler for cis_get_open_questions."""
    return {"questions": spine.query_open_questions()}


def handle_get_eric_gate_status(arguments):
    """Handler for cis_get_eric_gate_status."""
    return {"approvals": spine.query_eric_gate_status()}


def handle_search_sessions(arguments):
    """Handler for cis_search_sessions."""
    query_text = arguments.get("query", "")
    if not query_text:
        return {"error": "query is required"}
    limit = arguments.get("limit", 10)
    return {"sessions": spine.query_search_sessions(query_text, limit=limit)}


# ── Handler dispatch map ──────────────────────────────

HANDLERS = {
    "cis_get_current_phase": handle_get_current_phase,
    "cis_get_build_status": handle_get_build_status,
    "cis_get_next_actions": handle_get_next_actions,
    "cis_get_recent_runs": handle_get_recent_runs,
    "cis_get_run_detail": handle_get_run_detail,
    "cis_get_open_decisions": handle_get_open_decisions,
    "cis_get_open_questions": handle_get_open_questions,
    "cis_get_eric_gate_status": handle_get_eric_gate_status,
    "cis_search_sessions": handle_search_sessions,
}
