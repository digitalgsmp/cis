# CIS Current State
Version: 2.5
Date: 2026-05-31 (Phase 0 Recovery)
Authority: Eric (Architect)

---

## Current Objective

Phase 0 recovery complete. GitHub private repo exists at
https://github.com/digitalgsmp/cis. All three V4 Pro gateways
(Drafter/Reviewer/Implementer) are healthy, context-aware, and correctly
modeled as deepseek-v4-pro with xhigh reasoning. Qwen is paused.
R1/DeepSeek Reasoner is retired from active assumptions.

Next objective: minimal orchestrator scaffold (orchestrator.py state machine)
to remove Eric from the manual relay role.

## Model Roles (Corrected Phase 0)

| Role | Port | Model | Reasoning | NeMo? | Function |
|------|------|-------|-----------|-------|----------|
| Flash/Research | 8642→8800 | deepseek-v4-flash | — | Yes | Fast context, research |
| V4 Drafter | 8645 | deepseek-v4-pro | xhigh | No | Proposal/directive author |
| V4 Reviewer | 8643 | deepseek-v4-pro | xhigh | No | Adversarial reviewer |
| V4 Implementer | 8646 | deepseek-v4-pro | xhigh | No | Bounded executor |
| Judge | NeMo 8800 | no model | none | IS NeMo | Deterministic PASS/FAIL checklist |
| Orchestrator | orchestrator.py | no model | none | No | Backend state machine |

**Important:** Judge is NOT a reasoning model. NOT Qwen. NOT Flash.
Orchestrator is NOT Flash. `hermes-gateway-r1` is a stale service name
only — actual role is V4 Reviewer. Qwen is paused.

## System State

- GitHub: private repo at https://github.com/digitalgsmp/cis, commit b1bcf7d
- V4 Drafter: 8645 healthy, context-aware
- V4 Reviewer: 8643 healthy, context-aware
- V4 Implementer: 8646 healthy, context-aware
- Flash/Research: 8642→NeMo 8800, running
- Qwen: 8644, running but paused
- Context briefing: all four gateway profiles have HERMES_CIS_BRIEFING_PATH
- NeMo: port 8800, cis_fast config

## Next Safe Phase

Minimal orchestrator scaffold (orchestrator.py state machine with
Drafter→Reviewer deliberation loop only). No Judge, no Verifier, no UI changes.
