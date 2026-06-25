#!/usr/bin/env python3
"""CIS enforcement pre_tool_call hook — blocks terminal commands matching MWL_PROOF_BLOCK_ME.

Called by Hermes for every terminal tool invocation (matcher: "terminal" in config.yaml).
Receives the tool-call JSON payload on stdin, outputs a JSON decision on stdout.

Decision shapes:
  {}                          — allow (empty JSON object = no objection)
  {"decision":"block",...}    — block the tool call
"""
import sys
import json
import datetime
import os

ART = "/workspace"


def log(name: str, line: str) -> None:
    """Best-effort append to a log file under /workspace. Silently ignores errors."""
    try:
        with open(os.path.join(ART, name), "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main() -> None:
    raw = sys.stdin.read()

    # Log the raw payload for audit/debug
    log("shellhook_payload.jsonl", raw)

    tool = ""
    cmd = ""
    try:
        data = json.loads(raw)
        tool = str(data.get("tool_name", ""))
        ti = data.get("tool_input", "")
        if isinstance(ti, dict):
            cmd = str(ti.get("command", ti.get("cmd", "")))
        else:
            cmd = str(ti)
    except Exception:
        pass

    # Log tool name for wall-proof evidence
    log(
        "shellhook_seen.log",
        datetime.datetime.now().isoformat() + " SHELLHOOK_SEEN tool=" + tool,
    )

    # Enforcement rule: block terminal commands containing the proof marker
    if tool == "terminal" and "MWL_PROOF_BLOCK_ME" in cmd:
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": "MWL_PROOF: shell hook blocked in-container",
                }
            )
        )
    else:
        # Empty JSON object = allow (no objection)
        print("{}")


if __name__ == "__main__":
    main()
