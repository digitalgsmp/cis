import React from 'react'
import { NavLink } from 'react-router-dom'

/**
 * NavGroup — renders a labeled group of navigation links.
 * Props:
 *   label   — group label (string)
 *   items   — array of { path, label }
 */
export default function NavGroup({ label, items }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {label && (
        <span style={{
          fontFamily: '"Share Tech Mono", monospace',
          fontSize: 8,
          color: 'var(--t3)',
          letterSpacing: '.15em',
          textTransform: 'uppercase',
          paddingRight: 6,
          marginRight: 4,
          borderRight: '1px solid #1a1f2e',
          whiteSpace: 'nowrap',
        }}>
          {label}
        </span>
      )}
      {items.map(item => (
        <NavLink key={item.path} to={item.path}
          className={({ isActive }) => isActive ? 'active' : ''}>
          {item.label}
        </NavLink>
      ))}
      {/* Separator between groups */}
      <span style={{ width: 8, flexShrink: 0 }} />
    </div>
  )
}
