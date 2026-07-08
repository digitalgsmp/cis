#!/usr/bin/env bash
# gate_11a_no_writes.sh — Verify 11A has no POST/PUT/PATCH/DELETE endpoints
set -euo pipefail

echo "=== 11A: No Write Endpoints ==="

API_FILE="/mnt/projects/cis/runtime/api/dashboard_api.py"

if grep -qE '@dashboard_bp\.route.*methods.*POST|@dashboard_bp\.route.*methods.*PUT|@dashboard_bp\.route.*methods.*PATCH|@dashboard_bp\.route.*methods.*DELETE' "$API_FILE"; then
  echo "FAIL: Write method found in dashboard_api.py"
  grep -nE 'methods.*POST|methods.*PUT|methods.*PATCH|methods.*DELETE' "$API_FILE"
  exit 1
fi

# Also verify no INSERT/UPDATE/DELETE SQL (only SELECT)
if grep -qE 'INSERT|UPDATE|DELETE' "$API_FILE"; then
  echo "FAIL: Write SQL (INSERT/UPDATE/DELETE) found in dashboard_api.py"
  grep -nE 'INSERT|UPDATE|DELETE' "$API_FILE"
  exit 1
fi

echo "PASS: No write endpoints or write SQL in 11A"
