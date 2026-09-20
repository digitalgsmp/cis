import { useEffect, useState } from "react";
import { getProposal, confirmDirection, approveProposal, dispatchRun, getCard } from "./api";
import { getRequestId, clearRequestId } from "./requestId";
import CardPanel from "./CardPanel";
import RunPanel from "./RunPanel";
import DispatchForm from "./DispatchForm";

const KIND_LABEL = {
  mockup: "Mock-up",
  experiment: "Experiment",
  implementation: "Implementation",
};
const ACTIVE_RUN_STATUSES = new Set(["queued", "running", "stopping"]);
const correctionDraftKey = (proposalId) => `cis-workbench-correction-draft-${proposalId}`;
const reviewRunKey = (runId) => `cis-workbench-review-run-${runId}`;

function Field({ label, value }) {
  if (!value) return null;
  return (
    <div className="proposal-field">
      <div className="proposal-field-label">{label}</div>
      <div className="proposal-field-value">{value}</div>
    </div>
  );
}

// Shows one proposed action (backend `workbench_action_proposals` row)
// inline in the conversation: what would happen, in plain language, plus
// whatever card/run it has produced so far. Correcting it is a plain text
// box that sends a normal conversational message (mode='revise_proposal')
// — never a technical field-by-field form. Confirming direction and
// approving execution stay two separate, explicit buttons.
//
// `onProposalUpdated` MUST be called with the server's own fresh proposal
// object after every confirm/approve so the parent's list (and thus the
// `proposal` prop this component receives) never lags behind what was
// actually written — the source of a prior bug where a second confirm or
// approve was evaluated against stale revision/confirmed_revision.
export default function ProposalPanel({ proposal, onCorrect, sending, onProposalUpdated, projectId }) {
  const [card, setCard] = useState(null);
  const [run, setRun] = useState(null);
  const [detailError, setDetailError] = useState("");
  const [correction, setCorrection] = useState(() => localStorage.getItem(correctionDraftKey(proposal.id)) || "");
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState("");
  const [showApprove, setShowApprove] = useState(false);
  const [approveError, setApproveError] = useState("");
  const [checkingFresh, setCheckingFresh] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRunId, setReviewRunId] = useState(null);
  const [reviewedCard, setReviewedCard] = useState(null);
  const [reviewedCardError, setReviewedCardError] = useState("");

  // Initial/refresh load: covers a page reload of an already-confirmed
  // proposal (list responses never carry card/run) and re-fetches fresh
  // stale/eligible flags after a correction bumps `revision`. Confirm/
  // approve responses update `card`/`run` directly themselves (below) —
  // this effect does NOT re-run right after those (revision is unchanged
  // by either), so it never duplicates that work.
  useEffect(() => {
    let cancelled = false;
    async function loadDetail() {
      if (!proposal.card_factory_card_id && !proposal.card_runner_run_id) return;
      const result = await getProposal(proposal.id);
      if (cancelled) return;
      if (!result.ok) {
        setDetailError(result.error);
        return;
      }
      setDetailError("");
      if (result.data.card) setCard(result.data.card);
      if (result.data.run) setRun(result.data.run);
    }
    loadDetail();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proposal.id, proposal.revision]);

  // Restores a previously-dispatched review's run id across reload —
  // keyed on the IMPLEMENT run's id (not the proposal's), since a review
  // run has no column of its own on workbench_action_proposals.
  useEffect(() => {
    if (!proposal.card_runner_run_id) {
      setReviewRunId(null);
      return;
    }
    const saved = localStorage.getItem(reviewRunKey(proposal.card_runner_run_id));
    setReviewRunId(saved ? Number(saved) : null);
  }, [proposal.card_runner_run_id]);

  // The card an implement run was ACTUALLY dispatched against — read
  // independently of whatever `card` is currently linked/displayed above,
  // since a later correction can leave those pointing at two different
  // card_factory_cards rows. A review must target this one, never the
  // current one (the exact F5b gap this fixes).
  useEffect(() => {
    let cancelled = false;
    if (!run?.card_factory_card_id) {
      setReviewedCard(null);
      return;
    }
    getCard(run.card_factory_card_id).then((result) => {
      if (cancelled) return;
      if (!result.ok) {
        setReviewedCardError(result.error);
        return;
      }
      setReviewedCardError("");
      setReviewedCard(result.data.card);
    });
    return () => { cancelled = true; };
  }, [run?.card_factory_card_id]);

  useEffect(() => {
    if (correction) localStorage.setItem(correctionDraftKey(proposal.id), correction);
    else localStorage.removeItem(correctionDraftKey(proposal.id));
  }, [correction, proposal.id]);

  async function submitCorrection(e) {
    e.preventDefault();
    const text = correction.trim();
    if (!text) return;
    const result = await onCorrect(text);
    if (result?.ok !== false) setCorrection("");
  }

  async function handleConfirm() {
    setConfirming(true);
    setConfirmError("");
    const requestId = getRequestId("confirm", proposal.id, { revision: proposal.revision });
    const result = await confirmDirection(proposal.id, requestId);
    setConfirming(false);
    if (!result.ok) {
      setConfirmError(result.error);
      return; // request_id kept — a retry reuses it, no duplicate generation
    }
    clearRequestId("confirm", proposal.id);
    if (result.data.card) setCard(result.data.card);
    onProposalUpdated(result.data.proposal);
  }

  // Never approve a view Eric has not actually seen the current revision
  // of: re-checks the server immediately before opening the form, and
  // refuses to open it (refreshing the displayed proposal instead) if the
  // server's revision has moved on since the last render.
  async function handleOpenApprove() {
    setApproveError("");
    setCheckingFresh(true);
    const result = await getProposal(proposal.id);
    setCheckingFresh(false);
    if (!result.ok) {
      setApproveError(result.error);
      return;
    }
    const fresh = result.data.proposal;
    onProposalUpdated(fresh);
    if (result.data.card) setCard(result.data.card);
    if (fresh.revision !== proposal.revision) {
      setApproveError(
        "This proposal changed since it was last shown here — refreshed to the current version. " +
        "Review it again before approving."
      );
      return;
    }
    setShowApprove(true);
  }

  async function handleApprove(payload) {
    const result = await approveProposal(proposal.id, payload.request_id, payload);
    if (result.ok) {
      setShowApprove(false);
      setRun(result.data.run);
      onProposalUpdated(result.data.proposal);
    }
    return result;
  }

  async function handleRequestReview(payload) {
    // MUST match the implementation run's own card_factory_card_id — never
    // whatever card is currently displayed elsewhere, which may already be
    // a newer revision from a later correction. card_runner.dispatch()
    // itself enforces this (review_of_run_id must belong to the same
    // card_factory_card_id) and would reject a mismatch; this keeps the
    // request correct instead of relying on that rejection.
    const result = await dispatchRun({ ...payload, card_factory_card_id: run.card_factory_card_id });
    if (result.ok) {
      setShowReviewForm(false);
      setReviewRunId(result.data.run.id);
      localStorage.setItem(reviewRunKey(run.id), String(result.data.run.id));
    }
    return result;
  }

  const staleApproval = proposal.confirmed_revision != null && proposal.confirmed_revision !== proposal.revision;
  const canApprove = card && card.status === "pass" && card.is_current && !card.stale
    && !staleApproval && !proposal.unresolved_decisions;
  const runIsCurrent = run && card && run.card_factory_card_id === card.id;
  const runActive = run && ACTIVE_RUN_STATUSES.has(run.status);
  const canRequestReview = run && run.mode === "implement" && run.status === "completed" && !reviewRunId;

  return (
    <div className="proposal-panel">
      <div className="proposal-header">
        <span className="proposal-kind">{KIND_LABEL[proposal.kind] || proposal.kind}</span>
        <span className="muted">proposal revision {proposal.revision}</span>
        {proposal.status === "approved" && <span className="run-status run-status-ok">Approved</span>}
      </div>

      <Field label="Outcome" value={proposal.outcome} />
      <Field label="Action" value={proposal.action} />
      <Field label="Boundaries" value={proposal.boundaries} />
      <Field label="Success criteria" value={proposal.success_criteria} />

      {proposal.unresolved_decisions && (
        <div className="banner-error">
          Unresolved before this can be approved: {proposal.unresolved_decisions}
        </div>
      )}

      {staleApproval && (
        <div className="banner-error">
          This proposal was corrected after direction was last confirmed (confirmed at revision{" "}
          {proposal.confirmed_revision}, now at revision {proposal.revision}). Confirm direction
          again before approving.
        </div>
      )}

      <form className="proposal-correction" onSubmit={submitCorrection}>
        <textarea
          rows={2}
          placeholder="Correct this — tell Braingate what should change…"
          value={correction}
          onChange={(e) => setCorrection(e.target.value)}
          disabled={sending}
        />
        <button type="submit" disabled={sending || !correction.trim()}>
          {sending ? "Sending…" : "Send correction"}
        </button>
      </form>

      <div className="proposal-actions">
        <button onClick={handleConfirm} disabled={confirming}>
          {confirming ? "Confirming…" : proposal.card_factory_card_id ? "Confirm direction again" : "Confirm direction"}
        </button>
      </div>
      {confirmError && <div className="inline-error">{confirmError}</div>}

      {detailError && <div className="inline-error">Could not load linked records: {detailError}</div>}

      {card && (
        <div className="proposal-linked-card">
          <div className="proposal-subheading">Generated card</div>
          <CardPanel card={card} allowEdit={false} />
        </div>
      )}

      {run && (
        <div className="proposal-linked-run">
          <RunPanel
            runId={run.id}
            label={runIsCurrent ? "Run" : "Previous run (on an earlier version of this card)"}
            onUpdate={setRun}
          />
          {canRequestReview && (
            showReviewForm ? (
              <>
                {reviewedCardError && (
                  <div className="inline-error">Could not load the exact reviewed card: {reviewedCardError}</div>
                )}
                {reviewedCard && (
                  <div className="proposal-linked-card">
                    <div className="proposal-subheading">Card this run was actually dispatched against</div>
                    <CardPanel card={reviewedCard} allowEdit={false} />
                  </div>
                )}
                <DispatchForm
                  cardText={reviewedCard?.card_text}
                  knownFingerprint={run.card_fingerprint}
                  mode="review"
                  reviewOfRunId={run.id}
                  submitLabel="Dispatch review"
                  onSubmit={handleRequestReview}
                  onCancel={() => setShowReviewForm(false)}
                  dedupScope="review"
                  dedupId={`${proposal.id}-${run.id}`}
                  dedupFingerprintExtra={{ projectId }}
                />
              </>
            ) : (
              <button onClick={() => setShowReviewForm(true)}>Request review of this run…</button>
            )
          )}
          {reviewRunId && <RunPanel runId={reviewRunId} label="Review" />}
        </div>
      )}

      {card && (
        canApprove ? (
          showApprove ? (
            <DispatchForm
              cardText={card.card_text}
              mode="implement"
              submitLabel="Approve and run"
              onSubmit={handleApprove}
              onCancel={() => setShowApprove(false)}
              proposedFiles={proposal.permitted_files}
              proposedCommands={proposal.permitted_commands}
              expectedProposalRevision={proposal.revision}
              dedupScope="approve"
              dedupId={proposal.id}
              dedupFingerprintExtra={{ projectId, revision: proposal.revision }}
            />
          ) : (
            <>
              {runActive && (
                <div className="muted">
                  A run is already active for this card — approving now will be refused until it
                  finishes or is stopped.
                </div>
              )}
              <button className="approve-btn" onClick={handleOpenApprove} disabled={checkingFresh}>
                {checkingFresh ? "Checking latest version…" : "Approve and run…"}
              </button>
            </>
          )
        ) : (
          <div className="muted">
            Not eligible to run yet — {staleApproval
              ? "confirm direction again after the last correction."
              : proposal.unresolved_decisions
                ? "unresolved decisions remain."
                : `gate status is "${card.status}".`}
          </div>
        )
      )}
      {approveError && <div className="inline-error">{approveError}</div>}
    </div>
  );
}
