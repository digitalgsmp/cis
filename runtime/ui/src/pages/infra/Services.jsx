const rows = [
  [':5000', 'CIS Flask app (dashboard + kernel UI)'],
  [':7998', 'DeepSeek TUI HTTP bridge'],
  [':8001', 'vLLM Slot 1 (Qwen3-32B) — check health'],
]

export default function Services() {
  return (
    <div className="card">
      <div className="card-title">🔌 Running Services</div>
      <InfoTable rows={rows} />
    </div>
  )
}

function InfoTable({ rows, labelWidth = 80 }) {
  return (
    <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
      <tbody>
        {rows.map(([label, value], i) => (
          <tr key={i}>
            <td style={{ padding: '6px 0', color: 'var(--t3)', width: labelWidth, fontFamily: 'var(--mono)' }}>{label}</td>
            <td style={{ padding: '6px 0', color: 'var(--t1)' }}>{value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
