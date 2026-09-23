"""
workbench_oidc.py — OpenID Connect authentication for the Workbench UI.

WB.1 STANDARD-OIDC. The user experience this implements is an ordinary one:

    open Workbench -> Sign in -> Auth0 Universal Login
                   -> Continue with Google  OR  email + password
                   -> back in the Workbench, signed in as an individual

CIS is the Relying Party and nothing more. It does not store, validate, reset
or hash anyone's password, and it does not speak Google's OAuth protocol
itself — a Google identity and an Auth0 database identity arrive through this
one callback, are validated the same way, and are authorized by the same
server-side allowlist. There is no second login path to keep in step.

What is deliberately NOT here: any project, conversation, proposal, card
generation or dispatch capability. This blueprint answers "who is using the
currently registered stage", never "which stages exist". Registering it grants
authentication and nothing else — an owner who signs in still gets 404 from
Card Factory and Card Runner, because those blueprints are not registered.

── Protocol ─────────────────────────────────────────────────────────────────

Authorization Code flow with PKCE, against the provider's own discovery
document. The protocol work is done by maintained libraries rather than by
hand: oauthlib's WebApplicationClient builds the authorization request and
parses the token response, and PyJWT (with PyJWKClient) verifies the ID token's
signature against the provider's JWKS and checks iss/aud/exp/iat. Both are
already dependencies of this repository; nothing here re-implements a JWT
signature check.

Checks that must all pass before a CIS session exists:

    state          bound to a signed, short-lived, HttpOnly cookie
    PKCE           S256 challenge issued at login, verifier sent at exchange
    signature      provider JWKS, asymmetric algorithms only, never "none"
    issuer         exactly the configured issuer
    audience       exactly the configured client_id (azp checked if multi-aud)
    expiry         enforced by PyJWT, not trusted from the token
    nonce          constant-time compare against the login transaction
    sub            present — the canonical external user identifier
    email          present, and email_verified true where the provider sends it
    allowlist      CIS_WORKBENCH_ALLOWED_EMAILS, checked server-side
    role           computed server-side from configuration, never from input

Any failure establishes no session, sets no cookie, exposes no token and
returns an honest error. There is no code path that falls through to
"authenticated".

── Tokens ───────────────────────────────────────────────────────────────────

The provider's access token and refresh token are used for nothing and are
therefore kept nowhere: not in the session cookie, not in a database, not in a
log line, not in a response. The Workbench does not call Google or Auth0 APIs
on the user's behalf, so retaining a credential that would let it do so would
be storing risk in exchange for no capability. The ID token is validated,
read for its claims, and dropped.

── Redirect URI ─────────────────────────────────────────────────────────────

Built from CIS_WORKBENCH_PUBLIC_ORIGIN, never from the incoming Host or any
X-Forwarded-* header. Those are attacker-controllable, and a redirect URI
assembled from them is how an authorization code ends up at someone else's
callback. The configured origin must be HTTPS and is validated before use.

During development that origin is a Cloudflare Quick Tunnel URL
(https://<random-words>.trycloudflare.com). Quick Tunnel URLs change when the
tunnel is recreated; when that happens, Auth0's Allowed Callback/Logout/Origin
entries must be updated to the new exact URL. That is a property of temporary
development hosting, and the answer to it is never a wildcard redirect URI or
a relaxed redirect check — see tools/development/quick_tunnel.py, which prints
the exact values to paste.
"""
import base64
import hashlib
import hmac
import html
import os
import secrets
import time
from urllib.parse import urlencode, urlsplit

import jwt
import requests
from flask import Blueprint, jsonify, make_response, redirect, request
from jwt import PyJWKClient
from oauthlib.oauth2 import WebApplicationClient

from workbench_auth import (
    ALLOWED_EMAILS_ENV,
    CSRF_HEADER,
    FORBIDDEN_STATUS,
    NOT_CONFIGURED_STATUS,
    OWNER_EMAILS_ENV,
    SESSION_SECRET_ENV,
    UNAUTHORIZED_STATUS,
    allowed_emails,
    browser_auth_configured,
    configured_session_secret,
    cookie_secure_flag,
    current_session,
    misconfigured_owner_emails,
    resolve_role,
    sign_payload,
    verify_payload,
)
from workbench_session import clear_session_cookie, establish_session, safe_identity

workbench_oidc_bp = Blueprint("workbench_oidc", __name__)

OIDC_ISSUER_ENV = "CIS_WORKBENCH_OIDC_ISSUER"
OIDC_CLIENT_ID_ENV = "CIS_WORKBENCH_OIDC_CLIENT_ID"
OIDC_CLIENT_SECRET_ENV = "CIS_WORKBENCH_OIDC_CLIENT_SECRET"
PUBLIC_ORIGIN_ENV = "CIS_WORKBENCH_PUBLIC_ORIGIN"

AUTH_BASE = "/api/workbench/auth"
LOGIN_PATH = f"{AUTH_BASE}/login"
CALLBACK_PATH = f"{AUTH_BASE}/callback"
SESSION_PATH = f"{AUTH_BASE}/session"
LOGOUT_PATH = f"{AUTH_BASE}/logout"

# Where the browser is sent once a session exists. Same-origin and path-only,
# so no user-supplied value can turn the callback into an open redirect.
POST_LOGIN_PATH = "/"

OIDC_SCOPES = ["openid", "profile", "email"]

# The login transaction: state, nonce and the PKCE verifier, signed into a
# cookie rather than held in server memory (this app runs multiple workers and
# keeps no session store). SameSite=Lax, not Strict, because the browser
# arrives at the callback from the provider's origin and a Strict cookie would
# not be sent — which is exactly why the long-lived session cookie is a
# separate cookie that stays Strict.
TX_COOKIE_NAME = "cis_workbench_oidc_tx"
TX_COOKIE_PATH = AUTH_BASE
TX_COOKIE_SAMESITE = "Lax"
TX_MAX_AGE_SECONDS = 10 * 60

# Asymmetric only. An allowlist rather than "whatever the provider advertises"
# so that a provider document offering "none" or an HMAC algorithm — where the
# "key" would be the client secret, or nothing at all — cannot talk this client
# into accepting a token it should reject.
ALLOWED_ID_TOKEN_ALGORITHMS = frozenset({
    "RS256", "RS384", "RS512",
    "PS256", "PS384", "PS512",
    "ES256", "ES384", "ES512",
})

DISCOVERY_SUFFIX = "/.well-known/openid-configuration"
HTTP_TIMEOUT_SECONDS = 10
METADATA_TTL_SECONDS = 300

# Cached discovery document, keyed by issuer: {issuer: (fetched_at, metadata)}.
_metadata_cache = {}
# Cached JWKS clients, keyed by jwks_uri. PyJWKClient does its own key caching.
_jwks_clients = {}


# ── Configuration ────────────────────────────────────────────────────────

def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def configured_issuer() -> str:
    """The provider issuer, with any trailing slash removed.

    Auth0 writes its issuer WITH a trailing slash and CIS operators copy it
    from the dashboard either way; discovery and the `iss` claim comparison
    both need one settled form, so it is normalized once here.
    """
    return _env(OIDC_ISSUER_ENV).rstrip("/")


def configured_client_id() -> str:
    return _env(OIDC_CLIENT_ID_ENV)


def configured_client_secret() -> str:
    """Server-only. Never logged, never returned, never sent to the browser."""
    return _env(OIDC_CLIENT_SECRET_ENV)


def validate_public_origin(raw: str):
    """(origin, None) for a usable public origin, else (None, reason).

    The origin is the one security-sensitive piece of configuration that the
    protocol turns into a URL the provider will redirect a real authorization
    code to, so it is validated rather than trusted:

      * https only — http would send the code over plaintext, and a provider
        that accepted it would be the only thing standing between a code and
        anyone on the path;
      * a host, and no credentials in it — `https://user:pass@host` is both a
        credential in a URL and a classic redirect-parsing trick;
      * no path, query or fragment — those turn "the origin" into somewhere a
        path could be injected;
      * no whitespace or control characters anywhere.

    A `javascript:` value fails on the scheme check, as does `data:`,
    `file:` and every other non-https scheme.
    """
    text = (raw or "").strip()
    if not text:
        return None, f"{PUBLIC_ORIGIN_ENV} is not set"
    if any(c.isspace() or ord(c) < 0x20 or ord(c) == 0x7F for c in text):
        return None, f"{PUBLIC_ORIGIN_ENV} contains whitespace or control characters"
    try:
        parts = urlsplit(text)
    except ValueError as exc:
        return None, f"{PUBLIC_ORIGIN_ENV} is not a parseable URL ({exc})"
    if parts.scheme.lower() != "https":
        return None, (
            f"{PUBLIC_ORIGIN_ENV} must be an https:// origin for OIDC "
            f"(got {parts.scheme or 'no'} scheme)"
        )
    if not parts.hostname:
        return None, f"{PUBLIC_ORIGIN_ENV} has no host"
    if parts.username or parts.password or "@" in parts.netloc:
        return None, f"{PUBLIC_ORIGIN_ENV} must not contain credentials"
    if parts.path not in ("", "/"):
        return None, f"{PUBLIC_ORIGIN_ENV} must be an origin only, with no path"
    if parts.query or parts.fragment:
        return None, f"{PUBLIC_ORIGIN_ENV} must not contain a query or fragment"
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}", None


def configured_public_origin():
    return validate_public_origin(_env(PUBLIC_ORIGIN_ENV))


def redirect_uri() -> str:
    """The exact callback URL Auth0 must have on its Allowed Callback URLs.

    Built from configuration only. request.host, request.url_root and every
    X-Forwarded-* header are deliberately unused.
    """
    origin, _ = configured_public_origin()
    return f"{origin}{CALLBACK_PATH}" if origin else ""


def configuration_problems():
    """Every reason a login cannot be started right now, in plain words.

    Returned as a list so an operator sees all of them at once instead of
    fixing one variable per attempt. Values are never included — only names.
    """
    problems = []
    if not configured_issuer():
        problems.append(f"{OIDC_ISSUER_ENV} is not set")
    if not configured_client_id():
        problems.append(f"{OIDC_CLIENT_ID_ENV} is not set")
    if not configured_client_secret():
        problems.append(f"{OIDC_CLIENT_SECRET_ENV} is not set")
    _, origin_error = configured_public_origin()
    if origin_error:
        problems.append(origin_error)
    if not configured_session_secret():
        problems.append(f"{SESSION_SECRET_ENV} is not set")
    if not allowed_emails():
        problems.append(
            f"{ALLOWED_EMAILS_ENV} is empty — with no authorized address, a "
            "successful provider login still cannot become a Workbench session"
        )
    return problems


def oidc_configured() -> bool:
    return not configuration_problems()


# ── Provider metadata ────────────────────────────────────────────────────

def _http_get(url: str):
    """The only outbound GET. A single seam so tests can serve a fake provider
    without any network access."""
    return requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)


def _http_post(url: str, data: str, headers: dict):
    """The only outbound POST — the authorization code exchange."""
    return requests.post(url, data=data, headers=headers,
                         timeout=HTTP_TIMEOUT_SECONDS)


def fetch_provider_metadata(issuer: str):
    """(metadata, None) or (None, reason). Cached for METADATA_TTL_SECONDS.

    The discovery URL is derived from the configured issuer, so a provider
    cannot point this client at someone else's endpoints by what it returns.
    The endpoints it does return are required to be https and to belong to a
    document fetched from the configured issuer's own well-known path.
    """
    cached = _metadata_cache.get(issuer)
    if cached and (time.time() - cached[0]) < METADATA_TTL_SECONDS:
        return cached[1], None

    url = f"{issuer}{DISCOVERY_SUFFIX}"
    try:
        resp = _http_get(url)
    except Exception as exc:
        return None, f"provider discovery request failed: {type(exc).__name__}"
    if getattr(resp, "status_code", 0) != 200:
        return None, f"provider discovery returned HTTP {getattr(resp, 'status_code', '?')}"
    try:
        metadata = resp.json()
    except Exception:
        return None, "provider discovery returned a non-JSON document"
    if not isinstance(metadata, dict):
        return None, "provider discovery returned a non-object document"

    for key in ("issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"):
        value = metadata.get(key)
        if not isinstance(value, str) or not value:
            return None, f"provider discovery document has no usable {key}"
    if metadata["issuer"].rstrip("/") != issuer:
        # A document that names a different issuer than the one it was fetched
        # from is either a misconfiguration or a redirect somewhere unintended.
        return None, "provider discovery document issuer does not match the configured issuer"
    for key in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        if urlsplit(metadata[key]).scheme.lower() != "https":
            return None, f"provider {key} is not https"
    if metadata.get("end_session_endpoint") and \
            urlsplit(metadata["end_session_endpoint"]).scheme.lower() != "https":
        metadata = dict(metadata)
        metadata.pop("end_session_endpoint", None)

    _metadata_cache[issuer] = (time.time(), metadata)
    return metadata, None


def id_token_algorithms(metadata: dict):
    """The algorithms this client will accept for THIS provider.

    The provider's advertised list intersected with the asymmetric allowlist.
    An empty result is a refusal to guess, not a fallback to something.
    """
    advertised = metadata.get("id_token_signing_alg_values_supported")
    if not isinstance(advertised, list) or not advertised:
        advertised = ["RS256"]
    return sorted({a for a in advertised if a in ALLOWED_ID_TOKEN_ALGORITHMS})


def _jwks_client(jwks_uri: str):
    client = _jwks_clients.get(jwks_uri)
    if client is None:
        client = PyJWKClient(jwks_uri, timeout=HTTP_TIMEOUT_SECONDS)
        _jwks_clients[jwks_uri] = client
    return client


def reset_provider_cache():
    """Drop cached discovery documents and JWKS clients.

    For tests and for an operator who has just repointed the issuer; a stale
    document would otherwise keep a wrong configuration alive for its TTL.
    """
    _metadata_cache.clear()
    _jwks_clients.clear()


# ── ID token validation ──────────────────────────────────────────────────

def validate_id_token(id_token: str, metadata: dict, client_id: str,
                      expected_nonce: str):
    """(claims, None) for a token that passes every check, else (None, reason).

    Signature, issuer, audience, expiry and iat are verified by PyJWT against
    the provider's JWKS — this function adds only the checks PyJWT does not
    make for us: the algorithm allowlist, the OIDC azp rule for a multi-valued
    audience, and the nonce. Nothing here re-implements a signature check.

    The `iss` claim is compared against the discovery document's own `issuer`
    string, not against the configured one. They are the same issuer — 
    fetch_provider_metadata() refuses a document that says otherwise — but
    Auth0 writes its issuer with a trailing slash and operators paste it both
    ways, and PyJWT compares issuers byte for byte. Taking the provider's own
    spelling means a correctly configured tenant is not rejected over a slash.
    """
    if not isinstance(id_token, str) or not id_token:
        return None, "the provider returned no id_token"

    algorithms = id_token_algorithms(metadata)
    if not algorithms:
        return None, "the provider advertises no acceptable ID token signing algorithm"

    try:
        signing_key = _jwks_client(metadata["jwks_uri"]).get_signing_key_from_jwt(id_token)
    except Exception as exc:
        return None, f"ID token signing key could not be resolved ({type(exc).__name__})"

    try:
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=algorithms,
            audience=client_id,
            issuer=metadata["issuer"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
                "require": ["iss", "aud", "exp", "iat", "sub"],
            },
        )
    except jwt.InvalidTokenError as exc:
        # Every PyJWT rejection — bad signature, wrong issuer, wrong audience,
        # expired, missing required claim — lands here as a plain denial.
        return None, f"ID token validation failed ({type(exc).__name__})"
    except Exception as exc:
        return None, f"ID token could not be validated ({type(exc).__name__})"

    audience = claims.get("aud")
    if isinstance(audience, (list, tuple)) and len(audience) > 1:
        # OIDC Core 3.1.3.7: with more than one audience, azp is required and
        # must be this client. PyJWT is satisfied as long as client_id appears
        # anywhere in aud, which is not enough.
        if claims.get("azp") != client_id:
            return None, "ID token has multiple audiences and azp is not this client"

    presented_nonce = claims.get("nonce")
    if not expected_nonce:
        return None, "no nonce was recorded for this login"
    if not isinstance(presented_nonce, str) or not presented_nonce:
        return None, "ID token carries no nonce"
    if not hmac.compare_digest(presented_nonce.encode("utf-8"),
                               expected_nonce.encode("utf-8")):
        return None, "ID token nonce does not match this login"

    return claims, None


def identity_from_claims(claims: dict):
    """(identity, None) for claims CIS can act on, else (None, reason).

    Identity comes from the verified token and from nowhere else — never from a
    query parameter, a header, a form field or a display name.
    """
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return None, "the provider returned no subject (sub) claim"

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip() or "@" not in email:
        return None, (
            "the provider returned no email claim — the Workbench authorizes "
            "by email address, so an identity without one cannot be placed"
        )

    if "email_verified" in claims:
        verified = claims["email_verified"]
        if isinstance(verified, str):
            verified = verified.strip().lower() == "true"
        if verified is not True:
            return None, "the provider reports this email address as unverified"

    name = claims.get("name")
    if not isinstance(name, str):
        name = ""

    return {
        "subject": subject.strip(),
        "email": email.strip(),
        "name": name.strip(),
        "issuer": claims.get("iss") or "",
    }, None


# ── Login transaction cookie ─────────────────────────────────────────────

def _set_tx_cookie(response, token: str):
    response.set_cookie(
        TX_COOKIE_NAME, token,
        max_age=TX_MAX_AGE_SECONDS,
        path=TX_COOKIE_PATH,
        httponly=True,
        secure=cookie_secure_flag(),
        samesite=TX_COOKIE_SAMESITE,
    )
    return response


def _clear_tx_cookie(response):
    """A login transaction is single-use: cleared on success and on every
    failure, so a captured state/nonce/verifier cannot be replayed."""
    response.set_cookie(
        TX_COOKIE_NAME, "",
        max_age=0, expires=0,
        path=TX_COOKIE_PATH,
        httponly=True,
        secure=cookie_secure_flag(),
        samesite=TX_COOKIE_SAMESITE,
    )
    return response


def _read_tx(secret: str):
    """The login transaction for this callback, or None."""
    payload = verify_payload(request.cookies.get(TX_COOKIE_NAME, ""), secret)
    if not payload:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp <= int(time.time()):
        return None
    for key in ("state", "nonce", "cv"):
        if not isinstance(payload.get(key), str) or not payload[key]:
            return None
    return payload


# ── Honest failures ──────────────────────────────────────────────────────

_ERROR_PAGE = """<!doctype html>
<meta charset="utf-8">
<title>Workbench sign-in failed</title>
<style>
 body{{font:16px/1.5 system-ui,sans-serif;margin:0;padding:3rem 1.5rem;
      background:#14161a;color:#e7e9ee}}
 main{{max-width:34rem;margin:0 auto}}
 h1{{font-size:1.25rem;margin:0 0 .75rem}}
 p{{margin:0 0 1rem;color:#b9bfcc}}
 code{{background:#20242c;padding:.15em .4em;border-radius:3px}}
 a{{color:#8ab4f8}}
</style>
<main>
 <h1>{title}</h1>
 <p>{detail}</p>
 <p>You are not signed in.</p>
 <p><a href="/">Back to the Workbench</a></p>
</main>
"""


def _failure(code: str, status: int, title: str, detail: str, clear_tx=True):
    """One exit for every authentication failure.

    The same refusal in two shapes — HTML for a browser that has just been
    redirected here by the provider, JSON for anything else — so neither a
    person nor a test has to guess what happened. It sets no session cookie,
    carries no token, and never returns 2xx.
    """
    wants_html = "text/html" in (request.headers.get("Accept") or "")
    if wants_html:
        # Escaped: `detail` can carry the provider's own error_description,
        # which is not this server's text and must never be rendered as markup.
        body = _ERROR_PAGE.format(title=html.escape(title),
                                  detail=html.escape(detail))
        response = make_response(body, status)
        response.headers["Content-Type"] = "text/html; charset=utf-8"
    else:
        response = make_response(jsonify({
            "authenticated": False,
            "error": title,
            "error_code": code,
            "detail": detail,
        }), status)
    if clear_tx:
        _clear_tx_cookie(response)
    return response


# ── Routes ───────────────────────────────────────────────────────────────

def _pkce_challenge(verifier: str) -> str:
    """S256 code challenge: base64url(sha256(verifier)), unpadded (RFC 7636)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


@workbench_oidc_bp.route(LOGIN_PATH, methods=["GET"])
def login():
    """Begin sign-in: redirect the browser to the provider's Universal Login.

    No `connection` parameter is sent. Forcing one would pin every user to a
    single method and hide the others — the point of Universal Login is that
    Auth0 decides what to offer (Continue with Google, email + password) from
    what the tenant has enabled for this application.
    """
    problems = configuration_problems()
    if problems:
        return _failure(
            "oidc_not_configured", NOT_CONFIGURED_STATUS,
            "Sign-in is not configured on this server",
            "Identity provider configuration is incomplete: "
            + "; ".join(problems)
            + ". Nothing is accessible until it is configured, and retrying "
              "will not change that.",
            clear_tx=False,
        )

    issuer = configured_issuer()
    metadata, meta_error = fetch_provider_metadata(issuer)
    if metadata is None:
        return _failure(
            "provider_unavailable", NOT_CONFIGURED_STATUS,
            "The identity provider could not be reached",
            f"CIS could not read the provider's configuration: {meta_error}.",
            clear_tx=False,
        )

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    # 43-128 characters of unreserved ASCII, per RFC 7636. token_urlsafe(64)
    # yields 86.
    verifier = secrets.token_urlsafe(64)
    challenge = _pkce_challenge(verifier)

    client = WebApplicationClient(configured_client_id())
    authorization_url = client.prepare_request_uri(
        metadata["authorization_endpoint"],
        redirect_uri=redirect_uri(),
        scope=OIDC_SCOPES,
        state=state,
        nonce=nonce,
        code_challenge=challenge,
        code_challenge_method="S256",
    )

    response = make_response(redirect(authorization_url, code=302))
    _set_tx_cookie(response, sign_payload({
        "v": 1,
        "state": state,
        "nonce": nonce,
        "cv": verifier,
        "exp": int(time.time()) + TX_MAX_AGE_SECONDS,
    }, configured_session_secret()))
    return response


@workbench_oidc_bp.route(CALLBACK_PATH, methods=["GET"])
def callback():
    """Finish sign-in: validate everything, then mint the CIS session.

    The order matters and is the order the card specifies — state, exchange,
    token validation, nonce, claims, allowlist, role, session, CSRF, redirect.
    Nothing is written and no cookie is set until every one of them has passed.
    """
    problems = configuration_problems()
    if problems:
        return _failure(
            "oidc_not_configured", NOT_CONFIGURED_STATUS,
            "Sign-in is not configured on this server",
            "Identity provider configuration is incomplete: " + "; ".join(problems) + ".",
        )

    secret = configured_session_secret()
    issuer = configured_issuer()
    client_id = configured_client_id()

    # The provider may report its own failure (the user cancelled, the client
    # is misconfigured). Reported honestly; never treated as a sign-in.
    provider_error = request.args.get("error")
    if provider_error:
        description = request.args.get("error_description") or ""
        return _failure(
            "provider_error", UNAUTHORIZED_STATUS,
            "The identity provider refused this sign-in",
            f"{provider_error}: {description}" if description else str(provider_error),
        )

    # 1. state — bound to the signed transaction cookie, not to server memory.
    transaction = _read_tx(secret)
    if transaction is None:
        return _failure(
            "invalid_state", UNAUTHORIZED_STATUS,
            "This sign-in could not be verified",
            "No valid login transaction was found for this callback. It may "
            "have expired, already been used, or not started here. Start "
            "again from the Workbench.",
        )
    presented_state = request.args.get("state") or ""
    if not hmac.compare_digest(presented_state.encode("utf-8"),
                               transaction["state"].encode("utf-8")):
        return _failure(
            "invalid_state", UNAUTHORIZED_STATUS,
            "This sign-in could not be verified",
            "The state value returned by the provider does not match the one "
            "this browser started with.",
        )

    code = request.args.get("code") or ""
    if not code:
        return _failure(
            "missing_code", UNAUTHORIZED_STATUS,
            "This sign-in could not be completed",
            "The provider returned no authorization code.",
        )

    metadata, meta_error = fetch_provider_metadata(issuer)
    if metadata is None:
        return _failure(
            "provider_unavailable", NOT_CONFIGURED_STATUS,
            "The identity provider could not be reached",
            f"CIS could not read the provider's configuration: {meta_error}.",
        )

    # 2. authorization code exchange — oauthlib builds and parses it.
    client = WebApplicationClient(client_id)
    body = client.prepare_request_body(
        code=code,
        redirect_uri=redirect_uri(),
        client_id=client_id,
        client_secret=configured_client_secret(),
        code_verifier=transaction["cv"],
        include_client_id=True,
    )
    try:
        token_response = _http_post(
            metadata["token_endpoint"], body,
            {"Content-Type": "application/x-www-form-urlencoded",
             "Accept": "application/json"},
        )
        token = client.parse_request_body_response(token_response.text)
    except Exception as exc:
        # Includes oauthlib's OAuth2Error subclasses (invalid_grant, a reused
        # or expired code, a client secret the provider rejects) and any
        # transport failure. The exception text can echo provider output, so
        # only its type is reported.
        return _failure(
            "code_exchange_failed", UNAUTHORIZED_STATUS,
            "This sign-in could not be completed",
            f"The authorization code could not be exchanged ({type(exc).__name__}).",
        )

    # 3-4. ID token: signature, issuer, audience, expiry, nonce.
    claims, token_error = validate_id_token(
        token.get("id_token"), metadata, client_id, transaction["nonce"])
    if claims is None:
        return _failure(
            "invalid_id_token", UNAUTHORIZED_STATUS,
            "This sign-in could not be verified",
            f"The identity token from the provider was not accepted: {token_error}.",
        )

    # 5-6. the provider-authenticated identity and the claims CIS requires.
    identity, identity_error = identity_from_claims(claims)
    if identity is None:
        return _failure(
            "incomplete_identity", UNAUTHORIZED_STATUS,
            "This sign-in could not be completed",
            f"{identity_error}.",
        )

    # 7-8. authorization: allowlist, then role — both server-side only.
    role = resolve_role(identity["email"])
    if role is None:
        return _failure(
            "not_authorized", FORBIDDEN_STATUS,
            "This account is not authorized for this Workbench",
            "You signed in successfully, but this address is not on this "
            "Workbench's authorized list. Signing in with the identity "
            "provider is not by itself access to CIS. Ask the owner to add "
            "your address.",
        )
    identity["role"] = role

    # 9-11. session + CSRF, then back to the UI. The provider's access and
    # refresh tokens go no further than this function's local `token`.
    response = make_response(redirect(POST_LOGIN_PATH, code=302))
    response, _payload = establish_session(response, identity, secret)
    _clear_tx_cookie(response)
    return response


@workbench_oidc_bp.route(SESSION_PATH, methods=["GET"])
def session_status():
    """Honest authentication status for the UI.

    Never asserts a session that is absent, expired, unverifiable or no longer
    authorized. Returns identity and role and nothing else — no ID token, no
    access token, no client secret, no session secret, no API key, and not the
    allowlist itself.
    """
    if not configured_session_secret():
        return jsonify({
            "authenticated": False,
            "oidc_configured": False,
            "error": "Sign-in is not configured on this server",
            "detail": (
                f"{SESSION_SECRET_ENV} is not set, so no Workbench session can "
                "be issued or validated."
            ),
        }), NOT_CONFIGURED_STATUS

    if not browser_auth_configured():
        return jsonify({
            "authenticated": False,
            "oidc_configured": False,
            "error": "Sign-in is not configured on this server",
            "detail": (
                f"{ALLOWED_EMAILS_ENV} is empty, so no one is authorized to "
                "hold a Workbench session. This is not a temporary outage."
            ),
        }), NOT_CONFIGURED_STATUS

    session = current_session()
    if session is None:
        body = {
            "authenticated": False,
            "oidc_configured": oidc_configured(),
            "login_url": LOGIN_PATH,
        }
        problems = configuration_problems()
        if problems:
            body["detail"] = "; ".join(problems)
        return jsonify(body), 200

    role = resolve_role(session.get("email"))
    if role is None:
        # The cookie is intact but the address behind it is no longer allowed.
        # Answered as 403, not as "signed out": the person did authenticate,
        # and telling them so is the difference between "sign in again" and
        # "ask for access".
        response = make_response(jsonify({
            "authenticated": False,
            "oidc_configured": oidc_configured(),
            "error": "This account is not authorized for this Workbench",
            "detail": "This address is no longer on the authorized list.",
            "login_url": LOGIN_PATH,
        }), FORBIDDEN_STATUS)
        return clear_session_cookie(response)

    body = {
        "authenticated": True,
        "oidc_configured": oidc_configured(),
        "identity": safe_identity(session, role),
        # The SAME token already sealed inside the signed cookie, handed back
        # so a reloaded tab can send mutations without signing in again. Not a
        # new grant.
        "csrf_token": session["csrf"],
        "csrf_header": CSRF_HEADER,
        "expires_at": session["exp"],
    }
    misconfigured = misconfigured_owner_emails()
    if misconfigured:
        # Surfaced, not silently tolerated: an owner address missing from the
        # allowlist is denied at login, and an operator staring at a 403 needs
        # to be told which list it is missing from.
        body["configuration_warning"] = (
            f"{len(misconfigured)} address(es) in {OWNER_EMAILS_ENV} are not in "
            f"{ALLOWED_EMAILS_ENV} and will be refused. Owners must appear in both."
        )
    return jsonify(body), 200



@workbench_oidc_bp.route(LOGOUT_PATH, methods=["POST"])
def logout():
    """End the CIS Workbench session on this client.

    What this DOES:
      * clears the CIS session cookie here;
      * clears any half-finished login transaction cookie;
      * leaves the UI signed out, with its in-memory CSRF token dropped.

    What this does NOT do, stated plainly rather than implied:
      * it does not end the user's Auth0 session, and it does not end their
        Google session. Returning to the Workbench and signing in again may
        therefore complete without another password prompt — that is the
        provider's session, not CIS's.
      * it does not revoke a session token already copied elsewhere; see
        workbench_session.py for what actually does.

    When the provider advertises RP-initiated logout, its URL is RETURNED for
    the UI to offer, not followed automatically: sending someone to a global
    sign-out they did not ask for would log them out of every other
    application using that provider.

    Deliberately requires no CSRF token and no valid session: a cross-site
    forced logout is a nuisance, not a breach, and refusing to log out an
    expired session would strand the UI.
    """
    body = {
        "authenticated": False,
        "provider_logout_url": None,
        "provider_logout_note": (
            "Your CIS Workbench session on this browser has been cleared. Your "
            "sign-in with the identity provider has not been ended."
        ),
    }

    issuer = configured_issuer()
    origin, _ = configured_public_origin()
    if issuer and origin and configured_client_id():
        metadata, _error = fetch_provider_metadata(issuer)
        end_session = (metadata or {}).get("end_session_endpoint")
        if end_session:
            separator = "&" if "?" in end_session else "?"
            body["provider_logout_url"] = end_session + separator + urlencode({
                "client_id": configured_client_id(),
                "post_logout_redirect_uri": f"{origin}/",
            })
            body["provider_logout_note"] = (
                "Your CIS Workbench session on this browser has been cleared. "
                "To also end your session with the identity provider, follow "
                "provider_logout_url. That URL must be listed in the "
                "provider's Allowed Logout URLs to work."
            )

    response = make_response(jsonify(body), 200)
    clear_session_cookie(response)
    _clear_tx_cookie(response)
    return response
