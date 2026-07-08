#!/bin/bash
# gate_implementation_artifact_present.sh — pipeline-transition gate
# Stage: IMPLEMENT — validates implementation evidence in workflow_run_artifacts
# Usage: gate_implementation_artifact_present.sh [--run-id <id>]
# Exit 0: PASS — artifact_type='implementation' row exists with commit hash
#               or Created:/Modified: /mnt/projects/cis/ evidence
# Exit 1: FAIL — no implementation artifact or evidence insufficient
# Exit 2: ERROR — no run ID or DB unavailable
#
# NOTE: Completion status alone is NOT implementation evidence.
# This gate requires an explicit artifact record written by the implementer.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

resolve_run_id "$@"

query_spine "SELECT content FROM workflow_run_artifacts
             WHERE run_id = '$RUN_ID'
             AND artifact_type = 'implementation'
             ORDER BY created_at DESC LIMIT 1;" | python3 -c "
import sys, re

content = sys.stdin.read().strip()

if not content:
    print('FAIL: no implementation artifact found in workflow_run_artifacts. '
          'Implementer must write an artifact_type=implementation record '
          'containing a commit hash or file change evidence.')
    sys.exit(1)

# Check for commit hash: 7-40 lowercase hex chars at word boundary
commit_pattern = re.compile(r'\b[0-9a-f]{7,40}\b')
if commit_pattern.search(content):
    print('PASS: Implementation artifact present with commit hash evidence')
    sys.exit(0)

# Check for file change evidence
file_pattern = re.compile(r'(Created|Modified):\s*/mnt/projects/cis/')
if file_pattern.search(content):
    print('PASS: Implementation artifact present with file change evidence')
    sys.exit(0)

print('FAIL: implementation artifact exists but contains no commit hash '
      'or Created:/Modified: /mnt/projects/cis/ evidence')
sys.exit(1)
"
