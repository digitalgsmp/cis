# Reconciled review — reviewer-isolation

- packet hash: 0359f3bbe7b9e3ef
- advisor round-1 hash: c521f1c9e23d4bfe
- evaluator round-1 hash: 30d4209a00b985c5
- advisor reconcile hash: d6f6dda5b0895c02
- evaluator reconcile hash: 3f3a451098ca4634
- at: 2026-09-10T15:44:31-05:00

The two reviewer lineages reviewed the same packet independently (round 1),
then each saw the other's frozen findings and reconciled (round 2).
Dissent is preserved below; nothing here forces consensus.

---

## advisor (GLM) reconciliation

# Reconciliation — reviewer-isolation

- lineage: advisor
- packet: `reviews/pending/reviewer-isolation.md`
- own round-1 hash: c521f1c9e23d4bfe
- peer round-1 hash: 30d4209a00b985c5 (evaluator (Qwen))
- run tag: reviewer-isolation @ 2026-09-10T15:44:31-05:00
- at: 2026-09-10T15:44:31-05:00
- prompt_tokens: 5189
- completion_tokens: 352
- total_tokens: 5541
- token source: gateway response usage

---

RECONCILE: COMPLETE

AGREED

1. RIGHT_WORK frame. Both lineages independently framed this as the correct foundational work — establishing OS/container-level isolation before measurement or reconciliation logic can be trusted. The other lineage used the metaphor "builds the walls and the next card will install the cameras," which aligns with my assessment of timing and scope appropriateness.

2. Rejection of prompt-level and blacklist-based isolation. Both lineages explicitly endorsed the card's insistence on OS-level enforcement over model self-report or command blacklists. The other lineage called out "the most common pitfall in agent sandboxing"; I called out the two most common failure modes (trusting model self-report, trusting bypassable middleware hooks). Same finding, same reasoning.

3. DONE WHEN / EVIDENCE mapping and rigor. Both lineages praised the correspondence between required properties and probes, and specifically noted that requiring OS denials rather than model refusals is the critical evidence discipline. The other lineage noted that requiring the same probes for both advisor and evaluator "prevents asymmetric security gaps," which is my MUTATOR SEPARATION / BOTH ROLES point from a different angle.

4. Network boundary exception tension. Both lineages identified that the model-transport network exception is in tension with the egress denial and is the weakest or most operationally underspecified part of the card. The other lineage suggested proxying model API calls through a controlled harness endpoint as the safest implementation approach. I raised the operational vagueness of "minimal." Same finding, complementary elaboration.

5. Scope discipline (NOT IN THIS CARD / SCOPE_LOCK). Both lineages agreed the scoping is clean and correctly prevents scope creep into measurement and gating.

DISAGREE

1. Depth of network boundary critique. The other lineage treated the network exception as a "minor area for the implementer to watch" and offered a constructive suggestion (proxy through harness). I raised it as gap #2 — a structural underspecification that could result in inconsistent implementations, and I argued the card must require the allowed endpoint set to be documented concretely in the evidence report, not merely described as "minimal." I maintain my position is the stronger one: the other lineage's suggestion is a good implementation idea but does not address the card-level gap where "minimal" is unenforceable as written. The card should require the implementer to document the actual allowed set and justify why it cannot be narrower.

2. Recommendation threshold. The other lineage recommended approval for implementation as-is. I recommended approval with revisions, specifically requiring items 1 (session lifecycle), 2 (network boundary specificity), and 3 (dispatch boundary capability vs. rejection) to be addressed before implementation begins. This is a genuine difference in review philosophy: the other lineage treated these as implementer-discretion items; I treated them as card-level gaps that will produce ambiguous or unverifiable implementations if left unresolved. I hold my position. An implementer who receives a card with "minimal network exception" and no concrete documentation requirement will produce evidence that cannot be checked against a standard.

THEY MISSED (I caught)

1. No temporal/session boundary definition (my gap #1). The card never defines what constitutes the reviewer execution context's lifecycle — per-session container, persistent service, etc. This matters because if the reviewer identity persists and mounts change between sessions, a single evidence report does not transfer. The other lineage did not raise this.

2. Dispatch boundary: "cannot attempt" vs. "attempt fails" (my gap #3). The card asks for proof that a dispatch attempt fails, but does not require that the reviewer context lack the capability to reach any dispatch interface in the first place. The stronger formulation is capability absence, not attempt rejection. The other lineage did not distinguish these.

3. Provenance requirement is underspecified and has an implicit dependency on CARD-reviewer-measurement (my gap #4). "Provenance binds artifact to reviewer session/input/output hashes" is asserted without defining session or expected hash inputs. The other lineage did not flag this.

4. Advisor/evaluator mutual isolation (my gap #5). If both reviewer roles share an execution context, one could observe the other's output before the harness captures it. The card does not address whether advisor and evaluator must be isolated from each other, only from the builder. The other lineage did not raise this.

5. Network boundary failure-mode for dynamic/rotating provider endpoints (my gap #6). If the model transport exception cannot be narrowed to a single endpoint, the "minimal" requirement is unenforceable. The other lineage did not address this scenario.

6. Evidence reports should carry the CANONICAL_TOKEN for version traceability (my minor note). The other lineage did not raise this.

7. The protected-state list (spine storage, queue/job registry, artifact store) should be marked illustrative not exhaustive (my minor note). The other lineage did not raise this.

I MISSED (they caught)

1. Proxy-through-harness as the recommended implementation pattern for the network exception. The other lineage suggested that proxying model API calls through a controlled harness endpoint is the safest way to satisfy the model-transport exception without risking general egress. I identified the gap but did not propose a concrete architectural solution. I accept this as a useful implementation recommendation that complements my card-level critique. However, I note that suggesting an implementation pattern is different from fixing the card's specification gap — both are needed.

That is the only item the other lineage raised that I did not. The other lineage's review was more affirming and less gap-focused overall, which is why the overlap in "missed" items is small.

UNRESOLVED

1. Whether the network boundary gap is a card-level revision requirement (my position) or an implementer-discretion item (their position). This cannot be settled from the packet alone because it depends on whether the implementing team treats the card as a strict specification or as guidance. If the former, my revisions are required; if the latter, their approach suffices. Evidence that would settle this: the team's documented interpretation of card status (specification vs. guidance) and a sample evidence report showing whether the allowed endpoint set is concretely documented or merely described as "minimal."

2. Whether advisor/evaluator mutual isolation is in scope for this card or belongs in CARD-reviewer-measurement. The packet declares SCOPE_LOCK as "REVIEWER NON-MUTATION / PROCESS-BOUNDARY ISOLATION ONLY" and defers cross-feed logic to the companion card. Cross-role observation of review output before harness capture could be argued as either a process-boundary issue (this card) or a measurement/cross-feed issue (companion card). Cannot be settled without seeing CARD-reviewer-measurement. Evidence that would settle this: the companion card's scope and whether it addresses inter-reviewer information flow.

3. Whether the session lifecycle question (my gap #1) is implicitly answered by the contained-pipeline architecture referenced in DEPENDS_ON. The card says "The implementer must use the actual contained-pipeline architecture." If that architecture already defines per-session reviewer containers, my gap is moot. Cannotbe settled from this packet because the contained-pipeline architecture is referenced but not included. Evidence that would settle this: the pipeline architecture document showing whether reviewer execution contexts are per-session or persistent, and whether mount/identity configuration is re-established per review cycle.

4. Whether the provenance requirement (my gap #4) can be satisfied at all without the companion card. The card requires provenance binding to session/input/output hashes but does not define those terms. If CARD-reviewer-measurement defines them, the dependency is clean but should be explicit. If no card defines them, the requirement is dangling. Cannot be settled without reviewing CARD-reviewer-measurement. Evidence that would settle this: the companion card's definitions of session identity and hash inputs, or confirmation that no such definition exists yet.

Those are all unresolved differences. Dissent on items 1 and 2 of DISAGREE is preserved — I do not accept that the network boundary and recommendation threshold differences are merely stylistic.

---

## evaluator (Qwen) reconciliation

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
