import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// The sign-in gate and its failure modes. App.test.jsx covers the
// authenticated app; this suite covers getting there, being refused, and
// falling back out when a session ends.
//
// The real ./api module is mocked, so nothing here touches fetch or a server.
// Sign-in itself is a full-page navigation to the server's OIDC login route,
// so `beginSignIn` is the seam that stands in for "the browser left for
// Auth0" — there is no password to submit and no login() call to make.
vi.mock("./api", () => {
  function freshState() {
    return {
      sessionAuthenticated: false,
      oidcConfigured: true,
      accountAuthorized: true,
      identity: {
        subject: "auth0|eric",
        email: "eric@example.com",
        name: "Eric Shelton",
        role: "owner",
      },
      csrfToken: null,
      logoutCalls: 0,
      signInRedirects: 0,
      providerLogoutUrl: null,
      projectsUnauthenticated: false,
    };
  }
  const state = freshState();
  globalThis.__authState = state;
  globalThis.__resetAuthState = () => Object.assign(state, freshState());

  const ok = (data) => ({ ok: true, data: JSON.parse(JSON.stringify(data)) });
  const denied = (status, error, detail) => ({
    ok: false, status, error,
    data: { error, detail },
    unauthenticated: status === 401,
    forbidden: status === 403,
    authUnavailable: status === 503,
  });

  return {
    AUTH_LOGIN_URL: "/api/workbench/auth/login",
    getCsrfToken: vi.fn(() => state.csrfToken),
    setCsrfToken: vi.fn((t) => { state.csrfToken = t || null; }),

    beginSignIn: vi.fn(() => { state.signInRedirects += 1; }),

    refreshSession: vi.fn(async () => {
      if (!state.oidcConfigured) {
        return denied(503, "Sign-in is not configured on this server",
                      "CIS_WORKBENCH_OIDC_ISSUER is not set");
      }
      if (!state.accountAuthorized) {
        return denied(403, "This account is not authorized for this Workbench",
                      "This address is no longer on the authorized list.");
      }
      if (!state.sessionAuthenticated) return ok({ authenticated: false });
      state.csrfToken = state.csrfToken || "csrf-from-session";
      return ok({
        authenticated: true,
        csrf_token: state.csrfToken,
        identity: state.identity,
      });
    }),

    logout: vi.fn(async () => {
      state.logoutCalls += 1;
      state.sessionAuthenticated = false;
      state.csrfToken = null;
      return ok({ authenticated: false,
                  provider_logout_url: state.providerLogoutUrl });
    }),

    listProjects: vi.fn(async () => {
      if (state.projectsUnauthenticated || !state.sessionAuthenticated) {
        return denied(401, "Unauthorized", "Invalid or missing credential");
      }
      return ok({ projects: [{ id: "p1", name: "Test Project", direction_note: "" }] });
    }),
    listMessages: vi.fn(async () => ok({ messages: [] })),
    listProposals: vi.fn(async () => ok({ proposals: [] })),
    listRuns: vi.fn(async () => ok({ runs: [] })),
    createProject: vi.fn(async (name) => ok({ project: { id: "p2", name, direction_note: "" } })),
    updateDirectionNote: vi.fn(async (id, note) => ok({ project: { id, name: "T", direction_note: note } })),
    sendMessage: vi.fn(async () => ok({ duplicate: false, user_message: {}, brain_message: {} })),
    getProposal: vi.fn(async () => ok({ proposal: {} })),
    confirmDirection: vi.fn(async () => ok({})),
    approveProposal: vi.fn(async () => ok({})),
    getRunStatus: vi.fn(async () => ok({})),
    stopRun: vi.fn(async () => ok({})),
    getRunArtifact: vi.fn(async () => ok({})),
    editProposal: vi.fn(async () => ok({})),
    submitAsk: vi.fn(async () => ok({})),
    generateCard: vi.fn(async () => ok({})),
    listCards: vi.fn(async () => ok({ cards: [] })),
    getCard: vi.fn(async () => ok({})),
    editCard: vi.fn(async () => ok({})),
    regateCard: vi.fn(async () => ok({})),
    getAsk: vi.fn(async () => ok({})),
    editAsk: vi.fn(async () => ok({})),
    getSystemContext: vi.fn(async () => ok({})),
    getRecoveryPacket: vi.fn(async () => ok({})),
    getLedger: vi.fn(async () => ok({})),
  };
});

import App from "./App";
import * as api from "./api";

const signInButton = () => screen.getByRole("button", { name: /Continue to Sign In/i });

describe("workbench OIDC sign-in", () => {
  beforeEach(() => {
    cleanup();
    localStorage.clear();
    sessionStorage.clear();
    globalThis.__resetAuthState();
    vi.clearAllMocks();
  });

  afterEach(() => cleanup());

  it("shows the sign-in gate when there is no session, and fetches no workbench data", async () => {
    render(<App />);
    await waitFor(() => expect(signInButton()).toBeInTheDocument());
    expect(screen.queryByPlaceholderText(/Talk to Braingate/)).not.toBeInTheDocument();
    // The gate is not cosmetic: nothing was requested on the strength of an
    // assumption that the user is signed in.
    expect(api.listProjects).not.toHaveBeenCalled();
  });

  it("has no password field anywhere in the signed-out UI", async () => {
    const { container } = render(<App />);
    await waitFor(() => expect(signInButton()).toBeInTheDocument());
    // The architectural claim, asserted rather than described: CIS never
    // receives a password, so there is nothing to type one into.
    expect(container.querySelector('input[type="password"]')).toBeNull();
    expect(container.querySelectorAll("input")).toHaveLength(0);
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Workbench password/i)).not.toBeInTheDocument();
  });

  it("says plainly that the password never reaches CIS", async () => {
    render(<App />);
    await waitFor(() => expect(signInButton()).toBeInTheDocument());
    expect(screen.getByText(/password is never sent to\s+CIS/i)).toBeInTheDocument();
  });

  it("starts the OIDC redirect when Sign In is pressed", async () => {
    const user = userEvent.setup();
    render(<App />);
    await waitFor(() => expect(signInButton()).toBeInTheDocument());

    await user.click(signInButton());

    expect(api.beginSignIn).toHaveBeenCalledTimes(1);
    expect(globalThis.__authState.signInRedirects).toBe(1);
    // It is a redirect, not a credential submission — nothing was posted.
    expect(api.listProjects).not.toHaveBeenCalled();
  });

  it("points the sign-in redirect at the server's OIDC login route", () => {
    expect(api.AUTH_LOGIN_URL).toBe("/api/workbench/auth/login");
  });

  it("shows the workbench, the signed-in identity and the owner role", async () => {
    globalThis.__authState.sessionAuthenticated = true;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());

    expect(screen.getByText(/Eric Shelton — Owner/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign out/i })).toBeInTheDocument();
    expect(api.listProjects).toHaveBeenCalled();
  });

  it("shows a collaborator as a collaborator", async () => {
    globalThis.__authState.sessionAuthenticated = true;
    globalThis.__authState.identity = {
      subject: "google-oauth2|1", email: "collaborator@example.com",
      name: "", role: "collaborator",
    };
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());
    // With no display name the address stands in — the user still knows who
    // this browser is acting as.
    expect(screen.getByText(/collaborator@example\.com — Collaborator/)).toBeInTheDocument();
  });

  it("never exposes a token or secret in the signed-in UI", async () => {
    globalThis.__authState.sessionAuthenticated = true;
    const { container } = render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());
    const rendered = container.innerHTML;
    expect(rendered).not.toContain("csrf-from-session");
    expect(rendered).not.toMatch(/eyJ/);           // no JWT of any kind
    expect(rendered).not.toMatch(/client_secret/i);
    expect(rendered).not.toMatch(/api[_-]?key/i);
  });

  it("reports a 403 unauthorized account distinctly from being signed out", async () => {
    globalThis.__authState.accountAuthorized = false;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText(/not authorized for this Workbench/i)).toBeInTheDocument());
    // The difference that matters to the user: signing in again will not help,
    // asking for access will.
    expect(screen.getByText(/Ask the owner to add your address/i)).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Talk to Braingate/)).not.toBeInTheDocument();
    expect(api.listProjects).not.toHaveBeenCalled();
  });

  it("offers a different account after a 403 rather than a dead end", async () => {
    const user = userEvent.setup();
    globalThis.__authState.accountAuthorized = false;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText(/not authorized for this Workbench/i)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Try a different account/i }));
    expect(api.beginSignIn).toHaveBeenCalledTimes(1);
  });

  it("reports 503 sign-in-not-configured, and offers no sign-in button", async () => {
    globalThis.__authState.oidcConfigured = false;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByText(/not configured on this server/i)).toBeInTheDocument());
    // Retrying would be pointless, so the page does not invite it.
    expect(screen.queryByRole("button", { name: /Continue to Sign In/i })).not.toBeInTheDocument();
    expect(screen.getByText(/CIS_WORKBENCH_OIDC_ISSUER/)).toBeInTheDocument();
  });

  it("returns to the sign-in gate when a session expires mid-use", async () => {
    const user = userEvent.setup();
    globalThis.__authState.sessionAuthenticated = true;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());

    globalThis.__authState.projectsUnauthenticated = true;
    await user.click(screen.getByRole("button", { name: /Sign out/i }));

    await waitFor(() => expect(signInButton()).toBeInTheDocument());
    // There is no stored credential, so nothing could sign back in by itself
    // even if it wanted to.
    expect(screen.queryByPlaceholderText(/Talk to Braingate/)).not.toBeInTheDocument();
  });

  it("signs out, clears the session and the CSRF token, and hides the workbench", async () => {
    const user = userEvent.setup();
    globalThis.__authState.sessionAuthenticated = true;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /Sign out/i }));

    await waitFor(() => expect(screen.getByText(/signed out of the Workbench/i))
      .toBeInTheDocument());
    expect(globalThis.__authState.logoutCalls).toBe(1);
    expect(globalThis.__authState.sessionAuthenticated).toBe(false);
    expect(globalThis.__authState.csrfToken).toBeNull();
    expect(screen.queryByPlaceholderText(/Talk to Braingate/)).not.toBeInTheDocument();
  });

  it("offers the provider sign-out as a link, and never follows it automatically", async () => {
    const user = userEvent.setup();
    globalThis.__authState.sessionAuthenticated = true;
    globalThis.__authState.providerLogoutUrl =
      "https://tenant.example.auth0.com/oidc/logout?client_id=abc";
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /Sign out/i }));

    const link = await screen.findByRole("link", { name: /Also sign out of the identity provider/i });
    expect(link).toHaveAttribute("href",
      "https://tenant.example.auth0.com/oidc/logout?client_id=abc");
    // Still on the CIS signed-out page: nothing navigated on the user's behalf.
    expect(screen.getByText(/signed out of the Workbench/i)).toBeInTheDocument();
  });

  it("does not offer a provider sign-out link when the provider advertises none", async () => {
    const user = userEvent.setup();
    globalThis.__authState.sessionAuthenticated = true;
    globalThis.__authState.providerLogoutUrl = null;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Sign out/i }));
    await waitFor(() => expect(screen.getByText(/signed out of the Workbench/i))
      .toBeInTheDocument());
    expect(screen.queryByRole("link", { name: /identity provider/i })).not.toBeInTheDocument();
  });

  it("restores an existing session on reload without any sign-in step", async () => {
    globalThis.__authState.sessionAuthenticated = true;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());
    expect(api.beginSignIn).not.toHaveBeenCalled();
    expect(api.refreshSession).toHaveBeenCalled();
  });

  it("stores no credential in localStorage or sessionStorage", async () => {
    globalThis.__authState.sessionAuthenticated = true;
    render(<App />);
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Talk to Braingate/)).toBeInTheDocument());

    const dumped = JSON.stringify({
      local: { ...localStorage },
      session: { ...sessionStorage },
    });
    // The CSRF token lives in module memory only, and there is no password,
    // no ID token and no API key in this bundle to store in the first place.
    expect(dumped).not.toContain("csrf-from-session");
    expect(dumped).not.toMatch(/password/i);
    expect(dumped).not.toMatch(/token/i);
    expect(dumped).not.toMatch(/secret/i);
  });
});
