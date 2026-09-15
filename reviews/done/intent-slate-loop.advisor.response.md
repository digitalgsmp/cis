# Advisor review — intent-slate-loop

- packet: `reviews/pending/intent-slate-loop.md`
- advisor: advisor on port 8649, no tools
- run tag: intent-slate-loop @ 2026-09-09T19:29:53-05:00
- at: 2026-09-09T19:32:01
- prompt_tokens: 2936
- completion_tokens: 1531
- total_tokens: 4467
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

1. WHAT IS ERIC TRYING TO ACHIEVE

Eric wants a development loop that runs without him carrying information between tools. His only job is to pick which item gets worked next. Everything else — proposing candidates, building the work, reviewing it, checking the result, producing the next set of candidates — should happen inside the system and surface to him as a choice.

Underneath that, he is asking whether the apparatus itself is the right thing to build. He said it directly: "Are we building the right thing." He is not asking whether the code in any individual card is correct. He is asking whether the loop — the management layer being constructed around 120 items, 8 of which are done — is1. WHAT IS ERIC TRYING TO ACHIEVE

Eric wants a development loop where his only job is picking which item gets worked next. Everything else — proposing candidates, building the work, reviewing it, checking the result, producing the next slate of candidates — happens inside the system. He is a non-coder who validates by output inspection. Any step that requires him to read code, read dependencies, or shuttle output between tools is a defect in the design.

But he is also asking a deeper question: is the loop itself the right thing to build. He said so directly. And there is reason to think the answer is partly no — not because the loop is wrong in concept, but because it is being built on a queue that cannot answer three of the four questions the loop needs it to answer. The loop is designed to self-improve from a degraded start, which is sound. But the degraded start depends on a slate produced by an agent reading markdown and reasoning — the same kind of unstructured judgment the loop was created to replace. The loop may be ratifying itself before it can actually do the job it exists to do.

The framing in the handoff document is mostly honest but has one sleight of hand: it frames the missing capabilities as "the rest of the four questions" that will be built as queue items inside the loop. That makes the loop both the product and the factory that builds its own prerequisites. That can work — but it means the first several slates will be produced by reading stale markdown, and the items they surface will be items the loop itself needs. The document acknowledges this. It does not acknowledge that the advisors reviewing those early slates have, by Claude Code's own observation, never once challenged the frame. A self-improving loop whose reviewers only contest content will improve code quality while marching in the wrong direction with a clean record.

2. WHAT CAPABILITIES DOES THAT REQUIRE THAT DO NOT EXIST TODAY

A. Current-item designation. No field, row, or marker says which item is active right now. The queue has 120 rows with status buckets but no pointer to "this one is up." The slate needs this to avoid re-proposing completed work. Depends on: the spine table having a column or convention for this, and the card execution loop writing to it.

B. Dependency edges that regenerate. The dependency map is a hand-made snapshot from 2026-09-05. Nothing updates it. The slate needs current dependency information to order candidates and to say what each item depends on. Depends on: a source of truth for dependencies — either parsed from the build list or derived from code structure — that updates when items change.

C. Success signal per completed item. The success link was withdrawn because it inherited a false-success signal. No replacement exists. The slate needs to know whether the last item actually succeeded before proposing the next one. Depends on: a verification step that writes a real result — not "the card ran" but "the card's intent was met" — into the spine.

D. Real-time activity recording. Four activity tables exist and stopped being written between June and August. No tool_calls table exists. The slate's claim about current state is only as good as the freshness of the rows it reads. Depends on: the execution loop writing to activity tables on every card run, and a tool_calls table being created.

E. Slate production at result review. The loop design says the same round that reviews a result also produces the next slate. No mechanism exists for this today — advisors review cards and results but do not emit structured candidate lists. Depends on: a card or output format that asks advisors to return a slate as structured data, and a place for that slate to land so Eric can see it.

F. Two-way Telegram or an equivalent intake path. Telegram is one-way. Eric cannot reply to the waiting loop from where he receives messages. This means step 4 of the loop — Eric picks — has no input channel. Depends on: either making Telegram two-way or defining the terminal as the intake point and Eric accepting that constraint.

G. A frame-level review capability. Both advisor lineages contest content but not direction. The loop as designed has no mechanism for either lineage to say "this is the wrong item" or "this slate is built on a stale premise." Depends on: a review prompt that explicitly asks advisors to challenge the selection, not just the card — and advisors that have enough context to do so, which today means access to the queue state they are being asked to assess.

3. SMALLEST FIRST BUILD

The smallest first build that makes the loop self-improving is not real-time activity recording, though that is the right next item. It is the slate itself, produced in the most degraded form possible, paired with a current-item pointer and nothing else.

Here is why. The loop's core function is: result review produces a slate, Eric picks, card is built, card runs, repeat. If the slate exists even as "read the markdown, list five candidates with their dependency claims and benefit," the loop is running. It will be wrong sometimes — it will propose items already done, it will miss dependencies, it will not know if the last item succeeded. But Eric picks, and the act of picking against a visible slate is what makes the loop improve: the first slate will surface the staleness problem as a concrete instance Eric can see, the second will be better, and one of the early slate items will be the work that builds real-time recording or the current-item pointer.

What makes this self-improving rather than complete-before-it-runs is that each slate is produced from the result of the previous card. The advisor round that reviews a result also emits the slate. That emission is the thing to build. It can be a structured text block — item number, claimed benefit, claimed dependencies, confidence — that the advisors return and that lands somewhere Eric can read it. No new table, no migration, no schema. Just an output format and a place for it to appear.

The current-item pointer is the one thing to build alongside it, because without it every slate will propose done items and Eric will lose trust in the slate before the loop has a chance to improve. It can be a single column in the spine — CURRENT, boolean — that the card execution sets. That is enough for the first degraded slate to avoid the most obvious failure mode.

Real-time activity recording should come after, as a slate item the loop produces and Eric picks. It is the right second build. But if it is built first, the loop has nothing to run in, and Eric is back to choosing items unaided — which is the exact problem the loop exists to solve.

One thing the packet does not give me that I would need to be certain: I do not know what the 120 items actually are. I am told 8 are done and 42 are open, but I cannot assess whether the items that upgrade the loop are themselves near the top or buried at item 95. If the self-improvement items are deep in the queue, the degraded slate will spend many rounds on product work before it touches its own prerequisites, and the self-improving claim weakens. That changes the answer to question 3 — not the shape of the first build, but whether the first build is enough or whether the queue also needs reordering first.
