# CIS Final Build Direction — Hermes-Integrated Architecture

**Date:** 2026-06-17 | **Author:** R1 Reviewer | **Status:** PENDING ERIC APPROVAL

## 1. Target End State

CIS becomes a **Hermes add-on** — a specialized pipeline layer that registers CIS
methodology on Hermes primitives. One Hermes install, five profiles, per-profile
skills, MCP coordination, Hermes dashboard.

```
┌──────────────────────────────────────────────────────────┐
│                    HERMES DASHBOARD                       │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │CIS View │ │WIAS View │ │SWA View  │ │Build Monitor│ │
│  │(delib,  │ │(stages,  │ │(intake,  │ │(nodes,      │ │
│  │ gates,  │ │ projects,│ │ appts,   │ │ gates,      │ │
│  │ Eric    │ │ assets)  │ │ notes)   │ │ closeout)   │ │
│  │ Gate)   │ │          │ │          │ │             │ │
│  └─────────┘ └──────────┘ └──────────┘ └─────────────┘ │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────┐
│                    MCP COORDINATION LAYER                 │
│  Profiles expose pipeline state as MCP tools.            │
│  Orchestrator queries through MCP, not custom HTTP.      │
│  External advisors (ChatGPT, Claude) connect via MCP.    │
└──────────────────────────────────────────────────────────┘
                           │
     ┌─────────┬───────────┼───────────┬──────────┐
     │         │           │           │          │
┌────▼──┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│Prime  │ │Drafter │ │Reviewer│ │Implem- │ │Qwen    │
│Eric   │ │v4pro   │ │r1      │ │enter   │ │qwen3   │
│       │ │8645    │ │8643    │ │v4impl  │ │vl-30b  │
│       │ │        │ │        │ │8646    │ │8002    │
│       │ │        │ │        │ │        │ │        │
│SOUL:  │ │SOUL:   │ │SOUL:   │ │SOUL:   │ │SOUL:   │
│Eric   │ │Drafter │ │Reviewer│ │Builder │ │Auditor │
│Skills:│ │Skills: │ │Skills: │ │Skills: │ │Skills: │
│cis-   │ │spec-   │ │spec-   │ │tdd,    │ │spec-   │
│over-  │ │author, │ │review, │ │subagent│ │review  │
│view   │ │plan    │ │debug   │ │build   │ │(infer) │
└───────┘ └────────┘ └────────┘ └────────┘ └────────┘
                           │
┌──────────────────────────┴──────────────────────────────┐
│              CIS → HERMES ABSTRACTION LAYER               │
│  Maps CIS methodology to current Hermes features.        │
│  Isolates CIS from Hermes version changes.               │
│  When Hermes updates, only this layer changes.           │
└──────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────┐
│                   HERMES PLATFORM                         │
│  Profiles, Skills, Dashboard, Cron, Sub-agents,          │
│  MCP Client/Server, Messaging, Model Picker              │
└──────────────────────────────────────────────────────────┘
```

## 2. How the 16 Failure Modes Are Addressed

Every CIS guard-rail maps to a specific Hermes primitive in the target architecture.

### 2.1 Trust Failures → Profiles + Skills

| Failure | CIS Guard-Rail | Hermes Target |
|---------|---------------|---------------|
| Self-reported completion | Verification Hardening Rule | Reviewer profile auto-verifies implementer output via MCP query |
| Hallucinated claims | Evidence-Backed Response Rule | Skill enforces COMMAND/OUTPUT format; dashboard shows raw evidence |
| Rubber-stamp reviews | Dual-reviewer deliberation | Two profiles (R1 + Qwen) with different models, cross-feed objections via MCP |

### 2.2 Knowledge Failures → Dashboard + Cron

| Failure | CIS Guard-Rail | Hermes Target |
|---------|---------------|---------------|
| Training-data staleness | Staleness gate | Hermes `web_search` skill, cron-checked daily |
| Context amnesia | SQLite spine + AGENTS.md | Hermes state DB per profile + dashboard build monitor |
| Version drift | generate_agents_md.py from DB | Dashboard live view; AGENTS.md as cron-generated export snapshot |

### 2.3 Process Failures → Profiles + Skills + Cron

| Failure | CIS Guard-Rail | Hermes Target |
|---------|---------------|---------------|
| Scope creep | Approved File Manifest | Implementer profile has restricted toolset; Reviewer verifies manifest |
| Constraint bypass | NOT NULL FK enforcement | Spine schema with CHECK constraints; gate skills verify |
| Pipeline bypass | Gate sequence | Oversight SKILL hooks tool calls; no write without gate record |
| Role confusion | HERMES_HOME + gateway endpoint | Per-profile SOUL.md + toolset configuration; Hermes enforces |
| Silent gate failures | PASS/FAIL + COMMAND/OUTPUT | Gate skills produce structured output; dashboard shows gate history |
| Concurrency races | Atomic UPDATE...WHERE + rowcount | Hermes cron ensures single dispatch; sub-agents inherit isolation |

### 2.4 Protocol Failures → MCP + FINAL_JSON

| Failure | CIS Guard-Rail | Hermes Target |
|---------|---------------|---------------|
| Unstructured output | FINAL_JSON required | Skill enforces; MCP tool returns structured verdict |
| Missing FINAL_JSON | Repair prompt → fallback scan | Skill retry + escalation to Eric via messaging |
| Fake consensus | Cross-feed objections | MCP coordination: R1 response → Qwen review → compare → cross-feed if split |
| Single-model blind spots | Two reviewers, different models | Model picker: Reviewer=deepseek-v4-pro, Qwen=qwen3-vl-30b, External=Claude via MCP |

## 3. Domain Coverage

The three domains share one pipeline, one spine, one approval gate.

```
                       WorkIntent
                           │
                  Domain Classifier
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    CIS Domain         WIAS Domain       SWA Domain
    (adversarial       (creative         (case
     build pipeline)    production)       management)
         │                 │                 │
    ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
    │Drafter  │      │WIAS     │      │SWA      │
    │Reviewer │      │Adapter  │      │Adapter  │
    │Implem-  │      │         │      │         │
    │enter    │      │         │      │         │
    └────┬────┘      └────┬────┘      └────┬────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    Process Manager
                           │
                     Eric Gate
                           │
              ┌────────────┼────────────┐
              │            │            │
         CIS Action    WIAS Action  SWA Action
```

**CIS Domain:** Drafter authors specs, Reviewer verifies, Implementer builds. Eric approves.
This is live today — Tier 11D complete, 25/27 build nodes done.

**WIAS Domain:** Project intake → WIAS stage inference → tool/template surfacing →
production tracking → output → knowledge return. Multi-exit per stage. This is the
next domain to operationalize after CIS build completes.

**SWA Domain:** Validation use case only today (Tier 7R.3 SWAAdapter). CIS classifies
SWA intents but does not implement SWA features. Full SWA operationalization is
deferred — SWA is a separate project with its own development lifecycle.

**LIFE Domain:** Home/Body/Mind. Identified in the WIAS Project Manager spreadsheet.
No adapter, no implementation. Deferred until WIAS is operationalized.

## 4. Build Sequence

Eight phases, each with a defined Hermes primitive as the target.

| Phase | What | Hermes Primitive | Prerequisite |
|-------|------|-----------------|-------------|
| **P0** | Fix BLK-SEED-005 (r1 service loop) | systemd unit stability | None |
| **P1** | Collapse 5 installs → 1 install, 5 profiles | **Profiles system** | P0 |
| **P2** | Define per-profile SOUL.md + skill bundles | **Skills marketplace** | P1 |
| **P3** | CIS ↔ Hermes abstraction layer | **MCP client/server** | P1 |
| **P4** | Oversight skill (tool-call hooks) | **Skills enforcement** | P2, P3 |
| **P5** | Gate migration (bash → skills) | **Skills marketplace** | P4 |
| **P6** | UI overhaul — dashboard views | **Web dashboard** | P3 |
| **P7** | External advisor integration | **MCP client** | P3 |
| **P8** | WIAS domain adapter operational | **Profiles + MCP** | P5 |
| **P9** | SWA domain adapter operational | **Profiles + MCP** | P8 |

### Phase Detail

**P0 — BLK-SEED-005:** hermes-gateway-r1.service in fail-restart loop. Port 8643
held by manual `--replace` process. Fix: stop manual process, verify systemd binds
cleanly, test reboot. < 1 hour.

**P1 — Profiles:** `hermes profile create drafter`, `hermes profile create reviewer`,
etc. Migrate config.yaml, .env, SOUL.md from current installs. Verify each profile's
gateway starts on its port. ~2-4 hours.

**P2 — SOUL.md + Skills:** Each profile gets a role-specific SOUL.md (Drafter: "You
author specifications. You do not implement. You do not review."). Each profile
auto-loads its role skills from the marketplace. ~2-4 hours.

**P3 — Abstraction Layer:** MCP tools per profile: `review_proposal`, `draft_spec`,
`implement_directive`, `closeout_tier`. Orchestrator queries via MCP instead of
direct HTTP. External advisors (ChatGPT, Claude) connect via MCP. ~4-8 hours.

**P4 — Oversight Skill:** Loaded automatically when working in CIS project directory.
Hooks: before `write_file`/`patch` → check for deliberation record. Before `sqlite3 INSERT` →
check for migration approval. Before `git commit` → verify gate sequence passed. ~4-8 hours.

**P5 — Gate Migration:** 37 bash gates → Hermes skills. Keep bash as audit trail.
Skills encode the logic; bash verifies deterministically. ~4-8 hours.

**P6 — UI Overhaul:** Dashboard views: build plan monitor (nodes, gates, closeout),
deliberation viewer (R1 vs Qwen side-by-side), Eric Gate panel (approve/revise/kill),
staleness feed, profile manager. Prefer dashboard extensions over custom React. ~8-16 hours.

**P7 — External Advisors:** Register ChatGPT and Claude as MCP tools. Remove custom
`call_openai()`/`call_anthropic()` from reconcile.py. External escalation fires via
MCP when local reviewers deadlock. ~2-4 hours.

**P8 — WIAS Operational:** WIAS adapter classifies creative intents, infers WIAS stage,
surfaces stage-appropriate tools/templates. Projects tracked through stages. ~8-16 hours.

**P9 — SWA Operational:** SWA adapter for case management intents. Client intake,
appointment tracking, note generation. Full SWA pipeline but SWA features remain
in the SWA project. ~8-16 hours.

## 5. What Stays CIS, What Moves to Hermes

| Stays CIS (Methodology) | Moves to Hermes (Implementation) |
|------------------------|----------------------------------|
| Adversarial verification (ADR-SEED-002) | 5 installs → profiles |
| FINAL_JSON protocol | orchestrator HTTP → MCP coordination |
| Eric Gate (human approval) | gate scripts → skills |
| Evidence-Backed Response Rule | closeout scripts → cron jobs |
| Build plan spine (DB) | custom Flask UI → dashboard views |
| Dual-model deliberation | staleness script → web_search skill |
| Role enforcement (ADR-SEED-003/004) | Eric Gate delivery → messaging |
| Domain classification (CIS/WIAS/SWA) | external advisors → MCP tools |

## 6. What Does NOT Change

- **CIS is still CIS.** Adversarial review, evidence-backed responses, Eric Gate,
  FINAL_JSON — these are the methodology. They don't change when the implementation
  moves to Hermes primitives.
- **The spine is still authoritative.** `cis_memory.db` remains the source of truth.
  Profiles query it via MCP; it does not become per-profile state.
- **Eric always approves.** No auto-execute. The Eric Gate is human-in-the-loop,
  now delivered through Hermes messaging to any platform.
- **Hermes does not absorb CIS.** CIS registers on Hermes, not inside it. The
  abstraction layer ensures CIS methodology survives Hermes version updates.

## 7. First Action

The oversight SKILL (P4) should NOT be built first — it needs profiles (P1),
SOUL.md (P2), and MCP (P3) as prerequisites. The correct first action is:

**P0 → P1 → P2 → P3 → then P4.**

Start with BLK-SEED-005. Any reboot without fixing it means the Reviewer is down
and the pipeline cannot function.

## 8. Approval Conditions

Eric must explicitly approve this direction before any implementation begins.
This document defines the target architecture for the next major push.
Once approved, implementation proceeds P0 → P1 → P2...

```
Decision: APPROVE / REVISE / BLOCK
```
