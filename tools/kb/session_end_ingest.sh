#!/usr/bin/env bash
# session_end_ingest.sh — request the sanctioned session ingester when a Claude
# Code session ends, without making Claude wait for embedding to finish.
#
# Registered as a Claude Code SessionEnd hook. Claude Code passes the event as
# JSON on stdin (session_id, transcript_path, cwd, hook_event_name, reason). The
# hook records a durable pending marker and starts a detached worker; the hook
# itself returns immediately. The worker re-runs the whole family. That is the smaller
# mechanism: tools/ingest_claude_code_sessions.py already discovers every
# transcript from the policy's declared root and is idempotent by source_key, so
# passing one path would mean teaching a second place what the KB source policy
# already declares — and would silently miss any session whose own hook failed.
#
# What this does NOT do, on purpose:
#   - no model runs and nothing is summarised: the ingester copies verbatim text
#   - no transcript is written to, moved or truncated — read-only on ~/.claude
#   - nothing is promoted to authority: the rows land in knowledge_messages under
#     source 'claude_code', which config/kb_source_policy.yaml classifies
#     authority_class: evidence
#   - no secret handling is changed: filter_for_index() still drops secrets at
#     Chroma index time and redact_secrets() still masks on read
#
# Failure is visible in two places, by design:
#   1. this log, with an explicit "FAIL" line and the ingester's exit code
#   2. the coverage gate — config/kb_source_policy.yaml declares
#      claude_code_sessions with max_age_days: 2, so a hook that silently stops
#      working turns that family red within two days. The gate is the detector;
#      this log is the diagnostic.
#
# Exits 0 unconditionally. A session that is already ending has nothing useful to
# do with a non-zero status, and a KB hook must never be able to interfere with
# the harness shutting down. The pending marker is removed only after a successful
# ingest, so a failed or interrupted worker is retried by the next session end.

set -uo pipefail

REPO=/mnt/projects/cis
LOG="$REPO/logs/kb_session_end_ingest.log"
LOCK="$REPO/tmp/kb_session_end_ingest.lock"
PENDING_DIR="$REPO/tmp/kb_session_end_ingest.pending.d"
PY=python3.12
# Hard ceiling, kept BELOW the hook's own timeout (300s in settings.json) so the
# script always gets to write its own FAIL line rather than being killed silently.
# A steady-state run is ~0s; the first catch-up run after a gap was 48s.
BUDGET=240

[ -d "$REPO" ] || exit 0

mkdir -p "$(dirname "$LOG")" "$(dirname "$LOCK")" "$PENDING_DIR" 2>/dev/null || exit 0

stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }

if [ "${1:-}" != "--worker" ]; then
    # Consume the hook payload before detaching. The family-wide incremental
    # ingester remains the sole source-discovery authority.
    cat >/dev/null 2>&1 || true
    request=$(mktemp "$PENDING_DIR/request.XXXXXX") || exit 0
    printf '%s\n' "$(stamp)" >"$request" 2>/dev/null || exit 0

    # New session/process group plus closed standard streams is essential:
    # merely appending '&' leaves Claude waiting for inherited hook pipes.
    if command -v setsid >/dev/null 2>&1; then
        setsid -f "$0" --worker </dev/null >/dev/null 2>&1 || true
    else
        nohup "$0" --worker </dev/null >/dev/null 2>&1 &
    fi
    exit 0
fi

# flock, not a PID file: two sessions ending within the same second would
# otherwise both embed, and concurrent writers to the same Chroma collection is
# the one thing chroma_write() exists to prevent. Detached workers may wait here;
# Claude has already returned. Waiting rather than skipping guarantees that a
# request arriving at the end of another ingestion is not stranded.
exec 9>"$LOCK" 2>/dev/null || exit 0
flock 9 || exit 0

# Snapshot only the requests this scan will satisfy. A request created while the
# scan is running remains for its own waiting worker, preventing a lost wakeup.
set -- "$PENDING_DIR"/request.*
[ -e "$1" ] || exit 0

start=$(date +%s)
out=$(cd "$REPO" && timeout "$BUDGET" "$PY" tools/ingest_claude_code_sessions.py 2>&1)
rc=$?
elapsed=$(( $(date +%s) - start ))

# One line per run, plus the ingester's own counts. Keep it greppable.
chunks=$(printf '%s\n' "$out" | grep -oE 'knowledge_messages: \+[0-9]+' | tail -1)
if [ "$rc" -eq 0 ]; then
    echo "$(stamp) OK ${elapsed}s ${chunks:-no new chunks}" >>"$LOG"
    rm -f -- "$@"
else
    echo "$(stamp) FAIL rc=$rc ${elapsed}s — coverage gate will show" \
         "claude_code_sessions stale within max_age_days" >>"$LOG"
    printf '%s\n' "$out" | tail -20 | sed 's/^/    /' >>"$LOG"
fi

exit 0
