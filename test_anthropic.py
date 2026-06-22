#!/usr/bin/env python3
"""Test Anthropic API key with Claude Opus 4.8."""
import urllib.request as ur
import urllib.error as ue
import json
import os

# Read key from env file
key = None
with open("/mnt/projects/cis/runtime/config/runtime.env") as f:
    for line in f:
        if line.startswith("export ANTHROPIC_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not key:
    print("FAIL: key not found in runtime.env")
    exit(1)

print(f"Key loaded: {len(key)} chars, starts with {key[:18]}...")

# Test Claude Opus 4.8
for model_id in ["claude-opus-4-8", "claude-opus-4-20250514"]:
    body = json.dumps({
        "model": model_id,
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "What model and version are you? Who made you? One sentence."}]
    }).encode()
    req = ur.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        })
    try:
        resp = ur.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        actual_model = data.get("model", "?")
        content = ""
        has_thinking = False
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
            if block.get("type") == "thinking":
                has_thinking = True
        usage = data.get("usage", {})
        print(f"\n  Model: {actual_model}")
        print(f"  Extended thinking: {has_thinking}")
        print(f"  Tokens: in={usage.get('input_tokens','?')} out={usage.get('output_tokens','?')}")
        print(f"  Response: {content[:300]}")
        break  # first one worked
    except ue.HTTPError as e:
        err = e.read().decode()[:400]
        print(f"  [{model_id}] HTTP {e.code}: {err}")
    except Exception as e:
        print(f"  [{model_id}] FAIL: {e}")
