# CIS Chat-First Architecture v1

## Product Thesis

- Chat is the application. The conversation interface is the front door,
  not a tab or feature.
- Idea forms are structured outputs of chat, not the user's starting point.
  The AI fills the form from deliberation; the user reviews and approves.
- Projects are promoted, approved ideas. The promotion step is explicit
  and user-controlled.
- Reconciliation is the gate between open-ended conversation and structured
  output. It produces a single consensus record with a diff log from
  multi-agent deliberation.
- The knowledgebase is the memory layer underneath the entire workflow.
  Hermes session files feed SQLite, which feeds chunking, which feeds the
  vector database, which feeds retrieval back into the chat context.

## Current Prototype Assessment

### Reusable As-Is
- api/advisor.py — standalone blueprint, zero entanglement. Reusable as
  the core chat routing layer after Phase 1 removes hardcoded auto-routing.
- AdvisorChat.jsx — isolated React component, becomes the application
  home surface
- memory/memory_store.py — SQLite + ChromaDB hybrid, already operational
- cis_db.py + api/app_api.py — idea/project/asset CRUD, solid schema
- Ingestion pipeline (cis_ingest.py, ingest_spines.py) — working
- api/spines_api.py + SpineGraphPage.jsx — knowledge graph browse
- DAM (DamPage.jsx, AssetDetail.jsx) — asset management
- db/connection.py + utils/helpers.py — shared infrastructure

### Reference-Only (do not extend, do not delete)
- CollabTracker.jsx + collab_rounds.py — contains valuable traces of
  manual deliberation routing. Preserved as legacy reference.
- Current App.jsx nav structure — placeholder scaffolding, reference only
- Current IdeasPage.jsx form-first flow — reference for field schema only

### Do Not Touch Yet
- Database consolidation — two cis_memory.db files exist at
  /runtime/db/cis_memory.db (advisor) and /memory/cis_memory.db (collab).
  Document boundaries only. No consolidation in Phase 1-3.
- Folder reorganization — target structure is documented below as
  Architecture v2 target, not current work.

## Target Architecture

### Modules Required

**Chat/Deliberation Module** (exists, promote to home)
Handles multi-agent conversation. Prime/V4 proposes. R1 challenges.
Qwen extracts and summarizes. All models answer independently in
parallel/reconcile modes.

**Reconciliation Module** (new, backend only in Phase 3)
Consumes advisor_threads/advisor_messages. Produces single consensus
struct with divergence map, confidence level, unresolved uncertainty,
and recommended next action. This is the gate between conversation
and structured output.
Backend: api/reconciliation.py (separate blueprint)
Frontend: appears as a panel inside AdvisorChat, NOT a separate page.

**Auto-Structuring Pipeline** (new, Phase 4)
Consumes reconciliation output. Maps consensus struct to CIS idea
schema fields. Produces a pre-filled Idea Draft for user review.

**Idea Review Module** (refactor of IdeasPage, Phase 4)
Role flips: AI fills the form, user reviews and edits.
Form is no longer the starting point — it is the review artifact.

**Project Package Assembler** (new, Phase 5)
Auto-gathers related research spines, assets, and session context
into a project bundle after idea is promoted.

**Knowledgebase/Retrieval Layer** (exists, wire in Phase 6)
FTS5 + ChromaDB unified retrieval tool. Injects relevant context
into advisor chat so agents can reference past work without
manual copy-paste.

**Session Ingestion Pipeline** (exists, wire in Phase 6)
Hermes session files → SQLite → chunked → vectorized → ChromaDB.

## Backend Target Structure (Architecture v2 — not Phase 1 work)

```
cis/runtime/
├── app.py
├── api/
│   ├── chat/
│   │   ├── advisor.py
│   │   ├── reconciliation.py
│   │   └── orchestrator.py
│   ├── kernel/
│   │   └── app_api.py
│   ├── knowledge/
│   │   ├── ingest_spines.py
│   │   ├── spines_api.py
│   │   └── retrieval.py
│   ├── collab/
│   │   ├── tracker.py
│   │   └── rounds.py (legacy)
│   └── system/
├── db/
│   └── connection.py
└── memory/
    └── memory_store.py
```

Note: Current files stay in current locations through Phase 3.
Migration to this structure is a separate project after Phase 3
is proven stable.

## Frontend Target Structure (Architecture v2 — not Phase 1 work)

```
ui/src/
├── App.jsx (chat-primary shell, sidebar replaces top nav)
├── pages/
│   ├── Chat/
│   │   ├── AdvisorChat.jsx (home page)
│   │   ├── ReconciliationPanel.jsx (new, inside chat)
│   │   └── StructuredIdea.jsx (new, inside chat)
│   ├── Projects/
│   ├── Knowledge/
│   └── System/
└── components/
```

Note: Current nav/dashboard structure remains prototype scaffolding
through Phase 3. AdvisorChat becomes home surface without moving files.

## Data Architecture

### Current Database Boundaries
- /mnt/projects/cis/runtime/db/cis_memory.db
  Owner: api/advisor.py
  Tables: advisor_threads, advisor_messages, agent_instances

- /mnt/projects/cis/memory/cis_memory.db
  Known/expected use: collab/memory/session-related records. Exact table
  ownership must be confirmed by schema inventory before consolidation work.

### Consolidation Plan (future, not Phase 1-3)
1. Full schema inventory of both databases
2. Schema comparison and conflict identification
3. Migration plan with rollback
4. Backup both databases
5. Test migration on copy
6. Validate all dependent modules
7. Cutover

Do not begin consolidation until Phase 3 is stable.

## First Vertical Slice

1. User opens CIS — lands in Advisor Chat (not dashboard)
2. User describes a creative idea in conversation
3. AI asks clarifying questions (Direct Mode)
4. If complex: Parallel Compare Mode — all three models answer
   independently
5. If conflicting: Reconcile Mode — divergence map + consensus
6. Reconciled consensus is passed to Auto-Structuring Pipeline
7. Idea Draft is auto-filled from consensus struct
8. User reviews, edits, and approves Idea Draft
9. User clicks "Promote to Project"
10. Project shell is created with premise, goals, research needs,
    assets needed, open questions, next actions
11. Hermes session is saved to SQLite
12. Session is queued for chunking and vectorization

## Phase Plan

### Phase 0 — Architecture freeze (current)
Write and approve this document. Freeze current prototype state.
No file changes.

### Phase 1 — Stabilize Advisor Chat Direct Mode
Remove hardcoded auto-routing loop from advisor.py.
Direct Mode only: send to one model, no auto-routing.
Verify three panels work cleanly.

### Phase 2 — Parallel Compare Mode
Same question to all three models independently.
No cross-model visibility in first round.
Display results side by side.

### Phase 3 — Reconcile Mode
Independent round → divergence map → consensus → challenge pass →
escalation suggestion after two failed attempts.
Reconciliation panel appears inside AdvisorChat.
api/reconciliation.py created as separate blueprint.

### Phase 4 — Idea Draft Auto-Structuring
Reconciliation output mapped to CIS idea schema.
IdeasPage refactored to review-first flow.
StructuredIdea.jsx component created inside Chat.

### Phase 5 — Project Promotion
Approved idea promotes to Project.
Project Package Assembler gathers related spines and assets.

### Phase 6 — Session Ingestion and Retrieval Wiring
Hermes sessions feed SQLite on save.
Retrieval tool injects relevant context into chat.
Knowledgebase becomes live memory layer.

## Explicit Non-Goals for Phases 1-3

- Do not move files into Architecture v2 folder structure
- Do not consolidate the two databases
- Do not delete CollabTracker or collab_rounds.py
- Do not make Reconciliation a separate frontend page
- Do not rebuild App.jsx nav
- Do not rebuild the dashboard
- Do not begin Project Package Assembler
- Do not begin Session Ingestion wiring

## Execution Constraint

V4 operates as executor in all build phases. When given an approved
spec, V4 implements exactly what is specified. V4 does not extend
scope. If V4 encounters something not covered by the spec, it stops
and reports rather than deciding. R1 verifies all V4 output against
the approved spec before the phase is marked complete.

## Phase Completion Log

### Phase 0 — COMPLETE (2026-05-22)
- Architecture document written and frozen at this file.
- Prototype state frozen. No file changes.

### Phase 1 — COMPLETE (2026-05-22)
- Changed file: `/mnt/projects/cis/runtime/api/advisor.py` (325→268 lines)
- Removed hardcoded auto-routing block (lines 185–244, 60 lines):
  - Prime→R1 review loop removed
  - R1→Prime revision loop removed
  - Injected prompts removed ("Review the proposal above.", "Address the review above.")
  - Conditional `auto_routed` response key removed
- `/api/advisor/chat` now returns only `{'agent': agent_name, 'content': reply}`
- `AdvisorChat.jsx` required no change — no frontend dependencies on removed fields
- Direct Mode test results:
  - Prime: PASS — single response, no `auto_routed`
  - R1: PASS — single response, no `auto_routed`
  - Qwen: PASS as clean error — `HTTP 503: Loading model` (model not loaded, not an auto-routing issue)
- No injected prompts, no automatic partner response
