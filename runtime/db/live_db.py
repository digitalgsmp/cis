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
    Serialize only the current active (open) session to markdown.
    ADR-021: CIS_LIVE broadcasts active session only.
    """
    conn = live_db()
    try:
        session = conn.execute(
            "SELECT * FROM live_sessions WHERE status='open' ORDER BY id DESC LIMIT 1"
        ).fetchone()

        lines = [
            "# CIS_LIVE — Active Scratchpad",
            "Format: Bullets | 15 lines max | Newest first | Ends with ACTION",
            ""
        ]

        if not session:
            lines.append("_No active session._")
            return "\n".join(lines)

        s = dict(session)
        lines += [
            f"## {s['topic']} — {s['created_at'][:16]} [OPEN]",
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

        lines += ["---", ""]
        return "\n".join(lines)
    finally:
        conn.close()


def get_raw_url():
    """
    Derive the raw GitHub URL for CIS_LIVE.md from the vault git remote.
    Returns None if the remote cannot be determined.
    """
    try:
        r = subprocess.run(
            "git remote get-url origin",
            shell=True, capture_output=True, text=True, cwd=str(VAULT_DIR)
        )
        remote = r.stdout.strip()
        if "github.com" in remote:
            remote = remote.replace("git@github.com:", "https://github.com/")
            remote = remote.replace(".git", "")
            remote = remote.replace("https://github.com/", "https://raw.githubusercontent.com/")
            return f"{remote}/main/CIS_LIVE.md"
    except Exception:
        pass
    return None
