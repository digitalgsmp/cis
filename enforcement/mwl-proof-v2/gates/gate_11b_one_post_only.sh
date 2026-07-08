#!/usr/bin/env bash
# gate_11b_one_post_only.sh — Exactly one POST endpoint in dashboard_api.py
set -euo pipefail
echo "=== 11B: One POST endpoint ==="

API_FILE="/mnt/projects/cis/runtime/api/dashboard_api.py"

# Count POST methods
POST_COUNT=$(grep -c "methods.*POST\|methods=\[\"POST\"\]\|methods=\['POST'\]" "$API_FILE" || true)
echo "POST endpoints found: $POST_COUNT"

if [ "$POST_COUNT" -ne 1 ]; then
  echo "FAIL: Expected exactly 1 POST endpoint, found $POST_COUNT"
  exit 1
fi

# Verify it's the /approve endpoint
if ! grep -q "/api/dashboard/approve" "$API_FILE"; then
  echo "FAIL: POST endpoint is not /api/dashboard/approve"
  exit 1
fi

echo "PASS: Exactly one POST endpoint: /api/dashboard/approve"
