# Model Roles and Protocol — CIS Advisor Loop
Last updated: 2026-05-31 (Gate 7D verified)

## Route Table

| Label | Agent | Gateway | Port | Model | Function |
|-------|-------|---------|------|-------|----------|
| Fast | hermes-prime | NeMo → 8642 | 8800 | deepseek-v4-flash | Evidence firewall + conversational strategist |
| V4-Pro R1 | hermes-v4pro | Direct | 8645 | deepseek-v4-pro (thinking) | Proposal author, directive drafter |
| V4-Pro R2/Critic | hermes-r1 | Direct | 8643 | deepseek-v4-pro (thinking) | Adversarial reviewer, validator |
| Qwen Worker/Judge | hermes-qwen | Direct | 8644 | qwen3-vl-30b (local) | Execute FINAL_DIRECTIVE or judge JUDGE_REQUEST |

## Advisor Loop

```
User prompt
  → Fast/NeMo:8800 (evidence firewall)
     ├─ pass-through → deepseek-v4-flash:8642
     ├─ system config → local DB/port evidence
     ├─ external facts → Tavily web evidence
     └─ execution claims → FAST_EXECUTION_BLOCKED

  → V4-Pro R1:8645 (proposal drafting, receives NeMo preflight evidence)
  → V4-Pro R2:8643 (adversarial critique)
  → V4-Pro R1:8645 (final directive incorporating critique)
  → Qwen:8644 (gated — accepts only FINAL_DIRECTIVE or JUDGE_REQUEST)
```

## Architecture Principles

- **NeMo** is the behavioral/evidence firewall, not the reasoning validator.
- **V4-Pro R1/R2 adversarial loop** is the reasoning gate.
- **Qwen** is the execution/evidence gate.
- **Claude/ChatGPT** are Tier 3 escalation — pass/fail review when deliberation does not satisfy Eric.
- **Archon** remains design reference for future deterministic DAG verification.
- **DeepEval** remains deferred regression/semantic testing layer.

## Why V4-Pro is Direct (not through NeMo)

NeMo's response pipeline strips `reasoning_content` and `reasoning_tokens` from
DeepSeek thinking models (Gate 5C). V4-Pro preflight uses NeMo for evidence
collection, then calls V4-Pro direct.

## Qwen Gate Rules

Qwen accepts only:
- FINAL_DIRECTIVE — for execution (must come from reconciled V4-Pro output)
- JUDGE_REQUEST — for post-execution verification

Qwen blocks:
- Casual chat
- Proposal drafting
- Unresolved debate
- Unreconciled instructions

## Accepted Limitations

- NeMo uses semantic (embedding-based) intent matching; new query types may need manual pass-through intents
- No deterministic Archon-style verifier DAG yet
- No DeepEval regression/semantic testing yet
