# Advisor review — intent-bridge-verify

- packet: `reviews/pending/intent-bridge-verify.md`
- advisor: advisor on port 8649, no tools
- run tag: intent-bridge-verify @ 2026-09-11T23:56:45-05:00
- at: 2026-09-11T23:57:01
- prompt_tokens: 4723
- completion_tokens: 1053
- total_tokens: 5776
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

FRAME: RIGHT_WORKBuilding and testing the front-door gate is correct work — the two refusal paths that were exercised are the safety-critical ones. But the result is half a verdict: the negative paths are shown, and the one positive path (confirm, record, route) was never run, so we know the door locks but not that it opens.

VERDICT: NOT_ESTABLISHED
Claims 1 and 2 are substantially demonstrated: both refusals produced the expected message and exit code 2. However, the "must NOT write an intent_map row" and "must NOT dispatch" negative guarantees are not independently verified — we see command output andexit codes, but there is no evidence the intent_map table was checked and found empty, nor that no dispatch occurred. More critically, Claim 3 — the positive path (confirm on a non-implement direction writes a CONFIRMED row with eric_confirmed_at populated, then routes) — has NO reproduction output at all. The card promised three behaviors; only two were exercised. The third is the one that proves the system actually does something useful after it stops refusing. Without it, the card's claim is not established.

What is missing:
1. A live run of `--direction next --confirm` showing an intent_map row written with review_decision='CONFIRMED', eric_confirmed_at populated, and routing to the controlled-vocabulary entry point.
2. Post-condition checks for the two refusals: query intent_map showing no row, confirm no dispatch fired.

---

SLATE

WANTED: When Eric says "go ahead and do the next thing," the system should record that he said so, then hand the work to the right next step. [Claim 3 — the positive path]
WORKS TODAY: No — the refusals fire correctly, but the one run that should actually record and route was never shown, so we do not know the door opens, only that it locks.
NEEDED: Run the confirmed path live, show the record was written with Eric's confirmation timestamp, and show the hand-off to the next step actually happened.

WANTED: When the system refuses to act, it should leave no trace behind — no record, no side effects, no partial work started. [Claims 1 and 2 — post-conditions]
WORKS TODAY: Partly — we see the refusal messages and the correct exit codes, but nothing checks the database or the dispatch queue afterward to prove nothing leaked through.
NEEDED: After each refusal, look at the record store and the dispatch queue and show they are empty for that attempt. A refusal that prints the right words but still writes a row is a silent failure.

WANTED: The place the front door hands work to — the next step it routes confirmed work into — should actually exist and be ready to receive it. [Not verified — possible gap]
WORKS TODAY: Cannot tell — the card says routing goes to a "controlled-vocabulary entry point," but no evidence shows that target exists, is callable, or does anything when it receives work.
NEEDED: Confirm the routing target is real and functions; if it is a stub or does not exist yet, that is the true blocker, because a door that opens into a wall is still a wall. This may not be on any existing list — if it is not, it needs to be added as its own item.
