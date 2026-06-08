#!/bin/bash
# gate_proposal_schema_valid.sh — Tier 6.4 pipeline-transition gate
# Stage: DRAFT — validates ## Proposal section schema
#
# Usage: gate_proposal_schema_valid.sh [--kanban-card-id <id>]
#
# Exit 0: PASS — Proposal heading, ### Summary, ### Recommendation all present with content
# Exit 1: FAIL — section missing, sub-heading missing/empty, or duplicate heading
# Exit 2: ERROR — no card ID, kanban unavailable, JSON parse failure
#
# Marker spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §3.2
# Gate design: CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md §4.2
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

# ── Resolve card ID ──────────────────────────────────────────────────
resolve_card_id "$@"
CARD_BODY=$(read_card_body "$CARD_ID")

# ── Validate ─────────────────────────────────────────────────────────
echo "$CARD_BODY" | python3 -c "
import sys

def extract_sub_content(section_lines, sub_heading):
    found = False
    content_lines = []
    for line in section_lines:
        stripped = line.strip()
        if stripped == sub_heading:
            found = True
            continue
        if found:
            if stripped.startswith('### ') or stripped.startswith('## '):
                break
            content_lines.append(line)
    if not found:
        return None
    return '\n'.join(content_lines)

body = sys.stdin.read()
lines = body.split('\n')
target = '## Proposal'

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
    print('FAIL: Proposal section missing')
    sys.exit(1)

# 3. Extract section content
section_lines = []
for j in range(heading_idx + 1, len(lines)):
    stripped = lines[j].strip()
    if stripped.startswith('## '):
        break
    section_lines.append(lines[j])

# 4. Check ### Summary sub-heading
summary_content = extract_sub_content(section_lines, '### Summary')
if summary_content is None:
    print('FAIL: Proposal missing ### Summary')
    sys.exit(1)
if not summary_content.strip():
    print('FAIL: Proposal ### Summary empty')
    sys.exit(1)

# 5. Check ### Recommendation sub-heading
rec_content = extract_sub_content(section_lines, '### Recommendation')
if rec_content is None:
    print('FAIL: Proposal missing ### Recommendation')
    sys.exit(1)
if not rec_content.strip():
    print('FAIL: Proposal ### Recommendation empty')
    sys.exit(1)

print('PASS: Proposal section valid — Summary and Recommendation present with content')
sys.exit(0)
"
