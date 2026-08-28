#!/usr/bin/env bash
# gate_deliberation.sh — Automatic Pre-Execution Oversight Gate
#
# Every execution directive passes through this gate before reaching Eric.
# R1 (deepseek-v4-pro) and Qwen (qwen3-vl-30b) independently review the proposal.
# Staleness findings are injected so reviewers factor current web information.
#
# The gate blocks progression until BOTH reviewers reach CONSENSUS_REACHED,
# or Eric explicitly overrides.
#
# Usage:
#   bash tools/gates/gate_deliberation.sh --proposal-file proposal.txt
#   bash tools/gates/gate_deliberation.sh --proposal-file proposal.txt --staleness stale.json --max-rounds 2
#
# Exit codes:
#   0 — CONSENSUS_REACHED by both reviewers
#   1 — OBJECTIONS / SPLIT / ESCALATE (Eric must decide)
#   2 — configuration error
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# CIS_REPO is exported to every gate by the pipeline. Deriving the root from the
# script's own path breaks once the gate is baked into the sealed /opt/cis-gates,
# where ../.. resolves to "/". (2026-08-27)
if [ -n "${CIS_REPO:-}" ] && [ -d "$CIS_REPO" ]; then
    REPO_ROOT_RESOLVED="$CIS_REPO"
else
    REPO_ROOT_RESOLVED="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")"/../.. && pwd)"
    for _c in /workspace/cis /mnt/projects/cis; do
        [ "$REPO_ROOT_RESOLVED" = "/" ] && [ -d "$_c" ] && REPO_ROOT_RESOLVED="$_c" && break
    done
fi
REPO="$REPO_ROOT_RESOLVED"
RECONCILE_SCRIPT="$REPO/tools/pipeline/reviewer_reconcile.py"

# Load runtime environment (API keys, paths)
source "$REPO/runtime/config/runtime.env" 2>/dev/null || true

PROPOSAL_FILE=""
STALENESS_FILE=""
MAX_ROUNDS=2
NO_ESCALATE=false
VERBOSE=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --proposal-file)
            PROPOSAL_FILE="$2"
            shift 2
            ;;
        --staleness)
            STALENESS_FILE="$2"
            shift 2
            ;;
        --max-rounds)
            MAX_ROUNDS="$2"
            shift 2
            ;;
        --no-escalate)
            NO_ESCALATE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown arg: $1"
            echo "Usage: gate_deliberation.sh --proposal-file <path> [--staleness <json>] [--max-rounds N]"
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

# Input validation: reject obviously too-short proposals
PROP_LEN=$(wc -c < "$PROPOSAL_FILE")
if [[ "$PROP_LEN" -lt 30 ]]; then
    echo "ERROR: Proposal too short ($PROP_LEN chars). Minimum 30 chars required."
    echo "One-word directives bypass oversight. Provide a substantive proposal."
    exit 2
fi

echo "=== Gate: Deliberation (Automatic Pre-Execution Oversight) ==="
echo "Proposal: $PROPOSAL_FILE"
echo "Max deliberation rounds: $MAX_ROUNDS"
echo "Escalation: $($NO_ESCALATE && echo 'disabled' || echo 'enabled')"
echo ""

# If staleness report exists, inject findings into a combined proposal
COMBINED_PROPOSAL="$PROPOSAL_FILE"
if [[ -n "$STALENESS_FILE" && -f "$STALENESS_FILE" ]]; then
    echo "─── Integrating Staleness Findings ───"

    # Extract staleness summary
    STALE_SUMMARY=$(python3 -c "
import json
d = json.load(open('$STALENESS_FILE'))
lines = []
lines.append('## Pre-Deliberation Freshness Check')
for c in d.get('checks', []):
    verdict = c.get('verdict', '?').upper()
    icon = {'STALE': '🔶', 'FRESH': '✅', 'UNKNOWN': '❓'}.get(verdict, '❓')
    lines.append(f'{icon} {c[\"tool_name\"]}: {verdict} (training cutoff: {c[\"training_cutoff\"]})')
    for f in c.get('findings', [])[:2]:
        lines.append(f'   {f[\"finding\"][:200]}')
    lines.append('')
print('\n'.join(lines))
" 2>/dev/null || echo "⚠ Staleness report unparseable")

    # Create combined proposal file
    COMBINED_PROPOSAL=$(mktemp /tmp/cis_deliberation_prompt_XXXXXX.txt)
    cat "$PROPOSAL_FILE" > "$COMBINED_PROPOSAL"
    echo "" >> "$COMBINED_PROPOSAL"
    echo "---" >> "$COMBINED_PROPOSAL"
    echo "" >> "$COMBINED_PROPOSAL"
    echo "$STALE_SUMMARY" >> "$COMBINED_PROPOSAL"

    echo "Combined proposal with staleness: $COMBINED_PROPOSAL"
    echo ""
else
    echo "No staleness report — reviewing proposal as-is."
    echo ""
fi

# ── Run Reconciliation ──────────────────────────────────────────────────
echo "─── Starting Dual-Review Deliberation ───"
echo "R1 (8643): deepseek-v4-pro"
echo "Qwen (8644): qwen3-vl-30b"
echo ""

ESCALATE_FLAG=""
if $NO_ESCALATE; then
    ESCALATE_FLAG="--no-escalate"
fi

set +e
RECONCILE_OUTPUT=$(python3 "$RECONCILE_SCRIPT" \
    --proposal-file "$COMBINED_PROPOSAL" \
    --max-rounds "$MAX_ROUNDS" \
    $ESCALATE_FLAG \
    2>&1)
RECONCILE_EXIT=$?
set -e

# ── Parse Result ────────────────────────────────────────────────────────
# Extract status from the last JSON block in reconciliation output
STATUS=$(echo "$RECONCILE_OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
# Find last JSON object
matches = list(re.finditer(r'\{[^{}]*\"status\"[^{}]*\}', text))
if matches:
    try:
        d = json.loads(matches[-1].group())
        print(d.get('status', 'ERROR'))
    except:
        # Try to find the FINAL RESULT section
        for line in text.split('\n'):
            if 'CONSENSUS_REACHED' in line and 'JOINT' in line:
                print('CONSENSUS_REACHED')
                sys.exit(0)
        print('ERROR')
else:
    # Fallback: scan for consensus wording
    if 'JOINT CONSENSUS REACHED' in text:
        print('CONSENSUS_REACHED')
    elif 'ESCALATE' in text:
        print('ESCALATE')
    else:
        print('ERROR')
" 2>/dev/null || echo "ERROR")

ROUNDS=$(echo "$RECONCILE_OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
matches = list(re.finditer(r'\"rounds_taken\"\s*:\s*(\d+)', text))
if matches:
    print(matches[-1].group(1))
else:
    print('?')
" 2>/dev/null || echo "?")

R1_VERDICT=$(echo "$RECONCILE_OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
match = re.search(r'\"r1_verdict\"\s*:\s*\"([^\"]+)\"', text)
if match:
    print(match.group(1))
else:
    # Fallback: find last R1 verdict line
    for line in reversed(text.split('\n')):
        if 'R1 verdict:' in line:
            print(line.split('R1 verdict:')[-1].strip())
            break
    else:
        print('unknown')
" 2>/dev/null || echo "unknown")

QWEN_VERDICT=$(echo "$RECONCILE_OUTPUT" | python3 -c "
import sys, json, re
text = sys.stdin.read()
match = re.search(r'\"qwen_verdict\"\s*:\s*\"([^\"]+)\"', text)
if match:
    print(match.group(1))
else:
    for line in reversed(text.split('\n')):
        if 'Qwen verdict:' in line:
            print(line.split('Qwen verdict:')[-1].strip())
            break
    else:
        print('unknown')
" 2>/dev/null || echo "unknown")

# ── Display Report ──────────────────────────────────────────────────────
echo ""
echo "═══ Deliberation Result ═══"
echo ""
echo "Status:    $STATUS"
echo "Rounds:    $ROUNDS"
echo "R1:        $R1_VERDICT"
echo "Qwen:      $QWEN_VERDICT"
echo ""

# Print relevant portion of reconciliation output (last 30 lines)
echo "─── Reconciliation Detail ───"
echo "$RECONCILE_OUTPUT" | tail -n 40
echo ""

# ── Gate Decision ───────────────────────────────────────────────────────
case "$STATUS" in
    CONSENSUS_REACHED)
        echo "RESULT: PASS — Consensus reached."
        echo "Eric: Both reviewers agree. Approve to proceed."
        echo ""
        echo "DELIBERATION_TOKEN: $(date -u +%Y%m%d%H%M%S)_CONSENSUS"
        exit 0
        ;;
    OBJECTIONS|ESCALATE)
        echo "RESULT: BLOCKED — $STATUS"
        echo "Eric: Reviewers disagree. You must decide:"
        echo "  • 'approve' — override and proceed"
        echo "  • 'revise' — send back for revision"
        echo "  • 'kill'   — cancel this directive"
        echo ""
        if [[ "$STATUS" == "ESCALATE" ]]; then
            echo "External advisors have been consulted (see detail above)."
        fi
        exit 1
        ;;
    *)
        echo "RESULT: ERROR — reconciliation engine failed"
        echo "Eric: Manual review required. Raw output above."
        exit 2
        ;;
esac
