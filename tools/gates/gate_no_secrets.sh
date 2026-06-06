#!/bin/bash
# gate_no_secrets.sh — Deterministic pre-commit secret/sensitive file blocker
# Tier 1, Artifact 1.4 — CIS Dependency Graph Build Plan v2.0
#
# Usage: gate_no_secrets.sh
#
# Exit 0: PASS — no secrets or sensitive files in staged changes
# Exit 1: FAIL — secrets or sensitive files detected
# Exit 2: ERROR — not a git repo or git unavailable
#
# Design constraints:
#   - Scans staged files only (git index)
#   - No LLM in verification path
#   - Does not modify, stage, or commit files
#   - Does not restart services or call LLMs

set -euo pipefail

CIS_REPO="${CIS_REPO:-/mnt/projects/cis}"

# ── Preflight: git repo ────────────────────────────────────────────

if ! git -C "$CIS_REPO" rev-parse --is-inside-work-tree &>/dev/null; then
    echo "FAIL: $CIS_REPO is not a git repository"
    exit 2
fi

# ── Get staged files ───────────────────────────────────────────────

STAGED=$(git -C "$CIS_REPO" diff --cached --name-only 2>/dev/null)

if [ -z "$STAGED" ]; then
    echo "PASS: no staged files to scan"
    exit 0
fi

# ── Banned filename patterns ───────────────────────────────────────

BANNED_EXTS=(
    '.env'
    '.pem'
    '.key'
    '.p12'
    '.pfx'
    '.sqlite'
    '.db'
    '.tar'
    '.tar.gz'
    '.zip'
)

# Build grep pattern: (\.env|\.pem|\.key|...)$
BANNED_PATTERN=""
for ext in "${BANNED_EXTS[@]}"; do
    # Escape dots for regex
    escaped=$(echo "$ext" | sed 's/\./\\./g')
    if [ -z "$BANNED_PATTERN" ]; then
        BANNED_PATTERN="(${escaped})"
    else
        BANNED_PATTERN="${BANNED_PATTERN}|(${escaped})"
    fi
done
BANNED_PATTERN="(${BANNED_PATTERN})\$"

# ── Check filenames ────────────────────────────────────────────────

FILENAME_FAILS=""
while IFS= read -r f; do
    [ -z "$f" ] && continue
    if echo "$f" | grep -qE "$BANNED_PATTERN"; then
        FILENAME_FAILS="${FILENAME_FAILS}${f}\n"
    fi
done <<< "$STAGED"

if [ -n "$FILENAME_FAILS" ]; then
    echo "FAIL: staged files match banned sensitive patterns"
    echo ""
    echo "Banned files:"
    echo -e "$FILENAME_FAILS" | sort | while read -r f; do [ -n "$f" ] && echo "  $f"; done
    exit 1
fi

# ── Secret content patterns ────────────────────────────────────────

SECRET_PATTERNS=(
    'api_key='
    'secret='
    'password='
    'token='
    '[Aa]uthorization:\s*[Bb]earer'
    'BEGIN PRIVATE KEY'
)

# ── Scan staged text files for secrets ─────────────────────────────

CONTENT_FAILS=""
while IFS= read -r f; do
    [ -z "$f" ] && continue

    # Check if file is binary in the index
    NUMSTAT=$(git -C "$CIS_REPO" diff --cached --numstat -- "$f" 2>/dev/null)
    if echo "$NUMSTAT" | grep -q '^-\t-'; then
        # Binary file — skip
        continue
    fi

    # Get staged content and check each pattern
    STAGED_CONTENT=$(git -C "$CIS_REPO" show ":$f" 2>/dev/null)
    if [ -z "$STAGED_CONTENT" ]; then
        continue
    fi

    for pattern in "${SECRET_PATTERNS[@]}"; do
        if echo "$STAGED_CONTENT" | grep -qiE "$pattern" 2>/dev/null; then
            CONTENT_FAILS="${CONTENT_FAILS}${f}  (matched: ${pattern})\n"
            break  # one match per file is enough
        fi
    done
done <<< "$STAGED"

if [ -n "$CONTENT_FAILS" ]; then
    echo "FAIL: staged files contain likely secrets"
    echo ""
    echo "Files with secret patterns:"
    echo -e "$CONTENT_FAILS" | sort | while read -r f; do [ -n "$f" ] && echo "  $f"; done
    exit 1
fi

echo "PASS: no secrets or sensitive files in staged changes"
exit 0
