# CIS Roadmap — Current State to Functioning System
# Generated: 2026-06-28 | Sources: 287K knowledge base, 25+ sessions
# Status: Reviewed. Gaps and dependencies identified.

## What's Done (not on this list)
- Control plane: 4-panel portal, model dropdowns, dark mode
- Adapter API: /api/adapter/* (health, profiles, dispatch, chat)
- Knowledge base: 287K messages, FTS5 + ChromaDB, cis_search_knowledge
- Enforcement: MWL proof (5 walls), managed-scope pinning, T10 block
- Pipeline: Drafter→Reviewer→Implementer scripts, 52 gate scripts
- HCP/AGENTS.md: Regenerated, build plan nodes added
- Intent alignment: /api/intent/alignment, measure_intent.py
- MCP bridge: 17 tools, profiles configured (not activated)

---

## Phase 1 — Make the system runnable
**Who:** Eric + Claude (root/sudo work)

| # | Task | Why |
|---|---|---|
| 1.1 | Restart Qwen on 0.0.0.0:8002 | Container can't reach 127.0.0.1 |
| 1.2 | Complete MWL enforcement proof | Core trust question unanswered since June 23 |
| 1.3 | Start Prime gateway (8642) | Only down profile |
| 1.4 | Restart gateways → activate MCP | cis-knowledge MCP written but not loaded |
| 1.5 | Define per-profile SOUL.md + skills | DEV-PIVOT-05 P2 — agents need role identity |

**Verification:** curl /api/adapter/health → all 5 healthy. MWL proof log shows hook fired.

---

## Phase 2 — Portal becomes the tool
**Who:** Pipeline (Drafter→Reviewer→Eric→Implementer)

| # | Task | Source |
|---|---|---|
| 2.1 | Pipeline visibility — no black box. Show deliberation rounds, gate results, hook logs as expandable panels in Chat tab | Eric: "why is the conversation taken away from me into a black box" June 22 |
| 2.2 | Remove Roadmap iframe → native pipeline visualization | Portal still has iframe from old React SPA |
| 2.3 | De-hardcode gate status in Control tab | Mock data in portal.html since June 23 |
| 2.4 | Chat persistence to DB (not just localStorage) | Eric: "persist everything to the database" June 21 |
| 2.5 | Eric Gate batch review form | Eric: "batch review form, not one-at-a-time" June 26 |
| 2.6 | Session logging for direct models (Qwen, GLM, Claude) | Eric: "all models need persistent verbatim session files" June 22 |

---

## Phase 3 — Remote access
**Who:** Eric + Claude

| # | Task | Why |
|---|---|---|
| 3.1 | Sunshine/Moonlight remote desktop | Current workaround: SSH tunnel. Mentioned June 16, never configured. |

---

## Phase 4 — Pipeline intelligence
**Who:** Pipeline

| # | Task | Source |
|---|---|---|
| 4.1 | Chat as pipeline input — contextual inference trigger (not keyword match) | Eric: "detect when I'm asking for something that needs the pipeline" June 22 |
| 4.2 | Intent recovery deliverables — 5 documents from 50-document tag pass | DEV-PIVOT-12/13, scoped June 25, never produced |
| 4.3 | Web search for direct models | Eric: "back up recommendations with evidence outside training data" June 22 |
| 4.4 | Cross-model session access | Eric: "I want them to access each others' session files" June 22 |

---

## Phase 5 — WIASW creative pipeline foundation
**Who:** Pipeline

| # | Task | Source |
|---|---|---|
| 5.1 | WIASW Domain Model — Word→Image→Action→Sound→Web, multi-exit paths | DEV-PIVOT-05 §7.4, Eric: "earliest project WIASW was analog version of cis" |
| 5.2 | Multi-exit pipeline support — projects enter/exit any stage | Eric: "Multi-exit paths are a core design requirement" |
| 5.3 | LIFE domain registration — Home/Body/Mind as co-equal domain | WIAS Project Manager spreadsheet discovery |
| 5.4 | Authority separation for GPU tools — agent proposes read-only, GPU executes host-side | DEV-PIVOT-05, June 18 session |
| 5.5 | Creative tools inventory — 8 ComfyUI workflows, image/video generation skills | Skills directory, May 31 session |

---

## Phase 6 — Projects + Automation
**Who:** Pipeline

| # | Task | Source |
|---|---|---|
| 6.1 | SWA initial spec — case notes, client intake, appointments | SWA project at /mnt/projects/swa/ |
| 6.2 | Self-healing sidecar architecture — one-click Docker install, auto-maintenance | Idea #36, June 27 |
| 6.3 | Closeout automation — Hermes cron for stale workflow_runs | DEV-PIVOT-05 P8 |
| 6.4 | Visual designer next to chat — Penpot/Webflow-like page builder | Eric: "web flow like page designer to the right of the chat box" June 27 |
| 6.5 | Test infrastructure — adapter API, MCP bridge, portal pipeline trigger | Standard practice gap |
| 6.6 | Profiles collapse — 5 installs → 1 install + 5 profiles | DEV-PIVOT-05 P1, confirmed by Eric |

---

## Review Findings

**Dependency: Phase 1.5 (profiles) must complete before Phase 4.1 (inference trigger).**
The trigger routes to profiles. If profiles lack SOUL.md, routing is to blank agents.

**Risk: Gateway restarts (1.4) are fragile.**
Gateways running since June 18. Restart one at a time. Verify MCP loads after each.

**Gap: No automated post-phase verification.**
Every phase needs a health check script. Currently verification is manual.

**Priority decision needed: Intent recovery (4.2) vs Portal features (Phase 2).**
The 5 intent deliverables could inform portal design. But they need the tagging pass, which was abandoned. Option A: run the pass first. Option B: build portal from existing knowledge base.

**Stop criteria:**
- Phase 1 ends when all 5 profiles are healthy + MWL proof logged
- Phase 2 ends when portal has pipeline visibility + batch review form + DB persistence
- Phase 4 ends when inference trigger works + intent deliverables produced
- Phase 5 ends when WIASW domain model documented + multi-exit designed
