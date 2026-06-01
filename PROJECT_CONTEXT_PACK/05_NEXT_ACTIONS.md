# Next Actions — CIS
Last updated: 2026-06-01 (UI-002 Complete)

## Current Next Action

**UI-003 readability/layout pass** — AdvisorChat UI polish: font sizing,
panel spacing, lifecycle badge readability, dispatch log styling.
No backend changes. No new features.

## Completed
- Phase 0 — Boundary docs ✅
- Phase 1 — Proxmox snapshot fix ✅
- Phase 2 — Gateway verification ✅
- Phase 3A/3B — Context loader + auto-continuation ✅
- Phase 4A — Freshness verifier + wrapper gate ✅
- Gates 2-7D — V4-Pro gateway, NeMo, Tavily, Advisor routing ✅
- Router v0.1 — AdvisorChat input router ✅
- Phase 0 Recovery — Git versioning + gateway repair + context injection ✅
- ALLOV1-BE-001 — Backend lifecycle observability enforcement ✅
- ALLOV1-BE-002 — 6 lifecycle action handlers + 10 tests ✅
- ALLOV1-BE-002A — source_actor response normalization ✅
- ALLOV1-BE-002B — target_agent / target_endpoint response normalization ✅
- ALLOV1-UI-002 — Full interactive lifecycle UI + visibility fixes ✅
- OQ-009 — Gateway HERMES_HOME corrected to /home/eric/.hermes ✅
- hermes-gateway.service tracked at runtime/config/systemd/ ✅

## Deferred
- ALLOV1-BE-003 — Verifier (after UI-003)
- Phase 4B — Knowledge base extraction (deferred until infra stable)

## Do Not Start Yet
- Pass 5 implementation
- Unified memory build
- VDB pipeline rebuild
- Discord/Telegram gateway
- Judge implementation (architecturally blocked)
