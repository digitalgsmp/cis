import json
import logging
import sqlite3
import urllib.request
from datetime import datetime
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

reconciliation_bp = Blueprint('reconciliation', __name__)

DB_PATH = "/mnt/projects/cis/runtime/db/cis_memory.db"


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


def _call_gateway(gateway_url, model, api_key, messages, max_tokens=1000, timeout=120):
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


@reconciliation_bp.route('/api/reconciliation/reconcile', methods=['POST'])
def reconcile():
    """Reconcile deliberation agents + external reviews into consensus.

    R1 = reasoning input. V4-Pro = analysis/critique + synthesis caller.
    Claude/ChatGPT = optional external review input.
    Prime and Qwen are excluded.
    """
    data = request.json or {}
    thread_id = data.get('thread_id')
    batch_id = data.get('batch_id')

    if not thread_id or not batch_id:
        return jsonify({'error': 'thread_id and batch_id are required'}), 400

    # ── Fetch deliberation responses ──────────────────────────────────
    conn = get_db()
    messages = conn.execute(
        """SELECT agent_name, role, content FROM advisor_messages
           WHERE thread_id = ? AND batch_id = ?
           ORDER BY message_index, created_at""",
        (thread_id, batch_id)
    ).fetchall()

    if not messages:
        conn.close()
        return jsonify({'error': 'No messages found for this batch'}), 404

    user_msg = None
    responses = {}
    for m in messages:
        m = dict(m)
        if m['role'] == 'user':
            if user_msg is None:
                user_msg = m['content']
        elif m['role'] == 'assistant':
            if m['agent_name'] in ('hermes-r1', 'hermes-v4pro'):
                responses[m['agent_name']] = m['content']

    if not user_msg:
        conn.close()
        return jsonify({'error': 'No user message found in batch'}), 400

    if not responses:
        conn.close()
        return jsonify({'error': 'No R1 or V4-Pro responses found for this batch'}), 400

    # ── Fetch optional external reviews (thread-level, not batch-level) ──
    ext_rows = conn.execute(
        """SELECT id, source, response_text, recommendation_summary,
                  risks, proposed_next_action, verdict
           FROM advisor_external_reviews
           WHERE thread_id = ? AND status IN ('captured', 'reviewed')
           ORDER BY created_at ASC""",
        (thread_id,)
    ).fetchall()
    conn.close()

    external_reviews = [dict(r) for r in ext_rows]
    ext_ids = [r['id'] for r in external_reviews] if external_reviews else None

    # ── Build synthesis prompt ────────────────────────────────────────
    r1_text = responses.get('hermes-r1', '(not provided)')
    v4pro_text = responses.get('hermes-v4pro', '(not provided)')

    prompt = (
        "RECONCILE DELIBERATION RESPONSES.\n\n"
        f"USER QUESTION: {user_msg}\n\n"
        f"--- R1 (REASONING) ---\n{r1_text}\n\n"
        f"--- V4-PRO (ANALYSIS) ---\n{v4pro_text}\n\n"
    )

    if external_reviews:
        prompt += "--- EXTERNAL REVIEWS ---\n"
        for r in external_reviews:
            summary = r.get('recommendation_summary') or r.get('response_text', '')[:300]
            prompt += f"\n[{r['source'].upper()} — verdict: {r.get('verdict','unclear')}]\n{summary}\n"
            if r.get('risks'):
                prompt += f"Risks: {r['risks']}\n"
            if r.get('proposed_next_action'):
                prompt += f"Next action: {r['proposed_next_action']}\n"
        prompt += "\n"

    prompt += (
        "INSTRUCTIONS: Produce a reconciliation in exactly this JSON format:\n"
        "{\n"
        '  "divergence_map": {\n'
        '    "topic": "the core question being decided",\n'
        '    "r1": "R1 position summary or null",\n'
        '    "v4pro": "V4-Pro position summary or null",\n'
        '    "claude": "Claude review summary or null",\n'
        '    "chatgpt": "ChatGPT review summary or null"\n'
        '  },\n'
        '  "confidence": "high|medium|low",\n'
        '  "consensus": "brief statement of agreement, or none",\n'
        '  "unresolved": ["point 1", "point 2"],\n'
        '  "next_action": "single recommended next step for Eric to approve"\n'
        "}\n\n"
        "Return ONLY the JSON object, no other text."
    )

    # ── Call V4-Pro as synthesis caller ───────────────────────────────
    v4pro = get_agent('hermes-v4pro')
    if not v4pro:
        return jsonify({'error': 'V4-Pro agent not found or inactive'}), 500

    v4pro_key = read_api_key(v4pro['env_path'])
    if not v4pro_key:
        return jsonify({'error': 'API_SERVER_KEY not found for V4-Pro'}), 500

    try:
        raw = _call_gateway(
            v4pro['gateway_url'], v4pro['model'], v4pro_key,
            [{"role": "user", "content": prompt}],
            max_tokens=2000
        )
    except Exception as e:
        return jsonify({'error': f'Reconciliation call failed: {str(e)}'}), 502

    # ── Parse JSON response ───────────────────────────────────────────
    try:
        raw = raw.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            raw = raw.strip()
        if raw.lower().startswith('json'):
            raw = raw[4:].strip()
        reconciliation = json.loads(raw)
    except json.JSONDecodeError:
        reconciliation = {
            "divergence_map": {
                "topic": "see raw output",
                "r1": None,
                "v4pro": None,
                "claude": None,
                "chatgpt": None
            },
            "confidence": "low",
            "consensus": "none",
            "unresolved": ["V4-Pro did not return valid JSON"],
            "next_action": "Retry reconciliation or review raw output",
            "_raw": raw[:500]
        }

    # ── Build human-readable synthesis ─────────────────────────────────
    dm = reconciliation.get('divergence_map', {})
    synthesis = (
        f"Reconciliation complete.\n\n"
        f"Confidence: {reconciliation.get('confidence', 'unknown')}\n"
    )
    consensus = reconciliation.get('consensus', '')
    if consensus and consensus != 'none':
        synthesis += f"\nConsensus: {consensus}\n"
    synthesis += "\nPositions:\n"
    for key, label in [('r1', 'R1'), ('v4pro', 'V4-Pro'), ('claude', 'Claude'), ('chatgpt', 'ChatGPT')]:
        val = dm.get(key)
        if val:
            synthesis += f"  {label}: {val[:200]}\n"
    unresolved = reconciliation.get('unresolved', [])
    if unresolved:
        synthesis += f"\nUnresolved: {', '.join(unresolved)}\n"
    synthesis += f"\nNext action: {reconciliation.get('next_action', 'none')}"
    if external_reviews:
        synthesis += f"\n\nExternal reviews included: {len(external_reviews)}"

    # ── Save reconciliation + mark reviews in one transaction ──────────
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO advisor_reconciliations
               (thread_id, batch_id, agent_name, model, synthesis_content,
                reconciliation_json, external_review_ids)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (thread_id, batch_id, 'hermes-v4pro', v4pro['model'],
             synthesis, json.dumps(reconciliation),
             json.dumps(ext_ids) if ext_ids else None)
        )
        # Mark included reviews as reconciled
        if ext_ids:
            placeholders = ','.join('?' * len(ext_ids))
            conn.execute(
                f"UPDATE advisor_external_reviews SET status = 'reconciled' WHERE id IN ({placeholders})",
                ext_ids
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Save failed: {str(e)}'}), 500
    conn.close()

    return jsonify({
        'ok': True,
        'batch_id': batch_id,
        'synthesis_content': synthesis,
        'reconciliation_json': reconciliation,
        'external_reviews_included': len(external_reviews)
    })
