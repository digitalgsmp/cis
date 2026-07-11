import React, { useState, useEffect } from 'react'
import { api } from '../api'

const STATUS_COLORS = {
  draft: '#ffb830',
  reviewed: '#3dffa0',
  approved: '#4a9eff',
  locked: '#a855f7',
  deprecated: '#ff4a6a'
}

function TextPreview({ text, maxLen = 200 }) {
  if (!text) return <span style={{ color: '#5a6279', fontStyle: 'italic' }}>No transcription</span>
  const display = text.length > maxLen ? text.slice(0, maxLen) + '...' : text
  const lines = display.split('\n').filter(Boolean)
  return (
    <pre style={{
      fontFamily: '"Share Tech Mono", monospace',
      fontSize: 10,
      color: '#b0b8d0',
      whiteSpace: 'pre-wrap',
      lineHeight: 1.5,
      margin: 0,
      maxHeight: 200,
      overflow: 'auto'
    }}>
      {lines.slice(0, 15).join('\n')}
      {lines.length > 15 && '\n...'}
    </pre>
  )
}

export default function ReviewQueue() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)
  const [editing, setEditing] = useState('')
  const [savingId, setSavingId] = useState(null)
  const [filter, setFilter] = useState('all')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    loadQueue()
  }, [])

  async function loadQueue() {
    setLoading(true)
    try {
      const data = await api.reviewQueue()
      setItems(data.items || [])
    } catch (e) {
      setMsg('Failed to load: ' + e.message)
    }
    setLoading(false)
  }

  async function approve(id) {
    try {
      await api.approveAsset(id)
      setItems(items.filter(i => i.id !== id))
      if (selected?.id === id) setSelected(null)
      setMsg('✓ Approved')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  async function reject(id) {
    if (!confirm('Reject and delete this item?')) return
    try {
      await api.rejectAsset(id)
      setItems(items.filter(i => i.id !== id))
      if (selected?.id === id) setSelected(null)
      setMsg('🗑 Rejected')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
  }

  async function saveEdit(id) {
    setSavingId(id)
    try {
      await api.editAssetNotes(id, editing)
      setMsg('✓ Transcription saved')
      setTimeout(() => setMsg(''), 2000)
      // Update in-place
      setItems(items.map(i => i.id === id ? { ...i, notes: editing } : i))
      if (selected?.id === id) setSelected({ ...selected, notes: editing })
    } catch (e) {
      setMsg('Error: ' + e.message)
    }
    setSavingId(null)
  }

  function startEdit(item) {
    setSelected(item)
    setEditing(item.notes || '')
  }

  const filtered = filter === 'all' ? items : items.filter(i => i.type === filter)

  if (loading) return <div className="page-content"><div className="empty-state">Loading review queue...</div></div>

  return (
    <div className="page-content">
      <div className="hdr">
        <div className="hdr-title">📋 Review Queue</div>
        <div className="hdr-sub">{items.length} items pending approval</div>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
        <span style={{ color: '#7a8299', fontSize: 11 }}>Filter:</span>
        {['all', 'creative_work', 'reference', 'document', 'image'].map(t => (
          <button key={t}
            className={`btn ${filter === t ? 'btn-blue' : ''}`}
            onClick={() => setFilter(t)}
            style={{ fontSize: 10, padding: '4px 10px' }}>
            {t === 'all' ? 'All' : t.replace('_', ' ')}
          </button>
        ))}
        <span style={{ flex: 1 }} />
        <button className="btn" onClick={loadQueue} style={{ fontSize: 10 }}>↻ Refresh</button>
        {msg && <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#3dffa0' }}>{msg}</span>}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state" style={{ padding: 40, textAlign: 'center', color: '#5a6279' }}>
          Nothing pending — queue is empty!
        </div>
      ) : (
        <div className="row" style={{ gap: 16 }}>
          {/* List column */}
          <div className="col" style={{ flex: 1, maxHeight: '70vh', overflowY: 'auto' }}>
            {filtered.map(item => (
              <div key={item.id}
                className={`card ${selected?.id === item.id ? 'card-selected' : ''}`}
                onClick={() => startEdit(item)}
                style={{
                  cursor: 'pointer',
                  padding: 12,
                  marginBottom: 8,
                  border: selected?.id === item.id ? '1px solid #4a9eff' : '1px solid #1e2338'
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <strong style={{ fontSize: 12 }}>{item.name}</strong>
                  <span className="proj-status" style={{
                    fontSize: 9, padding: '2px 8px',
                    borderColor: STATUS_COLORS[item.status] || '#7a8299',
                    color: STATUS_COLORS[item.status] || '#7a8299'
                  }}>
                    {item.status}
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 4 }}>
                  <span className="tag" style={{ fontSize: 9 }}>📁 {item.type}</span>
                  {(item.tags || []).slice(0, 4).map((t, i) => (
                    <span key={i} className="tag" style={{ fontSize: 9 }}>{t}</span>
                  ))}
                </div>
                <TextPreview text={item.notes} maxLen={150} />
                <div style={{ fontSize: 9, color: '#5a6279', marginTop: 6, fontFamily: '"Share Tech Mono", monospace' }}>
                  {new Date(item.created).toLocaleDateString()} · {item.path?.split('/').slice(-2).join('/')}
                </div>
              </div>
            ))}
          </div>

          {/* Edit column */}
          <div className="col" style={{ flex: 2 }}>
            {selected ? (
              <div className="card">
                <div className="card-title">✏️ Edit Transcription</div>
                <div className="det-field">
                  <label className="field-label">Name</label>
                  <input className="cis-input" value={selected.name} disabled style={{ opacity: 0.6 }} />
                </div>
                <div className="det-field">
                  <label className="field-label">File path</label>
                  <input className="cis-input" value={selected.path || ''} disabled style={{ opacity: 0.6 }} />
                </div>
                <div className="det-row">
                  <div className="det-field">
                    <label className="field-label">Type</label>
                    <input className="cis-input" value={selected.type} disabled style={{ opacity: 0.6 }} />
                  </div>
                  <div className="det-field">
                    <label className="field-label">Tags</label>
                    <input className="cis-input"
                      value={(selected.tags || []).join(', ')}
                      disabled style={{ opacity: 0.6 }} />
                  </div>
                </div>
                <div className="det-field">
                  <label className="field-label">Transcribed Text (editable)</label>
                  <textarea className="cis-textarea"
                    style={{ minHeight: 280, fontFamily: '"Share Tech Mono", monospace', fontSize: 11 }}
                    value={editing}
                    onChange={e => setEditing(e.target.value)} />
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button className="btn btn-blue" onClick={() => saveEdit(selected.id)}
                    disabled={savingId === selected.id}>
                    {savingId === selected.id ? 'Saving...' : '💾 Save Edit'}
                  </button>
                  <button className="btn" onClick={() => approve(selected.id)}
                    style={{ background: '#1a3a2e', borderColor: '#3dffa0', color: '#3dffa0' }}>
                    ✅ Approve
                  </button>
                  <button className="btn btn-red" onClick={() => reject(selected.id)}>
                    🗑 Reject
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state" style={{
                padding: 40, textAlign: 'center', color: '#5a6279',
                border: '1px dashed #1e2338', borderRadius: 8
              }}>
                Select an item from the list to review and edit its transcription
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
