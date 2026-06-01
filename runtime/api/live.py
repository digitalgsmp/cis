"""
api/live.py — CIS_LIVE scratchpad endpoints.
Routes:
    GET  /api/live/sessions
    POST /api/live/sessions
    POST /api/live/sessions/<sid>/rounds
    POST /api/live/sessions/<sid>/resolve
    POST /api/live/push
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from config import LIVE_PATH, VAULT_DIR
from db.connection import db_connect, ensure_tables
from db.live_db import live_db, serialize_to_md, get_raw_url
from utils.helpers import run_command

live_bp = Blueprint("live", __name__)


@live_bp.route("/api/live/sessions", methods=["GET"])
def api_live_sessions_get():
    conn = live_db()
    try:
        sessions = conn.execute("SELECT * FROM live_sessions ORDER BY id DESC").fetchall()
        result = []
        for s in sessions:
            rounds = conn.execute(
                "SELECT * FROM live_rounds WHERE session_id=? ORDER BY round_number",
                (s["id"],)
            ).fetchall()
            result.append({"session": dict(s), "rounds": [dict(r) for r in rounds]})
        return jsonify(result)
    finally:
        conn.close()


@live_bp.route("/api/live/sessions", methods=["POST"])
def api_live_sessions_post():
    data    = request.get_json()
    topic   = data.get("topic", "").strip()
    problem = data.get("problem", "").strip()

    if not topic or not problem:
        return jsonify({"success": False, "error": "topic and problem required"}), 400

    conn = live_db()
    try:
        cur = conn.execute(
            "INSERT INTO live_sessions (topic, problem, tags, project_id, status, created_at) "
            "VALUES (?, ?, ?, ?, 'open', datetime('now'))",
            (topic, problem, data.get("tags", "").strip(), data.get("project_id") or None)
        )
        conn.commit()
        return jsonify({"success": True, "session_id": cur.lastrowid})
    finally:
        conn.close()


@live_bp.route("/api/live/sessions/<int:sid>/rounds", methods=["POST"])
def api_live_rounds_post(sid):
    data = request.get_json()
    conn = live_db()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM live_rounds WHERE session_id=?", (sid,)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO live_rounds "
            "(session_id, round_number, your_message, consolidated, "
            "gemini, claude, chatgpt, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (
                sid, count + 1,
                data.get("your_message", "").strip() or None,
                data.get("consolidated", "").strip() or None,
                data.get("gemini", "").strip() or None,
                data.get("claude", "").strip() or None,
                data.get("chatgpt", "").strip() or None
            )
        )
        conn.commit()
        return jsonify({"success": True, "round_number": count + 1})
    finally:
        conn.close()


@live_bp.route("/api/live/sessions/<int:sid>/resolve", methods=["POST"])
def api_live_resolve(sid):
    data       = request.get_json()
    solution   = data.get("solution", "").strip()
    decided_by = data.get("decided_by", "").strip()

    conn = live_db()
    # Also need captures table
    ensure_tables(conn)
    try:
        conn.execute(
            "UPDATE live_sessions SET status='resolved', solution=?, decided_by=?, "
            "resolved_at=datetime('now') WHERE id=?",
            (solution, decided_by, sid)
        )
        s = conn.execute("SELECT * FROM live_sessions WHERE id=?", (sid,)).fetchone()
        if s:
            s = dict(s)
            conn.execute(
                "INSERT INTO captures (capture_type, title, observation, project_id, created_at) "
                "VALUES (?, ?, ?, ?, datetime('now'))",
                (
                    "solution",
                    s["topic"],
                    f"Problem: {s['problem']}\n\nSolution: {solution}\n\nDecided by: {decided_by}",
                    s["project_id"]
                )
            )
        conn.commit()
        return jsonify({"success": True})
    finally:
        conn.close()


@live_bp.route("/api/live/push", methods=["POST"])
def api_live_push():
    """
    Push CIS_LIVE.md to all targets:
    1. Local LIVE_PATH (/mnt/projects/cis/CIS_LIVE.md)
    2. Vault copy + git commit/push (GitHub)
    3. SCP to Proxmox host → LXC bind mount → creative-intelligence-system.com
    """
    step_log = []
    try:
        md = serialize_to_md()

        # ── Step 1: Write local copy ──────────────────────────────────────────
        try:
            LIVE_PATH.write_text(md, encoding="utf-8")
            step_log.append("✓ Local CIS_LIVE.md written")
        except Exception as e:
            step_log.append(f"✗ Local write failed: {e}")

        # ── Step 2: Write vault copy + git push ───────────────────────────────
        git_ok = False
        try:
            vault_live = VAULT_DIR / "CIS_LIVE.md"
            vault_live.write_text(md, encoding="utf-8")
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            cmd = (
                f"cd {VAULT_DIR} && git add CIS_LIVE.md && "
                f"git commit -m 'CIS_LIVE {timestamp}' && git push"
            )
            result = run_command(cmd, timeout=30)
            if result["success"] or "nothing to commit" in result["stdout"] + result["stderr"]:
                git_ok = True
                step_log.append("✓ Git committed and pushed")
            else:
                step_log.append(f"✗ Git push failed: {result['stderr']}")
        except Exception as e:
            step_log.append(f"✗ Vault/git error: {e}")

        # ── Step 3: SCP to Proxmox → public endpoint ──────────────────────────
        scp_ok = False
        try:
            import tempfile, os
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.md', delete=False, encoding='utf-8'
            ) as tmp:
                tmp.write(md)
                tmp_path = tmp.name

            scp_cmd = (
                f"scp -i /home/eric/.ssh/cis_proxmox "
                f"-o StrictHostKeyChecking=no "
                f"{tmp_path} "
                f"root@192.168.1.200:/mnt/cis-live/CIS_LIVE.md"
            )
            scp_result = run_command(scp_cmd, timeout=30)
            os.unlink(tmp_path)

            if scp_result["success"]:
                scp_ok = True
                step_log.append("✓ SCP to Proxmox succeeded → creative-intelligence-system.com updated")
            else:
                step_log.append(f"✗ SCP failed: {scp_result['stderr']}")
        except Exception as e:
            step_log.append(f"✗ SCP error: {e}")

        return jsonify({
            "success": True,
            "synced":  scp_ok,
            "git_ok":  git_ok,
            "live_url": get_raw_url(),
            "step_log": step_log
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "step_log": step_log}), 500
