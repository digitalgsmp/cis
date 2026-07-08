#!/bin/bash
# gate_export_agreement.sh — Tier 5.6 deterministic export agreement verification
# Reads EXPORT_MANIFEST.json, verifies all artifacts match on disk.
#
# Usage: gate_export_agreement.sh [--manifest PATH]
#
# Exit 0: PASS — all artifacts match manifest
# Exit 1: FAIL — one or more artifacts mismatched
# Exit 2: ERROR — manifest missing, invalid, or unparseable
#
# Env override: GATE_EXPORT_MANIFEST=PATH

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ── Determine manifest path ────────────────────────────────────────────────

MANIFEST=""

# 1) --manifest flag
while [[ $# -gt 0 ]]; do
    case "$1" in
        --manifest)
            MANIFEST="$2"
            shift 2
            ;;
        *)
            echo "Usage: gate_export_agreement.sh [--manifest PATH]"
            exit 2
            ;;
    esac
done

# 2) env var fallback
if [ -z "$MANIFEST" ] && [ -n "${GATE_EXPORT_MANIFEST:-}" ]; then
    MANIFEST="$GATE_EXPORT_MANIFEST"
fi

# 3) default
if [ -z "$MANIFEST" ]; then
    MANIFEST="$REPO_ROOT/runtime/manifests/EXPORT_MANIFEST.json"
fi

FAILED=0
WARNINGS=0

# ── Python helper for JSON queries ─────────────────────────────────────────

pyval() {
    # Extract a JSON value from the manifest. Usage: pyval <key1> [key2 ...]
    # Prints the value as valid JSON to stdout.
    python3 - "$MANIFEST" "$@" << 'PYEOF'
import json, sys
path = sys.argv[1]
keys = sys.argv[2:]
with open(path) as f:
    data = json.load(f)
try:
    val = data
    for k in keys:
        if isinstance(val, list):
            val = val[int(k)]
        else:
            val = val[k]
    if val is None:
        print("null")
    elif isinstance(val, bool):
        print("true" if val else "false")
    elif isinstance(val, (int, float)):
        print(val)
    elif isinstance(val, str):
        print(val)
    else:
        print(json.dumps(val))
except (KeyError, IndexError, ValueError) as e:
    print("__MISSING__", file=sys.stderr)
    sys.exit(1)
PYEOF
}

# ── Check 1: manifest file exists ──────────────────────────────────────────

if [ ! -f "$MANIFEST" ]; then
    echo "FAIL: export manifest not found"
    echo "  path: $MANIFEST"
    exit 2
fi

# ── Check 2: valid JSON ────────────────────────────────────────────────────

if ! python3 -c "import json; json.load(open('$MANIFEST'))" 2>/dev/null; then
    echo "FAIL: export manifest is not valid JSON"
    echo "  path: $MANIFEST"
    exit 2
fi

# ── Check 3: required top-level fields ─────────────────────────────────────

REQUIRED_FIELDS=(run_id generated_at git_head generator db_path source_configs commands artifacts)
MISSING_FIELDS=""
for field in "${REQUIRED_FIELDS[@]}"; do
    VAL=$(pyval "$field" 2>/dev/null) || true
    if [ "$VAL" = "__MISSING__" ] || [ -z "$VAL" ]; then
        MISSING_FIELDS="${MISSING_FIELDS}${field} "
    fi
done

if [ -n "$MISSING_FIELDS" ]; then
    echo "FAIL: manifest missing required top-level fields: $MISSING_FIELDS"
    exit 2
fi

# ── Check 4: artifact count ────────────────────────────────────────────────

ARTIFACT_COUNT=$(pyval "artifacts" > /tmp/_gate_artifacts.json; python3 -c "
import json
with open('/tmp/_gate_artifacts.json') as f:
    print(len(json.load(f)))
" 2>/dev/null) || ARTIFACT_COUNT=0

if [ "$ARTIFACT_COUNT" -lt 1 ]; then
    echo "FAIL: manifest artifacts array is empty"
    exit 1
fi

EXPECTED_COUNT=12
if [ "$ARTIFACT_COUNT" -ne "$EXPECTED_COUNT" ]; then
    echo "WARN: expected ${EXPECTED_COUNT} artifacts, found ${ARTIFACT_COUNT}"
    WARNINGS=$((WARNINGS + 1))
fi

if [ "$ARTIFACT_COUNT" -eq 0 ]; then
    echo "FAIL: no artifacts to verify"
    exit 1
fi

# ── Extract manifest values ────────────────────────────────────────────────

RUN_ID=$(pyval "run_id")
GIT_HEAD=$(pyval "git_head")

# ── Check 5: Git HEAD ──────────────────────────────────────────────────────

CURRENT_HEAD=$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null) || CURRENT_HEAD="unknown"

if [ "$GIT_HEAD" != "$CURRENT_HEAD" ]; then
    echo "WARN: manifest git_head ($GIT_HEAD) differs from current HEAD ($CURRENT_HEAD)"
    echo "  Expected after committing generated artifacts. Artifact agreement is the pass/fail authority."
    WARNINGS=$((WARNINGS + 1))
fi

# ── Check 5.5: Build state coherence (spine vs static do_not_start) ────────

COHERENCE_GATE="$SCRIPT_DIR/gate_build_state_coherence.py"
if [ -x "$COHERENCE_GATE" ]; then
    echo "Running build state coherence check..."
    if ! python3 "$COHERENCE_GATE"; then
        echo "FAIL: build state coherence gate failed — spine and static config are contradictory"
        echo "  Fix: update config/agents_static.yaml do_not_start to match spine project_state"
        exit 1
    fi
else
    echo "WARN: coherence gate not found or not executable: $COHERENCE_GATE"
    WARNINGS=$((WARNINGS + 1))
fi

# ── Check 6: per-artifact verification ─────────────────────────────────────

echo "Verifying ${ARTIFACT_COUNT} artifacts against manifest..."

for idx in $(seq 0 $((ARTIFACT_COUNT - 1))); do
    ARTIFACT_PATH=$(pyval "artifacts" "$idx" "path")
    ARTIFACT_SHA=$(pyval "artifacts" "$idx" "sha256")
    ARTIFACT_SIZE=$(pyval "artifacts" "$idx" "size_bytes")
    ARTIFACT_CHARS=$(pyval "artifacts" "$idx" "char_count")
    ARTIFACT_LINES=$(pyval "artifacts" "$idx" "line_count")

    FULL_PATH="$REPO_ROOT/$ARTIFACT_PATH"

    if [ ! -f "$FULL_PATH" ]; then
        echo "FAIL: artifact not found: $ARTIFACT_PATH"
        FAILED=$((FAILED + 1))
        continue
    fi

    # SHA256
    DISK_SHA=$(sha256sum "$FULL_PATH" | awk '{print $1}')
    if [ "$DISK_SHA" != "$ARTIFACT_SHA" ]; then
        echo "FAIL: SHA256 mismatch — $ARTIFACT_PATH"
        echo "  manifest: $ARTIFACT_SHA"
        echo "  disk:     $DISK_SHA"
        FAILED=$((FAILED + 1))
    fi

    # size_bytes
    DISK_SIZE=$(stat -c%s "$FULL_PATH" 2>/dev/null) || DISK_SIZE=0
    if [ "$DISK_SIZE" -ne "$ARTIFACT_SIZE" ]; then
        echo "FAIL: size_bytes mismatch — $ARTIFACT_PATH"
        echo "  manifest: $ARTIFACT_SIZE"
        echo "  disk:     $DISK_SIZE"
        FAILED=$((FAILED + 1))
    fi

    # char_count
    DISK_CHARS=$(wc -m < "$FULL_PATH" | tr -d ' ')
    if [ "$DISK_CHARS" -ne "$ARTIFACT_CHARS" ]; then
        echo "FAIL: char_count mismatch — $ARTIFACT_PATH"
        echo "  manifest: $ARTIFACT_CHARS"
        echo "  disk:     $DISK_CHARS"
        FAILED=$((FAILED + 1))
    fi

    # line_count
    DISK_LINES=$(wc -l < "$FULL_PATH" | tr -d ' ')
    if [ "$DISK_LINES" -ne "$ARTIFACT_LINES" ]; then
        echo "FAIL: line_count mismatch — $ARTIFACT_PATH"
        echo "  manifest: $ARTIFACT_LINES"
        echo "  disk:     $DISK_LINES"
        FAILED=$((FAILED + 1))
    fi

    # Run ID in file header (for text files with a Run: line)
    if echo "$ARTIFACT_PATH" | grep -qE '\.md$'; then
        FILE_RUN=$(grep -oP 'Run: \Krun-[a-f0-9]+' "$FULL_PATH" 2>/dev/null | head -1) || true
        if [ -n "$FILE_RUN" ]; then
            if [ "$FILE_RUN" != "$RUN_ID" ]; then
                echo "FAIL: run ID mismatch in file header — $ARTIFACT_PATH"
                echo "  manifest run_id: $RUN_ID"
                echo "  file header:     $FILE_RUN"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
done

# ── Report ─────────────────────────────────────────────────────────────────

if [ "$WARNINGS" -gt 0 ]; then
    echo ""
    echo "${WARNINGS} warning(s) reported (see above)"
fi

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "FAIL: ${FAILED} artifact verification(s) failed"
    exit 1
fi

echo ""
echo "PASS: all ${ARTIFACT_COUNT} artifacts match manifest"
exit 0
