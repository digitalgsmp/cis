#!/usr/bin/env bash
# gate_staleness.sh — Pre-Deliberation Freshness Gate
# Verifies that all technology references in a proposal are checked against
# current web sources before the proposal enters deliberation.
#
# Usage:
#   bash tools/gates/gate_staleness.sh --proposal-file /path/to/proposal.txt
#   bash tools/gates/gate_staleness.sh --proposal-file /path/to/proposal.txt --strict
#
# Exit codes:
#   0 — all checks passed (fresh or no tools found)
#   1 — stale findings detected (reviewers will be notified)
#   2 — search errors / unknown state
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
CHECK_SCRIPT="$REPO/tools/pipeline/staleness_check.py"

PROPOSAL_FILE=""
STRICT=false
VERBOSE=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --proposal-file)
            PROPOSAL_FILE="$2"
            shift 2
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown arg: $1"
            echo "Usage: gate_staleness.sh --proposal-file <path> [--strict] [--verbose]"
            exit 2
            ;;
    esac
done

if [[ -z "$PROPOSAL_FILE" ]]; then
    echo "ERROR: --proposal-file is required"
    exit 2
fi

if [[ ! -f "$PROPOSAL_FILE" ]]; then
    echo "ERROR: Proposal file not found: $PROPOSAL_FILE"
    exit 2
fi

echo "=== Gate: Staleness (Pre-Deliberation Freshness) ==="
echo "Proposal: $PROPOSAL_FILE"
echo "Strict mode: $STRICT"
echo ""

# Run staleness check, capture JSON output + exit code
TMP_JSON=$(mktemp /tmp/cis_staleness_XXXXXX.json)
trap 'rm -f "$TMP_JSON"' EXIT

VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

# Run the check — always produce JSON for downstream consumption
set +e
python3 "$CHECK_SCRIPT" \
    --proposal-file "$PROPOSAL_FILE" \
    --json-only \
    $VERBOSE_FLAG \
    > "$TMP_JSON" 2>/tmp/cis_staleness_stderr.log
CHECK_EXIT=$?
set -e

# Parse results
STALE_COUNT=$(python3 -c "import json; d=json.load(open('$TMP_JSON')); print(d.get('stale_findings',0))" 2>/dev/null || echo "?")
UNKNOWN_COUNT=$(python3 -c "import json; d=json.load(open('$TMP_JSON')); print(d.get('unknown',0))" 2>/dev/null || echo "?")
FRESH_COUNT=$(python3 -c "import json; d=json.load(open('$TMP_JSON')); print(d.get('fresh',0))" 2>/dev/null || echo "?")
TOOLS_REF=$(python3 -c "import json; d=json.load(open('$TMP_JSON')); print(d.get('tools_referenced',0))" 2>/dev/null || echo "0")
OVERALL=$(python3 -c "import json; d=json.load(open('$TMP_JSON')); print(d.get('overall_verdict','ERROR'))" 2>/dev/null || echo "ERROR")

echo "Tools referenced: $TOOLS_REF"
echo "Fresh: $FRESH_COUNT   Stale: $STALE_COUNT   Unknown: $UNKNOWN_COUNT"
echo "Overall verdict: $OVERALL"
echo ""

# Print stale findings for visibility
if [[ "$STALE_COUNT" -gt 0 ]]; then
    echo "─── Stale Findings ───"
    python3 -c "
import json
d = json.load(open('$TMP_JSON'))
for c in d.get('checks', []):
    if c.get('verdict') == 'stale':
        print(f\"  🔶 {c['tool_name']} (training cutoff: {c['training_cutoff']})\")
        for f in c.get('findings', [])[:3]:
            print(f\"     {f['finding'][:150]}\")
        print()
"
    echo ""

    if $STRICT; then
        echo "RESULT: FAIL (strict mode — stale findings block progression)"
    else
        echo "RESULT: WARN (stale findings noted — reviewers will consider)"
    fi
elif [[ "$UNKNOWN_COUNT" -gt 0 ]]; then
    echo "RESULT: PASS with UNKNOWNS (some checks couldn't reach web sources)"
else
    echo "RESULT: PASS (all known tools appear current)"
fi

# Print the JSON path for downstream pipeline consumption
echo ""
echo "Staleness report: $TMP_JSON"

# Exit code
if $STRICT && [[ "$STALE_COUNT" -gt 0 ]]; then
    exit 1
elif [[ "$CHECK_EXIT" -eq 2 ]]; then
    exit 2
else
    # Non-strict: warn but don't block. Downstream consumers read the JSON.
    exit 0
fi
