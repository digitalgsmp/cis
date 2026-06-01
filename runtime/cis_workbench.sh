#!/usr/bin/env bash
# cis_workbench.sh — Fire-and-forget launcher for CIS Workbench
# No terminal popup. Starts Flask if not running, opens browser.

FLASK_PORT=5000
FLASK_APP="/mnt/projects/cis/runtime/app.py"
WORKBENCH_URL="http://127.0.0.1:${FLASK_PORT}/workbench"

# Port pre-check — skip startup if already running
if ! lsof -Pi :${FLASK_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    cd /mnt/projects/cis/runtime
    nohup python3 "${FLASK_APP}" > /dev/null 2>&1 &
    # Give it a moment to start
    sleep 2
fi

# Open the workbench in the default browser
xdg-open "${WORKBENCH_URL}"
