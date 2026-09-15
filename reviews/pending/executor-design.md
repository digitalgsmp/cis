# CARD REVIEW — how should the system that RUNS approved work be built?

**You are being asked to design, not to approve.** Your last answer assumed an
executor exists — "he does not choose whether to run it; the system does",
"run it automatically", "fix it automatically". **You never named it, and the
packet never told you what it is.** This packet tells you. Now say how it should
be built and where the human stops belong.

---

## FIRST — THE OPERATOR'S OWN DESIGN RECORD, WHICH YOU DID NOT HAVE

Written by Eric on 2026-07-03, recovered from the archive on 2026-09-04, two
months before the item that carries it was written. Verbatim, his typos:

> "this is not correct drafter has to stop for clarity and understanding check.
> then when approved it writes the spec and passes it to the reviewers. the pass
> is the only thing done with out waiting. the rreviewers have to stop to
> deliberate and reconcile any differences, **that is presented to the user again
> for clarity, understanding and alignment check.** if ok'ed it is returned to
> drafter for refinement or sent to the implementor. the implementor's work is
> quality checked and verified. **that is a stop where the user needs to be
> observing and making sure that what is being done is aligned with goal and
> intention.**"

**This contradicts what you both said.** You recommended sending nothing when a
plan has been checked and has not run. His design makes that an explicit stop —
"presented to the user again for clarity, understanding and alignment check."

**Do not simply reverse yourselves.** Your reasoning was that he cannot evaluate
a plan he cannot read, and that reasoning is sound. His design says he must see
it. Both can be true if what he is shown is not the plan but its meaning. **Say
how that stop should work such that it satisfies both** — or say his design
record is wrong on this point and why.

**Note the design also says which stops are NOT waits:** "the pass is the only
thing done with out waiting." Exactly one handoff runs unattended.

---

## WHAT THE EXECUTOR IS SUPPOSED TO BE

Named in the project's own instructions: a seven-role pipeline across six
gateway endpoints — **Router → Brainstorm → Drafter → Dual-Review (two lineages)
→ Eric Gate → Implementer → Verifier.** It runs in a container. It is the thing
meant to take approved work and carry it to a verified result.

**It has never done so.** Item 1.23: a code run has never completed end to end.
One documentation run completed. Two code attempts died before reaching the code
path — one on a billing error misreported as the model misbehaving, one on a
draft timeout with no cause recorded.

---

## THE QUEUE ITEMS THAT BUILD IT — all OPEN unless marked

```
1.14  Give the pipeline a stop button and validate its input
      Verified absent: the relay exposes eight routes, `grep -c cancel` = 0.
      No input validation, so a malformed intent enters and is caught downstream.

1.15  Remove Eric from the relay roles he still fills by hand
      "Human router, human triage clerk, human reviewer selector and human
      schema reconciler. The reviewer-implementer challenge loop halts on him;
      the Implementer-to-Verifier loop has no owner." Raised 5 times.
      Need: OPEN — "he is still the relay."

1.18  Cards are written and executed by the same party
      "A wrong card produces a result that satisfies a wrong EXPECT, and a
      review that checks the result against that EXPECT passes it."
      PARTLY ADDRESSED 2026-09-09: card review before execution now exists.
      Still true that one party writes AND executes.

1.3   Failure routing — not in code
1.4   Retry and escalation for agent failures — not in code
1.5   Commit route — approved work does not become canonical
1.9   Two approval paths, and the documented one does not continue
1.10  Assistant work reaches the code without ever passing a gate
1.7   Stream agent completions
4.19  A button that sends an issue card into the pipeline.
      Blocked by its own constraint: "Nothing routes in until a run can be
      stopped."
```

## WHAT ALREADY EXISTS AND WORKS

```
The Eric Gate            tools/eric_gate/record_decision.py — records a decision
                         of APPROVE | VETO | RETURN_TO_DRAFT after checking 13
                         preconditions, one transaction, writes nothing if any
                         precondition fails. 29 decisions recorded.
                         show_status.py reads state. build_briefing.py builds
                         what is decided on.
                         Its limit: every decision requires a workflow_run_id,
                         so it can only decide about pipeline runs.

The advisor loop         tools/advisor_review.sh — two lineages, one packet, one
                         hash, three rounds, a frame question first, three stop
                         points recorded as rows, one-way phone notifications.
                         This is what reviewed this packet.

The container            Seven role profiles, six gateway endpoints, running.
```

## WHAT IS ACTUALLY DOING THE WORK TODAY

**Claude Code — one agent with repo access.** It reads the queue, writes the
card, chooses which reviewers see it, reads the reviews, decides which
corrections to make, executes the change, writes the verification, and reports
the result. Measured today: **0 pipeline runs, 26 advisor rounds.**

That is item 1.18 in its strongest form, and item 1.15's "he is still the relay"
with the relay role moved from the operator to a single agent rather than
removed.

---

## WHAT TO ANSWER

1. **How should the executor be built, in what order, from the items above?**
   Which item is first, and what does each buy. Assume nothing exists that is
   not listed as existing.

2. **Where do the human stops go, and what is shown at each?** The design record
   names three moments where the user is involved and one handoff that runs
   unattended. Reconcile that with your position that he should not be asked to
   approve what he cannot evaluate. **What is shown at a stop such that a
   non-coder can judge alignment with goal and intention without reading code?**

3. **What must exist before any work runs unattended?** 1.14 says a run cannot
   be stopped. 4.19 says nothing routes in until it can. Is a stop button
   sufficient, or is more required.

4. **How does the party that writes the card stop being the party that runs
   it?** 1.18 is partly addressed by review before execution. What closes it.

5. **What in this list is NOT needed** — items that look load-bearing and are
   not, or that a different design makes unnecessary.

**Write the sequence and the mechanism. Do not describe principles.** If a queue
item is wrong, say which and why.
