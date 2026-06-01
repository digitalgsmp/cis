import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

// ── Dictation hook ──────────────────────────────────────────────
function useDictation({ onResult, language = 'en-US' }) {
  const [listening, setListening] = useState(false)
  const [supported, setSupported] = useState(true)
  const recognitionRef = useRef(null)

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setSupported(false)
      return
    }
    const rec = new SpeechRecognition()
    rec.continuous = true
    rec.interimResults = true
    rec.lang = language

    rec.onresult = (event) => {
      let transcript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript
      }
      if (onResult) onResult(transcript, event.results[event.results.length - 1].isFinal)
    }

    rec.onerror = (event) => {
      console.warn('Dictation error:', event.error)
      setListening(false)
    }

    rec.onend = () => {
      setListening(false)
    }

    recognitionRef.current = rec
    return () => { try { rec.abort() } catch {} }
  }, [language])

  const start = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start()
        setListening(true)
      } catch (e) {
        console.warn('Dictation start failed:', e)
      }
    }
  }, [])

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      setListening(false)
    }
  }, [])

  const toggle = useCallback(() => {
    if (listening) stop()
    else start()
  }, [listening, start, stop])

  return { listening, supported, start, stop, toggle }
}

// ── Props ───────────────────────────────────────────────────────
// idea: the full idea object from the API
// onBack: () => void — return to ideas list
// onSave: (idea, updates) => void — persist changes

export default function IdeaWorkbench({ idea, onBack, onSave }) {
  const navigate = useNavigate()
  const [content, setContent] = useState(idea.content || '')
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showMeta, setShowMeta] = useState(false)
  const [showImageOverlay, setShowImageOverlay] = useState(false)
  const [editingMeta, setEditingMeta] = useState(false)
  const [metaForm, setMetaForm] = useState({
    name: idea.name, tags: Array.isArray(idea.tags) ? idea.tags.join(', ') : (idea.tags || ''),
    domain: idea.domain || 'creative', category: idea.category || '',
    medium: idea.medium || '', description: idea.description || '',
    context: idea.context || '', status: idea.status || 'captured',
  })
  const imageRef = useRef(null)
  const [cropMode, setCropMode] = useState(false)
  const [croppedImage, setCroppedImage] = useState(null)

  const isImage = idea.file_path && /\.(jpg|jpeg|png|gif|webp|bmp)$/i.test(idea.file_path)

  // ── Mobile detection for responsive layout ──────────────────
  const [isMobile, setIsMobile] = useState(window.innerWidth < 900)
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 900)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  // ── Dictation ────────────────────────────────────────────────
  const onDictationResult = useCallback((transcript, isFinal) => {
    if (isFinal) {
      setContent(prev => (prev ? prev + ' ' : '') + transcript.trim())
      setDirty(true)
    } else {
      // Show interim results in a ghost span — simple approach: just append
      setContent(prev => {
        // If the last line is an interim, replace it
        const lines = prev.split('\n')
        if (lines.length > 0 && lines[lines.length - 1].startsWith('...')) {
          lines[lines.length - 1] = '...' + transcript
          return lines.join('\n')
        }
        return prev + '...' + transcript
      })
      setDirty(true)
    }
  }, [])

  const dictation = useDictation({ onResult: onDictationResult })

  // ── Crop ──────────────────────────────────────────────────────
  // Simple native canvas-based crop: draw a selection rectangle by dragging.
  const [cropRect, setCropRect] = useState(null) // { x, y, w, h } in raw image pixel coords
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState(null)
  const cropContainerRef = useRef(null)
  const cropImageRef = useRef(null)

  // Get the raw image pixel coordinates from a mouse event
  const getRawCoords = useCallback((e) => {
    const img = cropImageRef.current
    if (!img) return { x: 0, y: 0 }
    const rect = img.getBoundingClientRect()
    const scaleX = img.naturalWidth / (rect.width || 1)
    const scaleY = img.naturalHeight / (rect.height || 1)
    return {
      x: Math.max(0, Math.min((e.clientX - rect.left) * scaleX, img.naturalWidth)),
      y: Math.max(0, Math.min((e.clientY - rect.top) * scaleY, img.naturalHeight)),
    }
  }, [])

  const onCropMouseDown = useCallback((e) => {
    const pos = getRawCoords(e)
    setDragStart(pos)
    setIsDragging(true)
    setCropRect(null)
  }, [getRawCoords])

  const onCropMouseMove = useCallback((e) => {
    if (!isDragging || !dragStart) return
    const pos = getRawCoords(e)
    const x = Math.min(dragStart.x, pos.x)
    const y = Math.min(dragStart.y, pos.y)
    const w = Math.abs(pos.x - dragStart.x)
    const h = Math.abs(pos.y - dragStart.y)
    if (w > 2 || h > 2) {
      setCropRect({ x, y, w, h })
    }
  }, [isDragging, dragStart, getRawCoords])

  const onCropMouseUp = useCallback(() => {
    setIsDragging(false)
    setDragStart(null)
  }, [])

  const applyCrop = useCallback(() => {
    if (!cropRect || cropRect.w < 5 || cropRect.h < 5) return
    const img = cropImageRef.current
    if (!img) return
    const canvas = document.createElement('canvas')
    canvas.width = cropRect.w
    canvas.height = cropRect.h
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, cropRect.x, cropRect.y, cropRect.w, cropRect.h, 0, 0, cropRect.w, cropRect.h)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
    setCroppedImage(dataUrl)
    setCropMode(false)
    setCropRect(null)
  }, [cropRect])

  const cancelCrop = useCallback(() => {
    setCropMode(false)
    setCropRect(null)
    setIsDragging(false)
    setDragStart(null)
  }, [])

  // ── Save ─────────────────────────────────────────────────────
  async function handleSave() {
    setSaving(true)
    try {
      const updates = { content, ...metaForm }
      updates.tags = metaForm.tags.split(',').map(t => t.trim()).filter(Boolean)
      await api.updateIdea(idea.id, updates)
      setDirty(false)
      if (onSave) onSave(idea, updates)
    } catch (e) {
      console.error('Save failed:', e)
    }
    setSaving(false)
  }

  function handleBack() {
    if (dirty && !window.confirm('You have unsaved changes. Discard?')) return
    if (onBack) onBack()
  }

  // ── Styles ───────────────────────────────────────────────────
  const S = {
    container: {
      width: '100%', height: '100%', background: '#09090c',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    },
    topbar: {
      height: 40, background: '#101218', borderBottom: '1px solid #1e2338',
      display: 'flex', alignItems: 'center', padding: '0 12px', gap: 10, flexShrink: 0,
    },
    backBtn: {
      padding: '4px 10px', border: '1px solid #4a9eff', borderRadius: 4,
      background: 'transparent', color: '#4a9eff', cursor: 'pointer',
      fontSize: 10, fontFamily: '"Share Tech Mono", monospace',
    },
    main: {
      flex: 1, display: 'flex', overflow: 'hidden',
    },
    sidebar: {
      width: 240, borderRight: '1px solid #1e2338', padding: 12,
      overflow: 'auto', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 8,
    },
    imagePanel: {
      flex: 1, overflow: 'hidden', display: 'flex', alignItems: 'center',
      justifyContent: 'center', padding: 0, background: '#050508',
      borderRight: isMobile ? 'none' : '1px solid #1e2338',
    },
    image: {
      height: '100%', width: 'auto', maxWidth: 'none', cursor: 'pointer',
      objectFit: 'contain', display: 'block',
    },
    editorPanel: {
      flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden',
    },
    editor: {
      flex: 1, width: '100', border: 'none', outline: 'none', resize: 'none',
      background: '#0a0a0e', color: '#d0d4e0', fontSize: 13,
      fontFamily: '"Georgia", serif', lineHeight: 1.7, padding: 16,
    },
    label: {
      fontSize: 8, color: '#7a8299', textTransform: 'uppercase',
      letterSpacing: 1, fontFamily: '"Share Tech Mono", monospace', marginBottom: 2,
    },
    value: {
      fontSize: 10, color: '#b0b8d0', wordBreak: 'break-word',
    },
    micBtn: (active) => ({
      padding: '6px 14px', borderRadius: 6, border: 'none',
      background: active ? '#ff4a6a' : '#1a1d2e',
      color: active ? '#fff' : '#7a8299', cursor: 'pointer',
      fontSize: 16, display: 'flex', alignItems: 'center', gap: 6,
      transition: 'all 0.2s',
    }),
  }

  // ── Mobile layout (stacked) ──────────────────────────────────
  if (isMobile) {
    return (
      <div style={S.container}>
        {/* Top bar */}
        <div style={S.topbar}>
          <button style={S.backBtn} onClick={handleBack}>← Ideas</button>
          <span style={{ fontSize: 10, color: '#b0b8d0', fontFamily: '"Share Tech Mono", monospace', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {idea.name}
          </span>
          {dictation.supported && (
            <button style={S.micBtn(dictation.listening)} onClick={dictation.toggle} title={dictation.listening ? 'Stop dictation' : 'Start dictation'}>
              🎤 {dictation.listening ? 'Listening...' : 'Dictate'}
            </button>
          )}
          <button onClick={() => setShowMeta(true)} style={{ background: 'transparent', border: 'none', color: '#7a8299', cursor: 'pointer', fontSize: 14 }}>⋯</button>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
          {/* Image full width */}
          {isImage && (
            <img
              src={`/api/archive-file?path=${encodeURIComponent(idea.file_path)}`}
              alt={idea.name}
              style={{ width: '100%', height: 'auto', borderRadius: 6, marginBottom: 12, cursor: 'pointer' }}
              onClick={() => setShowImageOverlay(true)}
            />
          )}

          {/* Transcription area */}
          <textarea
            value={content}
            onChange={e => { setContent(e.target.value); setDirty(true) }}
            placeholder="Type or dictate the transcription..."
            style={{ ...S.editor, minHeight: 300, border: '1px solid #1e2338', borderRadius: 6 }}
          />

          {/* Save */}
          <div style={{ display: 'flex', gap: 8, marginTop: 8, paddingBottom: 20 }}>
            <button className="btn btn-blue" onClick={handleSave} disabled={saving}
              style={{ fontSize: 10, padding: '6px 20px' }}>
              {saving ? 'Saving...' : '💾 Save'}
            </button>
          </div>
        </div>

        {/* Meta sheet */}
        {showMeta && (
          <div style={{ position: 'fixed', bottom: 0, left: 0, width: '100%', background: '#12141e', borderTop: '1px solid #1e2338', zIndex: 999, padding: 16, maxHeight: '50vh', overflow: 'auto' }}
            onClick={() => setShowMeta(false)}>
            <div onClick={e => e.stopPropagation()} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontSize: 14, fontWeight: 700, marginBottom: 8 }}>{idea.name}</div>
              <div style={S.label}>File</div>
              <div style={S.value}>{idea.file_path}</div>
              <div style={S.label}>Tags</div>
              <div style={S.value}>{(Array.isArray(idea.tags) ? idea.tags : []).join(', ')}</div>
              <div style={S.label}>Domain / Category / Medium</div>
              <div style={S.value}>{idea.domain} / {idea.category} / {idea.medium}</div>
              <div style={S.label}>Status</div>
              <div style={S.value}>{idea.status}</div>
            </div>
          </div>
        )}

        {/* Image overlay */}
        {showImageOverlay && (
          <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.95)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
            onClick={() => setShowImageOverlay(false)}>
            <img
              src={`/api/archive-file?path=${encodeURIComponent(idea.file_path)}`}
              alt={idea.name}
              style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
            />
          </div>
        )}
      </div>
    )
  }

  // ── Desktop layout (3-column) ────────────────────────────────
  return (
    <div style={S.container}>
      {/* Top bar */}
      <div style={S.topbar}>
        <button style={S.backBtn} onClick={handleBack}>← Ideas</button>
        <span style={{
          fontSize: 10, color: '#b0b8d0', fontWeight: 600,
          fontFamily: '"Share Tech Mono", monospace',
        }}>
          {idea.file_path ? idea.file_path.split('/').pop() : idea.name}
        </span>
        {dirty && <span style={{ fontSize: 8, color: '#ffb830', fontFamily: '"Share Tech Mono", monospace' }}>● unsaved</span>}
        <div style={{ flex: 1 }} />
        {dictation.supported && (
          <button style={S.micBtn(dictation.listening)} onClick={dictation.toggle} title={dictation.listening ? 'Stop dictation' : 'Start dictation'}>
            🎤 {dictation.listening ? 'Listening...' : 'Dictate'}
          </button>
        )}
        <button className="btn btn-blue" onClick={handleSave} disabled={saving}
          style={{ fontSize: 9, padding: '4px 14px' }}>
          {saving ? 'Saving...' : '💾 Save'}
        </button>
        <button onClick={() => setShowMeta(true)} style={{ background: 'transparent', border: '1px solid #7a8299', borderRadius: 4, color: '#7a8299', cursor: 'pointer', fontSize: 10, padding: '4px 8px' }}>
          ⋮ Info
        </button>
      </div>

      {/* Main 3-column */}
      <div style={S.main}>
        {/* Left: file info sidebar */}
        <div style={S.sidebar}>
          <div style={S.label}>Name</div>
          <div style={S.value}>{idea.name}</div>

          {idea.file_path && (
            <>
              <div style={{ ...S.label, marginTop: 4 }}>File</div>
              <div style={{ ...S.value, fontSize: 8, fontFamily: '"Share Tech Mono", monospace' }}>{idea.file_path}</div>
            </>
          )}

          <div style={{ ...S.label, marginTop: 4 }}>Tags</div>
          <div style={S.value}>{(Array.isArray(idea.tags) ? idea.tags : []).join(', ')}</div>

          <div style={{ ...S.label, marginTop: 4 }}>Domain</div>
          <div style={S.value}>{idea.domain}</div>

          <div style={{ ...S.label, marginTop: 4 }}>Category</div>
          <div style={S.value}>{idea.category || '—'}</div>

          <div style={{ ...S.label, marginTop: 4 }}>Medium</div>
          <div style={S.value}>{idea.medium || '—'}</div>

          <div style={{ ...S.label, marginTop: 4 }}>Status</div>
          <div style={{ ...S.value, color: idea.status === 'promoted' ? '#3dffa0' : '#ffb830' }}>{idea.status}</div>

          <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
            {isImage && !cropMode && (
              <button className="btn" onClick={() => setCropMode(true)}
                style={{ fontSize: 9, padding: '4px 10px', textAlign: 'center' }}>
                ✂️ Crop Image
              </button>
            )}
            <button className="btn" onClick={() => setEditingMeta(!editingMeta)}
              style={{ fontSize: 9, padding: '4px 10px', textAlign: 'center' }}>
              ✏️ Edit Metadata
            </button>
            {idea.status !== 'promoted' && (
              <button className="btn" onClick={() => handleSave()}
                style={{ fontSize: 9, padding: '4px 10px', borderColor: '#4a9eff', color: '#4a9eff', textAlign: 'center' }}>
                Promote to Project →
              </button>
            )}
          </div>
        </div>

        {/* Center: image */}
        <div style={S.imagePanel} ref={imageRef}>
          {cropMode ? (
            <div
              ref={cropContainerRef}
              style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', cursor: 'crosshair', background: '#000' }}
              onMouseDown={onCropMouseDown}
              onMouseMove={onCropMouseMove}
              onMouseUp={onCropMouseUp}
              onMouseLeave={onCropMouseUp}
            >
              <img
                ref={cropImageRef}
                src={croppedImage || `/api/archive-file?path=${encodeURIComponent(idea.file_path)}`}
                alt="Crop"
                draggable={false}
                style={{ height: '100%', width: 'auto', display: 'block', margin: '0 auto' }}
                crossOrigin="anonymous"
              />
              {cropRect && (
                <div style={{
                  position: 'absolute',
                  left: cropRect.x, top: cropRect.y,
                  width: cropRect.w, height: cropRect.h,
                  border: '2px solid #4a9eff',
                  background: 'rgba(74, 158, 255, 0.1)',
                  pointerEvents: 'none',
                  zIndex: 5,
                  boxSizing: 'border-box',
                }} />
              )}
              <div style={{ position: 'sticky', bottom: 16, left: '100%', display: 'flex', gap: 8, zIndex: 10, padding: 8 }}>
                <button className="btn btn-blue" onClick={applyCrop} disabled={!cropRect || cropRect.w < 5}
                  style={{ fontSize: 10, padding: '6px 16px' }}>
                  {cropRect && cropRect.w >= 5 ? 'Apply Crop' : 'Drag to select'}
                </button>
                <button className="btn" onClick={cancelCrop} style={{ fontSize: 10, padding: '6px 16px' }}>Cancel</button>
              </div>
            </div>
          ) : isImage ? (
            <img
              src={croppedImage || `/api/archive-file?path=${encodeURIComponent(idea.file_path)}`}
              alt={idea.name}
              style={S.image}
              onClick={() => setShowImageOverlay(true)}
            />
          ) : (
            <div style={{ color: '#5a6279', fontSize: 11, padding: 40, textAlign: 'center' }}>
              No image attached
            </div>
          )}
        </div>

        {/* Right: text editor */}
        <div style={S.editorPanel}>
          <textarea
            value={content}
            onChange={e => { setContent(e.target.value); setDirty(true) }}
            placeholder="Type or dictate the transcription here..."
            style={S.editor}
          />
        </div>
      </div>

      {/* Metadata overlay */}
      {editingMeta && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.85)', zIndex: 9998, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setEditingMeta(false)}>
          <div style={{ background: '#12141e', border: '1px solid #fff', borderRadius: 10, padding: 24, maxWidth: 500, width: '90%', maxHeight: '80vh', overflow: 'auto' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 700, fontSize: 16, marginBottom: 12 }}>Edit Metadata</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <input className="cis-input" value={metaForm.name} onChange={e => setMetaForm(f => ({...f, name: e.target.value}))} placeholder="Name" />
              <input className="cis-input" value={metaForm.tags} onChange={e => setMetaForm(f => ({...f, tags: e.target.value}))} placeholder="Tags (comma-separated)" />
              <select className="cis-select" value={metaForm.domain} onChange={e => setMetaForm(f => ({...f, domain: e.target.value}))}>
                <option value="creative">Creative</option>
                <option value="technical">Technical</option>
                <option value="socialcare">Social Care</option>
                <option value="personal">Personal</option>
                <option value="learning">Learning</option>
              </select>
              <input className="cis-input" value={metaForm.category} onChange={e => setMetaForm(f => ({...f, category: e.target.value}))} placeholder="Category" />
              <input className="cis-input" value={metaForm.medium} onChange={e => setMetaForm(f => ({...f, medium: e.target.value}))} placeholder="Medium" />
              <textarea className="cis-textarea" value={metaForm.description} onChange={e => setMetaForm(f => ({...f, description: e.target.value}))} placeholder="Description" style={{ minHeight: 60 }} />
              <textarea className="cis-textarea" value={metaForm.context} onChange={e => setMetaForm(f => ({...f, context: e.target.value}))} placeholder="Context" style={{ minHeight: 60 }} />
              <select className="cis-select" value={metaForm.status} onChange={e => setMetaForm(f => ({...f, status: e.target.value}))}>
                <option value="captured">Captured</option>
                <option value="promoted">Promoted</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn btn-blue" onClick={() => setEditingMeta(false)} style={{ fontSize: 10 }}>Done</button>
              <button className="btn" onClick={() => setEditingMeta(false)} style={{ fontSize: 10 }}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Full-screen image overlay */}
      {showImageOverlay && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.95)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
          onClick={() => setShowImageOverlay(false)}>
          <img
            src={`/api/archive-file?path=${encodeURIComponent(idea.file_path)}`}
            alt={idea.name}
            style={{ maxWidth: '95%', maxHeight: '95%', objectFit: 'contain' }}
          />
        </div>
      )}

      {/* Info panel overlay */}
      {showMeta && (
        <div style={{ position: 'fixed', top: 0, right: 0, width: 360, height: '100%', background: '#12141e', borderLeft: '1px solid #1e2338', zIndex: 999, padding: 20, overflow: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <span style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 700, fontSize: 14 }}>Idea Info</span>
            <button className="btn" onClick={() => setShowMeta(false)} style={{ fontSize: 10, padding: '3px 8px' }}>✕</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={S.label}>ID</div>
            <div style={S.value}>{idea.id}</div>
            <div style={S.label}>Created</div>
            <div style={S.value}>{idea.created}</div>
            <div style={S.label}>Description</div>
            <div style={S.value}>{idea.description || '—'}</div>
            <div style={S.label}>Context</div>
            <div style={S.value}>{idea.context || '—'}</div>
            <div style={S.label}>Link</div>
            <div style={S.value}>{idea.link || '—'}</div>
            <div style={S.label}>Story Type</div>
            <div style={S.value}>{idea.story_type || '—'}</div>
            <div style={S.label}>User Level</div>
            <div style={S.value}>{idea.user_level || '—'}</div>
          </div>
        </div>
      )}
    </div>
  )
}
