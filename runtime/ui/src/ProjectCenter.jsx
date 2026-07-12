// CIS Control Panel — Project Center
// The project-centered view: shows build plan, recent runs, decisions, stats
// Entry point for working through the pipeline instead of terminal.
import { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'

export default function ProjectCenter({ onPipelineStarted, onSelectRun }) {
  const [project, setProject] = useState(null)
  const [overview, setOverview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [intent, setIntent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [expandedNode, setExpandedNode] = useState(null)
  const [showAllRuns, setShowAllRuns] = useState(false)

  const fetchOverview = useCallback(async () => {
    try {
      const data = await api.getProjectOverview('cis')
      setOverview(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchOverview()
    const iv = setInterval(fetchOverview, 10000)
    return () => clearInterval(iv)
  }, [fetchOverview])

  const startWork = async () => {
    if (!intent.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const result = await api.startPipeline(intent.trim())
      if (result.run_id) {
        setIntent('')
        if (onPipelineStarted) onPipelineStarted(result.run_id)
      } else {
        setError(result.error || 'Failed to start pipeline')
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <div className="project-view"><p className="loading-text">Loading project...</p></div>
  }

  const stats = overview?.stats || {}
  const buildStats = overview?.build_plan_stats || {}
  const buildPlan = overview?.build_plan || []
  const runs = overview?.recent_runs || []
  const decisions = overview?.decisions || []
  const blockers = overview?.active_blockers || []
  const devPivots = overview?.dev_pivots || []
  const closeoutStats = overview?.closeout_stats || {}
  const visibleRuns = showAllRuns ? runs : runs.slice(0, 5)

  return (
    <div className="project-view">
      {/* Project Header */}
      <div className="project-header">
        <div className="project-title">
          <h2>CIS — Creative Intelligence System</h2>
          <span className="project-id">project: cis</span>
        </div>
        <div className="project-stats-bar">
          <div className="stat-item">
            <span className="stat-num">{buildStats.complete || 0}/{buildStats.total || 0}</span>
            <span className="stat-label">Build Nodes</span>
          </div>
          <div className="stat-item">
            <span className="stat-num">{stats.total_runs || 0}</span>
            <span className="stat-label">Total Runs</span>
          </div>
          <div className="stat-item">
            <span className="stat-num" style={{ color: 'var(--accent)' }}>{stats.consensus_reached || 0}</span>
            <span className="stat-label">Consensus</span>
          </div>
          <div className="stat-item">
            <span className="stat-num" style={{ color: 'var(--warn)' }}>{stats.escalated || 0}</span>
            <span className="stat-label">Escalated</span>
          </div>
          <div className="stat-item">
            <span className="stat-num" style={{ color: 'var(--error)' }}>{stats.at_eric_gate || 0}</span>
            <span className="stat-label">At Gate</span>
          </div>
          {closeoutStats.total > 0 && (
            <div className="stat-item">
              <span className="stat-num">{closeoutStats.passed || 0}/{closeoutStats.total}</span>
              <span className="stat-label">Closeouts</span>
            </div>
          )}
        </div>
      </div>

      {error && <div className="action-msg error">{error}</div>}

      {/* Active Blockers */}
      {blockers.length > 0 && (
        <div className="project-section">
          <div className="section-header">ACTIVE BLOCKERS</div>
          {blockers.map((b, i) => (
            <div key={i} className="blocker-item">
              <span className="blocker-id">{b.blocker_id}</span>
              <span className="blocker-title">{b.title}</span>
              <span className="blocker-status">{b.status}</span>
            </div>
          ))}
        </div>
      )}

      {/* Start Work */}
      <div className="project-section">
        <div className="section-header">START NEW WORK</div>
        <div className="intent-input">
          <textarea
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            placeholder="Describe what you want the pipeline to build..."
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) startWork()
            }}
          />
          <button
            className="action-btn primary"
            onClick={startWork}
            disabled={submitting || !intent.trim()}
          >
            {submitting ? 'Starting...' : 'Start Pipeline'}
          </button>
          <span className="hint-text">Cmd+Enter to submit</span>
        </div>
      </div>

      {/* Build Plan Progress */}
      {buildPlan.length > 0 && (
        <div className="project-section">
          <div className="section-header">
            BUILD PLAN PROGRESS
            <span className="section-detail">
              {buildStats.complete} complete · {buildStats.deferred} deferred · {buildStats.pending} pending
            </span>
          </div>
          <div className="build-plan-list">
            {buildPlan.map((node, i) => (
              <div
                key={i}
                className={`build-node ${node.status.toLowerCase()}`}
                onClick={() => setExpandedNode(expandedNode === i ? null : i)}
              >
                <div className="build-node-header">
                  <span className={`node-status-dot ${node.status.toLowerCase()}`}></span>
                  <span className="node-tier">{node.tier}</span>
                  <span className="node-label">{node.node_label}</span>
                  <span className="node-status-text">{node.status}</span>
                </div>
                {expandedNode === i && node.blocked_reason && (
                  <div className="node-detail">{node.blocked_reason}</div>
                )}
                {expandedNode === i && node.commit_hash && (
                  <div className="node-detail">Commit: {node.commit_hash}</div>
                )}
                {expandedNode === i && node.completed_at && (
                  <div className="node-detail">Completed: {node.completed_at}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Runs */}
      {runs.length > 0 && (
        <div className="project-section">
          <div className="section-header">
            RECENT PIPELINE RUNS
            {runs.length > 5 && (
              <button className="link-btn" onClick={() => setShowAllRuns(!showAllRuns)}>
                {showAllRuns ? 'Show less' : `Show all (${runs.length})`}
              </button>
            )}
          </div>
          <div className="runs-list">
            {visibleRuns.map((run, i) => (
              <div
                key={i}
                className="run-item"
                onClick={() => onSelectRun && onSelectRun(run.id)}
              >
                <span className={`run-status-dot ${(run.status || '').toLowerCase()}`}></span>
                <span className="run-topic">{run.topic}</span>
                <span className={`run-status-badge ${(run.status || '').toLowerCase()}`}>{run.status}</span>
                <span className="run-time">{run.created_at ? new Date(run.created_at).toLocaleString() : ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Architecture Decisions — Governance Era (June 7-19) */}
      {decisions.length > 0 && (
        <div className="project-section">
          <div className="section-header">
            GOVERNANCE-ERA ADRs
            <span className="section-detail">Historical — June 7-19, pre-break</span>
          </div>
          <div className="decisions-list">
            {decisions.map((d, i) => (
              <div key={i} className="decision-item">
                <span className="decision-label">{d.label}</span>
                <span className="decision-text">{d.decision}</span>
                <span className="decision-status">{d.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dev Pivots — Real Governance Tracking */}
      {devPivots.length > 0 && (
        <div className="project-section">
          <div className="section-header">
            DEV PIVOTS — REAL STATUS
            <span className="section-detail">
              {devPivots.filter(p => p.status === 'LIVE').length} live ·
              {' '}{devPivots.filter(p => p.status === 'INVALIDATED').length} invalidated ·
              {' '}{devPivots.filter(p => p.status === 'PARTIALLY_INVALIDATED').length} partial
            </span>
          </div>
          <div className="decisions-list">
            {devPivots.map((p, i) => (
              <div key={i} className={`decision-item pivot-${p.status.toLowerCase()}`}>
                <span className="decision-label">{p.doc_id}</span>
                <span className="decision-text">{p.title}</span>
                <span className={`decision-status pivot-status-${p.status.toLowerCase()}`}>{p.status}</span>
                {p.invalidation_reason && (
                  <div className="node-detail">{p.invalidation_reason}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
