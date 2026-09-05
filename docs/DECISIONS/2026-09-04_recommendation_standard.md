# DECISION — agents recommend, they do not interrogate

**Date:** 2026-09-04
**Decided by:** Eric
**Status:** ACTIVE
**Affects:** queue item 1.8 (supersedes its framing), the Eric Gate, every container agent prompt

---

## The decision

The container agents must offer **informed, researched recommendations** rather
than asking Eric what he intends. The more knowledgeable models are expected to
say what best practice looks like, with the evidence and the reasoning behind it.
A choice is surfaced only where the evidence genuinely leaves one open.

## Why asking fails twice

**Eric is not a coder, so his intentions are not technically informed.** He can
say what he wants the system to do; he cannot specify it in engineering terms,
and asking him to is asking for a guess.

**The agents are stateless, so they carry no continuity of intention between
calls.** Even a good answer is gone by the next call. Retrieval hands an agent
facts; it does not hand it the thread of a decision.

So the question fails on both sides at once: he cannot answer it in the register
it was asked, and nothing remembers the answer if he does.

## The constraint — and it is half the decision

**Not enterprise logic slop.**

This is not a standard application and the development process is not a standard
one. A model asked for "best practice" reaches for enterprise defaults, because
enterprise practice is what has been written down. `docs/NEXT_SESSION.md` records
why that matters here: training data is overwhelmingly enterprise, it is how this
codebase grew ADRs, approval workflows, tiered build plans and governance
contracts with nobody deciding it should, and **the corpus is the only
counterweight, because nobody else wrote this method down**.

A recommendation must therefore be checked against Eric's recorded method before
it is offered. `bias_drift_detector` is the crude version of this — a term list —
and the record says it should be rebuilt on the corpus.

A recommendation that is sound in general and wrong for this system is not a
recommendation. It is the failure this decision exists to prevent.

## Relationship to queue item 1.8

1.8 says: give Eric options with their consequences, rather than a bare technical
question. **That stands as the floor.** A question mark with no options attached
is still a defect.

**This decision supersedes its framing.** Options with consequences are the
minimum, not the target. The standard is: bring a recommendation, and say which
one you would take and why. Surface a genuine choice only where the evidence
leaves one open — not as a way of moving the decision onto him.

## Open, and it should be closed before schema decisions

Eric raised incorporating **fundamental software development practices** roughly
a week before this date, and that conversation was lost in ongoing work. It has
not been recovered.

It should be recovered before schema decisions are made — those are exactly the
decisions where a recommendation has to be grounded in real practice and where a
wrong default is expensive to undo. The two mining passes over the Hermes
sessions (`design_intent`, `found_by` P7-design / P7b-design) did not surface it;
the raw session files are the place to look, since that is where the 2026-07-03
design record was eventually found after both indexes missed it.
