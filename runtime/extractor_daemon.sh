#!/usr/bin/env bash
# Extractor Daemon — LEGACY. Retired from autostart on 2026-10-12
# (card CIS-OPS-EXTRACTOR-PERMANENT-REMEDIATION).
#
# History: this script ran unattended from 2026-09-13 to 2026-10-12, retrying a
# rejected credential every ~48s. It processed zero files and grew
# logs/extractor_daemon.log to ~401 MB. Its @reboot crontab entry has been removed.
#
# It is now MANUAL-ONLY and BOUNDED:
#   * no credential is embedded here, and none may be added;
#   * it refuses to start unless DEEPSEEK_API_KEY is supplied by the operator;
#   * it runs at most EXTRACTOR_MAX_PASSES passes (default 1), never forever;
#   * it stops on authentication failure, on a pass that makes no progress,
#     and on a missing extractor script.
#
# Intentional manual use:
#   DEEPSEEK_API_KEY=... EXTRACTOR_MAX_PASSES=1 runtime/extractor_daemon.sh

set -uo pipefail

CIS_SCRIPT="/mnt/projects/cis/runtime/extractor.py"
SWA_SCRIPT="/mnt/projects/social_work_ai/extractor.py"
LOG="/mnt/projects/cis/logs/extractor_daemon.log"
MAX_PASSES="${EXTRACTOR_MAX_PASSES:-1}"
SLEEP_SECONDS="${EXTRACTOR_SLEEP_SECONDS:-30}"

# ── Fail closed BEFORE touching the log, the network, or any extractor ──
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    cat >&2 <<'EOF'
extractor_daemon.sh: refusing to run.

  DEEPSEEK_API_KEY is not set in the environment.

  This legacy daemon no longer embeds a credential and is no longer started at
  boot. If you intend to run it, supply a valid key yourself for this invocation:

      DEEPSEEK_API_KEY=... EXTRACTOR_MAX_PASSES=1 runtime/extractor_daemon.sh

  Nothing was executed and no network request was made.
EOF
    exit 78  # EX_CONFIG
fi

case "$MAX_PASSES" in
    ''|*[!0-9]*|0)
        echo "extractor_daemon.sh: EXTRACTOR_MAX_PASSES must be a positive integer." >&2
        exit 78
        ;;
esac

log() { echo "[$(date)] $*" >> "$LOG"; }

if [ ! -f "$CIS_SCRIPT" ]; then
    echo "extractor_daemon.sh: CIS extractor not found at $CIS_SCRIPT — stopping." >&2
    log "ABORT: CIS extractor missing at $CIS_SCRIPT"
    exit 72  # EX_OSFILE
fi

# A missing SWA extractor is a permanent condition, not something to retry.
# It is skipped for the whole run so it can never drive a retry loop.
RUN_SWA=1
if [ ! -f "$SWA_SCRIPT" ]; then
    RUN_SWA=0
    log "NOTICE: SWA extractor not present at $SWA_SCRIPT — skipping it for this run."
fi

log "Daemon started (manual, bounded: max ${MAX_PASSES} pass(es))"

# Counts files still awaiting extraction for one extractor root.
# Echoes nothing if the count cannot be determined.
remaining() {
    local root="$1"
    python3 -c "
import sys
sys.path.insert(0, '$root')
from extractor import find_source_files, already_extracted
print(len([1 for g, p in find_source_files() if not already_extracted(p)]))
" 2>/dev/null
}

# Runs one extractor, appending output to the log. Returns 2 if the API
# rejected the credential, otherwise the extractor's own exit status.
run_one() {
    local name="$1" script="$2" out status
    log "Starting $name"
    out=$(python3 "$script" 2>&1)
    status=$?
    printf '%s\n' "$out" >> "$LOG"
    log "$name exited ($status)"
    if printf '%s' "$out" | grep -qE 'API key rejected \(401\)|\b401\b.*[Uu]nauthoriz'; then
        return 2
    fi
    return $status
}

AUTH_FAILED=0
pass=0

while [ "$pass" -lt "$MAX_PASSES" ]; do
    pass=$((pass + 1))
    log "─── Pass ${pass}/${MAX_PASSES} ───"

    CIS_BEFORE=$(remaining /mnt/projects/cis/runtime)
    SWA_BEFORE=$(remaining /mnt/projects/social_work_ai)

    run_one "CIS-extractor" "$CIS_SCRIPT"
    [ $? -eq 2 ] && AUTH_FAILED=1

    if [ "$RUN_SWA" -eq 1 ]; then
        run_one "SWA-extractor" "$SWA_SCRIPT"
        [ $? -eq 2 ] && AUTH_FAILED=1
    fi

    if [ "$AUTH_FAILED" -eq 1 ]; then
        echo "extractor_daemon.sh: the API rejected the supplied credential (401) — stopping." >&2
        log "ABORT: credential rejected (401). Not retrying. Supply a working key and rerun."
        exit 77  # EX_NOPERM
    fi

    CIS_AFTER=$(remaining /mnt/projects/cis/runtime)
    SWA_AFTER=$(remaining /mnt/projects/social_work_ai)
    log "Remaining after pass ${pass}: CIS=${CIS_AFTER:-unknown}  SWA=${SWA_AFTER:-unknown}"

    # If progress cannot be measured, retrying is unsafe: stop rather than spin.
    if [ -z "$CIS_AFTER" ]; then
        echo "extractor_daemon.sh: could not determine the remaining file count — stopping." >&2
        log "ABORT: remaining-count probe failed after pass ${pass}. Not retrying."
        exit 75  # EX_TEMPFAIL
    fi

    if [ "${CIS_AFTER:-1}" = "0" ] && { [ "$RUN_SWA" -eq 0 ] || [ "${SWA_AFTER:-1}" = "0" ]; }; then
        log "All files extracted. Daemon exiting cleanly."
        exit 0
    fi

    # No forward progress means retrying cannot help. Stop instead of looping.
    if [ -n "$CIS_BEFORE" ] && [ -n "$CIS_AFTER" ] && [ "$CIS_AFTER" -ge "$CIS_BEFORE" ]; then
        echo "extractor_daemon.sh: pass ${pass} made no progress (${CIS_BEFORE} -> ${CIS_AFTER}) — stopping." >&2
        log "ABORT: pass ${pass} made no progress (CIS ${CIS_BEFORE} -> ${CIS_AFTER}). Not retrying."
        exit 75  # EX_TEMPFAIL
    fi

    [ "$pass" -lt "$MAX_PASSES" ] && sleep "$SLEEP_SECONDS"
done

log "Reached the ${MAX_PASSES}-pass limit. Daemon exiting without retrying further."
echo "extractor_daemon.sh: reached the ${MAX_PASSES}-pass limit; exiting." >&2
exit 0
