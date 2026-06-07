# Next Actions — Hermes Harness / CIS
Last updated: 2026-06-07 (Tier 5.3 COMPLETE — Tier 5.4 next)

## Current Next Action

**Tier 5.4 — generate_hcp.py.** Reads SQLite spine, writes HCP_00 through HCP_09
to PROJECT_CONTEXT_PACK_UPLOAD/. Replaces manual HCP editing.

Do NOT start:
- Tier 6 Pipeline Integration (gated on Tier 5)
- Judge checklist (gated on Tier 6)
- UI changes
- VDB/Chroma
- Router reclassification
- MCP bridge
- Stale folder cleanup (Tier 5.7, gated on Tier 5.6)

## Approved Build Order

| Tier | Description | Status | Commits |
|------|-------------|--------|---------|
| Tier 0 | Orchestrator scaffold | ✅ COMPLETE | `9d84351` |
| Tier 1 | Deterministic gate suite + runner | ✅ COMPLETE | `bc49beb`–`635a646` |
| Tier 2 | Kanban coordination layer | ✅ COMPLETE | `2989c5b` |
| Tier 3 | Pipeline smoke test | ✅ PASS_WITH_LIMITATIONS | — |
| Tier 4.1 | SQLite spine schema | ✅ COMPLETE | `88ea25f` |
| Tier 4.2 | database.py | ✅ COMPLETE | `0c19b4d` |
| Tier 4.3 | gate_db_state.py | ✅ COMPLETE | `ec14615` |
| Tier 4.4 | Context export state tables + seed | ✅ COMPLETE | `b2e6c98` |
| Tier 5.1 | generate_agents_md.py + AGENTS.md | ✅ COMPLETE | `ee8eb25` |
| Tier 5.2 | AGENTS.md canary + gateway repair | ✅ COMPLETE (4/4 PASS) | `353cef5` |
| Tier 5.3 | HERMES_CIS_BRIEFING_PATH retired | ✅ COMPLETE | `80f934c` |
| Tier 5.4 | generate_hcp.py | ← CURRENT | Not started |
| Tier 5.5 | generate_all.py + export manifest | Gated on 5.4 | — |
| Tier 5.6 | gate_export_agreement.sh | Gated on 5.5 | — |
| Tier 5.7 | Stale context pack cleanup | Gated on 5.6 | — |
| Tier 6 | Pipeline integration | Gated on 5 | — |
| Tier 7 | Router reclassification | Gated on 6 | — |
| Tier 8 | MCP bridge | Later | — |
| Tier 9 | Chroma/VDB | Later | — |
| Tier 10 | CIS UI/custom displays | Later | — |

## Remaining Tier 5 Tasks

1. Tier 5.4 — generate_hcp.py
2. Tier 5.5 — generate_all.py + export manifest with SHA256
3. Tier 5.6 — gate_export_agreement.sh (hash verification)
4. Tier 5.7 — stale context pack cleanup

## Known Limitations

- Orchestrator --output preserves only final-round detail (Tier 6 backlog)
- Hermes Kanban v0.13 has no custom lanes (CIS stages in card metadata)
- HCP files manually reconciled until Tier 5.4–5.6 complete
- TERMINAL_CWD required for gateway AGENTS.md discovery (deprecated but functionally required)
