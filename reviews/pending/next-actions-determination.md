# Next-step determination — post-verification + access reconfiguration

- VERSION: 1
- CHANGES: initial

## Intent (verbatim)

> "for the time being give the reviewers access and then run these questions
> through the review to determine next steps."

## Delta since queue-framing-v3 (what changed)

- V12 RESOLVED: migrations 0032/0033 are APPLIED to the live spine. `PRAGMA table_info(queue_items)` shows `status_changed_at`, `status_changed_by`, `check_class`; tables `queue_item_events` + `queue_sections` exist.
- V13 CONFIRMED: queue item 3.21 still OPEN. `need_status='OPEN'`, `need_raw='OPEN'`, `status_changed_at`/`status_changed_by` both NULL — the closure mechanism (`queue_set.py`) was built but never run against 3.21.
- Queue count corrected: 123 items (56 NULL-status, 44 OPEN, 11 UNASSESSED, 8 DONE, 4 HALF_DONE).
- D1 PROVEN: Claude Code sandbox built + kernel wall verified live + implementation-review wiring to 8643/8647 works.
- Verification scope grew 11 → 15 commits (4 new Drafter commits landed during the sandbox/wiring work).
- Reviewer access changed: KB retrieval (semantic + FTS) restored, and `cis_query` (guarded read-only SQL: SELECT/WITH/PRAGMA only, row-capped, cell-truncated) added. Reviewers now hold 21 read-only tools.

## Questions to determine next steps

1. ORDER — what is the correct next action, and the order after it?
   - a. Execute V1–V15 commit verification (execution evidence per commit)?
   - b. Close 3.21 with evidence via `queue_set.py` (V13's closure mechanism)?
   - c. Abandon/retire the stuck `ask_history.py` run (CL3)?
   - d. Something else first?
2. TOOL SPLIT — which remaining tasks are DETERMINISTIC (script-collected raw evidence, no LLM) vs NON-DETERMINISTIC (require reviewer judgment)? Intent: use deterministic tools wherever raw data exists; reserve reviewer judgment for alignment / trajectory / tangential-effect questions.
3. SCOPE — is expanding verification 11 → 15 commits the right reconciliation, or is there a smarter way to close the verification debt?

## GOAL_ALIGNMENT

- (seed 1) works from raw files — deterministic evidence over self-report.
- (seed 2) vision apparent — reviewers read KB intent history to judge alignment.
- (seed 3) checks and balances — dual-lineage reviewers determine next actions, not the Drafter.
