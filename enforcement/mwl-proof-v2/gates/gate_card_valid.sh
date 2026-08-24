#!/bin/bash
# gate_card_valid.sh — deterministic BUILD CARD validation via tools/card_gate.py
#
# Usage: gate_card_valid.sh <card_file> [docs_dir]
#
# Exit 0: card passes card_gate.py (verbatim quotes, no banned vocab,
#         runnable evidence, sections present)
# Exit 1: card fails (reasons printed by card_gate.py)
set -u
CARD="${1:?usage: gate_card_valid.sh <card_file> [docs_dir]}"
DOCS="${2:-}"

# Search order: baked sealed copy first, then volume mounts for development
if [ -f /opt/cis-tools/card_gate.py ]; then
    CARD_GATE=/opt/cis-tools/card_gate.py
elif [ -f "${CIS_ROOT:-}/tools/card_gate.py" ]; then
    CARD_GATE="$CIS_ROOT/tools/card_gate.py"
else
    echo "FAIL: card_gate.py not found (checked /opt/cis-tools and ${CIS_ROOT:-}/tools/)" >&2
    exit 1
fi
DB="${CIS_SPINE_PATH:-$CIS_ROOT/data/cis_memory.db}"

if [ -n "$DOCS" ]; then
    python3 "$CARD_GATE" --db "$DB" --docs "$DOCS" "$CARD"
else
    python3 "$CARD_GATE" --db "$DB" "$CARD"
fi
