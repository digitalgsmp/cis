#!/bin/bash
# _gate_common.sh — Shared utilities for pipeline-transition gates
# Source this in each gate script: source "$(dirname "$0")/_gate_common.sh"
# Do not execute directly.
# Kanban retired per ADR-013. All gates now query SQLite spine directly.

set -euo pipefail

CIS_DB_PATH="${CIS_DB_PATH:-/mnt/projects/cis/data/cis_memory.db}"

# resolve_run_id: parse --run-id from args, fall back to $CIS_RUN_ID env var.
# Sets RUN_ID variable. Exits 2 if none found.
resolve_run_id() {
    local run_id=""
    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --run-id)
                if [[ -z "${2:-}" ]]; then
                    echo "ERROR: --run-id requires a value" >&2
                    exit 2
                fi
                run_id="$2"
                shift 2
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    RUN_ID="${run_id:-${CIS_RUN_ID:-}}"
    if [[ -z "$RUN_ID" ]]; then
        echo "ERROR: no run ID — use --run-id <id> or set \$CIS_RUN_ID" >&2
        exit 2
    fi
}

# query_spine: run a sqlite3 query against the spine DB.
# Usage: query_spine "SELECT ..."
# Exits 2 on sqlite3 failure.
query_spine() {
    local sql="$1"
    local result
    result=$(sqlite3 "$CIS_DB_PATH" "$sql" 2>&1) || {
        echo "ERROR: sqlite3 query failed: $result" >&2
        exit 2
    }
    echo "$result"
}
