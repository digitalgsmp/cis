"""
test_workbench_oidc.py — OpenID Connect authentication for the Workbench.

Everything here runs against a FAKE provider built in this file: a real RSA
keypair, a real JWKS document, real RS256 ID tokens, and real PyJWT
verification against them. What is faked is only the network — the discovery
GET, the JWKS fetch and the token POST are redirected to functions in this
module. Nothing in this suite depends on Auth0 or Google being reachable, and
a deterministic result never waits on someone else's uptime.

No paid model call, no real agent subprocess, no live spine access: a temporary
SQLite fixture and a monkeypatched Brain gateway, with tripwires asserting that
card generation and dispatch are never reached.

Run: python3 runtime/tests/test_workbench_oidc.py
"""
import base64
import json
import logging
import os
import sqlite3
import sys
import tempfile
import time
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

API_KEY = "test-api-key"
SESSION_SECRET = "test-session-secret-not-a-real-one"
CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret-not-a-real-one"
ISSUER = "https://cis-test.example.auth0.com"
PUBLIC_ORIGIN = "https://fake-quick-tunnel.trycloudflare.com"

OWNER_EMAIL = "eric@example.com"
COLLABORATOR_EMAIL = "collaborator@example.com"
OUTSIDER_EMAIL = "stranger@example.com"

os.environ["CIS_PIPELINE_API_KEY"] = API_KEY
os.environ["CIS_WORKBENCH_SESSION_SECRET"] = SESSION_SECRET
os.environ["CIS_WORKBENCH_OIDC_ISSUER"] = ISSUER + "/"   # trailing slash, as Auth0 writes it
os.environ["CIS_WORKBENCH_OIDC_CLIENT_ID"] = CLIENT_ID
os.environ["CIS_WORKBENCH_OIDC_CLIENT_SECRET"] = CLIENT_SECRET
os.environ["CIS_WORKBENCH_PUBLIC_ORIGIN"] = PUBLIC_ORIGIN
os.environ["CIS_WORKBENCH_ALLOWED_EMAILS"] = f"{OWNER_EMAIL}, {COLLABORATOR_EMAIL}"
os.environ["CIS_WORKBENCH_OWNER_EMAILS"] = OWNER_EMAIL
# Tests drive plain HTTP through Flask's test client; the Secure flag's
# default-on posture is asserted explicitly rather than inferred. Production
# and the Cloudflare development path never set this.
os.environ["CIS_WORKBENCH_COOKIE_INSECURE"] = "1"

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "schema", "migrations")


# ── A fake OpenID Connect provider ───────────────────────────────────────

def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _int_b64u(value: int) -> str:
    return _b64u(value.to_bytes((value.bit_length() + 7) // 8, "big"))


class FakeProvider:
    """A minimal but genuine OIDC provider: real keys, real signatures.

    `imposter_key` signs tokens with a key the JWKS does not contain, which is
    how the "invalid signature" case is produced without hand-mangling bytes.
    """

    def __init__(self):
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.imposter_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = "test-key-1"
        # Set by each test to control what the token endpoint hands back.
        self.next_claims = {}
        self.next_claim_overrides = {}
        self.sign_with_imposter = False
        self.omit_id_token = False
        self.token_endpoint_error = None
        self.extra_token_fields = {}
        self.metadata_overrides = {}
        # Every token request this provider received, for assertions about
        # what CIS actually sent (PKCE verifier, client secret, redirect_uri).
        self.token_requests = []
        self.discovery_requests = []

    # -- documents ---------------------------------------------------------

    def metadata(self):
        doc = {
            # Auth0 publishes the issuer WITH a trailing slash.
            "issuer": ISSUER + "/",
            "authorization_endpoint": f"{ISSUER}/authorize",
            "token_endpoint": f"{ISSUER}/oauth/token",
            "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
            "end_session_endpoint": f"{ISSUER}/oidc/logout",
            "id_token_signing_alg_values_supported": ["RS256"],
            "response_types_supported": ["code"],
        }
        doc.update(self.metadata_overrides)
        return doc

    def jwks(self):
        numbers = self.key.public_key().public_numbers()
        return {"keys": [{
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": self.kid,
            "n": _int_b64u(numbers.n),
            "e": _int_b64u(numbers.e),
        }]}

    # -- tokens ------------------------------------------------------------

    def make_id_token(self, nonce):
        now = int(time.time())
        claims = {
            "iss": ISSUER + "/",
            "aud": CLIENT_ID,
            "sub": "auth0|default-subject",
            "iat": now,
            "exp": now + 300,
            "nonce": nonce,
            "email": OWNER_EMAIL,
            "email_verified": True,
            "name": "Eric Shelton",
        }
        claims.update(self.next_claims)
        for key, value in self.next_claim_overrides.items():
            if value is _OMIT:
                claims.pop(key, None)
            else:
                claims[key] = value
        signing_key = self.imposter_key if self.sign_with_imposter else self.key
        return jwt.encode(claims, signing_key, algorithm="RS256",
                          headers={"kid": self.kid})

    # -- transport seams ---------------------------------------------------

    def http_get(self, url):
        self.discovery_requests.append(url)
        if url.endswith("/.well-known/openid-configuration"):
            return _Response(200, self.metadata())
        return _Response(404, {"error": "not found"})

    def http_post(self, url, data, headers):
        form = {k: v[0] for k, v in parse_qs(data).items()}
        self.token_requests.append(form)
        if self.token_endpoint_error:
            return _Response(400, {"error": self.token_endpoint_error})
        body = {
            "access_token": "provider-access-token-SHOULD-NOT-BE-STORED",
            "refresh_token": "provider-refresh-token-SHOULD-NOT-BE-STORED",
            "token_type": "Bearer",
            "expires_in": 86400,
            "scope": "openid profile email",
        }
        if not self.omit_id_token:
            body["id_token"] = self._pending_id_token
        body.update(self.extra_token_fields)
        return _Response(200, body)

    def fetch_jwks(self, *a, **kw):
        return self.jwks()


class _OMIT:
    """Sentinel: remove a claim entirely rather than setting it to None."""


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def make_fixture_db(path):
    conn = sqlite3.connect(path)
    for name in ("0035_workbench.sql", "0038_workbench_action_proposals.sql"):
        with open(os.path.join(MIGRATIONS_DIR, name)) as f:
            conn.executescript(f.read())
    conn.execute("CREATE VIRTUAL TABLE knowledge_messages_fts USING fts5(content, source)")
    conn.execute("INSERT INTO knowledge_messages_fts (content, source) VALUES (?, ?)",
                 ("Workbench OIDC test corpus.", "kb-300459"))
    conn.commit()
    conn.close()


def cookie_header(resp, name):
    """The raw Set-Cookie line for `name`, or "" — so flags can be asserted as
    the browser would actually receive them."""
    for value in resp.headers.getlist("Set-Cookie"):
        if value.startswith(name + "="):
            return value
    return ""


def cookie_value(resp, name):
    raw = cookie_header(resp, name)
    return raw.split("=", 1)[1].split(";", 1)[0] if raw else ""


def decoded_session_payload(token):
    payload_b64 = token.partition(".")[0]
    return json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)))


def run():
    results = []

    def check(label, cond, detail=""):
        results.append(f"{'PASS' if cond else 'FAIL'}  {label}"
                       + ("" if cond else f" — {detail}"))

    tmp_root = tempfile.mkdtemp(prefix="wb_oidc_")
    db_path = os.path.join(tmp_root, "spine.db")
    make_fixture_db(db_path)

    orig_spine = os.environ.get("CIS_SPINE_PATH")
    os.environ["CIS_SPINE_PATH"] = db_path

    import workbench_app
    import card_factory_app
    import card_runner
    import workbench_auth
    import workbench_oidc
    import braingate_conversation

    for mod in (workbench_app, card_factory_app, card_runner):
        mod.DB_PATH = db_path

    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(workbench_oidc.workbench_oidc_bp)
    app.register_blueprint(braingate_conversation.braingate_conversation_bp)
    app.logger.disabled = True
    logging.getLogger("werkzeug").disabled = True

    provider = FakeProvider()
    workbench_oidc._http_get = provider.http_get
    workbench_oidc._http_post = provider.http_post
    orig_fetch_data = jwt.PyJWKClient.fetch_data
    jwt.PyJWKClient.fetch_data = provider.fetch_jwks

    calls = {"generator": 0, "dispatch": 0, "gateway": 0}
    orig_gateway = workbench_app._call_brain_gateway
    orig_generate_core = card_factory_app.generate_card_core
    orig_dispatch = card_runner.dispatch
    orig_wb_cr_dispatch = workbench_app._cr_dispatch
    orig_wb_generate_core = workbench_app.generate_card_core

    def fake_gateway(messages, timeout=60.0):
        calls["gateway"] += 1
        return "Understood — say more about the outcome you want.", None

    def tripwire_generator(*a, **kw):
        calls["generator"] += 1
        raise AssertionError("generate_card_core() reached")

    def tripwire_dispatch(*a, **kw):
        calls["dispatch"] += 1
        raise AssertionError("card_runner.dispatch() reached")

    workbench_app._call_brain_gateway = fake_gateway
    card_factory_app.generate_card_core = tripwire_generator
    card_runner.dispatch = tripwire_dispatch
    workbench_app._cr_dispatch = tripwire_dispatch
    workbench_app.generate_card_core = tripwire_generator

    def env(**kw):
        """Temporarily set/unset env vars, resetting the provider cache so a
        configuration change is not masked by a cached discovery document."""
        class _Ctx:
            def __enter__(self):
                self.saved = {k: os.environ.get(k) for k in kw}
                for k, v in kw.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
                workbench_oidc.reset_provider_cache()
            def __exit__(self, *a):
                for k, v in self.saved.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
                workbench_oidc.reset_provider_cache()
        return _Ctx()

    def start_login(client):
        """GET the login route; return (response, authorize params)."""
        resp = client.get(workbench_oidc.LOGIN_PATH)
        location = resp.headers.get("Location", "")
        query = parse_qs(urlsplit(location).query) if location else {}
        return resp, {k: v[0] for k, v in query.items()}, location

    def finish_login(client, params, claims=None, overrides=None,
                     state=None, code="auth-code-1", accept_json=True):
        """Drive the callback for a login started by start_login()."""
        provider.next_claims = dict(claims or {})
        provider.next_claim_overrides = dict(overrides or {})
        provider._pending_id_token = provider.make_id_token(params.get("nonce"))
        query = {"code": code, "state": state if state is not None else params.get("state")}
        query = {k: v for k, v in query.items() if v is not None}
        headers = {"Accept": "application/json"} if accept_json else {"Accept": "text/html"}
        return client.get(workbench_oidc.CALLBACK_PATH, query_string=query, headers=headers)

    def sign_in(email, name="Test Person", subject=None):
        """A complete, successful sign-in. Returns (client, callback response)."""
        client = app.test_client()
        _, params, _ = start_login(client)
        resp = finish_login(client, params, claims={
            "email": email,
            "name": name,
            "sub": subject or f"auth0|{email}",
        })
        return client, resp

    def csrf_of(client):
        return client.get(workbench_oidc.SESSION_PATH).get_json().get("csrf_token")

    try:
        # ── 1. Login initiation ───────────────────────────────────────────
        anon = app.test_client()
        resp, params, location = start_login(anon)
        check("1a. valid configuration -> 302 redirect to the provider",
              resp.status_code == 302, f"{resp.status_code} {location[:120]}")
        check("1b. the redirect goes to the provider's authorization endpoint",
              location.startswith(f"{ISSUER}/authorize?"), location[:160])
        check("1c. the redirect is HTTPS", urlsplit(location).scheme == "https")
        check("1d. response_type=code (Authorization Code flow)",
              params.get("response_type") == "code", str(params))
        check("1e. the configured client_id is sent",
              params.get("client_id") == CLIENT_ID)
        check("1f. a state value is generated", len(params.get("state", "")) >= 32,
              params.get("state", ""))
        check("1g. a nonce value is generated", len(params.get("nonce", "")) >= 32,
              params.get("nonce", ""))
        check("1h. PKCE S256 challenge is sent",
              params.get("code_challenge_method") == "S256"
              and len(params.get("code_challenge", "")) >= 43, str(params))
        check("1i. scopes are openid + profile + email",
              set((params.get("scope") or "").split()) == {"openid", "profile", "email"},
              params.get("scope"))
        check("1j. callback URI == configured public origin + the exact callback path",
              params.get("redirect_uri") == PUBLIC_ORIGIN + workbench_oidc.CALLBACK_PATH,
              params.get("redirect_uri"))
        check("1k. no `connection` is forced, so Universal Login can still offer "
              "Google AND email/password",
              "connection" not in params, str(params))
        check("1l. the client secret is nowhere in the redirect",
              CLIENT_SECRET not in location)
        tx_cookie = cookie_header(resp, workbench_oidc.TX_COOKIE_NAME)
        check("1m. the login transaction cookie is HttpOnly", "HttpOnly" in tx_cookie,
              tx_cookie)
        check("1n. the login transaction cookie is SameSite=Lax (it must survive "
              "the provider's cross-site redirect back)",
              "SameSite=Lax" in tx_cookie, tx_cookie)
        check("1o. the login transaction cookie is short-lived",
              f"Max-Age={workbench_oidc.TX_MAX_AGE_SECONDS}" in tx_cookie, tx_cookie)
        check("1p. the login transaction cookie is scoped to the auth routes only",
              f"Path={workbench_oidc.TX_COOKIE_PATH}" in tx_cookie, tx_cookie)

        # Two logins never reuse state/nonce/PKCE.
        _, params2, _ = start_login(app.test_client())
        check("1q. a second login gets a different state",
              params2["state"] != params["state"])
        check("1r. a second login gets a different nonce",
              params2["nonce"] != params["nonce"])
        check("1s. a second login gets a different PKCE challenge",
              params2["code_challenge"] != params["code_challenge"])

        # -- configuration failures --
        for var in ("CIS_WORKBENCH_OIDC_ISSUER", "CIS_WORKBENCH_OIDC_CLIENT_ID",
                    "CIS_WORKBENCH_OIDC_CLIENT_SECRET", "CIS_WORKBENCH_PUBLIC_ORIGIN",
                    "CIS_WORKBENCH_SESSION_SECRET"):
            with env(**{var: None}):
                r = app.test_client().get(workbench_oidc.LOGIN_PATH,
                                          headers={"Accept": "application/json"})
                check(f"1t. {var} unset -> login 503, not a redirect",
                      r.status_code == 503, f"got {r.status_code}")
                check(f"1u. {var} unset -> the missing variable is NAMED",
                      var in r.get_data(as_text=True))
        with env(CIS_WORKBENCH_ALLOWED_EMAILS=""):
            r = app.test_client().get(workbench_oidc.LOGIN_PATH,
                                      headers={"Accept": "application/json"})
            check("1v. empty allowlist -> login 503 (nobody could hold a session)",
                  r.status_code == 503, f"got {r.status_code}")

        for bad_origin, label in (
            ("http://plain.example.com", "plain HTTP"),
            ("javascript:alert(1)", "javascript:"),
            ("https://user:pass@example.com", "credentials in the URL"),
            ("https://example.com/injected/path", "an injected path"),
            ("https://example.com?next=evil", "a query string"),
            ("https://exa mple.com", "whitespace"),
            ("not-a-url", "a malformed value"),
            ("", "an empty value"),
        ):
            with env(CIS_WORKBENCH_PUBLIC_ORIGIN=bad_origin):
                r = app.test_client().get(workbench_oidc.LOGIN_PATH,
                                          headers={"Accept": "application/json"})
                check(f"1w. public origin with {label} -> refused 503, no redirect",
                      r.status_code == 503, f"got {r.status_code} for {bad_origin!r}")

        # The redirect URI never comes from the request's own Host header.
        spoof = app.test_client()
        r = spoof.get(workbench_oidc.LOGIN_PATH, base_url="https://attacker.example",
                      headers={"X-Forwarded-Host": "attacker.example",
                               "X-Forwarded-Proto": "https"})
        spoof_params = {k: v[0] for k, v in
                        parse_qs(urlsplit(r.headers.get("Location", "")).query).items()}
        check("1x. a spoofed Host/X-Forwarded-Host does NOT change the callback URI",
              spoof_params.get("redirect_uri") == PUBLIC_ORIGIN + workbench_oidc.CALLBACK_PATH,
              spoof_params.get("redirect_uri"))

        # ── 2. Callback: the happy path ───────────────────────────────────
        owner, owner_resp = sign_in(OWNER_EMAIL, "Eric Shelton", "auth0|eric")
        check("2a. valid state/code/token/claims -> 302 back into the Workbench",
              owner_resp.status_code == 302, owner_resp.get_data(as_text=True)[:200])
        check("2b. and it redirects to a same-origin path, not anywhere supplied",
              owner_resp.headers.get("Location") in ("/", "http://localhost/"),
              owner_resp.headers.get("Location"))
        session_cookie = cookie_header(owner_resp, workbench_auth.SESSION_COOKIE_NAME)
        check("2c. a CIS session cookie was issued", bool(session_cookie))
        check("2d. the login transaction cookie is cleared (single use)",
              "Max-Age=0" in cookie_header(owner_resp, workbench_oidc.TX_COOKIE_NAME),
              cookie_header(owner_resp, workbench_oidc.TX_COOKIE_NAME))

        status = owner.get(workbench_oidc.SESSION_PATH)
        body = status.get_json()
        check("2e. the session reports authenticated", body.get("authenticated") is True,
              str(body)[:200])
        check("2f. the identity is the provider's, with the canonical sub",
              body["identity"]["subject"] == "auth0|eric", str(body.get("identity")))
        check("2g. the email comes from the verified claim",
              body["identity"]["email"] == OWNER_EMAIL)
        check("2h. the display name is shown", body["identity"]["name"] == "Eric Shelton")
        check("2i. the role is owner, computed server-side",
              body["identity"]["role"] == "owner")

        # The exchange itself: what CIS actually sent to the token endpoint.
        last_request = provider.token_requests[-1]
        check("2j. the code exchange used grant_type=authorization_code",
              last_request.get("grant_type") == "authorization_code", str(last_request))
        check("2k. the code exchange sent the PKCE verifier",
              len(last_request.get("code_verifier", "")) >= 43, str(last_request))
        check("2l. the code exchange sent the client secret server-side",
              last_request.get("client_secret") == CLIENT_SECRET)
        check("2m. the code exchange sent the same configured redirect_uri",
              last_request.get("redirect_uri")
              == PUBLIC_ORIGIN + workbench_oidc.CALLBACK_PATH)

        # -- a collaborator goes through the SAME callback --
        collab, collab_resp = sign_in(COLLABORATOR_EMAIL, "A Collaborator",
                                      "google-oauth2|12345")
        check("2n. an allowlisted non-owner also signs in",
              collab_resp.status_code == 302)
        collab_identity = collab.get(workbench_oidc.SESSION_PATH).get_json()["identity"]
        check("2o. and gets the collaborator role",
              collab_identity["role"] == "collaborator", str(collab_identity))
        check("2p. a Google-connection subject flows through the same path",
              collab_identity["subject"] == "google-oauth2|12345")

        # ── 3. Callback: every rejection ──────────────────────────────────
        def rejected(label, expected_status, **finish_kwargs):
            client = app.test_client()
            _, p, _ = start_login(client)
            r = finish_login(client, p, **finish_kwargs)
            ok_status = r.status_code == expected_status
            no_cookie = not cookie_value(r, workbench_auth.SESSION_COOKIE_NAME)
            check(f"3{label} -> {expected_status}, and NO session is established",
                  ok_status and no_cookie,
                  f"status={r.status_code} cookie={cookie_value(r, workbench_auth.SESSION_COOKIE_NAME)[:40]}")
            # Whatever went wrong, the client must not be able to use the API.
            check(f"3{label} (cont.) the refused client stays unauthenticated",
                  client.get("/api/workbench/projects").status_code == 401)
            return r

        rejected("a. a forged state", 401, state="not-the-state")
        rejected("b. a missing state", 401, state="")

        # No transaction cookie at all: the callback was reached directly.
        direct = app.test_client()
        r = direct.get(workbench_oidc.CALLBACK_PATH,
                       query_string={"code": "c", "state": "s"},
                       headers={"Accept": "application/json"})
        check("3c. a callback with no login transaction at all -> 401",
              r.status_code == 401 and not cookie_value(r, workbench_auth.SESSION_COOKIE_NAME),
              f"got {r.status_code}")

        # A stale transaction: valid signature, expired.
        stale = app.test_client()
        stale_tx = workbench_auth.sign_payload(
            {"v": 1, "state": "s", "nonce": "n", "cv": "v" * 60,
             "exp": int(time.time()) - 5}, SESSION_SECRET)
        stale.set_cookie(workbench_oidc.TX_COOKIE_NAME, stale_tx,
                         path=workbench_oidc.TX_COOKIE_PATH)
        r = stale.get(workbench_oidc.CALLBACK_PATH, query_string={"code": "c", "state": "s"},
                      headers={"Accept": "application/json"})
        check("3d. an expired login transaction -> 401", r.status_code == 401)

        # A transaction cookie signed with the wrong secret.
        forged = app.test_client()
        forged.set_cookie(workbench_oidc.TX_COOKIE_NAME,
                          workbench_auth.sign_payload(
                              {"v": 1, "state": "s", "nonce": "n", "cv": "v" * 60,
                               "exp": int(time.time()) + 300}, "a-different-secret"),
                          path=workbench_oidc.TX_COOKIE_PATH)
        r = forged.get(workbench_oidc.CALLBACK_PATH, query_string={"code": "c", "state": "s"},
                       headers={"Accept": "application/json"})
        check("3e. a login transaction signed with another secret -> 401",
              r.status_code == 401)

        rejected("f. a nonce that does not match this login", 401,
                 overrides={"nonce": "some-other-nonce"})
        rejected("g. a missing nonce claim", 401, overrides={"nonce": _OMIT})
        rejected("h. an ID token from the wrong issuer", 401,
                 overrides={"iss": "https://evil.example.com/"})
        rejected("i. an ID token for another audience", 401,
                 overrides={"aud": "some-other-client-id"})
        rejected("j. a missing sub claim", 401, overrides={"sub": _OMIT})
        rejected("k. a missing email claim", 401, overrides={"email": _OMIT})
        rejected("l. an unverified email", 401, overrides={"email_verified": False})
        rejected("m. an expired ID token", 401,
                 overrides={"exp": int(time.time()) - 60})
        rejected("n. an email address not on the allowlist", 403,
                 claims={"email": OUTSIDER_EMAIL})

        provider.sign_with_imposter = True
        rejected("o. an ID token signed with a key the JWKS does not publish", 401)
        provider.sign_with_imposter = False

        provider.omit_id_token = True
        rejected("p. a token response with no id_token at all", 401)
        provider.omit_id_token = False

        provider.token_endpoint_error = "invalid_grant"
        rejected("q. a code the provider refuses to exchange", 401)
        provider.token_endpoint_error = None

        # An error handed back by the provider itself (user cancelled, etc.).
        cancelled = app.test_client()
        _, p, _ = start_login(cancelled)
        r = cancelled.get(workbench_oidc.CALLBACK_PATH, headers={"Accept": "application/json"},
                          query_string={"error": "access_denied",
                                        "error_description": "User cancelled",
                                        "state": p["state"]})
        check("3r. a provider-reported error -> 401 and no session",
              r.status_code == 401
              and not cookie_value(r, workbench_auth.SESSION_COOKIE_NAME))
        check("3s. and the provider's message is reported, not swallowed",
              "access_denied" in r.get_data(as_text=True))

        # A provider error description is attacker-influenced text.
        xss = app.test_client()
        _, p, _ = start_login(xss)
        r = xss.get(workbench_oidc.CALLBACK_PATH, headers={"Accept": "text/html"},
                    query_string={"error": "bad", "state": p["state"],
                                  "error_description": "<script>alert(1)</script>"})
        check("3t. provider-supplied error text is HTML-escaped, never rendered as markup",
              "<script>" not in r.get_data(as_text=True),
              r.get_data(as_text=True)[-300:])

        # A login transaction is single-use.
        replay = app.test_client()
        _, p, _ = start_login(replay)
        first = finish_login(replay, p)
        check("3u. the first use of a login transaction succeeds", first.status_code == 302)
        second = finish_login(replay, p)
        check("3v. replaying the same state/code afterwards -> 401 (transaction cleared)",
              second.status_code == 401, f"got {second.status_code}")

        # ── 4. No provider token is ever retained ─────────────────────────
        fresh = app.test_client()
        _, p, _ = start_login(fresh)
        cb = finish_login(fresh, p)
        token_value = cookie_value(cb, workbench_auth.SESSION_COOKIE_NAME)
        payload = decoded_session_payload(token_value)
        payload_text = json.dumps(payload)
        for label, secret in (
            ("the provider access token", "provider-access-token-SHOULD-NOT-BE-STORED"),
            ("the provider refresh token", "provider-refresh-token-SHOULD-NOT-BE-STORED"),
            ("the OIDC client secret", CLIENT_SECRET),
            ("the session secret", SESSION_SECRET),
            ("the API key", API_KEY),
        ):
            check(f"4a. the session cookie payload contains no {label}",
                  secret not in payload_text, payload_text[:200])
        check("4b. the session payload is exactly the expected claims and no more",
              set(payload) == {"v", "sub", "iss", "email", "name", "role",
                               "iat", "exp", "csrf"}, payload_text)
        check("4c. no raw ID token is kept in the session either",
              "eyJ" not in payload_text, payload_text[:200])

        status_text = owner.get(workbench_oidc.SESSION_PATH).get_data(as_text=True)
        for label, secret in (
            ("the provider access token", "provider-access-token-SHOULD-NOT-BE-STORED"),
            ("the provider refresh token", "provider-refresh-token-SHOULD-NOT-BE-STORED"),
            ("the OIDC client secret", CLIENT_SECRET),
            ("the session secret", SESSION_SECRET),
            ("the API key", API_KEY),
        ):
            check(f"4d. the session status response contains no {label}",
                  secret not in status_text, status_text[:200])
        check("4e. the session status response contains no raw JWT",
              "eyJ" not in status_text, status_text[:200])
        check("4f. the session status response does not publish the allowlist",
              OUTSIDER_EMAIL not in status_text and COLLABORATOR_EMAIL not in status_text,
              status_text[:200])

        # ── 5. Session cookie posture ─────────────────────────────────────
        check("5a. the session cookie is HttpOnly", "HttpOnly" in session_cookie,
              session_cookie)
        check("5b. the session cookie is SameSite=Strict",
              "SameSite=Strict" in session_cookie, session_cookie)
        check("5c. the session cookie is scoped to the Workbench API path",
              f"Path={workbench_auth.SESSION_COOKIE_PATH}" in session_cookie,
              session_cookie)
        check("5d. the session cookie is finite-lived", "Max-Age=" in session_cookie,
              session_cookie)
        check("5e. this run opted out of Secure explicitly, so it is absent",
              "Secure" not in session_cookie, session_cookie)
        with env(CIS_WORKBENCH_COOKIE_INSECURE=None):
            check("5f. the DEFAULT posture (no override) is Secure",
                  workbench_auth.cookie_secure_flag() is True)
            for bogus in ("0", "false", "no", "maybe", "TRUEISH"):
                with env(CIS_WORKBENCH_COOKIE_INSECURE=bogus):
                    check(f"5g. override value {bogus!r} does not disable Secure",
                          workbench_auth.cookie_secure_flag() is True)

        # ── 6. Authorization is re-derived, never trusted from the cookie ─
        demoted = app.test_client()
        _, p, _ = start_login(demoted)
        finish_login(demoted, p, claims={"email": OWNER_EMAIL, "sub": "auth0|eric"})
        check("6a. signed in as owner",
              demoted.get(workbench_oidc.SESSION_PATH).get_json()["identity"]["role"]
              == "owner")
        with env(CIS_WORKBENCH_OWNER_EMAILS=""):
            check("6b. removing the owner list demotes the SAME cookie to collaborator "
                  "immediately",
                  demoted.get(workbench_oidc.SESSION_PATH)
                  .get_json()["identity"]["role"] == "collaborator")
        with env(CIS_WORKBENCH_ALLOWED_EMAILS=COLLABORATOR_EMAIL):
            r = demoted.get(workbench_oidc.SESSION_PATH)
            check("6c. removing the address from the allowlist -> 403 on the same cookie",
                  r.status_code == 403, f"got {r.status_code}")
            check("6d. and the API denies it too, without waiting for expiry",
                  demoted.get("/api/workbench/projects").status_code == 401)
            check("6e. and the stale session cookie is cleared",
                  "Max-Age=0" in cookie_header(r, workbench_auth.SESSION_COOKIE_NAME))
        # Clearing the cookie on a 403 is the point: the de-authorized client is
        # not left holding a credential. Restoring the allowlist therefore
        # restores the ability to sign in, not the discarded session.
        check("6f. after the cookie was cleared, the old client is signed out",
              demoted.get(workbench_oidc.SESSION_PATH).get_json()["authenticated"]
              is False)
        restored, restored_resp = sign_in(OWNER_EMAIL, "Eric Shelton", "auth0|eric")
        check("6f2. and restoring the allowlist lets the same person sign in again",
              restored_resp.status_code == 302
              and restored.get("/api/workbench/projects").status_code == 200)

        # A role cannot be asserted by the browser.
        claimed = app.test_client()
        _, p, _ = start_login(claimed)
        finish_login(claimed, p, claims={"email": COLLABORATOR_EMAIL,
                                         "name": "Owner Admin Root",
                                         "sub": "auth0|c"})
        role_body = claimed.get(workbench_oidc.SESSION_PATH,
                                headers={"X-CIS-Role": "owner"},
                                query_string={"role": "owner"}).get_json()
        check("6g. neither a header, a query parameter nor a display name can "
              "confer the owner role",
              role_body["identity"]["role"] == "collaborator", str(role_body))

        # An owner address missing from the allowlist is denied, not promoted.
        with env(CIS_WORKBENCH_ALLOWED_EMAILS=COLLABORATOR_EMAIL,
                 CIS_WORKBENCH_OWNER_EMAILS=OWNER_EMAIL):
            c = app.test_client()
            _, p, _ = start_login(c)
            r = finish_login(c, p, claims={"email": OWNER_EMAIL, "sub": "auth0|eric"})
            check("6h. an owner address absent from the allowlist is refused 403, "
                  "never silently allowed", r.status_code == 403, f"got {r.status_code}")
            check("6i. and the misconfiguration is reported rather than hidden",
                  workbench_auth.misconfigured_owner_emails() == frozenset({OWNER_EMAIL}))

        # Case and whitespace in configuration and in claims.
        with env(CIS_WORKBENCH_ALLOWED_EMAILS=f"  {OWNER_EMAIL.upper()} , x@y.z ",
                 CIS_WORKBENCH_OWNER_EMAILS=f" {OWNER_EMAIL.upper()} "):
            c = app.test_client()
            _, p, _ = start_login(c)
            r = finish_login(c, p, claims={"email": OWNER_EMAIL.upper(), "sub": "auth0|e"})
            check("6j. allowlist matching is case-insensitive after normalization",
                  r.status_code == 302, f"got {r.status_code}")
        for wildcard in ("*", "*@example.com", "*@*"):
            with env(CIS_WORKBENCH_ALLOWED_EMAILS=wildcard):
                check(f"6k. wildcard allowlist {wildcard!r} authorizes nobody",
                      workbench_auth.resolve_role(OWNER_EMAIL) is None
                      and workbench_auth.allowed_emails() == frozenset())
        with env(CIS_WORKBENCH_ALLOWED_EMAILS=""):
            check("6l. an empty allowlist authorizes nobody",
                  workbench_auth.resolve_role(OWNER_EMAIL) is None)

        # ── 7. Session lifetime, CSRF, logout ─────────────────────────────
        owner_csrf = csrf_of(owner)
        check("7a. the session status hands back a CSRF token", bool(owner_csrf))
        check("7b. and names the header to send it in",
              owner.get(workbench_oidc.SESSION_PATH).get_json()["csrf_header"]
              == workbench_auth.CSRF_HEADER)
        check("7c. the status re-issues the SAME token, not a new grant",
              csrf_of(owner) == owner_csrf)
        check("7d. the session reports a finite expiry",
              owner.get(workbench_oidc.SESSION_PATH).get_json()["expires_at"]
              > int(time.time()))

        check("7e. an OIDC session authorizes a GET",
              owner.get("/api/workbench/projects").status_code == 200)
        r = owner.post("/api/workbench/projects", json={"name": "No CSRF"})
        check("7f. a session POST with no CSRF header -> 403", r.status_code == 403)
        r = owner.post("/api/workbench/projects", json={"name": "Bad CSRF"},
                       headers={workbench_auth.CSRF_HEADER: "not-the-token"})
        check("7g. a session POST with the wrong CSRF -> 403", r.status_code == 403)
        names = [p["name"] for p in
                 owner.get("/api/workbench/projects").get_json()["projects"]]
        check("7h. neither CSRF denial mutated anything",
              "No CSRF" not in names and "Bad CSRF" not in names, str(names))
        r = owner.post("/api/workbench/projects", json={"name": "With CSRF"},
                       headers={workbench_auth.CSRF_HEADER: owner_csrf})
        check("7i. a session POST with a valid CSRF -> 201", r.status_code == 201,
              r.get_data(as_text=True)[:160])
        pid = r.get_json()["project"]["id"]
        check("7j. another session's CSRF token is rejected",
              collab.post("/api/workbench/projects", json={"name": "Cross"},
                          headers={workbench_auth.CSRF_HEADER: owner_csrf}
                          ).status_code == 403)

        expired_client = app.test_client()
        expired_token, _ = workbench_auth.issue_session_token(
            SESSION_SECRET, 10, subject="auth0|eric", email=OWNER_EMAIL,
            role="owner", name="Eric", issuer=ISSUER, now=time.time() - 3600)
        expired_client.set_cookie(workbench_auth.SESSION_COOKIE_NAME, expired_token,
                                  path=workbench_auth.SESSION_COOKIE_PATH)
        check("7k. an expired session -> 401 on a read",
              expired_client.get("/api/workbench/projects").status_code == 401)
        check("7l. an expired session reports authenticated=false",
              expired_client.get(workbench_oidc.SESSION_PATH)
              .get_json()["authenticated"] is False)
        gw_before = calls["gateway"]
        r = expired_client.post(f"/api/workbench/projects/{pid}/messages",
                                json={"message": "x", "request_id": "expired-1"},
                                headers={workbench_auth.CSRF_HEADER: owner_csrf})
        check("7m. an expired session cannot mutate, and nothing ran",
              r.status_code == 401 and calls["gateway"] == gw_before)

        garbage = app.test_client()
        garbage.set_cookie(workbench_auth.SESSION_COOKIE_NAME, "!!!not-a-token!!!",
                           path=workbench_auth.SESSION_COOKIE_PATH)
        check("7n. a malformed session cookie -> 401, never 500",
              garbage.get("/api/workbench/projects").status_code == 401)

        # A v1 (shared-password era) token must not verify against this build.
        legacy = workbench_auth.sign_payload(
            {"v": 1, "sub": "workbench-browser", "iat": int(time.time()),
             "exp": int(time.time()) + 3600, "csrf": "x"}, SESSION_SECRET)
        legacy_client = app.test_client()
        legacy_client.set_cookie(workbench_auth.SESSION_COOKIE_NAME, legacy,
                                 path=workbench_auth.SESSION_COOKIE_PATH)
        check("7o. a pre-OIDC shared-password session token no longer authenticates",
              legacy_client.get("/api/workbench/projects").status_code == 401)

        out, _ = sign_in(OWNER_EMAIL, "Eric", "auth0|eric")
        out_csrf = csrf_of(out)
        r = out.post(workbench_oidc.LOGOUT_PATH)
        check("7p. logout -> 200", r.status_code == 200)
        cleared = cookie_header(r, workbench_auth.SESSION_COOKIE_NAME)
        check("7q. logout clears the session cookie", "Max-Age=0" in cleared, cleared)
        check("7r. the cleared cookie keeps HttpOnly and the same narrow path",
              "HttpOnly" in cleared
              and f"Path={workbench_auth.SESSION_COOKIE_PATH}" in cleared, cleared)
        check("7s. after logout the API denies the client",
              out.get("/api/workbench/projects").status_code == 401)
        check("7t. a retained CSRF token grants nothing after logout",
              out.post("/api/workbench/projects", json={"name": "after logout"},
                       headers={workbench_auth.CSRF_HEADER: out_csrf}).status_code == 401)
        check("7u. logout is idempotent", out.post(workbench_oidc.LOGOUT_PATH)
              .status_code == 200)
        logout_body = r.get_json()
        check("7v. logout offers the provider's end-session URL rather than "
              "following it silently",
              (logout_body.get("provider_logout_url") or "").startswith(
                  f"{ISSUER}/oidc/logout"), str(logout_body)[:200])
        check("7w. logout states honestly that the provider session is NOT ended",
              "has not been ended" in logout_body["provider_logout_note"]
              or "also end your session" in logout_body["provider_logout_note"],
              logout_body["provider_logout_note"])
        check("7x. the logout response leaks no secret",
              CLIENT_SECRET not in json.dumps(logout_body)
              and SESSION_SECRET not in json.dumps(logout_body))

        # ── 8. The combined (dual) auth contract ──────────────────────────
        api = app.test_client()
        api.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {API_KEY}"
        check("8a. a valid Bearer still works", api.get("/api/workbench/projects")
              .status_code == 200)
        check("8b. a Bearer POST needs no browser CSRF",
              api.post("/api/workbench/projects", json={"name": "Bearer made this"})
              .status_code == 201)
        wrong = app.test_client()
        wrong.environ_base["HTTP_AUTHORIZATION"] = "Bearer wrong-key"
        check("8c. a wrong Bearer -> 401", wrong.get("/api/workbench/projects")
              .status_code == 401)
        # An invalid Bearer does not fall back to anything unless the SAME
        # client also holds a genuinely valid session.
        both = app.test_client()
        _, p, _ = start_login(both)
        finish_login(both, p, claims={"email": OWNER_EMAIL, "sub": "auth0|eric"})
        both.environ_base["HTTP_AUTHORIZATION"] = "Bearer wrong-key"
        check("8d. an invalid Bearer alongside a VALID session is allowed on the "
              "session's own merit", both.get("/api/workbench/projects")
              .status_code == 200)
        check("8e. an invalid Bearer with no session is denied",
              wrong.get("/api/workbench/projects").status_code == 401)
        check("8f. neither mechanism presented -> 401",
              app.test_client().get("/api/workbench/projects").status_code == 401)
        with env(CIS_PIPELINE_API_KEY=None):
            check("8g. API key absent: an OIDC session still works",
                  owner.get("/api/workbench/projects").status_code == 200)
            check("8h. API key absent: Bearer no longer works",
                  api.get("/api/workbench/projects").status_code == 401)
        with env(CIS_WORKBENCH_ALLOWED_EMAILS=None, CIS_WORKBENCH_SESSION_SECRET=None):
            check("8i. browser auth absent: Bearer still works",
                  api.get("/api/workbench/projects").status_code == 200)
            check("8j. browser auth absent: a session is ignored",
                  owner.get("/api/workbench/projects").status_code == 401)
        with env(CIS_PIPELINE_API_KEY=None, CIS_WORKBENCH_ALLOWED_EMAILS=None,
                 CIS_WORKBENCH_SESSION_SECRET=None):
            check("8k. NO mechanism configured -> 503 fail-closed",
                  app.test_client().get("/api/workbench/projects").status_code == 503)
            check("8l. and a previously valid session cannot rescue it",
                  owner.get("/api/workbench/projects").status_code == 503)
            check("8m. and a valid Bearer cannot rescue it",
                  api.get("/api/workbench/projects").status_code == 503)
            check("8n. workbench_auth reports nothing configured",
                  not workbench_auth.is_configured())
            check("8o. and the session route says so honestly, as 503",
                  app.test_client().get(workbench_oidc.SESSION_PATH).status_code == 503)
        check("8p. after every permutation, normal access is restored",
              owner.get("/api/workbench/projects").status_code == 200)

        # ── 9. CIS owns no password endpoint any more ─────────────────────
        rules = sorted({str(r.rule) for r in app.url_map.iter_rules()
                        if r.endpoint != "static"})
        check("9a. no route in the registered surface mentions a password",
              not any("password" in p.lower() or "login" in p.lower().replace("auth/login", "")
                      for p in rules), str(rules))
        check("9b. the old shared-password login route is gone",
              "/api/workbench/session/login" not in rules, str(rules))
        for legacy_path in ("/api/workbench/session/login", "/api/workbench/session",
                            "/api/workbench/session/logout"):
            check(f"9c. {legacy_path} is no longer served -> 404",
                  app.test_client().post(legacy_path, json={"password": "x"})
                  .status_code == 404)
        import workbench_session as ws
        check("9d. workbench_session.py exports no blueprint at all",
              not hasattr(ws, "workbench_session_bp"))
        source_text = ""
        for name in ("workbench_oidc.py", "workbench_session.py", "workbench_auth.py"):
            with open(os.path.join(os.path.dirname(__file__), "..", name)) as f:
                source_text += f.read()
        check("9e. no module reads a browser password from the environment",
              "CIS_WORKBENCH_BROWSER_PASSWORD" not in source_text)
        check("9f. the auth surface is exactly the four OIDC lifecycle routes "
              "plus the Braingate conversation routes",
              set(rules) == {
                  workbench_oidc.LOGIN_PATH, workbench_oidc.CALLBACK_PATH,
                  workbench_oidc.SESSION_PATH, workbench_oidc.LOGOUT_PATH,
                  "/api/workbench/projects",
                  "/api/workbench/projects/<project_id>",
                  "/api/workbench/projects/<project_id>/messages",
              }, str(rules))

        # ── 10. Authentication never widens the stage boundary ────────────
        forbidden = [
            ("POST", "/api/cardfactory/asks", {"project": "p", "ask": "a", "done_when": "d"}),
            ("POST", "/api/cardfactory/asks/1/generate", {"request_id": "x"}),
            ("GET", "/api/cardfactory/cards", None),
            ("POST", "/api/cardrunner/dispatch", {"card_factory_card_id": 1}),
            ("GET", "/api/cardrunner/runs", None),
            ("GET", f"/api/workbench/projects/{pid}/proposals", None),
            ("GET", "/api/workbench/proposals/1", None),
            ("POST", "/api/workbench/proposals/1/confirm-direction", {"request_id": "x"}),
            ("POST", "/api/workbench/proposals/1/approve", {"expected_proposal_revision": 1}),
        ]
        gw_before = calls["gateway"]
        for role_label, client in (("owner", owner), ("collaborator", collab)):
            token = csrf_of(client)
            for method, path, payload in forbidden:
                r = client.open(path, method=method, json=payload,
                                headers={workbench_auth.CSRF_HEADER: token})
                check(f"10a. an authenticated {role_label} still cannot reach "
                      f"{method} {path}", r.status_code == 404, f"got {r.status_code}")
            for mode in ("draft_proposal", "revise_proposal"):
                r = client.post(f"/api/workbench/projects/{pid}/messages",
                                json={"message": "draft it", "mode": mode,
                                      "request_id": f"{role_label}-{mode}"},
                                headers={workbench_auth.CSRF_HEADER: token})
                check(f"10b. an authenticated {role_label}: mode={mode} still refused",
                      r.status_code == 403, r.get_data(as_text=True)[:140])
        check("10c. no model call came from any refused downstream attempt",
              calls["gateway"] == gw_before, str(calls))
        check("10d. generation tripwires remain at zero", calls["generator"] == 0)
        check("10e. dispatch tripwires remain at zero", calls["dispatch"] == 0)

        # The conversation capability itself still works for both roles.
        for role_label, client in (("owner", owner), ("collaborator", collab)):
            before = calls["gateway"]
            r = client.post(f"/api/workbench/projects/{pid}/messages",
                            json={"message": "hello", "request_id": f"chat-{role_label}"},
                            headers={workbench_auth.CSRF_HEADER: csrf_of(client)})
            check(f"10f. an authenticated {role_label} CAN hold a Braingate "
                  "conversation", r.status_code == 200 and calls["gateway"] == before + 1,
                  r.get_data(as_text=True)[:160])

        # ── 11. No schema change ──────────────────────────────────────────
        conn = sqlite3.connect(db_path)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        check("11a. OIDC auth created no session/user/auth/identity table",
              not any(t for t in tables
                      if any(w in t.lower() for w in
                             ("session", "user", "auth", "login", "identity", "oidc"))),
              str(sorted(tables)))
        check("11b. braingate_conversation still requires only 0035 + 0038",
              braingate_conversation.REQUIRED_MIGRATIONS
              == ("0035_workbench.sql", "0038_workbench_action_proposals.sql"))

        # ── 12. Algorithm allowlist ───────────────────────────────────────
        check("12a. `none` is never an acceptable ID token algorithm",
              "none" not in workbench_oidc.ALLOWED_ID_TOKEN_ALGORITHMS)
        check("12b. no HMAC algorithm is acceptable (the client secret is not a "
              "token signing key)",
              not any(a.startswith("HS")
                      for a in workbench_oidc.ALLOWED_ID_TOKEN_ALGORITHMS))
        check("12c. a provider advertising only `none` yields no usable algorithm",
              workbench_oidc.id_token_algorithms(
                  {"id_token_signing_alg_values_supported": ["none"]}) == [])
        check("12d. a provider advertising only HS256 yields no usable algorithm",
              workbench_oidc.id_token_algorithms(
                  {"id_token_signing_alg_values_supported": ["HS256"]}) == [])
        check("12e. RS256 is accepted where the provider advertises it",
              workbench_oidc.id_token_algorithms(
                  {"id_token_signing_alg_values_supported": ["RS256", "none"]}) == ["RS256"])

        # A discovery document that names a different issuer is refused.
        workbench_oidc.reset_provider_cache()
        provider.metadata_overrides = {"issuer": "https://someone-else.example.com/"}
        metadata, error = workbench_oidc.fetch_provider_metadata(ISSUER)
        check("12f. a discovery document naming a different issuer is refused",
              metadata is None and "issuer" in (error or ""), str(error))
        provider.metadata_overrides = {"token_endpoint": "http://plain.example.com/token"}
        workbench_oidc.reset_provider_cache()
        metadata, error = workbench_oidc.fetch_provider_metadata(ISSUER)
        check("12g. a discovery document with a plain-HTTP token endpoint is refused",
              metadata is None and "https" in (error or ""), str(error))
        provider.metadata_overrides = {}
        workbench_oidc.reset_provider_cache()

        check("13. FINAL: no generator or dispatch call anywhere in this suite",
              calls["generator"] == 0 and calls["dispatch"] == 0, str(calls))

    finally:
        jwt.PyJWKClient.fetch_data = orig_fetch_data
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
