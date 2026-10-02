"""
api/destination_architecture.py — Workbench "Destination Architecture" view
backend (WIASW destination-architecture card).

Read-only HTTP surface over tools/state/destination_architecture.py. Narrowly
scoped exactly like api/build_path.py: one GET route, no query parameters, no
caller-supplied database path (that would let a client point the Workbench at
an arbitrary file on disk), and no write path of any kind. The read model
underneath opens the spine with sqlite3's mode=ro URI, so even a bug here
cannot mutate project state.

Why its own blueprint rather than a route on build_path_bp: that blueprint's
subject is the P0–P6 build sequence — "what are we building now". This one's
subject is the destination architecture — "what is CIS ultimately being built
to support". Keeping them apart at the blueprint boundary is the same
separation the two read models keep in the database, and it keeps this
feature's surface visible as exactly one added route in
runtime/container_app.py's url_map.

Self-contained like api/build_path.py and api/system_context.py: no legacy
runtime/api/* blueprint, config or db module is imported, so this works inside
the cis-pipeline container exactly as it does on the host.

Route:
    GET /api/workbench/destination-architecture
        The destination-architecture read model: the WIASW hierarchy, its five
        media domains, the horizontal applications, CIS as substrate and the
        execution/tool layer, with explicit relationship semantics, activation
        state, per-element provenance back to the ADR-WIASW-* decisions, and
        Mermaid source generated per zoom level.

Failure behavior: a failure inside the read model (unreachable spine,
unparsable decision text) is returned as a 503 with an `error` field naming
the exception type — never a 500 traceback, and never a fabricated 200 with a
plausible-looking architecture in it. An architecture that is simply not
recorded is a 200 with present:false, which is a different answer and is kept
distinct from a failure.
"""
import sys
from pathlib import Path

from flask import Blueprint, jsonify

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import destination_architecture as da  # noqa: E402

destination_architecture_bp = Blueprint("destination_architecture", __name__)


@destination_architecture_bp.route("/api/workbench/destination-architecture",
                                   methods=["GET"])
def get_destination_architecture():
    try:
        model = da.get_destination_architecture()
    except Exception as e:  # noqa: BLE001 -- must not turn into a 500 for the Workbench screen
        return jsonify({
            "error": ("destination architecture read model unavailable: "
                      f"{type(e).__name__}: {e}"),
        }), 503
    return jsonify(model)
