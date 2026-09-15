# CARD REVIEW — specify the notification format. Do not approve mine; write it.

**You are being asked to SPECIFY A FORMAT, not to review a proposal.** Claude
Code has already tried three times and the operator rejected all three. Its
attempts are recorded below as failed data, not as a design to improve.

**Answer with the actual format.** Line by line, literally, as text that would be
sent. The operator's constraint: **it should only need a few lines to communicate
what is needed.**

---

## THE OPERATOR, IN HIS OWN WORDS, ACROSS FOUR MESSAGES TODAY

> "I read through the telegram messages, I can't determine if I am suppose to do
> anything from reading them."

> "This telegram user feature is still not clear cut describing the required user
> action. For the cards you just worked on I guessed and pasted the bash into
> you prompt."

> "None of this has explained to me what is happening in the context of the
> overall build. I am not a coder or architect and I am not really understanding
> what's being displayed in the context windows. Something seems to be working
> and even though it was difficult to track doing the manual transport, I feel
> even more detached from what is going on before."

> "where I am in the larger build is important but has to be plain language
> related to capabilities and functionality and not written as though I remember
> all the technical terms like current item pointer or what might have been on
> the previous card, frame gates or slate emission. What I mean by user
> experience is that as a non coder I am speaking in terms of I ask for it to do
> xyz, is it doing xyz and if not what needs to be addressed to make it work.
> That is what I should be choosing from."

> "Explain to me how I am expected to interpret and respond to this."

**He is not a coder.** He validates by checking output, not by reading code. He
does not remember component names between sessions. He received **eleven**
notifications today and could act on none of them.

---

## THE MESSAGE HE COULD NOT INTERPRET, VERBATIM

```
NEEDS YOU — work has run and been checked
card: loop-first-turn

*** THE EVIDENCE DID NOT SUPPORT EVERY CLAIM.
Something the card said it did was not proven.

advisor: UNPARSED
FRAME: RIGHT_WORK The card targeted the real gap: the operator was back to
choosing what to work on because nothing proposed alternatives. Two of three
pieces are built and verified — the frame questi…

evaluator: NOT_ESTABLISHED
The card claimed it would close the gap that put item selection back on Eric,
but the evidence shows Eric still carries information between tools and chooses
what to work on. The technical components …

WHAT THEY SUGGEST NEXT — advisor
WANTED: When a piece of work finishes, hand me a short list of what to do next,
in plain language I can choose from. [next-work proposal]
WORKS TODAY: No — the proposal step was built but has never actually run, so
nothing has ever handed me a list.
NEEDED: Make the step that produces the short list actually fire when work
completes, and write the list in the operator's own terms, not internal lab
WANTED: Tell me, at any moment, what the system is currently working on and
whether that is still active or already done. [current-item recorder]
...
WANTED: When

Full text: reviews/done/loop-first-turn.<lineage>.result.md

-----
TO PROCEED, in the terminal:
  bash tools/advisor_review.sh loop-first-turn --continue
IF YOU DO NOTHING: this stays stopped. Nothing runs, nothing is lost.
Replying to this message does nothing — the feed is one-way.
```

---

## WHAT CLAUDE CODE OBSERVED ABOUT THAT MESSAGE — treat as evidence, not as design

1. **It says NEEDS YOU and needs nothing.** There is no decision in it. The
   `--continue` command approves nothing and starts nothing; it clears a marker
   meaning "seen". Every stop carries the same NEEDS YOU banner whether or not a
   decision exists, so the one signal that should mean *act now* means nothing.
   This is the second time this defect has been introduced: an earlier version
   printed `signal: OBJECTIONS` on every review, which is a fixed internal value
   that appears whatever the reviewers said.
2. **`advisor: UNPARSED` is internal machinery.** It means the reviewer did not
   open its answer with the exact phrase the script scans for. It says nothing
   about the work. It reads as a failure and is not one.
3. **The text is cut mid-word** — `not internal lab`, `I cannot tel`, and a line
   that reads only `WANTED: When`. A character limit chopping reviewer prose.

**Claude Code's proposed rule, which you should accept, reject or replace:** send
a message ONLY when there is a decision the operator alone can make; everything
else goes to an on-demand view he can run when he chooses, and sends nothing.
Under that rule, today would have produced **zero** messages instead of eleven,
and the single genuine decision — choosing between four capabilities — would
have been the only thing sent.

**Do not defer to this.** It is one more Claude Code design and three have failed.

---

## THE THREE MOMENTS A MESSAGE COULD BE SENT

1. A plan has been written and not yet checked.
2. A plan has been checked by both reviewers and has not run.
3. Work has run and been checked.

**Which of these should send anything at all?** Say so. If a moment warrants no
message, say send nothing.

---

## WHAT THE SYSTEM CAN PUT IN A MESSAGE

Available without any new work: whether both reviewers saw the same document;
each reviewer's verdict; whether either judged the work aimed at the wrong thing;
whether the evidence supported the claims; the reviewers' own capability list in
the form *what was wanted / does it work today / what is needed*; whether
anything is blocked waiting on him; and the exact command that clears a stop.

**Constraints.** Plain text, no formatting. Under 4096 characters, and the
operator has asked for far less. He cannot reply — the channel is one-way, and a
reply reaches nothing. He will not remember component names, card names, or what
happened in a previous session.

---

## ANSWER WITH

1. **Which of the three moments sends a message.** For each: send, or send
   nothing, and why.
2. **The literal text of each message you would send**, as it would arrive on his
   phone. Write the actual lines. Use a real example from above if it helps.
3. **The one line that tells him whether he must act**, and how it differs when
   he must not.
4. **What you would leave out entirely** that is in the message above.

Do not describe the format in the abstract. Write it.
