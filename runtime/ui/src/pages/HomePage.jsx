import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function HomePage() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.dashboard().then(setStats).catch(() => {})
  }, [])

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto', padding: 24 }}>
      <div className="hdr-title" style={{ fontSize: 22, marginBottom: 4 }}>Dashboard</div>
      <div className="hdr-sub" style={{ fontSize: 11, marginBottom: 24 }}>System overview and quick actions</div>

      {/* Stats cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'Projects', value: stats?.projects_total || 0, color: '#4a9eff' },
          { label: 'Assets', value: stats?.assets_total || 0, color: '#3dffa0' },
          { label: 'Ideas', value: stats?.ideas_total || 0, color: '#a855f7' },
          { label: 'Schedule Slots', value: stats?.slots_total || 0, color: '#ffb830' },
          { label: 'CIS Spines', value: '444', color: '#4a9eff' },
          { label: 'SWA Spines', value: '1,092', color: '#3dffa0' },
          { label: 'Discoveries', value: '8,142', color: '#fff' },
        ].map(card => (
          <div key={card.label} style={{
            padding: '16px 20px', border: '1px solid #333', borderRadius: 8,
            background: '#101218', minWidth: 140, flex: 1,
          }}>
            <div style={{ fontSize: 9, color: '#7a8299', fontFamily: '"Share Tech Mono", monospace', textTransform: 'uppercase', marginBottom: 4 }}>
              {card.label}
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: card.color, fontFamily: '"Barlow Condensed", sans-serif' }}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* Quick links */}
      <div className="hdr-section" style={{ marginBottom: 12 }}>Quick Access</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {[
          { path: '/ideas', label: 'New Idea', desc: 'Capture and classify' },
          { path: '/projects', label: 'Projects', desc: 'Manage build plans' },
          { path: '/schedule', label: 'Schedule', desc: 'Plan your time' },
          { path: '/ingest', label: 'Ingestion', desc: 'Index extraction files' },
          { path: '/spines', label: 'Spine Map', desc: 'Explore knowledge graph' },
          { path: '/learn', label: 'Learning', desc: 'Courses and materials' },
        ].map(link => (
          <a key={link.path} href={link.path}
            onClick={e => { e.preventDefault(); window.history.pushState({}, '', link.path); window.dispatchEvent(new Event('popstate')) }}
            style={{
              padding: '12px 16px', border: '1px solid #333', borderRadius: 6, textDecoration: 'none',
              background: 'transparent', width: 180, cursor: 'pointer', display: 'block',
            }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#fff', fontFamily: '"Barlow Condensed", sans-serif', marginBottom: 2 }}>{link.label}</div>
            <div style={{ fontSize: 9, color: '#7a8299', fontFamily: '"Share Tech Mono", monospace' }}>{link.desc}</div>
          </a>
        ))}
      </div>
    </div>
  )
}
