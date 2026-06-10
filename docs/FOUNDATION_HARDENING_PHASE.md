# Foundation Hardening Phase
## Status: DESIGN — awaiting Component 1 draft from Claude
## Established: 2026-06-09 session
## Authority: Eric (approved scope and build order)
## External audit: Claude + ChatGPT both approved

---

## Purpose

The Foundation Hardening Phase sits between the current Kanban-retired state
and Tier 8 (MCP Bridge / shared memory). Its purpose is to bring every tier
from 0 through 7 to production-ready status before the knowledge base and
model integration layer is built on top of it.

The Kanban situation — temporary scaffolding that became load-bearing because
no retirement trigger was defined and no model flagged the gap — is the
primary motivation. The system needs governance infrastructure that prevents
this pattern from recurring.

---

## Core Principle

Eric's role is: veto power, goal alignment sensor, final approver. Not a
technical reviewer. The system must surface decisions in plain language with
full provenance — how the choice moves the project toward the defined goal,
the full path that produced it, and what was considered and rejected. This
is what would have surfaced the Kanban situation days earlier.

---

## Five Components

### Component 1 — Provenance and Lifecycle Base Schema
**Status: NOT STARTED — first design task next session**
**Depends on: nothing (foundation)**

New spine tables for:
- Goal references: how each action connects to defined project goals
- Decision trails: condensed path from problem → research → draft → review →
  external audit → proposed action
- Drift indicators: flags for temporary dependencies with no retirement
  trigger, actions diverging from dependency graph, dismissed objections
- Rejection rationale: what was considered and why it was not chosen

This schema is the foundation for Components 2, 3, and 4.
Claude drafts. ChatGPT audits. Eric approves. Then v4impl implements.

---

### Component 2 — Escalation Advisor Integration Protocol
**Status: NOT STARTED**
**Depends on: Component 1**

Defines the boundary between Hermes operational layer and Claude/ChatGPT
escalation advisor layer.

- Trigger conditions: when does the system escalate vs handle internally
- Escalation packet format: what context, spine state, and question goes
  to the advisor
- Response ingestion contract: how advisor responses are written back to
  the spine
- Current path: copy-paste to subscription account
- Future path: API integration (Tier 8)

Claude and ChatGPT are escalation advisors. They have no execution authority.
They receive structured packets and return structured audit responses.
The router constructs the packet. Eric transmits it (now by copy-paste,
later by API).

---

### Component 3 — Eric Gate Redesign
**Status: NOT STARTED**
**Depends on: Component 1 (provenance schema), Component 2 (escalation protocol)**

Current state: `eric_approved_at` timestamp column — placeholder only.
No setter. No briefing. Gate correctly fails until setter is built.

Target state: Provenance-gated approval checkpoint with four elements:
1. Action summary — one paragraph, plain language, what will change,
   whether reversible
2. Goal trace — how this action connects to defined project goal,
   which dependency graph node it closes, which tier it advances
3. Decision trail — condensed path from problem through deliberation
   to this proposal, key objections raised and how resolved
4. Drift indicators — automatic flags if: temporary dependency with no
   retirement trigger, action diverges from dependency graph, objection
   dismissed without resolution, component patched more than once without
   root cause fix

Eric sees this briefing before every approval. He either releases or vetoes.
His decision is recorded in the spine with timestamp and goal reference.

---

### Component 4 — Router Expansion
**Status: NOT STARTED**
**Depends on: Components 1, 2, 3**

Current state: 8-pass classifier, routes prompts to Hermes profiles.

Target state: Session orchestration layer.

New capabilities:
- Session start: freshness check, context load, surface last closeout
  status, present Eric with current project position in plain language
- Operator command classification: new route class OPERATOR_COMMAND.
  Deterministic system actions that bypass deliberation. Closeout is
  the first. No model reasoning at runtime.
  route_type = OPERATOR_COMMAND
  execution_mode = deterministic
  agent = none
  requires_deliberation = false
  requires_eric_gate = false
  writes_spine = true
- Escalation detection and packaging: construct structured escalation
  packet on failure or drift. Route to correct escalation path.
- Drift detection: query provenance schema before Eric Gate approval.
  Surface drift indicators in plain language.
- Closeout routing: chat phrases like "closeout", "end session",
  "wrap this up" route to OPERATOR_COMMAND → tools/closeout.sh.
  Same script as hermes closeout. One source of truth.

---

### Component 5 — Tier Retrofit Assessment
**Status: NOT STARTED**
**Depends on: Components 1, 2, 3, 4 (uses full system)**

Audit tiers 0 through 7 for production-readiness gaps.

For each tier, answer:
- What was the minimum viable completion criterion?
- What does production-ready actually require?
- Is there any temporary scaffolding with no defined retirement trigger?
- Has any component been patched more than once without root cause fix?
- Does the tier's gate suite fully verify its completion claim?

Output: concrete remediation list structured as a dependency graph,
fed into approved build order before Tier 8 begins.

---

## Build Order Within Foundation Hardening
Component 1 — Provenance + lifecycle base schema
→ Component 2 — Escalation advisor integration protocol
→ Component 3 — Eric Gate redesign
→ Component 4 — Router expansion
→ Component 5 — Tier retrofit assessment

ChatGPT audit confirmed this order. Escalation protocol must precede
Eric Gate redesign because the gate needs to know what happens when
Eric does not approve or escalates.

---

## Design Protocol for Each Component

1. Claude drafts the design document
2. ChatGPT audits independently
3. Eric reconciles and approves
4. v4impl implements only after Eric approval
5. Deterministic gates verify before spine record is written

No component implementation begins without completing steps 1-3.

---

## Entry Criterion
Kanban retirement repair complete. ✅ Completed 2026-06-09. HEAD: b8f7619.

## Exit Criterion
All five components implemented, gated, and verified. Tier retrofit
assessment complete. Dependency graph updated. Eric approves Foundation
Hardening Phase as complete before Tier 8 design begins.
