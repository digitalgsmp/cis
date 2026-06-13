#!/usr/bin/env python3
"""
gate_mcp_no_network.py — Security gate: verify MCP bridge has no network imports.

Scans runtime/mcp_bridge/ for socket, http, urllib, requests, httpx, aiohttp imports.

Exit 0: PASS — no network imports found
Exit 1: FAIL — network imports found
Exit 2: ERROR — path not found
"""
import re
import sys
from pathlib import Path

BRIDGE_DIR = Path(__file__).resolve().parents[2] / "runtime" / "mcp_bridge"

NETWORK_IMPORTS = [
    "socket",
    "http",
    "urllib",
    "requests",
    "httpx",
    "aiohttp",
    "urllib3",
    "websocket",
    "asyncio\\.streams",
    "ssl",
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
        for lib in NETWORK_IMPORTS:
            pattern = r"\bimport\s+" + lib + r"\b|\bfrom\s+" + lib + r"\b"
            match = re.search(pattern, text)
            if match:
                failures.append(
                    "  {}: imports '{}'".format(py_file.name, lib))

    if failures:
        print("FAIL: Network imports found in MCP bridge:")
        for f in failures:
            print(f)
        sys.exit(1)

    print("PASS: No network imports found in MCP bridge")
    sys.exit(0)


if __name__ == "__main__":
    main()
