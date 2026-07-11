import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../api'

export default function DecisionsPage() {
  const [decisions, setDecisions] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterText, setFilterText] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  const loadDecisions = useCallback(async () => {
    try {
      const data = await api.decisions()
      setDecisions(data)
      setError(null)
    } catch (e) {
      setError('Failed to load decisions: ' + e.message)
    }
  }, [])

  useEffect(() => {
    loadDecisions().finally(() => setLoading(false))
  }, [loadDecisions])

  const filtered = decisions && decisions.decisions
    ? decisions.decisions.filter(d => {
        if (!filterText) return true
        const q = filterText.toLowerCase()
        return (
          (d.decision_id || d.id || '').toLowerCase().includes(q) ||
          (d.label || d.title || '').toLowerCase().includes(q) ||
          (d.decision_text || '').toLowerCase().includes(q)
        )
      })
    : []

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  if (loading) {
    return <div style={{ padding: 20, color: '#7a8299' }}>Loading decisions...</div>
  }

  return (
    <div style={{ padding: 20, overflowY: 'auto', height: '100%' }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <h1 style={{
        fontFamily: '"Share Tech Mono", monospace',
        fontSize: 16,
        color: '#a03dff',
        marginBottom: 16,
        borderBottom: '1px solid #1a1a2e',
        paddingBottom: 8,
      }}>
        ▸ Decisions
      </h1>

      {/* ── Filter ──────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 12 }}>
        <input
          type="text"
          placeholder="Filter by keyword..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          style={{
            width: '100%',
            maxWidth: 400,
            padding: '6px 10px',
            fontSize: 11,
            fontFamily: '"Share Tech Mono", monospace',
            background: '#0e0e1a',
            border: '1px solid #1a1a2e',
            borderRadius: 3,
            color: '#a0b0d0',
            outline: 'none',
          }}
        />
      </div>

      {error && (
        <div style={{ color: '#ff3d3d', fontSize: 11, marginBottom: 12 }}>{error}</div>
      )}

      {/* ── Decision cards ──────────────────────────────────────────────── */}
      {filtered.length > 0 ? (
        <div>
          {filtered.map((decision, i) => {
            const id = decision.decision_id || decision.id || `item-${i}`
            return (
              <div key={i} style={{
                background: '#0e0e1a',
                border: '1px solid #1a1a2e',
                borderRadius: 4,
                padding: '10px 14px',
                marginBottom: 8,
                fontSize: 11,
                fontFamily: '"Share Tech Mono", monospace',
              }}>
                <div
                  onClick={() => toggleExpand(id)}
                  style={{
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <span style={{ color: '#3dffa0', marginRight: 8 }}>
                      {decision.decision_id || decision.id || '—'}
                    </span>
                    <span style={{ color: '#a0b0d0' }}>
                      {decision.label || decision.title || 'Untitled'}
                    </span>
                  </div>
                  <div>
                    <span style={{
                      padding: '1px 6px',
                      borderRadius: 2,
                      fontSize: 9,
                      fontWeight: 700,
                      background: decision.status === 'DECIDED' ? '#0a3d1a' : '#1a1a2e',
                      color: decision.status === 'DECIDED' ? '#3dffa0' : '#7a8299',
                      textTransform: 'uppercase',
                    }}>
                      {decision.status || 'unknown'}
                    </span>
                    {decision.superseded_by && (
                      <span style={{ color: '#ffd93d', marginLeft: 6, fontSize: 9 }}>
                        ← SUPERSEDED
                      </span>
                    )}
                  </div>
                </div>

                {expandedId === id && (
                  <div style={{
                    marginTop: 8,
                    padding: '8px 12px',
                    background: '#0a0a14',
                    borderRadius: 2,
                    color: '#606a80',
                    maxHeight: 200,
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}>
                    {decision.decision_text || decision.content || decision.description || 'No decision text available.'}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        <div style={{ color: '#7a8299', fontSize: 11 }}>
          {filterText ? 'No decisions match your filter.' : 'No decisions found.'}
        </div>
      )}
    </div>
  )
}
