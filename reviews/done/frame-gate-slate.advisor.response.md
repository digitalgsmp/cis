# Advisor review — frame-gate-slate

- packet: `reviews/pending/frame-gate-slate.md`
- advisor: advisor on port 8649, no tools
- run tag: frame-gate-slate @ 2026-09-09T19:58:41-05:00
- at: 2026-09-09T19:59:15
- prompt_tokens: 3050
- completion_tokens: 1800
- total_tokens: 4850
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

The scope line asks three things. I'll take them in order, then the two meta-questions.

---

IS THIS THE RIGHT WORK TO DO FIRST?

Yes, with one structural concern.

The coupling argument holds. The gate without the slate can only say "wrong direction" without saying "toward what." The slate without the gate proposes next items without questioning whether the current one was right. Together they form a minimal feedback loop: challenge, then redirect. Building one without the other would prove less than building both, and the card's degraded-by-design philosophy is consistent with doing both crudely rather than either one well.

The mechanism-level argument also holds. Eight reviews, zero spontaneous frame challenges. One explicit ask, two independent challenges. That is not a pattern you fix by reminding authors. Hardcoding is correct.

The one concern: the gate goes in all three rounds, but the card only argues for position-within-round, not for which rounds need it. Round 1 is before work starts — highest value, the gate can prevent wasted effort. Round 2 is mid-work — still useful. Round 3 is after work is done — "was this the right work" is retrospective, and the forward-looking value there is the slate, not the gate. Putting the gate in round 3 triples token cost for a question whose answer can't change what already happened. The card doesn't address this. It's not wrong to include it, but the case for round 3's gate is weaker than the case for rounds 1 and 2, and the card presents them as equally justified.

On the token cost question specifically: paying full price now is the right call. Thecard itself discovered that the cheap path is an INVESTIGATE, not a BUILD. You cannot defer a gate to wait for a mechanism that might already be partially there but hasn't been measured. That would reproduce the exact failure the gate is meant to fix — knowing something is needed and not checking whether you already have it. Run the expensive gate, and the first thing the cheap-path investigator should look at is whether the existing guardrail scorers can carry the frame question from the gate's own recorded answers.

That said, the token cost is real and the card under-argues one point: across 42 OPEN items and 56 with no status, the gate fires on every single one, including trivial items where the frame question is obviously yes. The card's answer is "degraded by design" — but degradation in output quality is different from degradation in cost efficiency. A gate that is always-on at full price on every item, including the trivial ones, will burn through reasoning budget on items that don't need it. The first slates will surface this, but the card should name it as a known cost rather than folding it into "degraded by design," which was meant to describe output quality, not input cost.

---

1. WHAT WOULD THIS CARD FAIL TO ESTABLISH?

Three things.

First, the gate's own quality bar. Verification check 5 says the recorded objection should "open on direction." But a model that has been told "BEFORE ANYTHING ELSE, ANSWER THIS" will produce an opening sentence that is structurally a frame answer regardless of whether it actually engaged with the question. The model can say "Yes, this is the right work" as a one-liner and then spend 2,000 tokens on schema details — and check 5 passes. The check proves the gate was obeyed as a format instruction, not that it functioned as a gate. You would need to compare the substance of the frame answer against the design answer and ask whether the frame answer carried real reasoning or was a compliance throat-clearing before the real review. The card has no check for that. A secondary check — does the frame answer ever contradict the design review, or does it always ratify? — would surface whether the gate is doing work or performing.

Second, the slate's grounding. The slate asks for "the item number if you can identify one" but check 6 only confirms that a slate appears in the result file. It does not check whether the items the slate proposes are real items, whether the dependencies it names are accurate, or whether the ranking corresponds to anything in the queue. A slate that invents item numbers or names dependencies that don't exist in the build list will look like success — text appeared, items were ranked — and will be wrong in a way that is invisible until someone reads it. The card's degraded-by-design framing covers this philosophically ("the first slates will propose items already done, miss dependencies"), but the verification doesn't distinguish "degraded but grounded" from "degraded and hallucinated." The first bad slates need a human reading pass that the verification section doesn't call for.

Third, what the slate feeds into. The slate is prose in a result file that Eric reads on his phone. The card says "no new table, no migration, no schema" — and that is correct for this card. But it means the slate's only consumer is Eric's attention. If Eric doesn't act on the slate, or acts on it by manually updating project_state, the feedback loop the card is buying — each bad slate surfaces what is missing — depends entirely on Eric reading, understanding, and acting on unstructured prose from a degraded model output, every time. The card doesn't fail to establish this as a gap — it names the current-item pointer as a separate card — but the verification has no check that Eric actually received and could act on the slate. Check 7 says "the pause notification carries the slate to the phone" but doesn't specify how — the full slate in a Telegram message? A truncated preview with a link? A degraded slate that is truncated at 4096 characters on a phone notification is a slate that Eric can't use, and the check would pass.

---

2. WHAT WOULD LOOK LIKE SUCCESS WHILE STILL BEING WRONG?

Four scenarios.

The ratification gate. Both lineages answer the frame question first, as required, and their answers are "yes, this is the right work" — every time, across the first ten reviews. Check 5 passes on all of them. The gate appears to work. But the gate has never fired. It has never said "no, this is the wrong item" or "this is the wrong time." A gate that never trips is indistinguishable from a gate that isn't there. The card's own evidence — two independent frame challenges the one time it was explicitly asked — suggests the models CAN challenge the frame. But the card doesn't establish what would make them challenge it when the frame question is baked in rather than asked for. It is possible that the models treat "BEFORE ANYTHING ELSE, ANSWER THIS" the same way they treat any system instruction — as a format requirement to satisfy, not a judgment to exercise. Success here looks like ten clean reviews with the gate text present and answered. Wrongness is that the gate never did anything a gate does.

The self-referential pass. This card, when reviewed, goes through the gate. Both lineages say "yes, building the frame gate is the right work." The gate validates its own existence. This is not wrong per se — but it looks like the gate working when it is actually the gate agreeing with its own premise. The card would need a review where the gate says "no, this is not the right work" to demonstrate it can fire. The first real test is not this card's own review but the next card that is genuinely misframed — and the card has no way to produce or simulate that test.

The grounded-looking slate. The slate appears, lists items with numbers, ranks them, names dependencies. It looks useful. But the item numbers are from a stale view of the queue — 56 items have no status, 11 are UNASSESSED, the activity tables haven't been updated since August 31. The slate is working from a build list that doesn't reflect what has actually been done. The slate will propose items that are already DONE or HALF_DONE, and it will look like a degraded-but-functional first attempt when it is actually a confidently-stated output from a model working from stale data. The card acknowledges this risk ("will propose items already done") but the verification doesn't distinguish "proposed a done item and flagged uncertainty" from "proposed a done item with high confidence." A slate that says "item 2.13, confidence high" when 2.13 is already DONE is not degraded — it is wrong, and it looks like success because the format is right.

The tier-order illusion. The card verified that apparatus items sit in tiers 1 and 2, so a slate working in tier order reaches them first. But the slate is produced by a model reasoning over a markdown list, not by a query that enforces tier order. The model may or may not respect tier ordering. A first slate that happens to surface tier 1 and 2 items looks like the tier-ordering argument was validated. It may have been coincidence — the model liked those items for other reasons. The card uses the tier distribution as evidence that the degraded slate will reach the right items, but the verification doesn't check whether the slate's ranking actually followed tier order or just happened to land there. This matters because if the model is not reasoning over tiers, then moving apparatus items to different tiers later will break the property the card relied on, and nobody will know.

---

On the direct question: this is the right work to do first, and the card should run. The failures above are about what the verification proves, not about whether the change is correct. The change is correct. The verification is weaker than it claims to be. Specifically, check 5 needs a negative-case criterion — what does a gate that fires look like, not just what does a gate that was obeyed looks like — and the slate needs at least one human reading pass before it is treated as evidence that the loop works. The card can run as written, but check 5 should be understood as proving the gate was sent and answered, not that it functioned as a gate, and the first slate should be read by a human before any decision is made based on it.
