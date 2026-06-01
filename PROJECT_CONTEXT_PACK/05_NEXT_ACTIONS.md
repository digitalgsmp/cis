# Next Actions — CIS
Last updated: 2026-05-31 (Phase 0 Recovery)

## Current Next Action

**Phase 0 recovery complete.** Git versioning protects source.
All gateways healthy and context-aware.

**Phase 1 — Minimal Orchestrator Scaffold:**
Build orchestrator.py state machine with Drafter→Reviewer deliberation
loop only. No Judge, no Verifier, no UI changes. Goal: remove Eric from
manual relay.

After Phase 1: Phase 2 (NeMo/Python Judge), Phase 3 (Post-Execution
Verifier), then Phase 4B (knowledge base extraction, deferred).

## Completed
- Phase 0 — Boundary docs ✅
- Phase 1 — Proxmox snapshot fix ✅
- Phase 2 — Gateway verification ✅
- Phase 3A/3B — Context loader + auto-continuation ✅
- Phase 4A — Freshness verifier + wrapper gate ✅
- Gates 2-7D — V4-Pro gateway, NeMo, Tavily, Advisor routing ✅
- Router v0.1 — AdvisorChat input router ✅
- Phase 0 Recovery — Git versioning + gateway repair + context injection ✅

## Do Not Start Yet
- Pass 5 implementation
- Unified memory build
- UI redesign
- VDB pipeline rebuild
- Discord/Telegram gateway
- Knowledge base extraction (Phase 4B, deferred)
- Judge implementation (Phase 2, after orchestrator)
- Verifier implementation (Phase 3, after Judge)
