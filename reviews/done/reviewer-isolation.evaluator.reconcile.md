# Reconciliation — reviewer-isolation

- lineage: evaluator
- packet: `reviews/pending/reviewer-isolation.md`
- own round-1 hash: 30d4209a00b985c5
- peer round-1 hash: c521f1c9e23d4bfe (advisor (GLM))
- run tag: reviewer-isolation @ 2026-09-10T15:44:31-05:00
- at: 2026-09-10T15:44:31-05:00
- prompt_tokens: 4454
- completion_tokens: 633
- total_tokens: 5087
- token source: gateway response usage

---

RECONCILE: COMPLETE

AGREED

Both lineages agree the card correctly identifies the foundational problem and is the right prerequisite work. Both agree the evidence discipline is the card's strongest feature, specifically the explicit rejection of model self-reports and application-level hook denials as sufficient proof. Both agree the rejection of command blacklists and the demand for OS-level enforcement is correct. Both agree the mutator separation requirement (item 7) prevents the naive failure mode of making the entire pipeline read-only. Both agree the scope lock and companion card separation are clean. Both flag the network boundary as the area needing the most implementer attention, though at different levels of urgency.

DISAGREE

I concluded "ready for implementation" while the GLM lineage concluded "approve with revisions" requiring items 1, 2, and 3 resolved before work begins. I treated the network boundary as a minor implementation note; they treated it as a gap requiring card-level clarification of what "minimal" means operationally. On reflection, their position is more defensible. The card says the implementer must "prove the effective runtime permissions" but leaves "minimal" network exception undefined, which means two implementers could produce very different solutions and both claim compliance. The card should at minimum require the evidence report to document the concrete allowed endpoint set. I was too generous in my initial read.

They propose strengthening the dispatch boundary from "attempt fails" to "cannot attempt" (removing the capability to reach the dispatch interface entirely). I did not raise this. The card's current language ("does not create a run, queue entry, job, or equivalent side effect") describes the outcome of an attempt, not the absence of the capability to attempt. Their proposed strengthening is architecturally sound but goes beyond what the card explicitly requires. This is a legitimate improvement suggestion, not a card defect.

THEY MISSED (I caught)

Nothing substantive. My one unique point was recommending proxying model API calls through a controlled harness endpoint rather than giving the reviewer container direct egress. However, they independently mentioned "a proxy that terminates TLS and inspects traffic" as one possible resolution, so this is effectively shared ground, not a unique catch.

I MISSED (they caught)

1. Temporal/session boundary definition. I accept this. The card uses "reviewer execution context" and "reviewer execution identity" throughout without defining whether this is per-session, per-container, or persistent. If the context persists and mounts change between sessions, evidence from one session does not transfer. This is a real gap.

2. Network boundary operational specification. I accept this. "Minimal" is not an enforceable standard. The card should require the evidence report to enumerate the concrete allowed endpoints and justify why they cannot be narrower.

3. Dispatch boundary capability vs. outcome. I accept the observation that the card currently requires "attempt fails" rather than "cannot attempt." Ipartially accept this. The card's evidence section does say "reviewer-originated dispatch/start attempt -> denied" which is outcome-based. Their suggestion to require the reviewer context to lack the capability to reach any dispatch interface at all is stronger and more robust, but the card's current language is not wrong — it's just a weaker guarantee than ideal. I'd recommend this as a revision rather than a blocker.

4. Provenance/session hash dependency. I accept this. The card requires "provenance binds artifact to reviewer session/input/output hashes" but doesn't define what constitutes a session or what hash inputs are expected. This either needs a forward reference to CARD-reviewer-measurement or the provenance detail should move to that card.

5. Advisor/evaluator mutual isolation. I accept this. The card requires both roles to be isolated from the builder but never states whether they must be isolated from each other. If they share an execution context, one could observe the other's draft findings before harness capture, which is a cross-role leakage path. The card should explicitly decide this.

6. Dynamic/rotating model provider endpoints. I accept this as a practical concern. If the model provider uses rotating endpoints that cannot be narrowed to a single address, the card should require the evidence report to document the actual allowed set and the justification for why it cannot be narrower.

UNRESOLVED

Whether the dispatch boundary should require "cannot attempt" (capability removal) versus "attempt fails" (outcome denial). The card as written requires the latter. The GLM lineage argues the former is architecturally superior. Settling this requires a decision from the card author about the threat model: is a reviewer that can reach the dispatch API but gets rejected sufficient, or must the reviewer be unable to reach it at all? The packet alone does not resolve this.

Whether advisor and evaluator must be in separate execution contexts from each other, or only from the builder. The card is silent on this. The GLM lineage flagged it as a cross-role leakage risk. Settling this requires the card author to decide whether the two reviewer lineages are trusted with respect to each other's in-progress findings. The packet alone does not resolve this.

Whether the provenance hashing requirement belongs in this card or should be deferred entirely to CARD-reviewer-measurement. The card asserts the requirement but doesn't define the mechanics. The GLM lineage notes this dependency. Settling this requires the card author to decide the boundary between isolation mechanics (this card) and output integrity mechanics (companion card). The packet alone does not resolve this.
