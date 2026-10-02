# Decisions Log — Hermes Harness / CIS
Generated: 2026-10-02 23:47 UTC | Run: run-306d570078b3
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

| Date | Decision | Reason | Status | Evidence |
|------|----------|--------|--------|----------|
| 2026-10-02 | [ADR-WIASW-001] WIASW destination architecture — Word, Image, Action, Sound, Web: Records the long-range destination/pro | The long-range product architecture was clarified in conversation and existed no | DECIDED | spine record |
| 2026-10-02 | [ADR-WIASW-002] CIS is the deterministic substrate beneath WIASW, not the destination: Records CIS's destination role un | ADR-WIASW-001 records what the destination is; without this record the substrate | DECIDED | spine record |
| 2026-10-02 | [ADR-WIASW-003] Deterministic validation and perceptual review are different evidence: Applies to the WIASW destination  | The 16 failure modes CIS exists to prevent are all about trust in technical clai | DECIDED | spine record |
| 2026-10-01 | [ADR-XDEV-001] External-developer work is not durable until independently verified from the remote: For repository-chang | Reached during independent review and previously resident only in ChatGPT/Claude | DECIDED | spine record |
| 2026-10-01 | [ADR-XDEV-002] Repository checkpoint status must be visible in the recovery chain: The external recovery path must surfa | A rule that is persisted but never surfaced still depends on someone going looki | DECIDED | spine record |
| 2026-10-01 | [ADR-PIPE-006] Roadmap and queue are separate authorities; triage reconciles, it does not merge: Clarifies the relations | Reached during independent review. ADR-PIPE-001 fixes the phase order and ADR-PI | DECIDED | spine record |
| 2026-09-30 | [ADR-SEED-018] Layer ownership — what is CIS Layer 2 and what is Hermes Layer 3: Clarifies the layer assignment named bu | A reviewed pipeline overview mislabelled pipeline_relay.py / dispatch.py / guard | DECIDED | spine record |
| 2026-09-30 | [ADR-PIPE-001] Contained-pipeline forward sequence P0 through P6: Canonical forward sequence for contained-pipeline deve | Persists the reviewed reorientation of 2026-09-30 so future cards, queue orderin | DECIDED | spine record |
| 2026-09-30 | [ADR-PIPE-002] Legacy workflow_runs.status values are quarantined, never rewritten: Historical workflow_runs.status valu | Historical rows are evidence. Rewriting them to satisfy a later enum would destr | DECIDED | spine record |
| 2026-09-30 | [ADR-PIPE-003] Missing telemetry is itself state — the run read model may not infer from absence: Missing telemetry is m | A read model that treats an empty telemetry table as 'nothing happened' would re | DECIDED | spine record |
| 2026-09-30 | [ADR-PIPE-004] Queue item 1.23 end-to-end code run is the product proof, targeted at P4: Queue item 1.23 - 'a code run h | Live evidence that this is the real gap, read 2026-09-30: the EXECUTION phase ha | DECIDED | spine record |
| 2026-09-30 | [ADR-PIPE-005] Roadmap status vocabulary and required wording for pipeline reviews: Classification vocabulary for roadma | Roadmap reviews were collapsing four different conditions into 'not built', whic | DECIDED | spine record |
| 2026-09-30 | [ADR-SEED-017] Development phase rule — functionality first, refactor deliberately: CIS is in a functionality-first impl | Agents and external auditors were treating the documented target architecture as | DECIDED | spine record |
| 2026-09-09 | [ADR-3.21-001] queue_items carries no run link and no success field: queue_items answers what an item is and what its st | Dual-lineage advisor review 2026-09-09 (queue-3.21-r2). The join would inherit b | DECIDED | spine record |
| 2026-06-19 | [ADR-SEED-016] Enforcement Primitive Approved: TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md approved via dual-review (Claud | Dual-advisor audit passed. Eric approved. Proposal is the authoritative spec for | DECIDED | spine record |
| 2026-06-19 | [ADR-SEED-015] Enforcement architecture: three-layer process isolation: CIS enforces Hermes via root-owned /opt/cis-cont | 16 failure modes are LLM behavior failures, not future app features. Prompt/SOUL | DECIDED | spine record |
| 2026-06-16 | [ADR-SEED-014] BLK-SEED-005 refresh-bug root cause: get_default_hermes_root collapses onto prime unit: FALSE CLAIM — RES | FALSE CLAIM. Investigation proved prime was never poisoned. BLK-SEED-005 is RESO | DECIDED | spine record |
| 2026-06-09 | [ADR-SEED-012] Orchestrator validation contract: Orchestrator validates state-transition signals only via FINAL_JSON blo | The router/Kanban canary failed with ERROR because Drafter Round 2 output was mi | DECIDED | spine record |
| 2026-06-09 | [ADR-SEED-013] Retire Kanban as required pipeline transport: Kanban is no longer required for router, orchestrator, gate | Kanban was documented as temporary scaffolding in the June 6 smoke test. The spi | DECIDED | spine record |
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
