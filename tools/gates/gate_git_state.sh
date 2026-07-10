#!/bin/bash
# gate_git_state.sh — Deterministic git working tree verification
# Tier 1, Artifact 1.1 — CIS Dependency Graph Build Plan v2.0
#
# Usage: gate_git_state.sh [expected_files...]
#
# Exit 0: PASS — working tree clean or only expected files changed
# Exit 1: FAIL — unexpected changes detected
# Exit 2: ERROR — git unavailable or repo inaccessible
#
# Design constraints:
#   - No LLM in verification path
#   - Does not stage, commit, delete, or modify any project files
#   - Works from any directory via git -C /mnt/projects/cis

set -euo pipefail

CIS_REPO="${CIS_REPO:-/mnt/projects/cis}"

# ── Preflight ──────────────────────────────────────────────────────

if ! git -C "$CIS_REPO" rev-parse --is-inside-work-tree &>/dev/null; then
    echo "FAIL: $CIS_REPO is not a git repository"
    exit 2
fi

# ── Gather working tree state ──────────────────────────────────────

# All uncommitted changes: modified + deleted + untracked (but not ignored)
DIRTY=$(git -C "$CIS_REPO" status --porcelain)

if [ -z "$DIRTY" ]; then
    echo "PASS: git working tree clean"
    exit 0
fi

# ── Check expected files ───────────────────────────────────────────

if [ $# -gt 0 ]; then
    # Collect changed files: modified (git diff --name-only) + untracked (git ls-files --others --exclude-standard)
    CHANGED_FILES=$(
        {
            git -C "$CIS_REPO" diff --name-only HEAD
            git -C "$CIS_REPO" diff --name-only --cached HEAD
            git -C "$CIS_REPO" ls-files --others --exclude-standard
        } | sort -u
    )

    # Collect unexpected files
    UNEXPECTED=""
    MATCHED=""
    while IFS= read -r f; do
        [ -z "$f" ] && continue
        expected=0
        for ef in "$@"; do
            # Match exact path or path suffix
            if [[ "$f" == "$ef" ]] || [[ "$f" == *"$ef" ]]; then
                expected=1
                break
            fi
        done
        if [ "$expected" -eq 1 ]; then
            MATCHED="${MATCHED}${f}\n"
        else
            UNEXPECTED="${UNEXPECTED}${f}\n"
        fi
    done <<< "$CHANGED_FILES"

    if [ -n "$UNEXPECTED" ]; then
        echo "FAIL: unexpected changes in working tree"
        echo ""
        echo "Unexpected files:"
        echo -e "$UNEXPECTED" | sort | while read -r f; do [ -n "$f" ] && echo "  $f"; done
        if [ -n "$MATCHED" ]; then
            echo ""
            echo "Expected changes present:"
            echo -e "$MATCHED" | sort | while read -r f; do [ -n "$f" ] && echo "  $f"; done
        fi
        exit 1
    fi

    echo "PASS: only expected files changed"
    echo ""
    echo "Changed files:"
    echo -e "$MATCHED" | sort | while read -r f; do [ -n "$f" ] && echo "  $f"; done
    exit 0
fi

# ── No expected files provided — any dirt is a fail ────────────────

echo "FAIL: unexpected uncommitted changes (no expected files specified)"
echo ""
echo "$DIRTY"
exit 1
