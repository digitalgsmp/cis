"""
workbench_session.py — the CIS browser-session layer that sits UNDERNEATH OIDC.

WB.1 continuity revision 26 first gave the Workbench UI a way to authenticate:
a shared password POSTed to CIS, exchanged for a signed HttpOnly session
cookie. The cookie mechanics were sound; the identity model was not. One shared
password cannot say *which individual* signed in, CIS had no business holding
anyone's password, and the password endpoint itself became revision 28 (no
login throttling).

WB.1 STANDARD-OIDC keeps the reviewed session mechanics and replaces only the
part that established identity. This module is what survived:

    HttpOnly cookie            kept
    Secure-by-default posture  kept
    SameSite=Strict            kept
    finite session lifetime    kept
    per-session CSRF token     kept
    stateless signed token     kept  (still no table, still no migration)
    shared-password login      GONE

There is deliberately no route in this file any more. It exports no blueprint
and registering it grants nothing, because there is nothing left to register:
the only way to obtain a session is now runtime/workbench_oidc.py's callback,
after an OpenID Connect provider has verified a real person and this server has
checked that person against its own allowlist. Two competing browser-login
systems is exactly what the card forbids, so CIS keeps one — and it is not the
one that handles passwords.

Session storage: none. The token is signed and stateless (see
workbench_auth.issue_session_token), so browser auth adds no table and no
migration — the live activation requirement stays 0035 + 0038, and the
project-state authority model is untouched.

Revocation, stated honestly, because logout is easy to overclaim:

  * logout clears the cookie on the client that calls it;
  * removing an address from CIS_WORKBENCH_ALLOWED_EMAILS denies its sessions
    on their very next request (workbench_auth.authorized_session re-derives
    authorization every time, it does not trust the cookie's sealed role);
  * a token already copied elsewhere by someone still on the allowlist stays
    valid until its own exp — there is no server-side revocation list;
  * to end every outstanding session at once, rotate
    CIS_WORKBENCH_SESSION_SECRET and restart: every previously-issued
    signature stops verifying;
  * none of this ends the user's session at Auth0 or at Google. That is a
    separate provider-side logout, offered as an explicit URL by
    workbench_oidc.py rather than silently assumed.
"""
from workbench_auth import (
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_PATH,
    cookie_secure_flag,
    issue_session_token,
    session_max_age_seconds,
)

# Strict is safe for the session cookie because every request that carries it
# originates from the Workbench UI on this same origin. The OIDC round-trip
# does NOT rely on it: the login transaction uses its own short-lived Lax
# cookie (workbench_oidc.py), precisely so the long-lived session cookie never
# has to be loosened to survive a cross-site redirect back from the provider.
SESSION_COOKIE_SAMESITE = "Strict"


def set_session_cookie(response, token: str, max_age: int):
    """Attach a freshly minted session token to a response."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=max_age,           # finite by construction
        path=SESSION_COOKIE_PATH,  # narrow: Workbench API routes only
        httponly=True,             # JS can never read it
        secure=cookie_secure_flag(),
        samesite=SESSION_COOKIE_SAMESITE,
    )
    return response


def clear_session_cookie(response):
    """Expire the session cookie on this client.

    Cleared with the SAME name, path and flags it was set with — a clear that
    differs in any of them silently leaves the original cookie in place.
    """
    response.set_cookie(
        SESSION_COOKIE_NAME,
        "",
        max_age=0,
        expires=0,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        secure=cookie_secure_flag(),
        samesite=SESSION_COOKIE_SAMESITE,
    )
    return response


def establish_session(response, identity: dict, secret: str):
    """Mint a CIS session for an already-verified identity and set the cookie.

    `identity` must be the output of workbench_oidc's claim validation: a dict
    with `subject`, `email`, `role`, and optionally `name` and `issuer`. This
    function performs NO authentication and NO authorization of its own — it is
    the layer beneath both, and calling it with unverified claims would be the
    bug. Its callers (one, at present: the OIDC callback) are responsible for
    having validated the ID token and checked the allowlist first.

    Returns (response, payload). The payload is what was sealed into the
    cookie; the provider's ID token, access token and refresh token are not in
    it and are not stored anywhere else either.
    """
    max_age = session_max_age_seconds()
    token, payload = issue_session_token(
        secret,
        max_age,
        subject=identity["subject"],
        email=identity["email"],
        role=identity["role"],
        name=identity.get("name") or "",
        issuer=identity.get("issuer") or "",
    )
    return set_session_cookie(response, token, max_age), payload


def safe_identity(session_payload: dict, role: str) -> dict:
    """The identity fields that may be shown to the browser that owns them.

    Exactly four fields, enumerated rather than filtered: adding a claim to the
    session payload must not silently publish it. No ID token, no access token,
    no refresh token, no client secret, no session secret, no API key — none of
    which are in the payload to begin with.

    `role` is passed in by the caller from a fresh workbench_auth.resolve_role()
    rather than read from the payload, so what the UI displays is what the
    server currently enforces.
    """
    return {
        "subject": session_payload.get("sub"),
        "email": session_payload.get("email"),
        "name": session_payload.get("name") or "",
        "role": role,
    }
