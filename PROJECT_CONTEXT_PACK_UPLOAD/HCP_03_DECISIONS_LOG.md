# Decisions Log — Hermes Harness / CIS
Last updated: 2026-06-01 (CIS Deterministic Pipeline Decision)

| Date | Decision | Reason | Status | Evidence |
|------|----------|--------|--------|----------|
| 2026-06-01 | ADR-051: SQLite spine organized around workflow events, not HCP document structure | CIS needs to preserve the lifecycle of research, proposals, review rounds, consensus, directives, implementation artifacts, verification runs, and exports | DECIDED | Claude proposal v1.0, ChatGPT + Claude deliberation converged |
| 2026-06-01 | ADR-052: Spine is bidirectional | Spine must brief the pipeline from verified history and receive only verified outputs from completed pipeline runs | DECIDED | Claude proposal v1.0 |
| 2026-06-01 | ADR-053: Gate scripts are the sole write authority for objective state | LLM self-report is not truth; objective state changes require deterministic evidence | DECIDED | Verification-hardening rule extended to pipeline |
| 2026-06-01 | ADR-054: AGENTS.md / Hermes-native context is target shared context mechanism, replacing HERMES_CIS_BRIEFING_PATH after verification | Drift problem came from multiple context paths; target must be one Hermes-native context path plus generated external HCP exports | DECIDED | Claude proposal v1.0 |
| 2026-06-01 | HCP files become generated exports, not manually maintained canonical source | Multiple competing context sources discovered; Hermes-native deterministic state must be root | DECIDED | This session; HCP_01-HCP_09 updated |
| 2026-06-01 | Context-source correction: Hermes briefing + HCP export from single SQL root | HCP_ files in PROJECT_CONTEXT_PACK_UPLOAD/ were stale vs Hermes briefing injected via HERMES_CIS_BRIEFING_PATH | DECIDED | Identified 4 stale context pack folders |
| 2026-05-31 | Phase 0 Recovery: Git versioning + gateway repair + context injection | AdvisorChat.jsx truncation proved versioning is blocking | COMPLETE | github.com/digitalgsmp/cis, commit b1bcf7d |
| 2026-05-31 | Verification-hardening rule: V4 Implementer self-report not source of truth | Implementer claimed changes must be verified by deterministic evidence | ACTIVE | 7 evidence sources defined |
| 2026-05-31 | Router v0.1: AdvisorChat Input Router (classify_route, 8-pass classifier) | User no longer manual API between agents | COMPLETE | 10/10 backend + 7/7 UI tests passed |

Note: HERMES_CIS_BRIEFING_PATH is transitional and must not remain as a parallel long-term source.
Target retirement: Phase E, after AGENTS.md loading is verified across all active profiles.
