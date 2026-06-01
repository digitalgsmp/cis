const rows = [
  ['vLLM Slot 1', 'Qwen3-32B-AWQ (slot1-qwen3-32b)'],
  ['Ollama', 'local models available'],
  ['Qwen3.6 GGUF', '/mnt/models2/Qwen3.6-GGUF/ (never deployed)'],
  ['Qwen3-VL GGUF', '/mnt/models/Qwen3-VL-GGUF/'],
  ['HuggingFace', '/mnt/models/huggingface/ (model cache)'],
]

export default function Models() {
  return (
    <div className="card">
      <div className="card-title">🧠 Models</div>
      <InfoTable rows={rows} />
    </div>
  )
}

function InfoTable({ rows, labelWidth = 110 }) {
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
