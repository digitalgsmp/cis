# Advisor review — notify-format

- packet: `reviews/pending/notify-format.md`
- advisor: evaluator on port 8650, no tools
- run tag: notify-format @ 2026-09-09T22:45:30-05:00
- at: 2026-09-09T22:47:37
- prompt_tokens: 2216
- completion_tokens: 2832
- total_tokens: 5048
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The operator has a concrete, recurring problem — he receives messages he cannot interpret and cannot act on. Specifying the notification format is exactly the work needed to fix that. This is the right item at the right time.

---

**1. WHICH MOMENTS SEND A MESSAGE**

Moment 1 — plan written, not checked: SEND NOTHING. The system hasn't validated its own plan yet. There is nothing for the operator to decide. Let the reviewers run.

Moment 2 — plan checked, not run: SEND NOTHING. If both reviewers approved, run it automatically. If either rejected, fix it automatically. The operator is not a coder and should not be asked to approve plans he cannot evaluate.

Moment 3 — work run and checked: SEND ONLY WHEN THERE IS A CHOICE THE OPERATOR ALONE CAN MAKE. If work succeeded and the next step is obvious, proceed silently. If work is done and nothing is queued, tell him. If reviewers disagree on what to do next, or there are multiple valid paths, give him the options in plain language.

Under this rule, most of today's eleven messages would not have been sent.

---

**2. THE LITERAL TEXT OF EACH MESSAGE**

There are exactly two message types.

**Type A: Decision needed** (work ran, something requires his choice)

```
DECISION NEEDED

The feature that gives you a short list of next steps when work finishes is not working yet. The list never appears.

Your options:
1. Try again — the system attempts to fix what is broken
2. Skip this — move on to the next feature
3. Stop — nothing runs until you give a new instruction

To choose: bash tools/pick.sh 1
Do nothing and work stays stopped. Nothing is lost.
```

Another example, for when all work is complete:

```
DECISION NEEDED

Everything queued is done. The system is idle.

Your options:
1. Ask for the next feature you want built
2. Ask for a status summary of what works now

To choose: bash tools/pick.sh 1
Do nothing and the system stays idle. Nothing is lost.
```

**Type B: Blocked on external input** (rare — something the system cannot resolve on its own)

```
BLOCKED

The system cannot continue because [one plain-language sentence describing the blocker].

What you can do:
[One or two concrete actions in plain language]

Until then, work stays stopped. Nothing is lost.
```

That is the complete set. No other messages are sent.

---

**3. THE ONE LINE THAT TELLS HIM WHETHER HE MUST ACT**

The first line is always one of:

- `DECISION NEEDED` — he must pick an option
- `BLOCKED` — he must do something outside the system

If neither applies, no message is sent at all. There is no third status line. There is no "FYI" or "WORK COMPLETED" or "REVIEW DONE" message. Silence means things are proceeding. He can check status on demand whenever he wants.

This is how it differs: the presence of a message IS the signal. No message means no action needed.

---

**4. WHAT TO LEAVE OUT ENTIRELY**

Everything in the example message that I would never send:

- Card names (`loop-first-turn`). He does not remember them between sessions.
- Reviewer internals (`advisor: UNPARSED`, `evaluator: NOT_ESTABLISHED`). These are machinery states, not information.
- Reviewer prose, whether truncated or full. He should not be reading essay-length analysis in a notification.
- The `NEEDS YOU` banner when no decision exists. It is noise that devalues the signal.
- References to previous cards, frame gates, slate emission, current item pointers, or any internal vocabulary.
- File paths (`reviews/done/loop-first-turn.<lineage>.result.md`). He will not open them.
- The `--continue` command when it does nothing meaningful. Commands appear only when they correspond to a real choice.
- Any mention of what reviewers "suggest next" as a block of text. If there is a genuine choice, it is distilled into numbered options. If there is no choice, it is not mentioned.
- The phrase "the evidence did not support every claim." This is reviewer language. Translate it to: what works, what doesn't, what happens next.
