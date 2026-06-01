#!/usr/bin/env python3
"""
cis_verify_semantic.py — Layer 2 Semantic Verification
CIS Creative Intelligence System
ADR-033 / Addendum A — Local Model Verification via vLLM Slot 1

Usage:
    python3 cis_verify_semantic.py --manifest /tmp/last_manifest.json --file /path/to/file [--log]
    python3 cis_verify_semantic.py --probe

Exit codes:
    0 — PASS
    1 — FAIL or UNCERTAIN
    2 — Script error (bad args, file missing, vLLM unreachable)
"""

import argparse
import json
import re
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

VLLM_SLOT1_URL   = "http://127.0.0.1:8001/v1/chat/completions"
VLLM_MODEL_NAME  = "slot1-qwen3-32b"   # confirm with: curl http://127.0.0.1:8001/v1/models
VLLM_MAX_TOKENS  = 768                 # PD.5 fix: was 1024

VERIFICATION_LOG = Path("/mnt/projects/cis/logs/verification_log.md")

VALID_VERDICTS = {"PASS", "FAIL", "UNCERTAIN"}

# ── Prompts ───────────────────────────────────────────────────────────────────

LAYER2_SYSTEM_PROMPT = """\
You are a verification agent for a software build system called CIS.
Your role is to assess whether a written file is complete, non-hollow,
and free of placeholders.

You MUST respond with valid JSON only. No prose. No markdown fences.
No text before or after the JSON object.

Required schema:
{
  "verdict": "PASS" | "FAIL" | "UNCERTAIN",
  "confidence": <float 0.0–1.0>,
  "issues": [<string>, ...],
  "reasoning": "<one or two sentences>"
}

Verdict definitions:
  PASS      — file matches manifest, no placeholders, content is substantive
  FAIL      — one or more hard failures (missing file, placeholder, hollow section, contradiction)
  UNCERTAIN — no hard failures but confidence is low; human review recommended
"""

PROBE_PROMPT = """\
Respond with valid JSON only. No prose. No markdown fences.

{
  "verdict": "PASS",
  "confidence": 1.0,
  "issues": [],
  "reasoning": "Probe successful. Layer 2 verification endpoint is reachable and responding."
}
"""

def build_verification_prompt(manifest: dict, file_content: str) -> str:
    action = manifest.get("action", "[unknown action]")
    manifest_text = json.dumps(manifest, indent=2)
    return f"""\
CIS LAYER 2 VERIFICATION REQUEST
Action: {action}

COMPLETION MANIFEST:
{manifest_text}

FILE CONTENT UNDER REVIEW:
{file_content}

Assess the file against the manifest claims and respond with JSON only.
Use verdict UNCERTAIN if you cannot confidently determine pass or fail."""


# ── Think-block stripping ─────────────────────────────────────────────────────

def strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks emitted by Qwen3 before structured output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


# ── vLLM call ─────────────────────────────────────────────────────────────────

def call_vllm(system_prompt: str, user_prompt: str) -> str:
    payload = {
        "model": VLLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "max_tokens": VLLM_MAX_TOKENS,
        # temperature intentionally omitted — generation_config.json governs default
        # PD.5 fix: explicit temperature=0.0 causes 400 on some models (Opus 4.7+)
    }
    try:
        response = requests.post(VLLM_SLOT1_URL, json=payload, timeout=120)
        response.raise_for_status()
        raw = response.json()["choices"][0]["message"]["content"]
        return strip_think_blocks(raw)
    except requests.exceptions.ConnectionError:
        print(json.dumps({
            "verdict": "UNCERTAIN",
            "confidence": 0.0,
            "issues": ["vLLM Slot 1 not reachable at port 8001 — is it running?"],
            "reasoning": "Connection refused. Start Slot 1 before running verification."
        }), flush=True)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "verdict": "UNCERTAIN",
            "confidence": 0.0,
            "issues": [f"vLLM call failed: {str(e)}"],
            "reasoning": "Unexpected error during model call."
        }), flush=True)
        sys.exit(2)


# ── Response parsing ──────────────────────────────────────────────────────────

def parse_response(raw: str) -> dict:
    """Parse model JSON response. Returns structured result with verdict UNCERTAIN on parse failure."""
    cleaned = re.sub(r"```json|```", "", raw).strip()
    try:
        parsed = json.loads(cleaned)
        verdict = str(parsed.get("verdict", "")).upper()
        if verdict not in VALID_VERDICTS:
            verdict = "UNCERTAIN"
        return {
            "verdict":    verdict,
            "confidence": float(parsed.get("confidence", 0.0)),
            "issues":     list(parsed.get("issues", [])),
            "reasoning":  str(parsed.get("reasoning", "")),
            "malformed":  False,
        }
    except json.JSONDecodeError:
        return {
            "verdict":    "UNCERTAIN",
            "confidence": 0.0,
            "issues":     ["Model response was not valid JSON"],
            "reasoning":  f"Raw response: {raw[:300]}",
            "malformed":  True,
        }


# ── Verification log writer ───────────────────────────────────────────────────

def append_to_log(action: str, result: dict):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    issues_text = "\n  ".join(result["issues"]) if result["issues"] else "NONE"

    entry = f"""
────────────────────────────────────────────────────────
VERIFICATION ENTRY
Date:       {timestamp}
Action:     {action}
Layer:      LAYER-2-LOCAL
Model:      Qwen3-32B-AWQ (vLLM Slot 1 — port 8001)
Verdict:    {result["verdict"]}
Confidence: {result["confidence"]:.2f}

Issues:
  {issues_text}

Reasoning:
  {result["reasoning"]}
────────────────────────────────────────────────────────
"""
    VERIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(VERIFICATION_LOG, "a") as f:
        f.write(entry)
    print(f"[LOG] Entry appended → {VERIFICATION_LOG}", file=sys.stderr)


# ── Modes ─────────────────────────────────────────────────────────────────────

def run_probe():
    """--probe: call Slot 1 without manifest/file. Confirms endpoint is live and responding."""
    print("[PROBE] Calling vLLM Slot 1...", file=sys.stderr)
    raw = call_vllm(LAYER2_SYSTEM_PROMPT, PROBE_PROMPT)
    result = parse_response(raw)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["verdict"] == "PASS" else 1)


def run_verify(manifest_path: Path, file_path: Path, write_log: bool):
    """Standard verification mode."""
    if not manifest_path.exists():
        print(json.dumps({
            "verdict": "UNCERTAIN", "confidence": 0.0,
            "issues": [f"Manifest not found: {manifest_path}"],
            "reasoning": "Cannot verify without a manifest."
        }), flush=True)
        sys.exit(2)

    if not file_path.exists():
        print(json.dumps({
            "verdict": "UNCERTAIN", "confidence": 0.0,
            "issues": [f"File not found: {file_path}"],
            "reasoning": "Cannot verify a file that does not exist."
        }), flush=True)
        sys.exit(2)

    with open(manifest_path) as f:
        manifest = json.load(f)
    with open(file_path) as f:
        file_content = f.read()

    action = manifest.get("action", "[unknown action]")
    print(f"[LAYER-2] Action: {action}", file=sys.stderr)
    print(f"[LAYER-2] File:   {file_path}", file=sys.stderr)
    print(f"[LAYER-2] Calling vLLM Slot 1...", file=sys.stderr)

    prompt = build_verification_prompt(manifest, file_content)
    raw    = call_vllm(LAYER2_SYSTEM_PROMPT, prompt)
    result = parse_response(raw)

    print(json.dumps(result, indent=2))

    if write_log:
        append_to_log(action, result)

    sys.exit(0 if result["verdict"] == "PASS" else 1)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CIS Layer 2 Semantic Verification")
    parser.add_argument("--manifest", help="Path to completion manifest JSON")
    parser.add_argument("--file",     help="Path to file under review")
    parser.add_argument("--log",      action="store_true",
                        help="Append result to verification_log.md (off by default)")
    parser.add_argument("--probe",    action="store_true",
                        help="Probe mode: test Slot 1 connectivity without manifest/file")
    args = parser.parse_args()

    if args.probe:
        run_probe()
    elif args.manifest and args.file:
        run_verify(Path(args.manifest), Path(args.file), args.log)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
