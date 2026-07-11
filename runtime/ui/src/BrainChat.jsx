import { useState, useRef, useEffect, useCallback } from 'react'
import { api } from './api.js'

export default function BrainChat({ onPipelineStarted }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [ready, setReady] = useState(false)
  const [kbContext, setKbContext] = useState([])
  const [starting, setStarting] = useState(false)
  const scrollRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // Restore session from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('cis_brain_session')
    if (saved) {
      setSessionId(saved)
      api.brainHistory(saved).then((data) => {
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages.map((m) => ({
            role: m.role,
            content: m.content,
          })))
          // Check if any brain message says READY
          const hasReady = data.messages.some(
            (m) => m.role === 'brain' && m.content.includes('READY TO PROCEED')
          )
          if (hasReady) setReady(true)
        }
      }).catch(() => {})
    }
  }, [])

  const send = useCallback(async () => {
    if (!input.trim() || loading) return
    const msg = input.trim()
    setInput('')
    setLoading(true)

    // Add user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: msg }])

    try {
      const resp = await api.brainChat(msg, sessionId)
      if (resp.session_id && !sessionId) {
        setSessionId(resp.session_id)
        localStorage.setItem('cis_brain_session', resp.session_id)
      }
      setMessages((prev) => [
        ...prev,
        { role: 'brain', content: resp.brain_response || '[No response]' },
      ])
      if (resp.kb_context) setKbContext(resp.kb_context)
      if (resp.ready) setReady(true)
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'brain', content: `[Error: ${e.message}]` },
      ])
    } finally {
      setLoading(false)
    }
  }, [input, loading, sessionId])

  const startPipeline = useCallback(async () => {
    if (!sessionId || starting) return
    setStarting(true)
    try {
      const resp = await api.brainStart(sessionId)
      if (resp.run_id) {
        onPipelineStarted(resp.run_id)
        // Reset brain chat state
        setMessages([])
        setSessionId(null)
        setReady(false)
        setKbContext([])
        localStorage.removeItem('cis_brain_session')
      }
    } catch (e) {
      alert(`Failed to start pipeline: ${e.message}`)
    } finally {
      setStarting(false)
    }
  }, [sessionId, starting, onPipelineStarted])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="brain-view">
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', marginTop: '40px' }}>
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>
              Talk to Brain to explore your idea
            </p>
            <p style={{ fontSize: '13px' }}>
              Brain searches the knowledge base and helps shape your intent
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            <div className="msg-label">
              {msg.role === 'user' ? 'Eric' : 'Brain'}
            </div>
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="msg brain">
            <div className="msg-label">Brain</div>
            <span style={{ color: 'var(--text-dim)' }}>thinking...</span>
          </div>
        )}
      </div>

      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Talk to Brain..."
          rows="1"
          disabled={loading}
        />
        <button
          className="chat-send"
          onClick={send}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
        {ready && (
          <button
            className="start-pipeline-btn"
            onClick={startPipeline}
            disabled={starting}
          >
            {starting ? 'Starting...' : 'Start Pipeline →'}
          </button>
        )}
      </div>
    </div>
  )
}
