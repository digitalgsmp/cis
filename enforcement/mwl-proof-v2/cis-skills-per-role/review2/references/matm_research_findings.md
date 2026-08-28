# MATM Research Findings — How Papers Map to CIS

## Paper 1: MATM (arXiv 2606.19911, CMU/UC Berkeley)

**Multi-Agent Transactive Memory** — shared repository where producer agents contribute trajectories, consumer agents retrieve them.

### Key Concepts → CIS Mapping

| MATM Concept | CIS Implementation |
|---|---|
| Shared trajectory repository | Spine DB (`cis_memory.db`) + ChromaDB |
| Producer agents contribute trajectories | Each agent writes output + reasoning to `agent_trajectories` table |
| Consumer agents retrieve trajectories | Before starting work, agent queries KB for similar prior trajectories |
| State-conditioned key-value indexing | Key = recent interaction history, Value = next steps from prior trajectory |
| LTRT reranker (SVMRank) | Rank retrieved trajectories by marginal utility — "did this actually help?" |
| RetrievalPlanner decides when to retrieve | Not every step needs retrieval; agent decides "I'm stuck, check if someone solved this" |

### Key Distinction from RAG
RAG retrieves human-authored documents for agents. MATM retrieves **agent-generated trajectories** — "atypical documents that differ fundamentally from human-written text." The CIS KB should support both: document search (existing `knowledge_messages`) and trajectory search (new `agent_trajectories`).

### Indexing Scheme
- Window size l=5 action-observation steps
- Key = f(x, τ_{t-l+1}, ..., τ_t) — recent history embedding
- Value = next l steps (τ_t, ..., τ_{t+l-1}) — what the agent did next
- Embedding: E5-Base

### Results
- ALFWorld: +8% success rate, -0.59 steps
- With SVMRank reranker: +17.2% success rate
- Benefits distributed across population — weak and strong agents both benefit
- Benefits do NOT require joint training or coordination

---

## Paper 2: Self-Evolving Agents (arXiv 2507.21046, Ant Group/HKUST/Tsinghua)

### Key Concepts → CIS Mapping

| Paper Concept | CIS Implementation |
|---|---|
| Agent = composite policy (LLM + harness + memory + tools + guardrails) | Each Hermes profile = base model + personality prompt + MCP tools + container gates |
| Data proxy captures ATDP trajectories | Docker container IS the data proxy; every tool call recorded |
| Evolution control plane | The pipeline relay decides when agent behavior changes |
| Different failures → different intervention surfaces | Brain misunderstanding → fix prompt. Draft overproduces → fix constraints. Menter shortcuts → tighten gates. |

### Formal Framework
- Agent system: Π = (Γ, {ψ}, {C}, {W}) where Γ=architecture, ψ=LLM, C=context/memory, W=tools
- Self-evolving strategy: f(Π, τ, r) = Π' — transform based on trajectory τ and feedback r

### Three Inclusion Criteria for Self-Evolution
1. Experience-dependent updates (not generic data synthesis)
2. Persistent, policy-changing effects (not transient instruction-following)
3. Autonomous exploration or self-initiated learning

### What Evolves
- **Models**: policy evolution, experience evolution
- **Context**: memory evolution (add/merge/update/delete), prompt optimization
- **Tools**: autonomous discovery, iterative refinement, scalable management
- **Architecture**: single-agent optimization, multi-agent workflow optimization

---

## Paper 3: EvoAgentX (EMNLP'25, 3.1k GitHub stars)

### Relevant Patterns
- **HITL layer**: `approval_manager.py` — human approval gates between workflow steps
- **Interceptor agent**: sits between steps, can block/redirect the workflow
- **Message passing**: agents pass Message objects with `next_actions` field — the message declares where it goes next
- **Workflow as DAG**: directed acyclic graph, not linear loop. Branching built into topology
- **Five layers**: basic components, agent, workflow, evolving, evaluation

---

## Paper 4: AgentWorkforce Relay Workflows

### Relevant Patterns
- **"Workflows repair before they fail"**: don't stop at red gate. Capture failure, route to repair agent, continue
- **Review-depth tiers**: light/standard/deep — each adds more fresh-eyes review passes
- **Human assistance**: agents print `HUMAN_QUESTION:` — workflow blocks, posts to Slack/Telegram, injects reply
- **Repairable validation gates**: `failOnError: false` for intermediate gates; pass output to repair agent

---

## Paper 5: Verifier Pattern (MindStudio)

### Critical Rule
The verifier must have **NO shared context** with the generator:
- No shared memory
- No shared reasoning chain
- No shared system prompt or session history
- Verifier sees only: spec + evidence (git diff, test output, file listing)

This is why CIS has a separate model (GLM-5.2 on port 8648) for Verify — different training data + isolated context prevents shared blind spots.
