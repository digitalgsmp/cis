import React, { useState, useRef, useEffect } from 'react'
import { flushSync } from 'react-dom'

const COLLAB = '/api/collab'

async function postJSON(path, body = {}) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`)
  return data
}

async function createRound(topic) {
  return postJSON(`${COLLAB}/rounds`, { topic, round_type: 'chat', eric_context: topic, current_concern: '', desired_outcome: '' })
}

function ReviewBlock({ label, modelName, loading, review, error, onAsk }) {
  return (
    <div style={{ marginTop: 10, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
      {!review && !loading && !error && (
        <button
          onClick={onAsk}
          style={{
            background: 'var(--bg-raised)',
            color: 'var(--blue)',
            border: '1px solid var(--border)',
            padding: '4px 12px',
            fontFamily: 'var(--mono)',
            fontSize: 10,
            cursor: 'pointer',
            borderRadius: 3,
          }}
        >
          Ask {label}
        </button>
      )}
      {loading && (
        <span style={{ color: 'var(--amber)', fontFamily: 'var(--mono)', fontSize: 10 }}>
          {modelName} thinking...
        </span>
      )}
      {error && (
        <div style={{ color: 'var(--red)', fontFamily: 'var(--mono)', fontSize: 10 }}>{error}</div>
      )}
      {review && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', padding: 12, borderRadius: 4 }}>
          <div style={{ fontFamily: 'var(--cond)', fontSize: 10, color: 'var(--blue)', letterSpacing: '.1em', marginBottom: 6, textTransform: 'uppercase' }}>
            {modelName}
          </div>
          <pre style={{
            fontFamily: 'var(--sans)',
            fontSize: 12,
            color: 'var(--t2)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: 1.5,
            margin: 0,
          }}>
            {review}
          </pre>
        </div>
      )}
    </div>
  )
}

export default function ChatConsole() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [roundId, setRoundId] = useState(null)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setSending(true)

    const userMsg = { role: 'user', content: text, ts: Date.now() }
    setMessages(prev => [...prev, userMsg])

    try {
      // Create or reuse round
      let rid = roundId
      if (!rid) {
        const created = await createRound(text)
        rid = created.id
        setRoundId(rid)
      }

      // Add a placeholder message for streaming
      const streamTs = Date.now()
      const placeholder = {
        role: 'v4',
        content: '▊ thinking...',
        ts: streamTs,
        roundId: rid,
        streaming: true,
        qwenReview: null, qwenLoading: false, qwenError: null,
        r1Review: null, r1Loading: false, r1Error: null,
      }
      setMessages(prev => [...prev, placeholder])

      // Stream from Hermes
      const response = await fetch(`${COLLAB}/rounds/${rid}/send-to-hermes-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulated = ''
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          const dataStr = trimmed.slice(6)
          try {
            const event = JSON.parse(dataStr)
            if (event.status === 'thinking') {
              // Keep showing thinking indicator
              setMessages(prev => prev.map(m =>
                m.ts === streamTs ? { ...m, content: '▊ thinking...' } : m
              ))
            } else if (event.delta) {
              accumulated += event.delta
              flushSync(() => {
                setMessages(prev => prev.map(m =>
                  m.ts === streamTs ? { ...m, content: accumulated } : m
                ))
              })
              // Yield to browser for paint — ensures visible word-by-word streaming
              await new Promise(r => setTimeout(r, 10))
            } else if (event.done) {
              flushSync(() => {
                setMessages(prev => prev.map(m =>
                  m.ts === streamTs ? { ...m, content: accumulated || '(no response)', streaming: false } : m
                ))
              })
            } else if (event.error) {
              flushSync(() => {
                setMessages(prev => prev.map(m =>
                  m.ts === streamTs ? { ...m, content: `Error: ${event.error}`, streaming: false, role: 'error' } : m
                ))
              })
            }
          } catch (parseErr) {
            // Skip malformed SSE lines
          }
        }
      }

      // If stream ended without a done event, finalize
      setMessages(prev => prev.map(m =>
        m.ts === streamTs && m.streaming ? { ...m, content: accumulated || '(no response)', streaming: false } : m
      ))

    } catch (e) {
      setMessages(prev => prev.map(m =>
        m.streaming ? { ...m, content: `Error: ${e.message}`, streaming: false, role: 'error' } : m
      ))
      if (!messages.find(m => m.role === 'error' && m.content.includes(e.message))) {
        setMessages(prev => [...prev, { role: 'error', content: e.message, ts: Date.now() }])
      }
    } finally {
      setSending(false)
    }
  }

  const askReviewer = async (idx, reviewer) => {
    const msg = messages[idx]
    if (!msg || !msg.roundId) return

    const loadingKey = reviewer === 'qwen' ? 'qwenLoading' : 'r1Loading'
    const reviewKey = reviewer === 'qwen' ? 'qwenReview' : 'r1Review'
    const errorKey = reviewer === 'qwen' ? 'qwenError' : 'r1Error'
    const endpoint = reviewer === 'qwen' ? 'send-to-reviewer' : 'send-to-r1'

    setMessages(prev => prev.map((m, i) => i === idx ? { ...m, [loadingKey]: true, [errorKey]: null } : m))

    try {
      const res = await postJSON(`${COLLAB}/rounds/${msg.roundId}/${endpoint}`)
      const reviewText = res.review || '(empty review)'
      setMessages(prev => prev.map((m, i) => i === idx ? { ...m, [reviewKey]: reviewText, [loadingKey]: false } : m))
    } catch (e) {
      setMessages(prev => prev.map((m, i) => i === idx ? { ...m, [errorKey]: e.message, [loadingKey]: false } : m))
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: 'var(--bg-base)', overflow: 'hidden',
    }}>
      <style>{`@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }`}</style>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
        background: 'var(--bg-surface)', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0,
      }}>
        <span style={{ fontFamily: 'var(--cond)', fontSize: 12, fontWeight: 800, letterSpacing: '.2em', color: 'var(--blue)', textTransform: 'uppercase' }}>
          Chat Console
        </span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--t3)' }}>
          V4 worker &bull; [Ask Qwen] [Ask R1] on any response
        </span>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 16px 0' }}>
        {messages.length === 0 && (
          <div style={{ color: 'var(--t3)', fontFamily: 'var(--mono)', fontSize: 11, textAlign: 'center', marginTop: 40 }}>
            Ask DeepSeek V4 anything. Click <span style={{ color: 'var(--blue)' }}>Ask Qwen</span> or{' '}
            <span style={{ color: 'var(--green)' }}>Ask R1</span> on any response to get a second opinion.
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={msg.ts} style={{ marginBottom: 20 }}>
            {/* Role label */}
            <div style={{
              fontFamily: 'var(--cond)', fontSize: 10, fontWeight: 700, letterSpacing: '.15em',
              color: msg.role === 'user' ? 'var(--green)' : msg.role === 'error' ? 'var(--red)' : 'var(--blue)',
              textTransform: 'uppercase', marginBottom: 4,
            }}>
              {msg.role === 'user' ? 'You' : msg.role === 'v4' ? 'DeepSeek V4' : msg.role === 'error' ? 'Error' : msg.role}
            </div>

            {/* Content */}
            <div style={{
              background: msg.role === 'user' ? 'var(--bg-surface)' : 'var(--bg-raised)',
              border: '1px solid var(--border)',
              borderRadius: 4,
              padding: 12,
            }}>
              <pre style={{
                fontFamily: 'var(--sans)', fontSize: 12, color: 'var(--t2)',
                whiteSpace: 'pre-wrap', wordBreak: 'break-word', lineHeight: 1.6, margin: 0,
              }}>
                {msg.content}
                {msg.streaming && <span style={{ animation: 'pulse 1s infinite', color: 'var(--blue)' }}>▌</span>}
              </pre>
            </div>

            {/* Reviewer buttons for V4 responses */}
            {msg.role === 'v4' && (
              <>
                <ReviewBlock
                  label="Qwen"
                  modelName="Qwen 30B Reviewer"
                  loading={msg.qwenLoading}
                  review={msg.qwenReview}
                  error={msg.qwenError}
                  onAsk={() => askReviewer(idx, 'qwen')}
                />
                <ReviewBlock
                  label="R1"
                  modelName="DeepSeek R1"
                  loading={msg.r1Loading}
                  review={msg.r1Review}
                  error={msg.r1Error}
                  onAsk={() => askReviewer(idx, 'r1')}
                />
              </>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '12px 16px', borderTop: '1px solid var(--border)',
        background: 'var(--bg-surface)', flexShrink: 0, display: 'flex', gap: 10,
      }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask DeepSeek V4..."
          disabled={sending}
          rows={2}
          style={{
            flex: 1,
            background: 'var(--bg-base)',
            color: 'var(--t1)',
            border: '1px solid var(--border)',
            borderRadius: 4,
            padding: '8px 12px',
            fontFamily: 'var(--sans)',
            fontSize: 12,
            resize: 'none',
            outline: 'none',
          }}
        />
        <button
          onClick={send}
          disabled={sending || !input.trim()}
          style={{
            background: sending ? 'var(--bg-raised)' : 'var(--blue)',
            color: sending ? 'var(--t3)' : 'var(--bg-base)',
            border: '1px solid var(--border)',
            padding: '8px 20px',
            fontFamily: 'var(--cond)',
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: '.1em',
            textTransform: 'uppercase',
            cursor: sending ? 'default' : 'pointer',
            borderRadius: 4,
            alignSelf: 'flex-end',
          }}
        >
          {sending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
