# Advisor review — frame-gate-slate

- packet: `reviews/pending/frame-gate-slate.md`
- advisor: evaluator on port 8650, no tools
- run tag: frame-gate-slate @ 2026-09-09T19:58:41-05:00
- at: 2026-09-09T20:00:15
- prompt_tokens: 2926
- completion_tokens: 1790
- total_tokens: 4716
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

The card's reasoning is sound and this is the right work to do first. Both lineages converged on it independently, it's minimal (one file, three string constants), and it creates the feedback mechanism the loop needs to self-correct. The degraded-by-design approach is correct — you can't design the slate format before you see what the first slates produce.

What this card fails to establish:

Whether the frame gate actually changes reviewer behavior beyond the first round. Check 5 tests one round, but a gate that works on card N and gets treated as boilerplate on cards N+1 through N+10 has failed in a way the verification doesn't catch. The card assumes positional primacy (first in the prompt) guarantees attention, but models easily learn to dismiss preamble as boilerplate over repeated invocations. It also fails to establish a baseline for evaluating slate quality, meaning early slates might be too noisy to reliably surface the missing infrastructure they are supposed to reveal.

What would look like success while still being wrong is a reviewer that satisfies the frame gate with a verbose, agreeable paragraph confirming the work is correct, burning tokens without actually applying critical pressure. For the slate, false success is a beautifully formatted, highly confident list of items that are already in the queue and perfectly ordered by tier. It looks like a successful slate because it is comprehensive and ranked, but it is wrong because it merely regurgitates the existing list instead of surfacing the unlisted structural work the loop actually needs.

To the scope line question, yes, this is the right work to do first. It builds the minimum viable feedback mechanism without premature optimization, letting the loop's own failures dictate the next build.
