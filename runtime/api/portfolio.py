"""
api/portfolio.py — Workbench Portfolio backend.

Read-only HTTP surface over tools/state/portfolio.py and the secure resolver
underneath it, tools/state/project_context.py. dev_continuity_events
revision 180 (task WB.1, status approved) is the reconciliation authority
for this slice: the Workbench is an application-level portfolio hub, and
CIS, WIASW and SWA are peer projects with separate repositories, spines,
roadmaps, gates and development histories. ADR-SEED-010's project-isolation
model (each project its own repo root, its own spine database, no shared
runtime spine) is not overridden by this — revision 180 is the authority
that reconciles an application-level portfolio VIEW with that isolation,
not a replacement for it. Narrowly scoped exactly like
api/project_intelligence.py and api/build_path.py: two GET routes, no query
parameters, no caller-supplied database/repo/spine path (that would let a
browser point the Workbench at an arbitrary file on disk — the only input
either route accepts beyond authentication is the project_id path
segment), and no write path of any kind.

Routes:
    GET /api/workbench/portfolio
        Every project the server-owned registry (`projects`, migration
        0022) currently carries, each resolved through the same secure
        resolver the detail route uses. Today that is exactly `cis` and
        `swa`. WIASW carries no registry row and is therefore absent from
        this list — it is not represented as a placeholder or a degraded
        entry, because it has no provisioned root or spine to report on.

    GET /api/workbench/portfolio/projects/<project_id>
        One project's resolved context. 404 when project_id names no
        registry row; otherwise always 200 — an unsafe path or a missing
        spine is reported honestly in the body (unsafe/error), the same
        way a composed Project-Map area degrades without taking the rest
        of the response down (see api/project_intelligence.py's docstring
        for the same rule applied there).

Distinct from, and never merged with, /api/workbench/projects/<project_id>
(braingate_conversation.py): that surface is workbench_projects, the
conversation-workspace mapping used by Braingate chat. This one is the
server-owned project REGISTRY (the `projects` table, migration 0022). The
two tables answer different questions and this blueprint reads only the
second.

Failure behavior: a failure inside the read model (registry unreachable,
schema missing) is returned as a 503 with an `error` field naming the
exception type — never a 500 traceback. Reaching into the read model and
getting back an honest "this project is not safe/not reachable" is not
failure — that is the information this screen exists to show, so it is
always a 200.
"""
import sys
from pathlib import Path

from flask import Blueprint, jsonify

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import portfolio as pf  # noqa: E402
import project_context as pc  # noqa: E402

_RUNTIME_DIR = Path(__file__).resolve().parents[1]
if str(_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_DIR))

from workbench_auth import check_auth  # noqa: E402

portfolio_bp = Blueprint("portfolio", __name__)


@portfolio_bp.route("/api/workbench/portfolio", methods=["GET"])
def get_portfolio():
    auth_err = check_auth()
    if auth_err:
        return auth_err

    try:
        model = pf.list_projects()
    except Exception as e:  # noqa: BLE001 -- must not turn into a 500 for the Workbench screen
        return jsonify({
            "error": f"portfolio registry unavailable: {type(e).__name__}: {e}",
        }), 503
    return jsonify(model)


@portfolio_bp.route("/api/workbench/portfolio/projects/<project_id>", methods=["GET"])
def get_portfolio_project(project_id):
    auth_err = check_auth()
    if auth_err:
        return auth_err

    try:
        project = pf.get_project(project_id)
    except pc.UnknownProjectError:
        return jsonify({"error": f"unknown project: {project_id}"}), 404
    except Exception as e:  # noqa: BLE001
        return jsonify({
            "error": f"portfolio registry unavailable: {type(e).__name__}: {e}",
        }), 503
    return jsonify(project)
