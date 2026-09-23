"""
workbench_auth.py — fail-closed authentication + authorization contract for the
Workbench-family APIs (workbench_app, card_factory_app, card_runner, and the
Braingate conversation-only activation surface).

Replaces the fail-OPEN pattern that all three modules previously carried
independently:

    def _check_auth():
        if not API_KEY:
            return None          # <-- unset key = auth skipped entirely
        ...

That pattern turned *missing server configuration* into *anonymous access*.
It was recorded as a blocking discovery twice — WB.1B-4 pre-activation checks
(2026-09-18) and again at WB.1 continuity revision 22 (2026-09-23), where it
was re-confirmed live: the running cis-pipeline container has no
CIS_PIPELINE_API_KEY at all, so registering any of those blueprints would have
exposed conversation, paid card generation and agent dispatch to anyone who
could reach port 5000.

The contract here has exactly three outcomes and no fourth:

    server credential configured + correct credential  -> allowed (None)
    a mechanism configured + missing/wrong credential  -> 401 denied
    NO mechanism configured                            -> 503 not ready

"Missing key" is never "allowed". There is deliberately no bypass flag, no
debug escape hatch and no "trusted local caller" exemption: a test that wants
an authenticated request must configure a mechanism and present a credential,
exactly as a real caller does.

Configuration is read from the environment on EVERY call rather than captured
into module constants at import time. Constants baked in at import made the
effective auth posture depend on import order (and let a test silently blank
them out), which is precisely how the fail-open behavior survived three
independent reviews. Reading per request also means a container that gains
configuration on restart does not need this module reloaded to honor it.

── WB.1 STANDARD-OIDC: where identity now comes from ────────────────────────

Until this card, a browser session was established by POSTing a single shared
password to CIS, and every browser that knew it was the same anonymous
"workbench-browser" subject. CIS no longer authenticates anyone's password.
Credential authentication is delegated to an external OpenID Connect provider
(Auth0 Universal Login: Continue with Google, or Auth0 email/password), and
this module's browser path now consumes a session minted from *verified OIDC
claims* by runtime/workbench_oidc.py.

Two things stay strictly separate and are both required:

    Authentication  — who is this person?   Answered by the OIDC provider.
                                            The `sub` claim is canonical.
    Authorization   — what may they do?     Answered HERE, from server-side
                                            configuration only, never from
                                            anything the browser sends.

CIS therefore holds no password, no password hash, no reset flow and no Google
OAuth stack of its own. There is no route in this codebase that validates a
user's login password — see runtime/tests/test_workbench_oidc.py, which asserts
that as a property of the registered surface rather than as a claim.
"""
import base64
import hmac
import hashlib
import json
import os
import secrets
import time

from flask import g, jsonify, request

API_KEY_ENV = "CIS_PIPELINE_API_KEY"

# ── Browser-session configuration ────────────────────────────────────────
# Deliberately SEPARATE from CIS_PIPELINE_API_KEY. The API key authenticates
# trusted non-browser callers and must never reach JavaScript.
SESSION_SECRET_ENV = "CIS_WORKBENCH_SESSION_SECRET"
SESSION_MAX_AGE_ENV = "CIS_WORKBENCH_SESSION_MAX_AGE_SECONDS"
COOKIE_INSECURE_ENV = "CIS_WORKBENCH_COOKIE_INSECURE"

# ── Authorization configuration ──────────────────────────────────────────
# The Workbench allowlist. Authentication by the provider is NOT authorization
# by CIS: Auth0 may be configured to let anyone sign up, and a person who has
# genuinely proven who they are still gets 403 here unless their address is on
# this list. There is no wildcard and no "allow everyone" default; an empty
# allowlist means nobody may hold a Workbench session.
ALLOWED_EMAILS_ENV = "CIS_WORKBENCH_ALLOWED_EMAILS"
OWNER_EMAILS_ENV = "CIS_WORKBENCH_OWNER_EMAILS"

ROLE_OWNER = "owner"
ROLE_COLLABORATOR = "collaborator"

SESSION_COOKIE_NAME = "cis_workbench_session"
# Scoped as narrowly as practical: every Workbench route lives under this
# prefix, so the cookie is never sent to /ui/, /api/relay/*, /dashboard/ or
# anything else this app serves.
SESSION_COOKIE_PATH = "/api/workbench"
CSRF_HEADER = "X-CIS-Workbench-CSRF"

# One working day. Finite by construction — there is no code path that mints a
# token without an exp, and no "remember me".
DEFAULT_SESSION_MAX_AGE_SECONDS = 8 * 60 * 60

# Browser sessions are a bearer credential carried automatically by the
# browser, so state-changing requests need CSRF proof. Bearer-API callers do
# not (they must set an Authorization header explicitly, which a cross-site
# form cannot do). OIDC `state` protects the login redirect; this protects
# application mutations. They are different controls and both exist.
CSRF_PROTECTED_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})

# Bumped from 1 when the payload stopped being an anonymous shared-password
# session and started carrying a verified individual identity. A v1 cookie
# minted by the old shared-password build does not verify against this build,
# so no pre-OIDC session survives the change.
SESSION_TOKEN_VERSION = 2

# Returned when the server itself is unconfigured. 503 (not 401) is the honest
# code: the caller did nothing wrong and no credential they could present would
# help — the service is not ready to authenticate anyone. It is still a denial.
NOT_CONFIGURED_STATUS = 503
UNAUTHORIZED_STATUS = 401
FORBIDDEN_STATUS = 403


def configured_api_key() -> str:
    """The server's currently-configured key, or "" when unset/blank.

    A key consisting only of whitespace is treated as unset rather than as a
    real (and trivially guessable) credential.
    """
    return (os.environ.get(API_KEY_ENV) or "").strip()


def is_configured() -> bool:
    """True when ANY authentication mechanism is usable — the API key, browser
    sessions, or both. False means every request is denied 503."""
    return bool(configured_api_key()) or browser_auth_configured()


def presented_credential() -> str:
    """The Bearer token on this request, or "" when absent/malformed."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return ""
    return header[7:].strip()


# ── Browser session: configuration ───────────────────────────────────────

def configured_session_secret() -> str:
    """The HMAC key used to sign session cookies, or "" when unset/blank.

    Never hard-coded, never generated on the fly. A process-generated secret
    would silently invalidate every session on restart and would differ between
    workers, so an unset secret disables browser sessions rather than inventing
    one.
    """
    return (os.environ.get(SESSION_SECRET_ENV) or "").strip()


def session_max_age_seconds() -> int:
    """Configured session lifetime. Falls back to the documented default on a
    missing, unparseable or non-positive value — never to 'unlimited'."""
    raw = (os.environ.get(SESSION_MAX_AGE_ENV) or "").strip()
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_SESSION_MAX_AGE_SECONDS
    return value if value > 0 else DEFAULT_SESSION_MAX_AGE_SECONDS


def cookie_secure_flag() -> bool:
    """True unless an operator has EXPLICITLY opted out for local plain-HTTP
    testing.

    The decision never looks at request.is_secure: deciding per-request would
    silently ship an insecure cookie the moment a deployment terminated TLS
    somewhere unexpected. Opting out takes a deliberate environment variable
    set to one of a small set of literal values, and anything else — including
    a typo — keeps the secure posture.

    The Cloudflare Quick Tunnel development path is HTTPS from the browser's
    point of view, so it must NOT set the opt-out. It exists for localhost-only
    automated tests driving Flask's test client over plain HTTP.
    """
    raw = (os.environ.get(COOKIE_INSECURE_ENV) or "").strip().lower()
    return raw not in ("1", "true", "yes", "on")


def browser_auth_configured() -> bool:
    """Browser sessions need a secret to sign with and at least one address
    authorized to hold one. Half-configured is not configured.

    Note what is deliberately NOT required here: the OIDC provider settings.
    A server with a signing secret and an allowlist can still *validate* an
    already-issued session even if the provider configuration is momentarily
    absent — but it cannot mint a new one, because
    runtime/workbench_oidc.py checks its own configuration and answers 503.
    """
    return bool(configured_session_secret()) and bool(allowed_emails())


# ── Authorization: allowlist and roles ───────────────────────────────────

def normalize_email(value) -> str:
    """Case-folded, whitespace-stripped address, or "" when unusable.

    Deliberately conservative: it lowercases and trims, and does nothing
    clever. It does not strip dots or +tags — two addresses that an identity
    provider treats as different people must not be collapsed into one here.
    A value containing a wildcard, a comma, or whitespace inside it is
    rejected outright ("" ), so a configuration line like `*@example.com`
    can never match anybody.
    """
    if not isinstance(value, str):
        return ""
    text = value.strip().lower()
    if not text or "@" not in text:
        return ""
    if "*" in text or "," in text or any(c.isspace() for c in text):
        return ""
    return text


def _parse_email_list(raw: str) -> frozenset:
    """Comma-separated addresses -> a normalized set. Unusable entries are
    dropped rather than approximated."""
    out = set()
    for piece in (raw or "").split(","):
        normalized = normalize_email(piece)
        if normalized:
            out.add(normalized)
    return frozenset(out)


def allowed_emails() -> frozenset:
    """Every address permitted to hold a Workbench session. Empty means nobody."""
    return _parse_email_list(os.environ.get(ALLOWED_EMAILS_ENV) or "")


def owner_emails() -> frozenset:
    """Addresses that get the `owner` role — IF they are also allowed."""
    return _parse_email_list(os.environ.get(OWNER_EMAILS_ENV) or "")


def resolve_role(email):
    """The CIS role for a provider-verified address, or None when not allowed.

    Computed here, on the server, from configuration alone. The browser never
    supplies a role, no role is inferred from a display name, and no role is
    trusted from the session cookie without this check running again — so
    removing someone from the allowlist takes effect on their very next
    request rather than whenever their cookie happens to expire.

    `owner` requires membership in BOTH lists. An address in
    CIS_WORKBENCH_OWNER_EMAILS but missing from CIS_WORKBENCH_ALLOWED_EMAILS is
    a misconfiguration and is denied, not silently promoted — the allowlist is
    the single gate, and an owner list that could widen it would be a second
    one. See misconfigured_owner_emails().
    """
    normalized = normalize_email(email)
    if not normalized:
        return None
    if normalized not in allowed_emails():
        return None
    return ROLE_OWNER if normalized in owner_emails() else ROLE_COLLABORATOR


def misconfigured_owner_emails() -> frozenset:
    """Owner addresses that are not in the allowlist, i.e. that will be denied.

    Reported by the session/status surface as a configuration diagnostic so an
    operator sees the mistake instead of silently being locked out. It names
    only addresses the operator themselves configured.
    """
    return frozenset(owner_emails() - allowed_emails())


# ── Browser session: token ───────────────────────────────────────────────
# A signed, stateless, server-validated token. No database table, no server-side
# session store — per the card's schema rule, browser auth must not touch the
# project-state authority model.
#
# Format:  base64url(payload_json) "." base64url(hmac_sha256(secret, payload_b64))
#
# The payload carries the verified identity, the server-computed role, the
# issue/expiry times and the session's CSRF token. It is signed, not encrypted,
# so it is readable by anyone holding the cookie — which is why the session
# secret, the OIDC client secret, the API key and the provider's own
# ID/access/refresh tokens are NEVER placed in it. What it does contain is the
# holder's own name and address, which they already know.


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload_b64: str, secret: str) -> str:
    return _b64e(hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"),
                          hashlib.sha256).digest())


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def sign_payload(payload: dict, secret: str) -> str:
    """base64url(json) "." base64url(hmac_sha256) — the one signing primitive.

    Shared by the session cookie and by workbench_oidc.py's short-lived login
    transaction cookie, so there is a single place where a signing mistake
    could live rather than two that must be kept in step. Signed, not
    encrypted: never put a secret in `payload`.
    """
    payload_b64 = _b64e(json.dumps(payload, separators=(",", ":"),
                                   sort_keys=True).encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64, secret)}"


def verify_payload(token: str, secret: str):
    """The signed dict back, or None on any failure whatsoever.

    Checks integrity only — no expiry, no claim rules. Callers add whatever
    their own payload requires. Never raises: it parses attacker-controlled
    bytes, so every surprise is a denial rather than a 500.
    """
    if not token or not secret:
        return None
    try:
        payload_b64, _, sig = token.partition(".")
        if not payload_b64 or not sig:
            return None
        if not hmac.compare_digest(sig, _sign(payload_b64, secret)):
            return None
        payload = json.loads(_b64d(payload_b64))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def issue_session_token(secret: str, max_age: int, subject: str, email: str,
                        role: str, name: str = "", issuer: str = "",
                        csrf: str = None, now: float = None) -> tuple:
    """Mints a signed session token for a provider-verified identity.

    Returns (token, payload). Never called without a secret — callers check
    browser_auth_configured() first. The CSRF token is random per session, not
    derived from any secret.

    `subject` is the OIDC `sub` claim: the canonical, provider-scoped user
    identifier. `issuer` records WHICH provider vouched for it, so a subject
    from one issuer can never be confused with the same string from another.
    """
    issued = int(now if now is not None else time.time())
    payload = {
        "v": SESSION_TOKEN_VERSION,
        "sub": subject,
        "iss": issuer,
        "email": email,
        "name": name or "",
        "role": role,
        "iat": issued,
        "exp": issued + max_age,
        "csrf": csrf or new_csrf_token(),
    }
    return sign_payload(payload, secret), payload


def verify_session_token(token: str, secret: str, now: float = None):
    """Returns the payload dict for a valid token, else None.

    Every failure mode — absent, malformed, bad base64, bad JSON, wrong
    signature, wrong version, expired, missing claims — returns None. None of
    them raises, because a malformed credential must be a denial, never a 500.

    This verifies the token's integrity and lifetime only. Whether the identity
    inside it is STILL authorized is a separate question, asked on every
    request by check_auth() via resolve_role().
    """
    payload = verify_payload(token, secret)
    if payload is None:
        return None
    try:
        if payload.get("v") != SESSION_TOKEN_VERSION:
            return None
        exp = payload.get("exp")
        csrf = payload.get("csrf")
        subject = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        if not isinstance(exp, int) or not isinstance(csrf, str) or not csrf:
            return None
        # An identity-bearing session with no identity in it is not a session.
        if not isinstance(subject, str) or not subject:
            return None
        if not isinstance(email, str) or not email:
            return None
        if role not in (ROLE_OWNER, ROLE_COLLABORATOR):
            return None
        if exp <= int(now if now is not None else time.time()):
            return None
        return payload
    except Exception:
        # Deliberately broad: this parses attacker-controlled bytes. Any
        # surprise here is a denial.
        return None


def current_session():
    """The verified session payload for this request, or None.

    Integrity + lifetime only; authorization is re-derived by the caller.
    """
    secret = configured_session_secret()
    if not secret:
        return None
    return verify_session_token(request.cookies.get(SESSION_COOKIE_NAME, ""), secret)


def authorized_session():
    """The verified session for this request whose identity is STILL allowed.

    Returns (payload, role) on success, or (None, None). The role returned is
    the one configuration says now — not the one sealed into the cookie when it
    was minted — so a demotion from owner to collaborator, or a removal from
    the allowlist entirely, takes effect immediately.
    """
    session = current_session()
    if session is None:
        return None, None
    role = resolve_role(session.get("email"))
    if role is None:
        return None, None
    return session, role


def csrf_ok(session_payload) -> bool:
    """Constant-time check of the CSRF header against this session's own token.

    The token lives inside the signed cookie, so an attacker who can make a
    cross-site request still cannot read it (HttpOnly) nor forge it (signed).
    """
    presented = (request.headers.get(CSRF_HEADER) or "").strip()
    expected = (session_payload or {}).get("csrf") or ""
    if not presented or not expected:
        return False
    return hmac.compare_digest(presented.encode("utf-8"), expected.encode("utf-8"))


def check_auth():
    """Returns None when the request may proceed, else a Flask (body, status).

    Callers keep the existing shape used throughout the Workbench family:

        auth_err = check_auth()
        if auth_err:
            return auth_err

    Two independent paths authorize a request, and the combined contract is:

        valid Bearer (CIS_PIPELINE_API_KEY)          -> allowed
        valid browser session cookie whose identity
          is still on the allowlist                  -> allowed
          ... but a state-changing method additionally needs a valid CSRF
              header bound to that session, or it is 403
        a mechanism is configured, credential absent
          or wrong                                   -> 401
        NEITHER mechanism configured                 -> 503 service not ready

    "API key missing = access allowed" is not, and must never become, a rule
    here. An unconfigured server denies.

    Being authenticated is NOT being authorized for everything: this function
    answers "may this caller use the currently registered surface", and the
    registered surface at this stage is Braingate conversation only. An owner
    session reaching a Card Factory or Card Runner route gets 404 because
    those blueprints are not registered — authentication never widens a stage
    boundary, and runtime/tests/test_workbench_oidc.py proves it for both roles.

    On success `g.cis_auth_method` records which path authorized ("api_key" or
    "browser_session"); for the browser path `g.cis_identity` carries the safe
    identity dict and `g.cis_role` the server-computed role.
    """
    api_configured = bool(configured_api_key())
    browser_configured = browser_auth_configured()

    if not api_configured and not browser_configured:
        return jsonify({
            "error": "Service not ready",
            "detail": (
                "No authentication mechanism is configured: "
                f"{API_KEY_ENV} is unset, and browser sessions need both "
                f"{SESSION_SECRET_ENV} and a non-empty {ALLOWED_EMAILS_ENV}. "
                "Requests are denied until one is configured — an unconfigured "
                "server is never treated as anonymous access."
            ),
        }), NOT_CONFIGURED_STATUS

    # ── Path A: trusted non-browser caller ──────────────────────────────
    if api_configured:
        key = configured_api_key()
        presented = presented_credential()
        # Constant-time comparison. Encoded to bytes first: hmac.compare_digest
        # raises TypeError on a str containing non-ASCII, and a non-ASCII
        # credential must be a plain denial, never a 500.
        if presented and hmac.compare_digest(
            presented.encode("utf-8"), key.encode("utf-8")
        ):
            g.cis_auth_method = "api_key"
            # No browser CSRF requirement: an Authorization header is not
            # something a cross-site form or image can cause a browser to send.
            return None

    # ── Path B: browser session established from verified OIDC identity ──
    if browser_configured:
        session, role = authorized_session()
        if session is not None:
            if request.method in CSRF_PROTECTED_METHODS and not csrf_ok(session):
                # Returned BEFORE the route body runs, so no mutation can have
                # happened by the time CSRF is judged.
                return jsonify({
                    "error": "CSRF check failed",
                    "detail": (
                        f"A browser-session request using {request.method} must "
                        f"present this session's CSRF token in the {CSRF_HEADER} "
                        "header. Fetch it from GET /api/workbench/auth/session."
                    ),
                }), FORBIDDEN_STATUS
            g.cis_auth_method = "browser_session"
            g.cis_role = role
            g.cis_identity = {
                "subject": session.get("sub"),
                "email": session.get("email"),
                "name": session.get("name") or "",
                "role": role,
            }
            return None

    return jsonify({
        "error": "Unauthorized",
        "detail": "Invalid or missing credential (API key or browser session)",
    }), UNAUTHORIZED_STATUS
