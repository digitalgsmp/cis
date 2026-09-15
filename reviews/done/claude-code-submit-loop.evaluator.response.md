# Advisor review — claude-code-submit-loop

- packet: `reviews/pending/claude-code-submit-loop.md`
- advisor: evaluator on port 8650, no tools
- run tag: claude-code-submit-loop @ 2026-09-11T14:26:59-05:00
- at: 2026-09-11T14:29:20
- prompt_tokens: 6176
- completion_tokens: 1217
- total_tokens: 7393
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

Eric explicitly asked for "one command to submit a card to Claude Code" with reviewers constraining it. The reviewer primitives are proven working. This card is pure orchestration glue wiring them together — exactly the missing piece Eric identified. No scope creep, no rebuild of working parts.

---

REVIEW:

STRENGTHS:
- Evidence-anchored hold is correct: the reviewer's HELD ruling already names objection + missing evidence, so no new mechanism needed.
- Idempotency requirement is right.
- Dual-lineage preserved.
- All three pauses preserved, no auto-continue.
- Round 3 after execution is right (verify-after).

GAPS / QUESTIONS:

1. **State detection for idempotency** — The card says "detects which step the card is at and resumes there" but does not specify how. Is there a status field in the packet? A row in `deliberation_rounds`? The implementer needs to know what to check.

2. **Claude Code evidence file for round 2** — Round 2 invokes Claude Code with an objection, collects its evidence, hands to reviewer via `--reply <evidence-file>`. How does Claude Code produce that file? Does it write to a known path? Does the orchestrator parse its stdout? The card says "collect its evidence" but does not say how.

3. **Reviewer MCP turns in round 2** — The card says "Round 2 must actually let it use those instruments, not collapse back to single-turn." But `advisor_review.sh --reply` is a single invocation. How does the reviewer get multiple turns to use MCP? Does the script loop internally? Does the orchestrator manage a session? This is not specified.

4. **What if Claude Code fails or times out in round 2?** — No fallback. Does the orchestrator retry? Does it mark the objection as unresolved and block?

5. **"Cleared card" for Claude Code execution** — The card says Claude Code receives the post-review card, not the raw draft. But where does that cleared card live? Is it written to a new file? Is it the original with objections marked WITHDRAWN?

These are implementable questions, not design flaws. The card is sound.
