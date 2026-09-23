import { useEffect, useRef, useState } from "react";
import {
  listProjects,
  createProject,
  listMessages,
  sendMessage,
  updateDirectionNote,
  listProposals,
  listRuns,
} from "./api";
import { getRequestId, clearRequestId } from "./requestId";
import ProposalPanel from "./ProposalPanel";
import CardFactory from "./CardFactory";
import SystemContext from "./SystemContext";

const LAST_PROJECT_KEY = "cis-workbench-last-project";
const draftKey = (projectId) => `cis-workbench-draft-${projectId}`;

function StatusBadge({ status }) {
  const map = {
    pending: ["Waiting…", "status-pending"],
    completed: ["", ""],
    failed: ["Failed", "status-failed"],
    interrupted: ["Interrupted", "status-interrupted"],
  };
  const [label, cls] = map[status] || [status, ""];
  if (!label) return null;
  return <span className={`status-badge ${cls}`}>{label}</span>;
}

function ContextPanel({ kbContext, limitations }) {
  const [open, setOpen] = useState(false);
  if (!kbContext || kbContext.length === 0) return null;
  return (
    <div className="context-panel">
      <button
        type="button"
        className="context-toggle"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? "Hide" : "Show"} {kbContext.length} source excerpt{kbContext.length === 1 ? "" : "s"} sent with this request
      </button>
      {open && (
        <div className="context-body">
          {kbContext.map((hit, i) => (
            <div className="context-hit" key={i}>
              <div className="context-source">{hit.source || "(no stable id)"}</div>
              <div className="context-excerpt">{hit.content}</div>
            </div>
          ))}
          {limitations && <div className="context-limitations">{limitations}</div>}
        </div>
      )}
    </div>
  );
}

function ProjectSwitcher({ projects, activeId, onSelect, onCreate, busy }) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function submitCreate(e) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name your project first.");
      return;
    }
    setError("");
    const result = await onCreate(name.trim());
    if (result.ok) {
      setName("");
      setCreating(false);
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="project-switcher">
      <div className="project-list">
        {projects.map((p) => (
          <button
            key={p.id}
            className={`project-item ${p.id === activeId ? "active" : ""}`}
            onClick={() => onSelect(p.id)}
          >
            {p.name}
          </button>
        ))}
      </div>
      {creating ? (
        <form className="project-create-form" onSubmit={submitCreate}>
          <input
            autoFocus
            placeholder="Project name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={busy}
          />
          <div className="project-create-actions">
            <button type="submit" disabled={busy}>Create</button>
            <button type="button" onClick={() => { setCreating(false); setError(""); }}>
              Cancel
            </button>
          </div>
          {error && <div className="inline-error">{error}</div>}
        </form>
      ) : (
        <button className="project-new-btn" onClick={() => setCreating(true)}>
          + New project
        </button>
      )}
    </div>
  );
}

function DirectionNote({ project, onSave }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(project.direction_note || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setValue(project.direction_note || "");
    setEditing(false);
  }, [project.id]);

  async function save() {
    setSaving(true);
    setError("");
    const result = await onSave(value);
    setSaving(false);
    if (result.ok) {
      setEditing(false);
    } else {
      setError(result.error);
    }
  }

  if (!editing) {
    return (
      <div className="direction-note">
        <span className="direction-note-text">
          {project.direction_note || "No direction note yet."}
        </span>
        <button className="link-btn" onClick={() => setEditing(true)}>Edit</button>
      </div>
    );
  }
  return (
    <div className="direction-note editing">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        maxLength={4000}
        rows={2}
        placeholder="Optional: a short note on the direction for this project."
      />
      <div className="direction-note-actions">
        <button onClick={save} disabled={saving}>{saving ? "Saving…" : "Save"}</button>
        <button onClick={() => { setEditing(false); setValue(project.direction_note || ""); }}>
          Cancel
        </button>
      </div>
      {error && <div className="inline-error">{error}</div>}
    </div>
  );
}

function UsageTotals({ project }) {
  const [totals, setTotals] = useState(null);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!project) return;
    listRuns(project.name).then((result) => {
      if (!result.ok) {
        setError(result.error);
        return;
      }
      setError("");
      setTotals(result.data.totals_by_project?.[project.name] || null);
    });
  }, [project?.name]);

  if (error) return <div className="inline-error">Usage totals unavailable: {error}</div>;
  if (!totals) return null;
  const gen = totals.generation;

  return (
    <div className="usage-totals">
      <button className="context-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide" : "Show"} usage totals for this project
      </button>
      {open && (
        <div className="context-body">
          <div>Generate (card drafting) attempts: {gen?.generate_attempts ?? 0}
            {gen?.unknown_usage_attempts ? ` (${gen.unknown_usage_attempts} with unknown usage)` : ""}</div>
          <div>Implement/Review runs: {totals.runs}
            {totals.unknown_usage_runs ? ` (${totals.unknown_usage_runs} with unknown usage)` : ""}</div>
          <div>Total tokens: {(totals.input_tokens || 0) + (gen?.input_tokens || 0)} in /{" "}
            {(totals.output_tokens || 0) + (gen?.output_tokens || 0)} out</div>
          <div>Total API-dollar estimate: ${((totals.cost_usd || 0) + (gen?.cost_usd || 0)).toFixed(4)}
            {" "}(not subscription quota)</div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("conversation");
  const [projects, setProjects] = useState(null);
  const [activeId, setActiveId] = useState(() => localStorage.getItem(LAST_PROJECT_KEY) || null);
  const [messages, setMessages] = useState(null);
  const [messagesError, setMessagesError] = useState("");
  const [proposals, setProposals] = useState([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const [loadError, setLoadError] = useState("");
  const pollRef = useRef(null);

  async function loadProjects(selectId) {
    const result = await listProjects();
    if (!result.ok) {
      setLoadError(result.error);
      return;
    }
    setLoadError("");
    setProjects(result.data.projects);
    const wanted = selectId || activeId;
    const stillExists = result.data.projects.some((p) => p.id === wanted);
    if (stillExists) {
      setActiveId(wanted);
    } else if (result.data.projects.length > 0) {
      setActiveId(result.data.projects[0].id);
    } else {
      setActiveId(null);
    }
  }

  async function loadMessages(projectId) {
    if (!projectId) {
      setMessages([]);
      return;
    }
    const result = await listMessages(projectId);
    if (!result.ok) {
      setMessagesError(result.error);
      return;
    }
    setMessagesError("");
    setMessages(result.data.messages);
  }

  async function loadProposals(projectId) {
    if (!projectId) {
      setProposals([]);
      return;
    }
    const result = await listProposals(projectId);
    if (result.ok) setProposals(result.data.proposals);
  }

  // Consumed by ProposalPanel after every confirm/approve so the list this
  // component owns — and therefore the `proposal` prop ProposalPanel
  // actually renders from — never lags behind what the server just wrote.
  function handleProposalUpdated(updated) {
    setProposals((prev) => {
      const exists = prev.some((p) => p.id === updated.id);
      return exists ? prev.map((p) => (p.id === updated.id ? updated : p)) : [updated, ...prev];
    });
  }

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (activeId) localStorage.setItem(LAST_PROJECT_KEY, activeId);
    loadMessages(activeId);
    loadProposals(activeId);
    setDraft(localStorage.getItem(draftKey(activeId)) || "");
  }, [activeId]);

  useEffect(() => {
    if (!activeId) return;
    if (draft) localStorage.setItem(draftKey(activeId), draft);
    else localStorage.removeItem(draftKey(activeId));
  }, [draft, activeId]);

  // Reload recovery for a reply still 'pending' when the page was closed:
  // poll briefly after a fresh load if the last message is pending.
  useEffect(() => {
    if (!messages || messages.length === 0) return;
    const last = messages[messages.length - 1];
    if (last.status !== "pending") {
      clearInterval(pollRef.current);
      return;
    }
    pollRef.current = setInterval(() => loadMessages(activeId), 4000);
    return () => clearInterval(pollRef.current);
  }, [messages, activeId]);

  async function handleCreate(name) {
    const result = await createProject(name);
    if (result.ok) {
      await loadProjects(result.data.project.id);
    }
    return result;
  }

  // Single entry point for every conversational turn — plain chat, asking
  // for a proposal, or correcting one. request_id is generated once and
  // persisted before the network call, so a failed send or a reload mid-
  // flight can retry with the SAME id and rely on the server's own dedup
  // rather than risking a second model call.
  async function handleSend(text, { mode = "chat", proposalId = null } = {}) {
    if (!text || sending || !activeId) return { ok: false, error: "nothing to send" };
    setSending(true);
    setSendError("");
    // Bound to project + mode + proposal + the exact text: retrying this
    // same attempt (a failed send, or a reload mid-flight) reuses this id;
    // editing the draft or targeting a different proposal mints a new one.
    const requestId = getRequestId("send", activeId, { mode, proposalId, text });

    if (mode === "chat") {
      setMessages((prev) => [
        ...(prev || []),
        { id: `local-${requestId}`, role: "user", content: text, status: "completed", created_at: "" },
        { id: `local-brain-${requestId}`, role: "brain", content: null, status: "pending", created_at: "" },
      ]);
      setDraft("");
    }

    const result = await sendMessage(activeId, text, requestId, { mode, proposalId });
    setSending(false);
    if (!result.ok) {
      setSendError(result.error);
      if (mode === "chat") setDraft(text); // recoverable draft — nothing typed is lost on failure
      await loadMessages(activeId);
      return result; // request_id kept in storage — a retry reuses it
    }
    clearRequestId("send", activeId);
    if (proposalId == null) setDraft("");
    await loadMessages(activeId);
    await loadProposals(activeId);
    if (result.data?.proposal_error) {
      // The conversational reply itself succeeded (HTTP 200) but applying
      // it to the proposal did not — e.g. the correction pushed
      // success_criteria over card_factory_app's own length bound. Must
      // never be read as a plain success: surfaced as an error, and the
      // correction text is kept (not cleared) by the caller.
      setSendError(result.data.proposal_error);
      return { ...result, ok: false, error: result.data.proposal_error };
    }
    return result;
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(draft.trim(), { mode: "chat" });
    }
  }

  const activeProject = projects?.find((p) => p.id === activeId) || null;

  // Each proposal is displayed right after the most recent message that
  // created or corrected it (the last id in its own source_message_ids) —
  // a correction moves the card forward in the conversation instead of
  // leaving a stale copy behind.
  const proposalByAnchor = {};
  for (const p of proposals) {
    const ids = p.source_message_ids || [];
    if (ids.length === 0) continue;
    proposalByAnchor[Math.max(...ids)] = p;
  }

  if (view === "cardfactory") {
    return <CardFactory onBack={() => setView("conversation")} />;
  }

  if (view === "recovery") {
    return <SystemContext onBack={() => setView("conversation")} />;
  }

  return (
    <div className="workbench">
      <header className="stage-banner">
        <span className="stage-label">Stage: Exploration</span>
        <span className="stage-detail">
          Braingate can clarify and propose here. Nothing runs until you explicitly approve it.
        </span>
        <button className="link-btn" onClick={() => setView("recovery")} style={{ marginLeft: "auto" }}>
          System Context / Recovery →
        </button>
        <button className="link-btn" onClick={() => setView("cardfactory")}>
          Card Factory (direct requests) →
        </button>
      </header>

      {loadError && <div className="banner-error">Could not load projects: {loadError}</div>}

      <div className="workbench-body">
        <aside className="sidebar">
          {projects === null ? (
            <div className="muted">Loading projects…</div>
          ) : (
            <ProjectSwitcher
              projects={projects}
              activeId={activeId}
              onSelect={setActiveId}
              onCreate={handleCreate}
              busy={sending}
            />
          )}
        </aside>

        <main className="conversation-pane">
          {!activeProject ? (
            <div className="empty-state">
              {projects === null ? "" : "Create a project to start a conversation with Braingate."}
            </div>
          ) : (
            <>
              <div className="conversation-header">
                <h1>{activeProject.name}</h1>
                <DirectionNote
                  project={activeProject}
                  onSave={(note) => updateDirectionNote(activeProject.id, note).then((r) => {
                    if (r.ok) setProjects((prev) => prev.map((p) => p.id === r.data.project.id ? r.data.project : p));
                    return r;
                  })}
                />
                <UsageTotals project={activeProject} />
              </div>

              {messagesError && (
                <div className="banner-error">
                  Could not load conversation: {messagesError}
                </div>
              )}

              <div className="message-list">
                {messages === null ? (
                  <div className="muted">Loading conversation…</div>
                ) : messages.length === 0 ? (
                  <div className="empty-state">No messages yet. Say what you're thinking about.</div>
                ) : (
                  messages.map((m) => (
                    <div key={m.id}>
                      <div className={`message message-${m.role}`}>
                        <div className="message-meta">
                          <span className="message-role">{m.role === "user" ? "You" : "Braingate"}</span>
                          <StatusBadge status={m.status} />
                        </div>
                        {m.status === "pending" && (
                          <div className="message-content pending">Waiting for a response…</div>
                        )}
                        {m.status === "failed" && (
                          <div className="message-content failed">
                            No response was received. {m.error || "The provider call failed."}
                          </div>
                        )}
                        {m.status === "interrupted" && (
                          <div className="message-content interrupted">
                            {m.error || "This response was interrupted before it completed."}
                          </div>
                        )}
                        {m.status === "completed" && m.content && (
                          <div className="message-content">{m.content}</div>
                        )}
                        {m.role === "brain" && m.status === "completed" && (
                          <ContextPanel kbContext={m.kb_context} limitations={m.kb_limitations} />
                        )}
                      </div>
                      {proposalByAnchor[m.id] && (
                        <ProposalPanel
                          proposal={proposalByAnchor[m.id]}
                          sending={sending}
                          projectId={activeId}
                          onProposalUpdated={handleProposalUpdated}
                          onCorrect={(text) => handleSend(text, { mode: "revise_proposal", proposalId: proposalByAnchor[m.id].id })}
                        />
                      )}
                    </div>
                  ))
                )}
              </div>

              <div className="composer">
                {sendError && <div className="inline-error">Send failed: {sendError}</div>}
                <textarea
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Talk to Braingate about this project… (Enter to send, Shift+Enter for a new line)"
                  rows={2}
                  disabled={sending}
                />
                <div className="composer-actions">
                  <button
                    className="send-btn"
                    onClick={() => handleSend(draft.trim(), { mode: "chat" })}
                    disabled={sending || !draft.trim()}
                  >
                    {sending ? "Sending…" : "Send"}
                  </button>
                  <button
                    className="propose-btn"
                    onClick={() => handleSend(draft.trim(), { mode: "draft_proposal" })}
                    disabled={sending || !draft.trim()}
                    title="Ask Braingate to propose a concrete next action from this"
                  >
                    Send &amp; propose action
                  </button>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
