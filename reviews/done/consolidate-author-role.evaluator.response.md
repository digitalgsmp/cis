# Advisor review — consolidate-author-role

- packet: `reviews/pending/consolidate-author-role.md`
- advisor: evaluator on port 8650, no tools
- run tag: consolidate-author-role @ 2026-09-12T10:00:58-05:00
- at: 2026-09-12T10:02:31
- prompt_tokens: 28869
- completion_tokens: 1840
- total_tokens: 30709
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

Eric's intent is explicit ("transfer from host drafter to consolidated brain drafter in the container"), the next pending action is Container Isolation enforcement (ADR-015/016) which requires work inside the container, and the current pipeline team includes both Brainstorm (8644) and Drafter (8645) as separate ports. This consolidation is the prerequisite infrastructure move, timed correctly.

---

**Review — consolidate-author-role**

**Critical gaps:**

1. **Port assignment unspecified.** The proposal says "one port" but doesn't say which one. The current pipeline team has Brainstorm (8644) and Drafter (8645) as separate roles. Consolidating them means the orchestrator/router configuration needs to be updated. Which port does the Author answer on, and what happens to the other?

2. **MCP bridge re-enablement unexplained.** Scope item 2 says re-enable `cis-knowledge` MCP bridge (currently `enabled: false`) but doesn't investigate why it was disabled. Was there a failure mode, security concern, or resource issue that needs to be addressed before re-enabling?

3. **Chat path vague.** Scope item 3 says "Telegram or the 5000 front-door" but doesn't specify which one or the implementation path. The acceptance criteria says "Eric can send a message to the Author and get a reply on a chat path" — but which path? This needs to be concrete.

4. **No migration plan.** What happens to existing Brain/Draft sessions? Are they terminated gracefully? Is there a transition period where both setups coexist? Does the orchestrator need to be reconfigured in the same change, or is this done first with the old profiles still warm?

5. **Acceptance criteria gap on the orchestrator.** The four DONE-WHEN items prove the Author exists and can talk to the spine. But they don't prove the pipeline still works — i.e., that a router/orchestrator run can still route to and receive a response from the consolidated Author. Without that, you've built a working profile that nothing can call.

**Minor gaps:**

6. **Personality spec thin.** "Explore → confirm → draft (cite intent + sources)" is a three-word personality. The existing profiles presumably have full SOUL/personality blocks. Does the merged profile need a new personality document, or does it inherit one and extend it?

7. **No rollback plan.** If the Author profile fails to boot or the MCP bridge misbehaves, how do you get back to the two-profile setup?

**What looks good:**

- The "Why" reasoning is sound — same model, same lineage, no independence value from the split.
- The acceptance criteria are empirically verifiable (curl, sqlite3, INSERT, delivered message).
- Out-of-scope items are correctly scoped (enforcement gates constrain the worker, not the Author).
- The Eric intent quote is verbatim and directly supports the work.

**Verdict:** The proposal is directionally correct and well-timed. It needs a small revision pass to nail down the port choice, chat path decision, orchestrator wiring, and a one-line rollback plan before it's actionable. Those are five minutes of decisions, not a redesign.
