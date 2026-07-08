# SPEC — Knowledge Surface Agent

**Status:** PROPOSAL | **Date:** 2026-07-04

## The Goal

Eric described it as a "Did You Know" capability. More precisely: a system component that, given Eric's current intention or topic, proactively surfaces adjacent knowledge, technologies, approaches, patterns, and pitfalls that are buried in the knowledge base — things Eric doesn't know exist to ask about.

The question for reviewers: can this be achieved through model inference alone (give an agent access to the KB and ask "what's relevant that Eric might not know?"), or does it require a mechanism (indexing, graph traversal, pre-computed relationships)?

## What Already Exists

- FTS5 full-text search (287K messages, 19 sources)
- ChromaDB semantic search (9.3GB)
- 11,775 Drive files (source documents)
- Pipeline agents with KB access (Brainstorm, Drafter, Reviewers)
- Brainstorm role: explores intentions broadly, challenges assumptions, finds better approaches

## Proposed Approaches

### Approach A: Inference-Only (Brainstorm Enhancement)

Give Brainstorm the KB and this instruction: "Eric is working on X. Search the knowledge base for anything relevant he might not know to ask about — technologies, patterns, approaches, pitfalls from past sessions, related projects, adjacent concepts. Surface what you find with source links."

Why it might work: models already do this when shown a problem and asked "what else should I know?" The KB is Eric's own corpus — his words, his projects, his patterns. A model with access can find connections a human forgot.

Why it might fail: models default to what's statistically probable, not what's novel. Without explicit direction to search broadly, they stay narrow. They might surface the obvious rather than the buried.

### Approach B: Mechanism-Assisted (Graph + Agent)

Build a lightweight knowledge graph that agents continuously update. Each session, agents mine the KB for connections and add edges between documents, concepts, and intentions. The graph provides a pre-computed map that makes novel surfacing more likely.

Agent instruction: "Traverse the knowledge graph from this intention node. Follow edges to related concepts that aren't obviously connected. Surface what you find."

Why it might work: pre-computed relationships mean the agent doesn't have to discover everything from scratch each time. The graph accumulates over sessions. A buried connection from three months ago is still there.

Why it might fail: building the graph is upfront work. The graph might encode biases from whoever built it. It could become another maintenance burden.

### Approach C: Hybrid (Inference with Graph Assistance)

Start with Approach A — inference-only via Brainstorm. Track what gets surfaced and what gets missed. If inference alone isn't finding buried connections, add lightweight graph support as a skill loaded by agents, not a standalone system. The graph builds incrementally from what agents discover, not from a pre-processing pipeline.

## Questions for Reviewers

1. Can inference alone (Approach A) achieve the "Did You Know" goal with the existing KB infrastructure? Has this already been demonstrated in prior sessions?

2. If not, is Approach C (hybrid) the right path — start inference-only, add graph support only if needed?

3. What failure modes should we watch for? (surfacing the obvious, missing buried connections, hallucinating connections that don't exist)

4. Does this replace Brainstorm as a separate role, or enhance Brainstorm's existing function?
