# Gate Scripts Analysis — 49 Scripts at `/mnt/projects/cis/enforcement/mwl-proof-v2/gates/`

## Context
Analyzed 2026-07-10. The gate scripts were written for the old tier-based CIS build process. They're baked into the Docker image at `/opt/cis-gates/` (root-owned, sealed) but NOTHING calls them during pipeline runs. The user asked: will they work in the current container pipeline? Answer: mostly no, but they serve as functional blueprints.

## Categorization

### Will Work As-Is (3 scripts)
- `gate_file_exists.sh` — pure filesystem check, no environment assumptions
- `gate_no_secrets.sh` — pure pattern scan, no dependencies
- `gate_git_state.sh` — checks `git -C /mnt/projects/cis` working tree. **Path is hardcoded** — inside container repo is at `/workspace/cis/`, needs path fix

### Will Break — Wrong DB Path (15 scripts)
All source `_gate_common.sh`, which hardcodes `CIS_DB_PATH="${CIS_DB_PATH:-/mnt/projects/cis/data/cis_memory.db}"`. Inside container the DB is at a different path. Fix is trivial — set `CIS_DB_PATH` env var or change the default. Scripts affected:
- `gate_research_artifact_present.sh`
- `gate_proposal_schema_valid.sh`
- `gate_review_round_valid.sh`
- `gate_consensus_signal_valid.sh`
- `gate_eric_approval_present.sh`
- `gate_implementation_artifact_present.sh`
- `gate_db_state.py` (hardcodes `DEFAULT_DB = "/mnt/projects/cis/data/cis_memory.db"`)
- `gate_build_state_coherence.py` / `.sh`
- `gate_closeout_complete.sh` (hardcodes `CIS_REPO=/mnt/projects/cis`)

### Will Break — Wrong Schema Assumptions (5+ scripts)
Query columns that may not exist or have changed:
- `gate_review_round_valid.sh` queries `reviewer_signal, objections_json, requires_eric_review` — verify these columns exist and are populated by the current orchestrator
- `gate_consensus_signal_valid.sh` expects `requires_eric_review` to be `1`
- `gate_implementation_artifact_present.sh` queries `workflow_run_artifacts` — does the current pipeline write to this table?
- `gate_eric_approval_present.sh` queries `eric_approved_at` — added by migration 0005, confirmed exists

### Will Break — External Dependencies (4 scripts)
- `gate_staleness.sh` calls `tools/pipeline/staleness_check.py` — may not exist or may be stale
- `gate_deliberation.sh` calls `tools/pipeline/reviewer_reconcile.py` — old CLI path, not container pipeline
- `gate_pre_execution_oversight.sh` calls `tools/pipeline/pipeline_dispatch.sh` — old CLI tool
- `gate_closeout_complete.sh` calls `tools/state_write.py`, `tools/closeout.sh`, `tools/export/generate_all.py` — three external scripts

### Will Break — UI/Tier-Specific (13 scripts)
- `gate_11a_*.sh` (6 scripts) — UI layout, nav groups, page regression for Tier 10/11
- `gate_11b_*.sh` (7 scripts) — Schema population, concurrency, idempotency for Tier 11B
- `gate_ui_*.sh` (4 scripts) — UI acceptance, method allowlist, no secrets in JSX, no write endpoints

### Security Gates — Already Wired (7 scripts)
- `gate_mcp_no_filesystem_write.py`
- `gate_mcp_no_network.py`
- `gate_mcp_readonly.py`
- `gate_chroma_no_secrets_in_results.py`
- `gate_chroma_secret_filter.py`
- `gate_eric_approval.py`
- `gate_escalation_packet.py`

These already fire in `container_gate_runner.py` (security only).

### Gate Runner (1 script)
- `gate_runner.sh` — sequencer. Runs base gates in order, exits on first failure, reports PASS/SKIP/FAIL counts. Never called by the pipeline.

## The "Functional Blueprint" Insight

Even though the scripts won't run directly in the container, they specify three things clearly enough to rebuild from:

1. **What to check** — the SQL query, grep pattern, or file command is in the script. The intent is unambiguous even if paths/columns need updating.

2. **What pass looks like vs what fail looks like** — every script has explicit exit code logic (0=PASS, 1=FAIL, 2=ERROR) with spelled-out thresholds (e.g., "drafter_output is not NULL, not empty, not 'NOT RECOVERED', and length > 50 characters").

3. **When it should fire** — each script's header says which pipeline stage it belongs to ("Stage: RESEARCH", "Stage: DRAFT", "Stage: CONSENSUS", "Stage: ERIC_GATE").

The pattern is also consistent: source `_gate_common.sh`, resolve `--run-id`, query the spine, pipe to Python for pass/fail logic, exit with the right code. That's a reusable template.

`gate_runner.sh` also shows the orchestration pattern — run gates in order, count PASS/SKIP/FAIL, exit on first hard failure, report totals. That's the Honesty Reporter from the guardrail spec (§1.7) already prototyped.

## What the Scripts DON'T Cover

The 49 scripts were built for the tier-based build process. They check "did the thing happen?" but NOT "is the thing any good?" The Tier 1 guardrails from the spec (sycophancy detection, scope compliance, content specificity, output schema validation) are NEW checks that need to be written from scratch.

## Rebuild Strategy

1. **Salvage ~15 scripts** — fix DB path, verify schema, adapt for container paths. These cover "did it happen?" checks (file exists, git state, DB artifact present, schema valid)
2. **Write new scripts** for "is it any good?" checks (sycophancy, scope drift, content depth, output validation). No existing gate script covers these.
3. **Wire via `gate_runner.sh`** or a Python equivalent that fires at the right pipeline phases

## Key Paths
- Source: `/mnt/projects/cis/enforcement/mwl-proof-v2/gates/` (49 scripts)
- Container: `/opt/cis-gates/` (baked into image, root-owned)
- Common: `_gate_common.sh` provides `resolve_run_id()` and `query_spine()` helpers
- DB path env var: `CIS_DB_PATH` (must be set for container)
