#!/bin/bash
# test_tier_6_4_gates.sh — Test suite for Tier 6.4 pipeline-transition gates
# Creates Kanban fixture cards, runs all six gates against them, reports results.
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
FIXTURE_IDS=()

cleanup() {
    # Optional: remove created fixture cards
    # for id in "${FIXTURE_IDS[@]}"; do
    #     hermes kanban archive "$id" &>/dev/null || true
    # done
    true
}
trap cleanup EXIT

# ── Helpers ──────────────────────────────────────────────────────────

create_fixture() {
    local title="$1"
    local body="$2"
    local card_id
    card_id=$(hermes kanban create "$title" --body "$body" --json 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null)
    if [[ -z "$card_id" ]]; then
        echo "ERROR: failed to create fixture: $title" >&2
        exit 2
    fi
    FIXTURE_IDS+=("$card_id")
    echo "$card_id"
}

run_gate() {
    local gate="$1"
    local card_id="$2"
    local expected_exit="$3"
    local expected_msg="$4"
    local desc="$5"

    local output exit_code
    output=$("$GATES_DIR/$gate" --kanban-card-id "$card_id" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

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

# ── Fixture 1: All valid markers (passing) ───────────────────────────

echo "=== Fixture 1: All valid markers ==="
F1=$(create_fixture "T6.4-test-passing" "## Research Artifact
Evidence collected.

## Proposal
### Summary
A valid summary.
### Recommendation
A valid recommendation.

## Review
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true

## Eric Gate
APPROVED

## Implementation
Commit: b34c0ea — Reconcile Tier 6.1 and 6.4 gate marker specs
Modified: /mnt/projects/cis/tools/gates/gate_research_artifact_present.sh
")

run_gate gate_research_artifact_present.sh "$F1" 0 "" "research: valid markers"
run_gate gate_proposal_schema_valid.sh "$F1" 0 "" "proposal: valid markers"
run_gate gate_review_round_valid.sh "$F1" 0 "" "review: valid markers"
run_gate gate_consensus_signal_valid.sh "$F1" 0 "" "consensus: valid markers"
run_gate gate_eric_approval_present.sh "$F1" 0 "" "eric: valid markers"
run_gate gate_implementation_artifact_present.sh "$F1" 0 "" "implement: valid markers"

# ── Fixture 2: Missing Proposal section ──────────────────────────────

echo ""
echo "=== Fixture 2: Missing Proposal section ==="
F2=$(create_fixture "T6.4-test-missing-proposal" "## Research Artifact
Evidence.

## Review
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true
")
run_gate gate_proposal_schema_valid.sh "$F2" 1 "Proposal section missing" "proposal: missing section"

# ── Fixture 3: Empty Research Artifact ──────────────────────────────

echo ""
echo "=== Fixture 3: Empty Research Artifact ==="
F3=$(create_fixture "T6.4-test-empty-research" "## Research Artifact

## Proposal
### Summary
S.
### Recommendation
R.
")
run_gate gate_research_artifact_present.sh "$F3" 1 "Research Artifact section empty" "research: empty section"

# ── Fixture 4: APPROVED in wrong section ────────────────────────────

echo ""
echo "=== Fixture 4: APPROVED in wrong section ==="
F4=$(create_fixture "T6.4-test-approved-wrong-section" "## Proposal
APPROVED
### Summary
S.
### Recommendation
R.

## Eric Gate
")
run_gate gate_eric_approval_present.sh "$F4" 1 "APPROVED not found" "eric: APPROVED in Proposal, not Eric Gate"

# ── Fixture 5: Suffixed headings ─────────────────────────────────────

echo ""
echo "=== Fixture 5: Suffixed heading ==="
F5=$(create_fixture "T6.4-test-suffixed-heading" "## Proposal Archive
### Summary
S.
### Recommendation
R.

## Review
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true
")
run_gate gate_proposal_schema_valid.sh "$F5" 1 "Proposal section missing" "proposal: ## Proposal Archive is not ## Proposal"

# ── Fixture 6: Duplicate Proposal heading ────────────────────────────

echo ""
echo "=== Fixture 6: Duplicate Proposal heading ==="
F6=$(create_fixture "T6.4-test-dup-proposal" "## Proposal

## Proposal
### Summary
Valid summary.
### Recommendation
Valid recommendation.
")
run_gate gate_proposal_schema_valid.sh "$F6" 1 "duplicate" "proposal: duplicate heading"

# ── Fixture 7: remaining_objections: 0 (rejected) ────────────────────

echo ""
echo "=== Fixture 7: remaining_objections: 0 ==="
F7=$(create_fixture "T6.4-test-ro-zero" "## Review
CONSENSUS_REACHED
remaining_objections: 0
requires_eric_review: true
")
run_gate gate_review_round_valid.sh "$F7" 1 "rejected remaining_objections" "review: rejects remaining_objections: 0"
run_gate gate_consensus_signal_valid.sh "$F7" 1 "rejected remaining_objections" "consensus: rejects remaining_objections: 0"

# ── Fixture 8: remaining_objections: [] (rejected) ──────────────────

echo ""
echo "=== Fixture 8: remaining_objections: [] ==="
F8=$(create_fixture "T6.4-test-ro-brackets" "## Review
CONSENSUS_REACHED
remaining_objections: []
requires_eric_review: true
")
run_gate gate_review_round_valid.sh "$F8" 1 "rejected remaining_objections" "review: rejects remaining_objections: []"
run_gate gate_consensus_signal_valid.sh "$F8" 1 "rejected remaining_objections" "consensus: rejects remaining_objections: []"

# ── Fixture 9: Case-insensitive none (NONE, None) ───────────────────

echo ""
echo "=== Fixture 9: Case-insensitive none ==="
F9a=$(create_fixture "T6.4-test-none-upper" "## Review
CONSENSUS_REACHED
remaining_objections: NONE
requires_eric_review: true
")
run_gate gate_review_round_valid.sh "$F9a" 0 "" "review: accepts NONE (case-insensitive)"
run_gate gate_consensus_signal_valid.sh "$F9a" 0 "" "consensus: accepts NONE"

F9b=$(create_fixture "T6.4-test-none-mixed" "## Review
CONSENSUS_REACHED
remaining_objections: None
requires_eric_review: true
")
run_gate gate_review_round_valid.sh "$F9b" 0 "" "review: accepts None (case-insensitive)"

# ── Fixture 10: Standalone vs embedded signal ────────────────────────

echo ""
echo "=== Fixture 10: Standalone vs embedded signal ==="
F10a=$(create_fixture "T6.4-test-signal-standalone" "## Review
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: true
")
run_gate gate_review_round_valid.sh "$F10a" 0 "" "review: standalone CONSENSUS_REACHED"

F10b=$(create_fixture "T6.4-test-signal-embedded" "## Review
We reached CONSENSUS_REACHED after deliberation.
")
run_gate gate_review_round_valid.sh "$F10b" 1 "no valid signal" "review: embedded CONSENSUS_REACHED rejected"

F10c=$(create_fixture "T6.4-test-signal-first-word" "## Review
CONSENSUS_REACHED with additional notes.
remaining_objections: none
requires_eric_review: true
")
run_gate gate_review_round_valid.sh "$F10c" 0 "" "review: CONSENSUS_REACHED as first word accepted"

# ── Fixture 11: OBJECTIONS dash bullet acceptance ────────────────────

echo ""
echo "=== Fixture 11: OBJECTIONS with dash bullets ==="
F11=$(create_fixture "T6.4-test-dash-bullets" "## Review
OBJECTIONS
- objection one
- objection two
")
run_gate gate_review_round_valid.sh "$F11" 0 "" "review: OBJECTIONS with dash bullets accepted"

# ── Fixture 12: OBJECTIONS * bullet rejected ─────────────────────────

echo ""
echo "=== Fixture 12: OBJECTIONS with star bullet rejected ==="
F12=$(create_fixture "T6.4-test-star-bullets" "## Review
OBJECTIONS
* objection one
* objection two
")
run_gate gate_review_round_valid.sh "$F12" 1 "OBJECTIONS missing bullet" "review: OBJECTIONS with * bullets rejected"

# ── Fixture 13: OBJECTIONS + bullet rejected ─────────────────────────

echo ""
echo "=== Fixture 13: OBJECTIONS with plus bullet rejected ==="
F13=$(create_fixture "T6.4-test-plus-bullets" "## Review
OBJECTIONS
+ objection one
+ objection two
")
run_gate gate_review_round_valid.sh "$F13" 1 "OBJECTIONS missing bullet" "review: OBJECTIONS with + bullets rejected"

# ── Fixture 14: Missing requires_eric_review ─────────────────────────

echo ""
echo "=== Fixture 14: Missing requires_eric_review ==="
F14=$(create_fixture "T6.4-test-missing-rer" "## Review
CONSENSUS_REACHED
remaining_objections: none
")
run_gate gate_consensus_signal_valid.sh "$F14" 1 "missing requires_eric_review" "consensus: missing requires_eric_review"

# ── Fixture 15: requires_eric_review: false ──────────────────────────

echo ""
echo "=== Fixture 15: requires_eric_review: false ==="
F15=$(create_fixture "T6.4-test-rer-false" "## Review
CONSENSUS_REACHED
remaining_objections: none
requires_eric_review: false
")
run_gate gate_consensus_signal_valid.sh "$F15" 1 "requires_eric_review is false" "consensus: requires_eric_review: false rejected"

# ── Fixture 16: Implementation path outside /mnt/projects/cis/ ──────

echo ""
echo "=== Fixture 16: Implementation path outside /mnt/projects/cis/ ==="
F16=$(create_fixture "T6.4-test-path-outside" "## Implementation
Created: /tmp/some_file.sh
")
run_gate gate_implementation_artifact_present.sh "$F16" 1 "no artifact evidence" "implement: path outside /mnt/projects/cis/ rejected"

# ── Fixture 17: Duplicate Eric Gate ──────────────────────────────────

echo ""
echo "=== Fixture 17: Duplicate Eric Gate ==="
F17=$(create_fixture "T6.4-test-dup-eric" "## Eric Gate

## Eric Gate
APPROVED
")
run_gate gate_eric_approval_present.sh "$F17" 1 "duplicate" "eric: duplicate heading rejected"

# ── Summary ──────────────────────────────────────────────────────────

echo ""
echo "========================================"
echo "Results: $PASSED passed, $FAILED failed"
echo "========================================"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
exit 0
