#!/bin/bash
# gate_proposal_schema_valid.sh — pipeline-transition gate
# Stage: DRAFT — validates proposal exists in final deliberation round
# Usage: gate_proposal_schema_valid.sh [--run-id <id>]
# Exit 0: PASS — final round drafter_output non-empty and non-placeholder
# Exit 1: FAIL — output missing, empty, or placeholder only
# Exit 2: ERROR — no run ID or DB unavailable

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

resolve_run_id "$@"

query_spine "SELECT drafter_output FROM deliberation_rounds
             WHERE run_id = '$RUN_ID'
             ORDER BY round_number DESC LIMIT 1;" | python3 -c "
import sys
output = sys.stdin.read().strip()
if not output:
    print('FAIL: no deliberation rounds found for this run')
    sys.exit(1)
if 'NOT RECOVERED' in output:
    print('FAIL: drafter_output is a placeholder — orchestrator did not persist this round')
    sys.exit(1)
if len(output) < 50:
    print('FAIL: drafter_output too short to be a valid proposal')
    sys.exit(1)
print('PASS: Proposal artifact present in final deliberation round')
sys.exit(0)
"
