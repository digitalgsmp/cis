const rows = [
  ['vda', '500 GB · system disk'],
  ['vdb', '250 GB · /mnt/projects'],
  ['vdc', '9.1 TB · /mnt/archive (88% full)'],
  ['vdd', '112 GB · /mnt/cache'],
  ['vde', '233 GB · /mnt/models'],
  ['vdf', '233 GB · /mnt/models2'],
]

export default function Storage() {
  return (
    <div className="card">
      <div className="card-title">💾 Storage</div>
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
