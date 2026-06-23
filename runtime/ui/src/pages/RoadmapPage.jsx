import { useState } from "react";

// ── Data ──────────────────────────────────────────────────────────────────

const ROADMAP = {
  built: [
    { title: "Orchestrator (Tier 0)", desc: "Drafter→Reviewer deliberation loop. Removed Eric from manual copy/paste relay.", date: "Jun 6", phase: "Foundation" },
    { title: "5 Verification Gates (Tier 1)", desc: "git_state, service_health, endpoint, no_secrets, file_exists — deterministic PASS/FAIL, no LLM in path.", date: "Jun 6", phase: "Foundation" },
    { title: "Kanban Coordination (Tier 2)", desc: "Shared board across all 5 profiles. Card schema, stage encoding in titles.", date: "Jun 6", phase: "Foundation" },
    { title: "SQLite Spine (Tier 4)", desc: "13-table persistent memory. Write authority model. Bidirectional bridge between pipeline runs and session context.", date: "Jun 6", phase: "Spine & Export" },
    { title: "Context Export Pipeline (Tier 5)", desc: "AGENTS.md auto-generated from spine. HCP packet for external advisors (ChatGPT/Claude). Manual context editing ended.", date: "Jun 7", phase: "Spine & Export" },
    { title: "Pipeline Integration (Tier 6)", desc: "Orchestrator→Kanban→Gates→Spine→Export. Full end-to-end pipeline run from one trigger.", date: "Jun 8", phase: "Spine & Export" },
    { title: "MCP Bridge (Tier 8)", desc: "Read-only stdio MCP server. Query tools for current state, decisions, next actions. 11 tools.", date: "Jun 13", phase: "MCP & VDB" },
    { title: "Chroma VDB (Tier 9)", desc: "Local vector search for CIS spine. ChromaDB 1.5.9. Retrieval only — never writes to spine.", date: "Jun 13", phase: "MCP & VDB" },
    { title: "CIS UI Display Views (Tier 10)", desc: "6 React display views, 1 Flask blueprint (8 GET endpoints), 57 tests. No write endpoints.", date: "Jun 13", phase: "MCP & VDB" },
    { title: "Dashboard + Nav Groups (Tier 11A)", desc: "System overview dashboard. Monitor/Work/Knowledge/Infra nav groups. Kernel status bar.", date: "Jun 14", phase: "Pipeline Oversight" },
    { title: "Eric Gate (Tier 11B)", desc: "APPROVE endpoint. 7 gates pass before Implementer receives directive. Eric stays in control.", date: "Jun 14", phase: "Pipeline Oversight" },
    { title: "Drafter→Reviewer Handoff (Tier 11C)", desc: "Pipeline handoff from proposal drafting to adversarial review. Lifecycle state tracking.", date: "Jun 15", phase: "Pipeline Oversight" },
    { title: "Pre-Execution Oversight (Tier 11D)", desc: "Automatic staleness check + dual-review deliberation (R1 + Qwen). Gate 7 in gate_runner.sh.", date: "Jun 17", phase: "Pipeline Oversight" },
    { title: "CIS Standalone Identity", desc: "Re-framed CIS as standalone application powered by Hermes — not a plugin, not an add-on.", date: "Jun 17", phase: "Pipeline Oversight" },
    { title: "FD.1 MCP Dispatch Tools", desc: "3 new dispatch tools (cis_dispatch_drafter/_reviewer/_implementer). 15 tests. Spine helper.", date: "Jun 20", phase: "Enforcement & Portal" },
    { title: "CIS Control Portal v0.1", desc: "Multi-model chat — Claude Opus 4.8, GLM 5.2, Mistral Large 3, GLM 4.7 Flash local. 4-panel Advisor Chat.", date: "Jun 22", phase: "Enforcement & Portal" },
    { title: "Thread Tracking + Context Bars", desc: "Portal thread_id tracking, context bars on all panels, pipeline trigger endpoints.", date: "Jun 23", phase: "Enforcement & Portal" },
    { title: "Cross-Panel Message Visibility", desc: "Advisor Chat panels show all agents' messages. 'other panel' badge for visual distinction. No more copy/paste between panels.", date: "Jun 23", phase: "Enforcement & Portal" },
  ],
  specified: [
    { title: "Pipeline-Visible Portal", desc: "Portal panels become windows into pipeline stages. Clarification→Trigger→Deliberation→Gates→Implementation all visible in real time. Eric never leaves the conversation.", date: "Jun 22", spec: "docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md" },
    { title: "Chat-to-Pipeline Trigger", desc: "Model infers intent from conversation. When Eric describes a task needing the pipeline, model signals [PIPELINE:intent]. Backend routes through classify_route(), pipeline runs in background.", date: "Jun 22", spec: "docs/CIS_CHAT_PIPELINE_INFERENCE_TRIGGER_SPEC.md" },
    { title: "Enforcement Primitive", desc: "TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1. 3-layer process isolation: CIS control plane → Hermes worker in Docker with RO /opt/cis-control. 15 acceptance tests. Awaiting §14 raw-evidence plan.", date: "Jun 19", spec: "docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md" },
    { title: "FD.1 Front Door (in progress)", desc: "14 MCP tools total (11 existing + 3 dispatch). ChromaDB 1.5.9, 8 router routes. NA-SEED-017 IN_PROGRESS.", date: "Jun 20", spec: "docs/CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md" },
    { title: "Enforcement Override Plane", desc: ".GATE_DISABLED built/tested before hook is trusted. Two enforcement walls: kernel (Docker RO mount) + policy hook (pre_tool_call).", date: "Jun 19", spec: "ADR-SEED-015" },
  ],
  theorized: [
    { title: "Unified Memory Build", desc: "Cross-session persistent memory that survives context windows. Not yet architected.", date: "Future", phase: "Do Not Start" },
    { title: "VDB Pipeline Rebuild", desc: "Vector database pipeline for session embeddings and semantic search. Blocked on memory architecture.", date: "Future", phase: "Do Not Start" },
    { title: "Pass 5 Implementation", desc: "Project promotion, schema migration. Gated on dependency graph completion.", date: "Future", phase: "Do Not Start" },
    { title: "Discord / Telegram Gateway", desc: "Multi-platform agent access. Not in current build scope.", date: "Future", phase: "Do Not Start" },
    { title: "SWA — Social Work App", desc: "Second CIS project. Schedule field-use work. WIASW creative workflow. Separate from CIS pipeline infra.", date: "Future", phase: "Second Project" },
    { title: "Briefing Center UI", desc: "Redesigned briefing/context display. Not in current scope.", date: "Future", phase: "Do Not Start" },
    { title: "Notes / Open Items DB", desc: "Dedicated database for tracking open questions and notes. Deferred.", date: "Future", phase: "Do Not Start" },
  ],
};

const ADRS = [
  { id: "001", title: "Dependency Graph Build Order", summary: "CIS built tier by tier. Nothing built before its dependencies exist." },
  { id: "002", title: "Verification Hardening", summary: "V4 Implementer self-report is not truth. Completion requires deterministic evidence (git diff, test output, DB queries, endpoint responses)." },
  { id: "003", title: "Role Identity Runtime-Derived", summary: "Role from HERMES_HOME and gateway endpoint, not briefing text or model self-description." },
  { id: "004", title: "Browser Role Enforcement", summary: "Role badge from gateway profile only. Implementation directives route only to hermes-v4impl:8646." },
  { id: "005", title: "Briefing Path Retired", summary: "HERMES_CIS_BRIEFING_PATH removed at Tier 5.3 after AGENTS.md canary passed all 4 profiles." },
  { id: "006", title: "Spine Migration Strategy", summary: "spine_schema.sql is the verified minimum. Extensions via numbered migration files. Verified artifacts never rewritten." },
  { id: "007", title: "AGENTS.md Gateway Loading", summary: "AGENTS.md loaded from CWD in gateway mode. Gateway processes require TERMINAL_CWD=/mnt/projects/cis." },
  { id: "008", title: "External Advisor Packet Permanent", summary: "HCP remains canonical external-model context for ChatGPT/Claude. AGENTS.md serves Hermes-native context." },
  { id: "009", title: "HCP Export CIS-Scoped", summary: "HCP export assumes CIS project. Must be refactored to project-agnostic before managing a second project." },
  { id: "010", title: "Project Isolation Model", summary: "--project-root: each CIS-managed project has its own git repo + spine. No cross-project contamination. No multi-project routing logic." },
  { id: "012", title: "Orchestrator Validation Contract", summary: "FINAL_JSON block required from every Drafter/Reviewer response. Role-scoped status values. Missing JSON → repair prompt → fallback text scan." },
  { id: "013", title: "Retire Kanban as Pipeline Transport", summary: "workflow_runs is authoritative in-flight work object. deliberation_rounds stores Drafter/Reviewer history. Kanban code paths commented out." },
  { id: "014", title: "BLK-SEED-005 False Positive", summary: "get_default_hermes_root collapse bug is LATENT architectural risk, not active runtime issue. Prime was never poisoned. Verified June 16." },
  { id: "015", title: "Enforcement Architecture", summary: "Three-layer process isolation: CIS enforces Hermes via root-owned /opt/cis-control mounted RO into Docker worker. Two walls: kernel + policy hook." },
  { id: "016", title: "Enforcement Primitive Approved", summary: "TASK_CONTRACT_ENFORCEMENT. 15 acceptance tests. No implementation until §14 raw-evidence plan executed. Dual-review approved." },
];

const ERIC_VISION = [
  "LLMs are the tools — I am trying to get LLMs to help me think by contributing factual information and expertise.",
  "I need checks and balance. I have to be able to paste it for another model to evaluate and give me independent analysis.",
  "I need a worker who is constrained to my working methods and two objective reviewers as expert advisors.",
  "I don't want summaries. I am trying to build a system that works from the raw files.",
  "The user does not leave the conversation. The pipeline does not run in a black box.",
];

const PHASES = [
  { name: "Foundation", range: "May 31 – Jun 6", color: "#6b7280", items: ["Initial commit. Gateway stabilization. Router v0.1.", "Build Plan v2.0 (Claude/ChatGPT consensus).", "Tier 0 orchestrator — removed Eric from manual relay.", "5 deterministic verification gates.", "Kanban coordination — 5-profile shared board."] },
  { name: "Spine & Export", range: "Jun 6 – 8", color: "#3b82f6", items: ["SQLite spine (13 tables) — persistent project memory.", "AGENTS.md auto-generator — manual context editing ends.", "HCP export for external advisors.", "Full pipeline integration: Router→Kanban→Gates→Spine→Export."] },
  { name: "MCP, VDB & UI", range: "Jun 13", color: "#8b5cf6", items: ["MCP Bridge — read-only stdio server, 11 tools.", "Chroma VDB — local vector search for spine.", "Tier 10 CIS UI — 6 React views, 57 tests."] },
  { name: "Pipeline Oversight", range: "Jun 14 – 17", color: "#10b981", items: ["Tiers 11A–D: Dashboard, Eric Gate, Drafter/Reviewer handoff.", "Pre-execution oversight pipeline (Gate 7).", "Dual-review deliberation (R1 + Qwen).", "CIS standalone product identity."] },
  { name: "Enforcement & Portal", range: "Jun 18 – 23", color: "#f59e0b", items: ["Enforcement architecture — 3-layer Docker isolation.", "Claude Code 16-failure-mode audit.", "CIS Control Portal v0.1 — multi-model chat.", "Pipeline-Visible Portal + Chat Trigger specs.", "Cross-panel message visibility."] },
];

// ── Components ─────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const colors = {
    built: { bg: "#10b98122", border: "#10b98144", text: "#10b981", label: "Built ✓" },
    specified: { bg: "#8b5cf622", border: "#8b5cf644", text: "#8b5cf6", label: "Specified 📝" },
    theorized: { bg: "#6b728022", border: "#6b728044", text: "#9ca3af", label: "Theorized 💭" },
  };
  const c = colors[status] || colors.theorized;
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 4, fontSize: 9, fontWeight: 700,
      background: c.bg, border: `1px solid ${c.border}`, color: c.text,
      textTransform: "uppercase", letterSpacing: ".05em", whiteSpace: "nowrap",
    }}>{c.label}</span>
  );
}

function Card({ item, status }) {
  return (
    <div style={{
      padding: "10px 12px", background: "#0f172a",
      border: "1px solid #1e293b", borderRadius: 6,
      marginBottom: 8,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8, marginBottom: 6 }}>
        <span style={{ color: "#e2e8f0", fontSize: 12, fontWeight: 600 }}>{item.title}</span>
        <StatusBadge status={status} />
      </div>
      <div style={{ color: "#94a3b8", fontSize: 11, lineHeight: 1.5, marginBottom: 6 }}>
        {item.desc}
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ color: "#475569", fontSize: 10, fontFamily: "monospace" }}>{item.date}</span>
        {item.phase && <span style={{ color: "#334155", fontSize: 10 }}>{item.phase}</span>}
        {item.spec && (
          <a href={`/${item.spec}`} target="_blank" rel="noreferrer"
            style={{ color: "#64748b", fontSize: 9, textDecoration: "none", marginLeft: "auto" }}>
            spec →
          </a>
        )}
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

function PhaseBlock({ phase, idx }) {
  return (
    <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 24 }}>
        <div style={{
          width: 10, height: 10, borderRadius: "50%",
          background: phase.color, marginTop: 4,
        }} />
        <div style={{ width: 2, flex: 1, background: "#1e293b", marginTop: 4 }} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
          <span style={{ color: phase.color, fontSize: 13, fontWeight: 700 }}>{phase.name}</span>
          <span style={{ color: "#475569", fontSize: 10, fontFamily: "monospace" }}>{phase.range}</span>
        </div>
        {phase.items.map((item, i) => (
          <div key={i} style={{ color: "#94a3b8", fontSize: 11, padding: "3px 0", display: "flex", gap: 6 }}>
            <span style={{ color: "#334155" }}>—</span>
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function RoadmapPage() {
  const [tab, setTab] = useState("roadmap");

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
        flexShrink: 0,
      }}>
        <span style={{ fontWeight: 700, fontSize: 14, color: "#94a3b8" }}>
          Roadmap
        </span>
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
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>

        {tab === "roadmap" && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 8 }}>
                Status Overview
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                {/* Built */}
                <div>
                  <div style={{ color: "#10b981", fontSize: 12, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    Built ✓ <span style={{ color: "#475569", fontSize: 10, fontWeight: 400 }}>({ROADMAP.built.length})</span>
                  </div>
                  {ROADMAP.built.map((item, i) => <Card key={i} item={item} status="built" />)}
                </div>
                {/* Specified */}
                <div>
                  <div style={{ color: "#8b5cf6", fontSize: 12, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    Specified 📝 <span style={{ color: "#475569", fontSize: 10, fontWeight: 400 }}>({ROADMAP.specified.length})</span>
                  </div>
                  {ROADMAP.specified.map((item, i) => <Card key={i} item={item} status="specified" />)}
                </div>
                {/* Theorized */}
                <div>
                  <div style={{ color: "#9ca3af", fontSize: 12, fontWeight: 700, marginBottom: 8, display: "flex", alignItems: "center", gap: 6 }}>
                    Theorized 💭 <span style={{ color: "#475569", fontSize: 10, fontWeight: 400 }}>({ROADMAP.theorized.length})</span>
                  </div>
                  {ROADMAP.theorized.map((item, i) => <Card key={i} item={item} status="theorized" />)}
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
            {PHASES.map((phase, idx) => <PhaseBlock key={idx} phase={phase} idx={idx} />)}
          </div>
        )}

        {tab === "adrs" && (
          <div>
            <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 8 }}>
              Architectural Decision Records ({ADRS.length})
            </div>
            <div style={{ color: "#475569", fontSize: 11, marginBottom: 16 }}>
              These are the binding architectural decisions that shape CIS. Each was adversarial-reviewed and Eric-approved.
            </div>
            {ADRS.map((adr, i) => <ADRCard key={i} adr={adr} />)}
          </div>
        )}

        {tab === "vision" && (
          <div>
            <div style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 16 }}>
              Eric's Core Vision — Verbatim
            </div>
            {ERIC_VISION.map((v, i) => (
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
              Source: session_20260520_215551_16187f.json, session_20260525_232304_b2d3b2.json, session_20260518_203801_265262.json
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
