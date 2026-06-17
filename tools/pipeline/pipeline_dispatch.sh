#!/usr/bin/env bash
# pipeline_dispatch.sh — Combined Pre-Execution Oversight Pipeline
#
# Every execution directive passes through this pipeline before reaching Eric.
# Two gates fire automatically:
#   1. Staleness Gate — web search for current versions/changes
#   2. Deliberation Gate — R1 + Qwen dual-review reconciliation
#
# The combined report is presented to Eric. No action executes without oversight.
#
# Usage:
#   bash tools/pipeline/pipeline_dispatch.sh --proposal proposal.txt
#   bash tools/pipeline/pipeline_dispatch.sh --proposal proposal.txt --no-staleness
#   bash tools/pipeline/pipeline_dispatch.sh --proposal proposal.txt --strict-staleness
#
# Exit codes:
#   0 — CONSENSUS_REACHED, ready for Eric approval
#   1 — BLOCKED (objections or staleness issues — Eric must decide)
#   2 — pipeline error
#
# Output:
#   Combined report at: /tmp/cis_dispatch_report_<timestamp>.json
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"
GATES_DIR="$REPO/tools/gates"
PIPELINE_DIR="$REPO/tools/pipeline"

PROPOSAL_FILE=""
SKIP_STALENESS=false
STRICT_STALENESS=false
MAX_DELIB_ROUNDS=2
VERBOSE=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --proposal)
            PROPOSAL_FILE="$2"
            shift 2
            ;;
        --no-staleness)
            SKIP_STALENESS=true
            shift
            ;;
        --strict-staleness)
            STRICT_STALENESS=true
            shift
            ;;
        --max-rounds)
            MAX_DELIB_ROUNDS="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown arg: $1"
            echo "Usage: pipeline_dispatch.sh --proposal <file> [--no-staleness] [--strict-staleness] [--max-rounds N]"
            exit 2
            ;;
    esac
done

if [[ -z "$PROPOSAL_FILE" ]]; then
    echo "ERROR: --proposal is required"
    exit 2
fi

if [[ ! -f "$PROPOSAL_FILE" ]]; then
    echo "ERROR: Proposal file not found: $PROPOSAL_FILE"
    exit 2
fi

TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
REPORT_FILE="/tmp/cis_dispatch_report_${TIMESTAMP}.json"
STALENESS_JSON=""

echo "═══════════════════════════════════════════"
echo "  CIS Pre-Execution Oversight Pipeline"
echo "═══════════════════════════════════════════"
echo "Proposal:  $PROPOSAL_FILE"
echo "Report:    $REPORT_FILE"
echo "Started:   $(date -u)"
echo ""

# Track overall status
STALENESS_STATUS="SKIPPED"
DELIB_STATUS="PENDING"
OVERALL="PENDING"

# ── Stage 1: Staleness Check ────────────────────────────────────────────
if $SKIP_STALENESS; then
    echo "─── Stage 1: Staleness Check ───"
    echo "SKIPPED (--no-staleness flag)"
    echo ""
else
    echo "─── Stage 1: Staleness Check ───"
    echo ""

    STALENESS_JSON=$(mktemp /tmp/cis_staleness_report_XXXXXX.json)
    STALENESS_FLAGS="--proposal-file $PROPOSAL_FILE --json-only"
    if $VERBOSE; then
        STALENESS_FLAGS="$STALENESS_FLAGS --verbose"
    fi

    set +e
    # Run staleness check but capture JSON output regardless of exit code
    python3 "$PIPELINE_DIR/staleness_check.py" \
        --proposal-file "$PROPOSAL_FILE" \
        --json-only \
        > "$STALENESS_JSON" 2>/tmp/cis_staleness_stderr.txt
    STALENESS_EXIT=$?
    set -e

    # Extract verdict from JSON
    STALENESS_VERDICT=$(python3 -c "
import json
d = json.load(open('$STALENESS_JSON'))
print(d.get('overall_verdict', 'ERROR'))
" 2>/dev/null || echo "ERROR")

    STALE_COUNT=$(python3 -c "
import json
d = json.load(open('$STALENESS_JSON'))
print(d.get('stale_findings', 0))
" 2>/dev/null || echo "?")

    echo "Staleness verdict: $STALENESS_VERDICT (stale: $STALE_COUNT)"

    if $STRICT_STALENESS && [[ "$STALENESS_VERDICT" == "STALE" ]]; then
        STALENESS_STATUS="BLOCKED"
        echo "BLOCKED — strict staleness mode. Review the report."
        echo ""
        OVERALL="BLOCKED"
    else
        STALENESS_STATUS="$STALENESS_VERDICT"
        echo "Proceeding to deliberation (staleness findings will be reviewed)"
        echo ""
    fi
fi

# If staleness blocked in strict mode, skip deliberation
if [[ "$OVERALL" == "BLOCKED" ]]; then
    echo "═══ Pipeline Stopped: Staleness Block ═══"
    echo "Staleness report: $STALENESS_JSON"
    exit 1
fi

# ── Stage 2: Deliberation ───────────────────────────────────────────────
echo "─── Stage 2: Dual-Review Deliberation ───"
echo ""

DELIB_FLAGS="--proposal-file $PROPOSAL_FILE --max-rounds $MAX_DELIB_ROUNDS"
if [[ -n "$STALENESS_JSON" && -f "$STALENESS_JSON" ]]; then
    DELIB_FLAGS="$DELIB_FLAGS --staleness $STALENESS_JSON"
fi

set +e
bash "$GATES_DIR/gate_deliberation.sh" $DELIB_FLAGS
DELIB_EXIT=$?
set -e

if [[ $DELIB_EXIT -eq 0 ]]; then
    DELIB_STATUS="CONSENSUS_REACHED"
    OVERALL="READY_FOR_ERIC"
elif [[ $DELIB_EXIT -eq 1 ]]; then
    DELIB_STATUS="OBJECTIONS_OR_ESCALATE"
    OVERALL="NEEDS_ERIC_DECISION"
else
    DELIB_STATUS="ERROR"
    OVERALL="ERROR"
fi

echo ""

# ── Stage 3: Combined Report ────────────────────────────────────────────
echo "─── Stage 3: Combined Eric Report ───"

# Build the combined JSON report
python3 -c "
import json, sys
from datetime import datetime, timezone

staleness = {}
if '$STALENESS_JSON' and __import__('os').path.exists('$STALENESS_JSON'):
    staleness = json.load(open('$STALENESS_JSON'))

report = {
    'pipeline': 'cis-pre-execution-oversight',
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'proposal_file': '$PROPOSAL_FILE',
    'stages': {
        'staleness': {
            'status': '$STALENESS_STATUS',
            'verdict': staleness.get('overall_verdict', 'SKIPPED'),
            'stale_findings': staleness.get('stale_findings', 0),
            'fresh': staleness.get('fresh', 0),
            'unknown': staleness.get('unknown', 0),
            'details': staleness.get('checks', []),
        },
        'deliberation': {
            'status': '$DELIB_STATUS',
            'exit_code': $DELIB_EXIT,
        },
    },
    'overall': '$OVERALL',
    'next_action': {
        'READY_FOR_ERIC': 'Eric: both gates passed. Approve to proceed.',
        'NEEDS_ERIC_DECISION': 'Eric: reviewers disagree or staleness found. You must decide: approve, revise, or kill.',
        'BLOCKED': 'Eric: staleness block in strict mode. Review freshness report first.',
        'ERROR': 'Eric: pipeline error — manual review required.',
    }.get('$OVERALL', 'UNKNOWN'),
}

with open('$REPORT_FILE', 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
" 2>/dev/null || echo '{\"error\": \"report generation failed\"}' > "$REPORT_FILE"

echo "Report saved: $REPORT_FILE"
echo ""

# ── Final Display ───────────────────────────────────────────────────────
echo "═══════════════════════════════════════════"
echo "  Pipeline Complete — $OVERALL"
echo "═══════════════════════════════════════════"
echo ""

# Print a clean Eric-facing summary
python3 -c "
import json
r = json.load(open('$REPORT_FILE'))

print('┌─────────────────────────────────────────┐')
print('│        Pre-Execution Oversight          │')
print('├─────────────────────────────────────────┤')

# Staleness
ss = r['stages']['staleness']
if ss['status'] == 'SKIPPED':
    print('│ 🔶 Staleness: SKIPPED')
else:
    icon = '✅' if ss['verdict'] == 'FRESH' else '🔶'
    print(f'│ {icon} Staleness: {ss[\"verdict\"]} ({ss[\"stale_findings\"]} stale, {ss[\"fresh\"]} fresh, {ss[\"unknown\"]} unknown)')
    for c in ss.get('details', []):
        v = c.get('verdict', '?').upper()
        ico = {'STALE': '🔶', 'FRESH': '✅', 'UNKNOWN': '❓'}.get(v, '❓')
        print(f'│    {ico} {c[\"tool_name\"]}: {v}')
        for f in c.get('findings', [])[:2]:
            snippet = f.get('finding', '')[:100]
            if snippet:
                print(f'│       {snippet}')

# Deliberation
ds = r['stages']['deliberation']
print(f'│')
if ds['status'] == 'CONSENSUS_REACHED':
    print(f'│ ✅ Deliberation: CONSENSUS REACHED')
else:
    icon = '⚠️' if ds['status'] != 'ERROR' else '🔴'
    print(f'│ {icon} Deliberation: {ds[\"status\"]}')

# Overall
print(f'├─────────────────────────────────────────┤')
print(f'│ Status: {r[\"overall\"]}')
print(f'│ {r[\"next_action\"][:70]}')
print(f'└─────────────────────────────────────────┘')
" 2>/dev/null

echo ""
echo "Staleness JSON: ${STALENESS_JSON:-N/A}"
echo "Report JSON:    $REPORT_FILE"

# Exit with appropriate code
case "$OVERALL" in
    READY_FOR_ERIC) exit 0 ;;
    NEEDS_ERIC_DECISION) exit 1 ;;
    *) exit 2 ;;
esac
