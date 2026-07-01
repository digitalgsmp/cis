# Next Actions — Hermes Harness / CIS
Generated: 2026-07-01 12:22 UTC | Run: run-0b261afa241a
Source: SQLite spine + config/hcp_static.yaml + config/agents_static.yaml
DO NOT MANUALLY EDIT — regenerate with tools/export/generate_hcp.py

## Current Next Action

**Enforcement — Container Isolation (ADR-015/016)**

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
- Any artifact not in the approved Dependency Graph Build Plan v2.0

## Approved Build Order

| Tier | Description | Status | Commits |
|------|-------------|--------|---------|
| 0 | Tier 0 — Deliberation Engine | ✅ COMPLETE | |
| 1 | Tier 1 — Deterministic Verification Gates | ✅ COMPLETE | |
| 2 | Tier 2 — Kanban Coordination Layer | ⏸ DEFERRED | |
| 3 | Tier 3 — Pipeline Smoke Test | ✅ COMPLETE | |
| 4 | Tier 4 — SQLite Spine | ✅ COMPLETE | |
| 5 | Tier 5 — Context Export Pipeline | ✅ COMPLETE | |
| 6 | Tier 6 — Pipeline Integration | ✅ COMPLETE | |
| 7 | Tier 7 — Full Durable Router Pipeline | ⏸ DEFERRED | |
| 7.1 | Tier 7.1 — Router Reclassification (archive route) | ✅ COMPLETE | |
| 7.5a | Tier 7.5a — Corpus Audit | ✅ COMPLETE | |
| 7.5b | Tier 7.5b — Clean Subset Import + FTS5 | ✅ COMPLETE | |
| 8 | Tier 8 — MCP Bridge | ✅ COMPLETE | |
| 9 | Tier 9 — Chroma/VDB | ✅ COMPLETE | |
| 10 | Tier 10 — CIS UI / Custom Display Views | ✅ COMPLETE | |
| 3.5 | Component 3.5 — Build-Plan Spine Authority | ✅ COMPLETE | |
| 7R | Tier 7R — Intent-to-Workflow Architecture Specification | ✅ COMPLETE | |
| 7R.1 | 7R.1 — WorkIntent schema + scope registry + Micro1 exclusion | ✅ COMPLETE | |
| 7R.2 | 7R.2 — CISAdapter (CIS domain only) | ✅ COMPLETE | |
| 7R.3 | 7R.3 — SWAAdapter (validation use case) | ⏸ DEFERRED | |
| 7R.4 | 7R.4 — Process Manager (state machine) | ✅ COMPLETE | |
| 7R.5 | 7R.5 — Human approval gate integration | ✅ COMPLETE | |
| 7R.6 | 7R.6 — Dead Letter / blocked handling | ✅ COMPLETE | |
| 7R.7 | 7R.7 — Acceptance test suite | ✅ COMPLETE | |
| 11A | Tier 11A — Dashboard, Navigation, System Overview | ✅ COMPLETE | |
| 11B | Tier 11B — Eric Gate Approval Record | ✅ COMPLETE | |
| 11C | Tier 11C — Drafter-to-Reviewer Handoff | ✅ COMPLETE | |
| 11D | Tier 11D — Reviewer-Side Handoff | ✅ COMPLETE | |
| 12 | Tier 12 — Knowledge Base Ingestion | ✅ COMPLETE | |
| 13 | Tier 13 — Abstraction Layer | ✅ COMPLETE | |
| ENFORCEMENT | Enforcement — Container Isolation (ADR-015/016) | ⬜ PENDING | |
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
| Tier Phase 0 | Build loop-breaker for successful-repeat tool calls. Root cause: tool_guardrails | PENDING | |
| Tier enforcement | Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md as proposal only. Route through  | COMPLETE | |
| Tier enforcement | Execute §14 raw-evidence capture plan from TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V | BLOCKED | |
| Tier enforcement | Draft §7/§14 Test-Rig Amendment to TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md. Re | COMPLETE | |
| Tier enforcement | Execute §7 Parts A+B override-plane evidence test (9 steps) against disposable t | COMPLETE | |
| Tier front-door | FD.1 BASELINE VERIFIED: 11 existing MCP tools (docstring stale — says 9, actual  | IN_PROGRESS | |

## Known Limitations

- Docker containment PROVEN on r1 CLI only — not yet extended to gateway path or scrape profile
- v4impl pre_tool_call hook behavior inside Docker container is unknown
- Correct scrape container image undecided (bare ubuntu insufficient; needs python-nodejs)
- Verifier Registry (DEV-PIVOT-16) specified but build/commit status unverified from spine

## Priority Next Actions

- 1. Extend containment proof from CLI to gateway path and to scrape profile (Docker backend, read-only source mounts, catalog RW, correct image)
- 2. Spine-gate pillar audit (READ ONLY) — confirm which gates exist, run, and reject bad input for failures #1, #8, #11, #13, #14
- 3. Drafter writes spec from spine-gate audit → Reviewer challenges → Claude+ChatGPT reconcile → Eric approves → implement
- 4. ARCHITECTURE — Per-project container as standing workflow: every project (CIS first) develops inside its own container. Source mounted per-authorization, spine + other projects read-only or absent, host unreachable. Full-access local backend removed/gated. DESIGN DIRECTION only — not locked architecture.
- 5. ARCHITECTURE — Scope-authorization gates (pairs with #4): spine gates enforce per-session authorization beyond path boundaries. Triggering evidence: Hermes modified generate_hcp.py during 2026-06-19 closeout without authorization (failure #7). Container would NOT have blocked — file is CIS's own editable tree. DESIGN DIRECTION only.

## Open / Unverified — Do Not Assume

- Gateway-with-Docker-backend is unproven (only CLI proof passed)
- Docker group refresh may still be required for gateway non-sudo Docker access
- /mnt/cache/catalog exists and is the intended writable catalog root; contains proof artifacts
- docs/DOCKER_CONTAINMENT_PROPOSAL.md committed this session
