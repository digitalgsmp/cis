# The Operator Approval Interface — design proposal

**Date:** 2026-08-30
**Status:** PROPOSAL. Nothing here is built. Written because Eric asked what the
best solution might be, after a day of repairs he had no way to check.
**Queue item:** 1.10. Related: 4.10, 2.8, 1.8.

---

## The problem, stated once

On 2026-08-30 an assistant made about twenty commits to the spine, the pipeline
relay, the gate tooling and the ingest tools. Every one of them changed how the
system behaves. Eric approved none of them. He approved *descriptions* of them.

The assistant chose which checks to run, ran them, and reported the results.
Three times that day it caught its own errors — but it caught them, and it chose
to report them. Nothing in the system would have caught them otherwise.

Eric's own words for this, the same day: *"you are working on me correcting."*

That is the whole problem. Everything below is about closing it.

## What Eric can and cannot do — the real constraint

This is not a preference, it is the design input. Get it wrong and the interface
is decoration.

**He can:**
- read plain language and judge whether it matches his intent
- compare a claim against an observed output
- say yes, no, or "that's not what I meant"
- recognise when a direction feels wrong, better than anyone else on the project

**He cannot:**
- read code and judge whether it is correct
- know whether a test is the *right* test
- detect a confident, plausible, wrong claim

So an interface that shows him a diff has failed before it starts. An interface
that says "tests passed" has failed too — he cannot tell whether the test tested
anything. What works is a claim he can check against an output he can see.

## Why the earlier attempts did not land

Stated so this proposal does not repeat them.

`docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md` (2026-06-23) has the right principle
— *"Nothing executes without Eric seeing it"* — but it specifies a live panel UI
for pipeline runs. It is a big build, it never shipped, and it would not have
covered a single thing that happened on 2026-08-30, because none of that was a
pipeline run.

`runtime/cis_dashboard.html` is 3,194 lines, last modified 2026-05-04, unchanged
since. The 13 `gate_11a_*`/`gate_11b_*` scripts written to guard its approval UI
have never executed once.

The common failure: **they were interfaces looking for a workflow.** This
proposal starts from the workflow and adds the smallest interface that serves it.

## The mechanism: a Work Order

One artifact per unit of work. Not per commit — per *thing being fixed*. On
2026-08-30 that would have been four documents, not twenty: the foreign keys,
the secret filter, the Chroma lock, the gate repairs.

Twenty approvals in a day is not review. It is noise, and he would have stopped
reading at the fourth. The unit matters as much as the content.

A Work Order has two halves, and the second is where his real leverage sits.

### Half one — before the work (authorise)

| section | what it says | why he can judge it |
|---|---|---|
| **What is broken** | plain language, one paragraph | it is his system; he knows if it matters |
| **Evidence it is broken** | actual command output, pasted | he compares a number to a claim |
| **What will change** | in behaviour, not in code | he can say "that's not what I want" |
| **What will prove it worked** | *the exact check, named in advance* | this is the load-bearing part |
| **If it goes wrong** | what breaks, and is it reversible | tells him how much care to spend |
| **Blast radius** | what else touches this | tells him what to watch afterwards |

**The predicted-proof line is the mechanism that does the work.** Naming the
check *before* doing the work means a wrong result has to survive a check chosen
while the outcome was still unknown. It is the difference between "I verified
it" and "here is the thing I said would prove it, and here is what it printed."

This is not new discipline — the operator rules already require it (*"Say what
output would prove the change worked, before making it"*). What is missing is
that nothing records it, so nothing can hold the work to it.

### Half two — after the work (accept)

The same document, extended. This half cannot be written in advance, which is
what makes it evidence rather than intent.

- **The predicted check, run, with its actual output pasted in.** Not a summary
  of the output. The output.
- **Before and after, as comparable numbers.** *80 foreign-key violations → 0.*
  *48 secret values → 0.* He can read those without reading code.
- **What was not done**, and why. Scope that was dropped, tests that were
  skipped, things left broken.
- **What deviated from the plan**, including mistakes found and corrected on the
  way. On 2026-08-30 there were three. They belong here, not in conversation.
- **How to undo it**, concretely — the backup path, the revert command.

Then he accepts or rejects. Rejecting does not mean the code is wrong; it means
the account of it is not good enough to accept.

### Tamper evidence

Both halves hashed, the way the Eric Gate briefing already is. The hash fixes
what he read at the moment he approved it, so the record shows the decision he
actually made rather than a document edited afterwards.

## Not everything needs approving

Requiring a Work Order for every action would collapse under its own weight in
an hour. Four classes, by consequence:

**Class 0 — reading.** Searches, greps, tests, reading files, running read-only
checks. **No approval.** Logged, so the record shows what was looked at. Most of
any session is this.

**Class 1 — reversible, contained.** A new tool, a new document, a change to
something with no dependants. **Approval after, not before.** He reads the
outcome half and accepts or rejects.

**Class 2 — enforcement, schema, or the live path.** Guardrails, gate scripts,
the spine schema, `pipeline_relay.py`, the ingest tools. **Approval before and
after.** Everything on 2026-08-30 was Class 2.

**Class 3 — irreversible or destructive.** Deleting data, dropping a collection,
rewriting history, anything with no backup path. **Approval before, with the
irreversibility stated in its own sentence and acknowledged separately.**

The class is declared in the Work Order and is itself checkable — a change
touching `enforcement/` that declares Class 1 is a lie a script can catch.

## What stops a false Work Order

The honest question, and the reason this is not sufficient on its own.

Nothing above prevents an assistant writing a confident, wrong Work Order. Three
things reduce it, and only the third is real enforcement:

1. **The check must be reproducible by someone else.** Every proof line is a
   command Eric — or another agent — can re-run and get the same output. A proof
   that only exists in the assistant's report is not a proof.

2. **The check is named before the outcome is known.** Fabricating then requires
   either predicting the wrong check, which shows, or faking output, which is a
   different and much larger step.

3. **A verifier that is not the author.** The Work Order is checked against the
   actual diff by something with no stake in it — the pipeline's own verify
   role, or a second model. *Does the diff do what the order says? Does the
   named check actually test the claim? Was anything changed that the order does
   not mention?*

Point 3 is the one that closes the loop, and it is the same separation HASE
insists on and 4.10 already records: **the evaluator must not be the builder.**
Without it, this is a better-organised version of trusting the assistant.

## What this does not solve

- **A wrong claim that passes its own check.** If the check is honest but
  measures the wrong thing, it passes. The verifier reduces this; nothing
  removes it.
- **Judgement about whether the work was worth doing.** That stays with Eric,
  which is correct.
- **Volume.** Four Work Orders a day is sustainable. Fifteen is not. If the
  system starts producing fifteen, the unit is drawn too small.

## Recommended build order

Smallest thing first, each step useful alone.

1. **The Work Order as a file.** A folder, one markdown file per work item,
   rendered by the same code that renders the Eric Gate briefing. **No new UI.**
   That renderer is proven — it produced a readable briefing today, with a stable
   hash. Reuse beats building.
2. **Record it in the spine.** A table, so a Work Order is a row with a hash and
   a decision, not a loose file. Approval reuses `record_decision.py`, which now
   works.
3. **Enforce the class rule.** A pre-commit check: a commit touching Class 2
   paths must reference an approved Work Order. **It ships with an off switch,
   tested before it is armed** — the record requires this of every guardrail, and
   a gate that can brick the repo is worse than the gap it closes.
4. **Add the independent verifier.** Point the existing verify role at the Work
   Order and the diff. This is where it stops depending on the author's honesty.
5. **A served view, only if reading files becomes the bottleneck.** Not before.
   The portal failed because it was built before the workflow existed.

Steps 1 and 2 are days, not weeks, and reuse code that already works. Step 4 is
the valuable one and depends on the pipeline completing runs reliably — which is
item 1.1, in progress as this was written.

## Decisions that are Eric's, recorded as open

1. **Does a rejected Work Order block the commit, or just record the objection?**
   Blocking is stronger and can stop work when he is unavailable.
2. **Is Class 1 approval required, or is a notification enough?** The lighter
   choice keeps the load down; the heavier one keeps the record complete.
3. **Where do Work Orders live** — in the repo, so they are versioned with the
   change, or in the spine, so they are queryable? Both is possible and costs
   duplication.

None of these block starting. Step 1 is the same under every answer.

---

## The one-line version

He already has the artifact — the Eric Gate briefing renders exactly what he
needs to read. What is missing is that assistant work never passes through it,
and that nobody but the author ever checks whether the account is true.
