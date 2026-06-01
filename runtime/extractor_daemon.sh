#!/usr/bin/env bash
# Extractor Daemon — runs both extractors in parallel, auto-restarts on interrupt
# Stops when all files are processed.

DEEPSEEK_API_KEY="sk-ba0b06b597c54bb9be63846d66b4f37d"
CIS_SCRIPT="/mnt/projects/cis/runtime/extractor.py"
SWA_SCRIPT="/mnt/projects/social_work_ai/extractor.py"
LOG="/mnt/projects/cis/logs/extractor_daemon.log"

export DEEPSEEK_API_KEY

log() { echo "[$(date)] $@" >> "$LOG"; }

log "Daemon started"

run_one() {
    local name="$1" script="$2"
    log "Starting $name"
    python3 "$script" >> "$LOG" 2>&1
    local exit=$?
    log "$name exited ($exit)"
    return $exit
}

while true; do
    # Run both in parallel
    run_one "CIS-extractor" "$CIS_SCRIPT" &
    PID_CIS=$!
    run_one "SWA-extractor" "$SWA_SCRIPT" &
    PID_SWA=$!

    wait $PID_CIS $PID_SWA
    log "Both extractors finished a pass"

    # Quick check remaining count
    CIS_REST=$(python3 -c "
import sys
sys.path.insert(0, '/mnt/projects/cis/runtime')
from extractor import find_source_files, already_extracted
print(len([1 for g,p in find_source_files() if not already_extracted(p)]))
" 2>/dev/null)

    SWA_REST=$(python3 -c "
import sys
sys.path.insert(0, '/mnt/projects/social_work_ai')
from extractor import find_source_files, already_extracted
print(len([1 for g,p in find_source_files() if not already_extracted(p)]))
" 2>/dev/null)

    log "Remaining: CIS=$CIS_REST  SWA=$SWA_REST"

    if [ "$CIS_REST" = "0" ] && [ "$SWA_REST" = "0" ]; then
        log "All done. Daemon exiting."
        break
    fi

    # Wait before retry (rate limit cooldown, or system came back up)
    sleep 30
done
