// CIS Control Panel — API client

const BASE = '/api/relay';

async function _post(path, body) {
  const resp = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return resp.json();
}

async function _get(path) {
  const resp = await fetch(`${BASE}${path}`);
  return resp.json();
}

export const api = {
  // Brain chat
  brainChat: (message, sessionId) =>
    _post('/brain/chat', { message, session_id: sessionId || '' }),

  brainHistory: (sessionId) =>
    _get(`/brain/history/${sessionId}`),

  brainStart: (sessionId) =>
    _post('/brain/start', { session_id: sessionId }),

  // Pipeline
  startPipeline: (intent) =>
    _post('/start', { intent }),

  getStatus: (runId) =>
    _get(`/${runId}`),

  getFeed: (runId) =>
    _get(`/${runId}/feed`),

  getRuns: () =>
    _get('/runs'),

  // Interjection (backchannel)
  interject: (runId, message) =>
    _post(`/${runId}/interject`, { message }),

  getInterjections: (runId) =>
    _get(`/${runId}/interjections`),

  // Gate approval
  approve: (runId, decision, rationale) =>
    _post(`/${runId}/gate`, { decision, rationale }),

  // Answer human question
  answer: (runId, answer) =>
    _post(`/${runId}/answer`, { answer }),
};
