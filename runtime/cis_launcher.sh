#!/usr/bin/env bash
# cis_launcher.sh — Idempotent CIS Flask startup + browser open
# PD.5 Step 2
# Canonical location: /mnt/projects/cis/runtime/cis_launcher.sh

FLASK_PORT=5000
FLASK_APP="/mnt/projects/cis/runtime/app.py"
DASHBOARD_URL="http://127.0.0.1:${FLASK_PORT}"

# Port pre-check — skip startup if already running
if lsof -Pi :${FLASK_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[CIS] Flask already running on port ${FLASK_PORT} — skipping startup."
else
    echo "[CIS] Starting Flask..."
    python3 "${FLASK_APP}" &
    echo "[CIS] Waiting for Flask to be ready..."
    until curl -s "${DASHBOARD_URL}" >/dev/null 2>&1; do
        sleep 1
    done
    echo "[CIS] Flask is up."
fi

echo "[CIS] Opening dashboard: ${DASHBOARD_URL}"
xdg-open "${DASHBOARD_URL}"
