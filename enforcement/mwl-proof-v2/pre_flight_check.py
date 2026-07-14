#!/usr/bin/env python3
"""
Pre-flight intent validator — runs INSIDE the container before a pipeline run starts.
Checks the intent against the project's overarching goals and known constraints.
If the intent conflicts with established architecture, ADRs, or containment rules,
the run is blocked with an explanation before any API tokens are spent.

This is the "expert pushback" layer — the agents don't just execute,
they verify the intent makes sense before working on it.
"""
import sys
import os
import re

# ── CIS Overarching Goal ────────────────────────────────────────────────
PROJECT_GOAL = (
    "CIS is an expert tool to assist a non-coder to use LLMs to develop projects. "
    "CIS is the first project of CIS."
)

# ── Known Bad Patterns (things that have caused problems before) ────────
BLOCKED_PATTERNS = [
    {
        "pattern": r"docker\s+socket|docker\.sock|/var/run/docker\.sock",
        "reason": "Docker socket access breaks containment (ADR-015/016). "
                  "The worker must not have docker access.",
        "severity": "critical",
    },
    {
        "pattern": r"docker\s+group|adduser.*docker|usermod.*docker|-G\s+docker",
        "reason": "Adding worker to docker group = root escalation. "
                  "Breaks the entire enforcement model.",
        "severity": "critical",
    },
    {
        "pattern": r"sudo|chmod\s+777|chown\s+-R\s+eric",
        "reason": "Privilege escalation or overly broad permissions. "
                  "Review whether this is actually needed.",
        "severity": "high",
    },
    {
        "pattern": r"rm\s+-rf\s+/",
        "reason": "Destructive filesystem operation.",
        "severity": "critical",
    },
]

# ── Containment Principles (from ADRs) ──────────────────────────────────
CONTAINMENT_PRINCIPLES = [
    "Worker runs as non-root (UID 1000)",
    "No docker socket, no docker CLI, no docker group",
    "Managed config is root-owned, worker cannot modify",
    "Enforcement plugins are root-owned, worker cannot modify",
    "Gate scripts are root-owned, worker cannot modify",
    "Hook consent and managed scope baked into image env",
    "Container restart is a HOST operation, never available from inside",
]

def validate_intent(intent: str) -> dict:
    """
    Validate an intent before kicking to the pipeline.
    Returns: {"approved": bool, "warnings": [...], "blocks": [...]}
    """
    blocks = []
    warnings = []
    intent_lower = intent.lower()

    # Check blocked patterns
    for bp in BLOCKED_PATTERNS:
        if re.search(bp["pattern"], intent, re.IGNORECASE):
            blocks.append({
                "pattern": bp["pattern"],
                "reason": bp["reason"],
                "severity": bp["severity"],
            })

    # Check if intent contradicts containment principles
    if "docker" in intent_lower and ("mount" in intent_lower or "access" in intent_lower):
        if "docker" not in blocks:
            blocks.append({
                "reason": "Intent mentions docker access/mount. Container must not have docker access.",
                "severity": "critical",
            })

    # Check if intent is too vague for a non-trivial pipeline run
    word_count = len(intent.split())
    if word_count < 10:
        warnings.append({
            "reason": f"Intent is very short ({word_count} words). "
                      "Vague intents waste tokens on failed runs. "
                      "Consider enriching with more detail.",
            "severity": "low",
        })

    # Check if intent references swapping the entire model stack
    # (costly operation that should be carefully considered)
    model_swap_patterns = [
        r"replace.*deepseek.*with.*local",
        r"switch.*all.*models.*to.*local",
        r"free.*model.*stack",
        r"replace.*api.*with.*local",
    ]
    for pat in model_swap_patterns:
        if re.search(pat, intent, re.IGNORECASE):
            warnings.append({
                "reason": "Intent proposes swapping the model stack. "
                          "Consider: local models serialize on one GPU (24GB), "
                          "a full pipeline run would take 20-30 minutes vs 30 seconds. "
                          "The cost-killer is stopping wasted runs, not replacing the API. "
                          "Capping output tokens and adding pre-flight checks saves more.",
                "severity": "medium",
            })
            break

    approved = len(blocks) == 0
    return {
        "approved": approved,
        "blocks": blocks,
        "warnings": warnings,
        "intent_length": word_count,
    }

def format_result(result: dict) -> str:
    """Format the validation result for display."""
    if result["approved"]:
        output = "✅ INTENT APPROVED\n\n"
    else:
        output = "🚫 INTENT BLOCKED\n\n"

    if result["blocks"]:
        output += "BLOCKS (must resolve before proceeding):\n"
        for b in result["blocks"]:
            output += f"  [{b['severity'].upper()}] {b['reason']}\n"

    if result["warnings"]:
        output += "\nWARNINGS (consider before proceeding):\n"
        for w in result["warnings"]:
            output += f"  [{w['severity'].upper()}] {w['reason']}\n"

    output += f"\nIntent length: {result['intent_length']} words"
    return output

if __name__ == "__main__":
    if len(sys.argv) > 1:
        intent = " ".join(sys.argv[1:])
    else:
        intent = sys.stdin.read().strip()

    if not intent:
        print("Usage: pre_flight_check.py <intent>")
        sys.exit(1)

    result = validate_intent(intent)
    print(format_result(result))

    if not result["approved"]:
        sys.exit(2)  # Exit code 2 = blocked
    if result["warnings"]:
        sys.exit(1)  # Exit code 1 = approved with warnings
    sys.exit(0)   # Exit code 0 = clean approve
