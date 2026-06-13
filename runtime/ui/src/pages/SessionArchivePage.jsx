import React, { useState, useCallback } from 'react'
import { api } from '../api'

export default function SessionArchivePage() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('fts')  // 'fts' or 'semantic'
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setHasSearched(true)
    try {
      let data
      if (mode === 'semantic') {
        data = await api.archiveSearchSemantic(query, 20)
      } else {
        data = await api.archiveSearchFts(query, 20)
      }
      setResults(data)
    } catch (e) {
      setError('Search failed: ' + e.message)
      setResults(null)
    } finally {
      setLoading(false)
    }
  }, [query, mode])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch()
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
        ▸ Session Archive
      </h1>

      {/* ── Search bar + mode toggle ─────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          placeholder={mode === 'fts' ? "Keyword search (e.g., 'closeout')" : "Semantic search (e.g., 'verification failures')"}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{
            flex: 1,
            maxWidth: 500,
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

        {/* Mode toggle buttons */}
        <div style={{ display: 'flex', gap: 2 }}>
          <button
            onClick={() => setMode('fts')}
            style={{
              padding: '6px 10px',
              fontSize: 10,
              fontFamily: '"Share Tech Mono", monospace',
              background: mode === 'fts' ? '#3dffa0' : '#0e0e1a',
              border: mode === 'fts' ? '1px solid #3dffa0' : '1px solid #1a1a2e',
              borderRadius: '3px 0 0 3px',
              color: mode === 'fts' ? '#09090c' : '#7a8299',
              cursor: 'pointer',
              fontWeight: 700,
            }}
          >
            Keyword
          </button>
          <button
            onClick={() => setMode('semantic')}
            style={{
              padding: '6px 10px',
              fontSize: 10,
              fontFamily: '"Share Tech Mono", monospace',
              background: mode === 'semantic' ? '#3da0ff' : '#0e0e1a',
              border: mode === 'semantic' ? '1px solid #3da0ff' : '1px solid #1a1a2e',
              borderRadius: '0 3px 3px 0',
              color: mode === 'semantic' ? '#09090c' : '#7a8299',
              cursor: 'pointer',
              fontWeight: 700,
            }}
          >
            Semantic
          </button>
        </div>

        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          style={{
            padding: '6px 14px',
            fontSize: 11,
            fontFamily: '"Share Tech Mono", monospace',
            background: loading ? '#1a1a2e' : '#3dffa0',
            border: 'none',
            borderRadius: 3,
            color: '#09090c',
            cursor: loading ? 'default' : 'pointer',
            fontWeight: 700,
          }}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div style={{ color: '#ff3d3d', fontSize: 11, marginBottom: 12 }}>{error}</div>
      )}

      {/* ── Results ─────────────────────────────────────────────────────── */}
      {results ? (
        (results.sessions || results.results) &&
        (results.sessions || results.results).length > 0 ? (
          <div>
            <div style={{
              fontSize: 10,
              color: '#606a80',
              marginBottom: 8,
              fontFamily: '"Share Tech Mono", monospace',
            }}>
              {(results.sessions || results.results).length} result{(results.sessions || results.results).length !== 1 ? 's' : ''} found
              {mode === 'semantic' && ' (semantic)'}
              {mode === 'fts' && ' (keyword)'}
            </div>
            {(results.sessions || results.results).map((item, i) => (
              <div key={i} style={{
                background: '#0e0e1a',
                border: '1px solid #1a1a2e',
                borderRadius: 4,
                padding: '10px 14px',
                marginBottom: 8,
                fontSize: 11,
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: 4,
                  fontFamily: '"Share Tech Mono", monospace',
                }}>
                  <span style={{ color: '#3dffa0' }}>
                    {item.id || item.session_id || item.document_id || `Result ${i + 1}`}
                  </span>
                  {item.status && (
                    <span style={{
                      padding: '1px 6px',
                      borderRadius: 2,
                      fontSize: 9,
                      fontWeight: 700,
                      background: item.status === 'PASS' ? '#0a3d1a' : item.status === 'FAIL' ? '#3d1a0a' : '#1a1a2e',
                      color: item.status === 'PASS' ? '#3dffa0' : item.status === 'FAIL' ? '#ff3d3d' : '#7a8299',
                      textTransform: 'uppercase',
                    }}>
                      {item.status}
                    </span>
                  )}
                  {item.score !== undefined && mode === 'semantic' && (
                    <span style={{ fontSize: 9, color: '#3dffa0', fontFamily: '"Share Tech Mono", monospace' }}>
                      Score: {typeof item.score === 'number' ? item.score.toFixed(3) : item.score}
                    </span>
                  )}
                </div>
                {item.completed_at && (
                  <div style={{ fontSize: 9, color: '#606a80', fontFamily: '"Share Tech Mono", monospace' }}>
                    Completed: {item.completed_at}
                  </div>
                )}
                {(item.failure_summary || item.summary || item.snippet || item.text) && (
                  <div style={{
                    color: '#7a8299',
                    fontSize: 10,
                    maxHeight: 60,
                    overflow: 'hidden',
                    marginTop: 4,
                  }}>
                    {(item.failure_summary || item.summary || item.snippet || item.text || '').substring(0, 200)}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : hasSearched ? (
          <div style={{ color: '#7a8299', fontSize: 11 }}>
            No sessions found for "{query}".
          </div>
        ) : null
      ) : null}

      {/* ── Empty state ──────────────────────────────────────────────────── */}
      {!hasSearched && !loading && (
        <div style={{ color: '#606a80', fontSize: 11, marginTop: 12 }}>
          Enter a query and press Search to find sessions.
        </div>
      )}
    </div>
  )
}
