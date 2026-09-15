CARD_ID: CARD-claude-code-submit-loop
VERSION: 1.0
CANONICAL_TOKEN: CCSL-V1-20260911-A
STATUS: DRAFT_FOR_ADVERSARIAL_REVIEW
DEPENDS_ON: tools/advisor_review.sh (rounds 1/2/3 + reconcile + resolve + pause, all proven working 2026-09-10); read-only reviewer MCP (CIS_MCP_MODE=readonly, advisor 8649 / evaluator 8650); CARD-reviewer-isolation; CARD-reviewer-measurement
SCOPE_LOCK: SUBMIT-TO-CLAUDE-CODE ORCHESTRATION ONLY

# CARD-claude-code-submit-loop
Give Eric one command to submit a card to Claude Code, with the advisor+evaluator reviewers constraining Claude Code from acting out of alignment — evidence-anchored, not a blind hard stop.

## INTENT (verbatim, from Eric)
"claude code [was] unreliable because the reviewers did not work. chatgtp recommended hard stops without evidence. so now I need to be able to submit a card to claude code and have it constrained by the reviewers from acting out of alignment."

## PROBLEM
The reviewer-constraint loop is proven working as a set of discrete tools: `tools/advisor_review.sh` runs round 1 (proposal review), `--reconcile` (cross-feed), `--reply` (Claude Code answers an objection with evidence, reviewer rules WITHDRAWN/HELD), `--result` (post-execution review, ESTABLISHED/NOT_ESTABLISHED + slate), and `--pause/--continue` (three hard stops: card-written, reviews-landed, result-reviewed). The reviewers now carry read-only MCP and can independently verify evidence (proven 2026-09-10 in the `--resolve` run, which cited exact file/line).

What does NOT exist is the single submit path Eric asked for. Today the sequence is manual: Eric writes the packet, invokes each round by hand, runs Claude Code by hand, and pastes its output back. The Claude Code execution step is not wired to the reviewer gate at all — nothing prevents Claude Code from being run against an unreviewed card. That is the "unreliable because the reviewers did not work" failure: the reviewers were not in the loop in front of Claude Code.

The missing piece is an orchestrator that makes "submit a card" one command and puts the proven reviewer gate directly in front of Claude Code execution, so Claude Code cannot act out of alignment because it only ever runs a card the reviewers have cleared.

## BUILD
Create a single submit entry point (a script, e.g. `tools/submit_card.sh <card-id>`) that drives the existing loop in order and inserts the Claude Code execution step behind the reviewer gate.

The sequence it drives, in order:
1. Verify the card packet exists at `reviews/pending/<id>.md`.
2. Round 1 — both lineages review the packet (`advisor_review.sh <id>`). Stop at `card-written` already set by the drafter; do not auto-continue.
3. Reconcile — cross-feed the two round-1 findings (`advisor_review.sh <id> --reconcile`).
4. If any objection is outstanding: round 2 — invoke Claude Code (headless, `claude -p`) with the objection, collect its evidence, and hand that evidence to the reviewer (`advisor_review.sh <id> --reply <evidence-file>`). Repeat per objection until the reviewer rules WITHDRAWN or HELD for each.
5. Stop at `reviews-landed` — execution does NOT proceed until Eric `--continue`.
6. If any objection remains HELD, the submit path refuses to execute and reports which objection is blocking and what evidence would release it. No blind stop — the block names the objection and the missing evidence.
7. On `--continue`: execute the card via Claude Code (headless), capturing full command output + diff.
8. Round 3 — result review (`advisor_review.sh <id> --result <output-file>`), ruling ESTABLISHED/NOT_ESTABLISHED and writing the plain-language slate.
9. Stop at `result-reviewed` — do not advance to the next item until Eric `--continue`.

The orchestrator must not rewrite the review logic. It calls `advisor_review.sh` and the existing pause rows as-is. It adds exactly two things: the wiring of Claude Code execution behind the gate, and the single-command surface.

## DONE WHEN
1. ONE COMMAND — `tools/submit_card.sh <id>` (or equivalent) takes an existing card packet and drives the full sequence above without Eric hand-running each round.

2. REVIEW GATE IN FRONT OF EXECUTION — Claude Code does not execute while any objection is HELD. A HELD objection blocks the execution step; the block reports which objection and what evidence would release it (not a blanket "paused").

3. EVIDENCE-ANCHORED HOLD — the hold is always tied to a specific objection plus the evidence Claude Code must produce to release it. A stop with no named objection and no named evidence is a failure of this card (this is the anti-"hard stop without evidence" requirement, verbatim from Eric's intent).

4. CLAUDE CODE RECEIVES THE CLEARED CARD — the card handed to Claude Code is the post-review card (objections resolved or withdrawn), not the raw draft.

5. ROUND 2 LETS THE REVIEWER VERIFY, NOT TRUST — in round 2 the reviewer may use its read-only MCP to independently check Claude Code's evidence (read the file, run the read-only query, compare the hash) before ruling WITHDRAWN/HELD. It must not be forced to trust pasted output.

6. PAUSES PRESERVED — all three stops (card-written, reviews-landed, result-reviewed) still require Eric's `--continue`. The orchestrator never auto-continues and never times out a stop.

7. RESULT REVIEW RUNS — after execution, round 3 runs and records ESTABLISHED/NOT_ESTABLISHED plus the slate for both lineages.

8. IDEMPOTENT — re-running the submit command does not duplicate review rounds or create a second execution; it detects which step the card is at and resumes there.

## EVIDENCE
Produce a repeatable end-to-end run on a real (or throwaway) card, captured as artifacts + raw output:

- **WITHDRAWN path:** a card with one objection where Claude Code's evidence resolves it → reviewer rules WITHDRAWN, execution proceeds, round 3 runs. Show the round-2 reply artifact with the WITHDRAWN verdict and the evidence that produced it.
- **HELD path:** a card with an objection Claude Code cannot resolve → reviewer rules HELD → the submit path refuses to execute and reports the blocking objection + missing evidence. Show the refusal and that no execution artifact was produced.
- **Independently-verified evidence:** at least one round-2 verdict where the reviewer cites a file/query/hash it checked itself via read-only MCP, not Claude Code's pasted output.
- **Pause proof:** an execution attempt while a stop is unresolved is refused; the pause is a durable row in `deliberation_rounds`, not a blocked process.
- **Full-artifact chain:** round-1 responses (both lineages), reconcile artifact, round-2 reply, the Claude Code execution output + diff, and the round-3 result — for the same card, all present and hash-bound to the packet.

Pass condition:
- Both WITHDRAWN and HELD paths are demonstrated.
- A "block" that names no objection and no evidence is a failure.
- A round-2 verdict that could not have verified (no read-only instrument used, or pasted output only) is acceptable only when the reviewer states it could not reach the evidence and says what is missing — never when it silently trusts.

## NOT IN THIS CARD
This card does not rebuild the review logic (`advisor_review.sh`), the reconcile/resolve rounds, the pause mechanism, or the read-only reviewer MCP. All of those are proven and reused as-is.

This card does not change the enforcement primitive (ADR-SEED-015/016, three-layer process isolation) or the Docker enforcement walls. It only wires the existing reviewer gate in front of the existing Claude Code execution.

This card does not add real-time per-action interception of Claude Code during execution. The constraint here is gate-before + verify-after: Claude Code runs only a cleared card, and its result is reviewed. Continuous mid-execution interception is a separate, later question.

## CLARITY FOR THE IMPLEMENTER
- The orchestrator is glue, not new logic. If you find yourself rewriting `advisor_review.sh`, you are off-card.
- Claude Code is invoked headless (`claude -p`). Its output must be captured to a file for round 3, not relied on as a self-report.
- The hold must name the objection and the evidence that releases it. A named hold with evidence is the constraint; a nameless stop is the ChatGPT failure Eric rejected.
- Do not auto-continue any pause. Eric is the conductor; the orchestrator stops and waits.
- The reviewer's read-only MCP is already configured (`CIS_MCP_MODE=readonly`, `max_turns: 90`). Round 2 must actually let it use those instruments, not collapse back to single-turn.
- Preserve the dual-lineage property: every round runs against both advisor (GLM, 8649) and evaluator (Qwen, 8650), same packet, same hash.
