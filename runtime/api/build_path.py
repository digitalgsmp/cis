"""
api/build_path.py — Workbench "Build Path" visualization backend
(WB.1 read-only build-path Mermaid card).

Read-only HTTP surface over tools/state/build_path.py. Narrowly scoped on
purpose: exactly one GET route, no query parameters, no caller-supplied
database path (that would let a client point the Workbench at an arbitrary
file on disk), and no write path of any kind. The read model underneath
opens the spine with sqlite3's mode=ro URI, so even a bug here cannot
mutate project state.

Why its own blueprint rather than a route added to system_context_bp: that
module's contract is "the canonical state + recovery packet", and its
docstring states both of its routes. A separate blueprint keeps this
feature's surface visible as exactly one added route in
runtime/container_app.py's url_map.

Self-contained like api/system_context.py: no legacy runtime/api/*
blueprint, config or db module is imported, so this works inside the
cis-pipeline container exactly as it does on the host.

Route:
    GET /api/workbench/build-path
        The normalized P0..P6 build-path read model: phase sequence parsed
        from project_state.pipeline_roadmap, current/next pointers, phase
        display statuses, migration unlock points, queue hooks, blockers
        from the discovery ledger, the external-developer checkpoint, the
        governing ADR rows, and generated Mermaid diagram source.

Failure behavior: a failure inside the read model (unreachable spine,
unparsable roadmap row) is returned as a 503 with an `error` field naming
the exception type — never a 500 traceback, and never a fabricated 200
with plausible-looking phases in it. The frontend shows that error instead
of a diagram.
"""
import sys
from pathlib import Path

from flask import Blueprint, jsonify

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import build_path as bp  # noqa: E402

build_path_bp = Blueprint("build_path", __name__)


@build_path_bp.route("/api/workbench/build-path", methods=["GET"])
def get_build_path():
    try:
        model = bp.get_build_path()
    except Exception as e:  # noqa: BLE001 -- must not turn into a 500 for the Workbench screen
        return jsonify({
            "error": f"build path read model unavailable: {type(e).__name__}: {e}",
        }), 503
    return jsonify(model)
