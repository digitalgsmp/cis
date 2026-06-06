#!/bin/bash
# gate_file_exists.sh — Deterministic file existence and line count verification
# Tier 1, Artifact 1.5 — CIS Dependency Graph Build Plan v2.0
#
# Usage: gate_file_exists.sh <path> [min_lines]
#
# Exit 0: PASS — file exists and meets minimum line count (if specified)
# Exit 1: FAIL — file missing or below minimum line count
# Exit 2: ERROR — missing arguments, invalid min_lines, or other config error
#
# Design constraints:
#   - Filesystem only — no network, no git, no LLM
#   - Does not modify, stage, or commit files
#   - Does not restart services or call LLMs

set -euo pipefail

# ── Usage / argument check ─────────────────────────────────────────

if [ $# -lt 1 ]; then
    echo "Usage: gate_file_exists.sh <path> [min_lines]"
    echo ""
    echo "  path       - absolute or relative file path to verify"
    echo "  min_lines  - optional: minimum expected line count"
    exit 2
fi

FILEPATH="$1"
MIN_LINES="${2:-}"

# ── Validate min_lines if provided ─────────────────────────────────

if [ -n "$MIN_LINES" ]; then
    if ! echo "$MIN_LINES" | grep -qE '^[1-9][0-9]*$'; then
        echo "FAIL: min_lines must be a positive integer"
        echo "  got: $MIN_LINES"
        exit 2
    fi
fi

# ── Check file existence ───────────────────────────────────────────

if [ ! -f "$FILEPATH" ]; then
    echo "FAIL: file not found"
    echo "  path: $FILEPATH"
    exit 1
fi

# ── No min_lines — existence is enough ─────────────────────────────

if [ -z "$MIN_LINES" ]; then
    echo "PASS: file exists"
    echo "  path: $FILEPATH"
    exit 0
fi

# ── Line count check ───────────────────────────────────────────────

ACTUAL_LINES=$(wc -l < "$FILEPATH" | tr -d ' ')

if [ "$ACTUAL_LINES" -ge "$MIN_LINES" ]; then
    echo "PASS: file exists with ${ACTUAL_LINES} lines (min: ${MIN_LINES})"
    echo "  path: $FILEPATH"
    exit 0
fi

echo "FAIL: file has ${ACTUAL_LINES} lines, expected at least ${MIN_LINES}"
echo "  path: $FILEPATH"
exit 1
