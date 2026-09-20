"""
workbench_app.py — CIS Workbench: fresh project + Braingate conversation.

Queue item WB.1A. Exploration only:
  - Named project creation, no repo path required.
  - Project-scoped conversation with the Brain gateway (port 8644 by default),
    persisted across reloads.
  - Compact KB context (existing FTS5 index, existing secret redaction).
  - No pipeline-start action lives here. /api/relay/brain/start (a separate,
    unconfirmed gate) is not called or referenced by this module.

Self-contained Flask Blueprint — does not import runtime/api/relay.py, so it
has no dependency on that module's pipeline machinery and can be unit tested
in isolation with a temporary database and a monkeypatched gateway call.
"""
import json
import os
import re
import sqlite3
import time
import uuid
from typing import Optional

from flask import Blueprint, jsonify, request

import httpx

from card_factory_app import (
    card_factory_bp,
    submit_ask_core,
    edit_ask_core,
    generate_card_core,
    _card_dict as _cf_card_dict,
)
from card_runner import (
    card_runner_bp,
    dispatch as _cr_dispatch,
    run_status as _cr_run_status,
    DEFAULT_TIMEOUT_SECONDS as _CR_DEFAULT_TIMEOUT_SECONDS,
    RunnerError as _CRRunnerError,
    RevisionMismatch as _CRRevisionMismatch,
    RunnerBusy as _CRRunnerBusy,
    NotFound as _CRNotFound,
)

workbench_bp = Blueprint("workbench", __name__)
# Card Factory (WB.1B-1) and Card Runner (WB.1B-2/2A) are sibling modules'
# blueprints, nested here so a single `app.register_blueprint(workbench_bp)`
# in container_app.py brings in Braingate, Card Factory and Card Runner
# routes together. workbench_app.py also calls card_factory_app's and
# card_runner's plain functions directly (below) for the proposal workflow
# — the nested blueprints expose the same operations over HTTP too, but the
# proposal routes never go through HTTP internally to reach them.
workbench_bp.register_blueprint(card_factory_bp)
workbench_bp.register_blueprint(card_runner_bp)

# ── Config ───────────────────────────────────────────────────────────────

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
API_KEY = os.environ.get("CIS_PIPELINE_API_KEY", "")
BRAIN_GATEWAY_URL = os.environ.get(
    "CIS_WORKBENCH_BRAIN_URL", "http://127.0.0.1:8644/v1/chat/completions"
)
BRAIN_API_KEY_ENV = "CIS_BRAIN_API_KEY"

# A row left in 'pending' longer than this is not an in-flight request
# anymore (a synchronous Flask handler resolves pending -> completed/failed
# within the same request) — it means the process died mid-call. Reconciled
# to 'interrupted' honestly rather than left showing as still-working.
STALE_PENDING_SECONDS = 90

# Documented, configurable input allowance for the single Brain-gateway call
# in send_message(): system instructions + KB excerpts ("explicitly linked
# relevant sources") + Eric's own message are always treated as required —
# if those alone exceed the budget, the call is refused before it happens
# (a visible overflow, not a silent drop). Older conversation history is the
# only thing this ever trims, and only by omitting the oldest messages —
# every omitted id is still reported and still lives in the stored
# transcript, never deleted.
WORKBENCH_CONTEXT_CHAR_BUDGET = int(
    os.environ.get("CIS_WORKBENCH_CONTEXT_CHAR_BUDGET", "12000")
)

# Eric must explicitly ask for a proposal (mode='draft_proposal' on a
# message send) — plain conversational replies never produce one, and this
# never triggers a second model call: the same single _call_brain_gateway
# call already made for the reply is reused, the model is just asked to
# append a structured block after its normal reply.
PROPOSAL_MARKER = "---PROPOSAL---"
PROPOSAL_KINDS = ("mockup", "experiment", "implementation")

BASE_SYSTEM_PROMPT = (
    "You are Braingate, the clarification partner for a new CIS project. "
    "Your role here is exploration and clarification only — you cannot "
    "start execution, approve work, or dispatch agents from this "
    "conversation. Ask a focused clarifying question only when something "
    "necessary is missing; routine technical choices need no "
    "interrogation.\n\n"
)
DRAFT_PROPOSAL_INSTRUCTIONS = (
    "Eric has explicitly asked for a proposed next action. If you have "
    "enough to propose one, reply normally, then on its own new line write "
    "exactly " + PROPOSAL_MARKER + " followed by a single JSON object (no "
    "markdown fence) with exactly these keys: kind (one of \"mockup\", "
    "\"experiment\", \"implementation\"), outcome, action, boundaries, "
    "success_criteria, unresolved_decisions (an empty string if none), "
    "permitted_files (a JSON array of the specific repo-relative file "
    "paths this action would need to change — Eric approves this exact "
    "list instead of typing paths himself, so name every file you can "
    "already tell it needs; an empty array only if you genuinely cannot "
    "name any yet), permitted_commands (a JSON array of shell command "
    "prefixes this action would need to run beyond editing files, e.g. "
    "\"pytest\" or \"npm run build\" — an empty array if none are needed). "
    "If you do not yet have enough to propose one, ask your clarifying "
    "question instead and omit the " + PROPOSAL_MARKER + " block entirely "
    "— never fabricate a proposal you are not ready to make.\n\n"
)
# mode='revise_proposal' is the backend's own natural-language-to-fields
# path for a conversational correction — it must never be left as a
# frontend-only concern, and must never add a second model call: this
# template is folded into the SAME system prompt the one _call_brain_gateway
# call already uses. The target proposal's current fields/boundaries are
# always included here (never subject to history trimming) — omitting them
# and merely recording their ids as "omitted" would not actually protect
# them, since the model doing the revision would never see them.
REVISE_PROPOSAL_TEMPLATE = (
    "Eric is revising an existing proposal below, not starting a new one — "
    "do not invent different current values.\n"
    "Its original verbatim words:\n{user_words}\n\n"
    "Its current fields (Braingate's own structured interpretation, not "
    "Eric's words):\n{fields_block}\n"
    "Reply normally to Eric's correction, then on its own new line write "
    "exactly " + PROPOSAL_MARKER + " followed by a single JSON object with "
    "the SAME keys as above, containing the FULLY revised proposal — repeat "
    "any field that is unchanged, update whichever changed. Omit the "
    + PROPOSAL_MARKER + " block entirely if you do not yet have enough for "
    "a confident revision.\n\n"
)


def _check_auth():
    if not API_KEY:
        return None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:].strip() == API_KEY:
        return None
    return jsonify({"error": "Unauthorized", "detail": "Invalid or missing API key"}), 401


def _db(db_path: str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ── Secret redaction on the way OUT (reuses the existing Tier 9 filter) ────

def _redact(text: str) -> str:
    """Mask secret-shaped strings before KB excerpts reach the page.

    Fails closed: if the filter can't be imported, the text is withheld
    rather than shown unfiltered. Mirrors runtime/abstraction/pipeline_relay
    ._redact_secrets.
    """
    try:
        from mcp_bridge.chroma_index import redact_secrets
    except Exception as e:
        return f"(KB content withheld — secret filter unavailable: {type(e).__name__})"
    return redact_secrets(text)


KB_RETRIEVAL_LIMITATIONS = (
    "Keyword match (FTS5) over the existing knowledge_messages index; top 5 "
    "hits; excerpts truncated to 500 characters; no reindexing performed for "
    "this request."
)


def _kb_search(conn: sqlite3.Connection, query: str, limit: int = 5) -> list:
    """Search the existing KB FTS5 index. Reuses the index built for the
    pipeline's Brain chat (runtime/api/relay.py::_kb_search) — no corpus
    mining or reindexing project."""
    keywords = re.sub(r'[."*(){}:^+\-]', ' ', query).strip() or "CIS project"
    try:
        rows = conn.execute(
            "SELECT content, source FROM knowledge_messages_fts "
            "WHERE knowledge_messages_fts MATCH ? ORDER BY rank LIMIT ?",
            (keywords, limit),
        ).fetchall()
    except Exception:
        return []
    return [{"content": _redact(r[0][:500]), "source": r[1]} for r in rows]


def _call_brain_gateway(messages: list, timeout: float = 60.0):
    """Call the configured Brain gateway. Returns (content, error) — exactly
    one of the two is not None. Never fabricates a response and never
    substitutes another model on failure."""
    key = os.environ.get(BRAIN_API_KEY_ENV, "")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    payload = {"model": "agent", "messages": messages, "max_tokens": 4096}
    try:
        resp = httpx.post(BRAIN_GATEWAY_URL, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            return None, "Brain gateway returned an empty response"
        return content, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


# ── Projects ─────────────────────────────────────────────────────────────

def _project_dict(row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "kind": row["kind"],
        "repo_path": row["repo_path"],
        "direction_note": row["direction_note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@workbench_bp.route("/api/workbench/projects", methods=["GET"])
def list_projects():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT * FROM workbench_projects ORDER BY updated_at DESC"
        ).fetchall()
        return jsonify({"projects": [_project_dict(r) for r in rows]})
    finally:
        conn.close()


@workbench_bp.route("/api/workbench/projects", methods=["POST"])
def create_project():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    if len(name) > 200:
        return jsonify({"error": "name too long (max 200 characters)"}), 400

    # This slice creates planning projects only — no provisioned repo is
    # created or inferred. The 'kind' column exists so a future provisioning
    # workflow has somewhere to record the distinction; it is not exercised
    # by this endpoint.
    kind = "planning"
    project_id = uuid.uuid4().hex[:12]

    conn = _db()
    try:
        conn.execute(
            "INSERT INTO workbench_projects (id, name, kind) VALUES (?, ?, ?)",
            (project_id, name, kind),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        return jsonify({"project": _project_dict(row)}), 201
    finally:
        conn.close()


@workbench_bp.route("/api/workbench/projects/<project_id>", methods=["GET"])
def get_project(project_id: str):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "project not found"}), 404
        return jsonify({"project": _project_dict(row)})
    finally:
        conn.close()


@workbench_bp.route("/api/workbench/projects/<project_id>", methods=["PATCH"])
def update_project(project_id: str):
    """Optional small editable direction note. Nothing here marks an intent
    approved or gates execution — it is a free-text scratch note only."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    if "direction_note" not in data:
        return jsonify({"error": "direction_note required"}), 400
    note = (data.get("direction_note") or "").strip()
    if len(note) > 4000:
        return jsonify({"error": "direction_note too long (max 4000 characters)"}), 400

    conn = _db()
    try:
        row = conn.execute(
            "SELECT id FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "project not found"}), 404
        conn.execute(
            "UPDATE workbench_projects SET direction_note = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (note, project_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        return jsonify({"project": _project_dict(row)})
    finally:
        conn.close()


# ── Conversation ─────────────────────────────────────────────────────────

def _message_dict(row) -> dict:
    kb_context = None
    if row["kb_context"]:
        try:
            kb_context = json.loads(row["kb_context"])
        except (TypeError, ValueError):
            kb_context = None
    context_used = None
    if row["context_meta"]:
        try:
            context_used = json.loads(row["context_meta"])
        except (TypeError, ValueError):
            context_used = None
    return {
        "id": row["id"],
        "role": row["role"],
        "content": row["content"],
        "status": row["status"],
        "kb_context": kb_context,
        "kb_limitations": KB_RETRIEVAL_LIMITATIONS if kb_context else None,
        "context_used": context_used,
        "error": row["error"],
        "created_at": row["created_at"],
    }


# ── Action proposals ────────────────────────────────────────────────────
# Eric explores/clarifies in conversation, sees a proposed bounded action
# (this table), approves it explicitly and receives results back in the
# same project — he never fills out a technical card by hand. See module
# docstring addendum in evidence.md for the full route/payload contract.

def _parse_proposal_block(content: str):
    """Splits an explicitly-requested draft reply into (fields, display_text).
    fields is None — and display_text is the ORIGINAL content, unmodified —
    whenever no well-formed proposal block is present; a proposal is never
    fabricated from malformed or missing model output."""
    if not content or PROPOSAL_MARKER not in content:
        return None, content
    prefix, _, block = content.partition(PROPOSAL_MARKER)
    try:
        data = json.loads(block.strip())
    except (json.JSONDecodeError, ValueError, TypeError):
        return None, content
    if not isinstance(data, dict) or data.get("kind") not in PROPOSAL_KINDS:
        return None, content
    permitted_files = data.get("permitted_files")
    permitted_commands = data.get("permitted_commands")
    fields = {
        "kind": data["kind"],
        "outcome": (data.get("outcome") or "").strip() or None,
        "action": (data.get("action") or "").strip() or None,
        "boundaries": (data.get("boundaries") or "").strip() or None,
        "success_criteria": (data.get("success_criteria") or "").strip() or None,
        "unresolved_decisions": (data.get("unresolved_decisions") or "").strip() or None,
        # Malformed/missing scope defaults to an empty, explicit list — never
        # invented, never silently dropped from the parsed result.
        "permitted_files": [str(f) for f in permitted_files] if isinstance(permitted_files, list) else [],
        "permitted_commands": [str(c) for c in permitted_commands] if isinstance(permitted_commands, list) else [],
    }
    return fields, prefix.strip()


def _proposal_dict(row) -> dict:
    return {
        "id": row["id"],
        "project_id": row["project_id"],
        "source_message_ids": json.loads(row["source_message_ids_json"] or "[]"),
        "user_words": row["user_words"],
        "kind": row["kind"],
        "outcome": row["outcome"],
        "action": row["action"],
        "boundaries": row["boundaries"],
        "success_criteria": row["success_criteria"],
        "unresolved_decisions": row["unresolved_decisions"],
        "permitted_files": json.loads(row["permitted_files_json"] or "[]"),
        "permitted_commands": json.loads(row["permitted_commands_json"] or "[]"),
        "revision": row["revision"],
        "confirmed_revision": row["confirmed_revision"],
        "status": row["status"],
        "approved_at": row["approved_at"],
        "approved_by": row["approved_by"],
        "approved_fingerprint": row["approved_fingerprint"],
        "card_factory_ask_id": row["card_factory_ask_id"],
        "card_factory_card_id": row["card_factory_card_id"],
        "card_runner_run_id": row["card_runner_run_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _proposal_fields_block(row) -> str:
    """The model-authored fields only — never user_words — clearly
    labeled wherever it's used (the generator's extra context, and the
    revise_proposal conversational prompt) so "user quotes" and "model
    interpretation" stay visibly distinct to whatever reads it next."""
    return (
        f"kind: {row['kind']}\n"
        f"outcome: {row['outcome'] or ''}\n"
        f"action: {row['action'] or ''}\n"
        f"boundaries: {row['boundaries'] or ''}\n"
        f"success_criteria: {row['success_criteria'] or ''}\n"
        f"unresolved_decisions: {row['unresolved_decisions'] or ''}\n"
        f"permitted_files: {row['permitted_files_json'] or '[]'}\n"
        f"permitted_commands: {row['permitted_commands_json'] or '[]'}\n"
    )


PROPOSAL_EDITABLE_FIELDS = (
    "kind", "outcome", "action", "boundaries", "success_criteria", "unresolved_decisions",
    "permitted_files", "permitted_commands",
)
# The two scope fields are stored as *_json columns (arrays), unlike every
# other editable field (plain text columns of the same name) — this map is
# the one place that distinction is handled, so _apply_proposal_correction
# and edit_proposal don't need their own copies of it.
PROPOSAL_LIST_FIELD_COLUMNS = {
    "permitted_files": "permitted_files_json",
    "permitted_commands": "permitted_commands_json",
}


def _apply_proposal_correction(conn, row, updates: dict, append_user_words=None,
                                append_source_message_id=None, set_request_id=None):
    """Applies a correction to an existing proposal row — used by both the
    technical PATCH route and the conversational mode='revise_proposal'
    turn, so the two can never diverge on the invalidation rule. ANY
    material change to the model-authored fields (not just
    success_criteria) bumps `revision`, clears any existing approval, and
    — if a card_factory_ask_id is already linked — force-bumps that ask's
    own revision too (via edit_ask_core's force_revision_bump), even for
    fields (action, boundaries, kind, unresolved_decisions) that have no
    column of their own on card_factory_asks. That is what actually stales
    the linked card_factory_cards row at the boundary card_runner.
    dispatch() independently checks.

    Validates and commits the ask-side invalidation AND the proposal's own
    row together, on this one connection, in that order — either both
    land or neither does. A prior version committed the proposal row
    first and discarded edit_ask_core's (status, body), so a rejected ask
    update (e.g. success_criteria one character over MAX_DONE_WHEN_CHARS)
    left a proposal claiming a new revision while the ask/card stayed on
    the old one — fully, directly dispatchable despite the proposal
    saying otherwise (revisions observed as (2,1,1): the exact
    reproduction an independent review filed). Returns (status_code,
    result): (200, refreshed_row) on success; on failure, whatever
    non-200 (status_code, body) edit_ask_core itself returned, with
    NOTHING written — not even the proposal's own fields/revision."""
    proposal_id = row["id"]

    def _field_changed(f, v):
        if f in PROPOSAL_LIST_FIELD_COLUMNS:
            return json.dumps(v if v is not None else []) != (row[PROPOSAL_LIST_FIELD_COLUMNS[f]] or "[]")
        return (v or None) != row[f]

    changed = any(_field_changed(f, v) for f, v in updates.items())

    if changed and row["card_factory_ask_id"]:
        # Validate + apply the authoritative invalidation FIRST, on this
        # same connection, without committing — a failure here must leave
        # the proposal's own row untouched too.
        prospective_user_words = row["user_words"] + append_user_words if append_user_words \
            else row["user_words"]
        prospective_success_criteria = updates.get("success_criteria", row["success_criteria"])
        ask_status, ask_body = edit_ask_core(
            row["card_factory_ask_id"], ask_text=prospective_user_words,
            done_when_text=prospective_success_criteria or "",
            done_when_verbatim=False, force_revision_bump=True, conn=conn,
        )
        if ask_status != 200:
            conn.rollback()
            return ask_status, ask_body

    set_parts, params = [], []
    for f, v in updates.items():
        if f in PROPOSAL_LIST_FIELD_COLUMNS:
            set_parts.append(f"{PROPOSAL_LIST_FIELD_COLUMNS[f]} = ?")
            params.append(json.dumps(v if v is not None else []))
        else:
            set_parts.append(f"{f} = ?")
            params.append(v)
    if append_user_words:
        set_parts.append("user_words = user_words || ?")
        params.append(append_user_words)
    if append_source_message_id is not None:
        current_ids = json.loads(row["source_message_ids_json"] or "[]")
        if append_source_message_id not in current_ids:
            current_ids.append(append_source_message_id)
        set_parts.append("source_message_ids_json = ?")
        params.append(json.dumps(current_ids))
    if set_request_id is not None:
        set_parts.append("request_id = ?")
        params.append(set_request_id)
    if changed:
        set_parts.append(
            "revision = revision + 1, status = 'proposed', approved_at = NULL, "
            "approved_by = NULL, approved_fingerprint = NULL"
        )
    if set_parts:
        set_parts.append("updated_at = datetime('now')")
        conn.execute(
            f"UPDATE workbench_action_proposals SET {', '.join(set_parts)} WHERE id = ?",
            params + [proposal_id],
        )
    # One commit covers both the ask-side invalidation above and the
    # proposal update here — other connections (e.g. a direct
    # card_runner.dispatch() call reading card_factory_asks) only ever
    # observe the fully-old or the fully-new state, never a mix.
    conn.commit()

    fresh_row = conn.execute(
        "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
    ).fetchone()
    return 200, fresh_row


def _reconcile_stale_pending(conn: sqlite3.Connection, project_id: str) -> None:
    """A message row still 'pending' after STALE_PENDING_SECONDS did not
    finish because the process handling it is gone, not because it is still
    working. Reconciled to 'interrupted' so the page never shows a stuck
    spinner as its only signal."""
    cutoff = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.gmtime(time.time() - STALE_PENDING_SECONDS)
    )
    conn.execute(
        "UPDATE workbench_messages SET status = 'interrupted', "
        "error = COALESCE(error, 'No response was received — the request was "
        "interrupted (process restart or lost connection).') "
        "WHERE project_id = ? AND status = 'pending' AND created_at < ?",
        (project_id, cutoff),
    )
    conn.commit()


@workbench_bp.route("/api/workbench/projects/<project_id>/messages", methods=["GET"])
def list_messages(project_id: str):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        proj = conn.execute(
            "SELECT id FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not proj:
            return jsonify({"error": "project not found"}), 404
        _reconcile_stale_pending(conn, project_id)
        rows = conn.execute(
            "SELECT * FROM workbench_messages WHERE project_id = ? ORDER BY id ASC",
            (project_id,),
        ).fetchall()
        return jsonify({"messages": [_message_dict(r) for r in rows]})
    finally:
        conn.close()


@workbench_bp.route("/api/workbench/projects/<project_id>/messages", methods=["POST"])
def send_message(project_id: str):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    request_id = (data.get("request_id") or "").strip()
    mode = (data.get("mode") or "chat").strip()
    if mode not in ("chat", "draft_proposal", "revise_proposal"):
        return jsonify({"error": "mode must be 'chat', 'draft_proposal' or 'revise_proposal'"}), 400
    if not request_id:
        return jsonify({"error": "request_id required"}), 400
    if not message:
        return jsonify({"error": "message required"}), 400
    if len(message) > 8000:
        return jsonify({"error": "message too long (max 8000 characters)"}), 400
    target_proposal_id = data.get("proposal_id")
    if mode == "revise_proposal" and not target_proposal_id:
        return jsonify({"error": "proposal_id required for mode='revise_proposal'"}), 400

    conn = _db()
    try:
        proj = conn.execute(
            "SELECT id FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not proj:
            return jsonify({"error": "project not found"}), 404

        target_proposal = None
        if mode == "revise_proposal":
            target_proposal = conn.execute(
                "SELECT * FROM workbench_action_proposals WHERE id = ? AND project_id = ?",
                (target_proposal_id, project_id),
            ).fetchone()
            if not target_proposal:
                return jsonify({"error": "proposal not found"}), 404

        # Duplicate-submit guard: the same request_id resolves to the same
        # pair of rows (plus whichever proposal it created or corrected)
        # instead of creating a new send or a second model call.
        existing_user = conn.execute(
            "SELECT * FROM workbench_messages WHERE project_id = ? AND request_id = ? "
            "AND role = 'user'",
            (project_id, request_id),
        ).fetchone()
        if existing_user:
            existing_brain = conn.execute(
                "SELECT * FROM workbench_messages WHERE project_id = ? AND request_id = ? "
                "AND role = 'brain'",
                (project_id, request_id),
            ).fetchone()
            existing_proposal = conn.execute(
                "SELECT * FROM workbench_action_proposals WHERE project_id = ? AND request_id = ?",
                (project_id, request_id),
            ).fetchone()
            return jsonify({
                "duplicate": True,
                "user_message": _message_dict(existing_user),
                "brain_message": _message_dict(existing_brain) if existing_brain else None,
                "proposal": _proposal_dict(existing_proposal) if existing_proposal else None,
            })

        conn.execute(
            "INSERT INTO workbench_messages (project_id, role, content, status, request_id) "
            "VALUES (?, 'user', ?, 'completed', ?)",
            (project_id, message, request_id),
        )
        user_row = conn.execute(
            "SELECT * FROM workbench_messages WHERE project_id = ? AND request_id = ? "
            "AND role = 'user'",
            (project_id, request_id),
        ).fetchone()

        # ── Bounded context: system instructions + KB excerpts ("explicitly
        # linked relevant sources") + the target proposal's own current
        # fields/boundaries (revise_proposal mode) + Eric's own message are
        # all required — if those alone don't fit the documented budget,
        # refuse before any model call rather than silently drop part of
        # them. Only older conversation history is ever trimmed, and only
        # by omitting the oldest messages (never deleted from storage,
        # always reported) — recording an id as "omitted" is bookkeeping,
        # not protection, so anything required never goes through that path.
        kb_results = _kb_search(conn, message)
        kb_block = (
            "".join(f"- [{hit['source']}] {hit['content'][:200]}\n" for hit in kb_results)
            if kb_results else "(No KB results found for this query)\n"
        )
        mode_instructions = ""
        if mode == "draft_proposal":
            mode_instructions = DRAFT_PROPOSAL_INSTRUCTIONS
        elif mode == "revise_proposal":
            mode_instructions = REVISE_PROPOSAL_TEMPLATE.format(
                user_words=target_proposal["user_words"],
                fields_block=_proposal_fields_block(target_proposal),
            )
        system_preface = BASE_SYSTEM_PROMPT + mode_instructions
        base_prompt = system_preface + "Knowledge base context for this message:\n" + kb_block
        required_chars = len(base_prompt) + len(message)

        if required_chars > WORKBENCH_CONTEXT_CHAR_BUDGET:
            context_meta = {
                "budget_chars": WORKBENCH_CONTEXT_CHAR_BUDGET,
                "required_chars": required_chars,
                "history_messages_included": [],
                "history_messages_omitted": None,
                "overflow": True,
            }
            overflow_error = (
                f"context overflow: required context ({required_chars} characters — system "
                "instructions, explicitly linked KB sources, and Eric's own message) exceeds "
                f"the configured budget ({WORKBENCH_CONTEXT_CHAR_BUDGET} characters, "
                "CIS_WORKBENCH_CONTEXT_CHAR_BUDGET) — refused before calling the model; "
                "nothing was silently dropped."
            )
            conn.execute(
                "INSERT INTO workbench_messages "
                "(project_id, role, content, status, kb_context, error, context_meta, request_id) "
                "VALUES (?, 'brain', NULL, 'failed', ?, ?, ?, ?)",
                (project_id, json.dumps(kb_results) if kb_results else None, overflow_error,
                 json.dumps(context_meta), request_id),
            )
            conn.execute(
                "UPDATE workbench_projects SET updated_at = datetime('now') WHERE id = ?",
                (project_id,),
            )
            conn.commit()
            brain_row = conn.execute(
                "SELECT * FROM workbench_messages WHERE project_id = ? AND request_id = ? "
                "AND role = 'brain'",
                (project_id, request_id),
            ).fetchone()
            return jsonify({
                "duplicate": False,
                "user_message": _message_dict(user_row),
                "brain_message": _message_dict(brain_row),
                "proposal": None,
            })

        conn.execute(
            "INSERT INTO workbench_messages "
            "(project_id, role, content, status, kb_context, request_id) "
            "VALUES (?, 'brain', NULL, 'pending', ?, ?)",
            (project_id, json.dumps(kb_results) if kb_results else None, request_id),
        )
        conn.commit()
        brain_row_id = conn.execute(
            "SELECT id FROM workbench_messages WHERE project_id = ? AND request_id = ? "
            "AND role = 'brain'",
            (project_id, request_id),
        ).fetchone()["id"]

        # "Recent messages" window: older history only, most recent first,
        # kept only while it fits what's left of the budget after the
        # required context above.
        history_rows = conn.execute(
            "SELECT id, role, content FROM workbench_messages "
            "WHERE project_id = ? AND status = 'completed' AND id < ? ORDER BY id DESC",
            (project_id, user_row["id"]),
        ).fetchall()
        remaining = WORKBENCH_CONTEXT_CHAR_BUDGET - required_chars
        included, omitted = [], []
        used = 0
        for r in history_rows:
            row_len = len(r["content"] or "")
            if used + row_len <= remaining:
                included.append(r)
                used += row_len
            else:
                omitted.append(r["id"])
        included.reverse()  # chronological order for the model
        context_meta = {
            "budget_chars": WORKBENCH_CONTEXT_CHAR_BUDGET,
            "required_chars": required_chars,
            "history_messages_included": [r["id"] for r in included],
            "history_messages_omitted": omitted,
            "overflow": False,
        }

        messages = [{"role": "system", "content": base_prompt}]
        for r in included:
            role = "assistant" if r["role"] == "brain" else "user"
            messages.append({"role": role, "content": r["content"]})
        messages.append({"role": "user", "content": message})

        content, error = _call_brain_gateway(messages)

        parsed = None
        if error is None and mode in ("draft_proposal", "revise_proposal"):
            parsed, content = _parse_proposal_block(content)

        if error is not None:
            conn.execute(
                "UPDATE workbench_messages SET status = 'failed', error = ?, context_meta = ? "
                "WHERE id = ?",
                (error, json.dumps(context_meta), brain_row_id),
            )
        else:
            conn.execute(
                "UPDATE workbench_messages SET status = 'completed', content = ?, context_meta = ? "
                "WHERE id = ?",
                (content, json.dumps(context_meta), brain_row_id),
            )
        conn.execute(
            "UPDATE workbench_projects SET updated_at = datetime('now') WHERE id = ?",
            (project_id,),
        )
        conn.commit()

        proposal_row = None
        proposal_error = None
        if parsed is not None and mode == "draft_proposal":
            # Multi-turn provenance: "a last message such as 'yes, draft
            # that' must not replace the substantive earlier request" — the
            # verbatim words backing this proposal are every user-authored
            # message actually sent to the model this turn (the same
            # `included` window computed above), not just the one that
            # happened to trigger drafting.
            user_history = [r for r in included if r["role"] == "user"]
            user_words = "\n\n".join(r["content"] for r in user_history + [user_row])
            source_ids = [r["id"] for r in user_history] + [user_row["id"]]
            conn.execute(
                "INSERT INTO workbench_action_proposals "
                "(project_id, source_message_ids_json, user_words, kind, outcome, action, "
                "boundaries, success_criteria, unresolved_decisions, permitted_files_json, "
                "permitted_commands_json, request_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, json.dumps(source_ids), user_words, parsed["kind"],
                 parsed["outcome"], parsed["action"], parsed["boundaries"],
                 parsed["success_criteria"], parsed["unresolved_decisions"],
                 json.dumps(parsed["permitted_files"]), json.dumps(parsed["permitted_commands"]),
                 request_id),
            )
            conn.commit()
            proposal_row = conn.execute(
                "SELECT * FROM workbench_action_proposals WHERE project_id = ? AND request_id = ?",
                (project_id, request_id),
            ).fetchone()
        elif parsed is not None and mode == "revise_proposal":
            # Applies the same field-level invalidation rule PATCH uses
            # (_apply_proposal_correction), so a conversational correction
            # and a technical one can never diverge. user_words is never
            # overwritten — only appended, preserving the substantive
            # original request across turns/corrections. The conversation
            # reply itself already succeeded (the model did produce a
            # revision) — but applying it can still be rejected (e.g. the
            # accumulated correction text now exceeds card_factory_app's
            # own bound); that failure is surfaced honestly as
            # `proposal_error`, never silently dropped or fabricated into
            # a fake success.
            correction_status, correction_result = _apply_proposal_correction(
                conn, target_proposal, dict(parsed),
                append_user_words=f"\n\n[correction, message id {user_row['id']}]: {message}",
                append_source_message_id=user_row["id"],
                set_request_id=request_id,
            )
            if correction_status == 200:
                proposal_row = correction_result
            else:
                proposal_error = correction_result.get("error") if isinstance(correction_result, dict) else str(correction_result)

        brain_row = conn.execute(
            "SELECT * FROM workbench_messages WHERE id = ?", (brain_row_id,)
        ).fetchone()
        return jsonify({
            "duplicate": False,
            "user_message": _message_dict(user_row),
            "brain_message": _message_dict(brain_row),
            "proposal": _proposal_dict(proposal_row) if proposal_row else None,
            "proposal_error": proposal_error,
        })
    finally:
        conn.close()


# ── Action proposal routes ───────────────────────────────────────────────

@workbench_bp.route("/api/workbench/projects/<project_id>/proposals", methods=["GET"])
def list_proposals(project_id: str):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        proj = conn.execute(
            "SELECT id FROM workbench_projects WHERE id = ?", (project_id,)
        ).fetchone()
        if not proj:
            return jsonify({"error": "project not found"}), 404
        rows = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE project_id = ? ORDER BY id DESC",
            (project_id,),
        ).fetchall()
        return jsonify({"proposals": [_proposal_dict(r) for r in rows]})
    finally:
        conn.close()


def _proposal_detail_body(conn, row) -> dict:
    body = {"proposal": _proposal_dict(row)}
    if row["card_factory_card_id"]:
        cfc = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (row["card_factory_card_id"],)
        ).fetchone()
        if cfc:
            ask_rev = conn.execute(
                "SELECT revision FROM card_factory_asks WHERE id = ?", (cfc["ask_id"],)
            ).fetchone()
            body["card"] = _cf_card_dict(cfc, ask_rev["revision"] if ask_rev else None)
    if row["card_runner_run_id"]:
        try:
            body["run"] = _cr_run_status(row["card_runner_run_id"])
        except _CRNotFound:
            body["run"] = None
    return body


@workbench_bp.route("/api/workbench/proposals/<int:proposal_id>", methods=["GET"])
def get_proposal(proposal_id: int):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "proposal not found"}), 404
        return jsonify(_proposal_detail_body(conn, row))
    finally:
        conn.close()


@workbench_bp.route("/api/workbench/proposals/<int:proposal_id>", methods=["PATCH"])
def edit_proposal(proposal_id: int):
    """Eric's conversational correction lands here as a technical PATCH
    (the UI's job is turning "no, do X instead" into these fields — this
    route just applies them). Any actual change bumps `revision` and clears
    any existing approval — a correction must never leave a stale approval
    looking current. user_words (Eric's verbatim original message) is
    never editable here; only the model's structured interpretation is."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    if "kind" in data and data["kind"] not in PROPOSAL_KINDS:
        return jsonify({"error": f"kind must be one of {PROPOSAL_KINDS}"}), 400
    for f in ("permitted_files", "permitted_commands"):
        if f in data and (not isinstance(data[f], list) or not all(isinstance(x, str) for x in data[f])):
            return jsonify({"error": f"{f} must be a list of strings"}), 400

    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "proposal not found"}), 404

        updates = {f: data[f] for f in PROPOSAL_EDITABLE_FIELDS if f in data}
        status, result = _apply_proposal_correction(conn, row, updates)
        if status != 200:
            # The linked ask rejected this correction (e.g. success_criteria
            # over MAX_DONE_WHEN_CHARS) — nothing was written, not even the
            # proposal's own fields/revision. Propagate the honest failure
            # rather than returning 200 with a partially-applied correction.
            return jsonify(result), status
        return jsonify({"proposal": _proposal_dict(result)})
    finally:
        conn.close()


@workbench_bp.route("/api/workbench/proposals/<int:proposal_id>/confirm-direction", methods=["POST"])
def confirm_direction(proposal_id: int):
    """"After direction is confirmed, reuse the existing bounded generator
    and gate." Creates (first time) or syncs (subsequent times) a
    card_factory_asks row from this proposal's verbatim user_words / model
    success_criteria (never inserted into the KB as if it were Eric's own
    words — done_when_verbatim=False), sends kind/outcome/action/
    boundaries/unresolved_decisions to the generator as clearly-labeled
    extra context on top of that, then calls the same generate+gate
    boundary card_factory_app.py's own route uses. Records the exact
    proposal revision this card was confirmed against
    (`confirmed_revision`) — approve_proposal requires the proposal still
    be at that revision, so ANY material correction after this point
    invalidates the binding, not just ones that happen to touch
    success_criteria. A draft or PASS verdict from this is never itself
    execution authorization — see approve_proposal below."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    request_id = (data.get("request_id") or "").strip()
    if not request_id:
        return jsonify({"error": "request_id required"}), 400

    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "proposal not found"}), 404
        proj = conn.execute(
            "SELECT name FROM workbench_projects WHERE id = ?", (row["project_id"],)
        ).fetchone()
        project_name = proj["name"] if proj else row["project_id"]
        ask_id = row["card_factory_ask_id"]
        revision_at_start = row["revision"]
        extra_context = _proposal_fields_block(row)
    finally:
        conn.close()

    if ask_id is None:
        status, body = submit_ask_core(
            project_name, row["user_words"], row["success_criteria"] or "",
            done_when_verbatim=False,
        )
        if status != 201:
            return jsonify(body), status
        ask_id = body["ask"]["id"]
        conn = _db()
        try:
            conn.execute(
                "UPDATE workbench_action_proposals SET card_factory_ask_id = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (ask_id, proposal_id),
            )
            conn.commit()
        finally:
            conn.close()
    else:
        # Idempotent sync: edit_ask_core only bumps the ask's revision (and
        # thus stales any already-generated card) when the wording actually
        # differs from what's already stored — a plain retry changes
        # nothing. This remains a secondary defense; the primary guard
        # against a stale approval is confirmed_revision, set below.
        status, body = edit_ask_core(
            ask_id, ask_text=row["user_words"], done_when_text=row["success_criteria"] or "",
            done_when_verbatim=False,
        )
        if status != 200:
            return jsonify(body), status

    gen_status, gen_body = generate_card_core(ask_id, request_id, extra_generator_context=extra_context)
    if gen_status not in (200, 201):
        return jsonify(gen_body), gen_status

    card_id = gen_body["card"]["id"]
    conn = _db()
    try:
        fresh = conn.execute(
            "SELECT revision FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if fresh is None or fresh["revision"] != revision_at_start:
            # The proposal was corrected while generation was in flight —
            # the card that just came back describes wording that is no
            # longer current. Discard the link (the card_factory_cards row
            # itself still exists, just never linked here) rather than
            # binding the proposal to a result that no longer matches it.
            return jsonify({
                "error": "proposal changed during generation; result discarded — "
                         "confirm direction again against the current wording"
            }), 409
        conn.execute(
            "UPDATE workbench_action_proposals SET card_factory_card_id = ?, "
            "confirmed_revision = ?, updated_at = datetime('now') WHERE id = ?",
            (card_id, revision_at_start, proposal_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
    finally:
        conn.close()
    return jsonify({"proposal": _proposal_dict(row), **gen_body}), gen_status


@workbench_bp.route("/api/workbench/proposals/<int:proposal_id>/approve", methods=["POST"])
def approve_proposal(proposal_id: int):
    """Eric's explicit execution approval. Binds the exact action/card
    revision, target, model, scope and limits by calling card_runner.
    dispatch() directly — reusing its own database validation (current
    revision, PASS verdict, matching ask revision, matching content) and
    request_id dedup unchanged. A confirmed direction / PASS card is never
    by itself treated as this approval; this is a separate, explicit call.

    Requires `expected_proposal_revision` (the caller's own belief about
    which revision it is approving — protects against a stale client, not
    just a stale server) and independently requires the server's own
    `revision == confirmed_revision` (protects against ANY material
    correction landing after confirm-direction last ran, regardless of
    which field changed — the gap an independent review found: only
    success_criteria edits used to reach the linked ask/card at all,
    so an action- or boundary-only correction left the original card
    fully dispatchable). Also refuses while the proposal still carries
    unresolved_decisions — drafting/confirming against open questions is
    fine, executing is not."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    expected_proposal_revision = data.get("expected_proposal_revision")
    if expected_proposal_revision is None:
        return jsonify({
            "error": "expected_proposal_revision is required: approval must be bound to "
                     "the exact proposal revision it was requested against"
        }), 400

    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "proposal not found"}), 404
        if not row["card_factory_card_id"]:
            return jsonify({
                "error": "no generated card linked to this proposal yet — confirm direction first"
            }), 409
        if row["unresolved_decisions"]:
            return jsonify({
                "error": f"cannot approve while unresolved decisions remain: {row['unresolved_decisions']}"
            }), 409
        if row["revision"] != expected_proposal_revision:
            return jsonify({
                "error": f"stale proposal revision: approval was requested against revision "
                         f"{expected_proposal_revision}, the proposal is now at revision "
                         f"{row['revision']}"
            }), 409
        if row["confirmed_revision"] != row["revision"]:
            return jsonify({
                "error": "proposal has been corrected since direction was last confirmed "
                         f"(confirmed at revision {row['confirmed_revision']}, now at revision "
                         f"{row['revision']}) — confirm direction again before approving"
            }), 409
        card_factory_card_id = row["card_factory_card_id"]
    finally:
        conn.close()

    try:
        run_row, duplicate = _cr_dispatch(
            card_factory_card_id=card_factory_card_id,
            mode=data.get("mode", "implement"),
            target=data.get("target"),
            request_id=data.get("request_id"),
            expected_card_fingerprint=data.get("expected_card_fingerprint"),
            authorized_by=data.get("authorized_by"),
            review_of_run_id=data.get("review_of_run_id"),
            model=data.get("model"),
            wall_clock_timeout_seconds=data.get(
                "wall_clock_timeout_seconds", _CR_DEFAULT_TIMEOUT_SECONDS
            ),
            max_turns=data.get("max_turns"),
            max_turns_ack_observation_only=bool(data.get("max_turns_ack_observation_only")),
            budget_usd=data.get("budget_usd"),
            accept_time_only_control=bool(data.get("accept_time_only_control")),
            permitted_files=data.get("permitted_files"),
            permitted_commands=data.get("permitted_commands"),
        )
    except (_CRRevisionMismatch, _CRRunnerBusy) as e:
        return jsonify({"error": str(e)}), 409
    except _CRRunnerError as e:
        return jsonify({"error": str(e)}), 400

    if duplicate and run_row["card_factory_card_id"] != card_factory_card_id:
        # This request_id was already used for a different card — attaching
        # it here would silently mislink a prior/unrelated run to a
        # proposal that has since changed. Never attach; the caller needs a
        # new request_id.
        return jsonify({
            "error": "request_id was already used to dispatch a different card — the "
                     "proposal has since changed; use a new request_id"
        }), 409

    conn = _db()
    try:
        conn.execute(
            "UPDATE workbench_action_proposals SET status = 'approved', "
            "approved_at = datetime('now'), approved_by = ?, approved_fingerprint = ?, "
            "card_runner_run_id = ?, updated_at = datetime('now') WHERE id = ?",
            (data.get("authorized_by"), data.get("expected_card_fingerprint"),
             run_row["id"], proposal_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
        ).fetchone()
    finally:
        conn.close()
    return jsonify({
        "proposal": _proposal_dict(row), "run": run_row, "duplicate": duplicate,
    }), (200 if duplicate else 201)
