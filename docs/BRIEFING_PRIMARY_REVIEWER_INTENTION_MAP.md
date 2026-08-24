# Primary Reviewer Briefing — Intention Map Spec v1.0

**To:** Claude (Fable 5)
**Role:** Primary Reviewer
**Task:** Evaluate the Intention Map specification for completeness, accuracy, and utility.

---

## Context

Eric has been building CIS (Control and Integration System) for 4 months — a multi-agent pipeline where AI models with different training data review each other's work, validate against his documented intentions, and execute in a constrained containerized environment.

Over the past 74 days, 188 intention cards were extracted from 444 sessions across 4 AI agents (DeepSeek V4 Pro, DeepSeek R1, Qwen 30B, GLM 4.7 Flash). Each card captures: what Eric was trying to accomplish, how it connects to the CIS mission, what was learned, and why a frontier model needs to know it.

The Intention Map specification proposes distilling these 188 cards into a single briefing document that a frontier model (like you) can read and immediately understand the mission, scope, constraints, and current state.

## Your Role

As primary reviewer, evaluate the specification against these criteria:

1. **Structure:** Is the proposed structure (Mission → Core Intentions → Timeline → Briefing → Constraints) the right shape? Would this actually help a frontier model understand Eric's project?

2. **Granularity:** Is 8-10 core intentions the right number? Too many? Too few?

3. **Traceability:** The spec requires each intention be traceable to at least 3 source cards across 2+ time periods. Is this threshold appropriate?

4. **Accountability:** Section 7 lists 5 accountability measures. Are they sufficient? What's missing?

5. **Scope:** Section 9 defers SWA and WIASW to separate maps. Is this the right boundary?

6. **Format:** What format would make the Frontier Model Briefing (Section 3.4) most useful when you have limited context window?

7. **The open questions (Section 8):** Answer each one with your recommendation.

## Evidence Available

The 188 intention cards are at `/mnt/projects/cis/cards/intentions.jsonl`. The spec references them as evidence. You can request specific cards or clusters if you need to verify claims.

## What We Need From You

A structured review with:
- What works — sections that are correctly designed
- What's missing — gaps in the specification
- What should change — specific recommendations
- Your answers to the 7 open questions in Section 8
- Any constraints you'd impose on the implementation

## Deliverable Format

Please end your review with a FINAL_JSON block:
```json
{
  "role": "reviewer",
  "status": "CONSENSUS_REACHED|OBJECTIONS|ESCALATE",
  "summary": "<one paragraph>",
  "recommendation": "<what to do next>",
  "next_action": "<specific next step>"
}
```
