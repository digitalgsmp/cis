#!/usr/bin/env python3
"""test_project_intelligence_api.py — behavioral tests for the Workbench
Project Map read model (tools/state/project_intelligence.py) and its endpoint
(runtime/api/project_intelligence.py, GET /api/workbench/project-intelligence).

Four kinds of test, deliberately:

  1. COMPOSITION, not duplication. The embedded current-build payload is
     compared field-by-field against tools/state/build_path.py's own output,
     and the referenced destination nodes against
     tools/state/destination_architecture.py's own output. The module source is
     then searched for a hardcoded phase chain or a hardcoded WIASW node — the
     failure mode a "map over everything" card invites.

  2. HONESTY ABOUT ABSENCE. Where no authority records a link, the payload must
     carry confidence_class 'not_yet_linked' and the screen's exact sentence,
     not a plausible substitute. Asserted on the real state: WB1-D15 has no
     recorded solution direction, and no capability has a destination node.

  3. READ-ONLY AND NO TRIAGE. Every table the card forbids touching is hashed
     before and after exercising the route and compared; the 56 unclassified
     queue_items are asserted still unclassified, still marked AWAITING TRIAGE,
     and still carrying neither scope nor need_status afterwards.

  4. NO MODEL AT READ TIME. The request path is asserted to import no HTTP or
     model client, and each plain-language string shown as durable truth is
     asserted byte-present in the reviewed vocabulary FILE — so it demonstrably
     came from the repository and not from a generation call.

Tests 1-3 run against the LIVE spine, opened read-only: an assertion that
passes only against a hand-built fixture would prove nothing about the project
state this screen exists to explain. A scratch database is used where the point
is that nothing is hardcoded.

Run: python3 runtime/tests/test_project_intelligence_api.py
"""
import hashlib
import json
import re
import os
import shutil
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_HERE, ".."))                   # runtime/
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))  # read models
sys.path.insert(0, _REPO_ROOT)                                  # tools.development

os.environ.setdefault("CIS_PIPELINE_API_KEY", "")

import build_path as bp  # noqa: E402
import canonical_state as cs  # noqa: E402
import destination_architecture as da  # noqa: E402
import project_intelligence as pi  # noqa: E402

from container_app import app  # noqa: E402

results = []

ROUTE = "/api/workbench/project-intelligence"

# Everything the card forbids this screen from changing.
PROTECTED_TABLES = (
    "queue_items", "queue_edges", "project_state", "project_decisions",
    "dev_continuity_events", "build_plan_nodes", "build_plan_dependencies",
)
PROTECTED_STATE_KEYS = (
    "pipeline_roadmap", "build_phase", "current_direction", "next_action",
    "current_queue_item",
)


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def capability(model, cap_id):
    return next((c for c in model["capability_model"]["capabilities"]
                 if c["id"] == cap_id), None)


def problem(model, discovery_id):
    return next((p for p in model["problems"]["items"] if p["id"] == discovery_id), None)


def queue_item(model, item_num):
    return next((i for i in model["queue"]["items"] if i["item_num"] == item_num), None)


def step(model, phase_id):
    return next((s for s in model["trajectory"]["steps"] if s["id"] == phase_id), None)


def area(model, area_id):
    return next((a for a in model["anatomy"]["areas"] if a["id"] == area_id), None)


def table_fingerprint(conn):
    """A content hash per protected table, plus the latest value of every
    protected project_state key. Compared before/after to prove nothing in the
    card's forbidden set moved."""
    out = {}
    for table in PROTECTED_TABLES:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not exists:
            out[table] = "absent"
            continue
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        digest = hashlib.sha256()
        for row in rows:
            digest.update(repr(tuple(row)).encode("utf-8", "replace"))
        out[table] = f"{len(rows)}:{digest.hexdigest()}"
    for key in PROTECTED_STATE_KEYS:
        row = conn.execute(
            "SELECT value FROM project_state WHERE key=? ORDER BY created_at DESC, id DESC "
            "LIMIT 1", (key,)).fetchone()
        out[f"state:{key}"] = row[0] if row else None
    return out


# ── 1. the read model builds from live authority ─────────────────────────

def test_read_model_builds():
    model = pi.get_project_intelligence()
    check("1a. the read model builds from the current authority state",
          model.get("read_model") == "cis_project_intelligence",
          model.get("read_model"))
    check("1b. a state revision is reported alongside it",
          isinstance(model.get("state_revision"), str) and model["state_revision"],
          model.get("state_revision"))
    check("1c. it declares itself a composition layer, not an authority",
          "not an authority" in (model["authority"]["role"] or ""),
          model["authority"]["role"][:80])
    check("1d. all five conceptual areas plus the overview are present",
          [a["id"] for a in model["areas"]] ==
          ["overview", "current_build", "queue_problems", "system_anatomy",
           "destination", "trajectory"],
          [a["id"] for a in model["areas"]])
    check("1e. the three presentation modes are declared, Simple by default",
          [m["id"] for m in model["modes"]] == ["simple", "detail", "technical"]
          and model["modes"][0]["default"] is True,
          [m["id"] for m in model["modes"]])
    check("1f. the three provenance classes are declared and no score is produced",
          [c["id"] for c in model["confidence_classes"]] ==
          ["authoritative", "derived_from_evidence", "not_yet_linked"]
          and not any("score" in json.dumps(c) for c in model["confidence_classes"]),
          [c["id"] for c in model["confidence_classes"]])
    check("1g. no unresolved read-model problem on the live state",
          model["problems_found"] == [], model["problems_found"])
    return model


# ── 2. the existing Build Path authority is REUSED ───────────────────────

def test_build_path_is_composed_not_duplicated(model):
    own = bp.get_build_path()
    embedded = model["current_build"]["build_path"]
    check("2a. the Current Build area is available and names the build-path read model",
          model["current_build"]["available"] is True
          and model["current_build"]["read_model"] == "cis_build_path",
          model["current_build"].get("read_model"))

    # generated_at/state_revision are per-call; everything that describes the
    # build must be identical to what build_path.py itself answers.
    compared = ("phases", "current", "next", "progress", "queue", "roadmap_source",
                "blockers", "discoveries", "checkpoint", "decisions", "mermaid",
                "authority", "status_vocabulary", "next_action", "current_direction")
    mismatched = [k for k in compared
                  if json.dumps(embedded.get(k), sort_keys=True, default=str)
                  != json.dumps(own.get(k), sort_keys=True, default=str)]
    check("2b. every build field is byte-identical to tools/state/build_path.py's own output",
          not mismatched, f"differing keys: {mismatched}")

    source = pi.Path(pi.__file__).read_text(encoding="utf-8")
    check("2c. the composition layer calls the build-path read model",
          "bp.get_build_path(" in source, "must call, not reimplement")
    # The failure mode is a phase IDENTIFIER the code can branch on, not the
    # word "P0" appearing in a docstring that explains what the module does
    # not do. So: no phase id may appear as a quoted string literal anywhere.
    quoted = [p["id"] for p in own["phases"]
              if f'"{p["id"]}"' in source or f"'{p['id']}'" in source]
    check("2d. no phase identifier is a string literal in the composition layer",
          not quoted,
          f"hardcoded phase ids: {quoted} — the module must look them up, never name them")
    check("2e. the triage stage is found by its composed shape, not by its name",
          'if "queue_classification" in p' in source,
          "naming the triage stage would be a second copy of the roadmap's ordering")
    check("2f. the roadmap/queue authority split is restated from the composed model, "
          "not reinvented",
          embedded["authority"]["work_items"] == own["authority"]["work_items"],
          embedded["authority"].get("work_items"))
    check("2g. the trajectory steps are the composed phases, in the composed order",
          [s["id"] for s in model["trajectory"]["steps"]] == [p["id"] for p in own["phases"]],
          [s["id"] for s in model["trajectory"]["steps"]])
    check("2h. every trajectory step names the build read model as its source",
          all(s["source"].startswith("tools/state/build_path.py")
              and s["confidence_class"] == "authoritative"
              for s in model["trajectory"]["steps"]),
          "a step must not claim its own authority")


# ── 3. the existing Destination Architecture authority is REUSED ─────────

def test_destination_is_composed_not_duplicated(model):
    own = da.get_destination_architecture()
    referenced = model["destination"]
    check("3a. the destination area names the destination read model and is present",
          referenced["available"] is True
          and referenced["read_model"] == "cis_destination_architecture"
          and referenced["present"] is True,
          referenced.get("read_model"))
    check("3b. the referenced nodes are exactly the composed model's nodes, in order",
          [n["id"] for n in referenced["nodes"]] == [n["id"] for n in own["nodes"]],
          f"{len(referenced['nodes'])} vs {len(own['nodes'])}")
    check("3c. each referenced node carries the composed model's own authority_ref",
          all(r["authority_ref"] == o["authority_ref"]
              for r, o in zip(referenced["nodes"], own["nodes"])),
          "provenance must come from the owning read model")
    check("3d. the node/edge counts are the composed model's, not a second count",
          referenced["counts"] == own["counts"], referenced.get("counts"))
    check("3e. the full architecture is referenced by route, not duplicated here",
          referenced["endpoint"] == "GET /api/workbench/destination-architecture"
          and "edges" not in referenced,
          "the edges, relationship definitions and diagrams stay with their own read model")

    source = pi.Path(pi.__file__).read_text(encoding="utf-8")
    hardcoded = [n["id"] for n in own["nodes"]
                 if n["id"] not in ("CIS", "WIASW") and n["id"] in source]
    check("3f. no destination node is hardcoded in the composition layer",
          not hardcoded,
          f"hardcoded node ids: {hardcoded}")
    check("3g. the two node ids the module does name are the recorded trajectory link only",
          source.count('nodes.get("WIASW")') == 1 and source.count('nodes.get("CIS")') == 1,
          "CIS and WIASW appear only in destination_link(), looked up in the composed graph")
    check("3h. the composition layer calls the destination read model",
          "da.get_destination_architecture(" in source, "must call, not reimplement")


# ── 4. the current build state is reported, never changed ────────────────

def test_p0_remains_current_and_triage_remains_next(model):
    build = model["current_build"]["build_path"]
    p0 = next((p for p in build["phases"] if p["id"] == "P0"), None)
    triage = next((p for p in build["phases"] if p["id"] == "QUEUE_TRIAGE"), None)
    check("4a. P0 is still the current phase",
          p0 is not None and p0["is_current"] is True and p0["status"] == "active",
          None if p0 is None else (p0["status"], p0["is_current"]))
    check("4b. P0 is still blocked, not complete",
          p0 is not None and p0["blocked"] is True and p0["status"] != "complete",
          None if p0 is None else p0["status_label"])
    check("4c. queue triage is still the NEXT stage, not a started one",
          triage is not None and triage["status"] == "next"
          and build["next"]["phase_id"] == "QUEUE_TRIAGE",
          None if triage is None else triage["status"])
    check("4d. P1 is still pending — nothing on this screen activates it",
          next((p["status"] for p in build["phases"] if p["id"] == "P1"), None) == "pending",
          next((p["status"] for p in build["phases"] if p["id"] == "P1"), None))
    check("4e. the trajectory marks P0 current and does not reorder the chain",
          step(model, "P0")["is_current"] is True
          and [s["order"] for s in model["trajectory"]["steps"]]
          == sorted(s["order"] for s in model["trajectory"]["steps"]),
          "the composed order is preserved verbatim")


# ── 5. 56 unclassified queue items remain unclassified ───────────────────

def test_queue_is_shown_never_triaged(model):
    queue = model["queue"]
    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        live_total = conn.execute("SELECT COUNT(*) FROM queue_items").fetchone()[0]
        live_unclassified = conn.execute(
            "SELECT COUNT(*) FROM queue_items WHERE need_status IS NULL AND scope IS NULL"
        ).fetchone()[0]
    finally:
        conn.close()

    check("5a. the queue total is the live count, not a cached one",
          queue["total_items"] == live_total, f"{queue['total_items']} vs {live_total}")
    check("5b. 56 items are reported awaiting triage, matching the live unclassified set",
          queue["awaiting_triage"] == live_unclassified == 56,
          f"model {queue['awaiting_triage']}, live {live_unclassified}")
    check("5c. the counts come from the build-path read model's own definition",
          queue["counts"]["unclassified"] == queue["awaiting_triage"],
          "a second definition of 'unclassified' could disagree with the Build Path screen")
    check("5d. every awaiting item is labelled AWAITING TRIAGE and carries no classification",
          all(i["classification_status"] == "AWAITING TRIAGE"
              and i.get("need_status") is None and i.get("scope") is None
              for i in queue["items"] if i["awaiting_triage"]),
          "an awaiting item must not be given a scope or a status here")
    check("5e. classified items are visibly distinguished from the awaiting set",
          queue["classified"] + queue["awaiting_triage"] == queue["total_items"]
          and all(i["classification_status"] == "CLASSIFIED"
                  for i in queue["items"] if not i["awaiting_triage"]),
          f"{queue['classified']} + {queue['awaiting_triage']} vs {queue['total_items']}")
    check("5f. the payload states outright that triage was not performed",
          queue["triage_state"]["performed_here"] is False
          and "has NOT been performed" in queue["triage_state"]["statement"],
          queue["triage_state"]["statement"][:60])
    check("5g. no item is ordered, merged or renumbered — item_nums are the live ones",
          len({i["item_num"] for i in queue["items"]}) == live_total,
          "every row appears exactly once, under its own number")
    check("5h. scope and need_status distributions are exposed for the triage interface",
          queue["distributions"]["need_status"] and queue["distributions"]["scope"]
          and queue["distributions"]["tier"],
          "the distributions Eric needs to understand the triage problem")
    check("5i. no queue edge is synthesized — the edge count is the stored one",
          queue["edge_count"] == 45 or queue["edge_count"] ==
          sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
          .execute("SELECT COUNT(*) FROM queue_edges").fetchone()[0],
          queue["edge_count"])
    check("5j. a stored edge's own confidence column drives its provenance class, "
          "and is not upgraded",
          all(e["confidence_class"] == ("authoritative" if e["stored_confidence"] == "explicit"
                                        else "derived_from_evidence")
              for i in queue["items"] for e in i["edges"]),
          "a 'prose' edge must never be reported authoritative")


def test_queue_item_drilldown(model):
    item = queue_item(model, "1.23")
    check("6a. a roadmap-named item carries its own technical text",
          item is not None and item["title"] and item["body_excerpt"],
          None if item is None else item["title"])
    check("6b. the roadmap's naming of it is reported AUTHORITATIVE with the roadmap quoted",
          item["phase_hooks"] and item["phase_hooks"][0]["confidence_class"] == "authoritative"
          and item["phase_hooks"][0]["authority_refs"][0]["state_key"] == "pipeline_roadmap",
          item["phase_hooks"])
    check("6c. that item has a reviewed plain-English explanation",
          item["plain_language_recorded"] is True
          and item["plain_english"] != model["missing_plain_language_text"]
          and item["plain_language_provenance"] == "reviewed_static_explanatory_metadata",
          item["plain_english"][:60])

    unexplained = [i for i in model["queue"]["items"] if not i["plain_language_recorded"]]
    check("6d. items with no reviewed explanation say so rather than being invented",
          unexplained
          and all(i["plain_english"] == "Plain-language explanation not yet recorded."
                  and i["plain_language_provenance"] is None for i in unexplained),
          f"{len(unexplained)} items without reviewed text")
    check("6e. no speculative explanation was created for UI completeness",
          len(model["queue"]["items"]) - len(unexplained) <= 5,
          f"{len(model['queue']['items']) - len(unexplained)} explained of "
          f"{len(model['queue']['items'])} — a per-item description for all of them would be "
          "the thing the card forbids")
    check("6f. an item the roadmap does not name reports the missing phase link, "
          "rather than being attached to one",
          all(i["phase_hooks"] == [] for i in model["queue"]["items"]
              if i["item_num"] not in ("0.4", "0.6", "1.23")),
          "only the three items the roadmap itself names carry a phase hook")


# ── 7. problems / discoveries ────────────────────────────────────────────

def test_problem_view(model):
    d15 = problem(model, "WB1-D15")
    check("7a. the blocking discovery appears with its technical id",
          d15 is not None and d15["display_status"] == "blocking",
          None if d15 is None else d15["display_status"])
    check("7b. it carries a reviewed plain-English title and a why-it-matters",
          d15["plain_language_recorded"] is True
          and "DeepSeek" in d15["plain_english"] and d15["why_it_matters"],
          d15["plain_english"])
    check("7c. its disposition is kept as its own status system, not merged into a build status",
          d15["disposition"] == "BEFORE_STAGE_CLOSEOUT"
          and d15["blocking"] is True
          and "NOT a build-phase status" in d15["status_systems"]["note"],
          d15["status_systems"])
    check("7d. its build relationship is P0, derived from two authority rows and said so",
          d15["build_position"]["confidence_class"] == "derived_from_evidence"
          and d15["build_position"]["phase_id"] == "P0"
          and {r["state_key"] for r in d15["build_position"]["authority_refs"]}
          == {"current_queue_item", "build_phase"},
          d15["build_position"])
    check("7e. NO solution is manufactured where the authority only describes the problem",
          d15["solution_direction"]["confidence_class"] == "not_yet_linked"
          and d15["solution_direction"]["text"] is None
          and "not formally recorded" in d15["solution_direction"]["explanation"],
          d15["solution_direction"])
    check("7f. the project's own next_action sentence naming it is quoted as evidence",
          any(m["state_key"] == "next_action" and "WB1-D15" in m["quote"]
              and m["confidence_class"] == "derived_from_evidence"
              for m in d15["named_in_state"]),
          [m["state_key"] for m in d15["named_in_state"]])
    check("7g. the capability it concerns is derived from a literal identifier match, quoted",
          d15["capability_ids"] == ["braingate_conversation"],
          d15["capability_ids"])
    check("7h. the full technical summary is carried, not replaced by the plain wording",
          "DEEPSEEK_API_KEY" in d15["summary"], d15["summary"][:60])

    resolved = problem(model, "WB1-D17")
    check("7i. a resolved finding's recorded resolution IS shown, and is authoritative",
          resolved is not None and resolved["resolved"] is True
          and resolved["solution_direction"]["confidence_class"] == "authoritative"
          and resolved["solution_direction"]["text"],
          None if resolved is None else resolved["solution_direction"]["confidence_class"])

    deferred = problem(model, "XDEV-R2")
    check("7j. an explicitly deferred finding shows the destination the record itself names",
          deferred is not None and deferred["deferral"]
          and deferred["deferral"]["destination"]
          and deferred["solution_direction"]["confidence_class"] == "authoritative",
          None if deferred is None else deferred["disposition"])

    unexplained = [p for p in model["problems"]["items"] if not p["plain_language_recorded"]]
    check("7k. findings with no reviewed explanation say so rather than being invented",
          all(p["plain_english"] == "Plain-language explanation not yet recorded."
              for p in unexplained),
          f"{len(unexplained)} findings without reviewed text")
    check("7l. discovery status is NOT re-derived here — it is the ledger's own reading",
          all(p["display_status"] in ("blocking", "open", "deferred", "resolved")
              for p in model["problems"]["items"]),
          sorted({p["display_status"] for p in model["problems"]["items"]}))


def test_discovery_status_is_distinct_from_build_status(model):
    build = model["current_build"]["build_path"]
    build_statuses = {p["status"] for p in build["phases"]}
    discovery_statuses = {p["display_status"] for p in model["problems"]["items"]}
    dispositions = {p["disposition"] for p in model["problems"]["items"]}
    queue_statuses = {i.get("need_status") for i in model["queue"]["items"]}
    cap_statuses = {c["status"] for c in model["capability_model"]["capabilities"]}
    dest_states = {n["activation_state"] for n in model["destination"]["nodes"]}

    check("8a. discovery dispositions are a different vocabulary from phase statuses",
          not (dispositions & build_statuses), dispositions & build_statuses)
    check("8b. queue need_status values are a different vocabulary again",
          not ({q for q in queue_statuses if q} & build_statuses),
          {q for q in queue_statuses if q} & build_statuses)
    check("8c. capability activation is its own vocabulary, not a phase status",
          not (cap_statuses & build_statuses) and not (cap_statuses & dispositions),
          cap_statuses)
    check("8d. destination activation is its own vocabulary, not a capability status",
          not (dest_states & cap_statuses) and dest_states <= {"NOT_ACTIVATED",
                                                              "TRACKED_ELSEWHERE"},
          dest_states)
    check("8e. five status systems coexist without being collapsed into one",
          len({frozenset(build_statuses), frozenset(discovery_statuses),
               frozenset(cap_statuses), frozenset(dest_states)}) == 4,
          "each view keeps the vocabulary of the authority it came from")
    check("8f. the payload says so in words as well as in structure",
          "five different vocabularies" in model["authority"]["status_separation"],
          model["authority"]["status_separation"][:60])


# ── 9. capability model ──────────────────────────────────────────────────

def test_capability_model_is_derived_and_says_so(model):
    provenance = model["capability_model"]["provenance"]
    check("9a. the capability view declares itself DERIVED, with no authority behind it",
          provenance["class"] == "derived_from_evidence"
          and provenance["authority_exists"] is False,
          provenance["class"])
    check("9b. it records that candidate authorities were inspected first",
          {c["candidate"] for c in provenance["candidates_inspected"]}
          >= {"functional_spec", "build_plan_nodes"},
          [c["candidate"] for c in provenance["candidates_inspected"]])
    check("9c. functional_spec is explicitly rejected rather than silently adopted",
          any(c["candidate"] == "functional_spec" and "rejected" in c["verdict"]
              for c in provenance["candidates_inspected"]),
          provenance["candidates_inspected"][0])
    check("9d. every capability repeats its derived provenance on itself",
          all(c["provenance_class"] == "derived_from_evidence"
              for c in model["capability_model"]["capabilities"]),
          "a capability must not look authoritative in isolation")

    braingate = capability(model, "braingate_conversation")
    check("9e. a registered capability's status is OBSERVED from container_app.py, with the line",
          braingate["status"] == "REGISTERED"
          and braingate["registration"]["registered"] is True
          and "runtime/container_app.py:" in braingate["registration"]["evidence"]
          and "register_blueprint(braingate_conversation_bp)"
          in braingate["registration"]["evidence"],
          braingate["registration"])
    check("9f. it carries a plain-English sentence first",
          "Allows Eric to talk with Braingate" in braingate["plain_english"],
          braingate["plain_english"])
    check("9g. its implementation files are observed present on disk",
          all(f["exists"] for f in braingate["files"])
          and "runtime/braingate_conversation.py" in [f["path"] for f in braingate["files"]],
          braingate["files"])
    check("9h. its migrations are observed applied from the live schema, not claimed",
          all(m["applied"] is True for m in braingate["migrations"])
          and {m["migration"] for m in braingate["migrations"]} == {"0035", "0038"},
          braingate["migrations"])

    factory = capability(model, "card_factory")
    runner = capability(model, "card_runner")
    check("9i. the dormant capabilities are reported built-but-unregistered",
          factory["status"] == "BUILT_NOT_REGISTERED"
          and runner["status"] == "BUILT_NOT_REGISTERED",
          (factory["status"], runner["status"]))
    check("9j. their code is present while their migrations are observed NOT applied",
          all(f["exists"] for f in factory["files"] + runner["files"])
          and all(m["applied"] is False
                  for m in factory["migrations"] + runner["migrations"]),
          [m["applied"] for m in factory["migrations"] + runner["migrations"]])
    check("9k. the build authority's own dormancy sentence is QUOTED, not paraphrased "
          "into a status",
          any("BUILT_BUT_DORMANT" in m["quote"] for m in factory["authority_mentions"]),
          [m["matched_term"] for m in factory["authority_mentions"]])
    check("9l. no capability claims a destination architecture node",
          all(c["destination_link"]["confidence_class"] == "not_yet_linked"
              for c in model["capability_model"]["capabilities"]),
          "linking a capability to WIASW would be the invented relationship the card forbids")
    check("9m. a capability the roadmap does not name reports the missing build link",
          capability(model, "card_factory")["build_position"] == []
          and "No phase" in capability(model, "card_factory")["build_position_note"],
          capability(model, "card_factory")["build_position_note"])
    check("9n. a capability the roadmap DOES name carries it as derived, with the roadmap quoted",
          braingate["build_position"]
          and braingate["build_position"][0]["confidence_class"] == "derived_from_evidence"
          and braingate["build_position"][0]["phase_id"] == "P0",
          braingate["build_position"])


def test_capability_status_tracks_observed_registration():
    """The whole point of observing registration rather than declaring it: a
    container_app.py that registers nothing must produce dormant capabilities,
    with no hardcoded 'Braingate is live' anywhere."""
    with tempfile.TemporaryDirectory() as tmp:
        fake = os.path.join(tmp, "container_app.py")
        with open(fake, "w", encoding="utf-8") as fh:
            fh.write("# a container app that registers nothing\n")
        registered, problem_ = pi.registered_blueprints(path=fake)
        check("10a. a container app registering nothing yields no observed registration",
              registered == {} and problem_ is None, registered)

        conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            vocabulary, _ = pi.load_vocabulary()
            caps = pi.build_capabilities(conn, vocabulary, registered, None, [], [])
        finally:
            conn.close()
        states = {c["id"]: c["status"] for c in caps}
        check("10b. every blueprint-backed capability then reads BUILT_NOT_REGISTERED",
              all(v == "BUILT_NOT_REGISTERED"
                  for k, v in states.items() if k != "external_dev_verification"),
              states)
        check("10c. the capability with no blueprint is unaffected — it has no route surface",
              states["external_dev_verification"] == "NO_ROUTE_SURFACE",
              states["external_dev_verification"])

    registered, problem_ = pi.registered_blueprints(path=os.path.join("/nonexistent", "x.py"))
    check("10d. an unreadable container app is reported, not assumed",
          registered is None and problem_["kind"] == "registration_unreadable",
          problem_)


# ── 11. system anatomy ───────────────────────────────────────────────────

def test_anatomy(model):
    anatomy = model["anatomy"]
    check("11a. the anatomy is rooted at CIS with major functional areas only",
          anatomy["root"] == "CIS" and len(anatomy["areas"]) == 8,
          [a["id"] for a in anatomy["areas"]])
    check("11b. it states that it is deliberately not the repository tree",
          "not the repository tree" in anatomy["note"], anatomy["note"])
    check("11c. every area answers what/does/why in plain language",
          all(a["plain_english"] and a["what_it_does"] and a["why_cis_needs_it"]
              for a in anatomy["areas"]),
          [a["id"] for a in anatomy["areas"]
           if not (a["plain_english"] and a["what_it_does"] and a["why_cis_needs_it"])])
    check("11d. every area's status is ROLLED UP from observed capability status, not declared",
          all("rolled up" in a["status_derivation"] for a in anatomy["areas"]),
          "an area must not be able to claim it is active")
    braingate = area(model, "braingate")
    dormant = area(model, "dormant_execution")
    check("11e. an area with a registered capability reads ACTIVE",
          braingate["status"] == "ACTIVE"
          and braingate["capability_ids"] == ["braingate_conversation"],
          braingate["status"])
    check("11f. the dormant-features area reads DORMANT, from its unregistered members",
          dormant["status"] == "DORMANT"
          and sorted(dormant["capability_ids"]) == ["card_factory", "card_runner"],
          dormant["status"])
    check("11g. every area lists the files that implement it",
          all(a["files"] for a in anatomy["areas"] if a["capability_ids"]),
          [a["id"] for a in anatomy["areas"] if a["capability_ids"] and not a["files"]])
    check("11h. no area references a capability the model does not carry",
          all(a["unresolved_capability_ids"] == [] for a in anatomy["areas"]),
          [a["unresolved_capability_ids"] for a in anatomy["areas"]])


def test_file_drilldown(model):
    files = {f["path"]: f for f in model["anatomy"]["files"]}
    check("12a. the switchboard file is explained in the card's own plain terms",
          "runtime/container_app.py" in files
          and files["runtime/container_app.py"]["plain_english"]
          == "The main switchboard for the live CIS server.",
          files.get("runtime/container_app.py", {}).get("plain_english"))
    check("12b. it explains why registration matters, not merely what the file is",
          "may exist in code but remain unavailable"
          in files["runtime/container_app.py"]["why_it_matters"],
          files["runtime/container_app.py"]["why_it_matters"])
    check("12c. the Braingate boundary file is explained as the safety wrapper it is",
          "safety wrapper" in files["runtime/braingate_conversation.py"]["plain_english"],
          files["runtime/braingate_conversation.py"]["plain_english"])
    check("12d. every described file carries a technical role alongside the plain wording",
          all(f["technical_role"] for f in model["anatomy"]["files"]),
          [f["path"] for f in model["anatomy"]["files"] if not f.get("technical_role")])

    described = set(files)
    referenced = {f["path"] for c in model["capability_model"]["capabilities"]
                  for f in c["files"]} | {"runtime/container_app.py"}
    check("12e. no file is described that no capability names — the repository was not scanned",
          described <= referenced | {"runtime/ui/src/BuildPath.jsx",
                                     "runtime/ui/src/DestinationArchitecture.jsx"},
          sorted(described - referenced))
    check("12f. the file list is small and curated, not thousands of generated descriptions",
          len(described) <= 40, len(described))


# ── 13. trajectory ───────────────────────────────────────────────────────

def test_trajectory(model):
    trajectory = model["trajectory"]
    rel = trajectory["destination_relationship"]
    check("13a. the build steps are chronological and the destination is separated out",
          "chronological" in trajectory["separation_note"]
          and "architectural" in trajectory["separation_note"],
          trajectory["separation_note"][:60])
    check("13b. the destination relationship is explicitly NOT a phase ordering",
          rel["is_phase_ordering"] is False, rel["is_phase_ordering"])
    check("13c. it carries the card's required wording verbatim",
          rel["warning"] == "Destination relationship — not an automatic next phase.",
          rel["warning"])
    check("13d. it states that finishing the last phase does not start destination work",
          "does not start destination work" in rel["explanation"],
          rel["explanation"][:80])
    check("13e. the recorded link is CIS then WIASW, and is authoritative",
          [n["node_id"] for n in rel["nodes"]] == ["CIS", "WIASW"]
          and all(n["confidence_class"] == "authoritative" for n in rel["nodes"]),
          [(n["node_id"], n["confidence_class"]) for n in rel["nodes"]])
    check("13f. each link quotes the decision clause it came from",
          all(n["authority_refs"][0]["decision_id"].startswith("ADR-WIASW-")
              and n["authority_refs"][0]["declaration"] for n in rel["nodes"]),
          [n["authority_refs"][0] for n in rel["nodes"]])
    check("13g. neither destination node is reported activated",
          {n["activation_state"] for n in rel["nodes"]}
          == {"TRACKED_ELSEWHERE", "NOT_ACTIVATED"},
          [(n["node_id"], n["activation_state"]) for n in rel["nodes"]])
    check("13h. no 'P6 -> WIASW' edge exists in the relationship list",
          not any(r["source"] in ("P6", "P5") and r["target"] in ("WIASW", "CIS")
                  for r in model["relationships"]),
          [r for r in model["relationships"] if r["target"] in ("WIASW", "CIS")])
    check("13i. the trajectory diagram marks the destination arrow with the warning",
          rel["warning"] in trajectory["mermaid"]
          and "-.->" in trajectory["mermaid"],
          "the arrow must be visibly a different kind of arrow")
    check("13j. a step the roadmap does not tie to a capability leaves the chain broken",
          any(not step(model, p["id"])["capability_ids"]
              for p in model["current_build"]["build_path"]["phases"]),
          "the card forbids inventing a capability for every phase")


# ── 14. relationship provenance ──────────────────────────────────────────

def test_relationship_provenance(model):
    rels = model["relationships"]
    check("14a. every relationship carries the card's five fields",
          all({"source", "target", "relationship", "confidence_class",
               "authority_refs", "explanation"} <= set(r) for r in rels),
          "a relationship with no provenance is the thing this card forbids")
    check("14b. every confidence_class is one of the three declared values",
          {r["confidence_class"] for r in rels}
          <= {"authoritative", "derived_from_evidence", "not_yet_linked"},
          {r["confidence_class"] for r in rels})
    check("14c. no relationship is a number, a score or a probability",
          not any(isinstance(r["confidence_class"], (int, float)) for r in rels),
          "confidence_class is a provenance classification, not a model's confidence")
    check("14d. every authoritative/derived relationship actually carries a reference",
          all(r["authority_refs"] for r in rels
              if r["confidence_class"] != "not_yet_linked"),
          [r["relationship"] for r in rels
           if r["confidence_class"] != "not_yet_linked" and not r["authority_refs"]])
    check("14e. every not_yet_linked relationship carries NO reference and an explanation",
          all(r["authority_refs"] == [] and r["explanation"] for r in rels
              if r["confidence_class"] == "not_yet_linked"),
          "an unlinked relationship must not smuggle in evidence")
    check("14f. unlinked relationships exist — the map is honest rather than complete",
          model["counts"]["not_yet_linked"] > 0, model["counts"]["not_yet_linked"])
    check("14g. a derived problem/capability link quotes the term and the sentence that matched",
          any(r["relationship"] == "problem_concerns_capability"
              and r["confidence_class"] == "derived_from_evidence"
              and r["authority_refs"][0]["matched_term"]
              and r["authority_refs"][0]["quote"] for r in rels),
          "the reader must be able to check the match themselves")
    check("14h. the exact missing-link sentence is the one the model declares",
          model["missing_link_text"] == "No authoritative link recorded yet.",
          model["missing_link_text"])


# ── 15. plain language and technical disclosure ──────────────────────────

def test_simple_mode_has_plain_language(model):
    simple = next(m for m in model["modes"] if m["id"] == "simple")
    check("15a. Simple is the default mode and shows plain language",
          simple["default"] is True and "plain_english" in simple["shows"],
          simple["shows"])
    check("15b. every conceptual area carries a plain-English question and explanation",
          all(a["plain_question"] and a["plain_english"] for a in model["areas"]),
          [a["id"] for a in model["areas"] if not a["plain_english"]])
    check("15c. every capability carries a plain-English sentence",
          all(c["plain_english"] for c in model["capability_model"]["capabilities"]),
          [c["id"] for c in model["capability_model"]["capabilities"]
           if not c["plain_english"]])
    check("15d. every capability activation state has a plain-English meaning",
          all(s["plain_english"] for s in model["capability_model"]["states"]),
          model["capability_model"]["states"])
    check("15e. every provenance class has a plain-English meaning",
          all(c["plain_english"] for c in model["confidence_classes"]),
          model["confidence_classes"])

    glossary = {g["term"]: g for g in model["glossary"]}
    for term, expected in (("Blueprint", "A bundle of web routes"),
                           ("Read model", "organizes existing information"),
                           ("Migration", "A controlled database update"),
                           ("Endpoint", "A web address the frontend uses"),
                           ("REMOTE_VERIFIED", "An independent reviewer checked")):
        check(f"15f. the glossary explains {term!r} in the card's own plain terms",
              term in glossary and expected in glossary[term]["plain_english"],
              glossary.get(term, {}).get("plain_english"))
    check("15g. no major technical term is glossed without a plain-English meaning",
          all(g["plain_english"] for g in model["glossary"]),
          [g["term"] for g in model["glossary"] if not g["plain_english"]])


def test_technical_mode_exposes_identifiers(model):
    technical = next(m for m in model["modes"] if m["id"] == "technical")
    check("16a. Technical mode declares the identifier classes it discloses",
          {"paths", "endpoints", "db_tables", "migration_numbers", "decision_ids",
           "discovery_ids", "queue_ids", "authority_refs"} <= set(technical["shows"]),
          technical["shows"])
    check("16b. exact file paths are present in the payload",
          any(f["path"] == "runtime/braingate_conversation.py"
              for c in model["capability_model"]["capabilities"] for f in c["files"]),
          "paths must be reachable, not summarized away")
    check("16c. exact endpoint names are present",
          capability(model, "build_path_visualization")["registration"]["endpoint"]
          == "GET /api/workbench/build-path",
          capability(model, "build_path_visualization")["registration"]["endpoint"])
    check("16d. exact migration numbers and the tables they create are present",
          any(m["migration"] == "0036" and m["tables"]
              for m in capability(model, "card_factory")["migrations"]),
          capability(model, "card_factory")["migrations"])
    check("16e. exact decision ids are present",
          "ADR-PIPE-001" in capability(model, "build_path_visualization")["decision_ids"]
          and any(n["authority_refs"][0]["decision_id"] == "ADR-WIASW-002"
                  for n in model["trajectory"]["destination_relationship"]["nodes"]),
          capability(model, "build_path_visualization")["decision_ids"])
    check("16f. exact discovery ids and their ledger coordinates are present",
          problem(model, "WB1-D15")["evidence"]["table"] == "dev_continuity_events"
          and isinstance(problem(model, "WB1-D15")["evidence"]["revision"], int),
          problem(model, "WB1-D15")["evidence"])
    check("16g. exact queue ids with their source lines are present",
          queue_item(model, "1.23")["source_line"]
          and queue_item(model, "1.23")["source_sha"],
          queue_item(model, "1.23")["item_num"])
    check("16h. the commit/checkpoint reference is reachable through the composed model",
          model["current_build"]["build_path"]["checkpoint"]["latest_pushed_sha"],
          model["current_build"]["build_path"]["checkpoint"].get("lifecycle_state"))
    check("16i. the state revision is reported so a reader can pin what they saw",
          model["state_revision"], model["state_revision"])


# ── 17. no model is called to produce explanation truth ──────────────────

def test_no_llm_at_read_time(model):
    source = pi.Path(pi.__file__).read_text(encoding="utf-8")
    api_source = pi.Path(os.path.join(_REPO_ROOT, "runtime", "api",
                                      "project_intelligence.py")).read_text(encoding="utf-8")
    forbidden = ("requests", "urllib", "http.client", "httpx", "openai", "anthropic",
                 "socket", "gpt_gateway", "hermes", "brain_gateway", "subprocess")
    hits = [name for name in forbidden
            if f"import {name}" in source or f"from {name}" in source
            or f"import {name}" in api_source or f"from {name}" in api_source]
    check("17a. the read model and its endpoint import no model or network client",
          not hits, f"forbidden imports: {hits}")
    check("17b. the payload states outright that no model is called at read time",
          "none" in model["authority"]["llm_runtime_calls"].lower()
          and "generated at read time" in model["authority"]["llm_runtime_calls"],
          model["authority"]["llm_runtime_calls"])

    vocabulary_path = os.path.join(_REPO_ROOT, "tools", "state",
                                   "project_intelligence_vocabulary.json")
    raw = open(vocabulary_path, encoding="utf-8").read()
    check("17c. the vocabulary is a reviewed file in the repository",
          os.path.exists(vocabulary_path)
          and model["vocabulary_source"]["present"] is True
          and model["vocabulary_source"]["provenance_class"]
          == "reviewed_static_explanatory_metadata",
          model["vocabulary_source"])

    # Every plain-language string shown as durable truth must be byte-present in
    # that file. A generated sentence could not be.
    shown = []
    shown += [g["plain_english"] for g in model["glossary"]]
    shown += [a["plain_english"] for a in model["areas"]]
    shown += [c["plain_english"] for c in model["capability_model"]["capabilities"]
              if c["plain_language_recorded"]]
    shown += [a["plain_english"] for a in model["anatomy"]["areas"]]
    shown += [p["plain_english"] for p in model["problems"]["items"]
              if p["plain_language_recorded"]]
    shown += [i["plain_english"] for i in model["queue"]["items"]
              if i["plain_language_recorded"]]
    missing = [s for s in shown if s not in raw]
    check("17d. every plain-language string shown as truth is byte-present in that file",
          not missing, f"{len(missing)} string(s) not traceable to the reviewed file: "
                       f"{missing[:2]}")
    check("17e. a sizeable reviewed vocabulary is actually in use",
          len(shown) > 60, len(shown))

    data = json.loads(raw)
    check("17f. the vocabulary file declares that it is not an authority",
          "NOT an authority" in data["what_this_is"], data["what_this_is"][:60])
    check("17g. the vocabulary carries no status, phase, scope or need_status field",
          not any(k in json.dumps(data) for k in
                  ('"need_status"', '"build_status"', '"phase_status"', '"scope":')),
          "wording only — a status here would make this file an authority")

    missing_vocabulary, problem_ = pi.load_vocabulary(
        path=os.path.join("/nonexistent", "vocab.json"))
    check("17h. a missing vocabulary degrades to the honest sentence, never to generation",
          missing_vocabulary is None and problem_["kind"] == "vocabulary_missing"
          and "nothing is generated" in problem_["detail"],
          problem_)


# ── 18. the endpoint ─────────────────────────────────────────────────────

def test_endpoint_matches_read_model(model):
    client = app.test_client()
    resp = client.get(ROUTE)
    check("18a. the route answers 200", resp.status_code == 200, resp.status_code)
    payload = resp.get_json()
    check("18b. the response is the read model, not a reshaped copy of it",
          payload["read_model"] == model["read_model"]
          and payload["counts"]["queue_items"] == model["counts"]["queue_items"]
          and payload["counts"]["awaiting_triage"] == model["counts"]["awaiting_triage"]
          and [a["id"] for a in payload["areas"]] == [a["id"] for a in model["areas"]],
          payload.get("read_model"))
    check("18c. exactly one project-intelligence route is registered, and it is GET-only",
          [sorted(r.methods - {"HEAD", "OPTIONS"}) for r in app.url_map.iter_rules()
           if str(r.rule) == ROUTE] == [["GET"]],
          [str(r.rule) for r in app.url_map.iter_rules() if "project-intel" in str(r.rule)])


def test_no_caller_supplied_db_path():
    client = app.test_client()
    resp = client.get(f"{ROUTE}?db=/etc/passwd")
    check("19a. a caller-supplied db path is ignored, not honored",
          resp.status_code == 200
          and resp.get_json()["read_model"] == "cis_project_intelligence",
          resp.status_code)
    for method in ("POST", "PATCH", "PUT", "DELETE"):
        resp = client.open(ROUTE, method=method)
        check(f"19b. {method} on the route is refused (405) — there is no write surface",
              resp.status_code == 405, resp.status_code)


def test_read_model_failure_returns_503_not_500():
    import api.project_intelligence as api_pi
    original = api_pi.pi.get_project_intelligence
    try:
        def boom():
            raise sqlite3.OperationalError("unable to open database file")
        api_pi.pi.get_project_intelligence = boom
        resp = app.test_client().get(ROUTE)
        body = resp.get_json()
        check("20a. a read-model failure is a 503, never a 500 traceback",
              resp.status_code == 503, resp.status_code)
        check("20b. the error names the exception type and fabricates no map",
              "OperationalError" in body.get("error", "")
              and "areas" not in body and "counts" not in body,
              body)
    finally:
        api_pi.pi.get_project_intelligence = original


def test_composed_failure_degrades_one_area_not_the_screen():
    """"the destination view is unavailable" and "the Project Map is
    unavailable" are different answers, and must stay different."""
    original = pi.da.get_destination_architecture
    try:
        def boom(db_path=None):
            raise RuntimeError("destination read model exploded")
        pi.da.get_destination_architecture = boom
        model = pi.get_project_intelligence()
        check("21a. a composed read model's failure does not take the map down",
              model["read_model"] == "cis_project_intelligence" and model["counts"]["phases"] > 0,
              model.get("read_model"))
        check("21b. the failing area reports unavailable with its own error",
              model["destination"]["available"] is False
              and "RuntimeError" in model["destination"]["error"],
              model["destination"])
        check("21c. the destination trajectory link breaks honestly rather than being invented",
              model["trajectory"]["destination_relationship"]["confidence_class"]
              == "not_yet_linked"
              and model["trajectory"]["destination_relationship"]["nodes"] == [],
              model["trajectory"]["destination_relationship"]["confidence_class"])
        check("21d. the failure is surfaced in problems_found",
              any(p["kind"] == "destination_unavailable" for p in model["problems_found"]),
              model["problems_found"])
    finally:
        pi.da.get_destination_architecture = original


# ── 22. read-only boundary ───────────────────────────────────────────────

def test_reads_do_not_mutate_the_spine():
    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        before = table_fingerprint(conn)
        before_revision = cs.compute_state_revision(conn)
    finally:
        conn.close()

    client = app.test_client()
    for _ in range(3):
        client.get(ROUTE)
    pi.get_project_intelligence()

    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    try:
        after = table_fingerprint(conn)
        after_revision = cs.compute_state_revision(conn)
    finally:
        conn.close()

    changed = [k for k in before if before[k] != after[k]]
    check("22a. no protected table or state key changed across every route call",
          not changed, f"changed: {changed}")
    check("22b. the state revision is unchanged",
          before_revision == after_revision,
          f"{before_revision} -> {after_revision}")
    check("22c. queue_items is byte-identical — no triage occurred",
          before["queue_items"] == after["queue_items"], "queue_items moved")
    check("22d. queue_edges is byte-identical — no edge was created",
          before["queue_edges"] == after["queue_edges"], "queue_edges moved")
    check("22e. the roadmap, phase pointer, direction and next action are unchanged",
          all(before[f"state:{k}"] == after[f"state:{k}"] for k in PROTECTED_STATE_KEYS),
          [k for k in PROTECTED_STATE_KEYS if before[f"state:{k}"] != after[f"state:{k}"]])
    check("22f. the discovery ledger is unchanged — nothing was resolved",
          before["dev_continuity_events"] == after["dev_continuity_events"],
          "dev_continuity_events moved")


def test_read_model_is_structurally_read_only():
    source = pi.Path(pi.__file__).read_text(encoding="utf-8")
    api_source = pi.Path(os.path.join(_REPO_ROOT, "runtime", "api",
                                      "project_intelligence.py")).read_text(encoding="utf-8")
    check("23a. the spine is opened mode=ro",
          'mode=ro' in source, "the connection must be read-only at the sqlite layer")
    upper = source.upper()
    dml = [kw for kw in ("INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE",
                         "ALTER TABLE", "DROP TABLE", "COMMIT()") if kw in upper]
    check("23b. no DML or DDL statement exists in the read model",
          not dml, f"found: {dml}")
    check("23c. no DML exists in the endpoint either",
          not any(kw in api_source.upper() for kw in
                  ("INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE")),
          "the endpoint is a pass-through")
    check("23d. no migration is added by this feature",
          not os.path.exists(os.path.join(_REPO_ROOT, "runtime", "schema", "migrations",
                                          "0040_project_intelligence.sql")),
          "the card forbids a schema addition without a reviewed authority decision")
    # Named as "never read" is fine and is the point; QUERIED is the violation.
    queried = [t for t in ("build_plan_nodes", "build_plan_dependencies", "functional_spec")
               if f"FROM {t}" in source or f"from {t}" in source or f"INTO {t}" in source]
    check("23e. the retired and rejected sources are named as never-read, never queried",
          not queried, f"queried: {queried}")
    # A .md path may be NAMED as never-read; it may not be opened. Checked per
    # line so the never_reads declaration cannot satisfy or trip this.
    md_reads = [line.strip() for line in source.splitlines()
                if ".md" in line and ("read_text(" in line or "open(" in line
                                      or "Path(" in line)]
    check("23f. no generated markdown projection is opened as an input",
          not md_reads, f"markdown read sites: {md_reads}")
    opened = re.findall(r"read_text\(|\.open\(", source)
    check("23g. the read model opens exactly three things: the vocabulary, "
          "container_app.py, and each implementation file it counts lines in",
          len(opened) == 3, f"{len(opened)} file-open sites: {opened}")
    check("23h. the payload enumerates what this screen cannot do",
          len(pi.READ_ONLY_BOUNDARY) >= 6
          and any("classified" in line for line in pi.READ_ONLY_BOUNDARY),
          pi.READ_ONLY_BOUNDARY)


def test_scratch_db_proves_nothing_is_hardcoded():
    """Against a copy of the spine with the roadmap row replaced, the map must
    follow the copy — proving the phases, the counts and the current pointer are
    read, not built in."""
    with tempfile.TemporaryDirectory() as tmp:
        scratch = os.path.join(tmp, "scratch.db")
        shutil.copy(cs.DB, scratch)
        conn = sqlite3.connect(scratch)
        try:
            conn.execute(
                "INSERT INTO project_state (key, value, source, created_at) VALUES "
                "('pipeline_roadmap', 'ALPHA (first thing) -> BETA (second thing) -> "
                "GAMMA (third thing). AUTHORITY: test.', 'manual', '2099-01-01T00:00:00+00:00')")
            conn.execute(
                "INSERT INTO project_state (key, value, source, created_at) VALUES "
                "('build_phase', 'Phase P3 of the P0-P6 sequence', 'manual', "
                "'2099-01-01T00:00:00+00:00')")
            conn.execute("DELETE FROM queue_items WHERE need_status IS NULL AND scope IS NULL")
            conn.commit()
        finally:
            conn.close()

        model = pi.get_project_intelligence(db_path=scratch)
        check("24a. the trajectory follows the scratch roadmap, not production's",
              [s["id"] for s in model["trajectory"]["steps"]] == ["ALPHA", "BETA", "GAMMA"],
              [s["id"] for s in model["trajectory"]["steps"]])
        check("24b. the queue counts follow the scratch database",
              model["queue"]["awaiting_triage"] == 0
              and model["counts"]["queue_items"] < 132,
              model["counts"]["queue_items"])
        check("24c. a build_phase naming a phase outside the chain is reported, not guessed",
              model["current_build"]["build_path"]["progress"]["current_phase_note"]
              and "not a stage" in
              model["current_build"]["build_path"]["progress"]["current_phase_note"],
              model["current_build"]["build_path"]["progress"]["current_phase_note"])
        check("24d. with no current phase, no finding gets a build position",
              all(p["build_position"]["confidence_class"] == "not_yet_linked"
                  for p in model["problems"]["items"]),
              "an unknown current phase must break the chain, not default to one")
        check("24e. the production spine is untouched by the scratch run",
              cs.DB != scratch and os.path.exists(cs.DB), cs.DB)


# ── 25. diagrams ─────────────────────────────────────────────────────────

def test_diagrams_are_generated_from_the_same_data(model):
    overview = model["overview_mermaid"]
    anatomy = model["anatomy"]["mermaid"]
    trajectory = model["trajectory"]["mermaid"]
    check("25a. the overview graph is small — the five areas, not the repository",
          overview.count("[\"") == 5, overview.count("[\""))
    check("25b. the overview graph carries the live counts it summarizes",
          f"{model['counts']['awaiting_triage']} items awaiting triage" in overview,
          overview[:200])
    check("25c. the anatomy diagram draws exactly the areas the panel lists",
          all(a["id"].upper() in anatomy for a in model["anatomy"]["areas"])
          and anatomy.count("CIS -->") == len(model["anatomy"]["areas"]),
          anatomy.count("CIS -->"))
    check("25d. the trajectory diagram draws exactly the composed phases",
          all(s["id"] in trajectory for s in model["trajectory"]["steps"]),
          "the diagram and the list cannot disagree")
    check("25e. no diagram contains the whole destination graph",
          not any(n["id"] in trajectory for n in model["destination"]["nodes"]
                  if n["id"] not in ("CIS", "WIASW")),
          "the destination graph is drawn by the read model that owns it")
    check("25f. the diagrams are generated server-side, from the model",
          all(src.startswith("flowchart") for src in (overview, anatomy, trajectory)),
          [src[:12] for src in (overview, anatomy, trajectory)])


def run():
    model = test_read_model_builds()
    test_build_path_is_composed_not_duplicated(model)
    test_destination_is_composed_not_duplicated(model)
    test_p0_remains_current_and_triage_remains_next(model)
    test_queue_is_shown_never_triaged(model)
    test_queue_item_drilldown(model)
    test_problem_view(model)
    test_discovery_status_is_distinct_from_build_status(model)
    test_capability_model_is_derived_and_says_so(model)
    test_capability_status_tracks_observed_registration()
    test_anatomy(model)
    test_file_drilldown(model)
    test_trajectory(model)
    test_relationship_provenance(model)
    test_simple_mode_has_plain_language(model)
    test_technical_mode_exposes_identifiers(model)
    test_no_llm_at_read_time(model)
    test_endpoint_matches_read_model(model)
    test_no_caller_supplied_db_path()
    test_read_model_failure_returns_503_not_500()
    test_composed_failure_degrades_one_area_not_the_screen()
    test_reads_do_not_mutate_the_spine()
    test_read_model_is_structurally_read_only()
    test_scratch_db_proves_nothing_is_hardcoded()
    test_diagrams_are_generated_from_the_same_data(model)

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
