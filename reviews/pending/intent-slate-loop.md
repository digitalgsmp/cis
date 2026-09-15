# INTENT REVIEW — what is being built, and is it the right thing

**THIS IS NOT A DESIGN REVIEW. Do not review a proposal.** You are being asked
to read a record of a conversation and say, in your own words, what the operator
is trying to achieve — and then what capabilities that requires which do not
exist.

Answer exactly these three questions:

1. **What is Eric trying to achieve?** State it as you understand it, not as the
   document states it. If the document's own framing is wrong, say so.
2. **What capabilities does that require that do not exist today?** Enumerate
   them. For each, say what it is for and what it depends on.
3. **What is the smallest first build** that makes this loop self-improving
   rather than needing to be complete before it runs?

**Deliberately minimal editorial.** The material below is the handoff document
almost verbatim, plus measured facts. Claude Code has kept its own reading out of
this packet on purpose: the thing being tested is whether two independent
lineages converge on what the operator wants, and a framing supplied here would
be handed back as agreement.

**Say plainly if you think the wrong thing is being built.** That is the most
useful answer you can give and the least likely to be volunteered.

---

## WHO IS INVOLVED

- **Eric** — the operator. **Not a coder.** He validates by checking output, not
  by reading code. Decisions requiring code reading cannot be routed to him.
  Decisions about intent, sequence, and what the system should do can.
- **Claude Code** — writes and executes cards against the repo. Has tools.
- **Two advisor lineages** (you) — GLM and Qwen, no tools, review each card
  before it runs and the result after.
- **chat-Claude** — a browser chat with no repo access. Wrote the handoff
  document below, blind.

---

## THE SYSTEM AS IT STANDS, MEASURED 2026-09-09

```
docs/UNIFIED_BUILD_LIST.md   120 items, the authoritative task queue
queue_items (spine table)    120 rows, regenerated from that file
                             OPEN 42  UNASSESSED 11  DONE 8  HALF_DONE 3
                             no status stated 56

advisor loop                 rounds 1 (review), 2 (reply), 3 (result review)
                             dual lineage, one packet, one hash
pause                        three stops: card-written, reviews-landed,
                             result-reviewed. A row in the spine, not a blocked
                             process. Messages Eric on Telegram, ONE-WAY.
```

**Activity recording, measured today — newest row in every table:**

```
dispatch_events      2026-06-18
lifecycle_events     2026-06-24
agent_trajectories   2026-08-31
run_progress         2026-08-31

today's session:     17 advisor rounds written, ZERO activity rows
```

Four activity tables exist and have stopped being written. No `tool_calls` table
exists at all; nothing records which files an agent read.

**Of the four questions the queue is supposed to answer** — what is the current
item, what does it depend on, what was just done, did it succeed — **one is
answered.** *What was just done.* The other three: nothing designates a current
item; dependency edges are a hand-made 2026-09-05 snapshot nothing regenerates;
and the success link was deliberately withdrawn because it would have inherited a
known false-success signal.

**No interpreter on the host can run the test suite.** Work ships on inspection
plus purpose-built verifiers. Do not treat tests as available evidence.

---

## THE HANDOFF DOCUMENT (verbatim except where marked)

### What changed in the development apparatus

Claude Code writes and executes the cards. Both advisor lineages review each card
before it runs and the result after. The loop pauses at three stops and messages
Eric. chat-Claude's role is design review and pushing back on scope — not
authoring cards.

This session was the first attempt at the new arrangement and it exposed a gap in
it, which is most of what follows.

### The gap: selection

> Eric selects which item is worked — the pipeline must not pull its own work
> (4.19 constraint 1, evaluator-must-not-be-the-builder). But Eric is not
> positioned to derive that choice unaided: he does not read the dependencies,
> and the list is not strictly ordered by them. Tier order governs the container
> plane only; apparatus items sit interleaved on purpose. "Go to the next item"
> is therefore wrong, and item 2.39 means the next item may already be done.
>
> chat-Claude had been filling that role. Handing card production to Claude Code
> removed the proposer without replacing it.
>
> **chat-Claude then proposed itself as the proposer. Eric rejected it,
> correctly:** any loop with a chat model in the selection seat puts him back to
> carrying responses between tools, which is the exact role the dev advisors were
> created to remove him from.

### The loop as designed

> 1. Card executes.
> 2. Both advisor lineages review the result.
> 3. **The same round produces a slate** — items found mismatched, malfunctioning
>    or incorrect, each with the benefit expected from resolving it and what it
>    depends on.
> 4. Eric picks an item number, or abides.
> 5. Claude Code authors the card for that item.
> 6. Advisors review the card, cited corrections are made, the card executes.
> 7. Return to 2.
>
> **Eric's participation is step 4 and nothing else.** Any step that requires him
> to propose items, or to move one tool's output into another tool, is a defect
> in this design and not a workaround.
>
> **Why this does not violate the evaluator-must-not-be-the-builder rule.**
> Claude Code both builds and enumerates the slate. That is not the builder
> selecting its own work: two independent lineages contest the slate, the source
> is a written list Eric can spot-check, and the pick stays human. The constraint
> is satisfied by the pick remaining his, not by the candidates being
> human-generated.

### The chicken and egg — THE OPERATOR ASKS THAT YOU WEIGH THIS PARTICULARLY

> **Bootstrapping — the chicken and egg, and how it breaks.** A good slate is a
> query against the queue: what is the current item, what does it depend on, what
> was just done, did it succeed. Those are the four questions, of which one
> shipped. Until the rest exist, the slate is an agent reading the markdown and
> reasoning — worse, and sufficient to pick the next few items, one of which is
> the work that upgrades it. **The loop is expected to start degraded and improve
> itself.** Do not treat the degraded first slate as a reason to defer building
> the loop.

### Why real-time updates come first

> Eric asked for real-time queue and model activity updates several days ago,
> instead of gathering them at closeout, specifically to avoid stale
> documentation. It was not built. He has now named it as the next item.
>
> **It is also a hard prerequisite to the slate.** A slate produced at result
> review is a claim about current state. If the rows it reads were written at the
> previous closeout, the slate offers items that may already be done — the
> staleness defect arriving inside the mechanism built to replace Eric's
> judgement.
>
> **The drift is not hypothetical.** It happened twice on 2026-09-09 and was
> caught by hand both times only because the session that edited the file also
> remembered to re-extract.

### Open questions the document records as unresolved

- **The status-marker convention**, open across three sessions. 56 of 120 items
  carry no status. Should the list require statuses be written as a specific
  marker? If yes, the items become a backfill job. If no, the bucket stays
  permanently ambiguous. The document says: put a recommendation in front of
  Eric so he accepts or rejects rather than originates it.
- **The NULL-bucket audit** — proposed then withdrawn as not moving the product.
  Nobody has checked whether "no status stated" is accurate for those 56.
- **An open decision blocking the success-link work:** does a run name its
  project-pivot at intake, or are repairs marked maintenance?
- **Telegram** — Eric does not know whether replying there reaches the waiting
  loop or whether he must answer in the terminal. (Measured: the feed is one-way.
  A reply reaches nothing.)

---

## WHAT THE OPERATOR SAID, IN HIS OWN WORDS, ASKING FOR THIS REVIEW

> "For me the emphasis should be placed on evaluation to the problem which you
> say should be relative to a broader scope or intent. Are we building the right
> thing. Right now I want to build all the capabilities we can infer from this
> conversation."

---

## ONE OBSERVATION FROM CLAUDE CODE, DECLARED AS ITS OWN

Across three review packets and one result review this session, both lineages
attacked **content** and never attacked the **frame**. Real defects were found —
a false premise about which code writes a table, an extractor contract that could
never complete, a missing reader, an unevidenced claim. **Not once did either
lineage say "you are working the wrong item."**

This is stated because it bears directly on question 1, and because a review
process that only ever contests details will ratify a wrong direction with a
clean record. **Treat it as a challenge to answer, not as a framing to accept.**

---

## WHAT YOU ARE NOT BEING ASKED

Not to review a schema, a migration, or a script. Not to check a verification
suite. Not to rank the existing 120 items.

Only: **what is he trying to achieve, what capabilities does it require that do
not exist, and what is the smallest first build that makes the loop improve
itself rather than needing to be finished before it starts.**
