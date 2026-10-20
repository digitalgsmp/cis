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
| Docker GID | 982 on host; this is a temporary bootstrap capability and conflicts with the final trust boundary |
| Containment status | Transitional, not retirement-ready; see queue 4.37 continuity revisions 1-4 |

## 2. Volume Mounts

| Host path | Container path | Mode |
|-----------|---------------|------|
| `/mnt/projects/cis` | `/workspace/cis` | read-only |
| `/mnt/projects/cis/data` | `/workspace/cis/data` | read-write nested exception |
| `/mnt/projects/cis/state` | `/workspace/cis/state` | read-write nested exception |
| `/mnt/projects/swa` | `/workspace/swa` | read-write (known over-broad mount; must be removed/narrowed) |
| `/mnt/projects/swa-app` | `/workspace/swa-app` | read-write (known over-broad mount; must be removed/narrowed) |
| `$SECRETS_FILE` (`/mnt/projects/cis/secrets.env`) | `/workspace/secrets.env` | read-only |

The launcher **never sources** the secrets file. It runs as host root under
systemd, so it parses the file as data with `awk`, copies a fixed allowlist of
names into a private mode-0600 env-file under `/tmp`, hands Docker that file
with `--env-file`, and deletes it on exit. A symlinked, missing or non-regular
secrets path is refused. `DEEPSEEK_API_KEY` and `OPENROUTER_API_KEY` are not
forwarded into the environment at all — the container reads them from the
read-only mount, which keeps them out of `docker inspect`.

The task workspace (`/mnt/cache/cis-workspaces/pipeline-control` →
`/workspace/output`) is created owned by uid/gid 1000 with mode 0700, because a
root-created directory under the unit's `UMask=0077` would be unwritable to the
contained worker. An existing workspace is adopted, not rewritten; the launcher
refuses to start if it is owned by anyone other than the worker.

There is **no Docker socket mount** in the live `cis-pipeline` container. The
older table said there was one; live `docker inspect` disproved it on
2026-10-16. Do not add one.

The current hardened container mounts its enforcement controls from the
root-owned `/opt/cis-control` tree read-only. Historical containers sourced
some of those controls from the developer repository; do not restore that
legacy arrangement.

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

**Lifecycle precedence:** before the native service is installed, direct
launcher and Docker commands below are bootstrap/recovery operations only.
After `cis-pipeline.service` is installed, lifecycle ownership moves to
`systemctl`; do not run the repository launcher or `docker restart` against a
systemd-managed container because that desynchronizes `RemainAfterExit` state.
The root-owned launcher in `/opt/cis-control/bin/cis-container` is the only
approved service launcher.

### Rebuild the image (after Dockerfile changes)
```bash
sg docker -c "docker build -t cis-hermes:pipeline \
  -f /mnt/projects/cis/enforcement/mwl-proof-v2/Dockerfile \
  /mnt/projects/cis/enforcement/mwl-proof-v2/"
```

### Recreate the container (after image rebuild)
```bash
# Bootstrap only, before native service installation:
/opt/cis-control/bin/cis-container stop
/opt/cis-control/bin/cis-container -d

# Once the native service is installed and activation is authorized:
sudo systemctl restart cis-pipeline.service
```

### Restart without rebuild
```bash
sudo systemctl restart cis-pipeline.service
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

Eric is currently in the `docker` group (GID 982). This permits bootstrap
administration but contradicts ADR-SEED-015's final assumption that ordinary
external-developer sessions cannot administer Docker. Use it only while queue
4.37 is open. The retirement-ready design replaces it with a narrow root-owned
launcher/service and removes ordinary developer Docker membership.

For read-only inspection during reconstruction: `sg docker -c "docker ..."`.
Do not use Docker bind mounts as a substitute for root installation into
`/opt/cis-control`; this host's UID mapping changed that tree to uid/gid 65534
during the 2026-10-16 proof. Repair requires the operator's real sudo path.

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

The System tab shows gateway health, service health, and gateway logs. It does
NOT have Docker container management. The worker has no Docker socket and must
never receive one; that would break ADR-SEED-015/016. Container restart remains
a temporary host/bootstrap operation while queue 4.37 is open:
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
- The secrets file (`SECRETS_FILE` in `run_container.sh`, currently
  `/mnt/projects/cis/secrets.env`) must contain `DEEPSEEK_API_KEY` and
  `OPENROUTER_API_KEY`, one `NAME=value` per line. It is read as data, never
  executed, so shell syntax in it has no effect
- The `cis-hermes:pinned` image is the enforcement PoC (runs sleep infinity, kept as reference)
- UI mockups in `runtime/ui_mockups/` are early experiments — Eric wants real design in Penpot
- `docker inspect` exposes container environment metadata to Docker
  administrators. Do not copy secret values into evidence or continuity
  records. Credentials exposed during inspection must be rotated.
- The live combined container has a writable root filesystem, default
  capabilities, no `no-new-privileges`, broad SWA write mounts, and shared
  control/worker state. It is operational but not evidence of retirement-ready
  containment. Do not restart it into a replacement manifest until a
  deterministic container-boundary gate passes.

## 10. Host Trust-Root Repair and Promotion

The reviewed release inventory is
`config/control-plane-release.json`. The read-only verifier is
`tools/development/gate_control_plane_install.py`. A file merely existing below
`/opt/cis-control` is not acceptance: its bytes, exact mode, root ownership, and
entire installed parent chain must pass that gate.

The earlier UID-remapping incident has been repaired: the current
`/opt/cis-control` release is root-owned and passed the release gate. A future
promotion or repair must still use real password-authorized operator authority;
do not treat a Docker bind mount as the normal installation path.

### 10.1 Complete manifest-driven promotion

Every command below corresponds to one artifact in
`config/control-plane-release.json`, and the list is complete: the gate fails if
any declared artifact is absent, and the `runtime/gates` tree check also fails on
any **undeclared** installed file or directory. Copy the tree with explicit
`install` globs, never with `cp -r` or `rsync` — a `__pycache__` directory
dragged along is an undeclared file and fails the gate. From `/mnt/projects/cis`,
after reviewing the manifest and the source diff:

```bash
sudo chown -R root:root /opt/cis-control
sudo chmod -R go-w /opt/cis-control
sudo install -d -o root -g root -m 0755 /opt/cis-control /opt/cis-control/bin /opt/cis-control/policy /opt/cis-control/systemd /opt/cis-control/contracts /opt/cis-control/runtime /opt/cis-control/runtime/plugin /opt/cis-control/runtime/profiles /opt/cis-control/gate
sudo install -d -o root -g root -m 0555 /opt/cis-control/runtime/gates
sudo install -o root -g root -m 0555 tools/development/control_dispatch.py /opt/cis-control/bin/cis-dispatch
sudo install -o root -g root -m 0444 tools/development/control_dispatch.py /opt/cis-control/bin/control_dispatch.py
sudo install -o root -g root -m 0555 tools/development/control_contract.py /opt/cis-control/bin/cis-contract
sudo install -o root -g root -m 0555 enforcement/mwl-proof-v2/run_container.sh /opt/cis-control/bin/cis-container
sudo install -o root -g root -m 0555 tools/development/gate_host_launch_service.py /opt/cis-control/bin/cis-host-launch-gate
sudo install -o root -g root -m 0555 tools/development/install_host_launch_service.py /opt/cis-control/bin/cis-host-launch-install
sudo install -o root -g root -m 0444 config/dispatch-policy.json /opt/cis-control/policy/dispatch-policy.json
sudo install -o root -g root -m 0444 config/pipeline-image-id.txt /opt/cis-control/policy/pipeline-image-id.txt
sudo install -o root -g root -m 0440 config/sudoers/cis-pipeline /opt/cis-control/policy/cis-pipeline.sudoers
sudo install -o root -g root -m 0444 config/systemd/cis-pipeline.service /opt/cis-control/systemd/cis-pipeline.service
sudo install -o root -g root -m 0555 enforcement/mwl-proof-v2/entrypoint.sh /opt/cis-control/runtime/entrypoint.sh
sudo install -o root -g root -m 0444 enforcement/mwl-proof-v2/managed-config.yaml /opt/cis-control/runtime/managed-config.yaml
sudo install -o root -g root -m 0555 enforcement/mwl-proof-v2/gates/*.py enforcement/mwl-proof-v2/gates/*.sh /opt/cis-control/runtime/gates/
sudo install -o root -g root -m 0444 enforcement/mwl-proof-v2/container_gate_runner.py /opt/cis-control/runtime/gates/container_gate_runner.py
sudo install -o root -g root -m 0444 enforcement/mwl-proof-v2/plugin/__init__.py /opt/cis-control/runtime/plugin/__init__.py
sudo install -o root -g root -m 0444 enforcement/mwl-proof-v2/plugin/plugin.yaml /opt/cis-control/runtime/plugin/plugin.yaml
sudo install -o root -g root -m 0444 enforcement/mwl-proof-v2/profiles/*.yaml /opt/cis-control/runtime/profiles/
sudo install -o root -g root -m 0444 .gate-control/README.md /opt/cis-control/gate/README.md
python3 tools/development/gate_control_plane_install.py --manifest config/control-plane-release.json --source-root /mnt/projects/cis
```

The last command must report `"passed": true`. A failed result blocks container
replacement and the host-launch install below. The `gate/DISABLED` file is
intentionally absent during normal operation; only the human operator may create
it for time-bounded break glass.

### 10.2 One-command host-launch installer

Once the promotion above passes, the systemd unit and the narrow sudoers policy
are installed by one sealed program, run once with native sudo:

```bash
sudo /opt/cis-control/bin/cis-host-launch-install
```

What it does, in this order:

1. Refuses unless it is running with real root authority.
2. Proves the sealed unit (0444), sudoers policy (0440), host-launch gate (0555)
   and `cis-container` launcher (0555) are root-owned, exact-mode, regular,
   non-symlinked files — before executing or copying any of them.
3. Refuses symlinked installation destinations (and symlinked parent directories).
4. Snapshots the existing `/etc/systemd/system/cis-pipeline.service`,
   `/etc/sudoers.d/cis-pipeline` and the unit's prior `is-enabled` state.
5. Syntax-checks the policy with `visudo`, stages it under a dotted name sudo
   ignores, re-checks it, then atomically renames it into place.
6. Installs the unit, reloads systemd, and runs the sealed gate
   (`/opt/cis-control/bin/cis-host-launch-gate`) **before** enabling anything.
7. Only then enables the unit, and proves the result by querying systemd:
   `is-enabled` must report `enabled` and `is-active` must report `inactive`.

Any failure at any step restores both files and the prior enabled state, reloads
systemd, and reports the rollback actions it took. It never starts or restarts
the service. On success it prints the `systemctl` strings it observed plus the
full command log, so the end state is read from systemd rather than asserted.

Re-verify independently at any time (read-only):

```bash
sudo /opt/cis-control/bin/cis-host-launch-gate
```

### 10.3 Activation is withdrawn

**Activation remains withdrawn pending verification.** Installing and enabling
the unit is not activation and is not authorization to run the service. Do not
run `sudo systemctl start cis-pipeline.service`, and do not treat an enabled unit
as a working launch path: nothing here has yet been proven on a live host. The
installer is deliberately incapable of starting the service for this reason.

Activation requires, in order: a passing manifest promotion, a passing
host-launch gate, independent verification of the launch path, and Eric's
explicit go. After promotion, validate the candidate/replacement container with:

```bash
python3 tools/gates/gate_container_boundary.py --container cis-pipeline
```

Do not call queue 4.37 complete until the promoted release passes, a hardened
container created from it passes the container gate, and one bounded real task
produces independently verified evidence.
