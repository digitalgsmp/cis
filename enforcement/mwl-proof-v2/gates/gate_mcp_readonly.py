#!/usr/bin/env python3
"""
gate_mcp_readonly.py — Security gate: verify MCP bridge has no write SQL.

Scans runtime/mcp_bridge/ for INSERT, UPDATE, DELETE, CREATE, DROP, ALTER
SQL statements. Excludes comments and docstrings describing prohibited ops.

Exit 0: PASS — no write SQL found
Exit 1: FAIL — write SQL found
Exit 2: ERROR — path not found
"""
import re
import os
import sys
from pathlib import Path

def _bridge_dir() -> Path:
    """Locate runtime/mcp_bridge without assuming where this file lives.

    Deriving the repo root from __file__ breaks whenever the gate is copied
    outside the repo: the container runs the copy at /opt/cis-gates/, two levels
    below root, so parents[2] resolved to "/" and the gate reported
    "/runtime/mcp_bridge not found" and exited 2 on every run (2026-08-26).
    CIS_REPO is the convention the other gates already use.
    """
    candidates = []
    env = os.environ.get("CIS_REPO")
    if env:
        candidates.append(Path(env))
    candidates.append(Path(__file__).resolve().parents[2])
    candidates += [Path("/workspace/cis"), Path("/mnt/projects/cis")]
    for base in candidates:
        d = base / "runtime" / "mcp_bridge"
        if d.is_dir():
            return d
    return (candidates[0] if candidates else Path(".")) / "runtime" / "mcp_bridge"


BRIDGE_DIR = _bridge_dir()

WRITE_PATTERNS = [
    (r'\.execute\s*\(\s*["\']\s*INSERT\b', "INSERT via .execute()"),
    (r'\.execute\s*\(\s*["\']\s*UPDATE\b', "UPDATE via .execute()"),
    (r'\.execute\s*\(\s*["\']\s*DELETE\b', "DELETE via .execute()"),
    (r'\.executescript\s*\(', "executescript() call (could contain writes)"),
    (r'\.execute\s*\(\s*["\']\s*CREATE\s+(TABLE|INDEX|TRIGGER|VIEW)\b', "CREATE via .execute()"),
    (r'\.execute\s*\(\s*["\']\s*DROP\b', "DROP via .execute()"),
    (r'\.execute\s*\(\s*["\']\s*ALTER\b', "ALTER via .execute()"),
]


def main():
    if not BRIDGE_DIR.is_dir():
        print(f"ERROR: Bridge directory not found: {BRIDGE_DIR}")
        sys.exit(2)

    py_files = list(BRIDGE_DIR.glob("*.py"))
    if not py_files:
        print(f"ERROR: No Python files in {BRIDGE_DIR}")
        sys.exit(2)

    failures = []
    for py_file in sorted(py_files):
        text = py_file.read_text()
        for pattern, label in WRITE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                failures.append(f"  {py_file.name}:{label}")

    if failures:
        print("FAIL: Write SQL statements found in MCP bridge:")
        for f in failures:
            print(f)
        sys.exit(1)

    print("PASS: No write SQL statements found in MCP bridge")
    sys.exit(0)


if __name__ == "__main__":
    main()
