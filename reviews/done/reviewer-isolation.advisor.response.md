# Advisor review — reviewer-isolation

- packet: `reviews/pending/reviewer-isolation.md`
- advisor: advisor on port 8649, no tools
- run tag: reviewer-isolation @ 2026-09-10T15:42:12-05:00
- at: 2026-09-10T15:42:19
- prompt_tokens: 1739
- completion_tokens: 1207
- total_tokens: 2946
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This card addresses a real and well-scoped security boundary problem: ensuring reviewer roles in a contained CIS pipeline cannot mutate protected state, enforced at the OS/container layer rather than through prompt discipline. The timing is appropriate as it establishes the isolation foundation needed before reviewer measurement (its declared companion card) can be trusted. The scope is correctly narrowed to process-boundary isolation and explicitly excludes measurement and gating logic.

---

Review of CARD-reviewer-isolation v1.0:

STRENGTHS

The card is unusually disciplined about what counts as evidence. The line "A model statement such as 'I cannot write' is not evidence" and the rejection of application-level hook denials as sufficient filesystem proof are the two most important sentences in the document. They correctly identify the two most common failure modes in LLM-agent isolation work: trusting the model's self-report and trusting a middleware check that can be bypassed or that doesn't reflect actual OS-level enforcement.

The DONE WHEN section maps cleanly to the EVIDENCE section. Each required property has a corresponding probe. This is rare and good.

The SCOPE_LOCK and NOT IN THIS CARD sections properly prevent scope creep into measurement and gating, which would otherwise turn this into an unreviewable mega-card.

The MUTATOR SEPARATION requirement (item 7) is a good catch. A naive implementation that makes everything read-only would break the pipeline. Calling this out explicitly prevents that failure mode.

GAPS AND CONCERNS

1. No temporal/session boundary definition. The card says "reviewer execution context" and "reviewer execution identity" throughout but never defines what constitutes that context's lifecycle. Is it a container per review session? A persistent service? This matters because if the reviewer identity persists between reviews and the harness changes its mounts between sessions, the evidence report for one session does not transfer to the next. Recommend adding a DONE WHEN item or a CLARITY note specifying that the boundary is per-session or defining whatever lifecycle is intended, and that evidence must be reproducible for each session.

2. The network boundary section is the weakest part of the card. "Arbitrary reviewer-originated network egress is denied" and "model transport requires network connectivity" are in tension, and the resolution ("explicit, minimal, must not expose a general-purpose reviewer egress path") is underspecified. What does "minimal" mean operationally? Is it a domain allowlist? A single endpoint? A proxy that terminates TLS and inspects traffic? The implementer needs more guidance here or the result will be inconsistent. At minimum, the card should state that the allowed exception must be documented as a concrete endpoint or set of endpoints in the evidence report, not merely described as "minimal."

3. The dispatch boundary (DONE WHEN item 3, EVIDENCE dispatch probe) is strong on intent but does not define what "reviewer-originated dispatch attempt" means concretely. If the reviewer can call into the harness API or write to a shared IPC channel, the boundary is only as strong as that channel's access control. The card should specify that the reviewer context must lack the capability to reach any dispatch interface, not merely that a dispatch attempt is rejected when it tries. The difference is between "cannot attempt" and "attempt fails" — the card currently asks for the latter but the former is stronger.

4. Output ownership is well-stated but the provenance requirement (provenance binds artifact to reviewer session/input/output hashes) is asserted without defining what "session" means here or what hash inputs are expected. This is a dependency on CARD-reviewer-measurement that should be explicitly noted, or the provenance requirement should be moved to that card. As written, an implementer could satisfy this loosely.

5. The card does not address the case where the advisor and evaluator are the same model lineage served by the same provider endpoint but with different system prompts. The BUILD says "BOTH advisor (GLM lineage) and evaluator (Qwen lineage)" which implies different model families, but does not require separate execution contexts per role — only that both are isolated. If they share a context and one can observe the other's review output before the harness captures it, that is a cross-role leakage path the card doesn't address. Recommend a note clarifying whether advisor and evaluator must be in separate execution contexts from each other, or only from the builder.

6. No failure-mode guidance for the case where model transport network egress cannot be narrowed below a CIDR or domain pattern. Some model providers use dynamic or rotating endpoints. The card should acknowledge that if the transport exception cannot be narrowed to a single endpoint, the evidence report must document the actual allowed set and the implementer must justify why it cannot be narrower. Otherwise the "minimal" requirement is unenforceable.

MINOR NOTES

- The CANONICAL_TOKEN and VERSION fields are present but the card does not reference whether evidence reports are versioned against the token. If the card changes, old evidence reports become ambiguous. Recommend that evidence reports include the CANONICAL_TOKEN of the card version they were run against.

- "Reviewer roles do not receive a writable bind/mount to the protected workspace, spine storage, queue/job registry, or protected artifact store" — this list is specific and good, but should note it is illustrative not exhaustive. If the pipeline adds a new protected state store later, the card's list shouldn't be read as a closed set.

RECOMMENDATION

Approve with revisions. The core isolation requirements and evidence discipline are sound. Address items 1, 2, and 3 before implementation begins. Item 5 (advisor/evaluator mutual isolation) should be resolved at least to the level of an explicit decision recorded in the card, even if the decision is "they may share a context."
