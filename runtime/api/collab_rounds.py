"""
api/collab_rounds.py — Advisor Round Wizard API.
Manages collaboration rounds between Claude, ChatGPT, and Hermes.
"""

from flask import Blueprint, jsonify, request, Response, stream_with_context
from db.connection import db_connect
from utils.helpers import ts
import json, urllib.request, urllib.error, os, sys, glob, http.client

sys.path.insert(0, '/mnt/projects/cis/runtime')


def auto_import_session(session_id, round_id, topic):
    """Import a Hermes API session into collab_session_imports, tagged with round."""
    session_path = None
    pattern = "/home/eric/.hermes/sessions/session_api-*.json"
    for f in glob.glob(pattern):
        try:
            with open(f) as fh:
                data = json.load(fh)
            sid_short = session_id.replace("chatcmpl-", "")
            if sid_short in f or sid_short in str(data.get("session_id", "")):
                session_path = f
                break
        except Exception:
            continue
    if not session_path:
        files = sorted(glob.glob(pattern), key=lambda x: os.path.getmtime(x), reverse=True)
        if files:
            session_path = files[0]
    if not session_path:
        return {"ok": False, "error": "Session file not found"}
    try:
        with open(session_path) as fh:
            sdata = json.load(fh)
        conn = db_connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collab_session_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                session_id TEXT NOT NULL,
                session_start TEXT NOT NULL,
                session_end TEXT NOT NULL,
                model TEXT DEFAULT '',
                base_url TEXT DEFAULT '',
                platform TEXT DEFAULT '',
                message_count INTEGER DEFAULT 0,
                imported_at TEXT DEFAULT '',
                round_id INTEGER DEFAULT NULL,
                round_topic TEXT DEFAULT '',
                UNIQUE(source_path, session_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS collab_session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                import_id INTEGER NOT NULL REFERENCES collab_session_imports(id),
                message_index INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                name TEXT DEFAULT '',
                tool_call_id TEXT DEFAULT '',
                finish_reason TEXT DEFAULT '',
                has_tool_calls INTEGER DEFAULT 0,
                tool_calls_json TEXT DEFAULT '',
                reasoning TEXT DEFAULT '',
                reasoning_content TEXT DEFAULT '',
                UNIQUE(import_id, message_index)
            )
        """)
        conn.commit()
        sid = sdata.get("session_id", "")
        cur = conn.execute(
            "INSERT OR IGNORE INTO collab_session_imports (source_path, session_id, session_start, session_end, model, base_url, platform, message_count, imported_at, round_id, round_topic) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (session_path, sid, sdata.get("session_start",""), sdata.get("last_updated",""),
             sdata.get("model",""), sdata.get("base_url",""), sdata.get("platform",""),
             len(sdata.get("messages",[])), ts(), round_id, topic)
        )
        conn.commit()
        if conn.execute("SELECT changes()").fetchone()[0] == 0:
            conn.close()
            return {"ok": True, "skipped": True, "session_path": session_path}
        import_id = cur.lastrowid
        messages = sdata.get("messages", [])
        for i, msg in enumerate(messages):
            content = msg.get("content","")
            if isinstance(content, list):
                content = json.dumps(content)
            tc = msg.get("tool_calls")
            conn.execute(
                "INSERT OR IGNORE INTO collab_session_messages (import_id, message_index, role, content, name, tool_call_id, finish_reason, has_tool_calls, tool_calls_json, reasoning, reasoning_content) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (import_id, i, msg.get("role",""), content, msg.get("name",""),
                 msg.get("tool_call_id",""), msg.get("finish_reason",""),
                 1 if tc else 0, json.dumps(tc) if tc else "",
                 msg.get("reasoning",""), msg.get("reasoning_content",""))
            )
        conn.commit()
        conn.close()
        return {"ok": True, "session_path": session_path, "message_count": len(messages)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


collab_rounds_bp = Blueprint("collab_rounds", __name__)

HERMES_API_URL = "http://127.0.0.1:8642/v1/chat/completions"
HERMES_API_KEY = os.environ.get("API_SERVER_KEY", "")
QWEN_API_URL = "http://127.0.0.1:8002/v1/chat/completions"
DEEPSEEK_R1_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_R1_KEY = os.environ.get("DEEPSEEK_R1_KEY", "")

# Reference documents injected into every reviewer prompt
REVIEWER_REFERENCE_FILES = [
    "/mnt/projects/cis/docs/architecture_atlas/original_CISChats/CIS_Canonical_Build_Sequence_Plain_Language.md",
    "/mnt/projects/cis/PROJECT_CONTEXT_PACK/02_ACTIVE_ARCHITECTURE.md",
    "/mnt/projects/cis/PROJECT_CONTEXT_PACK/03_DECISIONS_LOG.md",
    "/mnt/projects/cis/PROJECT_CONTEXT_PACK/06_MODEL_ROLES_AND_PROTOCOL.md",
    "/mnt/projects/cis/PROJECT_CONTEXT_PACK/09_TERMS_AND_NAMING.md",
]

def load_reference_docs():
    """Load reference documents for reviewer context. Returns combined text."""
    parts = ["# PROJECT REFERENCE DOCUMENTS\n"]
    for path in REVIEWER_REFERENCE_FILES:
        try:
            with open(path) as f:
                content = f.read()
            name = os.path.basename(path)
            # Truncate very long files to keep prompt manageable
            if len(content) > 8000:
                content = content[:8000] + "\n\n[... truncated for prompt size ...]"
            parts.append(f"## {name}\n{content}")
        except Exception:
            parts.append(f"## {os.path.basename(path)}\n[file not available]")
    return "\n\n".join(parts)


def ensure_rounds_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            round_type TEXT DEFAULT '',
            eric_context TEXT DEFAULT '',
            current_concern TEXT DEFAULT '',
            desired_outcome TEXT DEFAULT '',
            claude_input TEXT DEFAULT '',
            claude_summary TEXT DEFAULT '',
            chatgpt_input TEXT DEFAULT '',
            chatgpt_summary TEXT DEFAULT '',
            hermes_packet TEXT DEFAULT '',
            hermes_response TEXT DEFAULT '',
            hermes_session_id TEXT DEFAULT '',
            open_decision TEXT DEFAULT '',
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )
    """)
    conn.commit()


@collab_rounds_bp.route("/api/collab/rounds", methods=["GET"])
def get_rounds():
    conn = db_connect()
    ensure_rounds_table(conn)
    rows = conn.execute("SELECT * FROM collab_rounds ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@collab_rounds_bp.route("/api/collab/rounds", methods=["POST"])
def create_round():
    data = request.json
    now = ts()
    conn = db_connect()
    ensure_rounds_table(conn)
    cur = conn.execute(
        "INSERT INTO collab_rounds (topic, round_type, eric_context, current_concern, desired_outcome, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (data.get("topic",""), data.get("round_type",""), data.get("eric_context",""),
         data.get("current_concern",""), data.get("desired_outcome",""), "open", now, now)
    )
    conn.commit()
    round_id = cur.lastrowid
    conn.close()
    return jsonify({"ok": True, "id": round_id})


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>", methods=["GET"])
def get_round(round_id):
    conn = db_connect()
    ensure_rounds_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dict(row))


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>", methods=["PATCH"])
def update_round(round_id):
    data = request.json
    conn = db_connect()
    ensure_rounds_table(conn)
    allowed = ["topic","round_type","eric_context","current_concern","desired_outcome",
               "claude_input","claude_summary","chatgpt_input","chatgpt_summary",
               "hermes_packet","hermes_response","hermes_session_id","open_decision","status"]
    fields, values = [], []
    for key in allowed:
        if key in data:
            fields.append(f"{key}=?")
            values.append(data[key])
    fields.append("updated_at=?")
    values.append(ts())
    values.append(round_id)
    conn.execute(f"UPDATE collab_rounds SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/send-to-hermes", methods=["POST"])
def send_to_hermes(round_id):
    conn = db_connect()
    ensure_rounds_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Round not found"}), 404
    row = dict(row)

    packet = f"""COLLAB ROUND — ADVISOR INPUT

Topic: {row['topic']}

Eric Context: {row['eric_context']}
Current Concern: {row['current_concern']}
Desired Outcome: {row['desired_outcome']}

Claude Input: {row['claude_input']}

ChatGPT Input: {row['chatgpt_input']}

Hermes Role:
You are stenographer and continuity keeper for this round.
Do not execute. Do not decide. Do not compress away nuance.

Record:
1. Claude's position and recommendation
2. ChatGPT's position and recommendation
3. Points of agreement
4. Points of difference
5. Open decision for Eric
6. Suggested next question

Respond with a structured summary only."""

    try:
        payload = json.dumps({
            "model": "hermes-agent",
            "messages": [{"role": "user", "content": packet}]
        }).encode()
        req = urllib.request.Request(
            HERMES_API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {HERMES_API_KEY}"
            }
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode())
        response_text = result["choices"][0]["message"]["content"]
        session_id = result.get("id", "")

        conn = db_connect()
        conn.execute(
            "UPDATE collab_rounds SET hermes_packet=?, hermes_response=?, hermes_session_id=?, updated_at=? WHERE id=?",
            (packet, response_text, session_id, ts(), round_id)
        )
        conn.execute(
            "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
            ("Hermes", "collab_round", f"Round '{row['topic']}' processed by Hermes stenographer", "SENT", ts(), f"round-{round_id}")
        )
        conn.commit()
        # Auto-import the session
        import_result = auto_import_session(session_id, round_id, row['topic'])
        conn.close()
        return jsonify({"ok": True, "response": response_text, "session_id": session_id, "packet": packet, "import": import_result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "packet": packet})


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/send-to-hermes-stream", methods=["POST"])
def send_to_hermes_stream(round_id):
    """Stream Hermes response via SSE. Frontend sees text as it arrives."""
    conn = db_connect()
    ensure_rounds_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Round not found"}), 404
    row = dict(row)

    packet = f"""COLLAB ROUND — ADVISOR INPUT

Topic: {row['topic']}

Eric Context: {row['eric_context']}
Current Concern: {row['current_concern']}
Desired Outcome: {row['desired_outcome']}

Claude Input: {row['claude_input']}

ChatGPT Input: {row['chatgpt_input']}

Hermes Role:
You are stenographer and continuity keeper for this round.
Do not execute. Do not decide. Do not compress away nuance.

Record:
1. Claude's position and recommendation
2. ChatGPT's position and recommendation
3. Points of agreement
4. Points of difference
5. Open decision for Eric
6. Suggested next question

Respond with a structured summary only."""

    def generate():
        accumulated = ""
        session_id = ""
        connection = None
        try:
            payload = json.dumps({
                "model": "hermes-agent",
                "messages": [{"role": "user", "content": packet}],
                "stream": True
            }).encode()

            # Parse host/port from HERMES_API_URL
            url = HERMES_API_URL
            if url.startswith("http://"):
                url = url[7:]
            host, _, rest = url.partition(":")
            port, _, path = rest.partition("/")
            path = "/" + path

            connection = http.client.HTTPConnection(host, int(port), timeout=300)
            connection.request(
                "POST", path,
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {HERMES_API_KEY}"
                }
            )
            resp = connection.getresponse()

            # Yield an initial event so the frontend shows "thinking..."
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
                content = delta.get("content", "")
                if content:
                    accumulated += content
                    yield f"data: {json.dumps({'delta': content})}\n\n"

                # Capture session ID from first chunk
                if not session_id and chunk.get("id"):
                    session_id = chunk["id"]

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

        # Save the complete response
        if accumulated:
            try:
                conn2 = db_connect()
                conn2.execute(
                    "UPDATE collab_rounds SET hermes_packet=?, hermes_response=?, hermes_session_id=?, updated_at=? WHERE id=?",
                    (packet, accumulated, session_id, ts(), round_id)
                )
                conn2.execute(
                    "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
                    ("Hermes", "collab_round", f"Round '{row['topic']}' processed by Hermes stenographer", "SENT", ts(), f"round-{round_id}")
                )
                conn2.commit()
                auto_import_session(session_id, round_id, row['topic'])
                conn2.close()
            except Exception:
                pass

        # Signal completion
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "X-Accel-Buffering": "no",
                        "Connection": "keep-alive",
                    })


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/send-to-reviewer", methods=["POST"])
def send_to_reviewer(round_id):
    """Send round context to local Qwen reviewer for adversarial review."""
    conn = db_connect()
    ensure_rounds_table(conn)
    ensure_exchanges_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Round not found"}), 404
    row = dict(row)

    # Build handoff-like context for reviewer
    status_row = conn.execute("SELECT * FROM collab_status WHERE id=1").fetchone()
    status = dict(status_row) if status_row else {}

    activity = conn.execute(
        "SELECT source, activity_type, summary, verdict FROM collab_activity ORDER BY id DESC LIMIT 5"
    ).fetchall()
    conn.close()

    act_lines = "\n".join(
        f"- {dict(a).get('source','?')} [{dict(a).get('activity_type','?')}] {dict(a).get('summary','?')}"
        for a in activity
    )

    packet = f"""ADVERSARIAL REVIEW — QWEN REVIEWER

You are a skeptical architectural reviewer. Your job: find what the executor missed.

## Current State
Focus: {status.get('current_focus', '?')}
Next Action: {status.get('next_single_action', '?')}
Status: {status.get('status', '?')}

## Recent Activity
{act_lines}

## Round Context
Topic: {row['topic']}
Eric's Context: {row['eric_context']}
Current Concern: {row['current_concern']}
Desired Outcome: {row['desired_outcome']}

{load_reference_docs()}

## Hermes (DeepSeek) Response
{row.get('hermes_response') or '— no response yet —'}

## Your Task
1. What blind spot or assumption did DeepSeek make?
2. Is there enterprise-pattern drift (treating a creative OS like a CRUD app/dashboard/pipeline)?
3. What would you reject or ask Eric to clarify?
4. What is the single highest-risk thing in this proposal?

Respond concisely. Do not propose code. Do not execute. Flag architecture problems only."""

    try:
        payload = json.dumps({
            "model": "local",
            "messages": [{"role": "user", "content": packet}],
            "max_tokens": 1500,
            "temperature": 0.3
        }).encode()
        req = urllib.request.Request(
            QWEN_API_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
        review_text = result["choices"][0]["message"]["content"]

        conn = db_connect()
        ensure_exchanges_table(conn)
        now = ts()
        conn.execute(
            """INSERT INTO collab_exchanges
               (round_id, pass_number, topic, type, context, current_concern,
                desired_outcome, claude_response, chatgpt_response, captured_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (round_id, 99, row['topic'], 'reviewer',
             packet, row['current_concern'], row['desired_outcome'],
             review_text, '', now))
        conn.execute(
            "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
            ("Qwen Reviewer", "review", f"Adversarial review of round '{row['topic']}'", "FLAGGED", now, f"round-{round_id}")
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "review": review_text, "packet": packet})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "packet": packet})


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/send-to-r1", methods=["POST"])
def send_to_r1(round_id):
    """Send round context to DeepSeek R1 for reasoning review."""
    conn = db_connect()
    ensure_rounds_table(conn)
    ensure_exchanges_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Round not found"}), 404
    row = dict(row)

    status_row = conn.execute("SELECT * FROM collab_status WHERE id=1").fetchone()
    status = dict(status_row) if status_row else {}

    activity = conn.execute(
        "SELECT source, activity_type, summary, verdict FROM collab_activity ORDER BY id DESC LIMIT 5"
    ).fetchall()
    conn.close()

    act_lines = "\n".join(
        f"- {dict(a).get('source','?')} [{dict(a).get('activity_type','?')}] {dict(a).get('summary','?')}"
        for a in activity
    )

    packet = f"""DEEPSEEK R1 REASONING REVIEW

You are a rigorous step-by-step reasoning reviewer. Think through every implication before answering.

## Current State
Focus: {status.get('current_focus', '?')}
Next Action: {status.get('next_single_action', '?')}
Status: {status.get('status', '?')}

## Recent Activity
{act_lines}

## Round Context
Topic: {row['topic']}
Eric's Context: {row['eric_context']}
Current Concern: {row['current_concern']}
Desired Outcome: {row['desired_outcome']}

{load_reference_docs()}

## Hermes (DeepSeek V4) Response
{row.get('hermes_response') or '— no response yet —'}

## Your Task
Think step by step:
1. Walk through every logical implication of what DeepSeek proposed.
2. What second-order consequences did it miss?
3. What constraints or dependencies are unstated?
4. If you had to pick one thing to challenge, what is it and why?

Be thorough. This is a reasoning review — precision matters more than speed."""

    try:
        payload = json.dumps({
            "model": "deepseek-reasoner",
            "messages": [{"role": "user", "content": packet}]
        }).encode()
        req = urllib.request.Request(
            DEEPSEEK_R1_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_R1_KEY}"
            }
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
        review_text = result["choices"][0]["message"]["content"]

        conn = db_connect()
        ensure_exchanges_table(conn)
        now = ts()
        conn.execute(
            """INSERT INTO collab_exchanges
               (round_id, pass_number, topic, type, context, current_concern,
                desired_outcome, chatgpt_response, captured_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (round_id, 98, row['topic'], 'r1-reviewer',
             packet, row['current_concern'], row['desired_outcome'],
             review_text, now))
        conn.execute(
            "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
            ("DeepSeek R1", "review", f"R1 reasoning review of round '{row['topic']}'", "REVIEWED", now, f"round-{round_id}")
        )
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "review": review_text, "packet": packet})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "packet": packet})


def ensure_exchanges_table(conn):
    """Create collab_exchanges table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_exchanges (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id        INTEGER NOT NULL,
            pass_number     INTEGER NOT NULL DEFAULT 1,
            topic           TEXT DEFAULT '',
            type            TEXT DEFAULT '',
            context         TEXT DEFAULT '',
            current_concern TEXT DEFAULT '',
            desired_outcome TEXT DEFAULT '',
            claude_response TEXT DEFAULT '',
            chatgpt_response TEXT DEFAULT '',
            eric_addendum   TEXT DEFAULT '',
            captured_at     TEXT NOT NULL
        )
    """)
    conn.commit()


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/capture-exchange", methods=["POST"])
def capture_exchange(round_id):
    """Save raw advisor exchange to SQLite. No Hermes call. No external HTTP."""
    conn = db_connect()
    ensure_rounds_table(conn)
    ensure_exchanges_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Round not found"}), 404
    row = dict(row)
    data = request.json or {}
    # Compute next pass_number from existing exchanges for this round
    existing = conn.execute(
        "SELECT COALESCE(MAX(pass_number), 0) FROM collab_exchanges WHERE round_id=?",
        (round_id,)
    ).fetchone()[0]
    pass_number = data.get("pass_number", existing + 1)
    now = ts()
    conn.execute(
        """INSERT INTO collab_exchanges
           (round_id, pass_number, topic, type, context, current_concern,
            desired_outcome, claude_response, chatgpt_response, eric_addendum, captured_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (round_id, pass_number,
         row.get("topic", ""), row.get("round_type", ""),
         row.get("eric_context", ""), row.get("current_concern", ""),
         row.get("desired_outcome", ""),
         data.get("claude_response", row.get("claude_input", "")),
         data.get("chatgpt_response", row.get("chatgpt_input", "")),
         data.get("eric_addendum", ""),
         now)
    )
    conn.commit()
    exchange_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
        ("Wizard", "capture_exchange",
         f"Exchange {pass_number} captured for round '{row.get('topic','')}'",
         "CAPTURED", now, f"round-{round_id}")
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "status": "captured", "exchange_id": exchange_id, "pass_number": pass_number})


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/exchanges", methods=["GET"])
def get_exchanges(round_id):
    conn = db_connect()
    ensure_rounds_table(conn)
    rows = conn.execute(
        "SELECT * FROM collab_session_imports WHERE round_id=? ORDER BY id ASC",
        (round_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/followup-prompt", methods=["POST"])
def generate_followup(round_id):
    data = request.json or {}
    conn = db_connect()
    ensure_rounds_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    row = dict(row)
    eric_addendum = data.get("eric_addendum", "")
    prompt = f"""We are continuing the same collaboration topic.

Topic: {row['topic']}
Type: {row['round_type']}

Previous Hermes Synthesis:
{row['hermes_response']}

Original Context: {row['eric_context']}
Original Concern: {row['current_concern']}
Desired Outcome: {row['desired_outcome']}"""

    if eric_addendum:
        prompt += f"\n\nEric adds: {eric_addendum}"

    prompt += "\n\nPlease respond only to what remains unresolved. Help move this toward a final directive."
    return jsonify({"ok": True, "prompt": prompt})


# ── Final Directive ──────────────────────────────────────────────────────────

def ensure_final_directives_table(conn):
    """Create collab_final_directives table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_final_directives (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            round_id        INTEGER NOT NULL,
            exchange_ids    TEXT DEFAULT '',
            topic           TEXT DEFAULT '',
            decision_made   TEXT DEFAULT '',
            accepted_basis  TEXT DEFAULT '' CHECK(accepted_basis IN ('','claude','chatgpt','combined','eric_override','other')),
            final_directive TEXT DEFAULT '',
            scope           TEXT DEFAULT '',
            do_not_do       TEXT DEFAULT '',
            success_criteria TEXT DEFAULT '',
            evidence_required TEXT DEFAULT '',
            owner_executor  TEXT DEFAULT 'Hermes',
            status          TEXT DEFAULT 'draft' CHECK(status IN ('draft','approved','executing','complete','verified','rejected','superseded')),
            next_action     TEXT DEFAULT '',
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    conn.commit()
    for col_sql in [
        "ALTER TABLE collab_final_directives ADD COLUMN execution_status TEXT DEFAULT 'draft'",
        "ALTER TABLE collab_final_directives ADD COLUMN execution_report TEXT DEFAULT ''",
        "ALTER TABLE collab_final_directives ADD COLUMN reported_at TEXT DEFAULT ''",
        "ALTER TABLE collab_final_directives ADD COLUMN verified_by TEXT DEFAULT ''",
        "ALTER TABLE collab_final_directives ADD COLUMN verified_at TEXT DEFAULT ''",
        "ALTER TABLE collab_final_directives ADD COLUMN verification_result TEXT DEFAULT ''",
    ]:
        try:
            conn.execute(col_sql)
            conn.commit()
        except Exception:
            pass


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/final-directive", methods=["POST"])
def create_final_directive(round_id):
    """Create a final directive linked to a round."""
    conn = db_connect()
    ensure_rounds_table(conn)
    ensure_final_directives_table(conn)
    row = conn.execute("SELECT * FROM collab_rounds WHERE id=?", (round_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Round not found"}), 404
    row = dict(row)
    data = request.json or {}
    now = ts()
    # Collect exchange_ids for this round
    exchanges = conn.execute(
        "SELECT id FROM collab_exchanges WHERE round_id=? ORDER BY pass_number", (round_id,)
    ).fetchall()
    exchange_ids = ",".join(str(e[0]) for e in exchanges)
    conn.execute(
        """INSERT INTO collab_final_directives
           (round_id, exchange_ids, topic, decision_made, accepted_basis,
            final_directive, scope, do_not_do, success_criteria,
            evidence_required, owner_executor, status, next_action, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (round_id, exchange_ids,
         data.get("topic", row.get("topic", "")),
         data.get("decision_made", ""),
         data.get("accepted_basis", ""),
         data.get("final_directive", ""),
         data.get("scope", ""),
         data.get("do_not_do", ""),
         data.get("success_criteria", ""),
         data.get("evidence_required", ""),
         data.get("owner_executor", "Hermes"),
         data.get("status", "draft"), data.get("next_action", ""),
         now, now)
    )
    conn.commit()
    directive_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
        ("Wizard", "final_directive",
         f"Directive created for round '{row.get('topic','')}'",
         "DRAFT", now, f"round-{round_id}")
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "directive_id": directive_id, "status": data.get("status", "draft")})


@collab_rounds_bp.route("/api/collab/rounds/<int:round_id>/final-directive", methods=["GET"])
def get_final_directive(round_id):
    """Return the directive for a round if it exists."""
    conn = db_connect()
    ensure_final_directives_table(conn)
    row = conn.execute(
        "SELECT * FROM collab_final_directives WHERE round_id=? ORDER BY id DESC LIMIT 1",
        (round_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"ok": True, "directive": None})
    return jsonify({"ok": True, "directive": dict(row)})


@collab_rounds_bp.route("/api/collab/directives/<int:directive_id>", methods=["GET"])
def get_directive_by_id(directive_id):
    conn = db_connect()
    ensure_final_directives_table(conn)
    row = conn.execute(
        "SELECT * FROM collab_final_directives WHERE id=?", (directive_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"ok": True, "directive": dict(row)})


@collab_rounds_bp.route("/api/collab/directives/<int:directive_id>", methods=["PATCH"])
def update_final_directive(directive_id):
    """Update fields on an existing directive."""
    conn = db_connect()
    ensure_final_directives_table(conn)
    row = conn.execute("SELECT * FROM collab_final_directives WHERE id=?", (directive_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Directive not found"}), 404
    data = request.json or {}
    allowed = ["decision_made","accepted_basis","final_directive","scope","do_not_do",
               "success_criteria","evidence_required","owner_executor","status",
               "next_action","execution_status"]
    fields, values = [], []
    for key in allowed:
        if key in data:
            fields.append(f"{key}=?")
            values.append(data[key])
    if fields:
        fields.append("updated_at=?")
        values.append(ts())
        values.append(directive_id)
        conn.execute(f"UPDATE collab_final_directives SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


@collab_rounds_bp.route("/api/collab/directives/<int:directive_id>/report", methods=["POST"])
def directive_report(directive_id):
    """Hermes posts its execution report here on task completion."""
    conn = db_connect()
    ensure_final_directives_table(conn)
    row = conn.execute(
        "SELECT * FROM collab_final_directives WHERE id=?", (directive_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Directive not found"}), 404
    data = request.json or {}
    report_text = data.get("report", "")
    if not report_text:
        conn.close()
        return jsonify({"error": "report field required"}), 400
    now = ts()
    conn.execute(
        "UPDATE collab_final_directives SET execution_report=?, execution_status='executed', reported_at=?, updated_at=? WHERE id=?",
        (report_text, now, now, directive_id)
    )
    conn.execute(
        "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
        ("Hermes", "execution_report",
         f"Execution report received for directive {directive_id}",
         "EXECUTED", now, f"directive-{directive_id}")
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM collab_final_directives WHERE id=?", (directive_id,)
    ).fetchone()
    conn.close()
    return jsonify({"ok": True, "directive": dict(row)})


@collab_rounds_bp.route("/api/collab/directives/<int:directive_id>/verify", methods=["POST"])
def directive_verify(directive_id):
    """Eric marks verification result after advisor review."""
    conn = db_connect()
    ensure_final_directives_table(conn)
    row = conn.execute(
        "SELECT * FROM collab_final_directives WHERE id=?", (directive_id,)
    ).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Directive not found"}), 404
    row = dict(row)
    if not row.get("execution_report"):
        conn.close()
        return jsonify({"error": "Cannot verify — no execution report on record"}), 400
    data = request.json or {}
    valid_results = ("verified_pass", "verified_fail", "needs_revision")
    result = data.get("result", "").lower()
    if result not in valid_results:
        conn.close()
        return jsonify({"error": f"result must be one of {valid_results}"}), 400
    verified_by = data.get("verified_by", "")
    now = ts()
    conn.execute(
        "UPDATE collab_final_directives SET verification_result=?, verified_by=?, verified_at=?, execution_status=?, updated_at=? WHERE id=?",
        (result, verified_by, now, result, now, directive_id)
    )
    conn.execute(
        "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
        ("Eric", "verification",
         f"Directive {directive_id} marked {result} by {verified_by}",
         result.upper(), now, f"directive-{directive_id}")
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM collab_final_directives WHERE id=?", (directive_id,)
    ).fetchone()
    conn.close()
    return jsonify({"ok": True, "directive": dict(row)})


@collab_rounds_bp.route("/api/collab/handoff", methods=["GET"])
def generate_handoff():
    conn = db_connect()
    try:
        ensure_rounds_table(conn)

        status_row = conn.execute("SELECT * FROM collab_status WHERE id=1").fetchone()
        status = dict(status_row) if status_row else {}

        activity = conn.execute(
            """
            SELECT source, activity_type, summary, verdict, created_at
            FROM collab_activity
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        round_row = conn.execute(
            "SELECT * FROM collab_rounds WHERE status='open' ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if not round_row:
            round_row = conn.execute(
                "SELECT * FROM collab_rounds ORDER BY id DESC LIMIT 1"
            ).fetchone()

        round_data = dict(round_row) if round_row else {}
    finally:
        conn.close()

    now = ts()

    lines = [
        "# HERMES HARNESS SESSION HANDOFF",
        f"Generated: {now}",
        "",
        "## Purpose",
        "Orient a cold Claude / ChatGPT / Hermes session. Do not re-explain decisions already made. Continue from this state.",
        "",
        "## Current Focus",
        status.get("current_focus") or "—",
        "",
        "## Next Single Action",
        status.get("next_single_action") or "—",
        "",
        "## Status",
        f"{status.get('status') or '—'} — last updated by {status.get('updated_by') or '—'} at {status.get('updated_at') or '—'}",
        "",
        "## Recent Decisions and Activity",
    ]

    for row in activity:
        a = dict(row)
        verdict = f" → {a.get('verdict')}" if a.get("verdict") else ""
        lines.append(
            f"- {a.get('source', '—')} [{a.get('activity_type', '—')}] {a.get('summary', '—')}{verdict}"
        )

    if round_data:
        lines += [
            "",
            "## Active / Recent Round",
            f"Topic: {round_data.get('topic') or '—'}",
            f"Type: {round_data.get('round_type') or '—'}",
            f"Status: {round_data.get('status') or '—'}",
            "",
            "### Latest Hermes Synthesis",
            round_data.get("hermes_response") or "— none yet —",
            "",
            "### Open Decision",
            round_data.get("open_decision") or "— none recorded —",
        ]

    lines += [
        "",
        "## Do Not",
        "- Re-open decisions already marked complete.",
        "- Rebuild infrastructure that is already verified.",
        "- Ask Eric for context already present above.",
        "",
        "## Continue Here",
        status.get("next_single_action") or "Check current status and confirm next action with Eric.",
        "",
        "## Evidence",
        "- Collab Tracker: http://127.0.0.1:5000/ui/infra",
        "- Raw session logs: /home/eric/.hermes/sessions/",
        "- Database: /mnt/projects/cis/runtime/cis_memory.db",
        "- Project Context Pack: /mnt/projects/cis/PROJECT_CONTEXT_PACK/",
    ]

    handoff_text = "\n".join(lines)
    return jsonify({"ok": True, "handoff": handoff_text, "generated_at": now})


@collab_rounds_bp.route("/api/collab/context-pack/export-preview", methods=["POST"])
def export_context_pack_preview():
    import os
    from api.collab import ensure_extended_tables

    conn = db_connect()
    try:
        ensure_rounds_table(conn)
        ensure_extended_tables(conn)

        status_row = conn.execute("SELECT * FROM collab_status WHERE id=1").fetchone()
        status = dict(status_row) if status_row else {}

        activity = conn.execute(
            "SELECT * FROM collab_activity ORDER BY id DESC LIMIT 10"
        ).fetchall()

        decisions = conn.execute(
            "SELECT * FROM collab_decisions ORDER BY id"
        ).fetchall()

        open_questions = conn.execute(
            "SELECT * FROM collab_open_questions ORDER BY id"
        ).fetchall()

        next_actions = conn.execute(
            "SELECT * FROM collab_next_actions WHERE status != 'complete' ORDER BY priority"
        ).fetchall()

        files_changed = conn.execute(
            "SELECT * FROM collab_files_changed ORDER BY id DESC LIMIT 20"
        ).fetchall()

        round_row = conn.execute(
            "SELECT * FROM collab_rounds WHERE status='open' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not round_row:
            round_row = conn.execute(
                "SELECT * FROM collab_rounds ORDER BY id DESC LIMIT 1"
            ).fetchone()
        round_data = dict(round_row) if round_row else {}

    finally:
        conn.close()

    now = ts()
    preview_path = "/mnt/projects/cis/PROJECT_CONTEXT_PACK_GENERATED"
    upload_preview_path = "/mnt/projects/cis/PROJECT_CONTEXT_PACK_UPLOAD_GENERATED"
    os.makedirs(preview_path, exist_ok=True)
    os.makedirs(upload_preview_path, exist_ok=True)

    files_written = []

    def write_file(filename, content):
        for base, prefix in [(preview_path, ""), (upload_preview_path, "HCP_")]:
            with open(os.path.join(base, prefix + filename), "w", encoding="utf-8") as f:
                f.write(content)
        files_written.append(filename)

    activity_lines = "\n".join([
        f"- {dict(a)['source']} [{dict(a)['activity_type']}] {dict(a)['summary']}"
        for a in activity
    ])
    write_file("01_CURRENT_STATE.md", f"""# Current State — Hermes Harness
Last updated: {now}

## Current Focus
{status.get('current_focus') or '—'}

## Next Single Action
{status.get('next_single_action') or '—'}

## Status
{status.get('status') or '—'} — updated by {status.get('updated_by') or '—'} at {status.get('updated_at') or '—'}

## Recent Activity
{activity_lines}
""")

    dec_rows = "\n".join([
        f"| {dict(d).get('date','')} | {dict(d).get('decision','')} | {dict(d).get('reason','')} | {dict(d).get('status','')} | {dict(d).get('evidence','')} |"
        for d in decisions
    ])
    write_file("03_DECISIONS_LOG.md", f"""# Decisions Log — Hermes Harness
Last updated: {now}

| Date | Decision | Reason | Status | Evidence |
|------|----------|--------|--------|----------|
{dec_rows}
""")

    oq_sections = "\n\n".join([
        f"## {dict(q).get('code','')} — {dict(q).get('title','')}\n{dict(q).get('description','')}\nStatus: {dict(q).get('status','')}"
        for q in open_questions
    ])
    write_file("04_OPEN_QUESTIONS.md", f"""# Open Questions — Hermes Harness
Last updated: {now}

{oq_sections}
""")

    na_sections = "\n\n".join([
        f"## {dict(a).get('title','')}\nStatus: {dict(a).get('status','')}\n{dict(a).get('description','')}"
        for a in next_actions
    ])
    current_next = status.get('next_single_action') or '—'
    write_file("05_NEXT_ACTIONS.md", f"""# Next Actions — Hermes Harness
Last updated: {now}

## Current Next Action
{current_next}

## Queue
{na_sections}
""")

    handoff_activity = "\n".join([
        f"- {dict(a).get('source','—')} [{dict(a).get('activity_type','—')}] {dict(a).get('summary','—')}{' → ' + dict(a).get('verdict') if dict(a).get('verdict') else ''}"
        for a in activity[:5]
    ])
    round_section = ""
    if round_data:
        round_section = f"""
## Active / Recent Round
Topic: {round_data.get('topic','—')}
Status: {round_data.get('status','—')}

### Latest Hermes Synthesis
{round_data.get('hermes_response') or '— none yet —'}
"""
    write_file("07_RECENT_HANDOFF.md", f"""# HERMES HARNESS SESSION HANDOFF
Generated: {now}

## Purpose
Orient a cold Claude / ChatGPT / Hermes session. Do not re-explain decisions already made. Continue from this state.

## Current Focus
{status.get('current_focus') or '—'}

## Next Single Action
{status.get('next_single_action') or '—'}

## Status
{status.get('status') or '—'} — last updated by {status.get('updated_by') or '—'} at {status.get('updated_at') or '—'}

## Recent Decisions and Activity
{handoff_activity}
{round_section}
## Do Not
- Re-open decisions already marked complete.
- Rebuild infrastructure that is already verified.
- Ask Eric for context already present above.

## Continue Here
{status.get('next_single_action') or 'Check current status and confirm next action with Eric.'}

## Evidence
- Collab Tracker: http://127.0.0.1:5000/ui/infra
- Raw session logs: /home/eric/.hermes/sessions/
- Database: /mnt/projects/cis/runtime/cis_memory.db
- Project Context Pack: /mnt/projects/cis/PROJECT_CONTEXT_PACK/
""")

    if files_changed:
        fc_lines = "\n".join([
            f"- [{dict(f).get('action','')}] {dict(f).get('path','')} — {dict(f).get('notes','')} ({dict(f).get('related_task','')})"
            for f in files_changed
        ])
    else:
        fc_lines = "No files logged yet. Use POST /api/collab/files-changed to record changes."

    write_file("08_FILES_CHANGED_RECENTLY.md", f"""# Files Changed Recently — Hermes Harness
Last updated: {now}

{fc_lines}
""")

    return jsonify({
        "ok": True,
        "exported_at": now,
        "preview_path": preview_path,
        "files_written": files_written,
        "note": "Preview only — real HCP files not modified. Review generated files before approving replacement."
    })
