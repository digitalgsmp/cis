#!/usr/bin/env python3
"""pipeline_entities.py — server-owned read model for the Workbench
"Chatbot / Pipeline Roles / Procedures / Activity" surface (queue item 4.34,
dev_continuity_events revision 3).

Composes over four existing authorities rather than inventing a competing
registry:

    chatbot     -> runtime/braingate_conversation.py's ALLOWED_ROUTES, and
                   whether runtime/container_app.py actually registers that
                   blueprint right now
    roles       -> runtime/abstraction/dispatch.py PROFILES — the canonical
                   six-role adapter map
    procedures  -> runtime/abstraction/guardrails.py PHASE_GATE_MAP and
                   SECURITY_GATES — the deterministic gate definitions
    activity    -> workflow_runs, deliberation_rounds, agent_trajectories,
                   eric_gate_approvals and gate_outcomes, each read through a
                   strict per-table column allowlist

THE CHATBOT IS NOT A SEVENTH ROLE. Braingate conversation dispatches through
the 'brain' backend adapter (dispatch.PROFILES['brain']), the same adapter the
Brainstorm pipeline role uses, so backend_role is reported as 'brain' — but
the chatbot is composed and returned as its own distinct entity for the
braingate_conversation capability, never folded into get_roles()'s six-entry
list. dispatch.ROLE_ALIASES (which maps legacy names like 'prime' to 'brain')
is never consulted here, so a legacy alias can never be presented as the
chatbot's identity.

WHAT THIS DOES NOT DO. It accepts no caller-supplied database path beyond the
same db_path override every tools/state/ module accepts for tests, and no
caller-supplied repo root beyond the same pattern. It issues no write of any
kind — every connection opened here is mode=ro. It never returns a port, a
Hermes profile name, a gate script's args/arg_desc, a URL, a filesystem path
or a credential — dispatch ports and hermes_profile keys are stripped in
get_roles(), and gate args/arg_desc are stripped in get_procedures(). The
activity cohort never returns a prompt, an output, a feedback field, a human
question/answer, an objection, a rationale, an evidence field, a JSON
snapshot/blob, directive_hash, briefing_hash or max_consecutive_revisions —
see the column allowlists below, which are the only columns any SELECT in
this module ever names.

ONE SHARED COHORT, NOT FIVE INDEPENDENT TOP-20s. get_activity_cohort() takes
the newest ACTIVITY_COHORT_LIMIT workflow_runs, then returns only the rows in
the other four tables that belong to THAT SAME set of run ids — so every
table in the response is activity for the same bounded set of recent runs,
never a separately-windowed, unrelated top-20 of its own.

A MISSING ACTIVITY TABLE DEGRADES, IT DOES NOT FAIL. If any one of the five
tables is absent from the database, that table's entry reports
available=False with rows=[] and a plain-English note; the rest of the
response still renders.
"""
import sys
from pathlib import Path

_STATE_DIR = Path(__file__).resolve().parent
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import canonical_state as cs  # noqa: E402  (shared DB default + puts runtime/ on sys.path)

from abstraction import dispatch  # noqa: E402
from abstraction import guardrails  # noqa: E402
import braingate_conversation as _braingate  # noqa: E402

READ_MODEL_KIND = "cis_pipeline_entities"

ACTIVITY_COHORT_LIMIT = 20

# ── strict column allowlists ───────────────────────────────────────────────
# The only columns any SELECT in this module ever names. Every excluded
# column (prompts, outputs, feedback, human Q&A, objections, rationale,
# evidence, JSON snapshots/blobs, directive_hash, briefing_hash,
# max_consecutive_revisions) is named once here, as what is left OUT, rather
# than left implicit in which SELECT happens to have been written.
_WORKFLOW_RUNS_COLUMNS = (
    "id", "result", "requires_eric_review", "max_rounds", "rounds_completed",
    "created_at", "completed_at", "status", "route", "updated_at",
    "eric_approved_at", "project_id", "parent_run_id",
)
_DELIBERATION_ROUNDS_COLUMNS = (
    "id", "run_id", "round_number", "drafter_role", "reviewer_role",
    "reviewer_signal", "revision_number", "requires_eric_review", "created_at",
)
_AGENT_TRAJECTORIES_COLUMNS = (
    "id", "run_id", "role", "phase", "round_number", "outcome",
    "consensus_reached", "config_version", "marginal_utility", "created_at",
    "tokens_in", "tokens_out",
)
_ERIC_GATE_APPROVALS_COLUMNS = (
    "id", "workflow_run_id", "decision", "decided_at", "decided_by",
    "goal_reference_id", "is_current", "supersedes_approval_id", "created_at",
)
_GATE_OUTCOMES_COLUMNS = (
    "id", "run_id", "phase", "role", "guardrail_name", "verdict", "mode",
    "timestamp",
)

# Gate dict fields kept when reporting a procedure's gates. "args" and
# "arg_desc" are deliberately absent: PHASE_GATE_MAP's verify stage carries a
# port ("5000") and a localhost URL in its args, and gate args in general are
# backend configuration, not a procedure definition.
_GATE_FIELDS = ("script", "mode", "needs_run_id", "needs_card", "needs_proposal", "from_output")


def _connect(db_path=None):
    import sqlite3
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (name,)
    ).fetchone() is not None


def _select_cols(conn, table, columns, where_clause="", params=(), order_by="", limit=None):
    """SELECT over a fixed, hardcoded column tuple and a fixed, hardcoded
    table name — never built from caller input — so this is not a SQL
    injection surface despite the string formatting."""
    col_sql = ", ".join(columns)
    sql = f"SELECT {col_sql} FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit is not None:
        sql += f" LIMIT {int(limit)}"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ── chatbot (Braingate conversation, NOT a seventh role) ───────────────────

def get_chatbot(repo_root=None):
    root = Path(repo_root) if repo_root else cs.REPO_ROOT
    container_app_text = (root / "runtime" / "container_app.py").read_text()
    blueprint_registered = "register_blueprint(braingate_conversation_bp)" in container_app_text

    route_allowlist = [
        {"path": path, "methods": sorted(methods)}
        for path, methods, _func in _braingate.ALLOWED_ROUTES
    ]

    brain_profile = dispatch.PROFILES.get("brain", {})

    return {
        "id": "chatbot",
        "label": "Workbench Chatbot",
        "backend_role": "brain",
        "capability": "braingate_conversation",
        "is_pipeline_role": False,
        "description": brain_profile.get("description", "Braingate conversation surface"),
        "authority": {
            "route_allowlist": route_allowlist,
            "blueprint_registered": blueprint_registered,
            "source_module": "runtime/braingate_conversation.py",
        },
    }


# ── the six canonical pipeline roles ────────────────────────────────────────

def get_roles():
    """Exactly dispatch.PROFILES's roles, with port and hermes_profile
    stripped. Never reads dispatch.ROLE_ALIASES."""
    roles = []
    for role_key, profile in dispatch.PROFILES.items():
        roles.append({
            "role": profile.get("role", role_key),
            "label": profile.get("label", role_key),
            "description": profile.get("description"),
            "capabilities": list(profile.get("capabilities", [])),
        })
    return roles


# ── runtime procedure stages and deterministic gates ───────────────────────

def _strip_gate(gate):
    return {k: gate[k] for k in _GATE_FIELDS if k in gate}


def get_procedures():
    stages = {
        stage: [_strip_gate(g) for g in gates]
        for stage, gates in guardrails.PHASE_GATE_MAP.items()
    }
    security_gates = [_strip_gate(g) for g in guardrails.SECURITY_GATES]
    return {
        "stages": stages,
        "security_gates": security_gates,
    }


# ── shared newest-20-run activity cohort ────────────────────────────────────

_DEGRADED_NO_COHORT = {
    "available": False,
    "note": "no workflow_runs cohort available",
    "rows": [],
    "count": 0,
}

_DEPENDENT_TABLES = (
    ("deliberation_rounds", "deliberation_rounds", _DELIBERATION_ROUNDS_COLUMNS, "run_id", "id DESC"),
    ("agent_trajectories", "agent_trajectories", _AGENT_TRAJECTORIES_COLUMNS, "run_id", "id DESC"),
    ("eric_gate_approvals", "eric_gate_approvals", _ERIC_GATE_APPROVALS_COLUMNS, "workflow_run_id", "created_at DESC"),
    ("gate_outcomes", "gate_outcomes", _GATE_OUTCOMES_COLUMNS, "run_id", "id DESC"),
)


def get_activity_cohort(db_path=None, limit=ACTIVITY_COHORT_LIMIT):
    conn = _connect(db_path)
    try:
        if not _table_exists(conn, "workflow_runs"):
            result = {
                "cohort_run_ids": [],
                "workflow_runs": {
                    "available": False,
                    "note": "workflow_runs table not present on this database",
                    "rows": [], "count": 0,
                },
            }
            for key, *_rest in _DEPENDENT_TABLES:
                result[key] = dict(_DEGRADED_NO_COHORT)
            return result

        run_rows = _select_cols(
            conn, "workflow_runs", _WORKFLOW_RUNS_COLUMNS,
            order_by="created_at DESC, id DESC", limit=limit,
        )
        run_ids = [r["id"] for r in run_rows]

        result = {
            "cohort_run_ids": run_ids,
            "workflow_runs": {
                "available": True, "note": None,
                "rows": run_rows, "count": len(run_rows),
            },
        }

        for key, table, columns, fk_column, order_by in _DEPENDENT_TABLES:
            if not _table_exists(conn, table):
                result[key] = {
                    "available": False,
                    "note": f"{table} table not present on this database",
                    "rows": [], "count": 0,
                }
                continue
            if not run_ids:
                rows = []
            else:
                placeholders = ",".join("?" for _ in run_ids)
                rows = _select_cols(
                    conn, table, columns,
                    where_clause=f"{fk_column} IN ({placeholders})",
                    params=tuple(run_ids), order_by=order_by,
                )
            result[key] = {"available": True, "note": None, "rows": rows, "count": len(rows)}

        return result
    finally:
        conn.close()


# ── the composed response ───────────────────────────────────────────────────

def get_pipeline_entities(db_path=None, repo_root=None):
    return {
        "read_model": READ_MODEL_KIND,
        "chatbot": get_chatbot(repo_root=repo_root),
        "roles": get_roles(),
        "procedures": get_procedures(),
        "activity": get_activity_cohort(db_path=db_path),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_pipeline_entities(), indent=2))
