import { useState } from 'react'
import Hardware from './infra/Hardware'
import Storage from './infra/Storage'
import Software from './infra/Software'
import Models from './infra/Models'
import Services from './infra/Services'
import CollabTracker from './infra/CollabTracker'

const SECTIONS = [
  { id: 'hardware', label: 'Hardware',     icon: '⚙️', desc: 'AMD Ryzen 9 7950X · RTX 4090 · 47 GiB',   comp: Hardware },
  { id: 'storage',  label: 'Storage',      icon: '💾', desc: '6 volumes · 10.4 TB total',               comp: Storage },
  { id: 'software', label: 'Software',     icon: '🧰', desc: 'Blender · Python · Node · Git · more',     comp: Software },
  { id: 'models',   label: 'Models',       icon: '🧠', desc: 'Qwen3 · Ollama · GGUF · HF cache',        comp: Models },
  { id: 'services', label: 'Services',     icon: '🔌', desc: 'CIS · vLLM · DeepSeek TUI',               comp: Services },
  { id: 'collab',   label: 'Collab',       icon: '🤝', desc: 'Tracking collaborators and activity',      comp: CollabTracker },
]

export default function InfraPage() {
  const [active, setActive] = useState(null)

  // If a section is selected, show sidebar + detail
  if (active) {
    const ActiveComp = SECTIONS.find(s => s.id === active).comp
    return (
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <div style={{
          width: 180, minWidth: 180, background: 'var(--bg-surface)',
          borderRight: '1px solid var(--border)',
          display: 'flex', flexDirection: 'column', padding: '12px 0',
        }}>
          <button
            onClick={() => setActive(null)}
            style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              padding: '6px 14px 12px',
              fontFamily: 'var(--cond)', fontSize: 10,
              letterSpacing: '.15em', textTransform: 'uppercase',
              textAlign: 'left', color: 'var(--t3)',
            }}
          >
            ← Dashboard
          </button>
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => setActive(s.id)}
              style={{
                background: active === s.id ? 'var(--bg-raised)' : 'transparent',
                border: 'none', cursor: 'pointer', padding: '8px 14px',
                fontFamily: 'var(--cond)', fontSize: 11, fontWeight: 600,
                letterSpacing: '.08em', textTransform: 'uppercase',
                color: active === s.id ? 'var(--blue)' : 'var(--t3)',
                textAlign: 'left', transition: 'all .1s',
                borderLeft: active === s.id ? '2px solid var(--blue)' : '2px solid transparent',
              }}
            >
              {s.icon} {s.label}
            </button>
          ))}
        </div>

        {/* Content panel */}
        <div className="page-content" style={{ flex: 1, overflowY: 'auto' }}>
          <ActiveComp />
        </div>
      </div>
    )
  }

  // Dashboard landing: highlight cards
  return (
    <div className="page-content">
      <div className="hdr">
        <div className="hdr-title">Infrastructure</div>
        <div className="hdr-sub">Hardware, software, services, and storage on this machine</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
        {SECTIONS.map(s => (
          <div
            key={s.id}
            onClick={() => setActive(s.id)}
            className="card"
            style={{ cursor: 'pointer', transition: 'all .15s' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--blue)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            <div style={{ fontSize: 28, marginBottom: 8 }}>{s.icon}</div>
            <div className="card-title" style={{ marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 12, color: 'var(--t3)', lineHeight: 1.5 }}>{s.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
