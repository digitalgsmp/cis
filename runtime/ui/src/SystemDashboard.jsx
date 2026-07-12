// CIS Control Panel v1.1.0 — System Dashboard
import { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'

export default function SystemDashboard() {
  const [containers, setContainers] = useState([])
  const [gateways, setGateways] = useState([])
  const [services, setServices] = useState([])
  const [logs, setLogs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionMsg, setActionMsg] = useState(null)
  const [restarting, setRestarting] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchHealth = useCallback(async () => {
    try {
      const data = await api.getSystemHealth()
      setContainers(data.containers || [])
      setGateways(data.gateways || [])
      setServices(data.services || [])
    } catch (e) {
      setContainers([])
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

  const restartContainer = async (name) => {
    setRestarting(name)
    setActionMsg(null)
    try {
      const resp = await api.restartContainer(name)
      setActionMsg({ type: 'ok', text: `${name} restarted` })
      setTimeout(fetchHealth, 2000)
    } catch (e) {
      setActionMsg({ type: 'error', text: `Failed to restart ${name}: ${e.message}` })
    } finally {
      setRestarting(null)
    }
  }

  const viewLogs = async (name) => {
    try {
      const data = await api.getContainerLogs(name)
      setLogs({ name, lines: data.lines || [] })
    } catch (e) {
      setLogs({ name, lines: [`Error: ${e.message}`] })
    }
  }

  const restartAll = async () => {
    setRestarting('ALL')
    setActionMsg(null)
    try {
      const resp = await api.restartAllContainers()
      setActionMsg({ type: 'ok', text: 'All containers restarting...' })
      setTimeout(fetchHealth, 5000)
    } catch (e) {
      setActionMsg({ type: 'error', text: `Failed: ${e.message}` })
    } finally {
      setRestarting(null)
    }
  }

  // Summary counts
  const running = containers.filter(c => c.status === 'running').length
  const unhealthy = containers.filter(c => c.status === 'running' && !c.healthy).length
  const stopped = containers.filter(c => c.status !== 'running').length
  const gatewaysUp = gateways.filter(g => g.healthy).length
  const gatewaysDown = gateways.filter(g => !g.healthy).length

  return (
    <div className="system-view">
      {/* Summary bar */}
      <div className="system-summary">
        <div className="summary-card">
          <span className="summary-num">{running}</span>
          <span className="summary-label">Containers Running</span>
        </div>
        <div className="summary-card">
          <span className="summary-num" style={{ color: gatewaysDown > 0 ? 'var(--warn)' : 'var(--accent)' }}>{gatewaysUp}</span>
          <span className="summary-label">Gateways Up</span>
        </div>
        <div className="summary-card">
          <span className="summary-num" style={{ color: gatewaysDown > 0 ? 'var(--error)' : 'var(--text-dim)' }}>{gatewaysDown}</span>
          <span className="summary-label">Gateways Down</span>
        </div>
        <div className="summary-card">
          <span className="summary-num" style={{ color: stopped > 0 ? 'var(--error)' : 'var(--text-dim)' }}>{stopped}</span>
          <span className="summary-label">Containers Stopped</span>
        </div>
        <button
          className="action-btn"
          onClick={() => setAutoRefresh(!autoRefresh)}
          style={{ marginLeft: 'auto' }}
        >
          {autoRefresh ? 'Auto-refresh ON (5s)' : 'Auto-refresh OFF'}
        </button>
        <button
          className="action-btn danger"
          onClick={restartAll}
          disabled={restarting === 'ALL'}
        >
          {restarting === 'ALL' ? 'Restarting...' : 'Restart All'}
        </button>
      </div>

      {actionMsg && (
        <div className={`action-msg ${actionMsg.type}`}>
          {actionMsg.text}
        </div>
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
              </div>
            ))}
          </div>
        </>
      )}

      {/* Docker containers */}
      <div className="section-header">DOCKER CONTAINERS</div>
      {loading ? (
        <p className="loading-text">Loading...</p>
      ) : containers.length === 0 ? (
        <p className="loading-text">No containers found. Is Docker running?</p>
      ) : (
        <div className="container-list">
          {containers.map((c, i) => (
            <div key={i} className={`container-card ${c.status === 'running' ? (c.healthy ? 'healthy' : 'unhealthy') : 'stopped'}`}>
              <div className="container-card-header">
                <span className="container-name">{c.name}</span>
                <span className={`status-dot ${c.status === 'running' ? (c.healthy ? 'ok' : 'warn') : 'down'}`}></span>
                <span className="container-status">{c.status}{c.health ? ` / ${c.health}` : ''}</span>
              </div>
              <div className="container-meta">
                {c.image && <span className="meta-item">Image: {c.image}</span>}
                {c.uptime && <span className="meta-item">Up: {c.uptime}</span>}
                {c.ports && <span className="meta-item">Ports: {c.ports}</span>}
              </div>
              <div className="container-actions">
                <button
                  className="action-btn"
                  onClick={() => restartContainer(c.name)}
                  disabled={restarting === c.name}
                >
                  {restarting === c.name ? 'Restarting...' : 'Restart'}
                </button>
                <button
                  className="action-btn"
                  onClick={() => viewLogs(c.name)}
                >
                  Logs
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Services (non-Docker) */}
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

      {/* Log viewer modal */}
      {logs && (
        <div className="log-modal-overlay" onClick={() => setLogs(null)}>
          <div className="log-modal" onClick={e => e.stopPropagation()}>
            <div className="log-modal-header">
              <span>Logs: {logs.name}</span>
              <button className="action-btn" onClick={() => setLogs(null)}>Close</button>
            </div>
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
