# Next Actions — Hermes Harness / CIS
Last updated: 2026-05-31 (Gate 7 closeout)

## Current Next Action

**Gate 7 closeout is complete.** The Advisor loop is verified end-to-end:
Fast/NeMo → V4-Pro R1 → V4-Pro R2 → V4-Pro R1 → Qwen Worker → Qwen Judge

Next session should:
1. Review updated handoff
2. Decide between: AdvisorChat UI usability test, Phase 4B knowledge base extraction, or deterministic verifier DAG planning

**Phase 4B — Extract Eric's intent from Google Drive chat transcripts** remains
the canonical next build objective. 12 files (3.4MB) downloaded, not yet extracted.

## Completed (Phases 0-7D)
- Phase 0 — Boundary docs ✅
- Phase 1 — Proxmox snapshot fix ✅
- Phase 2 — Gateway verification and repair ✅
- Phase 3A — Automatic Context Loader ✅
- Phase 3B — Automated Session Continuation ✅
- Phase 4A — Deterministic Freshness Verifier ✅
- Phase 4A Integration — Wrapper Freshness Gate ✅
- Gates 2-6 — V4-Pro Gateway, NeMo Guardrails, Tavily ✅
- Gate 7A — V4-Pro Preflight Evidence Injection ✅
- Gate 7B — Qwen Worker/Judge Gate ✅
- Gate 7C — Mixed Prompt Classification Tuning ✅
- Gate 7D — Full Advisor Loop Smoke Test ✅

## Immediate Queue
1. AdvisorChat UI usability test (verify full loop in browser)
2. Phase 4B — Knowledge Base Extraction
3. Deterministic verifier DAG planning (Archon-style)
4. Phase 5 — Notes and Open Items

## Do Not Start Yet
- Pass 5 implementation
- Unified memory build
- Model routing changes
- Briefing Center UI redesign
- VDB pipeline rebuild
- Discord/Telegram gateway
- Schedule field-use work

## Build Order Rationale
Boundary docs → Storage safety → Gateway distinctness → Context loading → Advisor routing → Knowledge base → Verifier DAG → Notes/Open Items → VDB
