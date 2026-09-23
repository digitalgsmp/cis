const WORKBENCH_BASE = "/api/workbench";
const CARDRUNNER_BASE = "/api/cardrunner";
const CARDFACTORY_BASE = "/api/cardfactory";

// The OIDC authentication lifecycle. Sign-in is a full-page redirect to the
// identity provider, NOT a fetch: the browser has to actually visit Auth0
// Universal Login, and the callback has to arrive as a navigation so the
// server can set the session cookie on it.
export const AUTH_LOGIN_URL = `${WORKBENCH_BASE}/auth/login`;

const CSRF_HEADER = "X-CIS-Workbench-CSRF";
const MUTATING_METHODS = new Set(["POST", "PATCH", "PUT", "DELETE"]);

// This session's CSRF token, held in module memory ONLY.
//
// Deliberately not localStorage/sessionStorage: it is a session-bound secret,
// and browser storage is readable by any script on the origin and outlives the
// tab. Losing it on reload costs nothing — the HttpOnly session cookie
// survives, so GET /session hands the same token back (see refreshSession).
//
// The server API key never appears here, or anywhere else in this bundle. The
// browser has no access to it by design.
let csrfToken = null;

export function getCsrfToken() {
  return csrfToken;
}

export function setCsrfToken(token) {
  csrfToken = token || null;
}

async function request(base, path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };

  // Attached automatically so no individual call site can forget it. Harmless
  // on a Bearer-authenticated deployment: the server only requires CSRF for
  // browser-session-authenticated mutations and ignores the header otherwise.
  if (MUTATING_METHODS.has(method) && csrfToken) {
    headers[CSRF_HEADER] = csrfToken;
  }

  let resp;
  try {
    resp = await fetch(`${base}${path}`, {
      // Same-origin only: the session cookie goes to this server and nowhere
      // else, and no cross-origin request ever carries it.
      credentials: "same-origin",
      ...options,
      headers,
    });
  } catch (e) {
    // Network failure (offline, gateway down before it even reached Flask).
    // Never silently swallowed and never presented as a successful reply.
    return { ok: false, networkError: true, error: `Network error: ${e.message}` };
  }
  let body = null;
  try {
    body = await resp.json();
  } catch (e) {
    return { ok: false, error: `Bad response from server (status ${resp.status})` };
  }
  if (!resp.ok) {
    return {
      ok: false,
      error: body?.error || `Request failed (status ${resp.status})`,
      status: resp.status,
      data: body,
      // Lets callers distinguish "sign in again" (401), "you signed in but
      // this account is not on this Workbench's list" (403 from the session
      // route) and "the server has no sign-in configured" (503) from an
      // ordinary request failure. A 403 on an application route is the CSRF
      // check, which is why `forbidden` is reported separately rather than
      // being collapsed into either of the others.
      unauthenticated: resp.status === 401,
      forbidden: resp.status === 403,
      authUnavailable: resp.status === 503,
    };
  }
  return { ok: true, data: body, status: resp.status };
}

// ── Workbench: OIDC session ─────────────────────────────────────────────
//
// There is no login() any more, and that absence is the point. This bundle
// never sees, holds, transmits or stores anyone's password: the password is
// typed at Auth0 Universal Login, on Auth0's origin, and CIS is told only the
// verified result. Nothing here can be given a credential to mishandle.

/** Start sign-in by handing the browser to the identity provider. */
export function beginSignIn() {
  window.location.assign(AUTH_LOGIN_URL);
}

export async function refreshSession() {
  const result = await request(WORKBENCH_BASE, "/auth/session");
  if (result.ok && result.data?.authenticated) {
    setCsrfToken(result.data.csrf_token);
  } else {
    setCsrfToken(null);
  }
  return result;
}

export async function logout() {
  const result = await request(WORKBENCH_BASE, "/auth/logout", { method: "POST" });
  // Cleared locally regardless of the server's answer — a token we can no
  // longer use must not linger in memory. Note that this ends the CIS session
  // only; the server reports separately, in provider_logout_url, whether the
  // identity provider offers its own sign-out.
  setCsrfToken(null);
  return result;
}

const workbenchRequest = (path, options) => request(WORKBENCH_BASE, path, options);
const cardRunnerRequest = (path, options) => request(CARDRUNNER_BASE, path, options);
const cardFactoryRequest = (path, options) => request(CARDFACTORY_BASE, path, options);

// ── Workbench: projects & messages ──────────────────────────────────────

export function listProjects() {
  return workbenchRequest("/projects");
}

export function createProject(name) {
  return workbenchRequest("/projects", { method: "POST", body: JSON.stringify({ name }) });
}

export function getProject(projectId) {
  return workbenchRequest(`/projects/${projectId}`);
}

export function updateDirectionNote(projectId, directionNote) {
  return workbenchRequest(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify({ direction_note: directionNote }),
  });
}

export function listMessages(projectId) {
  return workbenchRequest(`/projects/${projectId}/messages`);
}

// mode: 'chat' | 'draft_proposal' | 'revise_proposal'. proposalId required
// only for 'revise_proposal'. This is the single call behind every
// conversational turn, including a correction to an existing proposal — the
// model is never called a second time for the same request_id.
export function sendMessage(projectId, message, requestId, { mode = "chat", proposalId = null } = {}) {
  const body = { message, request_id: requestId, mode };
  if (proposalId != null) body.proposal_id = proposalId;
  return workbenchRequest(`/projects/${projectId}/messages`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ── Workbench: action proposals ─────────────────────────────────────────

export function listProposals(projectId) {
  return workbenchRequest(`/projects/${projectId}/proposals`);
}

export function getProposal(proposalId) {
  return workbenchRequest(`/proposals/${proposalId}`);
}

export function confirmDirection(proposalId, requestId) {
  return workbenchRequest(`/proposals/${proposalId}/confirm-direction`, {
    method: "POST",
    body: JSON.stringify({ request_id: requestId }),
  });
}

// payload carries the exact fields card_runner.dispatch() itself requires
// (see runtime/card_runner.py `dispatch()`): authorized_by, target,
// expected_card_fingerprint, mode, review_of_run_id, model,
// wall_clock_timeout_seconds, max_turns, max_turns_ack_observation_only,
// budget_usd, accept_time_only_control, permitted_files, permitted_commands.
export function approveProposal(proposalId, requestId, payload) {
  return workbenchRequest(`/proposals/${proposalId}/approve`, {
    method: "POST",
    body: JSON.stringify({ request_id: requestId, ...payload }),
  });
}

// ── Card runner: dispatched runs ────────────────────────────────────────

export function getRunStatus(runId) {
  return cardRunnerRequest(`/runs/${runId}`);
}

export function stopRun(runId) {
  return cardRunnerRequest(`/runs/${runId}/stop`, { method: "POST" });
}

export function listRuns(project) {
  const qs = project ? `?project=${encodeURIComponent(project)}` : "";
  return cardRunnerRequest(`/runs${qs}`);
}

export function dispatchRun(payload) {
  return cardRunnerRequest("/dispatch", { method: "POST", body: JSON.stringify(payload) });
}

// name must be one of card_runner.py's fixed ARTIFACT_NAMES
// ("evidence.md", "completion.json", "review.md") — the route itself
// rejects anything else with a 400, never an arbitrary path.
export function getRunArtifact(runId, name) {
  return cardRunnerRequest(`/runs/${runId}/artifact/${encodeURIComponent(name)}`);
}

// ── Card Factory: direct asks & cards (Card Factory view) ──────────────

export function submitAsk(project, askText, doneWhenText) {
  return cardFactoryRequest("/asks", {
    method: "POST",
    body: JSON.stringify({ project, ask_text: askText, done_when_text: doneWhenText }),
  });
}

export function getAsk(askId) {
  return cardFactoryRequest(`/asks/${askId}`);
}

export function editAsk(askId, askText, doneWhenText) {
  return cardFactoryRequest(`/asks/${askId}`, {
    method: "PATCH",
    body: JSON.stringify({ ask_text: askText, done_when_text: doneWhenText }),
  });
}

export function generateCard(askId, requestId) {
  return cardFactoryRequest(`/asks/${askId}/generate`, {
    method: "POST",
    body: JSON.stringify({ request_id: requestId }),
  });
}

export function listCards(askId) {
  const qs = askId ? `?ask_id=${encodeURIComponent(askId)}` : "";
  return cardFactoryRequest(`/cards${qs}`);
}

export function getCard(cardId) {
  return cardFactoryRequest(`/cards/${cardId}`);
}

export function editCard(cardId, cardText) {
  return cardFactoryRequest(`/cards/${cardId}`, {
    method: "PATCH",
    body: JSON.stringify({ card_text: cardText }),
  });
}

export function regateCard(cardId) {
  return cardFactoryRequest(`/cards/${cardId}/regate`, { method: "POST" });
}

// ── System Context / Recovery (Card 03) ─────────────────────────────────
// Thin GET wrappers over runtime/api/system_context.py, itself a thin
// wrapper over tools/state/canonical_state.py + recovery_packet.py (Cards
// 01-02). Read-only — neither call can mutate anything.

export function getSystemContext() {
  return workbenchRequest("/system-context");
}

// issue: one of recovery_packet.py's ISSUE_AREAS, or omitted for the full
// packet. An unrecognized issue is rejected by the server with a 400.
export function getRecoveryPacket(issue) {
  const qs = issue ? `?issue=${encodeURIComponent(issue)}` : "";
  return workbenchRequest(`/system-context/recovery-packet${qs}`);
}
