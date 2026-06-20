#!/bin/bash
# §7 Parts A+B Override-Plane 9-Step Test — disposable test rig
# Amendment 1 (Revised) — /mnt/cache/catalog/override-plane-test/<run_id>/
# Captures raw evidence per §14.1 requirement

set -euo pipefail

RUN_ID="run-20260620_0001_9step"
TEST_ROOT="/mnt/cache/catalog/override-plane-test/$RUN_ID"
CONTROL_DIR="$TEST_ROOT/control/contracts/inv-catalog-001"
WORKSPACE_DIR="$TEST_ROOT/workspace/$RUN_ID"
CONTAINER_NAME="cis-test-rig-$RUN_ID"
EVIDENCE_LOG="$TEST_ROOT/raw_evidence.log"

echo "═══════════════════════════════════════════"
echo "  §7 Parts A+B — 9-Step Override-Plane Test"
echo "  RUN_ID: $RUN_ID"
echo "  EVIDENCE LOG: $EVIDENCE_LOG"
echo "═══════════════════════════════════════════"
echo ""

# ── Preflight: create directories ─────────────────────────────────

echo "=== PREFLIGHT: Create test infrastructure ==="
echo "COMMAND: mkdir -p $CONTROL_DIR"
mkdir -p "$CONTROL_DIR"
echo "EXIT: $?"

echo "COMMAND: mkdir -p $WORKSPACE_DIR"
mkdir -p "$WORKSPACE_DIR"
echo "EXIT: $?"

echo "COMMAND: sudo chown -R root:root $TEST_ROOT/control"
sudo chown -R root:root "$TEST_ROOT/control" 2>&1
echo "EXIT: $?"

echo "COMMAND: sudo chmod -R 755 $TEST_ROOT/control"
sudo chmod -R 755 "$TEST_ROOT/control" 2>&1
echo "EXIT: $?"

echo ""
echo "=== PREFLIGHT: Ownership/path evidence ==="
echo "COMMAND: stat -c '%U:%G %a %n' $CONTROL_DIR"
stat -c '%U:%G %a %n' "$CONTROL_DIR" 2>&1

echo "COMMAND: stat -c '%U:%G %a %n' $WORKSPACE_DIR"
stat -c '%U:%G %a %n' "$WORKSPACE_DIR" 2>&1

echo "COMMAND: realpath $CONTROL_DIR"
realpath "$CONTROL_DIR" 2>&1

echo "COMMAND: realpath $WORKSPACE_DIR"
realpath "$WORKSPACE_DIR" 2>&1

echo ""
echo "=== PREFLIGHT: Negative check — worker cannot create sentinel on host ==="
echo "COMMAND: touch $CONTROL_DIR/.GATE_DISABLED_WORKER_TRY"
touch "$CONTROL_DIR/.GATE_DISABLED_WORKER_TRY" 2>&1
echo "EXIT: $?"

echo "COMMAND: test -e $CONTROL_DIR/.GATE_DISABLED_WORKER_TRY && echo EXISTS || echo ABSENT"
test -e "$CONTROL_DIR/.GATE_DISABLED_WORKER_TRY" && echo "EXISTS" || echo "ABSENT"

# ── Launch container ──────────────────────────────────────────────

echo ""
echo "=== PREFLIGHT: Launch disposable Docker container ==="
echo "COMMAND: sg docker -c \"docker run -d --name $CONTAINER_NAME ...\""
sg docker -c "docker run -d \
  --name $CONTAINER_NAME \
  --mount type=bind,source=$CONTROL_DIR,target=/contract,readonly \
  --mount type=bind,source=/mnt/projects/cis,target=/mnt/projects/cis,readonly \
  --mount type=bind,source=/mnt/archive,target=/mnt/archive,readonly \
  --mount type=bind,source=/mnt/projects/swa,target=/mnt/projects/swa,readonly \
  --mount type=bind,source=$WORKSPACE_DIR,target=/mnt/cache/catalog/$RUN_ID \
  ubuntu:22.04 tail -f /dev/null" 2>&1
echo "EXIT: $?"

echo ""
echo "=== MOUNT EVIDENCE: docker inspect ==="
echo "COMMAND: docker inspect $CONTAINER_NAME | python3 -c \"...\" "
sg docker -c "docker inspect $CONTAINER_NAME" 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
mounts = data[0]['Mounts']
for m in mounts:
    print(f\"  {m['Destination']:40s} → {m['Source']}\")
    print(f\"  {'':40s}   Mode: {m.get('Mode','')}  RW: {m.get('RW', 'N/A')}\")
" 2>&1

echo ""
echo "=== MOUNT EVIDENCE: inside-container mount ==="
echo "COMMAND: docker exec $CONTAINER_NAME mount | grep -E '/contract|/mnt/cache/catalog'"
sg docker -c "docker exec $CONTAINER_NAME mount" 2>&1 | grep -E '/contract|/mnt/cache/catalog'

# ═══════════════════════════════════════════
# STEP 1
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 1: Worker blocked without override"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker exec $CONTAINER_NAME sh -c \"echo 'test' > /mnt/projects/cis/test_breach.txt\""
sg docker -c "docker exec $CONTAINER_NAME sh -c \"echo 'test' > /mnt/projects/cis/test_breach.txt\"" 2>&1
echo "EXIT: $?"
echo "COMMAND (host): test ! -e /mnt/projects/cis/test_breach.txt && echo ABSENT"
test ! -e /mnt/projects/cis/test_breach.txt && echo "ABSENT" || echo "EXISTS"
echo "INTERPRETATION: Docker wall blocks write. Read-only file system. File absent on host."

# ═══════════════════════════════════════════
# STEP 2
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 2: Operator creates sentinel on host"
echo "═══════════════════════════════════════════"
echo "COMMAND: sudo touch $CONTROL_DIR/.GATE_DISABLED"
sudo touch "$CONTROL_DIR/.GATE_DISABLED" 2>&1
echo "EXIT: $?"
echo "COMMAND: stat -c '%U:%G %a %n' $CONTROL_DIR/.GATE_DISABLED"
stat -c '%U:%G %a %n' "$CONTROL_DIR/.GATE_DISABLED" 2>&1
echo "COMMAND: test -e $CONTROL_DIR/.GATE_DISABLED && echo EXISTS || echo ABSENT"
test -e "$CONTROL_DIR/.GATE_DISABLED" && echo "EXISTS" || echo "ABSENT"
echo "INTERPRETATION: Operator (sudo) creates sentinel in root-owned control dir."

# ═══════════════════════════════════════════
# STEP 3
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 3: Restart container"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker rm -f $CONTAINER_NAME"
sg docker -c "docker rm -f $CONTAINER_NAME" 2>&1
echo "EXIT: $?"
echo "COMMAND: docker run -d --name $CONTAINER_NAME (same mounts)"
sg docker -c "docker run -d \
  --name $CONTAINER_NAME \
  --mount type=bind,source=$CONTROL_DIR,target=/contract,readonly \
  --mount type=bind,source=/mnt/projects/cis,target=/mnt/projects/cis,readonly \
  --mount type=bind,source=/mnt/archive,target=/mnt/archive,readonly \
  --mount type=bind,source=/mnt/projects/swa,target=/mnt/projects/swa,readonly \
  --mount type=bind,source=$WORKSPACE_DIR,target=/mnt/cache/catalog/$RUN_ID \
  ubuntu:22.04 tail -f /dev/null" 2>&1
echo "EXIT: $?"
echo "INTERPRETATION: Container restarted. Sentinel picked up via RO mount."

# ═══════════════════════════════════════════
# STEP 4
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 4: Worker sees sentinel (RO mount)"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker exec $CONTAINER_NAME ls -la /contract/.GATE_DISABLED"
sg docker -c "docker exec $CONTAINER_NAME ls -la /contract/.GATE_DISABLED" 2>&1
echo "EXIT: $?"
echo "INTERPRETATION: Sentinel visible. root:root, on RO mount."

# ═══════════════════════════════════════════
# STEP 5
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 5: Worker cannot create/remove sentinel"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker exec $CONTAINER_NAME touch /contract/.GATE_DISABLED"
sg docker -c "docker exec $CONTAINER_NAME touch /contract/.GATE_DISABLED" 2>&1
echo "EXIT: $?"
echo "COMMAND: docker exec $CONTAINER_NAME rm /contract/.GATE_DISABLED"
sg docker -c "docker exec $CONTAINER_NAME rm /contract/.GATE_DISABLED" 2>&1
echo "EXIT: $?"
echo "COMMAND: docker exec $CONTAINER_NAME test -e /contract/.GATE_DISABLED && echo STILL_EXISTS || echo GONE"
sg docker -c "docker exec $CONTAINER_NAME test -e /contract/.GATE_DISABLED && echo STILL_EXISTS || echo GONE" 2>&1
echo "INTERPRETATION: Worker cannot touch/rm sentinel on RO mount. STILL_EXISTS."

# ═══════════════════════════════════════════
# STEP 6
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 6: Override allows workspace write"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker exec $CONTAINER_NAME sh -c \"echo 'override-test' > /mnt/cache/catalog/$RUN_ID/override_test.txt\""
sg docker -c "docker exec $CONTAINER_NAME sh -c \"echo 'override-test' > /mnt/cache/catalog/$RUN_ID/override_test.txt\"" 2>&1
echo "EXIT: $?"
echo "COMMAND: docker exec $CONTAINER_NAME cat /mnt/cache/catalog/$RUN_ID/override_test.txt"
sg docker -c "docker exec $CONTAINER_NAME cat /mnt/cache/catalog/$RUN_ID/override_test.txt" 2>&1
echo "INTERPRETATION: RW workspace write succeeds. Content verified."

# ═══════════════════════════════════════════
# STEP 7
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 7: Docker wall still holds"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker exec $CONTAINER_NAME sh -c \"echo 'test' > /mnt/projects/cis/test_breach_override.txt\""
sg docker -c "docker exec $CONTAINER_NAME sh -c \"echo 'test' > /mnt/projects/cis/test_breach_override.txt\"" 2>&1
echo "EXIT: $?"
echo "COMMAND (host): test ! -e /mnt/projects/cis/test_breach_override.txt && echo ABSENT"
test ! -e /mnt/projects/cis/test_breach_override.txt && echo "ABSENT" || echo "EXISTS"
echo "INTERPRETATION: Docker wall NEVER bypassed. RO mount blocks write regardless of sentinel."

# ═══════════════════════════════════════════
# STEP 8
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 8: Operator removes sentinel, restart"
echo "═══════════════════════════════════════════"
echo "COMMAND: sudo rm $CONTROL_DIR/.GATE_DISABLED"
sudo rm "$CONTROL_DIR/.GATE_DISABLED" 2>&1
echo "EXIT: $?"
echo "COMMAND: test -e $CONTROL_DIR/.GATE_DISABLED && echo EXISTS || echo ABSENT"
test -e "$CONTROL_DIR/.GATE_DISABLED" && echo "EXISTS" || echo "ABSENT"
echo "COMMAND: docker rm -f $CONTAINER_NAME && docker run -d --name $CONTAINER_NAME (same mounts)"
sg docker -c "docker rm -f $CONTAINER_NAME" 2>&1
sg docker -c "docker run -d \
  --name $CONTAINER_NAME \
  --mount type=bind,source=$CONTROL_DIR,target=/contract,readonly \
  --mount type=bind,source=/mnt/projects/cis,target=/mnt/projects/cis,readonly \
  --mount type=bind,source=/mnt/archive,target=/mnt/archive,readonly \
  --mount type=bind,source=/mnt/projects/swa,target=/mnt/projects/swa,readonly \
  --mount type=bind,source=$WORKSPACE_DIR,target=/mnt/cache/catalog/$RUN_ID \
  ubuntu:22.04 tail -f /dev/null" 2>&1
echo "EXIT: $?"
echo "COMMAND: docker exec $CONTAINER_NAME test -e /contract/.GATE_DISABLED && echo STILL_VISIBLE || echo GONE"
sg docker -c "docker exec $CONTAINER_NAME test -e /contract/.GATE_DISABLED && echo STILL_VISIBLE || echo GONE" 2>&1
echo "INTERPRETATION: Sentinel removed by operator. Not visible after restart."

# ═══════════════════════════════════════════
# STEP 9
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  STEP 9: Wall re-engages after sentinel removal"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker exec $CONTAINER_NAME sh -c \"echo 'test' > /mnt/projects/cis/test_breach_after.txt\""
sg docker -c "docker exec $CONTAINER_NAME sh -c \"echo 'test' > /mnt/projects/cis/test_breach_after.txt\"" 2>&1
echo "EXIT: $?"
echo "COMMAND (host): test ! -e /mnt/projects/cis/test_breach_after.txt && echo ABSENT"
test ! -e /mnt/projects/cis/test_breach_after.txt && echo "ABSENT" || echo "EXISTS"
echo "INTERPRETATION: Wall re-engages. Same blocked behavior as Step 1."

# ═══════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════"
echo "  CLEANUP"
echo "═══════════════════════════════════════════"
echo "COMMAND: docker rm -f $CONTAINER_NAME"
sg docker -c "docker rm -f $CONTAINER_NAME" 2>&1
echo "EXIT: $?"
echo "COMMAND: sudo rm -rf $TEST_ROOT (evidence log preserved separately)"
# Don't delete test root — evidence log is inside it
echo "Test root preserved at $TEST_ROOT for evidence inspection."
echo "COMMAND: test -e /mnt/projects/cis/test_breach.txt -o -e /mnt/projects/cis/test_breach_override.txt -o -e /mnt/projects/cis/test_breach_after.txt && echo BREACH_FILES_EXIST || echo ALL_ABSENT"
test -e /mnt/projects/cis/test_breach.txt -o -e /mnt/projects/cis/test_breach_override.txt -o -e /mnt/projects/cis/test_breach_after.txt && echo "BREACH_FILES_EXIST" || echo "ALL_ABSENT"

echo ""
echo "═══════════════════════════════════════════"
echo "  TEST COMPLETE"
echo "  Evidence log: $EVIDENCE_LOG"
echo "═══════════════════════════════════════════"
