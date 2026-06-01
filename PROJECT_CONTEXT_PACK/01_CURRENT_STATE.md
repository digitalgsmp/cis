# CIS Current State
Version: 2.6
Date: 2026-06-01 (UI-002 Complete)
Authority: Eric (Architect)

---

## Current Objective

Backend lifecycle observability (BE-001, BE-002, BE-002A, BE-002B) and
full interactive lifecycle UI (UI-002) are complete. All six lifecycle
action handlers (reviewer_dispatch, approve_draft_directive,
reject_proposal, confirm_directive, revise_directive, execute_directive)
are implemented and tested (14/14 passing).

Gateway issue OQ-009 resolved: hermes-gateway.service had incorrect
HERMES_HOME pointing to v4impl profile. Corrected to /home/eric/.hermes.
Service file now tracked in repo at runtime/config/systemd/.

Next: UI-003 readability/layout pass. Verifier BE-003 deferred.

## Model Roles

| Role | Port | Model | Reasoning | NeMo? | Function |
|------|------|-------|-----------|-------|----------|
| Flash/Research | 8642 | deepseek-v4-flash | — | Yes | Fast context, research |
| V4 Drafter | 8645 | deepseek-v4-pro | xhigh | No | Proposal/directive author |
| V4 Reviewer | 8643 | deepseek-v4-pro | xhigh | No | Adversarial reviewer |
| V4 Implementer | 8646 | deepseek-v4-pro | xhigh | No | Bounded executor |
| Judge | NeMo 8800 | no model | none | IS NeMo | Future — deferred |
| Orchestrator | orchestrator.py | no model | none | No | Future — deferred |

## System State

- GitHub: private repo at https://github.com/digitalgsmp/cis
- All five gateways healthy (8642, 8643, 8644, 8645, 8646) + NeMo 8800
- hermes-gateway.service: HERMES_HOME=/home/eric/.hermes (corrected)
- Service file tracked: runtime/config/systemd/hermes-gateway.service
- Qwen: 8644, running but paused
- Context briefing: all gateway profiles have HERMES_CIS_BRIEFING_PATH
- NeMo: port 8800, cis_fast config

## Completed Directives

| Directive | Description | Commit |
|-----------|-------------|--------|
| BE-001 | Backend lifecycle observability enforcement | 83b8f7d |
| BE-002 | 6 lifecycle action handlers + 10 tests | 0ed9221 |
| BE-002A | source_actor response normalization | 3cdcfaf |
| BE-002B | target_agent / target_endpoint normalization | 97dd767 |
| UI-002 | Full interactive lifecycle UI + visibility fixes | 2caf40f |
| OQ-009 | Gateway HERMES_HOME fix + service tracking | cabd096 |

## Next Safe Phase

UI-003 — AdvisorChat readability/layout polish. Font sizing, panel spacing,
lifecycle badge readability, dispatch log styling. No backend changes.
