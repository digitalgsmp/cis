import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import IdeaWorkbench from '../components/IdeaWorkbench'

const DOMAIN_LABELS = {
  creative: 'Creative',
  socialcare: 'Social Care',
  personal: 'Personal',
  technical: 'Technical',
  learning: 'Learning',
}

const _isImageFile = (path) => {
  if (!path) return false
  const ext = path.split('.').pop().toLowerCase()
  return ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'tif'].includes(ext)
}

// ── Sample icon for uningested items — generates a colored thumbnail ────
function IdeaThumb({ title, type, selected, onClick }) {
  const colors = ['#2a1f3d', '#1f2d3d', '#3d2a1f', '#1f3d2a', '#3d1f2f', '#2a3d1f']
  const colorIdx = title.split('').reduce((a, c) => a + c.charCodeAt(0), 0) % colors.length
  const bg = colors[colorIdx]

  return (
    <div onClick={onClick}
      style={{
        width: '100%',
        aspectRatio: '3/4',
        background: bg,
        borderRadius: 6,
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        padding: 8,
        border: selected ? '2px solid #4a9eff' : '1px solid transparent',
        transition: 'border 0.15s',
        position: 'relative',
        overflow: 'hidden',
      }}>
      {/* Text preview — first few chars as a visual stand-in */}
      <div style={{
        fontFamily: '"Barlow Condensed", sans-serif',
        fontSize: 9,
        color: 'rgba(255,255,255,0.15)',
        lineHeight: 1.3,
        marginBottom: 4,
        overflow: 'hidden',
        display: '-webkit-box',
        WebkitLineClamp: 6,
        WebkitBoxOrient: 'vertical',
        wordBreak: 'break-word',
      }}>
        {title.split('').map((c, i) => (
          <span key={i} style={{ opacity: 0.3 + Math.random() * 0.4 }}>{c}</span>
        ))}
      </div>
      <div style={{
        fontFamily: '"Barlow Condensed", sans-serif',
        fontWeight: 600,
        fontSize: 11,
        color: '#fff',
        lineHeight: 1.2,
        textShadow: '0 1px 3px rgba(0,0,0,0.8)',
        wordBreak: 'break-word',
      }}>
        {title}
      </div>
      {type && (
        <div style={{
          position: 'absolute', top: 6, right: 6,
          background: 'rgba(0,0,0,0.6)',
          borderRadius: 3, padding: '1px 5px',
          fontSize: 8, color: '#7a8299',
          fontFamily: '"Share Tech Mono", monospace',
        }}>
          {type}
        </div>
      )}
    </div>
  )
}

export default function IdeasPage() {
  const navigate = useNavigate()
  const [ideas, setIdeas] = useState([])
  const [search, setSearch] = useState('')
  const [filterTag, setFilterTag] = useState('all')
  const [viewMode, setViewMode] = useState('grid') // 'grid' or 'list'
  const [selectedIdea, setSelectedIdea] = useState(null)
  const [workbenchIdea, setWorkbenchIdea] = useState(null)
  const [showForm, setShowForm] = useState(false)

  // For manual input
  const [form, setForm] = useState({
    name: '', link: '', date: '', description: '', context: '',
    domain: 'creative', category: '', medium: '', story_type: '', user_level: 'beginner',
    tags: '', content: '', file_path: ''
  })
  const [domains, setDomains] = useState([])
  const [statusMsg, setStatusMsg] = useState('')

  useEffect(() => {
    loadIdeas()
    api.domains().then(d => setDomains(d.domains || [])).catch(() => {})
  }, [])

  async function loadIdeas() {
    try {
      const r = await api.ideas()
      setIdeas(r.ideas || [])
    } catch {}
  }

  // ── Filtering ─────────────────────────────────────────────────────────
  const allTags = [...new Set(ideas.flatMap(i => {
    const t = i.tags
    if (Array.isArray(t)) return t
    if (typeof t === 'string') return t.split(',').map(s => s.trim()).filter(Boolean)
    return []
  }))].slice(0, 20)

  const filtered = ideas.filter(i => {
    if (filterTag !== 'all') {
      const tags = Array.isArray(i.tags) ? i.tags : (typeof i.tags === 'string' ? i.tags.split(',').map(s => s.trim()) : [])
      if (!tags.some(t => t.toLowerCase().includes(filterTag.toLowerCase()))) return false
    }
    if (search) {
      const q = search.toLowerCase()
      if (!i.name?.toLowerCase().includes(q) && !i.description?.toLowerCase().includes(q)) return false
    }
    return true
  })

  // ── Manual idea capture ───────────────────────────────────────────────
  const selectedDomain = domains.find(d => d.id === form.domain)
  const categories = selectedDomain?.categories || []
  const media = selectedDomain?.media || []

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.name.trim()) { setStatusMsg('Name required'); return }
    try {
      await api.createIdea({
        ...form,
        tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : []
      })
      setStatusMsg('✓ Captured')
      setForm({ name: '', link: '', date: '', description: '', context: '', domain: 'creative', category: '', medium: '', story_type: '', user_level: 'beginner', tags: '', content: '', file_path: '' })
      setShowForm(false)
      loadIdeas()
      setTimeout(() => setStatusMsg(''), 2000)
    } catch (e) { setStatusMsg('Error: ' + e.message) }
  }

  // ── Promote ───────────────────────────────────────────────────────────
  async function handlePromote(idea) {
    try {
      await api.updateIdea(idea.id, { status: 'promoted' })
      navigate('/projects?source=' + idea.id + '&name=' + encodeURIComponent(idea.name) + '&desc=' + encodeURIComponent(idea.description || '') + '&domain=' + idea.domain)
    } catch {}
  }

  // ── Detail / Workbench selection ─────────────────────────────
  function selectIdea(idea) {
    if (idea.file_path && /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(idea.file_path)) {
      // Card has a scanned image → open full workbench
      setWorkbenchIdea(idea)
      setSelectedIdea(null)
    } else {
      // Text-only idea → open existing detail panel
      setSelectedIdea(selectedIdea?.id === idea.id ? null : idea)
      setWorkbenchIdea(null)
    }
  }

  return workbenchIdea ? (
    <IdeaWorkbench
      idea={workbenchIdea}
      onBack={() => { setWorkbenchIdea(null); loadIdeas() }}
      onSave={(idea, updates) => { /* workbench saves via API */ }}
    />
  ) : (
    <div className="page-content" style={{ padding: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* ── Top bar ───────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '12px 20px', borderBottom: '1px solid #fff',
        flexShrink: 0,
      }}>
        <div>
          <div className="hdr-title" style={{ margin: 0, fontSize: 18 }}>Idea Bank</div>
          <div className="hdr-sub" style={{ margin: 0, fontSize: 10 }}>{ideas.length} ideas · {filtered.length} shown</div>
        </div>
        <div style={{ flex: 1 }} />

        {/* Search */}
        <input className="cis-input"
          style={{ width: 200, fontSize: 10, padding: '5px 10px' }}
          placeholder="🔍 Search ideas..."
          value={search}
          onChange={e => setSearch(e.target.value)} />

        {/* View toggle */}
        <button className="btn" onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          style={{ fontSize: 10, padding: '4px 10px' }}>
          {viewMode === 'grid' ? '☰ List' : '⊞ Grid'}
        </button>

        {/* New Idea button */}
        <button className="btn btn-blue" onClick={() => setShowForm(true)}
          style={{ fontSize: 10, padding: '4px 14px' }}>
          + New Idea
        </button>
      </div>

      {/* ── Tag filters ───────────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: 6, padding: '8px 20px',
        borderBottom: '1px solid #1e2338', overflowX: 'auto',
        flexShrink: 0,
      }}>
        <button className={`btn ${filterTag === 'all' ? 'btn-blue' : ''}`}
          onClick={() => setFilterTag('all')}
          style={{ fontSize: 9, padding: '2px 10px', whiteSpace: 'nowrap' }}>
          All
        </button>
        {allTags.map(t => (
          <button key={t}
            className={`btn ${filterTag === t ? 'btn-blue' : ''}`}
            onClick={() => setFilterTag(t)}
            style={{ fontSize: 9, padding: '2px 10px', whiteSpace: 'nowrap' }}>
            {t}
          </button>
        ))}
      </div>

      {/* ── Main content area ─────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Thumbnail grid / list (scrollable) */}
        <div style={{
          flex: 1, overflow: 'auto', padding: 16,
        }}>
          {filtered.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#5a6279', fontSize: 12 }}>
              {ideas.length === 0 ? 'No ideas yet. Add one or import from the archive.' : 'No ideas match your filter.'}
            </div>
          ) : viewMode === 'grid' ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
              gap: 12,
            }}>
              {filtered.map(idea => (
                <IdeaThumb key={idea.id}
                  title={idea.name}
                  type={idea.domain}
                  selected={selectedIdea?.id === idea.id}
                  onClick={() => selectIdea(idea)} />
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filtered.map(idea => (
                <div key={idea.id}
                  onClick={() => selectIdea(idea)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '6px 10px', cursor: 'pointer',
                    borderRadius: 4,
                    background: selectedIdea?.id === idea.id ? '#1a1d2e' : 'transparent',
                    border: selectedIdea?.id === idea.id ? '1px solid #4a9eff' : '1px solid transparent',
                    fontSize: 11,
                  }}>
                  <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: '#7a8299', width: 80, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {idea.date || idea.created?.slice(0, 10) || '—'}
                  </span>
                  <span style={{ flex: 1, fontWeight: 600 }}>{idea.name}</span>
                  <span className="tag" style={{ fontSize: 8 }}>{idea.domain}</span>
                  {idea.medium && <span className="tag" style={{ fontSize: 8 }}>{idea.medium}</span>}
                  <span className="tag" style={{
                    fontSize: 8,
                    borderColor: idea.status === 'promoted' ? '#3dffa0' : '#ffb830',
                    color: idea.status === 'promoted' ? '#3dffa0' : '#ffb830'
                  }}>{idea.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Detail / Preview panel ──────────────────────────── */}
        {selectedIdea && (
          <div style={{
            width: 350, borderLeft: '1px solid #1e2338',
            overflow: 'auto', padding: 16, flexShrink: 0,
          }}>
            {/* Thumbnail at top */}
            <div style={{ marginBottom: 12 }}>
              <IdeaThumb title={selectedIdea.name} type={selectedIdea.domain} />
            </div>

            <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
              {selectedIdea.name}
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
              <span className="tag" style={{ fontSize: 9 }}>{selectedIdea.domain}</span>
              {selectedIdea.category && <span className="tag" style={{ fontSize: 9 }}>{selectedIdea.category}</span>}
              {selectedIdea.medium && <span className="tag" style={{ fontSize: 9 }}>{selectedIdea.medium}</span>}
              {selectedIdea.story_type && <span className="tag" style={{ fontSize: 9 }}>{selectedIdea.story_type}</span>}
              <span className="proj-status" style={{
                fontSize: 9, padding: '1px 8px',
                borderColor: selectedIdea.status === 'promoted' ? '#3dffa0' : '#ffb830',
                color: selectedIdea.status === 'promoted' ? '#3dffa0' : '#ffb830'
              }}>{selectedIdea.status}</span>
            </div>

            {/* Tags */}
            {selectedIdea.tags && (Array.isArray(selectedIdea.tags) ? selectedIdea.tags : []).length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Tags</div>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {(Array.isArray(selectedIdea.tags) ? selectedIdea.tags : []).map((t, i) => (
                    <span key={i} className="tag" style={{ fontSize: 8 }}>{t}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Description */}
            {selectedIdea.description && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Description</div>
                <div style={{ fontSize: 11, color: '#b0b8d0', lineHeight: 1.5 }}>{selectedIdea.description}</div>
              </div>
            )}

            {/* Context / notes */}
            {selectedIdea.context && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Context</div>
                <div style={{ fontSize: 10, color: '#7a8299', fontStyle: 'italic', lineHeight: 1.5 }}>{selectedIdea.context}</div>
              </div>
            )}

            {/* Link */}
            {selectedIdea.link && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Source</div>
                <a href={selectedIdea.link} target="_blank" rel="noopener"
                  style={{ color: '#4a9eff', fontSize: 10 }}>{selectedIdea.link.slice(0, 60)}...</a>
              </div>
            )}

            {/* Document Content */}
            {selectedIdea.content && !_isImageFile(selectedIdea.file_path) && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>
                  {selectedIdea.file_path ? '📄 Document' : '📝 Content'}
                </div>
                {selectedIdea.file_path && (
                  <div style={{ fontSize: 8, color: '#5a6279', fontFamily: '"Share Tech Mono", monospace', marginBottom: 6 }}>
                    {selectedIdea.file_path}
                  </div>
                )}
                <div style={{
                  background: '#0a0a10', border: '1px solid #1e2338', borderRadius: 6,
                  padding: 12, maxHeight: 300, overflow: 'auto',
                  fontSize: 11, color: '#d0d4e0', lineHeight: 1.6,
                  fontFamily: '"Georgia", serif', whiteSpace: 'pre-wrap',
                }}>
                  {selectedIdea.content}
                </div>
              </div>
            )}

            {/* Scanned image preview */}
            {selectedIdea.file_path && _isImageFile(selectedIdea.file_path) && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 1 }}>🖼️ Scanned Image</div>
                <img
                  src={`/api/archive-file?path=${encodeURIComponent(selectedIdea.file_path)}`}
                  alt={selectedIdea.name}
                  style={{
                    width: '100%', maxHeight: 400, objectFit: 'contain',
                    borderRadius: 6, border: '1px solid #1e2338',
                    background: '#000',
                  }}
                  onError={(e) => { e.target.style.display = 'none' }}
                />
                {selectedIdea.content && (
                  <details style={{ marginTop: 8 }}>
                    <summary style={{ fontSize: 9, color: '#7a8299', cursor: 'pointer', fontFamily: '"Share Tech Mono", monospace' }}>
                      📝 OCR Transcription
                    </summary>
                    <div style={{
                      marginTop: 6, background: '#0a0a10', border: '1px solid #1e2338', borderRadius: 6,
                      padding: 12, maxHeight: 200, overflow: 'auto',
                      fontSize: 11, color: '#d0d4e0', lineHeight: 1.6,
                      fontFamily: '"Georgia", serif', whiteSpace: 'pre-wrap',
                    }}>
                      {selectedIdea.content}
                    </div>
                  </details>
                )}
                <div style={{ fontSize: 8, color: '#5a6279', fontFamily: '"Share Tech Mono", monospace', marginTop: 4 }}>
                  {selectedIdea.file_path}
                </div>
              </div>
            )}

            {/* File path without content */}
            {selectedIdea.file_path && !selectedIdea.content && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>📎 Attached File</div>
                <div style={{ fontSize: 10, color: '#4a9eff', fontFamily: '"Share Tech Mono", monospace' }}>
                  {selectedIdea.file_path}
                </div>
              </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', gap: 6, marginTop: 16, flexWrap: 'wrap' }}>
              {selectedIdea.status !== 'promoted' && (
                <button className="btn" onClick={() => handlePromote(selectedIdea)}
                  style={{ borderColor: '#4a9eff', color: '#4a9eff', fontSize: 10 }}>
                  Promote to Project →
                </button>
              )}
            </div>

            {/* Metadata */}
            <div style={{ marginTop: 16, fontFamily: '"Share Tech Mono", monospace', fontSize: 8, color: '#5a6279', lineHeight: 1.8 }}>
              <div>ID: {selectedIdea.id}</div>
              <div>Created: {new Date(selectedIdea.created).toLocaleString()}</div>
              {selectedIdea.date && <div>Date: {selectedIdea.date}</div>}
              <div>Level: {selectedIdea.user_level}</div>
            </div>
          </div>
        )}
      </div>

      {/* ── New Idea overlay (slides in from right) ───────────── */}
      {showForm && (
        <div style={{
          position: 'fixed', top: 0, right: 0, width: 420, height: '100%',
          background: '#12141e', borderLeft: '1px solid #fff', zIndex: 9999,
          display: 'flex', flexDirection: 'column',
          boxShadow: '-4px 0 20px rgba(0,0,0,0.5)',
        }}>
          {/* Header */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '14px 16px', borderBottom: '1px solid #1e2338',
          }}>
            <span style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 700, fontSize: 16, flex: 1 }}>
              + New Idea
            </span>
            <button className="btn" onClick={() => setShowForm(false)}
              style={{ fontSize: 10, padding: '3px 10px' }}>✕ Close</button>
          </div>

          {/* Form body — scrollable */}
          <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <input className="cis-input" type="text" placeholder="Idea name / working title" required
                value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              <input className="cis-input" type="url" placeholder="Source link (optional)"
                value={form.link} onChange={e => setForm(f => ({ ...f, link: e.target.value }))} />
              <input className="cis-input" type="date"
                value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
              <textarea className="cis-textarea" placeholder="What's the concept?" style={{ minHeight: 70 }}
                value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              <textarea className="cis-textarea" placeholder="Context — where did this come from?" style={{ minHeight: 50 }}
                value={form.context} onChange={e => setForm(f => ({ ...f, context: e.target.value }))} />

              {/* Document content */}
              <div style={{ border: '1px solid #1e2338', borderRadius: 6, padding: 8 }}>
                <div style={{ fontSize: 8, color: '#7a8299', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Document Content</div>
                <textarea className="cis-textarea" placeholder="Paste the full document text here..."
                  style={{ minHeight: 120, fontSize: 11, fontFamily: '"Georgia", serif', lineHeight: 1.6 }}
                  value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} />
                <input className="cis-input" type="text" placeholder="File path (optional)"
                  style={{ fontSize: 9, marginTop: 4, fontFamily: '"Share Tech Mono", monospace' }}
                  value={form.file_path} onChange={e => setForm(f => ({ ...f, file_path: e.target.value }))} />
              </div>

              <select className="cis-select" value={form.domain}
                onChange={e => setForm(f => ({ ...f, domain: e.target.value, category: '', medium: '' }))}>
                {Object.entries(DOMAIN_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <select className="cis-select" value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
                <option value="">Category — select</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <select className="cis-select" value={form.medium}
                onChange={e => setForm(f => ({ ...f, medium: e.target.value }))}>
                <option value="">Medium / Type — select</option>
                {media.map(m => <option key={m} value={m}>{m}</option>)}
              </select>

              <input className="cis-input" placeholder="Tags (comma-separated)"
                value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))} />

              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-blue" type="submit">+ Capture Idea</button>
                <button className="btn" type="button" onClick={() => {
                  setForm({ name: '', link: '', date: '', description: '', context: '', domain: 'creative', category: '', medium: '', story_type: '', user_level: 'beginner', tags: '', content: '', file_path: '' })
                }}>Clear</button>
              </div>
              {statusMsg && <div style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: '#3dffa0' }}>{statusMsg}</div>}
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
