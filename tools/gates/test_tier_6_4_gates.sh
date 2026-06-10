#!/bin/bash
# test_tier_6_4_gates.sh — Test suite for pipeline-transition gates
# Creates spine fixtures, runs all six gates against them, reports results.
# Kanban retired per ADR-013. Fixtures now use direct sqlite3 INSERT.
#
# Usage: ./test_tier_6_4_gates.sh
#
# Exit 0: all tests passed
# Exit 1: one or more tests failed
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GATES_DIR="$SCRIPT_DIR"
PASSED=0
FAILED=0
TOTAL=0
FIXTURE_RUN_IDS=()

CIS_DB_PATH="${CIS_DB_PATH:-/mnt/projects/cis/data/cis_memory.db}"

cleanup() {
    for run_id in "${FIXTURE_RUN_IDS[@]}"; do
        sqlite3 "$CIS_DB_PATH" "DELETE FROM workflow_run_artifacts WHERE run_id = '$run_id';" 2>/dev/null || true
        sqlite3 "$CIS_DB_PATH" "DELETE FROM deliberation_rounds WHERE run_id = '$run_id';" 2>/dev/null || true
        sqlite3 "$CIS_DB_PATH" "DELETE FROM workflow_runs WHERE id = '$run_id';" 2>/dev/null || true
    done
    true
}
trap cleanup EXIT

# ── Helpers ──────────────────────────────────────────────────────────

create_fixture() {
    local run_id="test-$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]' | head -c 8 || echo "$RANDOM$RANDOM")"
    local signal="$1"
    local requires_eric="${2:-1}"
    local objections_json="${3:-}"
    local drafter_output="${4:-Test drafter output content for validation.}"
    local eric_approved="${5:-}"

    # Insert workflow_run
    sqlite3 "$CIS_DB_PATH" "INSERT INTO workflow_runs
        (id, topic, result, status, requires_eric_review, max_rounds,
         max_consecutive_revisions, rounds_completed, created_at, eric_approved_at)
        VALUES ('$run_id', 'Test topic for gate validation',
                'PENDING', 'PENDING', $requires_eric, 3, 3, 1,
                datetime('now')"${eric_approved:+, '$eric_approved'}");"

    # Insert deliberation_round
    sqlite3 "$CIS_DB_PATH" "INSERT INTO deliberation_rounds
        (run_id, round_number, drafter_role, drafter_output,
         reviewer_role, reviewer_signal, objections_json,
         revision_number, requires_eric_review, created_at)
        VALUES ('$run_id', 1, 'hermes-v4pro', '$drafter_output',
                'hermes-r1', '$signal', ${objections_json:-NULL},
                1, $requires_eric, datetime('now'));"

    FIXTURE_RUN_IDS+=("$run_id")
    echo "$run_id"
}

run_gate() {
    local gate="$1"
    local run_id="$2"
    local expected_exit="$3"
    local expected_msg="$4"
    local desc="$5"

    local output exit_code
    output=$("$GATES_DIR/$gate" --run-id "$run_id" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}
    TOTAL=$((TOTAL + 1))

    if [[ "$exit_code" == "$expected_exit" ]]; then
        if [[ -n "$expected_msg" ]] && ! echo "$output" | grep -qF "$expected_msg"; then
            echo "  WARN: $desc — exit $exit_code OK, but output missing '$expected_msg'"
            echo "    got: $output"
        else
            echo "  PASS: $desc (exit $exit_code)"
            PASSED=$((PASSED + 1))
        fi
    else
        echo "  FAIL: $desc — expected exit $expected_exit, got $exit_code"
        echo "    output: $output"
        FAILED=$((FAILED + 1))
    fi
}

# ── Fixture 1: CONSENSUS_REACHED with all fields ────────────────────

echo "=== Fixture 1: CONSENSUS_REACHED, eric_approved ==="
F1=$(create_fixture "CONSENSUS_REACHED" "1" "" "A valid proposal with summary and recommendation sections." "2026-06-09T00:00:00Z")

run_gate gate_research_artifact_present.sh "$F1" 0 "" "research: drafter output present"
run_gate gate_proposal_schema_valid.sh "$F1" 0 "" "proposal: drafter output non-empty"
run_gate gate_review_round_valid.sh "$F1" 0 "" "review: CONSENSUS_REACHED"
run_gate gate_consensus_signal_valid.sh "$F1" 0 "" "consensus: CONSENSUS_REACHED with requires_eric"
run_gate gate_eric_approval_present.sh "$F1" 0 "" "eric: approved"
# gate_implementation: no artifact yet, expect FAIL
run_gate gate_implementation_artifact_present.sh "$F1" 1 "no implementation artifact" "implement: no artifact inserted"

# ── Fixture 2: OBJECTIONS signal ────────────────────────────────────

echo ""
echo "=== Fixture 2: OBJECTIONS with objections_json ==="
F2=$(create_fixture "OBJECTIONS" "1" "'[\"test objection one\", \"test objection two\"]'" "A proposal with objections.")

run_gate gate_review_round_valid.sh "$F2" 0 "" "review: OBJECTIONS with valid objections_json"
run_gate gate_consensus_signal_valid.sh "$F2" 1 "expected CONSENSUS_REACHED" "consensus: OBJECTIONS fails consensus gate"

# ── Fixture 3: ESCALATE signal ──────────────────────────────────────

echo ""
echo "=== Fixture 3: ESCALATE signal ==="
F3=$(create_fixture "ESCALATE" "1" "" "Proposal text for escalation test.")

run_gate gate_review_round_valid.sh "$F3" 0 "" "review: ESCALATE accepted"
run_gate gate_consensus_signal_valid.sh "$F3" 1 "expected CONSENSUS_REACHED" "consensus: ESCALATE fails consensus gate"

# ── Fixture 4: CONSENSUS_REACHED, requires_eric=0 (should fail) ────

echo ""
echo "=== Fixture 4: CONSENSUS but requires_eric_review false ==="
F4=$(create_fixture "CONSENSUS_REACHED" "0" "" "Proposal content.")

run_gate gate_consensus_signal_valid.sh "$F4" 1 "requires_eric_review is not true" "consensus: requires_eric false rejected"

# ── Fixture 5: Eric not approved ────────────────────────────────────

echo ""
echo "=== Fixture 5: CONSENSUS but no eric_approved ==="
F5=$(create_fixture "CONSENSUS_REACHED" "1" "" "Proposal content." "")

run_gate gate_eric_approval_present.sh "$F5" 1 "Eric approval pending" "eric: not approved fails"

# ── Fixture 6: Implementation artifact present ──────────────────────

echo ""
echo "=== Fixture 6: Implementation artifact with commit hash ==="
F6=$(create_fixture "CONSENSUS_REACHED" "1" "" "Proposal content." "2026-06-09T00:00:00Z")
sqlite3 "$CIS_DB_PATH" "INSERT INTO workflow_run_artifacts
    (run_id, artifact_type, content) VALUES
    ('$F6', 'implementation', 'Commit: abc1234def — Fixed gate wiring for Tier 8 readiness');"

run_gate gate_implementation_artifact_present.sh "$F6" 0 "" "implement: artifact with commit hash"

echo ""
echo "=== Fixture 7: Implementation artifact with file evidence ==="
F7=$(create_fixture "CONSENSUS_REACHED" "1" "" "Proposal content." "2026-06-09T00:00:00Z")
sqlite3 "$CIS_DB_PATH" "INSERT INTO workflow_run_artifacts
    (run_id, artifact_type, content) VALUES
    ('$F7', 'implementation', 'Modified: /mnt/projects/cis/tools/gates/_gate_common.sh');"

run_gate gate_implementation_artifact_present.sh "$F7" 0 "" "implement: artifact with file evidence"

# ── Fixture 8: Empty drafter_output (placeholder) ───────────────────

echo ""
echo "=== Fixture 8: Empty/placeholder drafter_output ==="
F8=$(create_fixture "ESCALATE" "1" "" "[ACTUAL OUTPUT NOT RECOVERED]")
run_gate gate_proposal_schema_valid.sh "$F8" 1 "" "proposal: placeholder rejected"

# ── Summary ──────────────────────────────────────────────────────────

echo ""
echo "========================================"
echo "Results: $PASSED passed, $FAILED failed (of $TOTAL total)"
echo "========================================"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
exit 0
