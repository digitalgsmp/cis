# CIS Next Actions — Post-Hardening, Pre-Front-Door

**Updated:** 2026-06-17 | **Source:** Eric directive | **Status:** ACTIVE

## Overview

Hardening v2.0 is deployed. Shell hooks enforce pre-execution oversight on all
4 agent profiles. CIS is 25/27 build nodes complete. But the pipeline sits idle
because Eric interacts with Hermes bots directly, not through CIS.

## Immediate Priorities

### 1. Wire the CIS Front Door (CRITICAL)

Eric needs one entry point. He submits an intent → CIS router classifies it →
Drafter dispatched → Reviewer + Qwen deliberate → Eric Gate approves from phone →
Implementer executes.

The infrastructure exists (router, deliberation, gates). It needs to be the
DEFAULT path for Eric's interactions, not bypassed via direct bot messages.

### 2. Archive / Knowledge Base Integration

The archive drives contain Eric's vision in his own words. This is the shared
knowledge base material. Need specification for:
- How archive connects to the VDB (Chroma, Tier 9)
- How MCP provides archive access to all profiles
- How the knowledge base informs deliberation (cross-reference claims against archive)

### 3. Let Hardening Settle

Shell hooks are deployed. Gateways restarted. Use CIS for a few days. Find
edge cases before building more on top.

## Deferred

| Item | Reason |
|------|--------|
| Profiles migration (5→1) | Front door problem is higher priority. Current 5-install works. |
| External escalation API keys | Paused. Keep wiring, don't activate charges. Eric manually audits. |
| SWA application | Separate project, own repo, own Hermes backend |
| WIAS full operationalization | After CIS is feature-complete |
| UI overhaul | After profiles migration |

## Completed Today

- Hermes Hardening v2.0: shell hooks on 4 profiles, commit 2d485ff
- Build direction revised: SWA removed, archive added, profiles deferred
- Qwen independently verified shell hook mechanism before reviewing

## Current State

- 5 gateways: all healthy, all ports up
- 4 profiles hardened: Prime (8642), R1 (8643), Drafter (8645), Implementer (8646)
- Qwen (8644): inference-only, no hooks
- CIS pipeline: complete but bypassed in normal use
- Eric Gate: functional but only fires during deliberate pipeline tests
