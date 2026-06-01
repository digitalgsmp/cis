# CIS Core Rebuild — Foundation Proposal

**For review by: ChatGPT, Claude**
**Prepared by: Hermes (via Eric)**
**Date: May 26, 2026**

---

## The Problem

Eric has three Hermes gateway profiles (Prime, R1, Qwen) running on separate ports (8642, 8643, 8644) with separate config directories (`~/.hermes/`, `~/.hermes-r1/`, `~/.hermes-qwen/`). A Flask/React application at `/mnt/projects/cis/runtime/` provides a dashboard, advisor chat UI, ingestion pipeline, and knowledge base.

**None of it works as intended.** The advisors are not actually different — they all answer as the same model. The KB exists but nobody reads from it. The dashboard shows system info but routes to the wrong gateways. Eric sits down to work and has to re-explain everything from scratch.

This proposal covers ONLY the foundation: making the gateways actually distinct and making new sessions load context automatically. Everything else depends on this.

---

## Current State — What Was Found

### 1. Systemd unit misconfigured (CRITICAL)

The main gateway service (`hermes-gateway.service`) has `HERMES_HOME=/home/eric/.hermes-qwen` — it's pointing at Qwen's config directory instead of Prime's. This means the Prime gateway is reading the wrong config.

```
[Service]
Environment="HERMES_HOME=/home/eric/.hermes-qwen"  # ← SHOULD BE /home/eric/.hermes
```

Additionally, port 8642 (Prime) is currently NOT listening. Only 8643 (R1) and 8644 (Qwen) have bound ports. The service shows "active" in systemd but the port binding may have silently failed.

### 2. reasoning_effort is "medium" everywhere

All three config files have `reasoning_effort: medium`. DeepSeek decides autonomously when to reason — the profiles are not in control of the behavior.

| Profile | Intended Role | Current reasoning_effort | Should Be |
|---------|--------------|--------------------------|-----------|
| Prime (8642) | Fast/snappy chat | medium | low (or disabled) |
| R1 (8643) | Deep reasoning | medium | high |
| V4-Pro (8642) | Deep analyst | medium | high |

### 3. providers dict is empty everywhere

All three config files have `providers: {}` — no named providers defined. Without named providers, there's no way to lock different `reasoning_effort` values per gateway. The `model:` field is set correctly (Prime: `deepseek-v4-flash`, R1: `deepseek-reasoner`) but `reasoning_effort` is a provider-level setting, not a model-level setting.

### 4. Qwen gateway in restart loop

```
hermes-gateway-qwen.service  loaded active auto-restart
```

The Qwen gateway (port 8644) cannot stay running. It's configured to use a custom local provider (`local-qwen`) pointing to `qwen3-vl-30b-a3b-instruct-q4_k_m.gguf` via llama-server on port 8002. The llama-server process IS running and listening on 8002, so the backend is alive — the Hermes gateway can't connect to it stably.

### 5. Agent instances table has 4 entries but only 2 are functional

```
hermes-prime    → port 8642, model deepseek-v4-flash    (NOT LISTENING)
hermes-r1       → port 8643, model deepseek-reasoner    (listening)
hermes-qwen     → port 8644, model qwen3-vl-30b         (listening, restarting)
hermes-v4pro    → port 8642, model deepseek-v4-pro       (shares port with prime)
```

V4-Pro shares port 8642 with Prime — it's the same gateway with a different model ID. This is by design (same gateway, different model) but won't work if the gateway is down.

---

## The Fix — Phase 1: Gateway Configuration

### Step 1: Fix systemd unit for Prime gateway

File: `/home/eric/.config/systemd/user/hermes-gateway.service`

Change:
```
Environment="HERMES_HOME=/home/eric/.hermes-qwen"
```
To:
```
Environment="HERMES_HOME=/home/eric/.hermes"
```

Then: `systemctl --user daemon-reload && systemctl --user restart hermes-gateway`

Verify: `ss -tlnp | grep 8642` should show port 8642 listening.

### Step 2: Define named providers in each config.yaml

The `providers:` dict needs entries with distinct `reasoning_effort` values. This is what locks each gateway to its intended behavior.

**For Prime** (`/home/eric/.hermes/config.yaml`):
```yaml
providers:
  deepseek-fast:
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    reasoning_effort: low
    default_model: deepseek-v4-flash
  deepseek-reasoning:
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    reasoning_effort: high
    default_model: deepseek-v4-pro

model:
  provider: deepseek-fast
```

**For R1** (`/home/eric/.hermes-r1/config.yaml`):
```yaml
providers:
  deepseek-r1:
    base_url: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    reasoning_effort: high

model: deepseek-reasoner
model:
  provider: deepseek-r1
```

**For Qwen** (`/home/eric/.hermes-qwen/config.yaml`):
```yaml
providers:
  local-qwen:
    base_url: http://127.0.0.1:8002/v1
    api_key: none

model:
  provider: local-qwen
```

Note: Qwen uses a local llama-server — `reasoning_effort` is not applicable. The fix here is stability, not reasoning setting.

### Step 3: Diagnose and stabilize Qwen gateway

The Qwen gateway is restarting. Likely causes:
- llama-server 8002 is alive but the gateway's connection settings don't match
- Context size mismatch (gateway sends full history, server has limited ctx)
- Model file path in custom_providers doesn't match what llama-server loaded

Diagnosis steps:
1. Check Qwen gateway logs: `journalctl --user -u hermes-gateway-qwen --since "5 minutes ago"`
2. Verify llama-server model: `curl http://127.0.0.1:8002/v1/models`
3. Test direct chat: `curl http://127.0.0.1:8002/v1/chat/completions -d '{"model":"qwen","messages":[{"role":"user","content":"hello"}]}'`
4. If direct chat works but gateway fails, the issue is in the Hermes config's custom_providers block

**Known issue from prior sessions:** The llama-server runs with `--ctx-size 8192` but Hermes config expects 32K or 65K context. The gateway sends more history than the server can handle, causing 502 errors. Fix: restart llama-server with `--ctx-size 32768` (fits in 24GB VRAM with Q4 quant).

### Step 4: Verify all three gateways answer differently

After config changes, restart all three gateway services and test each:

```bash
# Prime — should be fast, no reasoning
curl -s http://127.0.0.1:8642/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY ~/.hermes/.env | head -1 | cut -d= -f2)" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"Explain quantum computing in one sentence."}]}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:200])"

# R1 — should show reasoning tokens
curl -s http://127.0.0.1:8643/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY ~/.hermes-r1/.env | head -1 | cut -d= -f2)" \
  -d '{"model":"deepseek-reasoner","messages":[{"role":"user","content":"Explain quantum computing in one sentence."}]}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:200])"

# Qwen — should return from local model
curl -s http://127.0.0.1:8644/v1/chat/completions \
  -H "Authorization: Bearer $(grep API_SERVER_KEY ~/.hermes-qwen/.env | head -1 | cut -d= -f2)" \
  -d '{"model":"qwen3-vl-30b","messages":[{"role":"user","content":"Explain quantum computing in one sentence."}]}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:200])"
```

**Pass criteria:** All three return answers. The answers should be from different models — Prime should be short (low reasoning), R1 should show reasoning content, Qwen should identify as a different model.

---

## The Fix — Phase 2: Session Start Context Injection

Once the gateways are actually different, the next problem: when Eric creates a new chat thread, the LLM knows nothing about what he's working on.

### What exists that can be wired together

1. **Handoff endpoint** — `GET /api/collab/handoff` generates a structured briefing from the database: current focus, next action, last 5 activities, active round, do-not rules, evidence links. Returns `{"ok": true, "handoff": "..."}`.

2. **Project Context Pack** — `/mnt/projects/cis/PROJECT_CONTEXT_PACK/` contains 10 markdown files with current state, architecture, decisions, open questions, next actions, model roles.

3. **Knowledge base** — CSS ingestion pipeline feeds content into the KB at `/mnt/projects/cis/runtime/db/cis_memory.db`.

None of these are loaded when a session starts.

### What needs to change

**File:** `api/advisor.py` — the `/api/advisor/threads` POST endpoint

Currently:
```python
# Creates a thread with just a title
INSERT INTO advisor_threads (title) VALUES (?)
```

Should become:
```python
# 1. Create thread
# 2. Fetch handoff from /api/collab/handoff
# 3. Read current state from PROJECT_CONTEXT_PACK/01_CURRENT_STATE.md
# 4. Store both as the thread's context_summary
# 5. Inject as first system message so the LLM knows the context immediately
```

The injection format:
```markdown
[SYS: CIS HANDOFF — {today's date}]
Current focus: {from collab_status}
Next action: {from collab_status}
Recent activity: {last 3 items from collab_activity}
Active round: {current open round topic and decision status}

[SYS: PROJECT STATE]
What is working: {from 01_CURRENT_STATE.md}
What is planned: {from 01_CURRENT_STATE.md}
What is unstable: {from 01_CURRENT_STATE.md}

You are {agent_role}. {agent_description}. 
Do not re-explain decisions already recorded. Continue from this state.
```

**Key constraint:** This is a wire, not a new system. The handoff endpoint already exists. The context pack already exists. This change just loads them at thread creation time instead of waiting for Eric to paste them.

---

## What This Proposal Does NOT Cover

- Fixing the dashboard model picker to route to correct gateways (separate task, depends on Phase 1)
- Wiring the KB into advisor context retrieval (separate task, depends on Phase 1)
- Calendar/timeline integration (separate task)
- Modularity enforcement at the code level (separate architecture task)
- Any creative/project features

This is the foundation only. Everything else in CIS depends on gateways that are actually different and sessions that start with context.

---

## Success Criteria

After Phase 1:
- [ ] Port 8642 (Prime) is listening and responding
- [ ] All three gateways return different model behaviors
- [ ] Qwen gateway is stable (not restarting)
- [ ] Each gateway's config.yaml has named providers with distinct reasoning_effort

After Phase 2:
- [ ] Creating a new advisor thread injects the handoff + project state as system context
- [ ] Eric can start a new chat and the LLM already knows the current focus, next action, and open decisions
- [ ] No manual paste required
