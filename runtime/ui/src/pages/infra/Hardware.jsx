const rows = [
  ['CPU', 'AMD Ryzen 9 7950X · 16C/32T'],
  ['RAM', '47 GiB DDR5'],
  ['GPU', 'NVIDIA RTX 4090 · 24 GB VRAM'],
  ['Driver', '560.126.09'],
  ['OS', 'Ubuntu 24.04.4 LTS · kernel 6.17.0'],
]

export default function Hardware() {
  return (
    <div className="card">
      <div className="card-title">⚙️ Hardware</div>
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
