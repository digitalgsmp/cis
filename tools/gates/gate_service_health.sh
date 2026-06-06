#!/bin/bash
# gate_service_health.sh — Deterministic service health verification
# Tier 1, Artifact 1.2 — CIS Dependency Graph Build Plan v2.0
#
# Usage: gate_service_health.sh <port> <expected_string>
#
# Exit 0: PASS — port returned expected string
# Exit 1: FAIL — port did not return expected string
# Exit 2: ERROR — missing arguments, curl unavailable, or other tool error
#
# Design constraints:
#   - No LLM in verification path
#   - Does not modify, stage, or commit files
#   - Does not restart services
#   - Uses curl with short timeout

set -euo pipefail

# ── Usage / argument check ─────────────────────────────────────────

if [ $# -lt 2 ]; then
    echo "Usage: gate_service_health.sh <port> <expected_string>"
    echo ""
    echo "  port             - local port number (e.g., 8645)"
    echo "  expected_string  - substring expected in /health response"
    exit 2
fi

PORT="$1"
EXPECTED="$2"
TIMEOUT="${3:-5}"

# ── Preflight: curl available ──────────────────────────────────────

if ! command -v curl &>/dev/null; then
    echo "FAIL: curl is not available on this system"
    exit 2
fi

# ── Call health endpoint ───────────────────────────────────────────

URL="http://127.0.0.1:${PORT}/health"
set +e
RESPONSE=$(curl -s --max-time "$TIMEOUT" "$URL" 2>/dev/null)
CURL_EXIT=$?
set -e

if [ $CURL_EXIT -ne 0 ]; then
    echo "FAIL: port ${PORT} unreachable (curl exit code ${CURL_EXIT})"
    exit 1
fi

if [ -z "$RESPONSE" ]; then
    echo "FAIL: port ${PORT} returned empty response"
    exit 1
fi

# ── Check for expected string ──────────────────────────────────────

if echo "$RESPONSE" | grep -qF "$EXPECTED"; then
    echo "PASS: port ${PORT} healthy — contains '${EXPECTED}'"
    exit 0
fi

echo "FAIL: port ${PORT} did not return '${EXPECTED}'"
echo ""
echo "  Response: ${RESPONSE:0:500}"
exit 1
