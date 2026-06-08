# Decisions Log — Hermes Harness / CIS
Generated: 2026-06-08 19:39 UTC | Run: run-38bc43b972d8
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

| Date | Decision | Reason | Status | Evidence |
|------|----------|--------|--------|----------|
| 2026-06-08 | [ADR-SEED-010] Project isolation model: --project-root: Each CIS-managed project has its own git repo / project root. Th | Eric Gate approved 2026-06-08 | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-006] Spine migration strategy: spine_schema.sql is the verified Tier 4.1 two-table minimum. Extensions use num |  | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-005] HERMES_CIS_BRIEFING_PATH is transitional: Retired at Tier 5.3 after AGENTS.md canary passes all 4 active  |  | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-004] Browser role enforcement at router layer: Role badge derived from gateway endpoint/profile only. Implemen |  | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-003] Role identity must be runtime-derived: Hermes role identity must come from HERMES_HOME and gateway endpoi |  | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-002] Verification-hardening rule: V4 Implementer self-report is not a source of truth. Completion accepted onl |  | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-001] Dependency graph build order: CIS is built tier by tier per CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md. Nothing b |  | DECIDED | spine record |
| 2026-06-07 | [ADR-T44-001] Tier 4.4 migration: Four tables added for Tier 5 export dependencies |  | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-009] HCP export is currently CIS-scoped: generate_hcp.py assumes the CIS infrastructure project, including CIS | Architecture debt logged proactively before multi-project expansion begins. | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-008] External advisor packet remains permanent: PROJECT_CONTEXT_PACK_UPLOAD/HCP_* remains the canonical extern | This preserves Eric's adversarial workflow: Hermes remains the internal operatin | DECIDED | spine record |
| 2026-06-07 | [ADR-SEED-007] AGENTS.md gateway loading mechanism: AGENTS.md is loaded from cwd or TERMINAL_CWD in gateway mode, not au | Tier 5.2 investigation found _load_agents_md checks cwd only. run_agent.py uses  | DECIDED | spine record |
