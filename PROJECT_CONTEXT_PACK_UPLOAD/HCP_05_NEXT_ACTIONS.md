# Next Actions — Hermes Harness / CIS
Last updated: 2026-06-06 (Tier 0/1 complete — Tier 2 next per build plan)

## Current Next Action

**Tier 2 — Kanban Coordination Layer.** Per Dependency Graph Build Plan v2.0
(`docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`, committed `0ef6177`). Not started.

Scope: shared Kanban board creation, lane configuration, profile wiring, gateway
restart to pick up `HERMES_KANBAN_DB` + `HERMES_KANBAN_HOME` env vars.

**Judge checklist is NOT next.** The plan says Tier 2 Kanban before Tier 3 Judge.
Only re-approval changes this ordering.

## Approved Build Order

| Tier | Description | Status | Commit |
|------|-------------|--------|--------|
| Tier 0 | Orchestrator scaffold | ✅ COMPLETE | `9d84351` (2026-06-05) |
| Tier 1 | Deterministic gate suite + runner | ✅ COMPLETE | `bc49beb`–`635a646` (2026-06-06) |
| Tier 2 | Kanban coordination layer | ← CURRENT | Not started |
| Tier 3 | Judge checklist | Gated on 2 | — |
| Tier 4 | Verifier | Gated on 3 | — |
| Tier 5 | SQLite spine schema | Gated on 4 | — |
| Tier 6 | AGENTS.md export pipeline | Gated on 5 | — |
| Tier 7 | HCP export pipeline | Gated on 6 | — |
| Tier 8 | Router reclassification | Gated on 7 | — |
| Tier 9 | MCP bridge | Later | — |
| Tier 10 | Chroma/VDB | Later | — |

## Tier 0/1 Key Deliverables

- `runtime/orchestrator.py` + `runtime/orchestrator_config.yaml` — Drafter→Reviewer loop
- `tools/gates/gate_git_state.sh` — working tree verification
- `tools/gates/gate_service_health.sh` — port health check
- `tools/gates/gate_endpoint.sh` — HTTP endpoint string match
- `tools/gates/gate_no_secrets.sh` — pre-commit secret blocker
- `tools/gates/gate_file_exists.sh` — file + line count check
- `tools/gates/gate_runner.sh` — sequential gate orchestrator

## Do Not Start Yet

- Tier 3 Judge checklist (gated on Tier 2)
- Tier 4–10 (all gated on predecessor)
- SQLite schema creation
- Gateway service restarts (Tier 2)
- Retirement of HERMES_CIS_BRIEFING_PATH
- UI changes
