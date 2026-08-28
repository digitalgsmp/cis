# CIS Development Timeline & Vision

## The Original Vision (Pre-CIS Era)

Eric started working with Claude, Gemini, and ChatGPT as independent advisors. His goal:
get LLMs to help him think, contribute expertise, and check each other's work.

Eric's own words (from AGENTS.md §12 Seed Intent):

> "I don't want summaries, I am trying to build a system that works from the raw files."

> "the LLMs are the tools, I am trying to get LLMs to help me think by contributing factual
> information and expertise. when I sit down and interact with the LLMs they don't remember
> anything and the overall vision is not apparent to combine the vision of where I am trying
> to get to, to why we are working on the immediate task."

> "I need checks and balance, I am not a coder and if I don't trust something one of you says
> I have to be able to paste it for another model to evaluate and give me independent analysis.
> that is what claude and chatgpt did to each other. I need a worker who is constrained to my
> working methods and two objective reviewers as expert advisors."

> "LLMs are pretty smart, concern is alignment of action with understood intent."

The problem: models didn't remember between sessions, couldn't see each other's work,
had no shared context. Eric was manually copy-pasting between ChatGPT, Claude, and Gemini.

## Timeline — Three Eras

Eric's project went through three distinct eras. The transitions between eras are
themselves the most consequential decisions — and none were captured as ADRs.
See [governance_vs_direct_action.md](governance_vs_direct_action.md) for the full
pattern and self-evolving implications.

### Era 1: Governance Theater (May 31 – June 19)

Claude and ChatGPT guided Eric through heavy governance: ADRs, tier-by-tier build
plan, closeout rituals, DEV-PIVOT documents. Progress was real but slow — ~160
commits in 20 days, no working pipeline.

- **May 18** — Seed intent: three Hermes folders (DeepSeek V4, R1, Qwen 30B MOE) with UI chats
  so models could verify each other's opinions
- **May 20** — Vision: knowledge base in SQLite, vectorized to VDB. Models don't remember;
  the system remembers for them
- **May 25** — Core frustration articulated: LLMs don't remember, vision not apparent
- **May 31** — Initial git commit. CIS source tree established
- **June 1-7** — Tiers 0-5: deliberation engine, deterministic gates, SQLite spine (45+ tables),
  context export pipeline, HCP packet system for external advisors
- **June 7** — 16 ADRs recorded (ADR-SEED-001 through 016). **These are GOVERNANCE-ERA
  ARTIFACTS, not real decisions.** They were produced by Claude/ChatGPT advisory process
  that Eric later recognized as governance theater. Do not treat them as current decisions.
- **June 8-9** — Tiers 6-7: pipeline integration, Kanban coordination (later retired),
  intent-to-workflow architecture (Tier 7R)
- **June 12** — Tier 7R complete: WorkIntent schema, CIS/SWA domain adapters, process manager,
  human approval gate, dead letter handling, acceptance tests
- **June 13** — Tiers 8-10: MCP bridge, ChromaDB VDB, UI display views.
  298K messages ingested from 15 sources (archive 165K, cis_docs 75K, swa_project 23K)
- **June 14** — Tier 11A-D: Dashboard, Eric Gate approval, Drafter-Reviewer handoff specs
- **June 16** — Gateway collapse bug investigated (BLK-SEED-005) — false positive, closed
- **June 18** — Docker containment proposal. Enforcement architecture: three-layer process
  isolation (ADR-015/016). Approved via dual Claude + ChatGPT review
- **June 19** — Enforcement primitive approved. FD.1 MCP dispatch tools built, reverted, rebuilt.
  **Last act under governance process. No more ADRs after this date.**

### Era 2: The Break — Direct Action (June 20 – July 7)

Eric broke from the tier-by-tier governance process. No more ADRs, closeout rituals,
or tier gating. The build plan became a reference, not a constraint. ~20 commits in
18 days. Partial pipeline working.

- **June 20** — FD.1 MCP dispatch tools rebuilt successfully (after revert)
- **June 22-23** — CIS Control Portal v0.1 — multi-model chat, thread tracking, roadmap tab
- **June 24** — Phase PD CLOSED. Loop-breaker root cause committed. Live gateway monitor API
- **June 25** — Claude audit PASS. MWL sealed container closes self-disable bypass
- **June 28-29** — CIS front door: adapter API port 5000, intent alignment, knowledge search.
  Claude audited all work — PASS. Pre-commit hook for auto-regen
- **June 30** — Session handoff spine table. DEV-PIVOT status tracking created
  (17 entries, 4 immediately INVALIDATED — governance docs couldn't keep up with real progress)
- **July 7** — Gateway configs reconciled. Master goal inventory: 107 items.

### Era 3: The GLM Build — The Real App (July 8 – 12)

Eric allowed DeepSeek and then GLM 5.2 to build directly without ceremonial process.
The pipeline stall was broken. ~50 commits in 5 days. Working pipeline, 56 guardrails,
control plane UI, 23 consensus runs. **More working software in 5 days than 20 days
of governance.**

- **July 8** — Production pipeline relay, container multi-profile, verify isolation,
  data integrity fixes, code review gate, full pipeline end-to-end PASS (18 commits)
- **July 9** — Self-evolution bridge: pipeline narrative to knowledge base
- **July 10** — 14-component control plane build + 34 native guardrails + 22 external gates (56 total)
- **July 11** — Intent provenance, semantic drift detection (GLM-4.7-Flash 90 tok/s),
  brain chat UI, backchannel interjections. First CONSENSUS_REACHED run.
- **July 12** — Project-centered UI, menter_output surfaced in pipeline feed, dev pivots
  and closeout stats in project overview, real development history documented

### July 2026 — Container Pipeline & Control Plane

- **July 3** — cis-hermes:pinned container created (enforcement proof of concept)
- **July 7** — Master goal inventory: 107 items (CIS 30/12 done, SWA 35/0, WIASW 15/0).
  Gateway renaming to model-agnostic role names. Docker group escalation documented
- **July 8** — Production pipeline relay (1,500+ lines). Decision: one container, 6 profiles
- **July 9** — Container transition: all 6 gateways inside cis-pipeline. First pipeline run
- **July 10** — 34 guardrails wired. 14-component control plane spec. UI v1.1.0 (4 tabs)
- **July 11** — Intent provenance, drift detection (GLM-4.7-Flash 94 tok/s), brain chat UI,
  backchannel interjections. Full pipeline run: 11 phases, CONSENSUS_REACHED
- **July 12** — System dashboard health check fixed. Dead containers removed. Pushed to GitHub

## What's Built and Working

- Gated container with 6 internal Hermes gateways
- Pipeline: Brain → Review → Draft → Review → Menter → Verify with provenance + drift detection
- 34 guardrails (tool-loop prevention, context injection, secret detection, etc.)
- Knowledge base: 298,508 messages, FTS5 + ChromaDB semantic search
- UI: Control Panel v1.1.0 — Brain chat, Pipeline feed, Runs browser, System dashboard
- Eric Gate: approval step where Eric approves/rejects/refines
- Enforcement: sealed container, worker can't disable plugins
- SQLite spine: 45+ tables

## What's Still Needed

### Before creative work / SWA:

1. **Remote access** — Sunshine installed but not running. Tailscale not installed.
   2 users: "vector" (local) and "pirate" (remote, another state). RTX 4090 NVENC
2. **Corpus scrape** — Pass 1 scrape to recover Eric's verbatim intent from archive.
   Blocking prerequisite — everything downstream decided from recovered corpus
3. **Intent alignment** — Accumulated intentions need extraction, categorization, pipeline review
4. **UI as primary interface** — Conversational Brain chat + live feed + backchannel needs
   real-world testing. Eric wants UI to replace terminal for routine operations
5. **Loop closure** — Pipeline results aren't recorded as reusable trajectories yet.
   Corrections aren't fed back as learning signals

### For SWA specifically:

- SWA is a **separate application**, product OF the CIS process, with own repo and backend
- No SWA code exists yet — entirely vision/intent within corpus
- Primary use case: video tutorial indexing for skill training, creative asset management
- Build order: CIS complete → corpus scrape → SWA build begins
- WIAS workbook is the origin document for both CIS and SWA

## Build Plan Status

| Node | Tier | Status |
|------|------|--------|
| Deliberation Engine | 0 | COMPLETE |
| Deterministic Verification Gates | 1 | COMPLETE |
| Kanban Coordination Layer | 2 | DEFERRED (retired, Tier 7R replaces) |
| Pipeline Smoke Test | 3 | COMPLETE |
| SQLite Spine | 4 | COMPLETE |
| Context Export Pipeline | 5 | COMPLETE |
| Pipeline Integration | 6 | COMPLETE |
| Full Durable Router Pipeline | 7 | DEFERRED (superseded by 7R) |
| Router Reclassification | 7.1 | COMPLETE |
| Corpus Audit | 7.5a | COMPLETE |
| Clean Subset Import + FTS5 | 7.5b | COMPLETE |
| MCP Bridge | 8 | COMPLETE |
| Chroma/VDB | 9 | COMPLETE |
| CIS UI / Custom Display Views | 10 | COMPLETE |
| Intent-to-Workflow Architecture | 7R | COMPLETE |
| WorkIntent schema | 7R.1 | COMPLETE |
| CISAdapter | 7R.2 | COMPLETE |
| SWAAdapter | 7R.3 | DEFERRED |
| Process Manager | 7R.4 | COMPLETE |
| Human approval gate | 7R.5 | COMPLETE |
| Dead Letter handling | 7R.6 | COMPLETE |
| Acceptance test suite | 7R.7 | COMPLETE |
| Dashboard, Navigation, System Overview | 11A | COMPLETE |
| Eric Gate Approval Record | 11B | COMPLETE |
| Drafter-to-Reviewer Handoff | 11C | COMPLETE |
| Reviewer-Side Handoff | 11D | COMPLETE |
| Knowledge Base Ingestion | 12 | COMPLETE |
| Abstraction Layer | 13 | COMPLETE |
| Enforcement — Container Isolation | ENFORCEMENT | PENDING |

**Assessment**: ~80% through CIS infrastructure. Hard part (enforcement, pipeline, KB, UI) done.
Remaining: remote access, corpus scrape, real-world testing, loop closure.

## Pre-Commit Hook Behavior

The CIS repo has a pre-commit hook that auto-regenerates HCP exports and AGENTS.md from the
SQLite spine. This means:
- `git commit` regenerates 13 export artifacts and auto-stages them
- `git commit --amend --no-edit` produces NEW timestamp diffs (the hook runs again)
- This is expected behavior, NOT a bug — don't try to "fix" the timestamp drift
- The hook also runs an export agreement gate (verifies artifact count matches manifest)
- Warning "expected 12 artifacts, found 13" is benign — manifest count hasn't been updated

## Key Architecture Documents

- `data/drive_imports/X_*.md` — Original architecture documents (pre-LLM analog system design)
- `docs/claude crystallizes the vision.txt` — Claude session establishing pipeline execution
- `docs/DEV-PIVOT-06_BUILD_DIRECTION.md` — CIS final build direction, SWA separation
- `docs/MASTER_GOAL_INVENTORY.md` — 107 items across CIS, SWA, WIASW
- `docs/SECURITY_DOCKER_GROUP_ESCALATION.md` — Docker group vulnerability + transition plan
- `docs/SPEC_CONTROL_PLANE_BUILD.md` — 14-component control plane spec
- `docs/HANDOFF_PIPELINE_BUILD.md` — Container transition handoff
- `docs/HANDOFF_2026_07_12_SYSTEM_DASHBOARD.md` — System dashboard session handoff

## The Bootstrapping Problem

Eric articulated the core dilemma:
"I need a tool that will allow me to control the tools that I cannot control
but need to use to build their controller."

Resolution: Eric doesn't need to control the LLM, just the interface — what goes in,
what comes out, what gets recorded. The container enforces the interface. The LLMs
do the thinking inside the enforced boundary.
