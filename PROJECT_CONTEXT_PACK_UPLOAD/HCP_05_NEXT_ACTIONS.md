# Next Actions — Hermes Harness / CIS
Generated: 2026-06-12 22:25 UTC | Run: run-d403dd7bd863
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Current Next Action

**7R.2 — CISAdapter (CIS domain only)**

Do NOT start:

- Pass 5 implementation (project promotion, schema migration)
- Unified memory build
- Wiring V4-Pro through NeMo (architecturally blocked)
- Briefing Center UI redesign
- Notes/Open Items database implementation
- VDB pipeline rebuild
- Discord/Telegram gateway
- Schedule field-use work (SWA)
- CIS Foundation Build Plan Phases 1-3
- Snapshot trigger work (CIS-INFRA-STORAGE-002)
- Tier 8 MCP Bridge implementation (gated on Tier 8 specification planning complete)
- Tier 9 Chroma/VDB (gated on Tier 8)
- Tier 10 CIS UI/custom display views (gated on Tier 9)
- Any artifact not in the approved Dependency Graph Build Plan v2.0

## Approved Build Order

| Tier | Description | Status | Commits |
|------|-------------|--------|---------|
| 0 | Tier 0 — Deliberation Engine | ✅ COMPLETE | |
| 1 | Tier 1 — Deterministic Verification Gates | ✅ COMPLETE | |
| 2 | Tier 2 — Kanban Coordination Layer | ✅ COMPLETE | |
| 3 | Tier 3 — Pipeline Smoke Test | ✅ COMPLETE | |
| 4 | Tier 4 — SQLite Spine | ✅ COMPLETE | |
| 5 | Tier 5 — Context Export Pipeline | ✅ COMPLETE | |
| 6 | Tier 6 — Pipeline Integration | ✅ COMPLETE | |
| 7 | Tier 7 — Full Durable Router Pipeline | ⏸ DEFERRED | |
| 7.1 | Tier 7.1 — Router Reclassification (archive route) | ✅ COMPLETE | |
| 7.5a | Tier 7.5a — Corpus Audit | ✅ COMPLETE | |
| 7.5b | Tier 7.5b — Clean Subset Import + FTS5 | ✅ COMPLETE | |
| 8 | Tier 8 — MCP Bridge | 🚫 BLOCKED | |
| 9 | Tier 9 — Chroma/VDB | 🚫 BLOCKED | |
| 10 | Tier 10 — CIS UI / Custom Display Views | 🚫 BLOCKED | |
| 3.5 | Component 3.5 — Build-Plan Spine Authority | ✅ COMPLETE | |
| 7R | Tier 7R — Intent-to-Workflow Architecture Specification | ✅ COMPLETE | |
| 7R.1 | 7R.1 — WorkIntent schema + scope registry + Micro1 exclusion | ✅ COMPLETE | |
| 7R.2 | 7R.2 — CISAdapter (CIS domain only) | ⬜ PENDING | |
| 7R.3 | 7R.3 — SWAAdapter (validation use case) | ⬜ PENDING | |
| 7R.4 | 7R.4 — Process Manager (state machine) | ⬜ PENDING | |
| 7R.5 | 7R.5 — Human approval gate integration | ⬜ PENDING | |
| 7R.6 | 7R.6 — Dead Letter / blocked handling | ⬜ PENDING | |
| 7R.7 | 7R.7 — Acceptance test suite | ⬜ PENDING | |
| Tier 3.5 | Complete Build-Plan Spine Authority: finish generator switchover so AGENTS.md Se | COMPLETE | |
| Tier 5 | Build Tier 5.1: generate_agents_md.py — reads spine + static config, writes AGEN | COMPLETE | |
| Tier 5 | Build Tier 5.1a: config/agents_static.yaml — static Layer B content: infrastruct | COMPLETE | |
| Tier 5 | Run Tier 5.2: AGENTS.md canary test across all 4 active profiles | COMPLETE | |
| Tier 5 | Tier 5.3: Retire HERMES_CIS_BRIEFING_PATH from all 5 .env files after canary pas | COMPLETE | |
| Tier 5 | Build Tier 5.4: generate_hcp.py — reads spine, writes HCP_00 through HCP_09 | COMPLETE | |
| Tier 5 | Build Tier 5.5: generate_all.py — runs both generators, writes export manifest w | COMPLETE | |
| Tier 5 | Build Tier 5.6: gate_export_agreement.sh — verifies AGENTS.md and HCP hashes mat | COMPLETE | |
| Tier 5 | Tier 5.7: archive stale context packs (PROJECT_CONTEXT_PACK, _GENERATED, _UPLOAD | COMPLETE | |
| Tier 5 | Decide project isolation model for future CIS-managed projects before onboarding | COMPLETE | |
| Tier 5 | Build Tier 5 context export pipeline | COMPLETE | |
| Tier 6 | Closeout trigger design: define how CIS automatically triggers closeout when a d | COMPLETE | |
| Tier 6 | Harden Exact-Format Instruction Rule: ensure external advisors (ChatGPT, Claude) | COMPLETE | |

## Known Limitations

- Orchestrator --output preserves only final-round detail (Tier 6 backlog)
- Hermes Kanban v0.13 has no custom lanes (CIS stages in card metadata)
- HCP files manually reconciled until Tier 5.4–5.6 complete
- TERMINAL_CWD required for gateway AGENTS.md discovery (deprecated but functionally required)
