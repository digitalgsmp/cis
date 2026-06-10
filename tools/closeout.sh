#!/usr/bin/env bash
# tools/closeout.sh — CIS deterministic session closeout engine
# Invoked by: hermes wrapper (hermes closeout / hermes closeout --check)
# Future: router OPERATOR_COMMAND path calls same script
#
# --check mode: read-only safety check, no regeneration or commit
# Normal mode: full closeout — regenerate, gate, commit, verify clean
#
# Writes result to session_closeouts table in SQLite spine.
# Logs to runtime/logs/closeout/YYYYMMDD_HHMMSS_closeout.log
#
# SESSION CLOSED is printed only if final git status --short is empty.
# Any unexpected dirty files block closeout before regeneration begins.

set -euo pipefail

PROJECT_ROOT="${CIS_PROJECT_ROOT:-/mnt/projects/cis}"
DB_PATH="${CIS_DB_PATH:-$PROJECT_ROOT/data/cis_memory.db}"
LOG_DIR="$PROJECT_ROOT/runtime/logs/closeout"
CHECK_ONLY=false

# Parse --check flag
for arg in "$@"; do
    if [[ "$arg" == "--check" ]]; then
        CHECK_ONLY=true
    fi
done

mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/${TIMESTAMP}_closeout.log"
STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Tee all output to log file
exec > >(tee -a "$LOG_FILE") 2>&1

# ── Spine record writer (must be defined before any call) ─────────────────────
_write_spine_record() {
    local status="$1"
    local start_head="$2"
    local end_head="$3"
    local dirty_before="$4"
    local generated="$5"
    local export_status="$6"
    local coherence_status="$7"
    local commit_hash="$8"
    local dirty_after="$9"
    local failure_step="${10}"
    local failure_summary="${11}"
    local log_path="${12}"
    local push_status="${13}"
    local completed_at
    completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    sqlite3 "$DB_PATH" \
"INSERT INTO session_closeouts
    (started_at, completed_at, status, start_head, end_head,
     dirty_before_json, dirty_after_json, generated_context,
     export_agreement_status, build_state_coherence_status,
     commit_hash, log_path, failure_step, failure_summary, created_by,
     push_status)
VALUES
    ('$STARTED_AT', '$completed_at', '$status', '$start_head', '$end_head',
     '$(echo "$dirty_before" | sed "s/'/''/g")',
     '$(echo "$dirty_after" | sed "s/'/''/g")',
     $generated, '$export_status', '$coherence_status',
     '$commit_hash', '$log_path',
     '$(echo "$failure_step" | sed "s/'/''/g")',
     '$(echo "$failure_summary" | sed "s/'/''/g")',
     'operator_command',
     '$push_status');" 2>/dev/null || \
    echo "[CIS CLOSEOUT] Warning: could not write spine record" >&2
}

echo "[CIS CLOSEOUT] Started at $STARTED_AT"
echo "[CIS CLOSEOUT] Log: $LOG_FILE"
if $CHECK_ONLY; then
    echo "[CIS CLOSEOUT] Mode: CHECK ONLY (no regeneration or commit)"
else
    echo "[CIS CLOSEOUT] Mode: FULL CLOSEOUT"
fi
echo ""

cd "$PROJECT_ROOT" || {
    echo "[CIS CLOSEOUT] BLOCKED: could not cd to $PROJECT_ROOT"
    _write_spine_record "BLOCKED" "" "" "" "0" "" "" "" "" "cd to project root" \
        "could not cd to $PROJECT_ROOT" "$LOG_FILE"
    exit 1
}

START_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "[CIS CLOSEOUT] Start HEAD: $START_HEAD"

# ── Dirty file guard ──────────────────────────────────────────────────────────
# Allowed dirty files before closeout. Anything else blocks.
ALLOWED_DIRTY=(
    "AGENTS.md"
    "PROJECT_CONTEXT_PACK_UPLOAD/"
    "runtime/manifests/EXPORT_MANIFEST.json"
    "cis_kernel/source/SESSION_LOG.md"
    "runtime/memory/current_context.json"
)

echo "[CIS CLOSEOUT] Step 1/6: Checking for unexpected dirty files..."
DIRTY_FILES=$(git status --short 2>/dev/null || true)

if [[ -n "$DIRTY_FILES" ]]; then
    UNEXPECTED=""
    while IFS= read -r line; do
        FILEPATH=$(echo "$line" | awk '{print $2}')
        IS_ALLOWED=false
        for allowed in "${ALLOWED_DIRTY[@]}"; do
            if [[ "$FILEPATH" == "$allowed" ]] || \
               [[ "$FILEPATH" == ${allowed%/}/* ]]; then
                IS_ALLOWED=true
                break
            fi
        done
        if ! $IS_ALLOWED; then
            UNEXPECTED="$UNEXPECTED\n  $line"
        fi
    done <<< "$DIRTY_FILES"

    if [[ -n "$UNEXPECTED" ]]; then
        echo ""
        echo "[CIS CLOSEOUT] BLOCKED: unexpected dirty files found:"
        echo -e "$UNEXPECTED"
        echo ""
        echo "[CIS CLOSEOUT] What this means: implementation work may be"
        echo "[CIS CLOSEOUT] unfinished or uncommitted. Closeout would regenerate"
        echo "[CIS CLOSEOUT] context from an incomplete state."
        echo "[CIS CLOSEOUT] Next action: ask Hermes to inspect git status,"
        echo "[CIS CLOSEOUT] commit or stash unfinished work, then retry closeout."
        _write_spine_record "BLOCKED" "$START_HEAD" "" \
            "$(echo -e "$UNEXPECTED")" "0" "" "" "" "" \
            "dirty file guard" "unexpected dirty files: $(echo -e "$UNEXPECTED")" \
            "$LOG_FILE"
        exit 1
    fi
fi

echo "[CIS CLOSEOUT] Dirty file check: PASS"

if $CHECK_ONLY; then
    echo ""
    echo "[CIS CLOSEOUT] CHECK COMPLETE — closeout is safe to run."
    echo "[CIS CLOSEOUT] Run 'hermes closeout' to execute."
    exit 0
fi

# ── Regenerate context ────────────────────────────────────────────────────────
echo ""
echo "[CIS CLOSEOUT] Step 2/6: Regenerating context..."
if ! python3 tools/export/generate_all.py; then
    echo ""
    echo "[CIS CLOSEOUT] FAILED at step: generate_all.py"
    echo "[CIS CLOSEOUT] Next action: paste this output to your escalation"
    echo "[CIS CLOSEOUT] advisor or open a new Hermes session with this error."
    _write_spine_record "FAIL" "$START_HEAD" "" "" "0" "" "" "" "" \
        "generate_all.py" "generate_all.py exited non-zero" "$LOG_FILE"
    exit 1
fi
echo "[CIS CLOSEOUT] Context regeneration: PASS"

# ── Export agreement gate ─────────────────────────────────────────────────────
echo ""
echo "[CIS CLOSEOUT] Step 3/6: Verifying export agreement..."
if ! bash tools/gates/gate_export_agreement.sh; then
    echo ""
    echo "[CIS CLOSEOUT] FAILED at step: gate_export_agreement.sh"
    echo "[CIS CLOSEOUT] Next action: paste this output to your escalation"
    echo "[CIS CLOSEOUT] advisor or open a new Hermes session with this error."
    _write_spine_record "FAIL" "$START_HEAD" "" "" "1" "FAIL" "" "" "" \
        "gate_export_agreement.sh" "export agreement gate failed" "$LOG_FILE"
    exit 1
fi
echo "[CIS CLOSEOUT] Export agreement: PASS"

# ── Build state coherence gate ────────────────────────────────────────────────
echo ""
echo "[CIS CLOSEOUT] Step 4/6: Verifying build state coherence..."
if ! bash tools/gates/gate_build_state_coherence.sh; then
    echo ""
    echo "[CIS CLOSEOUT] FAILED at step: gate_build_state_coherence.sh"
    echo "[CIS CLOSEOUT] Next action: paste this output to your escalation"
    echo "[CIS CLOSEOUT] advisor or open a new Hermes session with this error."
    _write_spine_record "FAIL" "$START_HEAD" "" "" "1" "PASS" "FAIL" "" "" \
        "gate_build_state_coherence.sh" "build state coherence gate failed" \
        "$LOG_FILE"
    exit 1
fi
echo "[CIS CLOSEOUT] Build state coherence: PASS"

# ── Stage generated context ───────────────────────────────────────────────────
echo ""
echo "[CIS CLOSEOUT] Step 5/6: Staging generated context..."
git add \
    AGENTS.md \
    PROJECT_CONTEXT_PACK_UPLOAD/ \
    runtime/manifests/EXPORT_MANIFEST.json \
    2>/dev/null || true
git status --short

# ── Commit ────────────────────────────────────────────────────────────────────
echo ""
echo "[CIS CLOSEOUT] Step 6/6: Committing..."
COMMIT_HASH=""
if git diff --cached --quiet; then
    echo "[CIS CLOSEOUT] Nothing to commit — context already current."
else
    if ! git commit -m "Regenerate context after session closeout"; then
        echo ""
        echo "[CIS CLOSEOUT] FAILED at step: git commit"
        echo "[CIS CLOSEOUT] Next action: paste this output to your escalation"
        echo "[CIS CLOSEOUT] advisor or open a new Hermes session with this error."
        _write_spine_record "FAIL" "$START_HEAD" "" "" "1" "PASS" "PASS" "" "" \
            "git commit" "git commit failed" "$LOG_FILE"
        exit 1
    fi
    COMMIT_HASH=$(git rev-parse --short HEAD)
fi

# ── Push to GitHub ────────────────────────────────────────────────────────────
echo ""
echo "[CIS CLOSEOUT] Step 6b: Pushing to GitHub..."
PUSH_STATUS="SKIP"
if git remote get-url origin &>/dev/null; then
    PUSH_OUT=$(git push origin master 2>&1)
    PUSH_EXIT=$?
    echo "$PUSH_OUT"
    if [ $PUSH_EXIT -eq 0 ]; then
        PUSH_STATUS="PASS"
        echo "[CIS CLOSEOUT] GitHub push: PASS"
    else
        PUSH_STATUS="FAIL"
        echo "[CIS CLOSEOUT] WARNING: GitHub push failed — session will still"
        echo "[CIS CLOSEOUT] close locally. GitHub is not current."
        echo "[CIS CLOSEOUT] Next action: run 'git push origin master' when"
        echo "[CIS CLOSEOUT] connectivity is available."
    fi
else
    echo "[CIS CLOSEOUT] No remote origin configured — skipping push."
fi

# ── Final clean state check ───────────────────────────────────────────────────
END_HEAD=$(git rev-parse --short HEAD)
FINAL_STATUS=$(git status --short 2>/dev/null || true)
DIRTY_AFTER=""

if [[ -n "$FINAL_STATUS" ]]; then
    while IFS= read -r line; do
        FILEPATH=$(echo "$line" | awk '{print $2}')
        IS_ALLOWED=false
        for allowed in "${ALLOWED_DIRTY[@]}"; do
            if [[ "$FILEPATH" == "$allowed" ]] || \
               [[ "$FILEPATH" == ${allowed%/}/* ]]; then
                IS_ALLOWED=true
                break
            fi
        done
        if ! $IS_ALLOWED; then
            DIRTY_AFTER="$DIRTY_AFTER\n  $line"
        fi
    done <<< "$FINAL_STATUS"
fi

COMPLETED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if [[ -n "$DIRTY_AFTER" ]]; then
    echo ""
    echo "[CIS CLOSEOUT] INCOMPLETE — repo still dirty after commit:"
    echo -e "$DIRTY_AFTER"
    echo "[CIS CLOSEOUT] Next action: paste this output to your escalation"
    echo "[CIS CLOSEOUT] advisor or open a new Hermes session with this error."
    _write_spine_record "FAIL" "$START_HEAD" "$END_HEAD" "" "1" "PASS" "PASS" \
        "$COMMIT_HASH" "$(echo -e "$DIRTY_AFTER")" \
        "final clean check" "repo still dirty after commit" "$LOG_FILE"
    exit 1
fi

# ── Write spine record ────────────────────────────────────────────────────────
_write_spine_record "PASS" "$START_HEAD" "$END_HEAD" "" "1" "PASS" "PASS" \
    "$COMMIT_HASH" "" "" "" "$LOG_FILE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[CIS] SESSION CLOSED"
echo "[CIS] HEAD: $END_HEAD"
if [[ -n "$COMMIT_HASH" ]]; then
    echo "[CIS] Committed regenerated context: yes ($COMMIT_HASH)"
else
    echo "[CIS] Committed regenerated context: no (already current)"
fi
echo "[CIS] Repo clean: yes"
if [[ "$PUSH_STATUS" == "PASS" ]]; then
    echo "[CIS] GitHub push: yes"
elif [[ "$PUSH_STATUS" == "FAIL" ]]; then
    echo "[CIS] GitHub push: FAILED — run 'git push origin master' manually"
else
    echo "[CIS] GitHub push: skipped (no remote configured)"
fi
echo "[CIS] Log: $LOG_FILE"
echo "[CIS] Next safe action: open new session in READ_ONLY_STANDING_BY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
exit 0
