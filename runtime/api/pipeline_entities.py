"""
api/pipeline_entities.py — Workbench Pipeline Entities backend.

Read-only HTTP surface over tools/state/pipeline_entities.py. One GET route:

    GET /api/workbench/pipeline-entities
        {
          "read_model": "cis_pipeline_entities",
          "chatbot": {...},      # the braingate_conversation capability,
                                  # backend_role=brain, NOT a seventh role
          "roles": [...],        # exactly the six canonical PROFILES roles
          "procedures": {...},   # PHASE_GATE_MAP stages + SECURITY_GATES
          "activity": {...},     # the shared newest-20-run cohort
        }

Narrowly scoped exactly like api/portfolio.py and api/project_intelligence.py:
one GET route, no query parameters, no caller-supplied database/repo path,
and no write path of any kind.

Failure behavior: a failure inside the read model is returned as a 503 with
an `error` field naming the exception type — never a 500 traceback.
"""
import sys
from pathlib import Path

from flask import Blueprint, jsonify

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import pipeline_entities as pe  # noqa: E402

_RUNTIME_DIR = Path(__file__).resolve().parents[1]
if str(_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_DIR))

from workbench_auth import check_auth  # noqa: E402

pipeline_entities_bp = Blueprint("pipeline_entities", __name__)


@pipeline_entities_bp.route("/api/workbench/pipeline-entities", methods=["GET"])
def get_pipeline_entities():
    auth_err = check_auth()
    if auth_err:
        return auth_err

    try:
        model = pe.get_pipeline_entities()
    except Exception as e:  # noqa: BLE001 -- must not turn into a 500 for the Workbench screen
        return jsonify({
            "error": f"pipeline entities model unavailable: {type(e).__name__}: {e}",
        }), 503
    return jsonify(model)
