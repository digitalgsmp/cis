#!/usr/bin/env bash
# gate_11a_layout_no_overlap.sh — Verify HomePage archived and DashboardPage exists
set -euo pipefail

echo "=== 11A: Layout / HomePage Archive ==="

OLD="${CIS_REPO:-/mnt/projects/cis}/runtime/ui/src/pages/HomePage.jsx"
ARCHIVE="${CIS_REPO:-/mnt/projects/cis}/runtime/ui_archive/HomePage.jsx"
NEW="${CIS_REPO:-/mnt/projects/cis}/runtime/ui/src/pages/DashboardPage.jsx"

if [ -f "$OLD" ]; then
  echo "FAIL: HomePage.jsx still in pages/ (not archived)"
  exit 1
fi

if [ ! -f "$ARCHIVE" ]; then
  echo "FAIL: HomePage.jsx not found in ui_archive/"
  exit 1
fi

if [ ! -f "$NEW" ]; then
  echo "FAIL: DashboardPage.jsx not found in pages/"
  exit 1
fi

echo "PASS: HomePage archived, DashboardPage created, no overlap at file level"
