import { useEffect, useState } from "react";
import { getSystemContext, getRecoveryPacket } from "./api";

// Static mirror of tools/state/recovery_packet.py's ISSUE_AREAS keys, for
// the focused-packet picker only — there is no capabilities API route for
// this (same reasoning as caps.js). If recovery_packet.py's ISSUE_AREAS
// dict changes, this list must be updated to match.
const ISSUE_AREAS = [
  "workbench", "gateway", "braingate", "queue", "closeout",
  "card_factory", "container", "runtime", "database", "ui",
];

function fmtTime(iso) {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function downloadJson(filename, obj) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function copyJson(obj) {
  const text = JSON.stringify(obj, null, 2);
  await navigator.clipboard.writeText(text);
}

function Freshness({ state }) {
  const tables = state.source_table_freshness || {};
  const artifacts = state.generated_artifact_freshness || {};
  return (
    <section className="sc-section">
      <h3>Freshness</h3>
      <div className="sc-revision">
        State revision <code>{state.revision}</code>, computed {fmtTime(state.computed_at)}
      </div>
      <table className="sc-table">
        <thead>
          <tr><th>Source table</th><th>Rows</th><th>Last activity</th><th>Status</th></tr>
        </thead>
        <tbody>
          {Object.entries(tables).map(([table, info]) => (
            <tr key={table}>
              <td>{table}</td>
              <td>{info.row_count ?? "?"}</td>
              <td>{info.last_activity || "never"}</td>
              <td>
                {info.error ? <span className="sc-badge sc-badge-error">unreadable</span>
                  : info.dormant ? <span className="sc-badge sc-badge-warn">dormant ({info.days_since_activity}d)</span>
                  : <span className="sc-badge sc-badge-ok">active</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <h4>Generated artifacts</h4>
      <table className="sc-table">
        <thead><tr><th>Artifact</th><th>Fresh?</th><th>Detail</th></tr></thead>
        <tbody>
          {Object.entries(artifacts).map(([name, info]) => (
            <tr key={name}>
              <td>{name}</td>
              <td>
                {info.fresh === true ? <span className="sc-badge sc-badge-ok">fresh</span>
                  : info.fresh === false ? <span className="sc-badge sc-badge-error">stale</span>
                  : <span className="sc-badge sc-badge-warn">unknown</span>}
              </td>
              <td className="muted">{info.detail || (info.declared_revision ? `declared ${info.declared_revision}` : "")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function CurrentFocus({ state }) {
  // Card 04 R1 correction: current_queue_item and recent task activity
  // (e.g. an in-progress recovery/correction task) previously had no
  // dedicated surface here and could be lost among truncated queue lists.
  // Renders straight from canonical_state's current_focus section --
  // no inference performed here either.
  const cf = state.current_focus;
  if (!cf) return null;
  const pointer = cf.current_queue_item_pointer;
  const detail = cf.current_queue_item_detail;
  const recentItems = cf.recent_task_queue_items || {};
  return (
    <section className="sc-section">
      <h3>Current focus</h3>
      {!pointer ? (
        <div className="muted">No current_queue_item pointer recorded in project_state.</div>
      ) : (
        <div>
          <strong>{pointer.value}</strong>
          {detail && <> — {detail.title} <span className="sc-badge sc-badge-warn">{detail.need_status}</span></>}
          <div className="muted">source: {pointer.source}, set {pointer.created_at}</div>
        </div>
      )}
      <h4>Recent task activity</h4>
      {(cf.recent_task_activity || []).length === 0 ? (
        <div className="muted">No dev_continuity_events recorded.</div>
      ) : (
        <ul className="sc-list">
          {cf.recent_task_activity.slice(0, 10).map((e) => {
            const item = recentItems[e.task];
            return (
              <li key={e.id}>
                <strong>{e.task}</strong>
                {item && <> <span className="sc-badge sc-badge-warn">{item.need_status}</span></>}
                {" "}— {e.summary} ({e.kind}, rev {e.revision}, {e.created_at})
              </li>
            );
          })}
        </ul>
      )}
      {cf.recent_task_activity_fetch_handle && (
        <div className="muted">{cf.recent_task_activity_fetch_handle}</div>
      )}
    </section>
  );
}

function QueueFocus({ state }) {
  const qf = state.queue_focus || {};
  const counts = qf.counts_by_status || {};
  return (
    <section className="sc-section">
      <h3>Current queue focus</h3>
      <div className="sc-counts">
        {Object.entries(counts).map(([status, n]) => (
          <span key={status} className="sc-count-pill">{status}: {n}</span>
        ))}
      </div>
      {(qf.open_items || []).length === 0 ? (
        <div className="muted">No open queue items.</div>
      ) : (
        <ul className="sc-list">
          {qf.open_items.map((item) => (
            <li key={`${item.item_num}`}>
              <strong>{item.item_num}</strong> (tier {item.tier}) — {item.title}
              {" "}<span className="sc-badge sc-badge-warn">{item.need_status}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function OpenBlocked({ state }) {
  const ob = state.open_blocked_deferred || {};
  const discoveries = state.discoveries_requiring_attention || [];
  const blockers = state.active_blockers || [];
  return (
    <section className="sc-section">
      <h3>Open / blocked / discoveries</h3>
      <h4>Active blockers</h4>
      {blockers.length === 0 ? (
        <div className="muted">No ACTIVE blockers recorded.</div>
      ) : (
        <ul className="sc-list">
          {blockers.map((b) => (
            <li key={b.id}>
              <strong>{b.id}</strong>: {b.description}
              {b.source_dormant && <span className="sc-badge sc-badge-warn"> dormant source</span>}
            </li>
          ))}
        </ul>
      )}
      {discoveries.length === 0 ? (
        <div className="muted">No unresolved discoveries.</div>
      ) : (
        <ul className="sc-list">
          {discoveries.map((d, i) => (
            <li key={i}>
              {d.error ? <span className="sc-badge sc-badge-error">error</span> : null}
              {d.task ? <strong>{d.task}: </strong> : null}
              {d.title || d.summary || d.error || JSON.stringify(d)}
            </li>
          ))}
        </ul>
      )}
      <h4>Closeout status by task</h4>
      {Object.keys(ob.closeout_status_by_task || {}).length === 0 ? (
        <div className="muted">No tasks with continuity events.</div>
      ) : (
        <ul className="sc-list">
          {Object.entries(ob.closeout_status_by_task).map(([task, status]) => (
            <li key={task}><strong>{task}</strong>: {status.error ? `error — ${status.error}` : JSON.stringify(status)}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function RecentAndDecisions({ state }) {
  const recent = state.recent_verified_closed || {};
  const decisions = state.active_decisions || [];
  const questions = state.open_questions || [];
  return (
    <section className="sc-section">
      <h3>Recently verified / closed</h3>
      {(recent.queue_items_done || []).length === 0 ? (
        <div className="muted">No queue items marked DONE yet.</div>
      ) : (
        <ul className="sc-list">
          {recent.queue_items_done.slice(0, 10).map((it) => (
            <li key={it.item_num}>{it.item_num} — {it.title} ({it.status_changed_at})</li>
          ))}
        </ul>
      )}

      <h4>Active decisions</h4>
      {decisions.length === 0 ? <div className="muted">No active decisions recorded.</div> : (
        <ul className="sc-list">
          {decisions.map((d) => (
            <li key={d.id}><strong>{d.label}</strong>: {d.decision}</li>
          ))}
        </ul>
      )}

      <h4>Open questions</h4>
      {questions.length === 0 ? <div className="muted">No open questions recorded.</div> : (
        <ul className="sc-list">
          {questions.map((q) => (
            <li key={q.id}>
              {q.question}
              {q.source_dormant && <span className="sc-badge sc-badge-warn"> dormant source</span>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function RuntimeHealth({ health }) {
  if (!health) return null;
  const gateways = health.gateways || {};
  return (
    <section className="sc-section sc-observed">
      <h3>Observed runtime health <span className="sc-observed-tag">LIVE OBSERVATION — not authoritative, never written back</span></h3>
      <div className="sc-counts">
        <span className={`sc-count-pill ${health.repo_dirty ? "sc-pill-warn" : "sc-pill-ok"}`}>
          repo: {health.repo_dirty === null ? "unknown" : health.repo_dirty ? `dirty (${health.dirty_file_count} files)` : "clean"}
        </span>
        <span className={`sc-count-pill ${health.spine_db_reachable ? "sc-pill-ok" : "sc-pill-warn"}`}>
          spine db: {health.spine_db_reachable ? "reachable" : "unreachable"}
        </span>
      </div>
      <table className="sc-table">
        <thead><tr><th>Gateway</th><th>Port</th><th>Status</th></tr></thead>
        <tbody>
          {Object.entries(gateways).map(([role, info]) => (
            <tr key={role}>
              <td>{role}</td>
              <td>{info.port}</td>
              <td>{info.listening
                ? <span className="sc-badge sc-badge-ok">up</span>
                : <span className="sc-badge sc-badge-error">down</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function RecoveryPacketControls() {
  const [issue, setIssue] = useState("");
  const [busyFull, setBusyFull] = useState(false);
  const [busyFocused, setBusyFocused] = useState(false);
  const [error, setError] = useState("");
  const [lastAction, setLastAction] = useState(""); // e.g. "Copied full packet (rev abc123) at 3:04 PM"

  async function withPacket(issueArg, { copy, download, label }) {
    const result = await getRecoveryPacket(issueArg || undefined);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setError("");
    const packet = result.data;
    if (copy) {
      try {
        await copyJson(packet);
      } catch (e) {
        setError(`Clipboard write failed: ${e.message}`);
        return;
      }
    }
    if (download) {
      const suffix = issueArg ? `-${issueArg}` : "-full";
      downloadJson(`cis-recovery-packet${suffix}.json`, packet);
    }
    setLastAction(`${label} (revision ${packet.state_revision}) at ${fmtTime(packet.generated_at)}`);
  }

  async function copyFull() {
    setBusyFull(true);
    await withPacket(null, { copy: true, label: "Copied full recovery packet" });
    setBusyFull(false);
  }

  async function downloadFull() {
    setBusyFull(true);
    await withPacket(null, { download: true, label: "Downloaded full recovery packet" });
    setBusyFull(false);
  }

  async function copyFocused() {
    if (!issue) {
      setError("Pick a focus area first.");
      return;
    }
    setBusyFocused(true);
    await withPacket(issue, { copy: true, label: `Copied focused recovery packet (${issue})` });
    setBusyFocused(false);
  }

  async function downloadFocused() {
    if (!issue) {
      setError("Pick a focus area first.");
      return;
    }
    setBusyFocused(true);
    await withPacket(issue, { download: true, label: `Downloaded focused recovery packet (${issue})` });
    setBusyFocused(false);
  }

  return (
    <section className="sc-section">
      <h3>External recovery packet</h3>
      <p className="muted">
        Generated fresh from the same canonical CIS state shown above (tools/state/canonical_state.py
        → tools/state/recovery_packet.py). Suitable to paste directly into a ChatGPT or Claude
        subscription session after /clear, or in a fresh session, to diagnose or repair this system.
        Copy/download actions are read-only — nothing here can be written back as fact.
      </p>
      <div className="sc-packet-actions">
        <button onClick={copyFull} disabled={busyFull}>
          {busyFull ? "Working…" : "Copy full recovery context"}
        </button>
        <button onClick={downloadFull} disabled={busyFull} className="link-btn">
          Download full packet (.json)
        </button>
      </div>
      <div className="sc-packet-actions">
        <select value={issue} onChange={(e) => setIssue(e.target.value)} disabled={busyFocused}>
          <option value="">Choose a focus area…</option>
          {ISSUE_AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <button onClick={copyFocused} disabled={busyFocused || !issue}>
          {busyFocused ? "Working…" : "Copy focused recovery context"}
        </button>
        <button onClick={downloadFocused} disabled={busyFocused || !issue} className="link-btn">
          Download focused packet (.json)
        </button>
      </div>
      {error && <div className="inline-error">{error}</div>}
      {lastAction && <div className="sc-last-action">{lastAction}</div>}
    </section>
  );
}

export default function SystemContext({ onBack }) {
  const [state, setState] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lastLoadedAt, setLastLoadedAt] = useState(null);

  async function load() {
    setLoading(true);
    const result = await getSystemContext();
    setLoading(false);
    if (!result.ok) {
      setError(result.error);
      // Deliberately does NOT clear `state` — a prior successful load
      // stays visible, marked stale, rather than being replaced by
      // nothing (Card 03 failure-behavior requirement).
      return;
    }
    setError("");
    setState(result.data);
    setLastLoadedAt(new Date().toISOString());
  }

  useEffect(() => {
    load();
  }, []);

  const stale = Boolean(error && state);

  return (
    <div className="workbench">
      <header className="stage-banner">
        <button className="link-btn" onClick={onBack}>← Back to conversation</button>
        <span className="stage-label">System Context / Recovery</span>
        <span className="stage-detail">
          Read-only view of CIS's authoritative state, from the same canonical read model the
          pipeline itself uses. Nothing on this screen can change project state.
        </span>
        <button className="link-btn" onClick={load} disabled={loading} style={{ marginLeft: "auto" }}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      <div className="sc-body">
        {error && (
          <div className="banner-error">
            Could not load authoritative state: {error}
            {stale && " — showing the last successfully loaded state below."}
          </div>
        )}
        {stale && (
          <div className="sc-stale-notice">
            STALE — last successfully loaded {fmtTime(lastLoadedAt)}. This may no longer reflect
            current CIS state.
          </div>
        )}

        {!state && !error && loading && <div className="muted">Loading authoritative state…</div>}
        {!state && error && (
          <div className="muted">No authoritative state has loaded yet in this session.</div>
        )}

        {state && (
          <>
            <div className="sc-section-group">
              <h2>A. Authoritative project state</h2>
              <CurrentFocus state={state} />
              <Freshness state={state} />
              <QueueFocus state={state} />
              <OpenBlocked state={state} />
              <RecentAndDecisions state={state} />
            </div>

            <div className="sc-section-group">
              <h2>B. Observed runtime health</h2>
              <RuntimeHealth health={state.observed_runtime_health} />
            </div>

            <div className="sc-section-group">
              <h2>C. External recovery packet</h2>
              <RecoveryPacketControls />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
