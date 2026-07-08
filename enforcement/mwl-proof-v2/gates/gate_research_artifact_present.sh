#!/bin/bash
# gate_research_artifact_present.sh — pipeline-transition gate
# Stage: RESEARCH — validates research output exists in deliberation_rounds
# Usage: gate_research_artifact_present.sh [--run-id <id>]
# Exit 0: PASS — at least one deliberation round with non-empty drafter_output
# Exit 1: FAIL — no rounds found or drafter_output empty/placeholder
# Exit 2: ERROR — no run ID or DB unavailable

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

resolve_run_id "$@"

query_spine "SELECT COUNT(*) FROM deliberation_rounds
             WHERE run_id = '$RUN_ID'
             AND drafter_output IS NOT NULL
             AND drafter_output != ''
             AND drafter_output NOT LIKE '%NOT RECOVERED%';" | python3 -c "
import sys
count = int(sys.stdin.read().strip() or 0)
if count == 0:
    print('FAIL: no research/drafter output found in deliberation_rounds for this run')
    sys.exit(1)
print(f'PASS: Research artifact present — {count} round(s) with drafter output')
sys.exit(0)
"
