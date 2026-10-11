#!/usr/bin/env python3
"""test_revision_127_containment.py — deterministic proof that the public
trust-boundary exposure recorded at dev_continuity_events revision 127 is
contained at the application layer.

WHAT REVISION 127 RECORDED, by measurement and not inference: two public
Cloudflare hostnames (workbench.* and api.creative-intelligence-system.com)
forward to runtime/container_app.py on localhost:5000, and of the routes that
listener registers only workbench_oidc_bp and braingate_conversation_bp checked
a credential. Everything else answered the open internet with 200 and real
data — the full canonical state and recovery packet, the build path, the
destination architecture, the project-intelligence composition, the enforcement
security audit, gateway health, gateway logs, and all of relay_bp including its
MUTATING routes. relay_bp's own auth was fail-open BY CONSTRUCTION:

    def _check_auth():
        if not API_KEY:
            return None          # <-- unset key = auth skipped entirely

and CIS_PIPELINE_API_KEY is empty in the running container.

WHAT THIS FILE PROVES. Seven properties, each as a property of the registered
surface rather than as a claim about it:

    A. Missing API-key configuration fails CLOSED, never open.
    B. An invalid API key is refused.
    C. Every protected route class denies an unauthenticated request.
    D. An unauthorized mutation attempt creates NOTHING — no workflow run, no
       dispatch, no approval, no project, no model call, no spine write.
    E. An authenticated owner session can still use the Workbench read models
       and the Braingate conversation surface.
    F. A valid, explicitly configured API credential works on the relay/API
       surface and does NOT widen the stage boundary.
    G. Card Factory and Card Runner remain unavailable at this phase.

HOW IT AVOIDS SPENDING ANYTHING. Every mutation route is exercised ONLY
unauthenticated, i.e. only in the case that must be refused before the body
runs. The pipeline entry points are additionally replaced with recording
sentinels that raise if they are ever entered, and `pipeline_relay` is
shadowed in sys.modules by a module whose PipelineRelay refuses to be
constructed. So "no model call occurred" is proven by the sentinels, not by
reading the code. No test touches the live spine for a write; the fixture
spine is a temporary file and its row counts are compared before and after.

Run: python3 runtime/tests/test_revision_127_containment.py
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Configuration, set BEFORE container_app is imported ──────────────────
# workbench_auth reads the environment on every call, so these are not
# load-order sensitive; they are set up front only so the module-level
# `from container_app import app` below sees a configured server.
TEST_API_KEY = "rev127-containment-api-key"
TEST_SESSION_SECRET = "rev127-containment-session-secret-0123456789abcdef"
OWNER_EMAIL = "owner@example.test"
STRANGER_EMAIL = "stranger@example.test"

os.environ["CIS_PIPELINE_API_KEY"] = TEST_API_KEY
os.environ["CIS_WORKBENCH_SESSION_SECRET"] = TEST_SESSION_SECRET
os.environ["CIS_WORKBENCH_ALLOWED_EMAILS"] = OWNER_EMAIL
os.environ["CIS_WORKBENCH_OWNER_EMAILS"] = OWNER_EMAIL
# The test client drives Flask over plain HTTP; without this the session
# cookie is Secure-only and never sent back.
os.environ["CIS_WORKBENCH_COOKIE_INSECURE"] = "1"

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "schema", "migrations")
M0035 = os.path.join(MIGRATIONS_DIR, "0035_workbench.sql")
M0038 = os.path.join(MIGRATIONS_DIR, "0038_workbench_action_proposals.sql")

results = []


def check(label, cond, detail=""):
    results.append(f"{'PASS' if cond else 'FAIL'}  {label}"
                   + ("" if cond else f" — {detail!r}"))


# ── The route census ─────────────────────────────────────────────────────
# Stated here rather than derived, so that a route ADDED later without a
# credential check fails test C3 ("the public set is exactly this") instead of
# quietly joining the public surface. This is the same technique the Braingate
# boundary test uses for route absence.

# Minimal fixed-result liveness + the sign-in lifecycle + the static SPA shell.
PUBLIC_ROUTES = {
    # Fixed health result only: no configuration, model, log, route inventory,
    # database state or project data. Permitted explicitly by the revision-127
    # containment card.
    ("GET", "/api/relay/ping"),
    ("GET", "/api/ping"),
    ("GET", "/api/health"),
    ("GET", "/health"),
    # The OIDC sign-in lifecycle. It CANNOT sit behind check_auth() — it is how
    # a credential is obtained in the first place. Each route guards itself:
    # login/callback enforce issuer/audience/nonce/PKCE and the server-side
    # allowlist, and session reports {"authenticated": false} to a stranger.
    ("GET", "/api/workbench/auth/login"),
    ("GET", "/api/workbench/auth/callback"),
    ("GET", "/api/workbench/auth/session"),
    ("POST", "/api/workbench/auth/logout"),
    # The static SPA shell and its redirect. Must load before sign-in; carries
    # no project state — every datum it displays comes from a protected route.
    ("GET", "/"),
    ("GET", "/ui/"),
    ("GET", "/ui/<path:filename>"),
    # A standalone static HTML page, not named by revision 127 and holding no
    # operational state of its own.
    ("GET", "/dashboard/"),
}

# The mutation routes revision 127 named, plus the two system-mutation routes
# found during the bounded inspection. Exercised unauthenticated only.
MUTATION_ROUTES = [
    ("POST", "/api/relay/start", {"intent": "rev127 must never run this"}),
    ("POST", "/api/relay/run", {"intent": "rev127 must never run this"}),
    ("POST", "/api/relay/rev127-nonexistent-run/gate",
     {"decision": "approve", "approved_by": "rev127-unauthorized"}),
    ("POST", "/api/relay/rev127-nonexistent-run/answer", {"answer": "no"}),
    ("POST", "/api/relay/rev127-nonexistent-run/decompose", {}),
    ("POST", "/api/relay/rev127-nonexistent-run/interject", {"message": "no"}),
    ("POST", "/api/projects",
     {"id": "rev127-unauthorized", "name": "rev127-unauthorized",
      "repo_path": "/tmp/rev127", "spine_path": "/tmp/rev127.db"}),
    ("POST", "/api/relay/brain/chat", {"message": "no"}),
    ("POST", "/api/relay/brain/start", {"intent": "no"}),
    ("POST", "/api/relay/system/restart", {"container": "cis-pipeline"}),
    ("POST", "/api/relay/system/restart-all", {}),
    ("POST", "/system/restart", {"container": "cis-pipeline"}),
    ("POST", "/system/restart-all", {}),
    ("POST", "/api/workbench/projects", {"name": "rev127-unauthorized"}),
    ("POST", "/api/workbench/projects/p1/messages", {"message": "no"}),
]

# The sensitive read surfaces revision 127 named, by its own wording.
PROTECTED_READS = [
    ("system context", "/api/workbench/system-context"),
    ("recovery packet", "/api/workbench/system-context/recovery-packet"),
    ("build path", "/api/workbench/build-path"),
    ("destination architecture", "/api/workbench/destination-architecture"),
    ("project intelligence", "/api/workbench/project-intelligence"),
    ("enforcement/security audit", "/api/relay/system/security"),
    ("gateway health (container_app)", "/api/relay/system/health"),
    ("gateway health (relay_bp)", "/api/relay/health"),
    ("gateway health (docker sweep)", "/system/health"),
    ("gateway logs (container_app)", "/api/relay/system/logs/cis-pipeline"),
    ("gateway logs (relay_bp)", "/system/logs/cis-pipeline"),
    ("relay runs", "/api/relay/runs"),
    ("relay metrics", "/api/relay/metrics"),
    ("KB decisions", "/api/relay/kb/decisions"),
    ("KB search", "/api/relay/kb/search?q=anything"),
    ("relay guardrails", "/api/relay/guardrails"),
    ("relay DLQ", "/api/relay/dlq"),
    ("relay run status", "/api/relay/rev127-nonexistent-run"),
    ("relay trace", "/api/relay/rev127-nonexistent-run/trace"),
    ("relay verify", "/api/relay/rev127-nonexistent-run/verify"),
    ("relay feed", "/api/relay/rev127-nonexistent-run/feed"),
    ("relay errors", "/api/relay/rev127-nonexistent-run/errors"),
    ("relay children", "/api/relay/rev127-nonexistent-run/children"),
    ("relay interjections", "/api/relay/rev127-nonexistent-run/interjections"),
    ("brain history", "/api/relay/brain/history/rev127"),
    ("project list", "/api/projects"),
    ("project overview", "/api/relay/project/rev127/overview"),
    ("project build plan", "/api/relay/project/rev127/build-plan"),
    ("workbench project list", "/api/workbench/projects"),
]

DENIED = (401, 403, 503)


# ── Fixtures ─────────────────────────────────────────────────────────────

def make_fixture_spine(path):
    """A spine carrying the tables an unauthorized mutation would write to, so
    that "nothing was written" is a measured row count and not an assumption."""
    conn = sqlite3.connect(path)
    with open(M0035) as f:
        conn.executescript(f.read())
    with open(M0038) as f:
        conn.executescript(f.read())
    conn.executescript("""
        CREATE TABLE workflow_runs (
            id TEXT PRIMARY KEY, topic TEXT, status TEXT, created_at TEXT,
            directive_hash TEXT, rounds_completed INTEGER, result TEXT
        );
        CREATE TABLE deliberation_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT,
            round_number INTEGER, drafter_role TEXT, drafter_output TEXT,
            reviewer_role TEXT, reviewer_signal TEXT, reviewer1_output TEXT,
            reviewer2_output TEXT, brain_output TEXT, verify_output TEXT,
            human_question TEXT, human_answer TEXT, created_at TEXT
        );
        CREATE TABLE agent_trajectories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, role TEXT,
            phase TEXT, round_number INTEGER, outcome TEXT, input_text TEXT,
            output_text TEXT, created_at TEXT
        );
        CREATE TABLE projects (
            id TEXT PRIMARY KEY, name TEXT, repo_path TEXT, spine_path TEXT,
            agents_md_path TEXT, status TEXT, created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE gate_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, decision TEXT,
            approved_by TEXT, created_at TEXT
        );
    """)
    conn.commit()
    conn.close()


def table_counts(path):
    conn = sqlite3.connect(path)
    try:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'").fetchall()]
        return {n: conn.execute(f"SELECT COUNT(*) FROM \"{n}\"").fetchone()[0]
                for n in names}
    finally:
        conn.close()


class Tripwire:
    """Records every call and then raises. Installed over every entry point an
    unauthorized mutation would have to cross, so a leak is recorded even if
    the route swallows the exception and answers 200."""

    def __init__(self, name):
        self.name = name
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        raise AssertionError(
            f"TRIPWIRE: {self.name} was entered by an unauthorized request")


def fake_pipeline_relay_module(tripwire):
    """A stand-in for `pipeline_relay`, which the mutation handlers import
    LAZILY inside the function body — i.e. only if auth has already passed."""
    mod = types.ModuleType("pipeline_relay")

    class PipelineRelay:
        def __init__(self, *a, **kw):
            tripwire("pipeline_relay.PipelineRelay()")

    mod.PipelineRelay = PipelineRelay
    return mod


def owner_cookie(client, email=OWNER_EMAIL, role="owner"):
    """A genuine session minted by the production signing primitive — not a
    hand-rolled cookie, so the test cannot pass against a build whose token
    format has drifted."""
    import workbench_auth
    token, payload = workbench_auth.issue_session_token(
        secret=TEST_SESSION_SECRET,
        max_age=workbench_auth.session_max_age_seconds(),
        subject=f"oidc|rev127|{email}",
        email=email,
        role=role,
        name="Rev127 Owner",
        issuer="https://rev127.example.test/",
    )
    client.set_cookie(
        "cis_workbench_session", token,
        domain="localhost", path=workbench_auth.SESSION_COOKIE_PATH,
    )
    return token, payload


def run():
    tmp_root = tempfile.mkdtemp(prefix="rev127_containment_")
    spine_path = os.path.join(tmp_root, "spine.db")
    make_fixture_spine(spine_path)

    orig_spine = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = spine_path

    import workbench_auth
    import workbench_app
    import card_factory_app
    import card_runner
    from api import relay
    import container_app
    from container_app import app

    # Every WRITABLE DB handle the app can reach is redirected at the fixture.
    # Nothing in this test may write to the live spine.
    relay.DB_PATH = spine_path
    for mod in (workbench_app, card_factory_app, card_runner):
        mod.DB_PATH = spine_path

    # The four Workbench read models are the exception, and deliberately so.
    # They resolve the spine through the single module-level constant
    # canonical_state.DB and open it with sqlite3's mode=ro URI, so they CANNOT
    # write. Pointing them at the LIVE spine is what makes sections E and F
    # meaningful: "the owner can still read the build path" has to mean the
    # real read model built from the real authority state, not a 503 from a
    # fixture that was never given a project_state table. CIS_SPINE_PATH was
    # set before container_app imported, so cs.DB currently points at the
    # fixture; this puts it back.
    import canonical_state as cs
    live_spine = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "data", "cis_memory.db")
    saved_cs_db = cs.DB
    cs.DB = live_spine

    saved = {
        "run_bg": relay._run_pipeline_background,
        "gateway": getattr(workbench_app, "_call_brain_gateway", None),
        "generate": getattr(card_factory_app, "generate_card_core", None),
        "dispatch": getattr(card_runner, "dispatch", None),
        "pipeline_relay": sys.modules.get("pipeline_relay"),
    }
    tripwires = {
        "pipeline_background": Tripwire("relay._run_pipeline_background"),
        "model_gateway": Tripwire("workbench_app._call_brain_gateway"),
        "card_generate": Tripwire("card_factory_app.generate_card_core"),
        "agent_dispatch": Tripwire("card_runner.dispatch"),
        "pipeline_relay": Tripwire("pipeline_relay.PipelineRelay"),
    }

    relay._run_pipeline_background = tripwires["pipeline_background"]
    workbench_app._call_brain_gateway = tripwires["model_gateway"]
    card_factory_app.generate_card_core = tripwires["card_generate"]
    card_runner.dispatch = tripwires["agent_dispatch"]
    sys.modules["pipeline_relay"] = fake_pipeline_relay_module(
        tripwires["pipeline_relay"])

    # TESTING stays OFF deliberately. With it on, Flask re-raises inside the
    # test client, and the minimal fixture spine cannot satisfy every read
    # query's schema (relay metrics wants token columns, for instance). A
    # schema mismatch must surface as a 500 RESPONSE so that "the credential
    # was accepted" (anything that is not a denial) stays separable from "the
    # credential was refused". A tripwire firing is still recorded on the
    # tripwire object, so D7 detects a leak either way.
    app.config["TESTING"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = False

    try:
        # ── A. missing API-key configuration fails CLOSED ─────────────────
        # The exact condition revision 127 measured in the live container.
        saved_key = os.environ.get("CIS_PIPELINE_API_KEY")
        saved_secret = os.environ.get("CIS_WORKBENCH_SESSION_SECRET")
        saved_allowed = os.environ.get("CIS_WORKBENCH_ALLOWED_EMAILS")

        os.environ["CIS_PIPELINE_API_KEY"] = ""
        check("A1. an empty CIS_PIPELINE_API_KEY is read as unset, not as a credential",
              workbench_auth.configured_api_key() == "",
              workbench_auth.configured_api_key())

        client = app.test_client()
        a_codes = {}
        for label, path in PROTECTED_READS:
            a_codes[label] = client.get(path).status_code
        check("A2. with the API key empty (the live container's state), every "
              "protected read still denies — the fail-open branch is gone",
              all(c in DENIED for c in a_codes.values()),
              {k: v for k, v in a_codes.items() if v not in DENIED})

        # Presenting ANY bearer token against an empty configured key must not
        # pass. This is the specific "" == "" comparison that fail-open hid.
        client_blank = app.test_client()
        client_blank.environ_base["HTTP_AUTHORIZATION"] = "Bearer "
        check("A3. a blank Bearer token does not match an empty configured key",
              client_blank.get("/api/relay/runs").status_code in DENIED,
              client_blank.get("/api/relay/runs").status_code)

        # And with NO mechanism at all configured, the contract is 503 — a
        # denial, never anonymous access.
        os.environ["CIS_WORKBENCH_SESSION_SECRET"] = ""
        os.environ["CIS_WORKBENCH_ALLOWED_EMAILS"] = ""
        check("A4. with NO authentication mechanism configured the server is "
              "not ready and denies (503), it does not fall open",
              not workbench_auth.is_configured()
              and app.test_client().get("/api/relay/runs").status_code == 503,
              app.test_client().get("/api/relay/runs").status_code)
        check("A5. an unconfigured server also denies the mutation routes",
              all(app.test_client().post(p, json=b).status_code in DENIED
                  for _, p, b in MUTATION_ROUTES),
              [(p, app.test_client().post(p, json=b).status_code)
               for _, p, b in MUTATION_ROUTES
               if app.test_client().post(p, json=b).status_code not in DENIED])

        os.environ["CIS_PIPELINE_API_KEY"] = saved_key
        os.environ["CIS_WORKBENCH_SESSION_SECRET"] = saved_secret
        os.environ["CIS_WORKBENCH_ALLOWED_EMAILS"] = saved_allowed

        # ── B. an invalid API key is refused ─────────────────────────────
        bad = app.test_client()
        bad.environ_base["HTTP_AUTHORIZATION"] = "Bearer not-the-configured-key"
        bad_codes = {label: bad.get(path).status_code
                     for label, path in PROTECTED_READS}
        check("B1. a wrong Bearer token is refused on every protected read",
              all(c in DENIED for c in bad_codes.values()),
              {k: v for k, v in bad_codes.items() if v not in DENIED})
        check("B2. a wrong Bearer token is refused on every mutation route",
              all(bad.post(p, json=b).status_code in DENIED
                  for _, p, b in MUTATION_ROUTES),
              [(p, bad.post(p, json=b).status_code)
               for _, p, b in MUTATION_ROUTES
               if bad.post(p, json=b).status_code not in DENIED])
        malformed = app.test_client()
        for header in ("", "Basic abc", "Bearer", "bearer " + TEST_API_KEY,
                       "Token " + TEST_API_KEY, TEST_API_KEY):
            malformed.environ_base["HTTP_AUTHORIZATION"] = header
            code = malformed.get("/api/relay/runs").status_code
            check(f"B3. malformed Authorization {header[:16]!r} is refused",
                  code in DENIED, code)

        # ── C. every protected route class denies unauthenticated ────────
        anon = app.test_client()
        anon_codes = {label: (path, anon.get(path).status_code)
                      for label, path in PROTECTED_READS}
        check("C1. every sensitive read surface revision 127 named denies an "
              "unauthenticated request (401/403/503)",
              all(c in DENIED for _, c in anon_codes.values()),
              {k: v for k, v in anon_codes.items() if v[1] not in DENIED})
        check("C2. and specifically 401 or 403 while a mechanism IS configured, "
              "which is the live container's posture",
              all(c in (401, 403) for _, c in anon_codes.values()),
              {k: v for k, v in anon_codes.items() if v[1] not in (401, 403)})

        # The census: no route may be public that is not on the allowlist.
        unlisted = []
        for rule in app.url_map.iter_rules():
            for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
                if (method, str(rule.rule)) in PUBLIC_ROUTES:
                    continue
                probe = str(rule.rule)
                for arg in rule.arguments:
                    probe = probe.replace(f"<{arg}>", "rev127") \
                                 .replace(f"<path:{arg}>", "rev127") \
                                 .replace(f"<int:{arg}>", "1")
                    # werkzeug converters appear as <conv:name>
                    probe = probe.replace(f"<string:{arg}>", "rev127")
                resp = anon.open(probe, method=method, json={})
                if resp.status_code not in DENIED:
                    unlisted.append((method, str(rule.rule), resp.status_code))
        check("C3. the UNAUTHENTICATED surface of this listener is EXACTLY the "
              "declared public allowlist — any route added later without a "
              "credential check fails here",
              not unlisted, unlisted)
        check("C4. the declared public allowlist contains no relay mutation "
              "route and no sensitive read",
              not any(m != "GET" and p.startswith("/api/relay")
                      for m, p in PUBLIC_ROUTES)
              and not any(p in [q for _, q in PROTECTED_READS]
                          for _, p in PUBLIC_ROUTES),
              sorted(PUBLIC_ROUTES))

        # The one permitted public liveness result is FIXED and reveals nothing.
        ping = anon.get("/api/relay/ping")
        check("C5. the public liveness endpoint returns only a fixed health "
              "result — no configuration, model, log, route, DB or project data",
              ping.status_code == 200 and ping.get_json() == {"status": "ok"},
              (ping.status_code, ping.get_data(as_text=True)[:120]))
        health = anon.get("/api/health").get_json() or {}
        check("C6. the other public health routes expose only status metadata",
              set(health) <= {"status", "timestamp", "container"}, sorted(health))

        # ── D. an unauthorized mutation creates NOTHING ──────────────────
        before = table_counts(spine_path)
        mutation_codes = []
        for method, path, body in MUTATION_ROUTES:
            resp = anon.open(path, method=method, json=body)
            mutation_codes.append((path, resp.status_code))
        after = table_counts(spine_path)

        check("D1. every unauthorized mutation attempt is refused",
              all(c in DENIED for _, c in mutation_codes),
              [x for x in mutation_codes if x[1] not in DENIED])
        check("D2. NO spine row was written by any of them — identical table "
              "counts before and after",
              before == after,
              {k: (before.get(k), after.get(k))
               for k in set(before) | set(after) if before.get(k) != after.get(k)})
        check("D3. no workflow run was created", after.get("workflow_runs") == 0,
              after.get("workflow_runs"))
        check("D4. no project was created", after.get("projects") == 0,
              after.get("projects"))
        check("D5. no approval/gate decision was recorded",
              after.get("gate_decisions") == 0, after.get("gate_decisions"))
        check("D6. no deliberation round or trajectory was written",
              after.get("deliberation_rounds") == 0
              and after.get("agent_trajectories") == 0,
              (after.get("deliberation_rounds"), after.get("agent_trajectories")))
        check("D7. NO MODEL CALL and NO DISPATCH occurred — every tripwire on "
              "the pipeline, gateway, card generation and agent dispatch entry "
              "points is unentered",
              all(not t.calls for t in tripwires.values()),
              {k: len(t.calls) for k, t in tripwires.items() if t.calls})
        check("D8. the refusal bodies carry no credential, no key and no "
              "configuration value",
              not any(TEST_API_KEY in (anon.open(p, method=m, json=b)
                                       .get_data(as_text=True))
                      or TEST_SESSION_SECRET in (anon.open(p, method=m, json=b)
                                                 .get_data(as_text=True))
                      for m, p, b in MUTATION_ROUTES),
              "a refusal body echoed a configured secret")

        # ── E. the authenticated owner session still works ───────────────
        owner = app.test_client()
        owner_token, payload = owner_cookie(owner)
        check("E1. the session the production primitive mints verifies against "
              "the production verifier, and resolve_role() recomputes the role "
              "from configuration as owner",
              workbench_auth.verify_session_token(
                  owner_token, TEST_SESSION_SECRET) is not None
              and workbench_auth.resolve_role(OWNER_EMAIL) == "owner",
              (payload.get("role"), workbench_auth.resolve_role(OWNER_EMAIL)))

        owner_read_codes = {}
        for label, path in PROTECTED_READS:
            if path.startswith("/api/workbench/"):
                owner_read_codes[label] = owner.get(path).status_code
        check("E2. the owner browser session reaches every Workbench read "
              "surface — the cookie is scoped to /api/workbench, so adding "
              "check_auth() there did not lock the owner out",
              all(c not in DENIED for c in owner_read_codes.values()),
              {k: v for k, v in owner_read_codes.items() if v in DENIED})

        # Braingate conversation: a real GET and a real guarded POST.
        conv = owner.get("/api/workbench/projects")
        check("E3. the owner can list Braingate conversation projects",
              conv.status_code == 200, (conv.status_code,
                                        conv.get_data(as_text=True)[:160]))
        created = owner.post(
            "/api/workbench/projects",
            json={"name": "rev127 owner conversation"},
            headers={"X-CIS-Workbench-CSRF": payload["csrf"]},
        )
        check("E4. the owner can create a conversation project with a valid "
              "CSRF token (the Workbench remains usable, not merely reachable)",
              created.status_code in (200, 201),
              (created.status_code, created.get_data(as_text=True)[:200]))
        check("E5. the SAME owner session without the CSRF header is refused "
              "403 on a mutation — browser auth did not weaken CSRF",
              owner.post("/api/workbench/projects",
                         json={"name": "no csrf"}).status_code == 403,
              owner.post("/api/workbench/projects",
                         json={"name": "no csrf"}).status_code)

        project_id = None
        if created.status_code in (200, 201):
            project_id = (created.get_json() or {}).get("id") \
                or (created.get_json() or {}).get("project", {}).get("id")
        if project_id:
            msgs = owner.get(f"/api/workbench/projects/{project_id}/messages")
            check("E6. the owner can read the conversation message list",
                  msgs.status_code == 200, msgs.status_code)
            refused = owner.post(
                f"/api/workbench/projects/{project_id}/messages",
                json={"message": "draft me a proposal", "mode": "draft_proposal"},
                headers={"X-CIS-Workbench-CSRF": payload["csrf"]},
            )
            check("E7. an AUTHENTICATED OWNER is still refused a downstream "
                  "conversation mode — authentication never widens the stage",
                  refused.status_code == 403
                  and (refused.get_json() or {}).get("stage")
                  == "braingate_conversation",
                  (refused.status_code, refused.get_data(as_text=True)[:200]))
        else:
            check("E6. the owner can read the conversation message list",
                  False, "project creation did not return an id")
            check("E7. an authenticated owner is still refused a downstream mode",
                  False, "project creation did not return an id")

        # An authenticated person who is NOT on the allowlist gets nothing.
        stranger = app.test_client()
        owner_cookie(stranger, email=STRANGER_EMAIL, role="owner")  # noqa: F841
        check("E8. a provider-verified identity that is NOT on the allowlist is "
              "denied even though its cookie is validly signed, and even though "
              "the cookie claims role=owner",
              stranger.get("/api/workbench/system-context").status_code in DENIED,
              stranger.get("/api/workbench/system-context").status_code)

        # ── F. a valid configured API credential, and only its surface ───
        api = app.test_client()
        api.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {TEST_API_KEY}"
        api_codes = {label: api.get(path).status_code
                     for label, path in PROTECTED_READS}
        check("F1. a valid explicitly configured API credential is ACCEPTED on "
              "every protected read — no route denies it",
              all(c not in DENIED for c in api_codes.values()),
              {k: v for k, v in api_codes.items() if v in DENIED})
        # A handful of routes the minimal fixture spine can actually satisfy, so
        # that "accepted" is shown as a real 200 and not merely as "not a 401".
        # The rest of the surface answers 500 against this fixture because the
        # fixture carries only the tables an unauthorized mutation could write
        # to, which is what section D needs it for.
        served = {p: api.get(p).status_code for p in (
            "/api/relay/runs", "/api/projects", "/api/relay/system/security",
            "/api/workbench/build-path")}
        check("F2. and it is served real 200 responses on the routes this "
              "fixture can answer",
              all(c == 200 for c in served.values()), served)
        check("F3. the API credential does NOT widen the stage boundary — Card "
              "Factory and Card Runner are still 404, not 200",
              all(api.open(p, method=m, json={}).status_code == 404
                  for m, p in (("POST", "/api/workbench/cards/generate"),
                               ("POST", "/api/workbench/runs/dispatch"),
                               ("POST", "/generate"), ("POST", "/dispatch"))),
              [(m, p, api.open(p, method=m, json={}).status_code)
               for m, p in (("POST", "/api/workbench/cards/generate"),
                            ("POST", "/api/workbench/runs/dispatch"),
                            ("POST", "/generate"), ("POST", "/dispatch"))])
        check("F4. and it still cannot reach a downstream conversation mode",
              api.post("/api/workbench/projects/p1/messages",
                       json={"message": "x", "mode": "revise_proposal"}
                       ).status_code == 403,
              api.post("/api/workbench/projects/p1/messages",
                       json={"message": "x", "mode": "revise_proposal"}).status_code)
        check("F5. no tripwire fired for ANY authorized read either — the read "
              "surface spends nothing",
              all(not t.calls for t in tripwires.values()),
              {k: len(t.calls) for k, t in tripwires.items() if t.calls})

        # ── G. Card Factory and Card Runner remain dormant ───────────────
        rules = {str(r.rule) for r in app.url_map.iter_rules()}
        forbidden_markers = ("card-factory", "card_factory", "cards/generate",
                             "/generate", "card-runner", "card_runner",
                             "/dispatch", "runs/dispatch", "confirm-direction",
                             "/approve", "proposals")
        present = sorted(r for r in rules
                         if any(m in r for m in forbidden_markers))
        check("G1. no Card Factory, Card Runner, proposal confirm/approve or "
              "dispatch route is registered on this listener",
              not present, present)
        check("G2. the listener registers the Braingate conversation + auth "
              "surface, and that surface is what answers",
              {"/api/workbench/projects",
               "/api/workbench/auth/login"} <= rules, sorted(rules)[:5])
        check("G3. the blueprint census is unchanged by this card — seven "
               "blueprints, none added",
              len(app.blueprints) == 7, sorted(app.blueprints))

    finally:
        cs.DB = saved_cs_db
        relay._run_pipeline_background = saved["run_bg"]
        if saved["gateway"] is not None:
            workbench_app._call_brain_gateway = saved["gateway"]
        if saved["generate"] is not None:
            card_factory_app.generate_card_core = saved["generate"]
        if saved["dispatch"] is not None:
            card_runner.dispatch = saved["dispatch"]
        if saved["pipeline_relay"] is None:
            sys.modules.pop("pipeline_relay", None)
        else:
            sys.modules["pipeline_relay"] = saved["pipeline_relay"]
        if orig_spine is None:
            os.environ.pop("CIS_SPINE_PATH", None)
        else:
            os.environ["CIS_SPINE_PATH"] = orig_spine
        shutil.rmtree(tmp_root, ignore_errors=True)

    for line in results:
        print(line)
    failed = [r for r in results if r.startswith("FAIL")]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
