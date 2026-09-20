import { useState } from "react";
import { editCard, regateCard } from "./api";

const GATE_LABEL = {
  pass: "PASS — gate checked, not independently verified",
  fail: "FAILED gate",
  skip: "SKIPPED (no card text to check, or gate could not judge it)",
  error: "Gate could not run",
  pending: "Generating…",
};

const GATE_CLASS = {
  pass: "run-status-ok",
  fail: "run-status-danger",
  skip: "run-status-warn",
  error: "run-status-danger",
  pending: "run-status-pending",
};

// Renders one card_factory_cards row. `allowEdit` exposes the technical
// edit/re-gate controls — used by the standalone Card Factory view; the
// conversation view passes allowEdit={false} so a correction there always
// goes back through the conversational proposal flow, never a raw text box.
export default function CardPanel({ card, allowEdit = false, onChange }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(card.card_text || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [regating, setRegating] = useState(false);

  if (!card) return null;
  const label = GATE_LABEL[card.status] || card.status;
  const cls = GATE_CLASS[card.status] || "";

  async function save() {
    setSaving(true);
    setError("");
    const result = await editCard(card.id, text);
    setSaving(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setEditing(false);
    onChange?.(result.data.card);
  }

  async function regate() {
    setRegating(true);
    setError("");
    const result = await regateCard(card.id);
    setRegating(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    onChange?.(result.data.card);
  }

  return (
    <div className="card-panel">
      <div className="card-header">
        <span className={`run-status ${cls}`}>{label}</span>
        <span className="muted">card revision {card.card_revision}{card.is_current ? "" : " (superseded)"}</span>
      </div>
      {card.stale && (
        <div className="banner-error">
          This card was generated against an earlier version of the request — it no longer
          matches the current wording and is not eligible to run.
        </div>
      )}
      {!card.is_current && (
        <div className="banner-error">This card revision has been superseded by a newer edit.</div>
      )}

      {editing ? (
        <div className="card-edit">
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={12} />
          <div className="direction-note-actions">
            <button onClick={save} disabled={saving}>{saving ? "Saving…" : "Save & re-gate"}</button>
            <button onClick={() => { setEditing(false); setText(card.card_text || ""); }}>Cancel</button>
          </div>
        </div>
      ) : (
        <pre className="card-text">{card.card_text}</pre>
      )}
      {error && <div className="inline-error">{error}</div>}

      {allowEdit && !editing && (
        <div className="card-actions">
          <button onClick={() => setEditing(true)}>Edit card text</button>
          <button onClick={regate} disabled={regating}>{regating ? "Re-checking…" : "Re-check gate"}</button>
        </div>
      )}

      {card.gate_output && (
        <details className="run-final-message">
          <summary>Gate output</summary>
          <div className="context-excerpt">{card.gate_output}</div>
        </details>
      )}

      <div className="run-usage muted">
        {card.usage_input_tokens == null && card.usage_output_tokens == null
          ? "Generation usage unknown."
          : `Generation used ${card.usage_input_tokens ?? 0} in / ${card.usage_output_tokens ?? 0} out tokens` +
            (card.usage_cost_usd != null ? `, $${Number(card.usage_cost_usd).toFixed(4)} (API-dollar estimate).` : ".")}
      </div>

      {card.dispatch_status && (
        <div className="muted">Last dispatch: {card.dispatch_status} (run {card.dispatch_run_id}, target {card.dispatch_target})</div>
      )}
    </div>
  );
}
