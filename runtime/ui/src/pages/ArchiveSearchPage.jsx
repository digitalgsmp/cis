import React, { useState, useCallback } from 'react'
import { api } from '../api'

export default function ArchiveSearchPage() {
  const [query, setQuery] = useState('')
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
      const data = await api.archiveSearchSemantic(query, 20)
      setResults(data)
    } catch (e) {
      setError('Search failed: ' + e.message)
      setResults(null)
    } finally {
      setLoading(false)
    }
  }, [query])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div style={{ padding: 20, overflowY: 'auto', height: '100%' }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <h1 style={{
        fontFamily: '"Share Tech Mono", monospace',
        fontSize: 16,
        color: '#3da0ff',
        marginBottom: 16,
        borderBottom: '1px solid #1a1a2e',
        paddingBottom: 8,
      }}>
        ▸ Semantic Archive Search
      </h1>

      {/* ── Search bar ──────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Search by meaning (e.g., 'client intake workflow')"
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
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          style={{
            padding: '6px 14px',
            fontSize: 11,
            fontFamily: '"Share Tech Mono", monospace',
            background: loading ? '#1a1a2e' : '#3da0ff',
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
      {results && results.results ? (
        results.results.length > 0 ? (
          <div>
            <div style={{
              fontSize: 10,
              color: '#606a80',
              marginBottom: 8,
              fontFamily: '"Share Tech Mono", monospace',
            }}>
              {results.results.length} result{results.results.length !== 1 ? 's' : ''} found
            </div>
            {results.results.map((result, i) => (
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
                  <span style={{
                    padding: '1px 6px',
                    borderRadius: 2,
                    fontSize: 9,
                    fontWeight: 700,
                    background: '#1a1a2e',
                    color: '#a0b0d0',
                    textTransform: 'uppercase',
                  }}>
                    {result.source || result.collection || 'unknown'}
                  </span>
                  {result.score !== undefined && (
                    <span style={{
                      fontSize: 9,
                      color: '#3dffa0',
                      fontFamily: '"Share Tech Mono", monospace',
                    }}>
                      Score: {typeof result.score === 'number' ? result.score.toFixed(3) : result.score}
                    </span>
                  )}
                </div>
                {result.document_id && (
                  <div style={{
                    fontSize: 9,
                    color: '#606a80',
                    fontFamily: '"Share Tech Mono", monospace',
                    marginBottom: 4,
                  }}>
                    ID: {result.document_id}
                  </div>
                )}
                <div style={{
                  color: '#7a8299',
                  fontSize: 10,
                  maxHeight: 80,
                  overflow: 'hidden',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}>
                  {(result.text || result.snippet || result.content || '').substring(0, 300)}
                  {(result.text || result.snippet || result.content || '').length > 300 ? '...' : ''}
                </div>
              </div>
            ))}
          </div>
        ) : hasSearched ? (
          <div style={{ color: '#7a8299', fontSize: 11 }}>
            No results found for "{query}".
          </div>
        ) : null
      ) : hasSearched && !loading ? (
        <div style={{ color: '#7a8299', fontSize: 11 }}>No results returned.</div>
      ) : null}
    </div>
  )
}
