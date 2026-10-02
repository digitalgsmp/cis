"""
api/project_intelligence.py — Workbench "Project Map" backend
(Workbench Project Map card).

Read-only HTTP surface over tools/state/project_intelligence.py. Narrowly
scoped exactly like api/build_path.py and api/destination_architecture.py: one
GET route, no query parameters, no caller-supplied database path (that would
let a client point the Workbench at an arbitrary file on disk), and no write
path of any kind. The read model underneath opens the spine with sqlite3's
mode=ro URI, so even a bug here cannot mutate project state.

Why its own blueprint rather than a route on build_path_bp: that blueprint's
subject is the P0–P6 build sequence, and destination_architecture_bp's subject
is the WIASW destination. This one's subject is neither — it is the
EXPLANATORY LAYER ACROSS them, and it composes both by calling their read
models. Keeping it at its own blueprint keeps this feature's surface visible as
exactly one added route in runtime/container_app.py's url_map, and keeps the
two existing screens' routes untouched.

Self-contained like api/build_path.py and api/system_context.py: no legacy
runtime/api/* blueprint, config or db module is imported, so this works inside
the cis-pipeline container exactly as it does on the host.

Route:
    GET /api/workbench/project-intelligence
        The composed project-intelligence read model: the five conceptual
        areas, the reviewed plain-language glossary, the composed Build Path
        payload, a reference projection of the composed destination graph, the
        derived capability view with its provenance stated, the system-anatomy
        areas, the discovery ledger as plain-language problems, the queue
        inventory with every untriaged row marked AWAITING TRIAGE, the
        trajectory with its destination relationship explicitly marked as not
        a phase ordering, and every cross-view relationship carrying a
        confidence_class of authoritative / derived_from_evidence /
        not_yet_linked.

NO MODEL IS CALLED HERE OR BELOW HERE. The response is assembled from database
rows, files on disk and a reviewed static vocabulary file in the repository.
Nothing in this request path imports a model client or performs network access,
so the explanations the browser renders cannot have been generated ad hoc at
page-load time.

Failure behavior: a failure inside the read model (unreachable spine,
unreadable vocabulary) is returned as a 503 with an `error` field naming the
exception type — never a 500 traceback, and never a fabricated 200 with a
plausible-looking map in it. A COMPOSED read model that fails on its own is a
different matter and is deliberately not a 503: the area reports
available:false with its error, and the rest of the map still loads, because
"the destination view is unavailable" and "the Project Map is unavailable" are
different answers.
"""
import sys
from pathlib import Path

from flask import Blueprint, jsonify

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import project_intelligence as pi  # noqa: E402

project_intelligence_bp = Blueprint("project_intelligence", __name__)


@project_intelligence_bp.route("/api/workbench/project-intelligence", methods=["GET"])
def get_project_intelligence():
    try:
        model = pi.get_project_intelligence()
    except Exception as e:  # noqa: BLE001 -- must not turn into a 500 for the Workbench screen
        return jsonify({
            "error": ("project intelligence read model unavailable: "
                      f"{type(e).__name__}: {e}"),
        }), 503
    return jsonify(model)
