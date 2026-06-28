# CIS Intent Recovery — Tagging Directive v3.1
# Multi-pass pipeline: Tag → Review A → Drafter → Review B → Eric Gate → Implement
#
# This directive is for PASS 1 only: three models tag independently.
# Subsequent passes reconcile, draft, audit, and build from tagged output.
#
# v3.1 UPDATE: Added 5th deliverable — Reviewer Measurement Brief.
# Taggers must now capture content that tells reviewers what they measure against:
# Eric's core intentions, profile character/duties, two-lane model, confirmation gate,
# the 7-stage sequence, and the wall+reference architecture.
# This information must be tagged so the Drafter can synthesize it into a Reviewer
# Measurement Brief BEFORE Review Stage A runs — reviewers need to know what to measure
# against when they audit the raw tags.

## FORMAT RULES

Group every 5-15 lines into a tagged block. Output the block's exact text first,
then the metadata block below it, separated by a horizontal rule (---).

For each block:

  ---
  SPEAKER: [Eric | Model name | Document author]
  VOICE: [eric-verbatim | model-interpretation | technical-spec | governance]
  SUBJECT: [one-line summary of what this block is about]
  CATEGORIES: [from list below; create new ones freely when you recognize a pattern not covered]
  BUILD TARGET: [control-plane | abstraction-layer | hermes-backend | cross-cutting | pipeline | reviewer-measurement]
  FUNCTIONALITY: [what specific component/function/feature could this inform in the CIS application?
                 Name the part: e.g. 'panel model dropdown', 'dispatch router', 'pre_tool_call hook',
                 'orchestrator self-dispatch', 'Flask /api/portal/chat endpoint', 'managed-scope pinning'.
                 If it spans multiple, list them. If unclear, note 'needs Drafter assignment'.]
  INTENT: [if Eric's words: what is he asking for? 1 sentence. If model content: n/a]
  FAILURE FLAG: [if present: which CIS failure mode, enterprise-friction, or false-proof risk]
  ---

  Then a blank line and --- before the next block.

## PRIMARY SORT — VOICE

The most important field. Determines how the block is used downstream:

  eric-verbatim: Eric's actual words captured in chat transcripts or documents he authored.
    → These feed the Intent Map. They contain scope, vision, and what Eric is asking for.

  model-interpretation: A model trying to understand, reframe, or act on what Eric said.
    → These feed the Anti-Pattern Register when they drift toward enterprise defaults.

  technical-spec: Architecture docs, build plans, enforcement specs, code documentation.
    → These feed the Functional Specification and are measured against eric-verbatim intent.

  governance: ADRs, decisions, closeout procedures, pipeline rules.
    → These feed the guardrail mechanisms.

## CATEGORIES

Start with these. Create new ones at your discretion when you recognize a pattern
not covered — your training data may surface distinctions these miss.

  control-plane — portal, panels, UI, chat surface, model dropdowns, Flask endpoints
  enforcement — Docker container, RO mounts, pre_tool_call hook, managed scope, walls
  pipeline — orchestrator, Drafter/Reviewer/Implementer, gates, stages, dispatch
  intent-scrape — corpus recovery, extracting Eric's words, cataloging, provenance
  intent-inference — trigger mechanism, confirmation gate, intent recognition
  shared-memory — persistent memory, amnesia, agent knowledge, cross-session state
  agent-roles — model profiles, Drafter/Reviewer/Implementer functions, role enforcement
  lane-cis-product — how CIS works for any future user, general mechanism
  lane-cis-project — building CIS with CIS, this first project's specific build
  eric-intention — Eric's stated goals, what he wants, his purpose, his pain points
  failure-pattern — 16 failure modes, amnesia, enterprise defaults, false-proofs
  enterprise-friction — model pushing enterprise-dev workflow against Eric's intent
    (these are EVIDENCE — do not discard. They justify the guardrails.)
  decision — settled choice, fork resolved, Eric's approval/rejection
  open-question — unresolved, pending design choice
  wiasw-origin — traces back to WIASW analog framework (Word→Image→Action→Sound→Web)
  guardrail-mechanism — a specific check, gate, or wall that prevents a failure mode
  verification-method — how something is proven, evidence standards, test design
  profile-character — what a specific agent profile looks like: duties, SOUL.md, tools, hooks
  reviewer-duties — what a reviewer is supposed to check, audit, or challenge
  measurement-criteria — what the reviewers should measure against (Eric's intentions, goals)
  reviewer-brief — content that belongs in the Reviewer Measurement Brief (deliverable 5)

## BUILD TARGET

Which part of the CIS application does this block inform? The three application parts are:

  control-plane — the portal, chat panels, model dropdowns, Flask endpoints, Eric's interaction surface
  abstraction-layer — the dispatch boundary between portal and enforced container (routing, trigger, permission gate)
  hermes-backend — the enforced container: Docker, RO mounts, pre_tool_call hook, managed scope,
                   the 7-stage pipeline (intent→clarify→deliberate→conciliate→implement→verify→complete),
                   orchestrator, Drafter/Reviewer/Implementer agents
  pipeline — the multi-stage deliberation chain (use when specifically about pipeline mechanics, not backend generally)
  cross-cutting — applies to multiple application parts or the whole system
  reviewer-measurement — defines what reviewers measure against, profile duties, Eric's intentions

For a full mapping of categories to application parts, see enforcement/CATEGORY_TO_LAYER_MAP.md.

## FAILURE FLAGS

When the block contains a failure pattern, enterprise-friction, or false-proof risk,
flag it. Common patterns:

  false-proof: chain reported success but enforcement wasn't real
  shell-surface: UI wired but endpoints dead
  amnesia-trigger: model forgot prior context and re-litigated
  enterprise-default: model proposed enterprise-dev workflow when Eric asked for something simpler
  self-attestation: model claimed completion without evidence
  scope-creep: model expanded the task beyond Eric's stated intent
  blind-routing: model classified intent to wrong agent/role
  sequential-build-violation: building step 3 before step 1 exists

These are NOT things to discard. They are evidence that the enforcement + intent-memory
architecture solves a real problem. The Anti-Pattern Register is built from these.

## THE FIVE DELIVERABLES THIS FEEDS

Tagged output becomes raw material for:

  1. Intent-to-Function Map — Eric's ask → layer → component → build state → source
  2. Functional Specification by Layer — what each component must do, WIASW origin
  3. Anti-Pattern Register — Eric asked X, model produced Y, friction Z, guardrail W
  4. WIASW Domain Model — what CIS inherits from the analog Word→Image→Action→Sound→Web framework
  5. Reviewer Measurement Brief — what reviewers measure against: Eric's core intentions, 
     profile character/duties, two-lane model, confirmation gate, 7-stage sequence,
     wall+reference architecture, Eric's role (approve/disapprove/refine). This document
     must exist before Review Stage A so reviewers know what they're auditing against.

## WHAT REVIEWERS MEASURE AGAINST

When tagging, pay special attention to content that defines:

  1. Eric's role — "approve, disapprove, or refine intention." NOT coder/architect.
     The models have the expert information; Eric steers by intention.
  2. Two lanes — Lane 1: CIS-as-product (general mechanism for any user).
     Lane 2: CIS-as-project (building CIS with CIS, this first project).
  3. The 7-stage enforced sequence — intent inference → clarification → deliberation →
     conciliation → implementation → verification → completion. All seven must run
     inside the enforced container.
  4. Wall + reference architecture — the container is the wall (stops models from
     running off). The intent memory/corpus is the reference (tells models where to
     run toward). Neither alone overcomes the 16 failures.
  5. Confirmation gate — model reflects intent back to user, user confirms before
     pipeline triggers. Intent inference alone is not permission.
  6. Profile character — what each agent profile looks like: its duties, its
     SOUL.md content, its tools, its hooks. The container constrains the profile;
     the profile constrains the behavior.
  7. Intent memory — the scraped corpus of Eric's intentions becomes the reference
     every stage validates against. Without it, enforcement enforces against
     enterprise defaults.

## WIASW CONTEXT

WIASW (Word→Image→Action→Sound→Web) was the analog precursor to CIS, created before
AI became what it is. It contained Eric's self-improvement methodology and the general
mechanism for any user to set training targets across domains. CIS is the first AI-native
instantiation. When you recognize WIASW-origin patterns in a block, flag them — they
trace the lineage from analog framework to AI pipeline.

## FINAL INSTRUCTION

Tag the ENTIRE document. Every 5-15 lines gets a tagged block with metadata.
Create new categories freely. Your training data may surface distinctions these
predefined categories miss — use them, and note them as NEW CATEGORY in the output.
