import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

const STATUS_ORDER = ['captured','initiated','active','blocked','review','complete']
const STATUSES = ['captured','initiated','active','blocked','review','complete']
const PROJECT_TYPES = ['','new creation','iteration / revision','research / investigation','learning / study','infrastructure / system','maintenance','archive / documentation']
const PROJECT_GOALS = ['','explore / experiment','create / produce','learn / master','solve / fix','document / preserve','connect / share']

export default function ProjectsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [ideas, setIdeas] = useState([])
  const [sort, setSort] = useState('active')
  const [statusFilter, setStatusFilter] = useState('')
  const [domainFilter, setDomainFilter] = useState('')
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState({
    name: '', owner: '', start_date: '', due_date: '', level: 'beginner',
    type: '', goal: '', domain: 'creative', description: '', source_idea_id: ''
  })
  const [statusMsg, setStatusMsg] = useState('')

  // Load prefilled from idea promotion
  useEffect(() => {
    const source = searchParams.get('source')
    const name = searchParams.get('name')
    const desc = searchParams.get('desc')
    const domain = searchParams.get('domain')
    if (source || name) {
      setForm(f => ({ ...f, source_idea_id: source || '', name: name || '', description: desc || '', domain: domain || 'creative' }))
    }
  }, [searchParams])

  useEffect(() => {
    loadProjects()
    api.ideas({ status: 'captured' }).then(r => setIdeas(r.ideas || [])).catch(() => {})
  }, [])

  async function loadProjects() {
    try {
      const r = await api.projects()
      setProjects(r.projects || [])
    } catch {}
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!form.name.trim()) { setStatusMsg('Name is required'); return }
    try {
      await api.createProject(form)
      setStatusMsg('✓ Created')
      setForm({ name: '', owner: '', start_date: '', due_date: '', level: 'beginner', type: '', goal: '', domain: 'creative', description: '', source_idea_id: '' })
      loadProjects()
    } catch (e) { setStatusMsg('Error: ' + e.message) }
  }

  async function handleUpdate(id, field, value) {
    try {
      await api.updateProject(id, { [field]: value })
      setProjects(prev => prev.map(p => p.id === id ? { ...p, [field]: value } : p))
      if (selected?.id === id) setSelected(s => ({ ...s, [field]: value }))
    } catch {}
  }

  async function handleDelete(id) {
    if (!confirm('Delete this project?')) return
    try {
      await api.deleteProject(id)
      setSelected(null)
      loadProjects()
    } catch {}
  }

  let filtered = [...projects]
  if (domainFilter) filtered = filtered.filter(p => p.domain === domainFilter)
  if (statusFilter) filtered = filtered.filter(p => p.status === statusFilter)
  if (sort === 'active') filtered.sort((a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status))
  else if (sort === 'recent') filtered.sort((a, b) => new Date(b.updated || b.created) - new Date(a.updated || a.created))
  else if (sort === 'name') filtered.sort((a, b) => a.name.localeCompare(b.name))

  return (
    <div className="page-content">
      <div className="hdr">
        <div className="hdr-title">Projects</div>
        <div className="hdr-sub">Manage active projects — create, track status, link assets</div>
      </div>

      {/* Create form */}
      <div className="card" id="create-card">
        <div className="card-title">New Project</div>
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="row">
            <div className="col">
              <div className="field-row"><label className="field-label">Project name</label>
                <input className="cis-input" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
            </div>
            <div className="col">
              <div className="field-row"><label className="field-label">Owner</label>
                <input className="cis-input" value={form.owner} onChange={e => setForm(f => ({ ...f, owner: e.target.value }))} /></div>
            </div>
          </div>
          <div className="row">
            <div className="col"><div className="field-row"><label className="field-label">Start date</label><input className="cis-input" type="date" value={form.start_date} onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))} /></div></div>
            <div className="col"><div className="field-row"><label className="field-label">Due date</label><input className="cis-input" type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} /></div></div>
            <div className="col"><div className="field-row"><label className="field-label">Level</label>
              <select className="cis-select" value={form.level} onChange={e => setForm(f => ({ ...f, level: e.target.value }))}>
                <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option><option value="professional">Professional</option>
              </select></div></div>
          </div>
          <div className="row">
            <div className="col"><div className="field-row"><label className="field-label">Type</label>
              <select className="cis-select" value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                {PROJECT_TYPES.map(t => <option key={t} value={t}>{t || '— select —'}</option>)}
              </select></div></div>
            <div className="col"><div className="field-row"><label className="field-label">Goal</label>
              <select className="cis-select" value={form.goal} onChange={e => setForm(f => ({ ...f, goal: e.target.value }))}>
                {PROJECT_GOALS.map(g => <option key={g} value={g}>{g || '— select —'}</option>)}
              </select></div></div>
            <div className="col"><div className="field-row"><label className="field-label">Domain</label>
              <select className="cis-select" value={form.domain} onChange={e => setForm(f => ({ ...f, domain: e.target.value }))}>
                <option value="creative">Creative Production</option>
                <option value="socialcare">Social Care</option>
                <option value="personal">Personal</option>
                <option value="technical">Technical</option>
                <option value="learning">Learning</option>
              </select></div></div>
          </div>
          <div className="field-row"><label className="field-label">Idea source</label>
            <select className="cis-select" value={form.source_idea_id} onChange={e => setForm(f => ({ ...f, source_idea_id: e.target.value }))}>
              <option value="">— standalone —</option>
              {ideas.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
            </select></div>
          <textarea className="cis-textarea" placeholder="Description / goal statement" style={{ minHeight: 50 }}
            value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-blue" type="submit">+ Create Project</button>
            <button className="btn" type="button" onClick={() => setForm({
              name: '', owner: '', start_date: '', due_date: '', level: 'beginner',
              type: '', goal: '', domain: 'creative', description: '', source_idea_id: ''
            })}>Clear</button>
          </div>
          {statusMsg && <div style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#7a8299' }}>{statusMsg}</div>}
        </form>
      </div>

      {/* List */}
      <div className="card">
        <div className="card-title">All Projects</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
          {['active','all','recent','name'].map(s => (
            <button key={s} className="btn" style={{ fontSize: 9, padding: '4px 8px', background: sort === s ? 'rgba(74,158,255,.15)' : '' }}
              onClick={() => setSort(s)}>{s.charAt(0).toUpperCase() + s.slice(1)}</button>
          ))}
          <select className="cis-select" style={{ width: 'auto', minWidth: 120 }} value={domainFilter} onChange={e => setDomainFilter(e.target.value)}>
            <option value="">All domains</option>
            <option value="creative">Creative</option><option value="socialcare">Social Care</option>
            <option value="personal">Personal</option><option value="technical">Technical</option>
            <option value="learning">Learning</option>
          </select>
          <span style={{ flex: 1 }} />
          <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#7a8299', alignSelf: 'center' }}>{filtered.length} projects</span>
        </div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 12 }}>
          <button className="stat-btn" onClick={() => setStatusFilter('')} style={{ background: !statusFilter ? 'rgba(74,158,255,.15)' : '' }}>All</button>
          {STATUSES.map(s => (
            <button key={s} className="stat-btn" onClick={() => setStatusFilter(s)}
              style={{ background: statusFilter === s ? 'rgba(74,158,255,.15)' : '' }}>{s}</button>
          ))}
        </div>
        {filtered.length === 0 ? (
          <div className="empty-state">No projects match.</div>
        ) : filtered.map(p => (
          <div key={p.id} className="proj-card" onClick={() => navigate('/projects/' + p.id)}>
            <div className="proj-hdr">
              <div className="proj-name">{p.name}</div>
              <span className="proj-status" style={{ borderColor: p.status === 'complete' ? '#3dffa0' : p.status === 'blocked' ? '#ff4a6a' : p.status === 'active' ? '#4a9eff' : '#ffb830', color: p.status === 'complete' ? '#3dffa0' : p.status === 'blocked' ? '#ff4a6a' : p.status === 'active' ? '#4a9eff' : '#ffb830' }}>{p.status}</span>
            </div>
            <div className="proj-meta">
              <span className={`tag-domain ${p.domain}`}>{p.domain}</span>
              {p.type && <span className="tag">{p.type}</span>}
              {p.goal && <span className="tag">{p.goal}</span>}
              <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: '#7a8299' }}>{p.start_date || '—'} → {p.due_date || '—'}</span>
            </div>
            {p.description && <div className="proj-desc">{p.description.slice(0, 160)}{p.description.length > 160 ? '…' : ''}</div>}
            <div className="prog-bar"><div className="prog-fill" style={{ width: (p.progress || 0) + '%' }}></div></div>
          </div>
        ))}
      </div>
    </div>
  )
}
