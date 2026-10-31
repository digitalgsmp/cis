#!/usr/bin/env python3
"""development_activity.py — read-only projection of ACTUAL development
evidence, for the Workbench "Project Map" Development Activity area.

WHAT THIS IS. The rest of the Project Map (Current Build, Trajectory) explains
the MACRO build trajectory: the P0–P6 sequence the roadmap declares. This
module is the MICRO companion to it — what has actually been happening in
development, read straight off the record and off disk:

    the last session handoff -> recent during-work ledger events
    -> recent action proposals and the dispatch runs explicitly linked to
    them -> recent semantic-transaction ledger rows (when that ledger exists)
    -> the working tree, exactly as git reports it right now.

It is called from tools/state/project_intelligence.py with the SAME read-only
connection that module already opened — this module opens no connection of
its own and issues no write of any kind.

NEVER INVENT A LINK (same rule as project_intelligence.py). A proposal's
dispatch run is reported at exactly the confidence it is known:

    authoritative          workbench_action_proposals.card_runner_run_id is
                           an explicit, stored foreign key to the run.
    derived_from_evidence  no such foreign key is stored, but a
                           card_runner_runs row shares the proposal's exact
                           request_id — a literal match, quoted, never
                           upgraded to authoritative.
    not_yet_linked         neither of the above. Said out loud, not filled in.

project_id is NEVER used to create a link by itself — many unrelated rows
can share a project_id, and that is not evidence of a relationship between
any two of them. Likewise, dev_continuity_events and continuity_transactions
are reported here as their own independent activity feeds: nothing in this
module cross-links a continuity event or a transaction row to a proposal, a
run, or anything else. An old, unrelated continuity event is reported exactly
as it stands — never annotated with a "not linked" relationship to something
it has nothing to do with.

OPTIONAL TABLES ARE REPORTED HONESTLY. workbench_action_proposals (migration
0038), card_runner_runs (migration 0037) and continuity_transactions
(migration 0041) are additive migrations; none is guaranteed applied to any
given database. A missing table is reported as `available: False` with a
plain-English note, and the rest of this module's output still renders — a
missing optional table must never raise.

WORKING-TREE FACTS CARRY NO SEMANTIC CLAIM. get_working_tree_facts() reports
which files git sees as modified/added/deleted/untracked, and HEAD — nothing
more. It does not infer completion, intent, ownership or success from any of
that, and it issues no git write of any kind (status and rev-parse only).
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

READ_MODEL_KIND = "cis_development_activity"

AUTHORITATIVE = "authoritative"
DERIVED = "derived_from_evidence"
NOT_LINKED = "not_yet_linked"

RECENT_CONTINUITY_EVENTS_LIMIT = 20
RECENT_ACTION_PROPOSALS_LIMIT = 20
RECENT_CONTINUITY_TRANSACTIONS_LIMIT = 20

_GIT_TIMEOUT = 10


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (name,)
    ).fetchone() is not None


def _ref(kind, **fields):
    out = {"kind": kind}
    out.update(fields)
    return out


# ── session handoff ───────────────────────────────────────────────────────

def get_session_handoff(conn):
    """The current session_handoffs row, if the project is recording them on
    this database. A stored authority row, quoted as-is — nothing here
    interprets or summarizes it further."""
    if not _table_exists(conn, "session_handoffs"):
        return {
            "available": False,
            "note": "session_handoffs table not present on this database",
            "handoff": None,
        }
    row = conn.execute(
        "SELECT date, title, summary, decisions, next_actions, git_head, created_at "
        "FROM session_handoffs WHERE is_current = 1 "
        "ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return {
            "available": True,
            "note": "no row in session_handoffs is marked is_current",
            "handoff": None,
        }
    return {
        "available": True,
        "note": None,
        "handoff": dict(row),
        "confidence_class": AUTHORITATIVE,
        "authority_refs": [_ref("table_row", table="session_handoffs", is_current=1)],
    }


# ── development continuity ledger (raw feed, no cross-linking) ───────────

def get_recent_continuity_events(conn, limit=RECENT_CONTINUITY_EVENTS_LIMIT):
    """The most recent dev_continuity_events rows, across every task, exactly
    as the ledger holds them. No disposition is re-derived here — that
    belongs to tools/development/discovery.py, already used elsewhere on the
    Project Map for the Problems view — this is a raw activity feed, and no
    event here is linked to anything else in this module."""
    if not _table_exists(conn, "dev_continuity_events"):
        return {
            "available": False,
            "note": "dev_continuity_events table not present on this database",
            "events": [],
            "total_count": 0,
            "shown_count": 0,
        }
    total = conn.execute("SELECT COUNT(*) FROM dev_continuity_events").fetchone()[0]
    rows = conn.execute(
        "SELECT task, revision, kind, status, actor, summary, created_at "
        "FROM dev_continuity_events ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return {
        "available": True,
        "note": None,
        "total_count": total,
        "shown_count": len(rows),
        "events": [dict(r) for r in rows],
        "confidence_class": AUTHORITATIVE,
        "authority_refs": [_ref("table", table="dev_continuity_events")],
    }


# ── action proposals, with their dispatch-run link at its real confidence ─

def _card_runner_run_row(conn, run_id):
    row = conn.execute(
        "SELECT id, request_id, card_factory_card_id, mode, target, status, "
        "started_at, finished_at, exit_code, created_at "
        "FROM card_runner_runs WHERE id = ?", (run_id,)
    ).fetchone()
    return dict(row) if row else None


def _dispatch_run_link(conn, proposal, runner_available):
    if not runner_available:
        return {
            "confidence_class": NOT_LINKED,
            "run": None,
            "explanation": ("card_runner_runs table is not present on this database, so no "
                            "dispatch-run relationship can be resolved. No authoritative link "
                            "recorded yet."),
            "authority_refs": [],
        }

    run_id = proposal.get("card_runner_run_id")
    if run_id is not None:
        run = _card_runner_run_row(conn, run_id)
        if run is not None:
            return {
                "confidence_class": AUTHORITATIVE,
                "run": run,
                "explanation": ("workbench_action_proposals.card_runner_run_id is an explicit, "
                                "stored foreign key to this run."),
                "authority_refs": [_ref("foreign_key", table="workbench_action_proposals",
                                        column="card_runner_run_id", value=run_id)],
            }
        return {
            "confidence_class": NOT_LINKED,
            "run": None,
            "explanation": (f"card_runner_run_id={run_id} is stored on this proposal, but no "
                            "card_runner_runs row with that id exists. No authoritative link "
                            "recorded yet."),
            "authority_refs": [],
        }

    request_id = proposal.get("request_id")
    if request_id:
        match = conn.execute(
            "SELECT id, request_id, card_factory_card_id, mode, target, status, "
            "started_at, finished_at, exit_code, created_at "
            "FROM card_runner_runs WHERE request_id = ?", (request_id,)
        ).fetchone()
        if match is not None:
            return {
                "confidence_class": DERIVED,
                "run": dict(match),
                "explanation": ("No card_runner_run_id is stored on this proposal. A "
                                "card_runner_runs row shares the same request_id — quoted "
                                "evidence, not a recorded relationship, and never shown as "
                                "authoritative on that basis alone."),
                "authority_refs": [_ref("literal_match", column="request_id",
                                        value=request_id)],
            }

    return {
        "confidence_class": NOT_LINKED,
        "run": None,
        "explanation": ("No card_runner_run_id is recorded on this proposal, and no "
                        "card_runner_runs row shares its request_id. No authoritative link "
                        "recorded yet."),
        "authority_refs": [],
    }


def get_recent_action_proposals(conn, limit=RECENT_ACTION_PROPOSALS_LIMIT):
    """workbench_action_proposals rows, each carrying its dispatch-run
    relationship at exactly the confidence it is known. project_id is never
    used to form that link — shared project_id is not evidence of a
    relationship between any two rows."""
    if not _table_exists(conn, "workbench_action_proposals"):
        return {
            "available": False,
            "note": "workbench_action_proposals table not present on this database",
            "proposals": [],
            "total_count": 0,
            "shown_count": 0,
            "card_runner_available": False,
        }
    runner_available = _table_exists(conn, "card_runner_runs")
    total = conn.execute("SELECT COUNT(*) FROM workbench_action_proposals").fetchone()[0]
    rows = conn.execute(
        "SELECT id, project_id, kind, status, request_id, card_runner_run_id, "
        "card_factory_card_id, created_at, updated_at "
        "FROM workbench_action_proposals ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()

    proposals = []
    for row in rows:
        proposal = dict(row)
        proposal["dispatch_run"] = _dispatch_run_link(conn, proposal, runner_available)
        proposals.append(proposal)

    return {
        "available": True,
        "note": None,
        "total_count": total,
        "shown_count": len(proposals),
        "proposals": proposals,
        "card_runner_available": runner_available,
    }


# ── semantic-transaction ledger (migration 0041) ──────────────────────────

def get_recent_continuity_transactions(conn, limit=RECENT_CONTINUITY_TRANSACTIONS_LIMIT):
    """continuity_transactions rows, when migration 0041 has actually been
    applied to this database. 0041 is additive and staged, not applied to
    the live spine as of this card, so "not yet applied" is the honest,
    expected answer on production today — not a failure."""
    if not _table_exists(conn, "continuity_transactions"):
        return {
            "available": False,
            "note": ("continuity_transactions table not present on this database — migration "
                     "0041 has not been applied here"),
            "transactions": [],
            "total_count": 0,
            "shown_count": 0,
        }
    total = conn.execute("SELECT COUNT(*) FROM continuity_transactions").fetchone()[0]
    rows = conn.execute(
        "SELECT ledger_event_id, transaction_id, request_id, project_id, kind, "
        "criticality, actor, operation, verdict, decision, status, checked_at, "
        "committed_at, created_at "
        "FROM continuity_transactions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return {
        "available": True,
        "note": None,
        "total_count": total,
        "shown_count": len(rows),
        "transactions": [dict(r) for r in rows],
        "confidence_class": AUTHORITATIVE,
        "authority_refs": [_ref("table", table="continuity_transactions")],
    }


# ── working tree (observed facts only, no semantic claim) ────────────────

def _run_git(root, *args):
    try:
        return subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT,
        )
    except Exception:  # noqa: BLE001 — a git failure degrades, never raises
        return None


def get_working_tree_facts(repo_root=None):
    """What git reports right now: which files are dirty, and HEAD. Nothing
    is inferred from this about completion, intent, ownership or success —
    these are facts about files on disk at call time, not a claim about what
    any of them mean."""
    root = str(repo_root or REPO_ROOT)
    status = _run_git(root, "status", "--porcelain")
    if status is None or status.returncode != 0:
        detail = (status.stderr.strip() if status is not None and status.stderr
                  else "git status could not be run")
        return {
            "available": False, "note": detail,
            "dirty": None, "dirty_file_count": None, "files": [],
            "head_sha": None, "branch": None,
        }

    lines = [line for line in status.stdout.splitlines() if line.strip()]
    files = [{"status": line[:2].strip(), "path": line[3:]} for line in lines]

    head = _run_git(root, "rev-parse", "HEAD")
    head_sha = head.stdout.strip() or None if head is not None and head.returncode == 0 else None
    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch_name = (branch.stdout.strip() or None
                   if branch is not None and branch.returncode == 0 else None)

    return {
        "available": True,
        "note": ("observed directly from git at call time — facts about files on disk right "
                 "now, not a claim about what any of them mean, who owns them, or whether "
                 "anything is finished"),
        "dirty": bool(files),
        "dirty_file_count": len(files),
        "files": files,
        "head_sha": head_sha,
        "branch": branch_name,
    }


# ── the composed area ──────────────────────────────────────────────────────

def get_development_activity(conn, repo_root=None):
    """The Development Activity area: the micro trajectory of actual
    development evidence, composed from the caller's already-open read-only
    connection. Opens no connection of its own and writes nothing."""
    return {
        "read_model": READ_MODEL_KIND,
        "session_handoff": get_session_handoff(conn),
        "continuity_events": get_recent_continuity_events(conn),
        "action_proposals": get_recent_action_proposals(conn),
        "continuity_transactions": get_recent_continuity_transactions(conn),
        "working_tree": get_working_tree_facts(repo_root),
    }
