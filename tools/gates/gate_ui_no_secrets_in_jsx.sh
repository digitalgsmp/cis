#!/usr/bin/env bash
# gate_ui_no_secrets_in_jsx.sh — Tier 10 security gate S3.
# Scans new Tier 10 JSX files for hardcoded secret patterns.
# Exit 0 = PASS, exit 1 = FAIL.

PAGES_DIR="/mnt/projects/cis/runtime/ui/src/pages"
NEW_FILES=("PipelinePage.jsx" "EricGatePage.jsx" "ArchiveSearchPage.jsx" "SessionArchivePage.jsx" "DecisionsPage.jsx")

# Common secret patterns
PATTERNS=(
    'sk-[a-zA-Z0-9]{20,}'        # OpenAI key
    'gh[pousr]_[a-zA-Z0-9]{20,}'  # GitHub token
    'AKIA[A-Z0-9]{16}'            # AWS access key
    'eyJ[a-zA-Z0-9\-_]{10,}\.[a-zA-Z0-9\-_]{10,}'  # JWT
    'Bearer [a-zA-Z0-9\-_]{20,}'  # Bearer token
)

FAILURES=0
for fname in "${NEW_FILES[@]}"; do
    fpath="$PAGES_DIR/$fname"
    if [[ ! -f "$fpath" ]]; then
        echo "WARN: $fpath not found (skipping)"
        continue
    fi
    for pattern in "${PATTERNS[@]}"; do
        if grep -qE "$pattern" "$fpath" 2>/dev/null; then
            echo "FAIL: Secret pattern matched in $fname: $pattern"
            FAILURES=$((FAILURES + 1))
        fi
    done
done

if [[ $FAILURES -gt 0 ]]; then
    echo "FAIL: $FAILURES secret pattern(s) found"
    exit 1
fi

echo "PASS: No secrets in Tier 10 JSX files"
exit 0
