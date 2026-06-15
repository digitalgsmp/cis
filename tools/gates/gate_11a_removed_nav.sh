#!/usr/bin/env bash
# gate_11a_removed_nav.sh — Verify 4 removed-from-nav pages are reachable by direct URL
set -euo pipefail

echo "=== 11A: Removed-from-Nav Pages Accessible (E5) ==="

BASE="http://127.0.0.1:5000/ui"
FAILED=0

for path in "/spines" "/chat" "/ingest" "/infra"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${path}")
  if [ "$code" != "200" ]; then
    echo "FAIL: ${path} returned HTTP $code"
    FAILED=1
  else
    echo "PASS: ${path} returns HTTP 200"
  fi
done

if [ "$FAILED" -eq 1 ]; then
  exit 1
fi
echo "PASS: All 4 removed-from-nav pages accessible by direct URL"
