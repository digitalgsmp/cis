# Session 2026-08-25 — SKILL.md split, guardrail discovery, issue register

Operator: Eric. Method: manual relay, every claim verified by command.
Purpose of this doc: durable session record for KB ingestion, so future
pipeline runs can retrieve this work instead of the operator re-deriving it.

## Outcome

Fix-order item 1 (SKILL.md split) COMPLETE and verified end to end.
Run run-5c80ece4fdd0122d-1787703333 traversed BRAIN, INTENT_REVIEW, DRAFT,
PROPOSAL_REVIEW, consensus, and reached ERIC_GATE at 00:48.
Two agents (brain, review2) successfully wrote to references/pitfalls.md
during the run — brain 48099 to 49927 bytes, review2 to 50709 bytes.
This is the first confirmed agent skill write since the cap was hit.

## Root cause of the write failure

The mwl-proof wall blocks ALL MCP write tools. Agents READ the spine via
MCP cis-knowledge but cannot WRITE it. Per-profile SKILL.md files were
therefore the only contribution channel available to any agent.
All six copies grew past the 100000-char cap, so every write failed.

## What was executed

Per-copy split. Offsets differ per file and MUST be derived per file —
the Pitfalls heading sits at line 371 to 376 depending on the copy.
Pitfalls moved to a new references/pitfalls.md in each agent tree.
Lines 1..heading kept in SKILL.md with a pointer. All files newline-terminated.

Result: SKILL.md 52938 to 53000 bytes per copy (was ~100850).
references/pitfalls.md 48099 bytes, 64 bullets, in all six.
Backups: enforcement/mwl-proof-v2/skill-backups-20260825/
