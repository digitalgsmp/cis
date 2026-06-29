# CIS Integration Assessment — What CIS Was Built For, What It Prevents, and How It Registers on Hermes

**Date:** 2026-06-17 | **Author:** R1 Reviewer (deepseek-v4-pro) | **Purpose:** Pre-integration analysis

## 1. What CIS Was Built For — Eric's Original Intent

Source: AGENTS.md §12 — Seed Intent, verbatim from Eric's recorded sessions.

> I don't want summaries, I am trying to build a system that works from the raw files.

> I installed three hermes folders one for deepseek v4, one for deepseek r1 and one for qwen 30b MOE. Then made a UI interface with a chat for each so that I can have the models verify each other's opinions on topics and check the code that's written since they all have different training data and different blind spots. I then want to build a knowledge base in the sqlite db that will be vectorized and saved to a vdb.

> The LLMs are the tools, I am trying to get LLMs to help me think by contributing factual information and expertise. When I sit down and interact with the LLMs they don't remember anything and the overall vision is not apparent to combine the vision of where I am trying to get to, to why we are working on the immediate task.

> I need checks and balance, I am not a coder and if I don't trust something one of you says I have to be able to paste it for another model to evaluate and give me independent analysis. That is what Claude and ChatGPT did to each other. I need a worker who is constrained to my working methods and two objective reviewers as expert advisors.

**Core purpose distilled:**
1. Multi-model verification — different training data → different blind spots → cross-checking
2. Persistent memory — LLMs that remember the vision across sessions
3. Automated routing — Eric is not the manual transport layer between models
4. Human-in-the-loop approval — Eric Gate as final decision authority
5. Evidence-backed responses — raw evidence, not model self-report

---

## 2. What CIS Prevents — The Guard-Rail Functions

Every CIS mechanism exists to catch a specific failure mode. Here's the complete catalog.

### 2.1 Trust Failures (ADR-SEED-002)

| What CIS prevents | How | Failure if absent |
|------------------|-----|-------------------|
| Self-reported completion without evidence | Verification Hardening Rule: git diff, test output, DB queries required | Implementer says "done" but code is broken or missing |
| Hallucinated claims masquerading as facts | Evidence-Backed Response Rule: raw terminal output pasted, not summarized | Agent fabricates API responses, file contents, test results |
| Rubber-stamp reviews | Dual-reviewer deliberation (R1+Qwen) with cross-feed objections | Reviewer says "LGTM" without reading |

### 2.2 Knowledge Failures

| What CIS prevents | How | Failure if absent |
|------------------|-----|-------------------|
| Training-data staleness | Staleness gate: web freshness check before deliberation | Hermes v0.13.0 assumed current when v0.16.0 released; 3,000+ commits of new features missed |
| Context amnesia across sessions | SQLite spine + AGENTS.md + HCP exports | Each session starts from zero; vision and progress lost |
| Version drift in static configs | `generate_agents_md.py` regenerates from DB source of truth | AGENTS.md says "Tier 11C" when 11D is complete; gateways listed as "Paused" when running |

### 2.3 Process Failures

| What CIS prevents | How | Failure if absent |
|------------------|-----|-------------------|
| Scope creep by implementer | OQ-SEED-005: Approved File Manifest enforced during implement | Implementer builds test suite, refactors adjacent code, "helps" beyond directive |
| Constraint bypass through placeholder data | NOT NULL FKs enforced with 409 rejection, no auto-create | Placeholder goal_reference defeats the approval gate |
| Pipeline bypass (agents calling scripts directly) | Gate sequence in gate_runner.sh (6 gates before Eric approval) | Agent runs `generate_agents_md.py` directly, no oversight fires |
| Role confusion | HERMES_HOME + gateway endpoint derive role, not model self-description | Drafter acts as Reviewer, Implementer drafts proposals |
| Silent gate failures | PASS/FAIL criteria, numbered checks, COMMAND/OUTPUT evidence format | Gate says "PASS" but actually can't reach the endpoint |
| Concurrency races | Atomic UPDATE...WHERE + rowcount checks in dispatch scripts | Two agents claim the same dispatch row |

### 2.4 Protocol Failures

| What CIS prevents | How | Failure if absent |
|------------------|-----|-------------------|
| Unstructured model output | FINAL_JSON required on every Drafter/Reviewer response | Orchestrator can't parse model intent; freeform text routes wrong |
| Missing FINAL_JSON | Repair prompt, then fallback text scanning | Model produces analysis but no machine-parseable verdict |
| Cross-model agreement without genuine deliberation | Objections cross-fed between reviewers; must address each | Both say "CONSENSUS_REACHED" without reading each other's concerns |
| Single-model blind spots | Two independent reviewers with different models (R1/deepseek-v4-pro + Qwen/qwen3-vl-30b) | One model's training-data gap becomes the pipeline's gap |

---

## 3. What Hermes Already Provides — CIS Custom Code That Duplicates Hermes

| CIS Component | Current Implementation | Hermes v0.16.0 Equivalent | Duplication |
|--------------|----------------------|--------------------------|-------------|
| 5 separate Hermes installs | Manual installs at ~/.hermes, ~/.hermes-r1, ~/.hermes-v4pro, ~/.hermes-v4impl, ~/.hermes-qwen | Profiles system: `hermes profile create drafter` | **High** — profiles give per-role isolation with one install |
| Drafter/Reviewer/Implementer role separation | Manual config per install + AGENTS.md role badges | Per-profile SOUL.md + config.yaml model assignment | **High** — profiles are purpose-built for this |
| Closeout triggers | Manual: Eric runs closeout scripts | Hermes cron: "Check stale workflow_runs every 4h" | **High** — natural-language scheduling replaces custom trigger code |
| Implementer parallel builds | Custom Python subprocess management | Hermes sub-agent delegation (parallel workers) | **Medium** — sub-agents give isolated contexts |
| CIS UI (Tier 10) | Custom Flask blueprint + 6 React views | Hermes web dashboard (admin panel, point-and-click) | **Medium** — dashboard extensions vs. custom stack |
| External advisor integration | Custom HTTP calls in `reviewer_reconcile.py` | Hermes MCP client: query ChatGPT/Claude through MCP | **Medium** — MCP standard vs. custom urllib calls |
| Eric Gate notifications | Telegram bot via custom platform code | Hermes multi-platform messaging (Telegram, Discord, Slack, etc.) | **Medium** — Hermes messaging already connects all platforms |
| Model-to-model routing | `reviewer_reconcile.py` calls gateway APIs directly | MCP server per profile: Orchestrator queries through MCP | **Low-Medium** — direct API calls work, MCP adds discoverability |
| Pipeline gate scripts | 37 bash scripts in `tools/gates/` | Hermes skills loaded per profile | **Low** — skills can encode gate logic, but bash is deterministic and auditable |
| Staleness check | Custom `staleness_check.py` with DDG/GitHub API | Hermes `web_search` tool via skill | **Low** — custom script is purpose-built; Hermes web_search is general-purpose |

---

## 4. What CIS Must Preserve — Hermes Has No Equivalent

These are the non-negotiable CIS capabilities that Hermes does not provide.
They must survive integration intact — they define what CIS IS.

| CIS Feature | Why Hermes Can't Replace It |
|------------|---------------------------|
| **Adversarial verification** (ADR-SEED-002) | Hermes trusts its own self-evaluation. CIS trusts nothing. The entire self-improving loop (skills from completed tasks, memory from self-assessment) is the opposite of CIS methodology. |
| **Dual-model deliberation with cross-feed** | Hermes has no concept of "two independent models reviewing the same proposal and exchanging objections." Sub-agents are workers, not critics. Different models on different profiles is CIS architecture, not a Hermes feature. |
| **FINAL_JSON protocol** | Hermes has no structured output requirement for agent responses. Freeform text is the default. CIS requires machine-parseable verdicts with role, status, objections, recommendation. |
| **Eric Gate** | Hermes has no human-in-the-loop approval gate. The agent loop runs autonomously. CIS requires explicit human approval before execution. |
| **Evidence-Backed Response Rule** | Hermes summarizes and paraphrases. CIS requires raw terminal output, git diff, DB queries pasted verbatim. This is cultural/process, not technical — but it's the core trust mechanism. |
| **Build plan spine authority** | `build_plan_nodes` + `project_state` with supersession model. Hermes has memory and session state, but no multi-session build plan with dependency ordering and gate-verified state transitions. |
| **Gate sequence** | Deterministic bash gates with PASS/FAIL/EXIT codes. Hermes has no equivalent — skills are markdown documents with procedural knowledge, not executable enforcement. |
| **Role enforcement** (ADR-SEED-003, 004) | Hermes has no mechanism to ensure Drafter≠Reviewer≠Implementer. A profile can load any skill and call any tool. CIS requires that implementation directives route only to the Implementer, drafts only from the Drafter, etc. |

---

## 5. The Integration Architecture

CIS should register on Hermes, not be absorbed by it. The model:

```
┌──────────────────────────────────────────────┐
│                  CIS LAYER                     │
│  (Adversarial methodology, FINAL_JSON,        │
│   Eric Gate, Evidence Rules, Build Plan)       │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │         CIS → HERMES ADAPTER              │ │
│  │  Maps CIS needs to current Hermes features │ │
│  │  Changes when Hermes updates, CIS doesn't  │ │
│  └──────────────────────────────────────────┘ │
│                     │                          │
│  ┌──────────────────┴───────────────────────┐ │
│  │           HERMES PLATFORM                │ │
│  │  Profiles, Skills, Dashboard, Cron, MCP, │ │
│  │  Sub-agents, Messaging, Model Picker     │ │
│  └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

**The adapter layer is the key.** It isolates CIS from Hermes version changes. When Hermes ships v0.17.0 with a new feature, only the adapter changes. CIS methodology stays stable.

### What moves from CIS custom code to the adapter layer:

| CIS Component | Current | Adapter maps to Hermes |
|--------------|---------|----------------------|
| Role isolation | 5 installs, manual config | Hermes profiles with per-profile SOUL.md |
| Drafter/Reviewer routing | orchestrator HTTP calls to gateway ports | MCP-based coordination between profile servers |
| Closeout triggers | Manual scripts | Hermes cron jobs |
| Implementer builds | Custom subprocess | Hermes sub-agent delegation |
| UI views | Flask + React | Hermes dashboard extensions or MCP views |
| Eric Gate delivery | Custom Telegram bot | Hermes multi-platform messaging |
| Staleness checks | Custom DDG/GitHub script | Hermes web_search tool via skill |

### What stays in CIS as-is:

| CIS Component | Why it stays |
|--------------|-------------|
| FINAL_JSON protocol | Hermes has no structured output requirement |
| Adversarial deliberation engine | Two-model cross-feed is CIS-unique |
| Evidence-backed response rules | Cultural, not technical — enforced by skill, not Hermes |
| Eric Gate approval flow | Human-in-the-loop is CIS design, not a Hermes feature |
| Build plan spine (DB) | Multi-session state with dependency ordering |
| Gate sequence logic | Deterministic bash gates are the enforcement mechanism |

---

## 6. What Needs to Change Before the Oversight Skill

The oversight skill should not be built on the current architecture. First:

### 6.1 Resolve the install question (OQ-SEED-007)

Current: 5 independent Hermes installs sharing a single venv — a contradiction.
The 4-install migration is blocked on the profiles evaluation: can 5 installs become 5 profiles under 1 install?

**If profiles work:** The oversight skill lives in one place, loaded by all profiles.
**If installs remain:** The skill must be duplicated across installs or loaded via symlink.

### 6.2 Fix the source-patch dependency

The 4 source patches (deepseek reasoning, api_server reasoning_content, usage pricing)
are applied to Prime's install. Other installs share the same venv. When Hermes
updates, patches break. This is the fragility the abstraction layer must solve.

### 6.3 Define the CIS skill bundle

What skills does each CIS role load?

| Profile | Skills |
|---------|--------|
| Drafter (v4pro, 8645) | cis-specification-authoring, writing-plans, staleness awareness |
| Reviewer (r1, 8643) | cis-specification-review, systematic-debugging, staleness awareness |
| Implementer (v4impl, 8646) | subagent-driven-development, test-driven-development, architecture-review |
| Prime/Eric (8642) | cis-pipeline-overview, hermes-agent, kanban-orchestrator |
| Qwen (8644/8002) | cis-specification-review (inference-only via llama-server, no tools) |

### 6.4 Define the oversight skill's enforcement points

The oversight skill must hook at these tool-call boundaries:

```
Before write_file/patch:    Has proposal been through deliberation?
Before sqlite3 INSERT:      Has migration been reviewed?
Before git commit:          Have gates passed?
Before terminal (destructive): Is this in the Approved File Manifest?
```

Each hook checks the spine for a valid gate record. If absent, blocks with a
message: "This action requires pre-execution oversight. Run gate_runner.sh first."

---

## 7. CIS ↔ Hermes v0.16.0 Feature Correlation

Eric has concluded: 5 separate installs are not required. Profiles satisfy the isolation
that was thought to need independent installations. This resolves OQ-SEED-007.

CIS will register as a Hermes **add-on** — a specialized UI and pipeline layer that
exposes CIS-specific functionality (adversarial deliberation, evidence-backed
verification, Eric Gate) on top of Hermes primitives. Below is the complete correlation
of every CIS feature to its Hermes v0.16.0 target.

### 7.1 Feature Correlation Table

| CIS Feature | Current (Custom) | Hermes v0.16.0 Target | Action |
|------------|-----------------|----------------------|--------|
| **Role isolation** (Drafter/Reviewer/Implementer/Prime) | 5 independent installs at ~/.hermes, ~/.hermes-r1, ~/.hermes-v4pro, ~/.hermes-v4impl, ~/.hermes-qwen | **Profiles** — `hermes profile create drafter` → isolated config, model, skills, SOUL.md per role | **Collapse to 1 install with 5 profiles** |
| **Per-role model assignment** | Manual config per install | **Model picker** — per-profile model assignment. Drafter=deepseek-v4-pro, Reviewer=deepseek-v4-pro or Claude, Qwen=qwen3-vl-30b | Assign via dashboard or config.yaml per profile |
| **Per-role personality** | AGENTS.md loaded by TERMINAL_CWD | **SOUL.md per profile** — each profile gets its own role-specific briefing | Migrate AGENTS.md role sections to per-profile SOUL.md |
| **Skill loading per role** | Manual skill_view() calls during session | **Skills marketplace** — Drafter auto-loads cis-specification-authoring, Reviewer loads cis-specification-review, Implementer loads subagent-driven-development | Publish CIS bundle; profiles auto-load role skills |
| **Pipeline dispatch** | Bash scripts + Python orchestrator calling gateway APIs | **MCP server per profile** — Orchestrator queries Drafter/Reviewer state via MCP instead of custom HTTP | Replace direct API calls with MCP tool invocations |
| **Deliberation engine** | `reviewer_reconcile.py` — urllib to gateway ports | **MCP coordination** — two profile servers queried independently, results compared | Wrap reconciliation in MCP tool; profiles expose `review_proposal` endpoint |
| **Closeout triggers** | Manual: Eric runs closeout scripts | **Hermes cron** — `hermes cron "Check stale workflow_runs and trigger closeout" every 4h` | Natural-language cron job, replaces custom trigger code |
| **Implementer parallel builds** | Custom Python subprocess management | **Sub-agent delegation** — `delegate_task` spawns parallel workers with isolated contexts | Replace custom subprocess with delegate_task calls |
| **External advisor integration** | `call_openai()` / `call_anthropic()` in reconcile.py | **MCP client** — query ChatGPT/Claude through MCP server connections | Register external models as MCP tools; remove custom HTTP |
| **Eric Gate notifications** | Custom Telegram bot code | **Hermes multi-platform messaging** — already connected to Telegram, Discord, Slack, etc. | Use Hermes send_message; Eric replies from any platform |
| **CIS UI dashboard** | Flask blueprint + 6 React views (Tier 10) | **Hermes web dashboard** — admin panel with point-and-click management | Expose CIS views as dashboard extensions or MCP views |
| **Staleness checking** | `staleness_check.py` — DDG + GitHub API | **Hermes web_search tool** — available to any profile via skill | Wrap staleness check as a Hermes skill using web_search tool |
| **Gate sequence (37 bash scripts)** | `tools/gates/*.sh` invoked by gate_runner.sh | **Hermes skills** — procedural knowledge documents loaded on demand | Migrate gate logic to skills; bash remains as audit trail |
| **Pipeline state tracking** | SQLite spine (`cis_memory.db`, 380MB) | **Per-profile state DB** — each profile has its own SQLite | Spine stays as cross-profile source of truth; profiles query it via MCP |
| **AGENTS.md generation** | `generate_agents_md.py` from spine + static YAML | **Hermes dashboard view** — live view of build plan, blockers, next actions | Replace static doc with live dashboard; keep AGENTS.md as export snapshot |
| **HCP export** | `generate_hcp.py` + `generate_all.py` | **MCP exposure** — external advisors query pipeline state through MCP instead of static packet | Replace static HCP with live MCP queries |

### 7.2 What This Means for the Architecture

**Before (current):**
```
5 independent Hermes installs → 5 venvs → shared source patches
Custom Python scripts → direct HTTP to gateway ports
Custom Flask UI → React frontend
Bash gate scripts → invoked manually or by orchestrator
Eric Gate → custom Telegram bot
```

**After (target):**
```
1 Hermes install → 5 profiles (each: own config, model, SOUL.md, skills)
MCP coordination → profiles expose pipeline state as MCP tools
Hermes dashboard → CIS views as extensions
Skills → gate logic loaded per profile, enforced at tool-call level
Hermes messaging → Eric Gate notifications on any platform
```

### 7.3 Resolved Questions

| Question | Resolution |
|----------|-----------|
| OQ-SEED-007: 4-install migration scope | **Resolved.** 5 installs → 1 install with 5 profiles. Migration scope is now: consolidate configs, create profiles, migrate SOUL.md content. |
| OQ-SEED-006: deliberation_rounds schema lossy | **Still open.** Profiles sharing one spine need `reviewer_output` column. Add before MCP exposure. |
| Source-patch fragility | **Mitigated by profiles.** Patches applied once to the single install, all profiles inherit. Updates don't require per-install re-patching. |
| Role enforcement (ADR-SEED-003/004) | **Profiles provide native isolation.** Drafter profile has no Implementer tools. Reviewer profile has no write access. Hermes enforces per-profile toolset configuration. |

### 7.4 WIAS and SWA — Domain Definitions

From the archive (WIAS Project Manager spreadsheet, CIS_Chat_2026-04_013, CIS_Chat_2026-04_016):

**WIAS** = **W**ord, **I**mage, **A**ction, **S**ound, **W**eb — Eric's creative production
workflow. Each stage represents a phase in the creative process:
- **W**ord: planning, concept, writing, research
- **I**mage: visual design, aesthetic language, imagery
- **A**ction: execution, interaction, motion, implementation
- **S**ound: final resonance, polish, audio, refinement
- **W**eb: distribution, publishing, social/public life

WIAS is not a linear pipeline — projects can enter any stage and exit from any stage.
Multi-exit paths are a core design requirement.

**SWA** = "Schedule field-use work" — a separate project at `/mnt/projects/swa/`
for case management (client intake, appointments, D.A.P. notes, goal tracking).
CIS Tier 7R treats SWA as a validation use case: the architecture must handle
SWA-domain intents, but CIS must not implement SWA features or modify the SWA codebase.

**LIFE** = Home, Body, Mind — the life management domain. Discovered during archive
analysis: the WIAS Project Manager spreadsheet always contained both creation (WIAS)
and life management (LIFE) as co-equal halves. The CIS build plan had assumed WIAS-only
until the spreadsheet was recovered. LIFE domain objects (home maintenance, fitness,
mindfulness) are structurally different from creative production assets.

**CIS** orchestrates all three domains through a common pipeline: WorkIntent →
Domain Classifier (CIS/SWA/WIAS/OUT_OF_SCOPE) → Domain Adapter → Process Manager →
Human Approval Gate.

**Eric requires UI and pipeline exposure for all three domains** (CIS, WIAS, SWA)
in the Hermes-integrated system.

---

## 8. Revised Migration Phases

| Phase | What | Prerequisite | Status |
|-------|------|-------------|--------|
| **P0** | Resolve BLK-SEED-005 (hermes-gateway-r1 service loop) | None | **RESOLVED** — false positive; patch #7 applied June 16; prime not poisoned |
| **P1** | Collapse 5 installs → 1 install with 5 Hermes profiles | None (BLK-SEED-005 resolved — false positive, patch #7 applied June 16) | **CONFIRMED by Eric** |
| **P2** | Define per-profile SOUL.md and skill bundles | P1 | PENDING |
| **P3** | Build CIS ↔ Hermes adapter layer (MCP-based) | P1 | **COMPLETE** (2026-06-27) — `runtime/abstraction/dispatch.py` + `runtime/api/adapter.py` built. 4 endpoints live on port 5000: health, profiles, dispatch, chat. MCP bridge extended with `cis_adapter_status` and `cis_adapter_dispatch`. Profiles not yet collapsed (P1 pending). Adapter routes to existing 5-install gateways. |
| **P4** | Build oversight skill with tool-call hooks | P2, P3 | PENDING |
| **P5** | Migrate gates from bash to skills where sensible | P4 | PENDING |
| **P6** | UI overhaul — Hermes dashboard views for deliberation, build plan, Eric Gate | P3 | PENDING |
| **P7** | External advisor integration via MCP | P3 | PENDING |
| **P8** | Closeout triggers via Hermes cron | P3 | PENDING |

---

## 9. Summary (Revised)

CIS registers on Hermes, not inside it. The adapter layer (P3, COMPLETE 2026-06-27)
exposes CIS functionality — adversarial deliberation, evidence-backed verification,
Eric Gate — on top of Hermes primitives (profiles, skills, MCP, cron, messaging).

**What's different after the 2026-06-27 session:**

1. **Knowledge base is massive and searchable.** 287,589 messages from 12 sources
   ingested into knowledge_messages. FTS5 (SQLite full-text) + ChromaDB (semantic
   vectors) provide dual search. `cis_search_knowledge` MCP tool available to all
   profiles. Session format approach replaced complex tagging pipeline — semantic
   search over Eric's own words is superior.

2. **Intent alignment pipeline is live.** `POST /api/intent/alignment` checks new
   proposals against all 287K messages for consistency. Drafter dispatcher runs
   `measure_intent.py` automatically. Reviewer prompt requires intent verification.
   Pipeline won't produce work that contradicts Eric's established intent.

3. **Human-readable adapter status.** `GET /api/adapter/status` spells out each
   gateway's state in plain English — what was tested, what the response means,
   and what to do if something's wrong. No JSON decoding. No dots. No checkboxes.
   Claude-ready summary included: "4 of 5 gateways running. 1 down."

4. **Tier 12 and 13 COMPLETE.** Knowledge base ingestion (12 sources, 36,846 new
   messages appended to existing 250K) and abstraction layer (Flask blueprint,
   5 endpoints, 17 MCP tools). Build plan: 29 nodes, 24 COMPLETE.

5. **Roadmap exists.** `docs/CIS_ROADMAP_PHASES_1_6.md` — 6 phases, 28 items,
   dependency-ordered. Phase 1 (Root + Config) is immediate next work.

**What's pending:** Prime gateway (8642) down. Gateway restarts needed to activate
MCP tools. Qwen bind needs changing from 127.0.0.1:8002 to 0.0.0.0:8002 for
container access. Per-profile SOUL.md not written.

---

## 10. Session Handoff for Claude — June 27, 2026

### What We Built This Session

Eric and I completed a major integration push. Here's what Claude needs to know
to pick up the conversation:

**Core deliverables:**
- `runtime/abstraction/dispatch.py` — 181-line profile map, health checks, gateway URLs
- `runtime/api/adapter.py` — Flask blueprint, 5 endpoints including human-readable status
- `runtime/api/intent.py` — intent alignment endpoint (`GET /api/intent/alignment`)
- `tools/pipeline/measure_intent.py` — CLI tool called by Drafter on dispatch
- `tools/pipeline/drafter_start.py` — +25 lines, calls measure_intent automatically
- `tools/pipeline/reviewer_reconcile.py` — +12 lines, REVIEW_SYSTEM mandates intent check
- `docs/CIS_ROADMAP_PHASES_1_6.md` — 6-phase roadmap from 287K knowledge base
- `docs/PHASE1_ROOT_DIRECTIVE_FOR_CLAUDE.md` — 5 root/sudo tasks with exact commands

**Knowledge base stats:**
- 287,589 messages from 12 sources
- FTS5 (SQLite) + ChromaDB (9.3GB) dual search
- `cis_search_knowledge` MCP tool configured on all profiles (needs gateway restart)
- Sources: archive (165K), cis_docs (76K), swa (23K), claude_export (9.5K), cis_kernel (4K), chatgpt_export (3.8K), pve_architecture (2.8K), wiasw (883), claude_transcripts (757), cis_legacy_archive (604), cis_v1_vault (353), others (226)

**Adapter endpoints (port 5000):**
- `GET /api/adapter/health` — JSON health checks
- `GET /api/adapter/status` — HUMAN-READABLE status (Eric's preference)
- `GET /api/adapter/profiles` — profile listing
- `POST /api/adapter/dispatch` — intent routing
- `POST /api/adapter/chat` — chat passthrough

**Gateway status:**
- v4pro (Drafter, 8645): UP
- r1 (Reviewer, 8643): UP
- v4impl (Implementer, 8646): UP
- qwen (8644): UP
- prime (8642): DOWN — needs `systemctl --user start hermes-gateway.service`

**Eric's key feedback this session:**
- "I don't want JSON. I want words." → Built human-readable status endpoint
- "Every result is spelled out" → New status explains what healthy means, what was tested, what to do
- "Commit and push this new work" → Committed 3478da1, pushed to master
- "Excellent work" → Session concluded with approval
- "Update the dev-pivot files" → All 17 DEV-PIVOT files now carry session context footers (182bcd8)
- HCP regenerated at HEAD 9c921e2 — captures all 4 session commits

**What Eric wants next (per roadmap Phase 1):**
1. Qwen bind fix (127.0.0.1:8002 → 0.0.0.0:8002) for container access
2. Complete MWL proof in container
3. Start prime gateway (8642)
4. Restart v4pro/r1/v4impl gateways to activate MCP tools
5. Write per-profile SOUL.md (Drafter, Reviewer, Implementer)

**Working context for Claude:**
- Working directory: `/mnt/projects/cis/`
- Branch: main (commit 9c921e2)
- Flask server: running on 127.0.0.1:5000
- ChromaDB: `/mnt/projects/cis/data/chroma_data/`
- Spine DB: `/mnt/projects/cis/data/cis_memory.db`
- MCP bridge: `/mnt/projects/cis/runtime/mcp_bridge/tools.py` (17 tools)
- Eric's Hermes config: `~/.hermes-v4pro/config.yaml` (MCP server config written, needs restart)
- Eric's words (verbatim intent): AGENTS.md §12, plus 287K messages in ChromaDB
- DEV-PIVOT files: all 17 carry session footers pointing to this handoff
- HCP: regenerated at HEAD, 12 artifacts in PROJECT_CONTEXT_PACK_UPLOAD/

**Eric's communication preferences:**
- Speaks in thoughts/intentions, not formal specs
- Needs bullet points, cannot read text walls
- Changes topics every 5-15 lines
- Everything spelled out in text — no dots, no icons, no JSON
- Budget ~$10-20; DeepSeek for bulk, Claude for coding
- Approve/disapprove/refine intention — not a builder
- Evidence-backed responses required — raw terminal output pasted, not summarized
