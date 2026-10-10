import { useEffect, useState } from "react";
import { getBuildPath } from "./api";
import MermaidDiagram from "./MermaidDiagram";
import DestinationArchitecture from "./DestinationArchitecture";
import { atLeast, FULL_DISCLOSURE } from "./presentationMode";

// Read-only screen over GET /api/workbench/build-path (runtime/api/build_path.py
// -> tools/state/build_path.py). Every value shown here is rendered straight
// from that response. Nothing on this screen derives a status of its own, and
// nothing on it can write: there is no mutation call in this file, and the one
// api.js function it imports is a parameterless GET.
//
// The diagram is NOT drawn here either — the server sends Mermaid source
// generated from the same `phases` array the cards below render, so the picture
// and the panel cannot disagree. MermaidDiagram only asks Mermaid to lay it out.
//
// TWO TABS, TWO DIFFERENT QUESTIONS, ONE SCREEN:
//
//   Current Build            "what are we building now?"
//                            the P0–P6 chronological sequence, from
//                            project_state.pipeline_roadmap + ADR-PIPE-001
//   Destination Architecture "what is CIS ultimately being built to support?"
//                            the WIASW architecture, from the ADR-WIASW-*
//                            decisions (DestinationArchitecture.jsx)
//
// They are deliberately NOT merged. The current-build graph and the destination
// graph have different authorities, different node kinds and different edge
// semantics, and only one of them has build progress. Switching tabs switches
// read models; neither tab's data is fetched while the other is shown.

const STATUS_BADGE = {
  complete: "sc-badge-ok",
  active: "sc-badge-ok",
  resolved: "sc-badge-ok",
  blocked: "sc-badge-error",
  blocking: "sc-badge-error",
  next: "sc-badge-warn",
  deferred: "sc-badge-warn",
  open: "sc-badge-warn",
  pending: "",
};

function fmtTime(iso) {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function StatusBadge({ status, label }) {
  if (!status) return null;
  return (
    <span className={`sc-badge ${STATUS_BADGE[status] ?? ""}`}>{label || status}</span>
  );
}

/** The migration number is the identifier; the rule is the meaning. More
 *  Detail says a database update gates this phase and whether it has happened;
 *  Technical names which migration and how its state was detected. */
function MigrationLine({ migration, mode }) {
  const applied = migration.applied;
  const [label, cls] =
    applied === true ? ["applied", "sc-badge-ok"]
      : applied === false ? ["not applied", "sc-badge-warn"]
        : applied === "partial" ? ["partially applied", "sc-badge-error"]
          : ["applied state unknown", "sc-badge-warn"];
  return (
    <li>
      {atLeast(mode, "technical")
        ? <strong>migration {migration.migration}</strong>
        : <strong>a database update</strong>}{" "}
      — {migration.rule}{" "}
      <span className={`sc-badge ${cls}`}>{label}</span>
      {atLeast(mode, "technical") && migration.detected_by && (
        <div className="muted bp-fineprint">{migration.detected_by}</div>
      )}
    </li>
  );
}

function QueueHookLine({ hook, mode }) {
  const technical = atLeast(mode, "technical");
  if (!hook.found) {
    return (
      <li>
        {technical
          ? <strong>queue {hook.item_num}</strong>
          : <strong>a work item the roadmap names here</strong>}{" "}
        <span className="sc-badge sc-badge-error">not in queue_items</span>
        {hook.note && <div className="muted bp-fineprint">{hook.note}</div>}
      </li>
    );
  }
  return (
    <li>
      {technical && <><strong>queue {hook.item_num}</strong> — </>}
      {hook.title}{" "}
      <span className="sc-badge sc-badge-warn">{hook.need_status || "unclassified"}</span>
    </li>
  );
}

/** What was found, then how it is dispositioned, then which record it is.
 *  Simple keeps the sentence and the status; the record id and revision are
 *  the identifiers, so they wait for Technical. */
function DiscoveryLine({ record, mode }) {
  return (
    <li>
      {atLeast(mode, "technical") && (
        <><strong>{record.id || `revision ${record.revision}`}</strong>{" "}</>
      )}
      <StatusBadge status={record.status} />{" "}
      {atLeast(mode, "detail") && (
        <span className="muted">
          {/* A discovery record carries a disposition; a stage-closeout
              blocker from the closeout gate carries a blocker type instead
              (an unresolved plain unfinished_work event has no disposition
              at all). Whichever this record has is shown — never an empty
              parenthesis. */}
          ({record.disposition || record.type}
          {atLeast(mode, "technical") && <>, rev {record.revision}</>})
        </span>
      )}
      <div className="bp-discovery-summary">{record.summary}</div>
    </li>
  );
}

function PhaseCard({ phase, mode }) {
  const cls = phase.blocked ? "blocked" : phase.status;
  return (
    <section className={`sc-section bp-phase bp-phase-${cls}`}>
      <h3>
        {phase.label} <StatusBadge status={phase.status} label={phase.status_label} />
        {phase.is_current && <span className="bp-here">you are here</span>}
      </h3>
      <div className="bp-phase-desc">{phase.description}</div>

      {/* Simple answers "where are we, is it blocked, what is next, what is
          the roadmap" and stops there. Everything below is the mechanics of
          WHY a phase is gated, which is what More Detail is for. */}
      {atLeast(mode, "detail") && phase.migrations?.length > 0 && (
        <>
          <h4>Migration unlock points</h4>
          <ul className="sc-list">
            {phase.migrations.map((m) => (
              <MigrationLine key={m.migration} migration={m} mode={mode} />
            ))}
          </ul>
        </>
      )}

      {atLeast(mode, "detail") && phase.queue_hooks?.length > 0 && (
        <>
          <h4>Queue hooks (work-item authority)</h4>
          <ul className="sc-list">
            {phase.queue_hooks.map((h) => (
              <QueueHookLine key={h.item_num} hook={h} mode={mode} />
            ))}
          </ul>
        </>
      )}

      {atLeast(mode, "detail") && phase.queue_classification && (
        <>
          <h4>Triage subject</h4>
          <div className="sc-counts">
            <span className="sc-count-pill">
              {phase.queue_classification.unclassified} unclassified of{" "}
              {phase.queue_classification.total_items} queue_items
            </span>
          </div>
          <div className="muted bp-fineprint">
            {phase.queue_classification.unclassified_definition}
          </div>
        </>
      )}

      {atLeast(mode, "detail") && phase.constraints?.length > 0 && (
        <>
          <h4>Stated constraints</h4>
          <ul className="sc-list">
            {phase.constraints.map((c) => (
              <li key={c.constraint}>
                <strong>{c.constraint}</strong>
                <div className="muted bp-fineprint">
                  “{c.quote}”{atLeast(mode, "technical") && <> — {c.source}</>}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      {atLeast(mode, "detail") && phase.discoveries && (
        <>
          <h4>
            Discoveries on this phase
            {atLeast(mode, "technical") && <> ({phase.task || "unknown task"})</>}
          </h4>
          <div className="sc-counts">
            {Object.entries(phase.discoveries.counts).map(([status, n]) => (
              <span key={status} className="sc-count-pill">{status}: {n}</span>
            ))}
          </div>
          {phase.discoveries_note && (
            <div className="muted bp-fineprint">{phase.discoveries_note}</div>
          )}
        </>
      )}
    </section>
  );
}

function CurrentAndNext({ model, mode }) {
  const current = model.current;
  const next = model.next;
  const progress = model.progress || {};
  return (
    <section className="sc-section bp-headline">
      <h3>Current phase</h3>
      {!current ? (
        <div className="muted">
          No current phase is recorded.{" "}
          {progress.current_phase_note || "project_state.build_phase names none."}
        </div>
      ) : (
        <>
          <div className="bp-current-line">
            <strong>{current.label}</strong>{" "}
            <StatusBadge status={current.blocked ? "blocked" : current.status}
                         label={current.status_label} />
            {progress.current_order !== null && progress.current_order !== undefined && (
              <span className="muted">
                {" "}— stage {progress.current_order + 1} of {progress.total_phases}
              </span>
            )}
          </div>
          {atLeast(mode, "detail") && current.task && (
            <div className="muted">current task: {current.task}</div>
          )}
          {atLeast(mode, "technical") && current.evidence?.recorded_at && (
            <div className="muted bp-fineprint">
              from project_state.{current.evidence.state_key} (row{" "}
              {current.evidence.row_id}), recorded {fmtTime(current.evidence.recorded_at)}
            </div>
          )}
        </>
      )}

      <h4>Next stage</h4>
      {!next ? (
        /* A stage is named next only on phase-authority evidence, so "none"
           usually means the authority establishes no next stage rather than
           that the roadmap ran out. The read model says which, and that
           reason is shown instead of the old flat "none recorded". */
        <div className="muted">
          {progress.next_phase_note || "No following stage is recorded in the roadmap."}
        </div>
      ) : (
        <div>
          <strong>{next.label}</strong> <StatusBadge status={next.status} /> —{" "}
          {next.description}
        </div>
      )}

      <h4>Next action</h4>
      {!model.next_action ? (
        <div className="muted">No project_state.next_action row is recorded.</div>
      ) : (
        <div className="bp-next-action">
          <div className="bp-longtext">{model.next_action.text}</div>
          {atLeast(mode, "technical") && (
            <div className="muted bp-fineprint">
              project_state.next_action, recorded {fmtTime(model.next_action.recorded_at)}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

/** Whether the build is blocked, and by what, is a Simple question — so the
 *  blocking list itself is never deferred. The three other dispositions are
 *  the full discovery record, which is More Detail. */
function Blockers({ model, mode }) {
  const blockers = model.blockers || [];
  const groups = model.discoveries || {};
  return (
    <section className="sc-section bp-blockers">
      <h3>
        Blocking items{" "}
        <span className="sc-badge sc-badge-error">{blockers.length}</span>
      </h3>
      {atLeast(mode, "detail") && model.discoveries_note && (
        <div className="muted bp-fineprint">{model.discoveries_note}</div>
      )}
      {blockers.length === 0 ? (
        <div className="muted">
          {model.stage_closeout?.note
            || "No unresolved item blocks the current task's stage closeout."}
        </div>
      ) : (
        <ul className="sc-list">
          {blockers.map((b) => (
            <DiscoveryLine key={`${b.task}-${b.revision}`} record={b} mode={mode} />
          ))}
        </ul>
      )}

      {atLeast(mode, "detail") && groups.resolved?.length > 0 && (
        <>
          <h4>Resolved</h4>
          <ul className="sc-list">
            {groups.resolved.map((d) => (
              <DiscoveryLine key={`${d.task}-${d.revision}`} record={d} mode={mode} />
            ))}
          </ul>
        </>
      )}

      {atLeast(mode, "detail") && groups.deferred?.length > 0 && (
        <>
          <h4>Explicitly deferred</h4>
          <ul className="sc-list">
            {groups.deferred.map((d) => (
              <DiscoveryLine key={`${d.task}-${d.revision}`} record={d} mode={mode} />
            ))}
          </ul>
        </>
      )}

      {atLeast(mode, "detail") && groups.open?.length > 0 && (
        <>
          <h4>Open, not classified as blocking</h4>
          <ul className="sc-list">
            {groups.open.map((d) => (
              <DiscoveryLine key={`${d.task}-${d.revision}`} record={d} mode={mode} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function Checkpoint({ checkpoint, mode }) {
  if (!checkpoint || checkpoint.present === false) {
    return (
      <section className="sc-section">
        <h3>External developer checkpoint</h3>
        <div className="muted">
          {checkpoint?.note || "No external_dev_checkpoint row is recorded."}
        </div>
      </section>
    );
  }
  if (checkpoint.error) {
    return (
      <section className="sc-section">
        <h3>External developer checkpoint</h3>
        <div className="inline-error">
          The recorded checkpoint could not be read: {checkpoint.error}
        </div>
      </section>
    );
  }
  const verified = checkpoint.pushed_sha_is_independently_verified;
  return (
    <section className="sc-section bp-checkpoint">
      <h3>
        External developer checkpoint{" "}
        <span className={`sc-badge ${verified ? "sc-badge-ok" : "sc-badge-warn"}`}>
          {checkpoint.lifecycle_state || "state unknown"}
        </span>
      </h3>
      <div className="sc-counts">
        <span className={`sc-count-pill ${verified ? "sc-pill-ok" : "sc-pill-warn"}`}>
          pushed SHA independently verified: {verified ? "yes" : "no"}
        </span>
        {checkpoint.remote_review_required !== undefined && (
          <span className="sc-count-pill">
            remote review required: {String(checkpoint.remote_review_required)}
          </span>
        )}
      </div>
      {atLeast(mode, "technical") && (
        <table className="sc-table">
          <tbody>
            <tr><th>latest pushed</th><td><code>{checkpoint.latest_pushed_sha || "—"}</code></td></tr>
            <tr>
              <th>last independently verified</th>
              <td><code>{checkpoint.latest_remote_verified_sha || "—"}</code></td>
            </tr>
            <tr><th>remote ref</th><td>{checkpoint.remote_ref || "—"}</td></tr>
          </tbody>
        </table>
      )}
      {checkpoint.next_transition && (
        <div className="muted bp-fineprint">
          next: {checkpoint.next_transition.to} — requires{" "}
          {checkpoint.next_transition.requires}
        </div>
      )}
      {checkpoint.scope_boundary && (
        <div className="muted bp-fineprint">{checkpoint.scope_boundary}</div>
      )}
    </section>
  );
}

function AuthorityNote({ model, mode }) {
  const authority = model.authority || {};
  const [open, setOpen] = useState(false);
  const decisions = model.decisions || [];
  const roadmap = model.roadmap_source || {};
  return (
    <section className="sc-section bp-authority">
      <h3>What is authoritative here</h3>
      <ul className="sc-list">
        <li><strong>Roadmap / sequencing:</strong> {authority.sequencing || "—"}</li>
        <li><strong>Tasks / work items:</strong> {authority.work_items || "—"}</li>
        {authority.generated_view && <li>{authority.generated_view}</li>}
        {authority.retired && <li>{authority.retired}</li>}
        {authority.separation_note && (
          <li className="muted">{authority.separation_note}</li>
        )}
      </ul>
      {/* The quoted roadmap row and the decision ids behind it are the
          provenance itself, so the way into them waits for Technical. */}
      {atLeast(mode, "technical") && (
        <button className="context-toggle" onClick={() => setOpen((o) => !o)}>
          {open ? "Hide" : "Show"} the roadmap row and the decisions behind it
        </button>
      )}
      {atLeast(mode, "technical") && open && (
        <div className="context-body">
          {roadmap.raw ? (
            <>
              <h4>project_state.{roadmap.state_key} (row {roadmap.row_id})</h4>
              <div className="bp-longtext">{roadmap.raw}</div>
              {roadmap.parse_note && (
                <div className="inline-error">{roadmap.parse_note}</div>
              )}
            </>
          ) : (
            <div className="muted">No pipeline_roadmap row was found to quote.</div>
          )}
          <h4>Decisions</h4>
          {decisions.length === 0 ? (
            <div className="muted">No governing decision rows were found.</div>
          ) : (
            <ul className="sc-list">
              {decisions.map((d) => (
                <li key={d.id}>
                  <strong>{d.id}</strong> — {d.label}{" "}
                  <span className="sc-badge sc-badge-ok">{d.status}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

/**
 * The Current Build body, as a component, so the Project Map can render the
 * SAME panels from the SAME read model instead of carrying a second copy of
 * them.
 *
 * Exported for exactly one reason: ProjectMap.jsx's "Current Build" area is
 * required to reuse this view rather than reimplement it. It takes the
 * build-path model as a prop and fetches nothing — the Build Path screen below
 * passes what it loaded from /api/workbench/build-path, and the Project Map
 * passes the same payload as the project-intelligence response embedded it.
 * Both are the output of tools/state/build_path.py, so the two screens cannot
 * disagree about where the build is.
 *
 * `mode` is the Project Map's presentation mode (see presentationMode.js). It
 * selects how much of the SAME model is disclosed and nothing else: no branch
 * below reads a different field, recomputes a status or drops anything the
 * read model sent. The default is full disclosure, so the standalone Build
 * Path screen — which passes no mode — renders exactly what it rendered
 * before the mode existed.
 */
export function CurrentBuildPanel({ model, mode = FULL_DISCLOSURE }) {
  return (
    <>
      <div className="sc-section-group">
        <h2>Where the build is</h2>
        <CurrentAndNext model={model} mode={mode} />
      </div>

      <div className="sc-section-group">
        <h2>Roadmap</h2>
        <section className="sc-section">
          <h3>P0 → P6 sequence</h3>
          <MermaidDiagram source={model.mermaid} />
        </section>
        <div className="bp-phase-grid">
          {model.phases?.length > 0 ? (
            model.phases.map((p) => <PhaseCard key={p.id} phase={p} mode={mode} />)
          ) : (
            <div className="muted">
              No phases were parsed from the roadmap row, so none are shown.
            </div>
          )}
        </div>
      </div>

      <div className="sc-section-group">
        <h2>Blockers</h2>
        <Blockers model={model} mode={mode} />
      </div>

      {/* The push checkpoint and the quoted authority are evidence about the
          build, not the build. Simple says where the build is and what is in
          the way; this group is what More Detail and Technical are for. */}
      {atLeast(mode, "detail") && (
        <div className="sc-section-group">
          <h2>Checkpoint and authority</h2>
          <Checkpoint checkpoint={model.checkpoint} mode={mode} />
          <AuthorityNote model={model} mode={mode} />
          {atLeast(mode, "technical") && (
            <div className="muted bp-fineprint">
              state revision <code>{model.state_revision}</code>, generated{" "}
              {fmtTime(model.generated_at)}
            </div>
          )}
        </div>
      )}
    </>
  );
}

export default function BuildPath({ onBack }) {
  const [model, setModel] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lastLoadedAt, setLastLoadedAt] = useState(null);
  // "current" is the default on purpose: the question this screen was built to
  // answer first is still "where is the build right now".
  const [tab, setTab] = useState("current");

  async function load() {
    setLoading(true);
    const result = await getBuildPath();
    setLoading(false);
    if (!result.ok) {
      setError(result.error);
      // A prior successful load stays visible, marked stale, rather than
      // being replaced by nothing. A FAILED load never becomes a diagram.
      return;
    }
    setError("");
    setModel(result.data);
    setLastLoadedAt(new Date().toISOString());
  }

  useEffect(() => {
    load();
  }, []);

  const stale = Boolean(error && model);
  const onCurrent = tab === "current";

  return (
    <div className="workbench">
      <header className="stage-banner">
        <button className="link-btn" onClick={onBack}>← Back to conversation</button>
        <span className="stage-label">Build Path</span>
        <span className="stage-detail">
          {onCurrent
            ? "Read-only view of the P0–P6 contained-pipeline sequence, derived from the "
              + "spine. Nothing on this screen can change roadmap, queue or phase state."
            : "Read-only view of the destination architecture CIS is being built to "
              + "support. Not a build sequence, and not activated work."}
        </span>
        {/* Refresh belongs to the tab it refreshes. The destination tab carries
            its own, because it reads a different model from a different route. */}
        {onCurrent && (
          <button className="link-btn" onClick={load} disabled={loading}
                  style={{ marginLeft: "auto" }}>
            {loading ? "Loading…" : "Refresh"}
          </button>
        )}
      </header>

      {/* Two tabs, two read models, two different questions — see the note at the
          top of this file. The tabs switch which question is on screen; they never
          merge the two graphs. */}
      <div className="bp-tabs" role="tablist" aria-label="Build Path views">
        <button role="tab" aria-selected={onCurrent}
                className={`bp-tab${onCurrent ? " active" : ""}`}
                onClick={() => setTab("current")}>
          Current Build
        </button>
        <button role="tab" aria-selected={!onCurrent}
                className={`bp-tab${!onCurrent ? " active" : ""}`}
                onClick={() => setTab("destination")}>
          Destination Architecture
        </button>
      </div>

      {!onCurrent && (
        <div className="sc-body bp-body">
          <DestinationArchitecture />
        </div>
      )}

      {onCurrent && (
      <div className="sc-body bp-body">
        {error && (
          <div className="banner-error">
            Could not load the build path: {error}
            {stale && " — showing the last successfully loaded view below."}
          </div>
        )}
        {stale && (
          <div className="sc-stale-notice">
            STALE — last successfully loaded {fmtTime(lastLoadedAt)}. This may no longer
            reflect the current build path.
          </div>
        )}

        {!model && !error && loading && (
          <div className="muted">Loading the build path…</div>
        )}
        {!model && error && (
          <div className="muted">
            No build path has loaded in this session, so none is shown. Nothing on this
            screen is filled in from memory or assumption.
          </div>
        )}

        {model && <CurrentBuildPanel model={model} />}
      </div>
      )}
    </div>
  );
}
