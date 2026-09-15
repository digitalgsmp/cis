# Advisor review — claude-code-submit-loop

- packet: `reviews/pending/claude-code-submit-loop.md`
- advisor: advisor on port 8649, no tools
- run tag: claude-code-submit-loop @ 2026-09-11T14:26:59-05:00
- at: 2026-09-11T14:27:21
- prompt_tokens: 6710
- completion_tokens: 666
- total_tokens: 7376
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK. The intent is verbatim from Eric, the gap is real (no single submit path exists despite the reviewer rounds being proven yesterday), every dependency is marked proven and reused as-is, and the scope is narrowly locked to orchestration glue — it does not rebuild the review logic, the pause mechanism, or the read-only MCP. This is the natural next step: the pieces were validated 2026-09-10 and the missing piece is exactly the wiring Eric asked for. No prerequisites are unproven, no scope is overreached, and the "NOT IN THIS CARD" section correctly fences off the things that would make this the wrong card (rebuilding enforcement, adding mid-execution interception, changing the process model).

Now the review of what follows:

THE CARD IS WELL-CONSTRUCTED. Here is what it gets right and where it could fail.

WHAT IT GETS RIGHT:

1. Intent is verbatim and the problem statement traces the exact failure mode Eric named ("unreliable because the reviewers did not work") to a concrete gap: Claude Code execution is not wired to the reviewer gate. That is the right diagnosis.

2. Scope lock is tight. "SUBMIT-TO-CLAUDE-CODE ORCHESTRATION ONLY" plus the explicit "NOT IN THIS CARD" section prevents scope creep into rebuilding advisor_review.sh, the pause rows, or the enforcement walls. The implementer guidance ("If you find yourself rewriting advisor_review.sh, you are off-card") is the right tripwire.

3. The evidence-anchored hold requirement (DONE WHEN #3) directly answers Eric's rejection of "hard stops without evidence." A block that names no objection and no evidence is a failure of the card itself — that is the right invariant.

4. Round 2 letting the reviewer verify via read-only MCP rather than trusting pasted output (DONE WHEN #5, CLARITY section) closes the trust gap that would make the reviewer toothless.

5. Pauses preserved as durable rows, not blocked processes (EVIDENCE: "Pause proof"). This is the right design — the orchestrator stops and waits, it does not hold a process open.

6. Idempotency (DONE WHEN #8) prevents the obvious failure mode of re-running and duplicating rounds.

WHERE IT COULD FAIL — RISKS TO FLAG BEFORE BUILDING:

RISK 1 — Round 2 loop termination. The card says "Repeat per objection until the reviewer rules WITHDRAWN or HELD for each." If Claude Code produces evidence that the reviewer neither withdraws nor holds (e.g., it rules PARTIALLY_VERIFIED or requests more evidence without a HELD ruling), the loop could spin indefinitely. The card should specify a max-retry or a terminal state for the round-2 loop per objection. As written, WITHDRAWN and HELD are the only two exit states, but the advisor_review.sh --reply contract should be confirmed to only produce those two. If it can produce a third state, the orchestrator needs a rule for it.

RISK 2 — What "objection is outstanding" means in step 4 vs step 6. Step 4 says "If any objection is outstanding" and runs round 2. Step 6 says "If any objection remains HELD" and blocks. The gap between these two is: objections that are neither WITHDRAWN nor HELD after round 2. The orchestrator needs an explicit rule: an objection that is not WITHDRAWN after round 2 is treated as HELD (fail-safe), or the card must state that --reply only ever returns WITHDRAWN or HELD. Without this, there is a state where execution neither proceeds nor blocks — a stuck orchestrator.

RISK 3 — The card handed to Claude Code in step 7. DONE WHEN #4 says "the post-review card (objections resolved or withdrawn), not the raw draft." The orchestrator needs to know which file is the post-review card. If the review rounds mutate the packet in place, that is fine. If they produce a separate artifact (a reconciled/cleared packet), the orchestrator must pass the right path to `claude -p`. The card should name the path convention for the cleared card that Claude Code receives.

RISK 4 — Execution output capture for round 3. The card says "capturing full command output + diff" and "its output must be captured to a file for round 3." It should name the output path convention (e.g., `reviews/pending/<id>.execution.<timestamp>.output` or similar) so the --result call has a deterministic path. As written, the implementer could capture to an ad-hoc path and break the hash-bound artifact chain.

RISK 5 — The HELD path evidence requirement. The EVIDENCE section requires demonstrating a HELD path where "Claude Code cannot resolve" the objection. But if the reviewer rules HELD, step 6 refuses to execute — meaning Claude Code never runs in the HELD path. So the HELD path evidenceis just the refusal message plus the round-2 reply showing the HELD verdict. That is sufficient and correct — but the card should clarify that the HELD path does not produce an execution artifact by design, so the evidence reviewer does not mistake its absence for a gap. The EVIDENCE section already says "Show the refusal and that no execution artifact was produced," which is the right framing, but it should also say the absence is expected, not a missing artifact.

RISK 6 — Dual-lineage in round 2. The CLARITY section says "every round runs against both advisor (GLM, 8649) and evaluator (Qwen, 8650), same packet, same hash." But the round-2 --reply flow is described as a single Claude Code invocation producing evidence that goes to "the reviewer" (singular). The orchestrator must hand Claude Code's evidence to BOTH lineages independently, get BOTH verdicts, and treat the objection as cleared only when BOTH rule WITHDRAWN. If only one lineage withdraws and the other holds, the objection is still HELD. The card should make this dual-verdict rule explicit for round 2 — right now it reads as if one reviewer suffices.

RISK 7 — Idempotency detection mechanism. DONE WHEN #8 says "it detects which step the card is at and resumes there." The card should name what state the orchestrator reads to detect the current step — presumably the deliberation_rounds pause rows (card-written, reviews-landed, result-reviewed) or a state file. If the detection mechanism is not specified, two implementers could build two different resume strategies, and one could be wrong. A one-line pointer to the existing pause row as the source of truth for step detection would close this.

MINOR NOTES:

- The DEPENDS_ON list is thorough and cites the proven date (2026-09-10). Good.
- The CANONICAL_TOKEN is well-formed and versioned.
- The "NOT IN THIS CARD" section is the best part of this card — it is what keeps it from being the wrong card.
- The evidence pass conditions are measurable and falsifiable. A block that names no objection is a failure. A round-2 verdict that silently trusts is a failure. These are testable, not aspirational.

VERDICT: This is the right work at the right time. The card is ready to build after the six risks above are addressed — specifically: (1) round-2 loop termination states, (2) the outstanding-vs-HELD gap in steps 4/6, (3) the cleared-card path convention, (4) the execution output path convention, (6) dual-lineage verdict rule for round 2, and (7) the idempotency detection source. Risks 5 is a clarification, not a blocker. None of these are design changes to the card's intent — they are specification gaps the implementer would otherwise guess at, and guessing wrong would break the evidence-anchored hold invariant that is the whole point of this card.
