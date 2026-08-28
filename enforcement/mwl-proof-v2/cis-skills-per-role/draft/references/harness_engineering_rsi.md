# Harness Engineering and Recursive Self-Improvement

## Sources

- Lilian Weng, "Harness Engineering for Self-Improvement" (July 4, 2026)
  https://lilianweng.github.io/posts/2026-07-04-harness/
- HASE: "Harness-Aware Self-Evolving: Co-Evolving Model Weights, Harness, and Task Solutions"
  arXiv:2607.03935 (Haochen Luo et al., HKU/Jiutian/Grace Investment, July 2026)
- YouTube: "8B w/ LLM RL + Harness Tuning BEATS 120B AI (RSI)" by Discover AI
  https://www.youtube.com/watch?v=6Vw-Ffq6hRQ

## The RSI Roadmap

Weng outlines the progression of optimization targets:

  instruction prompts → structured context → workflow → harness code → optimizer code

RSI (Recursive Self-Improvement) is the feedback loop where AI uses its current
intelligence to improve the cognitive machinery that produces its intelligence.
Near-term RSI starts with the harness, not with model weights.

## What a Harness Is

"A harness is the system surrounding a base model that orchestrates execution
and decides how the model thinks and plans, calls tools and acts, perceives and
manages context, stores artifacts, and evaluates results."

This is broader than an "agent framework." It includes:
- Workflow design (loop engineering)
- Evaluation
- Permission controls
- Persistent state management

## Three Design Patterns (Weng)

1. **Workflow Automation** — goal-oriented loop: plan → execute → observe/test → improve → iterate until goal achieved. Proactive requests to users for clarity.

2. **File System as Persistent Memory** — don't carry everything in context. Durable state on disk: experiment logs, code diffs, summaries, error traces, past trajectories. "Leave receipts" discipline.

3. **Sub-agent and Backend Jobs** — parallel workers, explicit and inspectable. Outputs land as files and logs. Recoverable after interruptions.

## HASE: Co-Evolving Model + Harness + Solutions

Key result: a single Qwen3-8B model (via HASE) matches GPT-OSS-120B performance.
Small model + optimized harness = big model performance.

Three components co-evolved simultaneously:
1. Model weights
2. Harness (surrounding infrastructure/tooling)
3. Task solutions

Self-repair: HASE can identify and repair imperfect evaluation components
within the harness itself.

## How CIS Maps to the RSI Roadmap

CIS IS a harness. The pipeline relay, 6 agents, deliberation protocol, code
review gate, verification step, spine — all harness code.

- **Workflow Automation (Pattern 1)**: The pipeline is a goal-oriented loop.
  Brain → Review → Draft → Review → Eric Gate → Menter → Verify.
- **File System as Persistent Memory (Pattern 2)**: The SQLite spine stores
  all trajectories, deliberation rounds, gate approvals, code review chunks.
  Pre-discovery retrieves prior trajectories before each agent runs.
- **Sub-agent and Backend Jobs (Pattern 3)**: 6 gateway agents in parallel,
  each with isolated HERMES_HOME. Reviewers run in parallel via asyncio.gather.

### Where CIS sits on the RSI roadmap

CIS is at **harness code** optimization. The pipeline code itself is being
iteratively improved based on observed failures (retry logic, single-reviewer
degradation, feedback injection, execute_code guard fix). This is manual
harness engineering — the optimization is done by Eric + the verifier agent
analyzing failures and patching the harness.

### Next step on the roadmap: Self-Improving Harness

After each pipeline run, the system should:
1. Evaluate what worked and what failed (already have this data in the spine)
2. Propose harness improvements based on the evidence
3. Test the improvements against held-out runs
4. Accept or reject changes based on measured performance

This is the STOP (Self-Taught Optimizer) and Self-Harness pattern. The
pipeline already has the data for this — every run's trajectories, objections,
and outcomes are in the spine. The missing piece is the meta-loop: a harness
improvement agent that reads failure patterns and proposes fixes.

## Key Research Papers Referenced

- **ACE** (Agentic Context Engineering) — context as evolving playbook, structured bullets with IDs, deterministic merge logic
- **MCE** (Meta Context Engineering) — bi-level optimization: skill evolution (meta) + context optimization (base)
- **Meta-Harness** — harness for optimizing harnesses; proposer is a coding agent
- **STOP** (Self-Taught Optimizer) — recursively improves its own scaffolding. Key caveat: improved on GPT-4, degraded on weaker models. Recursion needs a strong base.
- **Self-Harness** — propose-evaluate-accept loop for harness self-improvement. Model-specific instructions targeting different weaknesses.
- **ADAS** — meta-agent programs new agent workflows in code, keeps archive
- **AFlow** — workflow as graph, MCTS search
- **AlphaEvolve** — evolutionary pool of candidate programs, EVOLVE-BLOCK markers
- **Darwin Gödel Machine** — agents rewrite their own harness codebase, matches handcrafted agents on SWE-bench
- **SIA** — combines harness improvement + model weight updates (early, provisional evidence)

## Seven Challenges for Full RSI (Weng)

1. Weak/fuzzy evaluators — many tasks lack fast, precise verifiers
2. Context and memory lifecycle — memory grows, needs management
3. Negative results — models bad at admitting failure, biased toward success
4. Diversity collapse — evolutionary loops exploit known patterns, lose diversity
5. Reward hacking — loops optimize whatever signal given, may cheat
6. Long-term success — short-term metrics miss maintainability, migration cost
7. Role of humans — humans should move up the stack, not be removed

**Key design rule**: The evaluator and permission control should sit OUTSIDE
the loop that evolves the harness. Held-out tests, trace audits, human review
at decision points. Otherwise the agent optimizes the referee instead of the
game.

This maps directly to CIS: the pipeline's adversarial review (Review1/Review2
check Brain and Menter) is the evaluator. Eric Gate is the human checkpoint.
The mwl-proof plugin and container isolation are the permission controls.
All sit outside the harness optimization loop — the agents can't modify them.

## Critical Gap Found (2026-07-10): Deterministic Harness Scripts Are Dead Code

Eric's direct question: "the folder of deterministic scripts that was copied
to the container is doing nothing to constrain the agents from taking short
cuts." He was right.

The 51 gate scripts are baked into the container image but NOTHING calls them
during pipeline runs. The pipeline relies 100% on LLM judgment for factual
accuracy — exactly the opposite of what HASE prescribes. The harness should
do the verification, not the LLM.

**Concrete impact**: ~200K tokens per pipeline run via OpenRouter, vs Eric's
manual 2-3 round process. The extra rounds come from LLMs catching errors
that deterministic scripts could catch for free (wrong file paths, fabricated
documents, already-existing features proposed as new).

**HASE's key result**: 8B model + optimized harness = 120B model performance.
CIS's current state: large models + unoptimized harness = expensive runs.
The path to cheaper local models runs through wiring deterministic pre-checks
into the pipeline, not through bigger models.

See [Deterministic Guardrail Gap](deterministic_guardrail_gap.md) for the
full three-layer analysis, 16-failure breakdown, and five optimization
strategies.
