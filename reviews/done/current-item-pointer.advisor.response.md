# Advisor review — current-item-pointer

- packet: `reviews/pending/current-item-pointer.md`
- advisor: advisor on port 8649, no tools
- run tag: current-item-pointer @ 2026-09-09T20:23:32-05:00
- at: 2026-09-09T20:23:46
- prompt_tokens: 1957
- completion_tokens: 704
- total_tokens: 2661
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This is the explicitly named second half of the previous card. GLM identified the current-item pointer as the one thing to build alongside the frame gate and slate emission, which already shipped. Without it, the slate loop is incomplete — it emits slates but nothing designates which item is current, so every slate risks proposing already-done work. The timing is correct: this is the direct companion to shipped work, not a speculative addition.

---

What this card fails to establish:

1. Staleness detection. The card names this as a known weakness but treats it as accepted. A pointer left on a finished item asserts something false, and no check catches it. This is not a edge case — it is the default state the pointer will drift into, because completion comes from the markdown and nothing pushes the pointer forward when an item is done.

2. No trigger to set the pointer. The helper is manual. Someone must remember to run it. The card acknowledges this is the same class of defect as item 2.39 (a human remembering), but does not propose even a lightweight guard against it. The safe-failure mode (NOT AVAILABLE when unset) is good, but it only protects against absence, not neglect.

3. The pointer-to-slate relationship is entirely soft. The slate is model-generated prose. Whether it respects the pointer is unenforceable. The card correctly scopes this out, but it means the card's actual value proposition —that slates will stop proposing done items — is not guaranteed by anything this card builds. The pointer could exist perfectly in the database and the slate could still propose whatever it wants. This is not a defect to fix in this card, but it means the card's success criteria should be framed as "the pointer exists, is queryable, and survives regeneration" — not as "slates now respect the current item." The verification checks already reflect this correctly, which is good.

4. No mechanism for the pointer to move forward. The card says "completion still comes from the markdown" but does not address the gap between markdown marking something done and the pointer advancing. In practice this means the pointer will sit on a finished item until someone manually moves it. That is the stale-pointer scenario from weakness 3 above, and it is the most likely operational state.

What success looks like while still being wrong:

- All seven checks pass, including check 7 (survives regeneration). The pointer exists, is readable, is consistent. But it is set once at the start and never updated. It sits on item 3.30 forever while the build moves on. Every query returns 3.30. The slate sees 3.30, proposes 3.30, which is already done. The system has the pointer, the pointer is technically correct per the checks, and it is useless because no one maintains it. This is worse than NOT AVAILABLE because it provides false confidence that the system knows where it is.

- Alternatively: the pointer is maintained diligently, slates consult it faithfully (by luck), and the loop appears to work. But this is the tier-order illusion the card itself names — a property that holds because the model happened to comply. Success here is real but fragile and unattributable to this card's mechanism.

What is missing that I would need to judge fully:

- The previous card (frame gate and slate emission) — I need to see what the slate actually reads and how, to know whether the pointer is plausibly consulted. The card says query_queue_item already exists and returns answers_2_30, but I do not see the slate's consumption path.
- The intended transition mechanism — even if this card does not build automatic pointer advancement, I need to know whether the next card is planned to do that, or whether this is expected to be manual indefinitely. The "does not decide who sets it" scope-out is fine for this card but leaves the pointer's lifecycle undefined beyond "someone runs the helper."
- Whether any existing project_state key (e.g., current_direction, next_action) already partially serves this purpose and whether this pointer duplicates or supersedes it. The measured state says those keys exist but does not say what they hold.

Bottom line: this is the right work at the right time. The design is sound within its scoped boundaries. The danger is not that it fails to build what it says it builds — the checks are honest and well-chosen, especially check 7. The danger is that the success state it creates — a live, correct, queryable pointer — is operationally a transient state that no mechanism here sustains, and the failure mode it does not handle (staleness) is the most likely one in practice. Ship it, but the next card should be about what advances the pointer when the markdown marks an item done.
