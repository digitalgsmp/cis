"""
db/live_db.py — CIS_LIVE session database connection and markdown serialiser.
Separate from the main DB to keep live scratchpad concerns isolated.
"""

import sqlite3
import subprocess
from config import DB_PATH, VAULT_DIR


def live_db():
    """
    Open a connection to the CIS memory database and ensure live session tables exist.
    Returns an open sqlite3 connection with row_factory set.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            topic      TEXT NOT NULL,
            problem    TEXT NOT NULL,
            tags       TEXT,
            project_id TEXT,
            status     TEXT DEFAULT 'open',
            solution   TEXT,
            decided_by TEXT,
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_rounds (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id    INTEGER NOT NULL,
            round_number  INTEGER NOT NULL,
            your_message  TEXT,
            consolidated  TEXT,
            gemini        TEXT,
            claude        TEXT,
            chatgpt       TEXT,
            created_at    TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def serialize_to_md():
    """
    Read all live sessions and rounds from the DB and return a formatted markdown string.
    Used by the push endpoint to write CIS_LIVE.md.
    Sessions are numbered newest-first. Empty rounds (no content) are skipped.
    """
    conn = live_db()
    try:
        sessions = conn.execute("SELECT * FROM live_sessions ORDER BY id DESC").fetchall()
        total = len(sessions)
        lines = [
            "# CIS_LIVE — Active Scratchpad",
            "Format: Bullets | 15 lines max | Newest first | Ends with ACTION",
            ""
        ]
        for idx, s in enumerate(sessions):
            s = dict(s)
            session_num = total - idx  # newest = highest number
            lines += [
                f"## {session_num:03d} · {s['topic']} — {s['created_at'][:16]} [{s['status'].upper()}]",
                f"Problem: {s['problem']}"
            ]
            if s.get("tags"):
                lines.append(f"Tags: {s['tags']}")
            lines.append("")

            rounds = conn.execute(
                "SELECT * FROM live_rounds WHERE session_id=? ORDER BY round_number",
                (s["id"],)
            ).fetchall()

            for r in rounds:
                r = dict(r)
                # Skip completely empty rounds
                has_content = any([
                    r.get("your_message"), r.get("consolidated"),
                    r.get("gemini"), r.get("claude"), r.get("chatgpt")
                ])
                if not has_content:
                    continue

                lines.append(f"### Round {r['round_number']} — {r['created_at'][:16]}")
                if r.get("your_message"):
                    lines += [f"[YOU]: {r['your_message']}", ""]
                if r.get("consolidated"):
                    lines += [f"[RESPONSES]: {r['consolidated']}", ""]
                if r.get("gemini"):
                    lines += [f"[Gemini]: {r['gemini']}", ""]
                if r.get("claude"):
                    lines += [f"[Claude]: {r['claude']}", ""]
                if r.get("chatgpt"):
                    lines += [f"[ChatGPT]: {r['chatgpt']}", ""]

            if s.get("solution"):
                lines += [
                    f"Solution: {s['solution']}",
                    f"Decided by: {s['decided_by']}",
                    "STATUS: resolved"
                ]
            lines += ["---", ""]

        return "\n".join(lines)
    finally:
        conn.close()


def get_raw_url():
    """
    Return the public Cloudflare static URL for CIS_LIVE.md.
    This is served via Cloudflare tunnel from the vault directory.
    """
    return "https://creative-intelligence-system.com/CIS_LIVE.md"
