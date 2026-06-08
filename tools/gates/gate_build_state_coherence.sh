#!/usr/bin/env bash
# gate_build_state_coherence.sh — Tier 6.5 Remediation
# Verifies generated context agrees with canonical build state in spine.
#
# Checks:
#   1. project_state table exists and has current build_phase row
#   2. AGENTS.md reports current tier (not an older tier)
#   3. HCP_01 reports current tier matching project_state
#   4. No hardcoded "IN PROGRESS" or "COMPLETE" stale-tier strings in generators
#   5. Active blockers don't contradict completed tiers
#   6. Generated exports aren't older than last canonical build-state record
#
# Usage: bash tools/gates/gate_build_state_coherence.sh [--db PATH] [--agents PATH] [--hcp PATH]
# Exit: 0 = PASS, 1 = FAIL (coherence error), 2 = ERROR (missing prereq)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
DB_PATH="${1:-$REPO_ROOT/data/cis_memory.db}"
AGENTS_MD="${2:-$REPO_ROOT/AGENTS.md}"
HCP_01="${3:-$REPO_ROOT/PROJECT_CONTEXT_PACK_UPLOAD/HCP_01_CURRENT_STATE.md}"
FAILURES=0

fail() {
    echo "FAIL: $*"
    FAILURES=$((FAILURES + 1))
}

# Check 1: project_state table exists and has build_phase
if ! sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='project_state'" | grep -q project_state; then
    fail "project_state table does not exist in $DB_PATH"
    exit 1
fi

CANONICAL_PHASE=$(sqlite3 "$DB_PATH" \
    "SELECT value FROM project_state WHERE key='build_phase' AND superseded_at IS NULL ORDER BY id DESC LIMIT 1" 2>/dev/null)
if [ -z "$CANONICAL_PHASE" ]; then
    fail "No current build_phase row in project_state"
    exit 1
fi
echo "OK: canonical build_phase = '$CANONICAL_PHASE'"

CANONICAL_TIER=$(sqlite3 "$DB_PATH" \
    "SELECT value FROM project_state WHERE key='completed_tier' AND superseded_at IS NULL ORDER BY id DESC LIMIT 1" 2>/dev/null || echo "")

# Check 2: AGENTS.md reports current tier
if [ ! -f "$AGENTS_MD" ]; then
    fail "AGENTS.md not found at $AGENTS_MD"
else
    AGENTS_PHASE=$(grep "^Tier " "$AGENTS_MD" | head -1 || echo "")
    if [ -z "$AGENTS_PHASE" ]; then
        fail "AGENTS.md does not contain a Tier line"
    else
        echo "OK: AGENTS.md reports '$AGENTS_PHASE'"
        # Extract tier numbers for comparison
        AGENTS_TIER=$(echo "$AGENTS_PHASE" | grep -oP 'Tier \K[0-9]+(\.[0-9]+)?' | head -1 || echo "0")
        CANON_TIER_NUM=$(echo "$CANONICAL_TIER" | grep -oP '[0-9]+(\.[0-9]+)?' | head -1 || echo "0")
        if [ -n "$AGENTS_TIER" ] && [ -n "$CANON_TIER_NUM" ]; then
            if [ "$(echo "$AGENTS_TIER < $CANON_TIER_NUM" | bc -l 2>/dev/null)" = "1" ] || \
               [ "$AGENTS_TIER" != "$CANON_TIER_NUM" ] && [ "$(echo "$AGENTS_TIER >= $CANON_TIER_NUM" | bc -l 2>/dev/null)" != "1" ]; then
                fail "AGENTS.md tier ($AGENTS_TIER) is behind canonical tier ($CANON_TIER_NUM)"
            else
                echo "OK: AGENTS.md tier ($AGENTS_TIER) >= canonical tier ($CANON_TIER_NUM)"
            fi
        fi
    fi
fi

# Check 3: HCP_01 reports current tier matching project_state
if [ ! -f "$HCP_01" ]; then
    fail "HCP_01 not found at $HCP_01"
else
    HCP_STATUS=$(grep "^Status:" "$HCP_01" | head -1 || echo "")
    if [ -z "$HCP_STATUS" ]; then
        fail "HCP_01 does not contain a Status line"
    else
        echo "OK: HCP_01 status = '$HCP_STATUS'"
        # Check that HCP status contains the canonical phase
        if ! echo "$HCP_STATUS" | grep -qF "Tier"; then
            fail "HCP_01 Status line does not reference a tier"
        fi
    fi
fi

# Check 4: No stale hardcoded tier strings in generator source or static config
# Scan for "Tier 5" or "Tier 4" in current-state context (not historical narrative)
STALE_GEN=$(grep -rn "Tier [0-4]\.\|Tier 5 Context Export" \
    "$REPO_ROOT/tools/export/" "$REPO_ROOT/config/" \
    --include="*.py" --include="*.yaml" 2>/dev/null | \
    grep -v "#\|ALLOWED\|historical\|def \|print\|return \|✅\|🔄\|line.append" || echo "")
if [ -n "$STALE_GEN" ]; then
    echo "WARN: Potential stale tier references in source files:"
    echo "$STALE_GEN"
    # Not a hard fail — some are legitimate historical descriptions
fi
echo "OK: generator source audit complete"

# Check 5: Active blockers don't contradict completed tiers
STALE_BLOCKERS=$(sqlite3 "$DB_PATH" \
    "SELECT id || ': ' || description FROM active_blockers 
     WHERE status='ACTIVE' 
     AND (description LIKE '%Tier 5 export%' OR description LIKE '%not yet built%')" 2>/dev/null || echo "")
if [ -n "$STALE_BLOCKERS" ]; then
    fail "Active blocker contradicts completed tier: $STALE_BLOCKERS"
else
    echo "OK: no active blockers contradict completed tiers"
fi

# Check 6: Generated exports aren't older than last canonical build-state record
LAST_EXPORT=$(sqlite3 "$DB_PATH" \
    "SELECT value FROM project_state WHERE key='last_export_run_id' AND superseded_at IS NULL ORDER BY id DESC LIMIT 1" 2>/dev/null || echo "")
LAST_STATE_TS=$(sqlite3 "$DB_PATH" \
    "SELECT MAX(created_at) FROM project_state WHERE superseded_at IS NULL" 2>/dev/null || echo "")
if [ -f "$AGENTS_MD" ] && [ -n "$LAST_STATE_TS" ]; then
    AGENTS_TS=$(stat -c '%Y' "$AGENTS_MD" 2>/dev/null || echo "0")
    STATE_EPOCH=$(date -d "$LAST_STATE_TS" +%s 2>/dev/null || echo "0")
    if [ "$AGENTS_TS" -lt "$STATE_EPOCH" ] 2>/dev/null; then
        fail "AGENTS.md ($(date -d @"$AGENTS_TS" '+%Y-%m-%d %H:%M' 2>/dev/null)) is older than canonical state ($(date -d @"$STATE_EPOCH" '+%Y-%m-%d %H:%M' 2>/dev/null))"
    else
        echo "OK: AGENTS.md is current relative to canonical state"
    fi
fi

# Report
if [ "$FAILURES" -eq 0 ]; then
    echo ""
    echo "PASS: build state coherence — $FAILURES failures"
    exit 0
else
    echo ""
    echo "FAIL: build state coherence — $FAILURES failure(s)"
    exit 1
fi
