# Terms and Naming — CIS Advisor Loop
Last updated: 2026-06-01 (CIS Deterministic Pipeline Decision)

## Agents

| Name | Label | Pipeline Lane |
|------|-------|---------------|
| hermes-prime | Flash / Research | RESEARCH |
| hermes-v4pro | V4 Drafter | DRAFT |
| hermes-r1 | V4 Reviewer | REVIEW |
| hermes-v4impl | V4 Implementer | IMPLEMENT |
| hermes-qwen | Qwen (paused) | — |

## Key Terms

- **NeMo / NeMo Guardrails**: NVIDIA guardrail framework on port 8800. Evidence firewall for RESEARCH lane.
- **classify_route()**: 8-pass classifier. Routes prompts and creates Kanban cards.
- **CONSENSUS_REACHED**: Structured Reviewer signal indicating no material objections remain and the proposal is ready for Eric Gate.
- **FINAL_DIRECTIVE**: Approved implementation instruction accepted by V4 Implementer only. Deterministic routing by prefix.
- **pipeline run**: One tracked CIS workflow from idea/research through verified state update or failure.
- **state-write worker**: Gated worker/event that writes verified results into the project state spine only after verifier PASS.
- **bidirectional spine**: Verified project state that both briefs future pipeline runs and receives verified outputs from completed runs.
- **gate scripts**: Deterministic bash/Python checks that decide objective PASS/FAIL conditions. No LLM.
- **blackboard**: Shared task/pipeline artifact space where Research, Drafter, Reviewer, Implementer, and Verifier exchange structured artifacts.
- **Eric Gate**: Human sanity/output gate after CONSENSUS_REACHED and before FINAL_DIRECTIVE. Not bypassable.

## Architecture Terms

- **Hermes-native context root**: AGENTS.md auto-loaded by all profiles. Replaces transitional HERMES_CIS_BRIEFING_PATH.
- **Deterministic state spine**: SQLite schema organized around workflow events, not HCP document structure.
- **Generated HCP export**: HCP_ files produced by deterministic script from state spine. Not manually edited. Not canonical.
- **External advisor packet**: HCP_ files exported for ChatGPT and Claude. Read-only for external advisors.
- **Context-source correction**: Session (2026-06-01) where five competing context realities were identified.
- **Stale context failure**: Context that is out of sync with the state spine must fail verification.
- **Unified shared knowledge foundation**: The pipeline + spine + export system. Pipeline is the product. Knowledge is downstream of deterministic gates.
- **Verification gate**: Post-implementation check confirming results using deterministic evidence.
- **Kanban contingency**: If kanban.db is profile-scoped, fall back to Flask/CIS database task tables.
