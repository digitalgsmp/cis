# Advisor review — intent-bridge-verify

- packet: `reviews/pending/intent-bridge-verify.md`
- advisor: evaluator on port 8650, no tools
- run tag: intent-bridge-verify @ 2026-09-11T23:56:45-05:00
- at: 2026-09-11T23:58:48
- prompt_tokens: 10079
- completion_tokens: 2893
- total_tokens: 12972
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The intent bridge is the clarify→confirm→gate→route artifact — the front door's enforcement layer. Testing that it refuses without confirmation and refuses dangerous actions outright is exactly what should come before trusting it with real routing. The work validates the gate before the gate is asked to let traffic through.

VERDICT: NOT_ESTABLISHED

The evidence establishes the two refusal behaviors (no-confirm refusal and implement-refusal) with live command output showing correct exit codes and messages. However, claim 3 — that with `--confirm` on a non-implement direction it writes an intent_map row with `review_decision='CONFIRMED'` and populated `eric_confirmed_at`, then routes to the controlled-vocabulary entry point — has no live reproduction. I see what it *would* record in the "NOT CONFIRMED" preview output, but I do not see evidence that the row was actually written to intent_map when `--confirm` was supplied, nor that `eric_confirmed_at` was populated, nor that routing to `tools/queue/propose_next.py` actually occurred. The card claims three behaviors; the evidence covers two.

---

SLATE

WANTED: The system should only take action on my requests after I confirm them, and should refuse certain dangerous actions entirely. [intent-bridge-verify]
WORKS TODAY: Partly — it correctly refuses to act without confirmation and refuses dangerous actions even with confirmation, but we have not verified it actually takes the confirmed actions correctly.
NEEDED: A test showing what happens when I DO confirm a safe request — does it record my approval in the tracking table and route to the right downstream system?

WANTED: When I confirm a safe request, the system should record that I approved it with a timestamp, then hand it off to the right specialist tool. [intent-bridge-verify — missing case]
WORKS TODAY: No — we only see what it *would* do in the refusal preview; we have no proof it actually writes the approval record or invokes the downstream tool when `--confirm` is present.
NEEDED: Run the bridge with `--confirm` on a non-dangerous direction and verify two things: a row appears in the intent tracking table with "CONFIRMED" status and a timestamp, and the appropriate specialist tool is invoked (or at least logged as dispatched).

WANTED: The front door should be the only way requests enter the system, so nothing can bypass the confirmation gate. [front-door-single-entry]
WORKS TODAY: Partly — the gate exists and refuses correctly, but we don't know if all requests actually go through it or if some paths can skip the bridge entirely.
NEEDED: Audit all entry points (CLI commands, API endpoints, direct tool invocations) and ensure none can execute without first passing through the intent bridge's confirmation check.
