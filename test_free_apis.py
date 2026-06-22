#!/usr/bin/env python3
"""Test free LLM APIs for CIS portal integration."""
import urllib.request as ur, json, subprocess, sys

# Get GitHub token from gh CLI
gh_token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

results = {}

# ── 1. GitHub Models ──────────────────────────────────────────
print("=== 1. GITHUB MODELS ===")
try:
    # List models
    req = ur.Request("https://models.inference.ai.azure.com/models",
        headers={"Authorization": f"Bearer {gh_token}"})
    resp = ur.urlopen(req, timeout=10)
    models = json.loads(resp.read())
    free_interesting = []
    for m in models:
        name = m.get("name", "")
        if any(x in name for x in ["gpt-5", "gpt-4", "claude", "llama", "deepseek", "mistral", "gemini"]):
            free_interesting.append(name)
    print(f"  Available models: {len(models)} total, interesting: {free_interesting[:15]}")
    
    # Test a chat completion
    body = json.dumps({
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": "What organization built you? One sentence."}],
        "max_tokens": 60
    }).encode()
    req2 = ur.Request("https://models.inference.ai.azure.com/chat/completions", data=body,
        headers={"Authorization": f"Bearer {gh_token}", "Content-Type": "application/json"})
    resp2 = ur.urlopen(req2, timeout=30)
    data = json.loads(resp2.read())
    c = data.get("choices", [{}])[0].get("message", {}).get("content", "")[:150]
    print(f"  Test (gpt-4.1-mini): {c}")
    results["github"] = "OK"
except Exception as e:
    print(f"  FAIL: {e}")
    results["github"] = str(e)[:100]

# ── 2. Groq (test with free tier) ─────────────────────────────
print("\n=== 2. GROQ ===")
# Groq has a free tier but needs a key. Check if we have one.
groq_key = None
for path in ["/mnt/projects/cis/runtime/config/runtime.env", "/home/eric/.env", "/home/eric/.bashrc"]:
    try:
        with open(path) as f:
            for line in f:
                if "GROQ_API_KEY" in line and "=" in line:
                    groq_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except: pass
if groq_key:
    print(f"  Key found ({len(groq_key)} chars)")
    try:
        body = json.dumps({
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "What org built you? One sentence."}],
            "max_tokens": 60
        }).encode()
        req = ur.Request("https://api.groq.com/openai/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"})
        resp = ur.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        c = data.get("choices", [{}])[0].get("message", {}).get("content", "")[:150]
        print(f"  Test (llama-3.3-70b): {c}")
        results["groq"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["groq"] = str(e)[:100]
else:
    print("  No key found. Get free key at: https://console.groq.com/keys")
    results["groq"] = "no key"

# ── 3. Google AI Studio (Gemini) ──────────────────────────────
print("\n=== 3. GOOGLE AI STUDIO (Gemini) ===")
gemini_key = None
for path in ["/mnt/projects/cis/runtime/config/runtime.env", "/home/eric/.env"]:
    try:
        with open(path) as f:
            for line in f:
                if "GEMINI_API_KEY" in line and "=" in line:
                    gemini_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except: pass
if gemini_key:
    print(f"  Key found ({len(gemini_key)} chars)")
    try:
        body = json.dumps({
            "contents": [{"parts": [{"text": "What org built you? One sentence."}]}]
        }).encode()
        req = ur.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
            data=body, headers={"Content-Type": "application/json"})
        resp = ur.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        c = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")[:150]
        print(f"  Test (gemini-2.5-flash): {c}")
        results["gemini"] = "OK"
    except Exception as e:
        print(f"  FAIL: {e}")
        results["gemini"] = str(e)[:100]
else:
    print("  No key found. Get free key at: https://aistudio.google.com/apikey")
    results["gemini"] = "no key"

# ── 4. Mistral AI ─────────────────────────────────────────────
print("\n=== 4. MISTRAL AI ===")
mistral_key = None
for path in ["/mnt/projects/cis/runtime/config/runtime.env", "/home/eric/.env"]:
    try:
        with open(path) as f:
            for line in f:
                if "MISTRAL_API_KEY" in line and "=" in line:
                    mistral_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except: pass
if mistral_key:
    print(f"  Key found ({len(mistral_key)} chars)")
else:
    print("  No key found. Get free key at: https://console.mistral.ai/api-keys/")
    results["mistral"] = "no key"

# ── Summary ───────────────────────────────────────────────────
print("\n=== SUMMARY ===")
for k, v in results.items():
    status = "✅" if v == "OK" else "❌" if v == "no key" else "⚠️"
    print(f"  {status} {k}: {v}")
