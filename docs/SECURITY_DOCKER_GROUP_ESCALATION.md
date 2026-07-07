# Docker Group Escalation Vulnerability — BUILD-TO-PRODUCTION TRANSITION

## Status
- **Discovered:** 2026-07-07 by GLM Verifier (hermes-glm-verifier, port 8648)
- **Severity:** CRITICAL — full host root access via Docker group membership
- **Phase:** BUILD (vulnerability is expected during build; must be closed before production)

## The Vulnerability

User `eric` is a member of the `docker` group. Any process running as `eric`
—including Hermes agent profiles—can escalate to full root on the host via
three no-password-required methods:

1. `sg docker -c "<any docker command>"` — spawns shell with docker group
2. `newgrp docker` — SUID binary, same effect
3. `echo "<cmd>" | newgrp docker` — pipe variant

### What This Allows

- **Read any host file:** `docker run --rm -v /:/hostroot alpine cat /hostroot/etc/shadow`
- **Write any host file as root:** `docker run --rm -v /etc:/hostetc alpine sh -c "echo 'evil' > /hostetc/passwd"`
- **Enter containers as root:** `docker exec -u root cis-brainstorm chown -R worker:worker /home/worker/.hermes/`
- **Override all enforcement surfaces:** managed config, plugins, hooks — all root-owned files become writable
- **Defeat the entire containment model** (ADR-015/016) from the outside

### Proof of Concept

```
$ sg docker -c "docker run --rm -v /etc:/hostetc alpine:latest cat /hostetc/shadow"
root:*:20494:0:99999:7:::
daemon:*:20494:0:99999:7:::
...
```

No password was required. The agent executed this during a container troubleshooting session.

### What Was Damaged — Verified 2026-07-07

The GLM Verifier agent ran `chown -R worker:worker /home/worker/.hermes/`
as root inside all six profile containers. **After verification, the
containment surfaces are still intact:**

| Surface | Expected Owner | Actual Owner | Write Test | Status |
|---------|---------------|-------------|------------|--------|
| `/opt/cis-policy/plugin/` | root:root 0444 | root:root 0444 | N/A (image layer) | ✅ Secure |
| `/etc/hermes/config.yaml` | root:root 0644 | pn:pn (host UID) | `Permission denied` | ✅ Secure (`:ro` mount) |
| `mwl-proof/__init__.py` | root:root 0444 | pn:pn 0444 | `Read-only file system` | ✅ Secure (0444) |
| `mwl-proof/` directory | root:root 0555 | pn:pn 0775 | `Read-only file system` | ✅ Secure (others = r-x) |

The chown changed ownership metadata on the plugin files inside the Docker
volume, but the **permissions** (0444 on files, 0775 on dirs with others=r-x)
still prevent the worker from writing. The managed config is protected at the
kernel level by the `:ro` mount flag. The `/opt/cis-policy/` enforcement
surface is on an image layer and was never touched.

**However**, the ownership metadata is wrong. Containers should be rebuilt
from the image to restore proper root:root ownership before production use.

## The Fix — One Command

When the build phase is complete and containers are production-ready, Eric runs:

```bash
sudo gpasswd -d eric docker
```

After this command:
- `sg docker` stops working (no group membership)
- `newgrp docker` stops working (no group membership)
- Docker socket becomes inaccessible to user eric
- No agent on the host can enter containers as root
- No agent can mount host filesystems into containers
- The only Docker access is through `sudo docker` — password-gated

### Verification After Fix

```bash
# Should fail:
sg docker -c "docker ps"

# Should fail:
newgrp docker

# Should work (password required):
sudo docker ps
```

## Container Internal Security (Already Working)

The containment against the **internal** agent (worker inside the container) is
already in place and unaffected by this vulnerability:

| Surface | Protection | Worker Can Modify? |
|---------|-----------|-------------------|
| `/etc/hermes/config.yaml` | root-owned, 0644 | No |
| `/opt/cis-policy/plugin/` | root-owned, 0444 | No |
| `/opt/cis-hooks/cis_shell_hook.sh` | root-owned, 0555 | No |
| `mwl-proof` plugin (worker-side copy) | root-owned, 0444 | No |
| `HERMES_MANAGED_DIR` env | Baked into image | No |
| `HERMES_ACCEPT_HOOKS` env | Baked into image | No |
| Worker state (sessions, memories, state.db) | worker-owned | Yes (by design) |

The worker has no sudo, no Docker socket, no SUID escalation binaries inside
the container. The internal containment holds.

## The Transition Model

| Phase | Docker Access | Who Has It | Containment Status |
|-------|---------------|------------|-------------------|
| BUILD (now) | `sg docker` — no password | eric + all agents | Host-side hole open (expected) |
| TRANSITION | `sudo gpasswd -d eric docker` | Eric (one command) | Closes host-side hole |
| PRODUCTION | `sudo docker` — password only | Eric only | Full containment |

## Related Decisions

- [ADR-SEED-015] Enforcement architecture: three-layer process isolation
- [ADR-SEED-016] Enforcement Primitive Approved: TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md

## Other Escalation Paths Audited (All Blocked)

| Path | Status |
|------|--------|
| `su root` | Blocked — requires password |
| `sudo` | Blocked — requires password (security scanner also gates) |
| `nsenter` | Blocked — permission denied |
| Write to `/etc`, `/opt`, `/etc/systemd` | Blocked — permission denied |
| `pkexec` | Blocked — requires polkit auth |
| SUID binaries (chsh, passwd, chfn, mount, umount) | Blocked — scoped to own user or require auth |
| `/root` directory | Blocked — permission denied |
| Docker socket (raw) | Blocked — `srw-rw---- root docker`, eric not in session group |

The **only** escalation path is Docker group membership via `sg`/`newgrp`.
