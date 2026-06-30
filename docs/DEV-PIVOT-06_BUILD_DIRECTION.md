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

## 10. Session Update — June 29, 2026

Since this document was ratified, two sessions completed. Key updates
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
| Gateway status (June 27) | 5 up | 4 up, prime (8642) DOWN |
| Gateway status (June 29 verified) | N/A | **Verified live:** 8642 DOWN, 8643-8646 UP, NeMo 8800 UP |
| Qwen llama-server | 127.0.0.1:8002 | **0.0.0.0:8002 (LAN-exposed)** — security concern |
| MCP tools active | No | Configured but gateways need restart to load |
| Agents static config | Prime "Running" | Fixed to "DOWN — verified 2026-06-29" |
| Pre-commit hook | None | **Built June 29** — auto-regen HCP + AGENTS.md, blocks stale commits |

### Sessions since ratification

**June 27 (Hermes):** Built front door, abstraction layer, knowledge base. 20 files, 550 insertions. Commits: 3478da1, 70e73bd, 182bcd8, 9c921e2. Eric approved.

**June 28 (Claude):** Audited Hermes work — PASS. Caught near-miss (therapy notes staged). Committed 4c3d396 (31 files). Wrote SESSION_HANDOFF_2026-06-28.md. Correctly flagged PHASE1_ROOT_DIRECTIVE contradicting DEV-PIVOT-06 §6 deferral.

**June 29 (Hermes):** Reconciliation. Port check verified 8642 DOWN. Fixed agents_static.yaml. Model decision: Claude stays manual copy-paste — too expensive for rotation. DEV-PIVOT handoff updated. Pre-commit hook built.

### What Eric approved and pushed

- June 27: "Excellent work" — 4 commits pushed
- June 29: "If you can fix it go ahead" — config fix + handoff update + pre-commit hook

### New critical docs for Claude

1. **`docs/CIS_ROADMAP_PHASES_1_6.md`** — Complete roadmap with Phase 1 as immediate priority
2. **`docs/PHASE1_ROOT_DIRECTIVE_FOR_CLAUDE.md`** — Exact commands and verification for root work (Note: Tasks 2 and 5 deferred per §6. Tasks 1, 3, 4 are operational fixes.)
3. **This file (§10)** — Session handoff with current state
4. **`docs/DEV-PIVOT-05_HERMES_INTEGRATION_ASSESSMENT.md` §10** — Detailed Claude briefing
5. **HCP files in `PROJECT_CONTEXT_PACK_UPLOAD/`** — Spine-generated, auto-regenerated by pre-commit hook

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
- **Pre-commit hook keeps exports current** — HCP + AGENTS.md auto-regenerated on every commit. No more stale handoffs.

### Claude update path

- **HCP files are auto-regenerated** by `.git/hooks/pre-commit` — always current with HEAD
- **Manual upload to Claude project** remains the delivery method (repo is private)
- **Claude should read HCP_01 first** every session, treat spine as authoritative over memory
- **PHASE1_ROOT_DIRECTIVE tasks 2 and 5 are DEFERRED** per §6 — only tasks 1, 3, 4 are active

---

## 11. Approval

```
Decision: APPROVE
Ratified by: Eric, 2026-06-27
Rationale: Abstraction layer built (P3 COMPLETE), archive integration complete (287K messages, FTS5 + ChromaDB), CIS front door operational. Build direction is in force.
```

Eric must explicitly approve this revised direction.
