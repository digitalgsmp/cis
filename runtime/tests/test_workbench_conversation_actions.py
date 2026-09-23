"""
test_workbench_conversation_actions.py — integration tests for the
Braingate-conversation-to-approved-action workflow (queue item WB.1B-2B,
including its CORRECTION.md pass), spanning workbench_app.py's proposal
routes, card_factory_app.py's generate+gate boundary (called directly, not
over HTTP) and card_runner.py's dispatch()/run_status() (also called
directly, plus once through the nested Flask blueprint to prove the HTTP
path too).

No paid model calls anywhere: card_factory_app._call_generator is
monkeypatched (same convention as test_card_factory_app.py); the real
tools/card_gate.py runs as a real subprocess against the temp db (free,
deterministic); dispatch()'s child process is a harmless real `python3 -c
...` via card_runner._TEST_COMMAND_OVERRIDE (same seam
test_card_runner.py's route-level tests use), never the real claude/codex
binaries.

Run: python3 runtime/tests/test_workbench_conversation_actions.py
"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Auth is fail-CLOSED (runtime/workbench_auth.py): an unset CIS_PIPELINE_API_KEY
# denies every request with 503 rather than granting anonymous access. A real
# key is configured and presented below, exactly as a real caller would.
TEST_API_KEY = "test-workbench-key"
os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY

REPO_SRC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MIGRATIONS_DIR = os.path.join(REPO_SRC, "runtime", "schema", "migrations")
MIGRATION_0035 = os.path.join(MIGRATIONS_DIR, "0035_workbench.sql")
MIGRATION_0036 = os.path.join(MIGRATIONS_DIR, "0036_card_factory.sql")
MIGRATION_0037 = os.path.join(MIGRATIONS_DIR, "0037_card_runner.sql")
MIGRATION_0038 = os.path.join(MIGRATIONS_DIR, "0038_workbench_action_proposals.sql")
REAL_EXECUTION_RULES = os.path.join(REPO_SRC, "cards", "EXECUTION_RULES.md")
REAL_REVIEW_RULES = os.path.join(REPO_SRC, "cards", "REVIEW_RULES.md")

KNOWLEDGE_MESSAGES_SCHEMA = """
CREATE TABLE knowledge_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    source_key TEXT,
    timestamp TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(
    content, source, role, content='knowledge_messages', content_rowid='id'
);
CREATE TRIGGER km_ai AFTER INSERT ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(rowid, content, source, role)
    VALUES (new.id, new.content, new.source, new.role);
END;
CREATE TRIGGER km_ad AFTER DELETE ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(knowledge_messages_fts, rowid, content, source, role)
    VALUES ('delete', old.id, old.content, old.source, old.role);
END;
CREATE TRIGGER km_au AFTER UPDATE ON knowledge_messages BEGIN
    INSERT INTO knowledge_messages_fts(knowledge_messages_fts, rowid, content, source, role)
    VALUES ('delete', old.id, old.content, old.source, old.role);
    INSERT INTO knowledge_messages_fts(rowid, content, source, role)
    VALUES (new.id, new.content, new.source, new.role);
END;
"""

QUOTE = "this fifteen-plus character phrase is Erics own verbatim words"

MODEL_CARD_TEXT = f"""CARD test-conv-action: Add a thing
SOURCE: message 1, 2026-09-18
INTENT (Eric, verbatim): "{QUOTE}"
BUILD: Eric sees a new button on the page.
DONE WHEN:
  - Eric clicks the button and sees a result.
EVIDENCE:
  - curl -s http://127.0.0.1:5000/ok
NOT IN THIS CARD: dashboards, refactors, other features, docs, migrations, telegram
"""

BASE_PROPOSAL_FIELDS = {
    "kind": "implementation",
    "outcome": "Eric can click a button and see a result.",
    "action": "Add the button and its handler.",
    "boundaries": "This page only; no new pages.",
    "success_criteria": "Eric clicks it and sees a result.",
    "unresolved_decisions": "",
    "permitted_files": ["runtime/ui/src/App.jsx"],
    "permitted_commands": [],
}


def _py(code):
    return [sys.executable, "-c", code]


def _mock_claude(exit_code=0, message="ok"):
    code = (
        "import sys, json\n"
        "sys.stdin.read()\n"
        "print(json.dumps({'num_turns': 1, "
        "'usage': {'input_tokens': 10, 'output_tokens': 5}, "
        f"'total_cost_usd': 0.001, 'result': {message!r}}}))\n"
        f"sys.exit({exit_code})\n"
    )
    return _py(code)


def _proposal_block(**overrides):
    fields = dict(BASE_PROPOSAL_FIELDS)
    fields.update(overrides)
    return json.dumps(fields)


def run():
    results = []

    def check(label, cond, detail=""):
        results.append((label, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'}  {label}" + (f"  -- {detail}" if not cond else ""))

    tmp_root = tempfile.mkdtemp(prefix="workbench_conv_actions_test_")
    repo_root = os.path.join(tmp_root, "repo")
    os.makedirs(repo_root)
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo_root, check=True)
    with open(os.path.join(repo_root, ".gitkeep"), "w") as f:
        f.write("x\n")
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo_root, check=True)

    cards_dir = os.path.join(repo_root, "cards")
    inbox_dir = os.path.join(cards_dir, "inbox")
    history_dir = os.path.join(cards_dir, "history")
    os.makedirs(inbox_dir)
    handoffs_dir = os.path.join(repo_root, "data", "agent_handoffs")
    os.makedirs(handoffs_dir)
    shutil.copy(REAL_EXECUTION_RULES, os.path.join(cards_dir, "EXECUTION_RULES.md"))
    shutil.copy(REAL_REVIEW_RULES, os.path.join(cards_dir, "REVIEW_RULES.md"))
    log_dir = os.path.join(tmp_root, "logs")

    db_path = os.path.join(tmp_root, "test_spine.db")
    conn = sqlite3.connect(db_path)
    conn.executescript(KNOWLEDGE_MESSAGES_SCHEMA)
    for mig in (MIGRATION_0035, MIGRATION_0036, MIGRATION_0037, MIGRATION_0038):
        with open(mig) as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()

    orig_db_path_env = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = db_path

    import workbench_app  # noqa: E402
    import card_factory_app  # noqa: E402
    import card_runner  # noqa: E402

    for mod in (workbench_app, card_factory_app, card_runner):
        mod.DB_PATH = db_path
        # mod.API_KEY = "" removed: the module constant no longer exists and
        # blanking it would no longer disable auth anyway. Credentials are
        # presented on the client instead (below).
    card_factory_app.CARDS_INBOX_DIR = inbox_dir
    card_factory_app.CARDS_HISTORY_DIR = history_dir
    card_runner.REPO_ROOT = repo_root
    card_runner.CARDS_DIR = cards_dir
    card_runner.EXECUTION_RULES_PATH = os.path.join(cards_dir, "EXECUTION_RULES.md")
    card_runner.REVIEW_RULES_PATH = os.path.join(cards_dir, "REVIEW_RULES.md")
    card_runner.HANDOFFS_DIR = handoffs_dir
    card_runner.LOG_DIR = log_dir

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(workbench_app.workbench_bp)
    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"

    orig_gateway = workbench_app._call_brain_gateway
    orig_generator = card_factory_app._call_generator
    orig_budget = workbench_app.WORKBENCH_CONTEXT_CHAR_BUDGET

    def wait_terminal(run_id, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            row = card_runner.run_status(run_id)
            if row["status"] in card_runner.TERMINAL_STATUSES:
                return row
            time.sleep(0.05)
        raise TimeoutError(f"run {run_id} never reached a terminal state")

    def new_project(name):
        return client.post("/api/workbench/projects", json={"name": name}).get_json()["project"]["id"]

    def draft(project_id, message, request_id, gateway_reply):
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: (gateway_reply, None)
        return client.post(
            f"/api/workbench/projects/{project_id}/messages",
            json={"message": message, "request_id": request_id, "mode": "draft_proposal"},
        )

    def kb_human_rows():
        c = sqlite3.connect(db_path)
        rows = c.execute("SELECT content FROM knowledge_messages WHERE role = 'human'").fetchall()
        c.close()
        return [r[0] for r in rows]

    try:
        # ══ 1. Plain chat never proposes; focused clarification proposes nothing ══
        p1 = new_project("Scenario 1")
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: (
            f"idea\n{workbench_app.PROPOSAL_MARKER}\n{{}}", None
        )
        resp = client.post(
            f"/api/workbench/projects/{p1}/messages",
            json={"message": "just chatting", "request_id": "chat-1"},
        )
        body = resp.get_json()
        check("1a. chat mode never creates a proposal", body["proposal"] is None, body)
        check("1b. raw marker text still shown honestly", workbench_app.PROPOSAL_MARKER in
              body["brain_message"]["content"], body)

        resp = draft(p1, QUOTE, "draft-clarify", "Which page should this appear on?")
        check("1c. clarification -> no proposal", resp.get_json()["proposal"] is None, resp.get_json())

        # ══ 2. Multi-turn proposal creation: a later "yes, draft that" must ══
        # not replace the substantive earlier request.
        p2 = new_project("Scenario 2")
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: ("Got it, tell me more.", None)
        client.post(f"/api/workbench/projects/{p2}/messages",
                    json={"message": QUOTE, "request_id": "m2-1"})
        resp = draft(p2, "yes, draft that", "draft-multiturn", f"ok\n{workbench_app.PROPOSAL_MARKER}\n{_proposal_block()}")
        body = resp.get_json()
        proposal = body["proposal"]
        check("2a. proposal created", proposal is not None, body)
        check("2b. user_words retains the earlier substantive message",
              QUOTE in proposal["user_words"], proposal)
        check("2c. user_words also retains the later trigger message",
              "yes, draft that" in proposal["user_words"], proposal)
        check("2d. source_message_ids covers both turns", len(proposal["source_message_ids"]) >= 2,
              proposal)
        proposal_id = proposal["id"]

        # ══ 3. Confirm direction: generator payload carries the full ══
        # confirmed proposal + provenance; KB row is never polluted with
        # model-authored text.
        captured_payloads = []
        card_factory_app._call_generator = lambda payload: (
            captured_payloads.append(payload), (MODEL_CARD_TEXT, None, None)
        )[1]
        resp = client.post(f"/api/workbench/proposals/{proposal_id}/confirm-direction",
                            json={"request_id": "confirm-1"})
        body = resp.get_json()
        check("3a. confirm-direction -> 201", resp.status_code == 201, (resp.status_code, body))
        payload_text = captured_payloads[-1]["text"]
        check("3b. generator payload carries the earlier request", QUOTE in payload_text, payload_text)
        check("3c. generator payload carries the later message", "yes, draft that" in payload_text,
              payload_text)
        for f in ("action", "boundaries", "outcome", "unresolved_decisions"):
            check(f"3d. generator payload carries confirmed field '{f}'",
                  BASE_PROPOSAL_FIELDS[f] in payload_text or (BASE_PROPOSAL_FIELDS[f] == "" and
                  f"{f}: " in payload_text),
                  payload_text)
        human_rows = kb_human_rows()
        check("3e. KB human row never contains model-authored action text",
              not any(BASE_PROPOSAL_FIELDS["action"] in r for r in human_rows), human_rows)
        check("3f. KB human row never contains model-authored outcome text",
              not any(BASE_PROPOSAL_FIELDS["outcome"] in r for r in human_rows), human_rows)
        check("3g. KB human row does contain Eric's actual words",
              any(QUOTE in r for r in human_rows), human_rows)

        card_id = body["card"]["id"]
        ask_id = body["proposal"]["card_factory_ask_id"]
        confirmed_rev = body["proposal"]["confirmed_revision"]
        check("3h. confirmed_revision recorded", confirmed_rev == body["proposal"]["revision"], body)

        run_count = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM card_runner_runs").fetchone()[0]
        check("3i. no execution from drafting/confirming alone", run_count == 0, run_count)

        fingerprint = card_runner._sha256_text(MODEL_CARD_TEXT)

        # ══ 4. Each material field alone invalidates approval — not just ══
        # success_criteria (the exact gap the independent review found).
        for field in ("kind", "outcome", "action", "boundaries", "success_criteria", "unresolved_decisions"):
            new_value = "mockup" if field == "kind" else f"corrected {field} value"
            resp = client.patch(f"/api/workbench/proposals/{proposal_id}", json={field: new_value})
            new_rev = resp.get_json()["proposal"]["revision"]
            resp = client.post(
                f"/api/workbench/proposals/{proposal_id}/approve",
                json={
                    "target": "claude", "request_id": f"approve-stale-{field}", "authorized_by": "eric",
                    "expected_card_fingerprint": fingerprint, "permitted_files": ["runtime/x.py"],
                    "accept_time_only_control": True, "expected_proposal_revision": new_rev,
                },
            )
            check(f"4-{field}. correction alone blocks approve (409), no worker started",
                  resp.status_code == 409 and
                  sqlite3.connect(db_path).execute(
                      "SELECT COUNT(*) FROM card_runner_runs"
                  ).fetchone()[0] == 0,
                  (field, resp.status_code, resp.get_json()))
            if field == "unresolved_decisions":
                # Only testing that THIS field alone invalidates approval —
                # clear it back so it doesn't block every later step in this
                # test (unresolved-decisions-blocks-approve gets its own
                # dedicated scenario, #9, further down).
                client.patch(f"/api/workbench/proposals/{proposal_id}", json={"unresolved_decisions": ""})
            # re-confirm so the next field's test starts from a clean, fresh
            # confirmed state (isolates each field's own contribution).
            card_factory_app._call_generator = lambda payload: (MODEL_CARD_TEXT, None, None)
            resp = client.post(f"/api/workbench/proposals/{proposal_id}/confirm-direction",
                                json={"request_id": f"reconfirm-{field}"})
            confirmed_rev = resp.get_json()["proposal"]["confirmed_revision"]
            card_id = resp.get_json()["card"]["id"]

        # ══ 5. Stale CLIENT revision is also rejected (not just a stale ══
        # server-side confirmation) — a client showing an old revision on
        # screen must not be able to approve against it.
        current_rev = client.get(f"/api/workbench/proposals/{proposal_id}").get_json()["proposal"]["revision"]
        resp = client.post(
            f"/api/workbench/proposals/{proposal_id}/approve",
            json={
                "target": "claude", "request_id": "approve-stale-client", "authorized_by": "eric",
                "expected_card_fingerprint": fingerprint, "permitted_files": ["runtime/x.py"],
                "accept_time_only_control": True, "expected_proposal_revision": current_rev - 1,
            },
        )
        check("5a. stale client-supplied revision -> 409", resp.status_code == 409, resp.get_json())
        check("5b. names 'stale' in the error", "stale" in resp.get_json().get("error", "").lower(),
              resp.get_json())

        # ══ 6. Correction landing DURING generation is discarded, not linked ══
        proposal_before = client.get(f"/api/workbench/proposals/{proposal_id}").get_json()["proposal"]

        def generator_that_corrects_mid_flight(payload):
            conn2 = card_runner._db(db_path)
            row2 = conn2.execute(
                "SELECT * FROM workbench_action_proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            workbench_app._apply_proposal_correction(conn2, row2, {"action": "a mid-flight correction"})
            conn2.close()
            return MODEL_CARD_TEXT, None, None

        card_factory_app._call_generator = generator_that_corrects_mid_flight
        resp = client.post(f"/api/workbench/proposals/{proposal_id}/confirm-direction",
                            json={"request_id": "confirm-midflight"})
        check("6a. correction during generation -> 409, discarded",
              resp.status_code == 409, (resp.status_code, resp.get_json()))
        after = client.get(f"/api/workbench/proposals/{proposal_id}").get_json()["proposal"]
        check("6b. confirmed_revision unchanged by the discarded attempt",
              after["confirmed_revision"] == proposal_before["confirmed_revision"], (proposal_before, after))

        # ══ 7. Fresh confirmed revision can run under explicit approval ══
        card_factory_app._call_generator = lambda payload: (MODEL_CARD_TEXT, None, None)
        resp = client.post(f"/api/workbench/proposals/{proposal_id}/confirm-direction",
                            json={"request_id": "confirm-final"})
        body = resp.get_json()
        fresh_rev = body["proposal"]["revision"]
        card_runner._TEST_COMMAND_OVERRIDE = _mock_claude(message="implemented ok")
        try:
            resp = client.post(
                f"/api/workbench/proposals/{proposal_id}/approve",
                json={
                    "target": "claude", "request_id": "approve-fresh", "authorized_by": "eric",
                    "expected_card_fingerprint": fingerprint, "permitted_files": ["runtime/x.py"],
                    "accept_time_only_control": True, "expected_proposal_revision": fresh_rev,
                },
            )
            body = resp.get_json()
            check("7a. approve on a fresh confirmed revision -> 201", resp.status_code == 201,
                  (resp.status_code, body))
            run_id = body["run"]["id"]
            terminal = wait_terminal(run_id)
            check("7b. mock run reaches completed", terminal["status"] == "completed", terminal)
        finally:
            card_runner._TEST_COMMAND_OVERRIDE = None
        check("7c. approval recorded on the proposal", client.get(
            f"/api/workbench/proposals/{proposal_id}"
        ).get_json()["proposal"]["status"] == "approved", None)

        # duplicate replay of the same request_id -> same run, no re-dispatch
        card_runner._TEST_COMMAND_OVERRIDE = _mock_claude()
        try:
            resp = client.post(
                f"/api/workbench/proposals/{proposal_id}/approve",
                json={
                    "target": "claude", "request_id": "approve-fresh", "authorized_by": "eric",
                    "expected_card_fingerprint": fingerprint, "permitted_files": ["runtime/x.py"],
                    "accept_time_only_control": True, "expected_proposal_revision": fresh_rev,
                },
            )
            check("7d. duplicate approve -> same run, flagged duplicate",
                  resp.get_json()["run"]["id"] == run_id and resp.get_json()["duplicate"] is True,
                  resp.get_json())
        finally:
            card_runner._TEST_COMMAND_OVERRIDE = None

        # ══ 8. Duplicate request_id belonging to a DIFFERENT card/proposal ══
        # must never be silently attached.
        p8 = new_project("Scenario 8")
        resp = draft(p8, QUOTE + " for scenario eight", "draft-8",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n{_proposal_block()}")
        proposal_8 = resp.get_json()["proposal"]["id"]
        card_factory_app._call_generator = lambda payload: (
            MODEL_CARD_TEXT.replace("test-conv-action", "test-conv-action-8")
            .replace(QUOTE, QUOTE + " for scenario eight"), None, None
        )
        resp = client.post(f"/api/workbench/proposals/{proposal_8}/confirm-direction",
                            json={"request_id": "confirm-8"})
        body8 = resp.get_json()
        fp8 = card_runner._sha256_text(body8["card"]["card_text"])
        resp = client.post(
            f"/api/workbench/proposals/{proposal_8}/approve",
            json={
                "target": "claude", "request_id": "approve-fresh", "authorized_by": "eric",
                "expected_card_fingerprint": fp8, "permitted_files": ["runtime/x.py"],
                "accept_time_only_control": True, "expected_proposal_revision": body8["proposal"]["revision"],
            },
        )
        check("8a. reused request_id for an unrelated card -> 409, not attached",
              resp.status_code == 409, (resp.status_code, resp.get_json()))
        check("8b. proposal 8 was never linked to proposal 1's run",
              client.get(f"/api/workbench/proposals/{proposal_8}").get_json()["proposal"]["card_runner_run_id"]
              is None, None)

        # ══ 9. Unresolved decisions block approval, even with a fresh confirmed revision ══
        p9 = new_project("Scenario 9")
        resp = draft(p9, QUOTE + " for scenario nine", "draft-9",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" +
                     _proposal_block(unresolved_decisions="which button color?"))
        proposal_9 = resp.get_json()["proposal"]["id"]
        card_factory_app._call_generator = lambda payload: (
            MODEL_CARD_TEXT.replace("test-conv-action", "test-conv-action-9")
            .replace(QUOTE, QUOTE + " for scenario nine"), None, None
        )
        resp = client.post(f"/api/workbench/proposals/{proposal_9}/confirm-direction",
                            json={"request_id": "confirm-9"})
        body9 = resp.get_json()
        fp9 = card_runner._sha256_text(body9["card"]["card_text"])
        resp = client.post(
            f"/api/workbench/proposals/{proposal_9}/approve",
            json={
                "target": "claude", "request_id": "approve-9", "authorized_by": "eric",
                "expected_card_fingerprint": fp9, "permitted_files": ["runtime/x.py"],
                "accept_time_only_control": True, "expected_proposal_revision": body9["proposal"]["revision"],
            },
        )
        check("9a. unresolved decisions block approve -> 409", resp.status_code == 409, resp.get_json())
        check("9b. names 'unresolved decisions'", "unresolved decisions" in resp.get_json().get("error", ""),
              resp.get_json())

        # ══ 10. Conversational correction (mode='revise_proposal') — the ══
        # backend does the natural-language-to-fields interpretation
        # itself, on the SAME single Brain call, no second model call, no
        # frontend-only field parsing.
        p10 = new_project("Scenario 10")
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: ("Sure, tell me more.", None)
        client.post(f"/api/workbench/projects/{p10}/messages",
                    json={"message": QUOTE + " for scenario ten", "request_id": "m10-1"})
        resp = draft(p10, "yes, draft that", "draft-10",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" +
                     _proposal_block(action="Add a small button."))
        proposal_10 = resp.get_json()["proposal"]["id"]
        rev_before_revise = resp.get_json()["proposal"]["revision"]

        gateway_calls = []

        def revise_gateway(messages, timeout=60.0):
            gateway_calls.append(messages)
            return (
                "Understood, switching to a bigger button.\n" + workbench_app.PROPOSAL_MARKER + "\n" +
                _proposal_block(action="Add a large, prominent button instead.")
            ), None

        workbench_app._call_brain_gateway = revise_gateway
        resp = client.post(
            f"/api/workbench/projects/{p10}/messages",
            json={
                "message": "actually make the button bigger", "request_id": "revise-10",
                "mode": "revise_proposal", "proposal_id": proposal_10,
            },
        )
        body = resp.get_json()
        check("10a. revise_proposal -> 200", resp.status_code == 200, (resp.status_code, body))
        check("10b. revision invalidated by the conversational correction",
              body["proposal"]["revision"] > rev_before_revise, body["proposal"])
        check("10c. action field updated to the revised value",
              body["proposal"]["action"] == "Add a large, prominent button instead.", body["proposal"])
        check("10d. original substantive words preserved across the correction",
              QUOTE in body["proposal"]["user_words"], body["proposal"])
        check("10e. correction message provenance retained",
              "actually make the button bigger" in body["proposal"]["user_words"], body["proposal"])
        check("10f. no second model call — one gateway call for this turn",
              len(gateway_calls) == 1, len(gateway_calls))
        sent_system_text = gateway_calls[0][0]["content"]
        check("10g. the model was shown the proposal's PRIOR boundaries to revise against",
              BASE_PROPOSAL_FIELDS["boundaries"] in sent_system_text, sent_system_text)

        card_factory_app._call_generator = lambda payload: (
            MODEL_CARD_TEXT.replace("test-conv-action", "test-conv-action-10")
            .replace(QUOTE, QUOTE + " for scenario ten"), None, None
        )
        resp = client.post(f"/api/workbench/proposals/{proposal_10}/confirm-direction",
                            json={"request_id": "confirm-10"})
        body10 = resp.get_json()
        check("10h. regenerated card after conversational correction -> 201",
              resp.status_code == 201, (resp.status_code, body10))
        fp10 = card_runner._sha256_text(body10["card"]["card_text"])
        card_runner._TEST_COMMAND_OVERRIDE = _mock_claude(message="scenario 10 ok")
        try:
            resp = client.post(
                f"/api/workbench/proposals/{proposal_10}/approve",
                json={
                    "target": "claude", "request_id": "approve-10", "authorized_by": "eric",
                    "expected_card_fingerprint": fp10, "permitted_files": ["runtime/x.py"],
                    "accept_time_only_control": True,
                    "expected_proposal_revision": body10["proposal"]["revision"],
                },
            )
            body = resp.get_json()
            check("10i. explicit approval after conversational correction -> 201",
                  resp.status_code == 201, (resp.status_code, body))
            terminal = wait_terminal(body["run"]["id"])
            check("10j. mock result reached", terminal["status"] == "completed", terminal)
        finally:
            card_runner._TEST_COMMAND_OVERRIDE = None

        # ══ 11. Bounded context protects the target proposal's boundaries; ══
        # only unrelated older history is trimmed. Stored-but-omitted ids
        # alone would not have protected this — the actual text must arrive.
        p11 = new_project("Scenario 11")
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: ("noted", None)
        for i in range(5):
            client.post(f"/api/workbench/projects/{p11}/messages",
                        json={"message": "x" * 300 + f" filler {i}", "request_id": f"filler11-{i}"})
        resp = draft(p11, QUOTE + " for scenario eleven", "draft-11",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" + _proposal_block())
        proposal_11 = resp.get_json()["proposal"]["id"]

        captured_revise_messages = []

        def revise_gateway_11(messages, timeout=60.0):
            captured_revise_messages.append(messages)
            return "ok, noted", None

        required_probe = client.post(
            f"/api/workbench/projects/{p11}/messages",
            json={"message": "probe", "request_id": "probe-11", "mode": "revise_proposal",
                  "proposal_id": proposal_11},
        ).get_json()
        # Budget: just enough over this mode's own required floor (system +
        # KB + this proposal's fields + message) to admit a couple of the
        # filler messages above but not all five — proves trimming still
        # happens to *unrelated* history while nothing required is dropped.
        required_floor = required_probe["brain_message"]["context_used"]["required_chars"]
        workbench_app.WORKBENCH_CONTEXT_CHAR_BUDGET = required_floor + 650
        workbench_app._call_brain_gateway = revise_gateway_11
        resp = client.post(
            f"/api/workbench/projects/{p11}/messages",
            json={
                "message": "small tweak", "request_id": "revise-11",
                "mode": "revise_proposal", "proposal_id": proposal_11,
            },
        )
        body = resp.get_json()
        check("11a. revise under a tight budget still succeeds (essentials fit)",
              resp.status_code == 200 and body["brain_message"]["status"] == "completed",
              (resp.status_code, body))
        sent = captured_revise_messages[0]
        sent_text = " ".join(m["content"] for m in sent)
        check("11b. proposal's boundaries text reached the model despite the tight budget",
              BASE_PROPOSAL_FIELDS["boundaries"] in sent_text, sent_text)
        check("11c. some unrelated older filler history was trimmed to make room",
              body["brain_message"]["context_used"]["history_messages_omitted"], body["brain_message"])
        workbench_app.WORKBENCH_CONTEXT_CHAR_BUDGET = orig_budget

        # essential context (system + proposal fields + message) too big
        # even alone -> honest overflow, refused before the gateway.
        workbench_app.WORKBENCH_CONTEXT_CHAR_BUDGET = 40
        workbench_app._call_brain_gateway = lambda messages, timeout=60.0: (
            None, "should not be called — overflow must refuse before this")
        resp = client.post(
            f"/api/workbench/projects/{p11}/messages",
            json={
                "message": "another tweak", "request_id": "revise-11-overflow",
                "mode": "revise_proposal", "proposal_id": proposal_11,
            },
        )
        body = resp.get_json()
        check("11d. essential proposal context too big for the budget -> honest overflow",
              body["brain_message"]["status"] == "failed" and
              "context overflow" in (body["brain_message"]["error"] or ""), body)
        workbench_app.WORKBENCH_CONTEXT_CHAR_BUDGET = orig_budget

        # ══ 13. Exact CORRECTION2.md reproduction: an old confirmation ══
        # request must never bless a stale card as a newer revision, must
        # never trigger a second model call on a rejected replay, and the
        # invalidation must hold at the authoritative boundary (ask
        # revision, which card_runner.dispatch() itself checks) — not just
        # workbench's own confirmed_revision bookkeeping.
        p13 = new_project("Scenario 13 (correction re-review)")
        resp = draft(p13, QUOTE + " for scenario thirteen", "draft-13",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" + _proposal_block())
        proposal_13 = resp.get_json()["proposal"]["id"]

        generator_calls_13 = []

        def gen13(payload):
            generator_calls_13.append(payload)
            return (MODEL_CARD_TEXT.replace("test-conv-action", "test-conv-action-13")
                    .replace(QUOTE, QUOTE + " for scenario thirteen")), None, None

        card_factory_app._call_generator = gen13
        resp = client.post(f"/api/workbench/proposals/{proposal_13}/confirm-direction",
                            json={"request_id": "confirm-1"})
        body13 = resp.get_json()
        check("13a. initial confirm-direction -> 201", resp.status_code == 201, (resp.status_code, body13))
        old_card_id = body13["card"]["id"]
        ask_id_13 = body13["proposal"]["card_factory_ask_id"]
        check("13b. exactly one generator call so far", len(generator_calls_13) == 1, generator_calls_13)

        # PATCH action/boundaries only — "mock-up only, no application
        # edits" — exactly the reproduction's own correction.
        resp = client.patch(
            f"/api/workbench/proposals/{proposal_13}",
            json={"action": "mock-up only, no application edits",
                  "boundaries": "no application edits"},
        )
        rev_after_patch = resp.get_json()["proposal"]["revision"]
        check("13c. revision bumped by the correction", rev_after_patch == 2, resp.get_json())

        ask_row_13 = sqlite3.connect(db_path).execute(
            "SELECT revision FROM card_factory_asks WHERE id = ?", (ask_id_13,)
        ).fetchone()
        check("13d. the underlying ask's own revision is ALSO bumped by an "
              "action/boundary-only correction (the authoritative boundary "
              "card_runner.dispatch() itself checks)",
              ask_row_13[0] == 2, ask_row_13)

        # Replay the OLD confirm-1 request_id after the correction.
        resp = client.post(f"/api/workbench/proposals/{proposal_13}/confirm-direction",
                            json={"request_id": "confirm-1"})
        check("13e. replaying an old confirm request_id after a correction "
              "is rejected (409), not silently accepted as the new revision",
              resp.status_code == 409, (resp.status_code, resp.get_json()))
        check("13f. rejecting the replay made NO additional generator call",
              len(generator_calls_13) == 1, generator_calls_13)
        after_replay = client.get(f"/api/workbench/proposals/{proposal_13}").get_json()["proposal"]
        check("13g. the proposal's card_factory_card_id/confirmed_revision "
              "were NOT relabeled by the rejected replay",
              after_replay["card_factory_card_id"] == old_card_id and
              after_replay["confirmed_revision"] != after_replay["revision"],
              after_replay)

        # A second replay of the same now-stale request_id is still
        # rejected, not resurrected.
        resp = client.post(f"/api/workbench/proposals/{proposal_13}/confirm-direction",
                            json={"request_id": "confirm-1"})
        check("13h. replaying confirm-1 again is still rejected (never resurrected)",
              resp.status_code == 409, resp.get_json())

        # Acceptance (3): a NEW request_id after the correction gets the
        # corrected full proposal and can be explicitly approved.
        resp = client.post(f"/api/workbench/proposals/{proposal_13}/confirm-direction",
                            json={"request_id": "confirm-2"})
        body13b = resp.get_json()
        check("13i. a new request_id after correction -> 201, fresh generator call",
              resp.status_code == 201 and len(generator_calls_13) == 2, (resp.status_code, body13b))
        new_card_id = body13b["card"]["id"]
        check("13j. the new card is a different row from the stale one",
              new_card_id != old_card_id, (new_card_id, old_card_id))
        payload_13 = generator_calls_13[-1]["text"]
        check("13k. the fresh generation carries the corrected action/boundaries",
              "mock-up only, no application edits" in payload_13, payload_13)

        # Acceptance (2): replaying confirm-2 at an UNCHANGED revision
        # stays idempotent — no third generator call, same card returned.
        resp = client.post(f"/api/workbench/proposals/{proposal_13}/confirm-direction",
                            json={"request_id": "confirm-2"})
        body13c = resp.get_json()
        check("13l. replaying confirm-2 at an unchanged revision is "
              "idempotent (no new generator call, same card)",
              len(generator_calls_13) == 2 and body13c["card"]["id"] == new_card_id,
              (generator_calls_13, body13c))

        fp13 = card_runner._sha256_text(body13b["card"]["card_text"])
        card_runner._TEST_COMMAND_OVERRIDE = _mock_claude(message="scenario 13 ok")
        try:
            resp = client.post(
                f"/api/workbench/proposals/{proposal_13}/approve",
                json={
                    "target": "claude", "request_id": "approve-13", "authorized_by": "eric",
                    "expected_card_fingerprint": fp13, "permitted_files": ["runtime/x.py"],
                    "accept_time_only_control": True,
                    "expected_proposal_revision": body13c["proposal"]["revision"],
                },
            )
            body = resp.get_json()
            check("13m. approving the corrected/fresh revision -> 201", resp.status_code == 201,
                  (resp.status_code, body))
            run_id_13 = body["run"]["id"]
            terminal = wait_terminal(run_id_13)
            check("13n. mock result reached", terminal["status"] == "completed", terminal)
        finally:
            card_runner._TEST_COMMAND_OVERRIDE = None

        # Acceptance (4): direct runner dispatch cannot execute the OLD,
        # invalidated card, even calling dispatch() directly (bypassing
        # workbench's approve route entirely) — proves the invalidation
        # lives at the authoritative boundary, not just workbench's own
        # bookkeeping.
        old_card_text = sqlite3.connect(db_path).execute(
            "SELECT card_text FROM card_factory_cards WHERE id = ?", (old_card_id,)
        ).fetchone()[0]
        fp_old = card_runner._sha256_text(old_card_text)
        try:
            card_runner.dispatch(
                card_factory_card_id=old_card_id, mode="implement", target="claude",
                request_id="direct-dispatch-old-card", expected_card_fingerprint=fp_old,
                authorized_by="eric", permitted_files=["runtime/x.py"],
                accept_time_only_control=True,
            )
            direct_dispatch_blocked = False
        except card_runner.RevisionMismatch:
            direct_dispatch_blocked = True
        check("13o. direct card_runner.dispatch() on the old card is "
              "refused (RevisionMismatch) — the invalidation is enforced "
              "at the authoritative boundary, not just workbench's own "
              "fields",
              direct_dispatch_blocked, None)

        # ══ 14. Atomic correction: a rejected ask-side update must never ══
        # leave a partially-applied proposal correction (independent
        # review's exact reproduction: PATCH returns HTTP 200 with
        # revisions (2,1,1), old card still directly dispatchable).
        p14 = new_project("Scenario 14 (atomic correction)")
        resp = draft(p14, QUOTE + " for scenario fourteen", "draft-14",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" + _proposal_block())
        proposal_14 = resp.get_json()["proposal"]["id"]
        card_factory_app._call_generator = lambda payload: (
            MODEL_CARD_TEXT.replace("test-conv-action", "test-conv-action-14")
            .replace(QUOTE, QUOTE + " for scenario fourteen"), None, None
        )
        resp = client.post(f"/api/workbench/proposals/{proposal_14}/confirm-direction",
                            json={"request_id": "confirm-14-1"})
        body14 = resp.get_json()
        old_card_id_14 = body14["card"]["id"]
        ask_id_14 = body14["proposal"]["card_factory_ask_id"]
        proposal_rev_before = body14["proposal"]["revision"]

        def ask_rev(aid):
            return sqlite3.connect(db_path).execute(
                "SELECT revision FROM card_factory_asks WHERE id = ?", (aid,)
            ).fetchone()[0]

        def card_ask_rev(cid):
            return sqlite3.connect(db_path).execute(
                "SELECT ask_revision FROM card_factory_cards WHERE id = ?", (cid,)
            ).fetchone()[0]

        ask_rev_before = ask_rev(ask_id_14)
        card_ask_rev_before = card_ask_rev(old_card_id_14)
        check("14a. baseline: proposal/ask/card revisions all consistent",
              proposal_rev_before == ask_rev_before == card_ask_rev_before == 1,
              (proposal_rev_before, ask_rev_before, card_ask_rev_before))

        # Exact reproduction: action corrected AND success_criteria pushed
        # one character over MAX_DONE_WHEN_CHARS in the same PATCH.
        oversized = "x" * (card_factory_app.MAX_DONE_WHEN_CHARS + 1)
        resp = client.patch(
            f"/api/workbench/proposals/{proposal_14}",
            json={"action": "mock-up only", "success_criteria": oversized},
        )
        check("14b. rejected correction never returns HTTP 200",
              resp.status_code != 200, (resp.status_code, resp.get_json()))
        after14 = client.get(f"/api/workbench/proposals/{proposal_14}").get_json()["proposal"]
        check("14c. proposal revision NOT partially bumped by the rejected correction",
              after14["revision"] == proposal_rev_before, (after14["revision"], proposal_rev_before))
        check("14d. proposal's action field NOT partially applied either",
              after14["action"] != "mock-up only", after14)
        check("14e. ask revision unchanged (never a (2,1,1)-shaped mix)",
              ask_rev(ask_id_14) == ask_rev_before, (ask_rev(ask_id_14), ask_rev_before))
        check("14f. card's own ask_revision unchanged too",
              card_ask_rev(old_card_id_14) == card_ask_rev_before,
              (card_ask_rev(old_card_id_14), card_ask_rev_before))

        # Nothing actually changed, so the still-current, still-valid old
        # card legitimately remains dispatchable — proving the rejection
        # didn't corrupt state, rather than accidentally over-blocking too.
        old_card_text_14 = sqlite3.connect(db_path).execute(
            "SELECT card_text FROM card_factory_cards WHERE id = ?", (old_card_id_14,)
        ).fetchone()[0]
        fp14 = card_runner._sha256_text(old_card_text_14)
        card_runner._TEST_COMMAND_OVERRIDE = _mock_claude(message="scenario 14 ok")
        try:
            resp = client.post(
                f"/api/workbench/proposals/{proposal_14}/approve",
                json={
                    "target": "claude", "request_id": "approve-14", "authorized_by": "eric",
                    "expected_card_fingerprint": fp14, "permitted_files": ["runtime/x.py"],
                    "accept_time_only_control": True,
                    "expected_proposal_revision": proposal_rev_before,
                },
            )
            check("14g. the untouched proposal still approves normally "
                  "(rejection didn't corrupt the still-valid state)",
                  resp.status_code == 201, (resp.status_code, resp.get_json()))
            run_id_14 = resp.get_json()["run"]["id"]
            terminal = wait_terminal(run_id_14)
            check("14h. mock result reached", terminal["status"] == "completed", terminal)
        finally:
            card_runner._TEST_COMMAND_OVERRIDE = None

        # A VALID correction (within bounds) still succeeds and still
        # atomically invalidates — the previous pass's fix, retained.
        resp = client.patch(
            f"/api/workbench/proposals/{proposal_14}",
            json={"boundaries": "no application edits, valid length"},
        )
        check("14i. a within-bounds correction still succeeds -> 200",
              resp.status_code == 200, resp.get_json())
        check("14j. and DOES bump the ask revision (still invalidated when "
              "the correction is actually valid)",
              ask_rev(ask_id_14) == ask_rev_before + 1, (ask_rev(ask_id_14), ask_rev_before))

        # ══ 15. Work already approved/dispatched before a later correction ══
        # is a distinct case — its own run record is unaffected by a
        # correction that happens afterward.
        snapshot_15 = card_runner.run_status(run_id_14)
        resp = client.patch(f"/api/workbench/proposals/{proposal_14}",
                             json={"outcome": "a later, unrelated correction"})
        check("15a. a later correction doesn't retroactively touch the "
              "earlier, already-completed run",
              resp.status_code == 200 and
              card_runner.run_status(run_id_14)["status"] == snapshot_15["status"] == "completed",
              None)

        # ══ 16. No execution anywhere from clarification/drafting/revising ══
        # beyond the explicitly approved runs.
        total_runs = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM card_runner_runs").fetchone()[0]
        check("16a. exactly the four approved runs exist (1, 10, 13, 14), nothing extra",
              total_runs == 4, total_runs)

        # ══ 17. Proposed scope (permitted_files/permitted_commands) — the ══
        # CORRECTION.md pass's own addition, so approval never requires
        # Eric to hand-type technical file paths: the model proposes them
        # on the SAME single draft_proposal call, no second call, stored
        # alongside every other structured field.
        p17 = new_project("Scenario 17")
        resp = draft(p17, QUOTE + " for scenario seventeen", "draft-17",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" + _proposal_block(
                         permitted_files=["runtime/ui/src/App.jsx", "runtime/ui/src/api.js"],
                         permitted_commands=["npm run build"],
                     ))
        proposal_17 = resp.get_json()["proposal"]
        check("17a. permitted_files parsed and stored from the model's proposal block",
              proposal_17["permitted_files"] == ["runtime/ui/src/App.jsx", "runtime/ui/src/api.js"],
              proposal_17)
        check("17b. permitted_commands parsed and stored from the model's proposal block",
              proposal_17["permitted_commands"] == ["npm run build"], proposal_17)

        # malformed scope (not a list) never fabricated into something else,
        # never crashes the parse — defaults to an explicit empty list.
        p17m = new_project("Scenario 17 malformed")
        malformed_block = dict(BASE_PROPOSAL_FIELDS)
        malformed_block["permitted_files"] = "not-a-list"
        malformed_block["permitted_commands"] = None
        resp = draft(p17m, QUOTE + " for scenario seventeen malformed", "draft-17m",
                     f"ok\n{workbench_app.PROPOSAL_MARKER}\n" + json.dumps(malformed_block))
        proposal_17m = resp.get_json()["proposal"]
        check("17c. malformed permitted_files defaults to an empty list, proposal still created",
              proposal_17m is not None and proposal_17m["permitted_files"] == [], proposal_17m)
        check("17d. malformed permitted_commands defaults to an empty list",
              proposal_17m["permitted_commands"] == [], proposal_17m)

        # revise_proposal: an UNCHANGED scope list must not spuriously bump
        # revision (the JSON-vs-Python-list comparison must not false-positive).
        rev_before_same_scope = proposal_17["revision"]

        def revise_same_scope(messages, timeout=60.0):
            return (
                "No change needed.\n" + workbench_app.PROPOSAL_MARKER + "\n" +
                _proposal_block(
                    permitted_files=["runtime/ui/src/App.jsx", "runtime/ui/src/api.js"],
                    permitted_commands=["npm run build"],
                )
            ), None

        workbench_app._call_brain_gateway = revise_same_scope
        resp = client.post(
            f"/api/workbench/projects/{p17}/messages",
            json={
                "message": "that's fine as is", "request_id": "revise-17-same",
                "mode": "revise_proposal", "proposal_id": proposal_17["id"],
            },
        )
        check("17e. echoing the identical scope back does not bump revision",
              resp.get_json()["proposal"]["revision"] == rev_before_same_scope, resp.get_json())

        # revise_proposal: a CHANGED scope list bumps revision and persists
        # the new list, exactly like any other material field correction.
        def revise_new_scope(messages, timeout=60.0):
            return (
                "Narrowing scope.\n" + workbench_app.PROPOSAL_MARKER + "\n" +
                _proposal_block(permitted_files=["runtime/ui/src/App.jsx"], permitted_commands=[])
            ), None

        workbench_app._call_brain_gateway = revise_new_scope
        resp = client.post(
            f"/api/workbench/projects/{p17}/messages",
            json={
                "message": "actually just the one file, no build step", "request_id": "revise-17-diff",
                "mode": "revise_proposal", "proposal_id": proposal_17["id"],
            },
        )
        body17 = resp.get_json()
        check("17f. a narrower scope bumps revision",
              body17["proposal"]["revision"] > rev_before_same_scope, body17["proposal"])
        check("17g. the narrower permitted_files is what's now stored",
              body17["proposal"]["permitted_files"] == ["runtime/ui/src/App.jsx"], body17["proposal"])
        check("17h. permitted_commands cleared to empty is also persisted",
              body17["proposal"]["permitted_commands"] == [], body17["proposal"])

        # Technical PATCH route: same validation/storage, for the Card
        # Factory-style technical path.
        resp = client.patch(f"/api/workbench/proposals/{proposal_17['id']}",
                             json={"permitted_files": "not-a-list"})
        check("17i. PATCH rejects a non-list permitted_files with 400",
              resp.status_code == 400, (resp.status_code, resp.get_json()))
        resp = client.patch(f"/api/workbench/proposals/{proposal_17['id']}",
                             json={"permitted_files": ["a.py", 3]})
        check("17j. PATCH rejects a list containing a non-string with 400",
              resp.status_code == 400, (resp.status_code, resp.get_json()))
        resp = client.patch(f"/api/workbench/proposals/{proposal_17['id']}",
                             json={"permitted_files": ["runtime/ui/src/App.jsx", "runtime/ui/src/index.css"]})
        check("17k. PATCH with a valid list -> 200 and stored",
              resp.status_code == 200 and resp.get_json()["proposal"]["permitted_files"] ==
              ["runtime/ui/src/App.jsx", "runtime/ui/src/index.css"], (resp.status_code, resp.get_json()))

    finally:
        workbench_app._call_brain_gateway = orig_gateway
        card_factory_app._call_generator = orig_generator
        workbench_app.WORKBENCH_CONTEXT_CHAR_BUDGET = orig_budget
        card_runner._TEST_COMMAND_OVERRIDE = None
        if orig_db_path_env is None:
            os.environ.pop("CIS_SPINE_PATH", None)
        else:
            os.environ["CIS_SPINE_PATH"] = orig_db_path_env
        shutil.rmtree(tmp_root, ignore_errors=True)

    failed = [l for l, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
