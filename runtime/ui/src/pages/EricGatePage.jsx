import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../api'

export default function EricGatePage() {
  const [gateData, setGateData] = useState(null)
  const [decisions, setDecisions] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadData = useCallback(async () => {
    try {
      const [gate, decs] = await Promise.all([
        api.ericGate().catch(e => ({ error: e.message })),
        api.decisions().catch(e => ({ error: e.message })),
      ])
      setGateData(gate)
      setDecisions(decs)
      setError(null)
    } catch (e) {
      setError('Failed to load: ' + e.message)
    }
  }, [])

  useEffect(() => {
    loadData().finally(() => setLoading(false))
  }, [loadData])

  if (loading) {
    return <div style={{ padding: 20, color: '#7a8299' }}>Loading Eric Gate data...</div>
  }

  return (
    <div style={{ padding: 20, overflowY: 'auto', height: '100%' }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <h1 style={{
        fontFamily: '"Share Tech Mono", monospace',
        fontSize: 16,
        color: '#ffd93d',
        marginBottom: 16,
        borderBottom: '1px solid #1a1a2e',
        paddingBottom: 8,
      }}>
        ▸ Eric Gate
      </h1>

      {error && (
        <div style={{ color: '#ff3d3d', fontSize: 11, marginBottom: 12 }}>{error}</div>
      )}

      {/* ── Pending Approvals ───────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{
          fontFamily: '"Share Tech Mono", monospace',
          fontSize: 13,
          color: '#a0b0d0',
          marginBottom: 8,
        }}>
          Pending Approvals
        </h2>

        {gateData && gateData.approvals ? (
          gateData.approvals.length > 0 ? (
            <div>
              {gateData.approvals.map((approval, i) => (
                <div key={i} style={{
                  background: '#0e0e1a',
                  border: '1px solid #1a1a2e',
                  borderRadius: 4,
                  padding: '10px 14px',
                  marginBottom: 8,
                  fontSize: 11,
                  fontFamily: '"Share Tech Mono", monospace',
                }}>
                  <div style={{ color: '#a0b0d0', marginBottom: 4 }}>
                    <span style={{ color: '#ffd93d' }}>{approval.run_id || approval.id || 'Unknown Run'}</span>
                    {approval.decision && (
                      <span style={{
                        marginLeft: 8,
                        padding: '1px 6px',
                        borderRadius: 2,
                        fontSize: 9,
                        fontWeight: 700,
                        background: approval.decision === 'APPROVE' ? '#0a3d1a' : '#3d1a0a',
                        color: approval.decision === 'APPROVE' ? '#3dffa0' : '#ff3d3d',
                        textTransform: 'uppercase',
                      }}>
                        {approval.decision}
                      </span>
                    )}
                  </div>
                  <div style={{ color: '#606a80', fontSize: 10 }}>
                    Status: {approval.status || 'pending'} | Created: {approval.created_at || '—'}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#7a8299', fontSize: 11 }}>No pending approvals.</div>
          )
        ) : (
          <div style={{ color: '#7a8299', fontSize: 11 }}>No approval data available.</div>
        )}
      </div>

      {/* ── Open Decisions ───────────────────────────────────────────────── */}
      <div>
        <h2 style={{
          fontFamily: '"Share Tech Mono", monospace',
          fontSize: 13,
          color: '#a0b0d0',
          marginBottom: 8,
        }}>
          Open Decisions
        </h2>

        {decisions && decisions.decisions ? (
          decisions.decisions.length > 0 ? (
            <div>
              {decisions.decisions.map((decision, i) => (
                <div key={i} style={{
                  background: '#0e0e1a',
                  border: '1px solid #1a1a2e',
                  borderRadius: 4,
                  padding: '10px 14px',
                  marginBottom: 8,
                  fontSize: 11,
                  fontFamily: '"Share Tech Mono", monospace',
                }}>
                  <div style={{ color: '#a0b0d0', marginBottom: 4 }}>
                    <span style={{ color: '#3dffa0' }}>{decision.decision_id || decision.id || '—'}</span>
                    {' — '}
                    <span>{decision.label || decision.title || 'Untitled'}</span>
                  </div>
                  <div style={{ color: '#606a80', fontSize: 10 }}>
                    Status: {decision.status || 'unknown'}
                    {decision.superseded_by && (
                      <span style={{ color: '#ffd93d', marginLeft: 8 }}>
                        ← Superseded by: {decision.superseded_by}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: '#7a8299', fontSize: 11 }}>No open decisions.</div>
          )
        ) : (
          <div style={{ color: '#7a8299', fontSize: 11 }}>No decision data available.</div>
        )}
      </div>
    </div>
  )
}
