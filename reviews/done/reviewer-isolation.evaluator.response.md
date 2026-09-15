# Advisor review — reviewer-isolation

- packet: `reviews/pending/reviewer-isolation.md`
- advisor: evaluator on port 8650, no tools
- run tag: reviewer-isolation @ 2026-09-10T15:42:12-05:00
- at: 2026-09-10T15:43:08
- prompt_tokens: 1848
- completion_tokens: 2193
- total_tokens: 4041
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK
Establishing hard process and filesystem boundaries for reviewer agents is the correct foundational step before implementing measurement or reconciliation logic. Without guaranteed isolation at the OS or container level, any reviewer output is inherently untrustworthy because the reviewer could mutate the system it is supposed to be evaluating, making this the exact right prerequisite for the broader contained pipeline architecture.

The proposal is exceptionally well-scoped and correctly identifies the failure mode of relying on prompt-level instructions for AI agent containment. By explicitly rejecting command blacklists and demanding OS-level enforcement, the card avoids the most common pitfall in agent sandboxing.

The required properties cover all necessary attack surfaces for a reviewer agent. Filesystem read-only mounts, non-root execution, dispatch prevention, and network egress restriction form a complete boundary. The explicit requirement that the harness handles output persistence is a strong design choice that prevents the reviewer from having any write path to protected storage.

The done when criteria and evidence sections are rigorous. Demanding negative probes that result in OS denials rather than polite model refusals ensures the implementer cannot cheat by relying on the model system prompt. Requiring the same probes for both the advisor and evaluator roles prevents asymmetric security gaps.

One minor area for the implementer to watch is the network boundary exception for model transport. The card correctly states this must be narrow, but in practice, proxying model API calls through a controlled harness endpoint rather than giving the reviewer container direct egress to the model provider would be the safest way to satisfy this requirement without risking a general egress path.

The separation of concerns with the companion measurement card is clean. This card builds the walls and the next card will install the cameras. The proposal is ready for implementation.
