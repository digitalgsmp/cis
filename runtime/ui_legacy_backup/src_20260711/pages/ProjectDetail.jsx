import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'

const STATUSES = ['captured', 'initiated', 'active', 'blocked', 'review', 'complete']
const LEVELS = ['beginner', 'intermediate', 'advanced', 'professional']

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.getProject(id).then(p => {
      setProject(p)
      setLoading(false)
    }).catch(() => {
      setLoading(false)
      setProject(null)
    })
  }, [id])

  async function handleSave() {
    if (!project) return
    setSaving(true)
    try {
      await api.updateProject(project.id, project)
      setMsg('✓ Saved')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setSaving(false)
  }

  async function handleDelete() {
    if (!confirm('Delete this project?')) return
    try {
      await api.deleteProject(project.id)
      navigate('/projects')
    } catch {}
  }

  function update(field, value) {
    setProject(p => ({ ...p, [field]: value }))
  }

  if (loading) return <div className="page-content"><div className="empty-state">Loading...</div></div>
  if (!project) return (
    <div className="page-content">
      <div className="hdr"><div className="hdr-title">Project Not Found</div></div>
      <button className="btn" onClick={() => navigate('/projects')}>← Back to Projects</button>
    </div>
  )

  const sc = project.status === 'complete' ? '#3dffa0' : project.status === 'blocked' ? '#ff4a6a' : project.status === 'active' ? '#4a9eff' : '#ffb830'

  return (
    <div className="page-content">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <button className="btn" onClick={() => navigate('/projects')}>← Back</button>
        <div>
          <div className="hdr-title" style={{ margin: 0 }}>{project.name}</div>
          <div className="hdr-sub" style={{ margin: 0 }}>Project detail · {project.id}</div>
        </div>
        <span style={{ flex: 1 }} />
        <span className="proj-status" style={{ borderColor: sc, color: sc, fontSize: 11, padding: '4px 12px' }}>{project.status}</span>
        <div className="prog-bar" style={{ width: 120 }}><div className="prog-fill" style={{ width: (project.progress || 0) + '%' }}></div></div>
      </div>

      <div className="row">
        <div className="col">
          <div className="card">
            <div className="card-title">Details</div>
            <div className="field-row">
              <label className="field-label">Status</label>
              <select className="cis-select" value={project.status} onChange={e => update('status', e.target.value)}>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="det-row">
              <div className="det-field">
                <label className="field-label">Progress</label>
                <input className="cis-input" type="number" min="0" max="100" value={project.progress || 0}
                  onChange={e => update('progress', parseInt(e.target.value) || 0)} />
              </div>
              <div className="det-field">
                <label className="field-label">Owner</label>
                <input className="cis-input" value={project.owner || ''} onChange={e => update('owner', e.target.value)} />
              </div>
            </div>
            <div className="det-row">
              <div className="det-field">
                <label className="field-label">Start date</label>
                <input className="cis-input" type="date" value={project.start_date || ''} onChange={e => update('start_date', e.target.value)} />
              </div>
              <div className="det-field">
                <label className="field-label">Due date</label>
                <input className="cis-input" type="date" value={project.due_date || ''} onChange={e => update('due_date', e.target.value)} />
              </div>
            </div>
            <div className="det-row">
              <div className="det-field">
                <label className="field-label">Level</label>
                <select className="cis-select" value={project.level} onChange={e => update('level', e.target.value)}>
                  {LEVELS.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
              <div className="det-field">
                <label className="field-label">Type</label>
                <input className="cis-input" value={project.type || ''} onChange={e => update('type', e.target.value)} />
              </div>
              <div className="det-field">
                <label className="field-label">Goal</label>
                <input className="cis-input" value={project.goal || ''} onChange={e => update('goal', e.target.value)} />
              </div>
            </div>
            <div className="det-field">
              <label className="field-label">Domain</label>
              <select className="cis-select" value={project.domain} onChange={e => update('domain', e.target.value)}>
                <option value="creative">Creative</option><option value="socialcare">Social Care</option>
                <option value="personal">Personal</option><option value="technical">Technical</option>
                <option value="learning">Learning</option>
              </select>
            </div>
            <div className="det-field">
              <label className="field-label">Description</label>
              <textarea className="cis-textarea" style={{ minHeight: 80 }} value={project.description || ''}
                onChange={e => update('description', e.target.value)} />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="btn btn-blue" onClick={handleSave} disabled={saving}>{saving ? 'Saving...' : 'Save Changes'}</button>
              <button className="btn btn-red" onClick={handleDelete}>Delete Project</button>
              {msg && <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#3dffa0', alignSelf: 'center' }}>{msg}</span>}
            </div>
          </div>
        </div>
        <div className="col">
          <div className="card">
            <div className="card-title">Linked Assets</div>
            <p style={{ color: '#7a8299', fontSize: 12 }}>Assets linked to this project will appear here.</p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
              <span className="tag">🔬 {(project.linked_research || []).length} research</span>
              <span className="tag">📎 {(project.linked_references || []).length} references</span>
              <span className="tag">🎓 {(project.linked_learning || []).length} learning</span>
              <span className="tag">📋 {(project.linked_templates || []).length} templates</span>
              <span className="tag">✅ {(project.linked_checklists || []).length} checklists</span>
            </div>
          </div>
          <div className="card">
            <div className="card-title">Schedule</div>
            <p style={{ color: '#7a8299', fontSize: 12 }}>Scheduled time blocks for this project.</p>
            <span className="tag">📅 {(project.schedule_slots || []).length} slots</span>
          </div>
          <div className="card">
            <div className="card-title">Metadata</div>
            <div style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: '#7a8299', lineHeight: 1.8 }}>
              <div>ID: {project.id}</div>
              <div>Created: {new Date(project.created).toLocaleString()}</div>
              <div>Updated: {new Date(project.updated || project.created).toLocaleString()}</div>
              {project.source_idea_id && <div>Source idea: {project.source_idea_id}</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
