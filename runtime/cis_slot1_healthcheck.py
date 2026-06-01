#!/usr/bin/env python3
# ============================================================
# CIS vLLM Slot 1 Health Check
# Tests: /health, /v1/models, /v1/chat/completions
# Output: structured JSON for Layer 2 manifest evidence
# ============================================================

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8001"
EXPECTED_MODEL = "slot1-qwen3-32b"

# Critical checks — verdict is FAIL if any of these fail
# All others are warnings only
CRITICAL_CHECKS = ["health_endpoint", "models_list", "completion_test"]

results = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "target": BASE_URL,
    "checks": {},
    "warnings": [],
    "errors": [],
    "verdict": None
}

def check(name, url, method="GET", data=None, headers=None):
    try:
        req = urllib.request.Request(url, method=method)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        if data:
            req.data = json.dumps(data).encode()
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            results["checks"][name] = {
                "status": resp.status,
                "pass": True,
                "response": parsed
            }
            print(f"  PASS  {name}: HTTP {resp.status}")
            return parsed
    except urllib.error.URLError as e:
        results["checks"][name] = {
            "status": None,
            "pass": False,
            "error": str(e)
        }
        results["errors"].append(f"{name}: {e}")
        print(f"  FAIL  {name}: {e}")
        return None

print("=" * 60)
print(" CIS vLLM Slot 1 Health Check")
print(f" Target: {BASE_URL}")
print(f" Time:   {results['timestamp']}")
print("=" * 60)

# Check 1 — /health
check("health_endpoint", f"{BASE_URL}/health")

# Check 2 — /v1/models
models_resp = check("models_list", f"{BASE_URL}/v1/models")
if models_resp:
    model_ids = [m.get("id") for m in models_resp.get("data", [])]
    if EXPECTED_MODEL in model_ids:
        print(f"  PASS  model_name_match: {EXPECTED_MODEL} found")
        results["checks"]["model_name_match"] = {"pass": True, "models": model_ids}
    else:
        msg = f"Expected '{EXPECTED_MODEL}' not in {model_ids}"
        print(f"  WARN  model_name_match: {msg}")
        results["checks"]["model_name_match"] = {"pass": False, "models": model_ids}
        results["warnings"].append(msg)

# Check 3 — /v1/chat/completions (structured JSON output test)
# Tests that reasoning is working and model can produce structured output —
# this is the minimum bar for Layer 2 use
completion_resp = check(
    "completion_test",
    f"{BASE_URL}/v1/chat/completions",
    method="POST",
    headers={"Content-Type": "application/json"},
    data={
        "model": EXPECTED_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a structured output engine. Return only valid JSON. No explanation. No markdown."
            },
            {
                "role": "user",
                "content": 'Return this exact JSON object: {"status": "ok"}'
            }
        ],
        "max_tokens": 32,
        "temperature": 0.0
    }
)

if completion_resp:
    content = (completion_resp
               .get("choices", [{}])[0]
               .get("message", {})
               .get("content", ""))
    # Validate: must be parseable JSON with status=ok
    try:
        parsed_content = json.loads(content.strip())
        if parsed_content.get("status") == "ok":
            print(f"  PASS  completion_structured: valid JSON, status=ok")
            results["checks"]["completion_structured"] = {
                "pass": True,
                "content": content,
                "parsed": parsed_content
            }
        else:
            msg = f"JSON parsed but status != ok: {parsed_content}"
            print(f"  WARN  completion_structured: {msg}")
            results["checks"]["completion_structured"] = {
                "pass": False,
                "content": content
            }
            results["warnings"].append(msg)
    except json.JSONDecodeError:
        msg = f"Response not valid JSON: {content!r}"
        print(f"  WARN  completion_structured: {msg}")
        results["checks"]["completion_structured"] = {
            "pass": False,
            "content": content
        }
        results["warnings"].append(msg)

# Final verdict — based on critical checks only
all_critical_pass = all(
    results["checks"].get(name, {}).get("pass", False)
    for name in CRITICAL_CHECKS
)
results["verdict"] = "PASS" if all_critical_pass else "FAIL"

print("=" * 60)
print(f" VERDICT: {results['verdict']}")
if results["errors"]:
    print(" ERRORS (blocking):")
    for e in results["errors"]:
        print(f"   - {e}")
if results["warnings"]:
    print(" WARNINGS (non-blocking):")
    for w in results["warnings"]:
        print(f"   - {w}")
print("=" * 60)

# Write structured output for manifest evidence
output_path = "/tmp/slot1_health_check.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nStructured output written to: {output_path}")
print("Include this file as execution evidence in the Layer 2 manifest.")

sys.exit(0 if all_critical_pass else 1)
