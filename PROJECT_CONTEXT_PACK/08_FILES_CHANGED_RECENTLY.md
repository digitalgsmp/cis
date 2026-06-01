# Files Changed Recently
Last updated: 2026-05-31 (Gate 7 closeout)

## Gate 7A-7D — Advisor Loop Routing Overhaul

### advisor.py (runtime/api/advisor.py)
- Added `run_fast_preflight()` — NeMo preflight for V4-Pro agents
- Added `_call_gateway_with_reasoning()` — preserves reasoning_content/tokens
- Added `validate_qwen_input()` — Qwen gate (FINAL_DIRECTIVE/JUDGE_REQUEST only)
- Added `_call_qwen()` — Qwen gateway caller
- Added V4PRO_R1_ROLE, V4PRO_R2_CRITIC_ROLE, QWEN_SYSTEM_PROMPT constants
- Rewired chat() for V4-Pro preflight + Qwen gate
- Rewired parallel() call_one() for V4-Pro preflight
- Updated execute_directive() with FINAL_DIRECTIVE tagging + system prompt

### main.co (runtime/rails/configs/cis_fast/rails/main.co)
- 5 Colang intents: general question, creative question, system config, external facts, execution work
- Mixed prompt patterns (creative + current/latest keywords) for external facts
- Directive-drafting patterns (draft a directive, FINAL_DIRECTIVE) for creative intent
- Critique/review patterns (critique this directive, review this for) for creative intent
- Execution-claim patterns tuned to avoid over-blocking

### actions.py (runtime/rails/configs/cis_fast/actions.py)
- Added `block_execution_claim` action — FAST_EXECUTION_BLOCKED
- Added `pass_through_query` action — calls deepseek-v4-flash directly on 8642

### CIS_CURRENT_STATE.md
- v2.2 → v2.3
- Model Roles section rewritten with Gate 7 architecture
- Execution Order updated with Gates 7A-7D
- Active Blockers updated
- Accepted Limitations section added

### CIS_SCRATCHPAD.md
- Gate 7A-7D closeout entry with route table and file list

### HCP Files
- All 10 PROJECT_CONTEXT_PACK files updated
- All 10 PROJECT_CONTEXT_PACK_UPLOAD HCP files updated

## Previous Sessions

### Gate 6A-6C — NeMo Guardrails
- nemo-fast.service created (persistent systemd service)
- Tavily key loaded from /home/eric/.config/cis-rails.env
- 5 Colang intents, 4 actions, all tests pass

### Gate 2-5C — V4-Pro Gateway + NeMo
- V4-Pro thinking gateway on 8645 (hermes-gateway-v4pro.service)
- NeMo native guardrails on 8800 (manual → systemd)
- Hermes source patches for DeepSeek reasoning support
