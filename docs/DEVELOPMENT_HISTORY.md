# CIS Development History — The Real Timeline

**Generated:** 2026-07-12  
**Source:** Git log, session_closeouts, handoff docs, spine tables  
**Purpose:** Document the actual development journey — including when the build plan was abandoned as obsolete and practical direct action took over. This is the real history, not the governance theater version.

---

## Era 1: Governance and Build Plan (May 31 – June 19)

### The Setup
Eric started with a vision: multiple LLM profiles verifying each other's work, a knowledge base in SQLite, and a pipeline that preserves reasoning. The initial work was guided by Claude and ChatGPT as external advisors who introduced heavy governance: ADRs (Architecture Decision Records), tier-by-tier build plans, closeout rituals, and DEV-PIVOT documents.

### What Was Built
- **May 31:** Initial commit. CIS source tree.
- **June 1:** cis_kernel extraction, lifecycle observability, backend action handlers, interactive UI.
- **June 5-6:** Tier 0-1: Orchestrator, gate runner, dependency graph build plan, SQLite spine schema, database layer, state gate.
- **June 7:** Tiers 2-5: HCP export, generate_all.py, export manifest verification, context pack cleanup, Tier 5 closeout. 16 ADRs recorded (ADR-SEED-001 through ADR-SEED-016) — all dated June 7-19. These are governance-era artifacts.
- **June 8:** Tier 6: Closeout commit integration, state write executor, evidence-backed response rule.
- **June 9:** Kanban retirement (ADR-013), spine-native orchestration transport, closeout command with GitHub push.
- **June 10-11:** Components 1-3: Provenance/lifecycle schema, escalation advisor protocol, Eric Gate approval schema + briefing builder + verification gates.
- **June 12:** Tier 7R: CISAdapter, SWAAdapter, Process Manager, WorkIntent schema.
- **June 13:** Tiers 8-10: MCP Bridge (read-only stdio server), Chroma/VDB (local vector search), runtime-verified.
- **June 14:** Tier 11A-C: Dashboard, Eric Gate endpoint, Drafter-to-Reviewer handoff.
- **June 15:** Tier 11C complete, BLK-SEED-005 blocker update.
- **June 16:** Pipeline: intent column, second reviewer (Qwen), NeMo bypass, WAL mode. BLK-SEED-005 resolved (false positive).
- **June 17:** Tier 11D: Reviewer-side handoff, pre-execution oversight pipeline, hardening hook. CIS reframed as standalone application. WIAS/SWA/LIFE domain definitions extracted from archive.
- **June 18:** Enforcement Architecture v3.0, DEV-PIVOT naming convention unified.
- **June 19:** Docker containment proposal, enforcement architecture decided, FD.1 MCP dispatch tools (built, reverted, rebuilt).

### The Problem
The build plan was ceremony-heavy. Every change required ADR documentation, closeout rituals, export regeneration, and multi-model advisory review. Progress was real but slow. The tier system forced sequential building even when practical shortcuts were obvious. Eric recognized the governance theater was consuming time without proportional value.

**Session closeouts: 51 records (June 10-25). Many BLOCKED or FAIL.** The closeout process itself became a bottleneck — a gate to pass before the next gate.

---

## Era 2: The Break — Direct Action (June 20 – July 7)

### What Changed
Eric broke from the tier-by-tier governance process and let models build directly. The build plan became a reference, not a constraint. Documentation shifted from ADRs to handoff docs written by the models that did the work.

### What Was Built
- **June 20:** FD.1 MCP dispatch tools rebuilt successfully (after revert).
- **June 21:** 16 failure modes catalog, MWL proof v2.
- **June 22-23:** CIS Control Portal v0.1 — multi-model chat with Claude Opus, GLM 5.2, Mistral Large, GLM 4.7 Flash. Thread tracking, context bars, pipeline trigger endpoints. Cross-panel message visibility. Roadmap tab with status grid.
- **June 24:** Phase PD CLOSED. Loop-breaker root cause committed. Live gateway monitor API.
- **June 25:** Claude audit and vision crystallization. MWL sealed container — managed-scope pinning closes self-disable bypass.
- **June 26:** Intent recovery pipeline + 3-model tagging proof.
- **June 28-29:** CIS front door — intent alignment, knowledge search, human-readable status, roadmap. Claude audit PASS (caught near-miss: therapy notes staged).
- **June 30:** Session handoff spine table + auto-generated AGENTS.md §13. DEV-PIVOT status tracking.
- **July 1:** Enforcement container decisions recorded in spine.
- **July 7:** Gateway configs reconciled. Brainstorm gateway added on 8644. Master goal inventory — 107 items across CIS, SWA, WIASW from deep knowledge base search.

### Key Shift
No more ADRs. No more closeout rituals. No more tier-by-tier gating. The DEV-PIVOT table was created to track what was still relevant versus what was invalidated by real work. 4 of 17 DEV-PIVOTs were immediately marked INVALIDATED or PARTIALLY_INVALIDATED — the governance docs couldn't keep up with actual progress.

---

## Era 3: The GLM Build — The Real App (July 8 – July 12)

### What Changed
Eric allowed GLM 5.2 (and DeepSeek) to go through and build what was needed without the ceremonial process. The pipeline stalled with circular building was broken. Direct implementation. This is the era that produced the working control plane.

### What Was Built

**July 8 — Pipeline Foundation (18 commits):**
- Production pipeline relay + container multi-profile + schema migration 0015
- Relay API bug fixes: auth, round numbers, empty directive, FTS5
- Pipeline relay end-to-end: menter output storage, per-role timeouts, gate hash
- L1 deterministic checks in verify phase + saga compensation
- Verify isolation via git worktree (clean-checkout L1 checks)
- MATM trajectory recording: outcome marking, config_version, run_id exclusion
- Pipeline data integrity: 4 bugs where DB records lied about reality — fixed
- Reviewers must complete their role: retry on empty, escalate on incomplete
- Zombie gateway detection: root cause of unreliability
- Default-to-success pattern eliminated in pipeline_relay
- Code Review Gate: pattern catalog + chunk-based + sequential three-pass review
- FINAL_JSON parser fix + migrations 0019/0020
- Full pipeline end-to-end PASS — code review gate verified

**July 9 — Self-Evolution Bridge:**
- Self-evolution bridge: pipeline narrative to knowledge base
- Retry logic for code review gate agent calls
- Container pipeline: dispatch profile names + approvals + smoke test

**July 10 — 14-Component Control Plane + Guardrails (14 commits):**
- 14-component control plane build: projects table, multi-project routing, relay endpoints, corpus entries + FTS5, role overlays with bias resistance, SWA project bootstrap, run dependencies, git workflow methods, automated checks, dead letter queue, retry logic, Telegram notification, metrics, spine schema sync
- Tier 1 guardrails: 10 deterministic checks (output schema, content specificity, honesty reporter, scope compliance, claim-action verifier, code quality, path contract, sycophancy, tool result sandboxing, unverified claim block)
- Tier 2 guardrails: 10 more (context budget, verbosity/density, output sanitizer, loop detector, mode collapse, goal anchoring, trajectory monitor, model diversity, version drift, position randomizer)
- Tier 3 guardrails: 10 deeper analysis checks (intent compliance AST, semantic spot check, consensus independence, hardcode detector, error handling, evidence hash chain, context injection gate, raw source preservation, bias drift detector)
- Tier 4 guardrails: 4 advanced (example diversifier, randomized eval timing, effort metric, capability claim verifier)
- Tier 5: 22 external gate scripts wired into pipeline (security gates, phase-specific gates)
- Total: 34 native + 22 external = 56 guardrail checks firing after every agent output

**July 11 — Provenance, Drift, Brain Chat (11 commits):**
- Intent provenance tracking
- Semantic drift detection via local Qwen3-VL-30B LLM
- GLM-4.7-Flash as primary drift model (90 tok/s, Qwen fallback)
- Brain chat UI + backchannel interjections
- Container enforcement: repair prompt for FINAL_JSON gaps
- Verification phase gates: service_health, pyyaml, eric_approval, result tracking
- Context injection gate fix: always include KB_CONTEXT marker
- External gate timing: fire after _complete_round in all 5 phases
- First successful end-to-end pipeline run reaching CONSENSUS_REACHED

**July 12 — Project-Centered UI (4 commits):**
- System dashboard health check: internal gateways + self-restart
- Project-centered UI: build plan progress, recent runs, ADRs, active blockers, start new work
- Menter output surfaced in pipeline feed (was stored but not displayed)
- All 6 pipeline roles now visible: Brain, Drafter, Reviewer1, Reviewer2, Menter, Verify

---

## What the ADRs Don't Capture

The 16 ADRs (ADR-SEED-001 through ADR-SEED-016) were all recorded between June 7 and June 19. They represent the governance-era decisions. The following real decisions were made by direct action, not by ADR:

1. **Breaking from the tier system** — No ADR. Eric simply stopped requiring tier-by-tier gating and let models build directly.
2. **One container, six profiles** — No ADR. Chosen over six separate containers for resource efficiency. Implemented directly.
3. **Health check checks internal gateways** — No ADR. Fixed a broken implementation, not a governance decision.
4. **34 native guardrails + 22 external gates** — No ADR. Built directly from the deterministic guardrail spec, which itself was written during the build, not pre-governed.
5. **Self-evolution bridge** — No ADR. Pipeline narrative feeds back into the knowledge base. Built as a feature, not a governance decision.
6. **Project-centered UI** — No ADR. Built from the case study of CIS itself.
7. **GLM-4.7-Flash as drift model** — No ADR. Performance optimization, 4x faster than Qwen for the same task.

The DEV-PIVOT table (17 entries) attempted to track what was still relevant but was created on June 30 and never updated after that. 4 entries were marked INVALIDATED, 2 PARTIALLY_INVALIDATED, 11 still LIVE — but the LIVE entries reference capabilities that have since been built. The table is stale.

---

## The Three Breaks

### Break 1: Claude/ChatGPT Governance → Direct Building (June 19-20)
Eric recognized that the ADR + closeout + tier process was governance theater. The FD.1 revert-and-rebuild on June 19-20 was the last act under the old process. After that, no more ADRs were recorded.

### Break 2: DeepSeek Pipeline Circular Building → GLM Direct Build (July 7-8)
The pipeline had stalled with circular building — specs about specs, reviews about reviews. Eric allowed DeepSeek and then GLM to go through and build what was needed. The 18 commits on July 8 are the result: a working pipeline relay, end-to-end verification, data integrity fixes, and a passing test.

### Break 3: Stale Context → Fresh Start (July 12, current)
The current break. Eric wants to stop using Telegram and host-level agents to do work, and start working through the pipeline UI. The project-centered UI was built to enable this. The goal is to transition from external agent orchestration (via Telegram chats) to internal pipeline orchestration (via the control plane UI).

---

## Self-Evolving Implication

This history document exists to demonstrate a pattern: when the build plan becomes obsolete, practical direct action produces better results than governance ceremony. The self-evolving feature should:

1. **Detect when progress stalls** — if the same spec is being revised without implementation, flag it.
2. **Allow direct action breaks** — when a model can build the thing, let it build the thing. Document after.
3. **Track real decisions, not just ADRs** — the most consequential decisions in this project were made by breaking from the documented process.
4. **Invalidate stale tracking** — the DEV-PIVOT table is stale. The ADRs are historical. The git log is the real record.
5. **Preserve the reasoning** — not "what was decided" but "why the process was abandoned in favor of direct action."

---

## Summary Statistics

| Metric | Governance Era | Direct Action Era | GLM Build Era |
|--------|---------------|-------------------|---------------|
| Duration | 20 days | 18 days | 5 days |
| Commits | ~160 | ~20 | ~50 |
| ADRs | 16 | 0 | 0 |
| Working pipeline | No | Partial | Yes |
| Working UI | Portal v0.1 | Front door | Control plane v1.1 |
| Guardrails | 0 | 0 | 56 |
| Pipeline runs to consensus | 0 | 0 | 23 |

The GLM build era produced more working software in 5 days than the governance era produced in 20. That's the lesson.
