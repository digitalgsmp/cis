import { useEffect, useState } from "react";
import { submitAsk, generateCard, listCards, dispatchRun } from "./api";
import { getRequestId, clearRequestId } from "./requestId";
import CardPanel from "./CardPanel";
import RunPanel from "./RunPanel";
import DispatchForm from "./DispatchForm";

const STATUS_LABEL = {
  pass: "PASS",
  fail: "FAILED",
  skip: "SKIPPED",
  error: "ERROR",
  pending: "Generating…",
};

function NewAskForm({ onCreated }) {
  const [project, setProject] = useState("");
  const [askText, setAskText] = useState("");
  const [doneWhen, setDoneWhen] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    if (!project.trim() || !askText.trim()) {
      setError("Project and your request are both required.");
      return;
    }
    setSubmitting(true);
    setError("");
    const result = await submitAsk(project.trim(), askText.trim(), doneWhen.trim());
    setSubmitting(false);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setAskText("");
    setDoneWhen("");
    onCreated(result.data.ask);
  }

  return (
    <form className="ask-form" onSubmit={submit}>
      <label className="dispatch-field">
        <span>Project</span>
        <input value={project} onChange={(e) => setProject(e.target.value)} />
      </label>
      <label className="dispatch-field">
        <span>What you want, in your own words</span>
        <textarea rows={3} value={askText} onChange={(e) => setAskText(e.target.value)} />
      </label>
      <label className="dispatch-field">
        <span>Done when… (optional, your own words)</span>
        <textarea rows={2} value={doneWhen} onChange={(e) => setDoneWhen(e.target.value)} />
      </label>
      {error && <div className="inline-error">{error}</div>}
      <button type="submit" disabled={submitting}>{submitting ? "Submitting…" : "Submit request"}</button>
    </form>
  );
}

function AskResult({ ask }) {
  const [card, setCard] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setGenerating(true);
    setError("");
    const requestId = getRequestId("generate", ask.id, { revision: ask.revision });
    const result = await generateCard(ask.id, requestId);
    setGenerating(false);
    if (!result.ok) {
      setError(result.error); // request_id kept — a retry reuses it, no duplicate generation
      return;
    }
    clearRequestId("generate", ask.id);
    setCard(result.data.card);
  }

  return (
    <div className="ask-result">
      <div className="muted">Request #{ask.id} · {ask.project} · revision {ask.revision}</div>
      {!card && (
        <button onClick={generate} disabled={generating}>{generating ? "Generating…" : "Generate card"}</button>
      )}
      {error && <div className="inline-error">{error}</div>}
      {card && <CardPanel card={card} allowEdit onChange={setCard} />}
    </div>
  );
}

function CardRow({ card, onChange }) {
  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState(card);
  const [runId, setRunId] = useState(null);
  const [showDispatch, setShowDispatch] = useState(false);
  const [showReview, setShowReview] = useState(false);

  function updateCard(c) {
    setCurrent(c);
    onChange?.(c);
  }

  async function submitDispatch(payload) {
    const result = await dispatchRun({ ...payload, card_factory_card_id: current.id });
    if (result.ok) {
      setRunId(result.data.run.id);
      setShowDispatch(false);
    }
    return result;
  }

  async function submitReview(payload) {
    const result = await dispatchRun({ ...payload, card_factory_card_id: current.id });
    if (result.ok) {
      setRunId(result.data.run.id);
      setShowReview(false);
    }
    return result;
  }

  return (
    <div className="card-row">
      <button className="card-row-summary" onClick={() => setOpen((o) => !o)}>
        <span>#{current.id}</span>
        <span>ask #{current.ask_id}</span>
        <span>{STATUS_LABEL[current.status] || current.status}</span>
        <span className="muted">{current.eligible_for_dispatch ? "eligible" : current.stale ? "stale" : "not eligible"}</span>
      </button>
      {open && (
        <div className="card-row-detail">
          <CardPanel card={current} allowEdit onChange={updateCard} />

          {current.eligible_for_dispatch && !runId && (
            showDispatch ? (
              <DispatchForm
                cardText={current.card_text}
                mode="implement"
                submitLabel="Dispatch"
                onSubmit={submitDispatch}
                onCancel={() => setShowDispatch(false)}
                dedupScope="dispatch"
                dedupId={current.id}
              />
            ) : (
              <button onClick={() => setShowDispatch(true)}>Dispatch…</button>
            )
          )}

          {runId && (
            <>
              <RunPanel runId={runId} />
              {showReview ? (
                <DispatchForm
                  cardText={current.card_text}
                  mode="review"
                  reviewOfRunId={runId}
                  submitLabel="Dispatch review"
                  onSubmit={submitReview}
                  onCancel={() => setShowReview(false)}
                  dedupScope="review"
                  dedupId={`${current.id}-${runId}`}
                />
              ) : (
                <button onClick={() => setShowReview(true)}>Request review of this run…</button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// The standalone view for a clear, direct request — bypasses the
// conversation entirely but writes to and reads from the exact same
// card_factory_asks/card_factory_cards/card_runner_runs records and the
// same CardPanel/RunPanel/DispatchForm controls the conversation view uses.
export default function CardFactory({ onBack }) {
  const [createdAsks, setCreatedAsks] = useState([]);
  const [cards, setCards] = useState(null);
  const [error, setError] = useState("");

  async function loadCards() {
    const result = await listCards();
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setError("");
    setCards(result.data.cards);
  }

  useEffect(() => {
    loadCards();
  }, []);

  return (
    <div className="workbench">
      <header className="stage-banner">
        <button className="link-btn" onClick={onBack}>← Back to conversation</button>
        <span className="stage-label">Card Factory</span>
        <span className="stage-detail">Direct requests, bypassing conversation. Same records, same gate.</span>
      </header>
      <div className="cardfactory-body">
        <section>
          <h2>New request</h2>
          <NewAskForm onCreated={(ask) => setCreatedAsks((prev) => [ask, ...prev])} />
          {createdAsks.map((a) => <AskResult key={a.id} ask={a} />)}
        </section>

        <section>
          <div className="cardfactory-cards-header">
            <h2>All cards</h2>
            <button onClick={loadCards}>Refresh</button>
          </div>
          {error && <div className="inline-error">{error}</div>}
          {cards === null ? (
            <div className="muted">Loading…</div>
          ) : cards.length === 0 ? (
            <div className="empty-state">No cards yet.</div>
          ) : (
            cards.map((c) => (
              <CardRow
                key={c.id}
                card={c}
                onChange={(updated) => setCards((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))}
              />
            ))
          )}
        </section>
      </div>
    </div>
  );
}
