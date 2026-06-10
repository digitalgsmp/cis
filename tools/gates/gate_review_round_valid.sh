#!/bin/bash
# gate_review_round_valid.sh — pipeline-transition gate
# Stage: REVIEW — validates reviewer_signal in final deliberation round
# Usage: gate_review_round_valid.sh [--run-id <id>]
# Exit 0: PASS — valid signal with required sub-fields
# Exit 1: FAIL — missing/invalid signal or sub-fields
# Exit 2: ERROR — no run ID or DB unavailable

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

resolve_run_id "$@"

query_spine "SELECT reviewer_signal, objections_json, requires_eric_review
             FROM deliberation_rounds
             WHERE run_id = '$RUN_ID'
             ORDER BY round_number DESC LIMIT 1;" | python3 -c "
import sys, json

row = sys.stdin.read().strip()
if not row:
    print('FAIL: no deliberation rounds found for this run')
    sys.exit(1)

parts = row.split('|')
if len(parts) < 3:
    print(f'FAIL: unexpected row format: {row}')
    sys.exit(1)

signal, objections_raw, requires_eric = parts[0], parts[1], parts[2]
VALID_SIGNALS = ['CONSENSUS_REACHED', 'OBJECTIONS', 'ESCALATE', 'ERROR']

if signal not in VALID_SIGNALS:
    print(f'FAIL: invalid reviewer_signal: {signal}')
    sys.exit(1)

if signal == 'OBJECTIONS':
    if not objections_raw or objections_raw in ('None', ''):
        print('FAIL: OBJECTIONS signal requires objections_json content')
        sys.exit(1)
    try:
        objections = json.loads(objections_raw)
        if not objections:
            print('FAIL: objections_json is empty list')
            sys.exit(1)
    except json.JSONDecodeError:
        print('FAIL: objections_json is not valid JSON')
        sys.exit(1)

print(f'PASS: Review round valid — signal {signal}')
sys.exit(0)
"
