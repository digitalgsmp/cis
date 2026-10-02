import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BuildPath from "./BuildPath";

// In-memory fake of runtime/api/build_path.py's single GET route — no real
// fetch, no network, no model call. The mock deliberately exposes ONLY
// getBuildPath: if BuildPath.jsx ever reached for a mutating api.js function,
// it would be undefined here, which is itself the guard that this screen stays
// read-only.
const state = { handler: null, mermaidThrows: false, renderCalls: [] };

vi.mock("./api", () => ({
  getBuildPath: (...args) => state.handler(...args),
}));

// Mermaid does real layout measurement, which jsdom has no engine for. Stubbed
// so these tests assert what THIS component does with Mermaid's answer —
// inject the SVG, or fall back to the source when it fails — rather than
// re-testing Mermaid itself.
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

// Shaped exactly like tools/state/build_path.py's output for the state the
// spine actually carries today (see runtime/tests/test_build_path_api.py,
// which asserts that shape against the live spine).
function fullModel(overrides = {}) {
  return {
    read_model: "cis_build_path",
    generated_at: "2026-10-01T18:40:00Z",
    state_revision: "34af09639ee7bdf3",
    status_vocabulary: ["complete", "active", "blocked", "next", "pending",
                        "deferred", "resolved", "blocking", "open"],
    authority: {
      sequencing: "project_decisions + project_state.pipeline_roadmap (ADR-PIPE-006)",
      work_items: "queue_items + queue_edges (ADR-PIPE-006)",
      generated_view: "docs/UNIFIED_BUILD_LIST.md is a generated projection of the queue, not an authority",
      retired: "build_plan_nodes is the retired tier-plan mechanism",
      separation_note: "the roadmap and the queue are intentionally separate planes",
    },
    roadmap_source: {
      state_key: "pipeline_roadmap", row_id: 130,
      recorded_at: "2026-10-01T05:26:27Z",
      raw: "P0 (activate WB.1 Slice 1) -> QUEUE TRIAGE (56 unclassified queue_items) -> …",
      constraints_text: "CONSTRAINTS: P1 before P2; triage after P0 and before P1.",
      parse_note: null,
    },
    progress: { total_phases: 9, complete: 0, current_order: 0, current_phase_note: null },
    current: {
      phase_id: "P0", label: "P0", status: "active", blocked: true,
      status_label: "active / blocked", task: "WB.1",
      evidence: {
        state_key: "build_phase", row_id: 141,
        recorded_at: "2026-10-01T17:48:05Z",
        value: "Phase P0 of the P0-P6 sequence is ACTIVATED BUT NOT COMPLETE",
      },
    },
    next: {
      phase_id: "QUEUE_TRIAGE", label: "QUEUE TRIAGE", status: "next",
      description: "56 unclassified queue_items",
    },
    next_action: {
      recorded_at: "2026-10-01T17:48:29Z", source: "manual",
      text: "Finish WB.1 P0 closeout. Bounded queue triage is NOT the next action.",
    },
    current_direction: {
      recorded_at: "2026-10-01T17:48:05Z", source: "manual",
      text: "P0 ACTIVATED BUT BLOCKED ON LIVE CLOSEOUT.",
    },
    phases: [
      {
        id: "P0", label: "P0", order: 0, description: "activate WB.1 Slice 1",
        status: "active", blocked: true, status_label: "active / blocked",
        is_current: true, is_next: false, task: "WB.1",
        migrations: [
          { migration: "0035", rule: "required at this phase", applied: true,
            tables: { workbench_projects: true }, detected_by: "presence of the tables 0035 creates" },
          { migration: "0038", rule: "required at this phase", applied: true,
            tables: { workbench_action_proposals: true }, detected_by: "presence of the tables 0038 creates" },
        ],
        queue_hooks: [], constraints: [],
        discoveries: {
          counts: { blocking: 2, open: 12, deferred: 14, resolved: 17 },
          blocking: [], open: [], deferred: [], resolved: [],
        },
      },
      {
        id: "QUEUE_TRIAGE", label: "QUEUE TRIAGE", order: 1,
        description: "56 unclassified queue_items", status: "next", blocked: false,
        status_label: "next", is_current: false, is_next: true,
        migrations: [], queue_hooks: [],
        constraints: [
          { constraint: "bounded mechanical classification", source: "ADR-PIPE-006",
            quote: "bounded mechanical classification pass over the currently unclassified queue_items" },
          { constraint: "no redesign", source: "ADR-PIPE-006",
            quote: "NO item redesign during triage" },
        ],
        queue_classification: {
          total_items: 132, unclassified: 56, missing_need_status: 56, missing_scope: 69,
          counts_by_need_status: { "(unset)": 56, OPEN: 47 },
          unclassified_definition: "queue_items rows carrying neither scope nor need_status",
        },
        discoveries: null,
      },
      {
        id: "P1", label: "P1", order: 2,
        description: "Layer-2 run-plane read model + /api/workbench/runs",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false,
        migrations: [], queue_hooks: [], constraints: [], discoveries: null,
      },
      {
        id: "P2", label: "P2", order: 3, description: "Slice 2 clarified direction",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false,
        migrations: [], queue_hooks: [], constraints: [], discoveries: null,
      },
      {
        id: "TIER_0_TRUST", label: "TIER-0 TRUST", order: 4,
        description: "queue 0.4 + 0.6, own card",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false, migrations: [],
        queue_hooks: [
          { item_num: "0.4", found: true, tier: 0, need_status: "HALF_DONE",
            title: "Override plane and fail-mode policy before any blocking gate is trusted" },
          { item_num: "0.6", found: true, tier: 0, need_status: "OPEN",
            title: "ARMING A GUARDRAIL NEEDS AN OVERRIDE POLICY THAT DOES NOT EXIST" },
        ],
        constraints: [], discoveries: null,
      },
      {
        id: "P3", label: "P3", order: 5,
        description: "Slice 3 reviewed work card; unlocks migration 0036",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false,
        migrations: [
          { migration: "0036", rule: "not permitted before this phase", applied: false,
            tables: { card_factory_asks: false }, detected_by: "presence of the tables 0036 creates" },
        ],
        queue_hooks: [], constraints: [], discoveries: null,
      },
      {
        id: "P4", label: "P4", order: 6,
        description: "Slice 4 execution visibility; unlocks migration 0037; queue 1.23",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false,
        migrations: [
          { migration: "0037", rule: "not permitted before this phase", applied: false,
            tables: { card_runner_runs: false }, detected_by: "presence of the tables 0037 creates" },
        ],
        queue_hooks: [
          { item_num: "1.23", found: true, tier: 1, need_status: "OPEN",
            title: "A code run has never completed end to end" },
        ],
        constraints: [], discoveries: null,
      },
      {
        id: "P5", label: "P5", order: 7, description: "Slice 5 verification and outcome",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false,
        migrations: [], queue_hooks: [], constraints: [], discoveries: null,
      },
      {
        id: "P6", label: "P6", order: 8, description: "Slice 6 recovery and learning loop",
        status: "pending", blocked: false, status_label: "pending",
        is_current: false, is_next: false,
        migrations: [], queue_hooks: [], constraints: [], discoveries: null,
      },
    ],
    blockers: [
      { id: "WB1-D15", task: "WB.1", revision: 65, status: "blocking",
        disposition: "BEFORE_STAGE_CLOSEOUT", blocking: true, resolved: false,
        malformed: false, summary: "WB1-D15: the Brain gateway's upstream credential is rejected",
        summary_truncated: false, created_at: "2026-10-01 16:42:22" },
      { id: "WB1-D11", task: "WB.1", revision: 48, status: "blocking",
        disposition: "BEFORE_STAGE_CLOSEOUT", blocking: true, resolved: false,
        malformed: false, summary: "WB1-D11: an OpenRouter API key is present in a tracked file",
        summary_truncated: false, created_at: "2026-09-25 23:56:17" },
    ],
    discoveries: {
      counts: { blocking: 2, open: 1, deferred: 1, resolved: 2 },
      blocking: [
        { id: "WB1-D15", task: "WB.1", revision: 65, status: "blocking",
          disposition: "BEFORE_STAGE_CLOSEOUT", blocking: true, resolved: false,
          summary: "WB1-D15: credential rejected upstream" },
      ],
      open: [
        { id: "WB1-D18", task: "WB.1", revision: 72, status: "open",
          disposition: "BEFORE_STAGE_CLOSEOUT", blocking: false, resolved: false,
          summary: "WB1-D18: the generated AGENTS.md projection is near its size guard" },
      ],
      deferred: [
        { id: "WB1-D14", task: "WB.1", revision: 56, status: "deferred",
          disposition: "EXPLICITLY_DEFERRED", blocking: false, resolved: false,
          summary: "WB1-D14: a daemon continuously dirties a tracked file" },
      ],
      resolved: [
        { id: "WB1-D17", task: "WB.1", revision: 68, status: "resolved",
          disposition: "BEFORE_STAGE_CLOSEOUT", blocking: true, resolved: true,
          summary: "WB1-D17: the public Workbench origin now reaches production" },
        { id: "WB1-D16", task: "WB.1", revision: 66, status: "resolved",
          disposition: "BEFORE_STAGE_CLOSEOUT", blocking: false, resolved: true,
          summary: "WB1-D16: brain generation errors now fail closed" },
      ],
    },
    discoveries_note: null,
    queue: {
      total_items: 132, unclassified: 56, missing_need_status: 56, missing_scope: 69,
      counts_by_need_status: { "(unset)": 56, OPEN: 47 },
      unclassified_definition: "queue_items rows carrying neither scope nor need_status",
    },
    checkpoint: {
      present: true, recorded_at: "2026-10-01T18:26:20Z", source: "git",
      lifecycle_state: "REMOTE_REVIEW_REQUIRED",
      latest_local_sha: "383b404dc2847aaa9a1260d5de5483535b774892",
      latest_pushed_sha: "383b404dc2847aaa9a1260d5de5483535b774892",
      latest_remote_verified_sha: "3d74c9f4bbd7f301de7fa88a0a8175cef73e8862",
      pushed_sha_is_independently_verified: false,
      remote_review_required: true, independently_verified: false,
      remote_ref: "origin/master",
      next_transition: { to: "REMOTE_VERIFIED", requires: "independent readback from the remote" },
      scope_boundary: "Repository-checkpoint lifecycle only. This key never records phase completion.",
    },
    decisions: [
      { id: "ADR-PIPE-001", label: "Contained-pipeline forward sequence P0 through P6",
        decision: "…", status: "DECIDED", decided_at: "2026-09-30T19:21:59Z" },
      { id: "ADR-PIPE-006", label: "Roadmap and queue are separate authorities",
        decision: "…", status: "DECIDED", decided_at: "2026-10-01T05:25:26Z" },
    ],
    mermaid: [
      "flowchart TD",
      '  P0["P0 — activate WB.1 Slice 1<br/>[active / blocked]"]',
      '  QUEUE_TRIAGE["QUEUE TRIAGE — 56 unclassified queue_items<br/>[next]"]',
      "  P0 --> QUEUE_TRIAGE",
      "  class P0 blockedPhase",
    ].join("\n"),
    ...overrides,
  };
}

beforeEach(() => {
  cleanup();
  state.mermaidThrows = false;
  state.renderCalls = [];
  state.handler = vi.fn(async () => ok(fullModel()));
});

describe("BuildPath (read-only build path visualization)", () => {
  it("loads the read model on mount and shows the current phase as active / blocked", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("Current phase")).toBeInTheDocument());
    expect(state.handler).toHaveBeenCalledTimes(1);
    // The status label comes from the server, and it is NOT "complete".
    expect(screen.getAllByText("active / blocked").length).toBeGreaterThan(0);
    expect(screen.queryByText("complete")).not.toBeInTheDocument();
    expect(screen.getByText(/stage 1 of 9/)).toBeInTheDocument();
    expect(screen.getByText(/current task: WB\.1/)).toBeInTheDocument();
  });

  it("shows Queue Triage as the next stage, with its bounded-classification constraints", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("Next stage")).toBeInTheDocument());
    expect(screen.getAllByText("QUEUE TRIAGE").length).toBeGreaterThan(0);
    expect(screen.getAllByText("next").length).toBeGreaterThan(0);
    expect(screen.getByText("bounded mechanical classification")).toBeInTheDocument();
    expect(screen.getByText("no redesign")).toBeInTheDocument();
    expect(screen.getByText(/56 unclassified of 132 queue_items/)).toBeInTheDocument();
  });

  it("shows the next action from project_state, attributed to its row", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("Next action")).toBeInTheDocument());
    expect(screen.getByText(/Finish WB\.1 P0 closeout/)).toBeInTheDocument();
    expect(screen.getByText(/project_state\.next_action, recorded/)).toBeInTheDocument();
  });

  it("renders every roadmap phase, with the migration unlock points on their own phases", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("P0 → P6 sequence")).toBeInTheDocument());
    for (const label of ["P0", "QUEUE TRIAGE", "P1", "P2", "TIER-0 TRUST", "P3", "P4", "P5", "P6"]) {
      expect(screen.getAllByText(new RegExp(`^${label}$`)).length).toBeGreaterThan(0);
    }
    // P3 unlocks 0036; P4 unlocks 0037 — both reported as not applied.
    expect(screen.getByText("migration 0036")).toBeInTheDocument();
    expect(screen.getByText("migration 0037")).toBeInTheDocument();
    expect(screen.getAllByText("not applied").length).toBe(2);
    // P0's own prerequisites are shown as applied.
    expect(screen.getByText("migration 0035")).toBeInTheDocument();
    expect(screen.getByText("migration 0038")).toBeInTheDocument();
    expect(screen.getAllByText("applied").length).toBe(2);
  });

  it("shows the Tier-0 trust and P4 queue hooks with their real queue item titles", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("queue 0.4")).toBeInTheDocument());
    expect(screen.getByText("queue 0.6")).toBeInTheDocument();
    expect(screen.getByText("queue 1.23")).toBeInTheDocument();
    expect(screen.getByText(/A code run has never completed end to end/)).toBeInTheDocument();
    expect(screen.getByText(/Override plane and fail-mode policy/)).toBeInTheDocument();
  });

  it("lists D15 as blocking and D16/D17 as resolved, without mixing the two", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("Blocking items")).toBeInTheDocument());

    const blockerSection = screen.getByText("Blocking items").closest(".bp-blockers");
    const blockingList = blockerSection.querySelector("ul.sc-list");
    expect(blockingList.textContent).toContain("WB1-D15");
    expect(blockingList.textContent).not.toContain("WB1-D16");
    expect(blockingList.textContent).not.toContain("WB1-D17");

    // Resolved items appear under their own heading, labelled resolved.
    const resolvedList = screen.getByText("Resolved").nextElementSibling;
    expect(resolvedList.textContent).toContain("WB1-D16");
    expect(resolvedList.textContent).toContain("WB1-D17");
    expect(resolvedList.querySelectorAll(".sc-badge").length).toBe(2);
    expect(resolvedList.textContent).toContain("resolved");

    // And D14 is shown as deferred, not as a blocker.
    const deferredList = screen.getByText("Explicitly deferred").nextElementSibling;
    expect(deferredList.textContent).toContain("WB1-D14");
    expect(deferredList.textContent).toContain("deferred");
  });

  it("renders the Mermaid diagram from the server's source", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByTestId("bp-diagram")).toBeInTheDocument());
    expect(state.renderCalls).toHaveLength(1);
    // The source handed to Mermaid is the server's, unmodified.
    expect(state.renderCalls[0].source).toBe(fullModel().mermaid);
    expect(screen.getByTestId("bp-diagram").querySelector("svg")).toBeTruthy();
    // Not shown until asked for — the picture is the default view.
    expect(screen.queryByTestId("bp-mermaid-source")).not.toBeInTheDocument();
  });

  it("falls back to the Mermaid source, and says why, when the diagram cannot be drawn", async () => {
    state.mermaidThrows = true;
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() =>
      expect(screen.getByText(/Could not draw the diagram/)).toBeInTheDocument());
    expect(screen.getByText(/no layout engine here/)).toBeInTheDocument();
    const pre = screen.getByTestId("bp-mermaid-source");
    expect(pre.textContent).toContain("flowchart TD");
    expect(pre.textContent).toContain("P0 --> QUEUE_TRIAGE");
    // The rest of the screen is unaffected: a failed drawing is not a failed load.
    expect(screen.getByText("Current phase")).toBeInTheDocument();
    expect(screen.queryByTestId("bp-diagram")).not.toBeInTheDocument();
  });

  it("can show the Mermaid source on request even when the diagram drew fine", async () => {
    const user = userEvent.setup();
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByTestId("bp-diagram")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Show Mermaid source/ }));
    expect(screen.getByTestId("bp-mermaid-source").textContent).toContain("flowchart TD");
  });

  it("shows the external checkpoint and refuses to call a pushed SHA verified", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() =>
      expect(screen.getByText("External developer checkpoint")).toBeInTheDocument());
    expect(screen.getByText("REMOTE_REVIEW_REQUIRED")).toBeInTheDocument();
    expect(screen.getByText(/pushed SHA independently verified: no/)).toBeInTheDocument();
    expect(screen.getByText(/never records phase completion/)).toBeInTheDocument();
  });

  it("distinguishes roadmap authority from queue authority", async () => {
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() =>
      expect(screen.getByText("What is authoritative here")).toBeInTheDocument());
    expect(screen.getByText(/Roadmap \/ sequencing:/)).toBeInTheDocument();
    expect(screen.getByText(/project_decisions \+ project_state\.pipeline_roadmap/))
      .toBeInTheDocument();
    expect(screen.getByText(/Tasks \/ work items:/)).toBeInTheDocument();
    expect(screen.getByText(/queue_items \+ queue_edges/)).toBeInTheDocument();
    expect(screen.getByText(/UNIFIED_BUILD_LIST\.md is a generated projection/))
      .toBeInTheDocument();
    expect(screen.getByText(/build_plan_nodes is the retired/)).toBeInTheDocument();
  });

  it("shows a load error and no fabricated roadmap when the read model fails", async () => {
    state.handler = vi.fn(async () => fail("build path read model unavailable: OperationalError"));
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() =>
      expect(screen.getByText(/Could not load the build path/)).toBeInTheDocument());
    expect(screen.getByText(/OperationalError/)).toBeInTheDocument();
    // Nothing invented in place of the real thing.
    expect(screen.queryByText("Current phase")).not.toBeInTheDocument();
    expect(screen.queryByText("P0 → P6 sequence")).not.toBeInTheDocument();
    expect(screen.queryByTestId("bp-diagram")).not.toBeInTheDocument();
    expect(state.renderCalls).toHaveLength(0);
    expect(screen.getByText(/No build path has loaded in this session/)).toBeInTheDocument();
  });

  it("keeps the last good view, marked stale, when a refresh fails", async () => {
    const user = userEvent.setup();
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("Current phase")).toBeInTheDocument());

    state.handler = vi.fn(async () => fail("gateway timeout"));
    await user.click(screen.getByRole("button", { name: /Refresh/ }));

    await waitFor(() => expect(screen.getByText(/STALE/)).toBeInTheDocument());
    expect(screen.getByText(/Could not load the build path/)).toBeInTheDocument();
    expect(screen.getByText("Current phase")).toBeInTheDocument();
  });

  it("is honest when the roadmap row carries no parsable phases", async () => {
    state.handler = vi.fn(async () => ok(fullModel({
      phases: [], current: null, next: null, blockers: [],
      discoveries: { counts: {}, blocking: [], open: [], deferred: [], resolved: [] },
      progress: { total_phases: 0, complete: 0, current_order: null,
                  current_phase_note: "project_state.build_phase names no 'Phase P<n>'" },
      mermaid: "",
    })));
    render(<BuildPath onBack={() => {}} />);
    await waitFor(() =>
      expect(screen.getByText(/No current phase is recorded/)).toBeInTheDocument());
    expect(screen.getByText(/names no 'Phase P<n>'/)).toBeInTheDocument();
    expect(screen.getByText(/No phases were parsed from the roadmap row/)).toBeInTheDocument();
    expect(screen.getByText(/carried no diagram source/)).toBeInTheDocument();
    expect(screen.getByText(/No unresolved blocking discovery is recorded/)).toBeInTheDocument();
    expect(state.renderCalls).toHaveLength(0);
  });

  it("calls onBack when the back control is used", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<BuildPath onBack={onBack} />);
    await waitFor(() => expect(screen.getByText("Current phase")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Back to conversation/ }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
