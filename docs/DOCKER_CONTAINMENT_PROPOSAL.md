# Docker Containment Install — Proposal (DRAFT ONLY)
Generated: 2026-06-18 | Author: V4 Drafter | Status: DRAFT — NO EXECUTION

Covers install, verification, Hermes config, containment proof, rollback, risks,
and recommended first step. **Do not implement. Review first.**

---

## 0. Pre-Flight State (Observed)

| Item | Status |
|------|--------|
| Host | creative-vm (PVE VM 100), Ubuntu 24.04.4 LTS, kernel 6.17.0-35 |
| GPU | RTX 4090 (24 GB), driver 580.159.03, CUDA 13.0 |
| Docker | **NOT INSTALLED** — `docker: command not found` |
| llama.cpp | Running on host, port 8002, model qwen3-vl-30b-a3b-instruct-q4_k_m.gguf (~18.5 GB on disk, ~4 GB VRAM) |
| Hermes profiles | 4 profiles (r1 @8643, qwen @8644, v4pro @8645, v4impl @8646) — all `terminal.backend: local` |
| /mnt/archive | 9.1 TB, 88% used (1.2 TB free), cifs mount, root-owned, 777 perms |
| /mnt/projects/cis | 246 GB, 34% used, owned by eric |
| /mnt/projects/swa | Exists at /mnt/projects/swa |
| cis_memory.db | Multiple copies; authoritative = `/mnt/projects/cis/data/cis_memory.db` (380 MB) |
| /mnt/cache/catalog | **DOES NOT EXIST** — needs creation (see §3.3) |
| /mnt/cache | 110 GB, 21% used, owned by eric, ext4 on /dev/vdd2 |

---

## 1. Docker Install — Exact Commands

```bash
# 1a. Remove any stale/dangling Docker packages (none currently, but safe)
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# 1b. Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 1c. Add Docker's official GPG key (Ubuntu 24.04 = noble)
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 1d. Add the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu noble stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 1e. Install Docker Engine + CLI + containerd + compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# 1f. Add eric to docker group (avoids sudo for docker commands)
sudo usermod -aG docker eric
# NOTE: requires logout/login or `newgrp docker` to take effect in current shell

# 1g. Start + enable the daemon
sudo systemctl enable docker
sudo systemctl start docker

# 1h. Verify
docker version
docker run --rm hello-world
```

### What gets touched:
- System packages: `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin`
- Config files: `/etc/apt/sources.list.d/docker.list`, `/etc/apt/keyrings/docker.gpg`
- Daemon: systemd service `docker.service` + `containerd.service`
- Network: `docker0` bridge interface added
- Disk: ~600 MB for packages, container images are additional
- User group: `eric` added to `docker` group

---

## 2. Qwen / llama.cpp (Port 8002) Verification After Install

The risk: Docker adds a `docker0` bridge (usually 172.17.0.0/16) and iptables rules.
llama-server binds `127.0.0.1:8002` — localhost binding is NOT affected by Docker
networking. The only way Docker could interfere is if:

- `docker0` subnet collides with a route needed by llama.cpp (essentially zero risk for localhost)
- Docker's iptables rules block localhost traffic (does not happen — Docker FORWARD chain only)
- Kernel module conflict between `nvidia` and `overlay` (both are well-tested together)

### Verification commands (run after Docker install, before any config change):
```bash
# 2a. Confirm llama-server process still running
ps aux | grep llama-server | grep -v grep

# 2b. Health check
curl -s http://localhost:8002/health
# Expected: {"status":"ok"}

# 2c. Model listing
curl -s http://localhost:8002/v1/models | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data'][0]['id'])"
# Expected: qwen3-vl-30b-a3b-instruct-q4_k_m.gguf

# 2d. Live inference test (lightweight)
curl -s http://localhost:8002/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Say hello in one word.", "max_tokens": 5, "temperature": 0}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['text'])"
# Expected: non-empty response

# 2e. GPU still allocated to llama
nvidia-smi | grep llama-server
```

### Pass/fail criteria:
- All 4 checks produce expected output
- No change in VRAM allocation (remains ~4 GB)
- No change in llama-server PID (not restarted)

---

## 3. Hermes Config: terminal.backend docker

### 3d. Which profile to configure

Start with ONE profile. Recommended: `hermes-r1` (port 8643) — it's the Reviewer,
so containment failure during testing is lower stakes than breaking the
Implementer or Drafter. Test, then roll out to others if the proof passes.

### 3a. Read-only mounts

Docker `docker_volumes` entries use `host_path:container_path:ro` syntax.
Multiple `cis_memory.db` files exist; the convention is to mount their parent
directories read-only so the file is accessible but not writable.

```bash
hermes -p r1 config set terminal.backend docker

hermes -p r1 config set terminal.docker_volumes '[
  "/mnt/archive:/mnt/archive:ro",
  "/mnt/projects/cis:/mnt/projects/cis:ro",
  "/mnt/projects/swa:/mnt/projects/swa:ro",
  "/mnt/projects/cis/data/cis_memory.db:/cis_memory.db:ro"
]'
```

**Important:** The `docker_volumes` YAML value must be a list of strings.
Before setting, verify the config accepts the array syntax. If `hermes config set`
doesn't handle arrays well, edit the file directly:

```bash
hermes -p r1 config edit
```

And add under `terminal:`:
```yaml
terminal:
  backend: docker
  docker_volumes:
    - "/mnt/archive:/mnt/archive:ro"
    - "/mnt/projects/cis:/mnt/projects/cis:ro"
    - "/mnt/projects/swa:/mnt/projects/swa:ro"
    - "/mnt/projects/cis/data/cis_memory.db:/cis_memory.db:ro"
```

**Discovery note on `cis_memory.db`:** The user specified `cis_memory.db` without
a path. There are multiple copies:
- `/mnt/projects/cis/data/cis_memory.db` — 380 MB (likely authoritative, most recent)
- `/mnt/projects/cis/runtime/db/cis_memory.db` — 1 MB
- `/mnt/projects/cis/memory/cis_memory.db` — 41 MB
- `/mnt/projects/cis/cis_memory.db` — 0 bytes (placeholder)

The proposal mounts `/mnt/projects/cis/data/cis_memory.db` as the single-file mount.
If a different copy is intended, adjust the path. Alternatively, mounting the entire
`/mnt/projects/cis` read-only already covers ALL copies — the single-file mount is
an explicit secondary path for clarity.

### 3b. Additional docker config keys

```bash
hermes -p r1 config set terminal.docker_image "nikolaik/python-nodejs:python3.11-nodejs20"
hermes -p r1 config set terminal.docker_mount_cwd_to_workspace false
hermes -p r1 config set terminal.docker_run_as_host_user false
hermes -p r1 config set terminal.container_persistent true
hermes -p r1 config set terminal.docker_persist_across_processes true
```

**Why `docker_run_as_host_user: false`:**
When true, the container runs as `1000:1000` (eric). This means the container
process has the same UID/GID as the host user — so `:ro` mounts enforce
read-only at the **filesystem** level, not the user level. A write attempt
to `:ro` is blocked by the kernel regardless of UID. So `false` (root in
container) is actually the more defensive posture here — it demonstrates
containment works even without user-mapping.

### 3c. Writable mount (/mnt/cache/catalog only)

```bash
# Create the directory first (does not exist currently)
mkdir -p /mnt/cache/catalog

# Add to docker_volumes list (writable — no :ro suffix)
# Final docker_volumes list:
#   - "/mnt/archive:/mnt/archive:ro"
#   - "/mnt/projects/cis:/mnt/projects/cis:ro"
#   - "/mnt/projects/swa:/mnt/projects/swa:ro"
#   - "/mnt/projects/cis/data/cis_memory.db:/cis_memory.db:ro"
#   - "/mnt/cache/catalog:/mnt/cache/catalog"
```

### 3d. Full terminal section (target)

```yaml
terminal:
  backend: docker
  cwd: "."
  timeout: 180
  docker_image: "nikolaik/python-nodejs:python3.11-nodejs20"
  docker_mount_cwd_to_workspace: false
  docker_run_as_host_user: false
  docker_volumes:
    - "/mnt/archive:/mnt/archive:ro"
    - "/mnt/projects/cis:/mnt/projects/cis:ro"
    - "/mnt/projects/swa:/mnt/projects/swa:ro"
    - "/mnt/projects/cis/data/cis_memory.db:/cis_memory.db:ro"
    - "/mnt/cache/catalog:/mnt/cache/catalog"
  container_persistent: true
  docker_persist_across_processes: true
```

---

## 4. Containment Proof Test

After config is applied and the gateway/service is restarted:

### 4a. Launch a session in the container

```bash
hermes -p r1 chat -q "Run: touch /mnt/archive/test_write && echo WRITE_SUCCEEDED || echo WRITE_REFUSED"
```

Or equivalently, from within an interactive session, instruct the agent:
```
Run: touch /mnt/archive/test_write && echo "WRITE SUCCEEDED" || echo "WRITE REFUSED"
```

### 4b. Expected output

```
touch: cannot touch '/mnt/archive/test_write': Read-only file system
WRITE REFUSED
```

### 4c. Write to writable mount (must succeed)

```
Run: echo "containment test $(date)" > /mnt/cache/catalog/proof.txt && cat /mnt/cache/catalog/proof.txt
```

Expected: writes and reads back the file successfully.

### 4d. Cross-check from host

```bash
cat /mnt/cache/catalog/proof.txt
ls /mnt/archive/test_write 2>&1   # should say "No such file or directory"
```

### 4e. cis_memory.db read test

```
Run: stat /cis_memory.db && echo "READABLE" || echo "NOT_READABLE"
```

Expected: file stats show size ~380 MB, `READABLE`.

### Pass criteria (all must pass):
1. Write to `/mnt/archive` → REFUSED (read-only filesystem error)
2. Write to `/mnt/projects/cis` → REFUSED
3. Write to `/mnt/projects/swa` → REFUSED
4. Write to `/cis_memory.db` → REFUSED
5. Write to `/mnt/cache/catalog` → SUCCEEDS
6. `cis_memory.db` is readable inside the container
7. Host filesystem unchanged (no test_write file on archive)

---

## 5. Bare-Shell Rollback

If ANYTHING breaks — container won't start, gateway crashes, Qwen becomes
unreachable, or any unexpected behavior:

```bash
# 5a. Revert terminal backend to local (per profile)
hermes -p r1 config set terminal.backend local

# 5b. Restart the gateway to pick up the change
systemctl --user restart hermes-gateway@r1

# 5c. Verify it works
hermes -p r1 chat -q "echo ROLLBACK_SUCCESSFUL"
```

### Nuclear option (if Docker itself causes problems):
```bash
# Stop containers
docker stop $(docker ps -q) 2>/dev/null || true

# Remove Docker packages
sudo apt-get purge -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo apt-get autoremove -y

# Clean up Docker data
sudo rm -rf /var/lib/docker /var/lib/containerd

# Remove docker group membership (optional)
sudo gpasswd -d eric docker 2>/dev/null || true
```

### What rollback touches:
- `~/.hermes-r1/config.yaml` — one line change (`backend: local`)
- Systemd gateway restart — brief downtime (~5 seconds for the r1 gateway)
- No filesystem state changed (all Docker-created dirs under /var/lib/docker)

### What rollback does NOT touch:
- Other 3 profiles (qwen, v4pro, v4impl) — they continue on `local` backend
- llama.cpp / Qwen on port 8002 — never affected
- Any project files under /mnt/projects or /mnt/archive
- Any Hermes sessions, memory, or skills

---

## 6. Risks, Touched State, and Recommended First Step

### 6a. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docker install breaks Qwen/llama.cpp | Very low | HIGH (Qwen is the only local model) | §2 verification runs immediately after install; rollback §5 is minutes |
| docker0 bridge IP collision | Very low | Medium (network disruption) | No VM uses 172.17.0.0/16; Proxmox host uses 192.168.1.0/24 |
| Hermes docker backend doesn't start | Low | Medium (r1 gateway offline) | Test with CLI `hermes -p r1` before touching the gateway service |
| Overlay2 + ext4 on /mnt/cache | None | — risk | ext4 is the native, most-tested backing fs for overlay2 |
| GPU passthrough to container | N/A | — | **NOT** in scope for this proposal — llama.cpp stays on host. Containers are CPU-only. |
| `docker_volumes` :ro syntax not honored by Hermes | Low | Medium | Verified in source: `tools/environments/docker.py` line 667 uses `:ro` suffix correctly |
| Read-only mount of a single file (cis_memory.db) | Medium | Low | Docker supports single-file bind mounts. If the file changes on host (e.g., sqlite WAL grows), the mount stays valid. BUT: sqlite creates `-wal` and `-shm` sibling files that won't be mounted. Mounting the directory read-only is safer. |
| Gateway hooks (cis_pre_tool_gate.sh) run in container | Medium | Medium | The v4impl profile has `hooks.pre_tool_call` pointing to `/mnt/projects/cis/tools/hooks/cis_pre_tool_gate.sh`. If r1 also has hooks, they'll try to execute inside the container — need to verify the hook works there. |

### 6b. System state touched

| What | Before | After |
|------|--------|-------|
| `docker` command | Not found | Available |
| docker.service / containerd.service | N/A | Running, enabled |
| `docker0` interface | N/A | Created (172.17.0.1/16) |
| iptables FORWARD chain | Default | Docker rules added |
| eric group membership | No docker group | Added to docker |
| `/var/lib/docker` | N/A | Created (~100 MB initially) |
| `/mnt/cache/catalog` | Does not exist | Created (empty dir) |
| `~/.hermes-r1/config.yaml` | `backend: local` | `backend: docker` + volumes |
| `~/.hermes-r1/.env` | Unchanged | Unchanged |
| Other 3 profiles | Unchanged | Unchanged |
| llama.cpp / port 8002 | Running on host | Running on host (unchanged) |
| `/mnt/archive`, `/mnt/projects/*` | Unchanged | Unchanged (read-only mounts) |

### 6c. Recommended first step

**Install Docker only. Do not touch Hermes config yet.**

```bash
# 1. Install Docker (§1)
# 2. Run Qwen verification (§2)
# 3. STOP AND REVIEW
```

After Docker install + Qwen verification passes:
- Start a manual `docker run --rm -it ubuntu:24.04 bash` and manually test the
  mount syntax:
  ```bash
  docker run --rm -it \
    -v /mnt/archive:/mnt/archive:ro \
    -v /mnt/cache/catalog:/mnt/cache/catalog \
    ubuntu:24.04 bash
  # Inside: touch /mnt/archive/test → should fail
  # Inside: touch /mnt/cache/catalog/test → should succeed
  ```
- Only then proceed to §3 (Hermes config).

---

## 7. Open Design Questions

1. **Which cis_memory.db?** Multiple copies exist. Mounting `/mnt/projects/cis:ro`
   already covers all of them. The single-file mount is belt-and-suspenders.
   Should we just drop it and rely on the directory mount?

2. **Sqlite WAL files.** If the container reads `/cis_memory.db:ro` while the
   host has an active writer, sqlite's WAL mode creates `cis_memory.db-wal`
   and `cis_memory.db-shm` sibling files. The single-file mount won't include
   those. Mounting the directory read-only avoids this entirely. Recommend:
   drop the single-file mount, use only the directory mount.

3. **Do gateways restart cleanly with docker backend?** The systemd services
   for all 4 profiles use `ExecStart` pointing at the venv python. When the
   config says `terminal.backend: docker`, Hermes will try to `docker run`
   a container. If the gateway process is running as user `eric` and eric is
   in the `docker` group, this should work — but the first launch will pull
   the `nikolaik/python-nodejs` image (~1 GB). Set a generous startup timeout.

4. **Which profile first?** r1 is recommended (Reviewer, lowest operational
   risk). v4impl has hooks that may break in the container — test r1 first,
   then assess gateway hook compatibility before rolling to v4impl.

5. **GPU access from container?** This proposal keeps all GPU work on the
   host (llama.cpp on port 8002). The container only runs Hermes tool calls
   (terminal, file ops) — CPU-only. GPU passthrough (`--gpus all`) is NOT
   included and would be a separate proposal.

---

## Appendix A: Hermes Source Confirmation — docker_volumes :ro Syntax

From `/home/eric/.hermes/hermes-agent/tools/environments/docker.py` lines 664-668:

```python
volume_args.extend([
    "-v",
    f"{mount_entry['host_path']}:{mount_entry['container_path']}:ro",
])
```

This confirms the `:ro` suffix is passed directly to `docker run -v`, which
is the standard Docker syntax for read-only bind mounts. The same mechanism
applies to user-configured `docker_volumes` entries (line 590-591):

```python
if ":" in vol:
    volume_args.extend(["-v", vol])
```

Any `docker_volumes` entry with `:ro` suffix is passed verbatim to Docker.

---

## Appendix B: Current Gateway/Service State

```
Profile      Port   Backend     Systemd Unit
hermes-r1    8643   local       hermes-gateway@r1
hermes-qwen  8644   local       hermes-gateway@qwen
hermes-v4pro 8645   local       hermes-gateway@v4pro
hermes-v4impl 8646  local       hermes-gateway@v4impl
```

All four run directly on the host (no Docker). Only r1 would change to Docker
backend in this proposal. The other three stay on `local`.

---

**END OF PROPOSAL — Do not implement. Awaiting review.**
