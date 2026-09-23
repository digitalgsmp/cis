import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SystemContext from "./SystemContext";

// In-memory fake of runtime/api/system_context.py's two GET routes — no
// real fetch, no network. Deliberately exposes ONLY read endpoints:
// getSystemContext / getRecoveryPacket, mirroring api.js. If SystemContext
// ever called anything else from ./api, importing it here would throw
// (vi.mock below has no other exports), which is itself a guard against
// the component silently growing a mutation call.
const state = {
  handlers: {
    systemContext: null, // function(): result
    recoveryPacket: null, // function(issue): result
  },
};

vi.mock("./api", () => ({
  getSystemContext: (...args) => state.handlers.systemContext(...args),
  getRecoveryPacket: (...args) => state.handlers.recoveryPacket(...args),
}));

function ok(data) {
  return { ok: true, data };
}

function fail(error) {
  return { ok: false, error };
}

function fullState(overrides = {}) {
  return {
    revision: "abc123",
    computed_at: "2026-09-21T00:00:00Z",
    source: "data/cis_memory.db (see AUTHORITY_TABLES)",
    queue_focus: {
      counts_by_status: { OPEN: 2, DONE: 5 },
      open_items: [
        { item_num: "4.30", tier: 4, title: "Workbench recovery UI", need_status: "OPEN" },
      ],
    },
    open_blocked_deferred: {
      queue_open_or_blocked: [],
      unresolved_discoveries: [],
      closeout_status_by_task: {},
    },
    recent_verified_closed: { queue_items_done: [], session_closeouts_pass: [], dev_continuity_verified_results: [] },
    active_decisions: [{ id: "D1", label: "use sqlite spine", decision: "keep it", reason: "", status: "ACTIVE", decided_at: "" }],
    open_questions: [],
    discoveries_requiring_attention: [],
    source_table_freshness: {
      queue_items: { row_count: 12, last_activity: "2026-09-20 10:00:00", days_since_activity: 1, dormant: false },
    },
    generated_artifact_freshness: {
      "docs/UNIFIED_BUILD_LIST.md": { fresh: true, detail: "" },
    },
    observed_runtime_health: {
      _note: "observed live at call time -- not authoritative, not persisted",
      gateways: { prime_chat: { port: 8642, listening: true }, reviewer1: { port: 8643, listening: false } },
      repo_dirty: true,
      dirty_file_count: 3,
      spine_db_reachable: true,
    },
    ...overrides,
  };
}

function fullPacket(issue = null, overrides = {}) {
  return {
    packet_kind: "cis_external_recovery_packet",
    generated_at: "2026-09-21T00:05:00Z",
    state_revision: "abc123",
    authority_statement: "The SQLite spine database is the sole authoritative source.",
    issue_focus: issue,
    ...overrides,
  };
}

beforeEach(() => {
  cleanup();
  state.handlers.systemContext = vi.fn(async () => ok(fullState()));
  state.handlers.recoveryPacket = vi.fn(async (issue) => ok(fullPacket(issue || null)));
});

// userEvent.setup() installs its own clipboard polyfill on
// navigator.clipboard, so a stub installed before it (e.g. in a shared
// beforeEach) gets clobbered. Call this AFTER userEvent.setup() in any
// test that asserts on clipboard writes.
function stubClipboard() {
  const writeText = vi.fn(async () => {});
  Object.defineProperty(window.navigator, "clipboard", {
    value: { writeText },
    configurable: true,
  });
  return writeText;
}

describe("SystemContext (Card 03)", () => {
  it("loads and renders authoritative state on mount", async () => {
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText(/Workbench recovery UI/)).toBeInTheDocument());
    expect(screen.getByText(/A\. Authoritative project state/)).toBeInTheDocument();
    expect(screen.getByText("use sqlite spine", { exact: false })).toBeInTheDocument();
  });

  it("surfaces current_focus and active_blockers (Card 04 R1 correction) when the canonical state carries them", async () => {
    state.handlers.systemContext = vi.fn(async () => ok(fullState({
      current_focus: {
        current_queue_item_pointer: { value: "WB.1", source: "manual", created_at: "2026-09-17T13:39:11Z" },
        current_queue_item_detail: { title: "workbench priority", need_status: "OPEN" },
        recent_task_activity: [
          { id: 34, task: "4.32", revision: 15, kind: "user_instruction", summary: "recovery drill work", created_at: "2026-09-22" },
        ],
        recent_task_queue_items: { "4.32": { need_status: "OPEN", title: "recovery drill" } },
        recent_task_activity_fetch_handle: "python3 -m tools.development.cli events <task>",
      },
      active_blockers: [
        { id: "BLK-SEED-004", description: "Google Drive backup integrity unverified", source_dormant: true },
      ],
    })));
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText("Current focus")).toBeInTheDocument());
    expect(screen.getByText("WB.1")).toBeInTheDocument();
    expect(screen.getByText(/recovery drill work/)).toBeInTheDocument();
    expect(screen.getByText("BLK-SEED-004", { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/dormant source/)).toBeInTheDocument();
  });

  it("renders observed runtime health as a visually/structurally distinct section", async () => {
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText(/B\. Observed runtime health/)).toBeInTheDocument());
    const tag = screen.getByText(/LIVE OBSERVATION/);
    expect(tag.className).toContain("sc-observed-tag");
    // The section it lives in must carry the distinct sc-observed class,
    // not just plain sc-section styling shared with authoritative state.
    expect(tag.closest(".sc-section").className).toContain("sc-observed");
  });

  it("shows an honest error and no fabricated data when the initial load fails", async () => {
    state.handlers.systemContext = vi.fn(async () => fail("spine unreachable"));
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText(/Could not load authoritative state/)).toBeInTheDocument());
    expect(screen.getByText(/spine unreachable/)).toBeInTheDocument();
    expect(screen.queryByText(/A\. Authoritative project state/)).not.toBeInTheDocument();
  });

  it("keeps the last successfully loaded state visible, marked stale, when a refresh fails", async () => {
    const user = userEvent.setup();
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText(/Workbench recovery UI/)).toBeInTheDocument());

    state.handlers.systemContext = vi.fn(async () => fail("gateway timeout"));
    await user.click(screen.getByRole("button", { name: /Refresh/ }));

    await waitFor(() => expect(screen.getByText(/Could not load authoritative state/)).toBeInTheDocument());
    // Prior data is NOT wiped out by the failed refresh.
    expect(screen.getByText(/Workbench recovery UI/)).toBeInTheDocument();
    expect(screen.getByText(/STALE/)).toBeInTheDocument();
  });

  it("copies the full recovery packet via getRecoveryPacket(undefined) and the clipboard, with no mutation call", async () => {
    const user = userEvent.setup();
    const writeText = stubClipboard();
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText(/Workbench recovery UI/)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /Copy full recovery context/ }));

    await waitFor(() => expect(state.handlers.recoveryPacket).toHaveBeenCalledWith(undefined));
    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    const copied = JSON.parse(writeText.mock.calls[0][0]);
    expect(copied.packet_kind).toBe("cis_external_recovery_packet");
    await waitFor(() => expect(screen.getByText(/Copied full recovery packet/)).toBeInTheDocument());
  });

  it("requires a focus area before copying a focused packet, then calls getRecoveryPacket(issue)", async () => {
    const user = userEvent.setup();
    stubClipboard();
    render(<SystemContext onBack={() => {}} />);
    await waitFor(() => expect(screen.getByText(/Workbench recovery UI/)).toBeInTheDocument());

    const focusedBtn = screen.getByRole("button", { name: /Copy focused recovery context/ });
    expect(focusedBtn).toBeDisabled();

    await user.selectOptions(screen.getByRole("combobox"), "queue");
    expect(focusedBtn).toBeEnabled();
    await user.click(focusedBtn);

    await waitFor(() => expect(state.handlers.recoveryPacket).toHaveBeenCalledWith("queue"));
    await waitFor(() => expect(screen.getByText(/Copied focused recovery packet \(queue\)/)).toBeInTheDocument());
  });

  it("calls onBack when the back control is used", async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();
    render(<SystemContext onBack={onBack} />);
    await waitFor(() => expect(screen.getByText(/Workbench recovery UI/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Back to conversation/ }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
