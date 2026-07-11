import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from './api.js'

export default function PipelineLive({ runId, onRunIdChange }) {
  const [feed, setFeed] = useState(null)
  const [input, setInput] = useState('')
  const [interjections, setInterjections] = useState([])
  const [collapsed, setCollapsed] = useState({})
  const [error, setError] = useState(null)
  const [manualRunId, setManualRunId] = useState('')
  const scrollRef = useRef(null)

  // Poll feed
  useEffect(() => {
    if (!runId) return
    let active = true

    const poll = async () => {
      try {
        const data = await api.getFeed(runId)
        if (active) {
          setFeed(data)
          setError(null)
          if (data.interjections) setInterjections(data.interjections)
        }
      } catch (e) {
        if (active) setError(e.message)
      }
    }

    poll()
    const iv = setInterval(poll, 2000)
    return () => {
      active = false
      clearInterval(iv)
    }
  }, [runId])

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [feed])

  const sendInterjection = useCallback(async () => {
    if (!input.trim() || !runId) return
    const msg = input.trim()
    setInput('')
    try {
      await api.interject(runId, msg)
      setInterjections((prev) => [
        ...prev,
        { message: msg, created_at: new Date().toISOString(), consumed_by_phase: null },
      ])
    } catch (e) {
      setError(e.message)
    }
  }, [input, runId])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendInterjection()
    }
  }

  const toggleCollapse = (idx) => {
    setCollapsed((prev) => ({ ...prev, [idx]: !prev[idx] }))
  }

  const loadManualRun = () => {
    if (manualRunId.trim()) {
      onRunIdChange(manualRunId.trim())
      setManualRunId('')
    }
  }

  // Group gates by phase
  const gatesByPhase = (gates || []).reduce((acc, g) => {
    const key = `${g.phase}/${g.role}`
    if (!acc[key]) acc[key] = []
    acc[key].push(g)
    return acc
  }, {})

  if (!runId) {
    return (
      <div className="pipeline-view">
        <div className="pipeline-feed" style={{ textAlign: 'center', paddingTop: '60px' }}>
          <p style={{ fontSize: '16px', marginBottom: '12px' }}>
            No active pipeline run
          </p>
          <p style={{ color: 'var(--text-dim)', marginBottom: '20px' }}>
            Start a conversation with Brain, or enter a run ID to observe
          </p>
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <input
              className="chat-input"
              style={{ width: '320px' }}
              value={manualRunId}
              onChange={(e) => setManualRunId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadManualRun()}
              placeholder="run-id..."
            />
            <button className="chat-send" onClick={loadManualRun}>Load</button>
          </div>
        </div>
      </div>
    )
  }

  const phases = feed?.phases || []
  const isActive = feed?.background?.active
  const status = feed?.status || ''
  const result = feed?.result || ''

  return (
    <div className="pipeline-view">
      <div className="pipeline-header">
        <div className="pipeline-status">
          <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{runId}</span>
          <span className={`status-badge ${isActive ? 'running' : result === 'CONSENSUS_REACHED' ? 'done' : 'error'}`}>
            {isActive ? 'RUNNING' : status}
          </span>
          {result && result !== status && (
            <span style={{ marginLeft: '8px', color: 'var(--text-dim)' }}>
              → {result}
            </span>
          )}
          <div style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-dim)' }}>
            {feed?.topic ? feed.topic.slice(0, 120) + '...' : ''}
          </div>
        </div>
      </div>

      <div className="pipeline-feed" ref={scrollRef}>
        {error && (
          <div style={{ color: 'var(--error)', fontSize: '13px', marginBottom: '12px' }}>
            Error: {error}
          </div>
        )}

        {phases.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', marginTop: '40px' }}>
            <p>Waiting for pipeline to start...</p>
          </div>
        )}

        {phases.map((phase, idx) => {
          const gateKey = `${phase.phase}/review1`
          const phaseGates = gatesByPhase[gateKey] || gatesByPhase[`${phase.phase}/brain`] || gatesByPhase[`${phase.phase}/draft`] || gatesByPhase[`${phase.phase}/menter`] || gatesByPhase[`${phase.phase}/verify`] || []
          const isCollapsed = collapsed[idx] !== false // default expanded
          const phaseDrift = (feed?.drift || []).find(d => d.phase === phase.phase)

          return (
            <div key={idx} className="phase-card">
              <div
                className="phase-header"
                onClick={() => toggleCollapse(idx)}
              >
                <span className="phase-name">{phase.phase}</span>
                <span style={{ color: 'var(--text-dim)', fontSize: '12px' }}>
                  round {phase.round}
                </span>
                {phase.signal && (
                  <span className={`phase-signal ${phase.signal}`}>
                    {phase.signal}
                  </span>
                )}
                {phaseDrift && (
                  <span style={{
                    fontSize: '11px',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    background: phaseDrift.verdict === 'ALIGNED' ? 'var(--accent-dim)' :
                               phaseDrift.verdict === 'MINOR_DRIFT' ? '#f0883e22' :
                               phaseDrift.verdict === 'SIGNIFICANT_DRIFT' ? '#f0883e33' :
                               '#f8514922',
                    color: phaseDrift.verdict === 'ALIGNED' ? 'var(--accent)' :
                           phaseDrift.verdict === 'MINOR_DRIFT' ? 'var(--warn)' :
                           phaseDrift.verdict === 'SIGNIFICANT_DRIFT' ? 'var(--warn)' :
                           'var(--error)',
                  }}>
                    drift {phaseDrift.drift_score?.toFixed(2)} ({phaseDrift.verdict})
                  </span>
                )}
                <span className="phase-time">
                  {phase.created_at ? new Date(phase.created_at).toLocaleTimeString() : ''}
                </span>
              </div>

              <div className={`phase-body ${isCollapsed ? 'collapsed' : ''}`}>
                {phase.brain_output && (
                  <>
                    <div className="phase-output-label">BRAIN OUTPUT</div>
                    {phase.brain_output}
                  </>
                )}
                {phase.drafter_output && (
                  <>
                    <div className="phase-output-label">DRAFTER OUTPUT</div>
                    {phase.drafter_output}
                  </>
                )}
                {phase.reviewer1_output && (
                  <>
                    <div className="phase-output-label">REVIEWER 1</div>
                    {phase.reviewer1_output}
                  </>
                )}
                {phase.reviewer2_output && (
                  <>
                    <div className="phase-output-label">REVIEWER 2</div>
                    {phase.reviewer2_output}
                  </>
                )}
                {phase.verify_output && (
                  <>
                    <div className="phase-output-label">VERIFY</div>
                    {phase.verify_output}
                  </>
                )}
                {phase.human_question && (
                  <>
                    <div className="phase-output-label" style={{ color: 'var(--warn)' }}>
                      HUMAN QUESTION — ANSWER NEEDED
                    </div>
                    {phase.human_question}
                  </>
                )}
              </div>

              {phaseGates.length > 0 && (
                <div className="gate-results">
                  {phaseGates.map((g, gi) => (
                    <div key={gi} className="gate-row">
                      <span className={`gate-verdict ${g.verdict}`}>{g.verdict}</span>
                      <span className="gate-name">{g.guardrail_name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Interjection history */}
      {interjections.length > 0 && (
        <div className="interjection-list">
          {interjections.map((ij, i) => (
            <div key={i} className="interjection-msg">
              → {ij.message}
              {ij.consumed_by_phase && (
                <span className="consumed">consumed by {ij.consumed_by_phase}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Backchannel input — always available, never blocks */}
      <div className="interjection-box">
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Interject a thought (backchannel — doesn't stop the pipeline)..."
          disabled={!runId}
        />
        <button
          className="chat-send"
          onClick={sendInterjection}
          disabled={!input.trim() || !runId}
          style={{ background: 'var(--warn)' }}
        >
          Interject
        </button>
      </div>
    </div>
  )
}
