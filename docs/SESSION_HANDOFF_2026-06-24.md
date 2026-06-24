# Session Handoff — 2026-06-24

## State at close

**Phase:** PD CLOSED (enforcement primitive PROVEN). Phase 0 IN PROGRESS — loop-breaker for successful-repeat tool calls.
**HEAD:** ddf8667 + uncommitted changes (portal.html, app.py context limits)

## What was done this session

### Portal dropdown context sizes
- All 4 panel dropdowns now show actual model context sizes from OpenRouter:
  - Drafter/Implementer/Prime: 1M (DeepSeek V4 Pro/Flash)
  - Reviewer: 160K (DeepSeek R1)
  - Qwen local: 32K, GLM 4.7 Flash: 32K
  - Claude Opus 4.8: 200K, GLM 5.2: 1M, Mistral Large 3: 128K
  - DeepSeek Reasoner: 64K, Qwen3.6 Max: 128K

### Backend context limits
- app.py `/api/portal/chat` now uses per-model context_limit instead of hardcoded 128K
- Uncommitted — needs commit

### Phase PD findings committed to DB
- session_closeouts row 45: full mechanism findings + loop-breaker root cause
- NA-SEED-018: "Build loop-breaker for successful-repeat tool calls" (Phase 0, PENDING)
- BLK-SEED-006: Loop-breaker gap (ACTIVE)

### Spine regeneration
- AGENTS.md regenerated: Phase PD CLOSED, Phase 0 IN PROGRESS
- HCP files regenerated (all 11 files in PROJECT_CONTEXT_PACK_UPLOAD/)

### UI issues identified (NOT FIXED)
- "Monitor" in old UI (/ui/) is a text label, not a clickable button — confusing UX
- Roadmap tab in portal is actually working (iframe loads SPA correctly)
- Portal has no `/new` command — no way to start fresh chat session
- context bar shows % but at wrong scale for models with >128K context

## Current blockers
- [BLK-SEED-006] Loop-breaker gap: successful repeated identical tool calls invisible to guardrail
- [BLK-SEED-004] Google Drive backup integrity unverified

## Next actions
- [NA-SEED-018] Build loop-breaker for successful-repeat tool calls
- [NA-SEED-017] FD.1 MCP dispatch tools (IN_PROGRESS)

## Next Phase — Control Portal as Control Plane

Eric's direction for the next session:
1. Spec what needs to be done to flesh out the control portal to function as the control plane over the abstraction layer
2. Spec the abstraction layer itself
3. Understand what it means to run the whole system on top of a Hermes backend
4. Remote access and multi-user auth

The portal currently has:
- 4-panel multi-model chat with context bars
- Pipeline engagement detection (||PIPELINE_ENGAGE|| signal)
- Deliberation tab (run deliberation, view results)
- Control tab (submit intent, approve/reject)
- Roadmap tab (iframe to React SPA)
- No auth, no multi-user, localhost only

## Files changed (uncommitted)
- runtime/ui/public/portal.html — dropdown context size labels
- runtime/app.py — per-model context_limit in /api/portal/chat
