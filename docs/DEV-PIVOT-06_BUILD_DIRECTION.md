# CIS Final Build Direction — Standalone Application, Hermes-Powered

**Date:** 2026-06-17 (revised same day) | **Author:** R1 Reviewer | **Status:** APPROVED 2026-06-27

## 1. Target End State

CIS is a **standalone application** — its own identity, its own UI, its own
dashboard. The user sees CIS, not Hermes. Under the hood, Hermes provides the
agentic backend: profiles for role separation, skills for procedural knowledge,
MCP for inter-profile coordination, messaging for Eric Gate delivery, cron for
automation, and the model picker for adversarial diversity.

The relationship: **CIS is to Hermes what a SaaS app is to AWS.**

## 2. What This Is NOT

- **NOT a Hermes plugin or add-on**
- **NOT a Hermes dashboard theme**
- **NOT a fork of Hermes** — Hermes updates independently
- **NOT the home for SWA** — SWA is a separate application, a product OF the CIS process, with its own Hermes backend and its own repo
- **NOT the home for WIAS** — WIAS is a creative pipeline methodology, pre-AI analog workflow being converted to LLM. Lives within the CIS creative platform as a domain, not a separate app.

## 3. Current State

### What's Complete

| Component | Status |
|-----------|--------|
| Build plan (25/27 nodes) | COMPLETE |
| Deliberation engine (R1 + Qwen) | COMPLETE |
| Gate runner (5 gates) | COMPLETE |
| CIS UI / display views (Tier 10) | COMPLETE |
| Drafter-to-Reviewer handoff (Tier 11C) | COMPLETE |
| Reviewer-side handoff (Tier 11D) | COMPLETE |
| Hermes hardening v2.0 (shell hooks) | COMPLETE — deployed on 4 profiles |
| Reconciliation engine | COMPLETE |
| Staleness check engine | COMPLETE |

### Critical Gap: Eric Isn't Using CIS

Eric interacts with Hermes bots directly via Telegram. The CIS pipeline
(Drafter → Reviewer → Eric Gate → Implementer) exists but never fires
for real work. Eric sends messages to @cis_hermes_r1bot — the router,
deliberation engine, and gate sequence are bypassed on every interaction.

**CIS needs a front door.** One entry point. Eric submits an intent.
CIS classifies it, routes it through the full adversarial pipeline,
and returns results. Eric approves from his phone.

## 4. Domain Coverage

Three domains share one pipeline, one spine, one approval gate.

```
                       WorkIntent
                           │
                  Domain Classifier
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    CIS Domain         WIAS Domain       External Projects
    (adversarial       (creative         (SWA, LIFE, etc.)
     build pipeline)    production)      
         │                 │                 │
    ┌────┴────┐      ┌────┴────┐      Deferred — separate
    │Drafter  │      │WIAS     │      apps built through
    │Reviewer │      │Adapter  │      the CIS process
    │Implement│      │         │
    └────┬────┘      └────┬────┘
         │                 │
         └─────────────────┘
                  │
           Process Manager
                  │
            Eric Gate
```

**CIS Domain:** Adversarial build pipeline. Drafter authors, Reviewer verifies,
Implementer builds. Eric approves. Live today — Tier 11D complete.

**WIAS Domain:** Word/Image/Action/Sound/Web — pre-AI analog creative pipeline
being converted to LLM workflow. WIAS adapter exists (Tier 7R.2) for intent
classification. Full operationalization deferred until CIS is feature-complete.

**External Projects (SWA, LIFE):** Separate applications, each with their own
Hermes backend and repo. Built THROUGH the CIS process, not integrated INTO CIS.
SWA removed from CIS build plan 2026-06-17.

## 5. The Archive and Knowledge Base

The archive drives contain Eric's own words — collected over time because LLMs
couldn't understand the vision being built. This is the **source material** for
the shared knowledge base.

**The archive is the knowledge base.** It's not MCP. It's not a vector database.
Those are access layers. The archive is the raw material — Eric's writing, his
vision, his workflow documents.

Role of the VDB (Chroma, Tier 9): Vectorized access layer. Enables semantic
search across the archive. Already built (Tier 9 COMPLETE).

Role of MCP: Inter-profile coordination. Allows Drafter to query the knowledge
base, Reviewer to cross-reference claims, Implementer to verify against specs.
NOT the knowledge base itself — the transport layer.

**Open question:** How are the archive drives integrated into the current build
plan? This needs its own specification before wiring.

## 6. Build Sequence (Revised)

The profiles migration and Hermes refactor are deferred until CIS is
feature-complete and Eric is actively using the pipeline.

| Phase | What | Status |
|-------|------|--------|
| **NOW** | Wire the CIS front door — Eric submits intents, pipeline fires | 🔴 Critical |
| **NOW** | Archive/knowledge base integration specification | 🔴 Critical |
| **SOON** | Complete remaining CIS functionality (external escalation wiring) | ⬜ Deferred |
| **LATER** | Profiles migration (P1) | ⬜ After CIS is feature-complete |
| **LATER** | UI overhaul + abstraction layer | ⬜ After profiles |
| **DEFERRED** | SWA application | ⬜ Separate project |
| **DEFERRED** | WIAS full operationalization | ⬜ After CIS complete |
| **PAUSED** | External escalation API keys | Keep wiring, don't activate charges |

### Why Profiles Migration Is Deferred

1. CIS is 90% complete but Eric isn't using the pipeline — the front door
   problem is higher priority than architectural refactoring
2. The current 5-install architecture WORKS. The hardening we just deployed
   works on it. There's no urgency to migrate.
3. Migrating to profiles while the front door is broken creates risk without
   benefit — we'd be refactoring infrastructure nobody's walking through
4. Finish CIS, make it usable, THEN refactor onto profiles

## 7. What Stays CIS, What Moves to Hermes (Eventually)

| Stays CIS (Methodology) | Moves to Hermes (Implementation) | Status |
|------------------------|----------------------------------|--------|
| Adversarial verification (ADR-SEED-002) | 5 installs → profiles | PENDING |
| FINAL_JSON protocol | orchestrator HTTP → MCP coordination | PENDING |
| Eric Gate (human approval) | gate scripts → skills | PENDING |
| Evidence-Backed Response Rule | closeout scripts → cron jobs | PENDING |
| Build plan spine (DB) | custom Flask UI → dashboard views | PENDING |
| Dual-model deliberation | staleness script → web_search skill | PENDING |
| Role enforcement (ADR-SEED-003/004) | Eric Gate delivery → messaging | PENDING |
| The archive (Eric's knowledge base) | VDB access layer (Chroma, Tier 9) | **COMPLETE** — 287,589 messages, FTS5 + ChromaDB |
| CIS ↔ Hermes adapter layer | Dispatch via abstraction layer API | **COMPLETE** (2026-06-27) — 4 endpoints on port 5000 |

## 8. What Does NOT Change

- **CIS is still CIS.** Methodology doesn't change when implementation moves.
- **The spine is authoritative.** `cis_memory.db` remains source of truth.
- **Eric always approves.** No auto-execute. Human-in-the-loop.
- **Hermes does not absorb CIS.** CIS registers on Hermes, not inside it.
- **SWA is separate.** Removed from CIS build plan. Own repo, own backend.
- **Escalation is paused.** API keys not activated. Eric manually audits with Claude/ChatGPT.

## 9. Next Actions (Immediate)

1. **CIS front door wired** (2026-06-27) — Abstraction layer built. `POST /api/adapter/dispatch` classifies intents and routes to correct profile. Gateway health checks operational.

2. **Archive integration COMPLETE** (2026-06-27) — 287,589 messages from 12 sources ingested into knowledge_messages. FTS5 + ChromaDB dual search operational. `cis_search_knowledge` MCP tool available to all profiles. Session format approach replaced complex tagging pipeline.

3. **Let the hardening settle** — Use CIS for real work. Verify shell hooks and pre_tool_call enforcement fire correctly. Find edge cases before building more.

## 10. Session Update — June 27, 2026

Since this document was ratified, a major build session completed. Key updates
for Claude to understand the current state:

### What changed since ratification

| Item | Before | After |
|------|--------|-------|
| Knowledge base | Stale: no recent ingestion | 287,589 messages FTS5 + ChromaDB (9.3GB), 12 sources |
| MCP search | FTS5-only | Dual: FTS5 + ChromaDB semantic search, `cis_search_knowledge` |
| Adapter layer | P3 pending | P3 COMPLETE — 5 endpoints including human-readable status |
| Intent alignment | Not built | Live: `/api/intent/alignment` + Drafter/Reviewer hooks |
| Roadmap | None | `CIS_ROADMAP_PHASES_1_6.md` — 6 phases, 28 items |
| Claude directive | None | `PHASE1_ROOT_DIRECTIVE_FOR_CLAUDE.md` — 5 root tasks |
| Build plan | 27 nodes | 29 nodes (Tier 12, 13 added), 24 COMPLETE |
| Human-readable status | None | `GET /api/adapter/status` — plain English, Claude-ready summary |
| Gateway status | 5 up | 4 up, prime (8642) DOWN |
| MCP tools active | No | Configured but gateways need restart to load |

### What Eric approved and pushed this session

- Commit 3478da1: "feat(abstraction): human-readable status + roadmap + Claude directive"
- 20 files changed, 550 insertions, 117 deletions
- Eric's words: "Excellent work" — session concluded with approval
- All 17 DEV-PIVOT files now carry session context footers (182bcd8)
- HCP regenerated at HEAD 9c921e2 — captures all session commits

### New critical docs for Claude

1. **`docs/CIS_ROADMAP_PHASES_1_6.md`** — Complete roadmap with Phase 1 as immediate priority
2. **`docs/PHASE1_ROOT_DIRECTIVE_FOR_CLAUDE.md`** — Exact commands and verification for root work
3. **This file (§10)** — Session handoff with current state
4. **`docs/DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md` §10** — Detailed Claude briefing

### What Eric wants from the human-readable status endpoint

He asked for "every result spelled out." The new `/api/adapter/status` endpoint
returns plain English explanations like:

> "V4 Drafter — authors proposals, designs, plans (port 8645) is responding. It returned an authentication error which is expected — the gateway is alive and ready, it just requires an API key to serve chat requests. Response time: 0.002s."

Plus a Claude-ready summary: "4 of 5 Hermes gateways are running. 1 gateway(s) are down and need attention."

No dots. No checkboxes. No JSON decoding. Everything explained.

### Eric's communication rules (for Claude)

These were reinforced this session:

- **Everything spelled out in text.** No dots, no icons, no checkboxes, no JSON.
- **Evidence-backed responses.** Raw terminal output pasted, not summarized. Eric sends packets to Claude/ChatGPT for adversarial audit — he needs verbatim evidence, not model self-report.
- **Bullet points.** Eric cannot read text walls. Changes topics every 5-15 lines.
- **Don't build without checking.** Discuss before building. Eric approves intention, not execution.
- **Hermes profiles load AGENTS.md and DEV-PIVOT files automatically** — these docs ARE the handoff.

---

## 11. Approval

```
Decision: APPROVE
Ratified by: Eric, 2026-06-27
Rationale: Abstraction layer built (P3 COMPLETE), archive integration complete (287K messages, FTS5 + ChromaDB), CIS front door operational. Build direction is in force.
```

Eric must explicitly approve this revised direction.
