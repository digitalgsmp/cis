import React, { useState, useEffect, useCallback } from 'react'
import { api } from '../api'

export default function IngestionPage() {
  const [status, setStatus] = useState(null)
  const [files, setFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [detail, setDetail] = useState(null)
  const [filter, setFilter] = useState('all')
  const [running, setRunning] = useState(false)
  const [polling, setPolling] = useState(null)

  // ── Load status ───────────────────────────────────────────────────────
  const loadStatus = useCallback(async () => {
    try {
      const s = await api.ingestStatus()
      setStatus(s)
      setRunning(s.run?.running || false)
    } catch(e) { console.error('Failed to load status:', e) }
  }, [])

  useEffect(() => { loadStatus() }, [loadStatus])

  // Poll while ingestion is running
  useEffect(() => {
    if (running) {
      const id = setInterval(async () => {
        try {
          const s = await api.ingestStatus()
          setStatus(s)
          if (!s.run?.running) {
            setRunning(false)
            clearInterval(id)
          }
        } catch(e) { /* ignore polling errors */ }
      }, 2000)
      return () => clearInterval(id)
    }
  }, [running])

  // ── Load file list ────────────────────────────────────────────────────
  const loadFiles = useCallback(async () => {
    try {
      const f = await api.ingestFiles()
      setFiles(f.files || [])
    } catch(e) { console.error('Failed to load files:', e) }
  }, [])

  useEffect(() => { loadFiles() }, [loadFiles])

  // ── Run ingestion ─────────────────────────────────────────────────────
  const handleRun = async (project) => {
    setRunning(true)
    try {
      await api.ingestRun(project)
    } catch(e) { console.error('Failed to start ingestion:', e) }
  }

  // ── File detail ───────────────────────────────────────────────────────
  const handleFileClick = async (f) => {
    setSelectedFile(f)
    if (f.ingested) {
      try {
        const d = await api.ingestFileDetail(f.name)
        setDetail(d)
      } catch(e) {
        console.error('Failed to load file detail:', e)
        setDetail(null)
      }
    } else {
      setDetail(null)
    }
  }

  // ── Filter files ──────────────────────────────────────────────────────
  const filteredFiles = files.filter(f => {
    if (filter === 'cis') return f.project === 'cis'
    if (filter === 'swa') return f.project === 'swa'
    if (filter === 'ingested') return f.ingested
    if (filter === 'missing') return !f.ingested
    return true
  })

  const summary = {
    cis_total: files.filter(f => f.project === 'cis').length,
    swa_total: files.filter(f => f.project === 'swa').length,
    cis_ingested: files.filter(f => f.project === 'cis' && f.ingested).length,
    swa_ingested: files.filter(f => f.project === 'swa' && f.ingested).length,
    total_ingested: files.filter(f => f.ingested).length,
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', padding: '14px 20px', borderBottom: '1px solid #fff', flexShrink: 0, gap: 12 }}>
        <div>
          <div className="hdr-title" style={{ fontSize: 18, margin: 0 }}>Ingestion</div>
          <div className="hdr-sub" style={{ fontSize: 10, margin: 0 }}>Extraction file index</div>
        </div>
        <span style={{ flex: 1 }} />
        <div style={{ display: 'flex', gap: 6 }}>
          <button onClick={() => handleRun('')}
            disabled={running}
            style={{ padding: '6px 14px', fontSize: 10, border: '1px solid #fff', borderRadius: 4,
              background: running ? '#333' : '#fff', color: running ? '#666' : '#09090c',
              cursor: running ? 'default' : 'pointer', fontFamily: '"Share Tech Mono", monospace' }}>
            {running ? '○ Running...' : '▶ Ingest All'}
          </button>
          <button onClick={() => handleRun('cis')} disabled={running}
            style={{ padding: '6px 10px', fontSize: 9, border: '1px solid #4a9eff', borderRadius: 4,
              background: 'transparent', color: '#4a9eff', cursor: running ? 'default' : 'pointer',
              fontFamily: '"Share Tech Mono", monospace' }}>
            CIS only
          </button>
          <button onClick={() => handleRun('swa')} disabled={running}
            style={{ padding: '6px 10px', fontSize: 9, border: '1px solid #3dffa0', borderRadius: 4,
              background: 'transparent', color: '#3dffa0', cursor: running ? 'default' : 'pointer',
              fontFamily: '"Share Tech Mono", monospace' }}>
            SWA only
          </button>
        </div>
      </div>

      {/* Body */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Status + stats panel */}
        <div style={{ width: 300, borderRight: '1px solid #333', padding: 16, overflow: 'auto', flexShrink: 0 }}>
          <div className="hdr-section">Database</div>
          {status ? (
            <div style={{ fontSize: 10, fontFamily: '"Share Tech Mono", monospace', color: '#7a8299', lineHeight: 2 }}>
              <div>CIS spines: <span style={{ color: '#4a9eff' }}>{status.db.cis_spines}</span></div>
              <div>SWA spines: <span style={{ color: '#3dffa0' }}>{status.db.swa_spines}</span></div>
              <div>CIS nodes:   <span style={{ color: '#4a9eff' }}>{status.db.cis_nodes}</span></div>
              <div>SWA nodes:   <span style={{ color: '#3dffa0' }}>{status.db.swa_nodes}</span></div>
              <div style={{ borderTop: '1px solid #333', margin: '8px 0' }}></div>
              <div>Total spines: <span style={{ color: '#fff' }}>{status.db.total_spines}</span></div>
              <div>Total nodes:  <span style={{ color: '#fff' }}>{status.db.total_nodes}</span></div>
            </div>
          ) : (
            <div style={{ fontSize: 10, color: '#7a8299' }}>Loading...</div>
          )}

          <div className="hdr-section" style={{ marginTop: 20 }}>Source Files</div>
          <div style={{ fontSize: 10, fontFamily: '"Share Tech Mono", monospace', color: '#7a8299', lineHeight: 2 }}>
            <div>CIS: <span style={{ color: '#4a9eff' }}>{summary.cis_total}</span> files · <span style={{ color: '#3dffa0' }}>{summary.cis_ingested}</span> ingested</div>
            <div>SWA: <span style={{ color: '#4a9eff' }}>{summary.swa_total}</span> files · <span style={{ color: '#3dffa0' }}>{summary.swa_ingested}</span> ingested</div>
            <div style={{ borderTop: '1px solid #333', margin: '8px 0' }}></div>
            <div>{summary.total_ingested}/{files.length} ingested</div>
            <div>{files.length - summary.total_ingested} pending</div>
          </div>

          {/* Run info */}
          {status?.run?.started_at && (
            <>
              <div className="hdr-section" style={{ marginTop: 20 }}>Last Run</div>
              <div style={{ fontSize: 9, fontFamily: '"Share Tech Mono", monospace', color: '#7a8299', lineHeight: 1.8 }}>
                <div>Started: {status.run.started_at}</div>
                {status.run.finished_at && <div>Finished: {status.run.finished_at}</div>}
                {status.run.last_progress && <div style={{ color: running ? '#ffb830' : '#3dffa0' }}>{status.run.last_progress}</div>}
              </div>
            </>
          )}
        </div>

        {/* File list */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Filter tabs */}
          <div style={{ display: 'flex', padding: '8px 16px', borderBottom: '1px solid #333', gap: 4, flexShrink: 0 }}>
            {[
              { key: 'all', label: `All (${files.length})` },
              { key: 'cis', label: `CIS (${summary.cis_total})` },
              { key: 'swa', label: `SWA (${summary.swa_total})` },
              { key: 'ingested', label: `Ingested (${summary.total_ingested})` },
              { key: 'missing', label: `Missing (${files.length - summary.total_ingested})` },
            ].map(t => (
              <button key={t.key} onClick={() => setFilter(t.key)}
                style={{ padding: '2px 8px', fontSize: 9, border: filter === t.key ? '1px solid #fff' : '1px solid #333',
                  borderRadius: 3, background: filter === t.key ? 'rgba(255,255,255,0.1)' : 'transparent',
                  color: filter === t.key ? '#fff' : '#7a8299', cursor: 'pointer',
                  fontFamily: '"Share Tech Mono", monospace' }}>
                {t.label}
              </button>
            ))}
          </div>

          {/* File rows */}
          <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
            {filteredFiles.length === 0 && (
              <div style={{ padding: 20, fontSize: 10, color: '#7a8299', textAlign: 'center' }}>No files match filter</div>
            )}
            {filteredFiles.map((f, i) => (
              <div key={f.path}
                onClick={() => handleFileClick(f)}
                style={{
                  display: 'flex', alignItems: 'center', padding: '3px 16px', cursor: 'pointer',
                  background: selectedFile?.path === f.path ? 'rgba(255,255,255,0.05)' : 'transparent',
                  borderBottom: '1px solid rgba(255,255,255,0.03)',
                  fontSize: 10, fontFamily: '"Share Tech Mono", monospace',
                }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%', marginRight: 8, flexShrink: 0,
                  background: f.ingested ? (f.project === 'cis' ? '#4a9eff' : '#3dffa0') : '#7a8299',
                }}></span>
                <span style={{
                  color: f.project === 'cis' ? '#4a9eff' : '#3dffa0', width: 28, flexShrink: 0, fontSize: 8,
                  textTransform: 'uppercase', opacity: 0.5,
                }}>{f.project}</span>
                <span style={{ flex: 1, color: f.ingested ? '#d0d4e0' : '#7a8299', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}>
                  {f.name}
                  <a href={`/api/ingest-spines/raw-file/${encodeURIComponent(f.name)}?project=${f.project}`}
                    target="_blank"
                    title={f.path}
                    onClick={e => e.stopPropagation()}
                    style={{ color: '#4a9eff', textDecoration: 'none', fontSize: 8, opacity: 0.5, flexShrink: 0 }}>
                    📄
                  </a>
                </span>
                {f.ingested && (
                  <span style={{ color: '#3dffa0', marginLeft: 8, flexShrink: 0 }}>
                    {f.node_count} nodes
                  </span>
                )}
                {!f.ingested && (
                  <span style={{ color: '#ffb830', marginLeft: 8, flexShrink: 0, fontSize: 8 }}>MISSING</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Detail panel */}
        <div style={{ width: 350, borderLeft: '1px solid #333', padding: 16, overflow: 'auto', flexShrink: 0 }}>
          {!selectedFile && (
            <div style={{ fontSize: 10, color: '#7a8299', textAlign: 'center', marginTop: 40 }}>
              Click a file to see details
            </div>
          )}

          {selectedFile && !detail && !selectedFile.ingested && (
            <div style={{ fontSize: 10, color: '#ffb830', textAlign: 'center', marginTop: 40 }}>
              Not yet ingested<br />
              <span style={{ color: '#7a8299' }}>Run ingestion to parse this file</span>
            </div>
          )}

          {selectedFile && detail && detail.spine && (
            <div>
              <div className="hdr-section">{detail.file}</div>
              <div style={{ fontSize: 9, fontFamily: '"Share Tech Mono", monospace', color: '#7a8299', lineHeight: 1.8, marginBottom: 16 }}>
                <div>Project: <span style={{ color: detail.project === 'cis' ? '#4a9eff' : '#3dffa0' }}>{detail.project}</span></div>
                <div>Subject: <span style={{ color: '#d0d4e0' }}>{detail.spine.subject}</span></div>
                <div>Source: <span style={{ color: '#d0d4e0' }}>{detail.spine.sub_domain}</span></div>
                <div>Nodes: <span style={{ color: '#fff' }}>{detail.spine.node_count}</span></div>
                <div>Status: <span style={{ color: '#3dffa0' }}>{detail.spine.status}</span></div>
                <div>Ingested: <span style={{ color: '#7a8299' }}>{detail.spine.ingested_at?.substring(0, 19)}</span></div>
              </div>

              {detail.nodes.length > 0 && (
                <>
                  <div className="hdr-section">Discoveries</div>
                  {detail.nodes.map((n, i) => (
                    <div key={n.node_id} style={{
                      padding: '8px 10px', marginBottom: 6,
                      border: '1px solid #333', borderRadius: 4,
                      fontSize: 9, fontFamily: '"Share Tech Mono", monospace',
                    }}>
                      <div style={{ color: '#4a9eff', fontWeight: 600, marginBottom: 4 }}>{n.title}</div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
