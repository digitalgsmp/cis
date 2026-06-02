# Recent Handoff — CIS Deterministic Pipeline Decision
Date: 2026-06-01
Session: Context-Source Correction → Claude Proposal → Pipeline Decision

## CIS Deterministic Pipeline Decision — 2026-06-01

### Deliberation Converged
Claude + ChatGPT reached agreement: the next build is the CIS deterministic pipeline
foundation, not generic unified memory. The pipeline is the product.

### Key Decisions
- CIS is a Hermes-native adversarial deliberation engine
- Pipeline: TRIAGE → RESEARCH → DRAFT → REVIEW ↔ LOOP → CONSENSUS → ERIC_GATE → IMPLEMENT → VERIFY → STATE_WRITE → EXPORT → DONE
- State spine is bidirectional: briefs pipeline from verified history, receives verified outputs
- Gate scripts are the sole write authority for objective state
- AGENTS.md is target context path (Phase E); HERMES_CIS_BRIEFING_PATH is transitional
- Kanban is preferred only if shared across profiles is proven locally (Phase A)
- Flask/CIS database task queue is contingency if Kanban is siloed or unavailable

### Approved Build Order
Phase A (substrate verification) → Phase B (gate scripts) → Phase C (Kanban) → Phase D (SQLite spine) → Phase E (AGENTS.md) → Phase F (HCP export) → Phase G (router) → Phase H (MCP) → Phase I (Chroma/VDB)

### Next Single Action
Phase A — run Hermes substrate verification commands and return raw terminal output.
No code build begins until Phase A output is reviewed.

## Previous: Context-Source Correction (2026-06-01)

Identified five competing context realities. Decided HCP files become generated exports,
not manually maintained canonical source. Updated all 10 HCP_ files.

## Previous: Phase 0 Recovery (2026-05-31)
- Git versioning: github.com/digitalgsmp/cis, commit b1bcf7d
- Gateway repair: all V4 Pro gateways healthy, context-aware
- Context injection: HERMES_CIS_BRIEFING_PATH added to all profile .env files
- R1 corrected to V4 Reviewer; Qwen confirmed paused

## Previous: Router v0.1 (2026-05-31)
- classify_route() 8-pass classifier in advisor.py
- 4-panel AdvisorChat UI with shared input + routing banner
- V4 Implementer profile on port 8646
