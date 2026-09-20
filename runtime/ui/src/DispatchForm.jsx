import { useEffect, useState } from "react";
import { CAPABILITIES, RUN_TARGETS, DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS, enforcementLabel } from "./caps";
import { sha256Hex } from "./hash";
import { getRequestId, clearRequestId } from "./requestId";

// One shared "Approve and run" / "Dispatch" form, used both by a proposal's
// approve step and by the standalone Card Factory view — the same enforced
// limits, the same plain-language caps explanation, the same fingerprint
// binding, in one place rather than two workflows that could quietly drift.
// `mode='implement'` requires at least one permitted file (card_runner.py's
// own rule); `mode='review'` requires `reviewOfRunId`.
//
// `proposedFiles`/`proposedCommands`, when given (even as empty arrays),
// mean this submission is backing a reviewed proposal: the scope Braingate
// itself proposed is shown as a plain-language, read-only summary and sent
// as-is — Eric is never asked to type repository paths as the normal path.
// Omit both entirely for a scope-free technical dispatch (Card Factory's
// own direct/manual path), where the raw editable fields are the norm.
//
// `dedupScope`/`dedupId` (+ `dedupFingerprintExtra`) bind the request_id
// used for this submission to the exact project/revision/parameters —
// changing ANY of them (including the caller-supplied extra, e.g. a
// proposal's revision) mints a fresh id; resubmitting unchanged reuses the
// same one, so a retry after a lost response never risks a second spend or
// a second dispatch.
//
// `knownFingerprint`, when given, is used as-is instead of being computed
// client-side from `cardText` — a review MUST target the exact card
// snapshot the implementation run it reviews was itself dispatched
// against (card_runner.dispatch() enforces this: review_of_run_id must
// belong to the same card_factory_card_id), which may differ from
// whatever proposal/card is currently displayed elsewhere on the page
// after a later correction. The caller supplies that run's own recorded
// `card_fingerprint` (already computed once, server-side, at the original
// dispatch) rather than this form re-deriving a fingerprint from text that
// might belong to a different, newer card entirely.
export default function DispatchForm({
  cardText, mode, reviewOfRunId, onSubmit, submitLabel, onCancel,
  proposedFiles, proposedCommands, expectedProposalRevision,
  dedupScope, dedupId, dedupFingerprintExtra, knownFingerprint,
}) {
  const hasProposedScope = Array.isArray(proposedFiles);
  const [fingerprint, setFingerprint] = useState(knownFingerprint || "");
  const [target, setTarget] = useState("claude");
  const [model, setModel] = useState("");
  const [authorizedBy, setAuthorizedBy] = useState("");
  const [showTechnical, setShowTechnical] = useState(!hasProposedScope);
  const [permittedFiles, setPermittedFiles] = useState((proposedFiles || []).join("\n"));
  const [permittedCommands, setPermittedCommands] = useState((proposedCommands || []).join("\n"));
  const [timeoutSeconds, setTimeoutSeconds] = useState(DEFAULT_TIMEOUT_SECONDS);
  const [budgetUsd, setBudgetUsd] = useState("");
  const [acceptTimeOnly, setAcceptTimeOnly] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [maxTurns, setMaxTurns] = useState("");
  const [ackObservationOnly, setAckObservationOnly] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (knownFingerprint) {
      setFingerprint(knownFingerprint);
      return;
    }
    let cancelled = false;
    sha256Hex(cardText || "").then((h) => { if (!cancelled) setFingerprint(h); });
    return () => { cancelled = true; };
  }, [cardText, knownFingerprint]);

  const cap = CAPABILITIES[target];
  const budgetSupported = cap.budget_usd.enforcement === "native";
  const turnsUnavailable = cap.max_turns.enforcement === "unavailable";

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!authorizedBy.trim()) {
      setError("Say who is authorizing this run.");
      return;
    }
    // Review mode is enforced read-only by card_runner.py's own permission
    // plan regardless of permitted_files/permitted_commands (Edit/Write/
    // Bash are always disallowed) — no scope to collect or send.
    const files = mode === "review" ? [] : hasProposedScope && !showTechnical
      ? proposedFiles
      : permittedFiles.split("\n").map((s) => s.trim()).filter(Boolean);
    const commands = mode === "review" ? [] : hasProposedScope && !showTechnical
      ? (proposedCommands || [])
      : permittedCommands.split("\n").map((s) => s.trim()).filter(Boolean);
    if (mode === "implement" && files.length === 0) {
      setError(hasProposedScope
        ? "Braingate hasn't proposed any files for this yet — go back to the conversation and ask it what this needs to touch."
        : "List at least one file this run is permitted to change.");
      return;
    }
    if (!budgetSupported && !acceptTimeOnly) {
      setError(`${target} has no spend cap available — check "accept time-only control" to proceed with only the wall-clock timeout enforced.`);
      return;
    }
    const payload = {
      target,
      mode,
      model: model.trim() || null,
      authorized_by: authorizedBy.trim(),
      expected_card_fingerprint: fingerprint,
      wall_clock_timeout_seconds: Number(timeoutSeconds) || DEFAULT_TIMEOUT_SECONDS,
      permitted_files: files,
      permitted_commands: commands,
      accept_time_only_control: acceptTimeOnly,
    };
    if (budgetSupported && budgetUsd) payload.budget_usd = Number(budgetUsd);
    if (mode === "review") payload.review_of_run_id = reviewOfRunId;
    if (expectedProposalRevision != null) payload.expected_proposal_revision = expectedProposalRevision;
    if (maxTurns && !turnsUnavailable) {
      payload.max_turns = Number(maxTurns);
      payload.max_turns_ack_observation_only = ackObservationOnly;
    }

    const requestId = getRequestId(dedupScope, dedupId, {
      ...dedupFingerprintExtra, ...payload, request_id: undefined,
    });
    setSubmitting(true);
    const result = await onSubmit({ ...payload, request_id: requestId });
    setSubmitting(false);
    if (!result?.ok) {
      setError(result?.error || "Dispatch failed.");
      // Deliberately NOT cleared: a failed/lost submit keeps the same
      // request_id so retrying (even after a reload) is safe to replay.
      return;
    }
    clearRequestId(dedupScope, dedupId);
  }

  return (
    <form className="dispatch-form" onSubmit={handleSubmit}>
      {mode === "review" && (
        <div className="muted">
          A review run is read-only — it can read files but cannot edit, write or run commands,
          regardless of any scope. Nothing to choose here.
        </div>
      )}

      {mode !== "review" && hasProposedScope && (
        <div className="dispatch-proposed-scope">
          <div className="proposal-field-label">What this action would touch</div>
          {proposedFiles.length === 0 && (!proposedCommands || proposedCommands.length === 0) ? (
            <div className="banner-error">
              Braingate hasn't proposed any files or commands for this yet. Go back to the
              conversation and ask what this needs to touch before approving.
            </div>
          ) : (
            <>
              {proposedFiles.length > 0 && (
                <ul className="dispatch-scope-list">
                  {proposedFiles.map((f) => <li key={f}><code>{f}</code></li>)}
                </ul>
              )}
              {(!proposedCommands || proposedCommands.length === 0) ? (
                <div className="muted">No commands proposed — this run may only edit the files above.</div>
              ) : (
                <ul className="dispatch-scope-list">
                  {proposedCommands.map((c) => <li key={c}><code>{c}</code></li>)}
                </ul>
              )}
            </>
          )}
          <button type="button" className="link-btn" onClick={() => setShowTechnical((s) => !s)}>
            {showTechnical ? "Use the proposed scope above" : "Show technical details (override)"}
          </button>
        </div>
      )}

      {mode !== "review" && showTechnical && (
        <>
          <label className="dispatch-field">
            <span>Files this run may change (one per line)</span>
            <textarea rows={3} value={permittedFiles} onChange={(e) => setPermittedFiles(e.target.value)} />
          </label>
          <label className="dispatch-field">
            <span>Commands this run may execute (one per line, optional)</span>
            <textarea rows={2} value={permittedCommands} onChange={(e) => setPermittedCommands(e.target.value)} />
          </label>
        </>
      )}

      <label className="dispatch-field">
        <span>Model target</span>
        <select value={target} onChange={(e) => setTarget(e.target.value)}>
          {RUN_TARGETS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </label>
      <div className="dispatch-caps muted">
        Spend cap: {enforcementLabel(cap.budget_usd.enforcement)} — {cap.budget_usd.note}
        <br />
        Turn cap: {enforcementLabel(cap.max_turns.enforcement)} — {cap.max_turns.note}
      </div>
      <label className="dispatch-field">
        <span>Model (optional — default: {DEFAULT_MODEL[target] || "target's own configured default"})</span>
        <input value={model} onChange={(e) => setModel(e.target.value)} placeholder={DEFAULT_MODEL[target] || "target default"} />
      </label>
      <label className="dispatch-field">
        <span>Authorized by (your name)</span>
        <input value={authorizedBy} onChange={(e) => setAuthorizedBy(e.target.value)} />
      </label>
      <label className="dispatch-field">
        <span>Time limit (seconds)</span>
        <input type="number" min="1" value={timeoutSeconds} onChange={(e) => setTimeoutSeconds(e.target.value)} />
      </label>
      {budgetSupported && (
        <label className="dispatch-field">
          <span>Spend cap ($ — leave blank to accept time-only control instead)</span>
          <input type="number" min="0" step="0.01" value={budgetUsd} onChange={(e) => setBudgetUsd(e.target.value)} />
        </label>
      )}
      {(!budgetSupported || !budgetUsd) && (
        <label className="dispatch-checkbox">
          <input type="checkbox" checked={acceptTimeOnly} onChange={(e) => setAcceptTimeOnly(e.target.checked)} />
          Accept time-only control ({budgetSupported ? "no spend cap set" : `${target} has no spend cap`} — only the time limit above is enforced)
        </label>
      )}

      <button type="button" className="link-btn" onClick={() => setShowAdvanced((s) => !s)}>
        {showAdvanced ? "Hide" : "Show"} advanced limits
      </button>
      {showAdvanced && (
        <div className="dispatch-advanced">
          <label className="dispatch-field">
            <span>Max turns (optional)</span>
            <input type="number" min="1" value={maxTurns} disabled={turnsUnavailable} onChange={(e) => setMaxTurns(e.target.value)} />
          </label>
          {maxTurns && cap.max_turns.enforcement === "observation_only" && (
            <label className="dispatch-checkbox">
              <input type="checkbox" checked={ackObservationOnly} onChange={(e) => setAckObservationOnly(e.target.checked)} />
              I understand this target only reports turns after the run — it cannot stop the run at this count.
            </label>
          )}
          {turnsUnavailable && <div className="muted">Not available for {target}.</div>}
        </div>
      )}

      <div className="dispatch-fingerprint muted">Card fingerprint: {fingerprint || "computing…"}</div>
      {error && <div className="inline-error">{error}</div>}
      <div className="direction-note-actions">
        <button type="submit" disabled={submitting || !fingerprint}>
          {submitting ? "Dispatching…" : submitLabel}
        </button>
        {onCancel && <button type="button" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  );
}
