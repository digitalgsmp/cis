#!/bin/bash
# launch_profiles.sh — Start all 6 Hermes gateway profiles inside container
# Each profile gets its own managed config and port.
# Called by Docker CMD or entrypoint.

set -e

CONFIG_DIR="/etc/hermes/profiles"
LOG_DIR="/workspace/logs"
mkdir -p "$LOG_DIR"

PROFILES=(brain draft review1 review2 menter verify)
PORTS=(8644 8645 8643 8647 8646 8648)

for i in "${!PROFILES[@]}"; do
    profile="${PROFILES[$i]}"
    port="${PORTS[$i]}"
    config="$CONFIG_DIR/${profile}.yaml"
    logfile="$LOG_DIR/${profile}.log"
    pidfile="/tmp/${profile}.pid"

    if [ -f "$pidfile" ] && kill -0 "$(cat $pidfile)" 2>/dev/null; then
        echo "[$profile] already running (pid $(cat $pidfile))"
        continue
    fi

    echo "[$profile] starting on port $port..."
    HERMES_HOME=/home/worker/.hermes-$profile \
    HERMES_MANAGED_DIR=/etc/hermes \
    HERMES_ACCEPT_HOOKS=1 \
    hermes gateway run --port "$port" --config "$config" \
        > "$logfile" 2>&1 &
    echo $! > "$pidfile"
    echo "[$profile] started (pid $!, log: $logfile)"
done

echo ""
echo "All profiles started. Checking health..."
sleep 3

for i in "${!PROFILES[@]}"; do
    profile="${PROFILES[$i]}"
    port="${PORTS[$i]}"
    if curl -s "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
        echo "  [$profile] port $port: UP"
    else
        echo "  [$profile] port $port: STARTING (check logs)"
    fi
done

echo ""
echo "Container ready. PIDs:"
for profile in "${PROFILES[@]}"; do
    echo "  $profile: $(cat /tmp/${profile}.pid 2>/dev/null || 'none')"
done

# Keep container alive
wait
