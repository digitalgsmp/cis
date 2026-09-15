# Advisor review — agent-claims-audit

- packet: `reviews/pending/agent-claims-audit.md`
- advisor: advisor on port 8649, no tools
- run tag: agent-claims-audit @ 2026-09-12T08:22:04-05:00
- at: 2026-09-12T08:23:09
- prompt_tokens: 5464
- completion_tokens: 4335
- total_tokens: 9799
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

VERDICT: NOT_ESTABLISHED

The evidence establishes some claims but not the card as a whole. C3 is proven: the tally shows 9 of 26 verdicts are negative (7 NOT_ESTABLISHED, 1 WITHDRAWN, 1 CANNOT_TELL), and the sample in section 6 is a detailed, genuine rejection with specific reasoning — that is not rubber-stamping. C2 is strongly supported: the three verdict families (FRAME, WITHDRAWN, ESTABLISHED/NOT_ESTABLISHED) all appear in the tally, meaning all three rounds produce output. G1 is confirmed: the port scan shows only 8648, 8649, 8650 listening, and 8643–8647 are dead.

What is NOT established: C1 says the reviewers are "stripped to no tools," but C4 says they "hold read-only measurement instruments." These contradict. The evidence (commits "un-blind reviewers: read-only measurement instruments," "reviewer read instruments") supports C4, not C1's "no tools." C1 also claims both reviewers "receive the same hashed packet" — nothing in the evidence proves packet identity. I see two lineages configured, but no artifact shows they were fed identical input. C5 has commits and configuration strings ("reconcile = --reconcile," "pause = --pause") but no runtime proof: no delivered Telegram message is shown, and no artifact demonstrates one reviewer's round-1 finding appearing in the other's round-2 input. Finally, the sample review itself admits "the proposal step has never actually run," meaning the loop has never completed end to end.

What would look like success while still being wrong: ports are up, three verdict types appear in the tally, the rounds are configured — the system looks alive. But if the two reviewers receive different packets, the independence guarantee is silently broken. If reconciliation is wired in code but never actually feeds across at runtime, the cross-check is theatrical. If Telegram is configured but never delivers, the operator is blind to pauses. And if the proposal step never runs, the operator never gets a short list — the entire system performs review-shaped activity that never produces its final deliverable. Everything looks like it is working except the one thing it exists to do.

---

SLATE

WANTED: The system should judge whether work actually does what was claimed, and then hand me a short list of what to do next. [build-list item not identifiable from this evidence — the card's own reviewer found this step has never run]
WORKS TODAY: No — the judging works (it catches incomplete work and says so honestly), but the step that turns those judgments into a ranked short list for me has never run even once.
NEEDED: Build or fix the step that takes the review verdicts and produces a ranked short list of next actions, then run it once with real input so I can see it hand me a list.

WANTED: The whole system should run inside its own sealed container so it is self-contained and I do not depend on the host machine.
WORKS TODAY: No — only 3 of the 8 roles are alive inside the container; the other 5 are dead and not listening.
NEEDED: Start up the 5 missing roles inside the container and confirm each one stays up and answers on its port.

WANTED: The system should tell me when it pauses and why, through a message I actually receive on my phone.
WORKS TODAY: Partly — the code to send these messages exists and the pause points are configured, but nothing in the evidence shows a message ever actually arrived on a phone.
NEEDED: Trigger a real pause, confirm the message reaches me, and save the delivered message as proof — then I know the notification path works end to end, not just on paper.

WANTED: The two reviewers should see each other's first-round findings before giving their second-round verdict, so neither one decides in a bubble.
WORKS TODAY: Partly — the wiring exists in the code, but no review artifact in the evidence shows one reviewer's first-round finding actually appearing in the other's second round.
NEEDED: Run a review where both reviewers are active, then check that each second-round verdict references or acknowledges the other's first-round finding — if it does not, the cross-feed is dead at runtime.

WANTED: Both reviewers should receive the exact same evidence packet so their verdicts are genuinely independent checks of the same thing.
WORKS TODAY: Cannot tell — the two reviewers are both running, but nothing in the evidence proves they were handed identical input.
NEEDED: Log or display the packet each reviewer receives for one real review and confirm they match — if they differ, the independence guarantee is broken and one reviewer may be judging different evidence than the other.
