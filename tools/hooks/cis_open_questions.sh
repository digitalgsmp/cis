#!/bin/bash
# cis_open_questions.sh — Digression guardrail
# Queries open_questions table in CIS spine and surfaces unresolved items.
# Hooked on pre_llm_call event — injects into agent context before every LLM call.
# Only fires when working directory is /mnt/projects/cis/

set -euo pipefail

CWD="${PWD:-$(pwd)}"
DB_PATH="/mnt/projects/cis/data/cis_memory.db"

# Only fire in CIS working directory
if [[ "$CWD" != /mnt/projects/cis ]] && [[ "$CWD" != /mnt/projects/cis/* ]]; then
    exit 0
fi

# Check DB exists
if [[ ! -f "$DB_PATH" ]]; then
    exit 0
fi

# Query open questions
OPEN_COUNT=$(sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM open_questions WHERE status='OPEN';" 2>/dev/null || echo "0")

if [[ "$OPEN_COUNT" -eq 0 ]]; then
    exit 0
fi

# Format open questions for context injection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPEN QUESTIONS (${OPEN_COUNT} unresolved):"
echo ""

sqlite3 "$DB_PATH" \
    "SELECT priority, question FROM open_questions 
     WHERE status='OPEN' 
     ORDER BY priority DESC, opened_at ASC;" 2>/dev/null | \
while IFS='|' read -r priority question; do
    case $priority in
        3) marker="🔴 HIGH" ;;
        2) marker="🟡 MED" ;;
        *) marker="⚪ LOW" ;;
    esac
    echo "  $marker | $question"
done

echo ""
echo "Address these before starting new work."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
