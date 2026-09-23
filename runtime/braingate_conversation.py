"""
braingate_conversation.py — the Braingate-conversation-only activation surface.

WB.1 is at the Braingate conversation stage. The host must deterministically
enforce, for that stage: **conversation may occur; downstream generation and
execution cannot occur.**

`runtime/workbench_app.py` cannot do that. Its `workbench_bp` nests
`card_factory_bp` and `card_runner_bp` at import time (workbench_app.py:54-55)
AND carries its own downstream action routes (`confirm-direction` calls
`generate_card_core()`; `approve` calls `card_runner.dispatch()`). So the single
statement

    app.register_blueprint(workbench_bp)

simultaneously exposes paid card generation and real agent-subprocess dispatch.
Recorded as WB.1 continuity revision 21. Deleting the two nested
`register_blueprint` lines would NOT be sufficient, because the downstream
routes live in workbench_app.py itself.

This module is the separation seam. It is a fresh Blueprint that binds ONLY the
conversation view functions, by direct reference:

    list_projects   GET    /api/workbench/projects
    create_project  POST   /api/workbench/projects
    get_project     GET    /api/workbench/projects/<project_id>
    update_project  PATCH  /api/workbench/projects/<project_id>
    list_messages   GET    /api/workbench/projects/<project_id>/messages
    send_message    POST   /api/workbench/projects/<project_id>/messages   (guarded)

Nothing else is bound. Because this blueprint is constructed here rather than
derived from `workbench_bp`, it cannot inherit workbench_bp's nested blueprints
or its proposal/confirm/approve routes — there is no code path by which a route
could arrive on this surface without being named in ALLOWED_ROUTES below. The
route inventory is asserted in
`runtime/tests/test_braingate_conversation_boundary.py`.

Design note — no duplicated logic. The view functions are the SAME objects
already defined and independently reviewed in workbench_app.py (Codex PASS,
WB-1B-3-ui/verification.json). Flask's `Blueprint.route` decorator returns the
undecorated function unchanged, so `workbench_app.list_projects` is the plain
callable and can be bound to a second blueprint without copying a line of its
body. The only new logic in this module is the conversation-mode guard below.

Importing this module imports workbench_app, which in turn imports
card_factory_app and card_runner. That is import, not registration: no route
from either module is reachable through this blueprint. The dormant downstream
implementations stay intact and unexposed, which is what the stage requires.
"""
from flask import Blueprint, jsonify, request

import workbench_app as _wb
from workbench_auth import check_auth

braingate_conversation_bp = Blueprint("braingate_conversation", __name__)

# The only conversation mode this surface permits. workbench_app.send_message
# also accepts 'draft_proposal' (creates an action proposal) and
# 'revise_proposal' (mutates one, and can force-bump a linked card_factory ask)
# — both are downstream-stage operations and are refused here.
CONVERSATION_ONLY_MODES = ("chat",)

# Payload keys that belong to the proposal/generation/execution stages. Any of
# them appearing on a conversation-only send is refused outright rather than
# ignored: silently dropping a field a caller believed was honored is how a
# boundary gets trusted for something it never enforced. This is defense in
# depth behind the mode check — `mode` alone already gates every one of these
# paths in workbench_app.send_message, but the card's rule is that an
# equivalent alternate payload must not be a way through either.
FORBIDDEN_PAYLOAD_KEYS = (
    "proposal_id",
    "expected_proposal_revision",
    "expected_card_fingerprint",
    "card_factory_ask_id",
    "card_factory_card_id",
    "card_runner_run_id",
    "authorized_by",
    "permitted_files",
    "permitted_commands",
    "target",
    "model",
    "max_turns",
    "budget_usd",
    "wall_clock_timeout_seconds",
    "review_of_run_id",
    "accept_time_only_control",
    "max_turns_ack_observation_only",
)

_STAGE_DETAIL = (
    "CIS is at the Braingate conversation stage. This surface permits "
    "conversation only — proposal drafting, proposal revision, card generation "
    "and execution dispatch are not registered here and cannot be reached by "
    "any payload."
)


def _refuse(detail_key: str, detail: str):
    return jsonify({
        "error": "Forbidden at the Braingate conversation stage",
        "detail": detail,
        "refused": detail_key,
        "stage": "braingate_conversation",
        "permitted_modes": list(CONVERSATION_ONLY_MODES),
    }), 403


@braingate_conversation_bp.route(
    "/api/workbench/projects/<project_id>/messages", methods=["POST"]
)
def send_conversation_message(project_id: str):
    """Ordinary Braingate conversation only.

    Refuses deterministically BEFORE delegating — no model call, no KB search,
    no row written, and in particular no path into `generate_card_core()` or
    `card_runner.dispatch()` is entered on a refusal. The refusal is a plain
    request-body check on this host, not a model instruction and not a
    frontend-only check.
    """
    auth_err = check_auth()
    if auth_err:
        return auth_err

    data = request.get_json(silent=True) or {}

    mode = (data.get("mode") or "chat")
    mode = mode.strip() if isinstance(mode, str) else mode
    if mode not in CONVERSATION_ONLY_MODES:
        return _refuse(
            "mode",
            f"mode={mode!r} is not available at this stage. {_STAGE_DETAIL}",
        )

    present = [k for k in FORBIDDEN_PAYLOAD_KEYS if k in data]
    if present:
        return _refuse(
            "payload_keys",
            f"downstream-stage field(s) {sorted(present)} are not accepted at "
            f"this stage. {_STAGE_DETAIL}",
        )

    # Delegate to the already-reviewed implementation, in this same request
    # context. It re-reads the body itself and re-runs its own validation
    # (message required, request_id required, length bounds, duplicate-replay
    # dedup) — none of which is reimplemented here.
    return _wb.send_message(project_id)


# ── Route inventory ──────────────────────────────────────────────────────
# Bound by direct reference to workbench_app's reviewed view functions. Kept
# as an explicit table so the boundary is a readable allowlist rather than an
# emergent property of which decorators happened to run, and so the test suite
# can assert the registered URL map matches it exactly.

ALLOWED_ROUTES = (
    ("/api/workbench/projects", ("GET",), _wb.list_projects),
    ("/api/workbench/projects", ("POST",), _wb.create_project),
    ("/api/workbench/projects/<project_id>", ("GET",), _wb.get_project),
    ("/api/workbench/projects/<project_id>", ("PATCH",), _wb.update_project),
    ("/api/workbench/projects/<project_id>/messages", ("GET",), _wb.list_messages),
    # POST .../messages is the guarded view defined above, not _wb.send_message
    # directly — registered by its own decorator.
)

for _rule, _methods, _view in ALLOWED_ROUTES:
    braingate_conversation_bp.add_url_rule(
        _rule, endpoint=_view.__name__, view_func=_view, methods=list(_methods)
    )
del _rule, _methods, _view


# Schema precondition for this surface. Documented here because it is NOT the
# single migration the activation card assumed.
#
# 0035_workbench.sql alone is insufficient: workbench_app.send_message's
# duplicate-replay branch queries `workbench_action_proposals` (workbench_app.py
# :644) on EVERY resend of a known request_id, including a plain chat one. With
# only 0035 applied, a duplicate chat send raises
# `sqlite3.OperationalError: no such table: workbench_action_proposals` and
# returns 500 — and duplicate-submission prevention is itself a required WB.1A
# conversation behavior, not a downstream feature.
#
# 0038 defines that table only. It registers no route, and every route that
# writes it (draft/revise/confirm/approve) lives on workbench_bp, which this
# surface does not register. Applying it therefore does not widen exposure.
#
# This module does not apply migrations. See evidence.md for the probe.
REQUIRED_MIGRATIONS = (
    "0035_workbench.sql",
    "0038_workbench_action_proposals.sql",
)

FORBIDDEN_MIGRATIONS = (
    "0036_card_factory.sql",
    "0037_card_runner.sql",
)
