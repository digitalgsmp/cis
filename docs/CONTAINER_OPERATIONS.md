# CIS Container Operations Reference

> **Purpose:** Single source of truth for container setup, build, deploy, and troubleshooting.
> Accessible by BOTH host-side agents (path: /mnt/projects/cis/docs/) and container agents (path: /workspace/cis/docs/).
> Load this file instead of re-discovering container architecture from scratch.

## 1. Container Architecture

| Property | Value |
|----------|-------|
| Container name | `cis-pipeline` |
| Image | `cis-hermes:pipeline` |
| Dockerfile | `enforcement/mwl-proof-v2/Dockerfile` |
| Entrypoint | `enforcement/mwl-proof-v2/entrypoint.sh` |
| Launch script | `enforcement/mwl-proof-v2/run_container.sh` |
| Runtime user | `worker` (UID 1000 = host user `eric`) |
| Docker GID | 982 (host `docker` group, worker is member) |

## 2. Volume Mounts

| Host path | Container path | Mode |
|-----------|---------------|------|
| `/mnt/projects/cis` | `/workspace/cis` | read-write |
| `/tmp/cis-secrets.env` | `/workspace/secrets.env` | read-only |
| `/var/run/docker.sock` | `/var/run/docker.sock` | read-write (for System Dashboard) |

## 3. Ports

| Port | Service | Scope |
|------|---------|-------|
| 5000 | Flask pipeline API | Published to host |
| 8644 | Brain gateway (deepseek-v4-pro) | Internal (127.0.0.1) |
| 8645 | Drafter gateway (deepseek-v4-pro) | Internal |
| 8643 | Reviewer1 gateway (qwen3.7-max) | Internal |
| 8647 | Reviewer2 gateway (glm-5.2) | Internal |
| 8646 | Implementer gateway (deepseek-v4-pro) | Internal |
| 8648 | Verifier gateway (glm-5.2) | Internal |

## 4. Build and Deploy Commands

### Rebuild the image (after Dockerfile changes)
```bash
sg docker -c "docker build -t cis-hermes:pipeline \
  -f /mnt/projects/cis/enforcement/mwl-proof-v2/Dockerfile \
  /mnt/projects/cis/enforcement/mwl-proof-v2/"
```

### Recreate the container (after image rebuild)
```bash
cd /mnt/projects/cis/enforcement/mwl-proof-v2
./run_container.sh stop
./run_container.sh -d
```

### Restart without rebuild
```bash
sg docker -c "docker restart cis-pipeline"
```

### View logs
```bash
sg docker -c "docker logs -f cis-pipeline"
# Or specific gateway log:
sg docker -c "docker exec cis-pipeline cat /tmp/cis-logs/brain.log"
```

### Exec into container
```bash
sg docker -c "docker exec -it cis-pipeline bash"
```

### UI build (React → dist/ → served by Flask)
```bash
# From host (npm installed on host):
cd /mnt/projects/cis/runtime/ui && npm run build
# Flask serves the built files from runtime/ui/dist/ at /ui/
# No container restart needed — files are on the mounted volume
```

## 5. Docker Access from Host

Eric is in the `docker` group (GID 982) but the active shell session doesn't load it.
**Always use:** `sg docker -c "<docker command>"`
Do NOT use sudo (requires password, not available in agent sessions).
Do NOT claim docker commands are impossible — `sg docker -c` works.

## 6. Host-Side Fallbacks

Eric intentionally runs systemd Hermes services on ports 8642-8648 as a fallback.
These are SEPARATE from the container gateways. Do NOT remove or modify them.
The container's internal gateways are the active pipeline; systemd is backup.

## 7. Container Profile Setup

The entrypoint.sh creates 6 Hermes profile homes inside the container:
- `/home/worker/.hermes-brain/` → port 8644
- `/home/worker/.hermes-draft/` → port 8645
- `/home/worker/.hermes-review1/` → port 8643
- `/home/worker/.hermes-review2/` → port 8647
- `/home/worker/.hermes-menter/` → port 8646
- `/home/worker/.hermes-verify/` → port 8648

Each gets:
- `config.yaml` copied from `/etc/hermes/profiles/<name>.yaml` (root-owned, sealed)
- `.env` with `API_SERVER_KEY` + `DEEPSEEK_API_KEY` + `OPENROUTER_API_KEY`
- Sealed `plugins/mwl-proof/` enforcement plugin (root-owned, read-only)

The managed config at `/etc/hermes/config.yaml` provides enforcement overrides
(hooks block, plugins.enabled, model pin) that the worker cannot modify.

## 8. System Dashboard (System Tab)

The System tab shows gateway health, service health, and gateway logs.
It does NOT have docker container management — the worker is contained and
must not have docker socket access (that would break the enforcement model,
ADR-015/016). Container restart must be done from the host:
  `sg docker -c "docker restart cis-pipeline"`

Available endpoints (Flask, port 5000):
- `GET /api/relay/system/health` — gateway health + service health (SQLite, ChromaDB, llama-servers)
- `GET /api/relay/system/logs/<container>` — reads gateway log files from /tmp/cis-logs/<profile>.log
- `POST /api/relay/system/restart` — returns 403 with instructions (not available from contained worker)
- `POST /api/relay/system/restart-all` — returns 403 (not available from contained worker)

## 9. Known Operational Notes

- Container restart preserves `/tmp` (Docker behavior), so entrypoint cleans stale pidfiles
- The Flask API process PID is stored at `/tmp/pipeline_api.pid`
- Gateway logs are at `/tmp/cis-logs/<profile>.log` inside the container
- Secrets file at `/tmp/cis-secrets.env` on host must contain `DEEPSEEK_API_KEY` and `OPENROUTER_API_KEY`
- The `cis-hermes:pinned` image is the enforcement PoC (runs sleep infinity, kept as reference)
- UI mockups in `runtime/ui_mockups/` are early experiments — Eric wants real design in Penpot
