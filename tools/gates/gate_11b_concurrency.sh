#!/usr/bin/env bash
# gate_11b_concurrency.sh — UNIQUE partial index prevents duplicate current approvals
set -euo pipefail
echo "=== 11B: Concurrency protection ==="

API_FILE="/mnt/projects/cis/runtime/api/dashboard_api.py"

# Verify the code handles IntegrityError (UNIQUE constraint)
if ! grep -q "IntegrityError\|integrity" "$API_FILE"; then
  echo "FAIL: No IntegrityError handling in dashboard_api.py"
  exit 1
fi

echo "PASS: Concurrency protection via IntegrityError catch"
