"""
api/tasks.py — Task management endpoints.
Routes:
    GET  /api/tasks
    POST /api/tasks
    POST /api/tasks/<id>/complete
    POST /api/tasks/<id>/run
"""

from flask import Blueprint, jsonify, request
from db.connection import db_connect, ensure_tables
from utils.helpers import ts, run_command

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/api/tasks")
def api_tasks_get():
    project_id = request.args.get("project_id")
    conn = db_connect()
    ensure_tables(conn)
    try:
        if project_id:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE project_id=? ORDER BY priority ASC, created_at ASC",
                (project_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY priority ASC, created_at ASC"
            ).fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@tasks_bp.route("/api/tasks", methods=["POST"])
def api_tasks_post():
    data       = request.get_json()
    title      = data.get("title", "").strip()
    desc       = data.get("description", "").strip()
    command    = data.get("command", "").strip() or None
    phase      = data.get("phase", "").strip() or None
    project_id = data.get("project_id", "").strip() or None
    priority   = int(data.get("priority", 5))

    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400

    conn = db_connect()
    ensure_tables(conn)
    try:
        conn.execute(
            "INSERT INTO tasks (title, description, command, phase, project_id, priority, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'open', ?)",
            (title, desc, command, phase, project_id, priority, ts())
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@tasks_bp.route("/api/tasks/<int:task_id>/complete", methods=["POST"])
def api_task_complete(task_id):
    conn = db_connect()
    ensure_tables(conn)
    try:
        conn.execute(
            "UPDATE tasks SET status='complete', completed_at=? WHERE id=?",
            (ts(), task_id)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@tasks_bp.route("/api/tasks/<int:task_id>/run", methods=["POST"])
def api_task_run(task_id):
    conn = db_connect()
    ensure_tables(conn)
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return jsonify({"success": False, "error": "Task not found"}), 404

        task = dict(row)
        if not task.get("command"):
            return jsonify({"success": False, "error": "No command defined for this task"}), 400

        result = run_command(task["command"])
        if result["success"]:
            conn.execute(
                "UPDATE tasks SET status='complete', completed_at=? WHERE id=?",
                (ts(), task_id)
            )
            conn.commit()
        return jsonify(result)
    finally:
        conn.close()
