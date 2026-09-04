#!/usr/bin/env bash
# test_override_plane.sh — deterministic acceptance test for the override plane.
#
# The record requires this to pass BEFORE the wall is ever trusted to block:
#   "The override plane must be verified by a deterministic acceptance test
#    BEFORE the hook is enabled in enforcement mode."
#
# Runs from a bare shell. No Hermes, no gateway, no pipeline run — it calls the
# plugin's pre_tool_call hook directly, which is the same function Hermes calls.
#
# Usage:  bash tools/test_override_plane.sh
# Exit:   0 = all assertions passed
#         1 = an assertion FAILED — do not trust the wall
#         2 = could not test (container down, mount absent, override already set)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CIS_CONTAINER:-cis-pipeline}"
HOST_FLAG="$REPO_ROOT/.gate-control/DISABLED"
CTR_FLAG="/opt/cis-control/gate/DISABLED"
PLUGIN="/home/worker/.hermes-review2/plugins/mwl-proof/__init__.py"
OVERRIDE_LOG="$REPO_ROOT/gate_override.log"

PASS=0
FAIL=0

say()  { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); printf '  PASS  %s\n' "$*"; }
bad()  { FAIL=$((FAIL+1)); printf '  FAIL  %s\n' "$*"; }
die()  { printf 'CANNOT TEST: %s\n' "$*" >&2; exit 2; }

# ── Preconditions ─────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || die "docker not on PATH"
docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$CONTAINER" \
    || die "container '$CONTAINER' is not running"

docker exec "$CONTAINER" test -d /opt/cis-control/gate 2>/dev/null \
    || die "/opt/cis-control/gate is not mounted in the container.
             The mount is added in run_container.sh but only takes effect on a
             container restart. Restart, then re-run this test."

docker exec "$CONTAINER" test -f "$PLUGIN" 2>/dev/null \
    || die "plugin not found at $PLUGIN inside the container"

# Refuse to run if the wall is already disabled — the test would remove the
# operator's own override on the way out and silently re-arm enforcement.
if [ -e "$HOST_FLAG" ]; then
    die "the override is already active ($HOST_FLAG exists).
             Enforcement is currently OFF. Remove the file yourself if that is
             stale, then re-run. This test will not delete it for you."
fi

# Any exit path removes a flag this test created. Never touches one it did not.
cleanup() { rm -f "$HOST_FLAG"; }
trap cleanup EXIT

# ── The call under test ───────────────────────────────────────────────────
# MWL_PROOF_BLOCK_ME is the gate runner's built-in proof marker
# (container_gate_runner.py:133) — a command that exists to be blocked.
probe() {
    docker exec -i "$CONTAINER" python3 - <<'PY' 2>/dev/null
import importlib.util, json
spec = importlib.util.spec_from_file_location(
    "mwl", "/home/worker/.hermes-review2/plugins/mwl-proof/__init__.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
r = mod._pre_tool_call(tool_name="terminal",
                       args={"command": "echo MWL_PROOF_BLOCK_ME"},
                       task_id="override-plane-test")
print("ALLOW" if r is None else "BLOCK")
PY
}

say "Override plane acceptance test"
say "  container: $CONTAINER"
say "  host flag: $HOST_FLAG"
say "  seen by container as: $CTR_FLAG"
say ""

# ── 1. Armed: a blocked call is blocked ───────────────────────────────────
say "1. No override file — the wall should BLOCK"
R1="$(probe)"
[ "$R1" = "BLOCK" ] && ok "blocked as expected" \
                    || bad "expected BLOCK, got '${R1:-<no output>}'"

# ── 2. Override present: the same call passes ─────────────────────────────
say "2. Override file present — the same call should be ALLOWED"
touch "$HOST_FLAG"
docker exec "$CONTAINER" test -f "$CTR_FLAG" 2>/dev/null \
    && ok "container sees the file through the read-only mount" \
    || bad "container cannot see $CTR_FLAG — the mount is not working"

LOG_BEFORE=0
[ -f "$OVERRIDE_LOG" ] && LOG_BEFORE=$(wc -l < "$OVERRIDE_LOG")

R2="$(probe)"
[ "$R2" = "ALLOW" ] && ok "allowed as expected" \
                    || bad "expected ALLOW, got '${R2:-<no output>}'"

LOG_AFTER=0
[ -f "$OVERRIDE_LOG" ] && LOG_AFTER=$(wc -l < "$OVERRIDE_LOG")
[ "$LOG_AFTER" -gt "$LOG_BEFORE" ] \
    && ok "override recorded in gate_override.log" \
    || bad "nothing written to gate_override.log — an override that leaves no trace"

# ── 3. The agent cannot set its own override ──────────────────────────────
# This is the security property the read-only mount exists for. An override the
# constrained agent can create is a self-disable, not an override.
say "3. The container must NOT be able to create the override itself"
if docker exec "$CONTAINER" touch /opt/cis-control/gate/AGENT_TRY 2>/dev/null; then
    bad "container CREATED a file in the override directory — mount is not read-only"
    docker exec "$CONTAINER" rm -f /opt/cis-control/gate/AGENT_TRY 2>/dev/null
else
    ok "container refused write to the override directory"
fi

# ── 4. Re-arm: removing the file restores the block ───────────────────────
say "4. Override removed — the wall should BLOCK again"
rm -f "$HOST_FLAG"
R4="$(probe)"
[ "$R4" = "BLOCK" ] && ok "block restored" \
                    || bad "expected BLOCK, got '${R4:-<no output>}' — the wall did not re-arm"

# ── Verdict ───────────────────────────────────────────────────────────────
say ""
say "passed: $PASS   failed: $FAIL"
if [ "$FAIL" -eq 0 ]; then
    say "OVERRIDE PLANE VERIFIED — the wall can be turned off and back on from a bare shell."
    exit 0
fi
say "OVERRIDE PLANE NOT VERIFIED — do not trust the wall to block."
exit 1
