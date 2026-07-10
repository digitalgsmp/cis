#!/usr/bin/env bash
# gate_11a_system_overview.sh — Verify system overview YAML loads and is wired
set -euo pipefail

echo "=== 11A: System Overview ==="

YAML="${CIS_REPO:-/mnt/projects/cis}/runtime/api/system_overview.yaml"

if [ ! -f "$YAML" ]; then
  echo "FAIL: system_overview.yaml not found"
  exit 1
fi

# Verify dashboard API endpoint returns overview_areas
RESP=$(curl -s http://127.0.0.1:5000/api/dashboard/full 2>&1)
if ! echo "$RESP" | grep -q "overview_areas"; then
  echo "FAIL: /api/dashboard/full missing overview_areas"
  exit 1
fi

AREA_COUNT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('overview_areas',{})))" 2>/dev/null)
if [ "$AREA_COUNT" -lt 1 ]; then
  echo "FAIL: overview_areas empty"
  exit 1
fi

echo "PASS: System overview YAML exists, endpoint returns overview_areas ($AREA_COUNT areas)"
