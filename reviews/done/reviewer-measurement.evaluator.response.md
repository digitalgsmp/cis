# Advisor review — reviewer-measurement

- packet: `reviews/pending/reviewer-measurement.md`
- advisor: evaluator on port 8650, no tools
- run tag: reviewer-measurement @ 2026-09-10T15:40:52-05:00
- at: 2026-09-10T15:42:08
- prompt_tokens: 1916
- completion_tokens: 1699
- total_tokens: 3615
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK
The advisory review previously failed due to an inability to measure the system and a lack of independent reconciliation; this card directly addresses both root causes by defining specific read-shaped measurement instruments and a strict two-round cross-feed protocol, while correctly deferring mutation isolation to a separate card to maintain a tight scope.

Review of the proposal packet:

The card is exceptionally well-structured and highly testable. The distinction between read-shaped measurement and generic shell access is a strong architectural constraint that will prevent scope creep and security leaks. The separation of concerns between this card and the isolation card is clean and logical.

The evidence section is particularly strong. Using a nonce read to prove the reviewer is actually interacting with the live environment rather than hallucinating or recycling old data is an excellent probe. The seeded-disagreement fixture is also a vital addition to ensure the reconciliation step does not just collapse into sycophantic consensus.

There are a few minor gaps to consider before implementation:

First, the handling of lineage failure or timeout is not explicitly defined in the build or protocol steps. While the pass conditions state that a missing lineage is a fail, the harness needs defined behavior for when one lineage crashes or times out during round one. Specify whether the harness aborts the entire run immediately or waits for a timeout threshold before marking it as a fail.

Second, the canonical input distribution could be tightened. The provenance section requires an input hash, but the protocol just says they receive the same canonical input. Explicitly state that the harness must hash the canonical input prior to distribution and that both lineages must acknowledge receipt of that specific hash to prevent subtle input-divergence bugs.

Third, the interface contract for the mediated reviewer surface is assumed but not detailed. If the reviewer interacts via tool calls or structured API requests, the schema for those requests and responses should be referenced or defined in a parent document to ensure the read-shaped constraint is enforceable at the interface level.

Overall, this is a rigorous and actionable proposal that correctly targets the stated failure modes.
