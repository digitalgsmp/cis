# Terms and Naming — CIS Advisor Loop
Last updated: 2026-05-31 (Gate 7)

## Agents

| Name | Label | Purpose |
|------|-------|---------|
| hermes-prime | Fast | Evidence firewall (NeMo) + conversational strategist |
| hermes-v4pro | V4-Pro R1 | Proposal author, directive drafter |
| hermes-r1 | V4-Pro R2/Critic | Adversarial reviewer, validator |
| hermes-qwen | Qwen Worker/Judge | Execution and post-execution verification |

## Gateway Architecture

| Gateway | Port | Path | Notes |
|---------|------|------|-------|
| NeMo Guardrails | 8800 | NeMo native, nemo-fast.service | Evidence firewall for Fast only |
| Fast (hermes-prime) | 8642 | behind NeMo, not direct | Pass-through from NeMo on 8800 |
| V4-Pro R1 (hermes-v4pro) | 8645 | direct | Thinking model, reasoning preserved |
| V4-Pro R2 (hermes-r1) | 8643 | direct | Thinking model, reasoning preserved |
| Qwen (hermes-qwen) | 8644 | direct, gated | FINAL_DIRECTIVE or JUDGE_REQUEST only |

## Key Terms

- **NeMo / NeMo Guardrails**: NVIDIA's guardrail framework running natively on 8800.
  Provides evidence firewall for Fast: local routing, Tavily web search, execution blocking.
- **Preflight**: advisor.py sends user prompt to NeMo before calling V4-Pro.
  If NeMo returns evidence, it's injected as a system message.
- **FINAL_DIRECTIVE**: The only format Qwen accepts for execution. Must come from
  reconciled V4-Pro output.
- **JUDGE_REQUEST**: Format Qwen accepts for post-execution verification.
- **FAST_EXECUTION_BLOCKED**: Response when Fast or V4-Pro preflight detects an
  execution/completion claim.
- **QWEN_GATE_BLOCKED**: Response when Qwen receives non-directive/non-judge input.
- **reasoning_content / reasoning_tokens**: DeepSeek V4 thinking model metadata,
  preserved by V4-Pro direct routing (stripped by NeMo).
- **Colang**: NeMo's flow definition language for guardrails.
- **Tavily**: Web search API used for current external facts.
- **Archon**: Design reference for future deterministic DAG verification.
- **DeepEval**: Deferred regression/semantic testing layer.
