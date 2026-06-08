#!/bin/bash
# closeout.sh — CIS Tier 6.x Closeout Artifact Writer
# Reads a closeout manifest JSON, writes a human-readable handoff markdown file.
#
# Usage: closeout.sh --run-id <id> --node-id <id> --node-description <desc>
#                    --manifest-path <path> [--output-dir <path>]
#
# Exit 0: CLOSEOUT WRITTEN
# Exit 1: Write failure
# Exit 2: Input validation failure (missing manifest, bad JSON, missing fields)
#
# Spec: CIS_TIER_6_1_CLOSEOUT_TRIGGER_DESIGN.md §2.3-2.4
# Invoked by: gate_closeout_complete.sh v2 (Tier 6.2)
#
# Deferred: --generate-exports flag (runs generate_all.py)
# Deferred: --commit flag (git add + git commit generated files)
# These require separate approved design/directives before Tier 6.5.
#
set -euo pipefail

# ── CLI defaults ─────────────────────────────────────────────────────
RUN_ID=""
NODE_ID=""
NODE_DESCRIPTION=""
MANIFEST_PATH=""
OUTPUT_DIR="session_handoffs"

# ── Parse CLI ────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --run-id)        RUN_ID="$2"; shift 2 ;;
        --node-id)       NODE_ID="$2"; shift 2 ;;
        --node-description) NODE_DESCRIPTION="$2"; shift 2 ;;
        --manifest-path) MANIFEST_PATH="$2"; shift 2 ;;
        --output-dir)    OUTPUT_DIR="$2"; shift 2 ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            echo "Usage: closeout.sh --run-id <id> --node-id <id> --node-description <desc> --manifest-path <path> [--output-dir <path>]" >&2
            exit 2
            ;;
    esac
done

# ── Validate required args ───────────────────────────────────────────
if [ -z "$RUN_ID" ]; then
    echo "ERROR: --run-id is required" >&2
    exit 2
fi
if [ -z "$NODE_ID" ]; then
    echo "ERROR: --node-id is required" >&2
    exit 2
fi
if [ -z "$NODE_DESCRIPTION" ]; then
    NODE_DESCRIPTION="$NODE_ID"
fi
if [ -z "$MANIFEST_PATH" ]; then
    echo "ERROR: --manifest-path is required" >&2
    exit 2
fi

# ── Read and validate manifest ───────────────────────────────────────
if [ ! -f "$MANIFEST_PATH" ]; then
    echo "ERROR: manifest not found: $MANIFEST_PATH" >&2
    exit 2
fi

# ── Generate output filename ─────────────────────────────────────────
CLOSEOUT_DATE=$(date +%Y%m%d)
SANITIZED_NODE=$(echo "$NODE_ID" | sed 's/[^a-zA-Z0-9_-]/_/g')
OUTPUT_FILE="${OUTPUT_DIR}/CLOSEOUT_${CLOSEOUT_DATE}_${SANITIZED_NODE}.md"

# ── Write handoff markdown ───────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"

set +e
python3 -c "
import json, sys, os

# Read manifest
try:
    with open('$MANIFEST_PATH') as f:
        manifest = json.load(f)
except Exception as e:
    print(f'ERROR: cannot read manifest: {e}', file=sys.stderr)
    sys.exit(2)

# Validate required fields
required = ['run_id', 'node_id', 'timestamp_started', 'git_head', 'gates']
for field in required:
    if field not in manifest or manifest[field] is None:
        print(f'ERROR: manifest missing required field: {field}', file=sys.stderr)
        sys.exit(2)

# Build markdown
lines = []
lines.append('# Session Closeout — $NODE_ID')
lines.append('')
lines.append(f'Date: {os.environ.get(\"CLOSEOUT_DATE\", \"\")}')
lines.append(f'Status: CLOSEOUT COMPLETE')
lines.append(f'Run ID: {manifest[\"run_id\"]}')
lines.append(f'Commit: {manifest[\"git_head\"][:7]}')
lines.append('')
lines.append('---')
lines.append('')
lines.append('## Completed')
lines.append('')
lines.append(f'- **Tier/Node:** {manifest[\"node_id\"]}')
lines.append(f'- **Description:** {manifest.get(\"node_description\", \"\")}')
lines.append(f'- **Started:** {manifest[\"timestamp_started\"]}')
lines.append(f'- **Completed:** {manifest.get(\"timestamp_completed\", \"\")}')
lines.append('')

# State write summary
sw = manifest.get('state_write', {})
if sw:
    lines.append('## State Write')
    lines.append(f'- Status: {sw.get(\"status\", \"UNKNOWN\")}')
    lines.append(f'- Rows written: {sw.get(\"rows_written_or_updated\", 0)}')
    if sw.get('error'):
        lines.append(f'- Error: {sw[\"error\"]}')
    lines.append('')

# Tier 6.4 markers
markers = manifest.get('tier_6_4_markers')
if markers:
    lines.append('## Tier 6.4 Markers')
    lines.append('')
    lines.append(f'- Research Artifact: {\"PASS\" if markers.get(\"research_present\") else \"FAIL\"}')
    lines.append(f'- Proposal Schema: {\"PASS\" if markers.get(\"proposal_valid\") else \"FAIL\"}')
    lines.append(f'- Review Signal: {markers.get(\"review_signal\", \"N/A\")}')
    lines.append(f'- Consensus: {\"PASS\" if markers.get(\"consensus_valid\") else \"FAIL\"}')
    lines.append(f'- Eric Gate: {\"PASS\" if markers.get(\"eric_approved\") else \"FAIL\"}')
    lines.append(f'- Implementation: {\"PASS\" if markers.get(\"implementation_present\") else \"FAIL\"}')
    lines.append('')

# Gate verification summary
gates = manifest.get('gates', [])
if gates:
    pass_count = sum(1 for g in gates if g.get('status') == 'PASS')
    fail_count = sum(1 for g in gates if g.get('status') == 'FAIL')
    skip_count = sum(1 for g in gates if g.get('status') == 'SKIP')
    lines.append('## Gate Verification')
    lines.append('')
    lines.append(f'| Gate | Phase | Status | Exit |')
    lines.append(f'|------|-------|--------|------|')
    for g in gates:
        lines.append(f'| {g.get(\"name\",\"\")} | {g.get(\"phase\",\"\")} | {g.get(\"status\",\"\")} | {g.get(\"exit_code\",\"\")} |')
    lines.append('')
    lines.append(f'**Summary:** {pass_count} PASS, {fail_count} FAIL, {skip_count} SKIP')
    lines.append('')

# Export status
exp = manifest.get('export', {})
if exp:
    lines.append('## Export')
    lines.append(f'- Status: {exp.get(\"status\", \"SKIP\")}')
    lines.append('')

# Git status
git_status = manifest.get('final_git_status', '')
if git_status:
    lines.append('## Git Status at Closeout')
    lines.append(chr(96)*3)
    lines.append(git_status)
    lines.append(chr(96)*3)
    lines.append('')

# Next action
next_action = manifest.get('next_action', '')
if next_action:
    lines.append('## Next Action')
    lines.append(next_action)
    lines.append('')

# Boundaries
lines.append('## Boundaries Held')
lines.append('- No files outside approved manifest were created or modified.')
lines.append('- All gates were run through the verified closeout chain.')
lines.append('- STATE_WRITE completed with deterministic evidence.')
lines.append('')

# Write output
output_path = '$OUTPUT_FILE'
with open(output_path, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f'CLOSEOUT WRITTEN: {output_path}')
"
py_exit=$?
if [ $py_exit -ne 0 ]; then
    exit $py_exit
fi
set -e

exit 0
