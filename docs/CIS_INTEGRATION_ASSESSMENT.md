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

## 7. Migration Phases (Recommended Order)

| Phase | What | Prerequisite |
|-------|------|-------------|
| **P0** | Resolve BLK-SEED-005 (hermes-gateway-r1 service loop) | None — any reboot risks Reviewer down |
| **P1** | Evaluate profiles: can 5 installs → 1 install with 5 profiles? | OQ-SEED-007 |
| **P2** | Define CIS skill bundle per role (section 6.3) | P1 |
| **P3** | Build abstraction layer — adapter that maps CIS needs to Hermes features | P1 |
| **P4** | Build oversight skill with tool-call hooks (section 6.4) | P2, P3 |
| **P5** | Migrate gates from bash to skills where sensible | P4 |
| **P6** | UI overhaul — Hermes dashboard or MCP views | P3 |
| **P7** | External advisor integration via MCP (replace custom HTTP in reconcile.py) | P3 |
| **P8** | Closeout triggers via Hermes cron | P3 |

---

## 8. Summary

**CIS prevents 16 specific failure modes** across 4 categories (trust, knowledge, process, protocol). Seven of these are unique to CIS and have no Hermes equivalent. Nine are partially or fully duplicated by Hermes v0.16.0 features.

**The integration strategy:** CIS keeps its methodology (adversarial review, evidence-backed responses, Eric Gate, FINAL_JSON). The implementation layer adapts to use Hermes primitives instead of custom code. An abstraction layer isolates CIS from Hermes version changes.

**The oversight skill should wait** until the install question, source-patch dependency, and role-skill mapping are resolved. Building it now on the current architecture would create rework when profiles are adopted.
