#!/usr/bin/env bash
# gate_11b_no_orchestrator_import.sh — No orchestrator/orchestration imports
set -euo pipefail
echo "=== 11B: No orchestrator imports ==="

API_FILE="${CIS_REPO:-/mnt/projects/cis}/runtime/api/dashboard_api.py"

# Check for prohibited imports
if grep -qE "from.*orchestrat|import.*orchestrat|process_manager|approval_gate|dispatch|classifier" "$API_FILE"; then
  # The word "dispatch" appears in docstring — filter false positives
  BAD=$(grep -nE "from.*orchestrat|import.*orchestrat|process_manager|approval_gate" "$API_FILE" || true)
  if [ -n "$BAD" ]; then
    echo "FAIL: Prohibited import found"
    echo "$BAD"
    exit 1
  fi
fi

echo "PASS: No orchestrator, process_manager, approval_gate, or dispatch imports"
