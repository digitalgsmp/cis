#!/usr/bin/env python3
"""Check OpenRouter account and find models in DeepSeek V4 Pro price range."""
import urllib.request as ur, json, os

# Read key
key = None
with open("/mnt/projects/cis/runtime/config/runtime.env") as f:
    for line in f:
        if "OPENROUTER_API_KEY" in line and "=" in line and not line.startswith("#"):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not key:
    print("No OpenRouter key found")
    exit(1)

# ── Account status ──
req = ur.Request("https://openrouter.ai/api/v1/auth/key",
    headers={"Authorization": f"Bearer {key}"})
resp = ur.urlopen(req, timeout=10)
data = json.loads(resp.read())["data"]
print(f"=== ACCOUNT ===")
print(f"Credits remaining: ${data.get('limit_remaining', 'unlimited')}")
print(f"Total usage: ${data['usage']:.4f}")
print(f"Is free tier: {data['is_free_tier']}")
print(f"Expires: {data.get('expires_at', 'none')}")

# ── Find models in DeepSeek V4 Pro price range ──
# DeepSeek V4 Pro: $0.435/M input, $0.87/M output
# Let's look for models in range: $0-$2/M output (still very cheap)
req2 = ur.Request("https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {key}"})
resp2 = ur.urlopen(req2, timeout=15)
models_data = json.loads(resp2.read())
models = models_data.get("data", [])

# Our target price ceiling: ~$2/Mtok output (about 2x DeepSeek V4 Pro)
# Filter for quality models only — skip tiny/free/deprecated
quality_families = ["deepseek", "qwen", "glm", "mistral", "gemini", "llama", "openai/gpt", "anthropic/claude", "minimax", "moonshot", "nvidia"]
target = []
for m in models:
    mid = m.get("id", "")
    pricing = m.get("pricing", {})
    prompt_p = float(pricing.get("prompt", "999"))
    compl_p = float(pricing.get("completion", "999"))
    ctx = m.get("context_length", 0)
    
    # Skip free models, deprecated, or tiny context
    if compl_p == 0 or "free" in mid.lower() or ctx < 32000:
        continue
    if compl_p > 5.0:  # Skip expensive ones
        continue
    
    # Only quality families
    if not any(f in mid.lower() for f in quality_families):
        continue
    
    target.append((compl_p, prompt_p, mid, m.get("name", ""), ctx))

target.sort()

print(f"\n=== MODELS IN DEEPSEEK V4 PRO PRICE RANGE (< $5/Mtok output) ===")
print(f"{'Output/M':>10s} {'Input/M':>10s} {'Context':>8s}  Model")
print("-" * 80)

# DeepSeek V4 Pro reference point
ref_output = 0.87
for compl_p, prompt_p, mid, name, ctx in target:
    ratio = compl_p / ref_output
    bar = "█" * min(int(ratio * 10), 30)
    print(f"${compl_p:>8.4f} ${prompt_p:>8.4f} {ctx:>7,}  {mid}")
