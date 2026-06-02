# Next Actions — Hermes Harness / CIS
Last updated: 2026-06-01 (CIS Deterministic Pipeline Decision)

## Current Next Action

**Phase A — Hermes substrate verification.** Run verification commands and return raw terminal output.

Phase A checks:
- `hermes --version` — confirm installed version and Kanban support
- `hermes kanban --help` — confirm Kanban CLI availability
- `hermes kanban boards list` — check existing boards
- Find `kanban.db` under all HERMES_HOME paths — confirm shared vs profile-scoped
- AGENTS.md canary loading test from `/mnt/projects/cis`
- Grep `HERMES_CIS_BRIEFING_PATH` across all profile `.env` files
- Verify Kanban dependency/assignment/worktree/gate features if available
- Verify git worktree status

**Hard stop:** No code build begins until Phase A raw output is reviewed and Kanban scoping is confirmed or contingency (Flask/CIS DB task tables) is selected.

## Approved Build Order

| Phase | Description | Gated On |
|-------|-------------|----------|
| Phase A | Hermes substrate verification | ← CURRENT |
| Phase B | Deterministic gate scripts | Phase A PASS |
| Phase C | Kanban board + profile configuration | Phase B |
| Phase D | SQLite spine schema (workflow-event organized) | Phase C |
| Phase E | AGENTS.md export pipeline (Hermes-native context) | Phase D |
| Phase F | HCP export pipeline (ChatGPT/Claude) | Phase E |
| Phase G | Router reclassification | Phase F |
| Phase H | MCP bridge (later) | Phase G |
| Phase I | Chroma/VDB (later) | Phase H |

## Sequencing Rules
- Nothing in Phase C or later begins until Phase A verification commands return known-good results.
- Nothing writes to the spine until Phase B gates exist and pass.
- Do not build unified knowledge before the deterministic gates.

## Current State
- GitHub/git versioning ✅ COMPLETE
- Context-source correction ✅ COMPLETE
- Claude proposal v1.0 ✅ COMPLETE
- ChatGPT + Claude deliberation converged ✅ COMPLETE
- Phase A substrate verification ← CURRENT

## Do Not Start Yet
- Phase B–I (all gated on Phase A)
- UI-003 layout pass
- Any SQLite schema creation
- Any gate script creation
- Any Kanban configuration
- Retirement of HERMES_CIS_BRIEFING_PATH
