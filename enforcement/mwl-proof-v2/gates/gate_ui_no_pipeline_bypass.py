#!/usr/bin/env python3
"""
gate_ui_no_pipeline_bypass.py — Tier 10 security gate S2.
Scans runtime/api/pipeline_views.py for pipeline module imports.
Exit 0 = PASS (no bypass), exit 1 = FAIL (bypass imports found).
"""

import sys
import os

BLUEPRINT = "/mnt/projects/cis/runtime/api/pipeline_views.py"

FORBIDDEN = [
    "process_manager",
    "approval_gate",
    "classifier",
    "work_intent",
    "dispatch",
    "dead_letter",
]


def main():
    if not os.path.exists(BLUEPRINT):
        print(f"FAIL: {BLUEPRINT} not found")
        sys.exit(1)

    with open(BLUEPRINT) as f:
        content = f.read()

    found = []
    for mod in FORBIDDEN:
        if mod in content:
            found.append(mod)

    if found:
        print(f"FAIL: Pipeline bypass imports found: {found}")
        sys.exit(1)

    print("PASS: No pipeline bypass imports in pipeline_views.py")
    sys.exit(0)


if __name__ == "__main__":
    main()
