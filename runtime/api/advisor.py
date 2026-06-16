import json
import logging
import os
import sqlite3
import urllib.request
import requests
import http.client
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, Response, stream_with_context

# ALLOV1-BE-001: Lifecycle observability imports
from api.orchestration import (
    generate_proposal_id, get_current_state, transition_state,
    create_dispatch, update_dispatch_inflight, complete_dispatch,
    fail_dispatch, abort_dispatch, freeze_directive,
    validate_directive_hash, LifecycleStateError,
    LifecycleTransitionError, DirectiveHashMismatchError,
    UnauthorizedDispatchError, AuthFailureError
)
import hashlib

logger = logging.getLogger(__name__)

advisor_bp = Blueprint('advisor', __name__)

DB_PATH = "/mnt/projects/cis/runtime/db/cis_memory.db"
SPINE_DB_PATH = "/mnt/projects/cis/data/cis_memory.db"  # CIS spine

# Agents that participate in deliberation (parallel mode, reconciliation).
# Prime is fast chat. Qwen is execution worker. Neither deliberates.
DELIBERATION_AGENTS = ('hermes-r1', 'hermes-v4pro')

# ── AdvisorChat Input Router v0.1 ────────────────────────────────────────

RESEARCH_SIGNALS = [
    "current", "latest", "recent", "today", "find", "search", "verify",
    "evidence", "source", "fact", "news", "check if", "is there", "who is",
    "what happened", "confirm", "look up", "real-time", "still"
]
DRAFTER_SIGNALS = [
    "design", "plan", "propose", "implement", "build", "architecture",
    "draft", "directive", "how should", "create", "structure", "approach",
    "strategy", "schema", "spec", "define", "write a", "outline", "pipeline"
]
REVIEWER_SIGNALS = [
    "critique", "review", "risk", "flaw", "adversarial", "validate",
    "challenge", "what's wrong", "missing", "weak", "counterargument",
    "devil's advocate", "push back", "check this", "tear apart", "poke holes"
]
# Tier 7: Archive retrieval signals — queries for Eric's own prior words/decisions
ARCHIVE_RETRIEVAL_SIGNALS = [
    "what did i say", "what did i decide", "where did i", "find where i",
    "search my sessions", "scan my archive", "recover my", "my own words",
    "my prior", "my previous", "what i wrote", "from my notes",
    "from my writing", "from my transcripts", "in my sessions",
    "use my archive", "my stated logic", "how i described"
]
ROUTER_AGENT_MAP = {
    "fast":           {"agent": "hermes-prime",  "port": 8800},
    "v4_drafter":     {"agent": "hermes-v4pro",  "port": 8645},
    "v4_reviewer":    {"agent": "hermes-r1",     "port": 8643},
    "v4_implementer": {"agent": "hermes-v4impl", "port": 8646},
    "qwen":           {"agent": "hermes-qwen",   "port": 8644},
}
# Tier 7: Blockers for routes that depend on future tiers
ROUTER_BLOCKERS = {
    "ARCHIVE_REQUIREMENTS_DISCOVERY": "BLOCKED_ON_ARCHIVE_INDEX",
    "EXTERNAL_RESEARCH": "BLOCKED_ON_WEB_RESEARCH_CONFIG",
}
ROUTER_NEXT_ACTION = {
    "fast":           "Evidence returned — continue to V4 Drafter",
    "v4_drafter":     "Send to V4 Reviewer for adversarial critique",
    "v4_reviewer":    "Incorporate critique, then issue FINAL_DIRECTIVE for V4 Implementer",
    "v4_implementer": "Review files changed, tests run, pass/fail evidence",
    "qwen":           "Review VERDICT / ACTION / EVIDENCE output",
    "blocked":        "Input must start with JUDGE_REQUEST to reach Qwen",
    "multihop":       "Research preflight complete — auto-forwarding to V4 Drafter",
}


def _score_signals(text, signals):
    t = text.lower()
    return [s for s in signals if s in t]


def classify_route(message, override=None):
    import uuid
    text = message.strip()
    mid  = str(uuid.uuid4())

    def _result(route, confidence, signals=None, multihop=False,
                qwen_blocked=False, qwen_block_reason=None, reason=""):
        key = "multihop" if multihop else route
        r = {
            "message_id":            mid,
            "route":                 route,
            "agent":                 ROUTER_AGENT_MAP.get(route, {}).get("agent"),
            "port":                  ROUTER_AGENT_MAP.get(route, {}).get("port"),
            "confidence":            confidence,
            "signals_matched":       signals or [],
            "reason":                reason,
            "multihop":              multihop,
            "qwen_blocked":          qwen_blocked,
            "next_suggested_action": ROUTER_NEXT_ACTION.get(key, ""),
        }
        if qwen_block_reason:
            r["qwen_block_reason"] = qwen_block_reason
        return r

    # Pass 0: Archive retrieval — queries for Eric's own prior words/decisions (Tier 7)
    archive_signals = _score_signals(text, ARCHIVE_RETRIEVAL_SIGNALS)
    if archive_signals:
        return _result("ARCHIVE_REQUIREMENTS_DISCOVERY", "high" if len(archive_signals) >= 2 else "medium",
                       signals=archive_signals,
                       reason=f"Archive retrieval intent detected — signals: {archive_signals}")

    # Pass 1a: FINAL_DIRECTIVE — V4 Implementer
    if text.startswith("FINAL_DIRECTIVE"):
        return _result("v4_implementer", "deterministic",
                       reason="Implementation directive — "
                              "NeMo preflight + V4 Implementer direct on 8646")

    # Pass 1b: JUDGE_REQUEST — Qwen
    if text.startswith("JUDGE_REQUEST"):
        return _result("qwen", "deterministic",
                       reason="Qwen gate: JUDGE_REQUEST detected")

    # Pass 2: Qwen override rejected when format not met
    if override == "qwen":
        return _result("blocked", "deterministic", qwen_blocked=True,
                       qwen_block_reason="Must start with JUDGE_REQUEST",
                       reason="Qwen gate: override rejected — "
                              "input must start with JUDGE_REQUEST")

    # Pass 3: Non-blocked manual override
    if override and override in ROUTER_AGENT_MAP:
        return _result(override, "override",
                       reason=f"Manual override to {override}")

    # Pass 4: Reviewer signals
    rv = _score_signals(text, REVIEWER_SIGNALS)
    if rv:
        return _result("v4_reviewer", "high" if len(rv) >= 2 else "medium", rv,
                       reason=f"Adversarial/critique intent detected — "
                              f"signals: [{', '.join(rv[:4])}]")

    rs = _score_signals(text, RESEARCH_SIGNALS)
    dr = _score_signals(text, DRAFTER_SIGNALS)

    # Pass 5: Research only
    if rs and not dr:
        return _result("fast", "high" if len(rs) >= 2 else "medium", rs,
                       reason=f"Current facts / evidence gathering detected — "
                              f"signals: [{', '.join(rs[:4])}]")

    # Pass 6: Research + Drafter multi-hop
    if rs and dr:
        return _result("fast", "high", rs + dr, multihop=True,
                       reason="Research preflight before drafting — "
                              "evidence will be injected into V4 Drafter")

    # Pass 7: Drafter signals
    if dr:
        return _result("v4_drafter", "high" if len(dr) >= 2 else "medium", dr,
                       reason=f"Architecture/proposal intent detected — "
                              f"signals: [{', '.join(dr[:4])}]")

    # Pass 8: Ambiguous fallback
    return _result("v4_drafter", "low",
                   reason="No clear signal — defaulted to V4 Drafter")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_agent(name):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM agent_instances WHERE name = ? AND active = 1", (name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def read_api_key(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith("API_SERVER_KEY="):
                return line.split("=", 1)[1].strip()
    return None


def get_thread_history(thread_id):
    """Return prior messages for a thread as OpenAI-format list.

    Queries advisor_messages ordered by message_index, skipping the
    last (most recent) entry (the one we're about to send). Returns
    at most the last 20 messages.
    """
    conn = get_db()
    rows = conn.execute(
        """SELECT role, content FROM advisor_messages
           WHERE thread_id = ?
           ORDER BY message_index, created_at""",
        (thread_id,)
    ).fetchall()
    conn.close()

    messages = [{"role": r["role"], "content": r["content"]} for r in rows]

    # Exclude the most recent message (the one we're about to send)
    if messages:
        messages.pop()

    # Keep only the last 20 to avoid context blowout
    if len(messages) > 20:
        messages = messages[-20:]

    return messages


def _call_gateway(gateway_url, model, api_key, messages, max_tokens=1000, timeout=120):
    """Call an agent gateway and return the assistant's reply text."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }).encode()

    req = urllib.request.Request(
        f"{gateway_url}/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read())
        return body["choices"][0]["message"]["content"]


# ── Gate 7A: V4-Pro Preflight Evidence Injection ───────────────────────

NEMO_PREFLIGHT_URL = "http://127.0.0.1:8800/v1/chat/completions"

# Role system prompts for V4-Pro agents
V4PRO_R1_ROLE = (
    "You are V4-Pro R1, Proposal Author and Directive Drafter. "
    "Your role is to draft structured proposals. "
    "You cannot claim execution or completion — execution belongs to Qwen Worker. "
    "Every response must include:\n"
    "OBJECTIVE:\n"
    "PROPOSED APPROACH:\n"
    "RISKS/UNKNOWNS:\n"
    "VERIFICATION PLAN:\n"
    "STOP CONDITION:"
)

V4PRO_R2_CRITIC_ROLE = (
    "You are V4-Pro R2/Critic, Adversarial Reviewer. "
    "Your role is to challenge proposals and identify missing evidence. "
    "You do not execute — Qwen Worker executes after reconciliation. "
    "Every response must include:\n"
    "OBJECTION/CONCERN:\n"
    "EVIDENCE OR MISSING EVIDENCE:\n"
    "RISK:\n"
    "RECOMMENDED CHANGE:\n"
    "READY FOR EXECUTION (yes/no):"
)


def run_fast_preflight(user_content):
    """Send a prompt to NeMo/Fast on port 8800 for evidence preflight.

    Returns the full NeMo response text, or None on failure.
    """
    try:
        payload = json.dumps({
            "model": "deepseek-v4-flash",
            "messages": [{"role": "user", "content": user_content}],
            "max_tokens": 500,
        }).encode()

        req = urllib.request.Request(
            NEMO_PREFLIGHT_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read())
            return body["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Fast preflight failed: %s", e)
        return None


def _call_gateway_with_reasoning(gateway_url, model, api_key, messages,
                                 max_tokens=2000, timeout=180):
    """Call a V4-Pro agent gateway and return content + reasoning metadata.

    Returns dict with keys: content, reasoning_content, reasoning_tokens.
    Unlike _call_gateway(), this preserves DeepSeek V4 reasoning fields.
    """
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        f"{gateway_url}/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read())

    choice = body["choices"][0]
    message = choice.get("message", {})

    result = {
        "content": message.get("content", ""),
        "reasoning_content": message.get("reasoning_content", ""),
        "reasoning_tokens": (
            body.get("usage", {})
            .get("completion_tokens_details", {})
            .get("reasoning_tokens", 0)
        ),
    }
    return result


# ── Gate 7B: Qwen Worker/Judge Gate ─────────────────────────────────────

QWEN_SYSTEM_PROMPT = (
    "You are Qwen Worker/Judge.\n"
    "You do not deliberate.\n"
    "You do not propose architecture.\n"
    "You execute FINAL_DIRECTIVE packets or judge JUDGE_REQUEST packets.\n"
    "You must report:\n"
    "VERDICT: PASS / FAIL / UNCLEAR\n"
    "ACTION TAKEN:\n"
    "EVIDENCE:\n"
    "MISSING PROOF:\n"
    "NEXT REPAIR STEP:"
)


def validate_qwen_input(content):
    """Validate that Qwen input is a proper FINAL_DIRECTIVE or JUDGE_REQUEST.

    Returns (is_valid, block_reason).
    - is_valid=True means the content can be sent to Qwen.
    - is_valid=False means block with block_reason.
    """
    stripped = content.strip()

    if stripped.startswith("FINAL_DIRECTIVE"):
        return True, None

    if stripped.startswith("JUDGE_REQUEST"):
        # Must include required fields
        required = ["CLAIMED RESULT", "APPROVED DIRECTIVE", "FILES CLAIMED CHANGED",
                    "COMMANDS CLAIMED RUN"]
        missing = [f for f in required if f not in stripped]
        if missing:
            return False, (
                "JUDGE_REQUEST_MALFORMED\n\n"
                "JUDGE_REQUEST requires these fields:\n"
                "  CLAIMED RESULT:\n"
                "  APPROVED DIRECTIVE:\n"
                "  FILES CLAIMED CHANGED:\n"
                "  COMMANDS CLAIMED RUN:\n"
                "  TERMINAL OUTPUT / VERIFICATION EVIDENCE:\n"
                "  KNOWN UNRESOLVED ITEMS:\n\n"
                f"Missing: {', '.join(missing)}"
            )
        return True, None

    return False, (
        "QWEN_GATE_BLOCKED\n\n"
        "Qwen Worker/Judge only accepts FINAL_DIRECTIVE or JUDGE_REQUEST packets.\n"
        "This prompt was blocked by the Qwen gate. It must be:\n"
        "- A reconciled FINAL_DIRECTIVE from the reconciliation pipeline, or\n"
        "- A JUDGE_REQUEST for post-execution verification.\n\n"
        "Casual chat, proposal drafting, unresolved debate, and unreconciled "
        "instructions must go through V4-Pro R1/R2 deliberation first."
    )


def _call_qwen(agent, api_key, messages, max_tokens=2000, timeout=180):
    """Call Qwen gateway and return content."""
    payload = json.dumps({
        "model": agent['model'],
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        f"{agent['gateway_url']}/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.loads(r.read())
        return body["choices"][0]["message"]["content"]


def _save_message(conn, thread_id, agent_name, role, model, content, batch_id=None):
    """Insert a message into advisor_messages and return the new message_index."""
    cur = conn.execute(
        """INSERT INTO advisor_messages
           (thread_id, agent_name, role, model, content, batch_id, message_index, created_at)
           VALUES (?,?,?,?,?,?,
               (SELECT COALESCE(MAX(message_index),0)+1 FROM advisor_messages WHERE thread_id=?),
               ?)""",
        (thread_id, agent_name, role, model, content, batch_id, thread_id, datetime.utcnow().isoformat())
    )
    return cur.lastrowid


# ──────────────────────────────────────────────────────────────────────
#  ALLOV1-BE-001: Authorization enforcement functions
# ──────────────────────────────────────────────────────────────────────

def assert_authorized_dispatch(source_actor, target_port,
                                proposal_id, action_type, db):
    """
    Enforce Rule 5 (corrected per v1.1):
    Dispatch is permitted only when:
      (a) source_actor = 'eric', or
      (b) source_actor = 'orchestrator' AND the current lifecycle
          state is one of the allowed automatic orchestration
          transitions defined in Section 5 of the spec.
    Hermes agents may never be source_actor for lateral dispatch.
    Raises UnauthorizedDispatchError on violation.
    """
    if source_actor == 'eric':
        return  # always permitted

    if source_actor == 'orchestrator':
        current_state = get_current_state(proposal_id, db)
        allowed_auto_states = {
            'RESEARCH_HANDOFF',
            'REVISE_REQUESTED',
            'ROUTING',
            'EXECUTION_COMPLETE',
        }
        if current_state in allowed_auto_states:
            return  # allowed automatic orchestration transition
        raise UnauthorizedDispatchError(
            f"Orchestrator dispatch rejected: lifecycle state "
            f"'{current_state}' does not permit automatic lateral "
            f"dispatch. Eric action required."
        )

    # source_actor is a Hermes agent label — always rejected
    raise UnauthorizedDispatchError(
        f"Lateral dispatch from '{source_actor}' is not permitted. "
        f"source_actor must be 'eric' or 'orchestrator'."
    )


def assert_implementer_authorized(proposal_id,
                                   directive_text, db):
    """
    Enforce Rules 2, 3, 4 for V4 Implementer dispatch.
    All three checks required. Raises on first failure.
    """
    # Rule 2: FINAL_DIRECTIVE prefix required
    if not directive_text.strip().startswith('FINAL_DIRECTIVE'):
        raise UnauthorizedDispatchError(
            "Implementer dispatch rejected: payload does not begin "
            "with FINAL_DIRECTIVE prefix."
        )
    # Rule 3: lifecycle state must be DIRECTIVE_READY
    current = get_current_state(proposal_id, db)
    if current != 'DIRECTIVE_READY':
        raise LifecycleStateError(
            f"Implementer dispatch rejected: current lifecycle state "
            f"is '{current}', expected 'DIRECTIVE_READY'."
        )
    # Rule 3: eric_approved must be 1 in most recent row
    row = db.execute(
        """SELECT eric_approved FROM lifecycle_events
           WHERE proposal_id=? ORDER BY id DESC LIMIT 1""",
        (proposal_id,)
    ).fetchone()
    if not row or not row['eric_approved']:
        raise UnauthorizedDispatchError(
            "Implementer dispatch rejected: Eric approval not "
            "recorded in lifecycle_events for this proposal."
        )
    # Rule 4: directive_hash must match frozen hash
    if not validate_directive_hash(proposal_id,
                                    directive_text, db):
        raise DirectiveHashMismatchError(
            "Implementer dispatch rejected: directive text hash "
            "does not match frozen hash in lifecycle_events."
        )


def handle_auth_failure(dispatch_id, error_message,
                         http_status_code, db):
    """
    Section 12: Auth failure stops immediately.
    Logs FAILED. Returns structured error for UI surface.
    No retry. No key search. No fallback.
    """
    fail_dispatch(dispatch_id, http_status_code,
                  error_message, db)
    return {
        "status": "ERROR",
        "error": (f"Dispatch failed: HTTP {http_status_code} "
                  f"— {error_message}"),
        "dispatch_id": dispatch_id,
        "lifecycle_state": "ERROR",
        "retry": False
    }


@advisor_bp.route('/api/advisor/agents', methods=['GET'])
def list_agents():
    conn = get_db()
    rows = conn.execute(
        "SELECT name, role, gateway_url, model, active FROM agent_instances ORDER BY id"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@advisor_bp.route('/api/advisor/threads', methods=['GET', 'POST'])
def threads():
    conn = get_db()
    if request.method == 'POST':
        data = request.json or {}
        cur = conn.execute(
            "INSERT INTO advisor_threads (round_id, title, context_summary) VALUES (?,?,?)",
            (data.get('round_id'), data.get('title', ''), data.get('context_summary', ''))
        )
        conn.commit()
        thread_id = cur.lastrowid
        conn.close()
        return jsonify({'id': thread_id}), 201
    rows = conn.execute(
        "SELECT * FROM advisor_threads ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@advisor_bp.route('/api/advisor/threads/<int:thread_id>/messages', methods=['GET'])
def get_messages(thread_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM advisor_messages WHERE thread_id = ? ORDER BY message_index, created_at",
        (thread_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@advisor_bp.route('/api/advisor/chat', methods=['POST'])
def chat():
    data = request.json or {}
    agent_name = data.get('agent')
    thread_id = data.get('thread_id')
    content = data.get('content', '').strip()

    if not agent_name or not thread_id or not content:
        return jsonify({'error': 'agent, thread_id, and content are required'}), 400

    agent = get_agent(agent_name)
    if not agent:
        return jsonify({'error': f'Agent {agent_name} not found or inactive'}), 404

    api_key = read_api_key(agent['env_path'])
    if not api_key:
        return jsonify({'error': f'API_SERVER_KEY not found for {agent_name}'}), 500

    # Save user message (original content, never the wrapper)
    conn = get_db()
    _save_message(conn, thread_id, agent_name, 'user', agent['model'], content)
    conn.commit()

    # Build message list: thread history + current user message
    messages = get_thread_history(thread_id)

    # ── Gate 7A: Preflight evidence injection for V4-Pro agents ─────────
    is_v4pro = agent_name in ('hermes-v4pro', 'hermes-r1')
    preflight_result = None
    block_reason = None
    evidence_packet = None

    if is_v4pro:
        preflight_result = run_fast_preflight(content)

        if preflight_result:
            # Check for execution block
            if "FAST_EXECUTION_BLOCKED" in preflight_result:
                block_reason = preflight_result
            # Check for evidence (local or web)
            elif ("NATIVE_ACTION_OK" in preflight_result or
                  "WEB_EVIDENCE_OK" in preflight_result):
                evidence_packet = preflight_result

    # ── Block execution claims before calling V4-Pro ────────────────────
    if block_reason:
        conn.close()
        blocked_msg = (
            "FAST_EXECUTION_BLOCKED (via preflight)\n\n"
            "V4-Pro cannot claim execution or completion. "
            "Escalate to Qwen Worker for execution after reconciliation."
        )
        _save_message(
            get_db(), thread_id, agent_name, 'assistant',
            agent['model'], blocked_msg
        )
        return jsonify({
            'agent': agent_name,
            'content': blocked_msg,
            'blocked': True,
        })

    # ── Build message list with role prompt + evidence ──────────────────
    v4pro_messages = list(messages)  # shallow copy for modification

    if is_v4pro:
        # System role prompt
        role_prompt = (
            V4PRO_R1_ROLE if agent_name == 'hermes-v4pro'
            else V4PRO_R2_CRITIC_ROLE
        )
        v4pro_messages.insert(0, {"role": "system", "content": role_prompt})

        # Evidence injection (before the user message)
        if evidence_packet:
            evidence_msg = (
                "VERIFIED_EVIDENCE_PACKET:\n"
                f"{evidence_packet}\n\n"
                "Instruction: Use this evidence for current/local/system "
                "factual claims. Mark anything not supported as unverified."
            )
            v4pro_messages.insert(-1, {"role": "system", "content": evidence_msg})

        # Structured output wrapper on the user message
        if agent_name == 'hermes-v4pro':
            wrapped = (
                f"{content}\n\n"
                f"---\n"
                f"Respond in this structured format:\n\n"
                f"OBJECTIVE:\n[clear objective]\n\n"
                f"PROPOSED APPROACH:\n[your approach]\n\n"
                f"RISKS/UNKNOWNS:\n[risks and unknowns]\n\n"
                f"VERIFICATION PLAN:\n[how to verify]\n\n"
                f"STOP CONDITION:\n[when to stop]"
            )
        else:  # hermes-r1 Critic
            wrapped = (
                f"{content}\n\n"
                f"---\n"
                f"Respond in this structured format:\n\n"
                f"OBJECTION/CONCERN:\n[your challenge]\n\n"
                f"EVIDENCE OR MISSING EVIDENCE:\n[what evidence exists or is missing]\n\n"
                f"RISK:\n[identified risk]\n\n"
                f"RECOMMENDED CHANGE:\n[your recommendation]\n\n"
                f"READY FOR EXECUTION (yes/no):\n[yes or no with brief rationale]"
            )
        v4pro_messages[-1] = {"role": "user", "content": wrapped}

        # ── Call V4-Pro directly (NOT through NeMo) ─────────────────────
        try:
            result = _call_gateway_with_reasoning(
                agent['gateway_url'], agent['model'], api_key,
                v4pro_messages, max_tokens=2000
            )
            reply = result["content"]
            reasoning_content = result["reasoning_content"]
            reasoning_tokens = result["reasoning_tokens"]
        except Exception as e:
            conn.close()
            return jsonify({'error': f'V4-Pro gateway call failed: {str(e)}'}), 502

        # Save assistant message
        _save_message(conn, thread_id, agent_name, 'assistant',
                      agent['model'], reply)
        conn.commit()
        conn.close()

        response = {
            'agent': agent_name,
            'content': reply,
            'reasoning_content': reasoning_content,
            'reasoning_tokens': reasoning_tokens,
            'preflight_evidence': bool(evidence_packet),
        }
        return jsonify(response)

    # ── Gate 7B: Qwen Worker/Judge gate ─────────────────────────────────
    if agent_name == 'hermes-qwen':
        is_valid, block_reason = validate_qwen_input(content)

        if not is_valid:
            conn.close()
            _save_message(
                get_db(), thread_id, agent_name, 'assistant',
                agent['model'], block_reason
            )
            return jsonify({
                'agent': agent_name,
                'content': block_reason,
                'blocked': True,
            })

        # Build Qwen messages: system prompt + directive/judge request
        qwen_messages = [
            {"role": "system", "content": QWEN_SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]

        try:
            reply = _call_qwen(agent, api_key, qwen_messages, max_tokens=2000)
        except Exception as e:
            conn.close()
            return jsonify({'error': f'Qwen gateway call failed: {str(e)}'}), 502

        _save_message(conn, thread_id, agent_name, 'assistant',
                      agent['model'], reply)
        conn.commit()
        conn.close()

        return jsonify({
            'agent': agent_name,
            'content': reply,
        })

    # ── Non-V4-Pro agents: existing behavior ────────────────────────────
    # R1 (legacy path — should not be hit, kept for safety)
    if agent_name == 'hermes-r1':
        wrapped = (
            f"{content}\n\n"
            f"---\n"
            f"Respond in this structured format:\n\n"
            f"CORE JUDGMENT:\n[one paragraph]\n\n"
            f"REASONING:\n[your reasoning]\n\n"
            f"RISKS / CONTRADICTIONS:\n[any contradictions or risks]\n\n"
            f"RECOMMENDED NEXT ACTION:\n[one clear next step]"
        )
        messages.append({"role": "user", "content": wrapped})
    else:
        messages.append({"role": "user", "content": content})

    # Call agent gateway with full history
    try:
        reply = _call_gateway(
            agent['gateway_url'], agent['model'], api_key,
            messages, max_tokens=1000
        )
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Gateway call failed: {str(e)}'}), 502

    # Save assistant message
    _save_message(conn, thread_id, agent_name, 'assistant', agent['model'], reply)
    conn.commit()

    conn.close()

    return jsonify({'agent': agent_name, 'content': reply})


@advisor_bp.route('/api/advisor/chat-stream', methods=['POST'])
def chat_stream():
    """Stream assistant response via SSE. Prime (hermes-prime) only for now."""
    data = request.json or {}
    agent_name = data.get('agent')
    thread_id = data.get('thread_id')
    content = data.get('content', '').strip()

    if not agent_name or not thread_id or not content:
        return jsonify({'error': 'agent, thread_id, and content are required'}), 400

    agent = get_agent(agent_name)
    if not agent:
        return jsonify({'error': f'Agent {agent_name} not found or inactive'}), 404

    api_key = read_api_key(agent['env_path'])
    if not api_key:
        return jsonify({'error': f'API_SERVER_KEY not found for {agent_name}'}), 500

    # Save user message
    conn = get_db()
    _save_message(conn, thread_id, agent_name, 'user', agent['model'], content)
    conn.commit()

    # Build message list: thread history + current user message
    messages = get_thread_history(thread_id)
    messages.append({"role": "user", "content": content})
    conn.close()

    def generate():
        accumulated = ""
        connection = None
        try:
            payload = json.dumps({
                "model": agent['model'],
                "messages": messages,
                "max_tokens": 1000,
                "stream": True
            }).encode()

            # Parse host/port/path from gateway_url
            url = agent['gateway_url']
            if url.startswith("http://"):
                url = url[7:]
            elif url.startswith("https://"):
                url = url[8:]
            host, _, rest = url.partition(":")
            port_str, _, path = rest.partition("/")
            port = int(port_str) if port_str else 80
            path = ("/" + path if path else "") + "/v1/chat/completions"

            connection = http.client.HTTPConnection(host, port, timeout=120)
            connection.request(
                "POST", path,
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            resp = connection.getresponse()

            yield f"data: {json.dumps({'status': 'thinking'})}\n\n"

            for line in resp:
                line = line.decode("utf-8", errors="replace").strip()
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                delta = chunk.get("choices", [{}])[0].get("delta", {})
                text = delta.get("content", "")
                if text:
                    accumulated += text
                    yield f"data: {json.dumps({'delta': text})}\n\n"

        except GeneratorExit:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

        # Save assistant message to DB
        if accumulated:
            try:
                conn2 = get_db()
                _save_message(conn2, thread_id, agent_name, 'assistant', agent['model'], accumulated)
                conn2.commit()
                conn2.close()
            except Exception:
                pass

        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "X-Accel-Buffering": "no",
                        "Connection": "keep-alive",
                    })


@advisor_bp.route('/api/advisor/parallel', methods=['POST'])
def parallel():
    """Send the same prompt to deliberation agents independently.
    Each agent sees identical context. No agent sees another's response.
    Individual failures do not abort sibling calls."""
    import concurrent.futures

    data = request.json or {}
    thread_id = data.get('thread_id')
    content = data.get('content', '').strip()

    if not thread_id or not content:
        return jsonify({'error': 'thread_id and content are required'}), 400

    import uuid
    batch_id = str(uuid.uuid4())

    # Look up deliberation agents only
    agents_config = {}
    for name in DELIBERATION_AGENTS:
        agent = get_agent(name)
        if not agent:
            return jsonify({'error': f'Agent {name} not found or inactive'}), 500
        key = read_api_key(agent['env_path'])
        if not key:
            return jsonify({'error': f'API_SERVER_KEY not found for {name}'}), 500
        agents_config[name] = {'agent': agent, 'key': key}

    # Save user message once with neutral agent name
    conn = get_db()
    _save_message(conn, thread_id, 'parallel', 'user', 'parallel', content, batch_id)
    conn.commit()

    # Build the context snapshot BEFORE any assistant responses exist
    history = get_thread_history(thread_id)
    base_messages = history + [{"role": "user", "content": content}]

    conn.close()

    # Call deliberation agents concurrently from the same frozen snapshot
    def call_one(name):
        cfg = agents_config[name]
        try:
            # ── Gate 7A: Preflight evidence injection ─────────────────
            preflight = run_fast_preflight(content)

            if preflight and "FAST_EXECUTION_BLOCKED" in preflight:
                blocked_msg = (
                    "FAST_EXECUTION_BLOCKED (via preflight)\n\n"
                    "V4-Pro cannot claim execution or completion. "
                    "Escalate to Qwen Worker for execution after reconciliation."
                )
                return {'agent': name, 'content': blocked_msg,
                        'ok': True, 'error': None, 'blocked': True}

            # Build per-agent messages with role prompt + evidence
            agent_msgs = list(base_messages)
            role_prompt = (
                V4PRO_R1_ROLE if name == 'hermes-v4pro'
                else V4PRO_R2_CRITIC_ROLE
            )
            agent_msgs.insert(0, {"role": "system", "content": role_prompt})

            if preflight and ("NATIVE_ACTION_OK" in preflight or
                              "WEB_EVIDENCE_OK" in preflight):
                evidence_msg = (
                    "VERIFIED_EVIDENCE_PACKET:\n"
                    f"{preflight}\n\n"
                    "Instruction: Use this evidence for current/local/system "
                    "factual claims. Mark anything not supported as unverified."
                )
                agent_msgs.insert(-1, {"role": "system", "content": evidence_msg})

            # Structured output wrapper for the last user message
            if name == 'hermes-v4pro':
                wrapped = (
                    f"{agent_msgs[-1]['content']}\n\n"
                    f"---\n"
                    f"Respond in this structured format:\n\n"
                    f"OBJECTIVE:\n[clear objective]\n\n"
                    f"PROPOSED APPROACH:\n[your approach]\n\n"
                    f"RISKS/UNKNOWNS:\n[risks and unknowns]\n\n"
                    f"VERIFICATION PLAN:\n[how to verify]\n\n"
                    f"STOP CONDITION:\n[when to stop]"
                )
            else:
                wrapped = (
                    f"{agent_msgs[-1]['content']}\n\n"
                    f"---\n"
                    f"Respond in this structured format:\n\n"
                    f"OBJECTION/CONCERN:\n[your challenge]\n\n"
                    f"EVIDENCE OR MISSING EVIDENCE:\n[what evidence exists or is missing]\n\n"
                    f"RISK:\n[identified risk]\n\n"
                    f"RECOMMENDED CHANGE:\n[your recommendation]\n\n"
                    f"READY FOR EXECUTION (yes/no):\n[yes or no with brief rationale]"
                )
            agent_msgs[-1] = {"role": "user", "content": wrapped}

            result = _call_gateway_with_reasoning(
                cfg['agent']['gateway_url'],
                cfg['agent']['model'],
                cfg['key'],
                agent_msgs,
                max_tokens=2000
            )
            return {
                'agent': name, 'content': result['content'], 'ok': True,
                'error': None,
                'reasoning_content': result['reasoning_content'],
                'reasoning_tokens': result['reasoning_tokens'],
            }
        except Exception as e:
            return {'agent': name, 'content': None, 'ok': False, 'error': str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(call_one, name): name for name in agents_config}
        results_map = {}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results_map[result['agent']] = result

    # Save responses sequentially (SQLite not concurrency-safe)
    conn = get_db()
    for name in DELIBERATION_AGENTS:
        result = results_map[name]
        if result['ok']:
            agent_model = agents_config[name]['agent']['model']
            _save_message(conn, thread_id, name, 'assistant', agent_model, result['content'], batch_id)
    conn.commit()
    conn.close()

    # Return in consistent order
    results = [results_map[name] for name in DELIBERATION_AGENTS]
    return jsonify({'results': results, 'batch_id': batch_id})


@advisor_bp.route('/api/advisor/execute', methods=['POST'])
def execute_directive():
    """Send approved reconciliation output to Qwen for execution.

    Qwen is execution-only. It receives a clean directive derived from
    the latest reconciliation — not raw thread messages.
    """
    data = request.json or {}
    thread_id = data.get('thread_id')

    if not thread_id:
        return jsonify({'error': 'thread_id is required'}), 400

    # ── Get thread metadata ────────────────────────────────────────────
    conn = get_db()
    thread = conn.execute(
        "SELECT * FROM advisor_threads WHERE id = ?", (thread_id,)
    ).fetchone()
    if not thread:
        conn.close()
        return jsonify({'error': 'Thread not found'}), 404

    # ── Fetch latest reconciliation ────────────────────────────────────
    recon = conn.execute(
        """SELECT * FROM advisor_reconciliations
           WHERE thread_id = ?
           ORDER BY id DESC
           LIMIT 1""",
        (thread_id,)
    ).fetchone()
    conn.close()

    if not recon:
        return jsonify({
            'error': 'No reconciliation found for this thread. Run deliberation and reconcile before executing.',
            'code': 'NO_RECONCILIATION'
        }), 409

    recon = dict(recon)

    # ── Parse reconciliation ───────────────────────────────────────────
    try:
        recon_json = json.loads(recon['reconciliation_json'])
    except (json.JSONDecodeError, TypeError):
        recon_json = {}

    next_action = recon_json.get('next_action', '')
    confidence = recon_json.get('confidence', 'unknown')
    unresolved = recon_json.get('unresolved', [])

    if not next_action or next_action.strip() in ('', '(no next action specified)'):
        return jsonify({
            'error': 'Latest reconciliation does not include an approved next action.',
            'code': 'NO_NEXT_ACTION'
        }), 409

    # ── Build FINAL_DIRECTIVE for Qwen ──────────────────────────────────
    thread_title = thread['title'] or f'Thread {thread_id}'

    # Count external reviews
    try:
        ext_ids = json.loads(recon.get('external_review_ids') or '[]')
        ext_count = len(ext_ids) if isinstance(ext_ids, list) else 0
    except (json.JSONDecodeError, TypeError):
        ext_count = 0

    directive = (
        f"FINAL_DIRECTIVE\n"
        f"Reconciliation ID: {recon['id']}\n"
        f"Thread: {thread_title}\n"
        f"Confidence: {confidence}\n"
    )
    if ext_count:
        directive += f"External reviews: {ext_count}\n"
    directive += (
        f"\n"
        f"--- RECONCILIATION SYNTHESIS ---\n"
        f"{recon['synthesis_content']}\n"
        f"--- END SYNTHESIS ---\n\n"
        f"APPROVED NEXT ACTION:\n{next_action}\n"
    )
    if unresolved:
        directive += f"\nUNRESOLVED ITEMS:\n"
        for item in unresolved:
            directive += f"- {item}\n"
    directive += (
        f"\n"
        f"INSTRUCTIONS:\n"
        f"- Deliberation and reconciliation are complete.\n"
        f"- Execute the approved next action above.\n"
        f"- Write code, run commands, report PASS/FAIL/UNCLEAR with terminal evidence.\n"
        f"- Do not re-debate or re-review.\n"
        f"- If something is uncovered that this directive does not cover, note it and stop.\n"
        f"\n"
        f"EVIDENCE REQUIREMENTS:\n"
        f"- Include terminal output for every command run.\n"
        f"- Include file paths touched or created.\n"
        f"- If evidence is missing, report VERDICT: UNCLEAR with MISSING PROOF.\n"
    )

    # ── Send to Qwen with system prompt ─────────────────────────────────
    qwen = get_agent('hermes-qwen')
    if not qwen:
        return jsonify({'error': 'Qwen agent not found or inactive'}), 500

    qwen_key = read_api_key(qwen['env_path'])
    if not qwen_key:
        return jsonify({'error': 'API_SERVER_KEY not found for Qwen'}), 500

    # Save the directive as a user message
    conn = get_db()
    _save_message(conn, thread_id, 'hermes-qwen', 'user', qwen['model'], directive)
    conn.commit()

    # Call Qwen gateway with system prompt
    try:
        result = _call_qwen(
            qwen, qwen_key,
            [
                {"role": "system", "content": QWEN_SYSTEM_PROMPT},
                {"role": "user", "content": directive},
            ],
            max_tokens=2000
        )
    except Exception as e:
        conn.close()
        return jsonify({'error': f'Qwen gateway call failed: {str(e)}'}), 502

    # Save Qwen's response
    _save_message(conn, thread_id, 'hermes-qwen', 'assistant', qwen['model'], result)
    conn.commit()
    conn.close()

    return jsonify({
        'ok': True,
        'agent': 'hermes-qwen',
        'content': result,
        'reconciliation_id': recon['id'],
        'next_action': next_action,
        'confidence': confidence
    })


# ═══════════════════════════════════════════════════════════════════════════
# AdvisorChat Input Router v0.1 — Backend
# ═══════════════════════════════════════════════════════════════════════════

ROUTING_DDL = [
    """CREATE TABLE IF NOT EXISTS routing_decisions (
        id                        INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id                TEXT NOT NULL,
        thread_id                 TEXT,
        original_message          TEXT NOT NULL,
        selected_route            TEXT NOT NULL,
        selected_agent            TEXT,
        matched_signals           TEXT,
        confidence                TEXT NOT NULL,
        override_used             TEXT,
        multihop                  INTEGER DEFAULT 0,
        qwen_blocked              INTEGER DEFAULT 0,
        preflight_response        TEXT,
        created_at                DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    "CREATE INDEX IF NOT EXISTS idx_rd_thread  ON routing_decisions(thread_id)",
    "CREATE INDEX IF NOT EXISTS idx_rd_route   ON routing_decisions(selected_route)",
    "CREATE INDEX IF NOT EXISTS idx_rd_created ON routing_decisions(created_at)",
]

_routing_table_ensured = False


def _ensure_routing_table():
    global _routing_table_ensured
    if _routing_table_ensured:
        return
    conn = sqlite3.connect(DB_PATH)
    for stmt in ROUTING_DDL:
        conn.execute(stmt)
    conn.commit()
    conn.close()
    _routing_table_ensured = True


def _persist_routing(routing, original_message, thread_id, override,
                     preflight_response=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO routing_decisions
            (message_id, thread_id, original_message, selected_route,
             selected_agent, matched_signals, confidence, override_used,
             multihop, qwen_blocked, preflight_response)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        routing["message_id"], thread_id, original_message,
        routing["route"], routing.get("agent"),
        json.dumps(routing.get("signals_matched", [])),
        routing["confidence"], override or None,
        int(routing.get("multihop", False)),
        int(routing.get("qwen_blocked", False)),
        preflight_response,
    ))
    conn.commit()
    conn.close()


# ── Tier 7: Workflow run creation (spine-native) ─────────────────────────
# DEPRECATED: _create_kanban_card() — Kanban is retired as pipeline transport.
# See session_handoffs/PROPOSAL_RETIRE_KANBAN_SPINE_API.md
#
# def _create_kanban_card(message, routing, thread_id=None):
#     ... (commented out — spine-native path now used)
#
# KEPT for legacy/compatibility: function body preserved below.


def _create_workflow_run(topic, route, agent=None):
    """Create a workflow_runs row and return the run_id.
    Uses the spine as the authoritative work object — no Kanban."""
    import uuid
    run_id = f"run-{uuid.uuid4().hex[:13]}"
    now = datetime.now(timezone.utc).isoformat()
    max_rounds = 3
    conn = sqlite3.connect(SPINE_DB_PATH)
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("""
        INSERT INTO workflow_runs
            (id, topic, route, status, result, requires_eric_review,
             max_rounds, max_consecutive_revisions, rounds_completed, created_at, updated_at)
        VALUES (?, ?, ?, 'PENDING', 'ERROR', 1,
                ?, 3, 0, ?, ?)
    """, (run_id, topic, route, max_rounds, now, now))
    conn.commit()
    conn.close()
    return run_id


# ── Router dispatch helpers ──────────────────────────────────────────────

def _call_routing_fast(message):
    """Call NeMo/Fast (port 8800) and return the response text."""
    text = run_fast_preflight(message)
    return {"content": text} if text else {"content": ""}


def _call_routing_v4pro(message, agent_name, port=None):
    """Call a V4-Pro agent directly and return dict with content + reasoning.

    agent_name: 'hermes-v4pro' (R1 Drafter) or 'hermes-r1' (R2 Reviewer)
    port:       override gateway port (used for V4 Implementer on 8646)
    """
    agent = get_agent(agent_name)
    if not agent:
        raise Exception(f"Agent {agent_name} not found or inactive")
    api_key = read_api_key(agent['env_path'])
    if not api_key:
        raise Exception(f"API_SERVER_KEY not found for {agent_name}")

    gateway_url = f"http://127.0.0.1:{port}" if port else agent['gateway_url']

    # Attach role prompt for deliberation agents
    if agent_name == 'hermes-v4pro':
        role_prompt = V4PRO_R1_ROLE
    elif agent_name == 'hermes-r1':
        role_prompt = V4PRO_R2_CRITIC_ROLE
    else:
        role_prompt = None

    messages = []
    if role_prompt:
        messages.append({"role": "system", "content": role_prompt})
    messages.append({"role": "user", "content": message})

    result = _call_gateway_with_reasoning(
        gateway_url, agent['model'], api_key, messages,
        max_tokens=2000
    )
    return result  # dict: content, reasoning_content, reasoning_tokens


def _call_routing_qwen(message):
    """Call Qwen Worker and return the response text."""
    agent = get_agent('hermes-qwen')
    if not agent:
        raise Exception("Qwen agent not found or inactive")
    api_key = read_api_key(agent['env_path'])
    if not api_key:
        raise Exception("API_SERVER_KEY not found for Qwen")

    messages = [
        {"role": "system", "content": QWEN_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    text = _call_qwen(agent, api_key, messages, max_tokens=2000)
    return {"content": text} if text else {"content": ""}


# ═══════════════════════════════════════════════════════════════════════════
#  ALLOV1-BE-002: Action Handlers
# ═══════════════════════════════════════════════════════════════════════════

def _standard_response(data, db, proposal_id, dispatch_id=None,
                       response_message_id=None, reviewer_message_id=None,
                       directive_hash=None, directive_text=None,
                       eric_approved=1, eric_bypass=0, revision_count=0,
                       verdict=None, critique=None, required_changes=None,
                       action=None, notes=None,
                       target_agent=None, target_endpoint=None):
    """Build the standard lifecycle response shape (Section D)."""
    return {
        "proposal_id": proposal_id,
        "session_id": data.get('session_id', 'unknown'),
        "source_actor": data.get('source_actor', 'eric'),
        "target_agent": target_agent,
        "target_endpoint": target_endpoint,
        "dispatch_id": dispatch_id,
        "lifecycle_state": get_current_state(proposal_id, db),
        "response_message_id": response_message_id,
        "research_message_id": data.get('research_message_id'),
        "reviewer_message_id": reviewer_message_id,
        "directive_hash": directive_hash,
        "directive_text": directive_text,
        "eric_approved": eric_approved,
        "eric_bypass": eric_bypass,
        "revision_count": revision_count,
        "verdict": verdict,
        "critique": critique,
        "required_changes": required_changes,
        "action": action,
        "notes": notes,
    }


def _state_conflict_response(proposal_id, current_state, expected_state, action, source_actor='eric'):
    """Build state conflict 409 response."""
    return {
        "proposal_id": proposal_id,
        "source_actor": source_actor,
        "target_agent": None,
        "target_endpoint": None,
        "lifecycle_state": current_state,
        "expected_state": expected_state,
        "status": "STATE_CONFLICT",
        "error": f"Expected state '{expected_state}', current state is '{current_state}'.",
        "action": action,
    }


def _post_to_agent(agent_name, port, payload, timeout=180):
    """POST payload to a Hermes gateway and return response dict."""
    agent = get_agent(agent_name)
    if not agent:
        raise Exception(f"Agent {agent_name} not found or inactive")
    api_key = read_api_key(agent['env_path'])
    if not api_key:
        raise Exception(f"API_SERVER_KEY not found for {agent_name}")

    gateway_url = f"http://127.0.0.1:{port}"
    messages = [{"role": "user", "content": payload}]

    result = _call_gateway_with_reasoning(
        gateway_url, agent['model'], api_key, messages,
        max_tokens=2000, timeout=timeout
    )
    return result


# ── C1: handle_reviewer_dispatch ───────────────────────────────────────

def handle_reviewer_dispatch(data, db):
    proposal_id = data['proposal_id']
    session_id = data.get('session_id', 'unknown')
    source_actor = data.get('source_actor', 'eric')

    # Step 1: Authorization
    try:
        assert_authorized_dispatch(source_actor, 8643,
                                    proposal_id, 'dispatch', db)
    except UnauthorizedDispatchError:
        current = get_current_state(proposal_id, db)
        return jsonify(_state_conflict_response(
            proposal_id, current, 'DRAFT_READY',
            'reviewer_dispatch')), 409

    # Step 2: State check
    current = get_current_state(proposal_id, db)
    if current != 'DRAFT_READY':
        db.close()
        return jsonify(_state_conflict_response(
            proposal_id, current, 'DRAFT_READY',
            'reviewer_dispatch')), 409

    # Step 3: Transition to REVIEW_PENDING
    try:
        transition_state(proposal_id, session_id,
            'DRAFT_READY', 'REVIEW_PENDING',
            initiated_by='eric', gate_type='human',
            eric_approved=1, db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 409

    # Step 4-5: Create dispatch
    payload = data.get('payload', '')
    dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor='orchestrator',
        target_agent='hermes-r1',
        target_endpoint='http://127.0.0.1:8643',
        lifecycle_state_at='REVIEW_PENDING',
        payload=payload,
        initiated_by='orchestrator',
        eric_approved=1,
        db=db
    )
    update_dispatch_inflight(dispatch_id, db)

    # Step 6: POST to reviewer
    verdict = 'MALFORMED'
    critique = None
    required_changes = None
    response_message_id = None

    try:
        result = _post_to_agent('hermes-r1', 8643, payload)
        response_body = result.get('content', '')
        response_message_id = complete_dispatch(
            dispatch_id, 200, response_body, db)

        # Step 7: Parse verdict from response
        try:
            verdict_json = json.loads(response_body)
            verdict = verdict_json.get('verdict', 'MALFORMED')
            critique = verdict_json.get('critique')
            required_changes = verdict_json.get('required_changes')
            response_message_id = verdict_json.get(
                'reviewer_message_id', response_message_id)
        except (json.JSONDecodeError, TypeError):
            verdict = 'MALFORMED'

    except Exception as e:
        fail_dispatch(dispatch_id, 0, str(e), db)
        db.close()
        return jsonify(handle_auth_failure(
            dispatch_id, str(e), 0, db)), 502

    # Step 9-10: State transitions
    try:
        transition_state(proposal_id, session_id,
            'REVIEW_PENDING', 'REVIEWING',
            initiated_by='orchestrator', gate_type='automatic',
            db=db)
        transition_state(proposal_id, session_id,
            'REVIEWING', 'REVIEW_COMPLETE',
            initiated_by='orchestrator', gate_type='automatic',
            reviewer_message_id=response_message_id,
            db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        logger.warning("reviewer_dispatch state transition failed: %s", e)

    # Step 11: Return
    return jsonify(_standard_response(
        data, db, proposal_id,
        dispatch_id=dispatch_id,
        response_message_id=response_message_id,
        reviewer_message_id=response_message_id,
        verdict=verdict,
        critique=critique,
        required_changes=required_changes,
        action='reviewer_dispatch',
        notes=f"Reviewer verdict: {verdict}",
        target_agent='hermes-r1',
        target_endpoint='http://127.0.0.1:8643'
    )), 200


# ── C2: handle_approve_draft ───────────────────────────────────────────

def handle_approve_draft(data, db):
    proposal_id = data['proposal_id']
    session_id = data.get('session_id', 'unknown')
    eric_bypass = data.get('eric_bypass', 0)

    # Step 1: State check
    current = get_current_state(proposal_id, db)
    if current not in ('REVIEW_COMPLETE', 'DRAFT_READY'):
        db.close()
        return jsonify(_state_conflict_response(
            proposal_id, current,
            'REVIEW_COMPLETE or DRAFT_READY',
            'approve_draft_directive')), 409

    # Step 2: Reviewer evidence check (unless bypass)
    reviewer_message_id = None
    if current == 'REVIEW_COMPLETE' and not eric_bypass:
        row = db.execute(
            """SELECT reviewer_message_id FROM lifecycle_events
               WHERE proposal_id=? AND reviewer_message_id IS NOT NULL
               ORDER BY id DESC LIMIT 1""",
            (proposal_id,)
        ).fetchone()
        reviewer_message_id = row['reviewer_message_id'] if row else None
        if not reviewer_message_id:
            db.close()
            return jsonify({
                "proposal_id": proposal_id,
                "lifecycle_state": current,
                "status": "STATE_CONFLICT",
                "error": "Reviewer evidence required. Set eric_bypass=1 to override.",
                "action": "approve_draft_directive",
            }), 409

    # Step 3-4: State transitions
    try:
        transition_state(proposal_id, session_id,
            current, 'ERIC_APPROVAL_GATE',
            initiated_by='eric', gate_type='human',
            eric_approved=1, eric_bypass=eric_bypass,
            reviewer_message_id=reviewer_message_id,
            db=db)
        transition_state(proposal_id, session_id,
            'ERIC_APPROVAL_GATE', 'DIRECTIVE_DRAFTING',
            initiated_by='eric', gate_type='human',
            eric_approved=1, db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 409

    # Step 5: POST to Drafter
    # Get original proposal text
    proposal_text = data.get('original_proposal', '')
    if not proposal_text:
        row = db.execute(
            """SELECT payload_summary FROM dispatch_log
               WHERE proposal_id=? ORDER BY id DESC LIMIT 1""",
            (proposal_id,)
        ).fetchone()
        if row and row['payload_summary']:
            proposal_text = row['payload_summary']

    drafting_prompt = (
        f"Compose a FINAL_DIRECTIVE block for the following proposal. "
        f"Include clear OBJECTIVE, SCOPE, FILES TO MODIFY, "
        f"VERIFICATION STEPS, and DO NOT boundaries.\n\n"
        f"PROPOSAL:\n{proposal_text}"
    )

    directive_text = None
    directive_hash = None
    dispatch_id = None
    response_message_id = None

    try:
        result = _post_to_agent('hermes-v4pro', 8645, drafting_prompt)
        response_body = result.get('content', '')

        # Step 6: Extract FINAL_DIRECTIVE candidate
        if 'FINAL_DIRECTIVE' in response_body:
            idx = response_body.index('FINAL_DIRECTIVE')
            directive_text = response_body[idx:].strip()
        else:
            directive_text = response_body.strip()

        # Step 7: Freeze directive
        directive_hash = freeze_directive(
            proposal_id, session_id, directive_text, db)

    except Exception as e:
        db.close()
        return jsonify({"error": str(e),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 502

    # Step 8: Return
    return jsonify(_standard_response(
        data, db, proposal_id,
        dispatch_id=dispatch_id,
        response_message_id=response_message_id,
        reviewer_message_id=reviewer_message_id,
        directive_hash=directive_hash,
        directive_text=directive_text,
        eric_bypass=eric_bypass,
        action='approve_draft_directive',
        notes='Directive authored and frozen.',
        target_agent='hermes-v4pro',
        target_endpoint='http://127.0.0.1:8645'
    )), 200


# ── C3: handle_reject_proposal ─────────────────────────────────────────

def handle_reject_proposal(data, db):
    proposal_id = data['proposal_id']
    session_id = data.get('session_id', 'unknown')

    # Step 1: State check
    current = get_current_state(proposal_id, db)
    allowed = {'DRAFT_READY', 'REVIEW_COMPLETE', 'ERIC_APPROVAL_GATE',
               'DIRECTIVE_AUTHORED', 'DIRECTIVE_READY'}
    if current not in allowed:
        db.close()
        return jsonify(_state_conflict_response(
            proposal_id, current,
            'DRAFT_READY, REVIEW_COMPLETE, ERIC_APPROVAL_GATE, '
            'DIRECTIVE_AUTHORED, or DIRECTIVE_READY',
            'reject_proposal')), 409

    # Step 3-4: State transitions
    try:
        transition_state(proposal_id, session_id,
            current, 'REJECTED',
            initiated_by='eric', gate_type='human',
            eric_approved=1, notes='Proposal rejected by Eric.',
            db=db)
        transition_state(proposal_id, session_id,
            'REJECTED', 'IDLE',
            initiated_by='orchestrator', gate_type='automatic',
            db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 409

    return jsonify(_standard_response(
        data, db, proposal_id,
        action='reject_proposal',
        notes='Proposal rejected by Eric.'
    )), 200


# ── C4: handle_confirm_directive ───────────────────────────────────────

def handle_confirm_directive(data, db):
    proposal_id = data['proposal_id']
    session_id = data.get('session_id', 'unknown')
    directive_text = data.get('directive_text', '')
    directive_hash = data.get('directive_hash', '')

    # Step 1: State check
    current = get_current_state(proposal_id, db)
    if current != 'DIRECTIVE_AUTHORED':
        db.close()
        return jsonify(_state_conflict_response(
            proposal_id, current, 'DIRECTIVE_AUTHORED',
            'confirm_directive')), 409

    # Step 2: Hash validation
    if not validate_directive_hash(proposal_id, directive_text, db):
        db.close()
        return jsonify({
            "proposal_id": proposal_id,
            "lifecycle_state": current,
            "status": "STATE_CONFLICT",
            "error": ("Directive hash mismatch. Text may have been "
                      "modified since approval."),
            "action": "confirm_directive",
        }), 409

    # Step 4: Transition
    try:
        transition_state(proposal_id, session_id,
            'DIRECTIVE_AUTHORED', 'DIRECTIVE_READY',
            initiated_by='eric', gate_type='human',
            eric_approved=1, directive_hash=directive_hash,
            db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 409

    return jsonify(_standard_response(
        data, db, proposal_id,
        directive_hash=directive_hash,
        directive_text=directive_text,
        action='confirm_directive',
        notes='Directive confirmed and ready for execution.'
    )), 200


# ── C5: handle_revise_directive ────────────────────────────────────────

def handle_revise_directive(data, db):
    proposal_id = data['proposal_id']
    session_id = data.get('session_id', 'unknown')
    revision_notes = data.get('revision_notes')

    # Step 1: State check
    current = get_current_state(proposal_id, db)
    if current not in ('DIRECTIVE_AUTHORED', 'DIRECTIVE_READY'):
        db.close()
        return jsonify(_state_conflict_response(
            proposal_id, current,
            'DIRECTIVE_AUTHORED or DIRECTIVE_READY',
            'revise_directive')), 409

    # Step 3: Get current revision count
    row = db.execute(
        """SELECT revision_count FROM lifecycle_events
           WHERE proposal_id=? ORDER BY id DESC LIMIT 1""",
        (proposal_id,)
    ).fetchone()
    previous_count = row['revision_count'] if row else 0
    new_count = previous_count + 1

    # Step 4-5: Transition
    try:
        transition_state(proposal_id, session_id,
            current, 'DIRECTIVE_DRAFTING',
            initiated_by='eric', gate_type='human',
            eric_approved=1,
            revision_count=new_count,
            notes=revision_notes,
            db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 409

    return jsonify(_standard_response(
        data, db, proposal_id,
        revision_count=new_count,
        action='revise_directive',
        notes=revision_notes or 'Directive revision requested.'
    )), 200


# ── C6: handle_execute_directive ───────────────────────────────────────

def handle_execute_directive(data, db):
    proposal_id = data['proposal_id']
    session_id = data.get('session_id', 'unknown')
    directive_text = data.get('directive_text', '')
    directive_hash = data.get('directive_hash', '')

    # Step 1: Implementer authorization
    try:
        assert_implementer_authorized(proposal_id, directive_text, db)
    except (UnauthorizedDispatchError, LifecycleStateError,
            DirectiveHashMismatchError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR",
                        "retry": False}), 403

    # Step 2: State check
    current = get_current_state(proposal_id, db)
    if current != 'DIRECTIVE_READY':
        db.close()
        return jsonify(_state_conflict_response(
            proposal_id, current, 'DIRECTIVE_READY',
            'execute_directive')), 409

    # Step 3: Hash validation
    if not validate_directive_hash(proposal_id, directive_text, db):
        db.close()
        return jsonify({
            "proposal_id": proposal_id,
            "lifecycle_state": current,
            "status": "STATE_CONFLICT",
            "error": "Directive hash mismatch.",
            "action": "execute_directive",
        }), 409

    # Step 4: Transition to EXECUTING
    try:
        transition_state(proposal_id, session_id,
            'DIRECTIVE_READY', 'EXECUTING',
            initiated_by='eric', gate_type='human',
            eric_approved=1, db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        db.close()
        return jsonify({"error": str(e),
                        "source_actor": data.get('source_actor', 'eric'),
                        "status": "ERROR",
                        "lifecycle_state": "ERROR"}), 409

    # Step 5-6: Create dispatch
    dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor='orchestrator',
        target_agent='hermes-v4impl',
        target_endpoint='http://127.0.0.1:8646',
        lifecycle_state_at='EXECUTING',
        payload=directive_text,
        initiated_by='orchestrator',
        eric_approved=1,
        directive_hash=directive_hash,
        db=db
    )
    update_dispatch_inflight(dispatch_id, db)

    # Step 7: POST to implementer
    response_message_id = None
    try:
        result = _post_to_agent('hermes-v4impl', 8646, directive_text,
                                timeout=600)
        response_body = result.get('content', '')
        response_message_id = complete_dispatch(
            dispatch_id, 200, response_body, db)
    except Exception as e:
        fail_dispatch(dispatch_id, 0, str(e), db)
        db.close()
        return jsonify(handle_auth_failure(
            dispatch_id, str(e), 0, db)), 502

    # Step 9: Transition to EXECUTION_COMPLETE
    try:
        transition_state(proposal_id, session_id,
            'EXECUTING', 'EXECUTION_COMPLETE',
            initiated_by='orchestrator', gate_type='automatic',
            db=db)
    except (LifecycleStateError, LifecycleTransitionError) as e:
        logger.warning("execute_directive final transition failed: %s", e)

    return jsonify(_standard_response(
        data, db, proposal_id,
        dispatch_id=dispatch_id,
        response_message_id=response_message_id,
        directive_hash=directive_hash,
        directive_text=directive_text,
        action='execute_directive',
        notes='Execution complete. Awaiting verification.',
        target_agent='hermes-v4impl',
        target_endpoint='http://127.0.0.1:8646'
    )), 200


# ── Action dispatch map ────────────────────────────────────────────────

ACTION_HANDLERS = {
    'reviewer_dispatch':       handle_reviewer_dispatch,
    'approve_draft_directive': handle_approve_draft,
    'reject_proposal':         handle_reject_proposal,
    'confirm_directive':       handle_confirm_directive,
    'revise_directive':        handle_revise_directive,
    'execute_directive':       handle_execute_directive,
}


# ── Router endpoint ──────────────────────────────────────────────────────

@advisor_bp.route('/api/advisor/route', methods=['POST'])
def route_message():
    # Auth: X-CIS-API-Key header (same pattern as app.py before_request)
    valid_key = os.environ.get("CIS_API_KEY", "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd")
    provided_key = request.headers.get("X-CIS-API-Key", "")
    if not valid_key or provided_key != valid_key:
        return jsonify({"error": "Unauthorized"}), 401

    _ensure_routing_table()
    data          = request.get_json() or {}

    # ── ALLOV1-BE-002: Action dispatch ────────────────────────────────
    action = data.get('action')
    if action and action in ACTION_HANDLERS:
        db = get_db()
        try:
            handler = ACTION_HANDLERS[action]
            result = handler(data, db)
            db.close()
            return result
        except Exception as e:
            db.close()
            logger.exception("Action handler %s failed", action)
            return jsonify({
                "error": f"Action handler '{action}' failed: {str(e)}",
                "status": "ERROR",
                "lifecycle_state": "ERROR",
                "action": action,
            }), 500
    # ── end action dispatch ──────────────────────────────────────────

    message       = (data.get("message") or "").strip()
    thread_id     = data.get("thread_id")
    override      = data.get("override")
    classify_only = bool(data.get("classify_only", False))

    if not message:
        return jsonify({"error": "message required"}), 400

    # ── ALLOV1-BE-001 enforcement ────────────────────────────────────
    db = get_db()
    proposal_id = data.get('proposal_id') or generate_proposal_id()
    session_id = data.get('session_id', 'unknown')
    source_actor = data.get('source_actor', 'eric')

    routing = classify_route(message, override)
    _persist_routing(routing, message, thread_id, override)

    # Resolve target port from routing decision
    target_port = routing.get('port')
    target_agent_label = routing.get('agent', 'unknown')
    target_endpoint = f"http://127.0.0.1:{target_port}" if target_port else "unknown"

    # Implementer gate (port 8646)
    if target_port == 8646:
        try:
            assert_implementer_authorized(
                proposal_id, message, db)
        except (UnauthorizedDispatchError,
                LifecycleStateError,
                DirectiveHashMismatchError) as e:
            db.close()
            return jsonify({
                "error": str(e),
                "status": "ERROR",
                "lifecycle_state": "ERROR",
                "retry": False
            }), 403

    # Lateral dispatch gate
    try:
        assert_authorized_dispatch(
            source_actor, target_port,
            proposal_id, 'dispatch', db)
    except UnauthorizedDispatchError as e:
        db.close()
        return jsonify({
            "error": str(e),
            "status": "ERROR",
            "lifecycle_state": "ERROR",
            "retry": False
        }), 403
    # ── end enforcement ──────────────────────────────────────────────

    # ── Tier 7: Pipeline/Archive routes create spine workflow runs ───
    # Deterministic fast paths (FINAL_DIRECTIVE, JUDGE_REQUEST) bypass workflow runs.
    # Pipeline routes (draft, review, research, archive) create durable spine records.
    tier7_pipeline_routes = {
        "ARCHIVE_REQUIREMENTS_DISCOVERY", "EXTERNAL_RESEARCH",
        "v4_drafter", "v4_reviewer", "fast", "multihop"
    }
    if routing["route"] in tier7_pipeline_routes or (
        override and override in ROUTER_AGENT_MAP and
        override not in ("v4_implementer", "qwen")
    ):
        run_id = _create_workflow_run(message, routing["route"])
        routing["run_id"] = run_id
        # RETIRED — kanban_card_id retired per ADR-013
        routing["agent_response"] = None
        # Add blocker info if applicable
        blocker = ROUTER_BLOCKERS.get(routing["route"])
        if blocker:
            routing["blocked_by"] = blocker
            routing["next_unlock"] = {
                "BLOCKED_ON_ARCHIVE_INDEX": "Tier 7.5 Archive Import + FTS5 Search",
                "BLOCKED_ON_WEB_RESEARCH_CONFIG": "Tier 7.6 Research Gateway Repair",
            }.get(blocker, "Unknown — check dependency graph")
        _persist_routing(routing, message, thread_id, override,
)
        db.close()
        return jsonify(routing), 200
    # ── end Tier 7 routing ───────────────────────────────────────────

    if classify_only:
        routing["classify_only"] = True
        routing["agent_response"] = None
        db.close()
        return jsonify(routing), 200

    if routing["route"] == "blocked" or routing.get("qwen_blocked"):
        routing["agent_response"] = None
        db.close()
        return jsonify(routing), 200

    agent_response          = None
    preflight_response_text = None
    final_route             = routing["route"]
    dispatch_id             = None
    response_message_id     = None

    # ── Create dispatch record ───────────────────────────────────────
    dispatch_id = create_dispatch(
        proposal_id=proposal_id,
        source_actor=source_actor,
        target_agent=target_agent_label,
        target_endpoint=target_endpoint,
        lifecycle_state_at=get_current_state(proposal_id, db) or 'ROUTING',
        payload=message,
        initiated_by=source_actor,
        eric_approved=1 if source_actor == 'eric' else 0,
        db=db
    )
    update_dispatch_inflight(dispatch_id, db)

    try:
        if routing.get("multihop"):
            preflight_response_text = run_fast_preflight(message)
            injected = (
                "[RESEARCH PREFLIGHT]\n" + (preflight_response_text or "") +
                "\n\n[USER PROMPT]\n" + message
            )
            agent_response = _call_routing_v4pro(injected, 'hermes-v4pro')
            final_route    = "v4_drafter"

        elif routing["route"] == "fast":
            agent_response = _call_routing_fast(message)

        elif routing["route"] == "v4_drafter":
            agent_response = _call_routing_v4pro(message, 'hermes-v4pro')

        elif routing["route"] == "v4_reviewer":
            agent_response = _call_routing_v4pro(message, 'hermes-r1')

        elif routing["route"] == "v4_implementer":
            # NeMo preflight → V4 Implementer direct on 8646
            preflight_response_text = run_fast_preflight(message)
            injected = (
                "[NEMO PREFLIGHT]\n" + (preflight_response_text or "") +
                "\n\n[DIRECTIVE]\n" + message
            ) if preflight_response_text else message
            agent_response = _call_routing_v4pro(
                injected, 'hermes-v4impl', port=8646
            )
            final_route = "v4_implementer"

        elif routing["route"] == "qwen":
            agent_response = _call_routing_qwen(message)

    except requests.exceptions.ConnectionError as e:
        fail_dispatch(dispatch_id, 0, str(e), db)
        db.close()
        return jsonify(handle_auth_failure(
            dispatch_id, str(e), 0, db)), 502

    except Exception as e:
        routing["dispatch_error"] = str(e)
        agent_response = None
        fail_dispatch(dispatch_id, 0, str(e), db)

    else:
        # Complete dispatch on success
        response_body = (agent_response.get('content', '')
                         if isinstance(agent_response, dict)
                         else str(agent_response or ''))
        try:
            response_message_id = complete_dispatch(
                dispatch_id, 200, response_body, db)
        except Exception as e:
            logger.warning("complete_dispatch failed: %s", e)

    routing["agent_response"] = agent_response
    routing["final_route"]    = final_route
    if preflight_response_text:
        routing["preflight_response"] = preflight_response_text

    # ALLOV1-BE-001 response fields
    routing["proposal_id"] = proposal_id
    routing["dispatch_id"] = dispatch_id
    routing["lifecycle_state"] = get_current_state(proposal_id, db)
    routing["response_message_id"] = response_message_id
    routing["research_message_id"] = data.get('research_message_id')
    routing["reviewer_message_id"] = None
    routing["directive_hash"] = None
    routing["eric_approved"] = 1 if source_actor == 'eric' else 0

    db.close()
    return jsonify(routing), 200
