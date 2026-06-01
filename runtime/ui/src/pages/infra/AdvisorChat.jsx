import { useState, useEffect, useRef } from "react";
import { flushSync } from "react-dom";

const AGENTS = [
  { name: "hermes-prime",  label: "Research / Evidence (Flash)", route: "fast",           role: "Evidence gathering / research preflight", color: "#f59e0b", model: "deepseek-v4-flash" },
  { name: "hermes-v4pro",  label: "V4 Drafter",                  route: "v4_drafter",     role: "Proposal author / directive drafter",    color: "#8b5cf6", model: "deepseek-v4-pro" },
  { name: "hermes-r1",     label: "V4 Reviewer",                 route: "v4_reviewer",    role: "Adversarial reviewer / validator",       color: "#6366f1", model: "deepseek-v4-pro" },
  { name: "hermes-v4impl", label: "V4 Implementer",              route: "v4_implementer", role: "Execution and evidence verification",     color: "#10b981", model: "deepseek-v4-pro" },
];

const ROUTE_LABELS = {
  fast:           "Research / Evidence (Flash)",
  v4_drafter:     "V4 Drafter",
  v4_reviewer:    "V4 Reviewer",
  v4_implementer: "V4 Implementer",
};

const OVERRIDE_OPTIONS = [
  { value: "",               label: "Auto" },
  { value: "fast",           label: "Research / Evidence (Flash)" },
  { value: "v4_drafter",     label: "V4 Drafter" },
  { value: "v4_reviewer",    label: "V4 Reviewer" },
  { value: "v4_implementer", label: "V4 Implementer" },
];

const API_KEY = "ff239b9b04b514b8bc57f166f0eebd8a6a67022575f7886c027b27728e53e6fd";

function R1StructuredMessage({ content }) {
  const sections = [];
  const patterns = [
    { key: "CORE JUDGMENT", label: "Core Judgment", color: "#6366f1" },
    { key: "REASONING", label: "Reasoning", color: "#818cf8" },
    { key: "RISKS / CONTRADICTIONS", label: "Risks / Contradictions", color: "#f59e0b" },
    { key: "RECOMMENDED NEXT ACTION", label: "Recommended Next Action", color: "#10b981" },
  ];

  let remaining = content;
  for (const pat of patterns) {
    const idx = remaining.toUpperCase().indexOf(pat.key);
    if (idx === -1) continue;
    let endIdx = remaining.length;
    for (const p2 of patterns) {
      const i2 = remaining.toUpperCase().indexOf(p2.key, idx + pat.key.length);
      if (i2 !== -1 && i2 < endIdx) endIdx = i2;
    }
    const body = remaining.slice(idx + pat.key.length, endIdx).replace(/^[\s:]+/, "").trim();
    if (body) sections.push({ ...pat, body });
    remaining = remaining.slice(endIdx);
  }

  if (sections.length < 2) return content;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {sections.map(s => (
        <div key={s.key}>
          <div style={{ fontSize: 10, fontWeight: 700, color: s.color, marginBottom: 2,
                        textTransform: "uppercase", letterSpacing: ".05em" }}>
            {s.label}
          </div>
          <div style={{ fontSize: 12, color: "#cbd5e1", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
            {s.body}
          </div>
        </div>
      ))}
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 8
    }}>
      <div style={{
        maxWidth: "80%",
        padding: "8px 12px",
        borderRadius: 8,
        background: isUser ? "#1e293b" : "#0f172a",
        border: `1px solid ${isUser ? "#334155" : "#1e293b"}`,
        color: "#e2e8f0",
        fontSize: 13,
        lineHeight: 1.5,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word"
      }}>
        {!isUser && (
          <div style={{ fontSize: 10, color: "#64748b", marginBottom: 4 }}>
            {msg.agent_name} · {msg.model}
          </div>
        )}
        {msg.role === "assistant" && msg.agent_name === "hermes-r1" && !msg.streaming
          ? <R1StructuredMessage content={msg.content} />
          : msg.content}
        {msg.streaming && <span style={{ animation: "pulse 1s ease-in-out infinite", color: "#94a3b8" }}>▌</span>}
      </div>
    </div>
  );
}

function AgentPanel({ agent, threadId, disabled, mode, refreshKey, onCritiqueV4Pro, onEscalate, routerContent }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const shouldScrollRef = useRef(false);
  const streamingRef = useRef(false);
  const [r1Elapsed, setR1Elapsed] = useState(0);
  const r1TimerRef = useRef(null);
  const [reasoningOpen, setReasoningOpen] = useState(false);

  useEffect(() => {
    if (agent.name !== "hermes-r1") return;
    if (loading) {
      setR1Elapsed(0);
      r1TimerRef.current = setInterval(() => setR1Elapsed(s => s + 1), 1000);
    } else {
      clearInterval(r1TimerRef.current);
      setR1Elapsed(0);
    }
    return () => clearInterval(r1TimerRef.current);
  }, [loading, agent.name]);

  useEffect(() => {
    if (!threadId) return;
    const poll = () => {
      fetch(`/api/advisor/threads/${threadId}/messages`)
        .then(r => r.json())
        .then(all => {
          if (streamingRef.current) return;
          const filtered = all.filter(m => m.agent_name === agent.name);
          setMessages(prev => {
            if (filtered.length !== prev.length) return filtered;
            return prev;
          });
        });
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [threadId, agent.name, refreshKey]);

  useEffect(() => {
    if (shouldScrollRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
      shouldScrollRef.current = false;
    }
  }, [messages]);

  const send = async () => {
    if (!input.trim() || !threadId || loading) return;
    const text = input.trim();
    setInput("");
    setLoading(true);
    shouldScrollRef.current = true;
    const userMsgId = Date.now();
    setMessages(prev => [...prev, {
      id: userMsgId, role: "user", agent_name: agent.name,
      model: agent.name, content: text
    }]);

    if (agent.name === "hermes-prime" || agent.name === "hermes-v4pro") {
      streamingRef.current = true;
      const streamId = Date.now() + 1;
      setMessages(prev => [...prev, {
        id: streamId, role: "assistant", agent_name: agent.name,
        model: agent.name, content: "", streaming: true
      }]);

      try {
        const response = await fetch("/api/advisor/chat-stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent: agent.name, thread_id: threadId, content: text })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";
        let buf = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n");
          buf = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data: ")) continue;
            const dataStr = trimmed.slice(6);
            try {
              const event = JSON.parse(dataStr);
              if (event.status === "thinking") {
              } else if (event.delta) {
                accumulated += event.delta;
                shouldScrollRef.current = true;
                flushSync(() => {
                  setMessages(prev => prev.map(m =>
                    m.id === streamId ? { ...m, content: accumulated } : m
                  ));
                });
                await new Promise(r => setTimeout(r, 10));
              } else if (event.done) {
                flushSync(() => {
                  setMessages(prev => prev.map(m =>
                    m.id === streamId ? { ...m, content: accumulated || "(no response)", streaming: false } : m
                  ));
                });
              } else if (event.error) {
                flushSync(() => {
                  setMessages(prev => prev.map(m =>
                    m.id === streamId ? { ...m, content: `Error: ${event.error}`, streaming: false } : m
                  ));
                });
              }
            } catch (parseErr) { /* skip malformed SSE */ }
          }
        }

        setMessages(prev => prev.map(m =>
          m.id === streamId && m.streaming ? { ...m, content: accumulated || "(no response)", streaming: false } : m
        ));

      } catch (e) {
        shouldScrollRef.current = true;
        setMessages(prev => prev.map(m =>
          m.id === streamId ? { ...m, content: `Error: ${e.message}`, streaming: false } : m
        ));
      }
      streamingRef.current = false;
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/advisor/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent: agent.name, thread_id: threadId, content: text })
      });
      const data = await res.json();
      if (data.content) {
        shouldScrollRef.current = true;
        setMessages(prev => [...prev, {
          id: Date.now() + 1, role: "assistant", agent_name: agent.name,
          model: agent.name, content: data.content
        }]);
      }
    } catch (e) {
      shouldScrollRef.current = true;
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: "assistant", agent_name: agent.name,
        model: "error", content: `Error: ${e.message}`
      }]);
    }
    setLoading(false);
  };

  return (
    <div style={{
      flex: 1, display: "flex", flexDirection: "column",
      border: `1px solid ${agent.color}33`,
      borderRadius: 8, overflow: "hidden", minWidth: 0, minHeight: 0
    }}>
      <div style={{
        padding: "8px 12px", background: `${agent.color}22`,
        borderBottom: `1px solid ${agent.color}44`,
        display: "flex", alignItems: "center", gap: 8
      }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: agent.color
        }} />
        <span style={{ color: agent.color, fontWeight: 600, fontSize: 13 }}>
          {agent.label}
        </span>
        <span style={{ color: "#64748b", fontSize: 11 }}>{agent.role}</span>
        <span style={{
          color: agent.color, fontSize: 9, opacity: 0.55,
          background: `${agent.color}15`, padding: "1px 6px",
          borderRadius: 3, fontFamily: "monospace", marginLeft: "auto"
        }}>{agent.model}</span>
      </div>

      <div style={{
        flex: 1, overflowY: "auto", padding: 12,
        background: "#020817", minHeight: 0
      }}>
        {/* Router response (injected above chat messages) */}
        {routerContent && (
          <div style={{
            marginBottom: 10, padding: "10px 12px",
            background: "#0f172a", border: `1px solid ${agent.color}44`,
            borderRadius: 6
          }}>
            {/* Reasoning (V4 Implementer only) */}
            {agent.route === "v4_implementer" && routerContent.reasoning_content && (
              <div style={{ marginBottom: 8 }}>
                <button
                  onClick={() => setReasoningOpen(!reasoningOpen)}
                  style={{
                    padding: "2px 8px", background: "#10b98122",
                    border: "1px solid #10b98144", borderRadius: 4,
                    color: "#10b981", fontSize: 10, cursor: "pointer",
                    display: "flex", alignItems: "center", gap: 4
                  }}
                >
                  <span>{reasoningOpen ? "\u25bc" : "\u25b6"} Reasoning</span>
                  <span style={{ color: "#64748b", fontSize: 9 }}>
                    ({routerContent.reasoning_tokens || 0}t)
                  </span>
                </button>
                {reasoningOpen && (
                  <div style={{
                    marginTop: 6, padding: "8px 10px",
                    background: "#1e293b", border: "1px solid #334155",
                    borderRadius: 4, color: "#94a3b8", fontSize: 11,
                    lineHeight: 1.5, whiteSpace: "pre-wrap", maxHeight: 200,
                    overflowY: "auto"
                  }}>
                    {routerContent.reasoning_content}
                  </div>
                )}
              </div>
            )}
            {/* Response content */}
            <div style={{ color: "#e2e8f0", fontSize: 12, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
              {routerContent.content}
            </div>
          </div>
        )}
        {messages.length === 0 && !loading && !routerContent && (
          <div style={{ color: "#334155", fontSize: 12, textAlign: "center", marginTop: 40 }}>
            No messages yet
          </div>
        )}
        {messages.map(m => <MessageBubble key={m.id} msg={m} />)}
        {loading && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, padding: "8px 12px",
            color: agent.color, fontSize: 12
          }}>
            <span style={{
              display: "inline-block", width: 8, height: 8, borderRadius: "50%",
              background: agent.color, animation: "pulse 1s ease-in-out infinite"
            }} />
            {agent.name === "hermes-r1"
              ? r1Elapsed < 2
                ? "Submitting to R1\u2026"
                : r1Elapsed < 8
                ? "Reasoning in progress\u2026"
                : `Reasoning: ${r1Elapsed}s`
              : "Thinking..."}
          </div>
        )}
        {(agent.name === "hermes-r1" || agent.name === "hermes-v4pro") && !loading && messages.length > 0 && (
          <div style={{ padding: "0 12px 8px", display: "flex", gap: 6, flexWrap: "wrap" }}>
            {agent.name === "hermes-r1" && (
              <button onClick={async () => {
                if (!threadId) return;
                const lastMsg = messages[messages.length - 1];
                try {
                  await fetch("/api/advisor/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      agent: "hermes-v4pro", thread_id: threadId,
                      content: "R1 produced this reasoning. Critique it:\n\n" + (lastMsg?.content || "")
                    })
                  });
                  if (onCritiqueV4Pro) onCritiqueV4Pro();
                } catch (e) { console.error("Critique send failed", e); }
              }}
                style={{
                  padding: "3px 8px", background: "#8b5cf622", border: "1px solid #8b5cf644",
                  borderRadius: 4, color: "#8b5cf6", fontSize: 10, cursor: "pointer"
                }}>Send to V4-Pro for critique</button>
            )}
            {agent.name === "hermes-r1" && (
              <button onClick={() => {
                const lastIdx = messages.length - 1;
                setMessages(prev => prev.map((m, i) => i === lastIdx ? { ...m, markedForRecon: true } : m));
              }}
                style={{
                  padding: "3px 8px", background: "#f59e0b22", border: "1px solid #f59e0b44",
                  borderRadius: 4, color: "#f59e0b", fontSize: 10, cursor: "pointer"
                }}>Mark for reconciliation</button>
            )}
            {messages[messages.length - 1]?.markedForRecon && (
              <span style={{ color: "#f59e0b", fontSize: 9, alignSelf: "center" }}>\u2713 Marked</span>
            )}
            <button onClick={() => {
              const lastMsg = messages[messages.length - 1];
              if (onEscalate) onEscalate(agent.name, lastMsg?.content);
            }}
              style={{
                padding: "3px 8px", background: "#f9731622", border: "1px solid #f9731644",
                borderRadius: 4, color: "#f97316", fontSize: 10, cursor: "pointer"
              }}>Escalate \u2192</button>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {mode === "parallel" && !disabled ? (
        <div style={{ padding: 8, borderTop: "1px solid #1e293b", textAlign: "center", color: "#64748b", fontSize: 11 }}>
          {agent.name === "hermes-r1" || agent.name === "hermes-v4pro"
            ? "Deliberating \u2014 R1 + V4-Pro"
            : agent.name === "hermes-prime"
              ? "Prime is not part of deliberation \u2014 use Direct for conversation."
              : "Worker receives final directives only \u2014 not part of deliberation."}
        </div>
      ) : (
        <div style={{
          padding: 8, borderTop: "1px solid #1e293b",
          display: "flex", gap: 6, background: "#0a0f1e"
        }}>
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }}}
            placeholder={disabled ? "Select a thread first" : agent.name === "hermes-r1" ? "Ask R1 something hard\u2026" : `Message ${agent.label}...`}
            disabled={disabled || loading}
            rows={2}
            style={{
              flex: 1, background: "#0f172a", border: "1px solid #1e293b",
              borderRadius: 6, color: "#e2e8f0", padding: "6px 10px",
              fontSize: 12, resize: "none", outline: "none",
              opacity: disabled ? 0.4 : 1
            }}
          />
          <button
            onClick={send}
            disabled={disabled || loading || !input.trim()}
            style={{
              padding: "6px 14px", background: agent.color,
              border: "none", borderRadius: 6, color: "#fff",
              fontSize: 12, cursor: "pointer", alignSelf: "flex-end",
              opacity: (disabled || loading || !input.trim()) ? 0.4 : 1
            }}
          >
            {loading ? "\u23f3" : "Send"}
          </button>
        </div>
      )}
    </div>
  );
}

export default function AdvisorChat() {
  const [threads, setThreads] = useState([]);
  const [activeThread, setActiveThread] = useState(null);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [mode, setMode] = useState("direct");
  const [lastBatchId, setLastBatchId] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [structuring, setStructuring] = useState(false);
  const [drafts, setDrafts] = useState([]);
  const [activeDraft, setActiveDraft] = useState(null);
  const [draftForm, setDraftForm] = useState(null);
  const [draftSaving, setDraftSaving] = useState(false);
  const [domainValues, setDomainValues] = useState(["creative","socialcare","personal","technical","learning"]);
  const [v4ProRefreshKey, setV4ProRefreshKey] = useState(0);
  const [externalReviews, setExternalReviews] = useState([]);
  const [reviewsExpanded, setReviewsExpanded] = useState(false);
  const [reviewForm, setReviewForm] = useState(null);
  const [editingReviewId, setEditingReviewId] = useState(null);
  const [reviewSaving, setReviewSaving] = useState(false);

  // Router state
  const [routerInput, setRouterInput] = useState("");
  const [routerOverride, setRouterOverride] = useState("");
  const [routerThreadId, setRouterThreadId] = useState(null);
  const [routerResponse, setRouterResponse] = useState(null);
  const [routerLoading, setRouterLoading] = useState(false);
  const [routerPanelContents, setRouterPanelContents] = useState({});

  useEffect(() => {
    fetch("/api/advisor/threads")
      .then(r => r.json())
      .then(threads => {
        setThreads(threads);
        if (threads.length > 0) setActiveThread(threads[0].id);
      });
    fetch("/api/app/domains").then(r => r.json()).then(d => { if (d && d.length) setDomainValues(d.map(x => x.name)); }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeThread) { setDrafts([]); return; }
    fetch(`/api/idea-drafts?thread_id=${activeThread}`)
      .then(r => r.json())
      .then(setDrafts)
      .catch(() => {});
  }, [activeThread]);

  useEffect(() => {
    if (!activeThread) { setExternalReviews([]); return; }
    fetch(`/api/advisor/external-reviews?thread_id=${activeThread}`)
      .then(r => r.json())
      .then(setExternalReviews)
      .catch(() => {});
  }, [activeThread]);

  const refreshReviews = async () => {
    if (!activeThread) return;
    const res = await fetch(`/api/advisor/external-reviews?thread_id=${activeThread}`);
    setExternalReviews(await res.json());
  };

  const handleEscalate = async (agentName, agentResponse) => {
    if (!activeThread) return;
    const target = "claude";
    const res = await fetch("/api/advisor/escalation-prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: activeThread, target,
        context_note: `${agentName} response:\n${agentResponse?.slice(0, 500) || ""}`
      })
    });
    const data = await res.json();
    setReviewForm({
      source: target,
      escalation_prompt: data.prompt_text || "",
      response_text: "",
      recommendation_summary: "",
      risks: "",
      proposed_next_action: "",
      verdict: "unclear"
    });
    setEditingReviewId(null);
    setReviewsExpanded(true);
  };

  const handleSaveReview = async () => {
    if (!reviewForm || !activeThread || reviewSaving) return;
    setReviewSaving(true);
    try {
      const url = editingReviewId
        ? `/api/advisor/external-reviews/${editingReviewId}`
        : "/api/advisor/external-reviews";
      const method = editingReviewId ? "PATCH" : "POST";
      const body = editingReviewId
        ? { recommendation_summary: reviewForm.recommendation_summary,
            risks: reviewForm.risks,
            proposed_next_action: reviewForm.proposed_next_action,
            verdict: reviewForm.verdict, response_text: reviewForm.response_text }
        : reviewForm;
      await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editingReviewId ? body : { ...body, thread_id: activeThread })
      });
      await refreshReviews();
      setReviewForm(null);
      setEditingReviewId(null);
    } catch (e) { console.error("Review save failed", e); }
    setReviewSaving(false);
  };

  const handleStartReview = () => {
    setReviewForm({
      source: "claude",
      escalation_prompt: "",
      response_text: "",
      recommendation_summary: "",
      risks: "",
      proposed_next_action: "",
      verdict: "unclear"
    });
    setEditingReviewId(null);
    setReviewsExpanded(true);
  };

  const createThread = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    const res = await fetch("/api/advisor/threads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTitle.trim() })
    });
    const t = await res.json();
    setThreads(prev => [{ id: t.id, title: newTitle.trim() }, ...prev]);
    setActiveThread(t.id);
    setNewTitle("");
    setCreating(false);
  };

  const executeDirective = async () => {
    if (!activeThread || executing) return;
    setExecuting(true);
    try {
      const res = await fetch("/api/advisor/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: activeThread })
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "Execute failed");
        setExecuting(false);
        return;
      }
      setExecuting("done");
      setTimeout(() => setExecuting(false), 2000);
    } catch (e) {
      console.error("Execute failed:", e);
      alert("Execute failed: " + e.message);
      setExecuting(false);
    }
  };

  const runReconciliation = async () => {
    if (!activeThread || !lastBatchId || reconciling) return;
    setReconciling(true);
    try {
      const res = await fetch("/api/reconciliation/reconcile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: activeThread, batch_id: lastBatchId })
      });
      const data = await res.json();
      if (data.ok) {
        setReconciliation(data);
      }
    } catch (e) {
      console.error("Reconciliation failed:", e);
    }
    setReconciling(false);
  };

  const structureThis = async () => {
    if (!activeThread || structuring) return;
    setStructuring(true);
    try {
      const res = await fetch("/api/idea-drafts/structure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: activeThread })
      });
      if (!res.ok) { const err = await res.json(); alert(err.error || "Structuring failed"); setStructuring(false); return; }
      const draft = await res.json();
      const refreshed = await fetch(`/api/idea-drafts?thread_id=${activeThread}`).then(r => r.json());
      setDrafts(refreshed);
      openDraft(draft);
    } catch (e) {
      alert("Structuring failed: " + e.message);
    }
    setStructuring(false);
  };

  const openDraft = async (draft) => {
    setActiveDraft(draft);
    setDraftForm({
      title: draft.title || "",
      summary: draft.summary || "",
      intent: draft.intent || "",
      domain: draft.domain || "creative",
      suggested_next_step: draft.suggested_next_step || ""
    });
    if (draft.status === "structured") {
      const res = await fetch(`/api/idea-drafts/${draft.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "reviewing" })
      });
      const updated = await res.json();
      setActiveDraft(updated);
    }
  };

  const saveDraft = async () => {
    if (!activeDraft || draftSaving) return;
    setDraftSaving(true);
    const res = await fetch(`/api/idea-drafts/${activeDraft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(draftForm)
    });
    const updated = await res.json();
    setActiveDraft(updated);
    fetch(`/api/idea-drafts?thread_id=${activeThread}`).then(r => r.json()).then(setDrafts);
    setDraftSaving(false);
  };

  const dismissDraft = async () => {
    if (!activeDraft) return;
    await fetch(`/api/idea-drafts/${activeDraft.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "dismissed" })
    });
    setActiveDraft(null);
    setDraftForm(null);
    fetch(`/api/idea-drafts?thread_id=${activeThread}`).then(r => r.json()).then(setDrafts);
  };

  // Router send
  const sendRouter = async () => {
    if (!routerInput.trim() || routerLoading) return;
    const text = routerInput.trim();
    setRouterInput("");
    setRouterLoading(true);
    setRouterResponse(null);

    try {
      const body = { message: text };
      if (routerThreadId) body.thread_id = routerThreadId;
      if (routerOverride) body.override = routerOverride;

      const res = await fetch("/api/advisor/route", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CIS-API-Key": API_KEY,
        },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      setRouterResponse(data);

      if (!routerThreadId && data.message_id) {
        setRouterThreadId(data.message_id);
      }

      if (data.agent_response && data.final_route) {
        const content = data.agent_response;
        setRouterPanelContents(prev => ({
          ...prev,
          [data.final_route]: content,
        }));
      }
    } catch (e) {
      console.error("Router send failed:", e);
      setRouterResponse({ error: e.message });
    }
    setRouterLoading(false);
  };

  const clearRouter = () => {
    setRouterThreadId(null);
    setRouterResponse(null);
    setRouterPanelContents({});
  };

  const handleRouterKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendRouter();
    }
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", height: "100%",
      background: "#020817", color: "#e2e8f0", fontFamily: "monospace"
    }}>
      {/* Header */}
      <div style={{
        padding: "12px 16px", borderBottom: "1px solid #1e293b",
        display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap"
      }}>
        <span style={{ fontWeight: 700, fontSize: 14, color: "#94a3b8" }}>
          Advisor Chat
        </span>

        <div style={{ display: "flex", background: "#0f172a", borderRadius: 6, overflow: "hidden", border: "1px solid #1e293b" }}>
          <button onClick={() => setMode("direct")}
            style={{
              padding: "3px 10px", border: "none", cursor: "pointer", fontSize: 11,
              background: mode === "direct" ? "#2563eb" : "transparent",
              color: mode === "direct" ? "#fff" : "#64748b",
              fontWeight: mode === "direct" ? 600 : 400
            }}>Direct</button>
          <button onClick={() => setMode("parallel")}
            style={{
              padding: "3px 10px", border: "none", cursor: "pointer", fontSize: 11,
              background: mode === "parallel" ? "#7c3aed" : "transparent",
              color: mode === "parallel" ? "#fff" : "#64748b",
              fontWeight: mode === "parallel" ? 600 : 400
            }}>Parallel</button>
        </div>

        <select
          value={activeThread || ""}
          onChange={e => setActiveThread(Number(e.target.value) || null)}
          style={{
            background: "#0f172a", border: "1px solid #1e293b",
            color: "#e2e8f0", borderRadius: 6, padding: "4px 8px", fontSize: 12
          }}
        >
          <option value="">{"\u2014"} select thread {"\u2014"}</option>
          {threads.map(t => (
            <option key={t.id} value={t.id}>{t.title || `Thread ${t.id}`}</option>
          ))}
        </select>

        <input
          value={newTitle}
          onChange={e => setNewTitle(e.target.value)}
          onKeyDown={e => e.key === "Enter" && createThread()}
          placeholder="New thread title..."
          style={{
            background: "#0f172a", border: "1px solid #1e293b",
            color: "#e2e8f0", borderRadius: 6, padding: "4px 8px",
            fontSize: 12, width: 180
          }}
        />
        <button
          onClick={createThread}
          disabled={creating || !newTitle.trim()}
          style={{
            padding: "4px 12px", background: "#1e293b",
            border: "1px solid #334155", borderRadius: 6,
            color: "#94a3b8", fontSize: 12, cursor: "pointer"
          }}
        >
          Create
        </button>

        <div style={{ flex: 1 }} />

        {activeThread && (
          <button
            onClick={executeDirective}
            disabled={!!executing}
            style={{
              padding: "4px 12px", background: reconciliation ? "#10b981" : "#475569",
              border: "none", borderRadius: 6, color: "#fff",
              fontSize: 12, cursor: "pointer",
              opacity: executing ? 0.6 : 1,
              fontFamily: "monospace", fontWeight: 600
            }}
          >
            {executing === true ? "Executing..." : executing === "done" ? "\u2713 Sent to Worker" : reconciliation ? "\u26a1 Execute" : "\u26a1 Execute (checks reconciliation)"}
          </button>
        )}

        {mode === "parallel" && lastBatchId && (
          <button
            onClick={runReconciliation}
            disabled={reconciling || !!reconciliation}
            style={{
              padding: "4px 12px", background: "#f59e0b",
              border: "none", borderRadius: 6, color: "#000",
              fontSize: 12, cursor: "pointer",
              opacity: (reconciling || reconciliation) ? 0.6 : 1,
              fontFamily: "monospace", fontWeight: 600
            }}
          >
            {reconciling ? "Reconciling..." : reconciliation ? "\u2713 Reconciled" : "\u21bb Reconcile"}
          </button>
        )}

        {activeThread && (
          <button
            onClick={structureThis}
            disabled={structuring || !activeThread}
            style={{
              padding: "4px 12px", background: "#06b6d4",
              border: "none", borderRadius: 6, color: "#000",
              fontSize: 12, cursor: "pointer",
              opacity: (structuring || !activeThread) ? 0.6 : 1,
              fontFamily: "monospace", fontWeight: 600
            }}
          >
            {structuring ? "Structuring..." : "Structure This"}
          </button>
        )}

      </div>

      {/* Shared Router Input */}
      <div style={{
        padding: "10px 12px", borderBottom: "1px solid #1e293b",
        background: "#0a0f1e", display: "flex", gap: 8, flexDirection: "column"
      }}>
        <span style={{ color: "#64748b", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".05em" }}>
          Router Input — messages are classified and sent to the appropriate agent.
        </span>
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end", flexWrap: "wrap" }}>
        <textarea
          value={routerInput}
          onChange={e => setRouterInput(e.target.value)}
          onKeyDown={handleRouterKeyDown}
          placeholder="Type a message \u2014 router classifies and dispatches\u2026"
          disabled={routerLoading}
          rows={2}
          style={{
            flex: 1, minWidth: 200, background: "#0f172a",
            border: "1px solid #1e293b", borderRadius: 6,
            color: "#e2e8f0", padding: "6px 10px",
            fontSize: 12, resize: "none", outline: "none",
            opacity: routerLoading ? 0.5 : 1
          }}
        />
        <select
          value={routerOverride}
          onChange={e => setRouterOverride(e.target.value)}
          style={{
            background: "#0f172a", border: "1px solid #1e293b",
            color: "#e2e8f0", borderRadius: 6, padding: "6px 8px",
            fontSize: 11, maxWidth: 200
          }}
        >
          {OVERRIDE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          onClick={sendRouter}
          disabled={routerLoading || !routerInput.trim()}
          style={{
            padding: "8px 18px", background: "#2563eb",
            border: "none", borderRadius: 6, color: "#fff",
            fontSize: 12, fontWeight: 600, cursor: "pointer",
            opacity: (routerLoading || !routerInput.trim()) ? 0.4 : 1,
            whiteSpace: "nowrap"
          }}
        >
          {routerLoading ? "Routing\u2026" : "Send"}
        </button>
        {routerThreadId && (
          <button
            onClick={clearRouter}
            style={{
              padding: "6px 10px", background: "#1e293b",
              border: "1px solid #334155", borderRadius: 6,
              color: "#64748b", fontSize: 10, cursor: "pointer",
              whiteSpace: "nowrap"
            }}
          >
            Clear
          </button>
        )}
        </div>
      </div>

      {/* Routing Banner */}
      {routerResponse && !routerResponse.error && (
        <div style={{
          margin: "4px 12px", padding: "8px 14px",
          background: "#0f172a", border: "1px solid #1e293b",
          borderRadius: 6, display: "flex", alignItems: "center",
          gap: 10, flexWrap: "wrap", fontSize: 11
        }}>
          <span style={{
            padding: "2px 8px", borderRadius: 4,
            background: "#2563eb22", border: "1px solid #2563eb44",
            color: "#60a5fa", fontWeight: 600, fontSize: 10
          }}>
            {ROUTE_LABELS[routerResponse.final_route || routerResponse.route] || routerResponse.route}
          </span>

          {routerResponse.confidence === "medium" && (
            <span style={{ color: "#f59e0b", fontSize: 10 }}>medium confidence</span>
          )}
          {routerResponse.confidence === "low" && (
            <span style={{ color: "#ef4444", fontSize: 10 }}>low confidence {"\u2014"} defaulted to V4 Drafter</span>
          )}
          {routerResponse.confidence === "override" && (
            <span style={{ color: "#8b5cf6", fontSize: 10, fontWeight: 600 }}>manual override</span>
          )}

          {(routerResponse.signals_matched || []).slice(0, 4).map(s => (
            <span key={s} style={{
              padding: "1px 6px", borderRadius: 3,
              background: "#334155", color: "#94a3b8",
              fontSize: 9, fontFamily: "monospace"
            }}>{s}</span>
          ))}

          {routerResponse.reason && (
            <span style={{ color: "#64748b", fontSize: 10, flexBasis: "100%" }}>
              {routerResponse.reason}
            </span>
          )}

          {routerResponse.next_suggested_action && (
            <span style={{ color: "#475569", fontSize: 9, flexBasis: "100%" }}>
              {"\u2192"} {routerResponse.next_suggested_action}
            </span>
          )}

          {routerResponse.preflight_response && (
            <span style={{
              padding: "1px 6px", borderRadius: 3,
              background: "#06b6d422", border: "1px solid #06b6d444",
              color: "#22d3ee", fontSize: 9
            }}>NeMo preflight ran</span>
          )}

          {routerThreadId && (
            <span style={{ color: "#334155", fontSize: 9, marginLeft: "auto", fontFamily: "monospace" }}>
              tid:{routerThreadId.slice(0, 8)}
            </span>
          )}
        </div>
      )}

      {routerResponse?.error && (
        <div style={{
          margin: "4px 12px", padding: "6px 12px",
          background: "#7f1d1d22", border: "1px solid #7f1d1d44",
          borderRadius: 6, color: "#fca5a5", fontSize: 11
        }}>
          Router error: {routerResponse.error}
        </div>
      )}

      {/* Draft review panel */}
      {activeDraft && draftForm && (
        <div style={{
          margin: "0 8px 8px", padding: "16px",
          background: "#0f172a", border: "1px solid #06b6d444",
          borderRadius: 8, maxHeight: 360, overflowY: "auto"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <span style={{ color: "#06b6d4", fontWeight: 600, fontSize: 13 }}>Idea Draft</span>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={saveDraft} disabled={draftSaving}
                style={{ padding: "4px 10px", background: "#10b981", border: "none", borderRadius: 4, color: "#fff", fontSize: 11, cursor: "pointer" }}>
                {draftSaving ? "Saving..." : "Save"}
              </button>
              <button onClick={dismissDraft}
                style={{ padding: "4px 10px", background: "#ef4444", border: "none", borderRadius: 4, color: "#fff", fontSize: 11, cursor: "pointer" }}>
                Dismiss
              </button>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div>
              <label style={{ color: "#64748b", fontSize: 10, display: "block", marginBottom: 2 }}>Title</label>
              <input value={draftForm.title} onChange={e => setDraftForm({...draftForm, title: e.target.value})}
                style={{ width: "100%", background: "#1e293b", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 12, outline: "none" }} />
            </div>

            <div>
              <label style={{ color: "#64748b", fontSize: 10, display: "block", marginBottom: 2 }}>Summary</label>
              <textarea value={draftForm.summary} onChange={e => setDraftForm({...draftForm, summary: e.target.value})}
                rows={3}
                style={{ width: "100%", background: "#1e293b", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 12, resize: "vertical", outline: "none" }} />
            </div>

            <div style={{ display: "flex", gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={{ color: "#64748b", fontSize: 10, display: "block", marginBottom: 2 }}>
                  Domain {activeDraft.domain_source === "ai_suggested" ? "(AI suggested)" : "(confirmed)"}
                </label>
                <select value={draftForm.domain} onChange={e => setDraftForm({...draftForm, domain: e.target.value})}
                  style={{ width: "100%", background: "#1e293b", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 12, outline: "none" }}>
                  {domainValues.map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label style={{ color: "#64748b", fontSize: 10, display: "block", marginBottom: 2 }}>Intent</label>
              <textarea value={draftForm.intent} onChange={e => setDraftForm({...draftForm, intent: e.target.value})}
                rows={2}
                style={{ width: "100%", background: "#1e293b", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 12, resize: "vertical", outline: "none" }} />
            </div>

            {activeDraft.open_questions && (() => {
              try { const oq = JSON.parse(activeDraft.open_questions); if (Array.isArray(oq) && oq.length > 0) return (
                <div>
                  <label style={{ color: "#64748b", fontSize: 10, display: "block", marginBottom: 2 }}>Open Questions</label>
                  {oq.map((q, i) => <div key={i} style={{ color: "#94a3b8", fontSize: 11, padding: "2px 0" }}>{"\u2022"} {q}</div>)}
                </div>
              ); } catch(e) {}
              return null;
            })()}

            <div>
              <label style={{ color: "#64748b", fontSize: 10, display: "block", marginBottom: 2 }}>Suggested Next Step</label>
              <input value={draftForm.suggested_next_step} onChange={e => setDraftForm({...draftForm, suggested_next_step: e.target.value})}
                style={{ width: "100%", background: "#1e293b", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 12, outline: "none" }} />
            </div>

            <div style={{ borderTop: "1px solid #1e293b", paddingTop: 8, marginTop: 4 }}>
              <span style={{ color: "#475569", fontSize: 10 }}>
                Structured by {activeDraft.structuring_agent} from thread #{activeDraft.source_thread_id}
                {" \u00b7 "}{(() => { try { return JSON.parse(activeDraft.source_message_ids).length; } catch(e) { return "?"; } })()} messages
                {" \u00b7 "}{activeDraft.created_at?.slice(0, 16) || ""}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Four panels — 2x2 grid */}
      <div style={{
        flex: 1, display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gridTemplateRows: "1fr 1fr",
        gap: 8, padding: 8,
        minHeight: 0, overflow: "hidden"
      }}>
        {AGENTS.map(agent => (
          <AgentPanel
            key={agent.name}
            agent={agent}
            threadId={activeThread}
            disabled={!activeThread}
            mode={mode}
            refreshKey={agent.name === "hermes-v4pro" ? v4ProRefreshKey : 0}
            onCritiqueV4Pro={() => setV4ProRefreshKey(k => k + 1)}
            onEscalate={handleEscalate}
            routerContent={routerPanelContents[agent.route] || null}
          />
        ))}
      </div>

      {/* External Reviews */}
      {activeThread && (
        <div style={{ margin: "0 8px 8px", border: "1px solid #f9731644", borderRadius: 8, overflow: "hidden" }}>
          <div onClick={() => setReviewsExpanded(!reviewsExpanded)}
            style={{
              padding: "8px 12px", background: "#f9731610", cursor: "pointer",
              display: "flex", alignItems: "center", gap: 8, userSelect: "none"
            }}>
            <span style={{ color: "#f97316", fontWeight: 600, fontSize: 12 }}>
              {reviewsExpanded ? "\u25bc" : "\u25b6"} External Reviews ({externalReviews.length})
            </span>
            {!reviewsExpanded && (
              <button onClick={e => { e.stopPropagation(); handleStartReview(); }}
                style={{
                  marginLeft: "auto", padding: "2px 8px", background: "#f9731622",
                  border: "1px solid #f9731644", borderRadius: 4, color: "#f97316",
                  fontSize: 10, cursor: "pointer"
                }}>+ Add</button>
            )}
          </div>
          {reviewsExpanded && (
            <div style={{ padding: 12, background: "#0f172a", maxHeight: 400, overflowY: "auto" }}>
              {reviewForm && (
                <div style={{
                  marginBottom: 12, padding: 12, background: "#1e293b",
                  border: "1px solid #334155", borderRadius: 6
                }}>
                  <div style={{ fontSize: 11, color: "#f97316", fontWeight: 600, marginBottom: 8 }}>
                    {editingReviewId ? "Edit Review" : "Add Review"}
                  </div>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <select value={reviewForm.source} onChange={e => setReviewForm({...reviewForm, source: e.target.value})}
                      style={{ background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", borderRadius: 4, padding: "3px 6px", fontSize: 11 }}>
                      <option value="claude">Claude</option>
                      <option value="chatgpt">ChatGPT</option>
                      <option value="other">Other</option>
                    </select>
                    <select value={reviewForm.verdict} onChange={e => setReviewForm({...reviewForm, verdict: e.target.value})}
                      style={{ background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", borderRadius: 4, padding: "3px 6px", fontSize: 11 }}>
                      <option value="unclear">Unclear</option>
                      <option value="approve">Approve</option>
                      <option value="revise">Revise</option>
                      <option value="reject">Reject</option>
                    </select>
                  </div>
                  <textarea value={reviewForm.escalation_prompt} onChange={e => setReviewForm({...reviewForm, escalation_prompt: e.target.value})}
                    placeholder="Escalation prompt sent to model..."
                    rows={3}
                    style={{ width: "100%", background: "#0f172a", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 11, resize: "vertical", outline: "none", marginBottom: 8, fontFamily: "monospace" }} />
                  <textarea value={reviewForm.response_text} onChange={e => setReviewForm({...reviewForm, response_text: e.target.value})}
                    placeholder="Paste model response here..."
                    rows={5}
                    style={{ width: "100%", background: "#0f172a", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "6px 8px", fontSize: 11, resize: "vertical", outline: "none", marginBottom: 8, fontFamily: "monospace" }} />
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <input value={reviewForm.recommendation_summary || ""} onChange={e => setReviewForm({...reviewForm, recommendation_summary: e.target.value})}
                      placeholder="Recommendation summary"
                      style={{ flex: 1, background: "#0f172a", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "4px 6px", fontSize: 10, outline: "none" }} />
                  </div>
                  <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                    <input value={reviewForm.risks || ""} onChange={e => setReviewForm({...reviewForm, risks: e.target.value})}
                      placeholder="Risks"
                      style={{ flex: 1, background: "#0f172a", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "4px 6px", fontSize: 10, outline: "none" }} />
                    <input value={reviewForm.proposed_next_action || ""} onChange={e => setReviewForm({...reviewForm, proposed_next_action: e.target.value})}
                      placeholder="Next action"
                      style={{ flex: 1, background: "#0f172a", border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", padding: "4px 6px", fontSize: 10, outline: "none" }} />
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button onClick={handleSaveReview} disabled={reviewSaving || !reviewForm.response_text.trim()}
                      style={{
                        padding: "4px 12px", background: "#f97316", border: "none", borderRadius: 4,
                        color: "#fff", fontSize: 11, cursor: "pointer", opacity: (!reviewForm.response_text.trim()) ? 0.4 : 1
                      }}>{reviewSaving ? "Saving..." : "Save"}</button>
                    <button onClick={() => { setReviewForm(null); setEditingReviewId(null); }}
                      style={{ padding: "4px 12px", background: "#1e293b", border: "1px solid #334155", borderRadius: 4, color: "#94a3b8", fontSize: 11, cursor: "pointer" }}>Cancel</button>
                    <div style={{ flex: 1 }} />
                    <button onClick={handleStartReview}
                      style={{ padding: "4px 10px", background: "#f9731622", border: "1px solid #f9731644", borderRadius: 4, color: "#f97316", fontSize: 10, cursor: "pointer" }}>+ Add Review</button>
                  </div>
                </div>
              )}
              {!reviewForm && (
                <button onClick={handleStartReview}
                  style={{
                    width: "100%", padding: "6px", background: "#f9731608", border: "1px dashed #f9731644",
                    borderRadius: 4, color: "#f97316", fontSize: 11, cursor: "pointer", marginBottom: 8
                  }}>+ Add Review</button>
              )}
              {externalReviews.map(r => (
                <div key={r.id} style={{
                  marginBottom: 8, padding: 10, background: "#0f172a",
                  border: "1px solid #1e293b", borderRadius: 6
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                    <span style={{
                      padding: "1px 6px", borderRadius: 3, fontSize: 9, fontWeight: 600,
                      background: r.source === "claude" ? "#f9731622" : "#10b98122",
                      color: r.source === "claude" ? "#f97316" : "#10b981"
                    }}>{r.source}</span>
                    <span style={{
                      padding: "1px 6px", borderRadius: 3, fontSize: 9,
                      background: r.verdict === "approve" ? "#10b98122" : r.verdict === "reject" ? "#ef444422" : r.verdict === "revise" ? "#f59e0b22" : "#64748b22",
                      color: r.verdict === "approve" ? "#10b981" : r.verdict === "reject" ? "#ef4444" : r.verdict === "revise" ? "#f59e0b" : "#64748b"
                    }}>{r.verdict}</span>
                    <span style={{ color: "#475569", fontSize: 9 }}>{r.created_at?.slice(0, 16)}</span>
                    <button onClick={() => {
                      setReviewForm({
                        source: r.source, escalation_prompt: r.escalation_prompt,
                        response_text: r.response_text,
                        recommendation_summary: r.recommendation_summary || "",
                        risks: r.risks || "", proposed_next_action: r.proposed_next_action || "",
                        verdict: r.verdict
                      });
                      setEditingReviewId(r.id);
                      setReviewsExpanded(true);
                    }}
                      style={{
                        marginLeft: "auto", padding: "2px 6px", background: "transparent",
                        border: "1px solid #334155", borderRadius: 3, color: "#64748b",
                        fontSize: 9, cursor: "pointer"
                      }}>Edit</button>
                  </div>
                  <div style={{ color: "#cbd5e1", fontSize: 11, lineHeight: 1.4 }}>
                    {r.recommendation_summary || r.response_text?.slice(0, 120) + (r.response_text?.length > 120 ? "\u2026" : "")}
                  </div>
                </div>
              ))}
              {externalReviews.length === 0 && !reviewForm && (
                <div style={{ color: "#334155", fontSize: 11, textAlign: "center", padding: 12 }}>
                  No external reviews yet. Paste Claude or ChatGPT responses here.
                </div>
              )}
            </div>
          )}
        </div>
      )}
      {reconciliation && (
        <div style={{
          margin: "0 8px 8px", padding: "12px",
          background: "#0f172a", border: "1px solid #f59e0b44",
          borderRadius: 8, maxHeight: 200, overflowY: "auto"
        }}>
          <div style={{ color: "#f59e0b", fontWeight: 600, fontSize: 12, marginBottom: 8 }}>
            {"\u21bb"} Reconciliation
            <span style={{ color: "#64748b", fontWeight: 400, marginLeft: 8, fontSize: 10 }}>
              Confidence: {reconciliation.reconciliation_json?.confidence || "\u2014"}
              {reconciliation.external_reviews_included > 0 && (
                <span> {"\u00b7"} {reconciliation.external_reviews_included} external review{reconciliation.external_reviews_included !== 1 ? "s" : ""} included</span>
              )}
            </span>
          </div>
          <div style={{ color: "#e2e8f0", fontSize: 12, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
            {reconciliation.synthesis_content}
          </div>
        </div>
      )}
      <style>{`@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }`}</style>
    </div>
  );
}
