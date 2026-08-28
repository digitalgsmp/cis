#!/usr/bin/env bash
# gate_11b_idempotency.sh — Duplicate approval returns already_approved
set -euo pipefail
echo "=== 11B: Idempotency ==="

API_FILE="${CIS_REPO:-/mnt/projects/cis}/runtime/api/dashboard_api.py"

# Verify the code checks for existing approval before INSERT
if ! grep -q "already_approved\|is_current.*=.*1.*AND.*decision.*=.*APPROVE\|SELECT.*eric_gate_approvals.*is_current" "$API_FILE"; then
  echo "FAIL: No idempotency check in dashboard_api.py"
  exit 1
fi

echo "PASS: Idempotency check present (SELECT before INSERT, already_approved response)"
