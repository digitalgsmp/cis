const WORKBENCH_BASE = "/api/workbench";
const CARDRUNNER_BASE = "/api/cardrunner";
const CARDFACTORY_BASE = "/api/cardfactory";

async function request(base, path, options = {}) {
  let resp;
  try {
    resp = await fetch(`${base}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
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
    return { ok: false, error: body?.error || `Request failed (status ${resp.status})`, status: resp.status, data: body };
  }
  return { ok: true, data: body, status: resp.status };
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
