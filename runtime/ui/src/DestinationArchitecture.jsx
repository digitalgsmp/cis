import { useEffect, useState } from "react";
import { getDestinationArchitecture } from "./api";
import MermaidDiagram from "./MermaidDiagram";

// The "Destination Architecture" tab of the Build Path screen, over GET
// /api/workbench/destination-architecture (runtime/api/destination_architecture.py
// -> tools/state/destination_architecture.py).
//
// This answers a DIFFERENT question than the Current Build tab beside it: not
// "what are we building now" (the P0–P6 sequence, from the roadmap authority)
// but "what is CIS ultimately being built to support". Nothing here is a phase,
// nothing here has build progress, and this file holds no architecture of its
// own: every node, edge, relationship meaning, activation state and diagram
// comes from the response. There is no hardcoded WIASW hierarchy in this
// component — if the ADR-WIASW-* decisions change, this screen changes with
// them, and if they are absent it says so instead of drawing something.
//
// Read-only: the one api.js function imported is a parameterless GET.

function fmtTime(iso) {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

/** Activation is NOT build progress. The badge wording comes from the model's
 *  own state token, and the scope word sits next to it so a reader cannot mistake
 *  a destination node for work in flight. */
function ActivationBadge({ state }) {
  if (!state) {
    return <span className="sc-badge sc-badge-error">activation unknown</span>;
  }
  const cls = state === "NOT_ACTIVATED" ? "da-badge-destination" : "";
  return <span className={`sc-badge ${cls}`}>{state.replace(/_/g, " ").toLowerCase()}</span>;
}

function NodeCard({ node, edgesFrom, edgesTo }) {
  return (
    <section className={`sc-section da-node da-node-${node.activation_state || "unknown"}`}>
      <h4>
        {node.label} <ActivationBadge state={node.activation_state} />
      </h4>
      <div className="muted bp-fineprint">
        {node.kind.replace(/_/g, " ")} · depth {node.depth} · <code>{node.id}</code>
      </div>
      <div className="bp-phase-desc">{node.description}</div>

      {(edgesFrom.length > 0 || edgesTo.length > 0) && (
        <ul className="sc-list da-edge-list">
          {edgesFrom.map((e) => (
            <li key={`out-${e.relationship}-${e.target}`}>
              <span className="da-rel">{e.relationship}</span> → {e.target}
            </li>
          ))}
          {edgesTo.map((e) => (
            <li key={`in-${e.relationship}-${e.source}`}>
              {e.source} <span className="da-rel">{e.relationship}</span> → this
            </li>
          ))}
        </ul>
      )}
      {node.authority_ref && (
        <div className="muted bp-fineprint da-provenance">
          declared by {node.authority_ref.decision_id} ({node.authority_ref.clause})
        </div>
      )}
    </section>
  );
}

function KindGroup({ kind, nodes, edges }) {
  return (
    <div className="sc-section-group">
      <h3 className="da-kind-heading">{kind.replace(/_/g, " ")}</h3>
      <div className="bp-phase-grid">
        {nodes.map((n) => (
          <NodeCard key={n.id} node={n}
                    edgesFrom={edges.filter((e) => e.source === n.id)}
                    edgesTo={edges.filter((e) => e.target === n.id)} />
        ))}
      </div>
    </div>
  );
}

function Relationships({ model }) {
  const relationships = model.relationships || [];
  const used = model.relationship_types_used || [];
  return (
    <section className="sc-section">
      <h3>What the relationships mean</h3>
      {relationships.length === 0 ? (
        <div className="muted">
          The authority declared no relationship vocabulary, so none is shown.
        </div>
      ) : (
        <ul className="sc-list">
          {relationships.map((r) => (
            <li key={r.name}>
              <span className="da-rel">{r.name}</span> — {r.definition}
              {!used.includes(r.name) && (
                <span className="muted"> (defined, not used by any edge)</span>
              )}
              <div className="muted bp-fineprint da-provenance">
                from {r.authority_ref?.decision_id}
              </div>
            </li>
          ))}
        </ul>
      )}
      <div className="muted bp-fineprint">
        {model.authority?.relationship_separation}
      </div>
    </section>
  );
}

function ActivationPanel({ model }) {
  const activation = model.activation || {};
  return (
    <section className="sc-section da-activation">
      <h3>
        Activation{" "}
        <span className="sc-badge da-badge-destination">
          architecture scope: {model.architecture_scope || "unstated"}
        </span>
      </h3>
      <div>
        Default for every node: <ActivationBadge state={activation.default} />
      </div>
      <ul className="sc-list">
        {(activation.vocabulary || []).map((v) => (
          <li key={v.state}>
            <strong>{v.state}</strong> — {v.definition}
            <div className="muted bp-fineprint da-provenance">
              from {v.authority_ref?.decision_id}
            </div>
          </li>
        ))}
      </ul>
      <div className="muted bp-fineprint">{activation.note}</div>
    </section>
  );
}

function AuthorityPanel({ model }) {
  const authority = model.authority || {};
  const [open, setOpen] = useState(false);
  const decisions = model.decisions || [];
  return (
    <section className="sc-section bp-authority">
      <h3>What is authoritative here</h3>
      <ul className="sc-list">
        <li><strong>Semantic authority:</strong> {authority.semantic_authority}</li>
        <li><strong>Structured graph:</strong> {authority.structured_projection}</li>
        <li><strong>Provenance:</strong> {authority.provenance}</li>
        {authority.not_stored_in?.length > 0 && (
          <li>
            <strong>Not stored in:</strong> {authority.not_stored_in.join(", ")}
          </li>
        )}
        <li className="muted">{authority.current_build_view}</li>
      </ul>
      <button className="context-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide" : "Show"} the decisions this architecture is read from
      </button>
      {open && (
        <div className="context-body">
          {decisions.length === 0 ? (
            <div className="muted">No decision rows were found to quote.</div>
          ) : (
            decisions.map((d) => (
              <div key={d.id} className="da-decision">
                <h4>
                  {d.id} — {d.label}{" "}
                  <span className="sc-badge sc-badge-ok">{d.status}</span>
                </h4>
                <div className="muted bp-fineprint">
                  decided {fmtTime(d.decided_at)} · clauses contributed:{" "}
                  {d.clauses_contributed?.length > 0
                    ? d.clauses_contributed.join(", ")
                    : "none (prose only)"}
                </div>
                <div className="bp-longtext">{d.decision}</div>
                {d.reason && (
                  <div className="bp-longtext muted">Reason: {d.reason}</div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </section>
  );
}

export default function DestinationArchitecture() {
  const [model, setModel] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [lastLoadedAt, setLastLoadedAt] = useState(null);
  const [levelId, setLevelId] = useState(null);

  async function load() {
    setLoading(true);
    const result = await getDestinationArchitecture();
    setLoading(false);
    if (!result.ok) {
      setError(result.error);
      // A prior successful load stays visible, marked stale, rather than being
      // replaced by nothing. A FAILED load never becomes a diagram.
      return;
    }
    setError("");
    setModel(result.data);
    setLastLoadedAt(new Date().toISOString());
  }

  useEffect(() => {
    load();
  }, []);

  const levels = model?.levels || [];
  const level = levels.find((lv) => lv.id === levelId) || levels[0] || null;
  const stale = Boolean(error && model);

  // Nodes grouped by the KINDS the authority used, in the order it used them —
  // no kind list is hardcoded here.
  const shownIds = level ? new Set(level.node_ids) : null;
  const groups = (model?.node_kinds || []).map((kind) => ({
    kind,
    nodes: (model?.nodes || []).filter((n) => n.kind === kind),
  })).filter((g) => g.nodes.length > 0);

  return (
    <div className="da-body">
      <div className="sc-stale-notice da-scope-banner" data-testid="da-scope-banner">
        DESTINATION ARCHITECTURE — NOT CURRENTLY ACTIVATED IMPLEMENTATION WORK.
        This is what CIS is ultimately being built to support. It is not the current
        build sequence, nothing here is a phase, and no progress is shown or implied.
        Activating any of it requires explicit human authorization.
      </div>

      <div className="da-toolbar">
        <button className="link-btn" onClick={load} disabled={loading}>
          {loading ? "Loading…" : "Refresh destination architecture"}
        </button>
      </div>

      {error && (
        <div className="banner-error">
          Could not load the destination architecture: {error}
          {stale && " — showing the last successfully loaded view below."}
        </div>
      )}
      {stale && (
        <div className="sc-stale-notice">
          STALE — last successfully loaded {fmtTime(lastLoadedAt)}.
        </div>
      )}

      {!model && !error && loading && (
        <div className="muted">Loading the destination architecture…</div>
      )}
      {!model && error && (
        <div className="muted">
          No destination architecture has loaded in this session, so none is shown.
          Nothing on this screen is filled in from memory or assumption.
        </div>
      )}

      {model && model.present === false && (
        <section className="sc-section">
          <h3>No destination architecture is recorded</h3>
          <div className="muted">{model.note}</div>
        </section>
      )}

      {model && model.present && (
        <>
          <div className="sc-section-group">
            <h2>The architecture</h2>
            <section className="sc-section">
              <div className="da-level-tabs" role="group" aria-label="Zoom level">
                {levels.map((lv) => (
                  <button key={lv.id}
                          className={`da-level-tab${lv.id === level?.id ? " active" : ""}`}
                          onClick={() => setLevelId(lv.id)}>
                    {lv.label}
                  </button>
                ))}
              </div>
              {level && (
                <>
                  <div className="muted da-level-question">{level.question}</div>
                  <MermaidDiagram source={level.mermaid} testIdPrefix="da"
                                  emptyNote="The read model carried no diagram source for this level." />
                </>
              )}
              <div className="sc-counts">
                <span className="sc-count-pill">{model.counts?.nodes} nodes</span>
                <span className="sc-count-pill">{model.counts?.edges} edges</span>
                <span className="sc-count-pill">
                  {model.counts?.relationship_types} relationship types
                </span>
                {level && (
                  <span className="sc-count-pill">
                    {level.node_count} shown at this level
                  </span>
                )}
              </div>
            </section>
          </div>

          {model.problems?.length > 0 && (
            <div className="sc-section-group">
              <h2>Problems in the recorded architecture</h2>
              <section className="sc-section">
                <ul className="sc-list" data-testid="da-problems">
                  {model.problems.map((p, i) => (
                    <li key={`${p.kind}-${i}`}>
                      <strong>{p.kind}</strong>
                      <div className="muted bp-fineprint">{p.detail}</div>
                    </li>
                  ))}
                </ul>
              </section>
            </div>
          )}

          <div className="sc-section-group">
            <h2>Semantics and activation</h2>
            <ActivationPanel model={model} />
            <Relationships model={model} />
          </div>

          <h2>Every recorded element</h2>
          {shownIds && level?.max_depth !== null && (
            <div className="muted bp-fineprint">
              The diagram above shows {level.node_count} of {model.counts?.nodes} nodes at
              this zoom level. Every node is listed below regardless of level.
            </div>
          )}
          {groups.map((g) => (
            <KindGroup key={g.kind} kind={g.kind} nodes={g.nodes}
                       edges={model.edges || []} />
          ))}

          <div className="sc-section-group">
            <h2>Authority</h2>
            <AuthorityPanel model={model} />
            <div className="muted bp-fineprint">
              state revision <code>{model.state_revision}</code>, generated{" "}
              {fmtTime(model.generated_at)}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
