# Next Actions — Hermes Harness / CIS
Generated: 2026-06-08 22:59 UTC | Run: run-ce329f7361f9
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Current Next Action

(No pending actions)

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
- Judge implementation (gated on Tier 6)
- Tier 6 Pipeline Integration (gated on Tier 5)
- Tier 7 Router Reclassification (gated on Tier 6)
- Tier 8 MCP Bridge (gated on Tier 7)
- Tier 9 Chroma/VDB (gated on Tier 8)
- Tier 10 CIS UI/custom display views (gated on Tier 9)
- Any artifact not in the approved Dependency Graph Build Plan v2.0

## Approved Build Order

| Tier | Description | Status | Commits |
|------|-------------|--------|---------|
| Tier 5 | Build Tier 5.1: generate_agents_md.py — reads spine + static config, writes AGEN | COMPLETE |  |
| Tier 5 | Build Tier 5.1a: config/agents_static.yaml — static Layer B content: infrastruct | COMPLETE |  |
| Tier 5 | Run Tier 5.2: AGENTS.md canary test across all 4 active profiles | COMPLETE |  |
| Tier 5 | Tier 5.3: Retire HERMES_CIS_BRIEFING_PATH from all 5 .env files after canary pas | COMPLETE |  |
| Tier 5 | Build Tier 5.4: generate_hcp.py — reads spine, writes HCP_00 through HCP_09 | COMPLETE |  |
| Tier 5 | Build Tier 5.5: generate_all.py — runs both generators, writes export manifest w | COMPLETE |  |
| Tier 5 | Build Tier 5.6: gate_export_agreement.sh — verifies AGENTS.md and HCP hashes mat | COMPLETE |  |
| Tier 5 | Tier 5.7: archive stale context packs (PROJECT_CONTEXT_PACK, _GENERATED, _UPLOAD | COMPLETE |  |
| Tier 5 | Decide project isolation model for future CIS-managed projects before onboarding | COMPLETE |  |
| Tier 5 | Build Tier 5 context export pipeline | COMPLETE |  |
| Tier 6 | Closeout trigger design: define how CIS automatically triggers closeout when a d | COMPLETE |  |
| Tier 6 | Harden Exact-Format Instruction Rule: ensure external advisors (ChatGPT, Claude) | COMPLETE |  |

## Known Limitations

- Orchestrator --output preserves only final-round detail (Tier 6 backlog)
- Hermes Kanban v0.13 has no custom lanes (CIS stages in card metadata)
- HCP files manually reconciled until Tier 5.4–5.6 complete
- TERMINAL_CWD required for gateway AGENTS.md discovery (deprecated but functionally required)
