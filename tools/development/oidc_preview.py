#!/usr/bin/env python3
"""oidc_preview.py — a loopback-only preview app for developing Workbench OIDC.

    python3 -m tools.development.oidc_preview serve  [--port 5055]
    python3 -m tools.development.oidc_preview tunnel [--port 5055] [--timeout 45]
    python3 -m tools.development.oidc_preview run    [--port 5055]   # both

WHY THIS EXISTS, AND WHAT IT DELIBERATELY CANNOT DO

Testing a real OIDC round trip needs a public HTTPS URL, because the identity
provider has to redirect a real browser back to a real callback. The temptation
is to point a tunnel at the live cis-pipeline on port 5000 and be done. This
module exists so that never happens.

The preview app registers EXACTLY three things:

    * the OIDC authentication lifecycle  (runtime/workbench_oidc.py)
    * the compiled UI's static files
    * two harmless read-only preview routes, described below

It does NOT import or register workbench_app, card_factory_app, card_runner or
braingate_conversation. Not "registers them but denies them" — does not import
them at all, so there is no route to reach, no database handle to misuse and no
model or agent it could call even if something went wrong. The live spine is
never opened. `python3 -m tools.development.oidc_preview routes` prints the
whole surface, and test_oidc_preview_boundary.py asserts it.

The listener binds 127.0.0.1 only. Port 5000 is never touched, and the tunnel
is pointed at this loopback port so nothing about the running system becomes
reachable from the Internet.

QUICK TUNNEL URLS ARE TEMPORARY

A Cloudflare Quick Tunnel gets a new random hostname every time it starts.
That is a property of free anonymous tunnels, not a defect in CIS, and the
answer to it is NOT a wildcard redirect URI or a relaxed callback check —
those would be the actual defect. When the URL changes, three values in the
Auth0 dashboard must be updated to the new exact URL before login will work
again. `tunnel` prints exactly which ones and exactly what to paste.
"""
import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUNTIME_DIR = os.path.join(REPO_ROOT, "runtime")
UI_DIST = os.path.join(RUNTIME_DIR, "ui", "dist")

DEFAULT_PORT = 5055
LOOPBACK = "127.0.0.1"

QUICK_TUNNEL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def _import_runtime():
    """runtime/ modules import each other by bare name, so it goes on the path.

    Deliberately appended in one place, and deliberately NOT an import of the
    Workbench app — see the module docstring.
    """
    if RUNTIME_DIR not in sys.path:
        sys.path.insert(0, RUNTIME_DIR)


def build_preview_app():
    """The preview Flask app. Authentication surface only."""
    _import_runtime()
    from flask import Flask, jsonify, send_from_directory

    import workbench_auth
    import workbench_oidc

    app = Flask(__name__, static_folder=None)
    app.register_blueprint(workbench_oidc.workbench_oidc_bp)

    @app.route("/api/workbench/preview/whoami", methods=["GET"])
    def whoami():
        """A test-only authenticated endpoint.

        It exists to answer one question during a real browser test — "did the
        session I just got actually authorize an API call?" — and it can do
        nothing else. It reads no database, writes nothing, and returns only
        what the signed session already told the browser about itself.
        """
        from flask import g
        auth_error = workbench_auth.check_auth()
        if auth_error:
            return auth_error
        return jsonify({
            "authenticated": True,
            "auth_method": getattr(g, "cis_auth_method", None),
            "identity": getattr(g, "cis_identity", None),
            "role": getattr(g, "cis_role", None),
            "note": "Preview-only endpoint. It reads and writes nothing.",
        }), 200

    @app.route("/api/workbench/preview/status", methods=["GET"])
    def status():
        """Unauthenticated, and honest about what is and is not configured.

        Reports variable NAMES and configured/not-configured only. No value of
        any secret appears here, which is what makes it safe to expose through
        a public tunnel while setting Auth0 up.
        """
        problems = workbench_oidc.configuration_problems()
        origin, origin_error = workbench_oidc.configured_public_origin()
        return jsonify({
            "preview": True,
            "oidc_configured": not problems,
            "configuration_problems": problems,
            "public_origin": origin,
            "public_origin_error": origin_error,
            "expected_callback_url": workbench_oidc.redirect_uri() or None,
            "login_url": workbench_oidc.LOGIN_PATH,
            "allowed_email_count": len(workbench_auth.allowed_emails()),
            "owner_emails_not_in_allowlist":
                sorted(workbench_auth.misconfigured_owner_emails()),
            "registered_routes": sorted(
                str(r.rule) for r in app.url_map.iter_rules()
                if r.endpoint != "static"),
        }), 200

    @app.route("/", methods=["GET"])
    @app.route("/<path:asset>", methods=["GET"])
    def ui(asset="index.html"):
        """The compiled UI, or index.html for any client-side route."""
        if not os.path.isdir(UI_DIST):
            return jsonify({
                "error": "The UI has not been built",
                "detail": f"{UI_DIST} does not exist. Run `npm run build` in "
                          "runtime/ui first.",
            }), 503
        target = asset if os.path.isfile(os.path.join(UI_DIST, asset)) else "index.html"
        return send_from_directory(UI_DIST, target)

    return app


# ── serve ────────────────────────────────────────────────────────────────

def cmd_serve(args):
    app = build_preview_app()
    print(f"preview listening on http://{LOOPBACK}:{args.port} (loopback only)")
    print("routes:")
    for rule in sorted(str(r.rule) for r in app.url_map.iter_rules()
                       if r.endpoint != "static"):
        print(f"  {rule}")
    # host is pinned to loopback and is not configurable: a --host flag is
    # exactly the flag someone would reach for at 2am to "just test it", and
    # binding 0.0.0.0 is the thing this module exists to prevent.
    app.run(host=LOOPBACK, port=args.port, debug=False, use_reloader=False)
    return 0


def cmd_routes(args):
    app = build_preview_app()
    for rule in sorted(str(r.rule) for r in app.url_map.iter_rules()
                       if r.endpoint != "static"):
        print(rule)
    return 0


# ── tunnel ───────────────────────────────────────────────────────────────

def start_quick_tunnel(port: int, timeout: float = 45.0):
    """Start `cloudflared tunnel --url http://127.0.0.1:<port>`.

    Returns (process, public_url) — public_url is None if cloudflared never
    printed one within the timeout, in which case the caller must not pretend
    a tunnel exists.
    """
    # --config with an empty file, deliberately.
    #
    # cloudflared reads ~/.cloudflared/config.yml by default even when --url is
    # given. This host already runs a NAMED tunnel whose config.yml ends with
    # `- service: http_status:404`, and that ingress list applies to the quick
    # tunnel too: the tunnel comes up, prints a working-looking URL, and then
    # answers 404 to every request while the local origin happily serves 200.
    # Pointing at an empty config isolates this tunnel from that one, and
    # leaves the named tunnel completely untouched.
    isolated_config = tempfile.NamedTemporaryFile(
        mode="w", suffix="-cis-quick-tunnel.yml", delete=False)
    isolated_config.write("# intentionally empty: quick tunnel uses --url only\n")
    isolated_config.close()

    process = subprocess.Popen(
        ["cloudflared", "--config", isolated_config.name, "--no-autoupdate",
         "tunnel", "--url", f"http://{LOOPBACK}:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    found = {"url": None}
    lines = []

    def reader():
        for line in process.stdout:
            lines.append(line)
            # Echoed through rather than swallowed. cloudflared's own
            # diagnostics are the only explanation available when the edge
            # serves 404 while the local origin serves 200, and a helper that
            # hides them turns a five-minute answer into guesswork.
            sys.stdout.write("  [cloudflared] " + line)
            sys.stdout.flush()
            if found["url"] is None:
                match = QUICK_TUNNEL_RE.search(line)
                if match:
                    found["url"] = match.group(0)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    deadline = time.time() + timeout
    while time.time() < deadline and found["url"] is None:
        if process.poll() is not None:
            break
        time.sleep(0.25)

    return process, found["url"], lines


def print_auth0_values(public_url: str, port: int, pid: int):
    """Exactly what to paste where. No secrets appear in this output."""
    callback = f"{public_url}/api/workbench/auth/callback"
    print("")
    print("=" * 72)
    print("CLOUDFLARE QUICK TUNNEL IS UP")
    print("=" * 72)
    print(f"  public URL        {public_url}")
    print(f"  local origin      http://{LOOPBACK}:{port}  (loopback only)")
    print(f"  cloudflared PID   {pid}")
    print("")
    print("-- Set this in the CIS server environment ---------------------------")
    print(f"  CIS_WORKBENCH_PUBLIC_ORIGIN={public_url}")
    print("")
    print("-- Paste these into the Auth0 application settings ------------------")
    print(f"  Allowed Callback URLs   {callback}")
    print(f"  Allowed Logout URLs     {public_url}/")
    print(f"  Allowed Web Origins     {public_url}")
    print("")
    print("-- Open this in a browser to test -----------------------------------")
    print(f"  {public_url}/")
    print("")
    print("IMPORTANT: this hostname is temporary. Every time the Quick Tunnel is")
    print("restarted it may get a DIFFERENT https://....trycloudflare.com name.")
    print("When that happens, all three Auth0 entries above AND")
    print("CIS_WORKBENCH_PUBLIC_ORIGIN must be updated to the new exact URL")
    print("before OIDC login will work. Do not use a wildcard redirect URI to")
    print("avoid this — a permissive callback is a real security hole traded")
    print("for a temporary convenience.")
    print("")
    print("Auth0 dashboard settings are NOT changed automatically by this tool.")
    print("Press Ctrl+C to stop the tunnel.")
    print("=" * 72)
    print("")


def cmd_tunnel(args):
    process, public_url, lines = start_quick_tunnel(args.port, args.timeout)
    if public_url is None:
        print("cloudflared did not report a Quick Tunnel URL within "
              f"{args.timeout:.0f}s. No tunnel is claimed.", file=sys.stderr)
        for line in lines[-20:]:
            sys.stderr.write(line)
        if process.poll() is None:
            process.terminate()
        return 1

    print_auth0_values(public_url, args.port, process.pid)

    if args.record:
        with open(args.record, "w", encoding="utf-8") as f:
            f.write(f"public_url={public_url}\n")
            f.write(f"local_origin=http://{LOOPBACK}:{args.port}\n")
            f.write(f"callback_url={public_url}/api/workbench/auth/callback\n")
            f.write(f"logout_url={public_url}/\n")
            f.write(f"web_origin={public_url}\n")
            f.write(f"cloudflared_pid={process.pid}\n")
            f.write(f"started_at_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        print(f"recorded tunnel identity in {args.record}")

    if args.seconds:
        # Bounded run, for scripted evidence capture: the tunnel is torn down
        # explicitly rather than left behind for someone to find later.
        time.sleep(args.seconds)
        _shutdown(process)
        return 0

    def stop(signum, frame):
        _shutdown(process)
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    process.wait()
    return 0


def _shutdown(process):
    if process.poll() is None:
        print(f"\nstopping cloudflared (pid {process.pid})…")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    print(f"cloudflared exited with {process.returncode}. Tunnel is closed.")


def cmd_run(args):
    """Open the tunnel FIRST, then serve the preview with that origin set.

    The order is not arbitrary and is the whole reason this subcommand exists.
    A Quick Tunnel's hostname is not known until cloudflared has been running
    for a few seconds, and CIS_WORKBENCH_PUBLIC_ORIGIN has to be that hostname
    before the preview starts — the login route reads it per request, but a
    process started without it simply answers 503 and looks broken through an
    otherwise working tunnel. Starting the server first is exactly that
    mistake, and it cost a confusing round of "the tunnel is up but everything
    is unconfigured" before this was written down.
    """
    import multiprocessing

    process, public_url, lines = start_quick_tunnel(args.port, args.timeout)
    if public_url is None:
        print("cloudflared did not report a Quick Tunnel URL within "
              f"{args.timeout:.0f}s. No tunnel is claimed, and the preview was "
              "not started.", file=sys.stderr)
        for line in lines[-20:]:
            sys.stderr.write(line)
        if process.poll() is None:
            process.terminate()
        return 1

    os.environ["CIS_WORKBENCH_PUBLIC_ORIGIN"] = public_url
    print_auth0_values(public_url, args.port, process.pid)
    print(f"CIS_WORKBENCH_PUBLIC_ORIGIN has been set to {public_url} for the "
          "preview process started below.\n")

    server = multiprocessing.Process(target=cmd_serve, args=(args,), daemon=True)
    server.start()
    try:
        if args.seconds:
            time.sleep(args.seconds)
        else:
            process.wait()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        server.terminate()
        server.join(timeout=5)
        _shutdown(process)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    for name, handler, helptext in (
        ("serve", cmd_serve, "run the loopback-only preview app"),
        ("tunnel", cmd_tunnel, "open a Cloudflare Quick Tunnel to the preview port"),
        ("run", cmd_run, "serve and tunnel together"),
        ("routes", cmd_routes, "print the preview app's entire route surface"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--port", type=int, default=DEFAULT_PORT)
        if name in ("tunnel", "run"):
            p.add_argument("--timeout", type=float, default=45.0,
                           help="seconds to wait for the Quick Tunnel URL")
            p.add_argument("--seconds", type=float, default=None,
                           help="run for this long, then shut the tunnel down")
            p.add_argument("--record", default=None,
                           help="write the tunnel's identity to this file")
        p.set_defaults(handler=handler)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
