import { useEffect, useRef, useState } from "react";
import { getRunStatus, stopRun, getRunArtifact } from "./api";

const ACTIVE_STATUSES = new Set(["queued", "running", "stopping"]);
const TERMINAL_STATUSES = new Set(["completed", "failed", "timeout"]);
const POLL_MS = 4000;

const STATUS_LABEL = {
  queued: "Queued",
  running: "Running",
  stopping: "Stopping…",
  stopped: "Stopped",
  stop_failed: "STOP FAILED — process may still be running",
  completed: "Finished",
  failed: "Failed",
  timeout: "Timed out",
};

const STATUS_CLASS = {
  queued: "run-status-pending",
  running: "run-status-pending",
  stopping: "run-status-pending",
  stopped: "run-status-warn",
  stop_failed: "run-status-danger",
  completed: "run-status-ok",
  failed: "run-status-danger",
  timeout: "run-status-warn",
};

function money(n) {
  if (n === null || n === undefined) return "—";
  return `$${Number(n).toFixed(4)}`;
}

// Displays one card_runner_runs row: status, Stop, usage, and — once
// terminal — the SAVED artifact the dispatched work actually produced
// (evidence.md for an implement run, review.md for a review run), read
// through the run-id-scoped, fixed-name `getRunArtifact` route. This is
// deliberately distinct from `final_message` (the CLI's own last-turn
// text, which can be as generic as "Done.") — final_message is shown too,
// separately labeled, never presented as if it were the saved evidence.
// `card_completion_status` is the worker's own self-report; nothing here
// treats it as independent verification. Status polling (GET only) never
// triggers a model call or an execution.
export default function RunPanel({ runId, label, onUpdate }) {
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");
  const [stopping, setStopping] = useState(false);
  const [stopError, setStopError] = useState("");
  const [artifact, setArtifact] = useState(null); // {name, found, content, truncated, error} | null while loading
  const [artifactError, setArtifactError] = useState("");
  const pollRef = useRef(null);

  async function load() {
    const result = await getRunStatus(runId);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setError("");
    setRun(result.data.run);
    onUpdate?.(result.data.run);
  }

  useEffect(() => {
    setRun(null);
    setError("");
    setArtifact(null);
    setArtifactError("");
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  useEffect(() => {
    clearInterval(pollRef.current);
    if (run && ACTIVE_STATUSES.has(run.status)) {
      pollRef.current = setInterval(load, POLL_MS);
    }
    return () => clearInterval(pollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run?.status]);

  // Fetched once the run reaches a terminal state — never while still
  // running, since the file may not be fully written yet.
  useEffect(() => {
    if (!run || !TERMINAL_STATUSES.has(run.status)) return;
    const artifactName = run.mode === "review" ? "review.md" : "evidence.md";
    let cancelled = false;
    (async () => {
      const result = await getRunArtifact(runId, artifactName);
      if (cancelled) return;
      if (!result.ok) {
        setArtifactError(result.error);
        return;
      }
      setArtifactError("");
      setArtifact(result.data);
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, run?.status]);

  async function handleStop() {
    setStopping(true);
    setStopError("");
    const result = await stopRun(runId);
    setStopping(false);
    if (!result.ok) {
      setStopError(result.error);
      return;
    }
    setRun(result.data.run);
    onUpdate?.(result.data.run);
  }

  if (error) return <div className="inline-error">Could not load run status: {error}</div>;
  if (!run) return <div className="muted">Loading run status…</div>;

  const statusLabel = STATUS_LABEL[run.status] || run.status;
  const cls = STATUS_CLASS[run.status] || "";
  const active = ACTIVE_STATUSES.has(run.status);
  const terminal = TERMINAL_STATUSES.has(run.status);
  const artifactLabel = run.mode === "review" ? "Saved review (review.md)" : "Saved evidence (evidence.md)";

  return (
    <div className="run-panel">
      <div className="run-header">
        {label && <span className="proposal-subheading">{label}</span>}
        <span className={`run-status ${cls}`}>{statusLabel}</span>
        <span className="muted">
          {run.target} · {run.mode} · {run.model || "(default model)"}
        </span>
        {active && (
          <button className="stop-btn" onClick={handleStop} disabled={stopping || run.status === "stopping"}>
            {stopping ? "Stopping…" : "Stop"}
          </button>
        )}
      </div>
      {stopError && <div className="inline-error">Stop failed: {stopError}</div>}
      <div className="run-note muted">
        Browser closure does not stop execution — Stop must be pressed explicitly.
      </div>

      {run.card_completion_status && (
        <div className="run-completion">
          Worker's own claim: <strong>{run.card_completion_status}</strong>
          {" — "}not independent verification. Review is a separately authorized action.
        </div>
      )}

      {run.status === "stop_failed" && (
        <div className="banner-error">
          The stop signal could not be confirmed — the process may still be running outside this
          page's control. Check the host directly.
        </div>
      )}

      {terminal && (
        <div className="run-results">
          <div className="proposal-field-label">{artifactLabel}</div>
          {artifactError && (
            <div className="inline-error">Could not load {artifactLabel.toLowerCase()}: {artifactError}</div>
          )}
          {!artifactError && artifact === null && <div className="muted">Loading…</div>}
          {!artifactError && artifact && artifact.found && (
            <>
              <div className="run-content">{artifact.content}</div>
              {artifact.truncated && (
                <div className="muted">Truncated — the saved file is longer than shown here.</div>
              )}
            </>
          )}
          {!artifactError && artifact && !artifact.found && (
            <div className="muted">
              No {artifactLabel.toLowerCase()} was saved for this run{artifact.error ? ` (${artifact.error})` : ""}.
            </div>
          )}

          <div className="proposal-field-label">CLI's own final message</div>
          {run.final_message ? (
            <div className="run-content">{run.final_message}</div>
          ) : (
            <div className="muted">No final message was recorded for this run.</div>
          )}
          <div className="muted">
            This is the CLI's own last-turn text, not the saved {run.mode === "review" ? "review" : "evidence"} file above.
          </div>

          {run.out_of_scope && run.out_of_scope.length > 0 && (
            <div className="banner-error">
              Changes outside the permitted scope were detected: {run.out_of_scope.join(", ")}
            </div>
          )}
          <div className="run-usage muted">
            {run.usage_unknown
              ? "Usage for this run is unknown (not reported by this target)."
              : `${run.input_tokens ?? 0} in / ${run.output_tokens ?? 0} out tokens, ${money(run.cost_usd)} (API-dollar estimate, not subscription quota).`}
            {run.num_turns != null && ` ${run.num_turns} turns (as reported by the CLI).`}
          </div>
          <div className="run-evidence muted">Technical reference — run folder: {run.run_dir || "(not recorded)"}</div>
        </div>
      )}
    </div>
  );
}
