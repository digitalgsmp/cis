#!/usr/bin/env python3
"""continuity_store.py — append-only development continuity log (WB.1C).

Not a second task queue: queue_items/queue_item_events remain the sole task
authority (see tools/queue/queue_set.py). This module records the DURING-WORK
record a queue item's body_md does not carry — proposals, decisions, verified
results, unfinished work, contradictions, user instructions and reconciliation
dispositions — scoped to a task (a queue item_num) so two external developers
(Claude Code, ChatGPT/Codex) can discover each other's consequential changes
without waiting for Eric to relay them or for session closeout.

Schema: runtime/schema/migrations/0039_dev_continuity.sql. That migration has
NOT been applied to the live spine (data/cis_memory.db). This module refuses
to create the schema against the live spine path unless the caller passes
allow_prod_init=True explicitly (see init_schema) — a safety guard, not a
formality, because the task that built this module was explicitly told not
to seed events into production.

Concurrency: revision is a monotonic-per-task counter assigned inside a
BEGIN IMMEDIATE transaction, which SQLite serializes at the file-lock level —
a second writer's transaction blocks until the first commits, then computes
its own next revision from the now-current max. That is what makes "two
concurrent publishes cannot lose data" true without a retry loop.

Idempotency: a caller-supplied request_id is checked before any write. Same
request_id + identical (task, kind, status, actor, summary, body,
evidence_refs, source_refs, against_revision) content replays the existing
row (no duplicate). Same request_id with ANY of those fields changed is a
hard error — silently accepting it would let a retry with edited content,
a different author, or a different evidence/reconciliation target
masquerade as the original request (WB.1C-R1 remediation 1).
"""
import hashlib
import json
import os
import sqlite3

DEFAULT_DB = os.environ.get("CIS_SPINE_PATH", "/mnt/projects/cis/data/cis_memory.db")

_KINDS = {
    "proposal", "decision", "verified_result", "unfinished_work",
    "contradiction", "user_instruction", "reconciliation",
}

_SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "runtime", "schema", "migrations", "0039_dev_continuity.sql",
)


class ContinuityError(Exception):
    pass


class NotInitializedError(ContinuityError):
    """The dev_continuity_* tables do not exist on this connection's database."""


class StaleRevisionError(ContinuityError):
    def __init__(self, task, expected, actual):
        self.task, self.expected, self.actual = task, expected, actual
        super().__init__(
            f"stale expected_prev_revision for task {task!r}: "
            f"caller expected {expected}, current latest is {actual}"
        )


class ConflictingRequestError(ContinuityError):
    def __init__(self, task, request_id):
        self.task, self.request_id = task, request_id
        super().__init__(
            f"request_id {request_id!r} for task {task!r} was already used "
            "with different content — a retry must resend identical content, "
            "not a revised one"
        )


class ProductionGuardError(ContinuityError):
    def __init__(self, db_path):
        super().__init__(
            f"refusing to initialize dev_continuity_* schema on {db_path!r} "
            "(looks like the production spine). Pass allow_prod_init=True "
            "only if this is a deliberate, reviewed activation step."
        )


def connect(db_path=None):
    # isolation_level=None (autocommit) so the explicit BEGIN IMMEDIATE in
    # publish_event() is the real transaction boundary — sqlite3's default
    # implicit-transaction wrapping would otherwise fight it.
    conn = sqlite3.connect(db_path or DEFAULT_DB, timeout=10, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def is_initialized(conn):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name='dev_continuity_events'"
    ).fetchone()
    return row is not None


def _looks_like_production(db_path):
    if db_path is None:
        return True
    return os.path.abspath(db_path) == os.path.abspath(DEFAULT_DB)


def init_schema(conn, db_path=None, allow_prod_init=False):
    """Create dev_continuity_* tables from the staged migration file.

    Refuses on the well-known production spine path unless allow_prod_init
    is explicitly True. Idempotent (CREATE TABLE/INDEX IF NOT EXISTS).
    """
    if _looks_like_production(db_path) and not allow_prod_init:
        raise ProductionGuardError(db_path or DEFAULT_DB)
    with open(_SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def _require_initialized(conn):
    if not is_initialized(conn):
        raise NotInitializedError(
            "dev_continuity_events does not exist on this database. This is "
            "either an uninitialized live spine (expected — 0039 is staged, "
            "not applied) or a fixture that forgot to call init_schema()."
        )


def latest_revision(conn, task):
    _require_initialized(conn)
    row = conn.execute(
        "SELECT MAX(revision) FROM dev_continuity_events WHERE task=?", (task,)
    ).fetchone()
    return row[0] or 0


def _content_hash(task, kind, status, actor, summary, body, evidence_refs, source_refs,
                   against_revision):
    """Hash every caller-controlled field whose change would alter the
    meaning, provenance, authorship, reconciliation target, or evidence of
    the publication (WB.1C-R1 remediation 1). Deliberately excludes
    generated fields (row id, assigned revision, created_at) — those are
    not caller-controlled and a retry cannot "change" them.

    evidence_refs/source_refs are canonicalized by sorting: a citation list
    is a set of references, not an ordered sequence, so [1,2] and [2,1] are
    semantically identical content and must hash identically. Coerced to
    str for the sort key so a caller mixing int/str refs cannot raise.
    """
    payload = json.dumps(
        {
            "task": task, "kind": kind, "status": status, "actor": actor,
            "summary": summary, "body": body or "",
            "evidence_refs": sorted(evidence_refs or [], key=str),
            "source_refs": sorted(source_refs or [], key=str),
            "against_revision": against_revision,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _row_to_dict(row):
    d = dict(row)
    for k in ("evidence_refs_json", "source_refs_json"):
        if d.get(k):
            try:
                d[k.replace("_json", "")] = json.loads(d[k])
            except (TypeError, ValueError):
                d[k.replace("_json", "")] = []
    return d


def publish_event(conn, *, task, kind, status, actor, summary, body="",
                   evidence_refs=None, source_refs=None,
                   expected_prev_revision, request_id=None,
                   against_revision=None):
    """Append one development-continuity event for `task`.

    expected_prev_revision must equal the task's current latest revision
    (0 if none published yet) or StaleRevisionError is raised — optimistic
    concurrency: the caller must have read the state it is building on.

    request_id (optional) makes a retry with IDENTICAL content a no-op that
    returns the original row (replay=True in the result); identical
    request_id with DIFFERENT content raises ConflictingRequestError.
    """
    _require_initialized(conn)
    if kind not in _KINDS:
        raise ContinuityError(f"unknown kind {kind!r}; known: {sorted(_KINDS)}")
    if kind == "reconciliation" and against_revision is None:
        raise ContinuityError(
            "kind='reconciliation' requires against_revision — the revision "
            "this reconciliation is a disposition against"
        )

    evidence_refs = evidence_refs or []
    source_refs = source_refs or []
    req_hash = (
        _content_hash(task, kind, status, actor, summary, body, evidence_refs,
                      source_refs, against_revision)
        if request_id else None
    )

    conn.execute("BEGIN IMMEDIATE")
    try:
        if request_id:
            existing = conn.execute(
                "SELECT * FROM dev_continuity_events WHERE task=? AND request_id=?",
                (task, request_id),
            ).fetchone()
            if existing is not None:
                conn.execute("ROLLBACK")
                if existing["request_hash"] == req_hash:
                    d = _row_to_dict(existing)
                    d["replay"] = True
                    return d
                raise ConflictingRequestError(task, request_id)

        current_latest = conn.execute(
            "SELECT MAX(revision) FROM dev_continuity_events WHERE task=?", (task,)
        ).fetchone()[0] or 0
        if current_latest != expected_prev_revision:
            conn.execute("ROLLBACK")
            raise StaleRevisionError(task, expected_prev_revision, current_latest)

        new_revision = current_latest + 1
        cur = conn.execute(
            "INSERT INTO dev_continuity_events "
            "(task, revision, kind, status, actor, summary, body, "
            " evidence_refs_json, source_refs_json, against_revision, "
            " request_id, request_hash) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (task, new_revision, kind, status, actor, summary, body,
             json.dumps(evidence_refs), json.dumps(source_refs),
             against_revision, request_id, req_hash),
        )
        conn.commit()
    except sqlite3.OperationalError:
        conn.rollback()
        raise

    row = conn.execute(
        "SELECT * FROM dev_continuity_events WHERE id=?", (cur.lastrowid,)
    ).fetchone()
    d = _row_to_dict(row)
    d["replay"] = False
    return d


def record_reconciliation(conn, *, task, actor, against_revision, disposition,
                           note, evidence_refs=None, source_refs=None,
                           expected_prev_revision, request_id=None):
    """Record an explicit disposition against a specific prior revision.

    disposition is free text but should be one of preserve/adapt/conflict/
    unknown per the task's evidence-classification vocabulary, or
    'acknowledged'/'superseded' for a plain acceptance. Re-running prepare
    is NOT a reconciliation — this is the only path that counts as one,
    and it always names the revision it is responding to.
    """
    return publish_event(
        conn, task=task, kind="reconciliation", status=disposition, actor=actor,
        summary=f"reconciled against revision {against_revision}: {disposition}",
        body=note, evidence_refs=evidence_refs, source_refs=source_refs,
        expected_prev_revision=expected_prev_revision, request_id=request_id,
        against_revision=against_revision,
    )


def list_events(conn, task, since_revision=None):
    _require_initialized(conn)
    if since_revision is not None:
        rows = conn.execute(
            "SELECT * FROM dev_continuity_events WHERE task=? AND revision>? "
            "ORDER BY revision", (task, since_revision),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM dev_continuity_events WHERE task=? ORDER BY revision",
            (task,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]
