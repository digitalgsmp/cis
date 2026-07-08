#!/usr/bin/env bash
# gate_ui_method_allowlist.sh — Tier 10 security gate S4.
# Confirms all new pipeline endpoints reject non-GET methods via grep on blueprint.
# Exit 0 = PASS, exit 1 = FAIL.

BLUEPRINT="/mnt/projects/cis/runtime/api/pipeline_views.py"

if [[ ! -f "$BLUEPRINT" ]]; then
    echo "FAIL: $BLUEPRINT not found"
    exit 1
fi

# Count route decorators in the blueprint
ROUTE_COUNT=$(grep -c '@pipeline_views_bp\.route(' "$BLUEPRINT")

if [[ $ROUTE_COUNT -lt 8 ]]; then
    echo "FAIL: Expected at least 8 route decorators, found $ROUTE_COUNT"
    exit 1
fi

# Verify no explicit methods=['GET', 'POST'] style (only implicit GET)
METHOD_SPECS=$(grep -c "methods" "$BLUEPRINT" || true)
if [[ $METHOD_SPECS -gt 0 ]]; then
    # Check if any specify non-GET
    if grep -qE "methods.*(POST|PUT|PATCH|DELETE)" "$BLUEPRINT"; then
        echo "FAIL: Non-GET methods specified in blueprint"
        exit 1
    fi
fi

echo "PASS: All $ROUTE_COUNT endpoints use GET only (implicit or explicit)"
exit 0
