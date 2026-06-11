#!/bin/bash
# gate_runner.sh — Tier 1 gate sequencer
# Runs the five base gates in order, exits on first failure.
#
# Usage: gate_runner.sh
#
# Exit 0: all configured gates pass
# Exit N: exit code of the first failing gate
#
# Configuration via environment variables:
#   GATE_SERVICE_HEALTH_PORT      — port for gate_service_health.sh
#   GATE_SERVICE_HEALTH_EXPECTED  — expected substring for gate_service_health.sh
#   GATE_ENDPOINT_URL             — URL for gate_endpoint.sh
#   GATE_ENDPOINT_EXPECTED        — expected substring for gate_endpoint.sh
#   GATE_ENDPOINT_AUTH            — optional auth header for gate_endpoint.sh
#   GATE_FILE_EXISTS_PATH         — file path for gate_file_exists.sh
#   GATE_FILE_EXISTS_MINLINES     — optional min lines for gate_file_exists.sh
#
# Design constraints:
#   - Does not modify, stage, or commit files
#   - Does not restart services or call LLMs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FAILED=0

# ── Helper: run a gate and exit on failure ─────────────────────────

run_gate() {
    local name="$1"
    shift
    echo ""
    echo "━━━ GATE: ${name} ━━━"
    if "$@" 2>&1; then
        echo "   RESULT: PASS"
    else
        local rc=$?
        echo "   RESULT: FAIL (exit ${rc})"
        FAILED=$rc
        return 1
    fi
}

# ── Gate 1: Git state (always runs — dirty tree is expected to fail) ─

run_gate "gate_git_state" "${SCRIPT_DIR}/gate_git_state.sh" "$@" || exit $FAILED

# ── Gate 2: No secrets (always runs) ────────────────────────────────

run_gate "gate_no_secrets" "${SCRIPT_DIR}/gate_no_secrets.sh" || exit $FAILED

# ── Gate 3: Service health (configured via env) ─────────────────────

if [ -n "${GATE_SERVICE_HEALTH_PORT:-}" ] && [ -n "${GATE_SERVICE_HEALTH_EXPECTED:-}" ]; then
    run_gate "gate_service_health" "${SCRIPT_DIR}/gate_service_health.sh" \
        "$GATE_SERVICE_HEALTH_PORT" "$GATE_SERVICE_HEALTH_EXPECTED" || exit $FAILED
else
    echo ""
    echo "━━━ GATE: gate_service_health ━━━"
    echo "   SKIP: GATE_SERVICE_HEALTH_PORT or GATE_SERVICE_HEALTH_EXPECTED not set"
fi

# ── Gate 4: Endpoint (configured via env) ───────────────────────────

if [ -n "${GATE_ENDPOINT_URL:-}" ] && [ -n "${GATE_ENDPOINT_EXPECTED:-}" ]; then
    if [ -n "${GATE_ENDPOINT_AUTH:-}" ]; then
        run_gate "gate_endpoint" "${SCRIPT_DIR}/gate_endpoint.sh" \
            "$GATE_ENDPOINT_URL" "$GATE_ENDPOINT_EXPECTED" "$GATE_ENDPOINT_AUTH" || exit $FAILED
    else
        run_gate "gate_endpoint" "${SCRIPT_DIR}/gate_endpoint.sh" \
            "$GATE_ENDPOINT_URL" "$GATE_ENDPOINT_EXPECTED" || exit $FAILED
    fi
else
    echo ""
    echo "━━━ GATE: gate_endpoint ━━━"
    echo "   SKIP: GATE_ENDPOINT_URL or GATE_ENDPOINT_EXPECTED not set"
fi

# ── Gate 5: File exists (configured via env) ────────────────────────

if [ -n "${GATE_FILE_EXISTS_PATH:-}" ]; then
    if [ -n "${GATE_FILE_EXISTS_MINLINES:-}" ]; then
        run_gate "gate_file_exists" "${SCRIPT_DIR}/gate_file_exists.sh" \
            "$GATE_FILE_EXISTS_PATH" "$GATE_FILE_EXISTS_MINLINES" || exit $FAILED
    else
        run_gate "gate_file_exists" "${SCRIPT_DIR}/gate_file_exists.sh" \
            "$GATE_FILE_EXISTS_PATH" || exit $FAILED
    fi
else
    echo ""
    echo "━━━ GATE: gate_file_exists ━━━"
    echo "   SKIP: GATE_FILE_EXISTS_PATH not set"
fi

# ── Gate 6: Export agreement (always runs) ─────────────────────────

run_gate "gate_export_agreement" "${SCRIPT_DIR}/gate_export_agreement.sh" || exit $FAILED

# ── Gate 7: Eric approval (optional, requires workflow run ID) ───────

if [ -n "${GATE_ERIC_APPROVAL_RUN_ID:-}" ]; then
    run_gate "gate_eric_approval" python3 "${SCRIPT_DIR}/gate_eric_approval.py" \
        --workflow-run-id "$GATE_ERIC_APPROVAL_RUN_ID" || exit $FAILED
else
    echo ""
    echo "━━━ GATE: gate_eric_approval ━━━"
    echo "   SKIP: GATE_ERIC_APPROVAL_RUN_ID not set"
fi

# ── All gates passed ────────────────────────────────────────────────

echo ""
echo "All configured gates PASSED"
exit 0
