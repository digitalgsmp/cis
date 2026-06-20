# NEXT SESSION — START HERE

Read DEV-PIVOT-17_ENFORCEMENT_ARCHITECTURE.md first. It carries the current
direction (generated HCP files are stale — no session-to-spine write path yet).

## Two design tasks, front of queue:

### 1. Draft the enforcement primitive spec
Have Hermes draft `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` — PROPOSAL
ONLY, no implementation, no /opt/cis-control creation, no live enforcement files.
Full drafting instruction: see NEXT_SESSION_DRAFTING_INSTRUCTION.md (or the
DEV-PIVOT-17 summary). Routes through Claude audit + ChatGPT audit + Eric approval.

### 2. Design the DB-as-source-of-truth doc pipeline
Answers the doc-sync brief. DB/spine = authority; HCP + DEV-PIVOT = generated
advisor packets; no hand-maintained authority docs. Requires solving the
session-to-spine write path (currently missing) BEFORE building a DEV-PIVOT
generator. Hermes drafts the design → Claude + ChatGPT audit → Eric approves →
build. See DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md.

## Do NOT:
- Start inventory until the enforcement primitive is built and proven.
- Let Hermes create live enforcement files or write spine schema unsupervised.
- Build generators at closeout.
