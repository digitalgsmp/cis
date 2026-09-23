import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// A small in-memory fake of the backend contract documented in
// data/agent_handoffs/WB-1B-2B-conversation-actions/evidence.md, extended
// per WB-1B-3's own CORRECTION.md pass — no real fetch, no network, no
// paid model call. Every read returns a FRESH clone (never the same
// object reference twice) so a bug where the UI forgets to actually apply
// a response can't be masked by a mock that mutates shared state in
// place — the exact blind spot an independent review found in the prior
// pass's tests.
vi.mock("./api", () => {
  function clone(x) { return x === null || x === undefined ? x : JSON.parse(JSON.stringify(x)); }

  function freshState() {
    return {
      messagesByProject: { p1: [] },
      proposalsById: {},
      cardsById: {},
      runsById: {},
      nextMsgId: 1,
      nextProposalId: 1,
      nextCardId: 900,
      nextRunId: 500,
      sentRequests: new Map(), // request_id -> stored response body (cloned on read)
      modelCallCount: 0,
      generateCallCount: 0,
      dispatchCallCount: 0,
      artifactsByRun: {}, // runId -> {"evidence.md"|"review.md"|"completion.json": content}
    };
  }
  const state = freshState();
  globalThis.__fakeApiState = state;
  globalThis.__resetFakeApiState = () => Object.assign(state, freshState());

  function ok(data) { return { ok: true, data: clone(data) }; }

  function buildCard(cardId, ask_revision) {
    return {
      id: cardId, ask_id: 1, ask_revision, lineage_id: cardId, card_revision: 1,
      supersedes_id: null, is_current: true, card_text: `CARD test-card-${cardId}\n...`,
      gate_exit_code: 0, gate_output: "PASS", status: "pass", saved_path: "cards/inbox/test.md",
      error: null, usage_input_tokens: 10, usage_output_tokens: 5, usage_cost_usd: 0.001,
      stale: false, eligible_for_dispatch: true, dispatch_target: null, dispatch_status: null,
      dispatch_run_id: null, dispatch_started_at: null, dispatch_finished_at: null,
      created_at: "", updated_at: "",
    };
  }

  return {
    // OIDC browser session. These existing tests exercise the authenticated
    // app, so the default session check answers "authenticated" with a real
    // identity — the sign-in gate and its failure modes have their own suite
    // (SignIn.test.jsx). There is deliberately no login() to mock: sign-in is
    // a redirect to the identity provider, not a call this bundle can make.
    refreshSession: vi.fn(async () => ok({
      authenticated: true,
      csrf_token: "test-csrf",
      identity: { subject: "auth0|eric", email: "eric@example.com",
                  name: "Eric Shelton", role: "owner" },
    })),
    beginSignIn: vi.fn(),
    logout: vi.fn(async () => ok({ authenticated: false, provider_logout_url: null })),
    getCsrfToken: vi.fn(() => "test-csrf"),
    setCsrfToken: vi.fn(),

    listProjects: vi.fn(async () => ok({ projects: [{ id: "p1", name: "Test Project", direction_note: "" }] })),
    createProject: vi.fn(async (name) => ok({ project: { id: "p2", name, direction_note: "" } })),
    updateDirectionNote: vi.fn(async (id, note) => ok({ project: { id, name: "Test Project", direction_note: note } })),
    listMessages: vi.fn(async (projectId) => ok({ messages: state.messagesByProject[projectId] || [] })),

    sendMessage: vi.fn(async (projectId, message, requestId, { mode = "chat", proposalId } = {}) => {
      if (state.sentRequests.has(requestId)) {
        return ok({ duplicate: true, ...state.sentRequests.get(requestId) });
      }
      state.modelCallCount += 1;
      const userMsg = { id: state.nextMsgId++, role: "user", content: message, status: "completed", created_at: "" };
      const brainMsg = {
        id: state.nextMsgId++, role: "brain", status: "completed", created_at: "",
        content: mode === "chat" ? "Got it." : "Here is a proposed next step.",
      };
      state.messagesByProject[projectId] = [...(state.messagesByProject[projectId] || []), userMsg, brainMsg];

      let proposal = null;
      if (mode === "draft_proposal") {
        const permittedFiles = message.includes("NO_SCOPE") ? [] : ["runtime/ui/src/App.jsx", "runtime/ui/src/api.js"];
        proposal = {
          id: state.nextProposalId++, project_id: projectId, source_message_ids: [userMsg.id],
          user_words: message, kind: "mockup", outcome: "Build a demo page", action: "Create a static mock-up",
          boundaries: "Only the mock-up file", success_criteria: "Eric can view it in a browser",
          unresolved_decisions: "", permitted_files: permittedFiles, permitted_commands: [],
          revision: 1, confirmed_revision: null, status: "proposed",
          card_factory_ask_id: null, card_factory_card_id: null, card_runner_run_id: null,
          created_at: "", updated_at: "",
        };
        state.proposalsById[proposal.id] = proposal;
      } else if (mode === "revise_proposal") {
        const p = state.proposalsById[proposalId];
        proposal = p;
        if (message.includes("TRIGGER_PROPOSAL_ERROR")) {
          const body = {
            duplicate: false, user_message: userMsg, brain_message: brainMsg,
            proposal, proposal_error: "done_when_text too long (max 2000 characters)",
          };
          state.sentRequests.set(requestId, clone(body));
          return ok(body);
        }
        p.revision += 1;
        p.outcome = "Build a demo page (corrected: two pages)";
        p.source_message_ids = [...p.source_message_ids, userMsg.id];
        p.status = "proposed";
      }
      const body = { duplicate: false, user_message: userMsg, brain_message: brainMsg, proposal, proposal_error: null };
      state.sentRequests.set(requestId, clone(body));
      return ok(body);
    }),

    listProposals: vi.fn(async (projectId) => ok({
      proposals: Object.values(state.proposalsById).filter((p) => p.project_id === projectId).sort((a, b) => b.id - a.id),
    })),

    getProposal: vi.fn(async (id) => {
      const proposal = state.proposalsById[id];
      const body = { proposal };
      if (proposal.card_factory_card_id) body.card = state.cardsById[proposal.card_factory_card_id];
      if (proposal.card_runner_run_id) body.run = state.runsById[proposal.card_runner_run_id];
      return ok(body);
    }),

    confirmDirection: vi.fn(async (id, requestId) => {
      const dedupKey = `confirm-${id}-${requestId}`;
      if (state.sentRequests.has(dedupKey)) return ok(state.sentRequests.get(dedupKey));
      state.generateCallCount += 1;
      const p = state.proposalsById[id];
      // Mirrors generate_card_core: every confirm-direction call (first
      // time or a resync after a correction) creates a NEW card_factory_
      // cards row — never reuses the previous one's id.
      const cardId = state.nextCardId++;
      const card = buildCard(cardId, p.revision);
      state.cardsById[cardId] = card;
      p.card_factory_card_id = cardId;
      p.confirmed_revision = p.revision;
      const body = { proposal: p, card, duplicate: false };
      state.sentRequests.set(dedupKey, clone(body));
      return ok(body);
    }),

    approveProposal: vi.fn(async (id, requestId, payload) => {
      // Mirrors the real route's own required-field check (workbench_app.py
      // approve_proposal): missing expected_proposal_revision is a 400
      // before anything else is evaluated.
      if (payload.expected_proposal_revision == null) {
        return { ok: false, status: 400, error: "expected_proposal_revision is required" };
      }
      const dedupKey = `approve-${requestId}`;
      if (state.sentRequests.has(dedupKey)) {
        return ok({ ...state.sentRequests.get(dedupKey), duplicate: true });
      }
      const p = state.proposalsById[id];
      if (p.revision !== payload.expected_proposal_revision) {
        return { ok: false, status: 409, error: `stale proposal revision: expected ${payload.expected_proposal_revision}, now ${p.revision}` };
      }
      if (p.confirmed_revision !== p.revision) {
        return { ok: false, status: 409, error: "proposal has been corrected since direction was last confirmed" };
      }
      state.dispatchCallCount += 1;
      const runId = state.nextRunId++;
      const run = {
        id: runId, status: "running", mode: "implement", target: payload.target || "claude",
        model: payload.model, card_factory_card_id: p.card_factory_card_id,
        card_fingerprint: `fp-${p.card_factory_card_id}`,
        active_lock: true, cancel_requested: false, usage_unknown: false, card_completion_status: null,
        input_tokens: 0, output_tokens: 0, cost_usd: 0, num_turns: null, final_message: null,
        out_of_scope: null, run_dir: `data/agent_handoffs/fake-run-${runId}`,
      };
      state.runsById[runId] = run;
      p.status = "approved";
      p.card_runner_run_id = runId;
      const body = { proposal: p, run, duplicate: false };
      state.sentRequests.set(dedupKey, clone(body));
      return ok(body);
    }),

    getRunStatus: vi.fn(async (runId) => ok({ run: state.runsById[runId] })),
    stopRun: vi.fn(async (runId) => {
      const run = state.runsById[runId];
      run.status = "stopped";
      run.active_lock = false;
      return ok({ run });
    }),
    listRuns: vi.fn(async () => ok({ runs: [], totals_by_project: {} })),
    dispatchRun: vi.fn(async (payload) => {
      // Mirrors card_runner.dispatch()'s own real constraint (mode='review'
      // requires review_of_run_id belonging to the SAME card_factory_card_id
      // being dispatched) so a wrong caller (e.g. sending the current card's
      // id instead of the reviewed run's own) is caught here exactly like
      // the real backend would reject it.
      if (payload.mode === "review") {
        const implRun = state.runsById[payload.review_of_run_id];
        if (!implRun || implRun.card_factory_card_id !== payload.card_factory_card_id) {
          return {
            ok: false, status: 400,
            error: "review_of_run_id does not belong to the same card_factory_card_id being reviewed",
          };
        }
      }
      state.dispatchCallCount += 1;
      const runId = state.nextRunId++;
      const run = {
        id: runId, status: "completed", mode: payload.mode || "review", target: payload.target || "claude",
        model: payload.model, card_factory_card_id: payload.card_factory_card_id,
        card_fingerprint: `fp-${payload.card_factory_card_id}`,
        active_lock: false, cancel_requested: false, usage_unknown: false, card_completion_status: null,
        input_tokens: 1, output_tokens: 1, cost_usd: 0.0001, num_turns: 1,
        final_message: "Review looks fine.", out_of_scope: null, run_dir: `data/agent_handoffs/fake-review-${runId}`,
      };
      state.runsById[runId] = run;
      return ok({ run, duplicate: false });
    }),

    getRunArtifact: vi.fn(async (runId, name) => {
      const fixture = state.artifactsByRun[runId]?.[name];
      if (fixture === undefined) return ok({ name, found: false, content: null, truncated: false, error: null });
      return ok({ name, found: true, content: fixture, truncated: false, error: null });
    }),

    submitAsk: vi.fn(async () => ok({ ask: { id: 1, project: "x", ask_text: "", done_when_text: "", revision: 1 } })),
    getAsk: vi.fn(async () => ok({ ask: {} })),
    editAsk: vi.fn(async () => ok({ ask: {} })),
    generateCard: vi.fn(async () => ok({ card: {} })),
    listCards: vi.fn(async () => ok({ cards: [] })),
    getCard: vi.fn(async (cardId) => ok({ card: state.cardsById[cardId] })),
    editCard: vi.fn(async () => ok({ card: {} })),
    regateCard: vi.fn(async () => ok({ card: {} })),
  };
});

import App from "./App";

beforeEach(() => {
  localStorage.clear();
  cleanup();
  globalThis.__resetFakeApiState();
  vi.clearAllMocks();
});

async function renderAppOnProject() {
  const user = userEvent.setup();
  render(<App />);
  await screen.findByRole("heading", { name: "Test Project" });
  return user;
}

async function draftProposal(user, { noScope = false } = {}) {
  const box = screen.getByPlaceholderText(/Talk to Braingate/);
  await user.type(box, noScope ? "Let's mock up a dashboard NO_SCOPE" : "Let's mock up a dashboard");
  await user.click(screen.getByRole("button", { name: /propose action/i }));
  await screen.findByText("Build a demo page");
}

async function confirmDirectionUI(user) {
  await user.click(screen.getByRole("button", { name: /^Confirm direction/ }));
  await screen.findByText(/CARD test-card-/);
}

async function fillAndSubmitApprove(user, { skipFiles = false } = {}) {
  await user.type(screen.getByLabelText(/Authorized by/), "Eric");
  if (skipFiles) {
    await user.click(screen.getByText("Show technical details (override)"));
    await user.type(screen.getByLabelText(/Files this run may change/), "runtime/ui/src/App.jsx");
  }
  await user.click(screen.getByLabelText(/Accept time-only control/));
  await user.click(screen.getByRole("button", { name: "Approve and run" }));
}

describe("conversation-first workbench", () => {
  it("sends a plain chat message and shows the reply", async () => {
    const user = await renderAppOnProject();
    const box = screen.getByPlaceholderText(/Talk to Braingate/);
    await user.type(box, "What should we build?");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await screen.findByText("Got it.");
    expect(screen.getByText("What should we build?")).toBeInTheDocument();
  });

  it("drafts a proposal, shows it inline, and lets Eric correct it conversationally", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);
    expect(screen.getByText("Mock-up")).toBeInTheDocument();

    const correctionBox = screen.getByPlaceholderText(/Correct this/);
    await user.type(correctionBox, "Actually make it two pages");
    await user.click(screen.getByRole("button", { name: "Send correction" }));

    await screen.findByText("Build a demo page (corrected: two pages)");
    expect(screen.getByText(/proposal revision 2/)).toBeInTheDocument();
    expect(screen.queryByText("Build a demo page")).not.toBeInTheDocument();
  });

  it("initial confirmation displays the generated card even though the proposal started with no linked records", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);
    expect(screen.queryByText(/CARD test-card-/)).not.toBeInTheDocument();
    await confirmDirectionUI(user);
    expect(screen.getByRole("button", { name: /Approve and run/ })).toBeInTheDocument();
  });

  it("blocks approval after a correction until direction is confirmed again, then clears once reconfirmed", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);
    await confirmDirectionUI(user);
    await screen.findByRole("button", { name: /Approve and run/ });

    const correctionBox = screen.getByPlaceholderText(/Correct this/);
    await user.type(correctionBox, "Actually make it two pages");
    await user.click(screen.getByRole("button", { name: "Send correction" }));

    await screen.findByText(/Confirm direction again before approving/);
    expect(screen.queryByRole("button", { name: /Approve and run/ })).not.toBeInTheDocument();

    // Reconfirm — the fresh confirmed_revision must clear the stale banner.
    await user.click(screen.getByRole("button", { name: "Confirm direction again" }));
    await waitFor(() => expect(screen.queryByText(/Confirm direction again before approving/)).not.toBeInTheDocument());
    expect(screen.getByRole("button", { name: /Approve and run/ })).toBeInTheDocument();
  });

  it("presents the model's own proposed file scope as a read-only summary, and sends it without technical typing", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);
    await confirmDirectionUI(user);
    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));

    // The proposed files are shown read-only; no "Files this run may
    // change" textbox is present unless technical details are opened.
    expect(screen.getByText("runtime/ui/src/App.jsx")).toBeInTheDocument();
    expect(screen.getByText("runtime/ui/src/api.js")).toBeInTheDocument();
    expect(screen.queryByLabelText(/Files this run may change/)).not.toBeInTheDocument();

    await fillAndSubmitApprove(user);
    await screen.findByText("Running");
    const api = await import("./api");
    expect(api.approveProposal.mock.calls[0][2].permitted_files).toEqual([
      "runtime/ui/src/App.jsx", "runtime/ui/src/api.js",
    ]);
  });

  it("sends Eric back to conversation instead of a blank technical form when no scope was proposed", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user, { noScope: true });
    await confirmDirectionUI(user);
    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));

    expect(screen.getByText(/hasn't proposed any files or commands/)).toBeInTheDocument();
    await user.type(screen.getByLabelText(/Authorized by/), "Eric");
    await user.click(screen.getByLabelText(/Accept time-only control/));
    await user.click(screen.getByRole("button", { name: "Approve and run" }));

    expect(screen.getByText(/hasn't proposed any files for this yet/)).toBeInTheDocument();
    const api = await import("./api");
    expect(api.approveProposal).not.toHaveBeenCalled();
  });

  it("submits expected_proposal_revision bound to the exact displayed revision, and rejects approving a stale view", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);
    await confirmDirectionUI(user);

    // Something else (another tab) corrects the proposal server-side,
    // without this page's `proposal` prop knowing yet.
    globalThis.__fakeApiState.proposalsById[1].revision = 2;
    globalThis.__fakeApiState.proposalsById[1].confirmed_revision = 1;

    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));
    // The stale-view refresh must refuse to open the approve form.
    await screen.findByText(/changed since it was last shown here/);
    expect(screen.queryByLabelText(/Authorized by/)).not.toBeInTheDocument();
    const api = await import("./api");
    expect(api.approveProposal).not.toHaveBeenCalled();
  });

  it("surfaces a failed correction honestly even though the chat reply itself succeeded (proposal_error)", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);

    const correctionBox = screen.getByPlaceholderText(/Correct this/);
    await user.type(correctionBox, "TRIGGER_PROPOSAL_ERROR");
    await user.click(screen.getByRole("button", { name: "Send correction" }));

    await screen.findByText(/done_when_text too long/);
    expect(screen.getByText("Build a demo page")).toBeInTheDocument();
    expect(screen.getByText(/proposal revision 1/)).toBeInTheDocument();
    expect(correctionBox).toHaveValue("TRIGGER_PROPOSAL_ERROR");
  });

  it("does not send a second model call on retry after a lost response, including across a remount (reload)", async () => {
    let user = await renderAppOnProject();
    const api = await import("./api");
    api.sendMessage.mockResolvedValueOnce({ ok: false, networkError: true, error: "network down" });

    const box = screen.getByPlaceholderText(/Talk to Braingate/);
    await user.type(box, "hello");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(api.sendMessage).toHaveBeenCalledTimes(1));
    const firstRequestId = api.sendMessage.mock.calls[0][2];
    expect(localStorage.getItem("cis-workbench-reqid-send-p1")).toContain(firstRequestId);
    await waitFor(() => expect(box).toHaveValue("hello"));

    // Simulate a real reload: unmount and remount from scratch.
    cleanup();
    user = await renderAppOnProject();
    expect(screen.getByPlaceholderText(/Talk to Braingate/)).toHaveValue("hello");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(api.sendMessage).toHaveBeenCalledTimes(2));
    const secondRequestId = api.sendMessage.mock.calls[1][2];
    expect(secondRequestId).toBe(firstRequestId);
    expect(globalThis.__fakeApiState.modelCallCount).toBe(1);
  });

  it("retrying a lost confirm-direction response reuses the same request_id and calls the generator once", async () => {
    const user = await renderAppOnProject();
    const api = await import("./api");
    await draftProposal(user);
    api.confirmDirection.mockResolvedValueOnce({ ok: false, error: "network down" });

    await user.click(screen.getByRole("button", { name: /^Confirm direction/ }));
    await waitFor(() => expect(api.confirmDirection).toHaveBeenCalledTimes(1));
    const firstId = api.confirmDirection.mock.calls[0][1];

    await user.click(screen.getByRole("button", { name: /^Confirm direction/ }));
    await waitFor(() => expect(api.confirmDirection).toHaveBeenCalledTimes(2));
    expect(api.confirmDirection.mock.calls[1][1]).toBe(firstId);
    expect(globalThis.__fakeApiState.generateCallCount).toBe(1);
  });

  it("retrying a lost approve/dispatch response reuses the same request_id and starts only one run", async () => {
    const user = await renderAppOnProject();
    const api = await import("./api");
    await draftProposal(user);
    await confirmDirectionUI(user);
    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));
    api.approveProposal.mockResolvedValueOnce({ ok: false, error: "network down" });

    await fillAndSubmitApprove(user);
    await waitFor(() => expect(api.approveProposal).toHaveBeenCalledTimes(1));
    const firstId = api.approveProposal.mock.calls[0][1];

    await user.click(screen.getByRole("button", { name: "Approve and run" }));
    await waitFor(() => expect(api.approveProposal).toHaveBeenCalledTimes(2));
    expect(api.approveProposal.mock.calls[1][1]).toBe(firstId);
    expect(globalThis.__fakeApiState.dispatchCallCount).toBe(1);
  });

  it("persists an unsent draft across a reload", async () => {
    const user = await renderAppOnProject();
    const box = screen.getByPlaceholderText(/Talk to Braingate/);
    await user.type(box, "not sent yet");
    expect(localStorage.getItem("cis-workbench-draft-p1")).toBe("not sent yet");

    cleanup();
    await renderAppOnProject();
    expect(screen.getByPlaceholderText(/Talk to Braingate/)).toHaveValue("not sent yet");
  });

  it("shows Stop on an active run and reflects a confirmed stop", async () => {
    const user = await renderAppOnProject();
    await draftProposal(user);
    await confirmDirectionUI(user);
    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));
    await fillAndSubmitApprove(user);

    await screen.findByText("Running");
    const stopBtn = screen.getByRole("button", { name: "Stop" });
    await user.click(stopBtn);

    await screen.findByText("Stopped");
    expect(screen.queryByRole("button", { name: "Stop" })).not.toBeInTheDocument();
  });

  it("closes the loop: implementation -> evidence -> explicit review, and a corrected next action stays approvable alongside the historical run", { timeout: 10000 }, async () => {
    const user = await renderAppOnProject();
    const api = await import("./api");
    await draftProposal(user);
    await confirmDirectionUI(user);
    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));
    await fillAndSubmitApprove(user);
    await screen.findByText("Running");

    // Implementation finishes. Its saved evidence.md (fixture text,
    // deliberately different from final_message) must be what's shown as
    // the run's real content — not final_message, which is shown too but
    // separately labeled. RunPanel discovers the status change via its own
    // status poll (POLL_MS=4000) — waited out for real here rather than
    // mocking timers, since userEvent interactions later in this test need
    // real timers too.
    const state = globalThis.__fakeApiState;
    state.runsById[500].status = "completed";
    state.runsById[500].final_message = "Done.";
    state.artifactsByRun[500] = { "evidence.md": "EVIDENCE: added the button, verified in browser." };
    await screen.findByText("Finished", {}, { timeout: 6000 });
    await screen.findByText("EVIDENCE: added the button, verified in browser.");
    expect(screen.getByText("Done.")).toBeInTheDocument();
    expect(screen.getByText(/CLI's own last-turn text, not the saved evidence file/)).toBeInTheDocument();

    // Explicit, separately authorized review — never automatic. Its own
    // review.md (fixture, distinct from its final_message) must be shown
    // as its content too.
    await user.click(screen.getByRole("button", { name: /Request review of this run/ }));
    // The exact card this run was dispatched against is shown for review
    // context, and the review targets THAT card, not any newer one.
    await screen.findByText(/Card this run was actually dispatched against/);
    expect(api.getCard).toHaveBeenCalledWith(900);
    await user.type(screen.getByLabelText(/Authorized by/), "Eric");
    await user.click(screen.getByLabelText(/Accept time-only control/));
    state.artifactsByRun[501] = { "review.md": "REVIEW: approved, no changes requested." };
    await user.click(screen.getByRole("button", { name: "Dispatch review" }));
    expect(api.dispatchRun.mock.calls[0][0].card_factory_card_id).toBe(900);
    expect(api.dispatchRun.mock.calls[0][0].expected_card_fingerprint).toBe("fp-900");
    await screen.findByText("REVIEW: approved, no changes requested.");

    // A correction + reconfirm must still be approvable, without the
    // historical implement run disappearing or blocking it.
    const correctionBox = screen.getByPlaceholderText(/Correct this/);
    await user.type(correctionBox, "Actually make it two pages");
    await user.click(screen.getByRole("button", { name: "Send correction" }));
    await user.click(screen.getByRole("button", { name: "Confirm direction again" }));

    expect(screen.getByText(/Previous run/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Approve and run…/ })).toBeInTheDocument();
  });

  it("targets a review at the implementation run's own dispatched card, not a newer one shown after a later correction (F5b)", { timeout: 10000 }, async () => {
    const user = await renderAppOnProject();
    const api = await import("./api");
    const state = globalThis.__fakeApiState;
    await draftProposal(user);
    await confirmDirectionUI(user); // card #900
    await user.click(screen.getByRole("button", { name: /Approve and run…/ }));
    await fillAndSubmitApprove(user); // run #500, card_factory_card_id 900
    await screen.findByText("Running");
    state.runsById[500].status = "completed";
    await screen.findByText("Finished", {}, { timeout: 6000 });

    // Correct and reconfirm BEFORE requesting review — this is what
    // produces card #901 as the newly displayed "Generated card", while
    // run #500 still only ever ran against card #900.
    const correctionBox = screen.getByPlaceholderText(/Correct this/);
    await user.type(correctionBox, "Actually make it two pages");
    await user.click(screen.getByRole("button", { name: "Send correction" }));
    await user.click(screen.getByRole("button", { name: "Confirm direction again" }));
    await screen.findByText(/CARD test-card-901/);

    await user.click(screen.getByRole("button", { name: /Request review of this run/ }));
    await user.type(screen.getByLabelText(/Authorized by/), "Eric");
    await user.click(screen.getByLabelText(/Accept time-only control/));
    await user.click(screen.getByRole("button", { name: "Dispatch review" }));

    await waitFor(() => expect(api.dispatchRun).toHaveBeenCalled());
    const sentPayload = api.dispatchRun.mock.calls[0][0];
    expect(sentPayload.card_factory_card_id).toBe(900); // run #500's own card, NOT 901
    expect(sentPayload.expected_card_fingerprint).toBe("fp-900");
    expect(sentPayload.review_of_run_id).toBe(500);
  });

  it("switches to the separate Card Factory view and back without losing the project", async () => {
    const user = await renderAppOnProject();
    await user.click(screen.getByRole("button", { name: /Card Factory/ }));
    await screen.findByText("New request");

    await user.click(screen.getByRole("button", { name: /Back to conversation/ }));
    await screen.findByRole("heading", { name: "Test Project" });
  });
});
