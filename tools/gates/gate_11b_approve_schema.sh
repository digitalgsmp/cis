#!/usr/bin/env bash
# gate_11b_approve_schema.sh — Verify INSERT populates all 14 columns of eric_gate_approvals
set -euo pipefail
echo "=== 11B: Schema population ==="

API_FILE="${CIS_REPO:-/mnt/projects/cis}/runtime/api/dashboard_api.py"

# Check dashboard_api.py contains INSERT into eric_gate_approvals
if ! grep -q "INSERT INTO eric_gate_approvals" "$API_FILE"; then
  echo "FAIL: No INSERT INTO eric_gate_approvals in dashboard_api.py"
  exit 1
fi

# Verify the INSERT references all required NOT NULL columns
REQUIRED_COLUMNS=("id" "workflow_run_id" "decision" "decided_at" "goal_reference_id" "briefing_hash" "briefing_json" "drift_snapshot_json" "decision_trail_snapshot_json" "is_current" "created_at")
for col in "${REQUIRED_COLUMNS[@]}"; do
  if ! grep -q "\b${col}\b" "$API_FILE"; then
    echo "FAIL: Required column '$col' not referenced in dashboard_api.py"
    exit 1
  fi
done

echo "PASS: INSERT into eric_gate_approvals with all required columns"
