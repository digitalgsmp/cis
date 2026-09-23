"""
card_runner.py — reusable server-side card dispatch runner (queue item
WB.1B-2, incl. its bounded-control addendum on card C2).

Dispatches a gated card (`cards/inbox/*.md`) to a non-interactive CLI target
(`claude -p` or `codex exec`) in `implement` or `review` mode, with the
rules text from `cards/EXECUTION_RULES.md` / `cards/REVIEW_RULES.md`
prepended, and enforces the limits that are actually enforceable — never an
invented one. Self-contained, same pattern as the sibling
`card_factory_app.py`/`workbench_app.py` modules: its own DB helper, its own
auth check, no import of either sibling. Not registered into
`container_app.py` — staged only, matching the rest of WB.1B (activation is
a later card's job).

Capabilities verified live/via --help in WB-1B-0-preflight/FACTS.md §4 and
§12 (this card's own lookup):
  - Neither `claude` nor `codex` has a CLI flag that caps turn count. A
    requested `max_turns` can only ever be *observed* after a run completes
    (claude's JSON result reports `num_turns`; codex's usage/turn reporting
    was never verified live and is always recorded as unknown) — never
    enforced. Callers must explicitly acknowledge this
    (`max_turns_ack_observation_only=True`) or dispatch is refused; this
    runner never silently drops a requested cap or invents a flag for it.
  - `claude` has a real spend cap, `--max-budget-usd` (documented via
    --help, never exercised live — no paid calls in this card). `codex` has
    none. A dispatch that sets no `budget_usd` must explicitly pass
    `accept_time_only_control=True`, so "wall-clock timeout is the only
    enforced limit" is always a deliberate choice, never a silent default.
  - Wall-clock timeout is always enforced by this runner itself (killing
    the child's process group), for both targets, regardless of any
    native cap.
  - `--safe-mode` (claude only, documented via --help) is used instead of
    the base card's original `--bare` wording: `--bare` forces
    ANTHROPIC_API_KEY/apiKeyHelper auth and never reads OAuth, and this
    deployment authenticates via OAuth (WB.1B-1's own finding) — `--bare`
    would break auth here. `--safe-mode`'s coverage of AGENTS.md, and
    codex's AGENTS.md handling entirely, are NOT verified (FACTS.md §12);
    no minimal-context flag is claimed for codex at all.

Legacy note: this path previously held an unrelated, much simpler
dry-run EVIDENCE-bullet checker (no dispatch, no limits). Its logic is
preserved verbatim below under the `legacy-evidence-check` subcommand
(preimage also saved to this card's `backups/`) — nothing deleted, just
no longer the bare/default CLI behavior, since positional-arg sniffing
between the old and new CLI shapes would be fragile. Its previous
unconditional `main()` call at import time (which made the file
unimportable as a module) is fixed: everything now runs only under
`if __name__ == "__main__":`.

Corrected by card WB.1B-2A (dispatch corrections): dispatch is validated
against the live card_factory_cards/card_factory_asks row (current
revision, PASS verdict, matching ask revision, matching content) instead of
trusting a caller-supplied path — "an inbox pathname is not proof of
validity." Every run gets its own unique evidence folder
(data/agent_handoffs/<card_id>/run-<id>-<mode>/) so an implementation and a
separately authorized review of it can coexist without either overwriting
the other's evidence. Setup/launch failures (folder creation, spawning the
child) now record failure and release the one-run-at-a-time lock instead of
leaving it stuck.
"""
import argparse
import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

from flask import Blueprint, jsonify, request

from workbench_auth import check_auth

# ── Config ───────────────────────────────────────────────────────────────

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")
# NOTE: the module-level API_KEY constant was REMOVED deliberately — see the
# matching note in workbench_app.py. Auth reads the environment per request via
# workbench_auth.check_auth().

CARDS_DIR = os.environ.get("CIS_CARD_RUNNER_CARDS_DIR", os.path.join(REPO_ROOT, "cards"))
EXECUTION_RULES_PATH = os.path.join(CARDS_DIR, "EXECUTION_RULES.md")
REVIEW_RULES_PATH = os.path.join(CARDS_DIR, "REVIEW_RULES.md")
HANDOFFS_DIR = os.environ.get(
    "CIS_CARD_RUNNER_HANDOFFS_DIR", os.path.join(REPO_ROOT, "data", "agent_handoffs")
)
LOG_DIR = os.environ.get(
    "CIS_CARD_RUNNER_LOG_DIR", os.path.join(REPO_ROOT, "data", "agent_handoffs", "_card_runner_logs")
)

CLAUDE_BIN = "claude"  # on PATH (FACTS.md §4)
CODEX_BIN = "/usr/lib/chatgpt/resources/codex"  # NOT on PATH (FACTS.md §4) — absolute path required

DEFAULT_TIMEOUT_SECONDS = 1800  # 30 min, per-card override
DEFAULT_MODEL_CLAUDE = "claude-haiku-4-5-20251001"  # cheapest capable (matches WB.1B-1's own choice)
# codex: FACTS.md has no documented "cheapest capable" alias for this install's
# config.toml (no `model =` line); no default is invented — a codex dispatch
# either passes --model explicitly or takes codex's own configured default.
DEFAULT_MODEL_CODEX = None

MAX_STORED_MESSAGE_CHARS = 20000  # bound on final_message/log excerpt kept in the DB row

# Capabilities are checked, not assumed (bounded-control addendum). Every
# value here traces to a FACTS.md citation; nothing is inferred.
CAPABILITIES = {
    "claude": {
        "max_turns": {
            "enforcement": "observation_only",
            "note": "no CLI flag exists (`claude --help` has none, FACTS.md §4); "
                    "num_turns is only reported after the run completes, in the JSON result.",
        },
        "budget_usd": {
            "enforcement": "native",
            "note": "--max-budget-usd <amount>, only with -p/--print (FACTS.md §4). "
                    "Documented via --help; never exercised live in this card (no paid calls).",
        },
    },
    "codex": {
        "max_turns": {
            "enforcement": "unavailable",
            "note": "no CLI flag exists (`codex exec --help` confirmed live, FACTS.md §12).",
        },
        "budget_usd": {
            "enforcement": "unavailable",
            "note": "no CLI flag exists (`codex exec --help` confirmed live, FACTS.md §12).",
        },
    },
}
# Whether a target's own JSON output has ever been confirmed live to report
# token/turn usage. claude's has (FACTS.md §2, from WB.1A's own run); codex's
# has not (FACTS.md §4/§12) — codex rows always record usage as unknown.
USAGE_REPORTING_VERIFIED = {"claude": True, "codex": False}

ACTIVE_STATUSES = ("queued", "running", "stopping")
TERMINAL_STATUSES = ("completed", "failed", "timeout", "stopped", "stop_failed")

# Test-only global fallback for dispatch()'s `_test_command` seam, so a test
# driving the Flask route (which has no `_test_command` field in its JSON
# body, by design — an HTTP caller must never be able to substitute the
# child command) can still avoid spawning a real, paid `claude`/`codex`
# call. Never read from request JSON; never set outside tests.
_TEST_COMMAND_OVERRIDE = None


class RunnerError(Exception):
    """Base class for dispatch-time rejections (400s)."""


class RevisionMismatch(RunnerError):
    """Card content no longer matches the fingerprint it was authorized against (409)."""


class RunnerBusy(RunnerError):
    """Another run is already active in this repo (409)."""


class NotFound(RunnerError):
    """No such run id (404)."""


# ── DB ───────────────────────────────────────────────────────────────────

def _db(db_path: str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _check_auth():
    """Delegates to the shared fail-CLOSED contract (runtime/workbench_auth.py).

    Previously fail-open, which mattered most here: /api/cardrunner/dispatch
    spawns a real agent subprocess. An unset CIS_PIPELINE_API_KEY is now a 503,
    not an implicit allow."""
    return check_auth()


def _run_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for json_col in ("limits_json", "permitted_files_json", "permitted_commands_json", "out_of_scope_json"):
        key = json_col[: -len("_json")]
        raw = d.pop(json_col, None)
        if raw:
            try:
                d[key] = json.loads(raw)
            except (TypeError, ValueError):
                d[key] = None
        else:
            d[key] = None
    d["active_lock"] = bool(d.get("active_lock"))
    d["cancel_requested"] = bool(d.get("cancel_requested"))
    d["usage_unknown"] = bool(d.get("usage_unknown"))
    d["card_completion_status"] = _read_card_completion_status(d.get("run_dir"))
    return d


def _read_card_completion_status(run_dir):
    """Best-effort read of the dispatched agent's own completion.json
    (status READY_FOR_VERIFICATION/BLOCKED) from THIS run's own evidence
    folder — a process exit code of 0 only means the CLI didn't crash, not
    that the agent itself concluded the card was ready. Local file read
    only, never an LLM call ('Do not poll an LLM for status')."""
    if not run_dir:
        return None
    path = os.path.join(REPO_ROOT, run_dir, "completion.json")
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("status") if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


# ── Card fingerprinting ──────────────────────────────────────────────────

def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()


def _card_id_from_path(card_path: str) -> str:
    return os.path.splitext(os.path.basename(card_path))[0]


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Scope check (bounded-control addendum: fingerprints, not status text) ─

def _git_dirty_paths() -> list:
    out = subprocess.run(
        ["git", "status", "--short"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    paths = []
    for line in out.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:  # rename/copy status lines
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    return paths


def _scope_snapshot(permitted_files) -> dict:
    """Content fingerprints (sha256) of every path git already shows as
    dirty/untracked PLUS every card-permitted path, tracked or untracked
    alike. Comparing these hashes before/after (not just git-status text)
    catches an already-dirty file being modified again during the run,
    which would otherwise look identical in git status before and after."""
    paths = set(_git_dirty_paths()) | set(permitted_files or [])
    fingerprints = {}
    for p in paths:
        full = os.path.join(REPO_ROOT, p)
        fingerprints[p] = _sha256_file(full) if os.path.isfile(full) else None
    return fingerprints


def _diff_scope(before: dict, after: dict, permitted_files, permitted_prefix: str = None) -> list:
    """A run's own handoff folder (permitted_prefix, e.g.
    'data/agent_handoffs/<card_id>/') is always implicitly in scope — every
    dispatched card is instructed to write its evidence.md/completion.json/
    backups/ there — on top of whatever files the card itself names."""
    permitted = set(permitted_files or [])
    changed = []
    for p in set(before) | set(after):
        if p in permitted:
            continue
        if permitted_prefix and p.startswith(permitted_prefix):
            continue
        if before.get(p) != after.get(p):
            changed.append(p)
    return sorted(changed)


# ── Process-group lifecycle ─────────────────────────────────────────────

def _pgroup_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _kill_pgroup(pgid: int, grace_seconds: float = 5.0) -> bool:
    """Best-effort SIGTERM then SIGKILL. Returns True once the group is
    confirmed dead (or was already gone)."""
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not _pgroup_alive(pgid):
            return True
        time.sleep(0.2)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    time.sleep(0.5)
    return not _pgroup_alive(pgid)


# ── Permission plan (narrowest mode proven to run unattended) ───────────

def _permission_plan(target: str, mode: str, permitted_commands) -> dict:
    if target == "claude":
        if mode == "review":
            return {
                "field": "acceptEdits",
                "flags": ["--permission-mode", "acceptEdits",
                          "--allowedTools", "Read Glob Grep",
                          "--disallowedTools", "Edit Write Bash"],
                "risk": "acceptEdits would auto-accept edit prompts, so Edit/Write/Bash are "
                        "explicitly disallowed and only Read/Glob/Grep are allowed — a review "
                        "run cannot modify the repo regardless of the permission mode.",
            }
        allowed = ["Edit", "Read", "Write", "Glob", "Grep"]
        flags = ["--permission-mode", "acceptEdits"]
        if permitted_commands:
            allowed.append(" ".join(f"Bash({c} *)" for c in permitted_commands))
            flags += ["--allowedTools", " ".join(allowed)]
        else:
            flags += ["--allowedTools", " ".join(allowed), "--disallowedTools", "Bash"]
        return {
            "field": "acceptEdits",
            "flags": flags,
            "risk": "acceptEdits auto-accepts file-edit permission prompts — the narrowest mode "
                    "proven to run unattended (WB.1A's own dispatch used it headless, exit 0, no "
                    "hangs; manual/dontAsk/plan block on prompts headlessly; bypassPermissions / "
                    "--dangerously-skip-permissions are wider than needed and were not used). "
                    "Bash is scoped to the card's permitted_commands, or disallowed entirely if none.",
        }
    else:  # codex
        if mode == "review":
            return {
                "field": "read-only",
                "flags": ["-s", "read-only"],
                "risk": "read-only sandbox: the child process cannot write to the repo at all; "
                        "this runner captures its final message via --output-last-message and "
                        "writes review.md itself.",
            }
        return {
            "field": "workspace-write",
            "flags": ["-s", "workspace-write", "--approve-for-me"],
            "risk": "workspace-write sandbox + --approve-for-me (routes approvals through "
                    "workspace-write review) is the narrowest combination that runs unattended; "
                    "danger-full-access and --dangerously-bypass-approvals-and-sandbox are wider "
                    "than needed and were not used.",
        }


# ── Command construction ────────────────────────────────────────────────

def _build_command(target, mode, model, session_id, perm, budget_usd, final_message_path):
    if target == "claude":
        cmd = [CLAUDE_BIN, "-p", "--model", model, "--output-format", "json",
               "--safe-mode", "--session-id", session_id]
        cmd += perm["flags"]
        if budget_usd is not None:
            cmd += ["--max-budget-usd", str(budget_usd)]
        # No -r/-c/--resume/--continue/--fork-session: every dispatch is a
        # fresh session by omission, never a continuation.
        return cmd
    # codex
    cmd = [CODEX_BIN, "exec", "--json", "--ephemeral", "-C", REPO_ROOT,
           "-o", final_message_path, "--skip-git-repo-check"]
    cmd += perm["flags"]
    if model:
        cmd += ["-m", model]
    # No `resume`/`fork` subcommand used: every dispatch is a fresh session.
    return cmd


def _parse_target_output(target, stdout_bytes, final_message_path=None):
    result = {
        "num_turns": None, "input_tokens": None, "cached_input_tokens": None,
        "output_tokens": None, "reasoning_tokens": None, "cost_usd": None,
        "final_message": None, "usage_unknown": True,
    }
    if target == "claude":
        try:
            data = json.loads((stdout_bytes or b"").decode("utf-8", "replace"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return result
        if not isinstance(data, dict):
            return result
        usage = data.get("usage") or {}
        result["num_turns"] = data.get("num_turns")
        result["input_tokens"] = usage.get("input_tokens")
        result["cached_input_tokens"] = usage.get("cache_read_input_tokens")
        result["output_tokens"] = usage.get("output_tokens")
        result["reasoning_tokens"] = usage.get("reasoning_output_tokens")
        result["cost_usd"] = data.get("total_cost_usd")
        msg = data.get("result")
        result["final_message"] = msg[:MAX_STORED_MESSAGE_CHARS] if isinstance(msg, str) else None
        result["usage_unknown"] = not usage and result["cost_usd"] is None
        return result
    # codex: usage/turns never verified live (FACTS.md §4/§12) — always unknown.
    if final_message_path and os.path.isfile(final_message_path):
        try:
            with open(final_message_path, "r", errors="replace") as f:
                result["final_message"] = f.read()[:MAX_STORED_MESSAGE_CHARS]
        except OSError:
            pass
    return result


# ── Finalization (runs in a background thread) ──────────────────────────

def _finalize(run_id, proc, started_monotonic, scope_before, permitted_files, mode,
              target, timeout_s, log_path, final_message_path, run_dir, db_path):
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
        timed_out = False
    except subprocess.TimeoutExpired:
        _kill_pgroup(proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            stdout, stderr = b"", b""
        timed_out = True

    wall_seconds = time.monotonic() - started_monotonic
    try:
        with open(log_path, "wb") as f:
            f.write(b"--- stdout ---\n")
            f.write(stdout or b"")
            f.write(b"\n--- stderr ---\n")
            f.write(stderr or b"")
    except OSError:
        pass

    # Only this run's own evidence folder is implicitly in scope — a
    # sibling run's folder (e.g. the implementation a review is reading)
    # must still be flagged if this run somehow modifies it, so "never
    # overwrite prior evidence" is enforced structurally, not just by rule.
    permitted_prefix = f"{run_dir}/"
    scope_after = _scope_snapshot(permitted_files)
    out_of_scope = _diff_scope(scope_before, scope_after, permitted_files, permitted_prefix)
    parsed = _parse_target_output(target, stdout, final_message_path)

    conn = _db(db_path)
    try:
        row = conn.execute("SELECT * FROM card_runner_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None or row["status"] not in ("running", "stopping"):
            return  # already finalized elsewhere (e.g. stop() completed first) — do not clobber

        if row["cancel_requested"]:
            final_status = "stopped"
        elif timed_out:
            final_status = "timeout"
        elif proc.returncode == 0:
            final_status = "completed"
        else:
            final_status = "failed"

        if mode == "review" and final_status == "completed" and parsed["final_message"] is not None:
            try:
                review_path = os.path.join(REPO_ROOT, run_dir, "review.md")
                with open(review_path, "w") as f:
                    f.write(parsed["final_message"])
            except OSError:
                pass

        conn.execute(
            "UPDATE card_runner_runs SET status = ?, active_lock = NULL, exit_code = ?, "
            "finished_at = datetime('now'), wall_seconds = ?, num_turns = ?, input_tokens = ?, "
            "cached_input_tokens = ?, output_tokens = ?, reasoning_tokens = ?, cost_usd = ?, "
            "usage_unknown = ?, final_message = ?, out_of_scope_json = ?, updated_at = datetime('now') "
            "WHERE id = ? AND status IN ('running', 'stopping')",
            (final_status, proc.returncode, wall_seconds, parsed["num_turns"], parsed["input_tokens"],
             parsed["cached_input_tokens"], parsed["output_tokens"], parsed["reasoning_tokens"],
             parsed["cost_usd"], int(parsed["usage_unknown"]), parsed["final_message"],
             json.dumps(out_of_scope), run_id),
        )
        conn.commit()
    finally:
        conn.close()


# ── Public API ───────────────────────────────────────────────────────────

def _mark_setup_failed(run_id, db_path, message, lock_released=True):
    """Setup/launch failures (folder creation, spawning the child, or
    recording that it started) must record failure — never leave a row
    stuck at status='queued' with no explanation. The lock is released
    (status='failed') only when no child remains; if a child was spawned
    and its termination could not be confirmed, the lock must stay held
    (status='stop_failed', same meaning stop() already gives that status)
    rather than let a second dispatch start while that process might still
    be running uncontrolled."""
    conn = _db(db_path)
    try:
        conn.execute(
            "UPDATE card_runner_runs SET status = ?, active_lock = ?, error = ?, "
            "finished_at = datetime('now'), updated_at = datetime('now') "
            "WHERE id = ? AND status IN ('queued', 'running')",
            ("failed" if lock_released else "stop_failed", None if lock_released else 1,
             message[:MAX_STORED_MESSAGE_CHARS], run_id),
        )
        conn.commit()
    finally:
        conn.close()


def dispatch(card_factory_card_id, mode, target, *, request_id, expected_card_fingerprint,
             authorized_by, review_of_run_id=None, model=None,
             wall_clock_timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
             max_turns=None, max_turns_ack_observation_only=False,
             budget_usd=None, accept_time_only_control=False,
             permitted_files=None, permitted_commands=None,
             db_path=None, _test_command=None):
    """Dispatch one card to one CLI target, once. Never retries, never
    chains to another dispatch. Returns (run_dict, duplicate: bool).

    `card_factory_card_id` identifies a row in card_factory_cards
    (migration 0036) — dispatch is validated against that row and its ask
    live, at dispatch time: it must be the lineage's current revision, its
    gate verdict must be 'pass', and its ask_revision must still match the
    ask's current revision (not stale). The card's file path is then taken
    from that row's own saved_path, never from caller input — a filename
    sitting in cards/inbox/ is not, on its own, proof that dispatch is
    still authorized.

    `review_of_run_id`, required when mode='review', names the specific
    prior implement-mode run (same card_factory_card_id) being reviewed.
    Its evidence folder is referenced, never overwritten; this run gets its
    own separate evidence folder.

    _test_command, if given, replaces the computed argv entirely — used
    only by tests, so they can exercise the real spawn/timeout/kill/
    finalize pipeline against a harmless real subprocess instead of a
    paid CLI call. Never set by the CLI or the Flask routes.
    """
    permitted_files = list(permitted_files or [])
    permitted_commands = list(permitted_commands or [])

    if not request_id:
        raise RunnerError("request_id is required")
    # Reusing a request_id must not start a second run: this is checked
    # first, before any other validation, so a replay is a pure idempotent
    # read — it never re-validates the fingerprint/limits/etc. of whatever
    # the caller happened to pass this time.
    conn = _db(db_path)
    try:
        existing = conn.execute(
            "SELECT * FROM card_runner_runs WHERE request_id = ?", (request_id,)
        ).fetchone()
    finally:
        conn.close()
    if existing:
        return _run_dict(existing), True

    if not card_factory_card_id:
        raise RunnerError("card_factory_card_id is required")
    if mode not in ("implement", "review"):
        raise RunnerError(f"unknown mode {mode!r}; must be 'implement' or 'review'")
    if target not in ("claude", "codex"):
        raise RunnerError(f"unknown target {target!r}; must be 'claude' or 'codex'")
    if not authorized_by:
        raise RunnerError("authorized_by is required: every dispatch needs explicit authorization on record")
    if not expected_card_fingerprint:
        raise RunnerError(
            "expected_card_fingerprint is required: dispatch must be bound to the exact card "
            "revision the caller authorized, not whatever is currently on disk"
        )
    if mode == "implement" and not permitted_files:
        raise RunnerError("implement dispatch requires at least one permitted_files entry")
    if mode == "implement" and review_of_run_id is not None:
        raise RunnerError("review_of_run_id is only valid for review-mode dispatch")
    if mode == "review" and not review_of_run_id:
        raise RunnerError("review dispatch requires review_of_run_id (the implementation run being reviewed)")
    if not wall_clock_timeout_seconds or wall_clock_timeout_seconds <= 0:
        raise RunnerError("wall_clock_timeout_seconds must be a positive number")

    cap = CAPABILITIES[target]
    if max_turns is not None:
        enforcement = cap["max_turns"]["enforcement"]
        if enforcement == "unavailable":
            raise RunnerError(f"max_turns unsupported for target={target}: {cap['max_turns']['note']}")
        if enforcement == "observation_only" and not max_turns_ack_observation_only:
            raise RunnerError(
                f"max_turns has no enforcement flag for target={target} ({cap['max_turns']['note']}); "
                "pass max_turns_ack_observation_only=True to dispatch anyway with turns only observed "
                "after the run, or omit max_turns"
            )
    if budget_usd is not None:
        if cap["budget_usd"]["enforcement"] != "native":
            raise RunnerError(f"budget_usd unsupported for target={target}: {cap['budget_usd']['note']}")
    elif not accept_time_only_control:
        raise RunnerError(
            "no spend cap requested and none is enforceable without one; pass "
            "accept_time_only_control=True to dispatch with wall-clock timeout as the only "
            "enforced limit, or set budget_usd (claude only)"
        )

    resolved_model = model or (DEFAULT_MODEL_CLAUDE if target == "claude" else DEFAULT_MODEL_CODEX)
    perm = _permission_plan(target, mode, permitted_commands)
    session_id = str(uuid.uuid4())

    limits_record = {
        "wall_clock_timeout_seconds": wall_clock_timeout_seconds,
        "max_turns_requested": max_turns,
        "max_turns_enforcement": cap["max_turns"]["enforcement"],
        "budget_usd": budget_usd,
        "budget_enforcement": cap["budget_usd"]["enforcement"] if budget_usd is not None else "not_requested",
        "time_only_control": budget_usd is None,
        "usage_reporting_verified": USAGE_REPORTING_VERIFIED[target],
    }

    conn = _db(db_path)
    try:
        # ── Validate against the database, live — not against a filename.
        # "An inbox pathname is not proof of validity": current revision,
        # PASS verdict, matching ask revision, matching approved content.
        cf_row = conn.execute(
            "SELECT * FROM card_factory_cards WHERE id = ?", (card_factory_card_id,)
        ).fetchone()
        if cf_row is None:
            raise RunnerError(f"card_factory_cards id {card_factory_card_id} not found")
        # A review is read-only and, by definition, about a SPECIFIC
        # already-dispatched historical snapshot — it never runs new work
        # against "the current state of the ask," so the two checks below
        # that exist to keep IMPLEMENT from running stale work (is_current,
        # ask_revision-matches-live) are relaxed only for mode='review'.
        # Identity of what's being reviewed is still pinned unconditionally
        # by the fingerprint check a few lines down — never by "current" or
        # "latest revision" status, which a review specifically does not
        # require. Implement mode's own current-revision requirement is
        # entirely unchanged.
        if not cf_row["is_current"] and mode != "review":
            raise RevisionMismatch(
                f"card_factory_cards id {card_factory_card_id} is not the current revision of "
                "its lineage — it has been superseded by an edit"
            )
        if cf_row["status"] != "pass":
            raise RunnerError(
                f"card_factory_cards id {card_factory_card_id} status is {cf_row['status']!r}, "
                "not 'pass' — dispatch refused"
            )
        ask_row = conn.execute(
            "SELECT * FROM card_factory_asks WHERE id = ?", (cf_row["ask_id"],)
        ).fetchone()
        if ask_row is None:
            raise RunnerError(f"ask {cf_row['ask_id']} for card_factory_cards id {card_factory_card_id} not found")
        if cf_row["ask_revision"] != ask_row["revision"] and mode != "review":
            raise RevisionMismatch(
                f"card_factory_cards id {card_factory_card_id} is stale: generated against ask "
                f"revision {cf_row['ask_revision']}, the ask is now at revision {ask_row['revision']}"
            )
        card_text = cf_row["card_text"]
        if not card_text:
            raise RunnerError(f"card_factory_cards id {card_factory_card_id} has no card_text on record")
        db_fingerprint = _sha256_text(card_text)
        if db_fingerprint != expected_card_fingerprint:
            raise RevisionMismatch(
                f"card_factory_cards id {card_factory_card_id} content does not match "
                "expected_card_fingerprint — it changed since this dispatch was authorized; a "
                "PASS gate result is not itself approval to dispatch"
            )
        saved_path = cf_row["saved_path"]
        if not saved_path:
            raise RunnerError(f"card_factory_cards id {card_factory_card_id} has no saved_path on record")
        card_path = saved_path if os.path.isabs(saved_path) else os.path.join(REPO_ROOT, saved_path)
        if not os.path.isfile(card_path):
            raise RunnerError(
                f"card file listed in the database does not exist on disk: {saved_path} — "
                "the database, not the filesystem, is authoritative here"
            )
        with open(card_path, "r") as f:
            file_text = f.read()
        if _sha256_text(file_text) != db_fingerprint:
            raise RevisionMismatch(
                f"on-disk file at {saved_path} does not match the database's card_text for "
                f"card_factory_cards id {card_factory_card_id} — possible out-of-band edit; refused"
            )
        project = ask_row["project"]

        impl_run_dir = None
        if mode == "review":
            impl_row = conn.execute(
                "SELECT * FROM card_runner_runs WHERE id = ?", (review_of_run_id,)
            ).fetchone()
            if impl_row is None:
                raise RunnerError(f"review_of_run_id {review_of_run_id} not found")
            if impl_row["mode"] != "implement":
                raise RunnerError("review_of_run_id must reference an implement-mode run")
            if impl_row["card_factory_card_id"] != card_factory_card_id:
                raise RunnerError(
                    "review_of_run_id does not belong to the same card_factory_card_id being reviewed"
                )
            if impl_row["status"] not in TERMINAL_STATUSES:
                raise RunnerError(
                    f"review_of_run_id {review_of_run_id} has not finished yet "
                    f"(status={impl_row['status']!r}); cannot review an in-progress run"
                )
            impl_run_dir = impl_row["run_dir"]

        active = conn.execute("SELECT id FROM card_runner_runs WHERE active_lock = 1").fetchone()
        if active:
            raise RunnerBusy(
                f"another run is already active (run id {active['id']}); refused — "
                "one run at a time per repo"
            )

        try:
            cur = conn.execute(
                "INSERT INTO card_runner_runs "
                "(request_id, card_factory_card_id, review_of_run_id, card_path, card_fingerprint, "
                "mode, target, model, project, limits_json, permitted_files_json, "
                "permitted_commands_json, authorized_by, permission_mode, permission_risk, "
                "status, active_lock) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'queued', 1)",
                (request_id, card_factory_card_id, review_of_run_id, card_path, db_fingerprint,
                 mode, target, resolved_model, project,
                 json.dumps(limits_record), json.dumps(permitted_files), json.dumps(permitted_commands),
                 authorized_by, perm["field"], perm["risk"]),
            )
            run_id = cur.lastrowid
            card_id = _card_id_from_path(card_path)
            run_dir = f"data/agent_handoffs/{card_id}/run-{run_id}-{mode}"
            conn.execute("UPDATE card_runner_runs SET run_dir = ? WHERE id = ?", (run_dir, run_id))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            existing = conn.execute(
                "SELECT * FROM card_runner_runs WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing:
                return _run_dict(existing), True
            active = conn.execute("SELECT id FROM card_runner_runs WHERE active_lock = 1").fetchone()
            if active:
                raise RunnerBusy(
                    f"another run is already active (run id {active['id']}); refused — "
                    "one run at a time per repo"
                )
            raise  # neither dedup nor the active-run lock explains this — a real schema/data error
    finally:
        conn.close()

    # Filesystem effects only happen after the DB row is durably committed
    # (same "commit first, file write after" ordering WB.1B-1 uses for its
    # own inbox writes). From here on, any failure must record status
    # 'failed' + release active_lock (never leave the lock stuck), and must
    # not leave an orphan process running untracked.
    handoff_dir = os.path.join(REPO_ROOT, run_dir)
    if mode == "review":
        card_md_text = (
            f"Folder: {run_dir}/\n"
            f"Implementation to review: {impl_run_dir}/ (read its evidence.md, completion.json, "
            "and the files completion.json's changed_files lists)\n\n"
            f"{card_text}"
        )
    else:
        card_md_text = f"Folder: {run_dir}/\n\n{card_text}"
    # Every setup step below runs before any child process exists, so a
    # failure anywhere in this block is always the "no child remains" case
    # — mark failed and release the lock. Nothing here may run unguarded:
    # a missing EXECUTION_RULES.md/REVIEW_RULES.md file, or a log directory
    # that can't be created, must not leave the row stuck at status='queued'
    # holding the lock forever (the original bug this block fixes).
    try:
        os.makedirs(handoff_dir, exist_ok=False)
        with open(os.path.join(handoff_dir, "CARD.md"), "w") as f:
            f.write(card_md_text)
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path = os.path.join(LOG_DIR, f"run-{run_id}.log")
        final_message_path = (
            os.path.join(LOG_DIR, f"run-{run_id}.final_message.txt") if target == "codex" else None
        )
        # The prompt (rules + card) is always built and always sent on
        # stdin, independent of which argv runs — only the CLI target's
        # real flags are test-substitutable, never whether the rules were
        # prepended.
        rules_path = EXECUTION_RULES_PATH if mode == "implement" else REVIEW_RULES_PATH
        with open(rules_path) as f:
            prompt = f.read() + "\n\n" + card_md_text
        scope_before = _scope_snapshot(permitted_files)
    except OSError as e:
        _mark_setup_failed(run_id, db_path, f"setup failed before launch: {e}")
        raise RunnerError(f"setup failed before launch: {e}") from e

    effective_test_command = _test_command if _test_command is not None else _TEST_COMMAND_OVERRIDE
    cmd = effective_test_command if effective_test_command is not None else _build_command(
        target, mode, resolved_model, session_id, perm, budget_usd, final_message_path
    )

    started = time.monotonic()
    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=REPO_ROOT, start_new_session=True,
        )
    except OSError as e:
        _mark_setup_failed(run_id, db_path, f"failed to launch the process: {e}")
        raise RunnerError(f"failed to launch the process: {e}") from e

    try:
        proc.stdin.write(prompt.encode())
    except BrokenPipeError:
        pass
    try:
        proc.stdin.close()
    except BrokenPipeError:
        pass
    proc.stdin = None  # already closed; communicate() below must not touch it again

    try:
        conn = _db(db_path)
        try:
            conn.execute(
                "UPDATE card_runner_runs SET status = 'running', pid = ?, pgid = ?, session_id = ?, "
                "log_path = ?, started_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
                (proc.pid, proc.pid, session_id, log_path, run_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM card_runner_runs WHERE id = ?", (run_id,)).fetchone()
        finally:
            conn.close()
    except Exception as e:
        # The process is already spawned but the DB never learned its pid —
        # leaving it running would be an orphan no stop()/status call could
        # ever reach. Kill it before giving up, and only release the lock
        # once termination is actually confirmed — if the kill itself
        # can't be confirmed, the lock must stay held (status='stop_failed',
        # same meaning stop() already gives that status) rather than let a
        # second dispatch start while this process might still be running.
        confirmed_dead = _kill_pgroup(proc.pid)
        detail = (f"failed to record run start after spawning the process "
                  f"(process was killed): {e}") if confirmed_dead else (
                  f"failed to record run start after spawning the process, AND could not confirm "
                  f"the process was killed — the one-run-at-a-time lock remains held: {e}")
        _mark_setup_failed(run_id, db_path, detail, lock_released=confirmed_dead)
        raise RunnerError(detail) from e

    thread = threading.Thread(
        target=_finalize,
        args=(run_id, proc, started, scope_before, permitted_files, mode, target,
              wall_clock_timeout_seconds, log_path, final_message_path, run_dir, db_path),
        daemon=True,
    )
    thread.start()

    return _run_dict(row), False


def stop(run_id, db_path=None):
    """Durably cancels a run: persists cancellation before signaling so a
    worker restart, browser reload, or a late completion from the child
    cannot resurrect it as successful. Idempotent — stopping an
    already-terminal run just reports its current state."""
    conn = _db(db_path)
    try:
        row = conn.execute("SELECT * FROM card_runner_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise NotFound(f"no such run: {run_id}")
        if row["status"] not in ("queued", "running", "stopping"):
            return _run_dict(row)

        conn.execute(
            "UPDATE card_runner_runs SET status = 'stopping', cancel_requested = 1, "
            "updated_at = datetime('now') WHERE id = ?",
            (run_id,),
        )
        conn.commit()

        pgid = row["pgid"]
        confirmed = _kill_pgroup(pgid) if pgid else True
        final_status = "stopped" if confirmed else "stop_failed"
        active_lock = None if confirmed else 1
        conn.execute(
            "UPDATE card_runner_runs SET status = ?, active_lock = ?, "
            "finished_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
            (final_status, active_lock, run_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM card_runner_runs WHERE id = ?", (run_id,)).fetchone()
        return _run_dict(row)
    finally:
        conn.close()


def run_status(run_id, db_path=None):
    conn = _db(db_path)
    try:
        row = conn.execute("SELECT * FROM card_runner_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise NotFound(f"no such run: {run_id}")
        return _run_dict(row)
    finally:
        conn.close()


# A worker's `final_message` (the CLI's own last-turn text, already on the
# run row) is NOT the saved evidence — it can be as generic as "Done." An
# implementer is instructed to write evidence.md/completion.json into its
# own run_dir; a review run has card_runner._finalize() itself write
# review.md there. This reads those three fixed, named artifacts back —
# nothing else, no arbitrary path — for a specific run_id the caller must
# already have authorization to read status for (same _check_auth as every
# other route here). A completion.json's own `status` claim
# (READY_FOR_VERIFICATION/BLOCKED) is the implementer's self-report, same
# as `card_completion_status` already exposed on the run — never treated
# as independent verification by anything that reads it.
ARTIFACT_NAMES = ("evidence.md", "completion.json", "review.md")
MAX_ARTIFACT_READ_CHARS = 100_000


def run_artifact(run_id, name, db_path=None):
    """Bounded, run-id-scoped read of one of a fixed set of named files
    from that run's OWN recorded run_dir — never an arbitrary path. Returns
    a dict with `found` always present and explicit: False (with `content`
    None) covers every "nothing to show" case — no run_dir yet recorded, no
    such file on disk, or an OSError reading it (never a silent 500 for a
    file that just isn't there, e.g. review.md on an implement-mode run)."""
    if name not in ARTIFACT_NAMES:
        raise RunnerError(f"unknown artifact name {name!r}; must be one of {ARTIFACT_NAMES}")
    conn = _db(db_path)
    try:
        row = conn.execute("SELECT run_dir FROM card_runner_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise NotFound(f"no such run: {run_id}")
        run_dir = row["run_dir"]
    finally:
        conn.close()

    if not run_dir:
        return {"name": name, "found": False, "content": None, "truncated": False,
                "error": "this run has no run_dir recorded (it never started)"}

    run_dir_abs = os.path.realpath(os.path.join(REPO_ROOT, run_dir))
    path = os.path.realpath(os.path.join(run_dir_abs, name))
    # `name` is drawn from the fixed ARTIFACT_NAMES allowlist (no path
    # separators possible in any of its values, and Flask's own route
    # converter for this segment already excludes "/"), so escaping
    # run_dir_abs is not actually reachable through this parameter — this
    # check is defense in depth, not the only thing preventing it.
    if os.path.commonpath([run_dir_abs, path]) != run_dir_abs:
        raise RunnerError("artifact path resolves outside its run directory")

    if not os.path.isfile(path):
        return {"name": name, "found": False, "content": None, "truncated": False, "error": None}
    try:
        with open(path, "r", errors="replace") as f:
            content = f.read(MAX_ARTIFACT_READ_CHARS + 1)
    except OSError as e:
        return {"name": name, "found": False, "content": None, "truncated": False,
                "error": f"could not read: {type(e).__name__}: {e}"}
    truncated = len(content) > MAX_ARTIFACT_READ_CHARS
    if truncated:
        content = content[:MAX_ARTIFACT_READ_CHARS]
    return {"name": name, "found": True, "content": content, "truncated": truncated, "error": None}


def _generation_totals(conn, project=None) -> dict:
    """Read-only merge of card_factory_cards' own usage columns (WB.1B-1)
    into this runner's totals, per the bounded-control addendum's
    requirement to include Generate attempts in available totals. Never
    executes or authorizes a Generate call — that remains
    card_factory_app.py's own request_id-gated route; a human calling it is
    itself that attempt's explicit authorization, the same pattern this
    runner requires for dispatch."""
    totals = {}
    query = (
        "SELECT cfc.usage_input_tokens, cfc.usage_output_tokens, cfc.usage_cost_usd, cfa.project "
        "FROM card_factory_cards cfc JOIN card_factory_asks cfa ON cfa.id = cfc.ask_id"
    )
    params = ()
    if project:
        query += " WHERE cfa.project = ?"
        params = (project,)
    try:
        rows = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        return totals  # card_factory_* tables absent from this DB (e.g. migration 0036 not applied)
    for r in rows:
        key = r["project"] or "_unknown"
        t = totals.setdefault(key, {
            "generate_attempts": 0, "input_tokens": 0, "output_tokens": 0,
            "cost_usd": 0.0, "unknown_usage_attempts": 0,
        })
        t["generate_attempts"] += 1
        if r["usage_input_tokens"] is None and r["usage_output_tokens"] is None and r["usage_cost_usd"] is None:
            t["unknown_usage_attempts"] += 1
        else:
            t["input_tokens"] += r["usage_input_tokens"] or 0
            t["output_tokens"] += r["usage_output_tokens"] or 0
            t["cost_usd"] += r["usage_cost_usd"] or 0.0
    return totals


def ledger(project=None, db_path=None) -> dict:
    """Never polls an LLM for status — pure DB reads. Includes Generate
    (card_factory_cards), Implement and Review (card_runner_runs) attempts
    in one set of per-project totals, per the bounded-control addendum."""
    conn = _db(db_path)
    try:
        if project:
            rows = conn.execute(
                "SELECT * FROM card_runner_runs WHERE project = ? ORDER BY id DESC", (project,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM card_runner_runs ORDER BY id DESC").fetchall()
        runs = [_run_dict(r) for r in rows]

        totals = {}
        for r in runs:
            key = r["project"] or "_unknown"
            t = totals.setdefault(key, {
                "runs": 0, "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
                "reasoning_tokens": 0, "cost_usd": 0.0, "unknown_usage_runs": 0,
            })
            t["runs"] += 1
            if r["usage_unknown"]:
                t["unknown_usage_runs"] += 1
            else:
                t["input_tokens"] += r["input_tokens"] or 0
                t["cached_input_tokens"] += r["cached_input_tokens"] or 0
                t["output_tokens"] += r["output_tokens"] or 0
                t["reasoning_tokens"] += r["reasoning_tokens"] or 0
                t["cost_usd"] += r["cost_usd"] or 0.0

        gen_totals = _generation_totals(conn, project)
        for key, gen in gen_totals.items():
            totals.setdefault(key, {
                "runs": 0, "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
                "reasoning_tokens": 0, "cost_usd": 0.0, "unknown_usage_runs": 0,
            })["generation"] = gen
        for key, t in totals.items():
            t.setdefault("generation", gen_totals.get(key))

        return {"runs": runs, "totals_by_project": totals}
    finally:
        conn.close()


# ── Flask routes: dispatch, stop, run status, ledger. No UI. ───────────

card_runner_bp = Blueprint("card_runner", __name__)


@card_runner_bp.route("/api/cardrunner/dispatch", methods=["POST"])
def route_dispatch():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    data = request.get_json(silent=True) or {}
    try:
        row, duplicate = dispatch(
            card_factory_card_id=data.get("card_factory_card_id"),
            mode=data.get("mode"),
            target=data.get("target"),
            request_id=data.get("request_id"),
            expected_card_fingerprint=data.get("expected_card_fingerprint"),
            authorized_by=data.get("authorized_by"),
            review_of_run_id=data.get("review_of_run_id"),
            model=data.get("model"),
            wall_clock_timeout_seconds=data.get("wall_clock_timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            max_turns=data.get("max_turns"),
            max_turns_ack_observation_only=bool(data.get("max_turns_ack_observation_only")),
            budget_usd=data.get("budget_usd"),
            accept_time_only_control=bool(data.get("accept_time_only_control")),
            permitted_files=data.get("permitted_files"),
            permitted_commands=data.get("permitted_commands"),
        )
        return jsonify({"run": row, "duplicate": duplicate}), (200 if duplicate else 201)
    except (RevisionMismatch, RunnerBusy) as e:
        return jsonify({"error": str(e)}), 409
    except RunnerError as e:
        return jsonify({"error": str(e)}), 400


@card_runner_bp.route("/api/cardrunner/runs/<int:run_id>/stop", methods=["POST"])
def route_stop(run_id):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    try:
        return jsonify({"run": stop(run_id)})
    except NotFound as e:
        return jsonify({"error": str(e)}), 404


@card_runner_bp.route("/api/cardrunner/runs/<int:run_id>", methods=["GET"])
def route_status(run_id):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    try:
        return jsonify({"run": run_status(run_id)})
    except NotFound as e:
        return jsonify({"error": str(e)}), 404


@card_runner_bp.route("/api/cardrunner/runs/<int:run_id>/artifact/<artifact_name>", methods=["GET"])
def route_artifact(run_id, artifact_name):
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    try:
        return jsonify(run_artifact(run_id, artifact_name))
    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except RunnerError as e:
        return jsonify({"error": str(e)}), 400


@card_runner_bp.route("/api/cardrunner/runs", methods=["GET"])
def route_ledger():
    auth_err = _check_auth()
    if auth_err:
        return auth_err
    return jsonify(ledger(project=request.args.get("project")))


# ── Legacy: pre-WB.1B dry-run EVIDENCE checker (preserved verbatim) ─────
# Never executes BUILD. No dispatch, no limits — unrelated to everything
# above. Kept for anything that still wants it; reached only via the
# `legacy-evidence-check` subcommand now (see module docstring).

_LEGACY_FIELD = re.compile(r'^([A-Z][A-Z ]+):\s*(.*)$')


def _legacy_parse(path):
    card = {"path": str(path), "EVIDENCE": [], "BUILD": ""}
    cur = None
    for line in path.read_text().splitlines():
        m = _LEGACY_FIELD.match(line)
        if m:
            cur = m.group(1).strip()
            if m.group(2).strip():
                card[cur] = m.group(2).strip()
            continue
        if cur == "EVIDENCE" and line.strip().startswith("- "):
            card["EVIDENCE"].append(line.strip()[2:])
    return card


def _legacy_check(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        return r.returncode == 0, r.returncode
    except Exception as e:
        return False, str(e)


def _legacy_main(cards_dir, halt):
    import pathlib
    files = sorted(pathlib.Path(cards_dir).glob("*.md"))
    print(f"CARDS: {len(files)}")
    for f in files:
        c = _legacy_parse(f)
        if not c["EVIDENCE"]:
            print(f"SKIP  {f.name}  (no EVIDENCE)")
            continue
        results = [_legacy_check(e) for e in c["EVIDENCE"]]
        ok = all(r[0] for r in results)
        print(f"{'DONE ' if ok else 'TODO '} {f.name}  "
              f"({sum(r[0] for r in results)}/{len(results)})")
        if not ok and halt:
            print("HALT")
            sys.exit(1)


# ── CLI ──────────────────────────────────────────────────────────────────

def _cli():
    ap = argparse.ArgumentParser(prog="card_runner.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_legacy = sub.add_parser("legacy-evidence-check", help="pre-WB.1B dry-run EVIDENCE checker")
    p_legacy.add_argument("cards_dir")
    p_legacy.add_argument("--halt", action="store_true")

    p_dispatch = sub.add_parser("dispatch")
    p_dispatch.add_argument("--card-factory-card-id", type=int, required=True)
    p_dispatch.add_argument("--mode", required=True, choices=["implement", "review"])
    p_dispatch.add_argument("--target", required=True, choices=["claude", "codex"])
    p_dispatch.add_argument("--request-id", required=True)
    p_dispatch.add_argument("--authorized-by", required=True)
    p_dispatch.add_argument("--expected-card-fingerprint", required=True)
    p_dispatch.add_argument("--review-of-run-id", type=int)
    p_dispatch.add_argument("--model")
    p_dispatch.add_argument("--wall-clock-timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    p_dispatch.add_argument("--max-turns", type=int)
    p_dispatch.add_argument("--max-turns-ack-observation-only", action="store_true")
    p_dispatch.add_argument("--budget-usd", type=float)
    p_dispatch.add_argument("--accept-time-only-control", action="store_true")
    p_dispatch.add_argument("--permitted-files", nargs="*", default=[])
    p_dispatch.add_argument("--permitted-commands", nargs="*", default=[])

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("run_id", type=int)

    p_status = sub.add_parser("status")
    p_status.add_argument("run_id", type=int)

    p_ledger = sub.add_parser("ledger")
    p_ledger.add_argument("--project")

    args = ap.parse_args()

    if args.cmd == "legacy-evidence-check":
        _legacy_main(args.cards_dir, args.halt)
        return
    if args.cmd == "dispatch":
        row, duplicate = dispatch(
            args.card_factory_card_id, args.mode, args.target,
            request_id=args.request_id, expected_card_fingerprint=args.expected_card_fingerprint,
            authorized_by=args.authorized_by, review_of_run_id=args.review_of_run_id, model=args.model,
            wall_clock_timeout_seconds=args.wall_clock_timeout_seconds,
            max_turns=args.max_turns, max_turns_ack_observation_only=args.max_turns_ack_observation_only,
            budget_usd=args.budget_usd, accept_time_only_control=args.accept_time_only_control,
            permitted_files=args.permitted_files, permitted_commands=args.permitted_commands,
        )
        print(json.dumps({"run": row, "duplicate": duplicate}, indent=2))
    elif args.cmd == "stop":
        print(json.dumps({"run": stop(args.run_id)}, indent=2))
    elif args.cmd == "status":
        print(json.dumps({"run": run_status(args.run_id)}, indent=2))
    elif args.cmd == "ledger":
        print(json.dumps(ledger(project=args.project), indent=2))


if __name__ == "__main__":
    _cli()
