"""
api/import_session.py — One-shot session JSON importer.

Usage:
    cd /mnt/projects/cis/runtime
    python3 -m api.import_session /path/to/session.json

Creates collab_session_imports and collab_session_messages tables,
imports the session file, deduplicates by (source_path, session_id).
"""

import json
import sys
import os

from db.connection import db_connect
from utils.helpers import ts


def ensure_session_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS collab_session_imports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path     TEXT NOT NULL,
            session_id      TEXT NOT NULL,
            session_start   TEXT NOT NULL,
            session_end     TEXT NOT NULL,
            model           TEXT DEFAULT '',
            base_url        TEXT DEFAULT '',
            platform        TEXT DEFAULT '',
            message_count   INTEGER DEFAULT 0,
            imported_at     TEXT DEFAULT '',
            UNIQUE(source_path, session_id)
        );

        CREATE TABLE IF NOT EXISTS collab_session_messages (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id         INTEGER NOT NULL REFERENCES collab_session_imports(id),
            message_index     INTEGER NOT NULL,
            role              TEXT NOT NULL,
            content           TEXT NOT NULL,
            name              TEXT DEFAULT '',
            tool_call_id      TEXT DEFAULT '',
            finish_reason     TEXT DEFAULT '',
            has_tool_calls    INTEGER DEFAULT 0,
            tool_calls_json   TEXT DEFAULT '',
            reasoning         TEXT DEFAULT '',
            reasoning_content TEXT DEFAULT '',
            UNIQUE(import_id, message_index)
        );
    """)
    conn.commit()


def import_session(file_path):
    file_path = os.path.abspath(file_path)

    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    session_id = data.get("session_id", "unknown")
    session_start = data.get("session_start", "")
    session_end = data.get("last_updated", "")
    model = data.get("model", "")
    base_url = data.get("base_url", "")
    platform = data.get("platform", "")
    messages = data.get("messages", [])
    message_count = data.get("message_count", len(messages))

    conn = db_connect()
    ensure_session_tables(conn)

    # Check for duplicate
    existing = conn.execute(
        "SELECT id FROM collab_session_imports WHERE source_path=? AND session_id=?",
        (file_path, session_id)
    ).fetchone()

    if existing:
        print(f"Session already imported, skipped")
        conn.close()
        return

    # Insert import record
    now = ts()
    conn.execute(
        """INSERT INTO collab_session_imports
           (source_path, session_id, session_start, session_end, model, base_url, platform, message_count, imported_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_path, session_id, session_start, session_end, model, base_url, platform, message_count, now)
    )
    import_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert messages
    inserted = 0
    for idx, msg in enumerate(messages):
        role = msg.get("role", "")
        content = msg.get("content", "")

        # If content is a list (multimodal / image blocks), serialize to JSON string
        if isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)

        name = msg.get("name", "")
        tool_call_id = msg.get("tool_call_id", "")
        finish_reason = msg.get("finish_reason", "")
        tool_calls = msg.get("tool_calls", None)
        has_tool_calls = 1 if tool_calls else 0
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else ""
        reasoning = msg.get("reasoning", "")
        reasoning_content = msg.get("reasoning_content", "")

        conn.execute(
            """INSERT INTO collab_session_messages
               (import_id, message_index, role, content, name, tool_call_id,
                finish_reason, has_tool_calls, tool_calls_json, reasoning, reasoning_content)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (import_id, idx, role, content, name, tool_call_id,
             finish_reason, has_tool_calls, tool_calls_json, reasoning, reasoning_content)
        )
        inserted += 1

    conn.commit()
    conn.close()

    print(f"Imported {inserted} messages from session {session_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m api.import_session <session.json>")
        sys.exit(1)
    import_session(sys.argv[1])
