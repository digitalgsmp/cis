# Docker Container Audit Reference

**Created:** 2026-07-07
**Verified by:** GLM Verifier (port 8648)

## When to Use

When verifying that Docker container profiles match host configuration, or when debugging container gateway issues. The containers are the enforcement reference architecture per ADR-SEED-015/016.

## 1. Container Overview (Updated 2026-07-12)

### Architecture: One Container, Not Six

The CIS pipeline runs inside **one container** — `cis-pipeline` (image `cis-hermes:pipeline`). This container holds:
- Flask API on port 5000 (published to host)
- All 6 Hermes gateways running internally on 127.0.0.1:8643-8648 (NOT published)
- The entrypoint.sh launches all 6 profiles + the Flask app

The 6 separate gateway containers (cis-brainstorm, cis-drafter, etc. on image `cis-hermes:v2`, ports 874x) were **leftover from an earlier build phase** and were **removed on 2026-07-12**. They were never the active architecture — the decision was always "one container, six profiles" (lighter on resources).

The `cis-hermes` container (image `cis-hermes:pinned`) is the original enforcement proof-of-concept. It runs `sleep infinity` and is not active. Kept as a reference snapshot for future VM expansion.

### Host-Side Services Are Intentional

The host-side systemd gateway services on 127.0.0.1:864x are **Eric's fallback** for root-required work and repairs the container can't do itself. Do NOT recommend stopping or removing them. Eric is not a coder and needs the host side as a safety net while learning the container system.

### Internal Gateway Health Check

The System Dashboard health check queries `127.0.0.1:864x/health` directly from inside the container. These are the internal gateways the pipeline actually uses. The Docker container list is shown for overview but gateway health is NOT checked via Docker port mappings (those don't work from inside the container).

## 2. Docker Access Pattern

Docker requires `sg docker` (group access) on this system. All docker commands must be prefixed:

```bash
sg docker -c "docker ps --filter 'name=cis-' --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

**⚠️ SECURITY WARNING:** `sg docker` gives full root-equivalent access with NO password. See §7 below. This is acceptable during BUILD phase only.

## 3. Container Audit Methodology

### Step 1: Verify Containers Are Running

```bash
sg docker -c "docker ps -a --filter 'name=cis-' --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'"
```

All 6 profile containers plus `cis-hermes` (the pinned reference) should be running.

### Step 2: Verify Model/Provider Inside Each Container

```bash
for c in cis-brainstorm cis-drafter cis-qwen-reviewer cis-glm-reviewer cis-implementer cis-verifier; do
  echo "=== $c ==="
  sg docker -c "docker exec $c cat /etc/hermes/config.yaml" 2>/dev/null | grep -E "default:|provider:|port:|reasoning" | head -4
  echo
done
```

Expected: same models, providers, and ports as host profiles.

### Step 3: Verify Hermes Version

```bash
sg docker -c "docker exec cis-brainstorm hermes --version"
# Should show: Hermes Agent v0.17.0
```

### Step 4: Check Gateway State Inside Containers

```bash
for c in cis-brainstorm cis-drafter cis-qwen-reviewer cis-glm-reviewer cis-implementer cis-verifier; do
  echo "=== $c ==="
  sg docker -c "docker exec $c cat /home/worker/.hermes/gateway_state.json" 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('State:', d.get('gateway_state'))
print('Platforms:', {k: v.get('state') for k, v in d.get('platforms', {}).items()})
" 2>/dev/null || echo "no state file"
  echo
done
```

### Step 5: Check Container Logs for Errors

```bash
sg docker -c "docker logs --tail 20 <container_name>" 2>&1
```

## 4. CRITICAL: Container Enforcement Ownership Model

**Never `chown -R` the entire `/home/worker/.hermes/` directory inside a container.** This breaks containment by changing ownership of enforcement surfaces from root to worker. The worker (LLM) can then overwrite the enforcement plugin, defeating the entire architecture.

### Ownership Rules

| Path | Owner | Purpose | Worker can write? |
|---|---|---|---|
| `/etc/hermes/config.yaml` | root (0644) | Managed config (sealed contract) | NO |
| `/opt/cis-policy/plugin/` | root (0444) | Enforcement plugin source | NO |
| `/home/worker/.hermes/plugins/mwl-proof/` | root (0444) | Active enforcement plugin | NO |
| `/home/worker/.hermes/sessions/` | worker | Session files | YES |
| `/home/worker/.hermes/state.db` | worker | Session store | YES |
| `/home/worker/.hermes/memories/` | worker | Memory files | YES |
| `/home/worker/.hermes/.env` | worker | Environment vars | YES |

### If Sessions Permission Errors Occur

Fix ONLY the state directories, not the entire `.hermes` tree:

```bash
# CORRECT — targeted fix
sg docker -c "docker exec -u root <container> chown -R worker:worker /home/worker/.hermes/sessions/"
sg docker -c "docker exec -u root <container> chown worker:worker /home/worker/.hermes/state.db"
sg docker -c "docker exec -u root <container> chown -R worker:worker /home/worker/.hermes/memories/"

# WRONG — breaks containment
sg docker -c "docker exec -u root <container> chown -R worker:worker /home/worker/.hermes/"
```

### If You Already Ran the Wrong chown

Verify which surfaces were affected. On 2026-07-07, the GLM Verifier ran `chown -R worker:worker /home/worker/.hermes/` on all 6 containers. Verification showed:

- `/opt/cis-policy/plugin/` — still root:root (image layer, untouched) ✅
- `/etc/hermes/config.yaml` — `:ro` mount flag held at kernel level ✅
- `mwl-proof/__init__.py` — ownership changed to `pn:pn` but permissions 0444 still prevent writes ✅
- Worker could NOT write to the plugin: `touch: cannot touch '.../test_write': Read-only file system` ✅

**Containment held because permissions (0444) prevented writes even after ownership changed.** But ownership metadata is wrong. Containers should be rebuilt from the image to restore proper root:root ownership before production.

**This is why Eric needs containment** — the LLM's training data biases it toward "fix the permission error" without considering that the permission model IS the security boundary. The containment only works if the container is owned by root. If the LLM can overwrite everything, it is not containment.

## 5. Known Container Issues (as of 2026-07-12)

### Issue: Flask Not Picking Up Code Changes After Edit

**Symptom:** You edit relay.py or container_app.py on the host (mounted volume) but the Flask process inside the container still serves old code.

**Root cause:** Python caches imported modules in `__pycache__`. The Flask process loaded the module at startup and doesn't re-import on file change.

**Fix:** Restart the container: `sg docker -c "docker restart cis-pipeline"`. Wait ~12 seconds for gateways to come up. The health endpoint (`/api/health`) responds before the relay blueprint finishes loading — wait for relay endpoints to work too (can take 5+ additional seconds).

### Issue: SQLite Case Sensitivity on project_id

**Symptom:** Project overview endpoint returns empty build_plan or runs for project "cis" even though data exists.

**Root cause:** `build_plan_nodes` table stores `project_id` as "CIS" (uppercase), but the API receives "cis" (lowercase). SQLite text comparison is case-sensitive by default.

**Fix:** Use `COLLATE NOCASE` in all project_id WHERE clauses in relay.py.

### Issue: Health Check Shows All Gateways Down

**Symptom:** System Dashboard shows all 6 gateways as "gateway-down" even though the pipeline works.

**Root cause:** The health check was trying to reach gateway container ports (874x) from inside the pipeline container, where those host-mapped ports aren't reachable.

**Fix (applied 2026-07-12):** Health check now queries `127.0.0.1:864x/health` directly — these are the internal gateways the pipeline actually uses.

## 6. Container Architecture (ADR-SEED-015/016)

### Enforcement Walls (container-only)

1. **Kernel RO mounts:** `/source/cis`, `/source/swa`, `/source/archive` mounted read-only
2. **Managed config scope:** `/etc/hermes/config.yaml` is root-owned (0644), worker cannot modify model, plugins, or tool_loop_guardrails
3. **Plugin immutability:** `mwl-proof` plugin root-owned, chmod 0444, worker cannot rewrite
4. **Environment baked into image:** `HERMES_MANAGED_DIR=/etc/hermes` and `HERMES_ACCEPT_HOOKS=1` are image ENV vars, not runtime — worker subprocess cannot repoint or de-consent

### Container File Layout

```
/etc/hermes/config.yaml          # Managed config (root-owned, sealed)
/opt/cis-policy/plugin/          # mwl-proof enforcement plugin (root-owned, 0444)
/home/worker/.hermes/            # Worker state (state.db, sessions, memories)
/home/worker/.hermes/plugins/    # Observer plugin copy (root-owned, sealed)
/source/cis/                     # CIS repo (read-only mount)
/source/archive/                 # Archive (read-only mount)
/workspace/                      # Per-run workspace (writable)
```

### Harness Script

`/mnt/projects/cis/enforcement/profile-harness.sh` launches all 6 containers. It:
- Seeds `.env` into Docker volumes (preserved across rebuilds)
- Mounts managed config as `/etc/hermes/config.yaml:ro`
- Maps 864x → 874x ports
- Creates writable workspace at `/mnt/cache/catalog/cis-<name>/`

## 7. CRITICAL: Docker Group Escalation Vulnerability

**Discovered:** 2026-07-07 by GLM Verifier
**Severity:** CRITICAL — full host root access via Docker group membership
**Documented in:** `docs/SECURITY_DOCKER_GROUP_ESCALATION.md`

### The Vulnerability

User `eric` is in the `docker` group. Any process running as `eric` — including Hermes agent profiles — can escalate to full root on the host via three no-password methods:

1. `sg docker -c "<any docker command>"` — spawns shell with docker group
2. `newgrp docker` — SUID binary, same effect
3. `echo "<cmd>" | newgrp docker` — pipe variant

### What This Allows

- Read any host file: `docker run --rm -v /:/hostroot alpine cat /hostroot/etc/shadow`
- Write any host file as root: `docker run --rm -v /etc:/hostetc alpine sh -c "echo 'evil' > /hostetc/passwd"`
- Enter containers as root: `docker exec -u root <container> chown -R worker:worker /home/worker/.hermes/`
- Override ALL enforcement surfaces (managed config, plugins, hooks)

### The Fix — One Command (PRODUCTION ONLY)

When the build phase is complete:

```bash
sudo gpasswd -d eric docker
```

After this:
- `sg docker` stops working
- `newgrp docker` stops working
- Docker socket becomes inaccessible to user eric
- No agent can enter containers as root or mount host filesystems
- Only `sudo docker` works (password-gated)

### Build-to-Production Transition Model

| Phase | Docker Access | Who Has It | Containment Status |
|-------|---------------|------------|-------------------|
| BUILD (now) | `sg docker` — no password | eric + all agents | Host-side hole open (expected) |
| TRANSITION | `sudo gpasswd -d eric docker` | Eric (one command) | Closes host-side hole |
| PRODUCTION | `sudo docker` — password only | Eric only | Full containment |

### Other Escalation Paths (All Blocked)

| Path | Status |
|------|--------|
| `su root` | Blocked — requires password |
| `sudo` | Blocked — requires password (security scanner also gates) |
| `nsenter` | Blocked — permission denied |
| Write to `/etc`, `/opt`, `/etc/systemd` | Blocked — permission denied |
| `pkexec` | Blocked — requires polkit auth |
| `/root` directory | Blocked — permission denied |

The ONLY escalation path is Docker group membership via `sg`/`newgrp`.

## 8. Host vs Container Summary (Updated 2026-07-12)

| Aspect | Host | Container (cis-pipeline) |
|---|---|---|
| Hermes version | v0.16.0 | v0.16.0 (pinned in image) |
| Models | Same | Same |
| Ports | 864x (direct) | 864x internal, 5000 published |
| AGENTS.md | Loaded from cwd | Loaded from /workspace/cis |
| Enforcement (mwl-proof) | No | Yes (root-owned plugin) |
| Managed config | No | Yes (/etc/hermes/config.yaml) |
| Role personality | Generic SOUL.md | Role-specific via profile configs |
| tool_loop_guardrails | No | hard_stop_enabled: true |
| Docker socket | Not needed | Mounted for System Dashboard |
| Purpose | Fallback for root work + repairs | Primary pipeline + UI |

### Key Principle
The container is the primary working environment. The host is the fallback for things the container can't do (root operations, image rebuilds, package installs). Eric wants to transition fully to the container UI and stop using terminal/Telegram for routine work.
