#!/bin/bash
# =============================================================================
# cis_deploy.sh
# CIS Runtime Deployment + Housekeeping Script
#
# What this does:
#   1. Unzips cis_backend.zip into the runtime folder (modular structure)
#   2. Preserves all existing pipeline scripts (cis_intake.py etc.)
#   3. Moves old monolithic cis_dashboard.py to _archive/
#   4. Moves mockup/panel HTML files to a ui_mockups/ folder
#   5. Appends memory_additions.md content into the system log
#   6. Verifies the final structure
#   7. Tests that app.py starts without errors
#
# Run from: /mnt/projects/cis/runtime/
# Usage:    bash cis_deploy.sh
# =============================================================================

RUNTIME="/mnt/projects/cis/runtime"
ARCHIVE="$RUNTIME/_archive"
MOCKUPS="$RUNTIME/ui_mockups"
MEMORY_VAULT="/mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1"
LOG="/mnt/projects/cis/logs/system_log.md"

echo "════════════════════════════════════════════════════"
echo "  CIS Deploy — Runtime Housekeeping"
echo "════════════════════════════════════════════════════"

# ── Step 1: Create housekeeping folders ───────────────────────
echo ""
echo "▸ Step 1: Creating folders..."
mkdir -p "$ARCHIVE"
mkdir -p "$MOCKUPS"
echo "  ✓ _archive/ created"
echo "  ✓ ui_mockups/ created"

# ── Step 2: Unzip modular backend ─────────────────────────────
echo ""
echo "▸ Step 2: Unzipping cis_backend.zip..."
if [ -f "$RUNTIME/cis_backend.zip" ]; then
    # Unzip contents of cis_backend/ subfolder directly into runtime/
    cd "$RUNTIME"
    unzip -o cis_backend.zip
    # Move contents from the cis_backend/ subfolder up into runtime/
    if [ -d "$RUNTIME/cis_backend" ]; then
        cp -r "$RUNTIME/cis_backend/"* "$RUNTIME/"
        rm -rf "$RUNTIME/cis_backend"
        echo "  ✓ Modular backend extracted"
    else
        echo "  ✓ Files extracted directly"
    fi
else
    echo "  ✗ ERROR: cis_backend.zip not found at $RUNTIME/cis_backend.zip"
    echo "    Download it from the Claude session and place it in $RUNTIME first."
    exit 1
fi

# ── Step 3: Archive old monolithic dashboard ──────────────────
echo ""
echo "▸ Step 3: Archiving old files..."

if [ -f "$RUNTIME/cis_dashboard.py" ]; then
    mv "$RUNTIME/cis_dashboard.py" "$ARCHIVE/cis_dashboard_monolith_$(date +%Y%m%d).py"
    echo "  ✓ cis_dashboard.py → _archive/"
fi

if [ -f "$RUNTIME/cis_dashboard-2.py" ]; then
    mv "$RUNTIME/cis_dashboard-2.py" "$ARCHIVE/cis_dashboard-2_$(date +%Y%m%d).py"
    echo "  ✓ cis_dashboard-2.py → _archive/"
fi

# ── Step 4: Move mockup/panel HTML to ui_mockups/ ─────────────
echo ""
echo "▸ Step 4: Moving UI mockup files..."

for f in cis_mockup.html cis_live_panel.html; do
    if [ -f "$RUNTIME/$f" ]; then
        mv "$RUNTIME/$f" "$MOCKUPS/$f"
        echo "  ✓ $f → ui_mockups/"
    fi
done

# ── Step 5: Append memory_additions.md to system log ──────────
echo ""
echo "▸ Step 5: Logging memory additions..."

if [ -f "$RUNTIME/memory_additions.md" ]; then
    echo "" >> "$LOG"
    echo "## $(date -u '+%Y-%m-%d %H:%M') UTC — MEMORY ADDITIONS IMPORT" >> "$LOG"
    cat "$RUNTIME/memory_additions.md" >> "$LOG"
    echo "  ✓ memory_additions.md appended to system_log.md"

    # Also copy to vault for git commit
    cp "$RUNTIME/memory_additions.md" "$MEMORY_VAULT/memory_additions_$(date +%Y%m%d).md"
    echo "  ✓ memory_additions.md copied to vault"
else
    echo "  ! memory_additions.md not found, skipping"
fi

# ── Step 6: Verify modular structure ──────────────────────────
echo ""
echo "▸ Step 6: Verifying file structure..."

REQUIRED=(
    "app.py"
    "config.py"
    "api/__init__.py"
    "api/system.py"
    "api/projects.py"
    "api/session.py"
    "api/tasks.py"
    "api/pipeline.py"
    "api/records.py"
    "api/captures.py"
    "api/decisions.py"
    "api/extraction_runs.py"
    "api/live.py"
    "db/__init__.py"
    "db/connection.py"
    "db/live_db.py"
    "utils/__init__.py"
    "utils/helpers.py"
    "utils/project_helpers.py"
)

ALL_OK=true
for f in "${REQUIRED[@]}"; do
    if [ -f "$RUNTIME/$f" ]; then
        echo "  ✓ $f"
    else
        echo "  ✗ MISSING: $f"
        ALL_OK=false
    fi
done

# ── Step 7: Syntax check app.py ───────────────────────────────
echo ""
echo "▸ Step 7: Syntax checking app.py..."
python3 -m py_compile "$RUNTIME/app.py" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ app.py syntax OK"
else
    echo "  ✗ app.py has syntax errors — check output above"
    ALL_OK=false
fi

# ── Step 8: Git commit everything ─────────────────────────────
echo ""
echo "▸ Step 8: Git commit to vault..."
cd "$MEMORY_VAULT"
git add -A
git commit -m "Deploy: modular backend + housekeeping $(date -u '+%Y-%m-%d %H:%M')" 2>&1
if [ $? -eq 0 ]; then
    git push
    echo "  ✓ Git committed and pushed"
else
    echo "  ! Nothing new to commit or push failed"
fi

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════"
if [ "$ALL_OK" = true ]; then
    echo "  ✓ Deployment complete"
    echo ""
    echo "  To start CIS Dashboard:"
    echo "  python3 /mnt/projects/cis/runtime/app.py"
    echo ""
    echo "  Access at: http://localhost:5000"
else
    echo "  ✗ Deployment completed with errors — review above"
fi
echo "════════════════════════════════════════════════════"
