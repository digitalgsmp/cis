"""
api/spines.py — Knowledge spine endpoints for extraction topology data.
Routes:
    GET  /api/spines              — all spines, with node counts
    GET  /api/spines/<spine_id>   — single spine with all nodes
    GET  /api/spines/by-project/<project>  — spines for a project (cis/swa)
"""

from flask import Blueprint, jsonify
from db.connection import db_connect

spines_bp = Blueprint("spines", __name__)


def row_to_dict(row):
    """Convert sqlite3.Row to dict."""
    return dict(row)


@spines_bp.route("/api/spines", methods=["GET"])
def api_spines_list():
    """Return all knowledge spines with node counts."""
    conn = db_connect()
    try:
        spines = conn.execute(
            "SELECT * FROM knowledge_spines ORDER BY domain, sub_domain, subject"
        ).fetchall()
        result = [row_to_dict(s) for s in spines]
        return jsonify({"success": True, "spines": result, "count": len(result)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@spines_bp.route("/api/spines/<spine_id>", methods=["GET"])
def api_spine_detail(spine_id):
    """Return a single spine with all its nodes."""
    conn = db_connect()
    try:
        spine = conn.execute(
            "SELECT * FROM knowledge_spines WHERE spine_id=?", (spine_id,)
        ).fetchone()
        if not spine:
            return jsonify({"success": False, "error": "Spine not found"}), 404

        nodes = conn.execute(
            "SELECT * FROM spine_nodes WHERE spine_id=? ORDER BY depth, node_id",
            (spine_id,)
        ).fetchall()

        spine_dict = row_to_dict(spine)
        spine_dict["nodes"] = [row_to_dict(n) for n in nodes]
        return jsonify({"success": True, "spine": spine_dict})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()


@spines_bp.route("/api/spines/by-project/<project>", methods=["GET"])
def api_spines_by_project(project):
    """Return all spines for a project (cis/swa) with their nodes."""
    domain = project.upper()
    conn = db_connect()
    try:
        spines = conn.execute(
            "SELECT * FROM knowledge_spines WHERE domain=? ORDER BY sub_domain, subject",
            (domain,)
        ).fetchall()

        result = []
        for s in spines:
            spine_dict = row_to_dict(s)
            nodes = conn.execute(
                "SELECT * FROM spine_nodes WHERE spine_id=? ORDER BY depth, node_id",
                (s["spine_id"],)
            ).fetchall()
            spine_dict["nodes"] = [row_to_dict(n) for n in nodes]
            result.append(spine_dict)

        return jsonify({"success": True, "project": project, "spines": result, "count": len(result)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        conn.close()
