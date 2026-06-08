#!/bin/bash
# gate_review_round_valid.sh — Tier 6.4 pipeline-transition gate
# Stage: REVIEW — validates ## Review section with exactly one signal
#
# Usage: gate_review_round_valid.sh [--kanban-card-id <id>]
#
# Exit 0: PASS — Review heading, exactly one standalone signal, required sub-fields
# Exit 1: FAIL — section missing, zero/multiple signals, embedded signal, missing sub-fields
# Exit 2: ERROR — no card ID, kanban unavailable, JSON parse failure
#
# Marker spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §3.3
# Gate design: CIS_TIER_6_4_PIPELINE_TRANSITION_GATES_DESIGN.md §4.3
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

VALID_SIGNALS = ['CONSENSUS_REACHED', 'OBJECTIONS', 'ESCALATE']

def find_standalone_signals(section_text):
    \"\"\"Find standalone signal tokens in section text. Returns list of signal names.\"\"\"
    found = []
    for line in section_text.split('\n'):
        stripped = line.strip()
        upper = stripped.upper()
        for signal in VALID_SIGNALS:
            sig_upper = signal.upper()
            # Exact match: line is exactly the signal
            if upper == sig_upper:
                found.append(signal)
                break
            # First-word match: signal at start, followed by non-alphanumeric
            if upper.startswith(sig_upper) and len(stripped) > len(sig_upper):
                next_char = stripped[len(sig_upper)]
                if not next_char.isalnum() and next_char != '_':
                    found.append(signal)
                    break
    return found

def check_remaining_objections(section_text):
    \"\"\"Check for remaining_objections: none (case-insensitive for none value).
    Returns (found: bool, value: str|None). Rejects 0, [], and all other values.\"\"\"
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

def check_bullets(section_text):
    \"\"\"Check for at least one dash-bullet line (- ) in section.\"\"\"
    for line in section_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('- ') and len(stripped) > 2:
            return True
    return False

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
    print('FAIL: Review section missing')
    sys.exit(1)

# 3. Extract section content
section_lines = []
for j in range(heading_idx + 1, len(lines)):
    stripped = lines[j].strip()
    if stripped.startswith('## '):
        break
    section_lines.append(lines[j])

section_text = '\n'.join(section_lines)

# 4. Find standalone signals
signals = find_standalone_signals(section_text)

if len(signals) == 0:
    print('FAIL: no valid signal in Review')
    sys.exit(1)

if len(signals) > 1:
    print('FAIL: multiple signals in Review')
    sys.exit(1)

signal = signals[0]

# 5. Validate signal sub-fields
if signal == 'CONSENSUS_REACHED':
    found, bad_value = check_remaining_objections(section_text)
    if not found:
        if bad_value == 'missing':
            print('FAIL: CONSENSUS missing remaining_objections: none')
        else:
            print(f'FAIL: CONSENSUS rejected remaining_objections value: {bad_value}')
        sys.exit(1)

elif signal == 'OBJECTIONS':
    if not check_bullets(section_text):
        print('FAIL: OBJECTIONS missing bullet list')
        sys.exit(1)

# ESCALATE: signal present is sufficient

print(f'PASS: Review section valid — signal {signal} with required sub-fields')
sys.exit(0)
"
