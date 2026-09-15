# Container working-state — block assessment

VERSION 2 — CHANGES: Block 1 (CIS_TG_NOTIFY_TOKEN not passed) is now FIXED.
`run_container.sh` sources secrets.env and passes `-e CIS_TG_NOTIFY_TOKEN`;
verified SET in container env (len 46), consumer polling.

## Intent (verbatim)

> "I am trying to get the container up to working state. make a card to have
> the reviewers judge what the current blocks to that is and let them use the
> new kb access."

## What "working state" means

The container pipeline is "working" when a card can run the full loop inside
it: Author → advisor review → Claude (sandboxed) build → pipeline review →
verification → evidence reaches Eric's phone, and Eric can release a pause from
the phone.

## Recent changes (this session — verify these yourself with your tools)

- Reviewer access widened to 21 read-only tools (restored semantic + FTS KB
  search; added `cis_query`, guarded read-only SQL).
- Semantic search fixed (local embedding model + pre-warm; was a 180s timeout).
- Telegram conflict cleared (host `hermes-r1` retired — it shared the evaluator
  token).
- TG2 two-way release built (`tools/reply_consumer.py` + entrypoint wiring +
  notify switched to `cis_notifyreply_bot`). Consumer running.
- `CIS_TG_NOTIFY_TOKEN` now passed explicitly via `run_container.sh` (`-e`
  flag, value sourced from secrets.env). Verified SET in container env.
- 8 stale PENDING pause rows superseded (0 remaining).
- Implementation-review token tracking added.

## Question

Using your read-only instruments — including the KB (semantic + FTS + `cis_query`)
and the queue/build list — determine the **current blocks** to the container
reaching working state. For each block: what it is, why it blocks, and the next
action to clear it. Order them. Do not restate the question; go to the evidence.

## GOAL_ALIGNMENT

- (seed 1) works from raw files — deterministic evidence over self-report.
- (seed 2) vision apparent — reviewers read KB intent history to judge.
- (seed 3) checks and balances — reviewers determine the blocks, not the Drafter.
