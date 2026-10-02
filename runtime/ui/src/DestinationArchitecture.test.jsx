import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DestinationArchitecture from "./DestinationArchitecture";

// In-memory fake of runtime/api/destination_architecture.py's single GET route.
// The mock exposes ONLY getDestinationArchitecture: if this component ever
// reached for a mutating api.js function — or for getBuildPath, which belongs
// to the other tab's authority — it would be undefined here. That is the guard
// that this view stays read-only AND stays out of the build path's model.
const state = { handler: null, mermaidThrows: false, renderCalls: [] };

vi.mock("./api", () => ({
  getDestinationArchitecture: (...args) => state.handler(...args),
}));

// Mermaid does real layout measurement, which jsdom has no engine for. Stubbed
// so these tests assert what THIS component does with Mermaid's answer. That
// the real generated source actually parses is proven separately, against the
// real library and the real generator, in DestinationArchitectureMermaid.test.jsx.
vi.mock("mermaid", () => ({
  default: {
    initialize: vi.fn(),
    render: vi.fn(async (id, source) => {
      state.renderCalls.push({ id, source });
      if (state.mermaidThrows) throw new Error("no layout engine here");
      return { svg: `<svg data-source-lines="${source.split("\n").length}"></svg>` };
    }),
  },
}));

function ok(data) {
  return { ok: true, data };
}

function fail(error) {
  return { ok: false, error };
}

function ref(decisionId, clause, declaration) {
  return { decision_id: decisionId, clause, declaration };
}

function node(id, kind, label, depth, activation, description) {
  return {
    id, kind, label, depth, description,
    activation_state: activation,
    authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH NODES",
                       `${id} [${kind}] "${label}" = ${description}`),
    activation_authority_ref: ref("ADR-WIASW-001", "ACTIVATION",
                                  `default ${activation}`),
  };
}

function edge(source, relationship, target) {
  return {
    source, relationship, target,
    source_declared: true, target_declared: true, relationship_defined: true,
    authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH EDGES",
                       `${source} ${relationship} ${target}`),
  };
}

// Shaped exactly like tools/state/destination_architecture.py's output for the
// architecture the spine actually carries today (see
// runtime/tests/test_destination_architecture_api.py, which asserts that shape
// against the live spine). Trimmed to the elements these tests need.
function fullModel(overrides = {}) {
  const nodes = [
    node("WIASW", "root", "WIASW — Word · Image · Action · Sound + Web", 0,
         "NOT_ACTIVATED", "the overarching destination/product architecture"),
    node("DOMAINS", "domain_group", "Media domains", 1, "NOT_ACTIVATED",
         "the five named WIASW media domains"),
    node("WORD", "domain", "Word", 2, "NOT_ACTIVATED", "ideas, research, scripts"),
    node("IMAGE", "domain", "Image", 2, "NOT_ACTIVATED", "concept art, illustration"),
    node("ACTION", "domain", "Action", 2, "NOT_ACTIVATED",
         "temporal, performed, simulated and moving visual production"),
    node("SOUND", "domain", "Sound", 2, "NOT_ACTIVATED", "music, sound design, mixing"),
    node("WEB", "domain", "Web", 2, "NOT_ACTIVATED",
         "web applications, social media, publishing, distribution, online sales"),
    node("HORIZONTAL_APPLICATIONS", "application_group", "Horizontal applications", 1,
         "NOT_ACTIVATED", "productivity applications that are NOT additional media domains"),
    node("IDEA_MANAGEMENT", "application", "Idea management", 2, "NOT_ACTIVATED",
         "capture and development of ideas"),
    node("CIS", "substrate", "CIS — deterministic AI / control substrate", 0,
         "TRACKED_ELSEWHERE", "the generalized deterministic control substrate"),
    node("EXECUTION_LAYER", "execution_group", "Execution / tool backends", 0,
         "TRACKED_ELSEWHERE", "the replaceable execution infrastructure"),
    node("CREATIVE_TOOL_BACKENDS", "execution_family", "Creative applications", 1,
         "NOT_ACTIVATED", "Blender, Houdini, ComfyUI, Unreal Engine, DAWs"),
  ];
  const edges = [
    edge("WIASW", "contains", "DOMAINS"),
    edge("WIASW", "contains", "HORIZONTAL_APPLICATIONS"),
    edge("DOMAINS", "contains", "WORD"),
    edge("DOMAINS", "contains", "IMAGE"),
    edge("DOMAINS", "contains", "ACTION"),
    edge("DOMAINS", "contains", "SOUND"),
    edge("DOMAINS", "contains", "WEB"),
    edge("HORIZONTAL_APPLICATIONS", "contains", "IDEA_MANAGEMENT"),
    edge("HORIZONTAL_APPLICATIONS", "supports", "DOMAINS"),
    edge("WIASW", "uses", "CIS"),
    edge("CIS", "controls", "EXECUTION_LAYER"),
    edge("EXECUTION_LAYER", "contains", "CREATIVE_TOOL_BACKENDS"),
    edge("CIS", "orchestrates", "CREATIVE_TOOL_BACKENDS"),
    edge("CIS", "executes-through", "CREATIVE_TOOL_BACKENDS"),
  ];
  return {
    read_model: "cis_destination_architecture",
    generated_at: "2026-10-02T04:30:00Z",
    state_revision: "deadbeefcafe0001",
    present: true,
    architecture_scope: "destination",
    architecture_scope_authority_ref: ref("ADR-WIASW-001", "ARCHITECTURE SCOPE",
                                          "destination."),
    authority: {
      semantic_authority: "project_decisions rows with id LIKE 'ADR-WIASW-%'",
      structured_projection: "parsed from those decision rows at read time — no second store",
      provenance: "every node and edge carries an authority_ref",
      not_stored_in: ["project_state.pipeline_roadmap", "queue_items", "queue_edges",
                      "build_plan_nodes", "build_plan_dependencies"],
      current_build_view: "'what are we building now' is a different question read by build_path.py",
      relationship_separation: "destination relationships are ARCHITECTURAL, build-order edges belong to the roadmap",
    },
    activation: {
      default: "NOT_ACTIVATED",
      default_authority_ref: ref("ADR-WIASW-001", "ACTIVATION", "default NOT_ACTIVATED"),
      exceptions: { CIS: { state: "TRACKED_ELSEWHERE" } },
      vocabulary: [
        { state: "NOT_ACTIVATED",
          definition: "recorded destination architecture carrying no activated implementation work",
          authority_ref: ref("ADR-WIASW-001", "ACTIVATION VOCABULARY", "NOT_ACTIVATED = …") },
        { state: "TRACKED_ELSEWHERE",
          definition: "this node is real today and its status is owned by a different authority",
          authority_ref: ref("ADR-WIASW-001", "ACTIVATION VOCABULARY", "TRACKED_ELSEWHERE = …") },
      ],
      note: "activation_state is NOT a build status and NOT ADR-PIPE-005's component-state vocabulary",
    },
    relationships: [
      { name: "contains", definition: "structural membership",
        authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH RELATIONSHIPS", "contains = …") },
      { name: "uses", definition: "the source is built on top of the target",
        authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH RELATIONSHIPS", "uses = …") },
      { name: "supports", definition: "the source assists the target without owning it",
        authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH RELATIONSHIPS", "supports = …") },
      { name: "controls", definition: "the source owns the authoritative control boundary",
        authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH RELATIONSHIPS", "controls = …") },
      { name: "orchestrates", definition: "the source coordinates multiple independent targets",
        authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH RELATIONSHIPS", "orchestrates = …") },
      { name: "executes-through", definition: "the source drives the target through a stable adapter contract",
        authority_ref: ref("ADR-WIASW-001", "DESTINATION GRAPH RELATIONSHIPS", "executes-through = …") },
    ],
    relationship_types_used: ["contains", "controls", "executes-through", "orchestrates",
                              "supports", "uses"],
    node_kinds: ["root", "domain_group", "domain", "application_group", "application",
                 "substrate", "execution_group", "execution_family"],
    nodes,
    edges,
    levels: [
      {
        id: "overview", label: "Level 1 — why",
        question: "What is CIS ultimately being built to support?",
        max_depth: 0,
        node_ids: ["WIASW", "CIS", "EXECUTION_LAYER"], node_count: 3,
        mermaid: "flowchart TD\n  WIASW[\"WIASW\"]\n  WIASW -->|uses| CIS",
      },
      {
        id: "full", label: "Level 2 — what WIASW is",
        question: "What are the WIASW domains, applications and backends?",
        max_depth: null,
        node_ids: nodes.map((n) => n.id), node_count: nodes.length,
        mermaid: "flowchart TD\n  WIASW[\"WIASW\"]\n  DOMAINS[\"Media domains\"]\n  WIASW -->|contains| DOMAINS",
      },
    ],
    mermaid: "flowchart TD\n  WIASW[\"WIASW\"]",
    decisions: [
      { id: "ADR-WIASW-001", label: "WIASW destination architecture — Word, Image, Action, Sound, Web",
        status: "DECIDED", decided_at: "2026-10-02T04:21:48Z", superseded_by: null,
        clauses_contributed: ["ACTIVATION", "ARCHITECTURE SCOPE", "DESTINATION GRAPH EDGES",
                              "DESTINATION GRAPH NODES"],
        decision: "WIASW = Word · Image · Action · Sound + Web. …", reason: "why it was recorded" },
      { id: "ADR-WIASW-003", label: "Deterministic validation and perceptual review are different evidence",
        status: "DECIDED", decided_at: "2026-10-02T04:21:48Z", superseded_by: null,
        clauses_contributed: ["ARCHITECTURE SCOPE"],
        decision: "Human creative authority remains above model recommendations. …",
        reason: "why it was recorded" },
    ],
    counts: { decisions: 3, nodes: nodes.length, edges: edges.length,
              relationship_types: 6, problems: 0 },
    problems: [],
    ...overrides,
  };
}

beforeEach(() => {
  cleanup();
  state.mermaidThrows = false;
  state.renderCalls = [];
  state.handler = vi.fn(async () => ok(fullModel()));
});

describe("DestinationArchitecture (read-only destination view)", () => {
  it("says outright that this is destination architecture and not activated work", async () => {
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByTestId("da-scope-banner")).toBeInTheDocument());
    const banner = screen.getByTestId("da-scope-banner").textContent;
    expect(banner).toMatch(/DESTINATION ARCHITECTURE/);
    expect(banner).toMatch(/NOT CURRENTLY ACTIVATED IMPLEMENTATION WORK/);
    expect(banner).toMatch(/requires explicit human authorization/);
    expect(screen.getByText(/architecture scope: destination/)).toBeInTheDocument();
  });

  it("shows WIASW, all five domains, the horizontal applications, CIS and the execution layer", async () => {
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText(/WIASW — Word · Image · Action · Sound \+ Web/))
        .toBeInTheDocument());
    for (const domain of ["Word", "Image", "Action", "Sound", "Web"]) {
      expect(screen.getByRole("heading", { name: new RegExp(`^${domain}\\b`) }))
        .toBeInTheDocument();
    }
    expect(screen.getByRole("heading", { name: /Horizontal applications/ }))
      .toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Idea management/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /CIS — deterministic AI \/ control substrate/ }))
      .toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Execution \/ tool backends/ }))
      .toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Creative applications/ })).toBeInTheDocument();
  });

  it("states that horizontal applications are not additional media domains", async () => {
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText(/NOT additional media domains/)).toBeInTheDocument());
  });

  it("renders every relationship type with the meaning the authority gave it", async () => {
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText("What the relationships mean")).toBeInTheDocument());
    for (const rel of ["contains", "uses", "supports", "controls", "orchestrates",
                       "executes-through"]) {
      expect(screen.getAllByText(rel).length).toBeGreaterThan(0);
    }
    expect(screen.getByText(/the source owns the authoritative control boundary/))
      .toBeInTheDocument();
    expect(screen.getByText(/build-order edges belong to the roadmap/)).toBeInTheDocument();
  });

  it("distinguishes a destination node from one whose status lives elsewhere", async () => {
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /^Word\b/ })).toBeInTheDocument());
    const word = screen.getByRole("heading", { name: /^Word\b/ }).closest("section");
    expect(word.className).toContain("da-node-NOT_ACTIVATED");
    expect(word.textContent).toContain("not activated");

    const cis = screen.getByRole("heading", { name: /CIS — deterministic/ })
      .closest("section");
    expect(cis.className).toContain("da-node-TRACKED_ELSEWHERE");
    expect(cis.textContent).toContain("tracked elsewhere");
    // And the vocabulary that gives those tokens meaning is on screen, from the
    // authority, rather than being something the reader has to infer.
    expect(screen.getByText(/status is owned by a different authority/))
      .toBeInTheDocument();
    expect(screen.getByText(/NOT ADR-PIPE-005's component-state vocabulary/))
      .toBeInTheDocument();
  });

  it("renders the Mermaid diagram from the server's source, per zoom level", async () => {
    const user = userEvent.setup();
    render(<DestinationArchitecture />);
    await waitFor(() => expect(screen.getByTestId("da-diagram")).toBeInTheDocument());
    // Level 1 is the default, and its source is the server's, unmodified.
    expect(state.renderCalls).toHaveLength(1);
    expect(state.renderCalls[0].source).toBe(fullModel().levels[0].mermaid);
    expect(screen.getByText(/What is CIS ultimately being built to support\?/))
      .toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Level 2 — what WIASW is/ }));
    await waitFor(() => expect(state.renderCalls).toHaveLength(2));
    expect(state.renderCalls[1].source).toBe(fullModel().levels[1].mermaid);
    // Still the server's source: this component never composes a diagram.
    expect(state.renderCalls.every((c) => c.source.startsWith("flowchart TD"))).toBe(true);
  });

  it("falls back to the Mermaid source, and says why, when the diagram cannot be drawn", async () => {
    state.mermaidThrows = true;
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText(/Could not draw the diagram/)).toBeInTheDocument());
    expect(screen.getByTestId("da-mermaid-source").textContent).toContain("flowchart TD");
    // A failed drawing is not a failed load: the elements are still listed.
    expect(screen.getByRole("heading", { name: /^Word\b/ })).toBeInTheDocument();
  });

  it("shows the provenance of the architecture, not a paraphrase of it", async () => {
    const user = userEvent.setup();
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText("What is authoritative here")).toBeInTheDocument());
    expect(screen.getByText(/project_decisions rows with id LIKE 'ADR-WIASW-%'/))
      .toBeInTheDocument();
    expect(screen.getByText(/no second store/)).toBeInTheDocument();
    expect(screen.getByText(/project_state.pipeline_roadmap, queue_items, queue_edges/))
      .toBeInTheDocument();
    expect(screen.getByText(/different question read by build_path.py/)).toBeInTheDocument();
    expect(screen.getAllByText(/declared by ADR-WIASW-001/).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: /Show the decisions/ }));
    expect(screen.getByText(/ADR-WIASW-001 — WIASW destination architecture/))
      .toBeInTheDocument();
    expect(screen.getByText(/WIASW = Word · Image · Action · Sound \+ Web/))
      .toBeInTheDocument();
    expect(screen.getByText(/Human creative authority remains above model recommendations/))
      .toBeInTheDocument();
  });

  it("surfaces problems in the recorded architecture instead of hiding them", async () => {
    state.handler = vi.fn(async () => ok(fullModel({
      problems: [{
        kind: "edge_names_undeclared_node",
        detail: "edge 'WIASW uses CIS' names CIS, which no DESTINATION GRAPH NODES clause declares",
      }],
      counts: { ...fullModel().counts, problems: 1 },
    })));
    render(<DestinationArchitecture />);
    await waitFor(() => expect(screen.getByTestId("da-problems")).toBeInTheDocument());
    expect(screen.getByText("edge_names_undeclared_node")).toBeInTheDocument();
    expect(screen.getByText(/which no DESTINATION GRAPH NODES clause declares/))
      .toBeInTheDocument();
  });

  it("says nothing is recorded, and draws nothing, when the authority carries no architecture", async () => {
    state.handler = vi.fn(async () => ok({
      read_model: "cis_destination_architecture",
      generated_at: "2026-10-02T04:30:00Z",
      state_revision: "deadbeefcafe0001",
      present: false,
      note: "no project_decisions row matches id LIKE 'ADR-WIASW-%' with status != 'SUPERSEDED'",
      decisions: [], nodes: [], edges: [], levels: [], problems: [], mermaid: null,
    }));
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText("No destination architecture is recorded")).toBeInTheDocument());
    expect(screen.getByText(/no project_decisions row matches/)).toBeInTheDocument();
    expect(screen.queryByTestId("da-diagram")).not.toBeInTheDocument();
    expect(state.renderCalls).toHaveLength(0);
  });

  it("shows a load error and no fabricated architecture when the read model fails", async () => {
    state.handler = vi.fn(async () =>
      fail("destination architecture read model unavailable: OperationalError"));
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByText(/Could not load the destination architecture/))
        .toBeInTheDocument());
    expect(screen.getByText(/OperationalError/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /^Word\b/ })).not.toBeInTheDocument();
    expect(screen.queryByTestId("da-diagram")).not.toBeInTheDocument();
    expect(screen.getByText(/No destination architecture has loaded in this session/))
      .toBeInTheDocument();
  });

  it("keeps the last good view, marked stale, when a refresh fails", async () => {
    const user = userEvent.setup();
    render(<DestinationArchitecture />);
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: /^Word\b/ })).toBeInTheDocument());

    state.handler = vi.fn(async () => fail("gateway timeout"));
    await user.click(screen.getByRole("button", { name: /Refresh destination architecture/ }));

    await waitFor(() => expect(screen.getByText(/STALE/)).toBeInTheDocument());
    expect(screen.getByRole("heading", { name: /^Word\b/ })).toBeInTheDocument();
  });
});

// PM-D3. This component is the ONE destination-architecture renderer, reused by
// the Project Map, and it now takes that screen's presentation mode. The
// standalone tab passes none and therefore gets full disclosure; the Project
// Map passes Simple / More Detail / Technical. Same response, same authority,
// different disclosure — assert what each level SHOWS, not how long it is.
describe("DestinationArchitecture — presentation mode (PM-D3)", () => {
  async function show(mode) {
    const utils = mode === undefined
      ? render(<DestinationArchitecture />)
      : render(<DestinationArchitecture mode={mode} />);
    await waitFor(() => expect(screen.getByTestId("da-scope-banner")).toBeInTheDocument());
    await waitFor(() => expect(state.handler).toHaveBeenCalled());
    // Mermaid is loaded by dynamic import, so the diagram lands a tick after
    // the model does. Settle it here or a rendering comparison races it.
    await waitFor(() => expect(screen.getByTestId("da-diagram")).toBeInTheDocument());
    return utils;
  }

  it("discloses everything when handed no mode, exactly as mode=technical does", async () => {
    const bare = await show(undefined);
    expect(screen.getByText("Every recorded element")).toBeInTheDocument();
    expect(screen.getByText("Authority")).toBeInTheDocument();
    const html = bare.container.innerHTML;
    bare.unmount();
    const technical = await show("technical");
    expect(technical.container.innerHTML).toBe(html);
  });

  it("Simple shows the plain-language hierarchy and defers the provenance", async () => {
    await show("simple");
    // The scope warning is never deferred — it is the first thing a reader of
    // this screen has to know, at every level.
    expect(screen.getByTestId("da-scope-banner").textContent)
      .toMatch(/NOT CURRENTLY ACTIVATED IMPLEMENTATION WORK/);

    // WIASW, its five media domains, CIS and the execution layer, nested the
    // way the authority records them.
    const outline = screen.getByTestId("da-outline");
    expect(outline).toBeInTheDocument();
    for (const label of ["WIASW — Word · Image · Action · Sound + Web", "Media domains",
                         "Word", "Image", "Action", "Sound", "Web",
                         "Horizontal applications",
                         "CIS — deterministic AI / control substrate",
                         "Execution / tool backends"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    // Deeper nodes are indented by the depth the read model computed.
    const row = (label) => screen.getByText(label).closest(".da-outline-node");
    expect(row("WIASW — Word · Image · Action · Sound + Web").style.marginInlineStart)
      .toBe("0rem");
    expect(row("Media domains").style.marginInlineStart).toBe("1.1rem");
    expect(row("Word").style.marginInlineStart).toBe("2.2rem");

    // WIASW uses CIS, and CIS controls / orchestrates / executes through the
    // backends — named by LABEL, with the nesting not repeated as text.
    const text = outline.textContent;
    expect(text).toMatch(/uses → CIS — deterministic AI \/ control substrate/);
    expect(text).toMatch(/controls → Execution \/ tool backends/);
    expect(text).toMatch(/orchestrates → Creative applications/);
    expect(text).toMatch(/executes-through → Creative applications/);
    expect(text).toMatch(/supports → Media domains/);
    expect(text).not.toMatch(/contains →/);

    // Nothing is activated, and that is said on every node.
    expect(screen.getAllByText("not activated").length).toBeGreaterThan(0);
    expect(screen.getAllByText("tracked elsewhere").length).toBeGreaterThan(0);

    // Deferred: the ids, the kinds, the depths, the ADRs, the counts, the
    // relationship vocabulary and the authority panel.
    expect(screen.queryByText(/declared by ADR-WIASW-001/)).toBeNull();
    expect(screen.queryByText(/root · depth 0/)).toBeNull();
    expect(screen.queryByText("Every recorded element")).toBeNull();
    expect(screen.queryByText("What the relationships mean")).toBeNull();
    expect(screen.queryByText("Authority")).toBeNull();
    expect(screen.queryByText(/12 nodes/)).toBeNull();
    expect(screen.queryByText(/project_decisions rows with id LIKE/)).toBeNull();
    expect(screen.queryByText(/state revision/)).toBeNull();
  });

  it("More Detail adds the domains, the relationship meanings and activation meaning",
     async () => {
    await show("detail");
    // The outline's job is done by the full node cards at this level.
    expect(screen.queryByTestId("da-outline")).toBeNull();
    expect(screen.getByText("Every recorded element")).toBeInTheDocument();
    expect(screen.getByText("Horizontal applications")).toBeInTheDocument();
    expect(screen.getByText("Creative applications")).toBeInTheDocument();
    expect(screen.getByText("Blender, Houdini, ComfyUI, Unreal Engine, DAWs"))
      .toBeInTheDocument();

    // What the relationships and the activation states MEAN.
    expect(screen.getByText("What the relationships mean")).toBeInTheDocument();
    expect(screen.getByText(/the source is built on top of the target/)).toBeInTheDocument();
    expect(screen.getByText(/the source coordinates multiple independent targets/))
      .toBeInTheDocument();
    expect(screen.getByText(/recorded destination architecture carrying no activated/))
      .toBeInTheDocument();
    expect(screen.getByText(/activation_state is NOT a build status/)).toBeInTheDocument();
    expect(screen.getByText("12 nodes")).toBeInTheDocument();

    // Edges still read by label, not by id, and the provenance is still deferred.
    // The relationship is its own <span>, so the matcher sees the li's own text.
    expect(screen.getAllByText(/→ CIS — deterministic AI/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/declared by ADR-WIASW-001/)).toBeNull();
    expect(screen.queryByText(/root · depth 0/)).toBeNull();
    expect(screen.queryByText("Authority")).toBeNull();
    expect(screen.queryByText(/project_decisions rows with id LIKE/)).toBeNull();
  });

  it("Technical adds the node ids, kinds, the declaring ADR and the quoted declarations",
     async () => {
    await show("technical");
    expect(screen.getByText(/root · depth 0/)).toBeInTheDocument();
    expect(screen.getByText("WIASW")).toBeInTheDocument();
    expect(screen.getAllByText(/declared by ADR-WIASW-001 \(DESTINATION GRAPH NODES\)/).length)
      .toBe(12);
    // Edges now name the declared id rather than the label.
    expect(screen.getByText(/→ CIS$/)).toBeInTheDocument();
    expect(screen.queryByText(/→ CIS — deterministic AI/)).toBeNull();
    // The authority panel, its ADR rows and the quoted decisions.
    expect(screen.getByText("Authority")).toBeInTheDocument();
    expect(screen.getByText(/project_decisions rows with id LIKE 'ADR-WIASW-%'/))
      .toBeInTheDocument();
    expect(screen.getByText(/parsed from those decision rows at read time/))
      .toBeInTheDocument();
    expect(screen.getAllByText(/from ADR-WIASW-001/).length).toBeGreaterThan(0);
    expect(screen.getByText(/state revision/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Show the decisions/ }));
    expect(screen.getByText(/WIASW = Word · Image · Action · Sound \+ Web/))
      .toBeInTheDocument();
  });

  it("changing the level of detail re-reads nothing", async () => {
    // The mode is presentation. It never refetches, and it never reaches the
    // build path's model — which is not even in this mock.
    const { unmount } = await show("simple");
    expect(state.handler).toHaveBeenCalledTimes(1);
    unmount();
    await show("technical");
    expect(state.handler).toHaveBeenCalledTimes(2);
  });

  it("keeps the recorded problems honest, and says so from More Detail up", async () => {
    state.handler = vi.fn(async () => ok(fullModel({
      problems: [{ kind: "undefined_relationship", detail: "an edge uses 'feeds', undefined" }],
    })));
    const { unmount } = await show("simple");
    // Simple is the plain hierarchy; a parser complaint is not part of it.
    expect(screen.queryByTestId("da-problems")).toBeNull();
    unmount();
    await show("detail");
    expect(screen.getByTestId("da-problems").textContent)
      .toMatch(/an edge uses 'feeds', undefined/);
  });
});
