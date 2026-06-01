# CIS Current State
Version: 2.4
Date: 2026-05-31
Status: LIVE — Router v0.1 complete. See canonical copy at /mnt/projects/cis/docs/CIS_CURRENT_STATE.md

## Quick Reference
- Router: classify_route() 8-pass classifier, /api/advisor/route, routing_decisions table
- Active panels: Research/Evidence (8800), V4 Drafter (8645), V4 Reviewer (8643), V4 Implementer (8646)
- Qwen (8644): deferred from UI, JUDGE_REQUEST backend-capable
- Next: Git versioning → Verification gate design → UI layout → Router validation → Verifier DAG → Phase 4B
- Verification rule: V4 Implementer self-report requires deterministic evidence (git diff, tests, DB, curl, service checks, UI, reviewer pass/fail)

## Model Roles
| Label | Agent | Port |
|-------|-------|------|
| Research / Evidence | hermes-prime | 8800 |
| V4 Drafter | hermes-v4pro | 8645 |
| V4 Reviewer | hermes-r1 | 8643 |
| V4 Implementer | hermes-v4impl | 8646 |
| Qwen (deferred) | hermes-qwen | 8644 |
