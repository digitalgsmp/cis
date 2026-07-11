import { useState, useEffect } from "react";

// ── Components ─────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const colors = {
    COMPLETE: { bg: "#10b98122", border: "#10b98144", text: "#10b981", label: "Built ✓" },
    IN_PROGRESS: { bg: "#f59e0b22", border: "#f59e0b44", text: "#f59e0b", label: "In Progress ⏳" },
    PENDING: { bg: "#8b5cf622", border: "#8b5cf644", text: "#8b5cf6", label: "Specified 📝" },
    Handoff: { bg: "#06b6d422", border: "#06b6d444", text: "#06b6d4", label: "Handoff 📋" },
  };
  const c = colors[status] || { bg: "#6b728022", border: "#6b728044", text: "#9ca3af", label: status };
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 4, fontSize: 9, fontWeight: 700,
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
      textTransform: "uppercase", letterSpacing: ".05em", whiteSpace: "nowrap",
    }}>{c.label}</span>
  );
}

function Card({ item, status }) {
  const stat = item.status || status || "PENDING";
  return (
    <div style={{
      padding: "10px 12px", background: "#0f172a",
      border: "1px solid #1e293b", borderRadius: 6,
      marginBottom: 8,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8, marginBottom: 6 }}>
        <span style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 600 }}>{item.title}</span>
        <StatusBadge status={stat} />
      </div>
      <div style={{ color: "#94a3b8", fontSize: 11, lineHeight: 1.5, marginBottom: 6 }}>
        {item.desc}
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ color: "#475569", fontSize: 10, fontFamily: "monospace" }}>{item.date}</span>
        {item.phase && <span style={{ color: "#334155", fontSize: 10 }}>{item.phase}</span>}
      </div>
    </div>
  );
}

function ADRCard({ adr }) {
  return (
    <div style={{
      padding: "10px 12px", background: "#0f172a",
      border: "1px solid #1e293b", borderRadius: 6,
      marginBottom: 6,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <span style={{
          padding: "1px 6px", borderRadius: 3, fontSize: 9, fontWeight: 700,
          background: "#f59e0b22", border: "1px solid #f59e0b44",
          color: "#f59e0b", fontFamily: "monospace",
        }}>ADR-{adr.id}</span>
        <span style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 600 }}>{adr.title}</span>
      </div>
      <div style={{ color: "#94a3b8", fontSize: 11, lineHeight: 1.5 }}>{adr.summary}</div>
    </div>
  );
}

function PhaseBlock({ phase, idx, isLast }) {
  return (
    <div style={{ display: "flex", gap: 12, marginBottom: isLast ? 0 : 20 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 24 }}>
        <div style={{
          width: 10, height: 10, borderRadius: "50%",
          background: phase.color, marginTop: 4,
        }} />
        {!isLast && <div style={{ width: 2, flex: 1, background: "#1e293b", marginTop: 4 }} />}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
          <span style={{ color: phase.color, fontSize: 13, fontWeight: 700 }}>{phase.name}</span>
          <span style={{ color: "#475569", fontSize: 10, fontFamily: "monospace" }}>{phase.range}</span>
        </div>
      </div>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function RoadmapPage() {
  const [tab, setTab] = useState("roadmap");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/api/pipeline/roadmap")
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", height: "100%", background: "#020817", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#64748b", fontSize: 12 }}>Loading roadmap from spine...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ display: "flex", height: "100%", background: "#020817", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#ef4444", fontSize: 12 }}>Failed to load roadmap: {error || "No data"}</span>
      </div>
    );
  }

  const built = data.built || [];
  const specified = data.specified || [];
  const theorized = data.theorized || [];
  const adrs = data.adrs || [];
  const ericVision = data.eric_vision || [];
  const phases = data.phases || [];
  const currentPhase = data.current_phase || "";

  return (
    <div style={{
      display: "flex", flexDirection: "column", height: "100%",
      background: "#020817", color: "#e2e8f0",
      overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{
        padding: "12px 16px", borderBottom: "1px solid #1e293b",
        background: "#0a0f1e", display: "flex", alignItems: "center", gap: 12,
        flexShrink: 0, flexWrap: "wrap",
      }}>
        <span style={{ fontWeight: 700, fontSize: 14, color: "#94a3b8" }}>
          Roadmap
        </span>
        <a href="/portal" style={{
          color: "#58a6ff", fontSize: 11, textDecoration: "none",
          padding: "3px 10px", border: "1px solid #30363d", borderRadius: 4,
          background: "#0f172a",
        }}>← Portal</a>
        <div style={{ display: "flex", background: "#0f172a", borderRadius: 6, overflow: "hidden", border: "1px solid #1e293b" }}>
          {["roadmap", "timeline", "adrs", "vision"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              style={{
                padding: "4px 12px", border: "none", cursor: "pointer", fontSize: 11,
                background: tab === t ? "#2563eb" : "transparent",
                color: tab === t ? "#fff" : "#64748b",
                fontWeight: tab === t ? 600 : 400,
                textTransform: "capitalize",
              }}>
              {t}
            </button>
          ))}
        </div>
        {currentPhase && (
          <span style={{ color: "#475569", fontSize: 10, marginLeft: "auto" }}>
            {currentPhase.length > 80 ? currentPhase.slice(0, 80) + "..." : currentPhase}
          </span>
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>

        {tab === "roadmap" && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 8 }}>
                Status Overview — Live from Spine
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                {/* Built */}
                <div>
                  <div style={{ color: "#10b981", fontSize: 12, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    Built ✓ <span style={{ color: "#475569", fontSize: 10, fontWeight: 400 }}>({built.length})</span>
                  </div>
                  {built.map((item, i) => <Card key={i} item={item} status="COMPLETE" />)}
                </div>
                {/* Specified */}
                <div>
                  <div style={{ color: "#8b5cf6", fontSize: 12, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    Specified 📝 <span style={{ color: "#475569", fontSize: 10, fontWeight: 400 }}>({specified.length})</span>
                  </div>
                  {specified.map((item, i) => <Card key={i} item={item} status={item.status || "PENDING"} />)}
                </div>
                {/* Handoffs — decision trail */}
                <div>
                  <div style={{ color: "#9ca3af", fontSize: 12, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    Decision Trail 💭 <span style={{ color: "#475569", fontSize: 10, fontWeight: 400 }}>({theorized.length})</span>
                  </div>
                  {theorized.map((item, i) => <Card key={i} item={item} status="Handoff" />)}
                </div>
              </div>
            </div>
          </div>
        )}

        {tab === "timeline" && (
          <div>
            <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 16 }}>
              Chronological Build Phases
            </div>
            {phases.map((phase, idx) => (
              <PhaseBlock key={idx} phase={phase} idx={idx} isLast={idx === phases.length - 1} />
            ))}
          </div>
        )}

        {tab === "adrs" && (
          <div>
            <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 8 }}>
              Architectural Decision Records ({adrs.length})
            </div>
            <div style={{ color: "#475569", fontSize: 11, marginBottom: 16 }}>
              Binding architectural decisions. Each adversarial-reviewed and Eric-approved.
            </div>
            {adrs.map((adr, i) => <ADRCard key={i} adr={adr} />)}
          </div>
        )}

        {tab === "vision" && (
          <div>
            <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 16 }}>
              Eric's Core Vision — Verbatim
            </div>
            {ericVision.map((v, i) => (
              <div key={i} style={{
                padding: "12px 16px", background: "#0f172a",
                border: "1px solid #1e293b", borderRadius: 6,
                marginBottom: 8, display: "flex", gap: 10, alignItems: "flex-start",
              }}>
                <span style={{ color: "#f59e0b", fontSize: 11, fontWeight: 700, flexShrink: 0 }}>"{i + 1}</span>
                <span style={{ color: "#cbd5e1", fontSize: 12, lineHeight: 1.6, fontStyle: "italic" }}>{v}</span>
              </div>
            ))}
            <div style={{ color: "#475569", fontSize: 10, marginTop: 12 }}>
              Source: Eric's recorded sessions — stored in agents_static.yaml seed_intent
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
