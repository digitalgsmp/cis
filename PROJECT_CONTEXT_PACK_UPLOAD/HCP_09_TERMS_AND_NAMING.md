# Terms and Naming — CIS Advisor Loop
Last updated: 2026-06-06 (Tier 0/1 complete — Tier 2 next)

## Agents

| Name | Label | Pipeline Lane |
|------|-------|---------------|
| hermes-prime | Flash / Research | RESEARCH |
| hermes-v4pro | V4 Drafter | DRAFT |
| hermes-r1 | V4 Reviewer | REVIEW |
| hermes-v4impl | V4 Implementer | IMPLEMENT |
| hermes-qwen | Qwen (paused) | — |

## Key Terms

- **CONSENSUS_REACHED**: Structured Reviewer signal. No material objections remain.
- **FINAL_DIRECTIVE**: Approved instruction for V4 Implementer only.
- **pipeline run**: One tracked CIS workflow from research through verified state update.
- **state-write worker**: Writes verified results to SQLite spine only after VERIFY PASS.
- **bidirectional spine**: Verified project state that briefs pipeline and receives verified outputs.
- **gate scripts**: Deterministic bash/Python checks. Exit 0 = PASS, non-zero = FAIL. No LLM.
- **blackboard**: Shared artifact space for Research/Drafter/Reviewer/Implementer/Verifier exchange.
- **Eric Gate**: Human sanity gate after CONSENSUS_REACHED, before FINAL_DIRECTIVE.

## Kanban Coordination Layer (Phase A Verified)

- **shared Kanban**: All Hermes profiles coordinate through one kanban.db. Achieved by setting `HERMES_KANBAN_DB` and `HERMES_KANBAN_HOME` to the same shared path in every profile `.env`. Coordinates work (tasks, lanes, assignments). Distinct from the SQLite state spine which stores verified knowledge.
- **HERMES_KANBAN_DB**: Env var that pins the kanban database file path. Required for cross-profile sharing. Set to `/mnt/projects/cis/data/kanban.db`.
- **HERMES_KANBAN_HOME**: Env var that pins the kanban root directory (board metadata, workspaces, logs). Required for cross-profile sharing because board registration is stored under `kanban_home()/kanban/boards/`. Set to `/mnt/projects/cis/data`.
- **kanban_home()**: Hermes function that resolves the kanban root. Defaults to `get_default_hermes_root()`. Overridden by `HERMES_KANBAN_HOME`.
- **Kanban coordination layer**: The shared Kanban board managing CIS pipeline task flow across profiles. Triage → Research → Draft → Review → Consensus → Implement → Verify → State Write. Coordinates work; does not store verified knowledge.
- **state spine**: SQLite database (`cis_memory.db`) storing verified project knowledge. Written only after VERIFY PASS. Distinct from Kanban coordination layer.

## Tier 0/1 Built Artifacts

- **orchestrator**: `runtime/orchestrator.py` — Python state machine that runs Drafter→Reviewer deliberation loop. Removes Eric from manual API relay. Bounded by timeouts and input truncation. Test mode for bounded execution.
- **orchestrator config**: `runtime/orchestrator_config.yaml` — drafter/reviewer timeouts, max rounds, input truncation limits.
- **gate scripts**: Standalone bash scripts at `tools/gates/` that exit 0 (PASS) or non-zero (FAIL). Deterministic. No LLM. Five base gates: git_state, service_health, endpoint, no_secrets, file_exists.
- **gate runner**: `tools/gates/gate_runner.sh` — chains base gates in sequence. Exits on first failure. Configurable via environment variables.
- **Dependency Graph Build Plan**: `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` — canonical build-order reference. Defines Tier 0–10 artifact ordering. Committed at `0ef6177`.

## Architecture Terms

- **Hermes-native context root**: AGENTS.md auto-loaded by all profiles. Replaces transitional HERMES_CIS_BRIEFING_PATH.
- **Deterministic state spine**: SQLite schema organized around workflow events.
- **Generated HCP export**: HCP_ files from deterministic script. Not manually edited.
- **External advisor packet**: HCP_ files for ChatGPT and Claude. Read-only.
- **Kanban contingency**: If shared Kanban fails in gateway context, fall back to Flask/CIS database task tables. Downgraded from primary to fallback after Phase A verification.
