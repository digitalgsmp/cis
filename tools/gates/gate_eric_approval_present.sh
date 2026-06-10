#!/bin/bash
# gate_eric_approval_present.sh — pipeline-transition gate
# Stage: ERIC_GATE — validates Eric's explicit approval via eric_approved_at
# Usage: gate_eric_approval_present.sh [--run-id <id>]
# Exit 0: PASS — eric_approved_at is non-null
# Exit 1: FAIL — eric_approved_at is null (Eric approval pending)
# Exit 2: ERROR — no run ID or DB unavailable
#
# IMPORTANT: eric_approved_at is added by migration 0005.
# The approval setter (UI button, API endpoint, or CLI command) is NOT
# implemented in this directive. Until the setter is built in the
# Foundation Hardening Phase, this gate will correctly fail for all
# unapproved runs. That is the intended behavior — do not stub or bypass.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

resolve_run_id "$@"

query_spine "SELECT eric_approved_at FROM workflow_runs
             WHERE id = '$RUN_ID';" | python3 -c "
import sys

value = sys.stdin.read().strip()
if not value:
    print('FAIL: workflow_run not found for this run_id')
    sys.exit(1)

if value in ('None', ''):
    print('FAIL: Eric approval pending — eric_approved_at is null. '
          'Approval setter not yet implemented. '
          'See Foundation Hardening Phase.')
    sys.exit(1)

print(f'PASS: Eric approval present — approved at {value}')
sys.exit(0)
"
