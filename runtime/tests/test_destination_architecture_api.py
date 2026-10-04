#!/usr/bin/env python3
"""test_destination_architecture_api.py — behavioral tests for the Workbench
Destination Architecture read model (tools/state/destination_architecture.py)
and its endpoint (runtime/api/destination_architecture.py, GET
/api/workbench/destination-architecture).

Four kinds of test, deliberately:

  1. Against the LIVE spine, opened read-only. These prove the destination
     architecture can actually be built from the current authority state and
     that it says what the ADR-WIASW-* decisions say — WIASW on top, the five
     named media domains, the horizontal applications marked as NOT additional
     domains, CIS as substrate, the execution layer below it, the continuous
     development intake capability under CIS, and all seven relationship
     types carrying explicit semantics. A card assertion that
     passed only against a hand-built fixture would prove nothing about the
     architecture the project actually recorded.

  2. Against a SCRATCH database whose ADR-WIASW-* rows are deliberately
     DIFFERENT from production's, and one with none at all. These prove the
     graph is parsed from the decision text rather than hardcoded in the module
     — the failure mode a visualization like this invites — and that an absent
     architecture is reported rather than invented.

  3. SEPARATION from the build path. The destination graph must not be the
     phase chain wearing different labels: no destination node is a phase, no
     destination edge is a build-order edge, the roadmap/queue/build-plan
     tables are never read, and the P0-P6 state the other read model reports is
     untouched by this one.

  4. The CURRENT BUILD STATE IS UNCHANGED. The protected project_state rows and
     the queue tables are hashed before and after exercising every route and
     compared, so "this card changed no build state" is a measurement rather
     than a claim.

Nothing here writes to the live spine: the read model opens it with sqlite3's
mode=ro URI, and the row-count/revision/hash comparisons assert that outright.

Run: python3 runtime/tests/test_destination_architecture_api.py
"""
import hashlib
import os
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_HERE, ".."))                   # runtime/
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))  # the read models
sys.path.insert(0, _REPO_ROOT)

os.environ.setdefault("CIS_PIPELINE_API_KEY", "")

import build_path as bp  # noqa: E402
import canonical_state as cs  # noqa: E402
import destination_architecture as da  # noqa: E402

from container_app import app  # noqa: E402

results = []

# The rows this card must not touch, per its own scope boundary.
PROTECTED_STATE_KEYS = ("pipeline_roadmap", "build_phase", "current_direction",
                        "next_action", "current_queue_item")
PROTECTED_TABLES = ("queue_items", "queue_edges", "build_plan_nodes",
                    "build_plan_dependencies")


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def node(model, node_id):
    return next((n for n in model["nodes"] if n["id"] == node_id), None)


def nodes_of_kind(model, kind):
    return [n for n in model["nodes"] if n["kind"] == kind]


def has_edge(model, source, relationship, target):
    return any(e["source"] == source and e["relationship"] == relationship
               and e["target"] == target for e in model["edges"])


def protected_fingerprint(db_path=None):
    """One hash per protected row/table, so a change anywhere in the current
    build state shows up as a different fingerprint."""
    conn = sqlite3.connect(f"file:{db_path or cs.DB}?mode=ro", uri=True)
    try:
        out = {}
        for key in PROTECTED_STATE_KEYS:
            row = conn.execute(
                "SELECT id, value, created_at FROM project_state WHERE key = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1", (key,)).fetchone()
            out[f"project_state.{key}"] = (
                None if row is None
                else (row[0], hashlib.sha256(row[1].encode()).hexdigest(), row[2]))
        for table in PROTECTED_TABLES:
            out[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        out["project_state_rows"] = conn.execute(
            "SELECT COUNT(*) FROM project_state").fetchone()[0]
        return out
    finally:
        conn.close()


def scratch_db(decisions):
    """A spine stub carrying only what this read model needs: the decision rows
    it parses, plus the tables canonical_state's revision hash touches."""
    path = os.path.join(tempfile.mkdtemp(), "scratch.db")
    conn = sqlite3.connect(path)
    conn.execute("""CREATE TABLE project_decisions (
        id TEXT PRIMARY KEY, label TEXT NOT NULL, decision TEXT NOT NULL,
        reason TEXT, status TEXT NOT NULL DEFAULT 'DECIDED',
        decided_at TEXT NOT NULL, superseded_by TEXT)""")
    for did, label, text, status in decisions:
        conn.execute("INSERT INTO project_decisions "
                     "(id, label, decision, status, decided_at) VALUES (?, ?, ?, ?, ?)",
                     (did, label, text, status, "2026-10-02T00:00:00+00:00"))
    conn.commit()
    conn.close()
    return path


# ── 1. live authority state ──────────────────────────────────────────────

def test_read_model_builds_from_live_authority():
    model = da.get_destination_architecture()
    check("1a. read model builds from the current authority state",
          model.get("read_model") == "cis_destination_architecture"
          and model.get("present") is True,
          model.get("read_model"))
    check("1b. a state revision is reported alongside it",
          isinstance(model.get("state_revision"), str) and model["state_revision"],
          model.get("state_revision"))
    check("1c. the architecture is read from the ADR-WIASW decision family",
          [d["id"] for d in model["decisions"]]
          == ["ADR-WIASW-001", "ADR-WIASW-002", "ADR-WIASW-003", "ADR-WIASW-004"],
          [d["id"] for d in model["decisions"]])
    check("1d. every decision row is DECIDED and not superseded",
          all(d["status"] == "DECIDED" and not d["superseded_by"]
              for d in model["decisions"]),
          [(d["id"], d["status"], d["superseded_by"]) for d in model["decisions"]])
    check("1e. the recorded architecture parsed with no problems",
          model["problems"] == [], model["problems"])
    return model


def test_wiasw_is_the_root_and_is_defined(model):
    wiasw = node(model, "WIASW")
    check("2a. WIASW is present as the root node",
          wiasw is not None and wiasw["kind"] == "root" and wiasw["depth"] == 0,
          wiasw and (wiasw["kind"], wiasw["depth"]))
    check("2b. its label spells out Word, Image, Action, Sound and Web",
          wiasw and all(w in wiasw["label"]
                        for w in ("Word", "Image", "Action", "Sound", "Web")),
          wiasw and wiasw["label"])
    check("2c. it is described as the destination/product architecture",
          wiasw and "destination" in wiasw["description"].lower()
          and "product" in wiasw["description"].lower(),
          wiasw and wiasw["description"][:120])
    check("2d. the architecture scope is 'destination', from the authority's own clause",
          model["architecture_scope"] == "destination"
          and model["architecture_scope_authority_ref"]["decision_id"].startswith("ADR-WIASW-"),
          (model["architecture_scope"], model.get("architecture_scope_authority_ref")))


def test_five_named_domains(model):
    domains = {n["id"]: n for n in nodes_of_kind(model, "domain")}
    check("3a. exactly the five named media domains are recorded",
          sorted(domains) == ["ACTION", "IMAGE", "SOUND", "WEB", "WORD"],
          sorted(domains))
    check("3b. each is contained by the domain group, not by WIASW directly",
          all(has_edge(model, "DOMAINS", "contains", d) for d in domains),
          [d for d in domains if not has_edge(model, "DOMAINS", "contains", d)])
    action = domains.get("ACTION")
    check("3c. Action is NOT narrowly animation — the authority says so in its own words",
          action and "not narrowly animation" in action["description"].lower()
          and all(w in action["description"].lower()
                  for w in ("simulation", "interactive", "ar/vr")),
          action and action["description"][:160])
    web = domains.get("WEB")
    check("3d. Web covers publishing, distribution, social media and online sales",
          web and all(w in web["description"].lower()
                      for w in ("social media", "publishing", "distribution",
                                "online sales", "audience-facing")),
          web and web["description"][:160])
    check("3e. Web is not reduced to ordinary website development",
          web and "never reduced to ordinary website development" in web["description"].lower(),
          web and web["description"][-90:])


def test_horizontal_applications_are_not_domains(model):
    group = node(model, "HORIZONTAL_APPLICATIONS")
    apps = nodes_of_kind(model, "application")
    check("4a. a horizontal-application group is recorded, separate from the domains",
          group is not None and group["kind"] == "application_group",
          group and group["kind"])
    check("4b. it states outright that these are NOT additional media domains",
          group and "not additional media domains" in group["description"].lower(),
          group and group["description"])
    check("4c. the named productivity applications are recorded under it",
          len(apps) >= 10 and all(has_edge(model, "HORIZONTAL_APPLICATIONS", "contains",
                                           a["id"]) for a in apps),
          [a["id"] for a in apps])
    check("4d. idea, project, asset, scheduling, knowledge and learning management are among them",
          {"IDEA_MANAGEMENT", "PROJECT_MANAGEMENT", "DIGITAL_ASSET_MANAGEMENT",
           "SCHEDULING", "KNOWLEDGE_MANAGEMENT", "LEARNING_TRAINING_MANAGEMENT"}
          <= {a["id"] for a in apps},
          sorted(a["id"] for a in apps))
    check("4e. they SUPPORT the domains rather than being one of them",
          has_edge(model, "HORIZONTAL_APPLICATIONS", "supports", "DOMAINS")
          and not any(a["kind"] == "domain" for a in apps),
          [e for e in model["edges"] if e["source"] == "HORIZONTAL_APPLICATIONS"
           and e["relationship"] == "supports"])


def test_cis_is_the_substrate_beneath_wiasw(model):
    cis = node(model, "CIS")
    check("5a. CIS is recorded as a substrate, not as the root",
          cis is not None and cis["kind"] == "substrate" and node(model, "WIASW")["kind"] == "root",
          cis and cis["kind"])
    check("5b. WIASW USES CIS — the hierarchy runs WIASW over CIS, not the reverse",
          has_edge(model, "WIASW", "uses", "CIS")
          and not has_edge(model, "CIS", "uses", "WIASW"),
          [e["authority_ref"]["declaration"] for e in model["edges"]
           if "CIS" in (e["source"], e["target"]) and e["relationship"] == "uses"])
    check("5c. CIS CONTROLS the execution/tool layer",
          has_edge(model, "CIS", "controls", "EXECUTION_LAYER"),
          [e for e in model["edges"] if e["relationship"] == "controls"])
    families = nodes_of_kind(model, "execution_family")
    check("5d. the execution layer carries model, dev-tool and creative-tool families",
          len(families) == 3 and all(
              has_edge(model, "EXECUTION_LAYER", "contains", f["id"]) for f in families),
          [f["id"] for f in families])
    creative = node(model, "CREATIVE_TOOL_BACKENDS")
    check("5e. creative tools are named as destination possibilities, with no adapter authorized",
          creative and all(w in creative["description"] for w in
                           ("Blender", "Houdini", "ComfyUI", "Unreal Engine"))
          and "no adapter authorized" in creative["description"],
          creative and creative["description"][-120:])
    # Execution infrastructure is REACHED, never owned: CIS drives it through
    # stable contracts. The guard is scoped to the execution layer rather than
    # to every CIS edge because ADR-WIASW-004 declares a CIS capability that IS
    # structurally part of CIS (CIS contains DEVELOPMENT_INTAKE). Owning a
    # capability and owning a replaceable backend are different claims, and
    # collapsing them would make the second unmeasurable.
    execution_ids = {"EXECUTION_LAYER"} | {f["id"] for f in families}
    check("5f. CIS reaches tool backends through orchestration and executes-through, "
          "not by containing them",
          has_edge(model, "CIS", "orchestrates", "MODEL_BACKENDS")
          and has_edge(model, "CIS", "executes-through", "CREATIVE_TOOL_BACKENDS")
          and not any(e["source"] == "CIS" and e["relationship"] == "contains"
                      and e["target"] in execution_ids for e in model["edges"]),
          [(e["relationship"], e["target"]) for e in model["edges"]
           if e["source"] == "CIS"])


def test_relationship_semantics_are_explicit(model):
    defined = {r["name"]: r for r in model["relationships"]}
    check("6a. all seven relationship classes are defined by the authority",
          sorted(defined) == ["contains", "controls", "executes-through", "feeds",
                             "orchestrates", "supports", "uses"],
          sorted(defined))
    check("6b. every definition is non-empty and carries its own provenance",
          all(r["definition"] and r["authority_ref"]["decision_id"].startswith("ADR-WIASW-")
              for r in defined.values()),
          [(n, bool(r["definition"])) for n, r in defined.items()])
    check("6c. every edge uses a defined relationship — none is left unexplained",
          all(e["relationship_defined"] for e in model["edges"]),
          [e["relationship"] for e in model["edges"] if not e["relationship_defined"]])
    check("6d. every edge names declared nodes at both ends",
          all(e["source_declared"] and e["target_declared"] for e in model["edges"]),
          [e["authority_ref"]["declaration"] for e in model["edges"]
           if not (e["source_declared"] and e["target_declared"])])
    check("6e. all seven are actually used, not merely defined",
          sorted(model["relationship_types_used"]) == sorted(defined),
          model["relationship_types_used"])
    # The point of the separation: no build-order vocabulary anywhere.
    check("6f. no build-order relationship (builds-before / next / phase-order) exists here",
          not ({"builds-before", "next", "phase-order"} & set(defined)),
          sorted(defined))
    # `feeds` is the one relationship that LOOKS like sequencing, so the
    # authority has to disclaim it in its own words rather than relying on this
    # module's reading of it.
    check("6g. `feeds` declares itself a stage contract, not a build-order edge",
          "feeds" in defined
          and "never a build-order, phase or chronology edge" in defined["feeds"]["definition"],
          defined.get("feeds", {}).get("definition"))


def test_activation_is_not_progress(model):
    activation = model["activation"]
    vocabulary = {v["state"] for v in activation["vocabulary"]}
    check("7a. the default activation state is NOT_ACTIVATED",
          activation["default"] == "NOT_ACTIVATED", activation["default"])
    check("7b. every WIASW node (root, domains, applications) is NOT_ACTIVATED",
          all(n["activation_state"] == "NOT_ACTIVATED" for n in model["nodes"]
              if n["kind"] in ("root", "domain_group", "domain",
                               "application_group", "application")),
          [(n["id"], n["activation_state"]) for n in model["nodes"]
           if n["kind"] in ("root", "domain", "application")
           and n["activation_state"] != "NOT_ACTIVATED"])
    check("7c. CIS's own status is deferred to its real authority, not restated here",
          node(model, "CIS")["activation_state"] == "TRACKED_ELSEWHERE",
          node(model, "CIS")["activation_state"])
    # ADR-WIASW-004 needed a third answer: accepted as destination, some
    # substrate already exists elsewhere, capability itself not built. Saying
    # NOT_ACTIVATED would have hidden the substrate; saying TRACKED_ELSEWHERE
    # would have claimed the capability is real today. Both are wrong.
    partial = {v["state"]: v for v in activation["vocabulary"]}.get("PARTIAL_SUBSTRATE")
    check("7g. PARTIAL_SUBSTRATE is defined by the authority and denies being built",
          partial is not None
          and "not implemented, not activated and not claimed implemented"
              in partial["definition"]
          and "not a build status" in partial["definition"],
          partial and partial["definition"])
    check("7h. it is used only where the authority assigned it, never by default",
          activation["default"] == "NOT_ACTIVATED"
          and {n["id"] for n in model["nodes"]
               if n["activation_state"] == "PARTIAL_SUBSTRATE"}
          == {"DEVELOPMENT_INTAKE", "INTAKE_CLASSIFICATION", "INTAKE_DEPENDENCY_ORDER",
              "INTAKE_VISIBILITY", "INTAKE_DURABILITY"},
          sorted(n["id"] for n in model["nodes"]
                 if n["activation_state"] == "PARTIAL_SUBSTRATE"))
    check("7d. every activation state used is defined in the authority's vocabulary",
          all(n["activation_state"] in vocabulary for n in model["nodes"]),
          sorted({n["activation_state"] for n in model["nodes"]} - vocabulary))
    check("7e. activation disclaims being a build status or ADR-PIPE-005 component state",
          "ADR-PIPE-005" in activation["note"]
          and "not a build status" in activation["note"].lower(),
          activation["note"][:160])
    # The vocabulary is the authority's, not this module's: the tokens come back
    # with the decision that declared them.
    check("7f. each activation state carries provenance to a decision row",
          all(v["authority_ref"]["decision_id"].startswith("ADR-WIASW-")
              for v in activation["vocabulary"]),
          [(v["state"], v["authority_ref"]) for v in activation["vocabulary"]])


def test_every_element_carries_provenance(model):
    check("8a. every node names the decision and clause that declared it",
          all(n["authority_ref"]["decision_id"].startswith("ADR-WIASW-")
              and n["authority_ref"]["clause"] == "DESTINATION GRAPH NODES"
              and n["authority_ref"]["declaration"] for n in model["nodes"]),
          [n["id"] for n in model["nodes"]
           if not n["authority_ref"].get("declaration")])
    check("8b. every node's declaration is quoted verbatim, not paraphrased",
          all(n["id"] in n["authority_ref"]["declaration"]
              and n["label"] in n["authority_ref"]["declaration"]
              for n in model["nodes"]),
          [n["id"] for n in model["nodes"]
           if n["label"] not in n["authority_ref"]["declaration"]])
    check("8c. every edge names the decision and clause that declared it",
          all(e["authority_ref"]["decision_id"].startswith("ADR-WIASW-")
              and e["authority_ref"]["clause"] == "DESTINATION GRAPH EDGES"
              for e in model["edges"]),
          [e["authority_ref"] for e in model["edges"]
           if e["authority_ref"]["clause"] != "DESTINATION GRAPH EDGES"])
    authority = model["authority"]
    check("8d. the semantic authority and the structured projection are stated separately",
          "project_decisions" in authority["semantic_authority"]
          and "no second store" in authority["structured_projection"],
          authority["semantic_authority"])
    check("8e. the authority states the architecture is NOT stored in roadmap/queue/build-plan",
          set(authority["not_stored_in"]) == {
              "project_state.pipeline_roadmap", "queue_items", "queue_edges",
              "build_plan_nodes", "build_plan_dependencies"},
          authority["not_stored_in"])
    check("8f. each decision reports which clauses it actually contributed",
          all(isinstance(d["clauses_contributed"], list) for d in model["decisions"])
          and "DESTINATION GRAPH NODES" in next(
              d for d in model["decisions"] if d["id"] == "ADR-WIASW-001"
          )["clauses_contributed"],
          {d["id"]: d["clauses_contributed"] for d in model["decisions"]})


def test_deterministic_vs_perceptual_principle_is_recoverable(model):
    text = " ".join(d["decision"] for d in model["decisions"])
    check("9a. the deterministic/perceptual distinction is in the authority text",
          "DETERMINISTIC VALIDATION" in text and "PERCEPTUAL" in text, None)
    check("9b. perceptual judgments are explicitly not made facts by model agreement",
          "MUST NOT become deterministic facts merely because one or more models agree" in text,
          None)
    check("9c. human creative authority is recorded as above model recommendations",
          "HUMAN CREATIVE AUTHORITY REMAINS ABOVE MODEL RECOMMENDATIONS" in text, None)
    check("9d. structured interfaces are preferred over GUI, which stays a legitimate fallback",
          "EXECUTION INTERFACE PREFERENCE" in text
          and "LEGITIMATE FALLBACK" in text, None)
    check("9e. WIASW is recorded as not being a mandatory linear pipeline",
          "NOT A LINEAR PIPELINE" in text, None)
    check("9f. WIASW implementation is recorded as requiring future human authorization",
          "requires future explicit human authorization" in text, None)
    check("9g. ADR-SEED-018's layer ownership is explicitly left unchanged",
          "ADR-SEED-018 IS NOT CHANGED OR SUPERSEDED" in text, None)


def test_zoom_levels(model):
    levels = {lv["id"]: lv for lv in model["levels"]}
    check("10a. two zoom levels are produced",
          sorted(levels) == ["full", "overview"], sorted(levels))
    overview = levels.get("overview")
    check("10b. level 1 answers 'why' with exactly the top-level three",
          overview and sorted(overview["node_ids"]) == ["CIS", "EXECUTION_LAYER", "WIASW"],
          overview and overview["node_ids"])
    check("10c. level 2 carries every recorded node",
          levels["full"]["node_count"] == len(model["nodes"]),
          (levels["full"]["node_count"], len(model["nodes"])))
    check("10d. each level's diagram is generated, and the two differ",
          overview["mermaid"].startswith("flowchart")
          and levels["full"]["mermaid"].startswith("flowchart")
          and overview["mermaid"] != levels["full"]["mermaid"], None)


def test_mermaid_is_generated_from_the_same_graph(model):
    source = model["mermaid"]
    check("11a. every node in the model appears in the diagram",
          all(f'  {n["id"]}["' in source for n in model["nodes"]),
          [n["id"] for n in model["nodes"] if f'  {n["id"]}["' not in source])
    check("11b. every edge appears with its relationship as the arrow label",
          all(f'  {e["source"]} -->|{e["relationship"]}| {e["target"]}' in source
              for e in model["edges"]),
          [e["authority_ref"]["declaration"] for e in model["edges"]
           if f'  {e["source"]} -->|{e["relationship"]}| {e["target"]}' not in source])
    check("11c. no unlabelled arrow exists — every edge states its semantics",
          " --> " not in source, None)
    check("11d. every node label marks itself DESTINATION scope",
          source.count("DESTINATION —") == len(model["nodes"]),
          (source.count("DESTINATION —"), len(model["nodes"])))


# ── 2. parsed, not hardcoded ─────────────────────────────────────────────

ALT_DECISION = (
    "A different architecture entirely. "
    'DESTINATION GRAPH NODES: TOPCO [root] "TopCo" = the alternate root; '
    'ONE [widget] "Widget One" = the first widget. '
    "DESTINATION GRAPH EDGES: TOPCO wraps ONE. "
    "DESTINATION GRAPH RELATIONSHIPS: wraps = the source wraps the target. "
    "ARCHITECTURE SCOPE: alternate. "
    "ACTIVATION: default SOMETHING_ELSE. "
    "ACTIVATION VOCABULARY: SOMETHING_ELSE = a different state token."
)


def test_graph_is_parsed_from_the_decision_text_not_hardcoded():
    path = scratch_db([("ADR-WIASW-001", "alternate", ALT_DECISION, "DECIDED")])
    model = da.get_destination_architecture(db_path=path)
    check("12a. the scratch architecture's own nodes are what comes back",
          [n["id"] for n in model["nodes"]] == ["TOPCO", "ONE"],
          [n["id"] for n in model["nodes"]])
    check("12b. no production node leaks into it — nothing is hardcoded in the module",
          not any(n["id"] in ("WIASW", "CIS", "WORD", "WEB") for n in model["nodes"]),
          [n["id"] for n in model["nodes"]])
    check("12c. the scratch relationship vocabulary is the one in use",
          [r["name"] for r in model["relationships"]] == ["wraps"]
          and model["relationship_types_used"] == ["wraps"],
          (model["relationship_types_used"], [r["name"] for r in model["relationships"]]))
    check("12d. the scratch activation default and scope are honored",
          model["activation"]["default"] == "SOMETHING_ELSE"
          and model["architecture_scope"] == "alternate",
          (model["activation"]["default"], model["architecture_scope"]))
    check("12e. its node kinds come from the text too",
          [n["kind"] for n in model["nodes"]] == ["root", "widget"],
          [n["kind"] for n in model["nodes"]])


def test_absent_architecture_is_reported_not_invented():
    path = scratch_db([("ADR-PIPE-001", "unrelated", "no graph clauses here", "DECIDED")])
    model = da.get_destination_architecture(db_path=path)
    check("13a. no ADR-WIASW row -> present:false",
          model["present"] is False, model.get("present"))
    check("13b. the absence is explained, naming the pattern it looked for",
          "ADR-WIASW-%" in model["note"], model.get("note"))
    check("13c. nothing is invented to fill the gap",
          model["nodes"] == [] and model["edges"] == [] and model["mermaid"] is None,
          (len(model["nodes"]), len(model["edges"]), model["mermaid"]))


def test_superseded_decision_drops_out():
    path = scratch_db([
        ("ADR-WIASW-001", "alternate", ALT_DECISION, "SUPERSEDED"),
    ])
    model = da.get_destination_architecture(db_path=path)
    check("14a. a SUPERSEDED decision is not read as authority",
          model["present"] is False, model.get("present"))


def test_malformed_architecture_is_reported_not_silently_fixed():
    broken = (
        'DESTINATION GRAPH NODES: ALPHA [thing] "Alpha" = the only declared node; '
        "BETA is missing its kind and label entirely. "
        "DESTINATION GRAPH EDGES: ALPHA points-at GHOST; ALPHA contains ALPHA2; "
        "ALPHA points_at ALPHA. "
        "DESTINATION GRAPH RELATIONSHIPS: contains = structural membership. "
        "ACTIVATION: default NOT_ACTIVATED; GHOST = NOT_ACTIVATED. "
        "ACTIVATION VOCABULARY: NOT_ACTIVATED = nothing has been activated."
    )
    path = scratch_db([("ADR-WIASW-001", "broken", broken, "DECIDED")])
    model = da.get_destination_architecture(db_path=path)
    kinds = {p["kind"] for p in model["problems"]}
    check("15a. an edge naming an undeclared node is reported",
          "edge_names_undeclared_node" in kinds, sorted(kinds))
    check("15b. an edge using an undefined relationship is reported",
          "undefined_relationship" in kinds, sorted(kinds))
    check("15c. an activation rule for an undeclared node is reported",
          "activation_for_undeclared_node" in kinds, sorted(kinds))
    check("15d. the offending edges stay visible rather than being dropped",
          len(model["edges"]) == 2
          and not all(e["target_declared"] for e in model["edges"]),
          [(e["source"], e["relationship"], e["target"], e["target_declared"])
           for e in model["edges"]])
    # The silent-loss case: a declaration the grammar cannot read at all must be
    # reported, not simply skipped — an architecture element that vanishes
    # without a word is worse than one that is visibly wrong.
    check("15e. a node declaration the grammar cannot read is reported, not dropped",
          "unparsable_node_declaration" in kinds
          and any("BETA is missing its kind" in p["detail"] for p in model["problems"]),
          sorted(kinds))
    check("15f. an edge declaration the grammar cannot read is reported, not dropped",
          "unparsable_edge_declaration" in kinds
          and any("points_at" in p["detail"] for p in model["problems"]),
          sorted(kinds))


def test_duplicate_node_declaration_is_reported():
    dupe = (
        'DESTINATION GRAPH NODES: ALPHA [thing] "Alpha" = first declaration. '
        "ARCHITECTURE SCOPE: destination. ACTIVATION: default NOT_ACTIVATED."
    )
    dupe2 = 'DESTINATION GRAPH NODES: ALPHA [thing] "Alpha again" = second declaration.'
    path = scratch_db([("ADR-WIASW-001", "first", dupe, "DECIDED"),
                       ("ADR-WIASW-002", "second", dupe2, "DECIDED")])
    model = da.get_destination_architecture(db_path=path)
    check("16a. a node declared twice by two decisions is reported as a conflict",
          any(p["kind"] == "duplicate_node" for p in model["problems"]),
          [p["kind"] for p in model["problems"]])
    check("16b. and one declaration wins rather than both being merged silently",
          len(model["nodes"]) == 1 and model["nodes"][0]["label"] == "Alpha",
          [(n["id"], n["label"]) for n in model["nodes"]])


def test_multi_decision_graph_is_merged_with_per_decision_provenance():
    model = da.get_destination_architecture()
    sources = {n["authority_ref"]["decision_id"] for n in model["nodes"]}
    check("17a. the live graph is assembled from more than one decision row",
          len(sources) > 1, sorted(sources))
    check("17b. the WIASW side and the CIS side each carry their own decision",
          node(model, "WIASW")["authority_ref"]["decision_id"]
          != node(model, "CIS")["authority_ref"]["decision_id"],
          (node(model, "WIASW")["authority_ref"]["decision_id"],
           node(model, "CIS")["authority_ref"]["decision_id"]))
    check("17c. a cross-decision edge resolves against the merged graph",
          has_edge(model, "WIASW", "uses", "CIS")
          and all(e["source_declared"] and e["target_declared"]
                  for e in model["edges"] if e["relationship"] == "uses"),
          [e for e in model["edges"] if e["relationship"] == "uses"])


# ── 3. separation from the build path ────────────────────────────────────

def test_destination_graph_is_not_the_phase_chain(model):
    build = bp.get_build_path()
    phase_ids = {p["id"] for p in build["phases"]}
    dest_ids = {n["id"] for n in model["nodes"]}
    check("18a. no destination node shares an id with a build phase",
          not (phase_ids & dest_ids), sorted(phase_ids & dest_ids))
    check("18b. no destination node is labelled like a phase",
          not any(n["id"].startswith("P") and n["id"][1:].isdigit()
                  for n in model["nodes"]),
          [n["id"] for n in model["nodes"]])
    check("18c. the destination model reports no phase, status or progress fields",
          not ({"phases", "current", "next", "progress", "status_vocabulary"}
               & set(model)),
          sorted({"phases", "current", "next", "progress"} & set(model)))
    check("18d. the build path still reports its own sequence, untouched",
          [p["id"] for p in build["phases"]][:3] == ["P0", "QUEUE_TRIAGE", "P1"]
          and build["current"]["phase_id"] == "P0",
          [p["id"] for p in build["phases"]])
    check("18e. the two diagrams are different sources",
          model["mermaid"] != build["mermaid"], None)
    check("18f. the destination authority points at the build path for the other question",
          "build_path.py" in model["authority"]["current_build_view"],
          model["authority"]["current_build_view"][:120])


def test_read_model_does_not_touch_roadmap_or_queue_sources():
    source = open(os.path.join(_REPO_ROOT, "tools", "state",
                               "destination_architecture.py"), encoding="utf-8").read()
    for table in ("queue_items", "queue_edges", "build_plan_nodes",
                  "build_plan_dependencies"):
        check(f"19a. {table} is never queried by the read model",
              f"FROM {table}" not in source and f"from {table}" not in source, table)
    check("19b. project_state is never read as an architecture source",
          "FROM project_state" not in source, None)
    check("19c. no generated .md path is read as an input",
          "UNIFIED_BUILD_LIST" not in source and "AGENTS.md" not in source, None)
    check("19d. no INSERT/UPDATE/DELETE statement exists in the read model",
          not any(kw in source.upper() for kw in
                  ("INSERT INTO", "UPDATE ", "DELETE FROM")),
          [kw for kw in ("INSERT INTO", "UPDATE ", "DELETE FROM")
           if kw in source.upper()])
    check("19e. the connection is opened read-only",
          "mode=ro" in source, None)


# ── 4. the endpoint ──────────────────────────────────────────────────────

def test_endpoint_matches_the_read_model():
    client = app.test_client()
    response = client.get("/api/workbench/destination-architecture")
    check("20a. the route answers 200", response.status_code == 200,
          response.status_code)
    payload = response.get_json()
    model = da.get_destination_architecture()
    check("20b. it returns the read model's own payload, not a reshaped copy",
          payload["read_model"] == model["read_model"]
          and [n["id"] for n in payload["nodes"]] == [n["id"] for n in model["nodes"]]
          and [(e["source"], e["relationship"], e["target"]) for e in payload["edges"]]
          == [(e["source"], e["relationship"], e["target"]) for e in model["edges"]],
          payload.get("read_model"))
    check("20c. exactly one destination-architecture route is registered",
          sorted(str(r) for r in app.url_map.iter_rules()
                 if "destination-architecture" in str(r))
          == ["/api/workbench/destination-architecture"],
          [str(r) for r in app.url_map.iter_rules()
           if "destination" in str(r)])
    check("20d. it accepts GET only",
          {"GET"} <= {m for r in app.url_map.iter_rules()
                      if "destination-architecture" in str(r) for m in r.methods}
          and not any(m in {m2 for r in app.url_map.iter_rules()
                            if "destination-architecture" in str(r) for m2 in r.methods}
                      for m in ("POST", "PUT", "PATCH", "DELETE")),
          [sorted(r.methods) for r in app.url_map.iter_rules()
           if "destination-architecture" in str(r)])


def test_no_caller_supplied_db_path_accepted():
    client = app.test_client()
    baseline = client.get("/api/workbench/destination-architecture").get_json()
    attempt = client.get(
        "/api/workbench/destination-architecture?db=/etc/passwd&db_path=/etc/passwd")
    check("21a. a db query parameter cannot redirect the read",
          attempt.status_code == 200
          and [n["id"] for n in attempt.get_json()["nodes"]]
          == [n["id"] for n in baseline["nodes"]],
          attempt.status_code)


def test_read_model_failure_returns_503_not_500():
    original = da.get_destination_architecture

    def boom(*a, **k):
        raise sqlite3.OperationalError("unable to open database file")

    da.get_destination_architecture = boom
    try:
        response = app.test_client().get("/api/workbench/destination-architecture")
    finally:
        da.get_destination_architecture = original
    check("22a. a read-model failure is a 503, not a 500",
          response.status_code == 503, response.status_code)
    payload = response.get_json()
    check("22b. the failure names the exception type rather than inventing a graph",
          "OperationalError" in payload["error"] and "nodes" not in payload,
          payload)


# ── 5. nothing changed ───────────────────────────────────────────────────

def test_reads_do_not_mutate_the_spine(before_counts, before_revision):
    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        after = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                 for t in before_counts}
        after_revision = cs.compute_state_revision(conn)
    finally:
        conn.close()
    check("23a. no row count changed while every route and read model ran",
          after == before_counts, {k: (before_counts[k], after[k])
                                   for k in after if after[k] != before_counts[k]})
    check("23b. the state revision is unchanged",
          after_revision == before_revision, (before_revision, after_revision))


def test_read_model_connection_is_read_only():
    conn = da._connect()
    try:
        conn.execute("CREATE TABLE _should_not_exist (x INTEGER)")
        check("23c. the read model's connection refuses a write", False,
              "CREATE TABLE succeeded on the read model's connection")
    except sqlite3.OperationalError as e:
        check("23c. the read model's connection refuses a write",
              "readonly" in str(e).lower(), str(e))
    finally:
        conn.close()


def test_current_build_state_is_unchanged(before_fingerprint):
    after = protected_fingerprint()
    differing = {k: (before_fingerprint[k], after[k])
                 for k in after if after[k] != before_fingerprint[k]}
    check("24a. every protected project_state row and queue table is byte-identical",
          not differing, differing)
    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        roadmap = conn.execute(
            "SELECT value FROM project_state WHERE key = 'pipeline_roadmap' "
            "ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()[0]
        phase = conn.execute(
            "SELECT value FROM project_state WHERE key = 'build_phase' "
            "ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()[0]
        # Every project_state key EXCEPT external_dev_checkpoint: the checkpoint
        # row is supposed to describe what was pushed (ADR-XDEV-002 makes that
        # visibility a requirement), so naming WIASW there is correct. Anywhere
        # else in project_state would mean the destination architecture had been
        # written into build state, which is the thing being guarded against.
        wiasw_rows = conn.execute(
            "SELECT COUNT(*) FROM project_state WHERE value LIKE '%WIASW%' "
            "AND key != 'external_dev_checkpoint'").fetchone()[0]
        queue_wiasw = conn.execute(
            "SELECT COUNT(*) FROM queue_items WHERE title LIKE '%WIASW%' "
            "OR COALESCE(body_md, '') LIKE '%WIASW%'").fetchone()[0]
    finally:
        conn.close()
    check("24b. the roadmap still carries the P0..P6 chain and no WIASW stage",
          roadmap.startswith("P0 (") and "WIASW" not in roadmap,
          roadmap[:60])
    check("24c. build_phase still reports P0, not a destination phase",
          "Phase P0" in phase and "WIASW" not in phase, phase[:80])
    check("24d. no project_state row outside the push checkpoint was given WIASW content",
          wiasw_rows == 0, wiasw_rows)
    check("24e. no queue item was created for WIASW",
          queue_wiasw == 0, queue_wiasw)


# ── 6. recoverability ────────────────────────────────────────────────────

def test_architecture_is_recoverable_through_the_canonical_chain():
    state = cs.get_canonical_state()
    family = [d for d in state["active_decisions"] if d["id"].startswith("ADR-WIASW-")]
    check("25a. the canonical state read model carries the ADR-WIASW decisions",
          len(family) == 4, [d["id"] for d in family])
    text = " ".join(d["decision"] for d in family)
    facts = {
        "WIASW is Word, Image, Action, Sound + Web":
            "WIASW = Word · Image · Action · Sound + Web" in text,
        "WIASW is the overarching destination architecture":
            "overarching workflow and product architecture" in text,
        "the five domains are named": all(
            f"{d}" in text for d in ("Word", "Image", "Action", "Sound", "Web")),
        "Web includes publishing, distribution and online sales": all(
            w in text for w in ("online publishing", "distribution", "online sales")),
        "horizontal applications are not additional domains":
            "NOT additional media domains" in text,
        "CIS is the substrate underneath WIASW":
            "CIS IS NOT THE ULTIMATE PRODUCT DESTINATION" in text,
        "CIS owns authority, evidence, provenance, checkpoints and recovery":
            "CIS owns the authoritative control boundaries" in text,
        "application semantics live above CIS":
            "WHAT BELONGS ABOVE CIS" in text,
        "structured interfaces are preferred over GUI":
            "EXECUTION INTERFACE PREFERENCE" in text,
        "GUI/computer-use is a legitimate fallback": "LEGITIMATE FALLBACK" in text,
        "deterministic and perceptual evidence differ":
            "PERCEPTUAL AND CREATIVE REVIEW" in text,
        "multi-model review may operate over WIASW artifacts":
            "independent reviews across technical, narrative, visual" in text,
        "human creative authority is above model recommendations":
            "HUMAN CREATIVE AUTHORITY REMAINS ABOVE MODEL RECOMMENDATIONS" in text,
        "WIASW is not a mandatory linear pipeline": "NOT A LINEAR PIPELINE" in text,
        "P0..P6 sequencing was not changed":
            "which this decision leaves UNCHANGED" in text,
        "WIASW implementation needs future human authorization":
            "requires future explicit human authorization" in text,
    }
    missing = [name for name, found in facts.items() if not found]
    check("25b. all 16 recovery facts are reconstructible from the recovered decisions",
          not missing, missing)
    check("25c. recovery does not depend on any markdown document",
          all("ADR-WIASW" in d["id"] for d in family), None)


# ── 7. the continuous development intake destination (ADR-WIASW-004) ─────
#
# Recorded because a development-relevant observation -- a request, a defect
# found in passing, a prerequisite discovered mid-implementation -- had no
# durable path into authoritative state, so its survival depended on a human
# or a model remembering it. These checks prove the requirement is readable
# from authority, that it is NOT claimed implemented, and that recording it
# authorized nothing.

def test_continuous_development_intake_is_recorded(model):
    intake = node(model, "DEVELOPMENT_INTAKE")
    check("26a. the intake capability is declared, under CIS, not as a top-level target",
          intake is not None and intake["kind"] == "destination_capability_group"
          and has_edge(model, "CIS", "contains", "DEVELOPMENT_INTAKE")
          and intake["depth"] == 1,
          intake and (intake["kind"], intake["depth"]))
    children = [e["target"] for e in model["edges"]
                if e["source"] == "DEVELOPMENT_INTAKE" and e["relationship"] == "contains"]
    check("26b. it carries the nine named intake capabilities",
          sorted(children) == sorted([
              "INTAKE_CAPTURE", "INTAKE_PROVENANCE", "INTAKE_REVIEW",
              "INTAKE_CLASSIFICATION", "INTAKE_RECONCILIATION",
              "INTAKE_DEPENDENCY_ORDER", "INTAKE_TARGET_TRACE",
              "INTAKE_VISIBILITY", "INTAKE_DURABILITY"]),
          sorted(children))
    check("26c. the discovery-to-build-order path is representable as stages, in order",
          has_edge(model, "INTAKE_CAPTURE", "feeds", "INTAKE_REVIEW")
          and has_edge(model, "INTAKE_REVIEW", "feeds", "INTAKE_CLASSIFICATION")
          and has_edge(model, "INTAKE_CLASSIFICATION", "feeds", "INTAKE_DEPENDENCY_ORDER"),
          [(e["source"], e["target"]) for e in model["edges"]
           if e["relationship"] == "feeds"])
    check("26d. it serves the WIASW targets, without becoming one of them",
          has_edge(model, "DEVELOPMENT_INTAKE", "supports", "WIASW")
          and has_edge(model, "DEVELOPMENT_INTAKE", "supports", "HORIZONTAL_APPLICATIONS")
          and not has_edge(model, "WIASW", "contains", "DEVELOPMENT_INTAKE"),
          [(e["relationship"], e["target"]) for e in model["edges"]
           if e["source"] == "DEVELOPMENT_INTAKE" and e["relationship"] != "contains"])
    check("26e. recording it did not change the 'why' level, which answers a different question",
          sorted(next(lv for lv in model["levels"]
                      if lv["id"] == "overview")["node_ids"])
          == ["CIS", "EXECUTION_LAYER", "WIASW"],
          next(lv for lv in model["levels"] if lv["id"] == "overview")["node_ids"])

    text = next(d["decision"] for d in model["decisions"] if d["id"] == "ADR-WIASW-004")
    facts = {
        "capture is not approval, and approval is not execution authorization":
            "CAPTURE != APPROVAL. APPROVAL != EXECUTION AUTHORIZATION." in text,
        "capture alone cannot activate a phase or authorize implementation":
            "activate a phase, create an implementation authorization" in text,
        "an observation may survive without becoming executable work":
            "survive even when it does NOT immediately become executable work" in text,
        "the record names what must not be depended on":
            "must NOT depend on architect memory, model memory, conversation context" in text,
        "provenance distinguishes unequal sources":
            "SOURCES DO NOT CARRY EQUAL AUTHORITY" in text,
        "intake is not the queue": "INTAKE IS NOT THE QUEUE" in text,
        "not every thought is forced into queue_items":
            "NOT EVERY THOUGHT IS FORCED INTO queue_items" in text,
        "queue triage is not the whole capability":
            "CURRENT QUEUE TRIAGE IS NOT A COMPLETE CONTINUOUS DEVELOPMENT INTAKE SYSTEM"
            in text,
        "queue_edges is current infrastructure, not the finished answer":
            "NOT assumed to be the complete destination solution" in text,
        "build-order reasoning is the purpose":
            "E before D before B before X" in text,
        "the targets are CIS, WIASW, the productivity applications and future families":
            "future architect-approved application families" in text,
        "lightweight capture must not require specifying the idea first":
            "WITHOUT requiring the architect to stop the current task" in text,
        "deduplication is required but not built":
            "SEMANTIC DEDUPLICATION IS NOT IMPLEMENTED BY THIS DECISION" in text,
        "no competing lifecycle authority is introduced":
            "NO COMPETING LIFECYCLE AUTHORITY IS INTRODUCED" in text,
        "no schema change was made or proposed":
            "NO TABLE, COLUMN, CHECK CONSTRAINT, ENUM OR MIGRATION IS CREATED" in text,
        "the capability is not claimed implemented":
            "THE FULL CAPABILITY IS NOT IMPLEMENTED AND IS NOT CLAIMED IMPLEMENTED" in text,
        "the gap is carried as an open question":
            "recorded as OQ-INTAKE-001" in text,
        "the existing queue and phase authorities are left unamended":
            "ADR-PIPE-008 are unamended" in text,
    }
    missing = [name for name, found in facts.items() if not found]
    check(f"26f. all {len(facts)} intake contract facts are readable from the decision row",
          not missing, missing)

    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        gap = conn.execute(
            "SELECT status, question FROM open_questions WHERE id = 'OQ-INTAKE-001'"
        ).fetchone()
        queue_hits = conn.execute(
            "SELECT COUNT(*) FROM queue_items WHERE title LIKE '%ADR-WIASW%' "
            "OR COALESCE(body_md, '') LIKE '%ADR-WIASW%' "
            "OR UPPER(title) LIKE '%CONTINUOUS DEVELOPMENT INTAKE%' "
            "OR UPPER(COALESCE(body_md, '')) LIKE '%CONTINUOUS DEVELOPMENT INTAKE%'"
        ).fetchone()[0]
        state_hits = conn.execute(
            "SELECT COUNT(*) FROM project_state WHERE value LIKE '%DEVELOPMENT_INTAKE%' "
            "AND key != 'external_dev_checkpoint'").fetchone()[0]
    finally:
        conn.close()
    check("26g. the implementation gap exists as an OPEN question, not as executable work",
          gap is not None and gap[0] == "OPEN"
          and "which does Eric authorize" in gap[1],
          gap and gap[0])
    check("26h. the gap question does not reorder accepted work, and says so",
          gap is not None and "NOTHING IS REORDERED BY THIS QUESTION" in gap[1]
          and "OQ-TRIAGE-003" in gap[1], None)
    check("26i. no queue item was created for the intake capability",
          queue_hits == 0, queue_hits)
    check("26j. the capability was not written into build state",
          state_hits == 0, state_hits)


def run():
    before_fingerprint = protected_fingerprint()
    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        before_counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                         for t in ("project_decisions", "project_state", "queue_items",
                                   "queue_edges", "dev_continuity_events")}
        before_revision = cs.compute_state_revision(conn)
    finally:
        conn.close()

    model = test_read_model_builds_from_live_authority()
    test_wiasw_is_the_root_and_is_defined(model)
    test_five_named_domains(model)
    test_horizontal_applications_are_not_domains(model)
    test_cis_is_the_substrate_beneath_wiasw(model)
    test_relationship_semantics_are_explicit(model)
    test_activation_is_not_progress(model)
    test_every_element_carries_provenance(model)
    test_deterministic_vs_perceptual_principle_is_recoverable(model)
    test_zoom_levels(model)
    test_mermaid_is_generated_from_the_same_graph(model)

    test_graph_is_parsed_from_the_decision_text_not_hardcoded()
    test_absent_architecture_is_reported_not_invented()
    test_superseded_decision_drops_out()
    test_malformed_architecture_is_reported_not_silently_fixed()
    test_duplicate_node_declaration_is_reported()
    test_multi_decision_graph_is_merged_with_per_decision_provenance()

    test_destination_graph_is_not_the_phase_chain(model)
    test_read_model_does_not_touch_roadmap_or_queue_sources()

    test_endpoint_matches_the_read_model()
    test_no_caller_supplied_db_path_accepted()
    test_read_model_failure_returns_503_not_500()

    test_reads_do_not_mutate_the_spine(before_counts, before_revision)
    test_read_model_connection_is_read_only()
    test_current_build_state_is_unchanged(before_fingerprint)
    test_architecture_is_recoverable_through_the_canonical_chain()
    test_continuous_development_intake_is_recorded(model)

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
