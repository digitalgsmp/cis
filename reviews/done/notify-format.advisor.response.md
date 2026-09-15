# Advisor review — notify-format

- packet: `reviews/pending/notify-format.md`
- advisor: advisor on port 8649, no tools
- run tag: notify-format @ 2026-09-09T22:45:30-05:00
- at: 2026-09-09T22:46:16
- prompt_tokens: 2149
- completion_tokens: 1198
- total_tokens: 3347
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

This is the right work. The operator explicitly asked for a notification format he can interpret, rejected three attempts, and the task says to write the actual format. Nothing else is needed.

---

1. WHICH MOMENTS SEND A MESSAGE

Moment 1 — a plan has been written and not yet checked. Send nothing. Nothing requires him. The reviewers run next; he does not.

Moment 2 — a plan has been checked by both reviewers and has not run. Send nothing. He does not choose whether to run it; the system does. If reviewers found the plan targets the wrong thing, that is a work problem, not an operator decision.

Moment 3 — work has run and been checked. Send a message ONLY if the check found a problem the operator must decide how to handle: the work did something different from what he asked for, and the fix is a choice only he can make (what to prioritize, what to drop, what to re-scope). If the check passed, send nothing. If the check failed for a technical reason the system can fix on its own, send nothing.

Under this rule, today would have produced one message or zero. The eleven were all noise.

---

2. THE LITERAL TEXT OF THE MESSAGE

Here is the message for moment 3, when a real decision exists. Using the loop-first-turn example, where the evidence showed the work did not fully do what was asked:

```
You asked the system to stop making you pick what to work on next. It built two of three parts but the third — the part that actually hands you a short list of options — has never run. Nothing is broken; the step that produces the list was never connected to fire automatically.

You have two choices:
A) Tell the system to connect it so the list appears when work finishes.
B) Leave it for now and pick something else.

Reply is not available. To choose A, run this in the terminal:
  bash tools/next_work.sh --connect
To choose B, run this:
  bash tools/next_work.sh --defer
If you do nothing, this waits. Nothing is lost.
```

That is the entire message. Five sentences of context, two choices, two commands, one line on what happens if he does nothing.

If the decision were different — say the work targeted the wrong capability entirely — the same structure applies:

```
You asked the system to record what it is currently working on. The check found that it is not doing that. Instead it built something that proposes next work, which is a different thing you also asked for but not what this step was for.

The system can fix the aim and retry, or you can move on to a different task.

To fix and retry:
  bash tools/retry.sh --reframe
To move on:
  bash tools/retry.sh --skip
If you do nothing, this waits.
```

---

3. THE ONE LINE THAT TELLS HIM WHETHER HE MUST ACT

When he must act, the message opens with a line that names the choice:

```
You asked the system to stop making you pick what to work on next. It built two of three parts but the third has never run.
You have two choices:
```

When he must not act — which means no message should be sent at all — there is no line, because there is no message. The rule is: if there is no decision only he can make, the system sends nothing. He runs an on-demand command when he wants a status update:

```
bash tools/status.sh
```

That command prints a plain-language summary of what is working, what is done, and what is waiting. It sends nothing to his phone.

The distinction is not a line inside the message. The distinction is the presence or absence of the message itself. A message exists because and only because he has a choice to make.

---

4. WHAT I WOULD LEAVE OUT ENTIRELY

Leave out the NEEDS YOU banner. It appeared on every stop and communicated nothing. If the message exists, he needs to act; the banner is redundant. If he does not need to act, no message should be sent.

Leave out the card name. He does not remember card names between sessions and does not need to. The message names what he asked for in plain language instead.

Leave out advisor and evaluator labels, their verdicts, their frame questions, their evidence summaries, and any internal state like UNPARSED or NOT_ESTABLISHED. He is not reviewing the reviewers. He is making a choice about his build. The message gives him the outcome in terms of what he asked for and what works or does not.

Leave out the WANTED / WORKS TODAY / NEEDED capability list. That is reviewer output written for the system, not for him. If it tells him something he needs to know, translate it into the two-choice statement. If it does not, it is not in the message.

Leave out the Full text: line and the file path. He cannot use a file path from a phone. If he needs detail, the on-demand status command can show it.

Leave out the TO PROCEED / IF YOU DO NOTHING block as a separate section. Fold "if you do nothing, this waits" into the message as the last line. The commands go inline with the choices they correspond to, not in a separate terminal block at the bottom.

Leave out any text that is cut mid-word or mid-sentence. The character limit exists; the message should be short enough that it is never reached. If the message cannot fit in under 500 characters, the decision is too complex for a phone notification and should be broken into a simpler choice or shown via the on-demand command instead.
