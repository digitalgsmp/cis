#!/bin/bash
# gate_endpoint.sh — Deterministic HTTP endpoint verification
# Tier 1, Artifact 1.3 — CIS Dependency Graph Build Plan v2.0
#
# Usage: gate_endpoint.sh <url> <expected_string> [auth_header]
#
# Exit 0: PASS — response contains expected string
# Exit 1: FAIL — response does not contain expected string
# Exit 2: ERROR — missing arguments, curl unavailable, or other tool error
#
# Design constraints:
#   - No LLM in verification path
#   - Does not modify, stage, or commit files
#   - Does not restart services or call LLMs
#   - Uses curl with short timeout

set -euo pipefail

# ── Usage / argument check ─────────────────────────────────────────

if [ $# -lt 2 ]; then
    echo "Usage: gate_endpoint.sh <url> <expected_string> [auth_header]"
    echo ""
    echo "  url              - full HTTP(S) endpoint URL"
    echo "  expected_string  - substring expected in response body"
    echo "  auth_header      - optional: value passed as -H (e.g., 'Authorization: Bearer TOKEN')"
    exit 2
fi

URL="$1"
EXPECTED="$2"
AUTH_HEADER="${3:-}"
TIMEOUT="${GATE_ENDPOINT_TIMEOUT:-5}"

# ── Preflight: curl available ──────────────────────────────────────

if ! command -v curl &>/dev/null; then
    echo "FAIL: curl is not available on this system"
    exit 2
fi

# ── Validate URL format ────────────────────────────────────────────

if ! echo "$URL" | grep -qE '^https?://'; then
    echo "FAIL: url must start with http:// or https://"
    echo "  got: $URL"
    exit 2
fi

# ── Build curl arguments ───────────────────────────────────────────

CURL_ARGS=(-s --max-time "$TIMEOUT")

if [ -n "$AUTH_HEADER" ]; then
    CURL_ARGS+=(-H "$AUTH_HEADER")
fi

# ── Call endpoint ──────────────────────────────────────────────────

set +e
RESPONSE=$(curl "${CURL_ARGS[@]}" "$URL" 2>/dev/null)
CURL_EXIT=$?
set -e

if [ $CURL_EXIT -ne 0 ]; then
    echo "FAIL: endpoint unreachable — curl exit code ${CURL_EXIT}"
    echo "  url: $URL"
    exit 1
fi

if [ -z "$RESPONSE" ]; then
    echo "FAIL: endpoint returned empty response"
    echo "  url: $URL"
    exit 1
fi

# ── Check for expected string ──────────────────────────────────────

if echo "$RESPONSE" | grep -qF "$EXPECTED"; then
    echo "PASS: endpoint response contains '${EXPECTED}'"
    echo "  url: $URL"
    exit 0
fi

echo "FAIL: endpoint response does not contain '${EXPECTED}'"
echo "  url: $URL"
echo ""
echo "  Response preview (first 500 chars):"
echo "  ${RESPONSE:0:500}"
exit 1
