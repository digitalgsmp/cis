# CIS — Mission, Intentions, and Current State

**Audience:** Frontier models (Claude, ChatGPT) working on CIS
**Source:** 188 intention cards extracted from 444 sessions across 4 AI agents (May 21 – Aug 2, 2026)
**Authority:** Eric's verbatim words, not summarized or interpreted
**Status:** This document replaces the build-plan framing of earlier HCP versions

---

## 1. What Eric Is Trying to Build

Eric is building a system where multiple AI models with different training data review each other's work, validate against his documented intentions, and execute in a constrained environment where they can't drift from the mission.

He is not building a chatbot. He is not building a code generator. He is building a **validation pipeline** — a system that enforces alignment between what AI agents produce and what Eric actually said he wanted.

He is a non-coder. He routes between models manually. He makes decisions after seeing independent analysis. The system must work FOR him, not require him to work for it.

## 2. Core Intentions (Persistent Across 4 Months)

### 2.1 Multi-Model Review With Different Training Data
**What:** Every consequential output must be reviewed by at least two models with different training data and different blind spots.
**Evidence:** 40+ exchanges from May 21 ("REVIEW THIS ARCHITECTURE. Do not build. Flag problems only.") through today.
**Rejected:** Single-model drafting, self-review, trusting any model's self-report.
**State:** Active — dual reviewers (Qwen 3.7 Max + GLM 5.2) operational on ports 8643 and 8647.

### 2.2 Knowledge Base as the Source of Truth
**What:** All conversations, all documents, all decisions must be searchable so models can verify claims against what Eric actually said.
**Evidence:** May 21 ("Create a Hermes built-in tool: retrieve_from_knowledge_base"), June 24 ("I need to find my own words"), July 24 ("the mining failed because it extracted entities instead of intent"), Aug 2 ("use all agent session verbatim logs").
**Rejected:** Keyword-only search, summary-based retrieval, losing context through extraction pipelines.
**State:** FTS5 + ChromaDB operational (287K messages). Intention card index built (188 cards). Live session ingestion NOT YET connected — KB frozen since July 24.

### 2.3 Containerized Enforcement
**What:** Agents must run in constrained environments where they cannot bypass rules. Root-owned control plane mounted read-only. Agents cannot author their own contracts.
**Evidence:** June 16-19 ("make the root owned docker carry out its function to secure the pipeline"), June 23 ("my concern is that you are still trying to make a work around and bypass root ownership").
**Rejected:** Trust-based enforcement, agents self-policing, workarounds that bypass root ownership.
**State:** Enforcement primitive proven (5 walls held). Override-plane test passed. Container isolation NOT YET wired into live pipeline.

### 2.4 Portal as Control Plane
**What:** A single UI where Eric can see all agents, route between them, approve/reject/reframe. Not a chat interface — a command center.
**Evidence:** June 1 ("redesign AdvisorChat into side-by-side 1x4 layout"), June 23 ("the portal is suppose to be the control plane the new ui to run the pipeline, i dont want a pass through link to the old site"), July 5 ("Eric is formalizing and validating a unified system architecture").
**Rejected:** Pass-through links to old UI, chat-only interfaces, separate dashboards.
**State:** Portal operational on port 5000. Monitor tab needs integration. Control plane not yet the default workflow — agents still interact through terminal/Telegram.

### 2.5 Intelligence Over Mechanism
**What:** The model IS the mechanism. Don't build extraction pipelines, pattern matchers, or keyword filters when the model can read and understand directly. Give it access + a clear question.
**Evidence:** July 3 ("just by getting annoyed one day and ask the model what do you think my intention is here... the LLM described exactly what I wanted to do... this is where I understood that using the models complex inference ability was the solution to the archive"), July 24 ("what was the prompting gap that did not make my intention the focus"), Aug 2 ("An intention is not a direct ask").
**Rejected:** Pre-built query strategies, extraction pipelines, keyword-based filtering, reducing intentions to build tasks.
**State:** Active principle. Applied in intention card generation (Qwen reasoning, not keyword matching). NOT consistently applied across all pipeline components.

### 2.6 Independent Runtime Cells
**What:** Each Hermes agent should be a fully self-contained installation — its own source tree, venv, service unit, logs. Not a shared install with profile switching.
**Evidence:** June 15 ("define the best way you can devise to replace the single installation of hermes with 4 individual entities that are full independent installations"), June 16 ("The best design is not 'copy the existing install four times.' The best design is make each Hermes profile a self-contained runtime cell").
**Rejected:** Shared-code multi-profile setup, symlink farms, single-venv-with-config-switching.
**State:** NOT YET IMPLEMENTED. Current deployment uses shared Hermes source with per-profile home directories.

### 2.7 Intent Alignment Before Execution
**What:** Before any agent builds anything, verify that what they're about to build matches what Eric actually asked for. Reviewers must check intent alignment, not just technical correctness.
**Evidence:** June 25 ("The reviewer should have a measurement criteria sheet that lists my core intentions... they measure the draft spec against those intentions"), July 4 ("intentions are NOT a build checklist. They are the reference material the pipeline agents infer against"), Aug 2 ("the models keep defaulting to literal tasks instead of considering how each task is intended to relate to the overall scope").
**Rejected:** Reviewers checking only format/accuracy, skipping intent verification, accepting technically-correct but misaligned outputs.
**State:** Intention cards created (188 cards). Pipeline NOT YET wired to check alignment against cards before execution.

### 2.8 Adversarial External Review
**What:** Claude and ChatGPT serve as external auditors. When the pipeline's internal reviewers disagree or Eric doesn't trust the output, route to frontier models for independent analysis.
**Evidence:** May 21 ("I need checks and balance, I am not a coder and if I don't trust something one of you says I have to be able to paste it for another model to evaluate"), June 20 ("Claude and ChatGPT: Tier 3 escalation — pass/fail review when deliberation does not satisfy Eric").
**Rejected:** Treating external models as primary workers, giving them direct execution authority.
**State:** HCP provides context to external models. No automated routing to Claude/ChatGPT — Eric copy-pastes manually. This is his deliberate design.

### 2.9 Anti-Enterprise Bias
**What:** Reject complexity, governance theater, and over-engineering. If it requires a framework, a multi-phase rollout, or a stakeholder review, it's wrong. Build simple, direct things that Eric can see and click.
**Evidence:** June 18 ("I don't want summaries, I am trying to build a system that works from the raw files"), June 24 ("stop building frameworks around frameworks"), July 3 ("this is where I understood that using the models complex inference ability was the solution to the archive"), Aug 2 ("An intention is not a direct ask").
**Rejected:** Architecture documents, governance ceremonies, multi-phase roadmaps, enterprise vocabulary (scalable, robust, modular, extensible, orchestration, infrastructure).
**State:** Banned word list active in card_gate.py. Still a recurring fight — models default to enterprise patterns.

## 3. What's Built (Infrastructure)

### Gateways and Ports
| Profile | Port | Model | Role |
|---------|------|-------|------|
| Brainstorm | 8644 | deepseek-v4-pro | Challenges assumptions before drafting |
| Drafter | 8645 | deepseek-v4-pro | Produces proposals and specs |
| Reviewer 1 | 8643 | qwen/qwen3.7-max | Primary reviewer |
| Reviewer 2 | 8647 | z-ai/glm-5.2 | Secondary reviewer (different blind spots) |
| Implementer | 8646 | deepseek-v4-pro | Executes only — no deliberation |
| Verifier | 8648 | z-ai/glm-5.2 | Evidence-based verification |
| Prime/Chat | 8642 | deepseek-v4-pro | General interaction, NeMo firewall |

### Infrastructure
- **Host:** creative-vm (Ubuntu 24.04, 192.168.1.15) on Proxmox wander (192.168.1.200)
- **Storage:** 500G + 250G local-lvm, 10TB archive passthrough
- **Repo:** github.com/digitalgsmp/cis
- **Container:** cis-hermes:pipeline image, enforcement at /opt/cis-control/
- **Knowledge Base:** SQLite spine (cis_memory.db, 364MB) + ChromaDB (9.3GB, 287K vectors)
- **Portal:** Flask on 127.0.0.1:5000, React UI at /ui
- **Local Models:** Qwen3-VL-30B on port 8002, GLM-4.7-Flash on port 8003

### Source Patches (Permanent)
1. DeepSeek reasoning_content extraction (run_agent.py, api_server.py, provider init, usage_pricing.py)
2. api.deepseek.com in _supports_reasoning_extra_body allowlist

## 4. Constraints and Non-Negotiables

### What You Must Do
1. **Provide evidence, not claims.** Every assertion must be backed by raw command output, file contents, or cited sources.
2. **Validate against Eric's intentions before executing.** Check the 188 intention cards.
3. **Get independent review before building.** Route through at least one reviewer with different training data.
4. **Preserve Eric's exact words.** Don't summarize, paraphrase, or "improve" what he said.

### What You Must Never Do
1. **Don't build without verification.** Self-reported completion is not accepted.
2. **Don't use enterprise vocabulary.** Banned: architecture, framework, governance, roadmap, phase, tier, milestone, scalable, enterprise, microservice, refactor, robust, comprehensive, modular, extensible, orchestration, infrastructure.
3. **Don't replace Eric's routing.** He manually decides which model does what. Don't automate his involvement.
4. **Don't build extraction pipelines.** The model is the mechanism. Give it access + a clear question.
5. **Don't bypass the container.** All execution must happen in constrained environments with read-only control plane.
6. **Don't trust self-reports.** Model claims about what they built must be independently verified.

## 5. How to Work on CIS

### The Validation Workflow
```
1. Understand the intention → Read the 188 cards for this domain
2. Propose an approach → Drafter produces spec
3. Get independent review → Two reviewers with different training data
4. Eric approves/rejects/reframes → Human gate (not bypassable)
5. Execute in container → Implementer runs in constrained environment
6. Verify with evidence → Verifier checks output against intention
7. Record in knowledge base → Results written to spine, available for future validation
```

### Current Priority
Based on intention card frequency and persistence:
1. **Wire KB to live sessions** (Intention 2.2) — KB frozen since July 24, no live write path
2. **Wire intention cards into pipeline** (Intention 2.7) — reviewers must check alignment against cards
3. **Container isolation in live pipeline** (Intention 2.3) — enforcement proven but not wired
4. **Portal as true control plane** (Intention 2.4) — agents still interact through terminal/Telegram

### Evidence Available
- 188 intention cards: `/mnt/projects/cis/cards/intentions.jsonl`
- 444 session transcripts: `/home/eric/.hermes-*/state.db`
- Knowledge base: `/mnt/projects/cis/data/cis_memory.db` (SQLite + FTS5) + `data/chroma_data/` (ChromaDB)
- Full infrastructure state: `config/agents_static.yaml`

---

*This document replaces the tier/build-plan framing of previous HCP versions. It is derived from 188 intention cards extracted via Qwen 30B reasoning across all agent sessions. Infrastructure facts verified as of 2026-08-02.*
