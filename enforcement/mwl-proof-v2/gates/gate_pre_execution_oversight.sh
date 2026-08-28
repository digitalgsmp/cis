#!/usr/bin/env bash
# gate_pre_execution_oversight.sh — Automatic Pre-Execution Oversight Gate
#
# Fires AUTOMATICALLY before any execution directive reaches Eric.
# Two sub-gates run in sequence:
#   1. Staleness Check — web freshness verification
#   2. Deliberation — R1 + Qwen dual-review reconciliation
#
# This gate is invoked from gate_runner.sh during every pipeline run.
# It does NOT auto-approve — it blocks on OBJECTIONS/ESCALATE so Eric
# always makes the final decision.
#
# Usage:
#   gate_pre_execution_oversight.sh --proposal-file <path>
#   gate_pre_execution_oversight.sh --proposal-file <path> --skip-staleness
#
# Exit codes:
#   0 — CONSENSUS_REACHED (ready for Eric approval)
#   1 — OBJECTIONS/ESCALATE (Eric must decide)
#   2 — pipeline error
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
DISPATCH="$REPO/tools/pipeline/pipeline_dispatch.sh"

PROPOSAL_FILE="${CIS_OVERSIGHT_PROPOSAL:-}"
SKIP_STALENESS=false
MAX_ROUNDS=2

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --proposal-file)
            PROPOSAL_FILE="$2"
            shift 2
            ;;
        --skip-staleness)
            SKIP_STALENESS=true
            shift
            ;;
        --max-rounds)
            MAX_ROUNDS="$2"
            shift 2
            ;;
        *)
            echo "Unknown arg: $1"
            echo "Usage: gate_pre_execution_oversight.sh --proposal-file <path> [--skip-staleness]"
            exit 2
            ;;
    esac
done

# If no proposal file provided and the env var isn't set, skip gracefully
if [[ -z "$PROPOSAL_FILE" ]]; then
    echo "Gate: Pre-Execution Oversight"
    echo "  SKIP: No proposal file provided (set --proposal-file or \$CIS_OVERSIGHT_PROPOSAL)"
    exit 0
fi

if [[ ! -f "$PROPOSAL_FILE" ]]; then
    echo "Gate: Pre-Execution Oversight"
    echo "  SKIP: Proposal file not found: $PROPOSAL_FILE"
    exit 0
fi

echo "━━━ GATE: Pre-Execution Oversight ━━━"
echo "Proposal: $PROPOSAL_FILE"
echo ""

# Build dispatch flags
DISPATCH_FLAGS="--proposal $PROPOSAL_FILE --max-rounds $MAX_ROUNDS"
if $SKIP_STALENESS; then
    DISPATCH_FLAGS="$DISPATCH_FLAGS --no-staleness"
fi

# Run the combined pipeline
set +e
bash "$DISPATCH" $DISPATCH_FLAGS 2>&1
DISPATCH_EXIT=$?
set -e

echo ""
case $DISPATCH_EXIT in
    0)
        echo "   RESULT: PASS — CONSENSUS_REACHED, ready for Eric approval"
        exit 0
        ;;
    1)
        echo "   RESULT: FAIL — OBJECTIONS or ESCALATE, Eric must decide"
        exit 1
        ;;
    *)
        echo "   RESULT: ERROR — pipeline failure (exit $DISPATCH_EXIT)"
        exit 2
        ;;
esac
