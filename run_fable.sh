#!/bin/bash
# run_fable.sh — Feed the CIS codebase to Claude Code (Fable) for analysis
# Usage: docker exec -it cis-pipeline /workspace/cis/run_fable.sh
#
# Prerequisites:
#   1. Claude Code logged in: docker exec -it cis-pipeline claude
#      (one-time, follow the browser link to log in with your subscription)
#   2. After login, run this script.

set -e

PROMPT_FILE="/workspace/cis/fable_prompt.md"
OUTPUT_FILE="/workspace/cis/FABLE_RECOMMENDATION_REPORT.md"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: $PROMPT_FILE not found"
    exit 1
fi

echo "=== Running Fable analysis ==="
echo "=== Evaluating CIS pipeline usability ==="
echo "=== This may take several minutes ==="
echo ""

# Run Claude Code non-interactively with the prompt
claude -p "$(cat $PROMPT_FILE)" \
    --allowedTools "Read,Write,Bash(grep:*),Bash(find:*),Bash(cat:*),Bash(ls:*),Bash(wc:*),Bash(head:*),Bash(tail:*),Bash(sqlite3:*),Bash(git:*)" \
    --output-format text \
    2>&1 | tee /tmp/fable_output.txt

echo ""
echo "=== Fable analysis complete ==="

if [ -f "$OUTPUT_FILE" ]; then
    echo "=== Report: $OUTPUT_FILE ($(wc -l < $OUTPUT_FILE) lines) ==="
else
    echo "=== WARNING: Report not created — check /tmp/fable_output.txt ==="
fi
