#!/usr/bin/env bash
# gate_11a_regression_pages.sh — Verify all 18 routed pages + 7 infra sub-components render
set -euo pipefail

echo "=== 11A: Page Regression ==="

BASE="http://127.0.0.1:5000/ui"
FAILED=0

# 18 top-level routed pages
PAGES=(
  "/"
  "/ideas" "/projects" "/schedule" "/dam" "/learn" "/review"
  "/ingest" "/spines" "/infra" "/chat" "/advisor-chat"
  "/pipeline" "/eric-gate" "/archive/search" "/archive/sessions"
  "/decisions" "/relay" "/roadmap"
)

for path in "${PAGES[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${path}")
  if [ "$code" != "200" ]; then
    echo "FAIL: ${path} returned HTTP $code"
    FAILED=1
  else
    echo "PASS: ${path} returns HTTP 200"
  fi
done

# 7 infra sub-components reachable through /infra route
INFRA_TABS=("?tab=collab" "?tab=hardware" "?tab=services" "?tab=models" "?tab=software" "?tab=storage" "?tab=advisor")
for tab in "${INFRA_TABS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/infra${tab}")
  if [ "$code" != "200" ]; then
    echo "FAIL: /infra${tab} returned HTTP $code"
    FAILED=1
  else
    echo "PASS: /infra${tab} returns HTTP 200"
  fi
done

if [ "$FAILED" -eq 1 ]; then
  exit 1
fi
echo "PASS: All pages render"
