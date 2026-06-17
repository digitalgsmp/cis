#!/bin/bash
set -euo pipefail

# cis_pre_tool_gate.sh — CIS guardrail hook for Hermes shell hooks
# Fires before every write_file, patch, and terminal call.
# Checks CIS spine for a valid gate record before allowing tool execution
# in the /mnt/projects/cis/ working directory.
#
# Usage: called by Hermes hooks system (not directly)
# Hermes provides $TOOL_NAME env var with the tool being called.
#
# Exit codes:
#   0 = allow tool to execute
#   1 = block tool execution (CIS oversight not satisfied)
#   2 = internal error (fail-open: allow tool)

# ── Tools subject to gate checking ──────────────────────────────────
BLOCKED_TOOLS="write_file patch terminal"

# ── Check if this tool type requires gate validation ─────────────────
if [[ -z "${TOOL_NAME:-}" ]]; then
    # No TOOL_NAME provided — not called from Hermes hooks system
    exit 0
fi

if ! echo "$BLOCKED_TOOLS" | grep -qw "$TOOL_NAME"; then
    # Not a blocked tool — allow through
    exit 0
fi

# ── Check working directory ─────────────────────────────────────────
CWD="${PWD:-$(pwd)}"
if [[ "$CWD" != /mnt/projects/cis ]] && [[ "$CWD" != /mnt/projects/cis/* ]]; then
    # Not inside CIS working directory — allow through
    exit 0
fi

# ── Query spine for valid gate record ───────────────────────────────
DB_PATH="/mnt/projects/cis/data/cis_memory.db"

if [[ ! -f "$DB_PATH" ]]; then
    echo "BLOCKED: CIS database not found at $DB_PATH" >&2
    exit 0  # fail-open: no db to check, don't block real work
fi

if ! command -v sqlite3 &>/dev/null; then
    echo "BLOCKED: sqlite3 not available for gate check" >&2
    exit 0  # fail-open: can't check, don't block
fi

# Check for any completed gate/deliberation run in the last 24 hours
# This proxies for "pre-execution oversight has been performed."
GATE_COUNT=$(sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM workflow_runs 
     WHERE created_at > datetime('now', '-24 hours') 
     AND result = 'CONSENSUS_REACHED';" 2>/dev/null || echo "0")

if [[ "$GATE_COUNT" -gt 0 ]]; then
    # Valid gate record exists — allow
    exit 0
fi

# No valid gate record — block the tool
echo "BLOCKED: pre-execution oversight required. Run gate_runner.sh first." >&2
exit 1
