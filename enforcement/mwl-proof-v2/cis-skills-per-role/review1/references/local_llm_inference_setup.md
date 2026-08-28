# Local LLM Inference Setup (2026-07-11)

## Available Hardware
- GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)
- Driver: 580.159.03, CUDA 13.0
- Host: creative-vm (192.168.1.15), Ubuntu 24.04

## Available Models

| Model | Path | Size | Quant | Active Params |
|-------|------|------|-------|---------------|
| Qwen3-VL-30B-A3B | `/home/eric/models/Qwen3-VL-GGUF/qwen3-vl-30b-a3b-instruct-q4_k_m.gguf` | 18.5GB | Q4_K_M | 3B (MoE) |
| GLM-4.7-Flash | `/home/eric/models/GLM-4.7-Flash-Q4_K_M.gguf` | ~18GB | Q4_K_M | — |
| llama3:8B | Ollama | 4.7GB | Q4_0 | 8B |
| llava:7B | Ollama | 4.7GB | Q4_0 | 7B |

## Qwen3-VL-30B Server (Primary for Semantic Tasks)

### Systemd Service
`~/.config/systemd/user/llama-server-qwen.service`

```ini
[Service]
Type=simple
ExecStart=/mnt/models/llama.cpp/build/bin/llama-server \
  --model /home/eric/models/Qwen3-VL-GGUF/qwen3-vl-30b-a3b-instruct-q4_k_m.gguf \
  --mmproj /home/eric/models/Qwen3-VL-GGUF/mmproj-qwen3-vl-30b-a3b-instruct.gguf \
  --port 8002 --host 127.0.0.1 \
  --n-gpu-layers -1 --cpu-moe --no-mmap \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --flash-attn on \
  --ctx-size 32768
Restart=on-failure
RestartSec=10
```

### Commands
```bash
# Start
systemctl --user start llama-server-qwen.service

# Status
systemctl --user status llama-server-qwen.service

# Stop
systemctl --user stop llama-server-qwen.service

# Logs
tail -f ~/.hermes-qwen/logs/llama-server.log
```

### Performance
- Load time: 2-3 minutes (MoE layers load to CPU memory first)
- First inference: ~60-70 seconds (warmup)
- Steady state: ~23 tokens/sec
- VRAM usage: ~2GB (small — MoE keeps most experts on CPU)
- CPU memory: ~16.7GB
- API: OpenAI-compatible at `http://127.0.0.1:8002/v1/chat/completions`

### Common Issue: Port Already in Use
If the service fails to start with "couldn't bind HTTP server socket",
check for stale processes on port 8002:
```bash
ss -tlnp | grep 8002
# Kill anything there, then start
```

## Usage in CIS Pipeline

The Qwen model is used for **semantic drift detection** — comparing
phase outputs against the locked intent to detect meaning drift that
word-overlap heuristics miss. See [Intent Provenance & Drift Detection](intent_provenance_drift.md).

Call pattern (from pipeline_relay.py):
```python
# Quick single-turn query
payload = json.dumps({
    "model": "qwen3-vl-30b-a3b-instruct-q4_k_m.gguf",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 200,
    "temperature": 0.1,
})
resp = urllib.request.urlopen(
    urllib.request.Request(
        "http://127.0.0.1:8002/v1/chat/completions",
        data=payload.encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    ),
    timeout=60,
)
```

## GLM-4.7-Flash Server (Alternative — Faster for Simple Tasks)

### Systemd Service
`~/.config/systemd/user/llama-server-glm.service`

```ini
[Service]
Type=simple
ExecStart=/mnt/models/llama.cpp/build/bin/llama-server \
  --model /home/eric/models/GLM-4.7-Flash-Q4_K_M.gguf \
  --port 8003 --host 127.0.0.1 \
  --n-gpu-layers -1 \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --flash-attn on \
  --ctx-size 8192
Restart=on-failure
RestartSec=10
```

### Commands
```bash
systemctl --user start llama-server-glm.service
systemctl --user status llama-server-glm.service
systemctl --user stop llama-server-glm.service
tail -f ~/.hermes-glm-verifier/logs/llama-server-glm.log
```

### ⚠️ Pitfall: Do NOT Run Both 18GB Models Simultaneously

Both Qwen (8002) and GLM (8003) are ~18GB GGUF files. Loading both at
the same time causes **severe system memory pressure** — the machine
becomes unresponsive, `systemctl` commands hang, and `nvidia-smi`
times out. The 4090 has 24GB VRAM but the models also need ~16GB system
RAM each.

**Rule**: Stop one before starting the other.
```bash
systemctl --user stop llama-server-qwen.service
# Wait for it to release memory, THEN:
systemctl --user start llama-server-glm.service
```

**If the system hangs during dual load**: Eric needs to kill one from a
terminal manually — the agent cannot do it because `systemctl` itself
hangs under memory pressure.

## Important: DeepSeek API Budget Constraint
Eric stated (2026-07-11): "there is only 2 dollars left on the deepseek
account so dont call any deepseek apis unless I have to in order to build."

Use local LLMs for any semantic analysis needed during builds. Only call
DeepSeek APIs (ports 8644-8646) when the pipeline itself runs — those
calls are the pipeline executing, not build-time analysis.
