#!/bin/bash
# _gate_common.sh — Shared utilities for Tier 6.4 pipeline-transition gates
# Source this in each gate script: source "$(dirname "$0")/_gate_common.sh"
# Do not execute directly.

set -euo pipefail

# ── Card ID resolution ───────────────────────────────────────────────

# resolve_card_id: parse --kanban-card-id from args, fall back to env var.
# Prints the card ID to stdout or exits 2 if none found.
# Consumes --kanban-card-id <id> from the positional arg list.
resolve_card_id() {
    local card_id=""
    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --kanban-card-id)
                if [[ -z "${2:-}" ]]; then
                    echo "ERROR: --kanban-card-id requires a value" >&2
                    exit 2
                fi
                card_id="$2"
                shift 2
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    # Rebuild $@ for the caller (so they can check for unexpected args)
    set -- "${args[@]}"
    CARD_ID="${card_id:-${CIS_KANBAN_CARD_ID:-}}"
    if [[ -z "$CARD_ID" ]]; then
        echo "ERROR: no card ID — use --kanban-card-id <id> or set \$CIS_KANBAN_CARD_ID" >&2
        exit 2
    fi
}

# ── Card body read ───────────────────────────────────────────────────

# read_card_body: calls hermes kanban show --json, extracts body field.
# Prints body text to stdout or exits 2 on any failure.
read_card_body() {
    local card_id="$1"

    if ! command -v hermes &>/dev/null; then
        echo "ERROR: hermes CLI not available on PATH" >&2
        exit 2
    fi

    local json_output
    json_output=$(hermes kanban show "$card_id" --json 2>&1) || {
        echo "ERROR: hermes kanban show failed for card $card_id" >&2
        exit 2
    }

    # Extract body using Python (established pattern from gate_export_agreement.sh)
    local body
    if ! body=$(echo "$json_output" | python3 -c "
import sys, json
raw = sys.stdin.read().strip()
if not raw.startswith('{'):
    print(f'ERROR: hermes kanban returned non-JSON: {raw[:200]}', file=sys.stderr)
    sys.exit(2)
try:
    data = json.loads(raw)
    task = data.get('task', {})
    body = task.get('body', '')
    if not isinstance(body, str):
        print('ERROR: body field is not a string', file=sys.stderr)
        sys.exit(2)
    print(body, end='')
except json.JSONDecodeError as e:
    print(f'ERROR: JSON parse failed: {e}', file=sys.stderr)
    sys.exit(2)
except Exception as e:
    print(f'ERROR: unexpected: {e}', file=sys.stderr)
    sys.exit(2)
"); then
        exit 2
    fi

    if [[ -z "$body" ]]; then
        echo "ERROR: empty or missing body in kanban card $card_id" >&2
        exit 2
    fi

    echo "$body"
}
