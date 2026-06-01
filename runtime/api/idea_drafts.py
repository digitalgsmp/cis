import json
import logging
import sqlite3
import urllib.request
from datetime import datetime
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

idea_drafts_bp = Blueprint('idea_drafts', __name__)

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


def _call_gateway(gateway_url, model, api_key, messages, max_tokens=2000, timeout=120):
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


# Fetch domain values for the prompt
def get_domain_values():
    try:
        conn = get_db()
        rows = conn.execute("SELECT name FROM domains ORDER BY name").fetchall()
        conn.close()
        return [r["name"] for r in rows] if rows else ["creative", "socialcare", "personal", "technical", "learning"]
    except Exception:
        return ["creative", "socialcare", "personal", "technical", "learning"]


@idea_drafts_bp.route('/api/idea-drafts/structure', methods=['POST'])
def structure():
    """Send full thread to Prime for structuring into an idea draft."""
    data = request.json or {}
    thread_id = data.get('thread_id')

    if not thread_id:
        return jsonify({'error': 'thread_id is required'}), 400

    # Fetch all messages for this thread
    conn = get_db()
    messages = conn.execute(
        """SELECT agent_name, role, content FROM advisor_messages
           WHERE thread_id = ? ORDER BY created_at ASC""",
        (thread_id,)
    ).fetchall()

    if not messages:
        conn.close()
        return jsonify({'error': 'Thread has no messages'}), 400

    # Check for at least one user message
    user_messages = [m for m in messages if m['role'] == 'user']
    if not user_messages:
        conn.close()
        return jsonify({'error': 'Thread has no user messages'}), 400

    # Collect source message IDs
    msg_ids = conn.execute(
        "SELECT id FROM advisor_messages WHERE thread_id = ? ORDER BY created_at ASC",
        (thread_id,)
    ).fetchall()
    source_ids = [m['id'] for m in msg_ids]
    conn.close()

    # Get valid domain values
    domains = get_domain_values()
    domain_list = ", ".join(domains)

    # Build conversation transcript
    transcript = ""
    for m in messages:
        role_label = "USER" if m['role'] == 'user' else m['agent_name'].upper()
        transcript += f"[{role_label}]: {m['content']}\n\n"

    # Build structuring prompt for Prime
    prompt = (
        "STRUCTURE THIS CONVERSATION INTO AN IDEA DRAFT.\n\n"
        "Below is a conversation transcript. Extract the core creative idea and "
        "produce a structured draft object.\n\n"
        "--- CONVERSATION TRANSCRIPT ---\n"
        f"{transcript}"
        "--- END TRANSCRIPT ---\n\n"
        "Return ONLY a JSON object with exactly these keys. No prose, no explanation, "
        "no markdown code fences around the JSON:\n\n"
        "{\n"
        '  "title": "A concise, descriptive title for the idea",\n'
        '  "summary": "2-3 sentence summary of what the idea is",\n'
        '  "intent": "What the user wants to accomplish with this idea",\n'
        f'  "domain": "One of: {domain_list}",\n'
        '  "open_questions": ["question 1", "question 2"],\n'
        '  "suggested_next_step": "One concrete action to move this idea forward"\n'
        "}\n\n"
        "RULES:\n"
        "- title: Required. Must be a real title, not 'Untitled'.\n"
        f"- domain: Must be exactly one of the listed values: {domain_list}. Pick the best fit.\n"
        "- open_questions: JSON array of strings. If no open questions, use empty array [].\n"
        "- If you cannot determine a field from the conversation, use null for that field value.\n"
        "- Do not hallucinate. Do not invent details not present in the conversation.\n"
        "- Return ONLY the JSON object. No other text."
    )

    # Call Prime
    prime = get_agent('hermes-prime')
    if not prime:
        return jsonify({'error': 'Prime agent not found or inactive'}), 500

    prime_key = read_api_key(prime['env_path'])
    if not prime_key:
        return jsonify({'error': 'API_SERVER_KEY not found for Prime'}), 500

    try:
        raw = _call_gateway(
            prime['gateway_url'], prime['model'], prime_key,
            [{"role": "user", "content": prompt}],
            max_tokens=2000
        )
    except Exception as e:
        return jsonify({'error': f'Structuring call failed: {str(e)}'}), 502

    # Parse Prime's JSON response
    try:
        raw = raw.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            raw = raw.strip()
        if raw.startswith('json'):
            raw = raw[4:].strip()
        draft_data = json.loads(raw)
    except json.JSONDecodeError:
        return jsonify({'error': 'Prime did not return valid JSON', 'raw': raw[:300]}), 502

    # Validate required field
    if not draft_data.get('title'):
        return jsonify({'error': 'Prime returned a draft with no title'}), 502

    # Validate domain
    domain = draft_data.get('domain', '')
    if domain and domain not in domains:
        domain = domains[0]  # fallback to first domain
        draft_data['domain'] = domain

    # Insert into idea_drafts
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO idea_drafts
           (title, summary, intent, domain, domain_source,
            open_questions, suggested_next_step,
            source_thread_id, source_message_ids, input_scope,
            structuring_agent, structuring_model)
           VALUES (?, ?, ?, ?, 'ai_suggested', ?, ?, ?, ?, 'full_thread', 'hermes-prime', ?)""",
        (
            draft_data.get('title', ''),
            draft_data.get('summary', ''),
            draft_data.get('intent', ''),
            domain,
            json.dumps(draft_data.get('open_questions', [])),
            draft_data.get('suggested_next_step', ''),
            thread_id,
            json.dumps(source_ids),
            prime['model']
        )
    )
    conn.commit()
    draft_id = cur.lastrowid

    # Fetch the full row to return
    row = conn.execute("SELECT * FROM idea_drafts WHERE id = ?", (draft_id,)).fetchone()
    conn.close()

    return jsonify(dict(row)), 201


@idea_drafts_bp.route('/api/idea-drafts', methods=['GET'])
def list_drafts():
    """Return all non-dismissed drafts, optionally filtered by thread."""
    thread_id = request.args.get('thread_id', type=int)
    conn = get_db()
    if thread_id:
        rows = conn.execute(
            "SELECT * FROM idea_drafts WHERE status != 'dismissed' AND source_thread_id = ? ORDER BY created_at DESC",
            (thread_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM idea_drafts WHERE status != 'dismissed' ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@idea_drafts_bp.route('/api/idea-drafts/<int:draft_id>', methods=['GET'])
def get_draft(draft_id):
    """Return a single draft by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM idea_drafts WHERE id = ?", (draft_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Draft not found'}), 404
    return jsonify(dict(row))


@idea_drafts_bp.route('/api/idea-drafts/<int:draft_id>', methods=['PATCH'])
def update_draft(draft_id):
    """Update editable fields on a draft."""
    data = request.json or {}
    conn = get_db()
    row = conn.execute("SELECT * FROM idea_drafts WHERE id = ?", (draft_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Draft not found'}), 404

    allowed = ['title', 'summary', 'intent', 'domain', 'domain_source',
               'suggested_next_step', 'status']
    updates = {}
    for key in allowed:
        if key in data:
            updates[key] = data[key]

    # Auto-transition domain_source when domain is edited
    if 'domain' in updates and 'domain_source' not in data:
        updates['domain_source'] = 'user_confirmed'

    if updates:
        updates['updated_at'] = datetime.utcnow().isoformat()
        set_clause = ', '.join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [draft_id]
        conn.execute(f"UPDATE idea_drafts SET {set_clause} WHERE id = ?", values)
        conn.commit()

    row = conn.execute("SELECT * FROM idea_drafts WHERE id = ?", (draft_id,)).fetchone()
    conn.close()
    return jsonify(dict(row))
