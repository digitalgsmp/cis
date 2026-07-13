// CIS Workbench v0.1 — Split-pane: Brain chat (left) + Construction view (right)
// Phase 1: Shell with working Brain chat + placeholder construction view + breadcrumb
import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from './api.js'

export default function Workbench() {
  // ── State ──────────────────────────────────────────────
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId] = useState(() => 'wb-' + Date.now())
  const [brainThinking, setBrainThinking] = useState(false)
  const [activeRun, setActiveRun] = useState(null)
  const [runStatus, setRunStatus] = useState(null)
  const [breadcrumbs, setBreadcrumbs] = useState([])
  const [backchannel, setBackchannel] = useState('')
  const [interjections, setInterjections] = useState([])
  const [enforcementStatus, setEnforcementStatus] = useState(null)
  const chatScrollRef = useRef(null)

  // ── Brain Chat ─────────────────────────────────────────
  const sendMessage = async () => {
    if (!input.trim() || brainThinking) return
    const msg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setBrainThinking(true)

    try {
      const data = await api.brainChat(msg, sessionId)
      if (data.response) {
        setMessages(prev => [...prev, { role: 'brain', text: data.response, refs: data.references || [] }])
      }
      if (data.run_id) {
        setActiveRun(data.run_id)
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'brain', text: `Error: ${e.message}`, isError: true }])
    } finally {
      setBrainThinking(false)
    }
  }

  // ── Poll active run status ─────────────────────────────
  useEffect(() => {
    if (!activeRun) return
    const poll = async () => {
      try {
        const data = await api.getStatus(activeRun)
        setRunStatus(data)
        // Update breadcrumbs from run data
        if (data.intent) {
          setBreadcrumbs(prev => {
            if (prev.length === 0) {
              return [{ label: 'CIS', type: 'root' }, { label: data.intent.substring(0, 40), type: 'run', runId: activeRun }]
            }
            return prev
          })
        }
      } catch (e) {
        // Run might not be ready yet
      }
    }
    poll()
    const iv = setInterval(poll, 3000)
    return () => clearInterval(iv)
  }, [activeRun])

  // ── Enforcement audit (bottom bar) ─────────────────────
  useEffect(() => {
    const checkEnforcement = async () => {
      try {
        const data = await api.getSecurityAudit()
        setEnforcementStatus(data)
      } catch (e) {}
    }
    checkEnforcement()
    const iv = setInterval(checkEnforcement, 10000)
    return () => clearInterval(iv)
  }, [])

  // ── Backchannel ─────────────────────────────────────────
  const sendInterjection = async () => {
    if (!backchannel.trim() || !activeRun) return
    const msg = backchannel.trim()
    setBackchannel('')
    try {
      await api.interject(activeRun, msg)
      setInterjections(prev => [...prev, { message: msg, timestamp: new Date().toISOString(), consumed: false }])
    } catch (e) {
      setInterjections(prev => [...prev, { message: msg, error: e.message }])
    }
  }

  // ── Auto-scroll chat ────────────────────────────────────
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [messages, brainThinking])

  // ── Render ──────────────────────────────────────────────
  return (
    <div className="workbench-container">
      {/* ── Top Bar: Breadcrumb Trail ─────────────────────── */}
      <div className="workbench-breadcrumb">
        {breadcrumbs.length === 0 ? (
          <span className="breadcrumb-item">CIS</span>
        ) : (
          breadcrumbs.map((bc, i) => (
            <span key={i} className="breadcrumb-group">
              <span className="breadcrumb-item">{bc.label}</span>
              {i < breadcrumbs.length - 1 && <span className="breadcrumb-sep">›</span>}
            </span>
          ))
        )}
      </div>

      {/* ── Split Pane ────────────────────────────────────── */}
      <div className="workbench-split">
        {/* ── LEFT: Brain Chat ─────────────────────────────── */}
        <div className="workbench-left">
          <div className="workbench-panel-header">
            <span className="panel-title">BRAIN</span>
            {brainThinking && <span className="thinking-indicator">searching KB...</span>}
          </div>
          <div className="workbench-chat" ref={chatScrollRef}>
            {messages.length === 0 && (
              <div className="chat-empty">
                <p>Talk to Brain about what you want to build.</p>
                <p className="chat-empty-hint">Brain will search the knowledge base, enrich your intent, and kick off the pipeline when ready.</p>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                <span className="chat-msg-author">{m.role === 'user' ? 'You' : 'Brain'}</span>
                <div className="chat-msg-text">
                  {m.text}
                  {m.refs && m.refs.length > 0 && (
                    <div className="chat-refs">
                      <span className="chat-refs-label">KB References:</span>
                      {m.refs.map((r, j) => (
                        <span key={j} className="chat-ref-tag">{r}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {brainThinking && (
              <div className="chat-msg brain thinking">
                <span className="chat-msg-author">Brain</span>
                <div className="chat-msg-text">
                  <span className="typing-dots">...</span>
                </div>
              </div>
            )}
          </div>
          <div className="workbench-input-bar">
            <input
              type="text"
              className="workbench-input"
              placeholder="Message Brain..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') sendMessage() }}
              disabled={brainThinking}
            />
          </div>
        </div>

        {/* ── RIGHT: Construction View ────────────────────── */}
        <div className="workbench-right">
          <div className="workbench-panel-header">
            <span className="panel-title">CONSTRUCTION</span>
            {runStatus && (
              <span className={`construction-status ${runStatus.status}`}>
                {runStatus.status}
              </span>
            )}
          </div>

          <div className="construction-view">
            {!activeRun && (
              <div className="construction-empty">
                <p className="construction-placeholder-icon">⚙</p>
                <p>Waiting for Brain to dispatch...</p>
                <p className="construction-empty-hint">
                  When you tell Brain to build something, the construction
                  will appear here in real-time.
                </p>
              </div>
            )}

            {activeRun && runStatus && (
              <div className="construction-active">
                {/* Intent */}
                {runStatus.intent && (
                  <div className="construction-intent">
                    <span className="construction-label">Intent:</span>
                    <span className="construction-intent-text">{runStatus.intent}</span>
                  </div>
                )}

                {/* Phase indicators */}
                {runStatus.phases && (
                  <div className="phase-track">
                    {runStatus.phases.map((p, i) => (
                      <div key={i} className={`phase-node ${p.status || 'pending'}`}>
                        <span className="phase-name">{p.name}</span>
                        <span className="phase-state">{p.status || '—'}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Latest output */}
                {runStatus.latest_output && (
                  <div className="construction-output">
                    <div className="construction-output-label">Latest output:</div>
                    <pre className="construction-code">
                      {runStatus.latest_output}
                    </pre>
                  </div>
                )}

                {/* No output yet */}
                {activeRun && !runStatus.latest_output && (
                  <div className="construction-waiting">
                    <span className="typing-dots">Pipeline starting...</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Backchannel (bottom of right panel) ─────────── */}
          {activeRun && (
            <div className="backchannel-bar">
              <div className="backchannel-history">
                {interjections.map((ij, i) => (
                  <div key={i} className={`backchannel-msg ${ij.consumed ? 'consumed' : ''} ${ij.error ? 'error' : ''}`}>
                    <span className="backchannel-text">{ij.message}</span>
                    {ij.consumed && <span className="backchannel-consumed">→ consumed by {ij.consumed_by}</span>}
                    {ij.error && <span className="backchannel-error">{ij.error}</span>}
                  </div>
                ))}
              </div>
              <div className="backchannel-input-bar">
                <input
                  type="text"
                  className="backchannel-input"
                  placeholder="Interject a thought (backchannel — doesn't stop the pipeline)..."
                  value={backchannel}
                  onChange={e => setBackchannel(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') sendInterjection() }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom Bar: Status Strip ──────────────────────── */}
      <div className="workbench-status-strip">
        <span className="status-item">
          {activeRun ? `Run: ${activeRun.substring(0, 20)}...` : 'No active run'}
        </span>
        <span className="status-item">
          {runStatus ? `Phase: ${runStatus.status || '—'}` : 'Idle'}
        </span>
        {enforcementStatus && (
          <span className={`status-enforcement ${enforcementStatus.enforcement_intact ? 'intact' : 'breached'}`}>
            {enforcementStatus.enforcement_intact ? '◆ Enforcement: INTACT' : '✕ Enforcement: BREACHED'}
          </span>
        )}
        <span className="status-item status-time">
          {new Date().toLocaleTimeString()}
        </span>
      </div>
    </div>
  )
}
