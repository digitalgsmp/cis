#!/usr/bin/env bash
# gate_drafter_closeout.sh — Tier 11C: Verify Drafter closeout invariants
# Usage: bash tools/gates/gate_drafter_closeout.sh --run-id WORKFLOW_RUN_ID
set -euo pipefail

DB="${CIS_DB_PATH:-/mnt/projects/cis/data/cis_memory.db}"
RUN_ID=""
FAILS=0

# Parse --run-id
while [[ $# -gt 0 ]]; do
    case "$1" in
        --run-id) RUN_ID="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "$RUN_ID" ]]; then
    echo "ERROR: --run-id is required"
    exit 1
fi

echo "=== Tier 11C: Drafter Closeout Gate ==="
echo "Run ID: $RUN_ID"
echo ""

# --- 1. Migration 0012 applied ---
if sqlite3 "$DB" "PRAGMA table_info(lifecycle_events);" | grep -q workflow_run_id && \
   sqlite3 "$DB" "PRAGMA table_info(dispatch_log);" | grep -q workflow_run_id; then
    echo "1. Migration 0012: PASS"
else
    echo "1. Migration 0012: FAIL — workflow_run_id column missing"
    FAILS=$((FAILS + 1))
fi

# --- 2. Lifecycle trail exists ---
EVENT_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM lifecycle_events WHERE workflow_run_id = '$RUN_ID';")
if [[ "$EVENT_COUNT" -ge 4 ]]; then
    echo "2. Lifecycle trail (≥ 4 events): PASS ($EVENT_COUNT events)"
else
    echo "2. Lifecycle trail (≥ 4 events): FAIL — got $EVENT_COUNT events"
    FAILS=$((FAILS + 1))
fi

# --- 3. Correct state transition sequence ---
STATE_SEQ=$(sqlite3 "$DB" "SELECT to_state FROM lifecycle_events WHERE workflow_run_id = '$RUN_ID' ORDER BY id ASC;")
EXPECTED="ROUTING.*DRAFTING.*DRAFT_READY.*REVIEW_PENDING"
if echo "$STATE_SEQ" | tr '\n' ' ' | grep -qE "ROUTING.*DRAFTING.*DRAFT_READY.*REVIEW_PENDING"; then
    echo "3. State sequence (ROUTING→DRAFTING→DRAFT_READY→REVIEW_PENDING): PASS"
else
    echo "3. State sequence (ROUTING→DRAFTING→DRAFT_READY→REVIEW_PENDING): FAIL"
    echo "   Actual: $STATE_SEQ"
    FAILS=$((FAILS + 1))
fi

# --- 4. Dispatch exists and is PENDING ---
DISPATCH_STATUS=$(sqlite3 "$DB" "SELECT current_status FROM dispatch_log WHERE workflow_run_id = '$RUN_ID';")
if [[ "$DISPATCH_STATUS" == "PENDING" ]]; then
    echo "4. Dispatch PENDING: PASS"
else
    echo "4. Dispatch PENDING: FAIL — got '$DISPATCH_STATUS'"
    FAILS=$((FAILS + 1))
fi

# --- 5. Dispatch targets Reviewer (port 8643) ---
DISPATCH_TARGET=$(sqlite3 "$DB" "SELECT target_agent || ':' || target_endpoint FROM dispatch_log WHERE workflow_run_id = '$RUN_ID';")
if [[ "$DISPATCH_TARGET" == "hermes-r1:http://127.0.0.1:8643" ]]; then
    echo "5. Dispatch target (hermes-r1:8643): PASS"
else
    echo "5. Dispatch target (hermes-r1:8643): FAIL — got '$DISPATCH_TARGET'"
    FAILS=$((FAILS + 1))
fi

# --- 6. No scope creep ---
CIS_REPO_VAL="${CIS_REPO:-/mnt/projects/cis}"
SCOPE_OK=0
for script in "${CIS_REPO_VAL}/tools/pipeline/drafter_start.py" \
              "${CIS_REPO_VAL}/tools/pipeline/drafter_session_init.py" \
              "${CIS_REPO_VAL}/tools/pipeline/drafter_closeout.py"; do
    if grep -qE 'from.*tier7r|import.*tier7r|from.*router|import.*router|process_manager|classifier|WorkIntent' "$script" 2>/dev/null; then
        echo "6. No scope creep: FAIL — prohibited import in $(basename "$script")"
        grep -nE 'from.*tier7r|import.*tier7r|from.*router|import.*router|process_manager|classifier|WorkIntent' "$script"
        SCOPE_OK=1
    fi
done
if [[ $SCOPE_OK -eq 0 ]]; then
    echo "6. No scope creep: PASS"
else
    FAILS=$((FAILS + 1))
fi

# --- 7. Git clean (no untracked files) ---
UNTRACKED=$(cd "${CIS_REPO:-/mnt/projects/cis}" && git status --porcelain 2>/dev/null | grep '^??' || true)
if [[ -z "$UNTRACKED" ]]; then
    echo "7. Git clean (no untracked files): PASS"
else
    echo "7. Git clean (no untracked files): FAIL"
    echo "$UNTRACKED"
    FAILS=$((FAILS + 1))
fi

echo ""
if [[ $FAILS -eq 0 ]]; then
    echo "RESULT: ALL PASS"
    exit 0
else
    echo "RESULT: $FAILS check(s) failed"
    exit 1
fi
