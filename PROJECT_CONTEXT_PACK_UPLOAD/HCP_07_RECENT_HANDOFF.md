# Recent Handoff — Tier 0–4 Complete, Tier 5 Next
Date: 2026-06-06
Session: Tier 2 Kanban → Tier 3 smoke test → Tier 4 SQLite spine → HCP reconciliation

## Tier 4 — SQLite Spine (2026-06-06)

### Tier 4.1 — Spine Schema (`88ea25f`)
- `runtime/schema/spine_schema.sql` — two-table minimum: workflow_runs + deliberation_rounds
- CHECK constraints on result, reviewer_signal, requires_eric_review
- UNIQUE(run_id, round_number), FK with ON DELETE CASCADE
- kanban_card_id + kanban_board linkage on workflow_runs
- max_consecutive_revisions for deadlock tracking

### Tier 4.2 — Database Layer (`0c19b4d`)
- `runtime/db/database.py` — 5 functions: init_db, insert_workflow_run, insert_deliberation_round, get_workflow_run, count_rounds
- Allowlist validation: result, reviewer_signal, positive ints, booleans
- Parameterized queries only — no raw SQL from callers
- 14/14 tests passing

### Tier 4.3 — DB State Gate (`ec14615`)
- `tools/gates/gate_db_state.py` — deterministic verification gate
- Three commands: value, count, not-null with compound --where filters
- Table/column allowlist enforcement
- Exit codes: 0=PASS, 1=FAIL, 2=ERROR
- 11/11 tests passing including G4 deterministic round-3 check

### Database State
- `data/cis_memory.db` — seeded with Tier 3 smoke test data (run-05b24781207e)
- 1 workflow_run, 3 deliberation_rounds with real round-3 Drafter/Reviewer output
- Rounds 1–2 marked as `[ACTUAL OUTPUT NOT RECOVERED]` (orchestrator --output limitation)

## Tier 3 — Pipeline Smoke Test (2026-06-06, PASS_WITH_LIMITATIONS)
- Smoke card `t_5bde980a` created with Tier 2.8 schema on cis-pipeline board
- Orchestrator ran 3 DRAFT→REVIEW rounds without manual relay
- Result: ESCALATE with 3 substantive unresolved objections
- gate_runner.sh: all 5 gates PASS with clean tree
- Card archived after evidence captured

## Tier 2 — Kanban Coordination (2026-06-06)
- Gateway env normalization: EnvironmentFile= added to 4 service files
- OQ-009 resolved: prime HERMES_HOME corrected to /home/eric/.hermes
- cis-pipeline board created, cross-profile visibility confirmed
- Systemd templates backed up to runtime/config/systemd/
- ENV_MANIFEST.md documented, proposals/ gitignored
- Limitation: Hermes v0.13 has no custom lanes — CIS stages in card metadata

## Previous: Tier 0/1 — Orchestrator + Gates (2026-06-05/06)
Tier 0 orchestrator at `9d84351`. Tier 1 base gates at `bc49beb`–`635a646`.
Gate runner at `635a646`.
