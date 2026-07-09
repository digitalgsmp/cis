# CIS Pipeline Build — Session Handoff

**Last updated:** 2026-07-09 (session 2)  
**Branch:** main  
**Latest commit:** `c5ad216` — handoff update (pre-container work)  
**Uncommitted changes:** Container transition — see below

---

## Container Status: RUNNING

The CIS pipeline is now running inside Docker container `cis-pipeline` (image `cis-hermes:pipeline`).

**All 7 services UP inside container:**
- 6 gateways: Brain 8644, Draft 8645, Review1 8643, Review2 8647, Menter 8646, Verify 8648
- Pipeline API: port 5000 (published to host)

**First real container pipeline run started:** `run-aed5aeb3911b6d6a-1783612242` — status was `BRAIN_PHASE` when session ended. Poll with:
```bash
curl -s http://localhost:5000/api/relay/run-aed5aeb3911b6d6a-1783612242 | python3 -m json.tool
```

## Fixes Applied This Session (Container Transition)

All changes are on disk, uncommitted. Files to commit:

### 1. `runtime/container_app.py` (NEW)
Minimal Flask app — imports only `relay_bp` + health endpoint. Avoids 30+ legacy blueprints in `app.py` with hardcoded `/mnt/projects` paths that crash in container. This is what the container runs instead of `app.py`.

### 2. `enforcement/mwl-proof-v2/Dockerfile`
- Worker UID changed from default to 1000 (matches host user `eric` so mounted volumes + SQLite DB are writable)
- `deluser pn` (base image's UID 1000 user) before creating `worker`
- Pre-creates all 6 profile home dirs with sealed enforcement plugin at build time (root-owned 0444)
- Removed model pinning from managed config (was forcing all profiles to llamacpp/qwen)

### 3. `enforcement/mwl-proof-v2/entrypoint.sh`
- `python3` → `/usr/local/lib/hermes-agent/venv/bin/python` (Flask installed in venv)
- `runtime.app` → `runtime.container_app` (minimal app)
- Creates per-profile `.env` files with `API_SERVER_KEY` + `DEEPSEEK_API_KEY` + `OPENROUTER_API_KEY`
- Plugin install moved to Dockerfile (entrypoint runs as worker, can't chown to root)

### 4. `enforcement/mwl-proof-v2/managed-config.yaml`
- Removed `model:` section (was pinning llamacpp/qwen for all profiles)
- Only enforcement surfaces pinned: `plugins`, `terminal.backend`, `tool_loop_guardrails`, `auxiliary.compression`

### 5. `enforcement/mwl-proof-v2/profiles/*.yaml` (all 6)
- Added `platforms.api_server.extra.port: <port>` — Hermes reads port from `config.extra.get("port")`, NOT top-level `api_server.port`
- Without this, all gateways defaulted to 8642 (prime port) and failed with "port already in use"

### 6. `runtime/api/idea_uploads.py`
- Hardcoded `/mnt/projects/cis/ingest/incoming` → `CIS_PROJECT_ROOT` env var

### 7. File permission fixes (already on disk)
- `runtime/config.py`, `runtime/api/relay.py`, `runtime/api/session.py`, `runtime/cis_conflict_append.py`, `runtime/primer_update_v2.py` — `0600` → `0644` (worker couldn't read them)

## Enforcement Verification

Container containment verified intact:
- `/etc/hermes/config.yaml` — root:root 0644 — worker **cannot write** ✅
- Plugin `__init__.py` (per-profile) — root:root 0444 — worker **cannot write** ✅
- `/opt/cis-gates/container_gate_runner.py` — root:root 0555 — worker **cannot write** ✅
- Worker has no sudo, no root access
- `HERMES_MANAGED_DIR=/etc/hermes` + `HERMES_ACCEPT_HOOKS=1` baked into image env

## How to Resume

### Start the container
```bash
cd /mnt/projects/cis/enforcement/mwl-proof-v2
./run_container.sh -d
# Pipeline API: http://localhost:5000
# Logs: ./run_container.sh logs
# Exec: ./run_container.sh exec
```

### Stop the container
```bash
./run_container.sh stop
```

### Rebuild after code changes (Dockerfile/profiles)
```bash
cd /mnt/projects/cis/enforcement/mwl-proof-v2
sg docker -c "docker build -t cis-hermes:pipeline -f Dockerfile ."
```
Note: `runtime/` code is mounted as a volume — no rebuild needed for Python changes. Only rebuild for Dockerfile/profile/plugin changes.

### Submit a pipeline run
```bash
curl -s -X POST http://localhost:5000/api/relay/start \
  -H "Content-Type: application/json" \
  -d '{"intent": "Your task description"}'
```

### Check status
```bash
curl -s http://localhost:5000/api/relay/<run_id> | python3 -m json.tool
```

### Prerequisites
- `/tmp/cis-secrets.env` with `DEEPSEEK_API_KEY` and `OPENROUTER_API_KEY`
- Docker image `cis-hermes:pipeline` built
- Host gateways on 8642-8648 should be STOPPED before starting container (port conflict on 5000 only — gateway ports are internal to container)

## What's Next

1. **Verify the test run completes** — poll `run-aed5aeb3911b6d6a-1783612242`. If it progresses through Brain → Draft → Review → Menter → Verify, the container pipeline is fully functional.
2. **Commit the container work** — all files listed above
3. **Stop host gateways** — host gateways (8643-8648) should be stopped when container is running to avoid confusion about which environment is handling work
4. **Systemd fix** — add `KillMode=control-group` to service files (item 4 from previous handoff)
5. **UI** — display pipeline runs in CIS portal (item 5 from previous handoff)

## Key Architecture Notes

- **Host = development.** Host gateways run for dev/testing. Container = production target.
- **Container app = `container_app.py`**, not `app.py`. The full `app.py` has 30+ legacy blueprints with hardcoded host paths. Container app imports only the relay blueprint.
- **Enforcement model**: Managed config (`/etc/hermes/config.yaml`) pins `plugins.enabled`, `plugins.disabled`, `tool_loop_guardrails`, `terminal.backend`. Profile configs own their model settings. The mwl-proof plugin is root-owned and read-only in every profile home.
- **DB path**: `CIS_SPINE_PATH=/workspace/cis/data/cis_memory.db` — set in Dockerfile ENV, points to the mounted volume.
- **Gateway ports are internal** — only port 5000 is published to host. Gateways communicate via `127.0.0.1:864X` inside the container.

## Known Issues

- **Host gateways still running** — if host gateways on 8643-8648 are up, they don't conflict (container ports are internal) but it's confusing. Stop them when using container.
- **DeepSeek API balance** — Brain/Draft/Menter depend on it. HTTP 402 if depleted.
- **Legacy `app.py`** — still used for host dev. Container uses `container_app.py`. Eventually `app.py` should be cleaned up to be container-compatible too.
