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

    for line in results:
        print(line)
    failed = [r for r in results if r.startswith("FAIL")]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
