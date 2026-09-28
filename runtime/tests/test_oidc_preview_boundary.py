"""
test_oidc_preview_boundary.py — the development preview is not a back door.

tools/development/oidc_preview.py exists so that a Cloudflare tunnel can be
pointed at *something* during OIDC development without that something being the
live workflow. This suite is the proof of that claim rather than a restatement
of it.

The interesting assertions run in a SUBPROCESS with a clean interpreter, so
"card_factory_app was never imported" means it was never imported — not that it
happened to be absent from this test runner's already-populated sys.modules.

No network, no database, no model call, no subprocess of the real system.

Run: python3 runtime/tests/test_oidc_preview_boundary.py
"""
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# What a clean interpreter must report after building the preview app.
PROBE = r"""
import json, sys, os
sys.path.insert(0, %(repo)r)
from tools.development.oidc_preview import build_preview_app
app = build_preview_app()
print("@@" + json.dumps({
    "routes": sorted(str(r.rule) for r in app.url_map.iter_rules()
                     if r.endpoint != "static"),
    "modules": sorted(m for m in sys.modules
                      if m in ("workbench_app", "card_factory_app", "card_runner",
                               "braingate_conversation", "cis_db", "connection")),
}))
"""


def run():
    results = []

    def check(label, cond, detail=""):
        results.append(f"{'PASS' if cond else 'FAIL'}  {label}"
                       + ("" if cond else f" — {detail}"))

    env = dict(os.environ)
    # A deliberately unconfigured preview: it must still build and still refuse.
    for var in ("CIS_WORKBENCH_OIDC_ISSUER", "CIS_WORKBENCH_OIDC_CLIENT_ID",
                "CIS_WORKBENCH_OIDC_CLIENT_SECRET", "CIS_WORKBENCH_PUBLIC_ORIGIN"):
        env.pop(var, None)

    proc = subprocess.run(
        [sys.executable, "-c", PROBE % {"repo": REPO_ROOT}],
        capture_output=True, text=True, env=env, cwd=REPO_ROOT, timeout=120,
    )
    check("0a. the preview app builds in a clean interpreter",
          proc.returncode == 0, proc.stderr[-400:])
    payload = None
    for line in proc.stdout.splitlines():
        if line.startswith("@@"):
            payload = json.loads(line[2:])
    check("0b. the probe reported its surface", payload is not None,
          proc.stdout[-300:])
    if payload is None:
        for line in results:
            print(line)
        return 1

    routes = payload["routes"]
    modules = payload["modules"]

    expected = {
        "/api/workbench/auth/login",
        "/api/workbench/auth/callback",
        "/api/workbench/auth/session",
        "/api/workbench/auth/logout",
        "/api/workbench/preview/whoami",
        "/api/workbench/preview/status",
        # POST, and the only non-GET application route on the preview. It exists
        # so the CSRF boundary can be demonstrated against a real browser
        # session — check_auth() only enforces CSRF for state-changing methods.
        # It writes nothing; see its docstring in tools/development/oidc_preview.py.
        "/api/workbench/preview/echo",
        "/",
        "/<path:asset>",
    }
    check("1a. the preview surface is exactly authentication + preview status "
          "+ static UI", set(routes) == expected, str(routes))

    for forbidden in ("/api/cardfactory", "/api/cardrunner", "/api/relay",
                      "/proposals", "/messages", "/dispatch", "/approve",
                      "/confirm-direction", "/generate"):
        check(f"1b. no preview route touches {forbidden}",
              not any(forbidden in r for r in routes), str(routes))

    check("2a. card_factory_app is never even imported by the preview",
          "card_factory_app" not in modules, str(modules))
    check("2b. card_runner is never even imported by the preview",
          "card_runner" not in modules, str(modules))
    check("2c. workbench_app is never even imported by the preview",
          "workbench_app" not in modules, str(modules))
    check("2d. braingate_conversation is never even imported by the preview",
          "braingate_conversation" not in modules, str(modules))
    check("2e. no database module is imported, so no spine can be written",
          "cis_db" not in modules and "connection" not in modules, str(modules))

    # The listener is loopback-pinned in source, with no host override.
    with open(os.path.join(REPO_ROOT, "tools", "development",
                           "oidc_preview.py"), encoding="utf-8") as f:
        source = f.read()
    check("3a. the preview binds loopback only",
          'app.run(host=LOOPBACK' in source and 'LOOPBACK = "127.0.0.1"' in source)
    check("3b. there is no --host flag to talk anyone into 0.0.0.0",
          '"--host"' not in source and "'--host'" not in source)
    check("3c. the tunnel points at loopback, never at port 5000",
          f'"--url", f"http://{{LOOPBACK}}:{{port}}"' in source and ":5000" not in source)

    # An unconfigured preview refuses honestly instead of half-working.
    probe2 = r"""
import json, sys
sys.path.insert(0, %(repo)r)
from tools.development.oidc_preview import build_preview_app
app = build_preview_app()
c = app.test_client()
login = c.get("/api/workbench/auth/login", headers={"Accept": "application/json"})
whoami = c.get("/api/workbench/preview/whoami")
status = c.get("/api/workbench/preview/status")
print("@@" + json.dumps({
    "login": login.status_code,
    "whoami": whoami.status_code,
    "status": status.status_code,
    "status_body": status.get_json(),
}))
""" % {"repo": REPO_ROOT}
    env2 = dict(env)
    env2.pop("CIS_PIPELINE_API_KEY", None)
    env2.pop("CIS_WORKBENCH_SESSION_SECRET", None)
    env2.pop("CIS_WORKBENCH_ALLOWED_EMAILS", None)
    proc2 = subprocess.run([sys.executable, "-c", probe2], capture_output=True,
                           text=True, env=env2, cwd=REPO_ROOT, timeout=120)
    payload2 = None
    for line in proc2.stdout.splitlines():
        if line.startswith("@@"):
            payload2 = json.loads(line[2:])
    check("4a. the unconfigured probe ran", payload2 is not None,
          proc2.stderr[-400:])
    if payload2:
        check("4b. an unconfigured preview refuses login with 503, not a redirect",
              payload2["login"] == 503, str(payload2["login"]))
        check("4c. the test-only authenticated endpoint fails closed (503) with "
              "nothing configured", payload2["whoami"] == 503, str(payload2["whoami"]))
        check("4d. the unauthenticated status endpoint still answers honestly",
              payload2["status"] == 200
              and payload2["status_body"]["oidc_configured"] is False,
              str(payload2["status_body"])[:200])
        body_text = json.dumps(payload2["status_body"])
        check("4e. the status endpoint names the missing variables",
              "CIS_WORKBENCH_OIDC_ISSUER" in body_text,
              body_text[:200])

    # …and with everything configured, it still publishes only names. The
    # sentinels below are what would appear if any value leaked into the body.
    env3 = dict(env)
    env3["CIS_WORKBENCH_OIDC_ISSUER"] = "https://tenant.example.auth0.com/"
    env3["CIS_WORKBENCH_OIDC_CLIENT_ID"] = "client-id-is-not-secret"
    env3["CIS_WORKBENCH_OIDC_CLIENT_SECRET"] = "SENTINEL-CLIENT-SECRET-VALUE"
    env3["CIS_WORKBENCH_SESSION_SECRET"] = "SENTINEL-SESSION-SECRET-VALUE"
    env3["CIS_PIPELINE_API_KEY"] = "SENTINEL-API-KEY-VALUE"
    env3["CIS_WORKBENCH_PUBLIC_ORIGIN"] = "https://words-here.trycloudflare.com"
    env3["CIS_WORKBENCH_ALLOWED_EMAILS"] = "eric@example.com"
    env3["CIS_WORKBENCH_OWNER_EMAILS"] = "eric@example.com,not-allowed@example.com"
    proc3 = subprocess.run([sys.executable, "-c", probe2], capture_output=True,
                           text=True, env=env3, cwd=REPO_ROOT, timeout=120)
    payload3 = None
    for line in proc3.stdout.splitlines():
        if line.startswith("@@"):
            payload3 = json.loads(line[2:])
    check("5a. the configured probe ran", payload3 is not None, proc3.stderr[-400:])
    if payload3:
        configured_text = json.dumps(payload3["status_body"])
        for label, sentinel in (
            ("the OIDC client secret", "SENTINEL-CLIENT-SECRET-VALUE"),
            ("the session secret", "SENTINEL-SESSION-SECRET-VALUE"),
            ("the pipeline API key", "SENTINEL-API-KEY-VALUE"),
        ):
            check(f"5b. the status endpoint never exposes {label}",
                  sentinel not in configured_text, configured_text[:200])
        check("5c. a fully configured preview reports itself configured",
              payload3["status_body"]["oidc_configured"] is True,
              configured_text[:200])
        check("5d. and publishes the exact callback URL to paste into Auth0",
              payload3["status_body"]["expected_callback_url"]
              == "https://words-here.trycloudflare.com/api/workbench/auth/callback",
              str(payload3["status_body"].get("expected_callback_url")))
        check("5e. an owner address missing from the allowlist is surfaced, "
              "not hidden",
              payload3["status_body"]["owner_emails_not_in_allowlist"]
              == ["not-allowed@example.com"],
              str(payload3["status_body"].get("owner_emails_not_in_allowlist")))
        check("5f. login now redirects to the provider instead of 503… or "
              "reports the provider unreachable, never a silent success",
              payload3["login"] in (302, 503), str(payload3["login"]))

    # ── 6. the preview's one POST route enforces CSRF ────────────────────
    # /api/workbench/preview/echo exists so the CSRF boundary can be shown
    # against a real browser session. It must therefore actually enforce it,
    # and must stay incapable of doing anything else.
    probe4 = r"""
import json, sys
sys.path.insert(0, %(repo)r)
sys.path.insert(0, %(runtime)r)
from tools.development.oidc_preview import build_preview_app
import workbench_auth as wa
from workbench_session import set_session_cookie

app = build_preview_app()
c = app.test_client()
secret = wa.configured_session_secret()
token, payload = wa.issue_session_token(
    secret, 3600, subject="auth0|test", email="eric@example.com",
    role="owner", name="Test")
c.set_cookie("cis_workbench_session", token, path="/api/workbench")

no_csrf = c.post("/api/workbench/preview/echo")
bad_csrf = c.post("/api/workbench/preview/echo",
                  headers={wa.CSRF_HEADER: "not-the-right-token"})
good = c.post("/api/workbench/preview/echo",
              headers={wa.CSRF_HEADER: payload["csrf"]})
anon = app.test_client().post("/api/workbench/preview/echo")
getecho = c.get("/api/workbench/preview/echo")
print("@@" + json.dumps({
    "no_csrf": no_csrf.status_code,
    "bad_csrf": bad_csrf.status_code,
    "good": good.status_code,
    "good_body": good.get_json(),
    "anon": anon.status_code,
    "get": getecho.status_code,
    "get_type": getecho.headers.get("Content-Type", ""),
    "get_is_echo": (getecho.get_json(silent=True) or {}).get("ok") is True,
}))
""" % {"repo": REPO_ROOT, "runtime": os.path.join(REPO_ROOT, "runtime")}
    env4 = dict(env3)
    env4.pop("CIS_PIPELINE_API_KEY", None)   # browser-session path only
    proc4 = subprocess.run([sys.executable, "-c", probe4], capture_output=True,
                           text=True, env=env4, cwd=REPO_ROOT, timeout=120)
    payload4 = None
    for line in proc4.stdout.splitlines():
        if line.startswith("@@"):
            payload4 = json.loads(line[2:])
    check("6a. the CSRF probe ran", payload4 is not None, proc4.stderr[-400:])
    if payload4:
        check("6b. a cookie-authenticated POST with NO CSRF header is refused 403",
              payload4["no_csrf"] == 403, str(payload4["no_csrf"]))
        check("6c. a WRONG CSRF token is refused 403, not merely a missing one",
              payload4["bad_csrf"] == 403, str(payload4["bad_csrf"]))
        check("6d. the correct CSRF token reaches the endpoint",
              payload4["good"] == 200, str(payload4["good"]))
        check("6e. and the server computed the role itself",
              (payload4["good_body"] or {}).get("role") == "owner",
              str(payload4["good_body"]))
        check("6f. authorization came from the browser session, not an API key",
              (payload4["good_body"] or {}).get("auth_method") == "browser_session",
              str(payload4["good_body"]))
        check("6g. an anonymous POST is refused (401), CSRF or not",
              payload4["anon"] == 401, str(payload4["anon"]))
        # GET on that path is swallowed by the SPA catch-all (/<path:asset>) and
        # returns index.html, exactly as every unregistered downstream path does.
        # The property that matters is that no GET ever reaches the echo handler,
        # so the endpoint cannot be triggered by a bare link or an <img> tag.
        check("6h. a GET never reaches the echo handler (SPA shell instead)",
              payload4["get_is_echo"] is False
              and "text/html" in payload4["get_type"],
              f"{payload4['get']} {payload4['get_type']}")

    # ── 7. the /ui/ prefix strip serves the bundle without opening a hole ──
    # Production Vite builds with base:'/ui/', so index.html asks for
    # /ui/assets/index-<hash>.js while the preview serves dist/ at the root.
    # The strip that reconciles those two must not become a traversal.
    #
    # The os.path.isfile spy below is the real assertion. send_from_directory
    # would refuse to SERVE an outside file regardless; what could still leak is
    # the existence check that CHOOSES between the asset and the SPA fallback.
    # If that check ever ran on an unconfined path, the chosen branch would
    # reveal whether an arbitrary host path exists. So the test records every
    # path the app stats and requires all of them to lie inside UI_DIST.
    probe5 = r"""
import hashlib, json, mimetypes, os, sys
sys.path.insert(0, %(repo)r)
import tools.development.oidc_preview as preview

UI_DIST = preview.UI_DIST
real_isfile = os.path.isfile
statted = []

def spy(path):
    statted.append(str(path))
    return real_isfile(path)

os.path.isfile = spy            # patched BEFORE the app is built
app = preview.build_preview_app()
c = app.test_client()

assets = os.path.join(UI_DIST, "assets")
names = sorted(os.listdir(assets)) if os.path.isdir(assets) else []
js = next((n for n in names if n.endswith(".js")), None)

def get(path):
    r = c.get(path)
    body = r.get_data()
    return {"status": r.status_code,
            "ctype": r.headers.get("Content-Type", ""),
            "sha": hashlib.sha256(body).hexdigest(),
            "len": len(body)}

css = next((n for n in names if n.endswith(".css")), None)

out = {"js_name": js, "css_name": css}
if js:
    out["prefixed"] = get("/ui/assets/" + js)     # what index.html actually asks for
    out["bare"] = get("/assets/" + js)            # the pre-existing spelling
if css:
    out["css_prefixed"] = get("/ui/assets/" + css)
    out["css_bare"] = get("/assets/" + css)
out["index"] = get("/")
out["spa_route"] = get("/some/client/side/route")
# A reference to a bundle that no longer exists — a stale index.html, a
# renamed hash, a half-finished build.
out["missing_css"] = get("/ui/assets/index-STALEHASH.css")
out["missing_js"] = get("/ui/assets/index-STALEHASH.js")
out["missing_bare"] = get("/assets/index-STALEHASH.css")
# What the compiled index.html literally asks for, read from the build itself
# rather than hard-coded, so a rebuild cannot silently invalidate this.
try:
    with open(os.path.join(UI_DIST, "index.html"), encoding="utf-8") as f:
        shell = f.read()
    import re as _re
    out["html_refs"] = _re.findall(r'(?:src|href)="(/ui/assets/[^"]+)"', shell)
    out["ref_results"] = {u: get(u) for u in out["html_refs"]}
except OSError as e:
    out["html_refs"] = "ERROR: %%s" %% e

# Representative traversal spellings — not one favourite spelling.
up = "/" + "../" * 6
traversals = {
    "dotdot": "/../etc/passwd",
    "dotdot2": "/../../etc/passwd",
    "ui_dotdot": "/ui/../../etc/passwd",
    "deep": up + "etc/passwd",
    "ui_deep": "/ui/" + "../" * 6 + "etc/passwd",
    "encoded": "/%%2e%%2e/%%2e%%2e/etc/passwd",
    "ui_encoded": "/ui/%%2e%%2e%%2f%%2e%%2e%%2fetc%%2fpasswd",
    "mixed_encoded": "/..%%2f..%%2fetc%%2fpasswd",
    "absolute": "/etc/passwd",
    "double_slash": "//etc/passwd",
    "dot_segment_pad": "/ui/....//....//etc/passwd",
    # An outside path that does NOT exist, paired with one that does: the two
    # responses must be identical, or the endpoint is an existence oracle.
    "absent_outside": up + "etc/cis-no-such-file-a1b2c3",
    "present_outside_pair": up + "etc/hostname",
}
out["traversals"] = {k: get(v) for k, v in traversals.items()}

# Anything the real /etc/passwd would contain must never appear in a body.
leaked = []
for k, v in traversals.items():
    body = c.get(v).get_data()
    if b"root:x:" in body or b"/bin/bash" in body:
        leaked.append(k)
out["leaked"] = leaked

# The stdlib's mimetypes.init() stats a FIXED list of system mime.types
# locations the first time send_file() guesses a content type. Those paths are
# a hard-coded constant inside CPython, identical on every request and derived
# from nothing the client sent, so they are excluded by exact membership in
# that constant — not by pattern, and not by widening the rule below.
stdlib_mime_probes = set(mimetypes.knownfiles)
request_derived = [p for p in statted if p not in stdlib_mime_probes]
outside = sorted({p for p in request_derived
                  if not os.path.abspath(p).startswith(
                      os.path.abspath(UI_DIST) + os.sep)})
out["statted_outside_ui_dist"] = outside
out["stat_count"] = len(request_derived)
out["excluded_stdlib_mime_probes"] = sorted(
    {p for p in statted if p in stdlib_mime_probes})
print("@@" + json.dumps(out))
""" % {"repo": REPO_ROOT}
    proc5 = subprocess.run([sys.executable, "-c", probe5], capture_output=True,
                           text=True, env=env, cwd=REPO_ROOT, timeout=120)
    payload5 = None
    for line in proc5.stdout.splitlines():
        if line.startswith("@@"):
            payload5 = json.loads(line[2:])
    check("7a. the asset/traversal probe ran", payload5 is not None,
          proc5.stderr[-400:])
    if payload5:
        spa = payload5["index"]["sha"]
        check("7b. an unknown client-side route gets the SPA shell",
              payload5["spa_route"]["sha"] == spa
              and payload5["spa_route"]["status"] == 200,
              str(payload5["spa_route"]))

        if not payload5["js_name"]:
            check("7c. the production bundle is present to test against",
                  False, "runtime/ui/dist/assets has no .js — run npm run build")
        else:
            pre, bare = payload5["prefixed"], payload5["bare"]
            check("7c. /ui/assets/<hash>.js serves the compiled asset, not the "
                  "SPA shell — the blank-page defect",
                  pre["status"] == 200 and pre["sha"] != spa, str(pre))
            check("7d. and serves it as JavaScript, so strict MIME checking "
                  "executes it",
                  "javascript" in pre["ctype"], pre["ctype"])
            check("7e. the pre-existing /assets/<hash>.js spelling still works",
                  bare["status"] == 200 and bare["sha"] != spa, str(bare))
            check("7f. both spellings serve byte-identical bytes from the one "
                  "production build",
                  pre["sha"] == bare["sha"], f"{pre['sha']} vs {bare['sha']}")

        # ── the CSS half of the same fix ──────────────────────────────────
        # Regression for the black-on-black contrast defect: when the
        # stylesheet URL answered with the SPA shell, Chrome refused it on
        # strict MIME grounds, the page lost --text and color-scheme:dark, and
        # body text fell back to black over a dark browser canvas.
        if not payload5["css_name"]:
            check("7m. the production bundle has a CSS asset to test against",
                  False, "runtime/ui/dist/assets has no .css — run npm run build")
        else:
            cpre, cbare = payload5["css_prefixed"], payload5["css_bare"]
            check("7m. /ui/assets/<hash>.css serves the compiled stylesheet, "
                  "not the SPA shell",
                  cpre["status"] == 200 and cpre["sha"] != spa, str(cpre))
            check("7n. and serves it as CSS, so strict MIME checking APPLIES "
                  "it — the black-on-black contrast defect",
                  "text/css" in cpre["ctype"], cpre["ctype"])
            check("7o. the bare /assets/<hash>.css spelling also serves CSS",
                  cbare["status"] == 200 and "text/css" in cbare["ctype"],
                  str(cbare))
            check("7p. both CSS spellings are byte-identical",
                  cpre["sha"] == cbare["sha"],
                  f"{cpre['sha']} vs {cbare['sha']}")

        # Every asset the compiled index.html actually references must resolve
        # with a usable type. Read out of the build, so a rebuild re-checks it.
        refs = payload5.get("html_refs")
        check("7q. the compiled index.html's asset references were read",
              isinstance(refs, list) and len(refs) >= 2, str(refs))
        if isinstance(refs, list):
            for url in refs:
                res = payload5["ref_results"][url]
                want = "text/css" if url.endswith(".css") else "javascript"
                check(f"7r. index.html reference {url} resolves as {want}",
                      res["status"] == 200 and want in res["ctype"]
                      and res["sha"] != spa,
                      f"{res['status']} {res['ctype']}")

        # ── a missed asset must 404, never the shell ──────────────────────
        # A 200 text/html against an immutable asset URL is cached by the edge
        # and the browser for hours, so one miss keeps breaking the page long
        # after the build is fixed. 404 fails loudly and is not cached that way.
        for label, key in (("stale .css", "missing_css"),
                           ("stale .js", "missing_js"),
                           ("stale bare-prefix .css", "missing_bare")):
            res = payload5[key]
            check(f"7s. a {label} reference 404s instead of returning the "
                  "SPA shell",
                  res["status"] == 404, f"{res['status']} {res['ctype']}")
            check(f"7t. a {label} reference is never answered as text/html",
                  "text/html" not in res["ctype"], res["ctype"])

        trav = payload5["traversals"]
        for name, res in sorted(trav.items()):
            check(f"7g. traversal {name!r} is not served content from outside "
                  "UI_DIST",
                  res["sha"] == spa, str(res))
            check(f"7h. traversal {name!r} raises no unexpected 500",
                  res["status"] == 200, str(res))
        check("7i. no traversal response contained /etc/passwd content",
              payload5["leaked"] == [], str(payload5["leaked"]))
        check("7j. an outside path that EXISTS and one that does NOT produce "
              "identical responses — no existence oracle",
              trav["present_outside_pair"] == trav["absent_outside"],
              f"{trav['present_outside_pair']} vs {trav['absent_outside']}")

        # The core hardening assertion.
        check("7k. every existence check the app performed was on a path "
              "already confined to UI_DIST",
              payload5["statted_outside_ui_dist"] == [],
              str(payload5["statted_outside_ui_dist"])[:400])
        check("7l. the probe actually exercised the existence check",
              payload5["stat_count"] > 0, str(payload5["stat_count"]))

    # ── 8. the preview echo route is absent from the production app ────────
    # The echo route is safe because nothing in production can reach it. That
    # is a property of the production route table, so it is asserted against
    # the production route table — a future refactor that imports the preview
    # app into container_app must fail here.
    probe6 = r"""
import json, sys
sys.path.insert(0, %(repo)r)
sys.path.insert(0, %(runtime)r)
import container_app
paths = sorted(str(r.rule) for r in container_app.app.url_map.iter_rules())
print("@@" + json.dumps({
    "has_echo": "/api/workbench/preview/echo" in paths,
    "preview_routes": [p for p in paths if "/preview/" in p],
    "preview_module_imported":
        "tools.development.oidc_preview" in sys.modules,
    "has_system_context": "/api/workbench/system-context" in paths,
    "count": len(paths),
}))
""" % {"repo": REPO_ROOT, "runtime": os.path.join(REPO_ROOT, "runtime")}
    proc6 = subprocess.run([sys.executable, "-c", probe6], capture_output=True,
                           text=True, env=env, cwd=REPO_ROOT, timeout=120)
    payload6 = None
    for line in proc6.stdout.splitlines():
        if line.startswith("@@"):
            payload6 = json.loads(line[2:])
    check("8a. the production route surface was enumerated", payload6 is not None,
          proc6.stderr[-400:])
    if payload6:
        check("8b. production really is the live app, not an empty stand-in",
              payload6["has_system_context"] and payload6["count"] > 10,
              str(payload6["count"]))
        check("8c. production does NOT register /api/workbench/preview/echo",
              payload6["has_echo"] is False, str(payload6["has_echo"]))
        check("8d. production registers no preview route at all",
              payload6["preview_routes"] == [], str(payload6["preview_routes"]))
        check("8e. production never even imports the preview module",
              payload6["preview_module_imported"] is False,
              str(payload6["preview_module_imported"]))

    for line in results:
        print(line)
    failed = [r for r in results if r.startswith("FAIL")]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
