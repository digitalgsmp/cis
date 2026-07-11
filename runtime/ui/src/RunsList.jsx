import { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'

export default function RunsList({ onSelectRun }) {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getRuns()
        setRuns(data.runs || data || [])
      } catch {
        setRuns([])
      } finally {
        setLoading(false)
      }
    }
    load()
    const iv = setInterval(load, 10000)
    return () => clearInterval(iv)
  }, [])

  return (
    <div className="runs-view">
      <h2 style={{ fontSize: '15px', marginBottom: '16px', color: 'var(--text-dim)' }}>
        Recent Pipeline Runs
      </h2>
      {loading && (
        <p style={{ color: 'var(--text-dim)' }}>Loading...</p>
      )}
      {!loading && runs.length === 0 && (
        <p style={{ color: 'var(--text-dim)' }}>No runs found.</p>
      )}
      {runs.map((run, i) => (
        <div
          key={run.id || i}
          className="run-card"
          onClick={() => onSelectRun(run.id)}
        >
          <div className="run-id">{run.id}</div>
          <div className="run-topic">
            {run.topic ? run.topic.slice(0, 100) : '(no topic)'}
          </div>
          <div className="run-meta">
            <span>Status: {run.status}</span>
            {run.result && <span>Result: {run.result}</span>}
            {run.created_at && <span>{new Date(run.created_at).toLocaleString()}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
