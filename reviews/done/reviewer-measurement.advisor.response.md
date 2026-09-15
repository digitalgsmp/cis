# Advisor review — reviewer-measurement

- packet: `reviews/pending/reviewer-measurement.md`
- advisor: advisor on port 8649, no tools
- run tag: reviewer-measurement @ 2026-09-10T15:40:52-05:00
- at: 2026-09-10T15:41:20
- prompt_tokens: 2982
- completion_tokens: 380
- total_tokens: 3362
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The stated failure was that reviewers could not measure the system and could not reconcile findings independently. This card directly addresses both failure modes, and it was correctly split from a combined card that conflated measurement with isolation — two genuinely different questions. The scope lock to CAN_MEASURE + INDEPENDENT_RECONCILIATION keeps the work bounded, and the "NOT IN THIS CARD" section explicitly defers write-prevention to a separate card. This is the right item at the right time because it is a prerequisite: without measurement and independent reconciliation, the advisory review cannot be trusted, and the project cannot proceed past it. I have sufficient context in this packet to make this call.

Now reviewing the proposal itself.

STRENGTHS

1. The DONE WHEN criteria are unusually well-constructed. Each is testable, has a concrete artifact or observable, and ties back to a specific evidence probe. The requirement that both lineages pass — not just one — closes an obvious gap.

2. The independence protocol is precise. Freezing round 1 before cross-feed, denying peer artifacts through the instrument surface until cross-feed, and forbidding shared scratchpads are three independent mechanisms that each prevent a different leakage path. The seeded-disagreement fixture is a strong test — it proves the protocol preserves dissent rather than silently converging.

3. The provenance requirements bind findings to actual sessions and exact inputs, which makes recycled or fabricated output detectable. Requiring the harness — not reviewer prose — to persist artifacts is the correct trust boundary.

4. The split from CARD-reviewer-readonly-and-reconciliation v3 is justified. "Can reviewers measure?" and "Can reviewers mutate?" are different questions with different threat models. Bundling them would make the card untestable as a single unit.

5. The CLARITY FOR THE IMPLEMENTER section preemptively kills three likely implementation shortcuts: treating read access as measurement (without citation), concatenating transcripts as reconciliation, and allowing models to read each other's round-1 work before freeze.

CONCERNS

1. The card says "read-shaped measurement instruments exposed through a mediated reviewer surface" and lists five instrument types. But it does not specify what "mediated" means at the boundary. Is mediation a whitelist of commands? A custom API? A restricted tool interface? The DONE WHEN criteria test outcomes (reviewer returns a nonce, cites a query) but do not constrain the mechanism. An implementer could satisfy the DONE WHEN criteria with a general-purpose shell plus a policy file, which would technically pass every probe while violating the spirit of "do not give the reviewer a generic shell." The card acknowledges this in NOT IN THIS CARD by deferring isolation, but the tension is real: the measurement probes cannot detect whether the reviewer used a generic shell to obtain its measurements. This is acceptable given the split, but the implementer should be warned that the measurement card's probes alone do not establish the absence of a general execution surface.

2. The reconciliation protocol requires "item-by-item" responses with explicit agreement, disagreement, or "cannot verify with available instruments." But the card does not define what counts as an "item." If the two reviewers produce findings at different granularities or use different framing, the item-by-item mapping becomes ambiguous. The implementer needs guidance on whether items are reviewer-defined (each finding as stated) or harness-defined (a canonical question list). The seeded-disagreement fixture partially addresses this by providing a controlled case, but it does not resolve the general mapping problem for organic reviews.

3. The cross-feed step says "the harness cross-feeds the complete frozen round-1 findings." The word "complete" is doing important work. If a reviewer's round-1 output is voluminous or includes extraneous content, the implementer needs to know whether "complete" means verbatim or structured. The provenance section requires hash binding, which implies verbatim, but the reconciliation section asks for item-by-item responses, which implies structure. These are compatible but the implementer should be told explicitly: cross-feed the verbatim frozen artifact, and let each reviewer perform its own structuring during reconciliation.

4. The evidence section lists positive probes but does not specify a negative probe for the independence requirement beyond "a request through the reviewer instrument surface for the peer round-1 artifact is unavailable/denied." This is good but narrow — it tests one surface. If the reviewer has multiple access paths (source read, log read, spine query, git inspection), the peer's round-1 artifact could theoretically be reachable through any of them if it is stored in a location those instruments can see. The implementer should ensure the peer artifact is not written to any location accessible by any in-scope instrument before cross-feed, and the probe should test all instrument surfaces, not just one.

5. The card references roles advisor (8649) and evaluator (8650) with lineage assignments (GLM and Qwen). These identifiers appear without context. If 8649/8650 are configuration references, the implementer will know what they mean. If they are port numbers, process IDs, or arbitrary labels, they need decoding. I cannot verify from this packet what they refer to. This is a minor concern but worth flagging.

6. The DONE WHEN section 5 (PROVENANCE) requires "canonical input token/version" and "input hash." The canonical token appears in the card header (RM-V1-20260910-A) but the card does not specify how the canonical input itself is defined, hashed, or frozen. If the canonical input changes between the two reviewers'sessions, the independence guarantee is undermined. The card should specify that the canonical input is frozen and hashed once, before either reviewer session begins, and that both reviewers receive the identical input verified by that hash. The provenance fields already require recording the input hash, which is good, but the freeze-before-sessions requirement should be explicit.

VERDICT

APPROVE WITH CONDITIONS

The card is well-structured, correctly scoped, and its DONE WHEN criteria are testable and thorough. The split from the combined card is justified. The independence and reconciliation protocol is the strongest part — it addresses the actual failure mode with multiple independent mechanisms.

Conditions before implementation:

1. Define what "mediated" means at the boundary, or explicitly acknowledge that the measurement card's probes do not detect a general execution surface and that this gap is CARD-reviewer-isolation's responsibility. The card already leans toward the latter but should state it more directly.

2. Specify whether reconciliation items are reviewer-defined or harness-defined, and add guidance for handling granularity mismatches between the two reviewers' findings.

3. Clarify that cross-feed delivers the verbatim frozen artifact and that each reviewer performs its own structuring during reconciliation.

4. Extend the independence probe to test all instrument surfaces for peer-artifact inaccessibility, not just one.

5. Specify that the canonical input is frozen and hashed once before either reviewer session begins, and that both reviewers receive input verified against that single hash.

6. Decode or contextualize the 8649/8650 identifiers if they are not self-evident to the implementer.

None of these are structural problems. They are specification gaps that an implementer could resolve by guessing, but guessing is exactly what this card is trying to eliminate elsewhere. Resolving them before implementation will prevent ambiguity-driven failures during review.
