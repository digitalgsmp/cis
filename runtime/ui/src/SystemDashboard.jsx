// CIS Control Panel v1.3.0 — System Dashboard
// No docker socket access — worker is contained. Shows gateway health, services, gateway logs,
// and deterministic enforcement audit.
import { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'

export default function SystemDashboard() {
  const [gateways, setGateways] = useState([])
  const [services, setServices] = useState([])
  const [security, setSecurity] = useState(null)
  const [logs, setLogs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionMsg, setActionMsg] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchHealth = useCallback(async () => {
    try {
      const [healthData, secData] = await Promise.all([
        api.getSystemHealth(),
        api.getSecurityAudit().catch(() => null),
      ])
      setGateways(healthData.gateways || [])
      setServices(healthData.services || [])
      setSecurity(secData)
    } catch (e) {
      setGateways([])
      setServices([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    if (autoRefresh) {
      const iv = setInterval(fetchHealth, 5000)
      return () => clearInterval(iv)
    }
  }, [fetchHealth, autoRefresh])

  const viewLogs = async (name) => {
    try {
      const data = await api.getContainerLogs(name)
      setLogs({ name, lines: data.lines || [], source: data.source || '' })
    } catch (e) {
      setLogs({ name, lines: [`Error: ${e.message}`], source: '' })
    }
  }

  // Summary counts
  const gatewaysUp = gateways.filter(g => g.healthy).length
  const gatewaysDown = gateways.filter(g => !g.healthy).length
  const servicesUp = services.filter(s => s.healthy).length
  const servicesDown = services.filter(s => !s.healthy).length
  const secPassed = security ? security.passed : 0
  const secFailed = security ? security.failed : 0

  return (
    <div className="system-view">
      {/* Summary bar */}
      <div className="system-summary">
        <div className="summary-card">
          <span className="summary-num" style={{ color: secFailed > 0 ? 'var(--error)' : 'var(--accent)' }}>{secPassed}</span>
          <span className="summary-label">Enforcement Checks Passed</span>
        </div>
        <div className="summary-card">
          <span className="summary-num" style={{ color: secFailed > 0 ? 'var(--error)' : 'var(--text-dim)' }}>{secFailed}</span>
          <span className="summary-label">Enforcement Checks Failed</span>
        </div>
        <div className="summary-card">
          <span className="summary-num" style={{ color: gatewaysDown > 0 ? 'var(--warn)' : 'var(--accent)' }}>{gatewaysUp}</span>
          <span className="summary-label">Gateways Up</span>
        </div>
        <div className="summary-card">
          <span className="summary-num" style={{ color: gatewaysDown > 0 ? 'var(--error)' : 'var(--text-dim)' }}>{gatewaysDown}</span>
          <span className="summary-label">Gateways Down</span>
        </div>
        <button
          className="action-btn"
          onClick={() => setAutoRefresh(!autoRefresh)}
          style={{ marginLeft: 'auto' }}
        >
          {autoRefresh ? 'Auto-refresh ON (5s)' : 'Auto-refresh OFF'}
        </button>
      </div>

      {actionMsg && (
        <div className={`action-msg ${actionMsg.type}`}>
          {actionMsg.text}
        </div>
      )}

      {/* Enforcement Audit Panel */}
      {security && (
        <>
          <div className="section-header" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span>ENFORCEMENT AUDIT</span>
            <span style={{
              fontSize: '12px', fontWeight: 'bold', padding: '2px 10px', borderRadius: '4px',
              background: security.enforcement_intact ? 'rgba(0,255,136,0.15)' : 'rgba(255,60,60,0.15)',
              color: security.enforcement_intact ? 'var(--accent)' : 'var(--error)',
              border: `1px solid ${security.enforcement_intact ? 'rgba(0,255,136,0.3)' : 'rgba(255,60,60,0.3)'}`,
            }}>
              {security.enforcement_intact ? '◆ CONTAINMENT INTACT' : '✕ CONTAINMENT BREACHED'}
            </span>
          </div>
          <div className="container-list">
            {security.checks.map((c, i) => (
              <div key={i} className={`container-card ${c.passed ? 'healthy' : 'unhealthy'}`}
                   style={{ minHeight: 'auto', padding: '6px 12px' }}>
                <div className="container-card-header" style={{ padding: '0' }}>
                  <span className={`status-dot ${c.passed ? 'ok' : 'down'}`}></span>
                  <span className="container-name" style={{ fontSize: '13px' }}>{c.name}</span>
                  <span className="container-status" style={{
                    fontSize: '11px', color: c.passed ? 'var(--accent)' : 'var(--error)',
                    marginLeft: 'auto', fontFamily: 'monospace'
                  }}>
                    {c.passed ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                <div className="container-meta" style={{ padding: '0' }}>
                  <span className="meta-item" style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-dim)' }}>
                    {c.detail}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Internal gateways */}
      {gateways.length > 0 && (
        <>
          <div className="section-header">PIPELINE GATEWAYS (INTERNAL)</div>
          <div className="container-list">
            {gateways.map((g, i) => (
              <div key={i} className={`container-card ${g.healthy ? 'healthy' : 'unhealthy'}`}>
                <div className="container-card-header">
                  <span className="container-name">{g.name}</span>
                  <span className={`status-dot ${g.healthy ? 'ok' : 'down'}`}></span>
                  <span className="container-status">{g.healthy ? 'UP' : 'DOWN'}</span>
                </div>
                <div className="container-meta">
                  <span className="meta-item">Port: {g.port}</span>
                  <span className="meta-item">Model: {g.model}</span>
                </div>
                <div className="container-actions">
                  <button
                    className="action-btn"
                    onClick={() => viewLogs(g.name)}
                  >
                    Logs
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Services (SQLite, ChromaDB, llama-servers) */}
      {services.length > 0 && (
        <>
          <div className="section-header">SERVICES</div>
          <div className="container-list">
            {services.map((s, i) => (
              <div key={i} className={`container-card ${s.healthy ? 'healthy' : 'unhealthy'}`}>
                <div className="container-card-header">
                  <span className="container-name">{s.name}</span>
                  <span className={`status-dot ${s.healthy ? 'ok' : 'down'}`}></span>
                  <span className="container-status">{s.healthy ? 'OK' : 'DOWN'}</span>
                </div>
                <div className="container-meta">
                  {s.url && <span className="meta-item">{s.url}</span>}
                  {s.detail && <span className="meta-item">{s.detail}</span>}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {loading && <p className="loading-text">Loading...</p>}

      {/* Log viewer modal */}
      {logs && (
        <div className="log-modal-overlay" onClick={() => setLogs(null)}>
          <div className="log-modal" onClick={e => e.stopPropagation()}>
            <div className="log-modal-header">
              <span>Logs: {logs.name}</span>
              <button className="action-btn" onClick={() => setLogs(null)}>Close</button>
            </div>
            {logs.source && (
              <div style={{ fontSize: '11px', color: 'var(--text-dim)', padding: '4px 8px' }}>
                Source: {logs.source}
              </div>
            )}
            <pre className="log-content">
              {logs.lines.map((line, i) => (
                <div key={i} className="log-line">{line}</div>
              ))}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
