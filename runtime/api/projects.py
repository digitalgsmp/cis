"""
api/projects.py — Project CRUD endpoints.
Routes:
    GET  /api/projects
    POST /api/projects
    GET  /api/projects/<project_id>
"""

from flask import Blueprint, jsonify, request
from config import PROJECTS_DIR, WIAS_STAGES
from utils.helpers import ts, save_json
from utils.project_helpers import get_all_projects, get_project, compute_wias_progress

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/api/projects")
def api_projects():
    return jsonify(get_all_projects())


@projects_bp.route("/api/projects", methods=["POST"])
def api_create_project():
    data          = request.get_json()
    title         = data.get("title", "").strip()
    concept       = data.get("concept", "").strip()
    output_type   = data.get("intended_output_type", "").strip()
    scope         = data.get("project_scope", "minor")
    active_stages = data.get("active_stages", ["word"])

    if not title:
        return jsonify({"success": False, "error": "title is required"}), 400

    slug       = title.upper().replace(" ", "_").replace("-", "_")[:40]
    project_id = f"PROJECT__{slug}__V1"

    project = {
        "project_id":           project_id,
        "project_type":         data.get("project_type", "creative"),
        "title":                title,
        "working_title":        title,
        "created_at":           ts(),
        "updated_at":           ts(),
        "created_by":           "human",
        "status":               "active",
        "concept":              concept,
        "intended_output_type": output_type,
        "project_scope":        scope,
        "active_stages":        active_stages,
        "knowledge_links": {
            "record_ids":    [],
            "research_ids":  [],
            "reference_ids": [],
            "learning_ids":  [],
            "template_ids":  []
        },
        "version":    "v1",
        "is_current": True
    }

    project_dir = PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    save_json(project_dir / f"{project_id.lower()}.json", project)

    return jsonify({"success": True, "project_id": project_id, "project": project})


@projects_bp.route("/api/projects/<project_id>")
def api_project_detail(project_id):
    project, _ = get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    project["_wias_progress"] = compute_wias_progress(project_id, project)
    return jsonify(project)
