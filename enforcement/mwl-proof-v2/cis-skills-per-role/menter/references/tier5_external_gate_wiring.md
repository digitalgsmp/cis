# Tier 5: External Gate Script Wiring

**Commit:** ab7e629 (2026-07-10)
**File:** `runtime/abstraction/guardrails.py` — `run_external_gates()` + `_run_gate_script()`

## What Was Built

22 of the 48 pre-built deterministic gate scripts in `tools/gates/` are now called from the pipeline alongside the 34 native Python guardrails (Tiers 1-4). A subprocess wrapper maps shell/Python gate script exit codes to guardrail verdicts.

## Architecture

### `_run_gate_script()` — Subprocess Wrapper
- Takes a script name (e.g., `gate_no_secrets.sh`), optional args, env, timeout, and mode
- Runs via `subprocess.run()` — `python3` for `.py` scripts, `bash` for `.sh` scripts
- Exit code mapping: 0=PASS, 1=FAIL, 2+=SKIP (missing config/args)
- Returns a `GuardrailResult` with the same shape as native guardrails
- Handles `TimeoutExpired` and `FileNotFoundError` gracefully → SKIP
- Gate names get `ext_` prefix (e.g., `ext_gate_no_secrets`) for `gate_outcomes` recording

### `PHASE_GATE_MAP` — Declarative Phase Mapping
A dict mapping each pipeline phase to its gate scripts:

| Phase | Gates | BLOCK gates |
|-------|-------|-------------|
| brain | staleness, research_artifact_present | — |
| draft | proposal_schema_valid | — |
| review | review_round_valid, consensus_signal_valid | review_round_valid |
| pre_menter | git_state, pre_execution_oversight, final_directive_allowed | final_directive_allowed |
| menter | file_exists, implementation_artifact_present | — |
| verify | service_health, endpoint, db_state, build_coherence, eric_approval | eric_approval |
| closeout | export_agreement, closeout_artifact, closeout_complete | — |

### `SECURITY_GATES` — Fire on ALL Phases
- `gate_no_secrets.sh` (BLOCK) — scans staged files for secrets
- `gate_mcp_readonly.py` (ADVISORY) — no write SQL in MCP bridge
- `gate_mcp_no_filesystem_write.py` (ADVISORY) — no file writes in MCP bridge
- `gate_mcp_no_network.py` (ADVISORY) — no network imports in MCP bridge

### `run_external_gates()` — Main Entry Point
Called from `pipeline_relay.py` after each native guardrail block. Same signature pattern: phase, role, agent_output, run_id, proposal_file, project_root. Returns a `GuardrailReport` that gets passed to `record_gate_outcomes()`.

## Pipeline Wiring (pipeline_relay.py)

External gates fire after native guardrails at 7 insertion points:
1. **Brain** — after `run_guardrails(phase="brain")`
2. **Intent Review** — after both reviewers' `run_guardrails()`
3. **Draft** — after `run_guardrails(phase="draft")`
4. **Proposal Review** — after both reviewers' `run_guardrails()`
5. **Pre-Menter** — before Menter dispatches (new insertion point)
6. **Menter** — after `run_guardrails(phase="execution")`
7. **Verify** — after `run_guardrails(phase="verification")`

If external gates return `any_blocked`, the block propagates to the same escalation logic as native guardrails.

## Special Handling

### `gate_file_exists.sh` — Path Extraction from Output
For the Menter phase, `gate_file_exists.sh` needs a file path argument. The wrapper extracts paths from Menter's output using regex: `(?:Created|Modified|Updated)[:\s]+(/[^\s,\n]+\.py)`. If no path is found, it SKIPs gracefully.

### `--run-id` vs `--workflow-run-id`
Shell gates use `--run-id` (via `_gate_common.sh`'s `resolve_run_id`). Python gates use `--workflow-run-id`. The wrapper detects the script type and passes the correct flag.

### `--proposal-file`
Gates that need a proposal file (`gate_staleness.sh`, `gate_pre_execution_oversight.sh`) get it via `--proposal-file` arg. If no proposal file is provided, they SKIP gracefully.

## Container Path Mismatch — FIXED (2026-07-10)

Gate scripts previously hardcoded paths:
- `CIS_REPO=/mnt/projects/cis` (host path)
- `CIS_DB_PATH=/mnt/projects/cis/data/cis_memory.db` (host path)

In the container, the repo is at `/workspace/cis`. The wrapper passes `CIS_REPO` and `CIS_DB_PATH` env vars, but 4 wired scripts had internal hardcoded paths that ignored the env vars. These scripts SKIPped gracefully (exit 2 → SKIP) rather than crashing.

**Fix applied:** All 4 wired scripts with hardcoded paths patched to use env-var fallback:
- `gate_git_state.sh` — `CIS_REPO="${CIS_REPO:-/mnt/projects/cis}"`
- `gate_db_state.py` — `DEFAULT_DB = os.environ.get("CIS_DB_PATH", ...)`
- `gate_eric_approval.py` — cascade `CIS_SPINE_PATH` → `CIS_DB_PATH`; subprocess paths from `CIS_REPO`
- `gate_implementation_artifact_present.sh` — regex matches `$CIS_REPO` OR `/mnt/projects/cis` fallback

Dockerfile now installs `sqlite3` CLI and bakes `CIS_REPO`/`CIS_DB_PATH` into image ENV.

See `container-gate-wiring` skill [Container Path Fix Pattern](references/container_path_fix_pattern.md) for full fix recipe.

## Test Results (commit ab7e629)

Pipeline run `run-4dec3443458bceb1-1783702140`:
- 24 total outcomes (18 native + 6 external)
- External gates: 2 PASS, 2 FAIL (ADVISORY), 2 SKIP
- `gate_no_secrets` SKIP — container doesn't have repo at `/mnt/projects/cis`
- `gate_mcp_readonly` PASS — no write SQL in MCP bridge
- `gate_mcp_no_filesystem_write` PASS — no file writes in MCP bridge
- `gate_mcp_no_network` FAIL — network imports found in MCP bridge (ADVISORY)
- `gate_staleness` SKIP — no proposal file provided
- `gate_research_artifact_present` FAIL — no deliberation rounds for test run (expected)

## Remaining ~26 Gate Scripts (Not Wired)

The remaining gate scripts are:
- **11a/11b tier gates** (12 scripts) — UI-specific checks for old CIS tier-based build (layout overlap, nav groups, regression pages, schema approval, concurrency, idempotency, no-veto, no-orchestrator-import, no-goal-reference-create, one-post-only, no-writes, removed-nav, system-overview). These are dead code — the old tier system no longer exists.
- **Chroma gates** (2 scripts) — `gate_chroma_no_secrets_in_results.py`, `gate_chroma_secret_filter.py`. These need ChromaDB running to work.
- **UI gates** (5 scripts) — `gate_ui_acceptance.sh`, `gate_ui_method_allowlist.sh`, `gate_ui_no_pipeline_bypass.py`, `gate_ui_no_secrets_in_jsx.sh`, `gate_ui_no_write_endpoints.sh`. These check the React UI for security issues. Could be wired as a pre-commit or build-time check rather than pipeline phase.
- **Other** — `gate_drafter_closeout.sh`, `gate_reviewer_closeout.sh`, `gate_build_state_coherence.sh` (shell version, Python version is wired). Redundant or superseded.
