#!/usr/bin/env bash
# gate_ui_no_write_endpoints.sh — Tier 10 security gate S1.
# Scans runtime/api/pipeline_views.py for POST/PUT/PATCH/DELETE decorators.
# Exit 0 = PASS (no write endpoints), exit 1 = FAIL (write endpoints found).

BLUEPRINT="/mnt/projects/cis/runtime/api/pipeline_views.py"

if [[ ! -f "$BLUEPRINT" ]]; then
    echo "FAIL: $BLUEPRINT not found"
    exit 1
fi

# Match any route decorator with explicit methods including POST/PUT/PATCH/DELETE
WRITE_ROUTES=$(grep -nE '@(pipeline_views_bp|app)\.route\(.*methods.*(POST|PUT|PATCH|DELETE)' "$BLUEPRINT" 2>/dev/null)

if [[ -n "$WRITE_ROUTES" ]]; then
    echo "FAIL: Write endpoints found in pipeline_views.py:"
    echo "$WRITE_ROUTES"
    exit 1
fi

echo "PASS: No POST/PUT/PATCH/DELETE endpoints in pipeline_views.py"
exit 0
