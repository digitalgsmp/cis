#!/bin/bash
# gate_implementation_artifact_present.sh — Tier 6.4 pipeline-transition gate
# Stage: IMPLEMENT — validates ## Implementation section with commit hash or file evidence
#
# Usage: gate_implementation_artifact_present.sh [--kanban-card-id <id>]
#
# Exit 0: PASS — Implementation heading, commit hash or file change evidence under /mnt/projects/cis/
# Exit 1: FAIL — section missing, no evidence, path outside /mnt/projects/cis/, or duplicate heading
# Exit 2: ERROR — no card ID, kanban unavailable, JSON parse failure
#
# Marker spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §3.6
# Gate design: CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md §4.6
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

# ── Resolve card ID ──────────────────────────────────────────────────
resolve_card_id "$@"
CARD_BODY=$(read_card_body "$CARD_ID")

# ── Validate ─────────────────────────────────────────────────────────
echo "$CARD_BODY" | python3 -c "
import sys, re

body = sys.stdin.read()
lines = body.split('\n')
target = '## Implementation'

# 1. Check for duplicate headings
count = sum(1 for l in lines if l.strip() == target)
if count > 1:
    print(f'FAIL: duplicate {target} heading in card body')
    sys.exit(1)

# 2. Find heading
heading_idx = None
for i, line in enumerate(lines):
    if line.strip() == target:
        heading_idx = i
        break

if heading_idx is None:
    print('FAIL: Implementation section missing')
    sys.exit(1)

# 3. Extract section content
section_lines = []
for j in range(heading_idx + 1, len(lines)):
    stripped = lines[j].strip()
    if stripped.startswith('## '):
        break
    section_lines.append(lines[j])

section_text = '\n'.join(section_lines)

# 4. Check for evidence
has_commit = False
has_file_evidence = False

# Commit hash: 7-40 lowercase hex chars, word boundary
commit_pattern = re.compile(r'\b[0-9a-f]{7,40}\b')

for line in section_lines:
    # Check for commit hash
    if commit_pattern.search(line):
        has_commit = True
        break

if not has_commit:
    # Check for file change evidence: Created: or Modified: followed by /mnt/projects/cis/ path
    file_pattern = re.compile(r'(Created|Modified):\s*/mnt/projects/cis/')
    for line in section_lines:
        if file_pattern.search(line):
            has_file_evidence = True
            break

if has_commit:
    print('PASS: Implementation section present with artifact evidence')
    sys.exit(0)

if has_file_evidence:
    print('PASS: Implementation section present with artifact evidence')
    sys.exit(0)

print('FAIL: no artifact evidence in Implementation section')
sys.exit(1)
"
