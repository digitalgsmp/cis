#!/bin/bash
# gate_smoke.sh — run the card's smoke script; its exit code is the verdict.
#
# Usage: gate_smoke.sh <smoke_script>
#
# The smoke script holds the card's EVIDENCE commands. No model judgment:
# exit 0 = the built behavior exists, anything else = it does not.
set -u
SMOKE="${1:?usage: gate_smoke.sh <smoke_script>}"
[ -f "$SMOKE" ] || { echo "FAIL: smoke script not found: $SMOKE"; exit 1; }

if bash "$SMOKE"; then
    echo "PASS: smoke script exit 0"
    exit 0
else
    rc=$?
    echo "FAIL: smoke script exit $rc"
    exit $rc
fi
