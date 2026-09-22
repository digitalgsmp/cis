#!/usr/bin/env python3
"""canonical_state.py — single canonical read model over CIS's DB-backed
authority (queue 4.29 / CARD_01_SINGLE_AUTHORITY_CONTRACT.md).

The spine database (data/cis_memory.db) is authoritative. AGENTS.md, the
HCP packet, docs/UNIFIED_BUILD_LIST.md, DEV-PIVOT_STATUS.md, and any
operating-state markdown are projections of it, never independent truth.
This module is the one place that assembles "what does CIS currently look
like" from live DB state, so those projections (and, later, Card 02's
external recovery packet and Card 03's Workbench screen) can all read the
same answer instead of each re-deriving their own.

Contract:
- Read-only, always. Nothing in this module writes to the database.
- Never parses a generated file as an input to project/authoritative
  state (AGENTS.md, the HCP files, UNIFIED_BUILD_LIST.md, and any
  operating-state markdown are outputs of this module's data, never
  inputs to it) -- so a hand-edited or conflicting generated file cannot
  become authority. The one narrow exception is get_artifact_freshness(),
  which reads a generated file's *own declared revision stamp* purely to
  report whether it's stale -- it never treats the file's prose content
  as a fact about the project.
- "Authoritative state" (from AUTHORITY_TABLES) and "observed runtime
  health" (from get_observed_runtime_health()) are kept in clearly
  separate sections of get_canonical_state()'s output, and the health
  section is never written back to any table merely by being observed.

Usage:
    python3 tools/state/canonical_state.py                 # full state as JSON
    python3 tools/state/canonical_state.py --revision       # just the state revision
    python3 tools/state/canonical_state.py --freshness       # generated-artifact freshness only
"""
import argparse
import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB = os.environ.get("CIS_SPINE_PATH", str(REPO_ROOT / "data" / "cis_memory.db"))

# Tables treated as authoritative sources for the read model, each paired
# with the column that marks recency. Used both to compute the state
# revision and to report per-source freshness.
#
# Discovered live on 2026-09-21 (see evidence.md): next_actions,
# open_questions, active_blockers and dev_pivot_status went quiet for
# weeks to months (last activity 2026-06-18 to 2026-07-04) while
# queue_items and dev_continuity_events are updated same-day. A table
# existing and being named "open_questions" does not make its rows
# current. This module does not silently drop dormant sources -- it
# reports dormancy on every response so a caller can decide, rather than
# an unseen judgment baked into the query.
AUTHORITY_TABLES = {
    "queue_items": "extracted_at",
    "queue_item_events": "changed_at",
    "dev_continuity_events": "created_at",
    "session_closeouts": "started_at",
    "project_decisions": "decided_at",
    "project_state": "created_at",
    "open_questions": "opened_at",
    "active_blockers": "created_at",
    "next_actions": "created_at",
    "dev_pivot_status": "updated_at",
}

DORMANT_DAYS = 30  # no activity this long -> flagged dormant, not dropped

NOT_DONE_STATUSES = ("OPEN", "HALF_DONE", "UNASSESSED")

# Live gateway ports this module treats as OBSERVED runtime health, never
# authoritative state (see docstring). Matches the Hermes role map in
# CLAUDE.md.
GATEWAY_PORTS = {
    8642: "prime_chat",
    8643: "reviewer1",
    8644: "brainstorm",
    8645: "drafter",
    8646: "implementer",
    8647: "reviewer2",
    8648: "verifier",
}


def _connect(db_path=None):
    conn = sqlite3.connect(db_path or DB)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _parse_ts(ts):
    """Best-effort parse of the mixed timestamp formats actually present in
    this spine ('YYYY-MM-DD HH:MM:SS' and ISO8601 with a 'T' and offset)."""
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(ts, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def table_freshness(conn):
    """Row count + last activity + dormancy flag for every AUTHORITY_TABLES
    entry. Deterministic given fixed DB content (no wall-clock value feeds
    the revision half of this -- only row_count/last_activity do)."""
    now = datetime.now(timezone.utc)
    out = {}
    for table, col in AUTHORITY_TABLES.items():
        try:
            row = conn.execute(
                f"SELECT COUNT(*), MAX({col}) FROM {table}"
            ).fetchone()
            count, last = row[0], row[1]
        except sqlite3.Error:
            out[table] = {"row_count": None, "last_activity": None,
                           "dormant": None, "error": "table unreadable"}
            continue
        last_dt = _parse_ts(last)
        days_since = (now - last_dt).total_seconds() / 86400 if last_dt else None
        out[table] = {
            "row_count": count,
            "last_activity": last,
            "days_since_activity": round(days_since, 1) if days_since is not None else None,
            "dormant": (days_since is not None and days_since > DORMANT_DAYS),
        }
    return out


def compute_state_revision(conn):
    """Deterministic content fingerprint over AUTHORITY_TABLES.

    CORRECTED 2026-09-21 per ChatGPT's independent review of Card 01: the
    original version hashed (row_count, MAX(recency_col)) per table. That
    is not a content fingerprint -- an in-place UPDATE that changes a
    row's mutable fields (status, body_md, resolution, ...) without
    changing row count or touching that table's own recency column left
    the revision unchanged (reproduced: update queue_items.body_md/
    need_status/status_changed_at/status_changed_by on a fixed row with
    fixed extracted_at -- revision did not change). See evidence.md Sec 2.

    Fixed by hashing every row's full column content instead of a count +
    a single timestamp, ordered by rowid for determinism. These tables are
    all small (dozens to low hundreds of rows; see table_freshness), so
    hashing full content on every call is cheap and bounded. No wall-clock
    or random input, so two calls against identical DB content always
    produce the same revision (required for render_build_list.py's
    byte-exact --verify)."""
    parts = []
    for table in sorted(AUTHORITY_TABLES):
        try:
            cur = conn.execute(f"SELECT * FROM {table} ORDER BY rowid")
            cols = [d[0] for d in cur.description]
            row_reprs = [
                "|".join(f"{c}={row[i]!r}" for i, c in enumerate(cols))
                for row in cur.fetchall()
            ]
            table_repr = f"{table}[{len(row_reprs)}]::" + "\x1f".join(row_reprs)
        except sqlite3.Error:
            table_repr = f"{table}:ERR"
        parts.append(table_repr)
    digest = hashlib.sha256("\x1e".join(parts).encode("utf-8", errors="replace")).hexdigest()
    return digest[:16]


def get_queue_focus(conn):
    by_status = {r["need_status"] or "UNPARSED": r["n"] for r in conn.execute(
        "SELECT need_status, COUNT(*) n FROM queue_items GROUP BY need_status"
    ).fetchall()}
    open_items = [_row_to_dict(r) for r in conn.execute(
        f"""SELECT item_num, tier, title, need_status FROM queue_items
            WHERE need_status IN {NOT_DONE_STATUSES}
            ORDER BY tier, item_num"""
    ).fetchall()]
    return {"counts_by_status": by_status, "open_items": open_items}


def _list_tasks_with_continuity(conn):
    try:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT task FROM dev_continuity_events"
        ).fetchall()]
    except sqlite3.Error:
        return []


def _run_dev_cli(*args, db_path=None, timeout=30):
    """Invoke tools/development/cli.py's read-only subcommands as a module.

    dev_continuity_events is an append-only log: a discovery's *current*
    disposition depends on reconciliation/supersession logic this module
    does not reimplement (a first version tried a direct SQL read and
    reported 4 discoveries as still blocking WB.1's closeout when the
    project's own closeout-check already showed 0 blockers -- see
    evidence.md). CARD_01 itself requires "read existing authority, not
    duplicate mutable authority"; shelling out to the sanctioned CLI is
    how that's honored here instead of re-deriving the resolution rules.
    """
    cmd = [sys.executable, "-m", "tools.development.cli"]
    if db_path:
        cmd += ["--db", db_path]
    cmd += list(args)
    return subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=str(REPO_ROOT))


def get_closeout_status(conn, db_path=None):
    """Per-task ready-to-close status via the sanctioned `closeout-check`
    subcommand (CARD 3/4) -- the deterministic gate, not a re-derivation."""
    out = {}
    for task in _list_tasks_with_continuity(conn):
        r = _run_dev_cli("closeout-check", task, db_path=db_path)
        try:
            out[task] = json.loads(r.stdout)
        except json.JSONDecodeError:
            out[task] = {"error": (r.stderr or r.stdout).strip()}
    return out


def get_unresolved_discoveries(conn, db_path=None):
    """Per-task unresolved discoveries via the sanctioned `discoveries`
    subcommand (CARD 3), default (unresolved-only) mode."""
    out = []
    for task in _list_tasks_with_continuity(conn):
        r = _run_dev_cli("discoveries", task, db_path=db_path)
        if r.returncode != 0:
            out.append({"task": task, "error": (r.stderr or r.stdout).strip()})
            continue
        try:
            items = json.loads(r.stdout)
        except json.JSONDecodeError:
            items = []
        for item in items:
            item.setdefault("task", task)
            out.append(item)
    return out


def get_open_blocked_deferred(conn, db_path=None):
    queue_open = [_row_to_dict(r) for r in conn.execute(
        f"""SELECT item_num, tier, title, need_status AS status FROM queue_items
            WHERE need_status IN {NOT_DONE_STATUSES}
            ORDER BY tier, item_num"""
    ).fetchall()]
    return {"queue_open_or_blocked": queue_open,
            "unresolved_discoveries": get_unresolved_discoveries(conn, db_path=db_path),
            "closeout_status_by_task": get_closeout_status(conn, db_path=db_path)}


def get_recent_verified_closed(conn, limit=10):
    queue_done = [_row_to_dict(r) for r in conn.execute(
        """SELECT item_num, tier, title, status_changed_at FROM queue_items
           WHERE need_status = 'DONE'
           ORDER BY status_changed_at DESC LIMIT ?""", (limit,)
    ).fetchall()]
    closeouts = [_row_to_dict(r) for r in conn.execute(
        """SELECT id, started_at, completed_at, status, commit_hash
           FROM session_closeouts WHERE status = 'PASS'
           ORDER BY started_at DESC LIMIT ?""", (limit,)
    ).fetchall()]
    verified = [_row_to_dict(r) for r in conn.execute(
        """SELECT task, revision, summary, created_at
           FROM dev_continuity_events WHERE kind = 'verified_result'
           ORDER BY created_at DESC LIMIT ?""", (limit,)
    ).fetchall()]
    return {"queue_items_done": queue_done, "session_closeouts_pass": closeouts,
            "dev_continuity_verified_results": verified}


def get_active_decisions(conn):
    rows = [_row_to_dict(r) for r in conn.execute(
        """SELECT id, label, decision, reason, status, decided_at
           FROM project_decisions WHERE status != 'SUPERSEDED'
           ORDER BY decided_at DESC"""
    ).fetchall()]
    return rows


def get_open_questions(conn, dormant_flag):
    rows = [_row_to_dict(r) for r in conn.execute(
        """SELECT id, question, status, opened_at FROM open_questions
           WHERE status = 'OPEN' ORDER BY opened_at DESC"""
    ).fetchall()]
    for r in rows:
        r["source_dormant"] = dormant_flag
    return rows


def get_discoveries_requiring_attention(conn, db_path=None):
    return get_unresolved_discoveries(conn, db_path=db_path)


def get_active_blockers(conn, dormant_flag):
    """Currently-ACTIVE rows from active_blockers, tagged with the same
    dormancy signal table_freshness already computes for this table --
    included honestly even when dormant (a blocker going quiet is not the
    same as it being resolved), never silently dropped."""
    rows = [_row_to_dict(r) for r in conn.execute(
        """SELECT id, description, status, created_at FROM active_blockers
           WHERE status = 'ACTIVE' ORDER BY created_at DESC"""
    ).fetchall()]
    for r in rows:
        r["source_dormant"] = dormant_flag
    return rows


RECENT_TASK_ACTIVITY_LIMIT = 20  # kept under recovery_packet._CAP (25)


def _item_detail(conn, item_num):
    row = conn.execute(
        "SELECT item_num, tier, title, need_status, body_md, status_changed_at "
        "FROM queue_items WHERE item_num = ?", (item_num,)
    ).fetchone()
    return _row_to_dict(row)


def get_current_focus(conn):
    """The one place 'where are we right now' is answered from live
    authority, for a Card 04 packet reader to actually locate current work
    -- never inferred from queue tier order or generated-file prose.

    - current_queue_item_pointer: the latest project_state row with
      key='current_queue_item' -- the same row an operator sets via
      queue_set.py/set_current_item.py. Whichever row has the newest
      created_at wins; this table is not superseded_at-maintained in
      practice (older pointer rows are simply left with superseded_at
      NULL), so recency by timestamp is the real signal, not a flag.
    - current_queue_item_detail: that pointer's own queue_items row
      (title, need_status, full body_md -- which is where an item's own
      recorded scope/return-point language actually lives).
    - recent_task_activity: the most recent dev_continuity_events rows
      across ALL tasks (not just the pointer task), so whichever task has
      truly recent work -- e.g. 4.32's Card 04 correction rounds -- shows
      up on its own recency, with no task named here in advance.
    - recent_task_queue_items: the queue_items row (status/title/body_md)
      for every distinct task named in recent_task_activity, so a task's
      own recorded OPEN/DONE status and return-point text travel with its
      activity instead of requiring a second lookup.
    - a named fetch handle for the full per-task history this is bounded
      from, so a capped view never silently implies there is nothing more.
    """
    pointer_row = conn.execute(
        "SELECT id, key, value, source, created_at FROM project_state "
        "WHERE key = 'current_queue_item' ORDER BY created_at DESC, id DESC LIMIT 1"
    ).fetchone()
    pointer = _row_to_dict(pointer_row)
    pointer_detail = _item_detail(conn, pointer["value"]) if pointer else None

    recent_activity = [_row_to_dict(r) for r in conn.execute(
        "SELECT id, task, revision, kind, status, actor, summary, created_at "
        "FROM dev_continuity_events ORDER BY id DESC LIMIT ?",
        (RECENT_TASK_ACTIVITY_LIMIT,),
    ).fetchall()]
    recent_tasks = sorted({r["task"] for r in recent_activity})
    recent_task_queue_items = {t: _item_detail(conn, t) for t in recent_tasks}

    return {
        "current_queue_item_pointer": pointer,
        "current_queue_item_detail": pointer_detail,
        "recent_task_activity": recent_activity,
        "recent_task_activity_fetch_handle": (
            "python3 -m tools.development.cli events <task>  -- full event "
            "history for any task named in recent_task_activity above"
        ),
        "recent_task_queue_items": recent_task_queue_items,
        "note": (
            "current_queue_item_pointer is read straight from the latest "
            "project_state row with key='current_queue_item' -- never "
            "advanced, inferred, or defaulted by this module. "
            "recent_task_activity is the most recent dev_continuity_events "
            "rows across all tasks, ordered by id, capped at "
            f"{RECENT_TASK_ACTIVITY_LIMIT}; a task's own queue_items row "
            "(need_status, body_md) is looked up for each distinct task "
            "named there."
        ),
    }


def get_observed_runtime_health():
    """Live, NON-authoritative observations. Never persisted to any table
    merely by being observed -- callers that want a fact remembered must
    go through a sanctioned write path (queue_set.py, discovery-record,
    etc.), not this function."""
    gateways = {}
    for port, role in GATEWAY_PORTS.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            gateways[role] = {"port": port, "listening": True}
        except OSError:
            gateways[role] = {"port": port, "listening": False}
        finally:
            s.close()

    try:
        git_status = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        repo_dirty = bool(git_status.strip())
        dirty_files = len(git_status.strip().splitlines()) if repo_dirty else 0
    except Exception:
        repo_dirty, dirty_files = None, None

    db_reachable = Path(DB).exists()

    return {
        "_note": "observed live at call time -- not authoritative, not persisted",
        "gateways": gateways,
        "repo_dirty": repo_dirty,
        "dirty_file_count": dirty_files,
        "spine_db_reachable": db_reachable,
    }


def get_artifact_freshness(conn, current_revision):
    """Report whether known generated projections declare the current
    state revision. Reads only each artifact's own declared stamp (a
    revision/run marker), never its prose, as input."""
    out = {}

    # docs/UNIFIED_BUILD_LIST.md: render_build_list.py already has a
    # byte-exact --verify mode; reuse it rather than re-implement.
    render_script = REPO_ROOT / "tools" / "queue" / "render_build_list.py"
    if render_script.exists():
        try:
            r = subprocess.run(
                [sys.executable, str(render_script), "--verify"],
                capture_output=True, text=True, timeout=30,
                cwd=str(REPO_ROOT),
            )
            out["docs/UNIFIED_BUILD_LIST.md"] = {
                "fresh": r.returncode == 0,
                "detail": r.stdout.strip(),
            }
        except Exception as e:
            out["docs/UNIFIED_BUILD_LIST.md"] = {"fresh": None, "detail": str(e)}

    # EXPORT_MANIFEST.json (and by extension AGENTS.md / the HCP packet /
    # DEV-PIVOT_STATUS.md, which all share its run) declares a
    # state_revision field once generate_all.py has been re-run after
    # this module existed. Older manifests predate the field.
    manifest_path = REPO_ROOT / "runtime" / "manifests" / "EXPORT_MANIFEST.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            declared = manifest.get("state_revision")
            out["runtime/manifests/EXPORT_MANIFEST.json (AGENTS.md/HCP/DEV-PIVOT)"] = {
                "declared_revision": declared,
                "current_revision": current_revision,
                "fresh": (declared == current_revision) if declared else None,
                "detail": "manifest predates state_revision field" if declared is None else "",
            }
        except Exception as e:
            out["runtime/manifests/EXPORT_MANIFEST.json (AGENTS.md/HCP/DEV-PIVOT)"] = {
                "fresh": None, "detail": str(e),
            }

    # CURRENT-OPERATING-STATE.md: a hand-written, one-time snapshot, not
    # regenerated by any script. It cannot be "fresh" or "stale" in the
    # revision sense above -- report its nature honestly instead.
    snapshot = REPO_ROOT / "CURRENT-OPERATING-STATE.md"
    if snapshot.exists():
        out["CURRENT-OPERATING-STATE.md"] = {
            "fresh": None,
            "detail": "manual point-in-time snapshot, not a generated projection; "
                      "not kept in sync automatically",
        }

    return out


def get_canonical_state(db_path=None):
    conn = _connect(db_path)
    try:
        revision = compute_state_revision(conn)
        freshness = table_freshness(conn)
        state = {
            "revision": revision,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "source": "data/cis_memory.db (see AUTHORITY_TABLES)",
            "queue_focus": get_queue_focus(conn),
            "open_blocked_deferred": get_open_blocked_deferred(conn, db_path=db_path),
            "recent_verified_closed": get_recent_verified_closed(conn),
            "active_decisions": get_active_decisions(conn),
            "open_questions": get_open_questions(conn, freshness["open_questions"]["dormant"]),
            "active_blockers": get_active_blockers(conn, freshness["active_blockers"]["dormant"]),
            "discoveries_requiring_attention": get_discoveries_requiring_attention(conn, db_path=db_path),
            "current_focus": get_current_focus(conn),
            "source_table_freshness": freshness,
            "generated_artifact_freshness": get_artifact_freshness(conn, revision),
            "observed_runtime_health": get_observed_runtime_health(),
        }
        return state
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--revision", action="store_true", help="print only the state revision")
    ap.add_argument("--freshness", action="store_true", help="print only generated-artifact freshness")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()

    if args.revision:
        conn = _connect(args.db)
        try:
            print(compute_state_revision(conn))
        finally:
            conn.close()
        return 0

    if args.freshness:
        conn = _connect(args.db)
        try:
            rev = compute_state_revision(conn)
            print(json.dumps(get_artifact_freshness(conn, rev), indent=2))
        finally:
            conn.close()
        return 0

    print(json.dumps(get_canonical_state(args.db), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
