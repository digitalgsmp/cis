#!/bin/bash
# gate_consensus_signal_valid.sh — Tier 6.4 pipeline-transition gate
# Stage: CONSENSUS — validates all three consensus markers in ## Review
#
# Usage: gate_consensus_signal_valid.sh [--kanban-card-id <id>]
#
# Exit 0: PASS — all three markers present (CONSENSUS_REACHED, remaining_objections: none, requires_eric_review: true)
# Exit 1: FAIL — any marker missing, requires_eric_review is false, or duplicate heading
# Exit 2: ERROR — no card ID, kanban unavailable, JSON parse failure
#
# Marker spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §3.4
# Gate design: CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md §4.4
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

def find_standalone_signal(section_text, signal_name):
    \"\"\"Check if signal appears as standalone token. Same logic as gate_review_round_valid.sh.\"\"\"
    for line in section_text.split('\n'):
        stripped = line.strip()
        upper = stripped.upper()
        sig_upper = signal_name.upper()
        if upper == sig_upper:
            return True
        if upper.startswith(sig_upper) and len(stripped) > len(sig_upper):
            next_char = stripped[len(sig_upper)]
            if not next_char.isalnum() and next_char != '_':
                return True
    return False

def check_remaining_objections(section_text):
    \"\"\"Same logic as gate_review_round_valid.sh — accepts only none (case-insensitive).\"\"\"
    for line in section_text.split('\n'):
        stripped = line.strip().lower()
        if stripped.startswith('remaining_objections'):
            if ':' in stripped:
                value = stripped.split(':', 1)[1].strip()
                if value == 'none':
                    return True, None
                else:
                    return False, value
    return False, 'missing'

def check_requires_eric_review(section_text):
    \"\"\"Check for requires_eric_review: true (case-insensitive for true value).
    Fails if false or missing.\"\"\"
    for line in section_text.split('\n'):
        stripped = line.strip().lower()
        if stripped.startswith('requires_eric_review'):
            if ':' in stripped:
                value = stripped.split(':', 1)[1].strip()
                if value == 'true':
                    return True
                else:
                    return False  # explicit false or other value
    return False  # missing

body = sys.stdin.read()
lines = body.split('\n')
target = '## Review'

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
    print('FAIL: Consensus signal invalid — missing Review section')
    sys.exit(1)

# 3. Extract section content
section_lines = []
for j in range(heading_idx + 1, len(lines)):
    stripped = lines[j].strip()
    if stripped.startswith('## '):
        break
    section_lines.append(lines[j])

section_text = '\n'.join(section_lines)

# 4. Check CONSENSUS_REACHED
if not find_standalone_signal(section_text, 'CONSENSUS_REACHED'):
    print('FAIL: Consensus signal invalid — missing CONSENSUS_REACHED')
    sys.exit(1)

# 5. Check remaining_objections: none
ro_found, ro_bad = check_remaining_objections(section_text)
if not ro_found:
    if ro_bad == 'missing':
        print('FAIL: Consensus signal invalid — missing remaining_objections: none')
    else:
        print(f'FAIL: Consensus signal invalid — rejected remaining_objections: {ro_bad}')
    sys.exit(1)

# 6. Check requires_eric_review
rer = check_requires_eric_review(section_text)
if rer is False:
    # Check if it's explicitly false or missing
    has_field = any('requires_eric_review' in line.strip().lower() for line in section_text.split('\n'))
    if has_field:
        print('FAIL: requires_eric_review is false')
    else:
        print('FAIL: Consensus signal invalid — missing requires_eric_review: true')
    sys.exit(1)

print('PASS: Consensus signal valid — all three markers present')
sys.exit(0)
"
