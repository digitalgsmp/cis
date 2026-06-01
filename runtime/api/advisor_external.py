"""api/advisor_external.py — External Claude/ChatGPT review capture."""
import json
import logging
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

advisor_external_bp = Blueprint('advisor_external', __name__)

DB_PATH = "/mnt/projects/cis/runtime/db/cis_memory.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── POST /api/advisor/external-reviews ──────────────────────────────────

@advisor_external_bp.route('/api/advisor/external-reviews', methods=['POST'])
def create_review():
    data = request.json or {}
    thread_id = data.get('thread_id')
    source = data.get('source')
    escalation_prompt = data.get('escalation_prompt', '').strip()
    response_text = data.get('response_text', '').strip()

    if not thread_id or not source or not escalation_prompt or not response_text:
        return jsonify({'error': 'thread_id, source, escalation_prompt, and response_text are required'}), 400

    if source not in ('claude', 'chatgpt', 'other'):
        return jsonify({'error': 'source must be claude, chatgpt, or other'}), 400

    conn = get_db()

    # Verify thread exists
    thread = conn.execute(
        "SELECT id FROM advisor_threads WHERE id = ?", (thread_id,)
    ).fetchone()
    if not thread:
        conn.close()
        return jsonify({'error': 'Thread not found'}), 404

    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        """INSERT INTO advisor_external_reviews
           (thread_id, batch_id, source, source_role, source_model, source_platform,
            escalation_prompt, response_text, recommendation_summary, risks,
            proposed_next_action, verdict, status, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            thread_id,
            data.get('batch_id'),
            source,
            data.get('source_role'),
            data.get('source_model'),
            data.get('source_platform', 'pasted'),
            escalation_prompt,
            response_text,
            data.get('recommendation_summary'),
            data.get('risks'),
            data.get('proposed_next_action'),
            data.get('verdict', 'unclear'),
            data.get('status', 'captured'),
            now,
            now,
        )
    )
    conn.commit()
    review_id = cur.lastrowid

    row = conn.execute(
        "SELECT * FROM advisor_external_reviews WHERE id = ?", (review_id,)
    ).fetchone()
    conn.close()

    return jsonify(dict(row)), 201


# ── GET /api/advisor/external-reviews ───────────────────────────────────

@advisor_external_bp.route('/api/advisor/external-reviews', methods=['GET'])
def list_reviews():
    thread_id = request.args.get('thread_id', type=int)
    if not thread_id:
        return jsonify({'error': 'thread_id query parameter is required'}), 400

    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM advisor_external_reviews
           WHERE thread_id = ? AND status != 'superseded'
           ORDER BY created_at DESC""",
        (thread_id,)
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


# ── GET /api/advisor/external-reviews/<id> ──────────────────────────────

@advisor_external_bp.route('/api/advisor/external-reviews/<int:review_id>', methods=['GET'])
def get_review(review_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM advisor_external_reviews WHERE id = ?", (review_id,)
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Review not found'}), 404

    return jsonify(dict(row))


# ── PATCH /api/advisor/external-reviews/<id> ────────────────────────────

EDITABLE_FIELDS = (
    'recommendation_summary', 'risks', 'proposed_next_action',
    'verdict', 'status', 'response_text', 'source_model', 'source_platform'
)

@advisor_external_bp.route('/api/advisor/external-reviews/<int:review_id>', methods=['PATCH'])
def update_review(review_id):
    data = request.json or {}

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM advisor_external_reviews WHERE id = ?", (review_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Review not found'}), 404

    updates = {}
    for field in EDITABLE_FIELDS:
        if field in data:
            val = data[field]
            if field == 'verdict' and val not in ('approve', 'revise', 'reject', 'unclear'):
                conn.close()
                return jsonify({'error': f'Invalid verdict: {val}'}), 400
            if field == 'status' and val not in ('captured', 'reviewed', 'reconciled', 'superseded'):
                conn.close()
                return jsonify({'error': f'Invalid status: {val}'}), 400
            updates[field] = val

    if not updates:
        conn.close()
        return jsonify(dict(row))

    updates['updated_at'] = datetime.utcnow().isoformat()

    set_clause = ', '.join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [review_id]

    conn.execute(
        f"UPDATE advisor_external_reviews SET {set_clause} WHERE id = ?",
        values
    )
    conn.commit()

    updated = conn.execute(
        "SELECT * FROM advisor_external_reviews WHERE id = ?", (review_id,)
    ).fetchone()
    conn.close()

    return jsonify(dict(updated))


# ── POST /api/advisor/escalation-prompt ─────────────────────────────────

@advisor_external_bp.route('/api/advisor/escalation-prompt', methods=['POST'])
def escalation_prompt():
    data = request.json or {}
    thread_id = data.get('thread_id')
    target = data.get('target')
    context_note = data.get('context_note', '')

    if not thread_id or not target:
        return jsonify({'error': 'thread_id and target are required'}), 400

    if target not in ('claude', 'chatgpt'):
        return jsonify({'error': 'target must be claude or chatgpt'}), 400

    conn = get_db()

    # Get thread title
    thread = conn.execute(
        "SELECT title FROM advisor_threads WHERE id = ?", (thread_id,)
    ).fetchone()
    if not thread:
        conn.close()
        return jsonify({'error': 'Thread not found'}), 404

    # Get last 10 messages
    rows = conn.execute(
        """SELECT agent_name, role, content FROM advisor_messages
           WHERE thread_id = ?
           ORDER BY message_index, created_at DESC
           LIMIT 10""",
        (thread_id,)
    ).fetchall()
    conn.close()

    # Reverse to chronological order
    messages = list(reversed(rows))

    deliberation = "\n\n".join(
        f"{'USER' if r['role'] == 'user' else r['agent_name'].upper()}: {r['content']}"
        for r in messages
    )

    target_role = "Technical Planner" if target == "claude" else "Workflow Auditor"

    prompt = (
        f"You are reviewing a deliberation in progress.\n\n"
        f"THREAD: {thread['title'] or f'Thread {thread_id}'}\n"
        f"TARGET ROLE: {target_role}\n\n"
        f"RECENT DELIBERATION:\n{deliberation}\n\n"
    )
    if context_note:
        prompt += f"CONTEXT NOTE: {context_note}\n\n"
    prompt += (
        "Please provide:\n"
        "- Recommendation summary\n"
        "- Risks or concerns\n"
        "- Proposed next action\n"
        "- Verdict: approve / revise / reject / unclear"
    )

    return jsonify({'prompt_text': prompt})
