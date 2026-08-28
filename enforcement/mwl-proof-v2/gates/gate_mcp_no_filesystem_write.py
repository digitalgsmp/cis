#!/usr/bin/env python3
"""
gate_mcp_no_filesystem_write.py — Security gate: verify MCP bridge has no
filesystem write operations.

Scans runtime/mcp_bridge/ for open('w'/'a'), write(), os.remove(), shutil, etc.

Exit 0: PASS — no filesystem write ops found
Exit 1: FAIL — filesystem write ops found
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
    (r"\bopen\s*\([^)]*['\"]w['\"]", "open() with write mode 'w'"),
    (r"\bopen\s*\([^)]*['\"]a['\"]", "open() with append mode 'a'"),
    (r"\bopen\s*\([^)]*['\"]wb['\"]", "open() with binary write mode 'wb'"),
    (r"\bos\.remove\b", "os.remove()"),
    (r"\bos\.unlink\b", "os.unlink()"),
    (r"\bos\.rename\b", "os.rename()"),
    (r"\bshutil\.(rmtree|move|copy|copytree)\b", "shutil write operation"),
    (r"\bimport\s+shutil\b", "shutil import"),
    (r"\.write_text\s*\(", "Path().write_text()"),
    (r"\.write_bytes\s*\(", "Path().write_bytes()"),
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
            match = re.search(pattern, text)
            if match:
                failures.append(
                    "  {}: {}".format(py_file.name, label))

    if failures:
        print("FAIL: Filesystem write operations found in MCP bridge:")
        for f in failures:
            print(f)
        sys.exit(1)

    print("PASS: No filesystem write operations found in MCP bridge")
    sys.exit(0)


if __name__ == "__main__":
    main()
