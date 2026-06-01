# Active Architecture — Hermes Harness
Last updated: 2026-05-19

## Phase Complete
Harness infrastructure is phase-complete. Full lifecycle: capture → exchange → directive → handoff.
Multi-Hermes live agent backend operational: Prime + R1 + Qwen.

## Stack
- React + Vite frontend at /mnt/projects/cis/runtime/ui/
- Flask backend at /mnt/projects/cis/runtime/app.py (port 5000)
- Flask runs as user systemd service: cis-flask.service
- SQLite database: /mnt/projects/cis/runtime/db/cis_memory.db
- Hermes Agent CLI at ~/.hermes/hermes-agent/

## Multi-Hermes Gateway Architecture
| Agent        | Role           | Gateway Port | Model              | Profile Dir         |
|-------------|----------------|-------------|--------------------|--------------------|
| hermes-prime | coordinator    | 8642        | deepseek-v4-pro    | ~/.hermes/          |
| hermes-r1   | senior-advisor  | 8643        | deepseek-reasoner  | ~/.hermes-r1/       |
| hermes-qwen | worker/reviewer | 8644        | qwen3-vl-30b (Q4)  | ~/.hermes-qwen/     |

Each profile has independent config.yaml, .env (with unique API_SERVER_KEY), sessions/, and logs/.

## Qwen Local Server
- llama.cpp server on 127.0.0.1:8002
- Model: qwen3-vl-30b-a3b-instruct-q4_k_m.gguf (18GB)
- ctx-size: 32768 (upgraded from 8192 per HHR-017C-QWEN-CONTEXT-AUDIT)
- Flags: --n-gpu-layers -1, --cpu-moe, --flash-attn on, --cache-type-k q8_0, --cache-type-v q8_0

## Active API endpoints

### Collab Tracker (api/collab_rounds.py)
- GET/POST /api/collab/agents, /status, /activity
- GET/POST/PATCH /api/collab/rounds
- POST /api/collab/rounds/<id>/capture-exchange
- POST /api/collab/rounds/<id>/send-to-hermes
- POST /api/collab/rounds/<id>/send-to-reviewer (Qwen on 8002)
- POST /api/collab/rounds/<id>/send-to-r1 (deepseek-reasoner API)
- POST /api/collab/rounds/<id>/followup-prompt
- GET /api/collab/rounds/<id>/exchanges
- POST/GET /api/collab/rounds/<id>/final-directive
- PATCH /api/collab/directives/<id>
- GET /api/collab/handoff

### Advisor Agent Routing (api/advisor.py) — NEW HHR-017D
- GET /api/advisor/agents — list registered agent instances
- GET/POST /api/advisor/threads — create/list advisor threads
- GET /api/advisor/threads/<id>/messages — thread message history
- POST /api/advisor/chat — route message to named agent gateway

## Database tables
- collab_agents, collab_status, collab_activity
- collab_rounds, collab_exchanges, collab_final_directives
- collab_session_imports, collab_session_messages
- agent_instances — NEW (HHR-017D): name, role, gateway_url, model, config_path, session_dir, env_path, write_permissions, active
- advisor_threads — NEW (HHR-017D): round_id, title, context_summary
- advisor_messages — NEW (HHR-017D): thread_id, agent_name, role, model, content, source_session_file, message_index

## Key files
- /mnt/projects/cis/runtime/api/collab.py
- /mnt/projects/cis/runtime/api/collab_rounds.py
- /mnt/projects/cis/runtime/api/advisor.py — NEW
- /mnt/projects/cis/runtime/app.py
- /mnt/projects/cis/runtime/ui/src/pages/infra/CollabTracker.jsx
- /home/eric/.hermes/config.yaml (Prime)
- /home/eric/.hermes-r1/config.yaml (R1)
- /home/eric/.hermes-qwen/config.yaml (Qwen)
- /home/eric/.hermes/.env (API_SERVER_KEY)
- /home/eric/.hermes-r1/.env (API_SERVER_KEY + DEEPSEEK_API_KEY)
- /home/eric/.hermes-qwen/.env (API_SERVER_KEY)
- /home/eric/.config/cis-flask.env (API_SERVER_KEY for systemd)
- /home/eric/.config/systemd/user/cis-flask.service
