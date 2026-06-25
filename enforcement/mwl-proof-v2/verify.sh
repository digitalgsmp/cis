#!/usr/bin/env bash
# verify.sh — prove enforcement walls hold in the standing cis-hermes container.
#
# Run by Eric on the HOST (not inside the container):
#   sudo docker exec cis-hermes bash /verify.sh
#
# Or if copied into the image at build time (at /opt/cis-hooks/verify.sh):
#   sudo docker exec cis-hermes bash /opt/cis-hooks/verify.sh
#
# Tests every enforcement wall from inside the container as the worker user.
# All config is baked at build time — this script only proves the walls hold.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

pass() { echo -e "  ${GREEN}PASS${NC}: $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}FAIL${NC}: $1"; FAIL=$((FAIL + 1)); }

echo "=== VERIFY: CIS Hermes Enforcement Walls ==="
echo "Identity: $(whoami)"
echo "UID:     $(id -u)"
echo "Home:    ${HOME}"
echo ""

# =========================================================================
# WALL 1: Read-only mounts hold (direct shell, no hermes needed)
# =========================================================================
echo "--- Wall 1: RO mounts hold ---"
echo forbidden > /cis-control/_verify_ro.txt 2>/dev/null \
    && fail "/cis-control RO mount (write succeeded — wall breached)" \
    || pass "/cis-control RO mount"
echo forbidden > /source/cis/_verify_ro.txt 2>/dev/null \
    && fail "/source/cis RO mount (write succeeded — wall breached)" \
    || pass "/source/cis RO mount"

# =========================================================================
# WALL 2: Workspace is writable (only permitted write target)
# =========================================================================
echo "--- Wall 2: Workspace writable ---"
echo "ok" > /workspace/_verify_rw.txt 2>/dev/null \
    && pass "/workspace writable" \
    || fail "/workspace writable"
# Clean up
rm -f /workspace/_verify_rw.txt

# =========================================================================
# WALL 3: config.yaml is sealed (worker cannot modify, append, delete, rename)
# =========================================================================
echo "--- Wall 3: config.yaml sealed ---"
CFG="/home/worker/.hermes/config.yaml"

# 3a. Append blocked
echo "# test" >> "$CFG" 2>/dev/null \
    && fail "config.yaml append (should be blocked)" \
    || pass "config.yaml append blocked"

# 3b. Deletion blocked
rm "$CFG" 2>/dev/null \
    && fail "config.yaml deletion (should be blocked)" \
    || pass "config.yaml deletion blocked"

# 3c. Rename blocked
mv "$CFG" "${CFG}.bak" 2>/dev/null \
    && fail "config.yaml rename (should be blocked)" \
    || pass "config.yaml rename blocked"

# =========================================================================
# WALL 4: Plugin directory sealed (worker cannot delete or rename)
# =========================================================================
echo "--- Wall 4: Plugin sealed ---"
PLUGIN="/home/worker/.hermes/plugins/mwl-proof"

# 4a. Plugin dir deletion blocked
rm -rf "$PLUGIN" 2>/dev/null \
    && fail "plugin deletion (should be blocked)" \
    || pass "plugin deletion blocked"

# 4b. Plugin dir rename blocked
mv "$PLUGIN" "${PLUGIN}.disabled" 2>/dev/null \
    && fail "plugin rename (should be blocked)" \
    || pass "plugin rename blocked"

# 4c. Plugin file modification blocked
echo "# test" >> "${PLUGIN}/__init__.py" 2>/dev/null \
    && fail "plugin file append (should be blocked)" \
    || pass "plugin file append blocked"

# =========================================================================
# WALL 5: Hook script sealed (worker cannot modify, delete)
# =========================================================================
echo "--- Wall 5: Hook script sealed ---"
HOOK="/opt/cis-hooks/cis_shell_hook.sh"

# 5a. Hook append blocked
echo "# test" >> "$HOOK" 2>/dev/null \
    && fail "hook script append (should be blocked)" \
    || pass "hook script append blocked"

# 5b. Hook deletion blocked
rm "$HOOK" 2>/dev/null \
    && fail "hook script deletion (should be blocked)" \
    || pass "hook script deletion blocked"

# =========================================================================
# WALL 6: No root escalation vectors
# =========================================================================
echo "--- Wall 6: No root escalation ---"

# 6a. sudo
sudo -n whoami 2>/dev/null \
    && fail "sudo available" \
    || pass "sudo unavailable"

# 6b. su
echo "" | su - root -c 'whoami' 2>/dev/null \
    && fail "su to root possible" \
    || pass "su to root blocked"

# 6c. docker socket (if mounted)
docker ps 2>/dev/null \
    && fail "docker socket accessible" \
    || pass "docker socket inaccessible"

# =========================================================================
# WALL 7: Runtime subdirs still writable (hermes can persist sessions)
# =========================================================================
echo "--- Wall 7: Runtime subdirs writable ---"
echo "ok" > /home/worker/.hermes/sessions/_verify.txt 2>/dev/null \
    && pass "sessions/ writable" \
    || fail "sessions/ writable"
rm -f /home/worker/.hermes/sessions/_verify.txt

echo "ok" > /home/worker/.hermes/logs/_verify.txt 2>/dev/null \
    && pass "logs/ writable" \
    || fail "logs/ writable"
rm -f /home/worker/.hermes/logs/_verify.txt

# =========================================================================
# WALL 8: Hook config present in sealed config.yaml
# =========================================================================
echo "--- Wall 8: Hook config present ---"
grep -q "cis_shell_hook.sh" "$CFG" 2>/dev/null \
    && pass "hook reference in config.yaml" \
    || fail "hook reference in config.yaml"

grep -q "/opt/cis-hooks" "$CFG" 2>/dev/null \
    && pass "hook path is /opt/cis-hooks/ (not /tmp)" \
    || fail "hook path is /opt/cis-hooks/ (not /tmp)"

# =========================================================================
# SUMMARY
# =========================================================================
echo ""
echo "=============================================="
echo -e "RESULTS: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed${NC}"
echo "=============================================="
if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}ALL WALLS HOLD — enforcement intact${NC}"
    exit 0
else
    echo -e "${RED}SOME WALLS BREACHED — enforcement compromised${NC}"
    exit 1
fi
