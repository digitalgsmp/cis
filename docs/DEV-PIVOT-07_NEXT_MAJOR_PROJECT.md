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

---

## Session Update — 2026-06-27: FRONT DOOR IS BUILT

The core gap identified in this document — "pipeline sits idle because Eric interacts
with Hermes bots directly" — has been addressed. The CIS abstraction layer is now live:

**What changed:**
- Front door: `POST /api/adapter/dispatch` classifies intents and routes to profiles
- Adapter layer: 5 endpoints on port 5000 (health, status, profiles, dispatch, chat)
- Human-readable status: `GET /api/adapter/status` — plain English, no JSON
- Knowledge base: 287,589 messages FTS5 + ChromaDB, `cis_search_knowledge` MCP tool
- Intent alignment: `POST /api/intent/alignment` checks proposals against Eric's words
- MCP bridge: 17 tools (up from 11), configured on all profiles

**What's still pending (Phase 1):**
- Prime gateway (8642) is DOWN — needs restart
- Gateway restarts needed to activate MCP tools
- Per-profile SOUL.md not written
- Qwen bind needs 0.0.0.0:8002 for container access

See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for full handoff.
Commit: 70e73bd.
