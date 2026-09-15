# Advisor review — current-item-pointer

- packet: `reviews/pending/current-item-pointer.md`
- advisor: evaluator on port 8650, no tools
- run tag: current-item-pointer @ 2026-09-09T20:23:32-05:00
- at: 2026-09-09T20:24:14
- prompt_tokens: 1681
- completion_tokens: 1380
- total_tokens: 3061
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The slate exists and is generating proposals, but without knowing what's currently in flight it will propose done or in-progress items, destroying trust before the loop can demonstrate value. This is the explicit second half of what GLM named as required alongside the slate build. It's appropriately scoped infrastructure that unblocks the loop from functioning at all.

---

**What this card would fail to establish:**

It establishes the pointer exists and is readable, but cannot establish that the slate actually consults it. The slate is prose from a model reading markdown; whether it respects the pointer is a behavioral property, not a structural one. It also cannot establish that anyone will set it consistently or that stale pointers will be detected. The verification proves the infrastructure is correct but not that it's used or kept current.

**What would look like success while being wrong:**

The pointer is set to item 3.30, the slate happens to avoid proposing 3.30 for two or three cycles, and you conclude "the system works." This is the tier-order illusion GLM already warned about: the model complied by coincidence, not because the pointer enforced anything. When the model eventually stops complying and proposes 3.30 anyway, you'll think something broke when it never actually worked. The infrastructure passed all seven checks, but the behavioral outcome you needed—slate never proposes the current item—was never guaranteed by those checks.

A secondary failure mode: the pointer is set correctly and survives regeneration (check 7 passes), but no workflow ever reads it. The infrastructure is perfect and unused, solving nothing. You'd only discover this when someone asks "why are we still proposing done items?" and realizes the slate was never wired to consult the pointer it can now access.
