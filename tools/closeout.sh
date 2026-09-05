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
    local push_status="${13:-}"
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
    "docs/DEV-PIVOT_STATUS.md"
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

# ── Dev-mode report (queue item 1.17) ─────────────────────────────────────────
# REPORTS, NEVER BLOCKS. A stripped agent is a fine state to end a session in —
# it is only a problem when a run starts. This exists so the state is never
# silently carried into tomorrow; the real guard belongs at run entry, which is
# still open work under 1.17.
echo ""
echo "[CIS CLOSEOUT] Step 1b: Dev-mode agent check (report only)..."
DEV_MODE_OUTPUT=""
DEV_MODE_RC=0
if [[ -x "$PROJECT_ROOT/tools/check_dev_mode.sh" ]]; then
    # One invocation, output and exit code together. The `||` is required —
    # set -e is on and this check exits non-zero by design when it finds
    # something. Running it twice could also report two different states.
    DEV_MODE_OUTPUT="$(bash "$PROJECT_ROOT/tools/check_dev_mode.sh" 2>&1)" \
        || DEV_MODE_RC=$?
    while IFS= read -r _line; do
        [[ -n "$_line" ]] && echo "[CIS CLOSEOUT]   $_line"
    done <<< "$DEV_MODE_OUTPUT"
    case "$DEV_MODE_RC" in
        0) DEV_MODE_STATE="all agents clean" ;;
        1) DEV_MODE_STATE="DEV MODE IN EFFECT — restore before any pipeline run (1.17)" ;;
        *) DEV_MODE_STATE="could not check — state unknown, not clean" ;;
    esac
else
    DEV_MODE_STATE="check script missing"
    echo "[CIS CLOSEOUT]   tools/check_dev_mode.sh not found or not executable"
fi
echo "[CIS CLOSEOUT] Dev-mode check: REPORTED (does not block closeout)"

if $CHECK_ONLY; then
    echo ""
    echo "[CIS CLOSEOUT] CHECK COMPLETE — closeout is safe to run."
    echo "[CIS CLOSEOUT] Run 'hermes closeout' to execute."
    exit 0
fi

# ── Ingest knowledge ──────────────────────────────────────────────────────────
# BUILD LIST 1.22. Closeout committed code and never ingested knowledge, so the
# KB only grew when someone remembered. Both ingest tools worked and nothing
# fired them. This is the four lines the item asked for.
#
# REPORT, NEVER BLOCK — same shape as the dev-mode check above. A failed ingest
# must not refuse a session close: the alternative teaches people to skip
# closeout, and then the code stops being committed too.
#
# Every invocation is `|| RC=$?` guarded because `set -e` is on at line 15 and
# these tools exit non-zero on partial work by design.
echo ""
echo "[CIS CLOSEOUT] Step 1c: Ingesting session knowledge (report only)..."
INGEST_STATE="not run"
INGEST_FAILED=0
INGEST_RAN=0
KM_BEFORE="$(sqlite3 "$PROJECT_ROOT/data/cis_memory.db" \
    'SELECT COUNT(*) FROM knowledge_messages;' 2>/dev/null || echo 0)"

# Hermes gateway sessions -> knowledge_messages. SQLite only; no Chroma write,
# so no lock is needed — verified 2026-09-05, the file has no chroma reference.
# Claude Code transcripts -> knowledge_messages. Takes chroma_write itself.
#
# NOT tools/catalog/append_embeddings.py. It writes Chroma through a bare
# chromadb.PersistentClient with NO LOCK (verified 2026-09-05), on the same
# store 0.3 protects — running it from closeout is exactly the concurrent write
# that corrupts a live container read. tools/sync_missing_embeddings.py does the
# same job, takes chroma_write, and is idempotent.
for _tool in "tools/catalog/ingest_sessions.py" \
             "tools/ingest_claude_code_sessions.py" \
             "tools/sync_missing_embeddings.py"; do
    if [[ ! -f "$PROJECT_ROOT/$_tool" ]]; then
        echo "[CIS CLOSEOUT]   SKIP $_tool — not found"
        continue
    fi
    INGEST_RAN=$((INGEST_RAN + 1))
    _rc=0
    _out="$(cd "$PROJECT_ROOT" && timeout 900 python3.12 "$_tool" 2>&1)" || _rc=$?
    if [[ $_rc -eq 0 ]]; then
        echo "[CIS CLOSEOUT]   OK   $_tool"
    else
        INGEST_FAILED=$((INGEST_FAILED + 1))
        echo "[CIS CLOSEOUT]   FAIL $_tool (exit $_rc) — reported, not blocking"
    fi
    echo "$_out" | tail -3 | while IFS= read -r _l; do
        [[ -n "$_l" ]] && echo "[CIS CLOSEOUT]        $_l"
    done
done

KM_AFTER="$(sqlite3 "$PROJECT_ROOT/data/cis_memory.db" \
    'SELECT COUNT(*) FROM knowledge_messages;' 2>/dev/null || echo 0)"
INGEST_STATE="$INGEST_RAN tool(s) run, $INGEST_FAILED failed; knowledge_messages ${KM_BEFORE} -> ${KM_AFTER}"
echo "[CIS CLOSEOUT]   knowledge_messages: ${KM_BEFORE} -> ${KM_AFTER}"
echo "[CIS CLOSEOUT] Ingest: REPORTED (does not block closeout)"

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
if ! python3 tools/gates/gate_build_state_coherence.py; then
    echo ""
    echo "[CIS CLOSEOUT] FAILED at step: gate_build_state_coherence.py"
    echo "[CIS CLOSEOUT] Next action: paste this output to your escalation"
    echo "[CIS CLOSEOUT] advisor or open a new Hermes session with this error."
    _write_spine_record "FAIL" "$START_HEAD" "" "" "1" "PASS" "FAIL" "" "" \
        "gate_build_state_coherence.py" "build state coherence gate failed" \
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
        "final clean check" "repo still dirty after commit" "$LOG_FILE" ""
    exit 1
fi

# ── Write spine record ────────────────────────────────────────────────────────
_write_spine_record "PASS" "$START_HEAD" "$END_HEAD" "" "1" "PASS" "PASS" \
    "$COMMIT_HASH" "" "" "" "$LOG_FILE" "$PUSH_STATUS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[CIS] SESSION CLOSED"
echo "[CIS] HEAD: $END_HEAD"
echo "[CIS] Dev-mode agents: ${DEV_MODE_STATE:-not checked}"
echo "[CIS] Knowledge ingest: ${INGEST_STATE:-not run}"
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
