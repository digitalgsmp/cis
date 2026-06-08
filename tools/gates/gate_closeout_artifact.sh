#!/bin/bash
# gate_closeout_artifact.sh — Tier 6.5 Closeout Artifact Verification Gate
# Verifies the closeout markdown file exists and contains required sections.
#
# Usage: gate_closeout_artifact.sh --closeout-file <path>
#
# Exit codes:
#   0  PASS — file exists with all required sections
#   1  FAIL — file missing or missing one or more required sections
#   2  ERROR — missing --closeout-file argument
#
# Required sections:
#   1. "State Write" or "STATE_WRITE"  (heading or content line)
#   2. "Tier 6.4 Markers"             (heading)
#   3. "Gate Verification"            (heading with PASS/FAIL/SKIP summary)
#   4. "Export" or "Git Status"       (heading)
#   5. "## Commit"                    (heading)
#   6. "HEAD:"                        (line with hex commit hash)
#
set -euo pipefail

# ── Parse CLI ────────────────────────────────────────────────────────

CLOSEOUT_FILE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --closeout-file)
            CLOSEOUT_FILE="$2"; shift 2 ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Usage: gate_closeout_artifact.sh --closeout-file <path>" >&2
            exit 2
            ;;
    esac
done

if [ -z "$CLOSEOUT_FILE" ]; then
    echo "FAIL: --closeout-file is required"
    exit 2
fi

# ── Check file exists ────────────────────────────────────────────────

if [ ! -f "$CLOSEOUT_FILE" ]; then
    echo "FAIL: closeout artifact not found: $CLOSEOUT_FILE"
    exit 1
fi

# ── Read file content ────────────────────────────────────────────────

CONTENT=$(cat "$CLOSEOUT_FILE")
FAILURES=0

# ── Check 1: "State Write" or "STATE_WRITE" ──────────────────────────

if echo "$CONTENT" | grep -qi "state.write\|STATE_WRITE"; then
    echo "PASS: State Write section found"
else
    echo "FAIL: missing State Write / STATE_WRITE section"
    FAILURES=$((FAILURES + 1))
fi

# ── Check 2: "Tier 6.4 Markers" heading ──────────────────────────────

if echo "$CONTENT" | grep -q "Tier 6.4 Markers"; then
    echo "PASS: Tier 6.4 Markers section found"
else
    echo "FAIL: missing Tier 6.4 Markers section"
    FAILURES=$((FAILURES + 1))
fi

# ── Check 3: "Gate Verification" heading with PASS/FAIL/SKIP summary ─

if echo "$CONTENT" | grep -q "Gate Verification"; then
    # Must contain at least one of PASS, FAIL, or SKIP
    if echo "$CONTENT" | grep -qE "PASS|FAIL|SKIP"; then
        echo "PASS: Gate Verification section found with status summary"
    else
        echo "FAIL: Gate Verification section missing status summary (PASS/FAIL/SKIP)"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo "FAIL: missing Gate Verification section"
    FAILURES=$((FAILURES + 1))
fi

# ── Check 4: "Export" or "Git Status" heading ────────────────────────

if echo "$CONTENT" | grep -qE "Export|Git Status"; then
    echo "PASS: Export / Git Status section found"
else
    echo "FAIL: missing Export / Git Status section"
    FAILURES=$((FAILURES + 1))
fi

# ── Check 5: "## Commit" heading ─────────────────────────────────────

if echo "$CONTENT" | grep -q "## Commit"; then
    echo "PASS: ## Commit section found"
else
    echo "FAIL: missing ## Commit section"
    FAILURES=$((FAILURES + 1))
fi

# ── Check 6: "HEAD:" with hex commit hash ─────────────────────────────

if echo "$CONTENT" | grep -qE "HEAD: [0-9a-f]{7,}"; then
    echo "PASS: Commit hash found (HEAD: <hash>)"
else
    echo "FAIL: missing or invalid commit hash (expected HEAD: <7+ hex chars>)"
    FAILURES=$((FAILURES + 1))
fi

# ── Final verdict ─────────────────────────────────────────────────────

if [ "$FAILURES" -eq 0 ]; then
    echo ""
    echo "PASS: all 6 required sections verified in $CLOSEOUT_FILE"
    exit 0
else
    echo ""
    echo "FAIL: $FAILURES section(s) missing from $CLOSEOUT_FILE"
    exit 1
fi
