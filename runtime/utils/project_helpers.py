"""
utils/project_helpers.py — Project data access and computation.
Functions that read/write project JSON files and derive project state.
"""

from config import PROJECTS_DIR, RECORDS_ROOT, WIAS_STAGES
from utils.helpers import load_json, save_json


def get_all_projects():
    """
    Scan the projects directory and return a list of all project dicts.
    Appends _record_count to each project indicating linked knowledge records.
    """
    projects = []
    if not PROJECTS_DIR.exists():
        return projects

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        for project_file in project_dir.glob("*.json"):
            try:
                p = load_json(project_file)
                record_count = 0
                for r in RECORDS_ROOT.rglob("*.json"):
                    try:
                        rec = load_json(r)
                        if rec.get("project_id") == p.get("project_id"):
                            record_count += 1
                    except Exception:
                        pass
                p["_record_count"] = record_count
                projects.append(p)
            except Exception:
                pass

    return projects


def get_project(project_id):
    """
    Find and return a single project by project_id.
    Returns (project_dict, project_file_path) or (None, None) if not found.
    """
    if not PROJECTS_DIR.exists():
        return None, None

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for project_file in project_dir.glob("*.json"):
            try:
                p = load_json(project_file)
                if p.get("project_id") == project_id:
                    return p, project_file
            except Exception:
                pass

    return None, None


def compute_wias_progress(project_id, project):
    """
    Compute WIAS stage progress scores for a project.
    Scores: 0=inactive, 1=active, 2=draft records, 3=checked records, 4=approved/locked records.
    Returns a dict keyed by stage name.
    """
    active_stages = [s.lower() for s in project.get("active_stages", [])]
    progress = {s: 0 for s in WIAS_STAGES}

    for stage in active_stages:
        if stage in progress:
            progress[stage] = max(progress[stage], 1)

    if not RECORDS_ROOT.exists():
        return progress

    for record_dir in RECORDS_ROOT.iterdir():
        if not record_dir.is_dir():
            continue
        for record_file in record_dir.glob("*.json"):
            try:
                rec = load_json(record_file)
                if rec.get("project_id") != project_id:
                    continue
                status = rec.get("status", "")
                for stage in (rec.get("active_stages") or []):
                    stage = stage.lower()
                    if stage not in progress:
                        continue
                    if status == "draft":
                        progress[stage] = max(progress[stage], 2)
                    elif status == "checked":
                        progress[stage] = max(progress[stage], 3)
                    elif status in ("approved", "locked"):
                        progress[stage] = max(progress[stage], 4)
            except Exception:
                pass

    return progress
