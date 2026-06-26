# CIS Intent Recovery — Tagging Directive v3
# Multi-pass pipeline: Tag → Review A → Drafter → Review B → Eric Gate → Implement
#
# This directive is for PASS 1 only: three models tag independently.
# Subsequent passes reconcile, draft, audit, and build from tagged output.

## FORMAT RULES

Group every 5-15 lines into a tagged block. Output the block's exact text first,
then the metadata block below it, separated by a horizontal rule (---).

For each block:

  ---
  SPEAKER: [Eric | Model name | Document author]
  VOICE: [eric-verbatim | model-interpretation | technical-spec | governance]
  SUBJECT: [one-line summary of what this block is about]
  CATEGORIES: [from list below; create new ones freely when you recognize a pattern not covered]
  BUILD TARGET: [control-plane | abstraction-layer | enforced-container | cross-cutting | pipeline]
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
  profile-character — specific profile traits, duties, SOUL.md content, tool assignments
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

## BUILD TARGET

Which CIS layer does this block inform?

  control-plane — the portal, chat panels, Eric's interaction surface
  abstraction-layer — the dispatch boundary between portal and enforced container
  enforced-container — Docker, RO mounts, hooks, managed scope, the wall
  pipeline — the multi-stage deliberation chain (intent→clarify→deliberate→conciliate→implement→verify)
  cross-cutting — applies to multiple layers or the whole system

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

## THE FOUR DELIVERABLES THIS FEEDS

Tagged output becomes raw material for:

  1. Intent-to-Function Map — Eric's ask → layer → component → build state → source
  2. Functional Specification by Layer — what each component must do, WIASW origin
  3. Anti-Pattern Register — Eric asked X, model produced Y, friction Z, guardrail W
  4. WIASW Domain Model — what CIS inherits from the analog Word→Image→Action→Sound→Web framework

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
