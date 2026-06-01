#!/bin/bash
# ============================================================
# CIS vLLM Startup Script — Slot 1
# Model:   Qwen3-32B-AWQ
# Runtime: vLLM OpenAI-compatible API
# Host:    127.0.0.1
# Port:    8001
# ADR-042: vLLM runtime for reasoning/verification
# ============================================================
# CRITICAL: Do not activate vllm-env via source/PATH.
#           Always invoke the binary directly.
#           The vllm-env shebang points to the wrong path.
# ============================================================
set -e
PYTHON=/mnt/models/vllm-env/bin/python
MODEL=/mnt/models/huggingface/hub/models--Qwen--Qwen3-32B-AWQ
HOST=127.0.0.1
PORT=8001
LOG=/mnt/projects/cis/logs/vllm_slot1.log

echo "============================================================"
echo " CIS vLLM Slot 1 Startup"
echo " Model:  Qwen3-32B-AWQ"
echo " Host:   $HOST:$PORT"
echo " Log:    $LOG"
echo "============================================================"

# Verify python binary exists
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Python binary not found at $PYTHON"
    exit 1
fi

# Verify model path exists
if [ ! -d "$MODEL" ]; then
    echo "ERROR: Model directory not found at $MODEL"
    exit 1
fi

# Ensure log directory exists
mkdir -p /mnt/projects/cis/logs

# Port pre-check — PD.5 Step 3
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "ERROR: Port ${PORT} is already in use. Is Slot 1 already running?"
    echo "Kill the existing process before starting a new instance."
    exit 1
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting Slot 1..." | tee -a "$LOG"

$PYTHON -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host $HOST \
    --port $PORT \
    --quantization awq_marlin \
    --enforce-eager \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.90 \
    --served-model-name "slot1-qwen3-32b" \
    2>&1 | tee -a "$LOG"
