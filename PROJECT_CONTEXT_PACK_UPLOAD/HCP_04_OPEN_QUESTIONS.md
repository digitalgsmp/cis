# Open Questions — Hermes Harness / CIS
Last updated: 2026-06-01 (CIS Deterministic Pipeline Decision)

## OQ-003 — VDB pipeline rebuild
Previous hybrid SQLite/ChromaDB attempt produced low-signal output.
Depends on pipeline foundation and Phase I Chroma/VDB.
Status: OPEN — Phase I (later).

## OQ-004 — Project Context Pack update trigger
Resolution: generated context/HCP export should be triggered by verifier PASS
on completed pipeline run / state-write event. Not by arbitrary "significant task."
Status: RESOLVED (2026-06-01).

## OQ-009 — Verify hermes-gateway.service HERMES_HOME target
Status: OPEN.
Note: hermes-gateway.service (Flash/Research) confirmed using HERMES_HOME=/home/eric/.hermes.
The stale "r1" name in hermes-gateway-r1.service refers to V4 Reviewer, not deepseek-reasoner.

## OQ-010 — Generator source hierarchy vs Project Context Pack
Resolution: Both Hermes briefing and HCP files must derive from a single SQLite spine.
Transitional: HERMES_CIS_BRIEFING_PATH. Target: AGENTS.md (Phase E) + HCP export (Phase F).
Status: DECIDED (2026-06-01).

## OQ-011 — Stale context pack folder cleanup
Four folders exist. Only PROJECT_CONTEXT_PACK_UPLOAD/HCP_* files are active.
Cleanup deferred until export pipeline generates HCP files (Phase F).
Status: OPEN — deferred to Phase F.

## OQ-012 — Minimal SQLite schema for unified project state
Resolution: schema should be organized around CIS workflow events (research, proposals,
review rounds, consensus, directives, implementation artifacts, verification runs, exports),
not HCP document structure. Claude proposal v1.0 defines 11 tables.
Status: RESOLVED (2026-06-01). Implementation: Phase D.

## OQ-013 — MCP exposure for shared knowledge base
Depends on SQLite spine (Phase D) and AGENTS.md export (Phase E).
Status: OPEN — Phase H (later).

## OQ-014 — Export verification for generated HCP files
Will be handled by verify_state.py manifest hash checks (Phase F).
Status: OPEN — Phase F.

## OQ-015 — Context-source staleness detection
Phase 4A freshness verifier checks timestamps. Semantic staleness detection
requires manifest hash comparison (Phase F).
Status: OPEN — Phase F.

## OQ-016 — Is kanban.db shared across profiles on the installed Hermes version?
Phase A substrate verification must determine whether Kanban can coordinate across
~/.hermes, ~/.hermes-v4pro, ~/.hermes-r1, ~/.hermes-v4impl, and ~/.hermes-qwen.
If Kanban is profile-scoped or unavailable, contingency is Flask/CIS database
task tables instead.
Status: OPEN — Phase A substrate verification will answer.
