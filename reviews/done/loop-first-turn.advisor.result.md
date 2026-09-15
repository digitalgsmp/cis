# Advisor review — loop-first-turn

- packet: `reviews/pending/loop-first-turn.md`
- advisor: advisor on port 8649, no tools
- run tag: loop-first-turn @ 2026-09-09T21:49:54-05:00
- at: 2026-09-09T21:50:29
- prompt_tokens: 1985
- completion_tokens: 914
- total_tokens: 2899
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The card targeted the real gap: the operator was back to choosing what to work on because nothing proposed alternatives. Two of three pieces are built and verified — the frame question appears first in all three review rounds, and the current-item recorder passes 32 checks. The third piece, the next-work proposal, was built but has never actually run, so the one thing that would change the operator's experience has not yet happened. The direction is correct; the result is incomplete.

VERDICT: NOT_ESTABLISHED

The evidence verifies two of three claims. The frame question is present in all three rounds, first position, with verdicts recorded and queryFRAME: RIGHT_WORK

The card addressed the actual gap: the operator was back to choosing what to work on because nothing proposed alternatives. Two of three pieces are built and verified — the frame question runs first in all three review rounds, and the current-item recorder passes 32 checks. The third piece, the next-work proposal, was built but has never actually run, so the one thing that would change the operator's experience has not yet happened. The direction was correct; the result is incomplete but not wrong.

VERDICT: NOT_ESTABLISHED

The evidence verifies two of three claims. The frame question appears first in all three rounds with verdicts recorded. The current-item recorder is thoroughly tested: it rejects nonexistent items, rejects finished ones, supersedes cleanly, survives queue rebuilds, and reports STALE correctly. What is missing is evidence that the proposal step actually runs and produces a short list for the operator. The output says plainly it has never run. Without seeing it produce even one proposal, the claim that reviewers hand the operator a short list is unverified. Also missing: evidence that the frame question ever changes an outcome — two RIGHT_WORK verdicts with zero changed outcomes is noted but insufficient, which the output itself acknowledges. The recorder also still depends on a human to move it, which the card disclosed but which means the claim "record which item is being worked" is only partially met.

What would look like success while still being wrong: the frame question gets asked every time and always returns RIGHT_WORK, but it never actually catches a wrong direction — it becomes a ritual. The recorder passes every test but never gets moved by the system, so it always points at stale or missing work. The proposal step runs and produces a list, but the list is drawn from the same 120-item document the operator does not read, written in terms he does not use, so he still ends up deriving his own choices.

---

SLATE

WANTED: When a piece of work finishes, hand me a short list of what to do next, in plain language I can choose from. [next-work proposal]
WORKS TODAY: No — the proposal step was built but has never actually run, so nothing has ever handed me a list.
NEEDED: Make the step that produces the short list actually fire when work completes, and write the list in the operator's own terms, not internal labels.

WANTED: Tell me, at any moment, what the system is currently working on and whether that is still active or already done. [current-item recorder]
WORKS TODAY: Partly — the recorder exists and is well tested, but nothing moves it automatically; a human still has to update it.
NEEDED: Connect the recorder to the work loop so it advances on its own when an item starts and marks itself stale when the item finishes.

WANTED: Before any review effort is spent, check whether this is even the right work to be doing, and tell me if it was not. [frame question]
WORKS TODAY: Partly — the question is asked first in every round and the answer is recorded, but it has never once changed an outcome, so I cannot tell if it is catching anything.
NEEDED: Run it enough times to see whether it ever catches a wrong direction; if it never does after enough rounds, change how it is asked so it is not just a courtesy.

WANTED: When the system tells me something is happening, say it in terms I use and show me where it sits in the overall build. [notifications in operator language]
WORKS TODAY: No — the operator reports the notifications use terms he does not use and do not place the work in the context of the whole build.
NEEDED: Rewrite the messages the system sends so each one says what just happened, what it is part of, and what is left, in the operator's own vocabulary.

WANTED: The system should carry information between its own tools without me moving anything by hand. [operator removed from the information loop]
WORKS TODAY: No — this is the original ask, and it is still not met; the recorder still needs a human, the proposal has never run, and notifications do not orient the operator.
NEEDED: This is not a separate item — it is what the four above combine to produce. Wire all four together and the loop stops depending on the operator to carry context.
