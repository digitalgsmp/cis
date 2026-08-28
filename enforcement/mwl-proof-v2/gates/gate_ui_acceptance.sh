#!/usr/bin/env bash
# gate_ui_acceptance.sh — Tier 10 functional acceptance tests A1-A10.
# Runs the unit, security, and integration test suites.
# Exit 0 = all pass, exit 1 = failures.

set -euo pipefail

echo "=== Tier 10 Acceptance Tests ==="
echo ""

TESTS_DIR="${CIS_REPO:-/mnt/projects/cis}/tests/ui"
PROJECT_ROOT="${CIS_REPO:-/mnt/projects/cis}"
FAILURES=0

# ── A1-A8: Unit tests (endpoint existence, security) ─────────────────────

PYTHON=/home/eric/.hermes/hermes-agent/venv/bin/python3

echo "--- Test Suite: Pipeline Views Unit Tests ---"
if $PYTHON -m pytest "$TESTS_DIR/test_pipeline_views.py" -v --tb=short 2>&1; then
    echo "A1-A8: PASS (pipeline views unit tests)"
else
    echo "A1-A8: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── S1-S3: Security tests ────────────────────────────────────────────────

echo "--- Test Suite: UI Security Tests ---"
if $PYTHON -m pytest "$TESTS_DIR/test_ui_security.py" -v --tb=short 2>&1; then
    echo "S1-S3: PASS (security tests)"
else
    echo "S1-S3: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── I1-I5: Integration tests ────────────────────────────────────────────

echo "--- Test Suite: UI Integration Tests ---"
if $PYTHON -m pytest "$TESTS_DIR/test_ui_integration.py" -v --tb=short 2>&1; then
    echo "I1-I5: PASS (integration tests)"
else
    echo "I1-I5: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── A9: No write endpoints (gate script) ─────────────────────────────────

echo "--- Gate: No Write Endpoints ---"
if bash "$PROJECT_ROOT/tools/gates/gate_ui_no_write_endpoints.sh" 2>&1; then
    echo "A9: PASS"
else
    echo "A9: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── S2: No pipeline bypass (gate script) ─────────────────────────────────

echo "--- Gate: No Pipeline Bypass ---"
if python3 "$PROJECT_ROOT/tools/gates/gate_ui_no_pipeline_bypass.py" 2>&1; then
    echo "S2 (gate): PASS"
else
    echo "S2 (gate): FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── S3: No secrets in JSX (gate script) ──────────────────────────────────

echo "--- Gate: No Secrets in JSX ---"
if bash "$PROJECT_ROOT/tools/gates/gate_ui_no_secrets_in_jsx.sh" 2>&1; then
    echo "S3 (gate): PASS"
else
    echo "S3 (gate): FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── I4: Existing UI regression check ─────────────────────────────────────

echo "--- Existing UI Regression: All 20 JSX pages present ---"
EXISTING_COUNT=$(find "$PROJECT_ROOT/runtime/ui/src/pages" -maxdepth 1 -name "*.jsx" -not -name "SchedulePage.css" | wc -l)
INFRA_COUNT=$(find "$PROJECT_ROOT/runtime/ui/src/pages/infra" -maxdepth 1 -name "*.jsx" | wc -l)
echo "Top-level JSX files: $EXISTING_COUNT (expected >= 17)"
echo "Infra JSX files: $INFRA_COUNT (expected 7)"

if [[ $EXISTING_COUNT -ge 17 ]] && [[ $INFRA_COUNT -ge 7 ]]; then
    echo "I4: PASS (all existing pages present + new Tier 10 pages)"
else
    echo "I4: FAIL"
    FAILURES=$((FAILURES + 1))
fi

echo ""

# ── Final verdict ────────────────────────────────────────────────────────

if [[ $FAILURES -eq 0 ]]; then
    echo "============================================"
    echo "ALL ACCEPTANCE TESTS PASSED (0 failures)"
    echo "============================================"
    exit 0
else
    echo "============================================"
    echo "FAIL: $FAILURES test suite(s) failed"
    echo "============================================"
    exit 1
fi
