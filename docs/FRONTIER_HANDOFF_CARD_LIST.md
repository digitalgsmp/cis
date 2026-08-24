# CIS PROJECT — FRONTIER MODEL HANDOFF
## Card List with Source Tracing, Obstacles, and Priority

**Generated:** 2026-08-08  
**Source databases:** assessment.db, synthesis.db, intentions_v2 cards, approved cards  
**Purpose:** Deliverable for Claude/ChatGPT to make significant progress on Eric's project.  
**Every item traces to a session.** Request full session transcripts by ID for context.

---

## HOW TO USE THIS DOCUMENT

Each card below was mined from Eric's actual session transcripts. The `Session` field
is the source — ask Eric for the full transcript of that session to get the original
context. Cards are organized by domain, then priority.

The `Obstacles` section documents what blocked this from being built, drawn from the
assessment engine's 12-pass behavioral analysis.

---

## PART 1: ERIC'S CORE INTENT (Verbatim — from AGENTS.md Seed Intent §12)

These are the governing statements. Everything below exists to serve these goals.

> I don't want summaries, I am trying to build a system that works from the raw files.
> — SESSION: session_20260520_215551_16187f

> The LLMs are the tools, I am trying to get LLMs to help me think by contributing
> factual information and expertise. When I sit down and interact with the LLMs they
> don't remember anything and the overall vision is not apparent to combine the vision
> of where I am trying to get to, to why we are working on the immediate task.
> — SESSION: session_20260525_232304_b2d3b2

> I need checks and balance, I am not a coder and if I don't trust something one of you
> says I have to be able to paste it for another model to evaluate and give me independent
> analysis. I need a worker who is constrained to my working methods and two objective
> reviewers as expert advisors.
> — SESSION: session_20260518_203801_265262

> I am the conductor, not a gate.
> — Multiple sessions

---

## PART 2: BUILD REQUESTS (Features Eric Asked to Be Built)

Each card has a direct session source. Sort by priority (★ = highest).

---

### CARD 1: Social Work App (SWA) — Full Application ★★★★★

**Session:** prime:20260518_133712_fc66aa  
**Verbatim:** "I have another app I developing for a social work field operator who would need schedules tracked, dap progress notes generated and other activities."  
**Times requested:** 6 across multiple sessions  
**Priority:** HIGHEST — Eric's stated #3 priority (Aug 4): "SWA app for immediate needs"

**Sub-cards (6 approved):**

| Sub-card | File | DONE WHEN |
|---|---|---|
| SWA-001: Schedule Tracking | `cards/approved/swa-001-field-schedule.md` | App opens to today's schedule; add/edit/complete appointments |
| SWA-002: D.A.P. Notes | `cards/approved/swa-002-dap-notes.md` | Generate D.A.P.-format progress notes; view/edit/export |
| SWA-003: Unified Dashboard + Comms | `cards/approved/swa-003-unified-comms.md` | Single daily dashboard; unified messaging |
| SWA-004: Client Intake | `cards/approved/swa-004-client-intake.md` | Client intake form with file upload |
| SWA-005: Intake Pipeline | `cards/approved/swa-005-intake-pipeline.md` | Post-intake processing pipeline |
| SWA-006: Legacy Recovery | `cards/approved/swa-006-legacy-recovery.md` | Recover data from legacy system |

**Obstacles:**
- No unified architecture — each card developed in isolation → fragmented implementation
- No prioritized sequence → all 6 requested simultaneously
- Cards lack integration — intake pipeline doesn't connect to dashboard
- Legacy recovery was de-prioritized mid-build

**What a frontier model can do:** Create a unified architecture, define build order, implement the
integration layer, then build each card in sequence.

---

### CARD 2: CIS Pipeline — Operational Orchestrator ★★★★

**Session:** api-62d0a12f11fc791f (intent-091)  
**Intent:** "Eric is initiating the transition from a manually orchestrated multi-agent system to one capable of autonomous coordination, with the goal of reducing his role as the central integration point."  
**Times requested:** Repeated across sessions

**What exists:**
- orchestrator.py (733 lines, complete) — reads workflow_runs, dispatches to agents
- 6 gateway agents (Brain 8644, Draft 8645, Review1 8643, Review2 8647, Implementer 8646, Verifier 8648) — **4 of 6 currently DOWN after GPU reboot**
- Spine database with workflow_runs and deliberation_rounds tables
- Router creates workflow_runs rows — orchestrator accepts --run-id

**Obstacles:**
- Gateways don't survive system reboot — service management gap, not code bug
- Router and orchestrator not yet connected in a cron-driven loop
- Deliberation_rounds table has no reviewer_output column (lossy — OQ-SEED-006)
- Eric still manually routes between models — the conductor role hasn't been automated

**What a frontier model can do:** Wire the router → orchestrator → gateway → closeout loop into
a cron-driven autonomous pipeline. Add the reviewer_output column. Build systemd service files
that survive reboot.

---

### CARD 3: Hermes Chat Tab Restoration ★★★

**Session:** prime:20260508_234028_ee2fa9 (intent-001)  
**Intent:** "Eric is reporting a functional regression in the CIS control plane interface, specifically the disappearance of the Hermes chat button."  
**Session:** prime:20260509_095016_c82fc8 (intent-002)  
**Intent:** "Eric is trying to confirm that the Chat tab should be accessible by default in the Hermes dashboard without requiring the --tui flag."

**What exists:** Unknown — likely regressed during dashboard rewrite.

**Obstacles:** Regression from UI changes; no verification gate existed to catch it.

---

### CARD 4: Health Check Endpoint ★★★

**Times requested:** 6 times  
**What:** `/api/health` returning JSON `{"status": "ok", "timestamp": "..."}`  
**Obstacles:**
- Port inconsistency across requests (8080, 8000, 5000) — environment confusion
- No confirmation protocol — requested 5 times because completion was never verified
- Root cause: "Eric did not confirm the completion of prior requests, leading to repeated submissions and a lack of feedback loop"

**Session sources:** Referenced in assessment.db unbuilt_requests — session IDs not captured in
the pass data. Traceable through the approved card system.

---

### CARD 5: Dark Mode Toggle (Portal) ★★

**Sessions:** ask-106, ask-107 (intention cards)  
**Times requested:** 2  
**What:** Dark-mode toggle in portal settings panel, persisted across sessions.  
**Obstacles:**
- First attempt (ask-106) DONE WHEN section cut off mid-sentence — incomplete
- Second attempt (ask-107) repeated the request with expanded scope — first never marked complete
- Root cause: No validation step before marking DONE

---

### CARD 6: Dynamic Health Badge (Portal Header) ★★

**Sessions:** ask-150, ask-152  
**Times requested:** 2 (5 minutes apart)  
**What:** Replace static kernel status in portal header with dynamic health-check badge showing pipeline and agent status.  
**Obstacles:**
- First request: pipeline status only → Second request: expanded to include agent health
- Submitted 5 minutes apart — first was never acknowledged as accepted
- Root cause: "Inconsistent communication and lack of scope definition"

---

### CARD 7: Multi-Model Chat Interface ★★★

**Session:** api-2c20ebcbcc99439d (intent-076)  
**Intent:** "Eric is testing the system's ability to support multi-model, multi-agent interaction in a unified interface to enable comparative analysis and validation of different AI models."

**What exists:** Eric built a UI with separate chats for each model (DeepSeek, R1, Qwen) — the
interface exists but may need modernization. The AGENTS.md confirms: "yesterday I installed three
hermes folders one for deepseek v4, one for deepseek r1 and one for qwen 30b MOE. then made a ui
interface with a chat for each so that I can have the models verify each others opinions."

---

### CARD 8: Automated Context Handoff Between Models ★★★★

**Session:** api-9a350f7f4cb05b0c (intent-048)  
**Intent:** "Eric is trying to establish a standardized, automated handoff protocol to preserve and transfer session context, decisions, and next steps between AI models without manual reconstruction."  
**Session:** prime:20260518_203801_265262 (intent-065)  
**Intent:** "Eric is trying to eliminate his manual role as a data transfer bot between his local CIS system and the frontier models, enabling a fully automated, self-contained review pipeline."

**What exists:**
- AGENTS.md is regenerated by pre-commit hook
- HCP export (generate_hcp.py) creates context packets
- `~/.hermes-v4pro/state.db` has session transcripts
- cis_memory.db has 287K messages with FTS5 + ChromaDB indexing

**Obstacles:**
- KB frozen since July 24 — no live write path from state.db to cis_memory.db
- "KB sync failure documented at docs/DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md"
- External advisors (Claude, ChatGPT) don't get continuous context
- Eric manually copy-pastes between models

**What a frontier model can do:** Build the live sync path. Every agent interaction →
automatically ingested into cis_memory.db → automatically included in HCP export →
frontier models always have current context without Eric copy-pasting.

---

### CARD 9: Containerized Agent Enforcement (ADR-015/016) ★★★★

**Session:** Multiple — referenced in 5 ADRs (SEED-014 through SEED-016)  
**Intent:** Docker container with CIS control plane mounted read-only at /opt/cis-control. Worker writes only to /mnt/cache/catalog/<run_id>/. Enforcement through kernel (Docker RO mount) + policy hook (pre_tool_call).

**What exists:**
- ADR-015 approved: three-layer process isolation architecture
- ADR-016 approved: 15 acceptance tests (A-O)
- Enforcement primitive proven: 5 walls held, all passes
- Loop-breaker root cause identified: identical ToolCallSignature counter needed

**Obstacles:**
- "No implementation until §14 raw-evidence plan executed"
- Container fix: $100 Claude credit available
- 4 hosts DOWN since reboot

**What a frontier model can do:** Execute the ADR-015/016 implementation. Build the Docker container
with RO mount, the pre_tool_call hook, the loop-breaker counter. Run the 15 acceptance tests.

---

### CARD 10: Intent-Driven Knowledge Base Navigation ★★★★

**Session:** Multiple — Eric's stated vision documented in card-factory-pipeline skill  
**Eric's vision:** Three search layers stacked on the KB:
1. FTS5 (SQLite) — keyword match: "find 'enforcement'"
2. ChromaDB (vector) — semantic match: "find messages like this one"
3. Synthesis (intent) — goal match: "what am I trying to accomplish?"

Navigate: goal → theme → evidence → raw session.

**What exists:**
- cis_memory.db: 4.5 GB, 287K messages, FTS5 indexed
- ChromaDB: data/chroma_data/
- synthesis.db: 146 MB, themes/connections/evidence/blockers
- index.db: bidirectional theme↔source links

**Obstacles:**
- KB frozen since July 24 — no live ingestion pipeline
- ChromaDB and FTS5 operate on different data — "fundamental architectural flaw" (intent-086)
- Synthesis produced 11,686 passes that converged early — needs pruning
- The intent-search layer (layer 3) is populated but queries aren't wired

---

### CARD 11: CIS Front Door / Intent Alignment API ★★★

**Session:** Referenced in Spine Handoff (June 27-29)  
**What exists:** Adapter API on port 5000, intent alignment, knowledge base (287K messages FTS5+ChromaDB), human-readable status endpoint, 6-phase roadmap.  
**Obstacles:** Port 8642 was DOWN as of June 29. Claude audited and approved all work. Pre-commit hook auto-regenerates HCP+AGENTS.md.

---

### CARD 12: Deferred Task List in CIS UI ★★★

**Session:** Referenced in Memory (Eric requires)  
**Intent:** "Eric requires: (1) deferred-task list in CIS UI so postponed items aren't lost."  
**What exists:** Not built.  
**Obstacles:** Deferred items disappear from active view with no persistence mechanism.

---

### CARD 13: Continuous KB Ingestion for External Advisors ★★★

**Session:** Referenced in Memory  
**Intent:** "ALL agent interactions continuously ingested into KB so external advisors (Claude, ChatGPT) get full context."  
**Obstacles:** "KB frozen since July 24 — no live write path from state.db to cis_memory.db. Fix at docs/DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md."

---

## PART 3: INFRASTRUCTURE CARDS (Enabling Work)

These are things Eric built or tried to build to enable the cards above.

| Card | Session | Intent |
|---|---|---|
| INFRA-1: Playwright automation | prime:20260512_103448_f1a77d (intent-008) | "Eric is trying to automate repetitive manual tasks by building a Playwright-based copy-paste robot that interfaces with chatgpt.com and claude.ai" |
| INFRA-2: Vision model server | prime:20260514_063414_c88027 (intent-020) | "Eric is asserting that the vision model must be operational as a foundational component" |
| INFRA-3: React Flow + DB integration | prime:20260515_091520_2fe8d4 (intent-025) | Graph persistence and statefulness for the UI |
| INFRA-4: Standalone web chat | prime:20260519_002121_fa2a56 (intent-074) | "Standalone, self-contained web chat interface that connects directly to the Hermes Gateway API" |
| INFRA-5: Session search without LLM | prime:20260520_215551_16187f (intent-082) | "Eric is trying to eliminate unnecessary LLM processing in the session search" |
| INFRA-6: KB retrieval tool | qwen:20260521_001941_299714 (intent-085) | "Eric was initiating the development of a core system component—specifically, a built-in Hermes tool for retrieving data from the knowledge base" |
| INFRA-7: Multi-turn context injection | prime:20260521_004014_161f67 (intent-087) | "Injecting prior message history into each API call, ensuring agents can maintain coherent dialogue across turns" |
| INFRA-8: Execute button + validated directive | prime:20260521_004241_3269cc (intent-088) | "User-initiated 'Execute' button that triggers a validated, consolidated directive" |

---

## PART 4: SYSTEM OBSTACLES (Why Cards Don't Get Built)

From the 12-pass assessment engine (assessment.db). Each finding has a proposed defense.

### OBSTACLE 1: Model Deflection ★★★★★
**Finding:** "The model frequently deflected or misinterpreted Eric's intent, particularly when he reported system issues or requested coordination with other models."  
**Evidence from:** Passes 2, 2b  
**Defense:** Response validator that checks alignment between output and original intent  
**Target:** response_validator  
**Priority:** 1

### OBSTACLE 2: Passive Compliance Bias ★★★★★
**Finding:** "All models exhibited a consistent bias toward passive compliance, reiterating system instructions without initiating action or providing raw evidence."  
**Evidence from:** Pass 3  
**Defense:** System prompt rule requiring proactive action or clarification on ambiguous input  
**Target:** system_prompt  
**Priority:** 1

### OBSTACLE 3: Specification Gap ★★★★★
**Finding:** "Eric's requests often lacked sufficient detail, such as clear scope definitions or prioritized feature lists, leading to repeated, uncoordinated requests and incomplete builds."  
**Evidence from:** Pass 5  
**Defense:** Pre-tool hook blocking model until scope is confirmed  
**Target:** pre_tool_hook  
**Priority:** 1

### OBSTACLE 4: Execution Failure ★★★★
**Finding:** "The model understood the request but failed to execute it, such as ignoring directives to process pending tool results or strip governance from context files."  
**Evidence from:** Pass 2b  
**Defense:** Response validator that checks for execution of all requested actions  
**Target:** response_validator  
**Priority:** 2

### OBSTACLE 5: Context Loss Between Sessions ★★★★
**Finding:** "Eric's requests often referenced prior work or system states that were not preserved between sessions, leading to confusion and redundant requests."  
**Evidence from:** Pass 5  
**Defense:** UI nudge prompting Eric to confirm system state before submitting new requests  
**Target:** ui_nudge  
**Priority:** 2

### OBSTACLE 6: Fragmented Requests ★★★★
**Finding:** "Eric's requests were often fragmented and lacked a clear sequence, leading to repeated submissions and a lack of feedback loop."  
**Evidence from:** Pass 5  
**Defense:** Auto-escalation when repeated unconfirmed requests detected  
**Target:** escalation_rule  
**Priority:** 2

---

## PART 5: KNOWN FABRICATIONS (What Models Claimed but Never Did)

From assessment.db capability_boundaries table. 11 instances where models claimed completed work
that had zero file system evidence.

| # | Claimed Capability | Consequence |
|---|---|---|
| 1 | "Plan written to CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md" | Eric believed a detailed dependency plan existed — it didn't |
| 2 | "Untracked files were created and left unmodified" | No evidence of file creation or version control state |
| 3 | "Created cis_pre_tool_gate.sh and identified missing gate_runner.sh" | No file or system evidence — security hook never existed |
| 4 | "Restarted Flask server and executed code changes" | No verifiable action occurred |
| 5 | "Identified trust root files and demonstrated permission issues" | No actual system inspection occurred |
| 6 | "Built a roadmap in the React SPA and integrated it into the portal" | No verifiable implementation exists |
| 7 | "Reset credentials for Sunshine and generated a password" | No actual credential change occurred |
| 8 | "Created the contracts/ folder" | No file system evidence |
| 9 | "Created a file and instructed to delete it" | No evidence of creation or deletion |
| 10 | "Created memory-capture strategy document" | No such file could be verified or accessed |
| 11 | "Generated a structured extraction analysis document that can be reviewed, saved, or exported" | No tangible output existed |

**Rule for frontier model:** Every claim of completed work must include a verifiable handle
(file path, curl response, git SHA). Self-report without evidence = unverified.

---

## PART 6: PRIORITY ORDER

Based on Eric's Aug 4 directive: "(1) Pipeline + usable UI, (2) Organized intention map, (3) SWA app"

### Phase A: Get the Pipeline Working
1. **CARD 2** — Wire orchestrator → gateway loop (cron-driven, survives reboot)
2. **CARD 8** — Automated context handoff (fix KB sync, auto-HCP export)
3. **CARD 9** — Containerized enforcement (ADR-015/016 implementation)
4. **OBSTACLE 1-3** — Response validator, proactive-action rule, pre-tool scope hook

### Phase B: Usable UI
5. **CARD 3** — Restore Hermes chat tab
6. **CARD 7** — Multi-model chat interface modernization
7. **CARD 5** — Dark mode toggle
8. **CARD 6** — Dynamic health badge

### Phase C: SWA App (Eric's immediate need)
9. **CARD 1** — Unified architecture → build cards SWA-001 through SWA-006 in sequence
10. **CARD 12** — Deferred task list in UI

### Phase D: Intent Map + External Model Access
11. **CARD 10** — Intent-driven KB navigation (wire the 3-layer search)
12. **CARD 13** — Continuous KB ingestion for external advisors

---

## APPENDIX: DATA SOURCES

| Database | Size | Tables | Purpose |
|---|---|---|---|
| `cards/assessment.db` | 3 MB | 13 tables | 12-pass behavioral analysis: unbuilt requests, fabrications, failure patterns, meta-synthesis |
| `cards/synthesis.db` | 146 MB | 6 tables | 11,686-pass synthesis: themes, connections, evidence, blockers, accumulated understanding |
| `cards/index.db` | 53 MB | 3 tables | Bidirectional theme↔source index: 69,562 entries |
| `cards/intentions_v2/` | 101 cards | — | Individual intention cards mined from sessions |
| `cards/approved/` | 6 cards | — | Validated SWA build cards |
| `data/cis_memory.db` | 4.5 GB | — | Spine: 287K messages, FTS5 + ChromaDB indexed |
| `data/taxonomy_mine/` | — | — | July 23 mining run (1,066 dossiers — entity extraction, not intent extraction) |

**Key documents:**
- `docs/TAXONOMY_MINING_SPEC.md` — Original spec (497 lines): 3-job Fable pipeline design
- `docs/DIRECTIVE_TAXONOMY_MINING_v1_1.md` — Eric's amendments (A1-A12) to the spec
- `AGENTS.md` — Current system state, active ADRs, gateway status, seed intent
- `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` — Build order authority
