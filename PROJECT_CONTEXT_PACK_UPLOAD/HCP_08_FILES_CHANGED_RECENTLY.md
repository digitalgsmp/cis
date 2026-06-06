# Files Changed Recently
Last updated: 2026-06-06 (Tier 0/1 complete — HCP reconciliation)

## Tier 1 Gate Suite + Runner — Build Session (2026-06-06)

### tools/gates/ — New Files
- `tools/gates/gate_endpoint.sh` — HTTP endpoint verification gate (`14fd08d`)
- `tools/gates/gate_no_secrets.sh` — pre-commit secret blocker gate (`82b506a`)
- `tools/gates/gate_file_exists.sh` — file existence/line count gate (`dac9d6a`)
- `tools/gates/gate_runner.sh` — sequential gate orchestrator (`635a646`)

### docs/ — New File
- `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` — canonical build-order reference (`0ef6177`)

### PROJECT_CONTEXT_PACK_UPLOAD/ — HCP Reconciliation (uncommitted)
- `HCP_01_CURRENT_STATE.md` — Tier 0/1 status, Tier labels, build plan reference
- `HCP_02_ACTIVE_ARCHITECTURE.md` — Tier 0/1 built artifacts, plan reference
- `HCP_04_OPEN_QUESTIONS.md` — OQ-017 (Tier ordering), OQ-018 (plan authority)
- `HCP_05_NEXT_ACTIONS.md` — Tier 2 next per plan
- `HCP_07_RECENT_HANDOFF.md` — Tier 0/1 completion handoff
- `HCP_08_FILES_CHANGED_RECENTLY.md` — this file
- `HCP_09_TERMS_AND_NAMING.md` — orchestrator, gate suite terms

**Build artifacts committed. Documentation reconciliation in progress.**

## Previous: Tier 0 Orchestrator (2026-06-05)
`runtime/orchestrator.py` + `runtime/orchestrator_config.yaml` committed (`9d84351`).

## Previous: Tier 1 Gate Suite Foundation (2026-06-05)
`tools/gates/gate_git_state.sh` (`bc49beb`) and `tools/gates/gate_service_health.sh` (`a5b123a`) committed.

## Previous: Phase A Substrate Verification HCP Closeout (2026-06-01)
HCP files updated. Phase A findings documented. Phase B gate scripts identified.

## Previous: CIS Deterministic Pipeline Decision (2026-06-01)
All 10 HCP_ files updated. Pipeline architecture documented.
