# CIS External Advisor Briefing — June 25, 2026

**Purpose:** Bring external AI models (Claude, ChatGPT) up to date on CIS state
so they can advise on the next architectural phase: making the Control Portal
a complete control plane over the Hermes agent backend.

**Format:** This is a raw-data briefing, not a summary. Recent changes shown with
commits, file paths, and evidence. The problem statement is Eric's own framing.

---

## 1. What CIS Is (Eric's Own Words)

> "The LLMs are the tools, I am trying to get LLMs to help me think by
> contributing factual information and expertise. When I sit down and interact
> with the LLMs they don't remember anything and the overall vision is not
> apparent to combine the vision of where I am trying to get to, to why we are
> working on the immediate task."

> "I need checks and balance, I am not a coder and if I don't trust something
> one of you says I have to be able to paste it for another model to evaluate
> and give me independent analysis. I need a worker who is constrained to my
> working methods and two objective reviewers as expert advisors."

> "I don't want summaries. I am trying to build a system that works from the
> raw files."

CIS is a Creative Intelligence System — a multi-model advisory pipeline where:
- Eric describes what he wants in natural language
- A Drafter model produces a proposal
- Two Reviewer models (DeepSeek R1 + Qwen) independently evaluate it
- Gates enforce deterministic checks (no secrets, git state, service health)
- An Implementer model builds only after Eric approves
- Everything is visible — no black boxes

---

## 2. What Changed This Week (June 19–24, 2026)

### Enforcement Primitive PROVEN (Phase PD CLOSED)
- **Commit:** e713d76, f2daf33
- **What:** 3-layer process isolation enforcement between CIS control plane
  and Hermes worker agent. Hermes runs in Docker container with read-only
  mounts to `/opt/cis-control/` and source code.
- **Evidence:** 5 containment walls tested, all PASS. Kernel mount table
  confirms RO. Hook blocks unauthorized writes. NOT self-reported — real
  in-container execution with actual kernel mount verification.
- **Docs:** `docs/PHASE_PD_CLOSE_AND_LOOPBREAKER_FINDINGS.md`
- **Trust root:** `/opt/cis-control/` is root-owned, never read by Hermes.
  Proof logs at `/opt/cis-control/proofs/mwl-proof/RESULTS/`

### Loop-Breaker Root Cause Found (Phase 0 IN PROGRESS)
- **Commit:** e713d76 (findings committed to DB)
- **What:** Successful repeated identical tool calls (same tool_name+args)
  are invisible to the built-in guardrail. Guardrail only counts failures
  and no-progress reads. A `skill_view` call repeated 20x with zero
  intervention because each call succeeded.
- **Fix target:** Extend `ToolCallSignature` counter to count all calls
  regardless of success/failure. First test is config-only
  (`hard_stop_enabled: true` + `same_tool` threshold).
- **Blocker:** [BLK-SEED-006] Active. Must fix before autonomous operation.

### CIS Control Portal v0.1 (Multi-Model Chat)
- **Commits:** 285144e, 12c5d5e, 5aa5d84, a88cb19, 45848d0, 41154e5
- **Access:** `http://localhost:5000/portal`
- **What exists:**
  - 4-panel chat grid: Hermes gateways (Drafter v4pro, Reviewer r1,
    Implementer v4impl, Prime/flash) + direct models (Qwen local, GLM 4.7,
    GLM 5.2, Claude Opus 4.8, Mistral Large 3, DeepSeek Reasoner)
  - 3 chat modes: 1:1, All Parallel, Adversarial Observer
  - Context usage bars per panel (tokens used / limit)
  - Cross-panel message visibility (all panels see all agents' messages
    with 'other panel' badge)
  - Thread tracking (persistent conversation IDs per panel)
  - Pipeline engagement detection (model signals `||PIPELINE_ENGAGE||` →
    portal shows pipeline trigger UI)
  - 4 tabs: Control (submit intent, approve), Deliberation (run reviewers),
    Chat (4-panel multi-model), Roadmap (iframe to React SPA)

### React SPA v0.1 (Tier 10-11)
- **Access:** `http://localhost:5000/ui/` (also embedded in portal Roadmap tab)
- **What exists:**
  - Monitor nav group: Pipeline, Eric Gate, Archive, Sessions, Decisions,
    Roadmap pages
  - Work nav group: Ideas, Projects, Schedule, DAM, Advisor Chat
  - Knowledge nav group: Learn, Review
  - Infra nav group: Hardware, Storage, Software, Models, Services, Collab
  - Dashboard with live data: current phase, active blockers, recent pipeline
    runs, Eric Gate approval form, completed capabilities
  - Roadmap page: static data — 18 Built items, 5 Specified, 7 Theorized,
    timeline, 15 ADRs, Eric's Vision verbatim quotes

### Context Export Regenerated
- **Commit:** e713d76
- AGENTS.md regenerated (Phase PD CLOSED, Phase 0 IN PROGRESS)
- HCP packet regenerated (11 files in PROJECT_CONTEXT_PACK_UPLOAD/)

---

## 3. What DOES NOT Work — The Portal Gap

Eric's current complaint:

> "I still am not able to work outside of the terminal and the roadmap button
> in the control panel does not display any information. I need the monitor
> script in the old ui added to the control panel roadmap tab."

The issues:

1. **Roadmap tab shows static data only.** The React SPA RoadmapPage has
   hardcoded arrays. It shows the right information but doesn't update with
   live state. No live gateway health. No live pipeline status. No live
   blocker status. It's an infographic, not a dashboard.

2. **No live gateway monitoring.** The portal has no way to see which
   gateways are running, their health status, or model availability.
   Gateways visible: v4pro:8645, r1:8643, v4impl:8646, qwen:8644,
   prime:8642 (currently down). The `gate_service_health.sh` script exists
   but isn't wired to any UI.

3. **Monitor was never functional.** In the old UI, "Monitor" was a text
   label, not a clickable button. In the new React SPA, "Monitor" IS
   clickable and navigates to pages — but those pages show static data.

4. **No unified control plane experience.** Eric must switch between tabs
   and pages. The portal Chat tab is disconnected from the pipeline (you
   chat, then switch to Control tab to submit intent). The Roadmap tab is
   an iframe to a separate React app. Nothing flows together.

5. **No `/new` command.** No way to start a fresh chat session from the
   portal.

---

## 4. The Goal — Eric's Own Framing

> "The focus needs to be how to get the control portal to function in a way
> that I am working completely in the control panel as we try to figure out
> the control plane, abstraction layer and hermes backend. Because the sooner
> everything is tied together we can finally scrape the session logs, archive
> files and everything else to see the entire scope of all the projects as
> I describe them in my own words to develop the ongoing project roadmaps
> for unified memory and chat focus group discussions for project development."

Translation: Eric wants ONE interface where he can:
1. Chat with models (works now)
2. See live system status — gateways, services, blocker health (missing)
3. Trigger and watch the pipeline (partially works, disconnected from chat)
4. Review and approve work (partially works via Eric Gate)
5. Eventually: scrape session logs, archive everything, generate project
   roadmaps from his own words, build unified memory, and run focus-group
   discussions between models for project development

The control portal must become the CONTROL PLANE — the single surface where
Eric operates CIS. Everything below it (pipeline, enforcement, gates,
Hermes backend) must be visible and controllable from here.

---

## 5. What's Needed — The Next Build Phase

### 5A. Live Gateway + Service Monitor (immediate)
Add a monitor panel to the portal that shows:
- Each gateway (v4pro, r1, v4impl, qwen, prime) — running/down indicator,
  port, health check response, model type
- Direct model endpoints (Qwen llama-server :8002, GLM :8003)
- CIS Flask app itself (:5000)
- Blocker status (BLK-SEED-006 loop-breaker, BLK-SEED-004 backup)
- Next action status (NA-SEED-017 FD.1, NA-SEED-018 loop-breaker build)

### 5B. Portal Roadmap Tab → Live Dashboard
Replace the iframe/static Roadmap tab with:
- Live build plan status from spine database
- Current phase + next action
- Active blockers with status
- Recent pipeline runs
- Gateway health (from 5A)
- All data fetched from API, auto-refreshing

### 5C. Unified Chat↔Pipeline Flow
Connect the Chat tab to the pipeline so Eric never leaves the conversation:
- Model detects pipeline intent → shows in chat
- Eric confirms → pipeline triggers
- Panels expand to show Drafter/Reviewer/Gates live
- Results surface back into chat
- Spec already drafted: `docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md`

### 5D. Abstraction Layer Definition
Define what "abstraction layer" means between the portal (control plane)
and the Hermes backend. This is the architectural question Eric wants
external advisors to help with:
- How does the portal command Hermes without being Hermes?
- What API surface does Hermes expose?
- How are roles enforced at this boundary?
- How does the trust root (/opt/cis-control/) interact with the abstraction
  layer?

### 5E. Session Log Scraping + Archive
Once the portal is the control plane, scrape all past session logs and
archive files to build a complete project corpus. This feeds into:
- Unified memory (cross-session persistence)
- Project roadmaps extracted from Eric's own words
- Focus-group discussions between models for project development

---

## 6. Current Technical Architecture

### Infrastructure
```
Proxmox Host: wander @ 192.168.1.200 (PVE 9.1.6)
  └─ creative-vm (VM 100): Ubuntu 24.04 @ 192.168.1.15
       ├─ CIS Flask app: localhost:5000
       ├─ Hermes gateways:
       │   ├─ prime (Flash/Research): 8642 → NeMo 8800
       │   ├─ v4pro (Drafter): 8645
       │   ├─ r1 (Reviewer): 8643
       │   ├─ v4impl (Implementer): 8646
       │   └─ qwen (Qwen3-VL-30B): 8644
       ├─ llama-server: :8002 (Qwen GGUF, OpenAI-compatible)
       ├─ GLM: :8003 (GLM 4.7 Flash GGUF)
       ├─ ChromaDB 1.5.9 (vector search)
       └─ SQLite spine: /mnt/projects/cis/data/cis_memory.db
```

### Key File Paths
| Path | What |
|------|------|
| `/mnt/projects/cis/runtime/app.py` | Flask backend (924 lines) |
| `/mnt/projects/cis/runtime/ui/public/portal.html` | Portal frontend (874 lines) |
| `/mnt/projects/cis/runtime/ui/src/` | React SPA source (30 .jsx files) |
| `/mnt/projects/cis/runtime/ui/dist/` | React SPA built output |
| `/mnt/projects/cis/data/cis_memory.db` | SQLite spine |
| `/mnt/projects/cis/docs/` | All specs, ADRs, handoffs |
| `/mnt/projects/cis/tools/gates/` | 20+ gate scripts |
| `/mnt/projects/cis/tools/pipeline/` | Pipeline orchestration |
| `/opt/cis-control/` | Trust root (root-owned, RO to workers) |
| `/mnt/archive/` | 10TB archive storage |

### Recent Specs (this week)
| Spec | File | Status |
|------|------|--------|
| Pipeline-Visible Portal | `docs/CIS_PIPELINE_VISIBLE_PORTAL_SPEC.md` | DRAFT |
| Chat-to-Pipeline Trigger | `docs/CIS_CHAT_PIPELINE_INFERENCE_TRIGGER_SPEC.md` | DRAFT |
| Enforcement Primitive | `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` | APPROVED |
| FD.1 MCP Dispatch Tools | `docs/CIS_TIER_FD1_MCP_DISPATCH_TOOLS_SPECIFICATION.md` | IN_PROGRESS |
| 16 Failure Modes | `docs/CIS_16_FAILURE_MODES.md` | DONE |
| MWL Proof v2 | `docs/MINIMAL_WORKER_LAUNCH_PROOF_v2.md` | DONE |

---

## 7. Constraints for External Advisors

- Eric is NOT a coder. He operates through natural language. All interfaces
  must be understandable without reading code.
- Trust root is ABSOLUTE. `/opt/cis-control/` is a black box. Never propose
  reading or bypassing it.
- Hermes Agent is the backend. The portal is the control plane. The
  abstraction layer sits between them. This is the architectural question.
- No implementation without Eric approval (Eric Gate).
- All evidence must be deterministic — git diff, test output, endpoint
  responses, DB queries. No self-reported completion.

---

## 8. The Question for External Advisors

Given this state, how should CIS architect the abstraction layer between:
- The Control Portal (what Eric sees and interacts with)
- The Hermes Agent backend (the AI agent runtime)
- The CIS control plane (trust root, enforcement, gates, pipeline)

Specifically:
1. What should the portal's API surface to Hermes look like?
2. How should role enforcement (Drafter/Reviewer/Implementer) be expressed
   at the abstraction layer?
3. How should the trust root constrain the backend without the portal
   needing to understand root-owned files?
4. What does a "unified memory" architecture look like when the portal
   is the control plane and Hermes is the backend?

Eric will read your answers. Use concrete examples, not abstractions.
Reference the existing files and architecture. Don't propose building
things already built.
