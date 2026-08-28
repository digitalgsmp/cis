# Local GLM-4.7-Flash for Drift Detection

## Model
- GLM-4.7-Flash (Q4_K_M quantization)
- Runs via llama-server on `localhost:8002`
- OpenAI-compatible API at `/v1/chat/completions`
- 94 tok/s, ~5 seconds per drift check
- Replaced Qwen3-VL-30B-A3B (4x faster)

## CRITICAL: Reasoning Model Token Pitfall

GLM-4.7-Flash is a **reasoning model**. It produces two fields:
1. `reasoning_content` — internal chain-of-thought (not the answer)
2. `content` — the actual answer (JSON, text, etc.)

Both consume from the same `max_tokens` budget.

| max_tokens | reasoning_content | content | Result |
|------------|-------------------|---------|--------|
| 200 | ~200 tokens (incomplete) | `""` empty | **Appears broken** |
| 500 | ~450 tokens (incomplete) | `""` empty | Still no output |
| 1000 | ~400 tokens (complete) | JSON answer | **Works correctly** |

**Fix**: Set `max_tokens: 1000` minimum for any drift comparison call.

## API Call Pattern

```python
import httpx

response = httpx.post(
    "http://localhost:8002/v1/chat/completions",
    json={
        "model": "glm-4.7-flash",
        "messages": [
            {
                "role": "system",
                "content": "Compare the intent against the output. Score alignment 1-10. Respond ONLY with JSON: {\"score\": <int>, \"reason\": \"<one sentence>\"}"
            },
            {
                "role": "user",
                "content": f"INTENT:\n{intent}\n\nOUTPUT:\n{output}"
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.3
    },
    timeout=30.0
)

data = response.json()
# The actual answer is in content, not reasoning_content
answer = data["choices"][0]["message"]["content"]  # {"score": 10, "reason": "..."}
```

## Drift Detection Architecture

Two-tier scoring:
1. **Deterministic** (instant, zero cost): keyword overlap (40%), scope expansion (30%), action alignment (30%)
2. **Semantic** (~5 seconds, local GLM): only fires when deterministic score is ambiguous (0.15–0.65 range)

Combined score: 40% deterministic + 60% semantic

### Verdicts
| Score Range | Verdict | UI Color |
|------------|---------|----------|
| 0.0–0.15 | ALIGNED | Green |
| 0.15–0.35 | MINOR_DRIFT | Orange |
| 0.35–0.65 | SIGNIFICANT_DRIFT | Amber |
| 0.65+ | DIVERGED | Red |

## Local vs Full Model Division of Labor

| Task | Model | Why |
|------|-------|-----|
| Per-phase drift scoring | Local GLM-4.7-Flash | Frequent, cheap, comparison task |
| Verify phase gate | Full GLM-5.2 (OpenRouter) | High-stakes, complex code review |
| Eric escalation reviews | Full GLM-5.2 | Edge cases, subtle misalignment |
| KB retrieval ranking | Local GLM | Frequent, classification |
| Interjection classification | Local GLM | Frequent, classification |

**Pattern**: Local model does comparison/classification (cheap, frequent). Full model does generation and complex verification (expensive, high-stakes).

## Candidate Use Cases (Not Yet Built)

1. **KB retrieval ranking** — score KB chunks for relevance before injection
2. **Interjection classification** — classify backchannel messages (correction/question/direction)
3. **Guardrail explanations** — plain-language explanation when guardrail fires
4. **Loop-breaker detection** — semantic comparison of tool call patterns
5. **Deliberation compression** — summarize prior rounds before passing to next phase
6. **Intent clarification flag** — check Brain chat for ambiguity before locking intent

## Session
2026-07-12: GLM tested for drift detection. Token pitfall discovered and resolved. Local-vs-full model comparison established. Supporting agent use cases identified.
