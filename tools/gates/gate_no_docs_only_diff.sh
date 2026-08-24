#!/bin/bash
# gate_no_docs_only_diff.sh — FAIL any build run whose output is only documents.
#
# Usage: gate_no_docs_only_diff.sh <build_dir>
#
# Git repo: changed+untracked files must include at least one non-.md file.
# Not a git repo (fresh app dir): the tree must contain at least one non-.md file.
set -u
DIR="${1:?usage: gate_no_docs_only_diff.sh <build_dir>}"
[ -d "$DIR" ] || { echo "FAIL: build dir not found: $DIR"; exit 1; }

if git -C "$DIR" rev-parse --git-dir >/dev/null 2>&1; then
    files=$(git -C "$DIR" status --porcelain | awk '{print $NF}')
    if [ -z "$files" ]; then
        echo "FAIL: no changed files — nothing was built"
        exit 1
    fi
else
    files=$(find "$DIR" -type f -not -path '*/.*' | sed "s|^$DIR/||")
    if [ -z "$files" ]; then
        echo "FAIL: build dir is empty — nothing was built"
        exit 1
    fi
fi

nonmd=$(echo "$files" | grep -vE '\.md$' || true)
if [ -z "$nonmd" ]; then
    echo "FAIL: output contains only .md files — documents are not deliverables"
    exit 1
fi
echo "PASS: non-document output present:"
echo "$nonmd" | head -10
exit 0
