#!/bin/bash
# gate_consensus_signal_valid.sh — pipeline-transition gate
# Stage: CONSENSUS — validates CONSENSUS_REACHED in final deliberation round
# Usage: gate_consensus_signal_valid.sh [--run-id <id>]
# Exit 0: PASS — CONSENSUS_REACHED with requires_eric_review true
# Exit 1: FAIL — wrong signal or requires_eric_review false/missing
# Exit 2: ERROR — no run ID or DB unavailable

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

resolve_run_id "$@"

query_spine "SELECT reviewer_signal, requires_eric_review
             FROM deliberation_rounds
             WHERE run_id = '$RUN_ID'
             ORDER BY round_number DESC LIMIT 1;" | python3 -c "
import sys

row = sys.stdin.read().strip()
if not row:
    print('FAIL: no deliberation rounds found for this run')
    sys.exit(1)

parts = row.split('|')
if len(parts) < 2:
    print(f'FAIL: unexpected row format: {row}')
    sys.exit(1)

signal, requires_eric = parts[0], parts[1]

if signal != 'CONSENSUS_REACHED':
    print(f'FAIL: expected CONSENSUS_REACHED, got {signal}')
    sys.exit(1)

if requires_eric != '1':
    print('FAIL: requires_eric_review is not true')
    sys.exit(1)

print('PASS: Consensus signal valid — CONSENSUS_REACHED with requires_eric_review true')
sys.exit(0)
"
