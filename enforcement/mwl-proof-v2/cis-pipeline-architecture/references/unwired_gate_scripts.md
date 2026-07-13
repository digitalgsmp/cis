# Unwired Gate Scripts Inventory (2026-07-10)

## Summary
- **Total gate scripts**: 52 (including `_gate_common.sh` and `test_tier_6_4_gates.sh`)
- **Wired into pipeline**: 22 (via `PHASE_GATE_MAP` + `SECURITY_GATES` in `guardrails.py`)
- **Unwired**: 26 real scripts + 2 `.pyc` artifacts + 1 test script + 1 common lib

## Unwired Scripts by Category

### Real Pipeline Gates — Should Be Wired (11)

| Script | Purpose | Where It Should Fire |
|--------|---------|---------------------|
| `gate_deliberation.sh` | Pre-execution oversight: dual-reviewer deliberation before Eric approval | Before Eric Gate (pre_menter phase or new deliberation phase) |
| `gate_eric_approval_present.sh` | Validates `eric_approved_at` is non-null in spine | At Eric Gate (verify phase, alongside `gate_eric_approval.py`) |
| `gate_escalation_packet.py` | Escalation packet completeness + hash verification | At escalation (new escalation phase or in closeout) |
| `gate_drafter_closeout.sh` | Verify Drafter closeout invariants (Tier 11C) | At closeout — Drafter-specific |
| `gate_reviewer_closeout.sh` | Verify Reviewer closeout invariants (Tier 11D) | At closeout — Reviewer-specific |
| `gate_chroma_secret_filter.py` | Security: filter secrets from ChromaDB results | When ChromaDB is queried (pre-discovery or verify) |
| `gate_chroma_no_secrets_in_results.py` | Security: verify no secrets in ChromaDB search results | When ChromaDB is queried |
| `gate_ui_acceptance.sh` | Tier 10 functional acceptance tests A1-A10 | When UI changes are made (menter/verify phase for UI tasks) |
| `gate_ui_method_allowlist.sh` | Security: verify UI only uses allowed HTTP methods | When UI code changes |
| `gate_ui_no_pipeline_bypass.py` | Security: verify UI doesn't bypass pipeline | When UI code changes |
| `gate_ui_no_secrets_in_jsx.sh` | Security: scan JSX for secrets | When UI code changes |
| `gate_ui_no_write_endpoints.sh` | Security: verify UI has no write endpoints | When UI code changes |

### Old Tier-Specific Gates — Need Evaluation (13)

These were built for old CIS tiers (11a, 11b) and check a specific version of the CIS UI/API that has since been rebuilt. Each needs to be evaluated: update to match current codebase and wire, or delete as obsolete.

| Script | Purpose | Status |
|--------|---------|--------|
| `gate_11a_layout_no_overlap.sh` | Verify no layout overlap in dashboard pages | Likely obsolete — UI rebuilt |
| `gate_11a_nav_groups.sh` | Verify nav groups exist in App.jsx | Likely obsolete |
| `gate_11a_no_writes.sh` | Verify dashboard API has no write endpoints | Superseded by `gate_ui_no_write_endpoints.sh` |
| `gate_11a_regression_pages.sh` | Regression test for pages | Likely obsolete |
| `gate_11a_removed_nav.sh` | Verify removed nav items are gone | Likely obsolete |
| `gate_11a_system_overview.sh` | Verify system overview YAML exists | Needs evaluation |
| `gate_11b_approve_schema.sh` | Verify approval schema in API | Needs evaluation |
| `gate_11b_concurrency.sh` | Verify concurrency handling | Needs evaluation |
| `gate_11b_idempotency.sh` | Verify idempotency | Needs evaluation |
| `gate_11b_no_goal_reference_create.sh` | Verify no goal reference CREATE | Needs evaluation |
| `gate_11b_no_orchestrator_import.sh` | Verify no orchestrator import in API | Needs evaluation |
| `gate_11b_no_veto.sh` | Verify no veto functionality | Needs evaluation |
| `gate_11b_one_post_only.sh` | Verify only one POST endpoint | Needs evaluation |

### Redundant / Duplicate (2)

| Script | Why Redundant |
|--------|-------------|
| `gate_runner.sh` | Chains base gates in sequence. Python `run_external_gates()` already does this — it's a runner, not a gate. |
| `gate_build_state_coherence.sh` | Shell version. Python version (`gate_build_state_coherence.py`) is already wired into the verify phase. |

### Not Real Gates (3)

| File | What It Is |
|------|-----------|
| `_gate_common.sh` | Shared library sourced by other scripts — not a gate itself |
| `test_tier_6_4_gates.sh` | Test script, not a production gate |
| `gate_db_state.cpython-311.pyc`, `gate_eric_approval.cpython-311.pyc` | Compiled bytecode artifacts — delete |

## Hardcoded Path Status

All wired scripts now have env-var fallback for container compatibility (fixed 2026-07-10).
The unwired scripts above still have hardcoded `/mnt/projects/cis` paths.
When wiring each script, apply the [Container Path Fix Pattern](container_path_fix_pattern.md):
- Shell: `CIS_REPO="${CIS_REPO:-/mnt/projects/cis}"`
- Python: `os.environ.get("CIS_DB_PATH", "/mnt/projects/cis/data/cis_memory.db")`
- Subprocess paths: `f"{os.environ.get('CIS_REPO', '/mnt/projects/cis')}/tools/..."`

## Wiring Priority

1. **Wire the 11 real pipeline gates** — these add actual verification coverage
2. **Evaluate the 13 old tier-specific gates** — update or delete based on current codebase
3. **Delete the 2 redundant/duplicate scripts** — they add maintenance burden without value
4. **Clean up .pyc artifacts and test script** — not production code
