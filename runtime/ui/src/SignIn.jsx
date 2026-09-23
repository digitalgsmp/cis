import { beginSignIn } from "./api";

/**
 * The Workbench sign-in gate.
 *
 * This component has no password field, and that is the design rather than an
 * omission. Credentials are entered at Auth0 Universal Login, on Auth0's own
 * origin, which is where "Continue with Google" and email/password both live.
 * The button below is a plain navigation to the server's OIDC login route; no
 * credential is ever typed into, held by, or sent from this bundle, so there
 * is nothing here for browser storage or a stray log line to leak.
 *
 * It renders four honest states, because "you are not signed in" and "you are
 * signed in but not allowed here" are different problems with different fixes:
 *
 *   anonymous     — not signed in; offer to start.
 *   unauthorized  — the provider verified you, CIS's allowlist did not. 403.
 *   unavailable   — the server has no sign-in configured. 503. Retrying is
 *                   pointless and the page says so.
 *   signedOut     — a completed sign-out, optionally offering the provider's
 *                   own sign-out as a separate, explicit step.
 */
export default function SignIn({ state = "anonymous", detail, providerLogoutUrl }) {
  if (state === "unavailable") {
    return (
      <div className="login-pane">
        <div className="login-card">
          <h1>Workbench</h1>
          <div className="banner-error">
            Sign-in is not configured on this server.
          </div>
          {detail && <p className="muted login-detail">{detail}</p>}
          <p className="muted">
            Nothing is accessible until it is configured. This is not a
            temporary outage and retrying will not change it.
          </p>
        </div>
      </div>
    );
  }

  if (state === "unauthorized") {
    return (
      <div className="login-pane">
        <div className="login-card">
          <h1>Workbench</h1>
          <div className="banner-error">
            This account is not authorized for this Workbench.
          </div>
          <p className="muted login-detail">
            {detail ||
              "You signed in successfully, but this address is not on this Workbench's authorized list."}
          </p>
          <p className="muted">
            Signing in with the identity provider is not by itself access to
            CIS. Ask the owner to add your address.
          </p>
          <button className="send-btn" type="button" onClick={beginSignIn}>
            Try a different account
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-pane">
      <div className="login-card">
        <h1>Workbench</h1>
        {state === "signedOut" ? (
          <p className="muted">You are signed out of the Workbench.</p>
        ) : (
          <p className="muted">Sign in to continue.</p>
        )}
        <button className="send-btn" type="button" onClick={beginSignIn}>
          Continue to Sign In
        </button>
        <p className="muted login-detail">
          You will be taken to the identity provider to continue with Google or
          with an email address and password. Your password is never sent to
          CIS.
        </p>
        {state === "signedOut" && providerLogoutUrl && (
          // Offered, never followed automatically: a global sign-out would end
          // the user's session with every other application using the same
          // provider, which is not what "sign out of the Workbench" asked for.
          <p className="muted login-detail">
            <a href={providerLogoutUrl}>
              Also sign out of the identity provider
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
