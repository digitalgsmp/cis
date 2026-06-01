import React, { useState, useEffect, useCallback } from 'react'
import ReactFlow, {
  Controls, Background, MiniMap,
  useNodesState, useEdgesState, MarkerType, addEdge, SelectionMode,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { api } from '../api'

const DOMAIN_COLORS = {
  cis: { bg: '#0a0d1a', border: '#4a9eff', text: '#ffffff' },
  swa: { bg: '#0a1a0e', border: '#3dffa0', text: '#ffffff' },
}

const CLUSTER_COLORS = {
  transcripts_claude: { border: '#4a9eff', bg: '#0a1224' },
  vision:            { border: '#a855f7', bg: '#140a1e' },
  vision_docs:       { border: '#3dffa0', bg: '#0a1a0e' },
  default:           { border: '#7a8299', bg: '#101218' },
}

const STATUS_OPTIONS = ['active', 'branch', 'done', 'future', 'proposed']
const BG_OPTIONS = ['dots', 'lines', 'cross']
const DOMAIN_OPTIONS = ['all', 'cis', 'swa']

let nodeCounter = 1000

export default function SpineGraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ label: '', narrative: '', status: 'proposed', parentId: '' })
  const [flashMsg, setFlashMsg] = useState(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [bgPattern, setBgPattern] = useState('dots')
  const [showMiniMap, setShowMiniMap] = useState(true)
  const [snapToGrid, setSnapToGrid] = useState(false)
  const [animatedEdges, setAnimatedEdges] = useState(false)
  const [domainFilter, setDomainFilter] = useState('all')
  const [expandedCluster, setExpandedCluster] = useState(null)
  const [loading, setLoading] = useState(true)

  const flash = useCallback((msg) => {
    setFlashMsg(msg)
    setTimeout(() => setFlashMsg(null), 3000)
  }, [])

  // ── Load and render graph ─────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false

    async function buildGraph() {
      setLoading(true)
      try {
        const statsR = await fetch('/api/spines/domains')
        const stats = await statsR.json()
        if (cancelled) return

        let filteredStats = stats
        if (domainFilter !== 'all') {
          filteredStats = stats.filter(s => s.domain === domainFilter)
        }

        let ec = expandedCluster
        if (ec) {
          const stillVisible = filteredStats.some(s => `${s.domain}/${s.sub_domain}` === ec)
          if (!stillVisible) ec = null
        }

        const newNodes = []
        const newEdges = []
        let yPos = 0

        // Domain headers
        if (domainFilter === 'all') {
          const cisTotal = filteredStats.filter(s => s.domain === 'cis').reduce((a, s) => a + s.spines, 0)
          const swaTotal = filteredStats.filter(s => s.domain === 'swa').reduce((a, s) => a + s.spines, 0)
          newNodes.push({ id: 'summary-cis', type: 'default', position: { x: 100, y: yPos },
            data: { label: 'CIS — Creative Intelligence System', status: 'active', domain: 'cis',
              narrative: `${cisTotal} extraction files` },
            style: { background: '#0a0d1a', border: '2px solid #4a9eff', color: '#ffffff', width: 280, fontSize: 12, fontWeight: 700 } })
          newNodes.push({ id: 'summary-swa', type: 'default', position: { x: 500, y: yPos },
            data: { label: 'SWA — Social Work AI', status: 'active', domain: 'swa',
              narrative: `${swaTotal} extraction files` },
            style: { background: '#0a1a0e', border: '2px solid #3dffa0', color: '#ffffff', width: 280, fontSize: 12, fontWeight: 700 } })
          yPos += 100
        }

        // Cluster nodes
        for (const s of filteredStats) {
          const colors = CLUSTER_COLORS[s.sub_domain] || CLUSTER_COLORS.default
          const clusterId = `${s.domain}/${s.sub_domain}`
          const isExpanded = ec === clusterId

          newNodes.push({
            id: `cluster-${clusterId}`, type: 'default', position: { x: 100, y: yPos },
            data: { label: `${s.sub_domain.replace(/_/g, ' ')} [${s.spines} spines · ${s.total_nodes} discoveries]`,
              status: isExpanded ? 'active' : 'future', domain: s.domain, clusterId: clusterId,
              narrative: `Source group: ${s.sub_domain}\n${s.spines} files\n${s.total_nodes} discoveries\n\nClick to ${isExpanded ? 'collapse' : 'expand'}` },
            style: { background: isExpanded ? '#ffffff' : colors.bg,
              border: `2px solid ${isExpanded ? '#ffffff' : colors.border}`,
              color: isExpanded ? '#09090c' : colors.border,
              width: 320, fontSize: 10, fontWeight: 700, cursor: 'pointer', borderRadius: 4 },
          })

          const summaryId = domainFilter === 'all' ? `summary-${s.domain}` : `summary-${domainFilter}`
          newEdges.push({ id: `e-${summaryId}-cluster-${clusterId}`,
            source: summaryId, target: `cluster-${clusterId}`,
            style: { stroke: colors.border, opacity: 0.3 },
            markerEnd: { type: MarkerType.ArrowClosed, color: colors.border } })
          yPos += 60

          // Expanded spines
          if (isExpanded) {
            try {
              const sr = await fetch(`/api/spines/by-sub-domain?domain=${s.domain}&sub_domain=${s.sub_domain}`)
              if (cancelled) return
              const spineData = await sr.json()
              for (const sp of (spineData.spines || []).slice(0, 20)) {
                let label = sp.subject
                if (label.length > 45) label = label.substring(0, 42) + '...'
                newNodes.push({
                  id: sp.spine_id, type: 'default', position: { x: 150, y: yPos },
                  data: { label: `${label} [${sp.node_count}]`, status: 'ingested', domain: s.domain,
                    spine_id: sp.spine_id, node_count: sp.node_count,
                    narrative: `Subject: ${sp.subject}\nNodes: ${sp.node_count}\nStatus: ${sp.status}` },
                  style: { background: DOMAIN_COLORS[s.domain]?.bg || '#101218',
                    border: `1px solid ${colors.border}`, color: '#ffffff', width: 300, fontSize: 9 },
                })
                yPos += 42
              }
            } catch(e) { console.error('Failed to load spines:', e) }
          }
        }

        if (!cancelled) {
          setNodes(newNodes)
          setEdges(newEdges)
          setLoading(false)
        }
      } catch(e) { console.error('Failed to build graph:', e); if (!cancelled) setLoading(false) }
    }
    buildGraph()
    return () => { cancelled = true }
  }, [domainFilter, expandedCluster])

  // ── Node click handler ────────────────────────────────────────────────
  const onNodeClick = useCallback((event, node) => {
    if (node.id.startsWith('cluster-')) {
      const clusterId = node.data?.clusterId
      if (clusterId) setExpandedCluster(prev => prev === clusterId ? null : clusterId)
      return
    }
    if (node.id.startsWith('summary-')) return
    setSelectedNode(node)
  }, [])

  const closeOverlay = useCallback(() => setSelectedNode(null), [])

  const onConnect = useCallback((params) => {
    setEdges(eds => addEdge({ ...params, animated: animatedEdges,
      style: { stroke: '#ffffff' }, markerEnd: { type: MarkerType.ArrowClosed, color: '#ffffff' }
    }, eds))
  }, [setEdges, animatedEdges])

  const onDoubleClick = useCallback((event) => {
    if (!reactFlowInstance) return
    const position = reactFlowInstance.screenToFlowPosition({ x: event.clientX, y: event.clientY })
    setForm({ label: '', narrative: '', status: 'proposed', parentId: '' })
    window._newNodePos = position
    setShowForm(true)
  }, [reactFlowInstance])

  const submitNode = useCallback(async () => {
    if (!form.label.trim()) return
    const id = 'manual-' + (nodeCounter++)
    const pos = window._newNodePos || { x: 250, y: 200 }
    setNodes(nds => [...nds, {
      id, type: 'default', position: pos,
      data: { label: form.label, narrative: form.narrative || '', status: form.status, domain: 'manual' },
      style: { background: '#12141e', border: '1px solid #ffffff', color: '#ffffff', width: 220, fontSize: 10 },
    }])
    setShowForm(false)
    flash('✓ Node created')
  }, [form, setNodes, flash])

  const toggleAnimated = useCallback(() => {
    setAnimatedEdges(a => {
      const newVal = !a
      setEdges(eds => eds.map(e => ({ ...e, animated: newVal })))
      return newVal
    })
  }, [setEdges])

  const totalSpines = nodes.filter(n => !n.id.startsWith('summary-') && !n.id.startsWith('cluster-')).length

  return (
    <div style={{ width: '100%', height: '100%', background: '#09090c', display: 'flex', flexDirection: 'column' }}>
      {/* Mini top bar */}
      <div style={{ height: 38, background: '#101218', borderBottom: '1px solid #fff', display: 'flex', alignItems: 'center', padding: '0 16px', gap: 8, flexShrink: 0 }}>
        <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 800, fontSize: 12, letterSpacing: '0.3em', color: '#4a9eff' }}>GRAPH █</div>
        {DOMAIN_OPTIONS.map(d => (
          <button key={d} onClick={() => { setDomainFilter(d); setExpandedCluster(null) }}
            style={{ padding: '2px 8px', fontSize: 9, fontFamily: '"Share Tech Mono", monospace', textTransform: 'uppercase',
              background: domainFilter === d ? (d === 'cis' ? '#0a1a2e' : d === 'swa' ? '#0a1a0e' : '#fff') : 'transparent',
              color: domainFilter === d ? (d === 'all' ? '#09090c' : '#fff') : '#7a8299',
              border: domainFilter === d ? '1px solid #fff' : '1px solid #7a8299', borderRadius: 3, cursor: 'pointer' }}>
            {d}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button onClick={() => setShowForm(true)}
          style={{ padding: '2px 10px', border: '1px solid #fff', borderRadius: 3, background: 'transparent', color: '#fff', cursor: 'pointer', fontSize: 9, fontFamily: '"Share Tech Mono", monospace' }}>
          + Node
        </button>
        <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 9, color: loading ? '#ffb830' : '#3dffa0' }}>
          {loading ? '○ loading' : '● live'}
        </span>
      </div>

      {/* Flash */}
      {flashMsg && (
        <div style={{ position: 'absolute', top: 46, left: '50%', transform: 'translateX(-50%)', zIndex: 999,
          background: '#0a1a0e', border: '1px solid #3dffa0', borderRadius: 6, padding: '4px 14px',
          fontSize: 10, color: '#3dffa0', fontFamily: '"Share Tech Mono", monospace' }}>
          {flashMsg}
        </div>
      )}

      {/* Flow canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <ReactFlow nodes={nodes} edges={edges}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onConnect={onConnect} onNodeClick={onNodeClick}
          onDoubleClick={onDoubleClick} onInit={setReactFlowInstance}
          fitView attributionPosition="bottom-left" deleteKeyCode="Delete"
          multiSelectionKeyCode="Shift" selectionMode={SelectionMode.Partial}
          snapToGrid={snapToGrid} snapGrid={[20, 20]}
          connectionLineStyle={{ stroke: '#fff' }}>
          <Controls />
          <Background color="#222840" gap={20} variant={bgPattern} />
          {showMiniMap && <MiniMap nodeColor={(n) => {
            if (n.data?.domain === 'cis') return '#0a0d1a'
            if (n.data?.domain === 'swa') return '#0a1a0e'
            return '#101218'
          }} maskColor="rgba(0,0,0,0.7)" style={{ border: '1px solid #fff' }} />}
        </ReactFlow>
      </div>

      {/* Status bar */}
      <div style={{ height: 20, background: '#101218', borderTop: '1px solid #fff', display: 'flex', alignItems: 'center', padding: '0 16px', gap: 12, flexShrink: 0 }}>
        <span style={{ fontFamily: '"Share Tech Mono", monospace', fontSize: 8, color: '#7a8299' }}>
          <span style={{ color: domainFilter === 'cis' ? '#4a9eff' : domainFilter === 'swa' ? '#3dffa0' : '#fff' }}>●</span> Spine Map
        </span>
        <span style={{ fontSize: 8, color: '#7a8299' }}>{nodes.length} nodes · {edges.length} edges</span>
        <span style={{ fontSize: 8, color: '#7a8299' }}>Click cluster to expand · Click spine for details</span>
      </div>

      {/* New node form */}
      {showForm && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.85)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setShowForm(false)}>
          <div style={{ background: '#12141e', border: '1px solid #fff', borderRadius: 10, padding: 24, maxWidth: 400, width: '90%' }} onClick={e => e.stopPropagation()}>
            <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 700, fontSize: 14, color: '#fff', marginBottom: 12, textTransform: 'uppercase' }}>New Node</div>
            <input value={form.label} onChange={e => setForm(f => ({ ...f, label: e.target.value }))}
              placeholder="Node title..." autoFocus
              style={{ width: '100%', padding: '8px 10px', borderRadius: 4, border: '1px solid #fff', background: '#0a0a0e', color: '#fff', fontSize: 13, outline: 'none', marginBottom: 12 }} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={submitNode} disabled={!form.label.trim()}
                style={{ flex: 1, padding: '6px 12px', borderRadius: 4, border: '1px solid #fff',
                  background: form.label.trim() ? '#fff' : 'transparent', color: form.label.trim() ? '#09090c' : '#7a8299',
                  cursor: form.label.trim() ? 'pointer' : 'default', fontSize: 10, fontWeight: 700,
                  fontFamily: '"Barlow Condensed", sans-serif', textTransform: 'uppercase' }}>
                Create
              </button>
              <button onClick={() => setShowForm(false)}
                style={{ padding: '6px 12px', borderRadius: 4, border: '1px solid #fff', background: 'transparent', color: '#fff', cursor: 'pointer', fontSize: 10 }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail overlay */}
      {selectedNode && (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', background: 'rgba(0,0,0,0.85)', zIndex: 9998, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={closeOverlay}>
          <div style={{ background: '#12141e', border: '1px solid #fff', borderRadius: 10, padding: 24, maxWidth: 460, width: '90%', margin: 20 }}
            onClick={e => e.stopPropagation()}>
            <div style={{ fontFamily: '"Barlow Condensed", sans-serif', fontWeight: 700, fontSize: 14, color: '#fff', marginBottom: 6 }}>{selectedNode.data.label}</div>
            <div style={{ fontSize: 9, color: '#7a8299', marginBottom: 4, fontFamily: '"Share Tech Mono", monospace', textTransform: 'uppercase' }}>
              Domain: {selectedNode.data.domain} · {selectedNode.data.node_count || 0} discoveries
            </div>
            <div style={{ fontSize: 10, color: '#d0d4e0', lineHeight: 1.6, marginBottom: 12, whiteSpace: 'pre-wrap' }}>{selectedNode.data.narrative}</div>
            <button onClick={closeOverlay} style={{ padding: '4px 12px', border: '1px solid #fff', borderRadius: 4, background: 'transparent', color: '#fff', cursor: 'pointer', fontSize: 10 }}>Close</button>
          </div>
        </div>
      )}
    </div>
  )
}
