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

  // System dashboard
  getSystemHealth: () =>
    _get('/system/health'),

  getSecurityAudit: () =>
    _get('/system/security'),

  getContainerLogs: (name) =>
    _get(`/system/logs/${name}`),

  // Project overview
  getProjectOverview: (projectId) =>
    _get(`/project/${projectId}/overview`),

  getProjectBuildPlan: (projectId) =>
    _get(`/project/${projectId}/build-plan`),

  // Projects
  getProjects: () =>
    _get('/projects').then(r => { throw new Error('use /api/projects instead') }).catch(() => {
      return fetch('/api/projects').then(r => r.json())
    }),
};
