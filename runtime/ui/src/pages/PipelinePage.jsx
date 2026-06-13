import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../api'

const STATUS_COLORS = {
  COMPLETE: '#3dffa0',
  IN_PROGRESS: '#3da0ff',
  PENDING: '#ffd93d',
  BLOCKED: '#ff3d3d',
  DEFERRED: '#7a8299',
  PROPOSED: '#a03dff',
}

export default function PipelinePage() {
  const [phase, setPhase] = useState(null)
  const [runs, setRuns] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedRun, setExpandedRun] = useState(null)
  const [runDetail, setRunDetail] = useState(null)

  // ── Load build plan status ─────────────────────────────────────────────
  const loadStatus = useCallback(async () => {
    try {
      const data = await api.pipelineStatus()
      setPhase(data)
      setError(null)
    } catch (e) {
      setError('Failed to load pipeline status: ' + e.message)
    }
  }, [])

  // ── Load recent runs ───────────────────────────────────────────────────
  const loadRuns = useCallback(async () => {
    try {
      const data = await api.pipelineRuns()
      setRuns(data)
    } catch (e) {
      console.error('Failed to load runs:', e)
    }
  }, [])

  useEffect(() => {
    Promise.all([loadStatus(), loadRuns()]).finally(() => setLoading(false))
  }, [loadStatus, loadRuns])

  // ── Expand run detail ──────────────────────────────────────────────────
  const handleExpandRun = async (runId) => {
    if (expandedRun === runId) {
      setExpandedRun(null)
      setRunDetail(null)
      return
    }
    setExpandedRun(runId)
    setRunDetail(null)
    try {
      const data = await api.pipelineRunDetail(runId)
      setRunDetail(data)
    } catch (e) {
      setRunDetail({ error: e.message })
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────
  const statusChip = (status) => (
    <span style={{
      display: 'inline-block',
      padding: '1px 8px',
      borderRadius: 3,
      fontSize: 10,
      fontWeight: 700,
      fontFamily: '"Share Tech Mono", monospace',
      background: STATUS_COLORS[status] || '#7a8299',
      color: '#09090c',
      textTransform: 'uppercase',
    }}>
      {status}
    </span>
  )

  if (loading) {
    return <div style={{ padding: 20, color: '#7a8299' }}>Loading pipeline status...</div>
  }

  return (
    <div style={{ padding: 20, overflowY: 'auto', height: '100%' }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <h1 style={{
        fontFamily: '"Share Tech Mono", monospace',
        fontSize: 16,
        color: '#3dffa0',
        marginBottom: 16,
        borderBottom: '1px solid #1a1a2e',
        paddingBottom: 8,
      }}>
        ▸ Pipeline
      </h1>

      {/* ── Build Plan Status ───────────────────────────────────────────── */}
      {error && (
        <div style={{ color: '#ff3d3d', fontSize: 11, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {phase && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{
            fontFamily: '"Share Tech Mono", monospace',
            fontSize: 13,
            color: '#a0b0d0',
            marginBottom: 8,
          }}>
            Build Plan Status
          </h2>

          {/* Phase summary cards */}
          {phase.current_phase && (
            <div style={{
              background: '#0e0e1a',
              border: '1px solid #1a1a2e',
              borderRadius: 4,
              padding: '12px 16px',
              marginBottom: 12,
              fontSize: 12,
              color: '#7a8299',
            }}>
              <span style={{ color: '#3dffa0', fontFamily: '"Share Tech Mono", monospace' }}>
                Current:
              </span>{' '}
              {phase.current_phase}
            </div>
          )}

          {/* Node table */}
          {phase.nodes && phase.nodes.length > 0 && (
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: 11,
              fontFamily: '"Share Tech Mono", monospace',
              color: '#7a8299',
            }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1a1a2e' }}>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Tier</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Label</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Status</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Completed</th>
                </tr>
              </thead>
              <tbody>
                {phase.nodes.map((node, i) => (
                  <tr key={i} style={{
                    borderBottom: '1px solid #0e0e1a',
                  }}>
                    <td style={{ padding: '4px 8px' }}>{node.tier || '—'}</td>
                    <td style={{ padding: '4px 8px', color: '#a0b0d0' }}>{node.node_label || node.label || '—'}</td>
                    <td style={{ padding: '4px 8px' }}>{statusChip(node.status)}</td>
                    <td style={{ padding: '4px 8px' }}>{node.completed_at || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ── Recent Pipeline Runs ─────────────────────────────────────────── */}
      <div>
        <h2 style={{
          fontFamily: '"Share Tech Mono", monospace',
          fontSize: 13,
          color: '#a0b0d0',
          marginBottom: 8,
        }}>
          Recent Pipeline Runs
        </h2>

        {runs && runs.runs ? (
          runs.runs.length > 0 ? (
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: 11,
              fontFamily: '"Share Tech Mono", monospace',
              color: '#7a8299',
            }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #1a1a2e' }}>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Run ID</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Topic</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Result</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Rounds</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px', color: '#a0b0d0' }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.runs.map((run, i) => (
                  <React.Fragment key={i}>
                    <tr
                      onClick={() => handleExpandRun(run.id || run.run_id)}
                      style={{
                        cursor: 'pointer',
                        borderBottom: '1px solid #0e0e1a',
                        background: expandedRun === (run.id || run.run_id) ? '#1a1a2e' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '4px 8px', color: '#3dffa0' }}>{run.id || run.run_id}</td>
                      <td style={{ padding: '4px 8px', color: '#a0b0d0', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {run.topic || run.title || '—'}
                      </td>
                      <td style={{ padding: '4px 8px' }}>{statusChip(run.result || run.status || 'unknown')}</td>
                      <td style={{ padding: '4px 8px' }}>{run.rounds_completed || '—'}</td>
                      <td style={{ padding: '4px 8px' }}>{run.created_at || '—'}</td>
                    </tr>
                    {expandedRun === (run.id || run.run_id) && (
                      <tr>
                        <td colSpan={5} style={{
                          padding: '8px 12px',
                          background: '#0a0a14',
                          borderBottom: '1px solid #1a1a2e',
                          fontSize: 11,
                          color: '#606a80',
                        }}>
                          {runDetail ? (
                            runDetail.error ? (
                              <span style={{ color: '#ff3d3d' }}>Error: {runDetail.error}</span>
                            ) : (
                              <div>
                                {runDetail.deliberation_rounds && runDetail.deliberation_rounds.length > 0 ? (
                                  <div>
                                    <div style={{ color: '#a0b0d0', marginBottom: 4 }}>
                                      Deliberation Rounds ({runDetail.deliberation_rounds.length}):
                                    </div>
                                    {runDetail.deliberation_rounds.map((round, ri) => (
                                      <div key={ri} style={{
                                        padding: '4px 8px',
                                        marginBottom: 2,
                                        background: '#0e0e1a',
                                        borderRadius: 2,
                                      }}>
                                        Round {round.round_number || ri + 1}
                                        {' — '}
                                        {round.role || '?'}
                                        {': '}
                                        <span style={{ color: '#7a8299' }}>
                                          {(round.summary || '').substring(0, 120)}
                                          {(round.summary || '').length > 120 ? '...' : ''}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div>No deliberation rounds recorded.</div>
                                )}
                              </div>
                            )
                          ) : (
                            <span>Loading detail...</span>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ color: '#7a8299', fontSize: 11 }}>No pipeline runs found.</div>
          )
        ) : (
          <div style={{ color: '#7a8299', fontSize: 11 }}>Loading runs...</div>
        )}
      </div>
    </div>
  )
}
