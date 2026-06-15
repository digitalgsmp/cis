// api.js — CIS API client
const BASE = '/api/app'
const INGEST = '/api/ingest'
const LMS = '/api/lms'

async function request(method, path, body = null, extraHeaders = {}) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  }
  if (body) opts.body = JSON.stringify(body)
  const r = await fetch(BASE + path, opts)
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`)
  return data
}

async function ingestRequest(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
  if (body) opts.body = JSON.stringify(body)
  const r = await fetch(INGEST + path, opts)
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`)
  return data
}

async function lmsRequest(method, path, body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
  if (body) opts.body = JSON.stringify(body)
  const r = await fetch(LMS + path, opts)
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`)
  return data
}

export const api = {
  // Dashboard
  dashboard: () => request('GET', '/dashboard'),

  // Domains
  domains: () => request('GET', '/domains'),
  getDomain: (id) => request('GET', `/domains/${id}`),
  updateDomain: (id, data) => request('PATCH', `/domains/${id}`, data),

  // Ideas
  ideas: (params) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return request('GET', '/ideas' + q)
  },
  getIdea: (id) => request('GET', `/ideas/${id}`),
  createIdea: (data) => request('POST', '/ideas', data),
  updateIdea: (id, data) => request('PATCH', `/ideas/${id}`, data),
  deleteIdea: (id) => request('DELETE', `/ideas/${id}`),

  // Idea Attachments
  getAttachments: (ideaId) => request('GET', `/ideas/${ideaId}/attachments`),
  createAttachment: (ideaId, data) => request('POST', `/ideas/${ideaId}/attachments`, data),
  updateAttachment: (ideaId, attId, data) => request('PATCH', `/ideas/${ideaId}/attachments/${attId}`, data),
  deleteAttachment: (ideaId, attId) => request('DELETE', `/ideas/${ideaId}/attachments/${attId}`),
  uploadAttachment: (ideaId, file, name, notes) => {
    const form = new FormData()
    form.append('file', file)
    if (name) form.append('name', name)
    if (notes) form.append('notes', notes)
    return fetch(BASE + `/ideas/${ideaId}/attachments/upload`, {
      method: 'POST',
      body: form,
    }).then(r => r.json())
  },

  // Projects
  projects: (params) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return request('GET', '/projects' + q)
  },
  getProject: (id) => request('GET', `/projects/${id}`),
  createProject: (data) => request('POST', '/projects', data),
  updateProject: (id, data) => request('PATCH', `/projects/${id}`, data),
  deleteProject: (id) => request('DELETE', `/projects/${id}`),
  projectStats: () => request('GET', '/projects/stats'),

  // Assets
  assets: (params) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return request('GET', '/assets' + q)
  },
  createAsset: (data) => request('POST', '/assets', data),
  updateAsset: (id, data) => request('PATCH', `/assets/${id}`, data),
  deleteAsset: (id) => request('DELETE', `/assets/${id}`),

  // Schedule
  schedule: (params) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return request('GET', '/schedule' + q)
  },
  createScheduleItem: (data) => request('POST', '/schedule', data),
  updateScheduleItem: (id, data) => request('PATCH', `/schedule/${id}`, data),
  deleteScheduleItem: (id) => request('DELETE', `/schedule/${id}`),

  // Auth
  login: (username, password) => request('POST', '/auth/login', { username, password }),
  register: (username, password, display_name) =>
    request('POST', '/auth/register', { username, password, display_name }),
  getUser: (userId) => request('GET', `/auth/user`, null, { 'X-CIS-User-Id': userId }),

  // Ingestion
  scanIngest: (source, limit) => ingestRequest('POST', '/scan', { source, limit }),
  runIngest: (source, limit) => ingestRequest('POST', '/run', { source, limit }),
  reviewQueue: () => ingestRequest('GET', '/review'),
  approveAsset: (id) => ingestRequest('POST', `/review/${id}/approve`),
  rejectAsset: (id) => ingestRequest('POST', `/review/${id}/reject`),
  editAssetNotes: (id, notes) => ingestRequest('PATCH', `/review/${id}/edit`, { notes }),

  // LMS
  lmsCourses: () => lmsRequest('GET', '/courses'),
  lmsCourse: (id) => lmsRequest('GET', `/courses/${id}`),
  lmsSearch: (params) => lmsRequest('POST', '/search', params),
  lmsScan: () => lmsRequest('POST', '/scan', { dry_run: false }),
  lmsIndex: () => lmsRequest('POST', '/index'),
  lmsSuggest: (params) => lmsRequest('POST', '/suggest', params),
  lmsDashboard: () => lmsRequest('GET', '/dashboard'),
  lmsSchedule: (params) => lmsRequest('POST', '/schedule', params),

  // Spines ingestion
  ingestStatus: () => fetch('/api/ingest-spines/status').then(r => r.json()),
  ingestRun: (project) => fetch('/api/ingest-spines/run', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ project: project || '' }),
  }).then(r => r.json()),
  ingestFiles: () => fetch('/api/ingest-spines/files').then(r => r.json()),
  ingestFileDetail: (path) =>
    fetch(`/api/ingest-spines/files/${encodeURIComponent(path)}`).then(r => r.json()),

  // ── Tier 10: Pipeline views (added 2026-06-13) ────────────────────────
  pipelineStatus: () =>
    fetch('/api/pipeline/status').then(r => r.json()),
  pipelineNodeStatus: (label) =>
    fetch(`/api/pipeline/status/${encodeURIComponent(label)}`).then(r => r.json()),
  pipelineNextActions: () =>
    fetch('/api/pipeline/next-actions').then(r => r.json()),
  pipelineRuns: (limit = 20) =>
    fetch(`/api/pipeline/runs?limit=${limit}`).then(r => r.json()),
  pipelineRunDetail: (runId) =>
    fetch(`/api/pipeline/runs/${encodeURIComponent(runId)}`).then(r => r.json()),
  ericGate: () =>
    fetch('/api/pipeline/eric-gate').then(r => r.json()),
  decisions: () =>
    fetch('/api/decisions').then(r => r.json()),
  archiveSearchSemantic: (query, topK = 20) =>
    fetch(`/api/archive/search/semantic?q=${encodeURIComponent(query)}&top_k=${topK}`).then(r => r.json()),
  archiveSearchFts: (query, limit = 20) =>
    fetch(`/api/archive/search/fts?q=${encodeURIComponent(query)}&limit=${limit}`).then(r => r.json()),

  // ── Tier 11A: Dashboard full ──────────────────────────────────────────
  dashboardFull: () =>
    fetch('/api/dashboard/full').then(r => r.json()),

  // ── Tier 11B: Eric Gate approve ────────────────────────────────────────
  approveRun: (runId, rationale) =>
    fetch('/api/dashboard/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId, rationale: rationale || '' }),
    }).then(r => r.json()),
}
