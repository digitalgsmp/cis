# CIS — Intention-Driven Directives

**Status:** PROPOSAL | **Date:** 2026-07-04 | **Author:** Drafter (V4 Pro)
**Purpose:** Replace AGENTS.md governance ceremony with Eric's verbatim intentions as the primary session directives.

## Problem

AGENTS.md has been bypassed. Agents don't follow it because:
1. It's stale (write-back gap — no agent can record completed work in the spine)
2. It blocks more than it directs (Do Not Start list, ceremony, theater)
3. It misdirects (says Brainstorm on 8644, reality is 8649)
4. Eric's actual intentions — what he wants built — are scattered across session files and never consolidated into operational directives

AGENTS.md is governance theater. Eric already ordered its ceremony stripped on June 18 (session `20260618_020230`). The governance reset proposal was written but never executed.

## What Eric Wants (Verbatim Intentions)

From session files, Eric's recurring directives:

1. **"Replace myself with the portal"** — build a control plane where models collaborate without Eric as the API loop. Portal becomes the tool Eric uses, not the manual paste-between-terminals workflow. (June 21, June 26)

2. **"I want all models to have access to the knowledge base"** — every model in the pipeline needs shared access to Eric's past decisions, intentions, and the knowledge base so they can learn from each other. (June 30)

3. **"Intelligence over mechanism"** — the model IS the mechanism. Give it access + a clear question. No extraction pipelines, query strategies, tagging systems, or pre-defined data paths where inference suffices. This is the core differentiator between CIS and enterprise architecture. (July 3, encoded as Principle 9)

4. **"Build the smallest working application path that reduces my manual burden"** — from the June 18 governance reset: "build the smallest working app path." Every session should produce working software, not more specs about specs.

5. **"Governance should be a feature of the finished application, not the development process"** — container enforcement walls are the governance. Prompts and ceremony are not. (June 18)

6. **"Three training distributions for checks and balances"** — DeepSeek, Anthropic, Z.ai/Tsinghua. No single training corpus dominates. Drafter ≠ Implementer (ADR-SEED-004). (June 30)

7. **"Don't work without collaborators"** — Claude and GLM reviewing alongside before any changes proceed. (June 21)

8. **"I need a worker who is constrained to my working methods and two objective reviewers as expert advisors"** — from the seed intent. Worker constrained, reviewers advisory, Eric decides. (May 18)

9. **"The LLMs don't remember anything and the overall vision is not apparent to combine the vision of where I am trying to get to, to why we are working on the immediate task"** — models need persistent context of the WHY, not just the WHAT. (May 25)

10. **"Complete the container setup and transition to working there"** — the permanent workshop in the sealed container is the prerequisite for agent write capability. No write path on the unregulated host. (July 3)

## Proposal: Intention-Driven Session Protocol

### What Changes

1. **INTENTIONS.md replaces AGENTS.md as the primary directive document**
   - Contains Eric's verbatim intentions with source provenance (session ID, date)
   - Updated when Eric states new intentions or refines existing ones
   - Loaded at session start alongside memory
   - No Do Not Start lists, no pipeline lane descriptions, no role ceremony

2. **Session startup loads intentions, not governance**
   - Hermes loads INTENTIONS.md → understands WHY we're working on this
   - Current task is framed as: "which intention does this advance?"
   - READ_ONLY_STANDING_BY protocol still applies (container enforcement, not ceremony — it prevents mutation before Eric approves)

3. **Reviewers operate under anti-bias rule (already in SPEC_CONTROL_PLANE_OBSERVATION.md §9)**
   - Objections must cite Eric's verbatim words or factual errors
   - "Underspecified mechanism" objections rejected when model inference handles the task
   - Reviewer job: catch blind spots, factual errors, misalignment with Eric's intentions — NOT demand enterprise architecture patterns

4. **Governance is the environment**
   - Container RO mounts, managed config, mwl-proof plugin = enforcement
   - No prompt-level governance claims ("Eric Gate not bypassable") — the container proves it
   - Three development rules from June 18 reset remain the only process rules:
     1. Don't destroy files or data
     2. Don't claim completion without evidence
     3. Build the smallest working app path that reduces Eric's manual burden

### What Gets Removed

- AGENTS.md as agent directive document (archive it)
- Do Not Start list (container walls prevent dangerous actions; intentions focus what to build)
- Pipeline lane descriptions, role identity ceremony
- Non-bypassability claims, escalation protocols
- Long-form verification rules (replaced by: evidence commands + raw output)
- The pre-commit hook that regenerates stale AGENTS.md/HCP from stale spine data

### What Stays

- ADRs as architecture decisions (move to INTENTIONS.md appendix or keep separate)
- Container enforcement specs (these are build artifacts, not governance)
- SPEC_CONTROL_PLANE_OBSERVATION.md (it's a build spec, not ceremony)
- Session handoff records (operational state, not governance)

### Implementation

1. **Create INTENTIONS.md** — extract Eric's verbatim intentions from session files (the 10 listed above are a start; full extraction uses the intention recovery pipeline already designed)

2. **Remove AGENTS.md** from the CIS repo (or archive to `docs/archive/`)

3. **Wire INTENTIONS.md loading** — add to Hermes system prompt via project context or TERMINAL_CWD directive

4. **Verify** — run one pipeline cycle under the new directive model; confirm reviewers operate under anti-bias rule

## Evidence Required from Reviewers

Per Eric's directive: reviewers refine the work, don't create ceremony. For this proposal, reviewers should check:

1. Does this correctly represent Eric's intentions as stated in sessions?
2. Does this remove governance theater without losing operational guardrails?
3. Does this make sessions more actionable — directly advancing intentions vs debating ceremony?
4. Any factual errors or missing intentions?

Anti-bias rule applies: if a reviewer objects that "intention extraction mechanism is undefined," the response is: the Drafter has KB access. The model determines how to find Eric's words. Intelligence, not mechanism.
