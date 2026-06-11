# CIS Future Build-Plan/Prose-Spine Architecture Requirement
Date: 2026-06-10
Status: FUTURE — Not part of current Component 2 scope
Author: Eric (Architect), documented by Hermes V4 Implementer
HEAD: 89b2347

---

## Purpose

This document records a structural gap identified in the CIS spine/control-plane model.
It is a future architecture requirement only. Component 2 (Escalation Advisor Integration
Protocol Design) proceeds unchanged.

---

## 1. Build Plan as First-Class Database Object

The build plan itself needs to become a first-class database object. Future CIS-managed
projects should not rely on prose documents alone to determine sequence, completion,
dependencies, or next action.

Each build-plan item should eventually be represented in SQLite with:

- project_id
- phase/component identity
- sequence order
- dependencies (foreign keys to other build-plan items)
- status (pending, in_progress, complete, blocked, rejected, diverged)
- required role (Drafter, Reviewer, Implementer, etc.)
- allowed mode (specification, implementation, verification)
- workflow_run linkage (foreign key to workflow_runs)
- evidence/artifact linkage (paths or references to verification artifacts)
- commit/closeout linkage (commit hashes, closeout timestamps)
- completed_at timestamp
- approved_at timestamp

## 2. Divergence Tracking

When reality forces divergence from the original build plan, the divergence should be
documented as structured data, not just prose. Future design should consider:

- original build_plan_item (foreign key)
- divergence reason (text)
- proposed branch/new_item
- impact on sequence
- Eric approval status
- resolution status
- linkage to workflow runs, artifacts, and commits

## 3. Derived next_action

Session startup should eventually derive exact_next_action from this database-backed
build plan, not from prose docs or stale next_actions rows. Query: find the highest-
sequence incomplete item whose dependencies are all satisfied.

The same startup/build-plan state should be mirrored into:

- AGENTS.md (Hermes-native context)
- HCP files (ChatGPT/Claude/external escalation context)
- CIS UI (browser display of current phase and next action)

## 4. Archive/Prose-to-Structure Pipeline

CIS must eventually support turning Eric's brainstorming and development conversations
with LLMs into structured, actionable, deterministic instructions. This means prose from
archives should be storable and manipulable in the database, not just retrieved as raw text.

Future archive/prose model should preserve:

- Eric's original words (immutable, source of truth)
- extracted ideas/concepts
- project candidates
- creative/application domain classification
- unresolved questions
- derived requirements
- proposed next actions
- transformation lineage: prose → concept → project → build plan item → agent directive

This is important because CIS is meant to convert human creative/development conversation
into executable project structures while preserving authorship and traceability.

## 5. Scope Boundaries

This requirement:

- Is NOT part of immediate Component 2 implementation unless directly required by Component 2.
- Component 2 should proceed as planned.
- Any future implementation must be proposed, reviewed, approved by Eric, and gated before schema changes.
- This document is a placeholder/backlog record only.

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-06-10 | Eric / Hermes V4 Implementer | Initial documentation of future build-plan/prose-spine requirement |
