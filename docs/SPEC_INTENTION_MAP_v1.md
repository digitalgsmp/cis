# Intention Map — Specification v1.0

**Author:** Hermes Prime (DeepSeek V4 Pro)
**Date:** 2026-08-02
**Status:** DRAFT — awaiting external reviewer feedback (Claude, ChatGPT)
**Source:** 188 intention cards extracted from 444 sessions across all agent profiles

---

## 1. What This Is

The Intention Map is a **context briefing for frontier models** (Claude, ChatGPT). It distills Eric's persistent intentions — what he's been trying to build for 4 months — into a single reference document that a frontier model can read and immediately understand the mission, scope, constraints, and what's already built.

It is derived from 188 intention cards captured across 444 sessions with 4 AI agents from May 21 to August 2, 2026.

## 2. What This Is NOT

- **NOT a build plan.** It doesn't sequence work or assign tasks.
- **NOT a spec.** It doesn't define components, APIs, or schemas.
- **NOT a todo list.** It captures direction, not execution steps.
- **NOT a replacement for the 188 cards.** Those are the evidence index. This is the synthesis.

## 3. Structure

```
INTENTION MAP
├── 3.1 MISSION STATEMENT
│   What CIS is, in Eric's own words. Not summarized. Not interpreted.
│
├── 3.2 CORE INTENTIONS (8-10)
│   Each intention:
│   ├── Statement — what Eric wants, clearly
│   ├── Persistence — how many exchanges support it (from 188 cards)
│   ├── Verbatim Evidence — 2-3 exact quotes from Eric
│   ├── What He Rejected — explicit NOs that define the boundary
│   ├── Current State — built / in progress / blocked
│   └── Linked Cards — IDs of supporting intention cards
│
├── 3.3 EVOLUTION TIMELINE
│   How intentions developed, shifted, or persisted over 4 months.
│   Shows what was abandoned vs. what survived.
│
├── 3.4 FRONTIER MODEL BRIEFING
│   One-page compact version: "If you're Claude/ChatGPT working on
│   CIS, here's what you need to know before you start."
│
└── 3.5 CONSTRAINTS AND NON-NEGOTIABLES
    Rules that every frontier model must follow when working on CIS.
    Derived from Eric's explicit rejections across the 188 cards.
```

## 4. Derivation Method

Each core intention must be traceable to the 188 cards. The process:

1. Cluster the 188 cards by thematic similarity
2. Extract persistent intentions that appear across multiple time periods
3. Rank by persistence (frequency × time span × explicitness)
4. Distill each cluster into a single intention statement
5. Link each intention back to its source cards
6. Identify what Eric explicitly rejected within each cluster

**Hard rule: no intention can appear that isn't supported by at least 3 cards across 2+ time periods.** Single-appearance intentions go in a "one-time asks" appendix.

## 5. Deliverables

| File | Purpose |
|------|---------|
| `cards/INTENTION_SYNTHESIS.md` | Full map with all sections, evidence links, timeline |
| `cards/FRONTIER_MODEL_BRIEFING.md` | Compact one-page version for context window |
| `cards/intentions.jsonl` | Source cards (already exists — 188 cards) |

## 6. Success Criteria

A frontier model reading the Intention Map should be able to:

1. State Eric's mission in one sentence without looking at the document
2. Identify which of his intentions are already built, in progress, or blocked
3. Understand what Eric has explicitly rejected and why
4. Trace any intention back to the exact conversation where Eric stated it
5. Propose new work that aligns with existing intentions, not contradicts them

## 7. Accountability Mechanism

**Before the Intention Map is considered complete:**

1. External reviewer(s) audit the map against the 188 cards — do the core intentions accurately reflect the evidence?
2. Eric reviews the map and confirms/reframes each core intention
3. Every core intention must have at least one rejected alternative listed
4. The "Current State" for each intention must be verified against live infrastructure (not self-reported)
5. The Frontier Model Briefing must fit in a single context window (~8K tokens)

## 8. Open Questions for Reviewers

1. Is 8-10 core intentions the right granularity, or should it be fewer/more?
2. Should the timeline show evolution within each intention, or be a separate section?
3. How should we handle intentions that Eric has stated but later contradicted or superseded?
4. What format makes the Frontier Model Briefing most useful for a model that has never interacted with Eric?
5. What accountability measures are missing from Section 7?
6. Should the intention map be regenerated/updated as new sessions accumulate, or is this a one-time artifact?

## 9. Scope Boundary

**IN SCOPE:** Eric's intentions about CIS — what the system should do, how it should work, what it should enforce, what it should never do.

**OUT OF SCOPE:** SWA app features, WIASW creative framework details, general AI philosophy discussions that don't directly inform CIS design.

**DEFERRED:** Intentions about SWA and WIASW will be addressed in separate intention maps derived from the same 188-card pool but filtered for domain relevance.

---

**Next Step:** Route to Claude and/or ChatGPT for review. Incorporate feedback. Present to Eric for confirmation. Then build.
