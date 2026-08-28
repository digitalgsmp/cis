# Deterministic Guardrail Gap

## Date: 2026-07-10
## Trigger: Eric's question — "the folder of deterministic scripts that was copied to the container is doing nothing to constrain the agents from taking short cuts"

## The Three Layers of Guardrails in the Container

### Layer 1: Container Gate Runner (FIRES on every tool call)
- **What**: `plugin/__init__.py` → `container_gate_runner.py` via subprocess
- **When**: Every `pre_tool_call` hook fires
- **Checks**: Dangerous commands (rm -rf, mkfs, dd, fork bombs, curl|sh, shutdown), secrets in content (API keys, tokens, private keys), forbidden write paths (/opt/cis-gates, /opt/cis-policy, /etc/hermes, Hermes source), MCP write tools blocked, loop guardrails (repeated identical tool calls via `tool_guardrails.py`)
- **Does NOT check**: Factual accuracy of agent claims, file path existence, code syntax, whether proposed features already exist, migration number validity

### Layer 2: The 51 Gate Scripts in /opt/cis-gates/ (DOES NOT FIRE)
- **What**: 51 `.sh`/`.py` gate scripts baked into Docker image, root-owned 0555
- **Includes**: gate_eric_approval.py, gate_db_state.py, gate_build_state_coherence.py, gate_final_directive_allowed.py, gate_deliberation.sh, gate_git_state.sh, gate_closeout_complete.sh (32KB), plus 44 more
- **Status**: DEAD CODE. Nothing invokes them. Not the pipeline_relay.py, not the container_gate_runner.py, not the plugin. They were written for the old CIS tier-based build process and copied into the container, but the pipeline has no code path that calls them.

### Layer 3: Pipeline's Own L1 Checks (FIRES only in verification, AFTER all work)
- **What**: `_run_l1_checks()` and `_run_isolated_l1()` in pipeline_relay.py
- **When**: Only in verification phase — the LAST phase, after Brain, Review, Draft, Review, Eric Gate, Pattern Catalog, and Code Review have all completed
- **Checks**: git diff --stat, git diff (full, capped at 2000 chars), changed file existence + size, untracked files. Creates a git worktree at pre-execution HEAD for isolation.
- **Does NOT check**: Code syntax (no py_compile), AST validity, test execution, claim verification, file path accuracy of agent proposals

## The 16 Failures — Breakdown by Root Cause

| Category | Count | Root Cause | Deterministic check that could have caught it |
|----------|-------|------------|-----------------------------------------------|
| Config/code bugs | 6 | execute_code approval block, intent truncation, FTS5 syntax | All fixed |
| Abandoned/stale early tests | 4 | Early portal UI tests, relay tests | N/A |
| Model failures | 2 | Reviewer returned 0 bytes (empty output) | No deterministic check — retry + degradation added |
| Correct behavior | 1 | Brain detected "nothing to do" (empty files_planned) | N/A — working as designed |
| Factual fabrication | 1 | Brain invented spec document SPEC_CONTROL_PLANE_OBSERVATION.md | `os.path.exists()` on claimed file paths |
| Same root cause repeating | 2 | SWA plan hitting unfixed bugs (before fixes applied) | Fixed in subsequent runs |
| Passed all phases | 1 | Reached ERIC_GATE | Working as designed |

**Key insight**: The only substantive failure that a deterministic check could have caught (Brain fabricating a spec document) was NOT caught by any guardrail — it was caught by Reviewer 2 (GLM) manually checking the filesystem. This is the exact problem: the LLM is doing work that deterministic scripts should do for free.

## Token Cost Analysis

- **Pipeline run cost**: ~200K tokens via OpenRouter (6+ rounds × input+output for 6 agents)
- **Eric's manual process**: 2-3 rounds (Model A reviews → Model B reviews with A's findings → maybe one revision → implement → verify)
- **Pipeline does**: 6+ rounds (Brain + Intent Review + Draft + Proposal Review + revision rounds + Code Review rounds + Verification)

### Where the extra rounds come from:

1. **Brain phase is unnecessary for clear intents** — When Eric's intent is already detailed (like the 14-component SWA plan), Brain just restates it and intent review just confirms the restatement. That's 2 rounds of tokens for zero value. Skip Brain for intents that are already specific and detailed.

2. **Draft doesn't self-verify** — Reviewer 1 caught: wrong file paths (`/workspace/cis/runtime/pipeline_relay.py` instead of `/workspace/cis/runtime/abstraction/pipeline_relay.py`), already-existing features proposed as new, wrong migration numbers. All of these could be caught by Draft itself with a simple "verify every claim against the filesystem before submitting" instruction.

3. **Parallel reviewers instead of sequential** — Eric's manual process was sequential (A reviews → B reviews with A's findings → A consensus). The pipeline uses parallel reviewers, which means both can miss the same blind spot and when they disagree there's no resolution mechanism (escalation instead).

### Optimization Options (zero-token-cost fixes):

**Option A: Skip Brain/Intent Review for clear intents.** When intent is longer than N characters and contains specific file paths or component lists, skip straight to Draft. Cuts 2 rounds.

**Option B: Merge Brain and Draft into one phase.** One agent does both: "read this intent, verify claims against the codebase, and write a proposal." Cuts 2 rounds.

**Option C: Make Draft self-verify before submission.** Add to Draft prompt: "Before submitting, verify every file path exists, every claim about existing code is checked against the actual codebase, and every migration number is the next available one." Eliminates most substantive objections, reducing proposal review to a single round.

**Option D: Use sequential reviewer protocol for intent/proposal review.** Instead of two parallel reviewers, do sequential: Reviewer A → Reviewer B sees A's findings → Reviewer A consensus. Matches the code review gate pattern and Eric's manual process.

**Option E: Wire deterministic pre-checks into pipeline_relay.py.** Before any LLM reviewer sees output, run:
- `os.path.exists()` on every file path mentioned in agent output
- `python3 -m py_compile` on any code in proposals
- `grep -r` for existing function/feature names to catch duplicate work
- `ls schema/migrations/` to verify migration numbers
Feed the results as L1 evidence to the reviewer alongside the output. Catches factual errors for zero tokens.

**Cheapest high-impact fix**: Option C (Draft self-verify) + Option D (sequential reviewers). Cuts token usage roughly in half without losing review quality. Most objections would be caught by Draft before submission, making the reviewer pass a confirmation instead of a correction.

## HASE Connection

The HASE paper (arXiv:2607.03935) proved that an optimized harness enables an 8B model to match a 120B model. The key insight: the harness (deterministic scripts, structured context, evaluation) does the verification work, not the LLM. CIS currently has the opposite — the LLM does all the verification work, and the deterministic harness scripts sit unused. Wiring deterministic pre-checks into the pipeline is the first step toward the HASE pattern: smaller, cheaper models can produce equivalent results when the harness catches factual errors deterministically.

See also: `references/harness_engineering_rsi.md` for the full RSI/HASE research mapping, `references/failure_mode_taxonomy.md` for the comprehensive 34-failure-mode taxonomy from Eric's KB words + external research, and `docs/DETERMINISTIC_GUARDRAIL_SPECIFICATION.md` in the CIS repo for the full guardrail spec with implementation priority tiers.
