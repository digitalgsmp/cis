# Model Roles and Protocol — CIS Advisor Loop
Last updated: 2026-06-01 (CIS Deterministic Pipeline Decision)

## CIS Pipeline Roles

| Label | Agent | Port | Model | Pipeline Lane | Function |
|-------|-------|------|-------|---------------|----------|
| Flash / Research | hermes-prime | 8642→8800 | deepseek-v4-flash | RESEARCH | Evidence firewall (NeMo) + topic grounding |
| V4 Drafter | hermes-v4pro | 8645 | deepseek-v4-pro (xhigh) | DRAFT | Proposal author from research + spine briefing |
| V4 Reviewer | hermes-r1 | 8643 | deepseek-v4-pro (xhigh) | REVIEW | Adversarial challenge. Emits OBJECTIONS or CONSENSUS_REACHED |
| V4 Implementer | hermes-v4impl | 8646 | deepseek-v4-pro (xhigh) | IMPLEMENT | Executes FINAL_DIRECTIVE only. No deliberation |
| Verifier | Bash/Python | — | — | VERIFY | Deterministic gate scripts. PASS or FAIL. No LLM |
| State-Write | Gated worker | — | — | STATE_WRITE | Writes verified results to SQLite spine |

**Qwen (hermes-qwen)** remains active on port 8644 but paused from active pipeline.
Future judge/evaluator role.

## External Advisor Protocol

| Advisor | Role | Context Source | Authority |
|---------|------|---------------|-----------|
| Hermes | Root operator, pipeline engine | AGENTS.md (native, Phase E target) | Deterministic context owner |
| ChatGPT | External advisor, escalation reviewer | Generated HCP exports | Review, consult. No execution |
| Claude | External advisor, proposal author | Generated HCP exports | Review, consult, draft proposals when asked |

## Pipeline Protocol

1. **TRIAGE:** Router creates Kanban card, assigns Research profile
2. **RESEARCH → DRAFT → REVIEW ↔ LOOP:** Adversarial deliberation. 2-3 rounds typical before CONSENSUS_REACHED
3. **CONSENSUS_REACHED:** Structured Reviewer signal meaning no material objections remain
4. **ERIC_GATE:** Eric reviews resolved proposal. Pass → IMPLEMENT. Redirect/Insight → DRAFT
5. **IMPLEMENT:** V4 Implementer executes FINAL_DIRECTIVE only
6. **VERIFY:** Deterministic scripts check evidence independently
7. **STATE_WRITE:** Only after VERIFY PASS. Writes to SQLite, triggers export, git commit

## Why V4 Models are Direct (not through NeMo)

NeMo's response pipeline strips `reasoning_content` and `reasoning_tokens` from
DeepSeek thinking models (Gate 5C). V4 Drafter/Reviewer/Implementer are routed direct.
NeMo preflight is used for evidence collection only.

## Verification-Hardening Rule (2026-05-31)

**V4 Implementer self-report is not a source of truth.** Completion is accepted only after
deterministic evidence. Accepted evidence: git diff, test output, DB queries, endpoint
responses, service health, browser/UI state, independent reviewer pass/fail.

## Kanban Contingency

Kanban is preferred for pipeline coordination. Phase A must confirm `kanban.db` is shared
across profiles. If Kanban is profile-scoped or unavailable, pipeline uses Flask/CIS
database task tables as the coordination layer.
