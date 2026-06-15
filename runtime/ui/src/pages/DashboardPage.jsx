import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // 11B: Eric Gate approval state
  const [approveRunId, setApproveRunId] = useState('')
  const [approveRationale, setApproveRationale] = useState('')
  const [approveResult, setApproveResult] = useState(null)
  const [approving, setApproving] = useState(false)

  useEffect(() => {
    api.dashboardFull()
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const handleApprove = () => {
    if (!approveRunId.trim()) return
    setApproving(true)
    setApproveResult(null)
    api.approveRun(approveRunId.trim(), approveRationale.trim())
      .then(r => { setApproveResult(r); setApproving(false) })
      .catch(e => { setApproveResult({ status: 'error', error: e.message }); setApproving(false) })
  }

  if (loading) return <div className="empty-state">Loading dashboard...</div>
  if (error) return <div className="empty-state" style={{ color: 'var(--red)' }}>Dashboard error: {error}</div>
  if (!data) return <div className="empty-state">No dashboard data available.</div>

  const { phase, blockers, runs, capabilities, overview_areas, quick_links } = data

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto', padding: '20px 24px' }}>
      {/* Header */}
      <div style={{ marginBottom: 18 }}>
        <div className="hdr-title">Dashboard</div>
        <div className="hdr-sub" style={{ color: 'var(--green)', fontFamily: '"Share Tech Mono", monospace', fontSize: 10 }}>
          {phase.build_phase || 'CIS Operational'}
        </div>
      </div>

      {/* Row 1: Phase + Next Action */}
      <div className="row" style={{ marginBottom: 16 }}>
        <div className="col">
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title">Current Phase</div>
            <div style={{ fontSize: 14, color: 'var(--t1)', fontFamily: 'var(--cond)', fontWeight: 600, marginBottom: 6 }}>
              {phase.next_tier || 'N/A'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--t3)', lineHeight: 1.4 }}>
              {phase.next_action || 'No pending action'}
            </div>
          </div>
        </div>
        <div className="col">
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-title">Active Blockers</div>
            {blockers && blockers.length > 0 ? (
              blockers.map(b => (
                <div key={b.id} style={{ fontSize: 11, color: 'var(--amber)', padding: '4px 0', borderBottom: '1px solid #1a1f2e' }}>
                  <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: 'var(--red)', marginRight: 6 }}>{b.id}</span>
                  {b.description}
                </div>
              ))
            ) : (
              <div style={{ fontSize: 11, color: 'var(--green)' }}>No active blockers</div>
            )}
          </div>
        </div>
      </div>

      {/* 11B: Eric Gate Approval */}
      <div className="card" style={{ marginBottom: 20, borderColor: 'rgba(61,255,160,0.3)' }}>
        <div className="card-title" style={{ color: 'var(--green)' }}>Eric Gate — Approve</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div className="field-row" style={{ flex: 1, minWidth: 200 }}>
            <span className="field-label">Run ID</span>
            <input
              className="cis-input"
              value={approveRunId}
              onChange={e => setApproveRunId(e.target.value)}
              placeholder="run-88032ce506724"
              style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 11 }}
            />
          </div>
          <div className="field-row" style={{ flex: 1, minWidth: 200 }}>
            <span className="field-label">Rationale (optional)</span>
            <input
              className="cis-input"
              value={approveRationale}
              onChange={e => setApproveRationale(e.target.value)}
              placeholder="Spec looks good, pass to Reviewer"
              style={{ fontSize: 11 }}
            />
          </div>
          <button
            className="btn btn-green"
            onClick={handleApprove}
            disabled={approving || !approveRunId.trim()}
            style={{ height: 38, padding: '0 24px', marginBottom: 8 }}
          >
            {approving ? 'Recording...' : 'APPROVE'}
          </button>
        </div>

        {approveResult && (
          <div style={{
            marginTop: 10, padding: '8px 12px', borderRadius: 4,
            border: '1px solid',
            borderColor: approveResult.status === 'approved' ? 'rgba(61,255,160,0.4)'
              : approveResult.status === 'already_approved' ? 'rgba(255,184,48,0.4)'
              : 'rgba(255,74,106,0.4)',
            background: approveResult.status === 'approved' ? 'rgba(61,255,160,0.06)'
              : approveResult.status === 'already_approved' ? 'rgba(255,184,48,0.06)'
              : 'rgba(255,74,106,0.06)',
          }}>
            <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 10, color: approveResult.status === 'approved' || approveResult.status === 'already_approved' ? 'var(--green)' : 'var(--red)' }}>
              [{approveResult.status}]
            </span>{' '}
            <span style={{ fontSize: 11, color: 'var(--t2)' }}>
              {approveResult.error || approveResult.message || `Approval ${approveResult.approval_id} recorded.`}
            </span>
          </div>
        )}
      </div>

      {/* Row 2: Recent Runs */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-title">Recent Pipeline Runs</div>
        {runs && runs.length > 0 ? (
          runs.map(r => (
            <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '6px 0', borderBottom: '1px solid #1a1f2e', fontSize: 11 }}>
              <span style={{
                fontFamily: '"Share Tech Mono", monospace', fontSize: 9, fontWeight: 700,
                color: r.result === 'CONSENSUS_REACHED' ? 'var(--green)' : r.result === 'ESCALATE' ? 'var(--amber)' : r.result === 'ERROR' ? 'var(--red)' : 'var(--t3)',
                minWidth: 140
              }}>
                {r.result || r.status}
              </span>
              <span style={{ flex: 1, color: 'var(--t2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {r.topic || r.id}
              </span>
              <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: 'var(--t3)', whiteSpace: 'nowrap' }}>
                {r.rounds_completed} rounds
              </span>
            </div>
          ))
        ) : (
          <div style={{ fontSize: 11, color: 'var(--t3)' }}>No pipeline runs recorded</div>
        )}
      </div>

      {/* Quick Links */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-title">Quick Links</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {quick_links && quick_links.map(link => (
            <a key={link.path} href={link.path}
              onClick={e => { e.preventDefault(); window.history.pushState({}, '', link.path); window.dispatchEvent(new Event('popstate')) }}
              className="btn"
              style={{ fontSize: 11, textDecoration: 'none' }}>
              {link.label}
            </a>
          ))}
        </div>
      </div>

      {/* Completed Capabilities */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-title">Completed Capabilities ({capabilities ? capabilities.length : 0})</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
          {capabilities && capabilities.map(c => (
            <div key={c.node_label} style={{
              padding: '10px 12px', border: '1px solid #1a1f2e', borderRadius: 6,
              background: 'var(--bg-surface)', fontSize: 11
            }}>
              <div style={{ fontFamily: 'var(--cond)', fontWeight: 600, fontSize: 12, color: 'var(--t1)', marginBottom: 4 }}>
                {c.node_label}
              </div>
              {c.operator_description && (
                <div style={{ color: 'var(--t3)', lineHeight: 1.4 }}>
                  {c.operator_description}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* System Overview by Area */}
      {overview_areas && Object.keys(overview_areas).length > 0 && (
        <div className="card">
          <div className="card-title">System Overview</div>
          {Object.entries(overview_areas).map(([area, items]) => (
            <div key={area} style={{ marginBottom: 16 }}>
              <div style={{
                fontFamily: 'var(--cond)', fontSize: 13, fontWeight: 700, color: 'var(--blue)',
                borderBottom: '1px solid #1a1f2e', paddingBottom: 4, marginBottom: 8
              }}>
                {area}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 6 }}>
                {items.map(item => (
                  <div key={item.node_label} style={{
                    padding: '8px 10px', border: '1px solid #1a1f2e', borderRadius: 4,
                    background: 'var(--bg-surface)', fontSize: 11, color: 'var(--t2)', lineHeight: 1.4
                  }}>
                    <span style={{ fontFamily: 'var(--cond)', fontWeight: 600, color: 'var(--t3)', fontSize: 10, display: 'block', marginBottom: 2 }}>
                      {item.node_label}
                    </span>
                    {item.description}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
