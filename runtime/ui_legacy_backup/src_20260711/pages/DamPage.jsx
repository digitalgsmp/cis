import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const ASSET_TYPES = ['research', 'reference', 'learning', 'template', 'checklist', 'output', 'note']
const REVIEW_STATUSES = ['draft', 'reviewed', 'approved', 'locked', 'deprecated']
const TYPE_ICONS = { research: '🔬', reference: '📎', learning: '🎓', template: '📋', checklist: '✅', output: '📦', note: '📝' }
const TYPE_COLORS = { research: '#4a9eff', reference: '#a855f7', learning: '#3dffa0', template: '#ffb830', checklist: '#3dffa0', output: '#22d3ee', note: '#7a8299' }

export default function DamPage() {
  const navigate = useNavigate()
  const [assets, setAssets] = useState([])
  const [projects, setProjects] = useState([])
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [projectFilter, setProjectFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selected, setSelected] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    name: '', type: 'reference', url: '', path: '', project_id: '', category: '', notes: '', tags: ''
  })

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [a, p] = await Promise.all([api.assets(), api.projects()])
      setAssets(a.assets || [])
      setProjects(p.projects || [])
    } catch {}
  }

  let filtered = [...assets]
  if (typeFilter) filtered = filtered.filter(a => a.type === typeFilter)
  if (projectFilter) filtered = filtered.filter(a => a.project_id === projectFilter)
  if (statusFilter) filtered = filtered.filter(a => a.status === statusFilter)
  if (search) {
    const q = search.toLowerCase()
    filtered = filtered.filter(a =>
      (a.name + ' ' + (a.notes || '') + ' ' + (a.category || '') + ' ' + (a.tags || []).join(' ')).toLowerCase().includes(q)
    )
  }
  filtered.sort((a, b) => new Date(b.updated || b.created) - new Date(a.updated || a.created))

  async function handleCreate(e) {
    e.preventDefault()
    if (!form.name.trim()) return
    try {
      await api.createAsset({ ...form, tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [] })
      setShowForm(false)
      setForm({ name: '', type: 'reference', url: '', path: '', project_id: '', category: '', notes: '', tags: '' })
      loadData()
    } catch {}
  }

  async function handleStatusUpdate(id, status) {
    try {
      await api.updateAsset(id, { status })
      setAssets(prev => prev.map(a => a.id === id ? { ...a, status } : a))
      if (selected?.id === id) setSelected(s => ({ ...s, status }))
    } catch {}
  }

  async function handleDelete(id) {
    if (!confirm('Delete this asset?')) return
    try {
      await api.deleteAsset(id)
      setSelected(null)
      loadData()
    } catch {}
  }

  return (
    <div className="page-content">
      <div className="hdr">
        <div className="hdr-title">DAM — Digital Asset Management</div>
        <div className="hdr-sub">Store, search, review, and link all project assets</div>
      </div>

      {/* Search + filters */}
      <div className="card" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input className="cis-input" type="text" placeholder="Search all assets…" value={search}
            onChange={e => setSearch(e.target.value)} style={{ flex: 1, minWidth: 200 }} />
          <select className="cis-select" style={{ width: 'auto', minWidth: 100 }} value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
            <option value="">All types</option>
            {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select className="cis-select" style={{ width: 'auto', minWidth: 120 }} value={projectFilter} onChange={e => setProjectFilter(e.target.value)}>
            <option value="">All projects</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select className="cis-select" style={{ width: 'auto', minWidth: 100 }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">Any status</option>
            {REVIEW_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button className="btn btn-blue" onClick={() => setShowForm(!showForm)}>+ Add Asset</button>
          <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#7a8299' }}>{filtered.length} assets</span>
        </div>
      </div>

      {/* Add form */}
      {showForm && <div className="card">
        <div className="card-title">New Asset</div>
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="row">
            <div className="col"><div className="field-row"><label className="field-label">Name</label>
              <input className="cis-input" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div></div>
            <div className="col"><div className="field-row"><label className="field-label">Type</label>
              <select className="cis-select" value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                {ASSET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select></div></div>
          </div>
          <div className="row">
            <div className="col"><div className="field-row"><label className="field-label">URL</label>
              <input className="cis-input" value={form.url} onChange={e => setForm(f => ({ ...f, url: e.target.value }))} /></div></div>
            <div className="col"><div className="field-row"><label className="field-label">File path</label>
              <input className="cis-input" value={form.path} onChange={e => setForm(f => ({ ...f, path: e.target.value }))} /></div></div>
          </div>
          <div className="row">
            <div className="col"><div className="field-row"><label className="field-label">Project</label>
              <select className="cis-select" value={form.project_id} onChange={e => setForm(f => ({ ...f, project_id: e.target.value }))}>
                <option value="">— global —</option>
                {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select></div></div>
            <div className="col"><div className="field-row"><label className="field-label">Category</label>
              <input className="cis-input" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} /></div></div>
          </div>
          <textarea className="cis-textarea" placeholder="Description / notes" style={{ minHeight: 50 }}
            value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          <input className="cis-input" placeholder="Tags (comma-separated)" value={form.tags}
            onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-blue" type="submit">+ Add</button>
            <button className="btn" type="button" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      </div>}

      {/* Asset grid */}
      <div className="asset-grid">
        {filtered.length === 0 ? (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>No assets match your filters.</div>
        ) : filtered.map(a => {
          const p = projects.find(x => x.id === a.project_id)
          return <div key={a.id} className="asset-card" onClick={() => navigate('/dam/' + a.id)}>
            <div className="asset-icon" style={{ color: TYPE_COLORS[a.type] || '#7a8299' }}>{TYPE_ICONS[a.type] || '📄'}</div>
            <div className="asset-body">
              <div className="asset-name">{a.name}</div>
              <div className="asset-meta">
                <span className="tag" style={{ borderColor: TYPE_COLORS[a.type] || '#fff', color: TYPE_COLORS[a.type] }}>{a.type}</span>
                {a.category && <span className="tag">{a.category}</span>}
                {p ? <span className={`tag-domain ${p.domain}`}>{p.name}</span> : <span className="tag" style={{ color: '#7a8299' }}>global</span>}
                <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 8, color: a.status === 'approved' ? '#3dffa0' : a.status === 'deprecated' ? '#ff4a6a' : '#ffb830' }}>{a.status}</span>
              </div>
              {a.notes && <div className="asset-desc">{a.notes.slice(0, 120)}{a.notes.length > 120 ? '…' : ''}</div>}
              {a.tags && a.tags.length > 0 && (
                <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', marginBottom: 3 }}>
                  {a.tags.map(t => <span key={t} className="tag">#{t}</span>)}
                </div>
              )}
              {a.url && <div style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: '#7a8299', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>🔗 {a.url}</div>}
            </div>
          </div>
        })}
      </div>

    </div>
  )
}
