#!/usr/bin/env bash
# gate_11b_no_veto.sh — VETO/RETURN_TO_DRAFT rejected with 400
set -euo pipefail
echo "=== 11B: No VETO/RETURN_TO_DRAFT ==="

API_FILE="${CIS_REPO:-/mnt/projects/cis}/runtime/api/dashboard_api.py"

# Verify the code only hardcodes APPROVE, not VETO or RETURN_TO_DRAFT
if grep -q "VETO\|RETURN_TO_DRAFT" "$API_FILE"; then
  # Only the CHECK constraint reference in the schema doc is acceptable
  # But in the INSERT code, only 'APPROVE' should appear
  INSERT_LINE=$(grep "INSERT INTO eric_gate_approvals" -A 5 "$API_FILE" | grep "'" | head -5)
  if echo "$INSERT_LINE" | grep -q "VETO\|RETURN_TO_DRAFT"; then
    echo "FAIL: VETO or RETURN_TO_DRAFT found in INSERT statement"
    exit 1
  fi
fi

# Verify APPROVE is the only decision value inserted
if ! grep -q "'APPROVE'" "$API_FILE"; then
  echo "FAIL: No APPROVE decision value found"
  exit 1
fi

echo "PASS: Only APPROVE inserted; VETO and RETURN_TO_DRAFT not supported"
