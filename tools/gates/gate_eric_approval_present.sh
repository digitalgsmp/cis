#!/bin/bash
# gate_eric_approval_present.sh — Tier 6.4 pipeline-transition gate
# Stage: ERIC_GATE — validates ## Eric Gate section with APPROVED marker
#
# Usage: gate_eric_approval_present.sh [--kanban-card-id <id>]
#
# Exit 0: PASS — Eric Gate heading present, APPROVED on standalone line
# Exit 1: FAIL — section missing, APPROVED not found, or duplicate heading
# Exit 2: ERROR — no card ID, kanban unavailable, JSON parse failure
#
# Marker spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §3.5
# Gate design: CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md §4.5
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

body = sys.stdin.read()
lines = body.split('\n')
target = '## Eric Gate'

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
    print('FAIL: Eric Gate section missing')
    sys.exit(1)

# 3. Extract section content and check for APPROVED on standalone line
# APPROVED must be the only non-whitespace content on its line
# Case-sensitive: APPROVED, not approved or Approved
for j in range(heading_idx + 1, len(lines)):
    stripped = lines[j].strip()
    if stripped.startswith('## '):
        break
    if stripped == 'APPROVED':
        print('PASS: Eric Gate section present with APPROVED')
        sys.exit(0)

print('FAIL: APPROVED not found in Eric Gate section')
sys.exit(1)
"
