# CIS Category to Application-Part Map
# Reference for taggers, reviewers, and the Drafter.
# Maps every tagging category to the CIS application parts it informs.
# Generated from TAGGING_DIRECTIVE_v3.1 — update both together.

## The Three Application Parts

| Part | What it is | Where it lives |
|------|-----------|----------------|
| **control-plane** | Portal, chat panels, model dropdowns, Flask endpoints, Eric's interaction surface | `portal/`, Flask blueprints, browser |
| **abstraction-layer** | Dispatch boundary: routing, trigger, permission gate, intent→pipeline handoff | `runtime/orchestrator.py`, `runtime/router.py`, intent-inference |
| **hermes-backend** | Enforced container: Docker, RO mounts, pre_tool_call hook, managed scope, 7-stage pipeline, orchestrator, Drafter/Reviewer/Implementer agents | `/opt/cis-control/`, Dockerfile, plugin hooks, managed-config |

## Category → Application Part Mapping

### control-plane
Categories that inform the portal, panels, and Eric's interaction surface:
| Category | Functionality it informs |
|----------|------------------------|
| control-plane | Panel layout, model dropdowns, chat modes (1:1, parallel, adversarial), Flask `/api/portal/*` endpoints, dark-mode toggle, settings panel |
| intent-inference | Chat-to-pipeline trigger, confirmation gate UI, [PIPELINE:] marker detection |
| eric-intention | What Eric wants the control plane to do, what he approves/disapproves |
| decision | Settled UI choices, panel architecture decisions |

### abstraction-layer
Categories that inform the dispatch boundary and routing:
| Category | Functionality it informs |
|----------|------------------------|
| intent-inference | Trigger mechanism, classify_route, intent recognition, confirmation gate |
| pipeline | Router → orchestrator dispatch, Drafter/Reviewer/Implementer routing |
| intent-scrape | Catalog output routing, provenance registration, spine writes |
| agent-roles | Role-based routing enforcement (Drafter→8645, Reviewer→8643, Implementer→8646) |
| enforcement | Container dispatch, verifying the dispatch path enters the container |
| open-question | Unresolved routing decisions, trigger design choices |

### hermes-backend
Categories that inform the enforced container and pipeline execution:
| Category | Functionality it informs |
|----------|------------------------|
| enforcement | Docker container, RO mounts, pre_tool_call hook, managed-scope pinning, T10 block, seal verification |
| pipeline | Orchestrator self-dispatch, deliberation rounds, Drafter/Reviewer/Implementer execution, gates, closeout |
| intent-scrape | Corpus extraction running inside container, Pass 1/Pass 2 catalog, provenance registration |
| shared-memory | Persistent memory, cross-session state, agent knowledge, amnesia prevention |
| agent-roles | Profile duties, Drafter/Reviewer/Implementer functions, role enforcement inside container |
| profile-character | SOUL.md content, tool assignments, hooks per profile, what each agent is constrained to |
| guardrail-mechanism | pre_tool_call hook, managed-scope, T10 block, verification gates, enforcement walls |
| verification-method | Evidence standards, test design, deterministic verification inside container |

### cross-cutting
Categories that apply across multiple application parts or the whole system:
| Category | Functionality it informs |
|----------|------------------------|
| lane-cis-product | How CIS works for any future user — control plane + abstraction + backend design |
| lane-cis-project | Building CIS with CIS — all three parts under development |
| failure-pattern | 16 failure modes — appear in any part, guardrails span all three |
| enterprise-friction | Model drift toward enterprise defaults — detected at any part |
| decision | Settled choices that affect architecture across parts |
| open-question | Unresolved design choices that may span parts |
| wiasw-origin | Lineage tracing from analog framework — applies to architecture across parts |
| guardrail-mechanism | Walls and gates that span the abstraction + backend boundary |
| verification-method | Evidence standards used across all parts |

### reviewer-measurement
Categories that feed the Reviewer Measurement Brief (deliverable 5):
| Category | Functionality it informs |
|----------|------------------------|
| eric-intention | Eric's stated goals — what reviewers validate against |
| profile-character | What each agent profile should look like, its duties and constraints |
| reviewer-duties | What reviewers are supposed to check, audit, or challenge |
| measurement-criteria | The specific criteria reviewers measure tagged output against |
| reviewer-brief | Any content that belongs in the Reviewer Measurement Brief |
| lane-cis-product | The general mechanism reviewers validate Lane 2 against |
| lane-cis-project | The specific build reviewers are auditing |

## How to Use This Map

**Taggers (Pass 1):** When you tag a block, use this map to choose accurate BUILD TARGET
and FUNCTIONALITY values. A block about the portal panel layout → control-plane,
FUNCTIONALITY: '4-panel layout'. A block about the pre_tool_call hook → hermes-backend,
FUNCTIONALITY: 'pre_tool_call hook — write-block'. A block about Eric's role →
reviewer-measurement, FUNCTIONALITY: 'Eric role definition'.

**Reviewers (Pass 2/4):** When auditing, verify that:
- BUILD TARGET assignments match this map
- FUNCTIONALITY entries are specific, not generic ('panel' not 'UI stuff')
- No category appears on a part it doesn't inform

**Drafter (Pass 3):** When synthesizing deliverables, use the FUNCTIONALITY field
to group tagged blocks by specific component, then by application part. The
Reviewer Measurement Brief (deliverable 5) is built primarily from
reviewer-measurement categories. Deliverables 1-2 are built from control-plane,
abstraction-layer, and hermes-backend categories.
