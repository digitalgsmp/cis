#!/bin/bash
# gate_research_artifact_present.sh — Tier 6.4 pipeline-transition gate
# Stage: RESEARCH — validates ## Research Artifact section
#
# Usage: gate_research_artifact_present.sh [--kanban-card-id <id>]
#
# Exit 0: PASS — heading present, content non-empty
# Exit 1: FAIL — heading missing, content empty, or duplicate heading
# Exit 2: ERROR — no card ID, kanban unavailable, JSON parse failure
#
# Marker spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §3.1
# Gate design: CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md §4.1
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/_gate_common.sh"

TARGET_HEADING="## Research Artifact"

# ── Resolve card ID ──────────────────────────────────────────────────
resolve_card_id "$@"
CARD_BODY=$(read_card_body "$CARD_ID")

# ── Validate ─────────────────────────────────────────────────────────
echo "$CARD_BODY" | python3 -c "
import sys

body = sys.stdin.read()
lines = body.split('\n')
target = '$TARGET_HEADING'

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
    print(f'FAIL: Research Artifact section missing')
    sys.exit(1)

# 3. Extract section content
content_lines = []
for j in range(heading_idx + 1, len(lines)):
    stripped = lines[j].strip()
    if stripped.startswith('## '):
        break
    content_lines.append(lines[j])

# 4. Check content is non-empty (at least one non-whitespace line)
has_content = any(l.strip() for l in content_lines)
if not has_content:
    print('FAIL: Research Artifact section empty')
    sys.exit(1)

print('PASS: Research Artifact section present with content')
sys.exit(0)
"
