#!/bin/bash
# entrypoint.sh — Start all 6 Hermes gateways, then the pipeline Flask API.
# Called by Docker CMD.
#
# Expected volume mounts:
#   /workspace/cis          — the CIS repo (code + SQLite spine)
#   /workspace/secrets.env  — API keys (DEEPSEEK_API_KEY, OPENROUTER_API_KEY, etc.)
#
# Pipeline API is on port 5000. Gateway ports: 8644-8648 (internal only).

set -e

LOG_DIR="/tmp/cis-logs"
mkdir -p "$LOG_DIR"

# ── Clean stale pidfiles from previous container run ───────────────────
# docker restart preserves /tmp, so old pidfiles cause false "already running"
rm -f /tmp/brain.pid /tmp/draft.pid /tmp/review1.pid /tmp/review2.pid /tmp/menter.pid /tmp/verify.pid /tmp/advisor.pid /tmp/evaluator.pid /tmp/pipeline_api.pid

# ── Load API keys from secrets file ────────────────────────────────────
if [ -f /workspace/secrets.env ]; then
    set -a
    source /workspace/secrets.env
    set +a
    echo "[entrypoint] Loaded API keys from /workspace/secrets.env"
else
    echo "[entrypoint] WARNING: /workspace/secrets.env not found — gateways will lack model API keys"
fi

# ── Gateway API keys (for pipeline relay → gateway auth) ───────────────
# These are the api_server.api_key values from the profile configs.
# The pipeline relay reads them via CIS_{ROLE}_API_KEY env vars.
export CIS_BRAIN_API_KEY="cis-brainstorm-gateway-key-2026"
export CIS_DRAFT_API_KEY="cis-drafter-gateway-key-2026"
export CIS_REVIEW1_API_KEY="cis-qwen-reviewer-gateway-key-2026"
export CIS_REVIEW2_API_KEY="cis-glm-reviewer-gateway-key-2026"
export CIS_MENTER_API_KEY="cis-implementer-gateway-key-2026"
export CIS_VERIFY_API_KEY="cis-verifier-gateway-key-2026"
export CIS_ADVISOR_API_KEY="cis-advisor-gateway-key-2026"
export CIS_EVALUATOR_API_KEY="cis-evaluator-gateway-key-2026"

# ── Create HERMES_HOME directories for each profile ────────────────────
# Each profile needs its own ~/.hermes-<name> with a config.yaml that sets
# the port, model, and personality. The managed config at /etc/hermes
# provides the enforcement keys (plugins, guardrails) that override
# whatever the worker's config says — so the worker can't disable enforcement.
# advisor (8649) and evaluator (8650) added 2026-09-03 — the review loop's two
# reviewers (queue items 1.18 and 1.20). Both are permanently stripped to zero
# tools in their profile configs; that is the role, not dev mode.
# This list is hardcoded and so is the one in Dockerfile:153. Profile nine means
# editing both.
PROFILES=(brain draft review1 review2 menter verify advisor evaluator)
PORTS=(8644 8645 8643 8647 8646 8648 8649 8650)

for i in "${!PROFILES[@]}"; do
    profile="${PROFILES[$i]}"
    port="${PORTS[$i]}"
    home_dir="/home/worker/.hermes-$profile"
    profile_config="/etc/hermes/profiles/${profile}.yaml"

    # Create profile directory (Dockerfile may not pre-create per-profile dirs)
    mkdir -p "$home_dir"
    cp "$profile_config" "$home_dir/config.yaml"
    chown worker:worker "$home_dir/config.yaml"
done

# ── Create .env files with API_SERVER_KEY for each profile ────────────
# Hermes reads API_SERVER_KEY from ~/.hermes-<profile>/.env, not from
# config.yaml's api_key field. Each profile needs its own .env.
#
# Telegram tokens are PER-PROFILE — each bot has its own token.
# They're passed via env vars from run_container.sh (not in secrets.env
# because that's shared and we need one token per profile).
GATEWAY_KEYS=(
    "cis-brainstorm-gateway-key-2026"
    "cis-drafter-gateway-key-2026"
    "cis-qwen-reviewer-gateway-key-2026"
    "cis-glm-reviewer-gateway-key-2026"
    "cis-implementer-gateway-key-2026"
    "cis-verifier-gateway-key-2026"
    "cis-advisor-gateway-key-2026"
    "cis-evaluator-gateway-key-2026"
)

# Per-profile Telegram tokens (env vars from run_container.sh)
# Empty = no Telegram for that profile (API-server-only)
TG_TOKENS=(
    "${CIS_TG_BRAIN_TOKEN:-}"
    "${CIS_TG_DRAFT_TOKEN:-}"
    "${CIS_TG_REVIEW1_TOKEN:-}"
    "${CIS_TG_REVIEW2_TOKEN:-}"
    "${CIS_TG_MENTER_TOKEN:-}"
    "${CIS_TG_VERIFY_TOKEN:-}"
    ""
    ""
)

for i in "${!PROFILES[@]}"; do
    profile="${PROFILES[$i]}"
    home_dir="/home/worker/.hermes-$profile"
    key="${GATEWAY_KEYS[$i]}"
    tg_token="${TG_TOKENS[$i]}"

    # Build .env with gateway API key + model provider keys
    {
        echo "API_SERVER_KEY=${key}"
        # Model provider keys (inherited from secrets.env, but also in .env for Hermes)
        [ -n "$DEEPSEEK_API_KEY" ] && echo "DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY"
        [ -n "$OPENROUTER_API_KEY" ] && echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY"

        # Telegram config (only for profiles with a bot token)
        if [ -n "$tg_token" ]; then
            echo "TELEGRAM_BOT_TOKEN=${tg_token}"
            echo "TELEGRAM_HOME_CHANNEL=${CIS_TG_HOME_CHANNEL:--5563618057}"
            echo "TELEGRAM_ALLOWED_USERS=6511416750"
            echo "GATEWAY_ALLOW_ALL_USERS=true"
        fi
    } > "$home_dir/.env"

    # Log Telegram config (outside .env redirect!)
    [ -n "$tg_token" ] && echo "[entrypoint]   + Telegram config for $profile"
    chown worker:worker "$home_dir/.env"
    chmod 600 "$home_dir/.env"
done

# ── Start 6 gateway profiles ──────────────────────────────────────────
for i in "${!PROFILES[@]}"; do
    profile="${PROFILES[$i]}"
    port="${PORTS[$i]}"
    home_dir="/home/worker/.hermes-$profile"
    logfile="$LOG_DIR/${profile}.log"
    pidfile="/tmp/${profile}.pid"

    if [ -f "$pidfile" ] && kill -0 "$(cat $pidfile)" 2>/dev/null; then
        echo "[$profile] already running (pid $(cat $pidfile))"
        continue
    fi

    echo "[$profile] starting on port $port..."
    cd /workspace/cis
    HERMES_HOME="$home_dir" \
    HERMES_MANAGED_DIR=/etc/hermes \
    HERMES_ACCEPT_HOOKS=1 \
    hermes gateway run --no-supervise --force --accept-hooks \
        > "$logfile" 2>&1 &
    cd /home/worker
    echo $! > "$pidfile"
    echo "[$profile] started (pid $!, log: $logfile)"
done

echo ""
echo "All profiles started. Waiting for gateways to be ready..."
sleep 10

# ── Health check ──────────────────────────────────────────────────────
HEALTHY=0
for i in "${!PROFILES[@]}"; do
    profile="${PROFILES[$i]}"
    port="${PORTS[$i]}"
    if curl -s "http://127.0.0.1:${port}/v1/models" >/dev/null 2>&1; then
        echo "  [$profile] port $port: UP"
        HEALTHY=$((HEALTHY + 1))
    else
        echo "  [$profile] port $port: NOT READY (check $LOG_DIR/${profile}.log)"
    fi
done

echo ""
echo "Gateways healthy: $HEALTHY/${#PROFILES[@]}"

if [ "$HEALTHY" -lt "${#PROFILES[@]}" ]; then
    echo "[entrypoint] WARNING: not all gateways are up — pipeline may fail"
fi

# ── Install Flask if missing (container image may not include it) ──────
/usr/local/lib/hermes-agent/venv/bin/pip install flask -q 2>/dev/null || true

# ── Start the Flask pipeline API ──────────────────────────────────────
echo ""
echo "[entrypoint] Starting pipeline API on port 5000..."
cd /workspace/cis
/usr/local/lib/hermes-agent/venv/bin/python -c "
from runtime.container_app import app
app.run(host='0.0.0.0', port=5000, debug=False)
" > "$LOG_DIR/pipeline_api.log" 2>&1 &
PIPELINE_PID=$!
echo $PIPELINE_PID > /tmp/pipeline_api.pid
echo "[entrypoint] Pipeline API started (pid $PIPELINE_PID)"

# Wait for API to be ready
sleep 3
if curl -s "http://127.0.0.1:5000/api/relay/health" >/dev/null 2>&1; then
    echo "[entrypoint] Pipeline API: UP on port 5000"
else
    echo "[entrypoint] Pipeline API: NOT READY (check $LOG_DIR/pipeline_api.log)"
    cat "$LOG_DIR/pipeline_api.log" 2>/dev/null | tail -10
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  CIS Pipeline Container Ready"
echo "  Gateways: 8644-8648 (internal)"
echo "  Pipeline API: http://localhost:5000"
echo "  Logs: $LOG_DIR/"
echo "═══════════════════════════════════════════════════════════════"

# Keep container alive — wait on the pipeline API process
wait $PIPELINE_PID
