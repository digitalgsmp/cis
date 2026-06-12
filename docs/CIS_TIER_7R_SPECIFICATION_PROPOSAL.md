# Tier 7R — Intent-to-Workflow Architecture Specification
## Proposal Document v1.0

## Eric Gate Status: APPROVED_AS_ARCHITECTURE_BASIS

This document defines the architectural direction for Tier 7R. It is **NOT** an
implementation directive. No code shall be written, no spine rows modified, and no
files staged under this document alone. Implementation proceeds one build_plan_node
at a time (7R.1 → 7R.2 → ...). Each node requires its own Eric Gate approval.

**Author:** Hermes V4 Implementer (deepseek-v4-pro)
**Date:** 2026-06-12 | **Revised:** 2026-06-12 (Eric Gate revision)
**Status:** APPROVED_AS_ARCHITECTURE_BASIS — phased build nodes pending
**Replaces:** Tier 7 — Full Durable Router Pipeline (DEFERRED)
**External Review:** ChatGPT (deepseek-v4-pro) — consensus confirmed
**Eric Gate Review:** APPROVE_WITH_REVISIONS → revisions applied below

---

## 1. Problem Statement

### 1.1 What exists now

Tier 7 is defined in the Dependency Graph Build Plan v2.0 as "Router Reclassification" with a single artifact:

> 7.1 — Router Kanban integration: classify_route() creates Kanban card, returns card ID. UI shows pipeline progress instead of chat response.

This was always marked as a placeholder: "Do not design implementation until Tier 6 is verified stable."

Tier 7.1 (Router Reclassification — archive route) was completed. It classifies whether a prompt contains archive discovery intent and routes it. Tier 7.5a (Corpus Audit) and Tier 7.5b (Clean Subset Import + FTS5) were completed as supporting work.

Tier 7 itself was marked DEFERRED with note: "Intentionally held pending Eric decision. Full reclassification must be spine-native; Kanban remains retired as pipeline transport per ADR-013."

### 1.2 Why a simple router is insufficient

The CIS Dependency Graph Build Plan's original vision of Tier 7 was narrow: classify a prompt, create a Kanban card, dispatch to an agent. This treats all work as the same shape: prompt-in, agent-out.

But the CIS Plain Language Build Roadmap and the SWA workflow documents reveal that CIS will handle structurally different kinds of work:

| Input | What it actually is | What a simple router would do |
|-------|-------------------|-------------------------------|
| "What did I say about the social worker app?" | Archive discovery — retrieve from session archives | Route to Research agent |
| "Use this SWA document to decide what the app needs" | Requirements recovery — extract candidate requirements from a document | Route to Drafter |
| "Implement Phase 45" | Potentially implementation — but only after approval and build-plan staging | Route to Implementer (dangerous) |
| "Process this PDF into knowledge" | Knowledge intake — run multi-pass extraction pipeline | Route to Drafter (wrong pipeline) |
| "Schedule intake for new client" | SWA domain workflow event — create client, schedule appointment | No handler exists |
| "Start Micro1 task planning" | Out of scope — accidental context contamination | Create card (wrong) |

A simple router conflates:
- Archive retrieval with requirements work
- Requirements work with implementation directives
- Domain-specific workflow with generic agent chat
- In-scope work with out-of-scope contamination

### 1.3 What the research says

Enterprise Integration Patterns (Hohpe & Woolf, 2003), Domain-Driven Design (Evans, 2003), and modern workflow engines (Temporal, Camunda, AWS Step Functions) all converge on the same architectural principle:

**A single router is the wrong abstraction for multi-domain workflow classification.**

The established pattern is a composite architecture:
- Content-Based Router for initial domain classification
- Domain Adapters (bounded contexts with anti-corruption layers) for domain-specific rules
- Process Manager (state machine) for workflow state tracking and legal transition enforcement
- Canonical Data Model for inter-domain communication
- Human Approval Gates as first-class architectural components
- Dead Letter Channel for unprocessable/out-of-scope inputs

### 1.4 Evidence from the two use-case documents

**SWA Analysis of Current Workflow** describes a real application workflow:
- Email arrives for new client → create client → schedule intake → document appointment → log action → generate D.A.P. note → access client hub
- The app needs to distinguish: pre-treatment-plan documentation, general service actions, structured goal actions, unlinked appointments, and note generation
- These are workflow states, not routing targets

**CIS Plain Language Build Roadmap** describes a structurally similar pipeline:
- Raw file → system reads it → system describes it → human reviews it → approved summary becomes permanent knowledge record
- Later stages add: project objects, WIAS stage routing, project attachment, stage-aware surfacing of tools/templates/knowledge
- These are state transitions, not agent assignments

The common structure is: incoming thing → classify what it is → attach to right domain/project → create or update durable object → move through allowed workflow → require human review at trust changes → make retrievable/actionable.

---

## 2. Preferred Architecture

### 2.1 Composite pattern

```
Incoming prompt / file / archive hit / workflow event
                    │
          ┌─────────▼──────────┐
          │  Normalizer         │  (Canonical Data Model)
          │  → WorkIntent       │  Convert any input to standard form
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  Domain Classifier  │  (Content-Based Router)
          │  CIS / SWA / WIAS   │  What domain does this belong to?
          │  / OUT_OF_SCOPE     │
          └─────────┬──────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼─────┐  ┌────▼─────┐  ┌─────▼────┐
│CIS       │  │SWA       │  │WIAS      │  (Domain Adapters
│Adapter   │  │Adapter   │  │Adapter   │   Bounded Contexts
│          │  │          │  │          │   Anti-Corruption Layer)
└────┬─────┘  └────┬─────┘  └─────┬────┘
     │              │              │
     │    ┌─────────▼──────────┐   │
     │    │ Object Classifier  │   │  Which objects are affected?
     │    │ Intent Classifier  │   │  What kind of work is this?
     │    │ State Validator    │   │  What state transitions are legal?
     │    └─────────┬──────────┘   │
     │              │              │
     └──────────────┼──────────────┘
                    │
          ┌─────────▼──────────┐
          │  Process Manager    │  (State Machine)
          │  Stage candidate /  │  Owns workflow lifecycle
          │  Request approval / │  Enforces legal transitions
          │  Dispatch / Block   │
          └─────────┬──────────┘
                    │
     ┌──────────────┼──────────────┐
     │              │              │
┌────▼─────┐  ┌────▼─────┐  ┌─────▼────┐
│Stage     │  │Human     │  │Dispatch  │
│Candidate │  │Approval  │  │Action    │
│(build_   │  │Gate      │  │(Drafter/ │
│plan_node)│  │(Eric)    │  │Impl/     │
└──────────┘  └──────────┘  │Research) │
                            └──────────┘

          ┌──────────────────────┐
          │  Dead Letter Channel │  Out of scope
          │  Invalid Message     │  Blocked capability
          │  Channel             │  Unrecognized domain
          └──────────────────────┘
```

### 2.2 Key architectural decisions

| Decision | Rationale | Source Pattern |
|----------|-----------|----------------|
| Canonical WorkIntent as central object | Prevents N*(N-1) translators between domain formats | Canonical Data Model (Hohpe/Woolf) |
| Domain Adapters, not monolithic router | New domains require new adapters, not router rewrites | Hexagonal/Ports & Adapters (Cockburn), Bounded Context (Evans) |
| Process Manager owns workflow state | State transitions are legal/illegal, not routing suggestions | Process Manager (Hohpe/Woolf), State Machine (AWS Step Functions) |
| Human approval gate before any mutation | CIS roadmap: "approved summary becomes permanent knowledge record" | Human Task (BPMN), Eric Gate (ADR-SEED-002) |
| Dead Letter Channel for out-of-scope | Unrecognized domains must not silently create work | Invalid Message Channel (Hohpe/Woolf) |
| All state in SQLite spine | Component 3.5 made build_plan_nodes authoritative; ADR-013 retired Kanban | Shared Database pattern, build_plan_nodes table |

### 2.3 What Tier 7R is not

- Not a new application or service
- Not a replacement for the existing /api/advisor/route endpoint
- Not a UI
- Not an agent
- Not a model selection system (that's the legacy Intelligence Router from Phase 1)

Tier 7R is a specification and a lightweight Python classification layer that reads from the SQLite spine and produces staged, reviewable WorkIntent objects and build_plan_nodes.

---

## 3. Scope Boundary

### 3.1 In scope

| Domain | Role | Evidence |
|--------|------|----------|
| CIS infrastructure / archive / knowledge workflow | Primary domain. Classify archive discovery, knowledge intake, requirements recovery, build-plan actions | CIS Plain Language Build Roadmap, CIS Canonical Build Sequence |
| SWA case-management workflow | Validation use case. Prove the architecture handles domain-specific objects and workflow states without building the SWA app | SWA Analysis of Current Workflow, SWA Technical Overview |
| WIAS/creative knowledge workflow | Present in CIS roadmap (Phases 3-5). Outline adapter rules. Not fully implemented | CIS Canonical Build Sequence §Phase 3-4 |

### 3.2 Explicitly out of scope

| Item | Reason |
|------|--------|
| Micro1 | Accidental context contamination. Belongs to another person. Must be removed from routing examples, test cases, HCP language, project taxonomy, and any scope registry entries. |
| Implementation of SWA app features | SWA is a validation use case, not a build target. Tier 7R must not modify files under `/mnt/projects/swa/`. |
| Tier 8 MCP Bridge | Gated on Tier 7R.4 (Process Manager) per revised dependency graph — see §11 |
| Tier 9 Chroma/VDB | Gated on Tier 8 |
| Tier 10 CIS UI/custom display views | Gated on Tier 9 |
| Discord/Telegram gateway | Listed in Do Not Start (AGENTS.md §2) |
| Schedule field-use work (SWA) | Listed in Do Not Start (AGENTS.md §2) |

---

## 4. Canonical WorkIntent Schema

### 4.1 Purpose

WorkIntent is the canonical interchange object. Every domain adapter receives and emits WorkIntent objects. The Process Manager operates on WorkIntent. This prevents domain-specific schemas from leaking across bounded contexts.

### 4.2 Draft schema

```
WorkIntent:
  id:                  TEXT        -- UUID, assigned at creation
  domain:              TEXT        -- CIS | SWA | WIAS | OUT_OF_SCOPE
  intent_class:        TEXT        -- ARCHIVE_DISCOVERY |
                                     REQUIREMENTS_RECOVERY |
                                     KNOWLEDGE_INTAKE |
                                     KNOWLEDGE_RETRIEVAL |
                                     PROJECT_WORKFLOW_ACTION |
                                     DOMAIN_WORKFLOW_EVENT |
                                     AGENT_ADVISORY |
                                     IMPLEMENTATION_DIRECTIVE |
                                     BLOCKED_MISSING_CAPABILITY
  object_type:         TEXT        -- source_manifest | knowledge_record | project |
                                     build_plan_node | workflow_run |
                                     client | appointment | need | goal | action_step |
                                     provider | progress_note | (etc.)
  object_refs:         TEXT[]      -- Array of specific object identifiers
  workflow_state:      TEXT        -- Current state of the primary object
                                     (domain-specific: pre_plan | intake | draft |
                                     approved | linked | unlinked | etc.)
  allowed_action:      TEXT        -- retrieve | stage_candidate |
                                     request_approval | dispatch | block
  evidence_refs:       TEXT[]      -- Source documents, session IDs, file paths,
                                     database rows supporting the intent
  requires_eric_gate:  BOOLEAN     -- true if this intent requires Eric approval
                                     before any mutation
  target_project_id:   TEXT        -- Project this intent belongs to (from
                                     build_plan_nodes or project registry)
  source_raw:          TEXT        -- Original user prompt or triggering event text
  source_type:         TEXT        -- prompt | file_upload | archive_hit |
                                     system_event | document_reference
  created_at:          TEXT        -- ISO 8601 timestamp
  status:              TEXT        -- CLASSIFIED | STAGED | APPROVED | REJECTED |
                                     DISPATCHED | BLOCKED | COMPLETE
```

### 4.3 Intent class definitions

| Intent Class | Meaning | Example |
|-------------|---------|---------|
| ARCHIVE_DISCOVERY | Find what Eric previously said across session archives | "What did I say about the social worker app?" |
| REQUIREMENTS_RECOVERY | Turn archive/session/document material into candidate requirements | "Use this SWA document to identify what the app needs" |
| KNOWLEDGE_INTAKE | Bring a file/source into the CIS knowledge pipeline | "Process this PDF into a knowledge record" |
| KNOWLEDGE_RETRIEVAL | Search approved records or indexed material | "Find everything about cloth simulation in Houdini" |
| PROJECT_WORKFLOW_ACTION | Move or inspect a project/workflow object | "Show status of project X" |
| DOMAIN_WORKFLOW_EVENT | Domain-specific workflow action (e.g., SWA client intake) | "Schedule intake for new client" |
| AGENT_ADVISORY | Ask Librarian/Researcher/Teacher/Drafter/Reviewer for proposal-only output | "What techniques exist for volumetric fog?" |
| IMPLEMENTATION_DIRECTIVE | Only after Eric approval; routes to Implementer | "Implement Phase 45" (requires Eric Gate) |
| BLOCKED_MISSING_CAPABILITY | Required index, object, adapter, or gate does not exist | "Start Micro1 task planning" (out of scope) |

### 4.4 SWA-specific workflow states (validation use case)

From the SWA Technical Overview, the CMAMP app has workflow states that don't fit a rigid Domain→Need→Goal→ActionStep hierarchy:

| Workflow State | Meaning | Source Evidence |
|---------------|---------|-----------------|
| PRE_PLAN | Work before formal needs/goals exist (first 30 days) | "Phase 1: Pre-Treatment Plan" |
| INTAKE | Client created, initial appointment scheduled | "on-the-fly client creation" |
| NEED_IDENTIFIED | Needs exist but no goals defined yet | "Log General Activity on a need" |
| GOAL_DEFINED | Formal goals exist, action steps linked to goals | "structured goal-oriented tasks" |
| APPOINTMENT_LINKED | Appointment linked to client/need/goal | "linked to client, need, or goal" |
| APPOINTMENT_UNLINKED | Appointment linked only to client (no need/goal) | "General Client Activity / No Specific Need" |
| ACTION_LOGGED | Billable action step recorded | "Log Completed Action" |
| NOTE_GENERATED | D.A.P. progress note generated | "Generate Progress Note" |
| APPROVED | Human review complete | "review and promotion pipeline" |

---

## 5. Domain Adapter Contract

### 5.1 Interface contract (prose specification)

Every domain adapter must satisfy the following contract. (The Python pseudocode that
was here has been moved to Appendix C: Implementation Notes — it is deferred until the
individual adapter build_plan_nodes are approved.)

**Required capabilities:**

1. **Classify intent** — Given a canonical WorkIntent with source_raw and source_type
   populated, the adapter must populate intent_class, object_type, and object_refs
   based on domain-specific rules.

2. **Validate state** — The adapter must query the spine for current object state and
   populate workflow_state. It must determine allowed_action based on the state
   transition rules in §6.

3. **Resolve objects** — The adapter must verify that referenced objects exist in the
   spine (or don't exist, for creation intents). Unresolvable references produce a
   blocked WorkIntent.

4. **Stage candidates** — The adapter must generate candidate WorkIntents for Eric
   review. It must NEVER mutate the spine directly. All candidates are proposals
   until Eric Gate approval.

**Contracted prohibitions** — see §5.2 below.

### 5.2 What adapters must NOT do

- Must not mutate the spine directly (no INSERT/UPDATE/DELETE)
- Must not dispatch to Implementer without Eric Gate approval
- Must not create build_plan_nodes without staging for review
- Must not leak domain-specific objects into the canonical WorkIntent schema
- Must not handle intents from other domains

### 5.3 CISAdapter rules

| Rule | Description |
|------|-------------|
| C1 | KNOWLEDGE_INTAKE with file evidence → classify object_type=source_manifest, allowed_action=stage_candidate |
| C2 | ARCHIVE_DISCOVERY → classify intent_class=ARCHIVE_DISCOVERY, allowed_action=retrieve (no mutation) |
| C3 | REQUIREMENTS_RECOVERY from docs → classify, extract candidate requirements, stage as build_plan_nodes with status=PROPOSED |
| C4 | IMPLEMENTATION_DIRECTIVE → requires_eric_gate=true, allowed_action=request_approval |
| C5 | Unrecognized within CIS domain → allowed_action=block, status=BLOCKED |
| C6 | KNOWLEDGE_RETRIEVAL → allowed_action=retrieve, routes to Research agent |

### 5.4 SWAAdapter — validation use case only (do not implement SWA features)

**IMPORTANT:** SWA (Social Work Application) is a validation use case for the Tier 7R
architecture. The SWAAdapter classifies SWA-domain intents and stages candidate
build_plan_nodes. It does **NOT** implement SWA application features. It does **NOT**
modify the SWA codebase at `/mnt/projects/swa/`. It does **NOT** connect to the SWA
application runtime. SWA exists only to prove the Tier 7R architecture handles
domain-specific objects (client, appointment, need, goal, action_step, D.A.P. note)
and workflow states (PRE_PLAN, APPOINTMENT_UNLINKED, NOTE_GENERATION) correctly.

The Do Not Start list (AGENTS.md §2) explicitly blocks "Schedule field-use work (SWA)."
Tier 7R's SWAAdapter does not perform field-use work. It classifies and stages.
Implementation of SWA features is the responsibility of the SWA project, not CIS.

| Rule | Description |
|------|-------------|
| S1 | DOMAIN_WORKFLOW_EVENT with objects client+appointment → check if client exists in SWA spine |
| S2 | PRE_PLAN workflow state → allowed_action=stage_candidate, requires_eric_gate=false (documentation only) |
| S3 | APPOINTMENT_UNLINKED → classify as valid workflow state (no need/goal required) |
| S4 | NOTE_GENERATION → classify, check prerequisites met, stage for review, never auto-generate |
| S5 | DOMAIN_MODEL_CHANGE request → classify as REQUIREMENTS_RECOVERY, stage candidate build_plan_nodes |
| S6 | SWA adapter never implements SWA app features — it only classifies and stages |

### 5.5 WIASAdapter outline

| Rule | Description |
|------|-------------|
| W1 | PROJECT_WORKFLOW_ACTION → classify project object, current WIAS stage |
| W2 | Stage transitions (Word→Image, etc.) → allowed_action=stage_candidate, requires_eric_gate=true |
| W3 | KNOWLEDGE_RETRIEVAL for creative context → allowed_action=retrieve |

---

## 6. Workflow State Rules

### 6.1 State machine principle

Every object in the CIS system has a declared state. Every state has allowed transitions. The Process Manager enforces these transitions. An action is only allowed if the current object state permits it.

### 6.2 CIS object state machines

From the CIS Canonical Build Sequence §Phase 0-2:

**Source manifest:**
```
arrived → classified → preprocessed → extracted
  → normalized → draft → reviewed → approved / rejected
```

**Knowledge record:**
```
draft → checked → approved → locked (or deprecated)
```

**Project:**
```
initiated → active → paused → archived
```

**Build plan node:**
```
PROPOSED → PENDING → IN_PROGRESS → COMPLETE
                                    → BLOCKED
                                    → DEFERRED
```

### 6.3 Allowed action determination

| Current State | Allowed Actions | Requires Eric Gate |
|---------------|-----------------|-------------------|
| Object does not exist | stage_candidate (create proposal) | No |
| Object exists, state=draft | retrieve, stage_candidate (update proposal) | No |
| Object exists, state=approved | retrieve, request_approval (for mutation) | Yes |
| Object exists, state=locked | retrieve only | N/A (no mutation allowed) |
| Object in invalid transition | block | N/A |
| Domain not recognized | block (Dead Letter) | N/A |
| Intent = IMPLEMENTATION_DIRECTIVE | request_approval | Yes — always |
| Intent = ARCHIVE_DISCOVERY | retrieve | No |
| Intent = KNOWLEDGE_RETRIEVAL | retrieve | No |

### 6.4 SWA-specific state rules (validation)

| State | Allowed Actions |
|-------|----------------|
| Client does not exist, PRE_PLAN | stage_candidate (create client + schedule intake) |
| Client exists, no needs | stage_candidate (create needs), log general service action |
| Client exists, needs exist, no goals | stage_candidate (create goals), log action linked to need |
| Client exists, goals defined | stage_candidate (create linked action step), generate note |
| Appointment UNLINKED | permitted — no forced need/goal hierarchy |

---

## 7. Human Approval Rules

### 7.1 Principle

From the CIS Canonical Build Sequence (§Constitutional Constraints):
> "Every promotion gate requires human approval; AI proposes only."
> "Intelligence generates draft records only; promotion to approved/locked requires human review."

### 7.2 When Eric Gate is required

| Trigger | Gate Required | Rationale |
|---------|---------------|-----------|
| Create new build_plan_node | Yes | ADR-SEED-002: implementer self-report is not truth |
| Change build_plan_node status to IN_PROGRESS | Yes | Work begins only after Eric approves |
| Dispatch IMPLEMENTATION_DIRECTIVE | Yes | ADR-SEED-004: implementation routes only to v4impl, only after approval |
| Mutate approved/locked knowledge record | Yes | Constitutional constraint: draft-only promotion |
| Change project state | Yes | Workflow transitions require human oversight |
| Stage candidate requirement | No | Candidates are proposals — Eric reviews, doesn't pre-approve |
| Retrieve archive/search results | No | Read-only operations |
| Log domain workflow event (pre-plan) | No | Documentation of existing work, not system mutation |
| Classify and stage for review | No | Classification is proposal, not action |

### 7.3 Gate mechanism

Eric Gate uses the existing Eric Gate infrastructure from Component 3 (designed, not yet built):
- Candidate WorkIntents staged with status=STAGED
- Eric reviews via `tools/eric_gate/show_status.py`
- Eric approves via `tools/eric_gate/record_decision.py`
- Approved candidates become build_plan_nodes or workflow_runs
- Rejected candidates status=REJECTED with reason

### 7.4 Emergency override

Eric may issue a FINAL_DIRECTIVE that bypasses classification entirely. This is the existing workflow — Hermes receives FINAL_DIRECTIVE, prints HERMES_HOME, executes. The Tier 7R layer does not intercept FINAL_DIRECTIVE.

---

## 8. Acceptance Tests

### 8.1 Test: SWA Phase 45 — Flexible Documentation Workflow

**Input:** SWA Technical Overview document (PDF or markdown)

**Expected classification:**
```
domain: SWA
intent_class: REQUIREMENTS_RECOVERY
object_type: [action_step, client_need, goal, appointment, progress_note]
workflow_state: PRE_PLAN (flexible documentation needed before formal treatment plan)
allowed_action: stage_candidate
requires_eric_gate: false (candidates only, not implementation)
```

**Expected staged candidates:**
1. Candidate build_plan_node: "SWA — Make goal_id optional in action_steps table"
2. Candidate build_plan_node: "SWA — Add client_need_id column to action_steps"
3. Candidate build_plan_node: "SWA — Update appointment scheduling to allow unlinked appointments"
4. Candidate build_plan_node: "SWA — Add General Service action step type"

**Verification:** No code changed. No database mutated. Candidates exist in spine with status=PROPOSED.

### 8.2 Test: SWA Unlinked Appointment

**Input:** "Schedule a crisis call with client — no formal goal exists yet"

**Expected classification:**
```
domain: SWA
intent_class: DOMAIN_WORKFLOW_EVENT
object_type: [client, appointment]
workflow_state: APPOINTMENT_UNLINKED
allowed_action: stage_candidate
requires_eric_gate: false
```

**Verification:** System recognizes APPOINTMENT_UNLINKED as valid. Does not force creation of placeholder need/goal.

### 8.3 Test: CIS File-to-Knowledge Pipeline

**Input:** "Process this PDF into a knowledge record" (with file path evidence)

**Expected classification:**
```
domain: CIS
intent_class: KNOWLEDGE_INTAKE
object_type: [source_manifest, knowledge_record]
workflow_state: arrived (source not yet in system)
allowed_action: stage_candidate
requires_eric_gate: false
```

**Expected staged candidates:**
1. Candidate source_manifest for the PDF
2. Candidate knowledge_record pipeline entry

### 8.4 Test: Archive Discovery

**Input:** "What did I say about the social worker app in past sessions?"

**Expected classification:**
```
domain: CIS
intent_class: ARCHIVE_DISCOVERY
object_type: [session_record]
workflow_state: N/A (read-only)
allowed_action: retrieve
requires_eric_gate: false
```

**Verification:** Routes to archive search. No build_plan_nodes created. No mutations.

### 8.5 Test: Micro1 Out-of-Scope Rejection

**Input:** "Start Micro1 task planning"

**Expected classification:**
```
domain: OUT_OF_SCOPE
intent_class: BLOCKED_MISSING_CAPABILITY
object_type: []
workflow_state: N/A
allowed_action: block
requires_eric_gate: false
```

**Verification:** WorkIntent status=BLOCKED. Reason logged. No build_plan_node created. No agent dispatched.

### 8.6 Test: Implementation Directive (blocked without Eric Gate)

**Input:** "Implement Phase 45" (no prior Eric approval)

**Expected classification:**
```
domain: SWA
intent_class: IMPLEMENTATION_DIRECTIVE
object_type: [build_plan_node]
workflow_state: N/A
allowed_action: request_approval
requires_eric_gate: true
```

**Verification:** Does not dispatch to Implementer. Stages for Eric review. Eric must approve before any code changes.

---

## 9. Tier 7 Node Structure

### 9.1 Proposed build_plan_nodes

| Node | Label | Status | Depends On |
|------|-------|--------|------------|
| Tier 7R | Tier 7R — Intent-to-Workflow Architecture Specification | PROPOSED | Component 3.5 (COMPLETE) |
| Tier 7R.1 | WorkIntent schema + canonical model | PROPOSED | Tier 7R approved |
| Tier 7R.2 | DomainAdapter interface + CISAdapter | PROPOSED | Tier 7R.1 |
| Tier 7R.3 | SWAAdapter (validation use case) | PROPOSED | Tier 7R.2 |
| Tier 7R.4 | Process Manager (state machine) | PROPOSED | Tier 7R.2 |
| Tier 7R.5 | Human approval gate integration | PROPOSED | Tier 7R.4 |
| Tier 7R.6 | Dead Letter / blocked handling | PROPOSED | Tier 7R.1 |
| Tier 7R.7 | Acceptance test suite | PROPOSED | Tier 7R.3, 7R.4, 7R.5 |

### 9.2 Relationship to existing nodes

| Existing Node | Action |
|---------------|--------|
| Tier 7 — Full Durable Router Pipeline (DEFERRED) | Keep DEFERRED. Do not revive. Replaced by Tier 7R. |
| Tier 7.1 — Router Reclassification (COMPLETE) | Preserved. Its archive discovery classification feeds into Tier 7R's CISAdapter. |
| Tier 7.5a — Corpus Audit (COMPLETE) | Preserved. |
| Tier 7.5b — Clean Subset Import + FTS5 (COMPLETE) | Preserved. |
| Tier 8 — MCP Bridge (BLOCKED) | **Keep BLOCKED.** Tier 8's hard dependency shifts from old Tier 7 (node 8) to Tier 7R.4 (new Process Manager node). Tier 8 is unblocked ONLY when ALL of: (a) Tier 7R.4 status = COMPLETE, (b) Process Manager enforces state machines for source, knowledge_record, and build_plan_node objects, (c) all 6 acceptance tests from §8 pass, (d) Eric Gate approval recorded for Tier 7R.4, (e) git diff + test output + spine query evidence verified. See §11 for full gating criteria. |
| Tier 9 — Chroma/VDB (BLOCKED) | Keep BLOCKED — gated on Tier 8. |
| Tier 10 — CIS UI (BLOCKED) | Keep BLOCKED — gated on Tier 9. |

---

## 10. Recommendation

**Replace Tier 7 with Tier 7R.**

The old Tier 7 ("Full Durable Router Pipeline") was defined before SWA existed as a use case, before the CIS Plain Language Build Roadmap was fully analyzed, and before the enterprise integration pattern research was conducted. It was a placeholder. The research from Hohpe & Woolf, Evans, Cockburn, and modern workflow engines all confirms that the correct architecture for multi-domain workflow classification is: Content-Based Router → Domain Adapters → Process Manager → Human Approval Gate → Dispatch.

Tier 7R should be created as a new build_plan_node set (7R, 7R.1–7R.7). Old Tier 7 remains DEFERRED. Tier 8 remains BLOCKED until Tier 7R.4 (Process Manager) is complete.

The acceptance test standard is concrete: Given the SWA Technical Overview, CIS classifies it as SWA requirements recovery, identifies affected objects (action_steps, client_need_id, goal_id, appointments, D.A.P. notes), stages candidate build_plan_nodes, and does not implement anything until Eric approves.

---

## 11. Phased Build Plan

### 11.1 Principle

This specification is an architecture basis, not an implementation directive. Tier 7R
must be built as sequential, independently-gated build_plan_nodes. Each node requires
its own Eric Gate approval before work begins. No node may start before its
dependencies are COMPLETE.

### 11.2 Minimum viable first implementation node: 7R.1

7R.1 is the smallest useful increment. Its scope:

| Deliverable | Description |
|-------------|-------------|
| WorkIntent schema | SQLite table or Python dataclass with fields from §4.2 |
| Scope registry | Hardcoded enum: CIS, SWA, WIAS, OUT_OF_SCOPE |
| Micro1 rejection | OUT_OF_SCOPE classification with logged reason |
| Empty adapter interface | Python ABC or protocol for 7R.2 to implement |
| No classification logic | 7R.1 only defines data structures and scope boundaries |

What 7R.1 does NOT include: domain adapter implementation (7R.2), intent
classification (7R.2), state machine (7R.4), human approval wiring (7R.5), dispatch
(7R.5).

### 11.3 Full 7R.1–7R.7 dependency graph

```
Tier 7R (umbrella specification — APPROVED_AS_ARCHITECTURE_BASIS)
  └── 7R.1 (WorkIntent schema, scope registry, Micro1 exclusion)
        ├── 7R.2 (CISAdapter — CIS domain only)
        │     ├── 7R.3 (SWAAdapter — validation use case)
        │     └── 7R.4 (Process Manager — state machine)
        │           └── 7R.5 (Human approval gate integration)
        │                 └── 7R.7 (Acceptance test suite) ← also depends on 7R.3
        └── 7R.6 (Dead Letter / blocked handling)
```

### 11.4 Node details

| Node | Label | Depends On | Scope |
|------|-------|-----------|-------|
| Tier 7R | Tier 7R — Intent-to-Workflow Architecture (umbrella) | Component 3.5 | Specification approved as architecture basis (this document) |
| 7R.1 | WorkIntent schema + scope registry + Micro1 exclusion | Tier 7R | Create canonical WorkIntent schema. Define scope registry. Explicitly exclude Micro1. Empty adapter interface. |
| 7R.2 | CISAdapter (CIS domain only) | 7R.1 | Classify CIS intents only: ARCHIVE_DISCOVERY, KNOWLEDGE_INTAKE, KNOWLEDGE_RETRIEVAL, REQUIREMENTS_RECOVERY. Map to Tier 7.1 archive route. Stage candidates. |
| 7R.3 | SWAAdapter (validation use case) | 7R.2 | Classify SWA intents. Handle PRE_PLAN, APPOINTMENT_UNLINKED, NOTE_GENERATION states. Stage candidates. Never touches SWA codebase. |
| 7R.4 | Process Manager (state machine) | 7R.2 | Enforce legal state transitions per §6. Determine allowed_action. Integrate with workflow_runs per ADR-013. |
| 7R.5 | Human approval gate integration | 7R.4 | Wire Eric Gate to staged candidates. Implement request_approval path. Block dispatch until Eric approves. |
| 7R.6 | Dead Letter / blocked handling | 7R.1 | OUT_OF_SCOPE rejection. BLOCKED_MISSING_CAPABILITY logging. Unrecognized domain routing. |
| 7R.7 | Acceptance test suite | 7R.3, 7R.4, 7R.5 | Six tests from §8: SWA Phase 45, SWA unlinked appointment, CIS knowledge intake, archive discovery, Micro1 rejection, implementation directive blocking. |

### 11.5 Tier 8 unblocking criteria

Tier 8 (MCP Bridge) is currently BLOCKED with hard dependency on old Tier 7 (node 8).
This dependency must be revised to point at Tier 7R.4.

Tier 8 shall remain BLOCKED until ALL of:

| # | Condition | Verification |
|---|-----------|-------------|
| 1 | Tier 7R.4 status = COMPLETE | build_plan_nodes row |
| 2 | Process Manager enforces state machines for ≥3 object types (source, knowledge_record, build_plan_node) | Acceptance test output |
| 3 | WorkIntent → Process Manager → allowed_action pipeline correct for all 6 acceptance tests | Test suite output |
| 4 | Eric Gate approval recorded for Tier 7R.4 | eric_gate_approvals row |
| 5 | Evidence manifest complete: git diff, test output, spine queries | Evidence directory |

### 11.6 Old Tier 7 disposition

Old Tier 7 (node 8, "Full Durable Router Pipeline") remains DEFERRED permanently.
It is not revived. It is not implemented. Its dependency edge to Tier 8 (node 12)
is superseded by a new edge from Tier 7R.4 to Tier 8 when 7R.4 nodes are created
in the spine.

### A.1 Current build_plan_nodes state
```
COMMAND: sqlite3 data/cis_memory.db "SELECT node_label, status FROM build_plan_nodes WHERE node_label LIKE '%Tier 7%' OR node_label LIKE '%Tier 8%' OR node_label LIKE '%Tier 9%' OR node_label LIKE '%Tier 10%' OR node_label LIKE '%Component 3.5%'"
OUTPUT:
Component 3.5 — Build-Plan Spine Authority|COMPLETE
Tier 7 — Full Durable Router Pipeline|DEFERRED
Tier 7.1 — Router Reclassification (archive route)|COMPLETE
Tier 7.5a — Corpus Audit|COMPLETE
Tier 7.5b — Clean Subset Import + FTS5|COMPLETE
Tier 8 — MCP Bridge|BLOCKED
Tier 9 — Chroma/VDB|BLOCKED
Tier 10 — CIS UI / Custom Display Views|BLOCKED
```

### A.2 Component 3.5 completion
```
COMMAND: sqlite3 data/cis_memory.db "SELECT node_label, evidence_path, commit_hash, completed_at FROM build_plan_nodes WHERE node_label LIKE '%3.5%'"
OUTPUT:
Component 3.5 — Build-Plan Spine Authority|git:65451e0|65451e0|2026-06-12 04:59:01
```

### A.3 ADR-013 (Kanban retirement)
```
COMMAND: grep 'ADR-SEED-013' AGENTS.md
OUTPUT:
[ADR-SEED-013] Retire Kanban as required pipeline transport: Kanban is no longer
required for router, orchestrator, gate, or closeout execution. workflow_runs is
the authoritative in-flight work object...
```

### A.4 SWA workflow evidence
```
Source: /mnt/projects/swa/social_work_ai/07_DOCUMENTS/Analysis of Current Workflow.md
Key excerpt: "The workflow you described — receiving an email for a new client,
needing to create that client, schedule their intake, and then document it —
reveals the friction in the current design."
```

```
Source: /mnt/projects/swa/social_work_ai/07_DOCUMENTS/3 Technical overview.pdf
Key excerpt: "Phase 1: Pre-Treatment Plan (First 30 Days): Billable activities...
occur before formal Needs and Goals are documented. The current system has no
natural way to log these essential, foundational activities."
```

### A.5 Enterprise Integration Patterns research
```
Source: https://www.enterpriseintegrationpatterns.com/patterns/messaging/ContentBasedRouter.html
Key excerpt: "Use a Content-Based Router to route each message to the correct
recipient based on message content."
```

```
Source: https://www.enterpriseintegrationpatterns.com/patterns/messaging/ProcessManager.html
Key excerpt: "Routing Slip is based on two key assumptions: the sequence of
processing steps has to be determined up-front and the sequence is linear. In
many cases, these assumptions may not be fulfilled."
```

### A.6 CIS Plain Language Build Roadmap
```
Source: /mnt/projects/cis/docs/_archive/CIS_Canonical_Build_Sequence/CIS_Plain_Language_Build_Roadmap.md
Key excerpt: "A file goes through five stages to become useful knowledge in CIS...
Everything being built in every phase exists to make those five stages work
reliably, repeatedly, and eventually at scale across 10TB of material."
```

### A.7 Current git HEAD
```
COMMAND: git rev-parse HEAD
OUTPUT: dafa5bb8d31c5fbd64ef40e0bc8749ee69b1afec
```

### A.8 Dependency graph
```
COMMAND: sqlite3 data/cis_memory.db "SELECT * FROM build_plan_dependencies"
OUTPUT (relevant rows):
12|8|7|HARD    -- Tier 8 depends on Tier 7 (node_id 8 depends_on node_id 7 = Tier 7)
13|12|8|HARD   -- Tier 9 depends on Tier 8
14|13|12|HARD  -- Tier 10 depends on Tier 9
```

---

## Appendix B: External Review Summary

ChatGPT (deepseek-v4-pro) reviewed this direction and confirmed:

> "Hermes' research supports replacing the old Tier 7 router with a broader
> intent-to-workflow layer. Routing remains inside the system, but it is not
> the system. The composite architecture — Content-based routing + domain
> adapters + workflow state machine + canonical WorkIntent object — gives
> the strongest balance of flexibility and control."

> "Do not implement Tier 7 yet. Create the Tier 7R specification first."

## Appendix C: Deferred Implementation Notes

The following Python pseudocode was moved from §5.1 (Domain Adapter Contract).
It is deferred until the individual adapter build_plan_nodes (7R.2, 7R.3) are
approved for implementation. It is included here as a reference for the adapter
interface shape.

```python
class DomainAdapter:
    domain: str  # "CIS", "SWA", "WIAS"

    def classify_intent(work_intent: WorkIntent) -> WorkIntent:
        """Classify intent_class, object_type, object_refs from raw input."""

    def validate_state(work_intent: WorkIntent) -> WorkIntent:
        """Check spine for current object state. Set workflow_state and allowed_action."""

    def resolve_objects(work_intent: WorkIntent) -> WorkIntent:
        """Resolve object_refs from spine. Verify objects exist and are accessible."""

    def stage_candidates(work_intent: WorkIntent) -> list[WorkIntent]:
        """Generate candidate build_plan_nodes, workflow_runs, or other durable work.
        NEVER mutates spine directly. Returns candidate WorkIntents for Eric review."""
```

---

*End of Tier 7R Specification Proposal v1.0 — Revised*
*Eric Gate disposition: APPROVED_AS_ARCHITECTURE_BASIS*
*Next step: Create build_plan_nodes for 7R.1–7R.7 in spine → PROCEED on 7R.1*
