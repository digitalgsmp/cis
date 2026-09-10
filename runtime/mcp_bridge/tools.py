"""
tools.py - MCP tool definitions and handler functions for the CIS MCP Bridge.

Defines 14 tools (11 read-only + 3 dispatch) per FD.1 specification:
  Read-only (11): cis_get_current_phase, cis_get_build_status, cis_get_next_actions,
  cis_get_recent_runs, cis_get_run_detail, cis_get_open_decisions,
  cis_get_open_questions, cis_get_eric_gate_status, cis_search_sessions,
  cis_search_semantic, cis_get_similar
  Dispatch (3): cis_dispatch_drafter, cis_dispatch_reviewer, cis_dispatch_implementer
"""
from . import spine
import hashlib
import os
import re
import subprocess

# ── Read-only gating (CARD-01: measurement instruments) ─────────────
# The bridge also carries three dispatch tools (write surface). Reviewers must
# get the read-shaped subset only, so we tag every read-only tool by name and
# let the server serve a filtered list when CIS_MCP_MODE=readonly.

READONLY_TOOL_NAMES = {
    # spine queries + search (all SELECT-only / Chroma reads)
    "cis_get_current_phase",
    "cis_get_build_status",
    "cis_get_queue_item",
    "cis_get_next_actions",
    "cis_get_recent_runs",
    "cis_get_run_detail",
    "cis_get_open_decisions",
    "cis_get_open_questions",
    "cis_get_eric_gate_status",
    "cis_search_sessions",
    "cis_search_semantic",
    "cis_get_similar",
    "cis_search_knowledge",
    "cis_get_dev_pivot_status",
    # read-shaped file / git / hash instruments (CARD-01 DONE-WHEN 1)
    "cis_read_file",
    "cis_search_files",
    "cis_git_log",
    "cis_git_show",
    "cis_hash_file",
}


def tools_for_mode(mode):
    """Tool list for a mode. 'readonly' excludes the dispatch (write) tools."""
    if mode == "readonly":
        return [t for t in TOOLS if t["name"] in READONLY_TOOL_NAMES]
    return TOOLS


def _repo_root():
    """Repo root inside the container (overridable via CIS_REPO_ROOT)."""
    return os.environ.get("CIS_REPO_ROOT", "/workspace/cis")


def _scope_path(path):
    """Resolve a repo-relative path under the repo root; None on escape.

    Read-shaped by construction: it only ever resolves a path, never writes.
    """
    if not isinstance(path, str) or not path:
        return None
    root = os.path.realpath(_repo_root())
    p = os.path.realpath(os.path.join(root, path.lstrip("/")))
    if p != root and not p.startswith(root + os.sep):
        return None
    return p


def _run_git(args):
    """Run a hardcoded read-only git subcommand in the repo root.

    The argument list is assembled here from validated inputs only; the
    reviewer never supplies a command string, so there is no shell injection
    surface. Returns (ok, stdout-or-error).
    """
    try:
        r = subprocess.run(
            ["git"] + args, capture_output=True, text=True,
            timeout=30, cwd=_repo_root(),
        )
        return (r.returncode == 0), (r.stdout or r.stderr or "").strip()
    except Exception as exc:
        return False, str(exc)


def _repo_rel(sub_path):
    """Return a repo-relative path for a scoped sub-path (git needs relative)."""
    sp = _scope_path(sub_path)
    if sp is None:
        return None
    return os.path.relpath(sp, os.path.realpath(_repo_root()))


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
            "DEPRECATED for build-list work. Reads build_plan_nodes, which holds "
            "the COMPLETED June 2026 dependency-graph plan (tiers 0-13), NOT the "
            "unified build list. For a build-list item like '3.21' use "
            "cis_get_queue_item instead. "
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
        "name": "cis_get_queue_item",
        "description": (
            "Get a unified-build-list item by its number, e.g. '3.21'. Returns "
            "tier, title, scope, need_status and the item's prose. Does NOT "
            "return dependency edges: queue_edges is a 2026-09-05 snapshot that "
            "nothing regenerates, and serving it would let a caller believe "
            "stale dependencies are current."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_num": {
                    "type": "string",
                    "description": "Build-list item number. Example: '3.21'",
                },
            },
            "required": ["item_num"],
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
    {
        "name": "cis_search_semantic",
        "description": (
            "Semantic (vector) search across indexed CIS content using Chroma. "
            "Finds sessions, deliberations, decisions, and closeouts by meaning, "
            "not just keyword. Returns top-K results with relevance scores. "
            "Use when keyword search misses related concepts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query for semantic search",
                },
                "top_k": {
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
    {
        "name": "cis_get_similar",
        "description": (
            "Find documents similar to a given indexed document by ID. "
            "Returns top-K semantically similar documents with similarity scores. "
            "Use for 'find me more like this' discovery."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": (
                        "Document ID from a prior search result "
                        "(e.g., 'session_12345', 'decision_ADR-SEED-001')"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum results (default: 10, max: 50)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "cis_search_knowledge",
        "description": (
            "Search the shared CIS knowledge base (Claude conversations, "
            "CIS docs, archive files) using combined FTS5 keyword search "
            "and ChromaDB semantic search. Returns Eric's verbatim words, "
            "project documents, and conversation history. "
            "Use to find what Eric said about a topic, verify intentions, "
            "or discover prior work on a problem."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query to search the knowledge base",
                },
                "top_k": {
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
    {
        "name": "cis_dispatch_drafter",
        "description": (
            "Start the CIS Drafter pipeline for a crystallized topic. "
            "Creates a workflow_run and dispatches the Drafter to produce "
            "a specification. Returns the workflow_run_id for tracking."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic to draft a specification for",
                },
                "intent": {
                    "type": "string",
                    "description": "Why this topic needs a specification",
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session ID for context linking",
                },
            },
            "required": ["topic", "intent"],
        },
    },
    {
        "name": "cis_dispatch_reviewer",
        "description": (
            "Dispatch the CIS Reviewer (R1 + Qwen dual-review) for a "
            "Drafter proposal. Requires an existing workflow_run_id from "
            "cis_dispatch_drafter."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "The workflow_run ID to review",
                },
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "cis_dispatch_implementer",
        "description": (
            "Dispatch the CIS Implementer to execute an Eric-approved "
            "FINAL_DIRECTIVE. Requires a workflow_run_id with an Eric "
            "Gate APPROVE decision (checked via eric_gate_approvals)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "The workflow_run ID to implement",
                },
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "cis_adapter_status",
        "description": (
            "Check the health and availability of all CIS Hermes profiles "
            "through the abstraction layer adapter. Returns per-profile: "
            "healthy, port, model, response_time. Use this to discover "
            "which profiles are online before dispatching work."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "cis_adapter_dispatch",
        "description": (
            "Classify an intent and get the dispatch decision from the "
            "abstraction layer. Returns the recommended route (drafter, "
            "reviewer, implementer), profile name, port, gateway URL, "
            "confidence, reason, and matched signals. Use before sending "
            "work to a profile to confirm correct routing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The intent or message to classify and route",
                },
                "override": {
                    "type": "string",
                    "description": "Optional: force a specific route (drafter, reviewer, etc.)",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "cis_get_dev_pivot_status",
        "description": (
            "Get the status of all DEV-PIVOT architecture documents. "
            "Returns per-document: doc_id, title, category, status "
            "(LIVE/INVALIDATED/PARTIALLY_INVALIDATED/SUPERSEDED), "
            "invalidation_reason, depends_on, capability_gap. "
            "Use to discover which architectural problems are solved, "
            "which assumptions have changed, and which are still unsolved. "
            "Filter by status or category."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Optional: filter by status (LIVE, INVALIDATED, PARTIALLY_INVALIDATED, SUPERSEDED)",
                },
                "category_filter": {
                    "type": "string",
                    "description": "Optional: filter by category (governance, enforcement, architecture, pipeline, data, operations)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "cis_read_file",
        "description": (
            "Read a file inside the CIS repo (scoped to the repo root). "
            "READ-ONLY. Use to verify a discrepancy against the actual source, "
            "config, log, or evidence file rather than guessing. Cite the path "
            "and the content you relied on."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Repo-relative path, e.g. 'tools/advisor_review.sh'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max lines to return (default 400, max 1000)",
                    "default": 400,
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "cis_search_files",
        "description": (
            "Search file contents inside the CIS repo (git grep, regex). "
            "READ-ONLY. Use to find where a symbol, string, or claim appears. "
            "Returns matching lines with file:line references."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "Optional sub-path to narrow the search (repo-relative)",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "cis_git_log",
        "description": (
            "Show git commit history (READ-ONLY). Use to check what changed and "
            "when, and to cite a commit hash as evidence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max commits to return (default 20, max 100)",
                    "default": 20,
                },
                "path": {
                    "type": "string",
                    "description": "Optional repo-relative path to filter history to",
                },
            },
            "required": [],
        },
    },
    {
        "name": "cis_git_show",
        "description": (
            "Show a git commit or the current HEAD diff stat (READ-ONLY). "
            "Use to inspect what a specific commit changed and cite the hash."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "description": "Commit hash, branch name, or 'HEAD' (default HEAD)",
                    "default": "HEAD",
                },
            },
            "required": [],
        },
    },
    {
        "name": "cis_hash_file",
        "description": (
            "Compute the SHA-256 of a file (READ-ONLY). Use to compare an "
            "expected hash against an observed one and detect drift."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Repo-relative path to hash",
                },
            },
            "required": ["path"],
        },
    },
]


# ── Handler functions ─────────────────────────────────

def handle_get_current_phase(arguments):
    """Handler for cis_get_current_phase."""
    return spine.query_current_phase()


def handle_get_build_status(arguments):
    """Handler for cis_get_build_status.

    REDIRECTS build-list item numbers. Before 2026-09-09 an agent asking this
    tool about item '3.21' got "No build_plan_node found with label: 3.21" --
    a wrong answer delivered silently, because this tool reads the June build
    plan and the unified list uses dotted item numbers it has never contained.
    Leaving that live beside a correct tool is build list item 2.12: two queues,
    and the caller cannot tell which one answered.
    """
    node_label = arguments.get("node_label", "")
    if not node_label:
        return {"error": "node_label is required"}

    if re.match(r"^[0-9]+\.[0-9]+$", node_label.strip()):
        item = spine.query_queue_item(node_label.strip())
        return {
            "redirected_from": "cis_get_build_status",
            "reason": (
                "'{}' is a unified-build-list item number, not a "
                "build_plan_node label. build_plan_nodes holds the completed "
                "June 2026 plan and has never contained this item. Answered "
                "from queue_items instead; call cis_get_queue_item directly."
            ).format(node_label.strip()),
            "item": item,
        }

    result = spine.query_build_status(node_label)
    if result is None:
        return {"error": (
            "No build_plan_node found with label: {}. Note this tool reads the "
            "completed June 2026 build plan. For a unified-build-list item, use "
            "cis_get_queue_item."
        ).format(node_label)}
    return result


def handle_get_queue_item(arguments):
    """Handler for cis_get_queue_item — BUILD LIST 3.21's first reader."""
    item_num = str(arguments.get("item_num", "")).strip()
    if not item_num:
        return {"error": "item_num is required, e.g. '3.21'"}
    result = spine.query_queue_item(item_num)
    if result is None:
        return {"error": "No queue_items row for item_num: {}".format(item_num)}
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


def _get_chroma_client():
    """Lazy-load the Chroma client (heavy import)."""
    from . import chroma_index
    return chroma_index.get_client()


def handle_search_semantic(arguments):
    """Handler for cis_search_semantic."""
    query_text = arguments.get("query", "")
    if not query_text:
        return {"error": "query is required"}
    top_k = arguments.get("top_k", 10)
    client = _get_chroma_client()
    results = client.search_semantic(query_text, top_k=top_k)
    return {"results": results}


def handle_get_similar(arguments):
    """Handler for cis_get_similar."""
    document_id = arguments.get("document_id", "")
    if not document_id:
        return {"error": "document_id is required"}
    top_k = arguments.get("top_k", 10)
    client = _get_chroma_client()
    result = client.get_similar(document_id, top_k=top_k)
    if isinstance(result, dict) and "error" in result:
        return result
    return {"results": result}


def handle_dispatch_drafter(arguments):
    """Handler for cis_dispatch_drafter."""
    topic = arguments.get("topic", "")
    intent = arguments.get("intent", "")
    if not topic:
        return {"error": "topic is required"}
    if not intent:
        return {"error": "intent is required"}
    try:
        result = subprocess.run(
            ["python3", "tools/pipeline/drafter_start.py", topic,
             "--intent", intent],
            capture_output=True, text=True, timeout=300,
            cwd="/mnt/projects/cis",
        )
        if result.returncode != 0:
            return {"error": "drafter_start.py failed", "stderr": result.stderr}
        return {"workflow_run_id": "dispatched", "status": "DISPATCHED"}
    except Exception as exc:
        return {"error": str(exc)}


def handle_dispatch_reviewer(arguments):
    """Handler for cis_dispatch_reviewer."""
    run_id = arguments.get("run_id", "")
    if not run_id:
        return {"error": "run_id is required"}
    try:
        result = subprocess.run(
            ["python3", "tools/pipeline/reviewer_reconcile.py",
             "--run-id", run_id],
            capture_output=True, text=True, timeout=300,
            cwd="/mnt/projects/cis",
        )
        if result.returncode != 0:
            return {"error": "reviewer_reconcile.py failed", "stderr": result.stderr}
        return {"run_id": run_id, "status": "DISPATCHED"}
    except Exception as exc:
        return {"error": str(exc)}


def handle_dispatch_implementer(arguments):
    """Handler for cis_dispatch_implementer."""
    run_id = arguments.get("run_id", "")
    if not run_id:
        return {"error": "run_id is required"}
    approved = spine.check_eric_gate_approval(run_id)
    if not approved:
        return {"error": "Eric Gate approval required",
                "gate_status": "UNAPPROVED", "run_id": run_id}
    try:
        result = subprocess.run(
            ["bash", "tools/pipeline/pipeline_dispatch.sh", run_id],
            capture_output=True, text=True, timeout=300,
            cwd="/mnt/projects/cis",
        )
        if result.returncode != 0:
            return {"error": "dispatch failed", "stderr": result.stderr}
        return {"run_id": run_id, "status": "DISPATCHED",
                "gate_status": "APPROVED"}
    except Exception as exc:
        return {"error": str(exc)}


def handle_search_knowledge(arguments):
    """Handler for cis_search_knowledge — search shared knowledge base."""
    query = arguments.get("query", "")
    top_k = arguments.get("top_k", 10)
    if not query:
        return {"error": "query is required"}

    results = []
    # FTS5 full-text search
    try:
        fts_results = spine.search_knowledge_fts(query, limit=top_k)
        for row in fts_results:
            results.append({
                "id": row["id"],
                "content": (row.get("content", "") or "")[:500],
                "source": row.get("source", ""),
                "role": row.get("role", ""),
                "search_type": "fts5",
            })
    except Exception as e:
        results.append({"error": f"FTS5 search failed: {e}"})

    # Semantic search via ChromaDB
    try:
        semantic_results = spine.search_knowledge_semantic(query, top_k=top_k)
        for hit in semantic_results:
            results.append({
                "id": hit.get("id", ""),
                "content": (hit.get("content", "") or "")[:500],
                "source": hit.get("source", ""),
                "role": hit.get("role", ""),
                "score": hit.get("score", 0),
                "search_type": "semantic",
            })
    except Exception as e:
        results.append({"error": f"Semantic search failed: {e}"})

    return {"query": query, "results": results, "total": len(results)}


def handle_adapter_status(arguments):
    """Handler for cis_adapter_status — query adapter health via Flask API."""
    import urllib.request as _ur, json as _json
    try:
        req = _ur.Request("http://127.0.0.1:5000/api/adapter/health")
        resp = _ur.urlopen(req, timeout=10)
        return _json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"Adapter unreachable: {e}"}


def handle_adapter_dispatch(arguments):
    """Handler for cis_adapter_dispatch — classify intent via adapter API."""
    import urllib.request as _ur, json as _json
    message = arguments.get("message", "")
    override = arguments.get("override")
    if not message:
        return {"error": "message is required"}
    payload = _json.dumps({
        "message": message,
        "override": override,
        "classify_only": True,
    }).encode("utf-8")
    try:
        req = _ur.Request(
            "http://127.0.0.1:5000/api/adapter/dispatch",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = _ur.urlopen(req, timeout=30)
        return _json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"Adapter dispatch failed: {e}"}


def handle_get_dev_pivot_status(arguments):
    """Handler for cis_get_dev_pivot_status."""
    status_filter = arguments.get("status_filter")
    category_filter = arguments.get("category_filter")
    return spine.query_dev_pivot_status(
        status_filter=status_filter,
        category_filter=category_filter,
    )


def handle_read_file(arguments):
    """Handler for cis_read_file — scoped, read-only file read."""
    path = arguments.get("path", "")
    limit = arguments.get("limit", 400)
    p = _scope_path(path)
    if p is None:
        return {"error": "path is outside the CIS repo scope: " + path}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except FileNotFoundError:
        return {"error": "file not found: " + path}
    except IsADirectoryError:
        return {"error": "is a directory: " + path}
    except Exception as exc:
        return {"error": str(exc)}
    lines = text.splitlines()
    try:
        limit = max(1, min(int(limit), 1000))
    except (TypeError, ValueError):
        limit = 400
    return {
        "path": path,
        "total_lines": len(lines),
        "content": "\n".join(lines[:limit]),
    }


def handle_search_files(arguments):
    """Handler for cis_search_files — git grep, read-only."""
    pattern = arguments.get("pattern", "")
    if not pattern:
        return {"error": "pattern is required"}
    args = ["grep", "-n", "-I", "--", pattern]
    sub = arguments.get("path", "")
    if sub:
        rel = _repo_rel(sub)
        if rel is None:
            return {"error": "path is outside the CIS repo scope: " + sub}
        args += ["--", rel]
    ok, out = _run_git(args)
    if not ok:
        return {"error": out or "git grep failed"}
    return {"pattern": pattern, "matches": out[:20000]}


def handle_git_log(arguments):
    """Handler for cis_git_log — read-only history."""
    limit = arguments.get("limit", 20)
    try:
        limit = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        limit = 20
    args = ["log", "--oneline", "-n", str(limit)]
    sub = arguments.get("path", "")
    if sub:
        rel = _repo_rel(sub)
        if rel is None:
            return {"error": "path is outside the CIS repo scope: " + sub}
        args += ["--", rel]
    ok, out = _run_git(args)
    if not ok:
        return {"error": out or "git log failed"}
    return {"commits": out}


def handle_git_show(arguments):
    """Handler for cis_git_show — read-only commit/HEAD inspection."""
    ref = str(arguments.get("ref", "HEAD") or "HEAD")
    if not re.match(r"^[A-Za-z0-9._~^/\-]+$", ref):
        return {"error": "invalid ref: " + ref}
    ok, out = _run_git(["show", "--stat", "--oneline", ref])
    if not ok:
        return {"error": out or "git show failed"}
    return {"ref": ref, "output": out[:20000]}


def handle_hash_file(arguments):
    """Handler for cis_hash_file — SHA-256 of a scoped file."""
    path = arguments.get("path", "")
    p = _scope_path(path)
    if p is None:
        return {"error": "path is outside the CIS repo scope: " + path}
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except FileNotFoundError:
        return {"error": "file not found: " + path}
    except IsADirectoryError:
        return {"error": "is a directory: " + path}
    except Exception as exc:
        return {"error": str(exc)}
    return {"path": path, "sha256": h.hexdigest()}


# ── Handler dispatch map ──────────────────────────────

HANDLERS = {
    "cis_get_current_phase": handle_get_current_phase,
    "cis_get_build_status": handle_get_build_status,
    "cis_get_queue_item": handle_get_queue_item,
    "cis_get_next_actions": handle_get_next_actions,
    "cis_get_recent_runs": handle_get_recent_runs,
    "cis_get_run_detail": handle_get_run_detail,
    "cis_get_open_decisions": handle_get_open_decisions,
    "cis_get_open_questions": handle_get_open_questions,
    "cis_get_eric_gate_status": handle_get_eric_gate_status,
    "cis_search_sessions": handle_search_sessions,
    "cis_search_semantic": handle_search_semantic,
    "cis_get_similar": handle_get_similar,
    "cis_dispatch_drafter": handle_dispatch_drafter,
    "cis_dispatch_reviewer": handle_dispatch_reviewer,
    "cis_dispatch_implementer": handle_dispatch_implementer,
    "cis_search_knowledge": handle_search_knowledge,
    "cis_adapter_status": handle_adapter_status,
    "cis_adapter_dispatch": handle_adapter_dispatch,
    "cis_get_dev_pivot_status": handle_get_dev_pivot_status,
    "cis_read_file": handle_read_file,
    "cis_search_files": handle_search_files,
    "cis_git_log": handle_git_log,
    "cis_git_show": handle_git_show,
    "cis_hash_file": handle_hash_file,
}
