# Next Actions — Hermes Harness / CIS
Last updated: 2026-06-06 (Tier 0–4 complete — Tier 5 next per build plan)

## Current Next Action

**Tier 5 — Context Export Pipeline.** Per Dependency Graph Build Plan v2.0
(`docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`). Not started.

Scope: `generate_agents_md.py` (AGENTS.md from spine), AGENTS.md canary test
on all 4 active profiles, retirement of HERMES_CIS_BRIEFING_PATH, `generate_hcp.py`
(HCP export from spine), HCP export verification via `gate_export_agreement.sh`.

**Judge checklist is NOT next.** The plan says Tier 5 Context Export before Tier 6
Pipeline Integration. Only re-approval changes this ordering.

## Approved Build Order

| Tier | Description | Status | Commits |
|------|-------------|--------|---------|
| Tier 0 | Orchestrator scaffold | ✅ COMPLETE | `9d84351` |
| Tier 1 | Deterministic gate suite + runner | ✅ COMPLETE | `bc49beb`–`635a646` |
| Tier 2 | Kanban coordination layer | ✅ COMPLETE | `2989c5b` |
| Tier 3 | Pipeline smoke test | ✅ PASS_WITH_LIMITATIONS | — |
| Tier 4.1 | SQLite spine schema | ✅ COMPLETE | `88ea25f` |
| Tier 4.2 | database.py write/read layer | ✅ COMPLETE | `0c19b4d` |
| Tier 4.3 | gate_db_state.py verification gate | ✅ COMPLETE | `ec14615` |
| Tier 5 | Context export pipeline | ← CURRENT | Not started |
| Tier 6 | Pipeline integration | Gated on 5 | — |
| Tier 7 | Router reclassification | Gated on 6 | — |
| Tier 8 | MCP bridge | Later | — |
| Tier 9 | Chroma/VDB | Later | — |
| Tier 10 | CIS UI/custom displays | Later | — |

## Tier 3–4 Key Deliverables

- Smoke test: 3-round deliberation with no manual relay, ESCALATE with real objections
- `runtime/schema/spine_schema.sql` — workflow_runs + deliberation_rounds
- `runtime/db/database.py` — insert/query with allowlist validation
- `tools/gates/gate_db_state.py` — deterministic DB verification with compound --where
- `data/cis_memory.db` — seeded with smoke test data (gitignored)

## Known Limitations

- Orchestrator --output preserves only final-round detail (Tier 6 backlog)
- Hermes Kanban v0.13 has no custom lanes (CIS stages in card metadata)
- HCP files manually reconciled until Tier 5 export pipeline exists

## Do Not Start Yet

- Tier 6 Pipeline Integration (gated on Tier 5)
- Judge checklist (Tier 6 component, gated on Tier 5)
- SQLite schema expansion
- Orchestrator per-round output preservation
- UI changes
