import React, { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../api'

const PHASE_LABELS = {
  INTAKE: 'Intake',
  BRAIN_PHASE: 'Brain',
  INTENT_REVIEW: 'Intent Review',
  DRAFT_PHASE: 'Draft',
  PROPOSAL_REVIEW: 'Proposal Review',
  ERIC_GATE: 'Eric Gate',
  PATTERN_CATALOG: 'Pattern Catalog',
  CODE_REVIEW_GATE: 'Code Review Gate',
  EXECUTION: 'Execution',
  VERIFICATION: 'Verification',
  CONSENSUS_REACHED: 'Complete',
  ESCALATED: 'Escalated',
  ERROR: 'Error',
  VERIFY_FAILED: 'Verify Failed',
}

const PHASE_ORDER = [
  'INTAKE', 'BRAIN_PHASE', 'INTENT_REVIEW', 'DRAFT_PHASE',
  'PROPOSAL_REVIEW', 'ERIC_GATE', 'PATTERN_CATALOG',
  'CODE_REVIEW_GATE', 'EXECUTION', 'VERIFICATION', 'CONSENSUS_REACHED',
]

const STATUS_COLORS = {
  ERIC_GATE: '#ffd93d',
  CONSENSUS_REACHED: '#3dffa0',
  ESCALATED: '#ff3d3d',
  ERROR: '#ff3d3d',
  VERIFY_FAILED: '#ff6b3d',
}

export default function RelayPage() {
  const [intent, setIntent] = useState('')
  const [runId, setRunId] = useState(null)
  const [runData, setRunData] = useState(null)
  const [runHistory, setRunHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [gateRationale, setGateRationale] = useState('')
  const [gateSubmitting, setGateSubmitting] = useState(false)
  const [expandedRound, setExpandedRound] = useState(null)
  const [showHistory, setShowHistory] = useState(false)
  const pollRef = useRef(null)

  // Load run history on mount
  useEffect(() => {
    api.relayListRuns(20).then(data => {
      setRunHistory(data.runs || [])
    }).catch(() => {})
  }, [])

  // Poll for run status
  const startPolling = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const data = await api.relayStatus(id)
        setRunData(data)
        // Stop polling when run reaches terminal state
        if (['CONSENSUS_REACHED', 'ESCALATED', 'ERROR', 'VERIFY_FAILED'].includes(data.status)) {
          clearInterval(pollRef.current)
          pollRef.current = null
        }
      } catch (e) {
        // keep polling on error
      }
    }, 2000)
  }, [])

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current)
  }, [])

  const handleSubmit = async () => {
    if (!intent.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.relayStart(intent.trim())
      if (result.error) {
        setError(result.error)
      } else {
        setRunId(result.run_id)
        setRunData(result)
        startPolling(result.run_id)
        // refresh history
        api.relayListRuns(20).then(data => setRunHistory(data.runs || [])).catch(() => {})
      }
    } catch (e) {
      setError(e.message)
    }
    setLoading(false)
  }

  const handleGate = async (decision) => {
    if (!runId) return
    setGateSubmitting(true)
    try {
      await api.relayGate(runId, decision, gateRationale)
      setGateRationale('')
      // immediately refresh status
      const data = await api.relayStatus(runId)
      setRunData(data)
      if (!['CONSENSUS_REACHED', 'ESCALATED', 'ERROR', 'VERIFY_FAILED'].includes(data.status)) {
        startPolling(runId)
      }
    } catch (e) {
      setError(e.message)
    }
    setGateSubmitting(false)
  }

  const loadRun = async (id) => {
    setRunId(id)
    setShowHistory(false)
    try {
      const data = await api.relayStatus(id)
      setRunData(data)
      if (!['CONSENSUS_REACHED', 'ESCALATED', 'ERROR', 'VERIFY_FAILED'].includes(data.status)) {
        startPolling(id)
      }
    } catch (e) {
      setError(e.message)
    }
  }

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768

  // ── Styles ──────────────────────────────────────────────────────────
  const s = {
    container: {
      display: 'flex',
      flexDirection: isMobile ? 'column' : 'row',
      height: '100%',
      gap: 0,
    },
    leftPane: {
      width: isMobile ? '100%' : '380px',
      minWidth: isMobile ? 'auto' : '380px',
      borderRight: isMobile ? 'none' : '1px solid #1a1a2e',
      borderBottom: isMobile ? '1px solid #1a1a2e' : 'none',
      display: 'flex',
      flexDirection: 'column',
      padding: 16,
      overflowY: 'auto',
    },
    rightPane: {
      flex: 1,
      padding: 16,
      overflowY: 'auto',
    },
    header: {
      fontFamily: '"Share Tech Mono", monospace',
      fontSize: 16,
      color: '#ffd93d',
      marginBottom: 16,
      borderBottom: '1px solid #1a1a2e',
      paddingBottom: 8,
    },
    label: {
      fontFamily: '"Share Tech Mono", monospace',
      fontSize: 11,
      color: '#7a8299',
      marginBottom: 6,
      textTransform: 'uppercase',
      letterSpacing: 0.5,
    },
    textarea: {
      width: '100%',
      minHeight: 120,
      background: '#0e0e1a',
      border: '1px solid #1a1a2e',
      borderRadius: 4,
      padding: '10px 12px',
      color: '#a0b0d0',
      fontFamily: '"Share Tech Mono", monospace',
      fontSize: 12,
      resize: 'vertical',
      outline: 'none',
    },
    btn: {
      background: '#1a3d1a',
      border: '1px solid #2a5d2a',
      borderRadius: 4,
      padding: '8px 16px',
      color: '#3dffa0',
      fontFamily: '"Share Tech Mono", monospace',
      fontSize: 12,
      cursor: 'pointer',
      textTransform: 'uppercase',
    },
    btnGate: {
      flex: 1,
      padding: '10px 8px',
      border: '1px solid',
      borderRadius: 4,
      fontFamily: '"Share Tech Mono", monospace',
      fontSize: 12,
      cursor: 'pointer',
      textTransform: 'uppercase',
      fontWeight: 700,
      textAlign: 'center',
      minWidth: isMobile ? '100%' : 'auto',
    },
    card: {
      background: '#0e0e1a',
      border: '1px solid #1a1a2e',
      borderRadius: 4,
      padding: '12px 14px',
      marginBottom: 10,
      fontSize: 11,
      fontFamily: '"Share Tech Mono", monospace',
    },
    phaseBar: {
      display: 'flex',
      gap: 2,
      marginBottom: 12,
      flexWrap: 'wrap',
    },
    phaseDot: {
      flex: 1,
      minWidth: 60,
      height: 4,
      borderRadius: 2,
      background: '#1a1a2e',
    },
    roundSection: {
      background: '#0e0e1a',
      border: '1px solid #1a1a2e',
      borderRadius: 4,
      marginBottom: 8,
      overflow: 'hidden',
    },
    roundHeader: {
      padding: '8px 12px',
      cursor: 'pointer',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontSize: 11,
      fontFamily: '"Share Tech Mono", monospace',
      color: '#a0b0d0',
    },
    roundBody: {
      padding: '12px 14px',
      borderTop: '1px solid #1a1a2e',
      fontSize: 11,
      fontFamily: '"Share Tech Mono", monospace',
      color: '#7a8299',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word',
      maxHeight: 400,
      overflowY: 'auto',
    },
    runHistoryItem: {
      padding: '8px 12px',
      cursor: 'pointer',
      borderBottom: '1px solid #1a1a2e',
      fontSize: 11,
      fontFamily: '"Share Tech Mono", monospace',
      color: '#7a8299',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
  }

  // ── Render ──────────────────────────────────────────────────────────
  return (
    <div style={{ padding: 20, height: '100%', overflowY: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h1 style={s.header}>▸ Relay Control Plane</h1>
        <button
          onClick={() => setShowHistory(!showHistory)}
          style={{ ...s.btn, background: '#0e0e1a', color: '#a0b0d0', border: '1px solid #1a1a2e' }}
        >
          {showHistory ? 'Hide' : 'History'} ({runHistory.length})
        </button>
      </div>

      {error && (
        <div style={{ color: '#ff3d3d', fontSize: 11, marginBottom: 12, fontFamily: '"Share Tech Mono", monospace' }}>
          ⚠ {error}
        </div>
      )}

      {showHistory ? (
        <div style={s.card}>
          <div style={s.label}>Run History</div>
          {runHistory.length === 0 ? (
            <div style={{ color: '#7a8299', fontSize: 11 }}>No runs yet.</div>
          ) : (
            runHistory.map((r, i) => (
              <div
                key={i}
                style={s.runHistoryItem}
                onClick={() => loadRun(r.id)}
              >
                <span style={{ color: STATUS_COLORS[r.status] || '#a0b0d0' }}>
                  {r.id.substring(0, 20)}...
                </span>
                <span style={{ color: STATUS_COLORS[r.status] || '#7a8299' }}>
                  {r.status}
                </span>
              </div>
            ))
          )}
        </div>
      ) : (
        <div style={s.container}>
          {/* ── Left Pane: Intent + Run Info ── */}
          <div style={s.leftPane}>
            <div style={s.label}>Submit Intent</div>
            <textarea
              style={s.textarea}
              value={intent}
              onChange={e => setIntent(e.target.value)}
              placeholder="Describe what you want to build..."
              disabled={loading}
            />
            <button
              style={{ ...s.btn, marginTop: 8, opacity: loading || !intent.trim() ? 0.5 : 1 }}
              onClick={handleSubmit}
              disabled={loading || !intent.trim()}
            >
              {loading ? 'Starting...' : '▶ Start Run'}
            </button>

            {runData && (
              <div style={{ marginTop: 16 }}>
                <div style={s.label}>Current Run</div>
                <div style={s.card}>
                  <div style={{ color: '#ffd93d', marginBottom: 4 }}>
                    {runData.run_id ? runData.run_id.substring(0, 25) + '...' : '—'}
                  </div>
                  <div style={{ color: STATUS_COLORS[runData.status] || '#a0b0d0', fontWeight: 700 }}>
                    {PHASE_LABELS[runData.status] || runData.status}
                  </div>
                  {runData.rounds_completed != null && (
                    <div style={{ color: '#7a8299', marginTop: 4 }}>
                      Rounds: {runData.rounds_completed}
                    </div>
                  )}
                </div>

                {/* Phase progress bar */}
                <div style={s.phaseBar}>
                  {PHASE_ORDER.map((phase, i) => {
                    const currentIdx = PHASE_ORDER.indexOf(runData.status)
                    const isActive = i === currentIdx
                    const isPast = i < currentIdx
                    return (
                      <div
                        key={phase}
                        style={{
                          ...s.phaseDot,
                          background: isActive ? '#ffd93d' : isPast ? '#2a5d2a' : '#1a1a2e',
                        }}
                        title={PHASE_LABELS[phase]}
                      />
                    )
                  })}
                </div>

                {/* Human question */}
                {runData.human_question && (
                  <div style={{ ...s.card, borderColor: '#ffd93d' }}>
                    <div style={{ color: '#ffd93d', marginBottom: 8 }}>❓ Question for Eric</div>
                    <div style={{ color: '#a0b0d0', marginBottom: 8 }}>{runData.human_question}</div>
                    <input
                      style={{ ...s.textarea, minHeight: 40 }}
                      placeholder="Your answer..."
                      onKeyDown={async (e) => {
                        if (e.key === 'Enter' && runId) {
                          await api.relayAnswer(runId, e.target.value)
                          e.target.value = ''
                        }
                      }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── Right Pane: Live Run View + Eric Gate ── */}
          <div style={s.rightPane}>
            {!runData ? (
              <div style={{ color: '#7a8299', fontSize: 12, fontFamily: '"Share Tech Mono", monospace' }}>
                Submit an intent to start a pipeline run. Live status will appear here.
              </div>
            ) : (
              <>
                {/* Eric Gate Panel */}
                {runData.status === 'ERIC_GATE' && (
                  <div style={{
                    ...s.card,
                    borderColor: '#ffd93d',
                    background: '#1a1a0e',
                    marginBottom: 16,
                  }}>
                    <div style={{ color: '#ffd93d', fontSize: 13, marginBottom: 12 }}>
                      ⬢ ERIC GATE — Decision Required
                    </div>

                    {/* Show latest Brain output */}
                    {runData.brain_output && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={s.label}>Brain Analysis</div>
                        <div style={{
                          ...s.roundBody,
                          maxHeight: 200,
                          background: '#0e0e1a',
                          border: '1px solid #1a1a2e',
                          borderRadius: 4,
                          padding: 10,
                        }}>
                          {runData.brain_output.substring(0, 2000)}
                          {runData.brain_output.length > 2000 ? '...' : ''}
                        </div>
                      </div>
                    )}

                    {/* Show latest reviewer outputs */}
                    {runData.reviewer1_output && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={s.label}>Reviewer 1</div>
                        <div style={{
                          ...s.roundBody,
                          maxHeight: 200,
                          background: '#0e0e1a',
                          border: '1px solid #1a1a2e',
                          borderRadius: 4,
                          padding: 10,
                        }}>
                          {runData.reviewer1_output.substring(0, 2000)}
                          {runData.reviewer1_output.length > 2000 ? '...' : ''}
                        </div>
                      </div>
                    )}
                    {runData.reviewer2_output && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={s.label}>Reviewer 2</div>
                        <div style={{
                          ...s.roundBody,
                          maxHeight: 200,
                          background: '#0e0e1a',
                          border: '1px solid #1a1a2e',
                          borderRadius: 4,
                          padding: 10,
                        }}>
                          {runData.reviewer2_output.substring(0, 2000)}
                          {runData.reviewer2_output.length > 2000 ? '...' : ''}
                        </div>
                      </div>
                    )}

                    {/* Rationale input */}
                    <div style={s.label} style={{ ...s.label, marginTop: 12 }}>Rationale (optional)</div>
                    <textarea
                      style={{ ...s.textarea, minHeight: 60 }}
                      value={gateRationale}
                      onChange={e => setGateRationale(e.target.value)}
                      placeholder="Reason for your decision..."
                      disabled={gateSubmitting}
                    />

                    {/* Gate buttons — full-width on mobile, inline on desktop */}
                    <div style={{
                      display: 'flex',
                      gap: 8,
                      marginTop: 12,
                      flexDirection: isMobile ? 'column' : 'row',
                    }}>
                      <button
                        style={{ ...s.btnGate, background: '#0a3d1a', borderColor: '#2a5d2a', color: '#3dffa0' }}
                        onClick={() => handleGate('APPROVE')}
                        disabled={gateSubmitting}
                      >
                        ✓ Approve
                      </button>
                      <button
                        style={{ ...s.btnGate, background: '#3d1a0a', borderColor: '#5d2a2a', color: '#ff3d3d' }}
                        onClick={() => handleGate('REJECT')}
                        disabled={gateSubmitting}
                      >
                        ✗ Reject
                      </button>
                      <button
                        style={{ ...s.btnGate, background: '#3d3d0a', borderColor: '#5d5d2a', color: '#ffd93d' }}
                        onClick={() => handleGate('REVISE')}
                        disabled={gateSubmitting}
                      >
                        ↻ Refine
                      </button>
                    </div>
                  </div>
                )}

                {/* Deliberation Rounds */}
                {runData.rounds && runData.rounds.length > 0 && (
                  <div>
                    <div style={s.label}>Deliberation Rounds</div>
                    {runData.rounds.map((round, i) => (
                      <div key={i} style={s.roundSection}>
                        <div
                          style={s.roundHeader}
                          onClick={() => setExpandedRound(expandedRound === i ? null : i)}
                        >
                          <span>
                            <span style={{ color: '#ffd93d' }}>Round {round.round_number}</span>
                            <span style={{ color: '#7a8299', marginLeft: 8 }}>{round.phase}</span>
                          </span>
                          <span style={{ color: STATUS_COLORS[round.signal] || '#7a8299' }}>
                            {round.signal}
                          </span>
                        </div>
                        {expandedRound === i && (
                          <div style={s.roundBody}>
                            {round.drafter_output && (
                              <div style={{ marginBottom: 12 }}>
                                <div style={{ color: '#a0b0d0', marginBottom: 4 }}>Drafter:</div>
                                <div style={{ color: '#7a8299' }}>
                                  {round.drafter_output.substring(0, 4000)}
                                  {round.drafter_output.length > 4000 ? '...' : ''}
                                </div>
                              </div>
                            )}
                            {round.reviewer1_output && (
                              <div style={{ marginBottom: 12 }}>
                                <div style={{ color: '#a0b0d0', marginBottom: 4 }}>Reviewer 1:</div>
                                <div style={{ color: '#7a8299' }}>
                                  {round.reviewer1_output.substring(0, 4000)}
                                  {round.reviewer1_output.length > 4000 ? '...' : ''}
                                </div>
                              </div>
                            )}
                            {round.reviewer2_output && (
                              <div style={{ marginBottom: 12 }}>
                                <div style={{ color: '#a0b0d0', marginBottom: 4 }}>Reviewer 2:</div>
                                <div style={{ color: '#7a8299' }}>
                                  {round.reviewer2_output.substring(0, 4000)}
                                  {round.reviewer2_output.length > 4000 ? '...' : ''}
                                </div>
                              </div>
                            )}
                            {round.brain_output && (
                              <div style={{ marginBottom: 12 }}>
                                <div style={{ color: '#a0b0d0', marginBottom: 4 }}>Brain:</div>
                                <div style={{ color: '#7a8299' }}>
                                  {round.brain_output.substring(0, 4000)}
                                  {round.brain_output.length > 4000 ? '...' : ''}
                                </div>
                              </div>
                            )}
                            {round.menter_output && (
                              <div style={{ marginBottom: 12 }}>
                                <div style={{ color: '#a0b0d0', marginBottom: 4 }}>Menter:</div>
                                <div style={{ color: '#7a8299' }}>
                                  {round.menter_output.substring(0, 4000)}
                                  {round.menter_output.length > 4000 ? '...' : ''}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Background error */}
                {runData.background && runData.background.error && (
                  <div style={{ ...s.card, borderColor: '#ff3d3d', color: '#ff3d3d' }}>
                    ⚠ Pipeline error: {runData.background.error}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
