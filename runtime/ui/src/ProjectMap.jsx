import { useEffect, useMemo, useState } from "react";
import { getProjectIntelligence } from "./api";
import MermaidDiagram from "./MermaidDiagram";
import DestinationArchitecture from "./DestinationArchitecture";
import { CurrentBuildPanel } from "./BuildPath";
import { atLeast } from "./presentationMode";

// The Workbench "Project Map", over GET /api/workbench/project-intelligence
// (runtime/api/project_intelligence.py -> tools/state/project_intelligence.py).
//
// WHAT THIS SCREEN IS FOR. One reader: Eric, who is not a programmer. So the
// plain-language sentence comes first and the identifier comes second —
// never instead of it. Technical terms stay on screen because development and
// recovery need them, but no major technical term appears here without an
// explanation reachable beside it (see the Terms panel on Overview, whose
// wording is the reviewed vocabulary file's, not this component's).
//
// WHAT IT HOLDS. Nothing. Every phase, node, capability, finding, queue row,
// relationship, status, plain-language string and diagram arrives in the
// response. There is no roadmap in this file, no destination architecture, no
// capability list and no queue classification. If an authority changes, this
// screen changes with it; if something is not recorded, it says so.
//
// REUSE, NOT DUPLICATION. The Current Build area renders <CurrentBuildPanel>
// from BuildPath.jsx against the build-path payload the response embedded, and
// the Destination area renders <DestinationArchitecture/>, which fetches its
// own route. Neither view is reimplemented here, so this screen cannot drift
// from the two screens that own those questions.
//
// ONE MODE, ALL SIX AREAS (PM-D3). Simple / More Detail / Technical is a single
// global control, so it has to reach the two reused components as well as the
// four areas this file draws. It does that by PASSING THE MODE as a prop —
// `mode` on CurrentBuildPanel and DestinationArchitecture — never by keeping a
// Project-Map-only copy of either view. The predicate itself lives in
// presentationMode.js precisely so all three files share one vocabulary.
//
// READ-ONLY. The one api.js function imported is a parameterless GET. There is
// no mutation call in this file, and nothing here classifies a queue item.

const AREA_ORDER = ["overview", "current_build", "queue_problems", "system_anatomy",
                    "destination", "trajectory"];

function fmtTime(iso) {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

/** How a statement is known. Rendered from the response's own
 *  confidence_classes, so the wording cannot drift from the read model's. */
function ConfidenceBadge({ cls, classes }) {
  if (!cls) return null;
  const def = (classes || []).find((c) => c.id === cls);
  const style = cls === "authoritative" ? "pm-conf-auth"
    : cls === "derived_from_evidence" ? "pm-conf-derived"
      : "pm-conf-none";
  return (
    <span className={`sc-badge ${style}`} title={def?.plain_english || cls}>
      {def?.label || cls.replace(/_/g, " ")}
    </span>
  );
}

/** A plain-language line, with the honest fallback when none is recorded. */
function PlainLine({ text, recorded }) {
  if (recorded === false || !text) {
    return <div className="pm-plain pm-plain-missing">Plain-language explanation not yet recorded.</div>;
  }
  return <div className="pm-plain">{text}</div>;
}

/** A broken chain, said out loud. The card requires this exact sentence
 *  wherever a relationship is not recorded. */
function MissingLink({ explanation }) {
  return (
    <div className="pm-missing">
      <strong>No authoritative link recorded yet.</strong>
      {explanation && <div className="muted bp-fineprint">{explanation}</div>}
    </div>
  );
}

function AuthorityRefs({ refs, mode }) {
  if (!atLeast(mode, "technical") || !refs || refs.length === 0) return null;
  return (
    <ul className="sc-list pm-refs">
      {refs.map((ref, i) => (
        <li key={i}>
          <code>{ref.kind}</code>
          {ref.decision_id && <> · decision <code>{ref.decision_id}</code></>}
          {ref.clause && <> · clause <code>{ref.clause}</code></>}
          {ref.state_key && <> · <code>project_state.{ref.state_key}</code></>}
          {ref.table && <> · <code>{ref.table}</code></>}
          {ref.task && <> · task <code>{ref.task}</code></>}
          {ref.revision !== undefined && ref.revision !== null && <> · revision {ref.revision}</>}
          {ref.field && <> · field <code>{ref.field}</code></>}
          {ref.matched_term && <> · matched <code>{ref.matched_term}</code></>}
          {(ref.quote || ref.declaration || ref.value) && (
            <div className="pm-quote">“{ref.quote || ref.declaration || ref.value}”</div>
          )}
        </li>
      ))}
    </ul>
  );
}

// ── Overview ────────────────────────────────────────────────────────────

function Glossary({ glossary, mode }) {
  const [open, setOpen] = useState(false);
  if (!glossary || glossary.length === 0) return null;
  return (
    <section className="sc-section">
      <h3>Terms used on this screen</h3>
      <div className="muted bp-fineprint">
        Every technical word below stays visible on the map because development and recovery
        need it. This is what each one means.
      </div>
      <button className="context-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide" : "Show"} {glossary.length} terms
      </button>
      {open && (
        <dl className="pm-glossary">
          {glossary.map((g) => (
            <div key={g.term} className="pm-glossary-entry">
              <dt>{g.term}</dt>
              <dd>
                <div className="pm-plain">{g.plain_english}</div>
                {atLeast(mode, "detail") && g.technical_note && (
                  <div className="muted bp-fineprint">{g.technical_note}</div>
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}

function ConfidenceLegend({ classes, mode }) {
  if (!classes || classes.length === 0) return null;
  return (
    <section className="sc-section">
      <h3>How to read the labels</h3>
      <ul className="sc-list">
        {classes.map((c) => (
          <li key={c.id}>
            <ConfidenceBadge cls={c.id} classes={classes} />{" "}
            <span className="pm-plain-inline">{c.plain_english}</span>
            {atLeast(mode, "technical") && c.technical_note && (
              <div className="muted bp-fineprint">{c.technical_note}</div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Overview({ model, mode, onGo }) {
  const counts = model.counts || {};
  const areas = (model.areas || []).filter((a) => a.id !== "overview");
  const overview = (model.areas || []).find((a) => a.id === "overview");
  const headline = {
    current_build: `${counts.phases ?? 0} build steps`,
    queue_problems: `${counts.problems ?? 0} findings · ${counts.awaiting_triage ?? 0} items awaiting triage`,
    system_anatomy: `${counts.anatomy_areas ?? 0} areas · ${counts.capabilities ?? 0} capabilities`,
    destination: `${counts.destination_nodes ?? 0} destination nodes, none activated`,
    trajectory: "today → destination",
  };
  return (
    <>
      <div className="sc-section-group">
        <h2>What this screen is</h2>
        <section className="sc-section">
          {overview && <PlainLine text={overview.plain_english} recorded />}
          <div className="muted bp-fineprint">
            Nothing on this screen can change the roadmap, the work list, the current phase or
            the destination. It only reads and explains.
          </div>
        </section>
        <section className="sc-section">
          <h3>The five views, and how they connect</h3>
          <MermaidDiagram source={model.overview_mermaid} />
          <div className="muted bp-fineprint">
            The dashed arrow is an explanation, not an order of work.
          </div>
        </section>
        <div className="pm-area-grid">
          {areas.map((area) => (
            <button key={area.id} className="pm-area-card" onClick={() => onGo(area.id)}>
              <div className="pm-area-label">{area.label} →</div>
              <div className="pm-area-question">{area.plain_question}</div>
              <PlainLine text={area.plain_english} recorded />
              <div className="pm-area-count">{headline[area.id]}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="sc-section-group">
        <h2>Reading this map</h2>
        <ConfidenceLegend classes={model.confidence_classes} mode={mode} />
        <Glossary glossary={model.glossary} mode={mode} />
        {atLeast(mode, "detail") && <AuthorityPanel model={model} mode={mode} />}
      </div>
    </>
  );
}

function AuthorityPanel({ model, mode }) {
  const authority = model.authority || {};
  return (
    <section className="sc-section pm-authority">
      <h3>What is authoritative here, and what is not</h3>
      <div className="pm-plain">{authority.role}</div>
      <h4>Views this one is built from</h4>
      <ul className="sc-list">
        {(authority.composes || []).map((c) => (
          <li key={c.read_model}>
            <strong>{c.answers}</strong>
            {atLeast(mode, "technical") && <> — <code>{c.module}</code></>}
            <div className="muted bp-fineprint">{c.note}</div>
          </li>
        ))}
      </ul>
      <h4>Read directly</h4>
      <ul className="sc-list">
        {(authority.reads_directly || []).map((r) => (
          <li key={r.source}>
            <code>{r.source}</code>
            <div className="muted bp-fineprint">{r.why}</div>
          </li>
        ))}
      </ul>
      <h4>This screen cannot</h4>
      <ul className="sc-list">
        {(model.read_only_boundary || []).map((line) => <li key={line}>{line}</li>)}
      </ul>
      <div className="muted bp-fineprint">
        Write paths: {authority.write_paths}. Model calls while this page loads:{" "}
        {authority.llm_runtime_calls}
      </div>
      {atLeast(mode, "technical") && (
        <>
          <div className="muted bp-fineprint">
            Never read as authority: {(authority.never_reads || []).join(", ")}
          </div>
          <div className="muted bp-fineprint">{authority.status_separation}</div>
        </>
      )}
      {(model.problems_found || []).length > 0 && (
        <>
          <h4>Things this read model could not resolve</h4>
          <ul className="sc-list">
            {model.problems_found.map((p, i) => (
              <li key={i}><code>{p.kind}</code> — {p.detail}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

// ── Queue / Problems ────────────────────────────────────────────────────

const PROBLEM_BADGE = {
  blocking: "sc-badge-error",
  open: "sc-badge-warn",
  deferred: "sc-badge-warn",
  resolved: "sc-badge-ok",
};

function ProblemDetail({ problem, mode, classes, capabilities }) {
  const solution = problem.solution_direction || {};
  const position = problem.build_position || {};
  const byId = useMemo(
    () => Object.fromEntries((capabilities || []).map((c) => [c.id, c])), [capabilities]);
  return (
    <div className="pm-detail">
      <h3>
        {problem.id || `finding ${problem.task} #${problem.revision}`}{" "}
        <span className={`sc-badge ${PROBLEM_BADGE[problem.display_status] || ""}`}>
          {problem.display_status}
        </span>
      </h3>

      <h4>Plain English</h4>
      <PlainLine text={problem.plain_english} recorded={problem.plain_language_recorded} />
      {problem.why_it_matters && (
        <>
          <h4>Why it matters</h4>
          <div className="pm-plain">{problem.why_it_matters}</div>
        </>
      )}

      <h4>Current disposition</h4>
      <div>
        <code>{problem.disposition}</code>
        {problem.blocking === true && <> · <strong>blocking</strong></>}
        {problem.blocking === false && <> · non-blocking</>}
        {problem.resolved ? <> · resolved</> : <> · not resolved</>}
      </div>
      {atLeast(mode, "technical") && problem.status_systems && (
        <div className="muted bp-fineprint">{problem.status_systems.note}</div>
      )}

      <h4>Current solution direction</h4>
      {solution.confidence_class === "not_yet_linked" ? (
        <MissingLink explanation={solution.explanation} />
      ) : (
        <>
          <ConfidenceBadge cls={solution.confidence_class} classes={classes} />
          <div className="bp-longtext">{solution.text}</div>
          <div className="muted bp-fineprint">{solution.explanation}</div>
          <AuthorityRefs refs={solution.authority_refs} mode={mode} />
        </>
      )}

      {problem.deferral && (
        <>
          <h4>Deferred to</h4>
          <div className="bp-longtext">{problem.deferral.destination}</div>
          {atLeast(mode, "detail") && problem.deferral.reason && (
            <div className="muted bp-fineprint">Reason: {problem.deferral.reason}</div>
          )}
          {atLeast(mode, "detail") && problem.deferral.trigger && (
            <div className="muted bp-fineprint">Reconsider when: {problem.deferral.trigger}</div>
          )}
        </>
      )}

      {atLeast(mode, "detail") && (
        <>
          <h4>Build relationship</h4>
          {position.confidence_class === "derived_from_evidence" ? (
            <>
              <ConfidenceBadge cls={position.confidence_class} classes={classes} />{" "}
              <strong>{position.phase_label || position.phase_id}</strong>{" "}
              <span className="muted">({position.phase_status})</span>
              <div className="muted bp-fineprint">{position.explanation}</div>
              <AuthorityRefs refs={position.authority_refs} mode={mode} />
            </>
          ) : (
            <MissingLink explanation={position.explanation} />
          )}

          <h4>Capability this concerns</h4>
          {problem.capability_ids.length === 0 ? (
            <MissingLink explanation={
              "No declared capability identifier appears in this finding's own text."} />
          ) : (
            <ul className="sc-list">
              {problem.capability_ids.map((id) => (
                <li key={id}>
                  <strong>{byId[id]?.label || id}</strong>{" "}
                  <ConfidenceBadge cls="derived_from_evidence" classes={classes} />
                  <PlainLine text={byId[id]?.plain_english} recorded />
                </li>
              ))}
            </ul>
          )}

          {problem.named_in_state.length > 0 && (
            <>
              <h4>Named in the project's own recorded state</h4>
              <ul className="sc-list">
                {problem.named_in_state.map((m, i) => (
                  <li key={i}>
                    <ConfidenceBadge cls={m.confidence_class} classes={classes} />{" "}
                    <code>project_state.{m.state_key}</code>
                    <div className="pm-quote">“{m.quote}”</div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      <h4>Technical detail</h4>
      <div className="bp-longtext">{problem.summary}</div>
      {atLeast(mode, "technical") && (
        <div className="muted bp-fineprint">
          <code>{problem.evidence.table}</code> · task <code>{problem.evidence.task}</code> ·
          revision {problem.evidence.revision} · kind <code>{problem.evidence.kind}</code> ·
          recorded {fmtTime(problem.evidence.recorded_at)}
          {problem.originating_stage && <> · originating stage <code>{problem.originating_stage}</code></>}
        </div>
      )}
    </div>
  );
}

function QueueItemDetail({ item, mode, classes }) {
  return (
    <div className="pm-detail">
      <h3>
        Queue {item.item_num}{" "}
        <span className={`sc-badge ${item.awaiting_triage ? "sc-badge-warn" : "sc-badge-ok"}`}>
          {item.classification_status}
        </span>
      </h3>
      <div className="pm-item-title">{item.title}</div>

      <h4>Plain English</h4>
      <PlainLine text={item.plain_english} recorded={item.plain_language_recorded} />
      {item.why_it_matters && (
        <>
          <h4>Why it matters</h4>
          <div className="pm-plain">{item.why_it_matters}</div>
        </>
      )}

      <h4>Current classification</h4>
      {item.awaiting_triage ? (
        <div className="pm-missing">
          <strong>AWAITING TRIAGE</strong>
          <div className="muted bp-fineprint">
            This item carries neither a scope nor a status. Nothing on this screen assigns
            either one.
          </div>
        </div>
      ) : (
        <ul className="sc-list">
          <li>status: <code>{item.need_status || "—"}</code></li>
          <li>scope: {item.scope ? <code>{item.scope}</code> : <span className="muted">not set</span>}</li>
          {item.check_class && <li>check class: <code>{item.check_class}</code></li>}
        </ul>
      )}

      <h4>Build-phase relationship</h4>
      {(item.phase_hooks || []).length === 0 ? (
        <MissingLink explanation={
          "The recorded roadmap does not name this item at any phase."} />
      ) : (
        <ul className="sc-list">
          {item.phase_hooks.map((h) => (
            <li key={h.phase_id}>
              <strong>{h.phase_label}</strong>{" "}
              <ConfidenceBadge cls={h.confidence_class} classes={classes} />
              <AuthorityRefs refs={h.authority_refs} mode={mode} />
            </li>
          ))}
        </ul>
      )}

      {atLeast(mode, "detail") && (
        <>
          <h4>Known relationships to other items</h4>
          {(item.edges || []).length === 0 ? (
            <MissingLink explanation={"No queue_edges row records a relationship for this item."} />
          ) : (
            <ul className="sc-list">
              {item.edges.map((e, i) => (
                <li key={i}>
                  {e.direction === "out" ? <>this <code>{e.kind}</code> {e.other}</>
                    : <>{e.other} <code>{e.kind}</code> this</>}{" "}
                  <ConfidenceBadge cls={e.confidence_class} classes={classes} />
                  {atLeast(mode, "technical") && (
                    <div className="muted bp-fineprint">
                      stored confidence <code>{e.stored_confidence}</code> — {e.evidence}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      <h4>Technical text as recorded</h4>
      <div className="bp-longtext pm-pre">{item.body_excerpt}</div>
      {item.body_truncated && (
        <div className="muted bp-fineprint">Excerpt — the stored item continues.</div>
      )}
      {atLeast(mode, "technical") && (
        <div className="muted bp-fineprint">
          <code>queue_items.item_num = {item.item_num}</code> · tier {item.tier} · source line{" "}
          {item.source_line} · source sha <code>{item.source_sha}</code>
        </div>
      )}
    </div>
  );
}

function QueueProblems({ model, mode }) {
  const classes = model.confidence_classes;
  const problems = model.problems?.items || [];
  const queue = model.queue || {};
  const capabilities = model.capability_model?.capabilities || [];

  const [pane, setPane] = useState("problems");
  const [problemKey, setProblemKey] = useState(null);
  const [itemNum, setItemNum] = useState(null);
  const [queueFilter, setQueueFilter] = useState("awaiting");
  const [problemFilter, setProblemFilter] = useState("unresolved");

  const keyOf = (p) => p.id || `${p.task}#${p.revision}`;
  const shownProblems = problems.filter((p) =>
    problemFilter === "all" ? true
      : problemFilter === "blocking" ? p.display_status === "blocking"
        : !p.resolved);
  const shownItems = (queue.items || []).filter((i) =>
    queueFilter === "all" ? true
      : queueFilter === "awaiting" ? i.awaiting_triage
        : !i.awaiting_triage);

  const selectedProblem = problems.find((p) => keyOf(p) === problemKey) || null;
  const selectedItem = (queue.items || []).find((i) => i.item_num === itemNum) || null;

  return (
    <>
      <div className="sc-section-group">
        <h2>Two different lists, kept apart</h2>
        <section className="sc-section">
          <div className="pm-plain">
            <strong>Problems</strong> are things found while working and written down so they
            cannot be quietly forgotten. <strong>Queue items</strong> are recorded pieces of
            work. They are not the same list, and a problem is not automatically a queue item.
          </div>
          {/* More Detail is where the two lists stop being two names and become
              two definitions: what a finding IS, and the exact rule by which a
              row counts as untriaged. Both sentences are the read model's. */}
          {atLeast(mode, "detail") && model.problems?.statement && (
            <div className="muted bp-fineprint">
              Findings: {model.problems.statement}
            </div>
          )}
          {atLeast(mode, "detail") && queue.counts?.unclassified_definition && (
            <div className="muted bp-fineprint">
              Awaiting triage means: {queue.counts.unclassified_definition}
            </div>
          )}
          <div className="sc-counts">
            <span className="sc-count-pill">{problems.length} findings recorded</span>
            <span className="sc-count-pill sc-pill-warn">
              {model.counts?.blocking_problems ?? 0} blocking
            </span>
            <span className="sc-count-pill">{queue.total_items ?? 0} queue items</span>
            <span className="sc-count-pill sc-pill-warn">
              {queue.awaiting_triage ?? 0} items awaiting formal triage
            </span>
            <span className="sc-count-pill sc-pill-ok">
              {queue.classified ?? 0} already classified
            </span>
          </div>
          <div className="pm-triage-notice">
            {/* DERIVED FROM THE LIVE COUNT, NOT HARDCODED. This headline was a
                literal rendered unconditionally, so once the queue authority
                reached zero awaiting it kept asserting the classification pass
                was outstanding directly above pills reading "0 items awaiting
                formal triage" — and it stated that unscoped, while the read
                model's own statement below is scoped "by this screen".
                Recorded as project_state rows 163 and 184 (observation 3).
                NEITHER BRANCH MAKES A CLAIM ABOUT THE QUEUE_TRIAGE *STAGE*:
                stage status is phase authority (ADR-PIPE-006), it is not
                derived here, and the sequencing line below still reports it
                exactly as the Build Path read model gives it. */}
            {(queue.awaiting_triage ?? 0) > 0 ? (
              <strong>Queue triage has not been performed.</strong>
            ) : (
              <strong>
                Every one of the {queue.total_items ?? 0} queue items carries a
                classification.
              </strong>
            )}
            <div className="muted bp-fineprint">{queue.triage_state?.statement}</div>
            {/* Where triage sits comes from the composed build model, not from
                wording in this component — see triage_state.sequencing.note. */}
            {queue.triage_state?.sequencing?.stage_label ? (
              <div className="muted bp-fineprint">
                The recorded roadmap places it at{" "}
                <strong>{queue.triage_state.sequencing.stage_label}</strong>, currently{" "}
                {queue.triage_state.sequencing.stage_status} (
                {queue.triage_state.sequencing.stage_description}).
                {atLeast(mode, "technical") && (
                  <> Authority: <code>{queue.triage_state.sequencing.authority}</code>.</>
                )}
              </div>
            ) : (
              <MissingLink explanation={queue.triage_state?.sequencing?.note} />
            )}
            {atLeast(mode, "detail") && queue.triage_state?.sequencing?.constraints_quote && (
              <div className="pm-quote">
                “{queue.triage_state.sequencing.constraints_quote}”
              </div>
            )}
          </div>
          {/* Which tables answer the work-item question, and how much of the
              relationship graph between items actually exists. */}
          {atLeast(mode, "technical") && (
            <div className="muted bp-fineprint">
              {queue.authority}
              {queue.edge_count !== undefined && (
                <> <code>queue_edges</code> records {queue.edge_count} relationships
                  between items.</>
              )}
              {(queue.stale_vocabulary_item_nums || []).length > 0 && (
                <> Items carrying a status outside the recorded vocabulary:{" "}
                  {queue.stale_vocabulary_item_nums.join(", ")}.</>
              )}
            </div>
          )}
        </section>
      </div>

      <div className="bp-tabs" role="tablist" aria-label="Queue and problems">
        <button role="tab" aria-selected={pane === "problems"}
                className={`bp-tab${pane === "problems" ? " active" : ""}`}
                onClick={() => setPane("problems")}>
          Problems / discoveries
        </button>
        <button role="tab" aria-selected={pane === "queue"}
                className={`bp-tab${pane === "queue" ? " active" : ""}`}
                onClick={() => setPane("queue")}>
          Queue items
        </button>
      </div>

      {pane === "problems" && (
        <div className="pm-split">
          <div className="pm-list-pane">
            <div className="pm-filters">
              {[["unresolved", "Not resolved"], ["blocking", "Blocking"], ["all", "All"]].map(
                ([id, label]) => (
                  <button key={id} className={`pm-filter${problemFilter === id ? " active" : ""}`}
                          onClick={() => setProblemFilter(id)}>{label}</button>
                ))}
            </div>
            {shownProblems.length === 0 ? (
              <div className="muted">No findings match this filter.</div>
            ) : (
              <ul className="pm-list">
                {shownProblems.map((p) => (
                  <li key={keyOf(p)}>
                    <button
                      className={`pm-list-item${problemKey === keyOf(p) ? " active" : ""}`}
                      onClick={() => setProblemKey(keyOf(p))}>
                      <span className="pm-list-id">{p.id || `#${p.revision}`}</span>{" "}
                      <span className={`sc-badge ${PROBLEM_BADGE[p.display_status] || ""}`}>
                        {p.display_status}
                      </span>{" "}
                      <span className="pm-list-text">
                        {p.plain_language_recorded ? p.plain_english : p.summary.slice(0, 110)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="pm-detail-pane">
            {selectedProblem ? (
              <ProblemDetail problem={selectedProblem} mode={mode} classes={classes}
                             capabilities={capabilities} />
            ) : (
              <div className="muted">Choose a finding to see what it is and what is being done about it.</div>
            )}
          </div>
        </div>
      )}

      {pane === "queue" && (
        <div className="pm-split">
          <div className="pm-list-pane">
            <div className="pm-filters">
              {[["awaiting", `Awaiting triage (${queue.awaiting_triage ?? 0})`],
                ["classified", `Classified (${queue.classified ?? 0})`],
                ["all", `All (${queue.total_items ?? 0})`]].map(([id, label]) => (
                  <button key={id} className={`pm-filter${queueFilter === id ? " active" : ""}`}
                          onClick={() => setQueueFilter(id)}>{label}</button>
                ))}
            </div>
            {atLeast(mode, "detail") && (
              <Distributions distributions={queue.distributions} />
            )}
            <ul className="pm-list">
              {shownItems.map((i) => (
                <li key={i.item_num}>
                  <button className={`pm-list-item${itemNum === i.item_num ? " active" : ""}`}
                          onClick={() => setItemNum(i.item_num)}>
                    <span className="pm-list-id">{i.item_num}</span>{" "}
                    <span className={`sc-badge ${i.awaiting_triage ? "sc-badge-warn" : "sc-badge-ok"}`}>
                      {i.awaiting_triage ? "awaiting triage" : i.need_status}
                    </span>{" "}
                    <span className="pm-list-text">{i.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="pm-detail-pane">
            {selectedItem ? (
              <QueueItemDetail item={selectedItem} mode={mode} classes={classes} />
            ) : (
              <div className="muted">
                Choose a work item to see it in full. Items marked awaiting triage are shown
                exactly as recorded — this screen does not classify them.
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function Distributions({ distributions }) {
  if (!distributions) return null;
  const blocks = [["need_status", "Status"], ["tier", "Tier"], ["check_class", "Check class"]];
  return (
    <div className="pm-distributions">
      {blocks.map(([key, label]) => {
        const rows = distributions[key];
        if (!rows) return null;
        return (
          <div key={key} className="pm-distribution">
            <h4>{label}</h4>
            <div className="sc-counts">
              {rows.map((r, i) => (
                <span key={i} className="sc-count-pill">
                  {r.value === null ? "not set" : String(r.value)}: {r.count}
                </span>
              ))}
            </div>
          </div>
        );
      })}
      {distributions.scope && (
        <div className="pm-distribution">
          <h4>Scope</h4>
          <div className="muted bp-fineprint">
            {distributions.scope.filter((r) => r.value === null).map((r) => r.count)[0] ?? 0} of{" "}
            {distributions.scope.reduce((n, r) => n + r.count, 0)} items have no scope recorded.
            The rest carry free text rather than a fixed set of values, which is one of the
            things triage has to settle.
          </div>
        </div>
      )}
    </div>
  );
}

// ── System Anatomy ──────────────────────────────────────────────────────

const CAP_BADGE = {
  REGISTERED: "sc-badge-ok",
  BUILT_NOT_REGISTERED: "sc-badge-warn",
  NO_ROUTE_SURFACE: "",
  FILES_MISSING: "sc-badge-error",
  UNKNOWN: "sc-badge-error",
};

function CapabilityDetail({ capability, model, mode }) {
  const classes = model.confidence_classes;
  const states = model.capability_model?.states || [];
  const state = states.find((s) => s.id === capability.status);
  const fileText = Object.fromEntries(
    (model.anatomy?.files || []).map((f) => [f.path, f]));
  const problems = model.problems?.items || [];
  const related = problems.filter((p) => p.capability_ids.includes(capability.id));
  const [openFile, setOpenFile] = useState(null);

  return (
    <div className="pm-detail">
      <h3>
        {capability.label}{" "}
        <span className={`sc-badge ${CAP_BADGE[capability.status] || ""}`}>
          {capability.status.replace(/_/g, " ").toLowerCase()}
        </span>
      </h3>

      <h4>Plain English</h4>
      <PlainLine text={capability.plain_english}
                 recorded={capability.plain_language_recorded} />

      <h4>Is it switched on?</h4>
      <div className="pm-plain">{state?.plain_english}</div>
      <div className="muted bp-fineprint">
        {capability.registration.evidence}
        {atLeast(mode, "technical") && state?.technical_note && <> — {state.technical_note}</>}
      </div>
      {atLeast(mode, "technical") && capability.registration.endpoint && (
        <div className="muted bp-fineprint">
          endpoint: <code>{capability.registration.endpoint}</code> · blueprint{" "}
          <code>{capability.registration.blueprint}</code>
        </div>
      )}

      {capability.authority_mentions.length > 0 && (
        <>
          <h4>What the build authority itself says about it</h4>
          <ul className="sc-list">
            {capability.authority_mentions.map((m, i) => (
              <li key={i}>
                <ConfidenceBadge cls="derived_from_evidence" classes={classes} />{" "}
                <code>project_state.{m.source}</code>
                <div className="pm-quote">“{m.quote}”</div>
                {atLeast(mode, "technical") && (
                  <div className="muted bp-fineprint">matched on <code>{m.matched_term}</code></div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      <h4>Where it exists in the system</h4>
      <ul className="sc-list">
        {capability.files.map((f) => (
          <li key={f.path}>
            <button className="link-btn pm-file-btn"
                    onClick={() => setOpenFile(openFile === f.path ? null : f.path)}>
              <code>{f.path}</code>
            </button>{" "}
            {f.exists ? (
              atLeast(mode, "technical") && <span className="muted">({f.lines} lines)</span>
            ) : (
              <span className="sc-badge sc-badge-error">not present</span>
            )}
            {openFile === f.path && (
              <div className="pm-file-detail">
                {fileText[f.path] ? (
                  <>
                    <PlainLine text={fileText[f.path].plain_english} recorded />
                    {fileText[f.path].what_it_does && (
                      <div className="muted bp-fineprint">
                        What it does: {fileText[f.path].what_it_does}
                      </div>
                    )}
                    {fileText[f.path].why_it_matters && (
                      <div className="muted bp-fineprint">
                        Why it matters: {fileText[f.path].why_it_matters}
                      </div>
                    )}
                    {atLeast(mode, "detail") && fileText[f.path].technical_role && (
                      <div className="muted bp-fineprint">
                        Technical role: {fileText[f.path].technical_role}
                      </div>
                    )}
                  </>
                ) : (
                  <PlainLine recorded={false} />
                )}
              </div>
            )}
          </li>
        ))}
      </ul>

      {capability.migrations.length > 0 && (
        <>
          <h4>Database updates it needs</h4>
          <ul className="sc-list">
            {capability.migrations.map((m) => (
              <li key={m.migration}>
                <strong>migration {m.migration}</strong>{" "}
                <span className={`sc-badge ${m.applied === true ? "sc-badge-ok"
                  : m.applied === false ? "sc-badge-warn" : "sc-badge-error"}`}>
                  {m.applied === true ? "applied" : m.applied === false ? "not applied"
                    : m.applied === "partial" ? "partially applied" : "unknown"}
                </span>
                {atLeast(mode, "technical") && (
                  <div className="muted bp-fineprint">{m.detected_by}</div>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      {atLeast(mode, "detail") && (
        <>
          <h4>Where it fits in the current build</h4>
          {capability.build_position.length === 0 ? (
            <MissingLink explanation={capability.build_position_note} />
          ) : (
            <ul className="sc-list">
              {capability.build_position.map((b) => (
                <li key={b.phase_id}>
                  <strong>{b.phase_label}</strong>{" "}
                  <span className="muted">({b.phase_status})</span>{" "}
                  <ConfidenceBadge cls={b.confidence_class} classes={classes} />
                  <AuthorityRefs refs={b.authority_refs} mode={mode} />
                </li>
              ))}
            </ul>
          )}

          <h4>Problems recorded against it</h4>
          {related.length === 0 ? (
            <div className="muted">No recorded finding names this capability.</div>
          ) : (
            <ul className="sc-list">
              {related.map((p) => (
                <li key={p.id || p.revision}>
                  <strong>{p.id || `#${p.revision}`}</strong>{" "}
                  <span className={`sc-badge ${PROBLEM_BADGE[p.display_status] || ""}`}>
                    {p.display_status}
                  </span>
                  <PlainLine text={p.plain_english} recorded={p.plain_language_recorded} />
                </li>
              ))}
            </ul>
          )}

          <h4>Larger goal it supports</h4>
          <MissingLink explanation={capability.destination_link.explanation} />
        </>
      )}

      {atLeast(mode, "technical") && (
        <>
          <div className="muted bp-fineprint">
            provenance: <code>{capability.provenance_class}</code> — {capability.provenance_note}
          </div>
          {capability.decision_ids.length > 0 && (
            <div className="muted bp-fineprint">
              decisions: {capability.decision_ids.map((d) => <code key={d}>{d} </code>)}
            </div>
          )}
        </>
      )}
    </div>
  );
}

const AREA_BADGE = {
  ACTIVE: "sc-badge-ok", DORMANT: "", INCOMPLETE: "sc-badge-error", UNKNOWN: "sc-badge-warn",
  INFORMATIONAL: "",
};

/** What is recorded about an area BEYOND its own description: how much of it is
 *  switched on, which findings name something inside it, and whether it claims
 *  a capability that does not resolve. Every line is derived from rows the
 *  response already carries — the same derivation CapabilityDetail uses one
 *  level down — so nothing here is invented to make More Detail look different.
 */
function AreaRelationships({ area, model }) {
  const caps = area.capabilities || [];
  const on = caps.filter((c) => c.status === "REGISTERED");
  const problems = (model.problems?.items || []).filter(
    (p) => (p.capability_ids || []).some((id) => (area.capability_ids || []).includes(id)));
  const unresolved = area.unresolved_capability_ids || [];
  return (
    <>
      <h4>How much of this area is switched on</h4>
      {caps.length === 0 ? (
        <div className="muted">
          Nothing is attached to this area, so there is nothing to be on or off.
        </div>
      ) : (
        <div className="pm-plain">
          {on.length} of {caps.length}{" "}
          {caps.length === 1 ? "capability is" : "capabilities are"} plugged into the live
          application.
          {on.length < caps.length && (
            <> Still off: {caps.filter((c) => c.status !== "REGISTERED")
              .map((c) => c.label).join(", ")}.</>
          )}
        </div>
      )}

      <h4>Problems recorded against this area</h4>
      {problems.length === 0 ? (
        <div className="muted">No recorded finding names a capability in this area.</div>
      ) : (
        <ul className="sc-list">
          {problems.map((p) => (
            <li key={p.id || `${p.task}#${p.revision}`}>
              <strong>{p.id || `#${p.revision}`}</strong>{" "}
              <span className={`sc-badge ${PROBLEM_BADGE[p.display_status] || ""}`}>
                {p.display_status}
              </span>
              <PlainLine text={p.plain_english} recorded={p.plain_language_recorded} />
            </li>
          ))}
        </ul>
      )}

      {unresolved.length > 0 && (
        <>
          <h4>Named here but not resolved</h4>
          <MissingLink explanation={
            `This area claims ${unresolved.join(", ")}, which the capability view does `
            + "not resolve to anything."} />
        </>
      )}
    </>
  );
}

function SystemAnatomy({ model, mode }) {
  const anatomy = model.anatomy || {};
  const areas = anatomy.areas || [];
  const capabilities = model.capability_model?.capabilities || [];
  const [areaId, setAreaId] = useState(areas[0]?.id || null);
  const [capId, setCapId] = useState(null);

  const area = areas.find((a) => a.id === areaId) || null;
  const capability = capabilities.find((c) => c.id === capId) || null;

  return (
    <>
      <div className="sc-section-group">
        <h2>The working parts of CIS</h2>
        <section className="sc-section">
          <div className="pm-plain">
            These are the major areas, not every file. An area is only called switched on if
            something in it is actually plugged into the live application.
          </div>
          <div className="muted bp-fineprint">{anatomy.note}</div>
          <MermaidDiagram source={anatomy.mermaid} />
        </section>
      </div>

      <div className="sc-section-group">
        <h2>Capability view</h2>
        <section className="sc-section pm-cap-provenance">
          <h3>Read this first</h3>
          <div className="pm-plain">
            CIS does not record a list of capabilities anywhere. The grouping below is worked
            out by this screen, and every "switched on" or "switched off" beside it is an
            observation, not a claim someone wrote down.
          </div>
          <div className="muted bp-fineprint">
            {model.capability_model?.provenance?.statement}
          </div>
          {atLeast(mode, "technical") && (
            <ul className="sc-list">
              {(model.capability_model?.provenance?.candidates_inspected || []).map((c) => (
                <li key={c.candidate}>
                  <code>{c.candidate}</code> — <strong>{c.verdict}</strong>
                  <div className="muted bp-fineprint">{c.detail}</div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <div className="pm-split">
        <div className="pm-list-pane">
          <h4>Areas</h4>
          <ul className="pm-list">
            {areas.map((a) => (
              <li key={a.id}>
                <button className={`pm-list-item${areaId === a.id ? " active" : ""}`}
                        onClick={() => { setAreaId(a.id); setCapId(null); }}>
                  <span className="pm-list-id">{a.label}</span>{" "}
                  <span className={`sc-badge ${AREA_BADGE[a.status] || ""}`}>
                    {a.status.toLowerCase()}
                  </span>{" "}
                  <span className="pm-list-text">{a.plain_english}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="pm-detail-pane">
          {capability ? (
            <>
              <button className="link-btn" onClick={() => setCapId(null)}>
                ← back to {area?.label}
              </button>
              <CapabilityDetail capability={capability} model={model} mode={mode} />
            </>
          ) : area ? (
            <div className="pm-detail">
              <h3>
                {area.label}{" "}
                <span className={`sc-badge ${AREA_BADGE[area.status] || ""}`}>
                  {area.status.toLowerCase()}
                </span>
              </h3>
              <h4>What is this?</h4>
              <PlainLine text={area.plain_english} recorded />
              {area.what_it_does && (
                <>
                  <h4>What does it do?</h4>
                  <div className="pm-plain">{area.what_it_does}</div>
                </>
              )}
              {area.why_cis_needs_it && (
                <>
                  <h4>Why does CIS need it?</h4>
                  <div className="pm-plain">{area.why_cis_needs_it}</div>
                </>
              )}
              <h4>Is it on?</h4>
              <div className="pm-plain">{area.status_plain}</div>
              {atLeast(mode, "technical") && (
                <div className="muted bp-fineprint">{area.status_derivation}</div>
              )}

              <h4>Capabilities it covers</h4>
              {area.capabilities.length === 0 ? (
                <div className="muted">
                  Nothing is attached to this area yet — it is described here for orientation.
                </div>
              ) : (
                <ul className="sc-list">
                  {area.capabilities.map((c) => (
                    <li key={c.id}>
                      <button className="link-btn" onClick={() => setCapId(c.id)}>
                        {c.label} →
                      </button>{" "}
                      <span className={`sc-badge ${CAP_BADGE[c.status] || ""}`}>
                        {c.status.replace(/_/g, " ").toLowerCase()}
                      </span>
                      <PlainLine text={c.plain_english} recorded />
                    </li>
                  ))}
                </ul>
              )}

              {atLeast(mode, "detail") && (
                <AreaRelationships area={area} model={model} />
              )}

              {atLeast(mode, "technical") && area.files.length > 0 && (
                <>
                  <h4>Files that implement it</h4>
                  <ul className="sc-list">
                    {area.files.map((f) => <li key={f}><code>{f}</code></li>)}
                  </ul>
                </>
              )}
            </div>
          ) : (
            <div className="muted">Choose an area.</div>
          )}
        </div>
      </div>
    </>
  );
}

// ── Trajectory ──────────────────────────────────────────────────────────

function Trajectory({ model, mode }) {
  const trajectory = model.trajectory || {};
  const rel = trajectory.destination_relationship || {};
  const classes = model.confidence_classes;
  const steps = trajectory.steps || [];
  const capabilities = model.capability_model?.capabilities || [];
  const capsByPhase = {};
  for (const cap of capabilities) {
    for (const position of cap.build_position || []) {
      (capsByPhase[position.phase_id] ||= []).push(cap);
    }
  }

  return (
    <>
      <div className="sc-section-group">
        <h2>{trajectory.question}</h2>
        <section className="sc-section">
          <div className="pm-plain">
            The steps below are the order of work the project has actually recorded. The part
            after them is a different kind of relationship — it explains what the work is
            ultimately for, and it is not the next thing that happens.
          </div>
          <MermaidDiagram source={trajectory.mermaid} />
          <div className="muted bp-fineprint">{trajectory.separation_note}</div>
        </section>
      </div>

      <div className="sc-section-group">
        <h2>Today, in order</h2>
        {steps.length === 0 ? (
          <div className="muted">No build steps are recorded, so none are shown.</div>
        ) : (
          <ol className="pm-steps">
            {steps.map((step) => (
              <li key={step.id} className={`pm-step pm-step-${step.blocked ? "blocked" : step.status}`}>
                <div className="pm-step-head">
                  <strong>{step.label}</strong>{" "}
                  <span className="sc-badge">{step.status_label}</span>
                  {step.is_current && <span className="bp-here">you are here</span>}
                </div>
                <div className="pm-plain">{step.description}</div>
                {atLeast(mode, "detail") && (
                  <>
                    {/* The label appears only when there is something to put
                        after it. An empty "what this establishes:" followed by a
                        broken-chain notice reads like a rendering fault rather
                        than the honest absence it is. */}
                    {(capsByPhase[step.id] || []).length > 0 ? (
                      <div className="muted bp-fineprint">
                        What this step is meant to establish:{" "}
                        {capsByPhase[step.id].map((c) => c.label).join(", ")}
                      </div>
                    ) : (
                      <MissingLink explanation={
                        "The roadmap's description of this step does not name a capability, so "
                        + "none is attached to it here."} />
                    )}
                    {step.queue_hooks.length > 0 && (
                      <div className="muted bp-fineprint">
                        work items the roadmap names here:{" "}
                        {step.queue_hooks.map((h) => h.item_num).join(", ")}
                      </div>
                    )}
                  </>
                )}
                {atLeast(mode, "technical") && (
                  <div className="muted bp-fineprint">
                    <code>{step.id}</code> · order {step.order} · source {step.source}
                  </div>
                )}
              </li>
            ))}
          </ol>
        )}
        {atLeast(mode, "technical") && (
          <div className="muted bp-fineprint">{trajectory.build_sequence_authority}</div>
        )}
      </div>

      <div className="sc-section-group">
        <h2>And then?</h2>
        <section className="sc-section pm-destination-rel">
          <div className="pm-destination-warning">{rel.warning}</div>
          <div className="pm-plain">{rel.explanation}</div>
          {rel.confidence_class === "not_yet_linked" ? (
            <MissingLink explanation={rel.explanation} />
          ) : (
            <ul className="sc-list">
              {(rel.nodes || []).map((node) => (
                <li key={node.node_id}>
                  <strong>{node.label}</strong>{" "}
                  <span className="sc-badge da-badge-destination">
                    {(node.activation_state || "unknown").replace(/_/g, " ").toLowerCase()}
                  </span>{" "}
                  <ConfidenceBadge cls={node.confidence_class} classes={classes} />
                  <div className="muted bp-fineprint">{node.explanation}</div>
                  <AuthorityRefs refs={node.authority_refs} mode={mode} />
                </li>
              ))}
            </ul>
          )}
          {atLeast(mode, "technical") && (
            <div className="muted bp-fineprint">
              is_phase_ordering: <code>{String(rel.is_phase_ordering)}</code>
            </div>
          )}
        </section>
      </div>
    </>
  );
}

// ── Current Build and Destination areas (reused views) ──────────────────

function CurrentBuildArea({ model, mode, onOpenBuildPath }) {
  const area = model.current_build || {};
  if (!area.available) {
    return (
      <div className="sc-section-group">
        <div className="banner-error">
          The current-build view is unavailable: {area.error || "the read model did not load."}
        </div>
        <div className="muted">
          The rest of this map still loaded. Nothing is filled in from assumption here.
        </div>
      </div>
    );
  }
  return (
    <>
      <div className="sc-section-group">
        <section className="sc-section">
          <div className="pm-plain">
            This is the existing Build Path view, shown here with the same panels and the same
            data — not a second copy of it.
          </div>
          <button className="link-btn" onClick={onOpenBuildPath}>
            Open the full Build Path screen →
          </button>
          {!atLeast(mode, "technical") && (
            <div className="muted bp-fineprint">
              The full Build Path screen always shows every panel. Here the level of detail
              above decides how much of the same data is shown.
            </div>
          )}
        </section>
      </div>
      {/* Same component, same payload — the mode only selects how much of it
          is disclosed. See CurrentBuildPanel in BuildPath.jsx. */}
      <CurrentBuildPanel model={area.build_path} mode={mode} />
    </>
  );
}

function DestinationArea({ model, mode }) {
  const area = model.destination || {};
  return (
    <>
      <div className="sc-section-group">
        <section className="sc-section">
          <div className="pm-plain">
            This is the existing Destination Architecture view. None of it is work in progress:
            it records what CIS is ultimately being built to support.
          </div>
          {area.activation_note && (
            <div className="muted bp-fineprint">{area.activation_note}</div>
          )}
          {atLeast(mode, "technical") && (
            <div className="muted bp-fineprint">
              referenced, not duplicated — {area.note}. Served by{" "}
              <code>{area.endpoint}</code>
            </div>
          )}
        </section>
      </div>
      {/* The destination view fetches and owns its own authority; the mode only
          selects how much of that one response it discloses. */}
      <DestinationArchitecture mode={mode} />
    </>
  );
}

// ── the screen ──────────────────────────────────────────────────────────

export default function ProjectMap({ onBack, onOpenBuildPath }) {
  const [model, setModel] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lastLoadedAt, setLastLoadedAt] = useState(null);
  const [area, setArea] = useState("overview");
  const [mode, setMode] = useState("simple");

  async function load() {
    setLoading(true);
    const result = await getProjectIntelligence();
    setLoading(false);
    if (!result.ok) {
      setError(result.error);
      // A prior successful load stays visible, marked stale, rather than being
      // replaced by nothing. A FAILED load never becomes a map.
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
  const areas = useMemo(() => {
    const declared = model?.areas || [];
    const byId = Object.fromEntries(declared.map((a) => [a.id, a]));
    return AREA_ORDER.filter((id) => byId[id]).map((id) => byId[id]);
  }, [model]);
  const modes = model?.modes || [];
  const selectedMode = modes.find((m) => m.id === mode) || null;

  return (
    <div className="workbench">
      <header className="stage-banner">
        <button className="link-btn" onClick={onBack}>← Back to conversation</button>
        <span className="stage-label">Project Map</span>
        <span className="stage-detail">
          Read-only. It explains how problems, work, capabilities, code, the build order and the
          destination relate — and says plainly where nothing has been recorded.
        </span>
        {/* The control, and immediately under it a sentence saying what the
            chosen level means. Eric found PM-D3 on a phone, where the content a
            mode reveals can be a long scroll away: without this line, tapping a
            button looked like it had done nothing. The wording is the read
            model's own modes[].plain_english, not this component's, so the
            explanation cannot drift from what the mode actually shows — and
            because it is a live region the change is ANNOUNCED, not only
            coloured, which is the same reason aria-pressed is on each button. */}
        <div className="pm-modes-group" style={{ marginLeft: "auto" }}>
          <div className="pm-modes" role="group" aria-label="Level of detail">
            {modes.map((m) => (
              <button key={m.id} className={`pm-mode${mode === m.id ? " active" : ""}`}
                      aria-pressed={mode === m.id}
                      title={m.plain_english}
                      onClick={() => setMode(m.id)}>
                {m.label}
              </button>
            ))}
          </div>
          {selectedMode && (
            <div className="pm-mode-note" role="status" aria-live="polite"
                 data-testid="pm-mode-note">
              <strong>{selectedMode.label}</strong>
              {" — "}
              {selectedMode.plain_english}
            </div>
          )}
        </div>
        <button className="link-btn" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </header>

      {areas.length > 0 && (
        <div className="bp-tabs" role="tablist" aria-label="Project Map views">
          {areas.map((a) => (
            <button key={a.id} role="tab" aria-selected={area === a.id}
                    className={`bp-tab${area === a.id ? " active" : ""}`}
                    onClick={() => setArea(a.id)}>
              {a.label}
            </button>
          ))}
        </div>
      )}

      <div className="sc-body bp-body pm-body">
        {error && (
          <div className="banner-error">
            Could not load the project map: {error}
            {stale && " — showing the last successfully loaded view below."}
          </div>
        )}
        {stale && (
          <div className="sc-stale-notice">
            STALE — last successfully loaded {fmtTime(lastLoadedAt)}. This may no longer reflect
            the project's current state.
          </div>
        )}

        {!model && !error && loading && <div className="muted">Loading the project map…</div>}
        {!model && error && (
          <div className="muted">
            No project map has loaded in this session, so none is shown. Nothing on this screen
            is filled in from memory or assumption.
          </div>
        )}

        {model && (
          <>
            {area !== "overview" && (
              <div className="pm-area-header">
                <h1>{areas.find((a) => a.id === area)?.label}</h1>
                <div className="pm-area-question">
                  {areas.find((a) => a.id === area)?.plain_question}
                </div>
              </div>
            )}

            {area === "overview" && <Overview model={model} mode={mode} onGo={setArea} />}
            {area === "current_build" && (
              <CurrentBuildArea model={model} mode={mode}
                                onOpenBuildPath={onOpenBuildPath} />
            )}
            {area === "queue_problems" && <QueueProblems model={model} mode={mode} />}
            {area === "system_anatomy" && <SystemAnatomy model={model} mode={mode} />}
            {area === "destination" && <DestinationArea model={model} mode={mode} />}
            {area === "trajectory" && <Trajectory model={model} mode={mode} />}

            <div className="muted bp-fineprint pm-footer">
              state revision <code>{model.state_revision}</code>, generated{" "}
              {fmtTime(model.generated_at)} · {model.counts?.relationships} recorded
              relationships, {model.counts?.not_yet_linked} of them not yet linked ·
              plain-language wording from{" "}
              <code>{model.vocabulary_source?.path}</code> (
              {model.vocabulary_source?.provenance_class}), never generated while this page
              loads
            </div>
          </>
        )}
      </div>
    </div>
  );
}
