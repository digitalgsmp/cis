#!/bin/bash
# gate_closeout_complete.sh v2 — Deterministic Closeout Orchestrator
# Tier 6.2 — CIS Dependency Graph Build Plan v2.0
#
# Usage: gate_closeout_complete.sh --run-id <id> --kanban-card-id <id> --node-id <id>
#                                  [--node-description <text>] [--skip-export]
#
# Exit codes:
#   0 — All phases passed. STATE_WRITE completed. Closeout completed.
#   1 — Phase 1 gate failure. STATE_WRITE not reached.
#   2 — STATE_WRITE or export regeneration failure. Phase 2 not reached.
#   3 — Phase 2 gate failure. STATE_WRITE succeeded but postcondition check failed.
#   4 — Configuration error (missing required arg, invalid env, missing required script).
#
# Design: docs/CIS_TIER_6_2_GATE_CLOSEOUT_COMPLETE_V2_DESIGN.md
# Depends on: docs/CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CIS_REPO="${CIS_REPO:-/mnt/projects/cis}"

# ── Default paths ────────────────────────────────────────────────────
STATE_WRITE_SCRIPT="${STATE_WRITE_SCRIPT:-${CIS_REPO}/tools/state_write.py}"
CLOSEOUT_SCRIPT="${CLOSEOUT_SCRIPT:-${CIS_REPO}/tools/closeout.sh}"
GENERATE_ALL_SCRIPT="${GENERATE_ALL_SCRIPT:-${CIS_REPO}/tools/export/generate_all.py}"
EXPORT_MANIFEST_PATH="${EXPORT_MANIFEST_PATH:-${CIS_REPO}/runtime/manifests/EXPORT_MANIFEST.json}"

# ── CLI arg defaults ─────────────────────────────────────────────────
RUN_ID=""
KANBAN_CARD_ID=""
NODE_ID=""
NODE_DESCRIPTION=""
SKIP_EXPORT=false

# ── Parse CLI arguments ──────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --run-id)
            RUN_ID="$2"; shift 2 ;;
        --kanban-card-id)
            KANBAN_CARD_ID="$2"; shift 2 ;;
        --node-id)
            NODE_ID="$2"; shift 2 ;;
        --node-description)
            NODE_DESCRIPTION="$2"; shift 2 ;;
        --skip-export)
            SKIP_EXPORT=true; shift ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Usage: gate_closeout_complete.sh --run-id <id> --kanban-card-id <id> --node-id <id> [--node-description <text>] [--skip-export]" >&2
            exit 4
            ;;
    esac
done

# ── Validate required args ───────────────────────────────────────────
if [ -z "$RUN_ID" ]; then
    echo "ERROR: --run-id is required" >&2
    exit 4
fi
if [ -z "$KANBAN_CARD_ID" ]; then
    echo "ERROR: --kanban-card-id is required" >&2
    exit 4
fi
if [ -z "$NODE_ID" ]; then
    echo "ERROR: --node-id is required" >&2
    exit 4
fi
if [ -z "$NODE_DESCRIPTION" ]; then
    NODE_DESCRIPTION="$NODE_ID"
fi

# ── Resolve git HEAD ─────────────────────────────────────────────────
GIT_HEAD=$(git -C "$CIS_REPO" rev-parse HEAD 2>/dev/null) || {
    echo "ERROR: cannot resolve git HEAD in $CIS_REPO" >&2
    exit 4
}

TIMESTAMP_STARTED=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GATE_RESULTS_FILE="/tmp/gate_results_${RUN_ID}.json"

# ── Helper: json_escape ──────────────────────────────────────────────
# Escapes a string for inclusion in a JSON string value.
# Takes first 500 characters, replaces newlines with spaces, then escapes
# backslash and double-quote for valid JSON.
json_escape() {
    local raw="$1"
    # Truncate to 500 chars
    raw="${raw:0:500}"
    # Replace newlines with spaces, then escape backslash and double-quote.
    # sed processes line-by-line and cannot see literal newlines, so we
    # use tr to normalize newlines first.
    printf '%s' "$raw" | tr '\n' ' ' | sed \
        -e 's/\\/\\\\/g' \
        -e 's/"/\\"/g'
}

# ── Helper: init_results_file ────────────────────────────────────────
init_results_file() {
    cat > "$GATE_RESULTS_FILE" <<JSONSTART
{
  "run_id": "$(json_escape "$RUN_ID")",
  "node_id": "$(json_escape "$NODE_ID")",
  "node_description": "$(json_escape "$NODE_DESCRIPTION")",
  "timestamp_started": "$TIMESTAMP_STARTED",
  "git_head": "$GIT_HEAD",
  "gates": [
JSONSTART
}

# ── Helper: append_gate_result ───────────────────────────────────────
# Args: name phase command exit_code status output_excerpt
# Appends a JSON gate result object to the results file.
# Handles comma placement: first entry gets no leading comma, subsequent do.
append_gate_result() {
    local name="$1"
    local phase="$2"
    local command="$3"
    local exit_code="$4"
    local status="$5"
    local output_excerpt="$6"

    local escaped_name
    local escaped_command
    local escaped_output

    escaped_name=$(json_escape "$name")
    escaped_command=$(json_escape "$command")
    escaped_output=$(json_escape "$output_excerpt")

    # Determine if we need a leading comma
    local comma=""
    if [ "$FIRST_GATE_WRITTEN" = "true" ]; then
        comma=","
    else
        FIRST_GATE_WRITTEN="true"
    fi

    cat >> "$GATE_RESULTS_FILE" <<JSONGATE
${comma}
    {
      "name": "${escaped_name}",
      "phase": "${phase}",
      "command": "${escaped_command}",
      "exit_code": ${exit_code},
      "status": "${status}",
      "output_excerpt": "${escaped_output}"
    }
JSONGATE
}

# ── Helper: finalize_results_file ────────────────────────────────────
finalize_results_file() {
    cat >> "$GATE_RESULTS_FILE" <<JSONEND

  ]
}
JSONEND
}

# ── Helper: run_gate ─────────────────────────────────────────────────
# Runs a gate script, captures output, records result, returns exit code.
# Args: gate_name script_path [args...]
# Returns: gate exit code (0 = PASS, non-zero = FAIL)
run_gate() {
    local name="$1"
    local script_path="$2"
    shift 2
    local args=("$@")

    echo ""
    echo "━━━ GATE: ${name} ━━━"

    local output
    local exit_code

    set +e
    output=$("$script_path" "${args[@]}" 2>&1)
    exit_code=$?
    set -e

    # Truncate output for display
    local display_output="${output:0:300}"
    if [ ${#output} -gt 300 ]; then
        display_output="${display_output}..."
    fi
    echo "$display_output"

    local status
    if [ "$exit_code" -eq 0 ]; then
        status="PASS"
        echo "   RESULT: PASS"
    else
        status="FAIL"
        echo "   RESULT: FAIL (exit ${exit_code})"
    fi

    local phase
    if [ "$CURRENT_PHASE" = "pre" ]; then
        phase="pre"
    else
        phase="post"
    fi

    append_gate_result "$name" "$phase" "$script_path ${args[*]}" "$exit_code" "$status" "$output"

    return "$exit_code"
}

# ── Helper: run_optional_gate ────────────────────────────────────────
# Runs a gate only if its env var is set. If env var is set but script
# is missing, FAILS. If env var is unset, records SKIP.
# Args: env_var_name gate_name script_path [args...]
# Returns: 0 on PASS or SKIP, 1 on FAIL
run_optional_gate() {
    local env_var="$1"
    local name="$2"
    local script_path="$3"
    shift 3
    local args=("$@")

    if [ -z "${!env_var:-}" ]; then
        echo ""
        echo "━━━ GATE: ${name} ━━━"
        echo "   SKIP: ${env_var} not set"
        local phase
        if [ "$CURRENT_PHASE" = "pre" ]; then phase="pre"; else phase="post"; fi
        append_gate_result "$name" "$phase" "$script_path ${args[*]}" 0 "SKIP" "SKIP: ${env_var} not set"
        return 0
    fi

    if [ ! -x "$script_path" ] && [ ! -f "$script_path" ]; then
        echo ""
        echo "━━━ GATE: ${name} ━━━"
        echo "   FAIL: ${env_var} is set but script not found: ${script_path}"
        local phase
        if [ "$CURRENT_PHASE" = "pre" ]; then phase="pre"; else phase="post"; fi
        append_gate_result "$name" "$phase" "$script_path ${args[*]}" 2 "FAIL" "FAIL: ${env_var} set but script missing: ${script_path}"
        return 1
    fi

    run_gate "$name" "$script_path" "${args[@]}"
}

# ── Helper: require_script ───────────────────────────────────────────
# Checks that a script exists and is executable. Exits with code 4 if not.
require_script() {
    local path="$1"
    local label="$2"
    if [ ! -f "$path" ]; then
        echo "ERROR: ${label} not found: ${path}" >&2
        exit 4
    fi
}

# ══════════════════════════════════════════════════════════════════════
# PHASE 1: Pre-STATE_WRITE
# ══════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════"
echo "  gate_closeout_complete.sh v2"
echo "  Run ID:  $RUN_ID"
echo "  Node:    $NODE_ID"
echo "  Started: $TIMESTAMP_STARTED"
echo "═══════════════════════════════════════════"
echo ""
echo "── PHASE 1: Pre-STATE_WRITE ──"

CURRENT_PHASE="pre"
FIRST_GATE_WRITTEN="false"
PHASE1_FAILED=0
init_results_file

# ── Always-on gates ──────────────────────────────────────────────────

GATE_GIT_STATE="${SCRIPT_DIR}/gate_git_state.sh"
require_script "$GATE_GIT_STATE" "gate_git_state.sh"
# Forward expected files if GATE_GIT_EXPECTED_FILES is set
if [ -n "${GATE_GIT_EXPECTED_FILES:-}" ]; then
    # Split on whitespace — each token is a file path
    read -ra EXPECTED_ARRAY <<< "$GATE_GIT_EXPECTED_FILES"
    run_gate "gate_git_state" "$GATE_GIT_STATE" "${EXPECTED_ARRAY[@]}" || PHASE1_FAILED=1
else
    run_gate "gate_git_state" "$GATE_GIT_STATE" || PHASE1_FAILED=1
fi

GATE_NO_SECRETS="${SCRIPT_DIR}/gate_no_secrets.sh"
require_script "$GATE_NO_SECRETS" "gate_no_secrets.sh"
run_gate "gate_no_secrets" "$GATE_NO_SECRETS" || PHASE1_FAILED=1

# ── Optional Tier 1 gates ────────────────────────────────────────────

if [ -n "${GATE_SERVICE_HEALTH_PORT:-}" ] && [ -n "${GATE_SERVICE_HEALTH_EXPECTED:-}" ]; then
    GATE_SERVICE_HEALTH="${SCRIPT_DIR}/gate_service_health.sh"
    run_optional_gate "GATE_SERVICE_HEALTH_PORT" "gate_service_health" \
        "$GATE_SERVICE_HEALTH" "$GATE_SERVICE_HEALTH_PORT" "$GATE_SERVICE_HEALTH_EXPECTED" || PHASE1_FAILED=1
else
    echo ""
    echo "━━━ GATE: gate_service_health ━━━"
    echo "   SKIP: GATE_SERVICE_HEALTH_PORT or GATE_SERVICE_HEALTH_EXPECTED not set"
    append_gate_result "gate_service_health" "pre" "${SCRIPT_DIR}/gate_service_health.sh" 0 "SKIP" "SKIP: env vars not set"
fi

if [ -n "${GATE_ENDPOINT_URL:-}" ] && [ -n "${GATE_ENDPOINT_EXPECTED:-}" ]; then
    GATE_ENDPOINT="${SCRIPT_DIR}/gate_endpoint.sh"
    if [ -n "${GATE_ENDPOINT_AUTH:-}" ]; then
        run_optional_gate "GATE_ENDPOINT_URL" "gate_endpoint" \
            "$GATE_ENDPOINT" "$GATE_ENDPOINT_URL" "$GATE_ENDPOINT_EXPECTED" "$GATE_ENDPOINT_AUTH" || PHASE1_FAILED=1
    else
        run_optional_gate "GATE_ENDPOINT_URL" "gate_endpoint" \
            "$GATE_ENDPOINT" "$GATE_ENDPOINT_URL" "$GATE_ENDPOINT_EXPECTED" || PHASE1_FAILED=1
    fi
else
    echo ""
    echo "━━━ GATE: gate_endpoint ━━━"
    echo "   SKIP: GATE_ENDPOINT_URL or GATE_ENDPOINT_EXPECTED not set"
    append_gate_result "gate_endpoint" "pre" "${SCRIPT_DIR}/gate_endpoint.sh" 0 "SKIP" "SKIP: env vars not set"
fi

if [ -n "${GATE_FILE_EXISTS_PATH:-}" ]; then
    GATE_FILE_EXISTS="${SCRIPT_DIR}/gate_file_exists.sh"
    if [ -n "${GATE_FILE_EXISTS_MINLINES:-}" ]; then
        run_optional_gate "GATE_FILE_EXISTS_PATH" "gate_file_exists" \
            "$GATE_FILE_EXISTS" "$GATE_FILE_EXISTS_PATH" "$GATE_FILE_EXISTS_MINLINES" || PHASE1_FAILED=1
    else
        run_optional_gate "GATE_FILE_EXISTS_PATH" "gate_file_exists" \
            "$GATE_FILE_EXISTS" "$GATE_FILE_EXISTS_PATH" || PHASE1_FAILED=1
    fi
else
    echo ""
    echo "━━━ GATE: gate_file_exists ━━━"
    echo "   SKIP: GATE_FILE_EXISTS_PATH not set"
    append_gate_result "gate_file_exists" "pre" "${SCRIPT_DIR}/gate_file_exists.sh" 0 "SKIP" "SKIP: GATE_FILE_EXISTS_PATH not set"
fi

# ── Pipeline-transition gates ────────────────────────────────────────

PIPELINE_GATES=(
    "GATE_RESEARCH:gate_research_artifact_present:${SCRIPT_DIR}/gate_research_artifact_present.sh"
    "GATE_PROPOSAL:gate_proposal_schema_valid:${SCRIPT_DIR}/gate_proposal_schema_valid.sh"
    "GATE_REVIEW:gate_review_round_valid:${SCRIPT_DIR}/gate_review_round_valid.sh"
    "GATE_CONSENSUS:gate_consensus_signal_valid:${SCRIPT_DIR}/gate_consensus_signal_valid.sh"
    "GATE_ERIC:gate_eric_approval_present:${SCRIPT_DIR}/gate_eric_approval_present.sh"
    "GATE_IMPLEMENT:gate_implementation_artifact_present:${SCRIPT_DIR}/gate_implementation_artifact_present.sh"
)

for entry in "${PIPELINE_GATES[@]}"; do
    IFS=':' read -r env_var gate_name script_path <<< "$entry"
    if [ -n "${!env_var:-}" ]; then
        run_optional_gate "$env_var" "$gate_name" "$script_path" "--kanban-card-id" "$KANBAN_CARD_ID" || PHASE1_FAILED=1
    else
        echo ""
        echo "━━━ GATE: ${gate_name} ━━━"
        echo "   SKIP: ${env_var} not set"
        append_gate_result "$gate_name" "pre" "$script_path --kanban-card-id $KANBAN_CARD_ID" 0 "SKIP" "SKIP: ${env_var} not set"
    fi
done

# ── Check Phase 1 result ─────────────────────────────────────────────

if [ "$PHASE1_FAILED" -ne 0 ]; then
    finalize_results_file
    echo ""
    echo "Phase 1 FAILED — STATE_WRITE not reached."
    echo "Gate results: $GATE_RESULTS_FILE"
    exit 1
fi

echo ""
echo "Phase 1 PASSED — all pre-STATE_WRITE gates passed."

# ══════════════════════════════════════════════════════════════════════
# STATE_WRITE
# ══════════════════════════════════════════════════════════════════════

echo ""
echo "── STATE_WRITE ──"

if [ ! -f "$STATE_WRITE_SCRIPT" ]; then
    echo "STATE_WRITE script not found: $STATE_WRITE_SCRIPT"
    echo "This is expected if state_write.py has not been implemented yet (Tier 6.x)."
    finalize_results_file
    echo ""
    echo "STATE_WRITE SKIPPED — script missing. Phase 2 not reached."
    echo "Gate results: $GATE_RESULTS_FILE"
    exit 2
fi

STATE_WRITE_OUTPUT=""
STATE_WRITE_EXIT=0

set +e
STATE_WRITE_OUTPUT=$(python3 "$STATE_WRITE_SCRIPT" \
    --run-id "$RUN_ID" \
    --node-id "$NODE_ID" \
    --node-description "$NODE_DESCRIPTION" \
    --gate-results "$GATE_RESULTS_FILE" \
    --git-head "$GIT_HEAD" 2>&1)
STATE_WRITE_EXIT=$?
set -e

echo "${STATE_WRITE_OUTPUT:0:500}"

if [ "$STATE_WRITE_EXIT" -ne 0 ]; then
    finalize_results_file
    echo ""
    echo "STATE_WRITE FAILED (exit ${STATE_WRITE_EXIT}) — Phase 2 not reached."
    echo "Gate results: $GATE_RESULTS_FILE"
    exit 2
fi

STATE_WRITE_COMPLETION_TS=$(date +%s)

echo "STATE_WRITE PASSED."

# ══════════════════════════════════════════════════════════════════════
# EXPORT REGENERATION
# ══════════════════════════════════════════════════════════════════════

echo ""
echo "── EXPORT REGENERATION ──"

if [ "$SKIP_EXPORT" = true ]; then
    echo "Export regeneration SKIPPED (--skip-export flag set)."
else
    RUN_GENERATE=false

    if [ ! -f "$EXPORT_MANIFEST_PATH" ]; then
        echo "Export manifest missing: $EXPORT_MANIFEST_PATH"
        RUN_GENERATE=true
    else
        MANIFEST_MTIME=$(stat -c %Y "$EXPORT_MANIFEST_PATH" 2>/dev/null) || MANIFEST_MTIME=0
        if [ "$MANIFEST_MTIME" -lt "$STATE_WRITE_COMPLETION_TS" ]; then
            echo "Export manifest is older than STATE_WRITE completion — regenerating."
            RUN_GENERATE=true
        else
            echo "Export manifest is newer than STATE_WRITE completion — skipping regeneration."
        fi
    fi

    if [ "$RUN_GENERATE" = true ]; then
        if [ ! -f "$GENERATE_ALL_SCRIPT" ]; then
            echo "generate_all.py not found: $GENERATE_ALL_SCRIPT"
            finalize_results_file
            exit 2
        fi

        GENERATE_OUTPUT=""
        GENERATE_EXIT=0
        set +e
        GENERATE_OUTPUT=$(python3 "$GENERATE_ALL_SCRIPT" --run-id "$RUN_ID" 2>&1)
        GENERATE_EXIT=$?
        set -e

        echo "${GENERATE_OUTPUT:0:500}"

        if [ "$GENERATE_EXIT" -ne 0 ]; then
            finalize_results_file
            echo ""
            echo "Export regeneration FAILED (exit ${GENERATE_EXIT}) — Phase 2 not reached."
            echo "Gate results: $GATE_RESULTS_FILE"
            exit 2
        fi
        echo "Export regeneration PASSED."
    fi
fi

# ══════════════════════════════════════════════════════════════════════
# PHASE 2: Post-STATE_WRITE
# ══════════════════════════════════════════════════════════════════════

echo ""
echo "── PHASE 2: Post-STATE_WRITE ──"

CURRENT_PHASE="post"
PHASE2_FAILED=0

# ── gate_export_agreement ────────────────────────────────────────────

if [ "$SKIP_EXPORT" = true ]; then
    echo ""
    echo "━━━ GATE: gate_export_agreement ━━━"
    echo "   SKIP: --skip-export flag set"
    append_gate_result "gate_export_agreement" "post" "${SCRIPT_DIR}/gate_export_agreement.sh" 0 "SKIP" "SKIP: --skip-export flag set"
elif [ -n "${GATE_EXPORT_AGREEMENT:-}" ]; then
    GATE_EXPORT_SCRIPT="${SCRIPT_DIR}/gate_export_agreement.sh"
    run_optional_gate "GATE_EXPORT_AGREEMENT" "gate_export_agreement" "$GATE_EXPORT_SCRIPT" || PHASE2_FAILED=1
else
    echo ""
    echo "━━━ GATE: gate_export_agreement ━━━"
    echo "   SKIP: GATE_EXPORT_AGREEMENT not set"
    append_gate_result "gate_export_agreement" "post" "${SCRIPT_DIR}/gate_export_agreement.sh" 0 "SKIP" "SKIP: GATE_EXPORT_AGREEMENT not set"
fi

# ── gate_db_state ────────────────────────────────────────────────────

if [ -n "${GATE_DB_STATE:-}" ] && [ -n "${GATE_DB_STATE_RUN_ID:-}" ]; then
    GATE_DB_STATE_SCRIPT="${CIS_REPO}/tools/gates/gate_db_state.py"
    run_optional_gate "GATE_DB_STATE" "gate_db_state" \
        "$GATE_DB_STATE_SCRIPT" "value" "workflow_runs" "result" "COMPLETE" \
        "--where" "id" "$GATE_DB_STATE_RUN_ID" || PHASE2_FAILED=1

    if [ -n "${GATE_DB_STATE_ROUND_COUNT:-}" ]; then
        run_optional_gate "GATE_DB_STATE" "gate_db_state_round_count" \
            "$GATE_DB_STATE_SCRIPT" "count" "deliberation_rounds" "$GATE_DB_STATE_ROUND_COUNT" \
            "--where" "run_id" "$GATE_DB_STATE_RUN_ID" || PHASE2_FAILED=1
    fi
else
    echo ""
    echo "━━━ GATE: gate_db_state ━━━"
    echo "   SKIP: GATE_DB_STATE or GATE_DB_STATE_RUN_ID not set"
    append_gate_result "gate_db_state" "post" "${CIS_REPO}/tools/gates/gate_db_state.py" 0 "SKIP" "SKIP: GATE_DB_STATE or GATE_DB_STATE_RUN_ID not set"
fi

# ── Check Phase 2 result ─────────────────────────────────────────────

if [ "$PHASE2_FAILED" -ne 0 ]; then
    echo ""
    echo "Phase 2 FAILED — STATE_WRITE succeeded but postcondition check failed."
    echo "Spine rows exist. Closeout NOT completed. Verification gap detected."
    echo "Gate results: $GATE_RESULTS_FILE"
    finalize_results_file
    exit 3
fi

echo ""
echo "Phase 2 PASSED — all post-STATE_WRITE gates passed."

# ══════════════════════════════════════════════════════════════════════
# CLOSEOUT
# ══════════════════════════════════════════════════════════════════════

echo ""
echo "── CLOSEOUT ──"

CLOSEOUT_MANIFEST="${CIS_REPO}/runtime/manifests/CLOSEOUT_${RUN_ID}.json"

if [ ! -f "$CLOSEOUT_SCRIPT" ]; then
    echo "closeout.sh not found: $CLOSEOUT_SCRIPT"
    echo "closeout.sh missing — closeout incomplete. Node is not DONE."
    echo ""
    echo "All gates PASSED. STATE_WRITE completed. Closeout artifact NOT written."
    echo "Gate results: $GATE_RESULTS_FILE"
    echo "Expected manifest: $CLOSEOUT_MANIFEST"
    append_gate_result "closeout" "closeout" "$CLOSEOUT_SCRIPT --run-id $RUN_ID --node-id $NODE_ID" 3 "FAIL" "FAIL: closeout.sh not found at $CLOSEOUT_SCRIPT"
    finalize_results_file
    exit 3
fi

CLOSEOUT_OUTPUT=""
CLOSEOUT_EXIT=0

set +e
CLOSEOUT_OUTPUT=$("$CLOSEOUT_SCRIPT" \
    --run-id "$RUN_ID" \
    --node-id "$NODE_ID" \
    --node-description "$NODE_DESCRIPTION" \
    --manifest-path "$CLOSEOUT_MANIFEST" 2>&1)
CLOSEOUT_EXIT=$?
set -e

echo "${CLOSEOUT_OUTPUT:0:500}"

if [ "$CLOSEOUT_EXIT" -ne 0 ]; then
    echo ""
    echo "Closeout script FAILED (exit ${CLOSEOUT_EXIT})."
    echo "All gates passed and STATE_WRITE completed, but CLOSEOUT_*.md was not written."
    echo "Gate results: $GATE_RESULTS_FILE"
    append_gate_result "closeout" "closeout" "$CLOSEOUT_SCRIPT --run-id $RUN_ID --node-id $NODE_ID" "$CLOSEOUT_EXIT" "FAIL" "FAIL: closeout.sh exit ${CLOSEOUT_EXIT}: ${CLOSEOUT_OUTPUT:0:400}"
    finalize_results_file
    exit 3
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  CLOSEOUT COMPLETE"
echo "  Run ID:  $RUN_ID"
echo "  Node:    $NODE_ID"
echo "═══════════════════════════════════════════"
append_gate_result "closeout" "closeout" "$CLOSEOUT_SCRIPT --run-id $RUN_ID --node-id $NODE_ID" 0 "PASS" "CLOSEOUT COMPLETE: $CLOSEOUT_OUTPUT"
finalize_results_file
exit 0
