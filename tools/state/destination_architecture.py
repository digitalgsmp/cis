#!/usr/bin/env python3
"""destination_architecture.py — read-only read model for the Workbench
"Destination Architecture" view (WIASW destination-architecture card).

WHAT THIS IS. The answer to a DIFFERENT question than tools/state/build_path.py
answers, kept deliberately separate from it:

    build_path.py                this module
    ───────────────────────────  ──────────────────────────────────────────
    "what are we building now?"  "what is CIS ultimately being built to
                                  support?"
    P0 → Queue Triage → P1 …     WIASW → uses → CIS → controls → execution
    CHRONOLOGICAL sequencing     ARCHITECTURAL relationships
    project_state.pipeline_      project_decisions ADR-WIASW-* decision text
    roadmap + ADR-PIPE-001

These are two graphs, not one. A destination node is never a phase node, a
destination edge is never a build-order edge, and nothing here advances,
reads or reports the P0–P6 sequence. If you want the build sequence, call
build_path.py; this module does not know it exists.

AUTHORITY AND PROJECTION (the thing most likely to go wrong here).
- SEMANTIC AUTHORITY is the project_decisions rows whose id starts with
  ADR-WIASW- and whose status is not SUPERSEDED. They are discovered by that
  pattern at query time, so a later decision in the family extends the
  architecture with no code change here, and a superseded one drops out.
- The MACHINE-READABLE GRAPH is parsed out of those rows' own decision text
  at read time. It is a projection with no separate store: there is no
  destination-architecture table, no project_state row, and no second copy
  that could drift from the decision. Every node and edge carries an
  authority_ref naming the decision it came from and quoting its own
  declaration verbatim.
- NOTHING about the destination architecture is written to
  project_state.pipeline_roadmap, queue_items, queue_edges, build_plan_nodes
  or build_plan_dependencies. This module does not read those either.
- Read-only, always. The spine is opened mode=ro and no statement here
  mutates anything.

THE CLAUSE GRAMMAR, which lives in the decision text and is only parsed here:

    DESTINATION GRAPH NODES: ID [kind] "Label" = description; ID [kind] …
    DESTINATION GRAPH EDGES: SOURCE relationship TARGET; SOURCE rel TARGET; …
    DESTINATION GRAPH RELATIONSHIPS: name = what the relationship means; …
    ARCHITECTURE SCOPE: destination
    ACTIVATION: default STATE; NODE_ID = STATE; …
    ACTIVATION VOCABULARY: STATE = what the state means; …

Node ids and activation states are UPPER_SNAKE, relationship names are
lowercase, and a description carries no ';' or '"'. Clauses may appear in
any decision of the family and are merged; the module carries the grammar,
never the content. Relationship names are NOT whitelisted here either — the
accepted set is whatever the RELATIONSHIPS clause defines, and an edge using
an undefined relationship is reported as a problem rather than silently
accepted or silently dropped.

HONEST ABOUT ABSENCE AND DISAGREEMENT. No ADR-WIASW-* row -> present:false
with a note, and no invented graph. A node declared twice, an edge pointing
at an undeclared node, an activation state outside the declared vocabulary,
a missing clause — each is reported in `problems` and the affected element
is kept visible rather than quietly dropped.

ACTIVATION IS NOT PROGRESS. Every node carries an activation_state from the
authority's own vocabulary. It is not a build status and it does not reuse
ADR-PIPE-005's component-state vocabulary or any phase status: its only job
is to say that this is recorded destination architecture and not activated
implementation work, and to point at the authority that does own a node's
real status when one exists.

Usage:
    python3 tools/state/destination_architecture.py             # full model
    python3 tools/state/destination_architecture.py --mermaid   # diagram only
    python3 tools/state/destination_architecture.py --level overview
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

import canonical_state as cs  # noqa: E402  (shared DB default + state revision)

READ_MODEL_KIND = "cis_destination_architecture"

# The decision family that carries the architecture. A PATTERN, not a list of
# ids. ADR-WIASW-004 (continuous development intake and build-order
# integration) joined the family on 2026-10-04 and required no change here,
# not even to the clause grammar — which is the property this pattern exists
# to have.
DECISION_ID_PATTERN = "ADR-WIASW-%"
DECISION_ID_DESCRIPTION = (
    "project_decisions rows with id LIKE 'ADR-WIASW-%' and status != 'SUPERSEDED', "
    "ordered by id"
)

# Clause headers of the grammar. The one list of content-free structure this
# module holds; everything inside a clause comes from the decision text.
CLAUSE_NODES = "DESTINATION GRAPH NODES"
CLAUSE_EDGES = "DESTINATION GRAPH EDGES"
CLAUSE_RELATIONSHIPS = "DESTINATION GRAPH RELATIONSHIPS"
CLAUSE_SCOPE = "ARCHITECTURE SCOPE"
CLAUSE_ACTIVATION = "ACTIVATION"
CLAUSE_VOCABULARY = "ACTIVATION VOCABULARY"

# Longest-first so "ACTIVATION VOCABULARY:" is never matched as "ACTIVATION:".
CLAUSE_HEADERS = (
    CLAUSE_RELATIONSHIPS, CLAUSE_NODES, CLAUSE_EDGES, CLAUSE_VOCABULARY,
    CLAUSE_SCOPE, CLAUSE_ACTIVATION,
)
_HEADER_RE = re.compile(
    "(" + "|".join(re.escape(h) for h in
                   sorted(CLAUSE_HEADERS, key=len, reverse=True)) + r")\s*:")

# ID [kind] "Label" = description   (description runs to the next ';' or clause end)
_NODE_RE = re.compile(
    r"([A-Z][A-Z0-9_]*)\s*\[\s*([a-z][a-z0-9_]*)\s*\]\s*\"([^\"]*)\"\s*=\s*([^;]*)")
# SOURCE relationship TARGET
_EDGE_RE = re.compile(r"([A-Z][A-Z0-9_]*)\s+([a-z][a-z-]*)\s+([A-Z][A-Z0-9_]*)")
# name = meaning
_DEFINITION_RE = re.compile(r"([a-z][a-z-]*)\s*=\s*([^;]*)")
# default STATE
_ACTIVATION_DEFAULT_RE = re.compile(r"\bdefault\s+([A-Z][A-Z0-9_]*)")
# NODE_ID = STATE
_ACTIVATION_EXCEPTION_RE = re.compile(r"([A-Z][A-Z0-9_]*)\s*=\s*([A-Z][A-Z0-9_]*)")
# STATE = meaning
_VOCABULARY_RE = re.compile(r"([A-Z][A-Z0-9_]*)\s*=\s*([^;]*)")

# The hierarchy relationship. Named here because DEPTH is a presentation
# concern (which zoom level a node appears at), computed per request and never
# persisted — the authority states membership, not levels.
CONTAINS = "contains"

# Zoom levels, as the card's own framing: level 1 answers "why", level 2
# answers what the destination actually holds. Levels 3 and 4 — the P0–P6
# sequence and the queue items under it — are a different authority and a
# different screen; see authority.current_build_view.
#
# Level 2's wording said "what WIASW is" while the family carried only WIASW,
# CIS and the execution layer. ADR-WIASW-004 added a CIS capability
# (continuous development intake), so that wording would now describe less than
# the level shows. The label states the level's SCOPE, never its contents:
# a later family decision must not require an edit here.
LEVELS = (
    {
        "id": "overview",
        "label": "Level 1 — why",
        "question": "What is CIS ultimately being built to support?",
        "max_depth": 0,
    },
    {
        "id": "full",
        "label": "Level 2 — what the destination holds",
        "question": ("What are the WIASW domains and applications, the execution "
                     "backends, and the CIS capabilities the destination requires?"),
        "max_depth": None,
    },
)


# ── low-level reads ──────────────────────────────────────────────────────

def _connect(db_path=None):
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def family_decisions(conn):
    """The architecture's semantic authority, discovered by id pattern."""
    rows = conn.execute(
        "SELECT id, label, decision, reason, status, decided_at, superseded_by "
        "FROM project_decisions WHERE id LIKE ? AND status != 'SUPERSEDED' "
        "ORDER BY id",
        (DECISION_ID_PATTERN,),
    ).fetchall()
    return [dict(r) for r in rows]


# ── clause parsing ───────────────────────────────────────────────────────

def parse_clauses(text):
    """Split one decision's text into {header: [segment, ...]}.

    A segment runs from its header to the next header or the end of the text.
    A header appearing twice yields two segments rather than one of them
    winning silently."""
    out = {}
    if not text:
        return out
    matches = list(_HEADER_RE.finditer(text))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        segment = text[match.end():end].strip()
        out.setdefault(match.group(1), []).append(segment)
    return out


def _quote(text, limit=600):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _fragments(segment):
    """A clause's ';'-separated declarations. Split rather than scanned so a
    declaration that does not parse can be REPORTED: a malformed node or edge
    that simply failed to match would otherwise disappear from the architecture
    silently, which is the one thing a read model over authority must not do."""
    return [f for f in (part.strip(" .") for part in (segment or "").split(";")) if f]


def parse_nodes(segment):
    """([{id, kind, label, description, declaration}], unparsed[]) from a
    NODES segment."""
    nodes, unparsed = [], []
    for fragment in _fragments(segment):
        found = list(_NODE_RE.finditer(fragment))
        if not found:
            unparsed.append(fragment)
            continue
        for match in found:
            nodes.append({
                "id": match.group(1),
                "kind": match.group(2),
                "label": " ".join(match.group(3).split()),
                "description": " ".join(match.group(4).split()).rstrip(" ."),
                "declaration": " ".join(match.group(0).split()),
            })
    return nodes, unparsed


def parse_edges(segment):
    """([{source, relationship, target, declaration}], unparsed[]) from an
    EDGES segment."""
    edges, unparsed = [], []
    for fragment in _fragments(segment):
        found = list(_EDGE_RE.finditer(fragment))
        if not found:
            unparsed.append(fragment)
            continue
        for match in found:
            edges.append({
                "source": match.group(1),
                "relationship": match.group(2),
                "target": match.group(3),
                "declaration": " ".join(match.group(0).split()),
            })
    return edges, unparsed


def parse_definitions(segment, pattern):
    out = []
    for match in pattern.finditer(segment or ""):
        out.append((match.group(1), " ".join(match.group(2).split()).rstrip(" .")))
    return out


# ── graph assembly ───────────────────────────────────────────────────────

def _ref(decision_id, clause, declaration):
    return {"decision_id": decision_id, "clause": clause, "declaration": declaration}


def _contains_depth(nodes, edges, problems):
    """Depth in the `contains` hierarchy: 0 for a node nothing contains, else
    one more than its container. Purely for zoom levels. A cycle (which the
    authority should not contain) is reported and left at its first depth."""
    parents = {}
    for edge in edges:
        if edge["relationship"] != CONTAINS:
            continue
        if edge["target"] in parents and parents[edge["target"]] != edge["source"]:
            problems.append({
                "kind": "multiple_containers",
                "detail": (f"{edge['target']} is contained by both "
                           f"{parents[edge['target']]} and {edge['source']}; "
                           "the first is used for zoom depth"),
            })
            continue
        parents[edge["target"]] = edge["source"]

    depths = {}
    for node_id in nodes:
        seen, current, depth = set(), node_id, 0
        while current in parents:
            if current in seen:
                problems.append({
                    "kind": "contains_cycle",
                    "detail": f"a contains cycle reaches {node_id}; depth left at {depth}",
                })
                break
            seen.add(current)
            current = parents[current]
            depth += 1
        depths[node_id] = depth
    return depths


def build_graph(decisions):
    """Merge every family decision's clauses into one graph.

    Returns (nodes, edges, meta, problems). `meta` carries the activation
    rule, the relationship vocabulary, the architecture scope and, per
    decision, which clauses it actually contributed."""
    problems = []
    nodes, node_order = {}, []
    edges = []
    relationships = {}
    vocabulary = {}
    activation_default, activation_default_ref = None, None
    activation_exceptions = {}
    scope, scope_ref = None, None
    contributed = {}

    for decision in decisions:
        did = decision["id"]
        clauses = parse_clauses(decision["decision"])
        contributed[did] = sorted(clauses)

        for segment in clauses.get(CLAUSE_NODES, []):
            parsed, unparsed = parse_nodes(segment)
            if not parsed:
                problems.append({
                    "kind": "unparsable_nodes_clause",
                    "detail": (f"{did} carries a {CLAUSE_NODES} clause from which no "
                               f"node declaration could be parsed: {_quote(segment, 160)}"),
                })
            for fragment in unparsed:
                problems.append({
                    "kind": "unparsable_node_declaration",
                    "detail": (f"{did}'s {CLAUSE_NODES} clause carries a declaration that "
                               "is not 'ID [kind] \"Label\" = description', so no node was "
                               f"read from it: {_quote(fragment, 200)}"),
                })
            for node in parsed:
                if node["id"] in nodes:
                    problems.append({
                        "kind": "duplicate_node",
                        "detail": (f"{node['id']} is declared by both "
                                   f"{nodes[node['id']]['authority_ref']['decision_id']} "
                                   f"and {did}; the first declaration is shown"),
                    })
                    continue
                nodes[node["id"]] = {
                    "id": node["id"],
                    "label": node["label"],
                    "kind": node["kind"],
                    "description": node["description"],
                    "authority_ref": _ref(did, CLAUSE_NODES, node["declaration"]),
                }
                node_order.append(node["id"])

        for segment in clauses.get(CLAUSE_EDGES, []):
            parsed, unparsed = parse_edges(segment)
            if not parsed:
                problems.append({
                    "kind": "unparsable_edges_clause",
                    "detail": (f"{did} carries a {CLAUSE_EDGES} clause from which no "
                               f"edge could be parsed: {_quote(segment, 160)}"),
                })
            for fragment in unparsed:
                problems.append({
                    "kind": "unparsable_edge_declaration",
                    "detail": (f"{did}'s {CLAUSE_EDGES} clause carries a declaration that "
                               "is not 'SOURCE relationship TARGET' with an UPPER_SNAKE "
                               "source and target and a lowercase relationship, so no edge "
                               f"was read from it: {_quote(fragment, 200)}"),
                })
            for edge in parsed:
                edges.append({
                    "source": edge["source"],
                    "target": edge["target"],
                    "relationship": edge["relationship"],
                    "authority_ref": _ref(did, CLAUSE_EDGES, edge["declaration"]),
                })

        for segment in clauses.get(CLAUSE_RELATIONSHIPS, []):
            for name, definition in parse_definitions(segment, _DEFINITION_RE):
                if name in relationships and relationships[name]["definition"] != definition:
                    problems.append({
                        "kind": "conflicting_relationship_definition",
                        "detail": (f"relationship '{name}' is defined differently by "
                                   f"{relationships[name]['authority_ref']['decision_id']} "
                                   f"and {did}; the first is shown"),
                    })
                    continue
                relationships[name] = {
                    "name": name,
                    "definition": definition,
                    "authority_ref": _ref(did, CLAUSE_RELATIONSHIPS, f"{name} = {definition}"),
                }

        for segment in clauses.get(CLAUSE_VOCABULARY, []):
            for state, definition in parse_definitions(segment, _VOCABULARY_RE):
                vocabulary.setdefault(state, {
                    "state": state,
                    "definition": definition,
                    "authority_ref": _ref(did, CLAUSE_VOCABULARY, f"{state} = {definition}"),
                })

        for segment in clauses.get(CLAUSE_ACTIVATION, []):
            default = _ACTIVATION_DEFAULT_RE.search(segment)
            if default:
                if activation_default and activation_default != default.group(1):
                    problems.append({
                        "kind": "conflicting_activation_default",
                        "detail": (f"{activation_default_ref['decision_id']} and {did} "
                                   "declare different activation defaults; the first is used"),
                    })
                elif not activation_default:
                    activation_default = default.group(1)
                    activation_default_ref = _ref(did, CLAUSE_ACTIVATION,
                                                  f"default {default.group(1)}")
            for node_id, state in _ACTIVATION_EXCEPTION_RE.findall(segment):
                activation_exceptions.setdefault(node_id, {
                    "state": state,
                    "authority_ref": _ref(did, CLAUSE_ACTIVATION, f"{node_id} = {state}"),
                })

        for segment in clauses.get(CLAUSE_SCOPE, []):
            value = " ".join(segment.split()).rstrip(" .").lower()
            if scope is None:
                scope, scope_ref = value, _ref(did, CLAUSE_SCOPE, segment.strip())
            elif value != scope:
                problems.append({
                    "kind": "conflicting_architecture_scope",
                    "detail": (f"{scope_ref['decision_id']} says scope '{scope}' and {did} "
                               f"says '{value}'; the first is used"),
                })

    # Activation per node, from the authority's default plus its exceptions.
    if activation_default is None:
        problems.append({
            "kind": "no_activation_default",
            "detail": (f"no {CLAUSE_ACTIVATION} clause in the family declares "
                       "'default <STATE>'; node activation is reported as unknown"),
        })
    for node_id in node_order:
        exception = activation_exceptions.get(node_id)
        state = exception["state"] if exception else activation_default
        nodes[node_id]["activation_state"] = state
        nodes[node_id]["activation_authority_ref"] = (
            exception["authority_ref"] if exception else activation_default_ref)
        if state is not None and vocabulary and state not in vocabulary:
            problems.append({
                "kind": "activation_state_outside_vocabulary",
                "detail": (f"{node_id} carries activation state '{state}', which the "
                           f"{CLAUSE_VOCABULARY} clause does not define"),
            })
    for node_id in activation_exceptions:
        if node_id not in nodes:
            problems.append({
                "kind": "activation_for_undeclared_node",
                "detail": (f"an {CLAUSE_ACTIVATION} clause names {node_id}, which no "
                           f"{CLAUSE_NODES} clause declares"),
            })

    # Edge integrity. A dangling or undefined-relationship edge stays visible.
    for edge in edges:
        edge["source_declared"] = edge["source"] in nodes
        edge["target_declared"] = edge["target"] in nodes
        edge["relationship_defined"] = edge["relationship"] in relationships
        if not edge["source_declared"] or not edge["target_declared"]:
            missing = [n for n in (edge["source"], edge["target"]) if n not in nodes]
            problems.append({
                "kind": "edge_names_undeclared_node",
                "detail": (f"edge '{edge['authority_ref']['declaration']}' names "
                           f"{', '.join(missing)}, which no {CLAUSE_NODES} clause declares"),
            })
        if not edge["relationship_defined"]:
            problems.append({
                "kind": "undefined_relationship",
                "detail": (f"edge '{edge['authority_ref']['declaration']}' uses "
                           f"relationship '{edge['relationship']}', which the "
                           f"{CLAUSE_RELATIONSHIPS} clause does not define"),
            })

    depths = _contains_depth(node_order, edges, problems)
    for node_id in node_order:
        nodes[node_id]["depth"] = depths[node_id]

    meta = {
        "architecture_scope": scope,
        "architecture_scope_authority_ref": scope_ref,
        "activation": {
            "default": activation_default,
            "default_authority_ref": activation_default_ref,
            "exceptions": activation_exceptions,
            "vocabulary": list(vocabulary.values()),
            "note": (
                "activation_state is NOT a build status and NOT ADR-PIPE-005's "
                "component-state vocabulary. It says whether this is recorded "
                "destination architecture or a node whose real status belongs to "
                "another authority. No progress through the P0–P6 build sequence is "
                "shown, implied or inferred on this screen."
            ),
        },
        "relationships": list(relationships.values()),
        "clauses_contributed": contributed,
    }
    return [nodes[n] for n in node_order], edges, meta, problems


# ── mermaid ──────────────────────────────────────────────────────────────

def _mermaid_text(value):
    """Mermaid node labels are quoted strings; quotes and angle brackets
    inside them break the parse, so they are replaced rather than escaped."""
    return (str(value or "")
            .replace('"', "'").replace("<", "‹").replace(">", "›")
            .replace("\n", " ").strip())


# Classes by ACTIVATION, not by kind: the one thing the diagram must make
# unmistakable is that this is destination architecture and not activated
# implementation work (and which nodes' real status lives elsewhere).
_ACTIVATION_CLASS = {
    "NOT_ACTIVATED": "destinationNode",
    "TRACKED_ELSEWHERE": "elsewhereNode",
}
_UNKNOWN_ACTIVATION_CLASS = "unknownNode"


def build_mermaid(nodes, edges, max_depth=None):
    """Generated from the same nodes/edges the panel renders, so the diagram
    and the lists beside it cannot disagree. `max_depth` draws one zoom level."""
    shown = [n for n in nodes
             if max_depth is None or n.get("depth", 0) <= max_depth]
    ids = {n["id"] for n in shown}
    lines = ["flowchart TD"]
    for node in shown:
        state = node.get("activation_state")
        parts = [node["label"], node["kind"].replace("_", " ")]
        parts.append("DESTINATION — not activated" if state == "NOT_ACTIVATED"
                     else f"DESTINATION — {state.replace('_', ' ').lower()}" if state
                     else "DESTINATION — activation unknown")
        label = "<br/>".join(_mermaid_text(p) for p in parts)
        lines.append(f'  {node["id"]}["{label}"]')
    for edge in edges:
        if edge["source"] not in ids or edge["target"] not in ids:
            continue
        lines.append(f'  {edge["source"]} -->|{_mermaid_text(edge["relationship"])}| '
                     f'{edge["target"]}')
    for node in shown:
        cls = _ACTIVATION_CLASS.get(node.get("activation_state"),
                                    _UNKNOWN_ACTIVATION_CLASS)
        lines.append(f'  class {node["id"]} {cls}')
    lines += [
        "  classDef destinationNode fill:#2a2340,stroke:#8a7bc8,color:#eee8fb,"
        "stroke-dasharray: 5 4",
        "  classDef elsewhereNode fill:#23262c,stroke:#4a5058,color:#c7ccd4",
        "  classDef unknownNode fill:#4a2630,stroke:#c9637a,color:#fbe9ee",
    ]
    return "\n".join(lines)


# ── the read model ───────────────────────────────────────────────────────

AUTHORITY = {
    "semantic_authority": DECISION_ID_DESCRIPTION,
    "semantic_authority_table": "project_decisions",
    "structured_projection": (
        "the nodes/edges below are PARSED from those decision rows' own text at "
        "read time by tools/state/destination_architecture.py. There is no "
        "destination-architecture table, no project_state row and no second store: "
        "the projection cannot drift from the authority because it is not stored"
    ),
    "provenance": (
        "every node and edge carries an authority_ref naming the decision id, the "
        "clause it came from, and its own declaration quoted verbatim"
    ),
    "not_stored_in": [
        "project_state.pipeline_roadmap", "queue_items", "queue_edges",
        "build_plan_nodes", "build_plan_dependencies",
    ],
    "current_build_view": (
        "this read model answers 'what is CIS ultimately being built to support'. "
        "'What are we building now' is a different question with a different "
        "authority — project_state.pipeline_roadmap + ADR-PIPE-001, read by "
        "tools/state/build_path.py — and is neither read nor restated here"
    ),
    "relationship_separation": (
        "destination relationships (contains, uses, supports, controls, "
        "orchestrates, executes-through) are ARCHITECTURAL. Build-order "
        "relationships (builds-before, next, phase-order) belong to the roadmap "
        "authority. The two are not interchangeable, and no destination node is a "
        "phase or queue node"
    ),
}


def get_destination_architecture(db_path=None):
    conn = _connect(db_path)
    try:
        decisions = family_decisions(conn)
        state_revision = cs.compute_state_revision(conn)
    finally:
        conn.close()

    base = {
        "read_model": READ_MODEL_KIND,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_revision": state_revision,
        "authority": AUTHORITY,
    }

    if not decisions:
        base.update({
            "present": False,
            "note": (
                "no project_decisions row matches "
                f"id LIKE '{DECISION_ID_PATTERN}' with status != 'SUPERSEDED', so no "
                "destination architecture is recorded. Nothing is shown rather than "
                "assumed: this read model has no built-in copy of the architecture"
            ),
            "decisions": [], "nodes": [], "edges": [], "levels": [],
            "problems": [], "mermaid": None,
        })
        return base

    nodes, edges, meta, problems = build_graph(decisions)

    levels = []
    for level in LEVELS:
        shown = [n["id"] for n in nodes
                 if level["max_depth"] is None or n["depth"] <= level["max_depth"]]
        levels.append({
            **level,
            "node_ids": shown,
            "node_count": len(shown),
            "mermaid": build_mermaid(nodes, edges, level["max_depth"]),
        })

    kinds = []
    for node in nodes:
        if node["kind"] not in kinds:
            kinds.append(node["kind"])

    base.update({
        "present": True,
        "architecture_scope": meta["architecture_scope"],
        "architecture_scope_authority_ref": meta["architecture_scope_authority_ref"],
        "activation": meta["activation"],
        "relationships": meta["relationships"],
        "relationship_types_used": sorted({e["relationship"] for e in edges}),
        "node_kinds": kinds,
        "nodes": nodes,
        "edges": edges,
        "levels": levels,
        "mermaid": build_mermaid(nodes, edges),
        "decisions": [{
            "id": d["id"],
            "label": d["label"],
            "status": d["status"],
            "decided_at": d["decided_at"],
            "superseded_by": d["superseded_by"],
            "clauses_contributed": meta["clauses_contributed"].get(d["id"], []),
            "decision": d["decision"],
            "reason": d["reason"],
        } for d in decisions],
        "counts": {
            "decisions": len(decisions),
            "nodes": len(nodes),
            "edges": len(edges),
            "relationship_types": len({e["relationship"] for e in edges}),
            "problems": len(problems),
        },
        "problems": problems,
    })
    return base


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mermaid", action="store_true",
                    help="print only the Mermaid diagram source")
    ap.add_argument("--level", choices=[level["id"] for level in LEVELS],
                    help="with --mermaid, print one zoom level's diagram")
    ap.add_argument("--db", default=os.environ.get("CIS_SPINE_PATH"),
                    help="spine database path (default: canonical_state.DB)")
    args = ap.parse_args()
    model = get_destination_architecture(db_path=args.db)
    if args.mermaid:
        source = model.get("mermaid")
        if args.level:
            source = next((lv["mermaid"] for lv in model.get("levels", [])
                           if lv["id"] == args.level), None)
        if source is None:
            print(model.get("note") or "no diagram source", file=sys.stderr)
            return 1
        print(source)
    else:
        print(json.dumps(model, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
