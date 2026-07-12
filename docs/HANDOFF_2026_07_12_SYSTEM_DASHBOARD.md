# Handoff — 2026-07-12: System Dashboard + Provenance Layer

**Git HEAD:** `3c677ea` (uncommitted changes in container_app.py, relay.py, ui/src/)
**Container:** `cis-pipeline` running, `cis-hermes:pipeline` image
**UI:** CIS Control Panel v1.1.0 — 4 tabs (Brain, Pipeline, Runs, System)

---

## What Was Built This Session

### 1. System Dashboard (UI v1.1.0 — new "System" tab)
- **`SystemDashboard.jsx`** — container health, service health, restart buttons, log viewer
- **API endpoints** registered directly on `container_app.py` (NOT relay.py — see Known Issues):
  - `GET /api/relay/system/health` — all Docker containers + SQLite/llama-servers/ChromaDB
  - `POST /api/relay/system/restart` — restart single container (whitelisted)
  - `POST /api/relay/system/restart-all` — restart all in dependency order
  - `GET /api/relay/system/logs/<container>` — last 50 lines
- **Docker socket mounted** into container: `-v /var/run/docker.sock:/var/run/docker.sock`
- **Docker CLI installed** in container via `apt-get install docker.io` (as root)
- **Docker GID matched**: host GID=982, container was 102, fixed with `groupmod -g 982 docker`
- **CSS** added to `index.css` for all System Dashboard components
- **API confirmed working** — returns 9 containers, service statuses

### 2. Provenance / Intent Alignment Layer (built prior, session carries over)
- `_lock_intent_provenance()` — stores Brain output as intent anchor with KB context hash
- `_intent_anchor_block()` — generates injection text for downstream phases
- `_record_phase_drift()` — stores drift scores at each phase boundary
- `guardrail_intent_drift` in `guardrails.py` — 40% keyword / 30% scope / 30% action alignment
- `gate_intent_verification.py` — aggregate drift check at verify phase
- Wired into all 6 downstream phases in `pipeline_relay.py`

### 3. Local GLM for Drift Detection (built prior)
- GLM-4.7-Flash (Q4_K_M) at 94 tok/s, ~5 seconds per check
- Needs 1000 max_tokens (reasoning model — thinks before answering)
- Only fires when deterministic score is ambiguous (0.15–0.65 range)
- Combined score: 40% deterministic + 60% semantic

### 4. UI Architecture (built prior)
- **Brain tab**: chat with KB search, intent enrichment, "Start Pipeline" button
- **Pipeline tab**: live feed with phase cards, drift badges, backchannel interjection
- **Runs tab**: browse past runs, click to view in Pipeline tab
- **System tab**: container/service health, restart, logs (new this session)
- React 19 + Vite 8, built to `runtime/ui/dist/`
- DB migrations 0028: `brain_chats`, `pipeline_interjections` tables

---

## Known Issues — Must Fix

### A. Gateway Health Check Port Mismatch (HIGH)
Containers map host ports 8743→8643, 8744→8644, etc. The health check in `_system_health()` pings `localhost:{internal_port}` which isn't reachable from the Flask process. All 6 gateways show "gateway-down" even though they're running.

**Fix:** Change the port extraction in `container_app.py` `_system_health()` to use the host-mapped port (left side of `→`), not the container-internal port.

### B. Relay.py Blueprint Routes Not Loading (HIGH)
New routes added to `relay.py` (system/health, system/restart, etc.) do not appear in Flask's URL map, even though:
- The file compiles cleanly (`py_compile` passes)
- The routes are in the file (grep confirms)
- The file is identical inside and outside the container (md5match)
- Container was fully stopped/started (not just restarted)

**Workaround applied:** Routes registered directly on `app` in `container_app.py` instead of via `relay_bp`. This works but means the system routes in `relay.py` (lines 1483+) are dead code. Should investigate why the blueprint doesn't pick up late-appended routes.

### C. Docker Socket + CLI Not in Dockerfile (MEDIUM)
The docker socket mount and docker CLI install were done at runtime. If the container is recreated from the image (`cis-hermes:pipeline`), these are lost.

**Fix needed:** 
- Add `apt-get install docker.io` to Dockerfile
- Add `-v /var/run/docker.sock:/var/run/docker.sock` to the docker run command or docker-compose
- Add `groupmod -g 982 docker && usermod -aG docker worker` to Dockerfile (GID 982 is host docker group)

### D. Restarting cis-pipeline From Itself (MEDIUM)
The "Restart" button on `cis-pipeline` kills the API mid-response. The user gets an error. Need to either:
- Return success before restarting, then restart asynchronously
- Or exclude `cis-pipeline` from the restart list and show a "restart manually" message

### E. Uncommitted Changes
The following files have uncommitted changes:
- `runtime/container_app.py` — system dashboard routes added directly
- `runtime/api/relay.py` — system dashboard routes added (dead code, see issue B)
- `runtime/ui/src/SystemDashboard.jsx` — new file
- `runtime/ui/src/App.jsx` — System tab added
- `runtime/ui/src/api.js` — system API client methods
- `runtime/ui/src/index.css` — system dashboard CSS
- `runtime/ui/package.json` — version bumped to 1.1.0
- `runtime/ui/dist/` — rebuilt

---

## Container Setup (Current)

```
Container: cis-pipeline
Image: cis-hermes:pipeline
Mounts:
  /mnt/projects/cis → /workspace/cis (rw)
  /mnt/projects/cis/secrets.env → /workspace/secrets.env (ro)
  /var/run/docker.sock → /var/run/docker.sock (rw)  ← NEW, runtime-only
Port: 5000
Restart: unless-stopped
Docker GID: 982 (matched to host)
```

**To recreate with docker socket:**
```bash
docker stop cis-pipeline && docker rm cis-pipeline
docker run -d \
  --name cis-pipeline \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /mnt/projects/cis:/workspace/cis \
  -v /mnt/projects/cis/secrets.env:/workspace/secrets.env:ro \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cis-hermes:pipeline
# Then install docker CLI and fix GID:
docker exec -u root cis-pipeline apt-get update -qq && apt-get install -y -qq docker.io
docker exec -u root cis-pipeline groupmod -g 982 docker
docker exec -u root cis-pipeline usermod -aG docker worker
docker restart cis-pipeline
```

---

## Gateway Containers (separate from cis-pipeline)

| Container | Host Port | Internal | Model | Image |
|-----------|-----------|----------|-------|-------|
| cis-brainstorm | 8744 | 8644 | deepseek-v4-pro | cis-hermes:v2 |
| cis-drafter | 8745 | 8645 | deepseek-v4-pro | cis-hermes:v2 |
| cis-qwen-reviewer | 8743 | 8643 | qwen3.7-max | cis-hermes:v2 |
| cis-glm-reviewer | 8747 | 8647 | glm-5.2 | cis-hermes:v2 |
| cis-implementer | 8746 | 8646 | deepseek-v4-pro | cis-hermes:v2 |
| cis-verifier | 8748 | 8648 | glm-5.2 | cis-hermes:v2 |
| cis-hermes (prime) | — | — | deepseek-v4-pro | cis-hermes:pinned |

All gateways run on `cis-hermes:v2` image, 5 days uptime. Prime on `cis-hermes:pinned`, 9 days.

---

## Entry Points for Next Session

### Direction 1: Fix Known Issues (recommended first)
1. Fix gateway health check port mapping (issue A)
2. Update Dockerfile with docker CLI + socket mount + GID fix (issue C)
3. Handle self-restart gracefully (issue D)
4. Commit everything (issue E)
5. Investigate relay.py blueprint route loading (issue B)

### Direction 2: Test Full Pipeline End-to-End
1. Start GLM llama-server and ChromaDB on host
2. Start a pipeline run from the Brain tab
3. Verify intent provenance, drift detection, backchannel all work
4. Check System tab shows everything green

### Direction 3: Expand Local GLM Usage
Candidate roles identified for local GLM-4.7-Flash:
1. Interjection classification (backchannel message routing)
2. Loop-breaker detection (semantic tool call comparison)
3. KB retrieval ranking (filter irrelevant context)
4. Guardrail explanations (plain-language failure messages)
5. Deliberation compression (summarize prior rounds)
6. Intent clarification flag (ambiguity detection)

---

## File Locations

| File | Purpose |
|------|---------|
| `runtime/container_app.py` | Flask app + system dashboard routes |
| `runtime/api/relay.py` | Pipeline relay blueprint (1480+ lines) |
| `runtime/ui/src/SystemDashboard.jsx` | System tab React component |
| `runtime/ui/src/App.jsx` | Main app with 4 tabs |
| `runtime/ui/src/api.js` | API client |
| `runtime/ui/src/index.css` | All styles |
| `runtime/ui/package.json` | v1.1.0 |
| `runtime/abstraction/pipeline_relay.py` | Pipeline state machine + provenance |
| `runtime/guardrails.py` | 34 guardrails + intent_drift |
| `data/cis_memory.db` | SQLite spine |

---

## Context for Next Session

- Eric wants the UI to be the primary interface — no more terminal for routine operations
- The System dashboard is the "ops" layer — see everything, restart from browser
- Provenance layer is built but NOT yet tested end-to-end (container was stale, now fixed)
- GLM-4.7-Flash is the local model for drift detection (94 tok/s, 1000 max_tokens)
- Only $2 left on DeepSeek account — don't call DeepSeek APIs unless necessary
- Eric prefers: build it, verify it works, show evidence — no promises
