import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../api'

const STATUS_OPTIONS = ['draft', 'reviewed', 'approved', 'locked', 'deprecated']

export default function AssetDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [asset, setAsset] = useState(null)
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    Promise.all([
      api.assets().then(r => {
        const found = (r.assets || []).find(a => a.id === id)
        return found || null
      }),
      api.projects()
    ]).then(([found, projRes]) => {
      setAsset(found)
      setProjects(projRes.projects || [])
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [id])

  async function handleSave() {
    if (!asset) return
    setSaving(true)
    try {
      await api.updateAsset(asset.id, asset)
      setMsg('✓ Saved')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setSaving(false)
  }

  async function handleDelete() {
    if (!confirm('Delete this asset?')) return
    try {
      await api.deleteAsset(asset.id)
      navigate('/dam')
    } catch {}
  }

  function update(field, value) {
    setAsset(a => ({ ...a, [field]: value }))
  }

  if (loading) return <div className="page-content"><div className="empty-state">Loading...</div></div>
  if (!asset) return (
    <div className="page-content">
      <div className="hdr"><div className="hdr-title">Asset Not Found</div></div>
      <button className="btn" onClick={() => navigate('/dam')}>← Back to DAM</button>
    </div>
  )

  const project = projects.find(p => p.id === asset.project_id)
  const statusColors = { draft: '#ffb830', reviewed: '#4a9eff', approved: '#3dffa0', locked: '#a855f7', deprecated: '#ff4a6a' }

  return (
    <div className="page-content">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button className="btn" onClick={() => navigate('/dam')}>← Back</button>
        <div>
          <div className="hdr-title" style={{ margin: 0 }}>{asset.name}</div>
          <div className="hdr-sub" style={{ margin: 0 }}>Asset detail · {asset.type} · {asset.id}</div>
        </div>
        <span style={{ flex: 1 }} />
        <span className="proj-status" style={{ borderColor: statusColors[asset.status] || '#7a8299', color: statusColors[asset.status] || '#7a8299', fontSize: 11, padding: '4px 12px' }}>{asset.status}</span>
      </div>

      <div className="row">
        <div className="col" style={{ flex: 2 }}>
          <div className="card">
            <div className="card-title">Details</div>
            <div className="det-row">
              <div className="det-field">
                <label className="field-label">Name</label>
                <input className="cis-input" value={asset.name} onChange={e => update('name', e.target.value)} />
              </div>
              <div className="det-field">
                <label className="field-label">Type</label>
                <select className="cis-select" value={asset.type} onChange={e => update('type', e.target.value)}>
                  <option value="research">Research</option>
                  <option value="reference">Reference</option>
                  <option value="learning">Learning</option>
                  <option value="template">Template</option>
                  <option value="checklist">Checklist</option>
                  <option value="output">Output</option>
                  <option value="note">Note</option>
                </select>
              </div>
              <div className="det-field">
                <label className="field-label">Status</label>
                <select className="cis-select" value={asset.status} onChange={e => update('status', e.target.value)}>
                  {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            {asset.url && (
              <div className="det-field">
                <label className="field-label">URL</label>
                <input className="cis-input" value={asset.url} onChange={e => update('url', e.target.value)} />
                <a href={asset.url} target="_blank" rel="noopener noreferrer" style={{ color: '#4a9eff', fontSize: 11, marginTop: 4, display: 'inline-block' }}>Open in new tab →</a>
              </div>
            )}
            <div className="det-field">
              <label className="field-label">File path</label>
              <input className="cis-input" value={asset.path || ''} onChange={e => update('path', e.target.value)} />
            </div>
            <div className="det-row">
              <div className="det-field">
                <label className="field-label">Category</label>
                <input className="cis-input" value={asset.category || ''} onChange={e => update('category', e.target.value)} />
              </div>
              <div className="det-field">
                <label className="field-label">Project</label>
                <select className="cis-select" value={asset.project_id || ''} onChange={e => update('project_id', e.target.value)}>
                  <option value="">— global —</option>
                  {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
                {project && <Link to={`/projects/${project.id}`} style={{ color: '#4a9eff', fontSize: 11, marginTop: 4, display: 'inline-block' }}>View project →</Link>}
              </div>
            </div>
            <div className="det-field">
              <label className="field-label">Notes</label>
              <textarea className="cis-textarea" style={{ minHeight: 100 }} value={asset.notes || ''}
                onChange={e => update('notes', e.target.value)} />
            </div>
            <div className="det-field">
              <label className="field-label">Tags</label>
              <input className="cis-input" value={(asset.tags || []).join(', ')}
                onChange={e => update('tags', e.target.value.split(',').map(t => t.trim()).filter(Boolean))} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="btn btn-blue" onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Changes'}</button>
              <button className="btn btn-red" onClick={handleDelete}>Delete Asset</button>
              {msg && <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#3dffa0', alignSelf: 'center' }}>{msg}</span>}
            </div>
          </div>
        </div>
        <div className="col">
          <div className="card">
            <div className="card-title">Metadata</div>
            <div style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: '#7a8299', lineHeight: 1.8 }}>
              <div>ID: {asset.id}</div>
              <div>Created: {new Date(asset.created).toLocaleString()}</div>
              <div>Updated: {new Date(asset.updated || asset.created).toLocaleString()}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
