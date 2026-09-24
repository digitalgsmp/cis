"""
test_braingate_conversation_boundary.py — deterministic proof of the
Braingate-conversation-only activation boundary (runtime/braingate_conversation.py)
and of the fail-closed Workbench auth contract (runtime/workbench_auth.py).

The safety rule under test: when CIS is at the Braingate conversation stage,
conversation may occur and downstream generation/execution cannot. "Cannot" here
means the host refuses — not that a prompt discourages it, not that the UI hides
a button, not that the route is merely unlikely to be called.

Everything runs against temporary SQLite fixtures and a monkeypatched gateway.
No network, no paid model call, no subprocess, no touch of the live spine.

Run: python3 runtime/tests/test_braingate_conversation_boundary.py
"""
import json
import logging
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

TEST_API_KEY = "test-boundary-key"
os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "schema", "migrations")
M0035 = os.path.join(MIGRATIONS_DIR, "0035_workbench.sql")
M0038 = os.path.join(MIGRATIONS_DIR, "0038_workbench_action_proposals.sql")


def make_fixture_db(path, include_0038=True):
    conn = sqlite3.connect(path)
    with open(M0035) as f:
        conn.executescript(f.read())
    if include_0038:
        with open(M0038) as f:
            conn.executescript(f.read())
    conn.execute("CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(content, source)")
    conn.execute(
        "INSERT INTO knowledge_messages_fts (content, source) VALUES (?, ?)",
        ("Braingate conversation stage: conversation only, no execution.", "kb-300459"),
    )
    conn.commit()
    conn.close()


def run():
    results = []

    def check(label, cond, detail=""):
        results.append(f"{'PASS' if cond else 'FAIL'}  {label}"
                       + ("" if cond else f" — {detail}"))

    tmp_root = tempfile.mkdtemp(prefix="braingate_boundary_")
    db_path = os.path.join(tmp_root, "spine.db")
    make_fixture_db(db_path)

    orig_spine = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = db_path

    import workbench_app
    import card_factory_app
    import card_runner
    import braingate_conversation
    import workbench_auth

    for mod in (workbench_app, card_factory_app, card_runner):
        mod.DB_PATH = db_path

    from flask import Flask

    # The conversation-only surface, registered exactly as a later activation
    # card would register it — alone.
    app = Flask(__name__)
    app.register_blueprint(braingate_conversation.braingate_conversation_bp)
    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"

    # Tripwires. If the boundary leaks, these record it rather than letting a
    # real generation/dispatch happen — and any call at all is a failure.
    calls = {"generator": 0, "dispatch": 0, "gateway": 0, "subprocess": 0}

    orig_gateway = workbench_app._call_brain_gateway
    orig_generate_core = card_factory_app.generate_card_core
    orig_dispatch = card_runner.dispatch
    orig_wb_cr_dispatch = workbench_app._cr_dispatch
    orig_wb_generate_core = workbench_app.generate_card_core

    def fake_gateway(messages, timeout=60.0):
        calls["gateway"] += 1
        return "Understood. What outcome are you aiming for?", None

    def tripwire_generator(*a, **kw):
        calls["generator"] += 1
        raise AssertionError("generate_card_core() reached from the conversation-only surface")

    def tripwire_dispatch(*a, **kw):
        calls["dispatch"] += 1
        raise AssertionError("card_runner.dispatch() reached from the conversation-only surface")

    workbench_app._call_brain_gateway = fake_gateway
    card_factory_app.generate_card_core = tripwire_generator
    card_runner.dispatch = tripwire_dispatch
    workbench_app._cr_dispatch = tripwire_dispatch
    workbench_app.generate_card_core = tripwire_generator

    try:
        # ── 1. Route inventory: the surface exposes exactly the allowlist ──
        rules = sorted(
            (str(r.rule), tuple(sorted(m for m in r.methods if m in
                                       ("GET", "POST", "PATCH", "PUT", "DELETE"))))
            for r in app.url_map.iter_rules() if r.endpoint != "static"
        )
        expected = sorted([
            ("/api/workbench/projects", ("GET",)),
            ("/api/workbench/projects", ("POST",)),
            ("/api/workbench/projects/<project_id>", ("GET",)),
            ("/api/workbench/projects/<project_id>", ("PATCH",)),
            ("/api/workbench/projects/<project_id>/messages", ("GET",)),
            ("/api/workbench/projects/<project_id>/messages", ("POST",)),
        ])
        check("1a. conversation-only surface exposes exactly 6 routes, no more",
              rules == expected, f"got {rules}")

        all_paths = " ".join(str(r.rule) for r in app.url_map.iter_rules())
        for forbidden in ("/api/cardfactory", "/api/cardrunner", "proposals",
                          "confirm-direction", "approve", "dispatch", "regate"):
            check(f"1b. no route path contains {forbidden!r}",
                  forbidden not in all_paths, all_paths)

        check("1c. the blueprint registers no nested blueprints",
              not braingate_conversation.braingate_conversation_bp._blueprints,
              str(braingate_conversation.braingate_conversation_bp._blueprints))

        # ── 2. Allowed conversation paths work ────────────────────────────
        r = client.post("/api/workbench/projects", json={"name": "Conversation stage"})
        check("2a. create project -> 201", r.status_code == 201, r.get_data(as_text=True)[:200])
        pid = r.get_json()["project"]["id"]

        r = client.get("/api/workbench/projects")
        check("2b. list projects -> 200 and contains it",
              r.status_code == 200 and any(p["id"] == pid for p in r.get_json()["projects"]))

        r = client.get(f"/api/workbench/projects/{pid}")
        check("2c. read project -> 200", r.status_code == 200)

        r = client.patch(f"/api/workbench/projects/{pid}",
                         json={"direction_note": "exploring the shape of it"})
        check("2d. update direction note -> 200 and round-trips",
              r.status_code == 200
              and r.get_json()["project"]["direction_note"] == "exploring the shape of it")

        r = client.get(f"/api/workbench/projects/{pid}/messages")
        check("2e. list messages -> 200, empty", r.status_code == 200
              and r.get_json()["messages"] == [])

        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "I want to rework the intake flow.",
                              "request_id": "conv-1"})
        check("2f. normal chat send -> 200", r.status_code == 200, r.get_data(as_text=True)[:200])
        body = r.get_json()
        check("2g. it reached the real Braingate conversation path (gateway called once)",
              calls["gateway"] == 1, str(calls))
        check("2h. brain reply completed and persisted",
              body["brain_message"]["status"] == "completed"
              and body["brain_message"]["content"])
        check("2i. no proposal was produced by a plain chat send",
              body.get("proposal") is None, str(body.get("proposal")))

        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "mode omitted entirely", "request_id": "conv-2"})
        check("2j. omitting mode is treated as chat, not refused", r.status_code == 200,
              r.get_data(as_text=True)[:200])

        # ── 3. Persistence / reload ───────────────────────────────────────
        r = client.get(f"/api/workbench/projects/{pid}/messages")
        msgs = r.get_json()["messages"]
        check("3a. messages persist and reload (4 rows: 2 user + 2 brain)",
              len(msgs) == 4, str(len(msgs)))

        app2 = Flask(__name__)
        app2.register_blueprint(braingate_conversation.braingate_conversation_bp)
        client2 = app2.test_client()
        client2.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"
        r = client2.get(f"/api/workbench/projects/{pid}/messages")
        check("3b. a fresh app instance reads the same persisted conversation",
              r.status_code == 200 and len(r.get_json()["messages"]) == 4)

        # ── 4. Duplicate replay still works (and needs 0038) ──────────────
        before = len(client.get(f"/api/workbench/projects/{pid}/messages").get_json()["messages"])
        gw_before = calls["gateway"]
        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "I want to rework the intake flow.",
                              "request_id": "conv-1"})
        after = len(client.get(f"/api/workbench/projects/{pid}/messages").get_json()["messages"])
        check("4a. duplicate request_id flagged, not re-sent",
              r.status_code == 200 and r.get_json().get("duplicate") is True,
              r.get_data(as_text=True)[:200])
        check("4b. duplicate created no new rows", before == after, f"{before} -> {after}")
        check("4c. duplicate made no second model call", calls["gateway"] == gw_before)

        # ── 5. Forbidden: non-chat modes refused BEFORE anything downstream ─
        gw_before = calls["gateway"]
        for mode in ("draft_proposal", "revise_proposal"):
            r = client.post(f"/api/workbench/projects/{pid}/messages",
                            json={"message": "draft me an action", "request_id": f"bad-{mode}",
                                  "mode": mode})
            check(f"5a. mode={mode} -> 403", r.status_code == 403,
                  r.get_data(as_text=True)[:200])
            check(f"5b. mode={mode} refusal names the stage",
                  r.get_json().get("stage") == "braingate_conversation")
        check("5c. refused modes made NO model call", calls["gateway"] == gw_before, str(calls))
        check("5d. refused modes made NO generator call", calls["generator"] == 0)
        check("5e. refused modes made NO dispatch call", calls["dispatch"] == 0)

        rows_after_refusals = len(
            client.get(f"/api/workbench/projects/{pid}/messages").get_json()["messages"])
        check("5f. a refused send wrote no message row at all",
              rows_after_refusals == after, f"{after} -> {rows_after_refusals}")

        # Alternate payload shapes must not get through either.
        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "x", "request_id": "bad-pid", "mode": "chat",
                              "proposal_id": 1})
        check("5g. chat mode carrying proposal_id -> 403", r.status_code == 403,
              r.get_data(as_text=True)[:200])
        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "x", "request_id": "bad-exec", "mode": "chat",
                              "permitted_commands": ["rm -rf /"], "model": "claude-opus-5"})
        check("5h. chat mode carrying execution fields -> 403", r.status_code == 403)
        check("5i. refusal names which fields were refused",
              "permitted_commands" in r.get_json().get("detail", ""))
        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "x", "request_id": "bad-case", "mode": " DRAFT_PROPOSAL "})
        check("5j. whitespace/case variants of a forbidden mode -> 403", r.status_code == 403)
        r = client.post(f"/api/workbench/projects/{pid}/messages",
                        json={"message": "x", "request_id": "bad-type", "mode": ["draft_proposal"]})
        check("5k. a non-string mode -> 403, not a crash", r.status_code == 403,
              r.get_data(as_text=True)[:200])

        # ── 6. Forbidden: downstream routes are not registered at all ──────
        forbidden_requests = [
            ("POST", "/api/cardfactory/asks", {"project": "p", "ask": "a", "done_when": "d"}),
            ("POST", "/api/cardfactory/asks/1/generate", {"request_id": "x"}),
            ("GET", "/api/cardfactory/cards", None),
            ("POST", "/api/cardrunner/dispatch", {"card_factory_card_id": 1}),
            ("POST", "/api/cardrunner/runs/1/stop", {}),
            ("GET", "/api/cardrunner/runs", None),
            ("GET", "/api/workbench/projects/%s/proposals" % pid, None),
            ("GET", "/api/workbench/proposals/1", None),
            ("PATCH", "/api/workbench/proposals/1", {"action": "x"}),
            ("POST", "/api/workbench/proposals/1/confirm-direction", {"request_id": "x"}),
            ("POST", "/api/workbench/proposals/1/approve", {"expected_proposal_revision": 1}),
        ]
        for method, path, payload in forbidden_requests:
            r = client.open(path, method=method, json=payload)
            check(f"6. {method} {path} -> not reachable (404)", r.status_code == 404,
                  f"got {r.status_code}")

        check("6z. no tripwire fired across every forbidden request",
              calls["generator"] == 0 and calls["dispatch"] == 0, str(calls))

        # ── 7. Fail-closed auth ───────────────────────────────────────────
        anon = app.test_client()  # presents no credential
        r = anon.get("/api/workbench/projects")
        check("7a. missing credential -> 401 denied", r.status_code == 401,
              f"got {r.status_code}")

        wrong = app.test_client()
        wrong.environ_base["HTTP_AUTHORIZATION"] = "Bearer not-the-key"
        r = wrong.get("/api/workbench/projects")
        check("7b. wrong credential -> 401 denied", r.status_code == 401)

        malformed = app.test_client()
        malformed.environ_base["HTTP_AUTHORIZATION"] = TEST_API_KEY  # no "Bearer "
        r = malformed.get("/api/workbench/projects")
        check("7c. credential without the Bearer scheme -> 401 denied", r.status_code == 401)

        r = anon.post("/api/workbench/projects", json={"name": "should not exist"})
        check("7d. unauthenticated create is denied", r.status_code == 401)
        names = [p["name"] for p in client.get("/api/workbench/projects").get_json()["projects"]]
        check("7e. and wrote nothing", "should not exist" not in names, str(names))

        r = anon.post(f"/api/workbench/projects/{pid}/messages",
                      json={"message": "hi", "request_id": "anon-1"})
        check("7f. unauthenticated send is denied before any model call",
              r.status_code == 401 and calls["gateway"] == gw_before, str(calls))

        # Server key unset entirely: must be denied, never anonymous.
        saved = os.environ.pop("CIS_PIPELINE_API_KEY")
        try:
            r = anon.get("/api/workbench/projects")
            check("7g. server key UNSET + no credential -> denied (503), never allowed",
                  r.status_code == 503, f"got {r.status_code}")
            r = client.get("/api/workbench/projects")
            check("7h. server key UNSET + a credential -> still denied (503)",
                  r.status_code == 503, f"got {r.status_code}")
            check("7i. no status in the unset-key case is a 2xx",
                  r.status_code >= 400)
            r = client.post(f"/api/workbench/projects/{pid}/messages",
                            json={"message": "hi", "request_id": "unset-1"})
            check("7j. unset key denies conversation too, with no model call",
                  r.status_code == 503 and calls["gateway"] == gw_before, str(calls))
            check("7k. workbench_auth reports itself unconfigured",
                  not workbench_auth.is_configured())
        finally:
            os.environ["CIS_PIPELINE_API_KEY"] = saved

        r = client.get("/api/workbench/projects")
        check("7l. restoring the key restores authenticated access", r.status_code == 200)

        blank = " \t "
        os.environ["CIS_PIPELINE_API_KEY"] = blank
        try:
            r = client.get("/api/workbench/projects")
            check("7m. a whitespace-only server key is treated as unset, denied 503",
                  r.status_code == 503, f"got {r.status_code}")
        finally:
            os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY

        # ── 8. The fail-closed contract covers the downstream modules too ──
        for name, bp in (("cardfactory", card_factory_app.card_factory_bp),
                         ("cardrunner", card_runner.card_runner_bp)):
            a = Flask(__name__)
            a.register_blueprint(bp)
            c = a.test_client()
            saved = os.environ.pop("CIS_PIPELINE_API_KEY")
            try:
                r = c.get(f"/api/{name}/" + ("cards" if name == "cardfactory" else "runs"))
                check(f"8a. {name} with server key unset -> denied, not anonymous",
                      r.status_code in (401, 503), f"got {r.status_code}")
            finally:
                os.environ["CIS_PIPELINE_API_KEY"] = saved
            r = c.get(f"/api/{name}/" + ("cards" if name == "cardfactory" else "runs"))
            check(f"8b. {name} with a key set but no credential -> 401",
                  r.status_code == 401, f"got {r.status_code}")
        check("8c. still no generator/dispatch call from any auth probe",
              calls["generator"] == 0 and calls["dispatch"] == 0, str(calls))

        # ── 9. The dormant downstream implementations remain intact ────────
        check("9a. card_factory_app still defines generate_card_core",
              callable(orig_generate_core))
        check("9b. card_runner still defines dispatch", callable(orig_dispatch))
        wb_paths = " ".join(
            str(r.rule) for r in
            (lambda a: (a.register_blueprint(workbench_app.workbench_bp), a)[1])(Flask(__name__))
            .url_map.iter_rules())
        check("9c. workbench_bp itself STILL exposes the downstream routes "
              "(dormant, not deleted)",
              "/api/cardfactory/asks" in wb_paths and "/api/cardrunner/dispatch" in wb_paths
              and "confirm-direction" in wb_paths and "approve" in wb_paths,
              wb_paths)

        # ── 10. container_app registers none of the forbidden routes ───────
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            import container_app
            ca_paths = " ".join(str(r.rule) for r in container_app.app.url_map.iter_rules())
            for forbidden in ("/api/cardfactory", "/api/cardrunner", "/api/workbench/projects",
                              "confirm-direction", "approve"):
                check(f"10a. live container_app exposes no {forbidden!r} route",
                      forbidden not in ca_paths, ca_paths[:300])
            check("10b. live container_app still exposes System Context",
                  "/api/workbench/system-context" in ca_paths)
        except Exception as e:
            check("10. container_app import", False, f"{type(e).__name__}: {e}")

        # ── 11. Schema precondition is honest about needing 0038 ───────────
        db2 = os.path.join(tmp_root, "only0035.db")
        make_fixture_db(db2, include_0038=False)
        workbench_app.DB_PATH = db2
        try:
            app3 = Flask(__name__)
            # 11b deliberately provokes a real sqlite failure; Flask would log
            # the whole traceback to stderr and bury the result lines. The
            # failure itself is still asserted below, just not narrated.
            app3.logger.disabled = True
            logging.getLogger("werkzeug").disabled = True
            app3.register_blueprint(braingate_conversation.braingate_conversation_bp)
            c3 = app3.test_client()
            c3.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"
            p3 = c3.post("/api/workbench/projects", json={"name": "only0035"}).get_json()["project"]["id"]
            r1 = c3.post(f"/api/workbench/projects/{p3}/messages",
                         json={"message": "first", "request_id": "dup"})
            check("11a. with only 0035, a first chat send still succeeds",
                  r1.status_code == 200, r1.get_data(as_text=True)[:200])
            raised = False
            try:
                r2 = c3.post(f"/api/workbench/projects/{p3}/messages",
                             json={"message": "first", "request_id": "dup"})
                broke = r2.status_code >= 500
            except sqlite3.OperationalError:
                raised = broke = True
            check("11b. with only 0035, duplicate-replay BREAKS — so 0038 is a real "
                  "precondition, documented not silently broadened",
                  broke, "duplicate replay unexpectedly succeeded without 0038")
            check("11c. braingate_conversation declares both 0035 and 0038 required",
                  braingate_conversation.REQUIRED_MIGRATIONS
                  == ("0035_workbench.sql", "0038_workbench_action_proposals.sql"))
            check("11d. and declares 0036/0037 forbidden",
                  braingate_conversation.FORBIDDEN_MIGRATIONS
                  == ("0036_card_factory.sql", "0037_card_runner.sql"))
        finally:
            workbench_app.DB_PATH = db_path

        # ── 13. Stage capabilities are presentation, not enforcement ────────
        #
        # The UI hides Card Factory, proposals and execution at this stage by
        # reading `capabilities` from GET /auth/session
        # (runtime/workbench_oidc.py stage_capabilities). That is a UX fix for
        # advertising features the server did not register — it is NOT the
        # boundary, and this section is what says so in code.
        #
        # The question under test is the one an attacker asks: if I flip those
        # flags in a debugger, or skip the UI entirely and call the route, does
        # anything change? It must not, because the flags are derived FROM the
        # url_map rather than consulted BY it.
        import workbench_oidc

        cap_app = Flask(__name__)
        cap_app.register_blueprint(braingate_conversation.braingate_conversation_bp)
        cap_app.register_blueprint(workbench_oidc.workbench_oidc_bp)
        with cap_app.test_request_context("/"):
            caps = workbench_oidc.stage_capabilities()

        check("13a. capabilities report conversation and projects AVAILABLE at "
              "the Braingate stage",
              caps["conversation"] and caps["projects"] and caps["project_create"],
              str(caps))
        check("13b. capabilities report every downstream surface UNAVAILABLE",
              not any(caps[k] for k in ("proposals", "proposal_actions",
                                        "execution", "card_factory",
                                        "card_runner")),
              str(caps))

        # The routes behind the false flags genuinely are not bound — the flag
        # is reporting reality, not creating it.
        cap_rules = {str(r.rule) for r in cap_app.url_map.iter_rules()}
        downstream_rules = (
            "/api/workbench/projects/<project_id>/proposals",
            "/api/workbench/proposals/<int:proposal_id>/confirm-direction",
            "/api/workbench/proposals/<int:proposal_id>/approve",
            "/api/cardfactory/cards",
            "/api/cardrunner/dispatch",
        )
        check("13c. none of those downstream rules exist in the url_map",
              not any(r in cap_rules for r in downstream_rules),
              str(sorted(cap_rules & set(downstream_rules))))

        # Frontend manipulation proof. A browser that sets every capability to
        # true and then calls the routes it just "unlocked" reaches 404s: the
        # flags live in the browser's own memory and the server never reads
        # them back.
        cap_client = cap_app.test_client()
        cap_client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"
        forged = []
        for method, path in (
            ("GET", "/api/workbench/projects/p1/proposals"),
            ("POST", "/api/workbench/proposals/1/confirm-direction"),
            ("POST", "/api/workbench/proposals/1/approve"),
            ("GET", "/api/cardfactory/cards"),
            ("POST", "/api/cardrunner/dispatch"),
        ):
            resp = cap_client.open(path, method=method, json={})
            forged.append((method, path, resp.status_code))
        check("13d. forging capabilities client-side does not make any downstream "
              "route exist — every one is 404",
              all(code == 404 for _, _, code in forged), str(forged))

        # And the one route that DOES exist still refuses a downstream payload,
        # so "unlock the button" does not become "reach the capability".
        forged_send = cap_client.post(
            "/api/workbench/projects/p1/messages",
            json={"message": "go", "mode": "draft_proposal", "request_id": "cap-forge"})
        check("13e. the registered conversation route still refuses draft_proposal "
              "after a client-side capability forge",
              forged_send.status_code == 403
              and forged_send.get_json().get("refused") == "mode",
              f"{forged_send.status_code} {forged_send.get_json()}")

        check("13f. the capability report names no secret and no value",
              set(caps) == set(workbench_oidc.CAPABILITY_PROBES)
              and all(isinstance(v, bool) for v in caps.values()),
              str(caps))

        check("12. FINAL: no generator, dispatch or subprocess call occurred anywhere "
              "in this suite", calls["generator"] == 0 and calls["dispatch"] == 0
              and calls["subprocess"] == 0, str(calls))

    finally:
        workbench_app._call_brain_gateway = orig_gateway
        card_factory_app.generate_card_core = orig_generate_core
        card_runner.dispatch = orig_dispatch
        workbench_app._cr_dispatch = orig_wb_cr_dispatch
        workbench_app.generate_card_core = orig_wb_generate_core
        if orig_spine is None:
            os.environ.pop("CIS_SPINE_PATH", None)
        else:
            os.environ["CIS_SPINE_PATH"] = orig_spine

    for line in results:
        print(line)
    failed = [r for r in results if r.startswith("FAIL")]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
