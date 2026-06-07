# Decisions Log — Hermes Harness / CIS
Last updated: 2026-06-07 (Tier 5.3 closeout)

| Date | Decision | Reason | Status | Evidence |
|------|----------|--------|--------|----------|
| 2026-06-07 | ADR-SEED-007: AGENTS.md loaded from cwd/TERMINAL_CWD, not automatic git root | Tier 5.2 investigation found _load_agents_md checks cwd only; run_agent.py uses TERMINAL_CWD for gateway discovery | DECIDED | Tier 5.2 canary evidence, run_agent.py:6061, prompt_builder.py:1355 |
| 2026-06-07 | HERMES_CIS_BRIEFING_PATH retired at Tier 5.3 | AGENTS.md canary passed 4/4 active gateways; retirement safe | DECIDED | Commit 80f934c |
| 2026-06-07 | Service topology repair — hermes-gateway.service restored to Flash/Research | Auto-overwrite changed HERMES_HOME from .hermes to .hermes-r1 | DECIDED | Commit 353cef5 |
| 2026-06-06 | AGENTS.md generator + static config committed | Tier 5.1: generate_agents_md.py from spine | DECIDED | Commit ee8eb25 |
| 2026-06-06 | Context export state tables (4 new tables) | Tier 4.4: project_decisions, open_questions, next_actions, active_blockers | DECIDED | Commit b2e6c98 |
| 2026-06-01 | HCP files become generated exports, not manually maintained canonical source | Multiple competing context sources; Hermes-native deterministic state must be root | DECIDED | Claude/ChatGPT deliberation |
| 2026-05-31 | Verification-hardening rule: V4 Implementer self-report not source of truth | Implementer claimed changes must be verified by deterministic evidence | ACTIVE | 7 evidence sources defined |
