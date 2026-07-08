#!/usr/bin/env python3
"""
gate_final_directive_allowed.py — FINAL_DIRECTIVE Enforcement (Component 3)

Blocks FINAL_DIRECTIVE emission for a workflow run unless Eric approval
provenance passes verification. This is a mandatory preflight check.

Usage:
    python3 tools/gates/gate_final_directive_allowed.py --workflow-run-id <RUN_ID>

Exit 0: PASS — FINAL_DIRECTIVE is allowed
Exit 1: FAIL — FINAL_DIRECTIVE is blocked (no valid approval)
Exit 2: ERROR — usage, config, or runtime error
"""

import argparse
import os
import subprocess
import sys

GATE_ERIC_APPROVAL = os.path.join(
    os.path.dirname(__file__), "gate_eric_approval.py"
)


def main():
    parser = argparse.ArgumentParser(
        description="FINAL_DIRECTIVE Enforcement Gate (Component 3)"
    )
    parser.add_argument(
        "--workflow-run-id", required=True,
        help="Workflow run ID to check FINAL_DIRECTIVE eligibility for",
    )
    args = parser.parse_args()

    print(f"FINAL_DIRECTIVE gate: checking approval for {args.workflow_run_id}")

    # Run the Eric approval gate — must pass all 6 checks
    result = subprocess.run(
        [sys.executable, GATE_ERIC_APPROVAL,
         "--workflow-run-id", args.workflow_run_id],
        capture_output=True, text=True, timeout=60,
    )

    if result.returncode != 0:
        print(f"BLOCKED: Eric Gate approval verification failed:")
        print(result.stderr.strip() or result.stdout.strip())
        sys.exit(1)

    print("PASS: FINAL_DIRECTIVE is allowed for this workflow run")
    sys.exit(0)


if __name__ == "__main__":
    main()
