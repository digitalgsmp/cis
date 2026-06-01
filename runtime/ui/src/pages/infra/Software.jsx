const rows = [
  ['Blender', '4.0.2'],
  ['Python', '3.12.3 (system) · 3.11.15 (hermes venv)'],
  ['Node', '22.22.2'],
  ['Git', '2.43.0'],
  ['Sunshine', '2025.924 (installed, not running)'],
  ['Ollama', 'running as service'],
  ['Hermes', 'main agent (this session)'],
]

export default function Software() {
  return (
    <div className="card">
      <div className="card-title">🧰 Software</div>
      <InfoTable rows={rows} />
    </div>
  )
}

function InfoTable({ rows, labelWidth = 100 }) {
  return (
    <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
      <tbody>
        {rows.map(([label, value], i) => (
          <tr key={i}>
            <td style={{ padding: '6px 0', color: 'var(--t3)', width: labelWidth }}>{label}</td>
            <td style={{ padding: '6px 0', color: 'var(--t1)' }}>{value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
