#!/usr/bin/env bash
# gate_11a_nav_groups.sh — Verify 4-group nav structure in App.jsx
set -euo pipefail

echo "=== 11A: Nav Groups ==="

APP="/mnt/projects/cis/runtime/ui/src/App.jsx"

# Verify NAV_GROUPS constant exists
if ! grep -q "NAV_GROUPS" "$APP"; then
  echo "FAIL: NAV_GROUPS constant not found in App.jsx"
  exit 1
fi

# Count groups
GROUP_COUNT=$(grep -c "label:" "$APP" | head -1)
if [ "$GROUP_COUNT" -lt 4 ]; then
  echo "FAIL: Expected 4+ nav groups, found $GROUP_COUNT"
  exit 1
fi

echo "PASS: NAV_GROUPS defined with expected group structure"
