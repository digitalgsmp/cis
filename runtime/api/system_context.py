"""
api/system_context.py — Workbench System Context / Recovery UI backend
(CARD_03_WORKBENCH_SYSTEM_CONTEXT_UI.md, queue 4.30).

Read-only HTTP surface over tools/state/canonical_state.py (queue 4.29 /
CARD_01) and tools/state/recovery_packet.py (CARD_02). Per Card 03's
architecture rule (Database -> canonical_state.py -> recovery_packet.py ->
Workbench UI), this module does not independently query or reconstruct
project truth, does not accept a caller-supplied database path (that would
let a client point the Workbench at an arbitrary file on disk), and never
writes anything -- both routes are GET-only and both underlying modules
are themselves read-only.

Self-contained like container_app.py itself: does not import the legacy
runtime/api/* blueprints or their host-path-dependent config/db modules,
so this works inside the container the same way the rest of
container_app.py's own routes do.

Routes:
    GET /api/workbench/system-context
        Full canonical_state.get_canonical_state() output: authoritative
        project state and observed runtime health in one payload.

    GET /api/workbench/system-context/recovery-packet[?issue=<area>]
        recovery_packet.build_recovery_packet(), optionally focused on one
        of recovery_packet.ISSUE_AREAS. An unrecognized ?issue is a 400,
        not a silent fall-back to the full packet.

Failure behavior: a failure inside either underlying module (e.g. the
spine database is unreachable) is caught here and returned as a 503 with
an `error` field naming the exception type -- never a 500 traceback, and
never a fabricated 200. This mirrors container_app.py's own
/api/relay/system/health pattern of failing one section visibly rather
than crashing the whole response.
"""
import sys
from pathlib import Path

from flask import Blueprint, jsonify, request

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import canonical_state as cs  # noqa: E402
import recovery_packet as rp  # noqa: E402

system_context_bp = Blueprint("system_context", __name__)


@system_context_bp.route("/api/workbench/system-context", methods=["GET"])
def get_system_context():
    try:
        state = cs.get_canonical_state()
    except Exception as e:  # noqa: BLE001 -- must not turn into a 500 for the Workbench screen
        return jsonify({
            "error": f"canonical state unavailable: {type(e).__name__}: {e}",
        }), 503
    return jsonify(state)


@system_context_bp.route("/api/workbench/system-context/recovery-packet", methods=["GET"])
def get_recovery_packet():
    issue = request.args.get("issue") or None
    if issue and issue not in rp.ISSUE_AREAS:
        return jsonify({
            "error": f"unknown issue area {issue!r}",
            "known_issue_areas": sorted(rp.ISSUE_AREAS),
        }), 400
    try:
        packet = rp.build_recovery_packet(issue=issue)
    except Exception as e:  # noqa: BLE001
        return jsonify({
            "error": f"recovery packet generation failed: {type(e).__name__}: {e}",
        }), 503
    return jsonify(packet)
