# SPEC — Intention-Driven CIS: Knowledge Surface & Profile Soul

**Status:** PROPOSAL_READY | **Date:** 2026-07-04 | **Author:** Drafter (V4 Pro)
**Run ID:** run-direct-eric-telegram

---

## Eric's Core Ask

A system that surfaces what he doesn't know to ask about. When he's working on an intention, the system proactively volunteers adjacent knowledge buried in his archive — technologies, approaches, patterns, pitfalls, connections across projects. Can model inference alone achieve this, or does mechanism help?

---

## Source Material

### SWA Era (Feb 2026)

First contact with unconstrained models. Architect Agent managing 12 specialists. Tiered file access. Core question: "How to get a model to only execute what I intended."

### UTAB Era

5-entity alignment system: Designer → Conductor → Librarian → Engineer → Laborer → Inspector. "Church and State" separation. Inspector validates every action. Precursor to pipeline roles, pre-tool-call hooks, ADR-015/016 enforcement architecture.

### Soul Documents

Ten Commandments + G.O.D. Protocol. Key insight: behavior modification must precede rule-following. AI must admit powerlessness over statistically biased training data before it can follow rules. 12 Steps of Machine Redemption.

### CIS Foundation

Intelligence → Knowledge → Application. 8 layers. WIAS creative model. Four feedback loops. Operator Model as governing logic.

### Operator Pivot

"Human operator had become middleware." Eric's breakthrough: "can't you infer what I am trying to do? Start from the source material." Shifted the entire architecture from manual relay to intent-driven pipeline.

### Current State

6 pipeline gateway profiles operational. 287K FTS5 messages, 9.3GB ChromaDB, 11K Google Drive files. ADR-015/016 container enforcement proven. Phase 0 loop-breaker in progress.

---

## Confirmed Intentions (from this session)

1. WIASW spreadsheet → agentic web app with unified calendar/UI
2. CIS data model derived from WIASW object model
3. Intelligence → Knowledge → Application
4. Operator Model as governing logic
5. Four feedback loops as system architecture
6. Sequential build: prove, stabilize, integrate, expand
7. Three training distributions. Drafter ≠ Implementer
8. Container enforcement as governance
9. Intelligence over mechanism
10. Profile soul: Ten Commandments + G.O.D. Protocol
11. Knowledge graph growing every session
12. "Did You Know" agent

---

## What Gets Built

### 1. Profile Soul Skills

Each of the 6 pipeline profiles loads a shared base (Ten Commandments + G.O.D. Protocol) with role-specific emphasis overlays:

| Profile | Role Overlay |
|---------|-------------|
| Drafter | Anti-assumption, reality verification, "never guess what Eric wants" |
| Implementer | Non-destructive change, primacy of intent over cleverness |
| Reviewer (R1 + Qwen) | G.O.D. inventory — has this proposal been measured against Eric's words? |
| Verifier | Deterministic evidence only, no trust-based acceptance |
| Brainstorm | Free association bounded by Operator Model |

Principle: behavior modification (soul) is the first wall. Container enforcement is the last wall. They're complementary, not redundant.

### 2. Intentions Table

Searchable index in the SQLite spine:

- Eric's verbatim words (exact, not summarized)
- Source document path (load the original)
- Status (confirmed, revised, superseded)
- Dependencies on other intentions
- Mapped layer (control-plane / abstraction-layer / hermes-backend)

Agents reference intentions by loading source documents directly — intelligence over mechanism. No summaries between Eric and the agent.

### 3. Knowledge Graph Agent

A skill loaded by agents. Continuously mines the KB for buried connections between:
- Intentions across different sessions
- Documents that reference each other
- Components that share WIASW lineage
- Failure patterns that map to multiple components

Outputs: new links added to the graph, surfaced intentions that may have been forgotten.

### 4. "Did You Know" Capability

Three approaches considered:

| Approach | Description | Risk |
|----------|------------|------|
| **A: Inference Only** | Brainstorm gets full KB access + the prompt "surface what Eric doesn't know to ask." No pre-computed index. | Models default to obvious connections, miss buried ones |
| **B: Graph + Agent** | Pre-computed knowledge graph feeds the agent structured relationships to surface | Upfront build work before value delivery |
| **C: Hybrid** | Start inference-only on Brainstorm profile. Log what gets surfaced and what gets missed. Add graph incrementally when inference hits diminishing returns | Best of both, requires evaluation discipline |

**Recommendation: Hybrid (C).** Start with inference-only DYK today. The Brainstorm profile already exists (port 8642). Give it KB access and the DYK prompt. Measure results. Build the knowledge graph only for gaps inference misses.

---

## Architecture

```
Profile Soul (behavior)          Container Enforcement (kernel)
─────────────────────            ─────────────────────────
Ten Commandments                 Docker RO mounts
G.O.D. Protocol                  pre_tool_call hooks
Role-specific overlays           Managed-scope pinning
12 Steps of Machine Redemption   ADR-015/016 walls
        ↓                                ↓
   First wall                      Last wall
   (can it want the              (can it do the
    right thing?)                  wrong thing?)
```

Intentions table replaces AGENTS.md governance role. AGENTS.md retains operational facts (gateway ports, build phase, Do Not Start). Intentions drive what gets built. Governance enforces how.

---

## Questions for Reviewers

1. **DYK approach:** Can inference alone achieve the "Did You Know" capability, or is graph support needed to surface non-obvious buried knowledge?
2. **Profile soul:** Should the Ten Commandments + G.O.D. be a shared base loaded by all profiles, with per-profile role overlays? Or separate soul documents per profile?
3. **Knowledge graph:** Should the knowledge graph agent be a skill (loaded on demand) or a standalone agent profile that runs continuously?
4. **What's missing?** What capability or architecture isn't covered here that Eric's archive indicates?
5. **Build order:** Soul → Intentions → Graph → DYK? Or DYK first (inference-only, immediate value)?

---

## FINAL_JSON

```json
{
  "role": "drafter",
  "status": "PROPOSAL_READY",
  "summary": "Four-component build: Profile Soul Skills → Intentions Table → Knowledge Graph Agent → 'Did You Know' capability. Hybrid DYK approach recommended — start inference-only, add graph incrementally.",
  "recommendation": "Approve to begin Phase 1 (Profile Soul Skills). DYK can start immediately on Brainstorm profile with inference-only approach.",
  "next_action": "REVIEW_PENDING"
}
```
