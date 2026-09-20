"""
card_factory_app.py — CIS Card Factory: turn an ask into a gate-checked
build card.

Queue item WB.1B-1. Sibling of runtime/workbench_app.py, registered by it
as a nested blueprint. Self-contained: its own DB helper and auth check,
so it can be unit tested in isolation with a temporary database and a
monkeypatched generator call — it does not import workbench_app.

Flow:
  submit ask -> stored in card_factory_asks, also inserted into
  knowledge_messages (role='human') so tools/card_gate.py's verbatim-quote
  check can find Eric's own words.
  generate   -> exactly one non-interactive `claude -p` call (no tools,
  minimal startup context, single turn, timeout, no retries) with
  cards/GENERATOR_PROMPT.txt plus the ask, as JSON on stdin. Requires a
  client request_id: replaying it returns the existing attempt rather than
  calling the model again, and only one generation may be in flight per ask
  revision at a time.
  gate       -> tools/card_gate.py run as a subprocess against the
  generated text. PASS (exit 0, stdout starts "PASS") saves the card to
  cards/inbox/. NO_CARD is a gate SKIP (exit 0, stdout starts "SKIP"), not
  a failure. Any other non-zero exit is FAIL. Output and exit code stored.
  edit       -> editing an ask bumps its revision, which makes every card
  generated against the old wording stale (application-computed: a card's
  ask_revision no longer equals its ask's current revision) and archives any
  of that ask's PASS cards out of the active cards/inbox/ into cards/history/
  — a stale file must not keep looking dispatch-eligible. Editing a card
  never overwrites its row: it inserts a new row in the same lineage
  (lineage_id/card_revision/supersedes_id), re-gates the new text, marks the
  old row is_current=0, and archives the old row's inbox file if it had one.
  A separate re-gate route re-verifies a row's existing text in place
  without creating a new revision.

card_gate.py, mine_asks.py and cards/GENERATOR_PROMPT.txt are called, never
modified. This module does not touch the UI.
"""
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile

from flask import Blueprint, jsonify, request

card_factory_bp = Blueprint("card_factory", __name__)

# ── Config ───────────────────────────────────────────────────────────────

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
API_KEY = os.environ.get("CIS_PIPELINE_API_KEY", "")

GENERATOR_PROMPT_PATH = os.path.join(REPO_ROOT, "cards", "GENERATOR_PROMPT.txt")
GATE_SCRIPT_PATH = os.path.join(REPO_ROOT, "tools", "card_gate.py")
CARDS_INBOX_DIR = os.environ.get(
    "CIS_CARD_FACTORY_INBOX_DIR", os.path.join(REPO_ROOT, "cards", "inbox")
)
# Where a card's saved file goes once it stops being dispatch-eligible
# (superseded by an edit, or stale because its ask was edited). Kept outside
# the active inbox so a scanner of cards/inbox/ never sees it as current.
CARDS_HISTORY_DIR = os.environ.get(
    "CIS_CARD_FACTORY_HISTORY_DIR", os.path.join(REPO_ROOT, "cards", "history")
)

# Single place the generator command is configured.
# --tools ""       : verified via `claude --help` to disable all tool calls —
#                     the single-turn requirement (checked live: exit 0).
# --safe-mode      : verified via `claude --help` to disable CLAUDE.md,
#                     skills, plugins, hooks, MCP servers, custom
#                     commands/agents, output styles, workflows, themes and
#                     keybindings, while leaving auth/model/permissions
#                     working normally. Chosen over --bare: --bare's own
#                     help text says it forces ANTHROPIC_API_KEY/apiKeyHelper
#                     auth and never reads OAuth or keychain, and this
#                     deployment's ~/.claude.json shows an OAuth
#                     (oauthAccount / stripe_subscription) login, not an API
#                     key — --bare would have broken auth here.
#                     NOT independently verified: whether --safe-mode's
#                     "CLAUDE.md" suppression also covers AGENTS.md (a
#                     second, separately-loaded memory file per
#                     WB-1B-0-preflight FACTS.md §11), and whether it
#                     suppresses --bare's separately-listed "auto-memory" /
#                     "background prefetches" behavior. No live call was
#                     made to check token counts either way — that would
#                     itself be a paid call this card does not need to make.
#                     Model is the cheapest capable one available in this
#                     deployment (claude-haiku-4-5) — a short, fixed-shape
#                     generation prompt does not need a larger model.
GENERATOR_COMMAND = [
    "claude", "-p", "--tools", "", "--safe-mode",
    "--model", "claude-haiku-4-5-20251001", "--output-format", "json",
]
GENERATOR_TIMEOUT_SECONDS = 90
GATE_TIMEOUT_SECONDS = 30

# Explicit, documented bounds — an over-limit request is rejected outright,
# never silently truncated (truncation could quietly cut a quote in half and
# make the gate fail for a reason Eric never sees).
MAX_ASK_TEXT_CHARS = 4000
MAX_DONE_WHEN_CHARS = 2000
MAX_GENERATOR_OUTPUT_CHARS = 8000

# knowledge_messages.role value for Eric's own words (FACTS.md §6: confirmed
# via tools/mine_asks.py and card_gate.py's MODEL_ROLES exclusion).
ERIC_ROLE = "human"


def _check_auth():
    if not API_KEY:
        return None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:].strip() == API_KEY:
        return None
    return jsonify({"error": "Unauthorized", "detail": "Invalid or missing API key"}), 401


def _db(db_path: str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _combined_text(ask_text: str, done_when_text: str) -> str:
    ask_text = (ask_text or "").strip()
    done_when_text = (done_when_text or "").strip()
    if done_when_text:
        return f"{ask_text}\n{done_when_text}"
    return ask_text


# ── Generator call (subprocess mocked in tests) ─────────────────────────

def _call_generator(payload: dict):
    """Exactly one non-interactive model call. Returns
    (result_text, error, usage) — exactly one of result_text/error is not
    None. usage is {'input_tokens', 'output_tokens', 'cost_usd'} with any
    field that the CLI's JSON output did not report left as None (unknown
    stays unknown — never estimated), or None entirely on error. Never
    retries, never loops."""
    try:
        with open(GENERATOR_PROMPT_PATH, "r") as f:
            prompt_text = f.read()
    except OSError as e:
        return None, f"could not read GENERATOR_PROMPT.txt: {e}", None

    stdin_text = prompt_text + "\n\n" + json.dumps(payload)
    try:
        proc = subprocess.run(
            GENERATOR_COMMAND,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=GENERATOR_TIMEOUT_SECONDS,
            cwd=REPO_ROOT,
        )
    except subprocess.TimeoutExpired:
        return None, f"generator timed out after {GENERATOR_TIMEOUT_SECONDS}s", None
    except OSError as e:
        return None, f"could not run generator: {type(e).__name__}: {e}", None

    if proc.returncode != 0:
        return None, f"generator exited {proc.returncode}: {proc.stderr.strip()[:500]}", None

    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return None, "generator returned malformed JSON output", None
    if not isinstance(data, dict):
        return None, "generator returned malformed JSON output (expected an object)", None

    if data.get("is_error"):
        return None, f"generator reported an error: {str(data.get('result', ''))[:500]}", None

    result_text = (data.get("result") or "").strip()
    if not result_text:
        return None, "generator returned an empty response", None

    usage = None
    u = data.get("usage")
    cost = data.get("total_cost_usd")
    if isinstance(u, dict) or cost is not None:
        usage = {
            "input_tokens": u.get("input_tokens") if isinstance(u, dict) else None,
            "output_tokens": u.get("output_tokens") if isinstance(u, dict) else None,
            "cost_usd": cost,
        }
    return result_text, None, usage


# ── Gate call (real subprocess — deterministic, no cost) ────────────────

def _run_gate(card_text: str):
    """Runs tools/card_gate.py against card_text. Returns
    (status, exit_code, output) where status is 'pass' | 'fail' | 'skip' |
    'error'. A gate that cannot even run (missing interpreter, timeout) is
    reported as status='error' with the reason in `output` — never an
    uncaught exception that would surface as a bare 500."""
    fd, fd_path = tempfile.mkstemp(suffix=".md", prefix="card-factory-gate-")
    with os.fdopen(fd, "w") as f:
        f.write(card_text)
    try:
        try:
            proc = subprocess.run(
                ["python3", GATE_SCRIPT_PATH, "--db", DB_PATH, fd_path],
                capture_output=True, text=True, timeout=GATE_TIMEOUT_SECONDS, cwd=REPO_ROOT,
            )
        except subprocess.TimeoutExpired:
            return "error", None, f"gate timed out after {GATE_TIMEOUT_SECONDS}s"
        except OSError as e:
            return "error", None, f"could not run gate: {type(e).__name__}: {e}"

        output = (proc.stdout + proc.stderr).strip()
        if proc.returncode == 0 and output.startswith("SKIP"):
            status = "skip"
        elif proc.returncode == 0 and output.startswith("PASS"):
            status = "pass"
        elif proc.returncode == 0:
            status = "skip"  # defensive: exit 0 with unrecognized text is treated as SKIP, never as a silent PASS
        else:
            status = "fail"
        return status, proc.returncode, output
    finally:
        try:
            os.remove(fd_path)
        except OSError:
            pass


def _slug(project: str, card_id: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (project or "card").lower()).strip("-")[:40]
    return f"cardfactory-{card_id:06d}-{slug or 'card'}.md"


def _save_to_inbox(card_id: int, project: str, card_text: str) -> str:
    os.makedirs(CARDS_INBOX_DIR, exist_ok=True)
    path = os.path.join(CARDS_INBOX_DIR, _slug(project, card_id))
    with open(path, "w") as f:
        f.write(card_text)
    return path


def _archive_to_history(saved_path: str) -> str:
    """Moves a no-longer-eligible card file out of the active inbox. Returns
    the new path, or the original path unchanged if the file is already
    gone (never raises — archiving is best-effort bookkeeping, not a gate)."""
    if not saved_path or not os.path.exists(saved_path):
        return saved_path
    os.makedirs(CARDS_HISTORY_DIR, exist_ok=True)
    dest = os.path.join(CARDS_HISTORY_DIR, os.path.basename(saved_path))
    try:
        shutil.move(saved_path, dest)
        return dest
    except OSError:
        return saved_path


# ── Serialization ────────────────────────────────────────────────────────

def _ask_dict(row) -> dict:
    return {
        "id": row["id"],
        "project": row["project"],
        "ask_text": row["ask_text"],
        "done_when_text": row["done_when_text"],
        "revision": row["revision"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _card_dict(row, ask_revision=None) -> dict:
    stale = None
    eligible_for_dispatch = None
    if ask_revision is not None:
        stale = row["ask_revision"] != ask_revision
        eligible_for_dispatch = bool(row["is_current"]) and row["status"] == "pass" and not stale
    return {
        "id": row["id"],
        "ask_id": row["ask_id"],
        "ask_revision": row["ask_revision"],
        "lineage_id": row["lineage_id"],
        "card_revision": row["card_revision"],
        "supersedes_id": row["supersedes_id"],
        "is_current": bool(row["is_current"]),
        "card_text": row["card_text"],
        "gate_exit_code": row["gate_exit_code"],
        "gate_output": row["gate_output"],
        "status": row["status"],
        "saved_path": row["saved_path"],
        "error": row["error"],
        "usage_input_tokens": row["usage_input_tokens"],
        "usage_output_tokens": row["usage_output_tokens"],
        "usage_cost_usd": row["usage_cost_usd"],
        "stale": stale,
        "eligible_for_dispatch": eligible_for_dispatch,
        "dispatch_target": row["dispatch_target"],
        "dispatch_status": row["dispatch_status"],
        "dispatch_run_id": row["dispatch_run_id"],
        "dispatch_started_at": row["dispatch_started_at"],
        "dispatch_finished_at": row["dispatch_finished_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _ask_revision(conn, ask_id: int):
    row = conn.execute(
        "SELECT revision FROM card_factory_asks WHERE id = ?", (ask_id,)
    ).fetchone()
    return row["revision"] if row else None


# A row left 'pending' longer than this did not finish because the process
# handling it crashed or restarted, not because generation is still running
# (GENERATOR_TIMEOUT_SECONDS + GATE_TIMEOUT_SECONDS bound how long a live
# attempt can legitimately take). Reconciled to 'error' so a dead attempt
# does not permanently hold the per-ask-revision concurrency lock — mirrors
# workbench_app.py's STALE_PENDING_SECONDS reconciliation for the same
# class of problem (a synchronous handler that never got to finish).
PENDING_STALE_SECONDS = GENERATOR_TIMEOUT_SECONDS + GATE_TIMEOUT_SECONDS + 30


def _reconcile_stale_pending(conn: sqlite3.Connection, ask_id: int = None) -> None:
    if ask_id is not None:
        conn.execute(
            "UPDATE card_factory_cards SET status = 'error', "
            "error = COALESCE(error, 'generation did not complete (process restarted or crashed)'), "
            "updated_at = datetime('now') "
            "WHERE ask_id = ? AND status = 'pending' "
            "AND datetime(created_at) < datetime('now', ?)",
            (ask_id, f"-{PENDING_STALE_SECONDS} seconds"),
        )
    else:
        conn.execute(
            "UPDATE card_factory_cards SET status = 'error', "
            "error = COALESCE(error, 'generation did not complete (process restarted or crashed)'), "
            "updated_at = datetime('now') "
            "WHERE status = 'pending' AND datetime(created_at) < datetime('now', ?)",
            (f"-{PENDING_STALE_SECONDS} seconds",),
        )
    conn.commit()


# ── Asks ─────────────────────────────────────────────────────────────────

def submit_ask_core(project, ask_text, done_when_text, done_when_verbatim=True):
    """Plain-function core of POST /api/cardfactory/asks — no auth check, no
    Flask request/response objects — so a sibling module (workbench_app.py's
    proposal "confirm direction" step) can call it directly without an HTTP
    round trip. Returns (status_code, body_dict).

    `done_when_verbatim` defaults True, preserving the original route's
    behavior: the /api/cardfactory/asks form has Eric type done_when_text
    himself, so it is genuinely his own words and belongs in the
    role='human' knowledge_messages row the gate's verbatim-quote check
    reads. A caller passing model-authored done_when_text (workbench's
    confirm-direction, using a proposal's success_criteria) must pass
    False so that text is never inserted into a row attributed to Eric —
    independent review found the prior version always combined both,
    letting a generated card cite the model's own words as if they were
    "Eric, verbatim."."""
    project = (project or "").strip()
    ask_text = (ask_text or "").strip()
    done_when_text = (done_when_text or "").strip()
    if not project:
        return 400, {"error": "project required"}
    if not ask_text:
        return 400, {"error": "ask_text required"}
    if len(ask_text) > MAX_ASK_TEXT_CHARS:
        return 400, {"error": f"ask_text too long (max {MAX_ASK_TEXT_CHARS} characters)"}
    if len(done_when_text) > MAX_DONE_WHEN_CHARS:
        return 400, {"error": f"done_when_text too long (max {MAX_DONE_WHEN_CHARS} characters)"}

    conn = _db()
    try:
        cur = conn.execute(
            "INSERT INTO card_factory_asks (project, ask_text, done_when_text) "
            "VALUES (?, ?, ?)",
            (project, ask_text, done_when_text or None),
        )
        ask_id = cur.lastrowid

        content = _combined_text(ask_text, done_when_text) if done_when_verbatim else ask_text
        km_cur = conn.execute(
            "INSERT INTO knowledge_messages (role, content, source, source_key) "
            "VALUES (?, ?, ?, ?)",
            (ERIC_ROLE, content, f"card-factory-ask-{ask_id}", str(ask_id)),
        )
        conn.execute(
            "UPDATE card_factory_asks SET knowledge_message_id = ? WHERE id = ?",
            (km_cur.lastrowid, ask_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        return 201, {"ask": _ask_dict(row)}
    finally:
        conn.close()


@card_factory_bp.route("/api/cardfactory/asks", methods=["POST"])
def submit_ask():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    status, body = submit_ask_core(
        data.get("project"), data.get("ask_text"), data.get("done_when_text")
    )
    return jsonify(body), status


@card_factory_bp.route("/api/cardfactory/asks/<int:ask_id>", methods=["GET"])
def get_ask(ask_id: int):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "ask not found"}), 404
        return jsonify({"ask": _ask_dict(row)})
    finally:
        conn.close()


def edit_ask_core(ask_id, ask_text=None, done_when_text=None, done_when_verbatim=True,
                   force_revision_bump=False, conn=None):
    """Plain-function core of PATCH /api/cardfactory/asks/<id>. `ask_text`/
    `done_when_text` of None means "leave unchanged" (mirrors the route's
    own `data.get(...) if 'x' in data else row['x']"). Returns
    (status_code, body_dict) — see submit_ask_core for why this exists as
    a separate function, and for what `done_when_verbatim` guards against.

    `force_revision_bump` (default False, unused by the route — no
    behavior change there) bumps `revision` even when `ask_text`/
    `done_when_text` are byte-identical to what's already stored.
    workbench_app.py's proposal correction uses this: a proposal field
    that has no column of its own on card_factory_asks (action,
    boundaries, kind, unresolved_decisions) still needs ANY material
    change to stale the linked card_factory_cards row at the boundary
    card_runner.dispatch() actually checks (ask_revision) — independent
    review found that without this, an action/boundary-only correction
    left the prior card fully dispatchable, from a direct runner-dispatch
    call as much as from workbench's own approve route.

    `conn`, when given, is used directly and is NEITHER committed NOR
    closed by this function — the caller owns that transaction.
    workbench_app.py's proposal correction needs this ask update and its
    own proposal-row update to land together or not at all: a prior
    version called this with no shared connection, discarded its
    (status, body) return, and had already committed the proposal update
    first — a rejected ask update (e.g. success_criteria over
    MAX_DONE_WHEN_CHARS) then left a proposal claiming a new revision
    while the ask/card stayed on the old one, fully, directly
    dispatchable (revisions observed as (2,1,1), independent review's
    exact reproduction). All validation below still runs, and still
    returns before any write on failure, whether or not `conn` is
    shared — the caller decides what "before any write" means for the
    rest of its own transaction."""
    owns_conn = conn is None
    if owns_conn:
        conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        if not row:
            return 404, {"error": "ask not found"}

        final_ask_text = (ask_text if ask_text is not None else row["ask_text"]) or ""
        final_done = (done_when_text if done_when_text is not None else row["done_when_text"]) or ""
        final_ask_text = final_ask_text.strip()
        final_done = final_done.strip()
        if not final_ask_text:
            return 400, {"error": "ask_text required"}
        if len(final_ask_text) > MAX_ASK_TEXT_CHARS:
            return 400, {"error": f"ask_text too long (max {MAX_ASK_TEXT_CHARS} characters)"}
        if len(final_done) > MAX_DONE_WHEN_CHARS:
            return 400, {"error": f"done_when_text too long (max {MAX_DONE_WHEN_CHARS} characters)"}

        changed = (
            final_ask_text != (row["ask_text"] or "") or final_done != (row["done_when_text"] or "")
            or force_revision_bump
        )

        conn.execute(
            "UPDATE card_factory_asks SET ask_text = ?, done_when_text = ?, "
            "revision = revision + ?, updated_at = datetime('now') WHERE id = ?",
            (final_ask_text, final_done or None, 1 if changed else 0, ask_id),
        )
        if changed and row["knowledge_message_id"]:
            km_content = _combined_text(final_ask_text, final_done) if done_when_verbatim else final_ask_text
            conn.execute(
                "UPDATE knowledge_messages SET content = ? WHERE id = ?",
                (km_content, row["knowledge_message_id"]),
            )

        if changed:
            # Every currently-inboxed PASS card for this ask was generated
            # against the wording that just changed underneath it — archive
            # it out of the active inbox so it stops looking dispatch-ready.
            # Cosmetic bookkeeping only, never the authority on eligibility
            # — that is always is_current/status/ask_revision in the DB,
            # committed (or not) below/by the caller, not this file move.
            stale_cards = conn.execute(
                "SELECT id, saved_path FROM card_factory_cards "
                "WHERE ask_id = ? AND is_current = 1 AND status = 'pass' AND saved_path IS NOT NULL",
                (ask_id,),
            ).fetchall()
            for c in stale_cards:
                new_path = _archive_to_history(c["saved_path"])
                if new_path != c["saved_path"]:
                    conn.execute(
                        "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
                        (new_path, c["id"]),
                    )
        if owns_conn:
            conn.commit()
        row = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        return 200, {"ask": _ask_dict(row)}
    finally:
        if owns_conn:
            conn.close()


@card_factory_bp.route("/api/cardfactory/asks/<int:ask_id>", methods=["PATCH"])
def edit_ask(ask_id: int):
    """Editing the ask text bumps its revision, which makes every card
    generated against the prior wording stale and archives any of that
    ask's currently-inboxed PASS cards out of cards/inbox/."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    status, body = edit_ask_core(
        ask_id,
        ask_text=data.get("ask_text") if "ask_text" in data else None,
        done_when_text=data.get("done_when_text") if "done_when_text" in data else None,
    )
    return jsonify(body), status


# ── Generate ─────────────────────────────────────────────────────────────

def generate_card_core(ask_id, request_id, extra_generator_context=None):
    """Plain-function core of POST /api/cardfactory/asks/<id>/generate —
    exactly one non-interactive model call plus the real gate subprocess,
    same as the route. Returns (status_code, body_dict). Exists so
    workbench_app.py's proposal "confirm direction" step can call the
    existing bounded generator + gate boundary directly, with no HTTP
    round trip and no behavior change from the route.

    `extra_generator_context`, when given, is appended to the generator
    payload's `text` field (which normally carries only ask_text +
    done_when_text) — this is how workbench_app.py sends the confirmed
    proposal's kind/outcome/action/boundaries/unresolved_decisions to the
    generator without changing cards/GENERATOR_PROMPT.txt's fixed
    {id, date, project, text} input contract. The route never passes
    this (default None -> unchanged payload, unchanged behavior)."""
    request_id = (request_id or "").strip()
    if not request_id:
        return 400, {"error": "request_id required"}

    conn = _db()
    try:
        ask = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        if not ask:
            return 404, {"error": "ask not found"}

        _reconcile_stale_pending(conn, ask_id)

        # Replaying the same request_id returns the existing attempt — never
        # a second model call, even if the first one failed. But if the ask
        # has since been edited, that old attempt no longer describes the
        # current wording: refuse rather than silently handing back stale
        # content as if it were current. A genuinely new attempt needs a
        # new request_id.
        existing = conn.execute(
            "SELECT * FROM card_factory_cards WHERE ask_id = ? AND request_id = ?",
            (ask_id, request_id),
        ).fetchone()
        if existing:
            if existing["ask_revision"] != ask["revision"]:
                return 409, {
                    "error": "request_id was already used against an earlier ask "
                             "revision; the ask has changed since — submit a new "
                             "request_id to generate against the current wording",
                }
            return 200, {
                "duplicate": True,
                "still_running": existing["status"] == "pending",
                "card": _card_dict(existing, ask["revision"]),
            }

        ask_revision = ask["revision"]
        try:
            cur = conn.execute(
                "INSERT INTO card_factory_cards "
                "(ask_id, ask_revision, card_revision, is_current, status, request_id) "
                "VALUES (?, ?, 1, 1, 'pending', ?)",
                (ask_id, ask_revision, request_id),
            )
            card_id = cur.lastrowid
            conn.execute(
                "UPDATE card_factory_cards SET lineage_id = ? WHERE id = ?", (card_id, card_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            return 409, {"error": "generation already in progress for this ask revision"}

        payload_text = _combined_text(ask["ask_text"], ask["done_when_text"])
        if extra_generator_context:
            payload_text = payload_text + "\n\n" + extra_generator_context
        payload = {
            "id": ask_id,
            "date": (ask["created_at"] or "")[:10],
            "project": ask["project"],
            "text": payload_text,
        }
        card_text, gen_error, usage = _call_generator(payload)

        # Stale-generation guard: if the ask changed while the model call
        # was in flight, this result no longer describes the current ask —
        # discard it rather than gating/saving it as if it did.
        fresh_ask = conn.execute(
            "SELECT revision FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        if fresh_ask["revision"] != ask_revision:
            conn.execute(
                "UPDATE card_factory_cards SET status = 'error', "
                "error = ?, updated_at = datetime('now') WHERE id = ?",
                ("ask changed during generation; result discarded", card_id),
            )
            conn.commit()
            return 409, {"error": "ask changed during generation; result discarded"}

        usage_input = usage.get("input_tokens") if usage else None
        usage_output = usage.get("output_tokens") if usage else None
        usage_cost = usage.get("cost_usd") if usage else None

        if gen_error is not None:
            conn.execute(
                "UPDATE card_factory_cards SET status = 'error', error = ?, "
                "usage_input_tokens = ?, usage_output_tokens = ?, usage_cost_usd = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (gen_error, usage_input, usage_output, usage_cost, card_id),
            )
            conn.commit()
            return 502, {"error": gen_error}

        if len(card_text) > MAX_GENERATOR_OUTPUT_CHARS:
            err = f"generator output exceeds {MAX_GENERATOR_OUTPUT_CHARS} characters"
            conn.execute(
                "UPDATE card_factory_cards SET status = 'error', error = ?, "
                "usage_input_tokens = ?, usage_output_tokens = ?, usage_cost_usd = ?, "
                "updated_at = datetime('now') WHERE id = ?",
                (err, usage_input, usage_output, usage_cost, card_id),
            )
            conn.commit()
            return 502, {"error": err}

        status, exit_code, output = _run_gate(card_text)

        # The gate subprocess can itself take up to GATE_TIMEOUT_SECONDS —
        # re-check staleness so a PASS is never written to the active inbox
        # for an ask that moved on while the gate was still running (the
        # earlier check only covers the model-call window, not this one).
        fresh_ask = conn.execute(
            "SELECT revision FROM card_factory_asks WHERE id = ?", (ask_id,)
        ).fetchone()
        went_stale_during_gate = fresh_ask["revision"] != ask_revision

        # Commit the verdict itself before touching the filesystem: the DB
        # row is the authority on eligibility (`eligible_for_dispatch`), so
        # if the process dies before the file write below, the record left
        # behind is self-consistent (status set, saved_path still NULL)
        # rather than a file sitting in cards/inbox/ with no committed row
        # to back it.
        conn.execute(
            "UPDATE card_factory_cards SET card_text = ?, gate_exit_code = ?, "
            "gate_output = ?, status = ?, usage_input_tokens = ?, usage_output_tokens = ?, "
            "usage_cost_usd = ?, updated_at = datetime('now') WHERE id = ?",
            (card_text, exit_code, output, status, usage_input, usage_output, usage_cost, card_id),
        )
        conn.commit()
        if status == "pass" and not went_stale_during_gate:
            saved_path = _save_to_inbox(card_id, ask["project"], card_text)
            conn.execute(
                "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
                (saved_path, card_id),
            )
            conn.commit()
        row = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()
        return 201, {"duplicate": False, "card": _card_dict(row, fresh_ask["revision"])}
    finally:
        conn.close()


@card_factory_bp.route("/api/cardfactory/asks/<int:ask_id>/generate", methods=["POST"])
def generate_card(ask_id: int):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    status, body = generate_card_core(ask_id, data.get("request_id"))
    return jsonify(body), status


# ── Cards ────────────────────────────────────────────────────────────────

@card_factory_bp.route("/api/cardfactory/cards", methods=["GET"])
def list_cards():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    ask_id = request.args.get("ask_id")
    conn = _db()
    try:
        _reconcile_stale_pending(conn, ask_id if ask_id else None)
        if ask_id:
            rows = conn.execute(
                "SELECT * FROM card_factory_cards WHERE ask_id = ? ORDER BY id DESC",
                (ask_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM card_factory_cards ORDER BY id DESC"
            ).fetchall()
        rev_cache = {}
        cards = []
        for r in rows:
            if r["ask_id"] not in rev_cache:
                rev_cache[r["ask_id"]] = _ask_revision(conn, r["ask_id"])
            cards.append(_card_dict(r, rev_cache[r["ask_id"]]))
        return jsonify({"cards": cards})
    finally:
        conn.close()


@card_factory_bp.route("/api/cardfactory/cards/<int:card_id>", methods=["GET"])
def get_card(card_id: int):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        row = conn.execute(
            "SELECT ask_id FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "card not found"}), 404
        _reconcile_stale_pending(conn, row["ask_id"])
        row = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()
        return jsonify({"card": _card_dict(row, _ask_revision(conn, row["ask_id"]))})
    finally:
        conn.close()


@card_factory_bp.route("/api/cardfactory/cards/<int:card_id>", methods=["PATCH"])
def edit_card(card_id: int):
    """Editing card text never overwrites the row: it inserts a new
    revision in the same lineage, re-gates the new text, retires the old
    row (is_current=0) and archives the old row's inbox file if it had
    one. Only the lineage's current tip may be edited."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    card_text = (data.get("card_text") or "").strip()
    if not card_text:
        return jsonify({"error": "card_text required"}), 400

    conn = _db()
    try:
        old = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()
        if not old:
            return jsonify({"error": "card not found"}), 404

        _reconcile_stale_pending(conn, old["ask_id"])
        old = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()

        if not old["is_current"]:
            current = conn.execute(
                "SELECT id FROM card_factory_cards WHERE lineage_id = ? AND is_current = 1",
                (old["lineage_id"],),
            ).fetchone()
            return jsonify({
                "error": "cannot edit a superseded card revision",
                "current_revision_id": current["id"] if current else None,
            }), 409
        if old["status"] == "pending":
            return jsonify({
                "error": "cannot edit a card while its generation is still in progress"
            }), 409

        ask = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (old["ask_id"],)
        ).fetchone()
        ask_revision = ask["revision"]

        status, exit_code, output = _run_gate(card_text)

        # Demote the old row before inserting the new one — never the other
        # way round — so the two never simultaneously claim is_current=1 for
        # the same lineage and trip the idx_cf_cards_lineage_current unique
        # index against themselves. A genuine concurrent edit (two PATCHes
        # racing on the same lineage) still trips that index on the second
        # transaction's INSERT, which is caught below and refused (409)
        # rather than silently leaving two "current" tips in one lineage.
        conn.execute("UPDATE card_factory_cards SET is_current = 0 WHERE id = ?", (old["id"],))
        try:
            cur = conn.execute(
                "INSERT INTO card_factory_cards "
                "(ask_id, ask_revision, lineage_id, card_revision, supersedes_id, is_current, "
                "card_text, gate_exit_code, gate_output, status) "
                "VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)",
                (old["ask_id"], ask_revision, old["lineage_id"], old["card_revision"] + 1,
                 old["id"], card_text, exit_code, output, status),
            )
            new_id = cur.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            return jsonify({
                "error": "concurrent edit on this card — another edit landed first, retry"
            }), 409

        # Core state is committed. Filesystem moves happen after, and their
        # own DB updates commit separately — a crash here leaves a
        # self-consistent DB (saved_path simply not yet updated) rather than
        # a file the DB doesn't know about being treated as authoritative.
        if old["saved_path"]:
            new_path = _archive_to_history(old["saved_path"])
            conn.execute(
                "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
                (new_path, old["id"]),
            )
            conn.commit()

        if status == "pass":
            saved_path = _save_to_inbox(new_id, ask["project"], card_text)
            conn.execute(
                "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
                (saved_path, new_id),
            )
            conn.commit()
        row = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (new_id,)
        ).fetchone()
        return jsonify({"card": _card_dict(row, ask_revision)}), 201
    finally:
        conn.close()


@card_factory_bp.route("/api/cardfactory/cards/<int:card_id>/regate", methods=["POST"])
def regate_card(card_id: int):
    """Re-verifies a row's existing text against the spine in place —
    no new revision. Never (re)adds a file to the active inbox unless the
    row is still the lineage's current tip and its ask hasn't moved on."""
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    conn = _db()
    try:
        row = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()
        if not row:
            return jsonify({"error": "card not found"}), 404
        if not row["card_text"]:
            return jsonify({"error": "card has no text to re-gate"}), 400

        ask_revision = _ask_revision(conn, row["ask_id"])
        status, exit_code, output = _run_gate(row["card_text"])
        # Commit the verdict before touching the filesystem (see generate_card
        # / edit_card for why): the DB row stays the authority even if the
        # process dies before a file move/write below completes.
        conn.execute(
            "UPDATE card_factory_cards SET gate_exit_code = ?, gate_output = ?, "
            "status = ?, updated_at = datetime('now') WHERE id = ?",
            (exit_code, output, status, card_id),
        )
        conn.commit()
        is_current = bool(row["is_current"])
        stale = row["ask_revision"] != ask_revision
        if status != "pass" and row["saved_path"]:
            # The verdict flipped away from PASS (e.g. the gate script or the
            # spine content it checks against changed) — a file that used to
            # look dispatch-ready must not keep sitting in the active inbox.
            new_path = _archive_to_history(row["saved_path"])
            conn.execute(
                "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
                (new_path, card_id),
            )
            conn.commit()
        elif status == "pass" and not row["saved_path"] and is_current and not stale:
            ask = conn.execute(
                "SELECT project FROM card_factory_asks WHERE id = ?", (row["ask_id"],)
            ).fetchone()
            saved_path = _save_to_inbox(
                card_id, ask["project"] if ask else "card", row["card_text"]
            )
            conn.execute(
                "UPDATE card_factory_cards SET saved_path = ? WHERE id = ?",
                (saved_path, card_id),
            )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_id,)
        ).fetchone()
        return jsonify({"card": _card_dict(row, ask_revision)})
    finally:
        conn.close()
