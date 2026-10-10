"""state_authority.py — the one place `project_state` current-record
authority is decided, and the one sanctioned way a single-valued key is
written.

WHY THIS MODULE EXISTS. Measured at dev_continuity_events revision 152, on
the spine, not inferred:

  * `database.insert_project_state` appended and never superseded, and
    `database.supersede_project_state` was a SEPARATE function with zero
    call sites anywhere in tools/ or runtime/. Supersession was therefore
    performed by caller convention — a raw UPDATE in
    tools/queue/set_current_item.py for its own key, and by hand for every
    other key. It held 31 of 32 times for `next_action` and failed once:
    rows 161 and 166 are both live. ~97% is what model compliance looks
    like.
  * Three readers resolved "current" by two different rules.
    `tools/state/build_path.py:_latest_state` ordered by created_at DESC
    and did not consult `superseded_at` at all;
    `database.get_project_state` and
    `tools/gates/gate_build_state_coherence.py` used
    `superseded_at IS NULL` + MAX(id). They agreed on the data of the day,
    so the divergence was latent — it goes live the moment a superseded row
    carries a later created_at than the live one.
  * Neither writer nor reader detected the conflict. build_path reported
    `next_action` as single-valued (row 166) with no indication row 161
    existed, and the coherence gate PASSED with both rows live.
  * The same weakness reaches the acceptance authority. A raw INSERT of an
    `external_dev_checkpoint` row claiming `lifecycle_state`
    REMOTE_VERIFIED for an arbitrary SHA left two live acceptance rows, and
    the newest-wins readers would then serve the forged SHA as the accepted
    baseline.

WHAT THIS MODULE DOES, AND WHAT IT DELIBERATELY DOES NOT DO.

  DOES: declares, per key, whether the authority contract requires exactly
  one live record (`KEY_CARDINALITY`); resolves a current record only when
  authority is unambiguous; returns a structured CONFLICT carrying the
  conflicting row ids when it is not; and performs a single-valued write as
  one atomic insert-and-supersede so a caller cannot forget the
  supersession half.

  DOES NOT: choose between conflicting rows, repair history, backfill a
  missing `superseded_by`, or write an acceptance record. A pre-existing
  ambiguity makes writes to that key FAIL CLOSED and reads to that key
  report CONFLICT; resolving it is an authority decision, not a cleanup
  this module is entitled to perform silently. Rows 161/166 are exactly
  that case and are untouched here.

NEWEST-ROW-WINS IS REJECTED, NOT RE-IMPLEMENTED SAFELY. Selection here
never consults `created_at` or MAX(id) to break a tie, because a tie IS the
defect. Two live rows for a single-valued key is a conflict whichever row is
newer, and a superseded row is never current however new it is.

THE SUPERSESSION CONTRACT, read off the schema and the live data rather than
wished for. `superseded_by` is `INTEGER REFERENCES project_state(id)` and
NULLABLE, and 104 of 166 historically superseded rows carry
`superseded_at` with `superseded_by` NULL — including every row closed by
`build_plan.sync_project_state_from_build_plan`'s bulk UPDATE. An unlinked
supersession is therefore schema-legal history, reported as an OBSERVATION
and never as a violation; calling 104 existing rows broken would fail every
key in the table and would be a verdict on history this card does not have.
What IS a violation is a relationship the schema cannot mean:

    live_row_claims_successor      superseded_by set while superseded_at IS NULL
    successor_missing              superseded_by points at no existing row
    successor_self_reference       superseded_by = id
    successor_key_mismatch         successor row carries a different key
    successor_predates_predecessor successor created_at older than the row it supersedes

All five are at zero occurrences on the production spine as of this card;
they are detected so they stay at zero, and so that a hand-built chain
cannot pass as a maintained one.

COLUMN TOLERANCE. Several existing fixtures build `project_state` with a
reduced column set (tools/export/tests/test_agents_md_size_guard.py has
only id/key/value/superseded_at). This module introspects the table and
degrades honestly: checks that need an absent column are reported as
unavailable rather than skipped silently. `superseded_at` is the one column
it cannot work without.

Usage:
    python3 -m db.state_authority                      # full report as JSON
    python3 -m db.state_authority --key next_action    # one key
    python3 -m db.state_authority --integrity          # table-wide integrity only
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

# ── cardinality registry ──────────────────────────────────────────────────

SINGLE = "single"
MULTI = "multi"
UNDECLARED = "undeclared"

# Keys whose existing authority contract requires exactly one current
# record. Each entry is here because a sanctioned reader already resolves
# that key to ONE value and would otherwise have to pick between rows.
#
# This is not a guess at intent: every one of these keys is served through
# a {key: value} mapping by `database.get_project_state`,
# `tools/export/generate_agents_md.py` and `tools/export/generate_hcp.py`,
# a structure that can physically hold only one value per key — and every
# one of them holds exactly one live row on the production spine, with a
# maintained supersession chain, except `next_action`, which holds two and
# is the conflict this module exists to stop being invisible.
KEY_CARDINALITY = {
    # read by generate_agents_md section 1, the coherence gate's tier
    # parse, and build_path's current-phase derivation
    "build_phase": SINGLE,
    # the coherence gate's primary input; a second live row changes which
    # tiers are considered complete
    "completed_tier": SINGLE,
    # generate_agents_md "Direction:" line
    "current_direction": SINGLE,
    # one build-list item number, written by tools/queue/set_current_item.py
    # whose own docstring says "one build-list item number, and only that"
    "current_queue_item": SINGLE,
    "devpivot_index": SINGLE,
    "enforcement_container": SINGLE,
    "enforcement_status": SINGLE,
    # the acceptance authority (ADR-XDEV-001), read by
    # tools/development/verification_plan.accepted_baseline,
    # tools/state/recovery_packet.py and build_path's checkpoint panel.
    # A second live row here is the forged-baseline case.
    "external_dev_checkpoint": SINGLE,
    "gateway_status_qwen": SINGLE,
    "last_export_run_id": SINGLE,
    "last_verified_closeout_tier": SINGLE,
    # CONFLICTED ON PRODUCTION: rows 161 and 166 are both live. Declared
    # single-valued because build_path already presents it as one value and
    # project_intelligence consumes it as one authority text. Selecting the
    # winner is phase authority (project_state row 163's own reasoning) and
    # is NOT done here.
    "next_action": SINGLE,
    # read by the coherence gate and tools/escalation/check_escalation_required
    "next_tier": SINGLE,
    # ADR-PIPE-006 sequencing authority; build_path parses one chain from it
    "pipeline_roadmap": SINGLE,
    "pipeline_stability_verified": SINGLE,
    # rows 154 -> 162 -> 163 are a fully linked supersession chain, so this
    # key is maintained single-valued in fact, not merely by convention
    "queue_projection_observation": SINGLE,
}

# Keys whose authority contract legitimately allows several live records at
# once. EMPTY, and that is a finding rather than an oversight: every key
# present on the production spine is consumed through a single-value
# mapping, and no reader anywhere in tools/ or runtime/ reads a list of
# live project_state rows for one key. The registry keeps the distinction
# expressible so that a future ledger-style key can be declared here and be
# exempt from single-valued enforcement, which is also what
# test_state_authority's multi-valued test exercises.
MULTI_VALUED_KEYS: dict = {}

ALLOWED_SOURCES = {"git", "gate", "manual"}

RESOLVED = "RESOLVED"          # exactly one unambiguous current record
RESOLVED_MULTI = "RESOLVED_MULTI"  # multi-valued key, all live rows returned
ABSENT = "ABSENT"              # no live record
CONFLICT = "CONFLICT"          # authority is ambiguous; no value is served
UNREADABLE = "UNREADABLE"      # the table cannot answer the question at all

RESOLVER_ID = "runtime/db/state_authority.resolve_current"

_REQUIRED_COLUMNS = ("key", "value", "superseded_at")

# Migration 0040's partial unique index — the database-level half of
# single-valued enforcement. Named here because three separate places have
# to agree on it: the migration file, spine_schema.sql (so a FRESH database
# is born with it), and `install_single_live_index` below (so an EXISTING
# database acquires it when opened through database.init_db).
SINGLE_LIVE_INDEX = "idx_project_state_one_live_per_single_valued_key"

_SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema")
MIGRATION_0040_PATH = os.path.join(
    _SCHEMA_DIR, "migrations", "0040_project_state_single_live.sql")
SPINE_SCHEMA_PATH = os.path.join(_SCHEMA_DIR, "spine_schema.sql")

_SINGLE_LIVE_INDEX_RE = re.compile(
    r"CREATE\s+UNIQUE\s+INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?" + SINGLE_LIVE_INDEX
    + r"\b(.*?);", re.I | re.S)


class StateAuthorityError(Exception):
    """Base for every refusal this module makes."""


class AmbiguousStateError(StateAuthorityError):
    """A single-valued key's current state is already ambiguous, so a write
    cannot know what it is replacing. Carries the conflicting rows."""

    def __init__(self, message, resolution=None):
        super().__init__(message)
        self.resolution = resolution or {}


class UndeclaredCardinalityError(StateAuthorityError):
    """A write named a key whose cardinality is not declared and gave no
    explicit `cardinality=`. Refused rather than guessed: guessing single
    would impose semantics no authority declared, and guessing multi would
    silently leave a new authority key unprotected."""


class DuplicateLiveRowsError(StateAuthorityError):
    """Migration 0040 cannot be installed because the data already violates
    the constraint it declares: some single-valued key carries more than one
    live row.

    REFUSED, NOT REPAIRED. The index would have to pick a survivor, and
    picking between two live authority rows is the authority decision this
    whole module exists to stop a mechanism from making silently. The
    conflicting keys and row ids are carried on `.conflicts` so the refusal
    names exactly what an architect has to decide, and NOTHING is written —
    no supersession, no winner, no backfill."""

    def __init__(self, message, conflicts=None):
        super().__init__(message)
        self.conflicts = conflicts or []


class MigrationKeyListDriftError(StateAuthorityError):
    """The key list in migration 0040's DDL and the single-valued entries of
    KEY_CARDINALITY have diverged, so installing the index would enforce a
    different contract from the one this module declares. Refused at install
    time as well as asserted by runtime/tests/test_state_authority.py: a
    test catches drift in the repository, this catches drift in whatever
    file a particular database is actually being migrated from."""

    def __init__(self, message, only_in_migration=(), only_in_registry=()):
        super().__init__(message)
        self.only_in_migration = list(only_in_migration)
        self.only_in_registry = list(only_in_registry)


class SupersessionIntegrityError(StateAuthorityError):
    """The supersession relationships around a key violate the schema
    contract, so no write may build on them."""

    def __init__(self, message, violations=None):
        super().__init__(message)
        self.violations = violations or []


def cardinality_of(key, override=None):
    """Declared cardinality for `key`. `override` is how a caller declares
    a key the registry does not know; without it an unknown key is refused
    on the write path and reported as UNDECLARED on the read path."""
    if override is not None:
        if override not in (SINGLE, MULTI):
            raise ValueError(f"cardinality must be {SINGLE!r} or {MULTI!r}, got {override!r}")
        return override
    if key in KEY_CARDINALITY:
        return KEY_CARDINALITY[key]
    if key in MULTI_VALUED_KEYS:
        return MULTI
    return UNDECLARED


def single_valued_keys():
    return tuple(sorted(k for k, v in KEY_CARDINALITY.items() if v == SINGLE))


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def _columns(conn):
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(project_state)").fetchall()}
    except sqlite3.Error:
        return set()


def _missing_required(cols):
    return [c for c in _REQUIRED_COLUMNS if c not in cols]


def _row_select(cols):
    """Diagnostic column list, restricted to what this database actually
    has. `id` is included when present because a conflict report whose rows
    cannot be named is not a usable conflict report."""
    wanted = ("id", "key", "value", "source", "evidence_hash", "evidence_run_id",
              "created_at", "superseded_at", "superseded_by")
    present = [c for c in wanted if c in cols]
    return ", ".join(present), present


def _trim(value, limit=240):
    if not isinstance(value, str) or len(value) <= limit:
        return value
    return value[:limit] + f"... [{len(value)} chars total]"


def _diag(row, present, *, trim=True):
    """One row rendered for a conflict/violation report. The full value is
    kept for the resolved case and trimmed for diagnostics, so a conflict
    naming four 20KB checkpoint rows stays readable while still naming
    every id."""
    out = {}
    for col in present:
        v = row[col]
        out[col] = _trim(v) if (trim and col == "value") else v
    return out


# ── supersession integrity ────────────────────────────────────────────────

def supersession_violations(conn, key=None):
    """Relationships the schema cannot mean. See the module docstring for
    why an unlinked supersession is NOT one of them.

    Returns a list of {kind, key, row_id, successor_id, detail} dicts, and
    a list of checks that could not run because a column is absent."""
    cols = _columns(conn)
    violations, unavailable = [], []
    has_id = "id" in cols
    has_by = "superseded_by" in cols
    has_created = "created_at" in cols
    where_key = " AND a.key = ?" if key is not None else ""
    params = (key,) if key is not None else ()

    if not has_by:
        unavailable.append({
            "check": "supersession_link_integrity",
            "reason": "project_state has no superseded_by column on this database",
        })
        return violations, unavailable

    def add(kind, rows, detail):
        for r in rows:
            violations.append({
                "kind": kind,
                "key": r["key"],
                "row_id": r["id"] if has_id else None,
                "successor_id": r["superseded_by"],
                "detail": detail,
            })

    sel = "a.id AS id, a.key AS key, a.superseded_by AS superseded_by" if has_id else \
          "NULL AS id, a.key AS key, a.superseded_by AS superseded_by"

    add("live_row_claims_successor", conn.execute(
        f"SELECT {sel} FROM project_state a "
        f"WHERE a.superseded_by IS NOT NULL AND a.superseded_at IS NULL{where_key}",
        params).fetchall(),
        "the row names a successor yet is still live, so it is both current and replaced")

    add("successor_missing", conn.execute(
        f"SELECT {sel} FROM project_state a WHERE a.superseded_by IS NOT NULL "
        f"AND NOT EXISTS (SELECT 1 FROM project_state b WHERE b.id = a.superseded_by)"
        f"{where_key}", params).fetchall(),
        "superseded_by points at a row id that does not exist")

    if has_id:
        add("successor_self_reference", conn.execute(
            f"SELECT {sel} FROM project_state a WHERE a.superseded_by = a.id{where_key}",
            params).fetchall(),
            "the row supersedes itself")

    add("successor_key_mismatch", conn.execute(
        f"SELECT {sel} FROM project_state a JOIN project_state b ON b.id = a.superseded_by "
        f"WHERE a.key <> b.key{where_key}", params).fetchall(),
        "the successor row carries a different key, so the chain crosses two authorities")

    if has_created:
        add("successor_predates_predecessor", conn.execute(
            f"SELECT {sel} FROM project_state a JOIN project_state b ON b.id = a.superseded_by "
            f"WHERE b.created_at < a.created_at{where_key}", params).fetchall(),
            "the successor was created before the row it supersedes")
    else:
        unavailable.append({
            "check": "successor_predates_predecessor",
            "reason": "project_state has no created_at column on this database",
        })

    return violations, unavailable


def supersession_observations(conn, key=None):
    """Schema-legal facts about the chain that a reader may want but that
    are NOT violations. Unlinked supersessions dominate history (104 rows)
    and every one of them is permitted by a nullable superseded_by."""
    cols = _columns(conn)
    if "superseded_by" not in cols:
        return []
    where_key = " AND key = ?" if key is not None else ""
    params = (key,) if key is not None else ()
    rows = conn.execute(
        f"SELECT key, COUNT(*) n FROM project_state "
        f"WHERE superseded_at IS NOT NULL AND superseded_by IS NULL{where_key} "
        f"GROUP BY key ORDER BY key", params).fetchall()
    return [{
        "kind": "unlinked_supersession",
        "key": r["key"],
        "row_count": r["n"],
        "severity": "historical",
        "detail": ("rows closed with superseded_at but no superseded_by. Permitted by the "
                   "schema (superseded_by is nullable) and the dominant historical pattern; "
                   "the chain is not reconstructible across them. Not repaired here."),
    } for r in rows]


# ── the canonical resolver ────────────────────────────────────────────────

def resolve_current(conn, key, *, cardinality=None):
    """THE one authoritative answer to "what is the current record for this
    key". Every reader goes through here instead of writing its own
    selection.

    A value is served only when authority is unambiguous: exactly one live
    row for a single-valued key, and no supersession-integrity violation
    touching that key. Otherwise the result carries status CONFLICT, no
    value, and the conflicting rows — never an arbitrary pick, and never a
    newest-row tiebreak.
    """
    conn.row_factory = sqlite3.Row
    cols = _columns(conn)
    card = cardinality_of(key, cardinality)
    base = {
        "key": key,
        "cardinality": card,
        "resolver": RESOLVER_ID,
        "status": None,
        "value": None,
        "row_id": None,
        "row": None,
        "live_row_count": 0,
        "live_rows": [],
        "violations": [],
        "observations": [],
        "checks_unavailable": [],
        "note": None,
    }

    if not cols:
        base.update({"status": UNREADABLE, "note": "project_state table is absent or unreadable"})
        return base
    missing = _missing_required(cols)
    if missing:
        base.update({"status": UNREADABLE,
                     "note": f"project_state lacks required column(s): {', '.join(missing)}"})
        return base

    select_cols, present = _row_select(cols)
    order = "ORDER BY id" if "id" in cols else ""
    live = conn.execute(
        f"SELECT {select_cols} FROM project_state WHERE key = ? AND superseded_at IS NULL {order}",
        (key,)).fetchall()
    violations, unavailable = supersession_violations(conn, key)
    base["violations"] = violations
    base["checks_unavailable"] = unavailable
    base["observations"] = supersession_observations(conn, key)
    base["live_row_count"] = len(live)
    base["live_rows"] = [_diag(r, present) for r in live]

    if violations:
        base.update({
            "status": CONFLICT,
            "note": (f"{len(violations)} supersession-integrity violation(s) involve key "
                     f"{key!r}; no current value is served while the chain is broken. "
                     "Nothing is repaired automatically."),
        })
        return base

    if card == MULTI:
        base.update({
            "status": RESOLVED_MULTI,
            "values": [r["value"] for r in live],
            "note": (f"{key!r} is declared multi-valued; all {len(live)} live row(s) are "
                     "returned and no single-valued enforcement applies."),
        })
        return base

    if card == UNDECLARED:
        base.update({
            "status": RESOLVED_MULTI if len(live) != 1 else RESOLVED,
            "values": [r["value"] for r in live],
            "note": (f"{key!r} has no declared cardinality in KEY_CARDINALITY, so "
                     "single-valued semantics are NOT imposed on it. All live rows are "
                     "returned. Declare it before relying on a single current value."),
        })
        if len(live) == 1:
            base["value"] = live[0]["value"]
            base["row_id"] = live[0]["id"] if "id" in cols else None
            base["row"] = _diag(live[0], present, trim=False)
        return base

    if len(live) == 0:
        total = conn.execute("SELECT COUNT(*) FROM project_state WHERE key = ?", (key,)).fetchone()[0]
        base.update({
            "status": ABSENT,
            "note": (f"no live row for {key!r}" if total == 0 else
                     f"no live row for {key!r}; all {total} row(s) for this key are superseded. "
                     "A superseded row is never served as current, however recent it is."),
        })
        return base

    if len(live) > 1:
        ids = [r["id"] for r in live] if "id" in cols else []
        base.update({
            "status": CONFLICT,
            "note": (f"{key!r} is declared single-valued but has {len(live)} live rows"
                     + (f" (ids {', '.join(str(i) for i in ids)})" if ids else "")
                     + ". Authority is ambiguous, so no value is served. Choosing between "
                       "them is an authority decision, not a read-model one."),
        })
        return base

    row = live[0]
    base.update({
        "status": RESOLVED,
        "value": row["value"],
        "row_id": row["id"] if "id" in cols else None,
        "row": _diag(row, present, trim=False),
    })
    return base


def resolve_all(conn, keys=None):
    """Resolve every key present in the table (or the given keys), each
    through `resolve_current`. Declared keys with no row are included so an
    absent authority key is visible rather than merely missing."""
    conn.row_factory = sqlite3.Row
    if keys is None:
        try:
            present = [r[0] for r in conn.execute(
                "SELECT DISTINCT key FROM project_state ORDER BY key").fetchall()]
        except sqlite3.Error:
            present = []
        keys = sorted(set(present) | set(KEY_CARDINALITY) | set(MULTI_VALUED_KEYS))
    return {k: resolve_current(conn, k) for k in keys}


class ConflictMarker:
    """What a {key: value} reader gets for a key whose authority is
    ambiguous. It is NOT a value and must never be mistaken for one: it has
    no plausible string form, carries the conflicting row ids, and is
    truthy so that a caller's `if value:` renders the conflict loudly
    instead of silently dropping the key."""

    __slots__ = ("resolution",)

    def __init__(self, resolution):
        self.resolution = resolution

    @property
    def key(self):
        return self.resolution.get("key")

    @property
    def row_ids(self):
        return [r.get("id") for r in self.resolution.get("live_rows", [])]

    def __bool__(self):
        return True

    def __str__(self):
        ids = ", ".join(str(i) for i in self.row_ids if i is not None)
        return (f"<<AUTHORITY CONFLICT: project_state.{self.key} is not single-valued "
                f"({self.resolution.get('live_row_count')} live rows"
                + (f": ids {ids}" if ids else "") + "). "
                "No current value. Resolve the conflict before relying on this key.>>")

    __repr__ = __str__


class ProjectStateView(dict):
    """`{key: value}` for every unambiguously resolved key, exactly as
    `database.get_project_state` has always returned — with two additions
    that cannot be ignored by accident: a conflicted key maps to a
    `ConflictMarker` rather than to one of the candidate values, and
    `.conflicts` / `.resolutions` carry the structured detail.

    An arbitrary pick is the one thing this must not do, so the dict
    position that used to hold "whichever row had MAX(id)" now holds an
    object that says so."""

    def __init__(self, resolutions):
        self.resolutions = resolutions
        self.conflicts = {k: r for k, r in resolutions.items() if r["status"] == CONFLICT}
        self.unreadable = {k: r for k, r in resolutions.items() if r["status"] == UNREADABLE}
        values = {}
        for k, r in resolutions.items():
            if r["status"] == CONFLICT:
                values[k] = ConflictMarker(r)
            elif r["status"] in (RESOLVED,) and r["value"] is not None:
                values[k] = r["value"]
            elif r["status"] in (RESOLVED_MULTI,) and r.get("value") is not None:
                values[k] = r["value"]
        super().__init__(values)

    @property
    def has_conflict(self):
        return bool(self.conflicts)


def current_state_map(conn, keys=None):
    return ProjectStateView(resolve_all(conn, keys=keys))


def current_value(conn, key, *, default=None, strict=True, cardinality=None):
    """The current value for one single-valued key.

    `strict=True` (the default) raises `AmbiguousStateError` on CONFLICT —
    for callers that must not proceed on a guess. `strict=False` returns
    `default` and leaves the caller to inspect `resolve_current` itself;
    either way no candidate row is ever returned as though it had won."""
    res = resolve_current(conn, key, cardinality=cardinality)
    if res["status"] == CONFLICT:
        if strict:
            raise AmbiguousStateError(res["note"], resolution=res)
        return default
    if res["status"] in (RESOLVED, RESOLVED_MULTI) and res["value"] is not None:
        return res["value"]
    return default


# ── the sanctioned writer ─────────────────────────────────────────────────

def set_state(conn, key, value, source, *, evidence_hash=None, evidence_run_id=None,
              created_at=None, cardinality=None):
    """Record a new current value for `key` as ONE atomic operation.

    For a single-valued key the insert and the supersession of the previous
    current row happen together or not at all, so there is no second
    operation for a caller to forget — which is the whole defect this
    replaces. The previous row gets `superseded_at` AND `superseded_by`
    pointing at the new row, so the chain stays reconstructible going
    forward (history is left exactly as it is).

    FAILS CLOSED, in four ways, rather than producing a plausible result:
      * an undeclared key with no explicit `cardinality=` is refused;
      * an already-ambiguous key (more than one live row) is refused, and
        nothing is written — the ambiguity is reported with its row ids;
      * a broken supersession relationship touching the key is refused;
      * if the post-write state is not exactly one live row, the whole
        transaction is rolled back.

    CONCURRENCY. The read-modify-write runs inside a single `BEGIN
    IMMEDIATE` transaction, so a second writer cannot interleave between
    "which row is live" and "supersede it": it waits for the write lock
    (set `PRAGMA busy_timeout` on the connection to wait rather than fail),
    then re-reads and supersedes the row the first writer just created.
    Where migration 0040's partial unique index is applied, the database
    refuses a second live row independently of this function.

    When the caller already has a transaction open, a SAVEPOINT is used and
    the caller keeps the commit — preserving `insert_project_state`'s
    long-standing "caller commits" contract.
    """
    if source not in ALLOWED_SOURCES:
        raise ValueError(f"Invalid source '{source}'. Allowed: {sorted(ALLOWED_SOURCES)}")
    card = cardinality_of(key, cardinality)
    if card == UNDECLARED:
        raise UndeclaredCardinalityError(
            f"project_state key {key!r} has no declared cardinality. Add it to "
            "KEY_CARDINALITY (or MULTI_VALUED_KEYS) in runtime/db/state_authority.py, "
            "or pass cardinality='single'/'multi' explicitly. Refusing to guess: "
            "guessing single would impose semantics no authority declared, and guessing "
            "multi would leave a new authority key unprotected.")

    conn.row_factory = sqlite3.Row
    cols = _columns(conn)
    missing = _missing_required(cols)
    if missing:
        raise StateAuthorityError(
            f"project_state lacks required column(s): {', '.join(missing)}")

    now = created_at or _iso_now()
    own_txn = not conn.in_transaction
    if own_txn:
        conn.execute("BEGIN IMMEDIATE")
    else:
        conn.execute("SAVEPOINT cis_set_state")

    try:
        superseded = []
        if card == SINGLE:
            violations, _unavailable = supersession_violations(conn, key)
            if violations:
                raise SupersessionIntegrityError(
                    f"refusing to write project_state.{key}: "
                    f"{len(violations)} supersession-integrity violation(s) involve this key. "
                    "The chain must be corrected by an authority decision first; this writer "
                    "does not repair history.", violations=violations)
            order = "ORDER BY id" if "id" in cols else ""
            live = conn.execute(
                f"SELECT id, value FROM project_state "
                f"WHERE key = ? AND superseded_at IS NULL {order}", (key,)).fetchall()
            if len(live) > 1:
                res = resolve_current(conn, key, cardinality=cardinality)
                raise AmbiguousStateError(
                    f"refusing to write project_state.{key}: it already has "
                    f"{len(live)} live rows (ids "
                    + ", ".join(str(r["id"]) for r in live) +
                    "). A write cannot know which record it is replacing, and selecting a "
                    "winner is an authority decision. Nothing was written.",
                    resolution=res)
            superseded = [dict(r) for r in live]

        # ORDER MATTERS, and not for style. The previous current row is
        # closed BEFORE the new one is inserted, so that migration 0040's
        # partial unique index — which counts only rows with
        # superseded_at IS NULL — is satisfied at every statement boundary.
        # Inserting first would momentarily present two live rows and the
        # database would (correctly) reject the insert. `superseded_by` is
        # then filled in once the new row has an id. All three statements
        # are inside one transaction, so a reader never observes an
        # intermediate state and a failure anywhere rolls back the lot.
        if card == SINGLE and superseded:
            for row in superseded:
                conn.execute(
                    "UPDATE project_state SET superseded_at = ? "
                    "WHERE id = ? AND superseded_at IS NULL",
                    (now, row["id"]))

        insert_cols = ["key", "value", "source"]
        insert_vals = [key, value, source]
        for col, val in (("evidence_hash", evidence_hash),
                         ("evidence_run_id", evidence_run_id)):
            if col in cols:
                insert_cols.append(col)
                insert_vals.append(val)
        if "created_at" in cols:
            insert_cols.append("created_at")
            insert_vals.append(now)
        placeholders = ", ".join("?" for _ in insert_cols)
        cur = conn.execute(
            f"INSERT INTO project_state ({', '.join(insert_cols)}) VALUES ({placeholders})",
            insert_vals)
        new_id = cur.lastrowid

        if card == SINGLE and superseded and "superseded_by" in cols:
            for row in superseded:
                conn.execute(
                    "UPDATE project_state SET superseded_by = ? WHERE id = ?",
                    (new_id, row["id"]))

        if card == SINGLE:
            n = conn.execute(
                "SELECT COUNT(*) FROM project_state WHERE key = ? AND superseded_at IS NULL",
                (key,)).fetchone()[0]
            if n != 1:
                raise StateAuthorityError(
                    f"post-write check failed for project_state.{key}: {n} live rows after "
                    "an atomic replace that must leave exactly 1. Rolled back; nothing was "
                    "written.")
    except Exception:
        if own_txn:
            conn.rollback()
        else:
            conn.execute("ROLLBACK TO cis_set_state")
            conn.execute("RELEASE cis_set_state")
        raise
    else:
        if own_txn:
            conn.commit()
        else:
            conn.execute("RELEASE cis_set_state")

    return {
        "key": key,
        "cardinality": card,
        "new_row_id": new_id,
        "superseded_row_ids": [r["id"] for r in superseded],
        "recorded_at": now,
        "committed_by": "set_state" if own_txn else "caller",
    }


# ── migration 0040 installation (fresh databases and recovery) ────────────

def parse_single_live_index_keys(sql_text):
    """The key list of migration 0040's partial unique index, read out of
    whatever SQL text declares it — the migration file, spine_schema.sql, or
    a `.schema` dump of a live database.

    Returns a sorted tuple of keys, or None when the text declares no such
    index at all. None means "this file does not install it"; an empty tuple
    would mean "it installs it constraining nothing", and the two must not
    be confused."""
    match = _SINGLE_LIVE_INDEX_RE.search(sql_text or "")
    if not match:
        return None
    return tuple(sorted(set(re.findall(r"'([^']+)'", match.group(1)))))


def migration_0040_keys(migration_path=None):
    """The key list migration 0040 itself declares, read from the file."""
    path = migration_path or MIGRATION_0040_PATH
    with open(path, encoding="utf-8") as fh:
        return parse_single_live_index_keys(fh.read())


def single_live_index_present(conn):
    """Whether THIS database carries the index, observed from its own
    schema. The one question "is migration 0040 applied here" is answered
    from sqlite_master and never from a migrations-applied table, a file
    timestamp or a prose claim."""
    try:
        return conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name = ?",
            (SINGLE_LIVE_INDEX,)).fetchone() is not None
    except sqlite3.Error:
        return False


def duplicate_live_single_valued_rows(conn):
    """Every key registered single-valued in KEY_CARDINALITY that currently
    carries more than one live row, with the offending row ids.

    This is migration 0040's precondition, asked of the data BEFORE the
    index is created, because `CREATE UNIQUE INDEX` on violating data fails
    with SQLite's own message — which names neither the key nor the rows and
    is therefore not an actionable refusal. Returns None when project_state
    cannot answer the question at all."""
    cols = _columns(conn)
    if not cols or _missing_required(cols):
        return None
    keys = single_valued_keys()
    if not keys:
        return []
    has_id = "id" in cols
    placeholders = ", ".join("?" for _ in keys)
    rows = conn.execute(
        f"SELECT key{', id' if has_id else ''} FROM project_state "
        f"WHERE superseded_at IS NULL AND key IN ({placeholders}) "
        f"ORDER BY key{', id' if has_id else ''}", keys).fetchall()
    by_key = {}
    for row in rows:
        by_key.setdefault(row[0], []).append(row[1] if has_id else None)
    return [{
        "key": key,
        "live_row_count": len(ids),
        "row_ids": [i for i in ids if i is not None],
    } for key, ids in sorted(by_key.items()) if len(ids) > 1]


def install_single_live_index(conn, *, migration_path=None):
    """Install migration 0040 on `conn` if the index is absent, and do
    nothing if it is already there.

    WHY THIS EXISTS. The index was applied to the production spine by hand.
    A migration that only ever reaches a database through a hand-run
    `sqlite3 < file` is not installed by any supported path, so a fresh
    database built from spine_schema.sql, or an existing one reopened
    through `database.init_db`, silently came up WITHOUT the
    database-level half of single-valued enforcement — leaving the
    sanctioned writer as the only thing standing between a direct INSERT and
    two live authority rows. That is the gap this closes.

    IDEMPOTENT by observation of the live schema, not by bookkeeping: the
    index's presence in sqlite_master is the applied/not-applied answer, so
    calling this on every open costs one catalogue lookup and changes
    nothing on an already-migrated database (the production spine included).

    FAILS CLOSED on the one case that matters. If any single-valued key
    already has two live rows, `DuplicateLiveRowsError` is raised naming the
    keys and row ids, and not one row is touched: no winner is selected, no
    row is superseded, no `superseded_by` is backfilled, and the index is
    not created. A migration that resolved its own precondition by picking a
    survivor would be the defect, not the fix.

    Returns a result dict (never raises for an already-installed index):
        status   applied | already_present | unavailable
        applied  True only when this call created the index
        keys     the key list the index constrains
        note     why, in the unavailable case
    """
    path = migration_path or MIGRATION_0040_PATH
    result = {
        "index": SINGLE_LIVE_INDEX,
        "migration": os.path.basename(path),
        "status": None,
        "applied": False,
        "keys": [],
        "conflicts": [],
        "note": None,
    }

    cols = _columns(conn)
    if not cols:
        result.update({"status": "unavailable",
                       "note": "project_state is absent on this database; there is no "
                               "single-valued authority to enforce yet"})
        return result
    missing = _missing_required(cols)
    if missing:
        result.update({"status": "unavailable",
                       "note": ("project_state lacks required column(s): "
                                + ", ".join(missing)
                                + " — a partial index over live rows cannot be "
                                  "expressed, so enforcement is reported unavailable "
                                  "rather than silently skipped")})
        return result

    if single_live_index_present(conn):
        result.update({"status": "already_present",
                       "keys": list(single_valued_keys()),
                       "note": "index already in sqlite_master; nothing applied"})
        return result

    declared = set(single_valued_keys())
    in_migration = migration_0040_keys(path)
    if in_migration is None:
        raise MigrationKeyListDriftError(
            f"{os.path.basename(path)} declares no {SINGLE_LIVE_INDEX} index; refusing to "
            "report migration 0040 installed from a file that does not install it.")
    in_migration = set(in_migration)
    if in_migration != declared:
        raise MigrationKeyListDriftError(
            f"refusing to install {SINGLE_LIVE_INDEX}: its key list in "
            f"{os.path.basename(path)} does not match the single-valued entries of "
            "KEY_CARDINALITY, so the database would enforce a different contract from "
            "the one runtime/db/state_authority.py declares. Only in the migration: "
            f"{sorted(in_migration - declared)}; only in the registry: "
            f"{sorted(declared - in_migration)}.",
            only_in_migration=sorted(in_migration - declared),
            only_in_registry=sorted(declared - in_migration))

    conflicts = duplicate_live_single_valued_rows(conn)
    if conflicts:
        named = "; ".join(
            f"{c['key']} has {c['live_row_count']} live rows"
            + (f" (ids {', '.join(str(i) for i in c['row_ids'])})" if c["row_ids"] else "")
            for c in conflicts)
        raise DuplicateLiveRowsError(
            f"refusing to install {SINGLE_LIVE_INDEX}: the data already violates it — "
            f"{named}. Nothing was written: no row was superseded, no winner was "
            "selected and no supersession link was backfilled. Choosing which record is "
            "current is an authority decision; supersede the others through "
            "state_authority.set_state and reopen the database.",
            conflicts=conflicts)

    with open(path, encoding="utf-8") as fh:
        conn.executescript(fh.read())
    conn.commit()
    if not single_live_index_present(conn):
        raise StateAuthorityError(
            f"{os.path.basename(path)} ran without error but {SINGLE_LIVE_INDEX} is still "
            "absent from sqlite_master; enforcement is not installed and this is reported "
            "rather than assumed.")
    result.update({"status": "applied", "applied": True,
                   "keys": sorted(declared),
                   "note": f"installed from {os.path.basename(path)} after confirming no "
                           "single-valued key carried duplicate live rows"})
    return result


# ── table-wide integrity, for the coherence gate ──────────────────────────

def integrity_report(conn):
    """Everything the coherence gate needs to fail on conflicting
    authoritative state, with the affected key and records named.

    `failures` are contract violations: a single-valued key with more than
    one live row, and any broken supersession relationship.
    `warnings` are visible-but-not-fatal: a key with no declared
    cardinality carrying several live rows (single-valued semantics are not
    imposed on it, and its ambiguity is still said out loud).
    """
    conn.row_factory = sqlite3.Row
    cols = _columns(conn)
    report = {
        "resolver": RESOLVER_ID,
        "readable": bool(cols) and not _missing_required(cols),
        "single_valued_keys": list(single_valued_keys()),
        "multi_valued_keys": sorted(MULTI_VALUED_KEYS),
        "failures": [],
        "warnings": [],
        "observations": [],
        "checks_unavailable": [],
        "keys_checked": 0,
        # Always present, on every return path: a caller must never have to
        # distinguish "passed is absent" from "passed is False".
        "passed": False,
    }
    if not report["readable"]:
        report["failures"].append({
            "kind": "project_state_unreadable",
            "detail": ("project_state is absent or lacks required column(s): "
                       + ", ".join(_missing_required(cols) or ["<table missing>"])),
        })
        return report

    violations, unavailable = supersession_violations(conn)
    report["checks_unavailable"] = unavailable
    for v in violations:
        report["failures"].append(v)

    resolutions = resolve_all(conn)
    report["keys_checked"] = len(resolutions)
    for key, res in resolutions.items():
        if res["cardinality"] == SINGLE and res["live_row_count"] > 1:
            report["failures"].append({
                "kind": "duplicate_live_rows",
                "key": key,
                "live_row_count": res["live_row_count"],
                "row_ids": [r.get("id") for r in res["live_rows"]],
                "rows": res["live_rows"],
                "detail": (f"{key!r} is declared single-valued and has "
                           f"{res['live_row_count']} live rows. A reader that picks one of "
                           "them is guessing."),
            })
        elif res["cardinality"] == UNDECLARED and res["live_row_count"] > 1:
            report["warnings"].append({
                "kind": "undeclared_cardinality_multiple_live_rows",
                "key": key,
                "live_row_count": res["live_row_count"],
                "row_ids": [r.get("id") for r in res["live_rows"]],
                "detail": (f"{key!r} has {res['live_row_count']} live rows and no declared "
                           "cardinality, so single-valued enforcement is NOT applied to it. "
                           "Declare it in KEY_CARDINALITY if exactly one is intended."),
            })

    report["observations"] = supersession_observations(conn)
    report["passed"] = not report["failures"]
    return report


# ── CLI ───────────────────────────────────────────────────────────────────

def _default_db():
    return os.environ.get(
        "CIS_SPINE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "data", "cis_memory.db"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default=_default_db())
    ap.add_argument("--key", help="resolve one key instead of the whole table")
    ap.add_argument("--integrity", action="store_true",
                    help="table-wide integrity report only")
    args = ap.parse_args(argv)

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        if args.key:
            out = resolve_current(conn, args.key)
            bad = out["status"] in (CONFLICT, UNREADABLE)
        elif args.integrity:
            out = integrity_report(conn)
            bad = not out["passed"]
        else:
            out = {"integrity": integrity_report(conn),
                   "keys": resolve_all(conn)}
            bad = not out["integrity"]["passed"]
    finally:
        conn.close()
    print(json.dumps(out, indent=2, default=str))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
