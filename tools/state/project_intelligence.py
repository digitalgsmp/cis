#!/usr/bin/env python3
"""project_intelligence.py — read-only COMPOSITION read model for the
Workbench "Project Map" (Workbench Project Map card).

WHAT THIS IS. One navigable, plain-language explanation of how the project's
existing authorities relate to each other, for a reader who is not a
programmer:

    problem / discovery -> work -> solution direction -> capability
    -> code / files -> build position -> destination

It is a LAYER OVER existing read models, not a new one beside them, and not a
new authority. Its three rules, in order of importance:

  1. COMPOSE, NEVER RESTATE. The P0–P6 sequence is whatever
     tools/state/build_path.py says it is; the WIASW destination graph is
     whatever tools/state/destination_architecture.py says it is. Both are
     CALLED here. Neither is parsed again, cached, re-derived or hardcoded,
     and this module contains no phase list and no destination node list. If
     one of them fails, that is reported — its area goes unavailable, and the
     rest of the map still loads.

  2. NEVER INVENT A LINK. Every relationship this module reports carries a
     confidence_class saying how it is known:

        authoritative          an authority states it outright (a decision
                               clause, a project_state row, a queue_edges row)
        derived_from_evidence  a deterministic, quoted observation — a literal
                               name appearing in an authority's own text, a
                               file present on disk, a blueprint registered in
                               runtime/container_app.py
        not_yet_linked         nothing records it. Said out loud rather than
                               filled in: "No authoritative link recorded yet."

     An inferred relationship is NEVER reported as authoritative, and no
     probabilistic score is produced — confidence_class is a provenance
     classification, not a model's confidence.

  3. WRITE NOTHING, CLASSIFY NOTHING. The spine is opened mode=ro. No queue
     item is classified, renumbered, merged, re-titled or given a scope or a
     need_status; no queue edge is created or implied; no phase advances; no
     discovery is resolved. The 56 unclassified queue_items are COUNTED and
     LISTED as awaiting triage, which is the whole point of showing them.

CAPABILITIES ARE DERIVED, AND SAY SO. CIS has no capability table, and this
card is not permitted to add one. The capability grouping below is therefore a
DERIVED READ-MODEL CLASSIFICATION whose membership comes from reviewed static
metadata (project_intelligence_vocabulary.json) and whose STATUS comes entirely
from observation: does the file exist on disk, does runtime/container_app.py
register the blueprint, do the tables the migration creates exist. Where the
build authority's own text names a capability, that sentence is quoted beside
it rather than paraphrased into a status. functional_spec was inspected as a
candidate authority and rejected: it is a June-2026 document-block extraction
whose build_status is 'unspecified' on all 63 rows, so treating it as a
capability authority would manufacture one.

NO MODEL IS CALLED AT READ TIME. Every plain-language string shown as durable
truth is either quoted from an authority row or read from the reviewed static
vocabulary file. This module imports no HTTP client, no model client and no
gateway, and performs no network access of any kind.

STATUS SYSTEMS ARE KEPT APART. A build-phase status, a discovery disposition, a
queue need_status, a capability activation and a destination activation state
are five different vocabularies answering five different questions. They are
never merged into one badge here; each is carried with the name of the system
it belongs to.

Usage:
    python3 tools/state/project_intelligence.py              # full model
    python3 tools/state/project_intelligence.py --summary    # counts only
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

import build_path as bp  # noqa: E402  (COMPOSED, not reimplemented)
import canonical_state as cs  # noqa: E402  (shared DB default + state revision)
import destination_architecture as da  # noqa: E402  (COMPOSED, not reimplemented)

from tools.development import continuity_store as _continuity  # noqa: E402
from tools.development import discovery as _discovery  # noqa: E402

READ_MODEL_KIND = "cis_project_intelligence"

VOCABULARY_PATH = _STATE_DIR / "project_intelligence_vocabulary.json"
CONTAINER_APP_PATH = REPO_ROOT / "runtime" / "container_app.py"

# ── provenance vocabulary ────────────────────────────────────────────────
# The card's own three classes. NOT a probability, and deliberately not a
# number: each value names HOW a relationship is known, and "not_yet_linked"
# is a first-class answer rather than a gap to be filled in.
AUTHORITATIVE = "authoritative"
DERIVED = "derived_from_evidence"
NOT_LINKED = "not_yet_linked"

CONFIDENCE_CLASSES = [
    {
        "id": AUTHORITATIVE,
        "label": "Stated by an authority",
        "plain_english": "A decision, a recorded state row or a stored relationship says this outright.",
        "technical_note": "project_decisions clause, project_state row, or a queue_edges row with confidence='explicit'.",
    },
    {
        "id": DERIVED,
        "label": "Derived from quoted evidence",
        "plain_english": "Nobody wrote this link down directly, but something checkable implies it — and the evidence is quoted beside it.",
        "technical_note": ("a literal identifier appearing in an authority's own text, a file observed on "
                           "disk, a blueprint observed registered in runtime/container_app.py, a table "
                           "observed present in the live schema, or a queue_edges row with "
                           "confidence='prose'."),
    },
    {
        "id": NOT_LINKED,
        "label": "No authoritative link recorded yet",
        "plain_english": "Nothing in the project records a connection here. This is shown as a gap, not filled in with a guess.",
        "technical_note": "the chain is broken deliberately; see the explanation on the element itself.",
    },
]

MISSING_LINK_TEXT = "No authoritative link recorded yet."
MISSING_PLAIN_LANGUAGE_TEXT = "Plain-language explanation not yet recorded."

# Presentation modes. Named here so the payload declares which fields belong to
# which level of disclosure and the screen cannot invent a fourth mode or hide
# a technical field the card requires to be reachable.
MODES = [
    {
        "id": "simple",
        "label": "Simple",
        "default": True,
        "plain_english": "Plain language only: what it is, what it does, why it matters, whether it is on.",
        "shows": ["plain_english", "what_it_does", "why_it_matters", "status_plain", "connections"],
    },
    {
        "id": "detail",
        "label": "More Detail",
        "default": False,
        "plain_english": "Adds the capability, the build position, the related problems and work, and the evidence.",
        "shows": ["capability", "build_position", "problems", "queue", "destination_relationship",
                  "files", "evidence"],
    },
    {
        "id": "technical",
        "label": "Technical",
        "default": False,
        "plain_english": "Adds the exact identifiers: paths, modules, endpoints, tables, migration numbers and record ids.",
        "shows": ["paths", "module_names", "endpoints", "db_tables", "migration_numbers",
                  "decision_ids", "discovery_ids", "queue_ids", "commit_refs", "authority_refs"],
    },
]

# Endpoint surface of the Workbench read-only views, for Technical mode. These
# are the routes this project's own blueprints declare; they are reported, not
# called.
_ENDPOINTS = {
    "build_path_bp": "GET /api/workbench/build-path",
    "destination_architecture_bp": "GET /api/workbench/destination-architecture",
    "project_intelligence_bp": "GET /api/workbench/project-intelligence",
    "system_context_bp": "GET /api/workbench/system-context",
    "braingate_conversation_bp": "GET/POST /api/workbench/projects …",
    "workbench_oidc_bp": "GET /api/workbench/auth/session …",
    "relay_bp": "POST /api/relay/start …",
}

# app.register_blueprint(NAME)
_REGISTER_RE = re.compile(r"^\s*app\.register_blueprint\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
                          re.M)

_QUEUE_BODY_LIMIT = 800
_SUMMARY_LIMIT = 2000


# ── low-level reads ──────────────────────────────────────────────────────

def _connect(db_path=None):
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (name,)
    ).fetchone() is not None


def _truncate(text, limit=_SUMMARY_LIMIT):
    text = text or ""
    if len(text) <= limit:
        return text, False
    return text[:limit].rstrip() + "…", True


def _sentences(text):
    """Rough sentence split, used only to QUOTE the sentence an authority
    actually wrote around a literal match. Never used to decide anything."""
    return [s.strip() for s in re.split(r"(?<=[.;])\s+", text or "") if s.strip()]


def _quote_mentioning(text, needle):
    """The authority's own sentence containing `needle`, or None. Case
    insensitive, because the match is a literal identifier the authority
    chose and this module must not depend on its capitalisation."""
    low = (needle or "").lower()
    if not low:
        return None
    for sentence in _sentences(text):
        if low in sentence.lower():
            return " ".join(sentence.split())
    return None


def _ref(kind, **fields):
    """One authority reference. `kind` names the KIND of source so a reader
    can tell a decision clause from an observed file without reading the
    fields."""
    out = {"kind": kind}
    out.update(fields)
    return out


def _relationship(source, target, relationship, confidence_class, authority_refs,
                  explanation):
    """The card's relationship object, used for every cross-view link in this
    model. `confidence_class` is provenance, never probability."""
    return {
        "source": source,
        "target": target,
        "relationship": relationship,
        "confidence_class": confidence_class,
        "authority_refs": list(authority_refs or []),
        "explanation": explanation,
    }


# ── reviewed static explanatory metadata ─────────────────────────────────

def load_vocabulary(path=None):
    """The reviewed plain-language layer. Returns (vocabulary, problem).

    This file is NOT an authority and nothing is derived from it: it supplies
    wording keyed to elements that the live state already produced. A missing
    or unreadable file is reported and the map renders with technical text and
    "Plain-language explanation not yet recorded." everywhere — degraded, but
    never fabricated."""
    target = Path(path or VOCABULARY_PATH)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, {
            "kind": "vocabulary_missing",
            "detail": (f"{target.relative_to(REPO_ROOT) if target.is_absolute() and str(target).startswith(str(REPO_ROOT)) else target} "
                       "is not present, so no reviewed plain-language text is available. "
                       "Technical text is shown instead; nothing is generated to cover for it"),
        }
    except (OSError, ValueError) as e:
        return None, {
            "kind": "vocabulary_unreadable",
            "detail": f"the reviewed vocabulary file could not be read: {type(e).__name__}: {e}",
        }
    if not isinstance(data, dict):
        return None, {"kind": "vocabulary_unreadable",
                      "detail": "the reviewed vocabulary file is not a JSON object"}
    return data, None


def _index(entries, key):
    out = {}
    for entry in entries or []:
        if isinstance(entry, dict) and entry.get(key):
            out.setdefault(entry[key], entry)
    return out


# ── observed implementation evidence ─────────────────────────────────────

def registered_blueprints(path=None):
    """{blueprint_name: line_number} actually registered in
    runtime/container_app.py, observed by reading the file.

    This is deliberately the activation fact and nothing more. Registration is
    what makes a route answer (ADR-level: route absence IS the stage boundary
    in this project), so observing it is observing whether the capability has
    a surface. It is NOT read as an architectural relationship, and no import
    graph is built from it — a module importing another module says nothing
    about architecture and is not treated as if it did."""
    try:
        source = Path(path or CONTAINER_APP_PATH).read_text(encoding="utf-8")
    except OSError as e:
        return None, {
            "kind": "registration_unreadable",
            "detail": (f"runtime/container_app.py could not be read ({type(e).__name__}), so "
                       "no capability's registration could be observed; capability surfaces "
                       "are reported as unknown rather than assumed"),
        }
    out = {}
    for match in _REGISTER_RE.finditer(source):
        line = source.count("\n", 0, match.start()) + 1
        out.setdefault(match.group(1), line)
    return out, None


def _file_evidence(rel_path):
    """Observed existence of one implementation file. Size and line count are
    reported so Technical mode can show something checkable; nothing is
    inferred from the contents."""
    target = REPO_ROOT / rel_path
    try:
        stat = target.stat()
    except OSError:
        return {"path": rel_path, "exists": False,
                "note": "declared as implementation but not present at this path"}
    lines = None
    try:
        lines = sum(1 for _ in target.open("r", encoding="utf-8", errors="replace"))
    except OSError:
        pass
    return {"path": rel_path, "exists": True, "bytes": stat.st_size, "lines": lines}


def _migration_evidence(conn, migration):
    """Whether a migration's own tables are present in the live schema.

    bp.migration_tables() is REUSED rather than reimplemented: the question
    "what does migration NNNN create" already has exactly one answer in this
    repository, and a second copy of it could disagree with the Build Path
    screen about whether 0036 is applied."""
    tables = bp.migration_tables(migration)
    if not tables:
        return {"migration": migration, "applied": None, "tables": {},
                "detected_by": ("unknown — no readable "
                                f"runtime/schema/migrations/{migration}_*.sql")}
    present = {t: _table_exists(conn, t) for t in tables}
    applied = True if all(present.values()) else ("partial" if any(present.values()) else False)
    return {
        "migration": migration, "applied": applied, "tables": present,
        "detected_by": f"presence of the tables {migration}_*.sql creates: {', '.join(tables)}",
    }


# ── capability read model (DERIVED — see module docstring) ───────────────

CAPABILITY_PROVENANCE = {
    "class": DERIVED,
    "authority_exists": False,
    "statement": (
        "CIS has no capability authority. There is no capability table, no capability "
        "project_state row and no capability decision family, and this card is not "
        "permitted to create one. The grouping below is a DERIVED read-model "
        "classification: its membership comes from reviewed static metadata in "
        "tools/state/project_intelligence_vocabulary.json, and every status on it is "
        "observed (file present on disk, blueprint registered in runtime/container_app.py, "
        "migration tables present in the live schema). It must not be treated as a "
        "planning authority, and nothing writes it back."
    ),
    "candidates_inspected": [
        {
            "candidate": "functional_spec",
            "verdict": "rejected as a capability authority",
            "detail": ("63 rows from a 2026-06-26 document-block extraction. build_status is "
                       "'unspecified' on every row, component_name holds prose descriptions of "
                       "document blocks rather than capability names, and nothing maintains it. "
                       "Reading it as capability authority would manufacture an authority that "
                       "the project never decided on"),
        },
        {
            "candidate": "build_plan_nodes",
            "verdict": "rejected",
            "detail": "retired tier-plan mechanism per ADR-PIPE-006; not read by this read model",
        },
        {
            "candidate": "workbench_oidc.stage_capabilities()",
            "verdict": "not an architecture authority",
            "detail": ("it reports which routes the live Flask app registered, for the browser. "
                       "That is the same observation this read model makes from "
                       "runtime/container_app.py, and it is activation evidence, not a "
                       "capability model"),
        },
    ],
}

# Capability activation vocabulary — this read model's OWN, kept deliberately
# distinct from ADR-PIPE-005's component-state vocabulary, from build-phase
# status, from queue need_status and from destination activation state.
CAPABILITY_STATES = [
    {"id": "REGISTERED", "plain_english": "Switched on — the server plugs this in.",
     "technical_note": "its blueprint appears in a register_blueprint call in runtime/container_app.py"},
    {"id": "BUILT_NOT_REGISTERED", "plain_english": "Built, but deliberately switched off.",
     "technical_note": "the implementation files are present; the blueprint is not registered"},
    {"id": "NO_ROUTE_SURFACE", "plain_english": "Present, but not something the browser calls directly.",
     "technical_note": "declared with no blueprint — a process or tooling capability"},
    {"id": "FILES_MISSING", "plain_english": "Declared, but the code is not where it is said to be.",
     "technical_note": "at least one declared implementation file does not exist at its path"},
    {"id": "UNKNOWN", "plain_english": "Could not be determined.",
     "technical_note": "runtime/container_app.py could not be read, so registration was not observed"},
]


def _capability_status(entry, files, registered, registration_problem):
    blueprint = entry.get("blueprint")
    if any(not f["exists"] for f in files):
        return "FILES_MISSING"
    if not blueprint:
        return "NO_ROUTE_SURFACE"
    if registration_problem is not None or registered is None:
        return "UNKNOWN"
    return "REGISTERED" if blueprint in registered else "BUILT_NOT_REGISTERED"


def _authority_mentions(entry, authority_texts):
    """Sentences the BUILD authority itself wrote about this capability.

    A capability's real component state (ADR-PIPE-005's BUILT_AND_ACTIVE /
    BUILT_BUT_DORMANT vocabulary) belongs to the build authority, not to this
    screen. Rather than restating it — which would be a second copy that can
    drift — the authority's own sentence is quoted whenever it names one of the
    capability's declared identifiers. The LINK is derived (a literal name
    match); the TEXT is the authority's."""
    found = []
    for term in entry.get("identifier_terms", []):
        for source_name, text in authority_texts:
            quote = _quote_mentioning(text, term)
            if quote and not any(f["quote"] == quote for f in found):
                found.append({"source": source_name, "matched_term": term, "quote": quote})
    return found


def build_capabilities(conn, vocabulary, registered, registration_problem,
                       authority_texts, phases):
    """The derived capability view. Every element carries its provenance."""
    capabilities = []
    for entry in (vocabulary or {}).get("capabilities", []):
        files = [_file_evidence(p) for p in entry.get("files", [])]
        migrations = [_migration_evidence(conn, m) for m in entry.get("migrations", [])]
        status = _capability_status(entry, files, registered, registration_problem)

        registration = {
            "blueprint": entry.get("blueprint"),
            "surface": entry.get("surface"),
            "endpoint": _ENDPOINTS.get(entry.get("blueprint")),
            "observed_in": "runtime/container_app.py",
        }
        if entry.get("blueprint") and registered is not None:
            line = registered.get(entry["blueprint"])
            registration["registered"] = line is not None
            registration["evidence"] = (
                f"runtime/container_app.py:{line} — app.register_blueprint({entry['blueprint']})"
                if line is not None else
                f"no app.register_blueprint({entry['blueprint']}) in runtime/container_app.py")
        elif entry.get("blueprint"):
            registration["registered"] = None
            registration["evidence"] = "registration could not be observed"
        else:
            registration["registered"] = None
            registration["evidence"] = "no blueprint declared — this capability has no HTTP surface"

        # Build position: ONLY where the roadmap's own phase description names
        # one of the capability's declared terms. No phase is assigned here.
        build_position = []
        for phase in phases:
            for term in entry.get("roadmap_phase_terms", []):
                if term.lower() in (phase.get("description") or "").lower():
                    build_position.append({
                        "phase_id": phase["id"],
                        "phase_label": phase["label"],
                        "phase_status": phase["status"],
                        "confidence_class": DERIVED,
                        "authority_refs": [_ref(
                            "project_state_row", state_key="pipeline_roadmap",
                            quote=f"{phase['label']} ({phase['description']})",
                            matched_term=term)],
                    })
                    break

        capabilities.append({
            "id": entry["id"],
            "label": entry["label"],
            "anatomy_id": entry.get("anatomy_id"),
            "plain_english": entry.get("plain_english") or MISSING_PLAIN_LANGUAGE_TEXT,
            "plain_language_recorded": bool(entry.get("plain_english")),
            "provenance_class": DERIVED,
            "provenance_note": ("membership from reviewed static metadata; status observed from "
                                "the repository and the live schema"),
            "status": status,
            "registration": registration,
            "files": files,
            "migrations": migrations,
            "decision_ids": entry.get("decision_ids", []),
            "identifier_terms": entry.get("identifier_terms", []),
            "build_position": build_position,
            "build_position_note": (None if build_position else
                                    "No phase in the recorded roadmap names this capability. "
                                    + MISSING_LINK_TEXT),
            "authority_mentions": _authority_mentions(entry, authority_texts),
            # Deliberately empty and deliberately explained. See
            # destination_link() for the one recorded link between current work
            # and the destination graph.
            "destination_link": {
                "confidence_class": NOT_LINKED,
                "explanation": (
                    "No decision links this capability to a destination architecture node. "
                    "The only recorded relationship between current CIS work and the "
                    "destination graph is CIS itself (ADR-WIASW-002), shown in Trajectory. "
                    + MISSING_LINK_TEXT),
            },
            "problem_ids": [],   # filled in by link_problems_to_capabilities()
        })
    return capabilities


# ── system anatomy ───────────────────────────────────────────────────────

def build_anatomy(vocabulary, capabilities):
    """Major functional areas, each answering the card's seven questions.

    Status is NOT stated by the metadata: it is rolled up from the observed
    capability statuses underneath, so an area cannot claim to be active while
    everything in it is unregistered."""
    by_id = {c["id"]: c for c in capabilities}
    areas = []
    for entry in (vocabulary or {}).get("anatomy", []):
        members, missing = [], []
        for cap_id in entry.get("capability_ids", []):
            if cap_id in by_id:
                members.append(by_id[cap_id])
            else:
                missing.append(cap_id)

        states = {m["status"] for m in members}
        if not members:
            status, plain = "INFORMATIONAL", "Described here, with no capability attached to it yet."
        elif "REGISTERED" in states:
            status, plain = "ACTIVE", "At least one part of this is switched on."
        elif states == {"NO_ROUTE_SURFACE"}:
            status, plain = "ACTIVE", "Working, as tooling rather than as a web feature."
        elif "FILES_MISSING" in states:
            status, plain = "INCOMPLETE", "Something declared here is not present in the code."
        elif "UNKNOWN" in states:
            status, plain = "UNKNOWN", "Could not be determined from the repository."
        else:
            status, plain = "DORMANT", "Built, and deliberately switched off."

        areas.append({
            "id": entry["id"],
            "label": entry["label"],
            "plain_english": entry.get("plain_english") or MISSING_PLAIN_LANGUAGE_TEXT,
            "what_it_does": entry.get("what_it_does"),
            "why_cis_needs_it": entry.get("why_cis_needs_it"),
            "status": status,
            "status_plain": plain,
            "status_derivation": ("rolled up from the observed status of the capabilities below; "
                                  "not stated by any authority and not written anywhere"),
            "capability_ids": [m["id"] for m in members],
            "capabilities": [{
                "id": m["id"], "label": m["label"], "status": m["status"],
                "plain_english": m["plain_english"],
            } for m in members],
            "unresolved_capability_ids": missing,
            "files": sorted({f["path"] for m in members for f in m["files"]}),
        })
    return areas


# ── problems / discoveries ───────────────────────────────────────────────

_SOLUTION_FIELDS = {
    "RESOLVED_NOW": ("resolution_result", "the resolution recorded with the finding itself"),
    "EXPLICITLY_DEFERRED": ("destination", "where the finding was deferred to"),
}


def _discovery_tasks(conn):
    if not _table_exists(conn, "dev_continuity_events"):
        return [], "dev_continuity_events table not present on this database"
    rows = conn.execute(
        "SELECT DISTINCT task FROM dev_continuity_events ORDER BY task").fetchall()
    return [r[0] for r in rows], None


def _reconciliations(db_path, task):
    """Reconciliation events for `task`, keyed by the revision they close.
    A reconciliation is how this project records that something was DONE about
    a finding, so it is the authoritative recorded solution when one exists."""
    conn = _continuity.connect(db_path or cs.DB)
    try:
        if not _continuity.is_initialized(conn):
            return {}, {}
        events = _continuity.list_events(conn, task)
    except Exception as e:  # noqa: BLE001 — an odd ledger must not 500 the screen
        return {}, {"error": f"{type(e).__name__}: {e}"}
    finally:
        conn.close()
    by_against = {}
    payloads = {}
    for event in events:
        if event["kind"] == "reconciliation" and event.get("against_revision") is not None:
            by_against.setdefault(event["against_revision"], {
                "revision": event["revision"],
                "disposition": event["status"],
                "actor": event["actor"],
                "summary": event["summary"],
                "created_at": event["created_at"],
            })
        if event["kind"] == "unfinished_work":
            try:
                body = json.loads(event.get("body") or "{}")
            except (TypeError, ValueError):
                body = {}
            if isinstance(body, dict):
                payloads[event["revision"]] = body
    return by_against, payloads


def _solution_direction(record, payload, reconciliation):
    """What the project RECORDED doing about this finding — never a solution
    composed here. A finding whose authority only describes the problem gets
    the honest answer."""
    refs, text, cls = [], None, NOT_LINKED
    disposition = record.get("disposition")
    field = _SOLUTION_FIELDS.get(disposition)
    if field and payload.get(field[0]):
        text = " ".join(str(payload[field[0]]).split())
        cls = AUTHORITATIVE
        refs.append(_ref("discovery_record", task=record["task"], revision=record["revision"],
                         field=field[0], note=field[1]))
    if reconciliation:
        summary = " ".join((reconciliation["summary"] or "").split())
        refs.append(_ref("reconciliation_event", task=record["task"],
                         revision=reconciliation["revision"],
                         against_revision=record["revision"],
                         disposition=reconciliation["disposition"], quote=summary))
        cls = AUTHORITATIVE
        if not text:
            text = summary
    if cls == NOT_LINKED:
        return {
            "confidence_class": NOT_LINKED,
            "text": None,
            "explanation": ("Current solution direction: not formally recorded. The authority "
                            "describes the problem only, and nothing is composed here to fill "
                            "the gap."),
            "authority_refs": [],
        }
    return {"confidence_class": cls, "text": text,
            "explanation": "Recorded by the project itself, quoted above.",
            "authority_refs": refs}


def _next_action_mentions(discovery_id, state_texts):
    """project_state rows that name this finding by id. The quote is the
    authority's; the LINK is derived from a literal id match and labelled so."""
    out = []
    if not discovery_id:
        return out
    for key, text in state_texts:
        quote = _quote_mentioning(text, discovery_id)
        if quote:
            out.append({"state_key": key, "quote": quote,
                        "confidence_class": DERIVED,
                        "matched_term": discovery_id})
    return out


def build_problems(conn, db_path, vocabulary, current_task, state_texts):
    """Every recorded discovery, as a problem a non-programmer can read.

    Display status, "resolved" and "blocking" are NOT redefined here:
    bp.task_discoveries() is reused, so the Project Map, the Build Path screen
    and the closeout gate cannot disagree about whether something is blocking."""
    problems, problems_note = [], None
    tasks, note = _discovery_tasks(conn)
    if note:
        return [], note, []

    explanations = _index((vocabulary or {}).get("discoveries", []), "id")
    used_explanations = set()

    for task in tasks:
        # bp.task_discoveries is the single definition of a discovery's display
        # status; the raw payload fields (resolution_result / destination /
        # reason / trigger) are read alongside it because that function does
        # not carry them.
        records, task_note = bp.task_discoveries(task, db_path=db_path)
        if task_note and not problems_note:
            problems_note = task_note
        reconciliations, payloads = _reconciliations(db_path, task)

        for record in records:
            payload = payloads.get(record["revision"], {})
            reconciliation = reconciliations.get(record["revision"])
            explanation = explanations.get(record["id"]) if record["id"] else None
            if explanation:
                used_explanations.add(record["id"])
            summary, truncated = _truncate(record["summary"])

            problems.append({
                "id": record["id"],
                "task": task,
                "revision": record["revision"],
                "plain_english": (explanation or {}).get("plain_english")
                                 or MISSING_PLAIN_LANGUAGE_TEXT,
                "why_it_matters": (explanation or {}).get("why_it_matters"),
                "plain_language_recorded": bool(explanation),
                "plain_language_provenance": ("reviewed_static_explanatory_metadata"
                                              if explanation else None),
                # Three distinct status systems, kept apart on purpose.
                "display_status": record["status"],
                "disposition": record["disposition"],
                "blocking": record["blocking"],
                "resolved": record["resolved"],
                "malformed": record["malformed"],
                "status_systems": {
                    "discovery_disposition": record["disposition"],
                    "discovery_display_status": record["status"],
                    "note": ("a discovery disposition is NOT a build-phase status and NOT a "
                             "queue need_status; the three are different vocabularies"),
                },
                "summary": summary,
                "summary_truncated": truncated,
                "solution_direction": _solution_direction(record, payload, reconciliation),
                "deferral": {
                    "reason": payload.get("reason"),
                    "destination": payload.get("destination"),
                    "trigger": payload.get("trigger"),
                } if record["disposition"] == "EXPLICITLY_DEFERRED" else None,
                "originating_stage": payload.get("originating_stage"),
                "named_in_state": _next_action_mentions(record["id"], state_texts),
                "is_current_task": task == current_task,
                "evidence": {
                    "table": "dev_continuity_events",
                    "task": task,
                    "revision": record["revision"],
                    "recorded_at": record["created_at"],
                    "kind": "unfinished_work",
                },
                "capability_ids": [],      # filled in by link_problems_to_capabilities()
                "build_position": None,    # filled in by attach_problem_build_position()
            })

    stale = sorted(set(explanations) - used_explanations)
    return problems, problems_note, stale


def link_problems_to_capabilities(problems, capabilities):
    """Derived, quoted, two-way links between a finding and a capability.

    The only mechanism is a literal identifier the vocabulary declares for the
    capability appearing in the finding's own text. Nothing is matched on
    similarity, and every link carries the term that matched and the sentence
    it matched in."""
    links = []
    by_id = {c["id"]: c for c in capabilities}
    for problem in problems:
        text = problem["summary"] or ""
        for capability in capabilities:
            matched = None
            for term in capability["identifier_terms"]:
                if term.lower() in text.lower():
                    matched = term
                    break
            if not matched:
                continue
            problem["capability_ids"].append(capability["id"])
            by_id[capability["id"]]["problem_ids"].append(
                problem["id"] or f"{problem['task']}#{problem['revision']}")
            links.append(_relationship(
                source=problem["id"] or f"{problem['task']}#{problem['revision']}",
                target=capability["id"],
                relationship="problem_concerns_capability",
                confidence_class=DERIVED,
                authority_refs=[_ref("discovery_record", task=problem["task"],
                                     revision=problem["revision"], matched_term=matched,
                                     quote=_quote_mentioning(text, matched))],
                explanation=(f"The finding's own text names {matched!r}, which is a declared "
                             f"identifier of the {capability['label']} capability. The link is "
                             "derived from that literal match, not stated by any authority."),
            ))
    return links


def attach_problem_build_position(problems, build, current_task):
    """A finding's build position, where the two authority rows support it:
    project_state.current_queue_item names the task, and
    project_state.build_phase names the phase."""
    current = (build or {}).get("current") or {}
    phase_id = current.get("phase_id")
    links = []
    for problem in problems:
        if not problem["is_current_task"] or not phase_id:
            problem["build_position"] = {
                "confidence_class": NOT_LINKED,
                "explanation": (
                    f"This finding is recorded against task {problem['task']}, which is not the "
                    "task the project currently points at, so no build position follows from it. "
                    + MISSING_LINK_TEXT) if not problem["is_current_task"] else
                    ("No current phase is recorded in project_state.build_phase, so no build "
                     "position follows. " + MISSING_LINK_TEXT),
            }
            continue
        refs = [
            _ref("project_state_row", state_key="current_queue_item", value=current_task),
            _ref("project_state_row", state_key="build_phase",
                 value=(current.get("evidence") or {}).get("value"),
                 row_id=(current.get("evidence") or {}).get("row_id")),
        ]
        problem["build_position"] = {
            "confidence_class": DERIVED,
            "phase_id": phase_id,
            "phase_label": current.get("label"),
            "phase_status": current.get("status_label"),
            "explanation": (f"Recorded against task {current_task}, which project_state names as "
                            f"the current task, while project_state names {phase_id} as the "
                            "current phase. Both rows are authority; joining them is this "
                            "screen's derivation."),
            "authority_refs": refs,
        }
        links.append(_relationship(
            source=problem["id"] or f"{problem['task']}#{problem['revision']}",
            target=phase_id, relationship="problem_sits_at_phase",
            confidence_class=DERIVED, authority_refs=refs,
            explanation=problem["build_position"]["explanation"]))
    return links


# ── queue ────────────────────────────────────────────────────────────────

def _distribution(conn, column):
    if not _has_column(conn, "queue_items", column):
        return None
    rows = conn.execute(
        f"SELECT {column}, COUNT(*) FROM queue_items GROUP BY {column} "
        "ORDER BY COUNT(*) DESC").fetchall()
    return [{"value": r[0], "count": r[1]} for r in rows]


def _has_column(conn, table, column):
    try:
        return any(r[1] == column for r in conn.execute(f"PRAGMA table_info({table})"))
    except sqlite3.Error:
        return False


def build_queue(conn, vocabulary, build):
    """The queue as it is RIGHT NOW, with nothing classified.

    bp.queue_classification() is reused for the counts so the Project Map and
    the Build Path screen cannot report different triage numbers. Everything
    added here is inventory and distribution — no item is given a scope, a
    need_status, an order, an edge or a rewritten title, and every row with
    neither scope nor need_status is marked AWAITING TRIAGE and left alone."""
    counts = bp.queue_classification(conn)

    has_scope = _has_column(conn, "queue_items", "scope")
    has_check = _has_column(conn, "queue_items", "check_class")
    cols = ["item_num", "tier", "title", "need_status", "body_md", "source_line", "source_sha"]
    if has_scope:
        cols.append("scope")
    if has_check:
        cols.append("check_class")
    rows = conn.execute(
        f"SELECT {', '.join(cols)} FROM queue_items ORDER BY tier, item_num").fetchall()

    explanations = _index((vocabulary or {}).get("queue_items", []), "item_num")
    used = set()

    # Phase hooks the ROADMAP itself declares, taken from the composed build
    # model rather than re-derived. This is the only phase relationship any
    # queue item gets here.
    phases = (build or {}).get("phases", [])
    hooks = {}
    for phase in phases:
        for hook in phase.get("queue_hooks", []):
            hooks.setdefault(hook["item_num"], []).append({
                "phase_id": phase["id"], "phase_label": phase["label"],
                "confidence_class": AUTHORITATIVE,
                "authority_refs": [_ref("project_state_row", state_key="pipeline_roadmap",
                                        quote=f"{phase['label']} ({phase['description']})")],
            })

    edges = []
    if _table_exists(conn, "queue_edges"):
        edges = [dict(r) for r in conn.execute(
            "SELECT from_num, to_num, kind, confidence, evidence FROM queue_edges "
            "ORDER BY from_num, to_num, kind")]
    by_item = {}
    for edge in edges:
        entry = {
            "other": edge["to_num"], "direction": "out", "kind": edge["kind"],
            # queue_edges carries its OWN confidence column. 'explicit' is the
            # authority stating the relation; 'prose' is the extractor reading
            # it out of text. Mapped onto this model's provenance classes
            # rather than invented.
            "confidence_class": AUTHORITATIVE if edge["confidence"] == "explicit" else DERIVED,
            "stored_confidence": edge["confidence"],
            "evidence": _truncate(edge["evidence"], 300)[0],
        }
        by_item.setdefault(edge["from_num"], []).append(entry)
        by_item.setdefault(edge["to_num"], []).append({**entry, "other": edge["from_num"],
                                                      "direction": "in"})

    items = []
    for row in rows:
        item = dict(row)
        body, truncated = _truncate(item.pop("body_md", ""), _QUEUE_BODY_LIMIT)
        awaiting = item.get("need_status") is None and (
            item.get("scope") is None if has_scope else True)
        explanation = explanations.get(item["item_num"])
        if explanation:
            used.add(item["item_num"])
        items.append({
            **item,
            "body_excerpt": body,
            "body_truncated": truncated,
            "awaiting_triage": awaiting,
            "classification_status": "AWAITING TRIAGE" if awaiting else "CLASSIFIED",
            "plain_english": (explanation or {}).get("plain_english")
                             or MISSING_PLAIN_LANGUAGE_TEXT,
            "why_it_matters": (explanation or {}).get("why_it_matters"),
            "plain_language_recorded": bool(explanation),
            "plain_language_provenance": ("reviewed_static_explanatory_metadata"
                                          if explanation else None),
            "phase_hooks": hooks.get(item["item_num"], []),
            "edges": by_item.get(item["item_num"], []),
        })

    # Where the roadmap places triage, taken from the composed build model
    # rather than written out here. The triage stage is found by the fact that
    # the Build Path read model attaches the queue classification to it — so no
    # phase label or phase id is hardcoded, and if the roadmap moves triage,
    # this moves with it.
    triage_phase = next((p for p in phases if "queue_classification" in p), None)
    sequencing = {
        "stage_label": (triage_phase or {}).get("label"),
        "stage_status": (triage_phase or {}).get("status_label"),
        "stage_description": (triage_phase or {}).get("description"),
        "authority": "ADR-PIPE-006",
        "constraints_quote": _truncate(
            ((build or {}).get("roadmap_source") or {}).get("constraints_text"), 600)[0] or None,
        "note": ("the stage, its position and its status come from the Build Path read model, "
                 "which is the authority on where the build is. Nothing about sequencing is "
                 "restated here."),
    }
    if triage_phase is None:
        sequencing["note"] = ("The recorded roadmap does not attach the queue classification to "
                              "any stage, so where triage sits is not shown. "
                              + MISSING_LINK_TEXT)

    return {
        "counts": counts,
        "total_items": counts["total_items"],
        "awaiting_triage": sum(1 for i in items if i["awaiting_triage"]),
        "classified": sum(1 for i in items if not i["awaiting_triage"]),
        "distributions": {
            "need_status": _distribution(conn, "need_status"),
            "scope": _distribution(conn, "scope"),
            "tier": _distribution(conn, "tier"),
            "check_class": _distribution(conn, "check_class"),
        },
        "edge_count": len(edges),
        "items": items,
        "stale_vocabulary_item_nums": sorted(set(explanations) - used),
        "triage_state": {
            "performed_here": False,
            "statement": (
                "Queue triage has NOT been performed by this screen and is not performed by it. "
                "Every row with neither a scope nor a need_status is shown as AWAITING TRIAGE "
                "exactly as the database holds it. Nothing here assigns a scope or a "
                "need_status, renumbers, merges, re-titles, orders or creates an edge."
            ),
            "sequencing": sequencing,
        },
        "authority": ("queue_items + queue_edges are the work-item authority (ADR-PIPE-006). "
                      "docs/UNIFIED_BUILD_LIST.md is a generated projection and is not read."),
    }


# ── trajectory ───────────────────────────────────────────────────────────

def destination_link(destination):
    """The ONE recorded relationship between current CIS build work and the
    destination graph, and the explicit statement that it is not a next phase.

    Both halves are quoted from the authority: ADR-WIASW-002 declares the CIS
    node TRACKED_ELSEWHERE because its implementation status belongs to the
    build authority, and ADR-WIASW-001 declares the WIASW uses CIS edge and
    states outright that finishing P6 does not activate WIASW."""
    if not destination or not destination.get("present"):
        return {
            "confidence_class": NOT_LINKED,
            "explanation": ("No destination architecture is recorded, so no trajectory to one "
                            "is shown. " + MISSING_LINK_TEXT),
            "nodes": [],
        }
    nodes = {n["id"]: n for n in destination.get("nodes", [])}
    steps, refs = [], []

    cis = nodes.get("CIS")
    if cis:
        steps.append({
            "node_id": "CIS", "label": cis["label"], "kind": cis["kind"],
            "activation_state": cis.get("activation_state"),
            "confidence_class": AUTHORITATIVE,
            "explanation": ("The destination architecture records CIS as the substrate, and "
                            "records that CIS's own implementation status belongs to the build "
                            "authority rather than to the destination graph. That is what "
                            "connects today's work to this picture."),
            "authority_refs": [_ref("decision_clause",
                                    decision_id=(cis.get("activation_authority_ref") or {}).get("decision_id"),
                                    clause=(cis.get("activation_authority_ref") or {}).get("clause"),
                                    declaration=(cis.get("activation_authority_ref") or {}).get("declaration"))],
        })
        refs.append(steps[-1]["authority_refs"][0])

    uses = next((e for e in destination.get("edges", [])
                 if e["source"] == "WIASW" and e["target"] == "CIS"), None)
    wiasw = nodes.get("WIASW")
    if uses and wiasw:
        steps.append({
            "node_id": "WIASW", "label": wiasw["label"], "kind": wiasw["kind"],
            "activation_state": wiasw.get("activation_state"),
            "confidence_class": AUTHORITATIVE,
            "explanation": ("The destination architecture states that WIASW uses CIS. That is an "
                            "architectural relationship, not an order of work."),
            "authority_refs": [_ref("decision_clause",
                                    decision_id=(uses.get("authority_ref") or {}).get("decision_id"),
                                    clause=(uses.get("authority_ref") or {}).get("clause"),
                                    declaration=(uses.get("authority_ref") or {}).get("declaration"))],
        })
        refs.append(steps[-1]["authority_refs"][0])

    return {
        "confidence_class": AUTHORITATIVE if steps else NOT_LINKED,
        "is_phase_ordering": False,
        "warning": "Destination relationship — not an automatic next phase.",
        "explanation": (
            "This is an explanatory relationship, not a step in the build order. Completing the "
            "last build phase does not start destination work: the destination architecture says "
            "so in its own words, and destination work requires separate explicit human "
            "authorization."),
        "nodes": steps,
        "authority_refs": refs,
    }


def build_trajectory(build, destination):
    """Today's build order (from the build authority, in its order) followed by
    the destination relationship, visibly separated.

    No phase is reordered, renamed, added or given a status here: each step is
    a reference to the phase the Build Path read model already produced."""
    phases = (build or {}).get("phases", [])
    steps = []
    for phase in phases:
        steps.append({
            "kind": "build_phase",
            "id": phase["id"],
            "label": phase["label"],
            "description": phase["description"],
            "status": phase["status"],
            "status_label": phase["status_label"],
            "blocked": phase["blocked"],
            "is_current": phase["is_current"],
            "order": phase["order"],
            "queue_hooks": [{"item_num": h["item_num"], "found": h.get("found"),
                             "title": h.get("title")} for h in phase.get("queue_hooks", [])],
            "capability_ids": [],   # filled in below
            "source": "tools/state/build_path.py (project_state.pipeline_roadmap + ADR-PIPE-001)",
            "confidence_class": AUTHORITATIVE,
        })
    return {
        "question": "How does today's work move toward that destination?",
        "build_sequence_authority": (
            "the order, the labels and the statuses of these steps come from the Build Path read "
            "model, which parses project_state.pipeline_roadmap. Nothing is sequenced here."),
        "steps": steps,
        "destination_relationship": destination_link(destination),
        "separation_note": (
            "The build steps are chronological. The destination below them is architectural. The "
            "arrow between the two sections is an explanation, not a dependency, and no phase "
            "ordering is encoded between them."),
    }


# ── mermaid ──────────────────────────────────────────────────────────────

def _mermaid_text(value):
    return (str(value or "")
            .replace('"', "'").replace("<", "‹").replace(">", "›")
            .replace("\n", " ").strip())


def build_overview_mermaid(areas, counts):
    """The small overview graph the card asks for: the five conceptual areas
    and how a reader moves between them. Deliberately NOT a repository tree and
    deliberately not the build or destination graph — both of those are drawn
    by the read models that own them, at their own zoom levels."""
    lines = ["flowchart LR"]
    labels = {
        "current_build": f"Current Build<br/>{counts.get('phases', 0)} steps",
        "queue_problems": (f"Queue / Problems<br/>{counts.get('problems', 0)} findings"
                           f"<br/>{counts.get('awaiting_triage', 0)} items awaiting triage"),
        "system_anatomy": (f"System Anatomy<br/>{counts.get('anatomy_areas', 0)} areas"
                           f"<br/>{counts.get('capabilities', 0)} capabilities"),
        "destination": f"Destination<br/>{counts.get('destination_nodes', 0)} nodes",
        "trajectory": "Trajectory<br/>today → destination",
    }
    for area in areas:
        if area["id"] == "overview":
            continue
        text = _mermaid_text(labels.get(area["id"], area["label"]))
        lines.append(f'  {area["id"].upper()}["{text}"]')
    lines += [
        "  QUEUE_PROBLEMS -->|what the work is for| CURRENT_BUILD",
        "  CURRENT_BUILD -->|what it builds| SYSTEM_ANATOMY",
        "  SYSTEM_ANATOMY -->|what it is for| TRAJECTORY",
        "  TRAJECTORY -.->|explains, does not sequence| DESTINATION",
        "  classDef area fill:#1f3350,stroke:#5b8fd6,color:#e8f0fb",
        "  classDef dest fill:#2a2340,stroke:#8a7bc8,color:#eee8fb,stroke-dasharray: 5 4",
        "  class CURRENT_BUILD,QUEUE_PROBLEMS,SYSTEM_ANATOMY,TRAJECTORY area",
        "  class DESTINATION dest",
    ]
    return "\n".join(lines)


def build_anatomy_mermaid(areas):
    """The functional-area tree the card specifies — major areas only, never
    the repository tree."""
    lines = ["flowchart TD", '  CIS["CIS"]']
    for area in areas:
        label = _mermaid_text(f"{area['label']}<br/>{area['status_plain']}")
        lines.append(f'  {area["id"].upper()}["{label}"]')
        lines.append(f'  CIS --> {area["id"].upper()}')
    for area in areas:
        cls = {"ACTIVE": "activeArea", "DORMANT": "dormantArea",
               "INCOMPLETE": "problemArea"}.get(area["status"], "unknownArea")
        lines.append(f'  class {area["id"].upper()} {cls}')
    lines += [
        "  classDef activeArea fill:#1f3d2b,stroke:#3f8f5f,color:#e6f3ea",
        "  classDef dormantArea fill:#23262c,stroke:#4a5058,color:#c7ccd4",
        "  classDef problemArea fill:#4a2630,stroke:#c9637a,color:#fbe9ee",
        "  classDef unknownArea fill:#3d3520,stroke:#b79a43,color:#f8f1dc",
    ]
    return "\n".join(lines)


def build_trajectory_mermaid(trajectory):
    """Today's steps in a row, then a DASHED arrow to the destination with the
    card's required wording on it."""
    lines = ["flowchart TD"]
    steps = trajectory.get("steps", [])
    for step in steps:
        label = _mermaid_text(f"{step['label']} — {step['description']}<br/>[{step['status_label']}]")
        lines.append(f'  {step["id"]}["{label}"]')
    for a, b in zip(steps, steps[1:]):
        lines.append(f'  {a["id"]} --> {b["id"]}')
    rel = trajectory.get("destination_relationship") or {}
    previous = steps[-1]["id"] if steps else None
    for node in rel.get("nodes", []):
        label = _mermaid_text(f"{node['label']}<br/>DESTINATION — not activated")
        lines.append(f'  D_{node["node_id"]}["{label}"]')
        if previous:
            lines.append(f'  {previous} -.->|{_mermaid_text(rel.get("warning"))}| '
                         f'D_{node["node_id"]}')
        previous = f'D_{node["node_id"]}'
    for step in steps:
        cls = {"complete": "donePhase", "active": "activePhase",
               "next": "nextPhase"}.get(step["status"], "pendingPhase")
        if step["status"] == "active" and step["blocked"]:
            cls = "blockedPhase"
        lines.append(f'  class {step["id"]} {cls}')
    for node in rel.get("nodes", []):
        lines.append(f'  class D_{node["node_id"]} destinationNode')
    lines += [
        "  classDef donePhase fill:#1f3d2b,stroke:#3f8f5f,color:#e6f3ea",
        "  classDef activePhase fill:#1f3350,stroke:#5b8fd6,color:#e8f0fb",
        "  classDef blockedPhase fill:#4a2630,stroke:#c9637a,color:#fbe9ee",
        "  classDef nextPhase fill:#3d3520,stroke:#b79a43,color:#f8f1dc",
        "  classDef pendingPhase fill:#23262c,stroke:#4a5058,color:#c7ccd4",
        "  classDef destinationNode fill:#2a2340,stroke:#8a7bc8,color:#eee8fb,"
        "stroke-dasharray: 5 4",
    ]
    return "\n".join(lines)


# ── the read model ───────────────────────────────────────────────────────

AUTHORITY = {
    "role": (
        "this is a COMPOSITION layer, not an authority. It reads existing authorities and "
        "existing read models, labels every relationship with how it is known, and writes "
        "nothing. It must not become a planning authority."
    ),
    "composes": [
        {"read_model": "cis_build_path", "module": "tools/state/build_path.py",
         "answers": "what are we building now",
         "note": "CALLED, never restated. No phase sequence exists in this module."},
        {"read_model": "cis_destination_architecture",
         "module": "tools/state/destination_architecture.py",
         "answers": "what is CIS ultimately being built to support",
         "note": ("CALLED, never restated. The WIASW nodes and edges are not duplicated here; "
                  "the graph below is the one that read model produced.")},
    ],
    "reads_directly": [
        {"source": "queue_items + queue_edges",
         "why": "the work-item authority (ADR-PIPE-006); inventory and distribution only"},
        {"source": "dev_continuity_events",
         "why": "the append-only discovery ledger; read through tools/development/discovery.py "
                "so 'resolved' and 'blocking' mean what the closeout gate means by them"},
        {"source": "tools/state/project_intelligence_vocabulary.json",
         "why": "reviewed static explanatory metadata — plain-language wording only, no status, "
                "no ordering, no classification"},
        {"source": "runtime/container_app.py",
         "why": "observed blueprint registration — the activation fact behind a capability's "
                "surface. No import graph is built and no code-import relationship is treated "
                "as an architectural relationship"},
    ],
    "never_reads": ["docs/UNIFIED_BUILD_LIST.md", "build_plan_nodes", "build_plan_dependencies",
                    "functional_spec"],
    "write_paths": "none — the spine is opened mode=ro and this module issues no DML",
    "llm_runtime_calls": ("none. No model client, HTTP client or gateway is imported, and no "
                          "explanatory text is generated at read time"),
    "status_separation": (
        "build-phase status, discovery disposition, queue need_status, capability activation and "
        "destination activation are five different vocabularies. They are carried separately and "
        "never collapsed into one status here."
    ),
}

READ_ONLY_BOUNDARY = [
    "no queue item is classified, scoped, renumbered, merged or re-titled",
    "no queue edge is created, inferred or implied",
    "no phase is advanced and no roadmap row is written",
    "no discovery is resolved and no continuity event is published",
    "no migration is applied and no schema is created",
    "no destination architecture is written anywhere",
]


def get_project_intelligence(db_path=None):
    generated_at = datetime.now(timezone.utc).isoformat()
    vocabulary, vocabulary_problem = load_vocabulary()
    registered, registration_problem = registered_blueprints()
    problems_found = [p for p in (vocabulary_problem, registration_problem) if p]

    # ── composed read models ──────────────────────────────────────────────
    # Each is called independently and each failure is contained: one area
    # going unavailable must not take the whole map down, and must not be
    # papered over with a substitute.
    build, build_error = None, None
    try:
        build = bp.get_build_path(db_path=db_path)
    except Exception as e:  # noqa: BLE001
        build_error = f"{type(e).__name__}: {e}"
        problems_found.append({"kind": "build_path_unavailable", "detail": build_error})

    destination, destination_error = None, None
    try:
        destination = da.get_destination_architecture(db_path=db_path)
    except Exception as e:  # noqa: BLE001
        destination_error = f"{type(e).__name__}: {e}"
        problems_found.append({"kind": "destination_unavailable", "detail": destination_error})

    conn = _connect(db_path)
    try:
        state_revision = cs.compute_state_revision(conn)

        current_task = ((build or {}).get("current") or {}).get("task")
        # The authority TEXT used for literal-match evidence. Taken from the
        # composed build model rather than re-queried, so there is one reading
        # of project_state on this screen.
        state_texts = []
        for key, block in (("next_action", (build or {}).get("next_action")),
                           ("current_direction", (build or {}).get("current_direction"))):
            if block and block.get("text"):
                state_texts.append((key, block["text"]))
        phase_evidence = ((build or {}).get("current") or {}).get("evidence") or {}
        if phase_evidence.get("value"):
            state_texts.append(("build_phase", phase_evidence["value"]))

        capabilities = build_capabilities(
            conn, vocabulary, registered, registration_problem,
            state_texts, (build or {}).get("phases", []))
        anatomy = build_anatomy(vocabulary, capabilities)
        problems, problems_note, stale_problem_ids = build_problems(
            conn, db_path, vocabulary, current_task, state_texts)
        queue = build_queue(conn, vocabulary, build)
    finally:
        conn.close()

    relationships = []
    relationships += link_problems_to_capabilities(problems, capabilities)
    relationships += attach_problem_build_position(problems, build, current_task)
    for capability in capabilities:
        for position in capability["build_position"]:
            relationships.append(_relationship(
                source=capability["id"], target=position["phase_id"],
                relationship="capability_named_by_phase",
                confidence_class=position["confidence_class"],
                authority_refs=position["authority_refs"],
                explanation=("The roadmap's own description of this phase names this "
                             "capability's declared term.")))
        if not capability["build_position"]:
            relationships.append(_relationship(
                source=capability["id"], target=None,
                relationship="capability_named_by_phase",
                confidence_class=NOT_LINKED, authority_refs=[],
                explanation=capability["build_position_note"]))
        relationships.append(_relationship(
            source=capability["id"], target=None,
            relationship="capability_supports_destination_node",
            confidence_class=NOT_LINKED, authority_refs=[],
            explanation=capability["destination_link"]["explanation"]))

    trajectory = build_trajectory(build, destination)
    rel = trajectory["destination_relationship"]
    for node in rel.get("nodes", []):
        relationships.append(_relationship(
            source="CURRENT_BUILD", target=node["node_id"],
            relationship="trajectory_explains",
            confidence_class=node["confidence_class"],
            authority_refs=node["authority_refs"],
            explanation=rel["warning"] + " " + node["explanation"]))

    if stale_problem_ids:
        problems_found.append({
            "kind": "stale_vocabulary_entries",
            "detail": ("the reviewed vocabulary carries plain-language text for findings that no "
                       f"longer appear in the ledger: {', '.join(stale_problem_ids)}. The text is "
                       "not shown; nothing is rendered for a finding that does not exist"),
        })
    if queue["stale_vocabulary_item_nums"]:
        problems_found.append({
            "kind": "stale_vocabulary_entries",
            "detail": ("the reviewed vocabulary carries plain-language text for queue items that "
                       f"are not in queue_items: {', '.join(queue['stale_vocabulary_item_nums'])}"),
        })
    for capability in capabilities:
        for missing in (f for f in capability["files"] if not f["exists"]):
            problems_found.append({
                "kind": "declared_file_absent",
                "detail": (f"{capability['label']} declares {missing['path']} as implementation, "
                           "but no such file exists; the capability is reported FILES_MISSING "
                           "rather than being quietly dropped"),
            })

    counts = {
        "phases": len((build or {}).get("phases", [])),
        "problems": len(problems),
        "blocking_problems": sum(1 for p in problems if p["display_status"] == "blocking"),
        "unresolved_problems": sum(1 for p in problems if not p["resolved"]),
        "queue_items": queue["total_items"],
        "awaiting_triage": queue["awaiting_triage"],
        "capabilities": len(capabilities),
        "capabilities_registered": sum(1 for c in capabilities if c["status"] == "REGISTERED"),
        "anatomy_areas": len(anatomy),
        "destination_nodes": len((destination or {}).get("nodes", [])),
        "relationships": len(relationships),
        "not_yet_linked": sum(1 for r in relationships
                              if r["confidence_class"] == NOT_LINKED),
        "problems_reported": len(problems_found),
    }

    areas = (vocabulary or {}).get("areas", [])

    return {
        "read_model": READ_MODEL_KIND,
        "generated_at": generated_at,
        "state_revision": state_revision,
        "authority": AUTHORITY,
        "read_only_boundary": READ_ONLY_BOUNDARY,
        "confidence_classes": CONFIDENCE_CLASSES,
        "modes": MODES,
        "missing_link_text": MISSING_LINK_TEXT,
        "missing_plain_language_text": MISSING_PLAIN_LANGUAGE_TEXT,
        "vocabulary_source": {
            "path": "tools/state/project_intelligence_vocabulary.json",
            "provenance_class": (vocabulary or {}).get("provenance_class"),
            "schema_version": (vocabulary or {}).get("schema_version"),
            "present": vocabulary is not None,
            "what_this_is": (vocabulary or {}).get("what_this_is"),
        },
        "glossary": (vocabulary or {}).get("glossary", []),
        "areas": areas,
        "counts": counts,
        # The two composed read models. `build_path` is the FULL payload the
        # Build Path screen renders, so the Project Map's Current Build area
        # can reuse that renderer instead of carrying a second one.
        "current_build": {
            "available": build is not None,
            "error": build_error,
            "read_model": (build or {}).get("read_model"),
            "build_path": build,
        },
        "destination": {
            "available": destination is not None,
            "error": destination_error,
            "read_model": (destination or {}).get("read_model"),
            "present": (destination or {}).get("present"),
            "architecture_scope": (destination or {}).get("architecture_scope"),
            "counts": (destination or {}).get("counts"),
            "activation_note": ((destination or {}).get("activation") or {}).get("note"),
            # A reference projection of the composed graph — node identity and
            # provenance only, for linking. The full architecture, its edges,
            # its relationship definitions and its diagrams stay with the read
            # model that owns them and are fetched from its own route.
            "nodes": [{
                "id": n["id"], "label": n["label"], "kind": n["kind"],
                "activation_state": n.get("activation_state"),
                "authority_ref": n.get("authority_ref"),
            } for n in (destination or {}).get("nodes", [])],
            "endpoint": "GET /api/workbench/destination-architecture",
            "note": ("the full destination architecture is served by its own route and rendered "
                     "by its own component; it is referenced here, never duplicated"),
        },
        "capability_model": {
            "provenance": CAPABILITY_PROVENANCE,
            "states": CAPABILITY_STATES,
            "capabilities": capabilities,
        },
        "anatomy": {
            "root": "CIS",
            "note": ("major functional areas only. This is deliberately not the repository tree, "
                     "and no file is described here unless a capability already names it."),
            "areas": anatomy,
            "files": (vocabulary or {}).get("files", []),
            "mermaid": build_anatomy_mermaid(anatomy),
        },
        "problems": {
            "note": problems_note,
            "statement": ("findings recorded during the work, from the append-only continuity "
                          "ledger. A finding's disposition is its own status system and is not a "
                          "build status."),
            "items": problems,
        },
        "queue": queue,
        "trajectory": {**trajectory, "mermaid": build_trajectory_mermaid(trajectory)},
        "relationships": relationships,
        "overview_mermaid": build_overview_mermaid(areas, counts),
        "problems_found": problems_found,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", action="store_true", help="print the counts block only")
    ap.add_argument("--db", default=os.environ.get("CIS_SPINE_PATH"),
                    help="spine database path (default: canonical_state.DB)")
    args = ap.parse_args()
    model = get_project_intelligence(db_path=args.db)
    if args.summary:
        print(json.dumps({"counts": model["counts"],
                          "problems_found": model["problems_found"]},
                         indent=2, default=str))
    else:
        print(json.dumps(model, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
