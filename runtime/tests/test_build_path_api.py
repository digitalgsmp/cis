#!/usr/bin/env python3
"""test_build_path_api.py — behavioral tests for the Workbench Build Path
read model (tools/state/build_path.py) and its endpoint
(runtime/api/build_path.py, GET /api/workbench/build-path).

Two kinds of test, deliberately:

  1. Against the LIVE spine, opened read-only. These prove the read model
     can actually be built from the current authority state and that it
     reports that state honestly — P0 active/blocked rather than complete,
     queue triage next, D15 blocking, D16/D17 resolved, the migration
     unlock points and queue hooks on the phases the roadmap attaches them
     to. A card assertion that passes only against a hand-built fixture
     would prove nothing about the project's real state, which is the one
     thing this screen exists to show.

  2. Against a SCRATCH database whose pipeline_roadmap row is deliberately
     DIFFERENT from production's. These prove the phase sequence is parsed
     from project_state.pipeline_roadmap rather than hardcoded in the
     module — the failure mode a visualization like this invites.

Nothing here writes to the live spine: the read model opens it with
sqlite3's mode=ro URI, and a row-count/revision comparison before and
after hitting every route asserts that outright.

Run: python3 runtime/tests/test_build_path_api.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_HERE, ".."))                 # runtime/
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))  # canonical_state, build_path
sys.path.insert(0, _REPO_ROOT)                                 # tools.development

os.environ.setdefault("CIS_PIPELINE_API_KEY", "")

import build_path as bp  # noqa: E402
import canonical_state as cs  # noqa: E402

from container_app import app  # noqa: E402

results = []


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def phase(model, phase_id):
    return next((p for p in model["phases"] if p["id"] == phase_id), None)


def migration_rules(ph):
    return {m["migration"]: m for m in (ph or {}).get("migrations", [])}


def hook_nums(ph):
    return [h["item_num"] for h in (ph or {}).get("queue_hooks", [])]


def discovery_by_id(records, discovery_id):
    return next((d for d in records if d["id"] == discovery_id), None)


# ── 1. live authority state ──────────────────────────────────────────────

def test_read_model_builds_from_live_authority():
    model = bp.get_build_path()
    check("1a. read model builds from the current authority state",
          model.get("read_model") == "cis_build_path" and model.get("phases"),
          model.get("read_model"))
    check("1b. a state revision is reported alongside it",
          isinstance(model.get("state_revision"), str) and model["state_revision"],
          model.get("state_revision"))
    check("1c. the roadmap row it parsed is named and quoted, not paraphrased",
          model["roadmap_source"]["state_key"] == "pipeline_roadmap"
          and bool(model["roadmap_source"]["raw"]),
          model["roadmap_source"]["state_key"])
    check("1d. the parse consumed every '->' segment (no unparsed note)",
          model["roadmap_source"]["parse_note"] is None,
          model["roadmap_source"]["parse_note"])
    return model


def test_p0_is_active_and_blocked_not_complete(model):
    p0 = phase(model, "P0")
    check("2a. P0 is present in the parsed sequence", p0 is not None)
    check("2b. P0 is the current phase", p0 and p0["is_current"], p0 and p0["is_current"])
    check("2c. P0 status is 'active', NOT 'complete'",
          p0 and p0["status"] == "active", p0 and p0["status"])
    check("2d. P0 is marked blocked", p0 and p0["blocked"] is True, p0 and p0["blocked"])
    check("2e. P0's display label says active / blocked",
          p0 and p0["status_label"] == "active / blocked", p0 and p0["status_label"])
    check("2f. the current pointer agrees with the phase list",
          model["current"] and model["current"]["phase_id"] == "P0"
          and model["current"]["blocked"] is True,
          model.get("current"))
    check("2g. no phase anywhere is reported complete while P0 is current",
          all(p["status"] != "complete" for p in model["phases"]),
          [p["id"] for p in model["phases"] if p["status"] == "complete"])
    check("2h. P0's current-phase claim carries its project_state evidence",
          model["current"]["evidence"]["state_key"] == "build_phase"
          and "P0" in (model["current"]["evidence"]["value"] or ""),
          model["current"]["evidence"]["state_key"])
    check("2i. P0 shows migrations 0035 and 0038 applied, 'applied' observed from the schema",
          migration_rules(p0).get("0035", {}).get("applied") is True
          and migration_rules(p0).get("0038", {}).get("applied") is True,
          {k: v.get("applied") for k, v in migration_rules(p0).items()})


def test_queue_triage_is_next(model):
    triage = phase(model, "QUEUE_TRIAGE")
    check("3a. QUEUE TRIAGE is the stage after P0",
          triage is not None and triage["order"] == phase(model, "P0")["order"] + 1,
          triage and triage["order"])
    check("3b. QUEUE TRIAGE status is 'next'",
          triage and triage["status"] == "next", triage and triage["status"])
    check("3c. the next pointer agrees with the phase list",
          model["next"] and model["next"]["phase_id"] == "QUEUE_TRIAGE",
          model.get("next"))
    check("3d. triage shows the live unclassified queue_items count",
          triage["queue_classification"]["unclassified"] ==
          model["queue"]["unclassified"] and model["queue"]["unclassified"] > 0,
          model["queue"]["unclassified"])
    constraints = {c["constraint"]: c for c in triage["constraints"]}
    check("3e. triage notes 'bounded mechanical classification', quoted from ADR-PIPE-006",
          "bounded mechanical classification" in constraints
          and constraints["bounded mechanical classification"]["source"] == "ADR-PIPE-006",
          list(constraints))
    check("3f. triage notes 'no redesign', quoted from ADR-PIPE-006",
          "no redesign" in constraints
          and "NO item redesign" in constraints["no redesign"]["quote"],
          list(constraints))


def test_later_phases_are_pending(model):
    later = [p for p in model["phases"] if p["order"] > phase(model, "QUEUE_TRIAGE")["order"]]
    check("4a. every stage after triage is pending",
          later and all(p["status"] == "pending" for p in later),
          {p["id"]: p["status"] for p in later})
    check("4b. the full P0..P6 sequence with triage and the Tier-0 card is present, in order",
          [p["id"] for p in model["phases"]] ==
          ["P0", "QUEUE_TRIAGE", "P1", "P2", "TIER_0_TRUST", "P3", "P4", "P5", "P6"],
          [p["id"] for p in model["phases"]])


def test_p1_p2_descriptions(model):
    p1, p2 = phase(model, "P1"), phase(model, "P2")
    check("5a. P1 describes the Layer-2 run-plane read model and /api/workbench/runs",
          "run-plane" in p1["description"] and "/api/workbench/runs" in p1["description"],
          p1["description"])
    check("5b. P2 describes the Slice 2 clarified direction",
          "clarified direction" in p2["description"], p2["description"])


def test_migration_unlock_points(model):
    p3, p4 = phase(model, "P3"), phase(model, "P4")
    m3, m4 = migration_rules(p3), migration_rules(p4)
    check("6a. P3 carries migration 0036 as its unlock point", "0036" in m3, list(m3))
    check("6b. P3's 0036 rule is quoted from the roadmap authority",
          "0036" in m3 and ("ADR-PIPE-001" in m3["0036"]["source_quote"]
                            or "pipeline_roadmap" in m3["0036"]["source_quote"]),
          m3.get("0036", {}).get("source_quote"))
    check("6c. 0036 is reported NOT applied (observed from the live schema)",
          m3.get("0036", {}).get("applied") is False, m3.get("0036", {}).get("applied"))
    check("6d. P4 carries migration 0037 as its unlock point", "0037" in m4, list(m4))
    check("6e. 0037 is reported NOT applied (observed from the live schema)",
          m4.get("0037", {}).get("applied") is False, m4.get("0037", {}).get("applied"))
    check("6f. 0036/0037 are not attached to P0 or to any earlier phase",
          all("0036" not in migration_rules(p) and "0037" not in migration_rules(p)
              for p in model["phases"] if p["order"] < p3["order"]),
          [(p["id"], list(migration_rules(p))) for p in model["phases"]])


def test_queue_hooks(model):
    tier0, p4 = phase(model, "TIER_0_TRUST"), phase(model, "P4")
    check("7a. Tier-0 Trust shows queue hooks 0.4 and 0.6",
          hook_nums(tier0) == ["0.4", "0.6"], hook_nums(tier0))
    check("7b. both Tier-0 hooks resolve to real queue_items rows with their own status",
          all(h["found"] and h["title"] and "need_status" in h
              for h in tier0["queue_hooks"]),
          tier0["queue_hooks"])
    check("7c. P4 shows queue hook 1.23 (the end-to-end proof target)",
          "1.23" in hook_nums(p4), hook_nums(p4))
    check("7d. queue 1.23 resolves to its real queue_items row",
          next(h for h in p4["queue_hooks"] if h["item_num"] == "1.23")["found"] is True,
          p4["queue_hooks"])
    check("7e. no queue hook is attached to a phase the roadmap does not name it in",
          hook_nums(phase(model, "P0")) == [] and hook_nums(phase(model, "P1")) == [],
          (hook_nums(phase(model, "P0")), hook_nums(phase(model, "P1"))))


def test_blockers_and_resolved_discoveries(model):
    blockers = model["blockers"]
    d15 = discovery_by_id(blockers, "WB1-D15")
    check("8a. WB1-D15 appears as a blocker", d15 is not None,
          [b["id"] for b in blockers])
    check("8b. WB1-D15's display status is 'blocking'",
          d15 and d15["status"] == "blocking", d15 and d15["status"])
    check("8c. WB1-D15 is unresolved and flagged blocking in the ledger itself",
          d15 and d15["resolved"] is False and d15["blocking"] is True,
          d15 and (d15["resolved"], d15["blocking"]))
    check("8d. every blocker is genuinely unresolved and blocking (nothing padded in)",
          all(b["resolved"] is False and b["blocking"] is True for b in blockers),
          [(b["id"], b["resolved"], b["blocking"]) for b in blockers])

    resolved = model["discoveries"]["resolved"]
    d16 = discovery_by_id(resolved, "WB1-D16")
    d17 = discovery_by_id(resolved, "WB1-D17")
    check("8e. WB1-D16 appears as resolved",
          d16 is not None and d16["status"] == "resolved" and d16["resolved"] is True,
          d16 and d16["status"])
    check("8f. WB1-D17 appears as resolved",
          d17 is not None and d17["status"] == "resolved" and d17["resolved"] is True,
          d17 and d17["status"])
    check("8g. neither D16 nor D17 is also listed as a blocker",
          discovery_by_id(blockers, "WB1-D16") is None
          and discovery_by_id(blockers, "WB1-D17") is None,
          [b["id"] for b in blockers])

    deferred = model["discoveries"]["deferred"]
    d14 = discovery_by_id(deferred, "WB1-D14")
    check("8h. WB1-D14 appears as deferred",
          d14 is not None and d14["status"] == "deferred", d14 and d14["status"])

    p0 = phase(model, "P0")
    check("8i. the discoveries are attached to the current phase and name their task",
          p0["discoveries"]["counts"]["blocking"] == len(blockers)
          and p0["task"] == model["current"]["task"],
          (p0.get("task"), p0["discoveries"]["counts"]))
    check("8j. every display status comes from the declared vocabulary",
          all(d["status"] in model["status_vocabulary"]
              for group in ("blocking", "open", "deferred", "resolved")
              for d in model["discoveries"][group]),
          model["status_vocabulary"])


def test_checkpoint_and_authority(model):
    cp = model["checkpoint"]
    check("9a. the external checkpoint state is reported", cp["present"] is True, cp)
    check("9b. lifecycle_state is passed through from project_state, not recomputed",
          isinstance(cp["lifecycle_state"], str) and cp["lifecycle_state"],
          cp.get("lifecycle_state"))
    check("9c. a pushed SHA is not reported as independently verified unless it matches "
          "latest_remote_verified_sha (ADR-XDEV-001)",
          cp["pushed_sha_is_independently_verified"] ==
          (bool(cp["latest_pushed_sha"])
           and cp["latest_pushed_sha"] == cp["latest_remote_verified_sha"]),
          (cp["latest_pushed_sha"], cp["latest_remote_verified_sha"],
           cp["pushed_sha_is_independently_verified"]))
    check("9d. the checkpoint carries its own scope boundary (never phase completion)",
          "scope_boundary" in cp, list(cp))

    authority = model["authority"]
    check("9e. the authority split names roadmap sequencing and queue work items separately",
          "pipeline_roadmap" in authority["sequencing"]
          and "queue_items" in authority["work_items"],
          authority)
    check("9f. UNIFIED_BUILD_LIST.md is named as a generated projection, not an authority",
          "not an authority" in authority["generated_view"], authority["generated_view"])
    check("9g. build_plan_nodes is named as retired",
          "retired" in authority["retired"], authority["retired"])
    ids = [d["id"] for d in model["decisions"]]
    check("9h. the governing ADR rows travel with the model",
          {"ADR-PIPE-001", "ADR-PIPE-006", "ADR-XDEV-001"}.issubset(set(ids)), ids)


def test_mermaid_is_generated_from_the_same_phases(model):
    mermaid = model["mermaid"]
    check("10a. the Mermaid source is a flowchart", mermaid.startswith("flowchart"),
          mermaid[:40])
    check("10b. every phase in the read model is a node in the diagram",
          all(f'{p["id"]}["' in mermaid for p in model["phases"]),
          [p["id"] for p in model["phases"] if f'{p["id"]}["' not in mermaid])
    check("10c. the diagram wires the phases in the parsed order",
          all(f'{a["id"]} --> {b["id"]}' in mermaid
              for a, b in zip(model["phases"], model["phases"][1:])),
          mermaid)
    check("10d. the blocked current phase is styled as blocked, not as plain active",
          "class P0 blockedPhase" in mermaid, mermaid)
    check("10e. each blocker appears as a node pointing at the current phase",
          all(f'|blocks closeout| {model["current"]["phase_id"]}' in mermaid
              for _ in model["blockers"]) and (
              "blocks closeout" in mermaid if model["blockers"] else True),
          mermaid)
    check("10f. no unescaped double quote leaked into a node label",
          all(line.count('"') % 2 == 0 for line in mermaid.splitlines()),
          [l for l in mermaid.splitlines() if l.count('"') % 2])
    check("10g. P3's 0036 and P4's 0037 unlock markers are visible in the diagram",
          "migration 0036" in mermaid and "migration 0037" in mermaid, mermaid)
    check("10h. queue hooks 0.4, 0.6 and 1.23 are visible in the diagram",
          "queue 0.4" in mermaid and "queue 0.6" in mermaid and "queue 1.23" in mermaid,
          mermaid)


# ── 2. scratch database: the sequence is parsed, not hardcoded ───────────

SCRATCH_SCHEMA = """
CREATE TABLE queue_items (
    item_num TEXT PRIMARY KEY, tier INTEGER NOT NULL, title TEXT NOT NULL,
    body_md TEXT NOT NULL, form TEXT NOT NULL, scope TEXT, need_status TEXT,
    source_line INTEGER NOT NULL, source_sha TEXT NOT NULL,
    extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
    status_changed_at TEXT, status_changed_by TEXT, check_class TEXT
);
CREATE TABLE queue_item_events (
    id INTEGER PRIMARY KEY, item_num TEXT NOT NULL, field TEXT NOT NULL,
    old_value TEXT, new_value TEXT, changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    changed_by TEXT, evidence TEXT, note TEXT
);
CREATE TABLE queue_edges (
    from_num TEXT NOT NULL, to_num TEXT NOT NULL, kind TEXT NOT NULL,
    evidence TEXT, confidence REAL, extracted_at TEXT
);
CREATE TABLE dev_continuity_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT NOT NULL,
    revision INTEGER NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL,
    actor TEXT NOT NULL, summary TEXT NOT NULL, body TEXT,
    evidence_refs_json TEXT NOT NULL DEFAULT '[]',
    source_refs_json TEXT NOT NULL DEFAULT '[]',
    against_revision INTEGER, request_id TEXT, request_hash TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE session_closeouts (
    id INTEGER PRIMARY KEY, started_at TEXT NOT NULL, completed_at TEXT,
    status TEXT NOT NULL, commit_hash TEXT
);
CREATE TABLE project_decisions (
    id TEXT PRIMARY KEY, label TEXT NOT NULL, decision TEXT NOT NULL,
    reason TEXT, status TEXT NOT NULL DEFAULT 'DECIDED', decided_at TEXT NOT NULL,
    superseded_by TEXT
);
CREATE TABLE project_state (
    id INTEGER PRIMARY KEY, key TEXT NOT NULL, value TEXT NOT NULL,
    source TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE open_questions (
    id TEXT PRIMARY KEY, question TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'OPEN',
    resolution TEXT, opened_at TEXT NOT NULL, resolved_at TEXT
);
CREATE TABLE active_blockers (
    id TEXT PRIMARY KEY, description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ACTIVE',
    resolution TEXT, created_at TEXT NOT NULL, resolved_at TEXT
);
CREATE TABLE next_actions (
    id TEXT PRIMARY KEY, tier TEXT, description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', depends_on TEXT,
    created_at TEXT NOT NULL, updated_at TEXT
);
CREATE TABLE dev_pivot_status (
    id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
    category TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'LIVE',
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

# Deliberately NOT production's roadmap: a different number of stages, a
# different current phase, a different migration attached to a different
# phase, and a queue hook on a stage production does not have one on.
SCRATCH_ROADMAP = (
    "P0 (stand up the thing) -> SHAKEDOWN (tidy the inputs) -> "
    "P1 (first real surface; unlocks migration 0036) -> "
    "P2 (second surface, queue 9.1). CONSTRAINTS: P1 before P2. "
    "AUTHORITY: project_decisions ADR-PIPE-001."
)
SCRATCH_ADR001 = (
    "Canonical forward sequence. MIGRATION UNLOCK POINTS: 0035 at P0; "
    "0036 not before P1. Nothing else."
)


def make_scratch_db():
    tmp = tempfile.mkdtemp(prefix="cis_build_path_test_")
    path = os.path.join(tmp, "scratch.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCRATCH_SCHEMA)
    conn.executemany(
        "INSERT INTO project_state (key, value, source, created_at) VALUES (?,?,?,?)",
        [
            ("pipeline_roadmap", SCRATCH_ROADMAP, "manual", "2026-01-01T00:00:00+00:00"),
            ("build_phase", "Scratch build. Phase P1 of the sequence is underway.",
             "manual", "2026-01-02T00:00:00+00:00"),
            ("current_direction", "scratch direction", "manual", "2026-01-02T00:00:00+00:00"),
            ("next_action", "scratch next action", "manual", "2026-01-02T00:00:00+00:00"),
            ("current_queue_item", "9.1", "manual", "2026-01-02T00:00:00+00:00"),
        ],
    )
    conn.execute(
        "INSERT INTO project_decisions (id, label, decision, reason, decided_at) "
        "VALUES ('ADR-PIPE-001', 'scratch sequence', ?, '', '2026-01-01T00:00:00+00:00')",
        (SCRATCH_ADR001,),
    )
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, scope, "
        "need_status, source_line, source_sha) VALUES "
        "('9.1', 9, 'scratch hooked item', '### 9.1', 'heading', 'CONTAINER', 'OPEN', 1, 'x')"
    )
    conn.execute(
        "INSERT INTO queue_items (item_num, tier, title, body_md, form, "
        "source_line, source_sha) VALUES "
        "('9.2', 9, 'scratch unclassified item', '### 9.2', 'heading', 2, 'x')"
    )
    conn.commit()
    return tmp, path, conn


def test_sequence_is_parsed_from_the_roadmap_row_not_hardcoded():
    tmp, path, conn = make_scratch_db()
    try:
        model = bp.get_build_path(db_path=path)
        ids = [p["id"] for p in model["phases"]]
        check("11a. the parsed sequence follows the scratch roadmap row, not production's",
              ids == ["P0", "SHAKEDOWN", "P1", "P2"], ids)
        check("11b. the current phase follows the scratch build_phase row",
              model["current"]["phase_id"] == "P1", model["current"])
        check("11c. phases before the current one are 'complete'",
              [p["status"] for p in model["phases"][:2]] == ["complete", "complete"],
              [p["status"] for p in model["phases"]])
        check("11d. the stage after the current one is 'next'",
              model["next"]["phase_id"] == "P2", model["next"])
        check("11e. an unlock point lands on the phase THIS roadmap names, not P3",
              "0036" in migration_rules(phase(model, "P1"))
              and all("0036" not in migration_rules(p)
                      for p in model["phases"] if p["id"] != "P1"),
              [(p["id"], list(migration_rules(p))) for p in model["phases"]])
        check("11f. a queue hook lands on the phase THIS roadmap names",
              hook_nums(phase(model, "P2")) == ["9.1"], hook_nums(phase(model, "P2")))
        check("11g. the hooked item resolves against this database's queue_items",
              phase(model, "P2")["queue_hooks"][0]["title"] == "scratch hooked item",
              phase(model, "P2")["queue_hooks"][0])
        check("11h. unclassified counts come from this database, not production's",
              model["queue"]["total_items"] == 2 and model["queue"]["unclassified"] == 1,
              model["queue"])
        check("11i. the constraints tail after the last stage is preserved verbatim",
              "P1 before P2" in (model["roadmap_source"]["constraints_text"] or ""),
              model["roadmap_source"]["constraints_text"])
        check("11j. the Mermaid diagram follows the scratch sequence too",
              'SHAKEDOWN["' in model["mermaid"]
              and "P0 --> SHAKEDOWN" in model["mermaid"]
              and "TIER_0_TRUST" not in model["mermaid"],
              model["mermaid"])
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_roadmap_row_is_reported_not_invented():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute("DELETE FROM project_state WHERE key='pipeline_roadmap'")
        conn.commit()
        model = bp.get_build_path(db_path=path)
        check("12a. with no pipeline_roadmap row, no phases are invented",
              model["phases"] == [], model["phases"])
        check("12b. the absence is stated in a parse note",
              "no pipeline_roadmap value" in (model["roadmap_source"]["parse_note"] or ""),
              model["roadmap_source"]["parse_note"])
        check("12c. current and next pointers are null rather than guessed",
              model["current"] is None and model["next"] is None,
              (model["current"], model["next"]))
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_unknown_current_phase_is_reported_not_guessed():
    tmp, path, conn = make_scratch_db()
    try:
        conn.execute("UPDATE project_state SET value='Scratch build, no phase named here.' "
                     "WHERE key='build_phase'")
        conn.commit()
        model = bp.get_build_path(db_path=path)
        check("13a. a build_phase row naming no phase yields no current pointer",
              model["current"] is None, model["current"])
        check("13b. the reason is stated rather than defaulting to the first phase",
              "names no 'Phase P" in (model["progress"]["current_phase_note"] or ""),
              model["progress"]["current_phase_note"])
        check("13c. with no current phase, nothing is claimed complete or active",
              all(p["status"] == "pending" for p in model["phases"]),
              {p["id"]: p["status"] for p in model["phases"]})
    finally:
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


# ── 3. the endpoint ──────────────────────────────────────────────────────

def test_endpoint_matches_the_read_model():
    client = app.test_client()
    resp = client.get("/api/workbench/build-path")
    check("14a. GET /api/workbench/build-path returns 200", resp.status_code == 200,
          resp.status_code)
    body = resp.get_json()
    direct = bp.get_build_path()
    check("14b. the route returns the read model, not a second reconstruction of it",
          body["read_model"] == direct["read_model"]
          and [p["id"] for p in body["phases"]] == [p["id"] for p in direct["phases"]]
          and body["mermaid"] == direct["mermaid"],
          body.get("read_model"))
    check("14c. the route is registered exactly once and only as GET",
          sorted(sorted(r.methods - {"HEAD", "OPTIONS"})
                 for r in app.url_map.iter_rules()
                 if str(r.rule) == "/api/workbench/build-path") == [["GET"]],
          [sorted(r.methods) for r in app.url_map.iter_rules()
           if str(r.rule) == "/api/workbench/build-path"])
    check("14d. this feature adds no mutating route to the app",
          not any("build-path" in str(r.rule) and (r.methods - {"GET", "HEAD", "OPTIONS"})
                  for r in app.url_map.iter_rules()),
          [str(r.rule) for r in app.url_map.iter_rules() if "build-path" in str(r.rule)])


def test_no_caller_supplied_db_path_accepted():
    """A client must not be able to point the Workbench at another file."""
    client = app.test_client()
    baseline = client.get("/api/workbench/build-path").get_json()
    forged = client.get("/api/workbench/build-path?db=/tmp/nope.db&db_path=/tmp/nope.db")
    check("15a. a db query param is ignored, not honored as a path override",
          forged.status_code == 200
          and [p["id"] for p in forged.get_json()["phases"]] ==
          [p["id"] for p in baseline["phases"]],
          forged.status_code)


def test_read_model_failure_returns_503_not_500():
    orig = cs.DB
    cs.DB = "/nonexistent/path/definitely-not-a-spine.db"
    try:
        client = app.test_client()
        resp = client.get("/api/workbench/build-path")
        check("16a. an unreachable spine is a 503, not a 500 traceback",
              resp.status_code == 503, resp.status_code)
        body = resp.get_json()
        check("16b. the 503 body carries an error naming the exception type",
              "error" in body and "build path read model unavailable" in body["error"],
              body)
        check("16c. the failure response contains no fabricated phases",
              "phases" not in body, list(body))
    finally:
        cs.DB = orig


def test_reads_do_not_mutate_the_spine():
    conn = sqlite3.connect(f"file:{cs.DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        before_counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                         for t in cs.AUTHORITY_TABLES}
        before_rev = cs.compute_state_revision(conn)

        client = app.test_client()
        client.get("/api/workbench/build-path")
        client.get("/api/workbench/build-path")
        bp.get_build_path()

        after_counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                        for t in cs.AUTHORITY_TABLES}
        after_rev = cs.compute_state_revision(conn)
        check("17a. no authority table row count changed after repeated reads",
              before_counts == after_counts,
              f"before={before_counts} after={after_counts}")
        check("17b. the state revision is unchanged by viewing the build path",
              before_rev == after_rev, f"before={before_rev} after={after_rev}")
    finally:
        conn.close()


def test_read_model_connection_is_read_only():
    """Not merely 'we only wrote SELECTs' — the connection itself refuses."""
    conn = bp._connect()
    try:
        failed = False
        try:
            conn.execute("INSERT INTO project_state (key, value, source, created_at) "
                         "VALUES ('x','x','x','x')")
        except sqlite3.OperationalError:
            failed = True
        check("18a. the read model's own connection rejects a write outright", failed)
    finally:
        conn.close()


def test_retired_and_generated_sources_are_not_used_as_authority():
    """ADR-PIPE-006's authority split, asserted against the module itself:
    the generated build list is a projection and build_plan_nodes is
    retired, so neither may be an input to this read model."""
    source = bp.Path(bp.__file__).read_text(encoding="utf-8")
    check("19a. build_plan_nodes is never queried",
          "FROM build_plan_nodes" not in source and "build_plan_nodes," not in source,
          "build_plan_nodes must not be a live planning source")
    check("19b. the only files the read model opens are migration SQL files",
          source.count("read_text(") == 1
          and "MIGRATIONS_DIR.glob" in source,
          f"read_text( occurrences: {source.count('read_text(')}")
    check("19c. no generated markdown projection is opened",
          ".md\"" not in source and ".md'" not in source,
          "no generated .md path may be read as an input")
    check("19d. no INSERT/UPDATE/DELETE statement exists in the read model",
          not any(kw in source.upper() for kw in
                  ("INSERT INTO", "UPDATE ", "DELETE FROM")),
          [kw for kw in ("INSERT INTO", "UPDATE ", "DELETE FROM") if kw in source.upper()])


def run():
    model = test_read_model_builds_from_live_authority()
    test_p0_is_active_and_blocked_not_complete(model)
    test_queue_triage_is_next(model)
    test_later_phases_are_pending(model)
    test_p1_p2_descriptions(model)
    test_migration_unlock_points(model)
    test_queue_hooks(model)
    test_blockers_and_resolved_discoveries(model)
    test_checkpoint_and_authority(model)
    test_mermaid_is_generated_from_the_same_phases(model)

    test_sequence_is_parsed_from_the_roadmap_row_not_hardcoded()
    test_missing_roadmap_row_is_reported_not_invented()
    test_unknown_current_phase_is_reported_not_guessed()

    test_endpoint_matches_the_read_model()
    test_no_caller_supplied_db_path_accepted()
    test_read_model_failure_returns_503_not_500()
    test_reads_do_not_mutate_the_spine()
    test_read_model_connection_is_read_only()
    test_retired_and_generated_sources_are_not_used_as_authority()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
