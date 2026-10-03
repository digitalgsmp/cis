#!/usr/bin/env python3
"""build_path.py — read-only build-path read model for the Workbench
"Build Path" visualization (WB.1 read-only build-path Mermaid card).

WHAT THIS IS. One normalized answer to "where is the CIS build right now,
what comes next, and what is holding it up", assembled from the live spine
so the Workbench screen does not carry a second hand-written copy of the
roadmap that can drift. It sits beside canonical_state.py as a sibling
read model (Database -> read model -> api wrapper -> UI), and the Workbench
endpoint over it is a thin pass-through.

CONTRACT.
- Read-only, always. Nothing here writes to the database, and nothing here
  writes a derived display status back as authority.
- Authority split is respected exactly as ADR-PIPE-006 states it:
    project_decisions + project_state.pipeline_roadmap = sequencing authority
    queue_items + queue_edges                          = work-item authority
    docs/UNIFIED_BUILD_LIST.md                         = generated projection
    build_plan_nodes                                   = retired
  The phase sequence is PARSED FROM project_state.pipeline_roadmap, never
  hardcoded here. docs/UNIFIED_BUILD_LIST.md is never read. build_plan_nodes
  is never read. No queue edge is synthesized, invented or implied: queue
  items named by the roadmap are looked up, and that is all.
- Display statuses ("active", "next", "pending", ...) are a PRESENTATION
  vocabulary computed per request. They are never persisted, and they never
  replace ADR-PIPE-005's component-state vocabulary (BUILT_AND_ACTIVE,
  BUILT_BUT_DORMANT, ...), which classifies something different.
- Honest about absence. If the roadmap row is missing, if build_phase names
  no phase, if a queue item named by the roadmap does not exist, or if a
  migration file cannot be read, the payload says so in a `note`/`error`
  field rather than substituting a plausible value.

DERIVATION SOURCES, per field.
    phases[]              project_state.pipeline_roadmap (the "A -> B -> C"
                          chain and each stage's parenthesised description)
    phases[].migrations   the MIGRATION UNLOCK POINTS clause of
                          project_decisions ADR-PIPE-001, plus `unlocks
                          migration NNNN` in the roadmap itself; "applied"
                          is observed from the live schema by looking for
                          the tables runtime/schema/migrations/NNNN_*.sql
                          actually creates
    phases[].queue_hooks  `queue N.N` mentions in the roadmap, resolved
                          against the queue_items rows
    current / next        the phase named by project_state.build_phase,
                          and its successor in the parsed chain
    blockers              unresolved, blocking=true discoveries for the
                          current task, via tools/development/discovery.py
                          (the same mechanism the closeout gate uses)
    checkpoint            project_state.external_dev_checkpoint (JSON)
    mermaid               generated from the phases above, so the diagram
                          cannot disagree with the panel beside it

Usage:
    python3 tools/state/build_path.py            # full read model as JSON
    python3 tools/state/build_path.py --mermaid  # just the diagram source
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_STATE_DIR = REPO_ROOT / "tools" / "state"
if str(_STATE_DIR) not in sys.path:
    sys.path.insert(0, str(_STATE_DIR))

import canonical_state as cs  # noqa: E402  (shared DB default + revision)

from tools.development import continuity_store as _continuity  # noqa: E402
from tools.development import discovery as _discovery  # noqa: E402

READ_MODEL_KIND = "cis_build_path"

MIGRATIONS_DIR = REPO_ROOT / "runtime" / "schema" / "migrations"

# Display vocabulary. The first seven are the card's own roadmap display
# statuses; "blocking" and "open" are the discovery-side tokens (a discovery
# blocks a phase, a phase is blocked). Nothing here is written back.
STATUS_VOCABULARY = (
    "complete", "active", "blocked", "next", "pending", "deferred",
    "resolved", "blocking", "open",
)

# Sequencing/authority decisions surfaced with the model so the screen can
# show the real decision text instead of a paraphrase of it.
ROADMAP_DECISION_IDS = (
    "ADR-PIPE-001", "ADR-PIPE-002", "ADR-PIPE-003", "ADR-PIPE-004",
    "ADR-PIPE-005", "ADR-PIPE-006", "ADR-XDEV-001", "ADR-XDEV-002",
)

# The phase-sequence authority. Parsed, never assumed.
ROADMAP_STATE_KEY = "pipeline_roadmap"
PHASE_POINTER_STATE_KEY = "build_phase"
CURRENT_TASK_STATE_KEY = "current_queue_item"

_SUMMARY_LIMIT = 400

# "P0 (activate WB.1 Slice 1)" / "QUEUE TRIAGE (...)" / "TIER-0 TRUST (...)"
_STAGE_RE = re.compile(r"\s*([A-Z][A-Z0-9][A-Za-z0-9 \-]*?)\s*\(([^)]*)\)")
# The stage separator. Scanned for positionally rather than str.split("->"),
# because the roadmap's own trailing prose contains "roadmap<->queue", and
# splitting on "->" would manufacture a tenth stage out of that sentence.
_ARROW_RE = re.compile(r"\s*->\s*")
# "Phase P0 of the P0-P6 sequence" -> P0
_CURRENT_PHASE_RE = re.compile(r"\bPhase\s+(P[0-6])\b")
# "unlocks migration 0036"
_UNLOCK_RE = re.compile(r"unlocks\s+migration\s+(\d{4})", re.I)
# "queue 0.4 + 0.6" / "queue 1.23"
_QUEUE_HOOK_RE = re.compile(r"queue\s+(\d+\.\d+)((?:\s*\+\s*\d+\.\d+)*)", re.I)
_QUEUE_NUM_RE = re.compile(r"\d+\.\d+")
# ADR-PIPE-001: "MIGRATION UNLOCK POINTS: 0035 + 0038 at P0; 0036 not before P3; ..."
_UNLOCK_CLAUSE_RE = re.compile(r"MIGRATION UNLOCK POINTS:\s*([^.]*)\.", re.I)
_AT_PHASE_RE = re.compile(r"((?:\d{4})(?:\s*\+\s*\d{4})*)\s+at\s+(P[0-6])", re.I)
_NOT_BEFORE_RE = re.compile(r"(\d{4})\s+not before\s+(P[0-6])", re.I)
# "WB1-D15: ..." / "CF-D1: ..." / "XDEV-R2 (roadmap/queue risk B): ..."
_DISCOVERY_ID_RE = re.compile(r"^([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\b")

# Constraint phrases the roadmap authority states about queue triage. Probed
# for literally in ADR-PIPE-006's own decision text and quoted back with the
# match — so the UI shows the authority's words, and a phrase that is no
# longer in the authority simply stops being displayed.
_TRIAGE_CONSTRAINT_PROBES = (
    ("bounded mechanical classification",
     re.compile(r"bounded mechanical classification[^.;]*", re.I)),
    ("no redesign", re.compile(r"NO item redesign[^.;]*", re.I)),
)


# ── low-level reads ──────────────────────────────────────────────────────

def _connect(db_path=None):
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _latest_state(conn, key):
    """The newest project_state row for `key`. Recency by created_at, the
    same rule canonical_state.get_current_focus() documents (this table is
    not superseded_at-maintained in practice)."""
    row = conn.execute(
        "SELECT id, key, value, source, created_at FROM project_state "
        "WHERE key = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (key,),
    ).fetchone()
    return dict(row) if row is not None else None


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (name,)
    ).fetchone() is not None


def _has_column(conn, table, column):
    try:
        return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table})"))
    except sqlite3.Error:
        return False


def _slug(label):
    return re.sub(r"_+", "_", re.sub(r"[^A-Z0-9]+", "_", label.upper())).strip("_")


def _truncate(text):
    text = text or ""
    if len(text) <= _SUMMARY_LIMIT:
        return text, False
    return text[:_SUMMARY_LIMIT].rstrip() + "…", True


# ── roadmap sequence ─────────────────────────────────────────────────────

def parse_roadmap_sequence(roadmap_value):
    """Split project_state.pipeline_roadmap's "A (...) -> B (...) -> ..."
    chain into ordered stages. Returns (stages, trailing_text, note).

    The chain is the contiguous "LABEL (description)" run at the start of
    the value; the first thing that is not one ends it. `trailing_text` is
    everything after it — the CONSTRAINTS / AUTHORITY prose — returned
    rather than discarded so the screen can show the ordering constraints
    verbatim. A value whose chain cannot be parsed at all is reported in
    `note` with no phases invented to cover for it."""
    if not roadmap_value:
        return [], "", "no pipeline_roadmap value to parse"

    stages, pos, note = [], 0, None
    while True:
        match = _STAGE_RE.match(roadmap_value, pos)
        if not match:
            if stages:
                note = ("pipeline_roadmap's stage chain ended before an arrow it "
                        f"still carried, at: {roadmap_value[pos:pos + 80]!r}")
            else:
                note = ("pipeline_roadmap's value does not start with a "
                        "'LABEL (description)' stage; no sequence parsed")
            break
        label = " ".join(match.group(1).split())
        stages.append({
            "id": _slug(label),
            "label": label,
            "order": len(stages),
            "description": " ".join(match.group(2).split()),
        })
        pos = match.end()
        arrow = _ARROW_RE.match(roadmap_value, pos)
        if not arrow:
            break
        pos = arrow.end()

    return stages, roadmap_value[pos:].strip(), note


# ── migration unlock points ──────────────────────────────────────────────

def migration_tables(migration):
    """Tables that runtime/schema/migrations/<migration>_*.sql creates, read
    from the migration file itself rather than restated here. Returns [] if
    no such file is readable, which is reported as unknown, not as absent."""
    try:
        matches = sorted(MIGRATIONS_DIR.glob(f"{migration}_*.sql"))
    except OSError:
        return []
    for path in matches:
        try:
            sql = path.read_text(encoding="utf-8")
        except OSError:
            continue
        return sorted(set(re.findall(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?([A-Za-z_][A-Za-z0-9_]*)",
            sql, re.I)))
    return []


def _migration_applied(conn, migration):
    """Observed from the live schema, never from a prose claim: a migration
    counts as applied when the tables its own file creates are present."""
    tables = migration_tables(migration)
    if not tables:
        return {
            "migration": migration, "applied": None, "tables": {},
            "detected_by": ("unknown — no readable "
                            f"runtime/schema/migrations/{migration}_*.sql"),
        }
    present = {t: _table_exists(conn, t) for t in tables}
    if all(present.values()):
        applied = True
    elif any(present.values()):
        applied = "partial"
    else:
        applied = False
    return {
        "migration": migration, "applied": applied, "tables": present,
        "detected_by": ("presence of the tables "
                        f"{migration}_*.sql creates: {', '.join(tables)}"),
    }


def parse_migration_unlock_points(adr_pipe_001_decision):
    """The MIGRATION UNLOCK POINTS clause of ADR-PIPE-001, as
    {phase_label: [{migration, rule, source_quote}]}."""
    out = {}
    if not adr_pipe_001_decision:
        return out
    clause_match = _UNLOCK_CLAUSE_RE.search(adr_pipe_001_decision)
    if not clause_match:
        return out
    clause = clause_match.group(1).strip()
    quote = f"ADR-PIPE-001: MIGRATION UNLOCK POINTS: {clause}."
    for group, phase in _AT_PHASE_RE.findall(clause):
        for migration in re.findall(r"\d{4}", group):
            out.setdefault(phase.upper(), []).append({
                "migration": migration,
                "rule": "required at this phase",
                "source_quote": quote,
            })
    for migration, phase in _NOT_BEFORE_RE.findall(clause):
        out.setdefault(phase.upper(), []).append({
            "migration": migration,
            "rule": "not permitted before this phase",
            "source_quote": quote,
        })
    return out


# ── queue hooks ──────────────────────────────────────────────────────────

def _queue_hook_nums(text):
    """Queue item numbers the roadmap text names, in order of appearance."""
    found = []
    for match in _QUEUE_HOOK_RE.finditer(text or ""):
        for num in _QUEUE_NUM_RE.findall(match.group(0)):
            if num not in found:
                found.append(num)
    return found


def _queue_item(conn, item_num):
    """The item's own queue_items row — work-item authority. A number the
    roadmap names but the queue does not carry comes back as `found: False`
    rather than as a fabricated row."""
    cols = "item_num, tier, title, need_status"
    if _has_column(conn, "queue_items", "scope"):
        cols += ", scope"
    row = conn.execute(
        f"SELECT {cols} FROM queue_items WHERE item_num = ?", (item_num,)
    ).fetchone()
    if row is None:
        return {"item_num": item_num, "found": False,
                "note": "named by the roadmap; no queue_items row with this item_num"}
    item = dict(row)
    item["found"] = True
    return item


def queue_classification(conn):
    """Triage's own subject matter, counted live. 'Unclassified' is
    ADR-PIPE-006's definition verbatim — rows carrying neither scope nor
    need_status — not a looser reading of it.

    TWO COUNTS, DELIBERATELY NOT ONE (OQ-TRIAGE-001 option 1, 2026-10-03).
    `unclassified` answers "how many rows is triage's subject", and ADR-PIPE-006
    fixes that as rows carrying NEITHER field: "a bounded mechanical
    classification pass over the currently unclassified queue_items (56 of 132
    rows carry neither scope nor need_status as of 2026-10-01)". It is not this
    module's business to redefine it.

    But ADR-PIPE-001 defines the triage WRITE as both fields, so a row holding
    one of the two is not triaged either — and counting it under `unclassified`
    would contradict ADR-PIPE-006 while counting it as done would overstate the
    work. `fully_classified` / `partially_classified` carry that distinction
    explicitly instead, so neither number has to lie. On the production table
    today: 56 neither, 13 need_status-only (mostly DONE rows predating the scope
    column), 0 scope-only, 63 both.
    """
    total = conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
    no_need = conn.execute(
        "SELECT COUNT(*) FROM queue_items WHERE need_status IS NULL").fetchone()[0]
    has_scope = _has_column(conn, "queue_items", "scope")
    if has_scope:
        no_scope = conn.execute(
            "SELECT COUNT(*) FROM queue_items WHERE scope IS NULL").fetchone()[0]
        unclassified = conn.execute(
            "SELECT COUNT(*) FROM queue_items "
            "WHERE need_status IS NULL AND scope IS NULL").fetchone()[0]
        full = conn.execute(
            "SELECT COUNT(*) FROM queue_items "
            "WHERE need_status IS NOT NULL AND scope IS NOT NULL "
            "AND TRIM(scope) <> ''").fetchone()[0]
    else:
        no_scope = None
        unclassified = no_need
        full = total - no_need
    counts = {r[0] or "(unset)": r[1] for r in conn.execute(
        "SELECT need_status, COUNT(*) FROM queue_items GROUP BY need_status")}
    return {
        "total_items": total,
        "unclassified": unclassified,
        "missing_need_status": no_need,
        "missing_scope": no_scope,
        "fully_classified": full,
        "partially_classified": total - unclassified - full,
        "counts_by_need_status": counts,
        "unclassified_definition": (
            "queue_items rows carrying neither scope nor need_status "
            "(ADR-PIPE-006's own definition of the triage subject)"
        ),
        "fully_classified_definition": (
            "queue_items rows carrying BOTH scope and need_status — the triage "
            "write ADR-PIPE-001 defines. A row with one of the two is counted "
            "under partially_classified and is NOT triaged; it is kept separate "
            "from unclassified so ADR-PIPE-006's definition of the triage "
            "subject is not quietly widened."
        ),
    }


# ── discoveries / blockers ───────────────────────────────────────────────

def _discovery_display_status(record):
    if record["resolved"]:
        return "resolved"
    if record["disposition"] == "EXPLICITLY_DEFERRED":
        return "deferred"
    if record["fields"].get("blocking") is True:
        return "blocking"
    return "open"


def _discovery_id(summary):
    match = _DISCOVERY_ID_RE.match(summary or "")
    return match.group(1) if match else None


def task_discoveries(task, db_path=None):
    """Every discovery record for `task`, annotated with a display status.
    Resolution is NOT re-derived here: discovery.list_discoveries() already
    defines "resolved" as a reconciliation event naming the discovery's own
    revision, and that single definition is reused so this screen cannot
    disagree with the closeout gate."""
    conn = _continuity.connect(db_path or cs.DB)
    try:
        if not _continuity.is_initialized(conn):
            return [], "dev_continuity_events table not present on this database"
        records = _discovery.list_discoveries(conn, task)
    except Exception as e:  # noqa: BLE001 — a missing/odd ledger must not 500 the screen
        return [], f"discoveries unavailable: {type(e).__name__}: {e}"
    finally:
        conn.close()

    out = []
    for record in records:
        summary, truncated = _truncate(record["summary"])
        out.append({
            "id": _discovery_id(record["summary"]),
            "task": task,
            "revision": record["revision"],
            "status": _discovery_display_status(record),
            "disposition": record["disposition"],
            "blocking": record["fields"].get("blocking"),
            "resolved": record["resolved"],
            "malformed": record["malformed"],
            "summary": summary,
            "summary_truncated": truncated,
            "created_at": record["created_at"],
        })
    out.sort(key=lambda d: d["revision"])
    return out, None


def _discovery_groups(discoveries):
    by_status = {"blocking": [], "open": [], "deferred": [], "resolved": []}
    for d in discoveries:
        by_status.setdefault(d["status"], []).append(d)
    newest_first = {k: sorted(v, key=lambda d: d["revision"], reverse=True)
                    for k, v in by_status.items()}
    return {
        "counts": {k: len(v) for k, v in newest_first.items()},
        "blocking": newest_first["blocking"],
        "open": newest_first["open"],
        "deferred": newest_first["deferred"],
        "resolved": newest_first["resolved"],
    }


# ── decisions / checkpoint ───────────────────────────────────────────────

def roadmap_decisions(conn):
    rows = conn.execute(
        "SELECT id, label, decision, status, decided_at, superseded_by "
        "FROM project_decisions WHERE id IN "
        f"({','.join('?' * len(ROADMAP_DECISION_IDS))}) ORDER BY id",
        ROADMAP_DECISION_IDS,
    ).fetchall()
    return [dict(r) for r in rows]


def external_checkpoint(conn):
    """project_state.external_dev_checkpoint, parsed. ADR-XDEV-001's point
    is that a pushed SHA is not an accepted SHA, so the two SHAs are
    compared here and the answer stated outright."""
    row = _latest_state(conn, "external_dev_checkpoint")
    if row is None:
        return {"present": False,
                "note": "no project_state row with key='external_dev_checkpoint'"}
    try:
        packet = json.loads(row["value"])
    except (TypeError, ValueError) as e:
        return {"present": True, "error": f"value is not JSON: {e}",
                "raw": row["value"][:1000], "recorded_at": row["created_at"]}
    pushed = packet.get("latest_pushed_sha")
    verified = packet.get("latest_remote_verified_sha")
    return {
        "present": True,
        "recorded_at": row["created_at"],
        "source": row["source"],
        "lifecycle_state": packet.get("lifecycle_state"),
        "latest_local_sha": packet.get("latest_local_sha"),
        "latest_pushed_sha": pushed,
        "latest_remote_verified_sha": verified,
        "pushed_sha_is_independently_verified": bool(pushed) and pushed == verified,
        "remote_review_required": packet.get("remote_review_required"),
        "independently_verified": packet.get("independently_verified"),
        "remote_ref": packet.get("remote_ref"),
        "next_transition": packet.get("next_transition"),
        "scope_boundary": packet.get("scope_boundary"),
        "authority": packet.get("authority"),
        "note": packet.get("note"),
    }


# ── mermaid ──────────────────────────────────────────────────────────────

def _mermaid_text(value):
    """Mermaid node labels are quoted strings; quotes and angle brackets
    inside them break the parse, so they are replaced rather than escaped."""
    return (str(value or "")
            .replace('"', "'").replace("<", "‹").replace(">", "›")
            .replace("\n", " ").strip())


def build_mermaid(phases, blockers, current_id):
    """Generated from the same `phases` the panel renders, so the diagram
    and the status cards cannot disagree."""
    lines = ["flowchart TD"]
    for phase in phases:
        parts = [f"{phase['label']} — {phase['description']}",
                 f"[{phase['status_label']}]"]
        for migration in phase.get("migrations", []):
            applied = migration["applied"]
            mark = "applied" if applied is True else (
                "not applied" if applied is False else "unknown")
            parts.append(f"migration {migration['migration']}: "
                         f"{migration['rule']} ({mark})")
        for hook in phase.get("queue_hooks", []):
            if hook.get("found"):
                parts.append(f"queue {hook['item_num']} — {hook['title']}")
            else:
                parts.append(f"queue {hook['item_num']} — not in queue_items")
        label = "<br/>".join(_mermaid_text(p) for p in parts)
        lines.append(f'  {phase["id"]}["{label}"]')
    for a, b in zip(phases, phases[1:]):
        lines.append(f'  {a["id"]} --> {b["id"]}')

    if blockers and current_id:
        for blocker in blockers:
            node = "BLK_" + _slug(blocker["id"] or f"REV{blocker['revision']}")
            text = _mermaid_text(f"{blocker['id'] or 'discovery'} "
                                 f"(rev {blocker['revision']}) blocking")
            lines.append(f'  {node}["{text}"]')
            lines.append(f'  {node} -.->|blocks closeout| {current_id}')
            lines.append(f"  class {node} blockerNode")

    for phase in phases:
        cls = {"complete": "donePhase", "active": "activePhase",
               "next": "nextPhase"}.get(phase["status"], "pendingPhase")
        if phase["status"] == "active" and phase["blocked"]:
            cls = "blockedPhase"
        lines.append(f'  class {phase["id"]} {cls}')

    lines += [
        "  classDef donePhase fill:#1f3d2b,stroke:#3f8f5f,color:#e6f3ea",
        "  classDef activePhase fill:#1f3350,stroke:#5b8fd6,color:#e8f0fb",
        "  classDef blockedPhase fill:#4a2630,stroke:#c9637a,color:#fbe9ee",
        "  classDef nextPhase fill:#3d3520,stroke:#b79a43,color:#f8f1dc",
        "  classDef pendingPhase fill:#23262c,stroke:#4a5058,color:#c7ccd4",
        "  classDef blockerNode fill:#3a1f27,stroke:#c9637a,color:#fbe9ee",
    ]
    return "\n".join(lines)


# ── the read model ───────────────────────────────────────────────────────

def _status_label(status, blocked):
    if status == "active" and blocked:
        return "active / blocked"
    return status


def get_build_path(db_path=None):
    conn = _connect(db_path)
    try:
        roadmap_row = _latest_state(conn, ROADMAP_STATE_KEY)
        phase_row = _latest_state(conn, PHASE_POINTER_STATE_KEY)
        direction_row = _latest_state(conn, "current_direction")
        next_action_row = _latest_state(conn, "next_action")
        task_row = _latest_state(conn, CURRENT_TASK_STATE_KEY)

        stages, constraints_text, parse_note = parse_roadmap_sequence(
            roadmap_row["value"] if roadmap_row else None)

        decisions = roadmap_decisions(conn)
        by_id = {d["id"]: d for d in decisions}
        unlock_points = parse_migration_unlock_points(
            (by_id.get("ADR-PIPE-001") or {}).get("decision"))

        # Current phase: the one project_state.build_phase names. Never
        # advanced or inferred from how much work looks done.
        current_id, current_note = None, None
        if phase_row:
            match = _CURRENT_PHASE_RE.search(phase_row["value"])
            if match:
                candidate = match.group(1).upper()
                if any(s["id"] == candidate for s in stages):
                    current_id = candidate
                else:
                    current_note = (f"build_phase names {candidate}, which is not a "
                                    "stage in the parsed pipeline_roadmap chain")
            else:
                current_note = ("project_state.build_phase names no 'Phase P<n>' — "
                                "current phase is unknown, not assumed")
        else:
            current_note = "no project_state row with key='build_phase'"

        current_task = task_row["value"] if task_row else None
        discoveries, discovery_note = ([], None)
        if current_task:
            discoveries, discovery_note = task_discoveries(current_task, db_path=db_path)
        else:
            discovery_note = (f"no project_state row with key='{CURRENT_TASK_STATE_KEY}' — "
                              "no task's discoveries are attributed to the current phase")
        groups = _discovery_groups(discoveries)
        blockers = groups["blocking"]

        # Triage constraints, quoted from ADR-PIPE-006 itself.
        triage_constraints = []
        adr006 = (by_id.get("ADR-PIPE-006") or {}).get("decision") or ""
        for name, pattern in _TRIAGE_CONSTRAINT_PROBES:
            found = pattern.search(adr006)
            if found:
                triage_constraints.append({
                    "constraint": name,
                    "source": "ADR-PIPE-006",
                    "quote": " ".join(found.group(0).split()),
                })

        queue = queue_classification(conn)
        current_index = next((s["order"] for s in stages if s["id"] == current_id), None)

        phases = []
        for stage in stages:
            if current_index is None:
                status = "pending"
            elif stage["order"] < current_index:
                status = "complete"
            elif stage["order"] == current_index:
                status = "active"
            elif stage["order"] == current_index + 1:
                status = "next"
            else:
                status = "pending"
            blocked = status == "active" and bool(blockers)

            migrations = [dict(m) for m in unlock_points.get(stage["id"], [])]
            for migration in _UNLOCK_RE.findall(stage["description"]):
                if not any(m["migration"] == migration for m in migrations):
                    migrations.append({
                        "migration": migration,
                        "rule": "unlocked at this phase",
                        "source_quote": (f"project_state.pipeline_roadmap: "
                                         f"{stage['label']} ({stage['description']})"),
                    })
            for migration in migrations:
                migration.update(_migration_applied(conn, migration["migration"]))

            phase = {
                "id": stage["id"],
                "label": stage["label"],
                "order": stage["order"],
                "description": stage["description"],
                "status": status,
                "blocked": blocked,
                "status_label": _status_label(status, blocked),
                "is_current": stage["id"] == current_id,
                "is_next": status == "next",
                "migrations": migrations,
                "queue_hooks": [_queue_item(conn, n)
                                for n in _queue_hook_nums(stage["description"])],
                "constraints": [],
                "discoveries": None,
            }

            if stage["id"] == "QUEUE_TRIAGE":
                phase["constraints"] = triage_constraints
                phase["queue_classification"] = queue
            if stage["id"] == current_id:
                phase["task"] = current_task
                phase["discoveries"] = groups
                if discovery_note:
                    phase["discoveries_note"] = discovery_note
            phases.append(phase)

        current = next((p for p in phases if p["id"] == current_id), None)
        following = next((p for p in phases if p["status"] == "next"), None)

        return {
            "read_model": READ_MODEL_KIND,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "state_revision": cs.compute_state_revision(conn),
            "status_vocabulary": list(STATUS_VOCABULARY),
            "authority": {
                "sequencing": ("project_decisions + project_state.pipeline_roadmap "
                               "(ADR-PIPE-006)"),
                "work_items": "queue_items + queue_edges (ADR-PIPE-006)",
                "generated_view": ("docs/UNIFIED_BUILD_LIST.md is a generated "
                                   "projection of the queue, not an authority — "
                                   "it is not read by this read model"),
                "retired": ("build_plan_nodes is the retired tier-plan mechanism "
                            "and is not read by this read model"),
                "separation_note": ("the roadmap and the queue are intentionally "
                                    "separate planes; no queue edge encodes phase "
                                    "sequencing, and none is synthesized here"),
            },
            "roadmap_source": {
                "state_key": ROADMAP_STATE_KEY,
                "row_id": roadmap_row["id"] if roadmap_row else None,
                "recorded_at": roadmap_row["created_at"] if roadmap_row else None,
                "raw": roadmap_row["value"] if roadmap_row else None,
                "constraints_text": constraints_text or None,
                "parse_note": parse_note,
            },
            "progress": {
                "total_phases": len(phases),
                "complete": sum(1 for p in phases if p["status"] == "complete"),
                "current_order": current_index,
                "current_phase_note": current_note,
            },
            "current": None if current is None else {
                "phase_id": current["id"],
                "label": current["label"],
                "status": current["status"],
                "blocked": current["blocked"],
                "status_label": current["status_label"],
                "task": current_task,
                "evidence": {
                    "state_key": PHASE_POINTER_STATE_KEY,
                    "row_id": phase_row["id"] if phase_row else None,
                    "recorded_at": phase_row["created_at"] if phase_row else None,
                    "value": phase_row["value"] if phase_row else None,
                },
            },
            "next": None if following is None else {
                "phase_id": following["id"],
                "label": following["label"],
                "status": following["status"],
                "description": following["description"],
            },
            "next_action": None if next_action_row is None else {
                "recorded_at": next_action_row["created_at"],
                "source": next_action_row["source"],
                "text": next_action_row["value"],
            },
            "current_direction": None if direction_row is None else {
                "recorded_at": direction_row["created_at"],
                "source": direction_row["source"],
                "text": direction_row["value"],
            },
            "phases": phases,
            "blockers": blockers,
            "discoveries": groups,
            "discoveries_note": discovery_note,
            "queue": queue,
            "checkpoint": external_checkpoint(conn),
            "decisions": decisions,
            "mermaid": build_mermaid(phases, blockers, current_id),
        }
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mermaid", action="store_true",
                    help="print only the Mermaid diagram source")
    ap.add_argument("--db", default=os.environ.get("CIS_SPINE_PATH"),
                    help="spine database path (default: canonical_state.DB)")
    args = ap.parse_args()
    model = get_build_path(db_path=args.db)
    if args.mermaid:
        print(model["mermaid"])
    else:
        print(json.dumps(model, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
