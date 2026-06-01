"""
api/collab.py — Collab Tracker API.
Routes for agent status, current focus, and activity log.
"""

from flask import Blueprint, jsonify, request
from db.connection import db_connect
from utils.helpers import ts

collab_bp = Blueprint("collab", __name__)


def ensure_collab_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'waiting',
            last_activity_summary TEXT DEFAULT '',
            last_active TEXT DEFAULT '',
            updated_by TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_status (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_focus TEXT DEFAULT '',
            next_single_action TEXT DEFAULT '',
            blocked_waiting TEXT DEFAULT '',
            status TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            updated_by TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            verdict TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            related_task TEXT DEFAULT ''
        )
    """)
    conn.commit()

    existing = conn.execute("SELECT COUNT(*) FROM collab_agents").fetchone()[0]
    if existing == 0:
        now = ts()
        for name, role in [
            ("Eric", "Architect"),
            ("Hermes", "Executor"),
            ("Claude", "Planner / Verifier"),
            ("ChatGPT", "Auditor / Verifier"),
            ("DeepSeek", "Reasoning Model"),
        ]:
            conn.execute(
                "INSERT INTO collab_agents (name, role, status, last_active) VALUES (?,?,?,?)",
                (name, role, "active", now)
            )
        conn.execute("""
            INSERT OR IGNORE INTO collab_status (id, current_focus, next_single_action, status, updated_at, updated_by)
            VALUES (1, 'Build Collab Tracker as visual harness control surface',
            'Implement minimal database-backed Collab Tracker', 'in_progress', ?, 'Claude')
        """, (now,))
        for source, activity_type, summary in [
            ("Eric", "action", "Created Hermes harness review packet"),
            ("Claude", "recommendation", "Proposed Collab Tracker scope"),
            ("ChatGPT", "decision", "Approved expanded first feature slice"),
        ]:
            conn.execute(
                "INSERT INTO collab_activity (source, activity_type, summary, created_at) VALUES (?,?,?,?)",
                (source, activity_type, summary, now)
            )
        conn.commit()


def ensure_extended_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            decision TEXT NOT NULL,
            reason TEXT DEFAULT '',
            status TEXT DEFAULT 'DECIDED',
            evidence TEXT DEFAULT '',
            related_round_id INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            UNIQUE(date, decision)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_open_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'OPEN',
            related_round_id INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_next_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            priority INTEGER DEFAULT 0,
            title TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            related_task TEXT DEFAULT '',
            related_round_id INTEGER DEFAULT NULL,
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS collab_files_changed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            action TEXT NOT NULL,
            related_task TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            UNIQUE(path, action, related_task)
        )
    """)
    conn.commit()

    now = ts()

    decisions = [
        ("2026-05-17", "Restore backup config as functional baseline", "Minimal config stripped MCP servers", "COMPLETE", "HHR-002"),
        ("2026-05-17", "Set deepseek-v4-pro as default model", "Better reasoning for complex collaboration work", "COMPLETE", "config.yaml verified"),
        ("2026-05-17", "Use Collab Tracker as screenshot state surface", "Replaces document copy-paste for model updates", "COMPLETE", "HHR-006B"),
        ("2026-05-17", "Enable Hermes Gateway API via env var not config file", "Cleaner than config section, auto-starts", "COMPLETE", "HHR-011A"),
        ("2026-05-17", "Wizard as overlay drawer not inline sidebar", "Preserves briefing layout for screenshots", "COMPLETE", "HHR-011C"),
        ("2026-05-17", "Auto-import session after wizard send", "Closes capture loop without manual step", "COMPLETE", "HHR-012"),
        ("2026-05-17", "Option B for follow-up with Eric addendum", "Reduces mental logistics, preserves steering", "COMPLETE", "HHR-012"),
        ("2026-05-17", "Handoffs are transitory not archival", "Long-term value belongs in VDB", "DECIDED", "This session"),
        ("2026-05-17", "Project Context Pack Hermes Harness scope only", "CIS is separate project", "DECIDED", "This session"),
        ("2026-05-17", "Direct Claude/ChatGPT API routing deferred", "Expected cost and complexity", "DECIDED", "This session"),
        ("2026-05-17", "DeepSeek as right-hand collaborator", "Role separation matches model strengths", "DECIDED", "This session"),
        ("2026-05-17", "SQLite as single source of truth", "Eliminates split-brain state between DB and markdown", "DECIDED", "HHR-014"),
    ]
    for d in decisions:
        conn.execute(
            "INSERT OR IGNORE INTO collab_decisions (date, decision, reason, status, evidence, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (d[0], d[1], d[2], d[3], d[4], now, now)
        )

    questions = [
        ("OQ-001", "Hermes Gateway API timeout", "urllib timeout was 120s in collab_rounds.py. Raised to 300s.", "RESOLVED"),
        ("OQ-002", "Flask API_SERVER_KEY startup", "Fixed via /home/eric/.config/cis-flask.env and systemd EnvironmentFile.", "RESOLVED"),
        ("OQ-003", "VDB pipeline rebuild", "Previous attempt failed — extraction operated on summaries not raw text. Correct approach: chunk collab_session_messages.content with message_index as citation anchor.", "OPEN"),
        ("OQ-004", "Project Context Pack update trigger", "What constitutes a significant task that triggers a pack update? Needs clear rule.", "OPEN"),
        ("OQ-005", "Hermes TUI copy/paste", "Ctrl+Shift+C does not work. /paste slash command may be correct path.", "OPEN"),
        ("OQ-006", "HHR-013 Handoff Endpoint Design", "Implemented and verified. GET /api/collab/handoff live.", "RESOLVED"),
        ("OQ-007", "Synthesis Step Fortification", "Approved design: async job + polling (HHR-016). Current workaround: timeout=300.", "DESIGNED, NOT YET BUILT"),
        ("OQ-008", "Split-brain state between SQLite and Project Context Pack", "Fixed by making SQLite single source of truth and HCP an export. HHR-014 implements this.", "IN PROGRESS"),
    ]
    for q in questions:
        conn.execute(
            "INSERT OR IGNORE INTO collab_open_questions (code, title, description, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (q[0], q[1], q[2], q[3], now, now)
        )

    actions = [
        (1, "HHR-014A: Fix Flask service environment", "Add API_SERVER_KEY to systemd service via cis-flask.env", "complete", "HHR-014A"),
        (2, "HHR-014B: Add structured state tables", "Add collab_decisions, open_questions, next_actions, files_changed tables", "in_progress", "HHR-014B"),
        (3, "HHR-014C: Context Pack exporter", "Add export endpoint that generates HCP files from SQLite", "pending", "HHR-014C"),
        (4, "HHR-015: Final Directive capture", "Add task ticket step to Advisor Round Wizard", "pending", "HHR-015"),
        (5, "HHR-016: Recoverable synthesis jobs", "Async job + polling for Hermes Gateway synthesis requests", "pending", "HHR-016"),
        (6, "HHR-017: VDB pipeline rebuild", "Chunk collab_session_messages with message_index as citation anchor", "pending", "HHR-017"),
    ]
    for a in actions:
        conn.execute(
            "INSERT OR IGNORE INTO collab_next_actions (priority, title, description, status, related_task, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (a[0], a[1], a[2], a[3], a[4], now, now)
        )

    conn.commit()


# ── Core routes ──────────────────────────────────────────────────────────

@collab_bp.route("/api/collab/agents")
def get_agents():
    conn = db_connect()
    ensure_collab_tables(conn)
    rows = conn.execute("SELECT * FROM collab_agents ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@collab_bp.route("/api/collab/agents/<int:agent_id>", methods=["PATCH"])
def update_agent(agent_id):
    data = request.json
    conn = db_connect()
    ensure_collab_tables(conn)
    fields, values = [], []
    for key in ("status", "last_activity_summary", "updated_by"):
        if key in data:
            fields.append(f"{key}=?")
            values.append(data[key])
    fields.append("last_active=?")
    values.append(ts())
    values.append(agent_id)
    conn.execute(f"UPDATE collab_agents SET {', '.join(fields)} WHERE id=?", values)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/status")
def get_status():
    conn = db_connect()
    ensure_collab_tables(conn)
    row = conn.execute("SELECT * FROM collab_status WHERE id=1").fetchone()
    conn.close()
    return jsonify(dict(row) if row else {})


@collab_bp.route("/api/collab/status", methods=["PATCH"])
def update_status():
    data = request.json
    conn = db_connect()
    ensure_collab_tables(conn)
    fields, values = [], []
    for key in ("current_focus", "next_single_action", "blocked_waiting", "status", "updated_by"):
        if key in data:
            fields.append(f"{key}=?")
            values.append(data[key])
    fields.append("updated_at=?")
    values.append(ts())
    conn.execute(f"UPDATE collab_status SET {', '.join(fields)} WHERE id=1", values)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/activity")
def get_activity():
    conn = db_connect()
    ensure_collab_tables(conn)
    rows = conn.execute("SELECT * FROM collab_activity ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@collab_bp.route("/api/collab/activity", methods=["POST"])
def post_activity():
    data = request.json
    conn = db_connect()
    ensure_collab_tables(conn)
    conn.execute(
        "INSERT INTO collab_activity (source, activity_type, summary, verdict, created_at, related_task) VALUES (?,?,?,?,?,?)",
        (data.get("source",""), data.get("activity_type",""), data.get("summary",""),
         data.get("verdict",""), ts(), data.get("related_task",""))
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ── Extended state routes ────────────────────────────────────────────────

@collab_bp.route("/api/collab/decisions")
def get_decisions():
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        rows = conn.execute("SELECT * FROM collab_decisions ORDER BY id").fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@collab_bp.route("/api/collab/decisions", methods=["POST"])
def add_decision():
    data = request.json or {}
    if not data.get("decision"):
        return jsonify({"ok": False, "error": "decision required"}), 400
    now = ts()
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        conn.execute(
            "INSERT OR IGNORE INTO collab_decisions (date, decision, reason, status, evidence, related_round_id, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (data.get("date", now[:10]), data.get("decision",""), data.get("reason",""),
             data.get("status","DECIDED"), data.get("evidence",""),
             data.get("related_round_id"), now, now)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/open-questions")
def get_open_questions():
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        rows = conn.execute("SELECT * FROM collab_open_questions ORDER BY id").fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@collab_bp.route("/api/collab/open-questions", methods=["POST"])
def add_open_question():
    data = request.json or {}
    if not data.get("code") or not data.get("title"):
        return jsonify({"ok": False, "error": "code and title required"}), 400
    now = ts()
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        conn.execute(
            "INSERT OR IGNORE INTO collab_open_questions (code, title, description, status, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (data.get("code",""), data.get("title",""), data.get("description",""),
             data.get("status","OPEN"), now, now)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/open-questions/<int:qid>", methods=["PATCH"])
def update_open_question(qid):
    data = request.json or {}
    now = ts()
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        fields, values = [], []
        for key in ("title", "description", "status"):
            if key in data:
                fields.append(f"{key}=?")
                values.append(data[key])
        if not fields:
            return jsonify({"ok": False, "error": "no fields to update"}), 400
        fields.append("updated_at=?")
        values.append(now)
        values.append(qid)
        conn.execute(f"UPDATE collab_open_questions SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/next-actions")
def get_next_actions():
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        rows = conn.execute("SELECT * FROM collab_next_actions ORDER BY priority").fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@collab_bp.route("/api/collab/next-actions", methods=["POST"])
def add_next_action():
    data = request.json or {}
    if not data.get("title"):
        return jsonify({"ok": False, "error": "title required"}), 400
    now = ts()
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        conn.execute(
            "INSERT OR IGNORE INTO collab_next_actions (priority, title, description, status, related_task, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (data.get("priority", 0), data.get("title",""), data.get("description",""),
             data.get("status","pending"), data.get("related_task",""), now, now)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/next-actions/<int:aid>", methods=["PATCH"])
def update_next_action(aid):
    data = request.json or {}
    now = ts()
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        fields, values = [], []
        for key in ("title", "description", "status", "priority", "related_task"):
            if key in data:
                fields.append(f"{key}=?")
                values.append(data[key])
        if not fields:
            return jsonify({"ok": False, "error": "no fields to update"}), 400
        fields.append("updated_at=?")
        values.append(now)
        values.append(aid)
        conn.execute(f"UPDATE collab_next_actions SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


@collab_bp.route("/api/collab/files-changed")
def get_files_changed():
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        rows = conn.execute("SELECT * FROM collab_files_changed ORDER BY id DESC LIMIT 30").fetchall()
    finally:
        conn.close()
    return jsonify([dict(r) for r in rows])


@collab_bp.route("/api/collab/files-changed", methods=["POST"])
def add_file_changed():
    data = request.json or {}
    if not data.get("path") or not data.get("action"):
        return jsonify({"ok": False, "error": "path and action required"}), 400
    now = ts()
    conn = db_connect()
    try:
        ensure_extended_tables(conn)
        conn.execute(
            "INSERT OR IGNORE INTO collab_files_changed (path, action, related_task, notes, created_at) VALUES (?,?,?,?,?)",
            (data.get("path",""), data.get("action",""),
             data.get("related_task",""), data.get("notes",""), now)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})
