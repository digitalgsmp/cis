#!/usr/bin/env bash
# gate_11b_no_goal_reference_create.sh — No INSERT into goal_references; 409 on missing
set -euo pipefail
echo "=== 11B: No goal reference creation ==="

API_FILE="/mnt/projects/cis/runtime/api/dashboard_api.py"

# 1. Verify no INSERT INTO goal_references
if grep -q "INSERT.*INTO.*goal_references" "$API_FILE"; then
  echo "FAIL: INSERT INTO goal_references found in dashboard_api.py"
  grep -n "INSERT.*goal_references" "$API_FILE"
  exit 1
fi

# 2. Verify 409 response for missing goal_reference
if ! grep -q "409\|No goal reference" "$API_FILE"; then
  echo "FAIL: No 409 response for missing goal reference"
  exit 1
fi

# 3. Verify endpoint returns 409 when no goal exists (live test)
RESP=$(curl -s -X POST http://127.0.0.1:5000/api/dashboard/approve -H "Content-Type: application/json" -d '{"run_id":"run-b77483fe75234"}')
if echo "$RESP" | grep -q '"status":"rejected"' && echo "$RESP" | grep -q "No goal reference"; then
  echo "PASS: Endpoint returns 409 for missing goal reference"
else
  echo "FAIL: Unexpected response for missing goal reference"
  echo "$RESP"
  exit 1
fi
