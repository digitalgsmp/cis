#!/usr/bin/env bash
# gate_reviewer_closeout.sh — Tier 11D: Verify Reviewer closeout invariants
# Usage: bash tools/gates/gate_reviewer_closeout.sh --run-id WORKFLOW_RUN_ID
set -euo pipefail

DB="${CIS_DB_PATH:-/mnt/projects/cis/data/cis_memory.db}"
REPO="${CIS_REPO:-/mnt/projects/cis}"
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

echo "=== Tier 11D: Reviewer Closeout Gate ==="
echo "Run ID: $RUN_ID"
echo ""

# --- 1. Migration 0012 applied ---
if sqlite3 "$DB" "PRAGMA table_info(lifecycle_events);" | grep -q workflow_run_id && \
   sqlite3 "$DB" "PRAGMA table_info(dispatch_log);" | grep -q workflow_run_id; then
    echo "1. Migration 0012:                        PASS"
else
    echo "1. Migration 0012:                        FAIL — workflow_run_id column missing"
    FAILS=$((FAILS + 1))
fi

# --- 2. Full lifecycle trail (≥7 events) ---
EVENT_COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM lifecycle_events WHERE workflow_run_id = '$RUN_ID';")
if [[ "$EVENT_COUNT" -ge 7 ]]; then
    echo "2. Full lifecycle trail (≥7 events):      PASS ($EVENT_COUNT events)"
else
    echo "2. Full lifecycle trail (≥7 events):      FAIL — got $EVENT_COUNT events"
    FAILS=$((FAILS + 1))
fi

# --- 3. Correct state sequence ---
STATE_SEQ=$(sqlite3 "$DB" "SELECT to_state FROM lifecycle_events WHERE workflow_run_id = '$RUN_ID' ORDER BY id ASC;")
EXPECTED="ROUTING.*DRAFTING.*DRAFT_READY.*REVIEW_PENDING.*REVIEWING.*REVIEW_COMPLETE"
if echo "$STATE_SEQ" | tr '\n' ' ' | grep -qE "$EXPECTED"; then
    echo "3. State sequence correct:                 PASS"
else
    echo "3. State sequence correct:                 FAIL"
    echo "   Expected: $EXPECTED"
    echo "   Actual: $STATE_SEQ"
    FAILS=$((FAILS + 1))
fi

# --- 4. Drafter dispatch SUCCESS ---
DISPATCH_STATUS=$(sqlite3 "$DB" \
    "SELECT current_status FROM dispatch_log
     WHERE workflow_run_id = '$RUN_ID' AND source_actor = 'drafter';")
if [[ "$DISPATCH_STATUS" == "SUCCESS" ]]; then
    echo "4. Drafter dispatch SUCCESS:              PASS"
else
    echo "4. Drafter dispatch SUCCESS:              FAIL — got '$DISPATCH_STATUS'"
    FAILS=$((FAILS + 1))
fi

# --- 5. Verdict routing valid ---
LAST_TO=$(sqlite3 "$DB" \
    "SELECT to_state FROM lifecycle_events
     WHERE workflow_run_id = '$RUN_ID'
     ORDER BY id DESC LIMIT 1;")
if [[ "$LAST_TO" == "REVISE_REQUESTED" || "$LAST_TO" == "ERIC_APPROVAL_GATE" ]]; then
    echo "5. Verdict routing valid:                 PASS ($LAST_TO)"
else
    echo "5. Verdict routing valid:                 FAIL — got '$LAST_TO'"
    FAILS=$((FAILS + 1))
fi

# --- 6. Return dispatch if REVISE_REQUESTED ---
if [[ "$LAST_TO" == "REVISE_REQUESTED" ]]; then
    RETURN_DISP=$(sqlite3 "$DB" \
        "SELECT current_status FROM dispatch_log
         WHERE workflow_run_id = '$RUN_ID' AND source_actor = 'reviewer'
         AND target_agent = 'hermes-v4pro';")
    if [[ "$RETURN_DISP" == "PENDING" ]]; then
        echo "6. Return dispatch (REVISE_REQUESTED):     PASS"
    else
        echo "6. Return dispatch (REVISE_REQUESTED):     FAIL — got '$RETURN_DISP'"
        FAILS=$((FAILS + 1))
    fi
else
    echo "6. Return dispatch (if REVISE_REQUESTED):  N/A (routing=$LAST_TO)"
fi

# --- 7. Deliberation round recorded (M2: reviewer_signal not reviewer_status) ---
ROUND_SIGNAL=$(sqlite3 "$DB" \
    "SELECT reviewer_signal FROM deliberation_rounds
     WHERE run_id = '$RUN_ID' ORDER BY round_number DESC LIMIT 1;")
if [[ -n "$ROUND_SIGNAL" ]]; then
    echo "7. Deliberation round recorded:           PASS (signal=$ROUND_SIGNAL)"
else
    echo "7. Deliberation round recorded:           FAIL — no round found"
    FAILS=$((FAILS + 1))
fi

# --- 8. No scope creep ---
SCOPE_OK=0
for script in "$REPO/tools/pipeline/reviewer_pickup.py" \
              "$REPO/tools/pipeline/reviewer_session_init.py" \
              "$REPO/tools/pipeline/reviewer_closeout.py"; do
    if grep -qE 'from.*tier7r|import.*tier7r|from.*router|import.*router|process_manager|classifier|WorkIntent' \
        "$script" 2>/dev/null; then
        echo "8. No scope creep:                         FAIL — prohibited import in $(basename "$script")"
        grep -nE 'from.*tier7r|import.*tier7r|from.*router|import.*router|process_manager|classifier|WorkIntent' \
            "$script"
        SCOPE_OK=1
    fi
done
if [[ $SCOPE_OK -eq 0 ]]; then
    echo "8. No scope creep:                         PASS"
else
    FAILS=$((FAILS + 1))
fi

# --- 9. Git clean (no untracked files) ---
UNTRACKED=$(cd "$REPO" && git status --porcelain 2>/dev/null | grep '^??' || true)
if [[ -z "$UNTRACKED" ]]; then
    echo "9. Git clean:                              PASS"
else
    echo "9. Git clean:                              FAIL"
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
