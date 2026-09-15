# CARD REVIEW — the frame gate becomes the primary gate, and round 3 emits a slate

**Nothing below has been built.** This is a card under review before it runs.

Answer the questions the scope line puts to you, then these two:

1. **What would this card fail to establish?**
2. **What would look like success while still being wrong?**

---

## WHY THIS CARD EXISTS — you two wrote it

On 2026-09-09 both lineages were asked, for the first time, to say what the
operator was trying to achieve rather than whether a design was correct. Both
independently contradicted the plan that had been written for them:

> **GLM:** "The smallest first build is **not** real-time activity recording…
> It is **the slate itself, produced in the most degraded form possible**… if it
> is built first, the loop has nothing to run in, and Eric is back to choosing
> items unaided — which is the exact problem the loop exists to solve."

> **Qwen:** "**Do not** build the real time database updates, the dependency
> graph, or the success signals first… **The loop bootstraps its own
> infrastructure by tripping over the lack of it.**"

That was the first frame-level challenge in nine reviews. It appeared the one
time a packet explicitly asked for it.

**Eric's ruling, 2026-09-09:** that must not be something a packet author
remembers to ask for. *"It should be the primary gate not something we have to
ask for."*

**The reasoning, which you should attack.** If the frame challenge is per-packet,
the author who chose the frame also chooses whether the frame gets challenged —
inviting scrutiny of their own framing, on their own initiative, in a document
they wrote. Across eight prior reviews nobody refused; nobody thought to ask.
Hardcoding removes the author's discretion and makes it a property of the
mechanism rather than a thing we get right when paying attention.

---

## THE CHANGE

One file: `tools/advisor_review.sh`. Three string constants that today read as
transport instructions become the governing question of the loop.

### A. The frame gate, first position, all three rounds

Prepended to `SCOPE_LINE` (round 1), `REPLY_LINE` (round 2) and `RESULT_LINE`
(round 3), ahead of everything else:

```
BEFORE ANYTHING ELSE, ANSWER THIS. Is this the right work? Not "is this design
correct" — is this the right ITEM, at the right TIME, given what the project is
for? If the work is sound but aimed at the wrong thing, say so first and say it
plainly. If you cannot tell from what you have been given, say what you would
need. Only after answering that, review what follows.
```

**Position is part of the change, not decoration.** A reviewer that has spent its
reasoning on schema details will ratify direction on the way out — failure mode
3 in a new place. It goes first or it is not a gate.

### B. Round 3 additionally emits a slate

Appended to `RESULT_LINE` only:

```
THEN PRODUCE A SLATE. Having seen this result, list the candidate items that
should be considered next. For each: the item number if you can identify one,
what resolving it buys, what it depends on, and your confidence. Rank them. If
the right next work is not on the build list at all, say that instead — a slate
that only contains items someone already wrote down cannot surface what is
missing.
```

**Where it lands.** The result file `reviews/done/<id>.<lineage>.result.md`,
which already exists, and the `result-reviewed` pause notification Eric receives
on his phone, which already exists. **No new table, no migration, no schema** —
per both lineages: *"just an output format and a place for it to appear."*

---

## WHAT THIS CARD DELIBERATELY DOES NOT DO

- **No structured slate format, no parser, no slate table.** The slate is prose
  in the result file. Turning it into a queryable structure is later work that
  the first slates should themselves surface.
- **No current-item pointer.** GLM called this the one thing to build alongside,
  so the first slate does not propose completed items. It is a separate card
  because it touches a different surface — `project_state`, which already carries
  keys like `current_direction` and `next_action` and has supersession built in,
  so it needs no schema change and survives `queue_items` being regenerated.
- **No cheap frame-checker.** See the token-cost section below.

---

## TOKEN COST — the objection Eric raised against his own ruling

Every review now spends reasoning on direction, including cards where the answer
is obviously yes. He raised this himself and proposed three cheaper mechanisms: a
local agent, a lower-reasoning model, or a script comparing against a priority
list.

**Measured while writing this card, and it changes the shape of that work:** the
machinery may already exist. `runtime/abstraction/guardrails.py` carries
`guardrail_intent_compliance` (line 2121) and `guardrail_intent_drift` (line
3238), both already invoked by the guardrail runner. Build-list item 0.6 records
`intent_drift` firing twice on a real run and being **right** both times —
0.63 DIVERGED, 0.42 SIGNIFICANT_DRIFT — on a run that deliberately deviated from
a spec whose own verification would have certified a falsehood.

The knowledge base also holds material, though not under the operator's term:
`"frame continuity"` returns **0**, but `intent drift` returns 164,
`original intent` 174, `scope creep` 621.

**So the cheap-check work is an INVESTIGATE, not a BUILD**, and it is not this
card. This card pays full price deliberately, because a gate that is cheap and
wrong is worse than one that is expensive and right, and nobody has yet measured
whether the existing scorer can carry this.

**Is paying full price now the right call, or should the gate wait for the cheap
path?** Eric's instruction is to start degraded and evolve. Say if you disagree.

---

## DEGRADED BY DESIGN — the property this card is buying

The first slates will be produced by a model reading a markdown list and
reasoning. They will propose items already done, miss dependencies, and not know
whether the last card succeeded. **That is expected and is not a reason to
defer.** The loop's improvement mechanism is that each bad slate surfaces a
concrete instance of what is missing, and the item that fixes it appears on the
next slate.

**Verified against the queue so that this is not a hope:** the loop's own
prerequisites are not buried. OPEN items by tier are T0 2, T1 11, T2 16, T3 8,
T4 5, and the apparatus items — 1.21, 2.13, 2.30, 2.32, 2.39, 2.40 — all sit in
tiers 1 and 2, where a slate working in tier order reaches them first. GLM raised
this exact risk and could not check it.

---

## MEASURED STATE

```
tools/advisor_review.sh    rounds 1/2/3, dual lineage, one packet, one hash
                           three pause stops, Telegram feed ONE-WAY
SCOPE_LINE / REPLY_LINE / RESULT_LINE   three constants, no frame question in any

queue_items                120 rows   OPEN 42  UNASSESSED 11  DONE 8
                                      HALF_DONE 3  no status stated 56
2.30's four questions      one answered (what was just done)
activity tables            newest rows 2026-06-18, 2026-06-24, 2026-08-31 x2
                           today: 17 advisor rounds written, ZERO activity rows
test suite                 cannot run — no interpreter on this host has pytest
```

---

## VERIFICATION — every claim a command that can fail

```bash
# 1. the gate is in all three constants, at the front
grep -c "BEFORE ANYTHING ELSE" tools/advisor_review.sh          # expect 3
# 2. it precedes the old text in each
python3 - <<'PY'  # asserts index(gate) < index(original opening) per constant
PY
# 3. the slate request is in RESULT_LINE only
grep -c "THEN PRODUCE A SLATE" tools/advisor_review.sh          # expect 1
# 4. syntax and every embedded heredoc still parse
bash -n tools/advisor_review.sh && ast.parse each PY block
# 5. LIVE: run one round-1 review and confirm both lineages answer the frame
#    question before the design question, in the recorded objection text
# 6. LIVE: run one round-3 result review and confirm a slate appears in
#    reviews/done/<id>.<lineage>.result.md
# 7. the pause notification carries the slate to the phone
```

**Check 5 is the one that can embarrass this card.** A gate that is present in
the file and ignored in the answer is a gate in name only. The check is not that
the text was sent — it is that the recorded objection *opens* on direction.

---

## WHAT YOU ARE NOT BEING ASKED

Not whether the loop should exist — Eric has ruled. Not the current-item pointer
or the cheap frame-checker, both separate cards. Not the slate's eventual
structured form.

Only: **would this card and its verification prove what they claim, what would
look like success while still being wrong, and — the gate's own question — is
this the right work to do first?**
