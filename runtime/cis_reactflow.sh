#!/usr/bin/env bash
# cis_reactflow.sh — Fire-and-forget launcher for CIS React Flow UI
FLASK_PORT=5000
FLASK_APP="/mnt/projects/cis/runtime/app.py"
UI_URL="http://127.0.0.1:${FLASK_PORT}/ui/"

if ! lsof -Pi :${FLASK_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    cd /mnt/projects/cis/runtime
    nohup python3 "${FLASK_APP}" > /dev/null 2>&1 &
    sleep 2
fi

xdg-open "${UI_URL}"
