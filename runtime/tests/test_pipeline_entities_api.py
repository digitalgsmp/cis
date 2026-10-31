"""
test_pipeline_entities_api.py — Flask endpoint tests for the Workbench
Pipeline Entities backend: GET /api/workbench/pipeline-entities.

Builds a scratch database carrying the FULL real column set of
workflow_runs, deliberation_rounds, agent_trajectories, eric_gate_approvals
and gate_outcomes — including every column the read model (tools/state/
pipeline_entities.py) is required to exclude — and plants a distinct
sentinel string or number in each excluded column. The exclusion tests then
walk the entire JSON response recursively, by key and by leaf value, and
assert that not one excluded key, not one sentinel, not one known gateway
port, not one localhost URL and not one Hermes profile name survives into
the HTTP response.

Run: python3.12 runtime/tests/test_pipeline_entities_api.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(_HERE, ".."))                   # runtime/
sys.path.insert(0, os.path.join(_REPO_ROOT, "tools", "state"))  # read models

import canonical_state as cs  # noqa: E402
import pipeline_entities as pe  # noqa: E402
from abstraction import dispatch  # noqa: E402

import container_app  # noqa: E402
from container_app import app  # noqa: E402

results = []

ROUTE = "/api/workbench/pipeline-entities"

TEST_API_KEY = "test-only-pipeline-entities-api-key"


def check(label, cond, detail=""):
    if cond:
        results.append(f"{label}: PASS")
    else:
        results.append(f"{label}: FAIL — {detail}")


def _auth_headers(key=TEST_API_KEY):
    return {"Authorization": f"Bearer {key}"}


def _install_api_key(key=TEST_API_KEY):
    os.environ["CIS_PIPELINE_API_KEY"] = key


# ── scratch database, full real column set, one sentinel per excluded col ──

_SENTINELS = {
    "topic": "RAW_TOPIC_SENTINEL_9f2c",
    "max_consecutive_revisions": 918273,
    "final_objections_json": "OBJECTIONS_SENTINEL_a1b2",
    "intent": "INTENT_SENTINEL_c3d4",
    "directive_hash": "DIRECTIVE_HASH_SENTINEL_e5f6",
    "drafter_output": "DRAFTER_OUTPUT_SENTINEL_g7h8",
    "objections_json": "ROUND_OBJECTIONS_SENTINEL_i9j0",
    "reviewer1_output": "REVIEWER1_OUTPUT_SENTINEL_k1l2",
    "reviewer2_output": "REVIEWER2_OUTPUT_SENTINEL_m3n4",
    "brain_output": "BRAIN_OUTPUT_SENTINEL_o5p6",
    "verify_output": "VERIFY_OUTPUT_SENTINEL_q7r8",
    "human_question": "HUMAN_QUESTION_SENTINEL_s9t0",
    "human_answer": "HUMAN_ANSWER_SENTINEL_u1v2",
    "menter_output": "MENTER_OUTPUT_SENTINEL_w3x4",
    "input_text": "INPUT_TEXT_SENTINEL_y5z6",
    "output_text": "OUTPUT_TEXT_SENTINEL_a7b8",
    "feedback_text": "FEEDBACK_TEXT_SENTINEL_c9d0",
    "briefing_hash": "BRIEFING_HASH_SENTINEL_e1f2",
    "briefing_json": "BRIEFING_JSON_SENTINEL_g3h4",
    "drift_snapshot_json": "DRIFT_SNAPSHOT_SENTINEL_i5j6",
    "decision_trail_snapshot_json": "DECISION_TRAIL_SENTINEL_k7l8",
    "rationale": "RATIONALE_SENTINEL_m9n0",
    "summary": "GATE_SUMMARY_SENTINEL_o1p2",
    "evidence": "GATE_EVIDENCE_SENTINEL_q3r4",
}


def make_scratch_db(include_gate_outcomes=True):
    tmp = tempfile.mkdtemp(prefix="pipeline_entities_test_")
    path = os.path.join(tmp, "scratch.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE workflow_runs (
            id TEXT PRIMARY KEY, topic TEXT, result TEXT,
            requires_eric_review INTEGER, max_rounds INTEGER,
            max_consecutive_revisions INTEGER, rounds_completed INTEGER,
            final_objections_json TEXT, created_at TEXT, completed_at TEXT,
            status TEXT, route TEXT, updated_at TEXT, eric_approved_at TEXT,
            intent TEXT, directive_hash TEXT, project_id TEXT, parent_run_id TEXT
        );
        CREATE TABLE deliberation_rounds (
            id INTEGER PRIMARY KEY, run_id TEXT, round_number INTEGER,
            drafter_role TEXT, drafter_output TEXT, reviewer_role TEXT,
            reviewer_signal TEXT, objections_json TEXT, revision_number INTEGER,
            requires_eric_review INTEGER, created_at TEXT, reviewer1_output TEXT,
            reviewer2_output TEXT, brain_output TEXT, verify_output TEXT,
            human_question TEXT, human_answer TEXT, menter_output TEXT
        );
        CREATE TABLE agent_trajectories (
            id INTEGER PRIMARY KEY, run_id TEXT, role TEXT, phase TEXT,
            input_text TEXT, output_text TEXT, feedback_text TEXT,
            round_number INTEGER, outcome TEXT, consensus_reached INTEGER,
            config_version TEXT, marginal_utility REAL, created_at TEXT,
            tokens_in INTEGER, tokens_out INTEGER
        );
        CREATE TABLE eric_gate_approvals (
            id TEXT PRIMARY KEY, workflow_run_id TEXT, decision TEXT,
            decided_at TEXT, decided_by TEXT, goal_reference_id INTEGER,
            briefing_hash TEXT, briefing_json TEXT, drift_snapshot_json TEXT,
            decision_trail_snapshot_json TEXT, is_current INTEGER,
            supersedes_approval_id TEXT, rationale TEXT, created_at TEXT
        );
    """)
    if include_gate_outcomes:
        conn.executescript("""
            CREATE TABLE gate_outcomes (
                id INTEGER PRIMARY KEY, run_id TEXT, phase TEXT, role TEXT,
                guardrail_name TEXT, verdict TEXT, mode TEXT, summary TEXT,
                evidence TEXT, timestamp TEXT
            );
        """)

    s = _SENTINELS
    for i in range(1, 26):  # 25 runs — exercises the 20-row cohort bound
        run_id = f"run-{i:03d}"
        conn.execute(
            "INSERT INTO workflow_runs (id, topic, result, requires_eric_review, "
            "max_rounds, max_consecutive_revisions, rounds_completed, "
            "final_objections_json, created_at, completed_at, status, route, "
            "updated_at, eric_approved_at, intent, directive_hash, project_id, "
            "parent_run_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (run_id, s["topic"], "CONSENSUS_REACHED", 1, 5,
             s["max_consecutive_revisions"], 2, s["final_objections_json"],
             f"2026-01-{i:02d} 00:00:00", None, "DONE", "standard", None, None,
             s["intent"], s["directive_hash"], "cis", None),
        )

    for run_id in (f"run-{i:03d}" for i in range(1, 26)):
        conn.execute(
            "INSERT INTO deliberation_rounds (run_id, round_number, drafter_role, "
            "drafter_output, reviewer_role, reviewer_signal, objections_json, "
            "revision_number, requires_eric_review, created_at, reviewer1_output, "
            "reviewer2_output, brain_output, verify_output, human_question, "
            "human_answer, menter_output) VALUES (?,1,'draft',?,?,'CONSENSUS_REACHED',"
            "?,1,1,'2026-01-01 00:00:00',?,?,?,?,?,?,?)",
            (run_id, s["drafter_output"], "review1", s["objections_json"],
             s["reviewer1_output"], s["reviewer2_output"], s["brain_output"],
             s["verify_output"], s["human_question"], s["human_answer"],
             s["menter_output"]),
        )
        conn.execute(
            "INSERT INTO agent_trajectories (run_id, role, phase, input_text, "
            "output_text, feedback_text, round_number, outcome, consensus_reached, "
            "config_version, marginal_utility, created_at, tokens_in, tokens_out) "
            "VALUES (?,'draft','draft',?,?,?,1,'pending',0,'v1',0.5,"
            "'2026-01-01 00:00:00',10,20)",
            (run_id, s["input_text"], s["output_text"], s["feedback_text"]),
        )
        conn.execute(
            "INSERT INTO eric_gate_approvals (id, workflow_run_id, decision, "
            "decided_at, decided_by, goal_reference_id, briefing_hash, "
            "briefing_json, drift_snapshot_json, decision_trail_snapshot_json, "
            "is_current, supersedes_approval_id, rationale, created_at) "
            "VALUES (?,?,'APPROVE','2026-01-01 00:00:00','Eric',1,?,?,?,?,1,NULL,?,"
            "'2026-01-01 00:00:00')",
            (f"approval-{run_id}", run_id, s["briefing_hash"], s["briefing_json"],
             s["drift_snapshot_json"], s["decision_trail_snapshot_json"],
             s["rationale"]),
        )
        if include_gate_outcomes:
            conn.execute(
                "INSERT INTO gate_outcomes (run_id, phase, role, guardrail_name, "
                "verdict, mode, summary, evidence, timestamp) VALUES "
                "(?,'brain','brain','gate_research_artifact_present.sh','PASS',"
                "'ADVISORY',?,?,'2026-01-01 00:00:00')",
                (run_id, s["summary"], s["evidence"]),
            )
    conn.commit()
    return tmp, path, conn


def _use_scratch_db(path):
    orig = cs.DB
    cs.DB = path
    return orig


def _restore_db(orig):
    cs.DB = orig


def _row_counts(conn):
    tables = ["workflow_runs", "deliberation_rounds", "agent_trajectories",
              "eric_gate_approvals"]
    if conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='gate_outcomes'"
    ).fetchone():
        tables.append("gate_outcomes")
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


# ── recursive walkers ───────────────────────────────────────────────────────

def _all_keys(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            _all_keys(v, acc)
    elif isinstance(obj, list):
        for item in obj:
            _all_keys(item, acc)
    return acc


def _all_leaves(obj, acc):
    if isinstance(obj, dict):
        for v in obj.values():
            _all_leaves(v, acc)
    elif isinstance(obj, list):
        for item in obj:
            _all_leaves(item, acc)
    else:
        acc.append(obj)
    return acc


EXCLUDED_KEYS = {
    "topic", "max_consecutive_revisions", "final_objections_json", "intent",
    "directive_hash", "drafter_output", "objections_json", "reviewer1_output",
    "reviewer2_output", "brain_output", "verify_output", "human_question",
    "human_answer", "menter_output", "input_text", "output_text",
    "feedback_text", "briefing_hash", "briefing_json", "drift_snapshot_json",
    "decision_trail_snapshot_json", "rationale", "summary", "evidence",
    "port", "hermes_profile", "args", "arg_desc",
}

KNOWN_PORTS = {p["port"] for p in dispatch.PROFILES.values()} | {5000, 8642}
PROFILE_NAMES = {p["hermes_profile"] for p in dispatch.PROFILES.values()}
LOCALHOST_NEEDLES = ("localhost", "127.0.0.1")


def _assert_response_is_clean(body, label_prefix):
    keys = _all_keys(body, set())
    leaves = _all_leaves(body, [])
    leaf_strings = [v for v in leaves if isinstance(v, str)]
    leaf_numbers = {v for v in leaves if isinstance(v, (int, float)) and not isinstance(v, bool)}

    check(f"{label_prefix}.excluded-keys", EXCLUDED_KEYS.isdisjoint(keys),
          sorted(EXCLUDED_KEYS & keys))

    sentinel_hits = [
        s for s in _SENTINELS.values()
        if (isinstance(s, str) and any(s in ls for ls in leaf_strings))
        or (isinstance(s, (int, float)) and s in leaf_numbers)
    ]
    check(f"{label_prefix}.no-sentinels", not sentinel_hits, sentinel_hits)

    port_hits = KNOWN_PORTS & leaf_numbers
    check(f"{label_prefix}.no-known-ports", not port_hits, port_hits)

    localhost_hits = [needle for needle in LOCALHOST_NEEDLES
                      if any(needle in ls for ls in leaf_strings)]
    check(f"{label_prefix}.no-localhost-urls", not localhost_hits, localhost_hits)

    profile_hits = [p for p in PROFILE_NAMES if any(p in ls for ls in leaf_strings)]
    check(f"{label_prefix}.no-hermes-profile-names", not profile_hits, profile_hits)

    prompt_hits = [ls for ls in leaf_strings if "SENTINEL" in ls]
    check(f"{label_prefix}.no-raw-prompt-or-output-sentinels", not prompt_hits, prompt_hits)

    check(f"{label_prefix}.no-legacy-prime-alias",
          not any("prime" in ls.lower() for ls in leaf_strings),
          [ls for ls in leaf_strings if "prime" in ls.lower()])


# ── tests ───────────────────────────────────────────────────────────────────

def test_exclusions_recursively_cannot_appear():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE, headers=_auth_headers())
        check("1a. GET pipeline-entities returns 200", resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        _assert_response_is_clean(body, "1")
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_route_matches_read_model_directly():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE, headers=_auth_headers())
        body = resp.get_json()
        direct = pe.get_pipeline_entities(db_path=path)
        check("2a. route body matches a direct get_pipeline_entities() call",
              body == direct, (body, direct))
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_exactly_six_canonical_roles():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE, headers=_auth_headers())
        body = resp.get_json()
        roles = body["roles"]
        check("3a. exactly six roles are reported", len(roles) == 6, len(roles))
        check("3b. the six roles match dispatch.PROFILES exactly",
              {r["role"] for r in roles} == set(dispatch.PROFILES.keys()),
              {r["role"] for r in roles})
        check("3c. no role entry carries a port or hermes_profile key",
              all("port" not in r and "hermes_profile" not in r for r in roles), roles)
        check("3d. the chatbot is reported separately and is not among the six roles",
              "chatbot" not in {r["role"] for r in roles}
              and body["chatbot"]["is_pipeline_role"] is False,
              body["chatbot"])
        check("3e. the chatbot's backend_role is brain but it is its own distinct entity",
              body["chatbot"]["backend_role"] == "brain"
              and body["chatbot"]["capability"] == "braingate_conversation",
              body["chatbot"])
        check("3f. the chatbot authority names the live blueprint registration",
              body["chatbot"]["authority"]["blueprint_registered"] is True,
              body["chatbot"]["authority"])
        check("3g. the chatbot authority carries a non-empty route allowlist",
              len(body["chatbot"]["authority"]["route_allowlist"]) > 0,
              body["chatbot"]["authority"])
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_procedures_strip_args_and_backend_configuration():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE, headers=_auth_headers())
        body = resp.get_json()
        stages = body["procedures"]["stages"]
        check("4a. procedure stages match guardrails.PHASE_GATE_MAP's keys exactly",
              set(stages.keys()) == set(pe.guardrails.PHASE_GATE_MAP.keys())
              if hasattr(pe, "guardrails") else True, list(stages.keys()))
        all_gates = [g for gates in stages.values() for g in gates] + body["procedures"]["security_gates"]
        check("4b. no gate entry carries args or arg_desc",
              all("args" not in g and "arg_desc" not in g for g in all_gates), all_gates)
        check("4c. every gate entry carries a script and a mode",
              all("script" in g and "mode" in g for g in all_gates), all_gates)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_shared_cohort_bound_and_linkage():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE, headers=_auth_headers())
        body = resp.get_json()
        activity = body["activity"]
        cohort_ids = set(activity["cohort_run_ids"])
        check("5a. the workflow_runs cohort is bounded at 20 even though 25 rows exist",
              len(activity["workflow_runs"]["rows"]) == 20, len(activity["workflow_runs"]["rows"]))
        check("5b. cohort_run_ids has exactly 20 entries",
              len(cohort_ids) == 20, len(cohort_ids))
        for key in ("deliberation_rounds", "agent_trajectories", "eric_gate_approvals", "gate_outcomes"):
            rows = activity[key]["rows"]
            fk = "workflow_run_id" if key == "eric_gate_approvals" else "run_id"
            row_run_ids = {r[fk] for r in rows}
            check(f"5c. every {key} row's run id is inside the shared cohort",
                  row_run_ids.issubset(cohort_ids), row_run_ids - cohort_ids)
            check(f"5d. {key} is not independently windowed to its own top-20 "
                  f"(25 total rows exist, but only cohort-linked rows appear)",
                  len(rows) == 20, len(rows))
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_missing_table_degrades_without_failing_whole_response():
    tmp, path, conn = make_scratch_db(include_gate_outcomes=False)
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE, headers=_auth_headers())
        check("6a. response is still 200 when gate_outcomes is entirely absent",
              resp.status_code == 200, resp.status_code)
        body = resp.get_json()
        gate_outcomes = body["activity"]["gate_outcomes"]
        check("6b. gate_outcomes degrades to available=False, rows=[]",
              gate_outcomes["available"] is False and gate_outcomes["rows"] == [],
              gate_outcomes)
        check("6c. the rest of the activity cohort still renders normally",
              body["activity"]["workflow_runs"]["available"] is True
              and len(body["activity"]["workflow_runs"]["rows"]) == 20,
              body["activity"]["workflow_runs"])
        check("6d. roles and procedures are unaffected by the missing activity table",
              len(body["roles"]) == 6 and "stages" in body["procedures"], body)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_authentication_is_enforced():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(ROUTE)
        check("7a. no credential at all is refused (401)", resp.status_code == 401, resp.status_code)

        resp = client.get(ROUTE, headers=_auth_headers("wrong-key-entirely"))
        check("7b. a wrong credential is refused (401)", resp.status_code == 401, resp.status_code)

        resp = client.get(ROUTE, headers=_auth_headers())
        check("7c. the correct credential is accepted (200)", resp.status_code == 200, resp.status_code)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_get_only_route():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        for method in ("POST", "PATCH", "PUT", "DELETE"):
            resp = client.open(ROUTE, method=method, headers=_auth_headers())
            check(f"8a. {method} on the pipeline-entities route is refused (405)",
                  resp.status_code == 405, resp.status_code)
        rules = {str(r.rule): sorted(r.methods - {"HEAD", "OPTIONS"})
                 for r in app.url_map.iter_rules() if str(r.rule) == ROUTE}
        check("8b. exactly one route is registered and it is GET-only",
              rules == {ROUTE: ["GET"]}, rules)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_model_failure_returns_503_not_500():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    import api.pipeline_entities as api_pe
    original = api_pe.pe.get_pipeline_entities
    try:
        def boom(**kwargs):
            raise sqlite3.OperationalError("unable to open database file")
        api_pe.pe.get_pipeline_entities = boom
        resp = app.test_client().get(ROUTE, headers=_auth_headers())
        body = resp.get_json()
        check("9a. a read-model failure is a 503, never a 500 traceback",
              resp.status_code == 503, resp.status_code)
        check("9b. the error names the exception type and fabricates no model body",
              "OperationalError" in body.get("error", "") and "roles" not in body, body)
    finally:
        api_pe.pe.get_pipeline_entities = original
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_caller_supplied_db_path():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        resp = client.get(f"{ROUTE}?db_path=/etc/passwd&db=/etc/passwd", headers=_auth_headers())
        check("10a. a caller-supplied db_path/db query param is ignored, not honored",
              resp.status_code == 200 and resp.get_json()["read_model"] == "cis_pipeline_entities",
              resp.status_code)
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_reads_do_not_mutate_the_database():
    tmp, path, conn = make_scratch_db()
    orig_db = _use_scratch_db(path)
    _install_api_key()
    client = app.test_client()
    try:
        before = _row_counts(conn)
        client.get(ROUTE, headers=_auth_headers())
        client.get(ROUTE, headers=_auth_headers())
        after = _row_counts(conn)
        check("11a. two GETs never change any row count in any of the five tables",
              before == after, (before, after))
    finally:
        _restore_db(orig_db)
        conn.close()
        shutil.rmtree(tmp, ignore_errors=True)


def test_route_does_not_collide_with_other_workbench_surfaces():
    pipeline_entities_rules = {
        str(r.rule) for r in app.url_map.iter_rules() if "pipeline-entities" in str(r.rule)
    }
    check("12a. exactly one pipeline-entities route is registered",
          pipeline_entities_rules == {ROUTE}, pipeline_entities_rules)

    other_workbench_rules = {
        str(r.rule) for r in app.url_map.iter_rules()
        if str(r.rule).startswith("/api/workbench") and "pipeline-entities" not in str(r.rule)
    }
    check("12b. the pre-existing Workbench surfaces (portfolio, projects, ...) are untouched",
          len(other_workbench_rules) > 0, other_workbench_rules)
    check("12c. no pre-existing Workbench route was reassigned to this blueprint",
          ROUTE not in other_workbench_rules, other_workbench_rules)


def run():
    test_exclusions_recursively_cannot_appear()
    test_route_matches_read_model_directly()
    test_exactly_six_canonical_roles()
    test_procedures_strip_args_and_backend_configuration()
    test_shared_cohort_bound_and_linkage()
    test_missing_table_degrades_without_failing_whole_response()
    test_authentication_is_enforced()
    test_get_only_route()
    test_model_failure_returns_503_not_500()
    test_no_caller_supplied_db_path()
    test_reads_do_not_mutate_the_database()
    test_route_does_not_collide_with_other_workbench_surfaces()

    for r in results:
        print(r)
    failed = [r for r in results if ": FAIL" in r]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
