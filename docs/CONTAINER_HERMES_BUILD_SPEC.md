# Container Hermes — Permanent Installation Build Spec

**For:** Claude (external advisor, guide role)  
**Audience:** Eric (operator, non-coder, approves/disapproves)  
**Date:** 2026-07-01  
**Status:** BUILD READY — all architecture decisions settled, POC proven

---

## What This Is

A step-by-step build guide for Claude to walk Eric through creating a **permanent, sealed Hermes installation running inside a Docker container** that enforces the CIS three-layer process isolation architecture.

After this build, all CIS work (pipeline, knowledge base, development) happens inside the container. The host is only for launching the container and reading results.

---

## What Already Exists (Do Not Rebuild)

These are proven artifacts. Claude should reference them, not recreate them.

### Architecture Decisions (settled — no debate needed)

| Document | What it decides |
|---|---|
| `docs/DEV-PIVOT-17_ENFORCEMENT_ARCHITECTURE.md` | Three-layer isolation: CIS control plane → Hermes worker (Docker) → workspace |
| `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` | 703-line spec: contract shape, policy hook, evidence requirements, 15 acceptance tests |
| ADR-SEED-015 (in spine) | Enforcement architecture approved — three-layer process isolation |
| ADR-SEED-016 (in spine) | Enforcement primitive approved — 15 acceptance tests A–O |
| `AGENTS.md` §4 Active Decisions | Contains the settled enforcement decisions |

### POC Proof Files (proven working)

| File | What it proves |
|---|---|
| `enforcement/mwl-proof-v2/Dockerfile` | Builds a non-root worker container with Hermes 0.17.0, managed config, and plugin |
| `enforcement/mwl-proof-v2/managed-config.yaml` | The sealed contract the worker cannot edit (model pin, plugin enforcement, hook consent) |
| `enforcement/mwl-proof-v2/standing_container_block_proof.txt` | Proves: worker tried to disable enforcement, Docker RO mount + root-owned plugin blocked it. Wall holds. |
| `enforcement/mwl-proof-v2/run_v6.txt` | Full POC run log |
| `enforcement/mwl-proof-v2/run_v7.txt` | Full POC run log |
| `enforcement/mwl-proof-v2/verify_seal.sh` | Seal verification script |
| `enforcement/mwl-proof-v2/cis_shell_hook.sh` | Shell hook for terminal command interception |

### Infrastructure (running, do not touch)

| Component | Status | Details |
|---|---|---|
| Docker | Installed (29.6.0) | Eric NOT in docker group — requires `sudo` |
| Qwen model server | Running | Port 8002, `--ctx-size 32768`, model: `qwen3-vl-30b-a3b-instruct-q4_k_m.gguf` |
| Hermes gateways | Running | Ports 8643 (r1), 8644 (qwen), 8645 (v4pro), 8646 (v4impl) |
| CIS spine | `/mnt/projects/cis/data/cis_memory.db` | 32 tables, 287K knowledge messages |
| ChromaDB | `/mnt/projects/cis/data/chroma_data/` | 287,636 documents |
| `/opt/cis-control/` | Exists at `proofs/` | Needs full control plane structure (see Step 4) |

---

## What's Broken or Missing (These Are the Build Steps)

### Critical blockers (container won't run without these)

1. **`plugin/` directory is missing.** The Dockerfile says `COPY plugin/` but `enforcement/mwl-proof-v2/plugin/` does not exist. The mwl-proof plugin code must be created or recovered.

2. **No Docker image built.** `docker images` shows nothing. The image was built during POC but has been removed or never persisted.

3. **No container running.** `docker ps` is empty.

4. **`managed-config.yaml` has wrong context_length.** Shows `65536` — the Qwen server runs with `--ctx-size 32768`. Must match or Hermes will crash on long contexts.

5. **No harness script.** There's no script that Eric can run to launch the container with correct mounts, volumes, and network config.

### Non-critical (container runs but isn't "permanent")

6. **No workspace directory.** `/mnt/cache/catalog/` doesn't exist. The container needs a writable workspace mount.

7. **Hermes version may be stale.** Dockerfile pins `0.17.0`. Current Hermes may be newer. Loop-breaker code is in host Hermes at `tool_guardrails.py` line 235 — must be present in container Hermes too.

8. **No `/opt/cis-control/` control plane structure.** Only `proofs/` exists. The full structure from DEV-PIVOT-17 (contract templates, policy checker, frozen contracts, task templates) doesn't exist yet.

9. **No `--add-host` in Dockerfile or harness.** Container needs `host.docker.internal` to reach Qwen on port 8002.

10. **No persistent state volume.** Container state.db and sessions die with the container. Need a Docker volume or bind mount for `~worker/.hermes/`.

---

## Build Plan (For Claude to Guide Eric Through)

### Step 1: Fix the managed config (Eric, 2 minutes)

File: `/mnt/projects/cis/enforcement/mwl-proof-v2/managed-config.yaml`

Change both `context_length` values from `65536` to `32768`:

```yaml
model:
  provider: llamacpp
  base_url: http://host.docker.internal:8002/v1
  default: qwen3-vl-30b-a3b-instruct-q4_k_m.gguf
  context_length: 32768    # ← was 65536

auxiliary:
  compression:
    context_length: 32768  # ← was 65536
```

**Why:** Qwen's llama-server is running with `--ctx-size 32768`. Hermes will crash with OOM or silent truncation if it tries to use 65536.

**Evidence check:** After change, `grep context_length /mnt/projects/cis/enforcement/mwl-proof-v2/managed-config.yaml` should show `32768` twice.

---

### Step 2: Recover or create the mwl-proof plugin (Claude writes, Eric places)

The `plugin/` directory needs these files:

```
enforcement/mwl-proof-v2/plugin/
├── plugin.yaml        # Plugin manifest
└── __init__.py        # pre_tool_call hook — the enforcement wall
```

**`plugin.yaml`:**
```yaml
name: mwl-proof
version: "1.0.0"
description: "CIS enforcement wall — pre_tool_call policy hook"
hooks:
  - pre_tool_call
```

**`__init__.py`:** Claude must write this. Minimum requirements:
- `pre_tool_call(tool_name, tool_args, context) → dict` — return `{"allow": True}` or `{"allow": False, "reason": "..."}`
- Must check: tool name against allowlist, file paths against RO mounts, writes only to workspace
- Must be root-owned (644) in the container so worker cannot edit
- The POC proven in `standing_container_block_proof.txt` used this hook pattern — Claude should reference the run logs for what was tested

**Evidence check:** After placing, `find /mnt/projects/cis/enforcement/mwl-proof-v2/plugin -type f` should show `plugin.yaml` and `__init__.py`.

---

### Step 3: Create workspace and control plane directories (Eric, 2 minutes)

```bash
# Workspace — the ONLY writable mount
sudo mkdir -p /mnt/cache/catalog
sudo chown eric:eric /mnt/cache/catalog

# Control plane structure (basic scaffolding)
sudo mkdir -p /opt/cis-control/contracts
sudo mkdir -p /opt/cis-control/templates
sudo mkdir -p /opt/cis-control/policy
sudo mkdir -p /opt/cis-control/proofs
```

**Evidence check:** `ls -d /mnt/cache/catalog /opt/cis-control/{contracts,templates,policy,proofs}` should show all five directories.

---

### Step 4: Update the Dockerfile if needed (Claude reviews)

The existing Dockerfile at `enforcement/mwl-proof-v2/Dockerfile`:
- Pins Hermes `0.17.0`
- Copies `plugin/` (now exists after Step 2)
- Copies `managed-config.yaml` to `/etc/hermes/config.yaml`
- Creates `worker` user, bakes enforcement env vars
- Sets `CMD ["sleep", "infinity"]`

Claude should check:
- **Hermes version:** Host checkout is `0.13.0` (May 7, 2026). Dockerfile pins `0.17.0`. The install script (`install.sh`) installs the latest release, so `0.17.0` was correct at POC time. If the release has moved, update the `grep -q "X.Y.Z"` line in the Dockerfile to match whatever `hermes --version` reports after install.
- **Loop-breaker:** Host has it at `tool_guardrails.py` lines 235, 264, 372-373 (`_success_repeat_counts`). The container's Hermes is installed from the release script — if the release includes the loop-breaker, no action needed. If it doesn't, the Dockerfile must COPY or patch the file. Claude must test this (Step 6.7 — run a query, watch for 9+ identical tool calls, verify they get blocked).
- **`--add-host`:** This is a **run-time** flag, not a Dockerfile instruction. The harness script (Step 5) must include `--add-host=host.docker.internal:host-gateway`.

**Evidence check:** `docker build --dry-run` or just review the Dockerfile for correctness.

---

### Step 5: Write the harness script (Claude writes, Eric places)

File: `/mnt/projects/cis/enforcement/mwl-proof-v2/harness.sh`

This is the script Eric runs to launch the container. One command — `./harness.sh` — builds the image (if needed), creates the container, and starts it.

Minimum content:

```bash
#!/bin/bash
# harness.sh — Launch the sealed CIS Hermes worker container
set -e

IMAGE="cis-hermes:pinned"
CONTAINER="cis-worker"
WORKSPACE="/mnt/cache/catalog"
CIS_ROOT="/mnt/projects/cis"
CONTROL="/opt/cis-control"

echo "=== Building image (if needed) ==="
sudo docker build -t "$IMAGE" -f Dockerfile .

echo "=== Removing old container (if exists) ==="
sudo docker rm -f "$CONTAINER" 2>/dev/null || true

echo "=== Launching sealed worker ==="
sudo docker run -d \
  --name "$CONTAINER" \
  --add-host=host.docker.internal:host-gateway \
  -v "$CIS_ROOT":/mnt/projects/cis:ro \
  -v "$CONTROL":/opt/cis-control:ro \
  -v "$WORKSPACE":/mnt/cache/catalog:rw \
  -v cis-worker-state:/home/worker/.hermes \
  "$IMAGE" sleep infinity

echo "=== Container started: $CONTAINER ==="
sudo docker ps --filter "name=$CONTAINER"
```

**Key details:**
- `cis-worker-state` is a Docker volume — persists state.db, sessions, memories across container rebuilds
- `:ro` on CIS root and control plane — Docker enforces read-only at kernel level
- `:rw` only on workspace
- `--add-host` lets the container reach Qwen on the host

**Evidence check:** After running, `sudo docker ps` should show `cis-worker` with status `Up`.

---

### Step 6: Test the seal (Eric + Claude verify)

Once the container is running:

```bash
# 1. Enter the container
sudo docker exec -it cis-worker bash

# 2. Verify managed config is in effect
hermes doctor 2>&1 | grep -i managed
# Should show: "Managed config dir: /etc/hermes"

# 3. Verify plugin is loaded
hermes plugins list
# Should show: mwl-proof (enabled)

# 4. Try to write to RO mount — should FAIL
echo "breach" > /mnt/projects/cis/breach.txt
# Must return: "Read-only file system"

# 5. Try to disable plugin — should FAIL
mv ~/.hermes/plugins/mwl-proof ~/.hermes/plugins/mwl-proof.disabled
# Must return: "Permission denied"

# 6. Verify Hermes can reach Qwen
curl -s http://host.docker.internal:8002/v1/models | head -c 200
# Should return model info JSON

# 7. Run a simple Hermes query
echo "Say hello and confirm you are running in a Docker container." | hermes run --no-tools
```

**Evidence check:** All seven tests must pass. Capture output for the proof file.

---

### Step 7: Run the acceptance tests (Claude designs, Eric executes)

From `TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` §7, there are 15 acceptance tests (A–O). Claude should:
1. Select 3–5 tests that verify the core isolation primitive
2. Write them as bash commands Eric can paste
3. Have Eric run them and capture output

At minimum, verify:
- **Test A-like:** Container refuses write to RO mount (kernel wall)
- **Test B-like:** Worker cannot disable plugin (permissions wall)
- **Test C-like:** Worker cannot edit managed config (managed scope wall)
- **Test D-like:** Hermes can complete a simple read-only task (proves the system works)

---

### Step 8: Install CIS tools inside the container (Eric + Claude)

For the worker to do CIS work:

```bash
# Inside container
pip install chromadb sentence-transformers

# Copy the CIS spine tools into the container
# (Or mount them — but they must be RO since they're in /mnt/projects/cis)
```

The worker needs access to:
- `/mnt/projects/cis/runtime/` — MCP bridge, adapter, tools (read-only)
- `/mnt/projects/cis/data/cis_memory.db` — spine (read-only for worker, RW for CIS control plane queries)
- `/mnt/projects/cis/tools/` — catalog scripts (read-only)

Since these are under the RO mount, the worker can use them but not modify them. This IS the enforcement.

---

## What Comes After (Future, Not This Build)

These are OUT OF SCOPE for this build. Do not attempt them now.

- Contract compiler (template validator from TASK_CONTRACT spec)
- Reviewer quality gate (Claude API as adversarial reviewer)
- Write-back from agent to spine (Eric Gate required)
- Spine restructure (observations/entities/intentions design from 2026-07-01 conversation)
- Multi-profile container (just Qwen for now — one model, one worker)
- Gateway inside container (Hermes CLI only for now)

---

## Acceptance Criteria — When Is This "Done"?

The build is complete when ALL of these are true:

1. [ ] `sudo docker ps` shows `cis-worker` running
2. [ ] `sudo docker exec cis-worker hermes doctor` shows managed config from `/etc/hermes`
3. [ ] `sudo docker exec cis-worker hermes plugins list` shows `mwl-proof` enabled
4. [ ] Container refuses writes to `/mnt/projects/cis/` (Read-only file system)
5. [ ] Worker cannot rename/delete the plugin directory (Permission denied)
6. [ ] Worker cannot edit `/etc/hermes/config.yaml` (Permission denied)
7. [ ] Hermes can reach Qwen at `host.docker.internal:8002` and complete a query
8. [ ] Loop-breaker is active (Hermes stops after 9 identical successful tool calls)
9. [ ] Worker state persists across `docker rm` + `docker run` (Docker volume `cis-worker-state`)
10. [ ] Eric can run `harness.sh` to rebuild and restart the container with one command
11. [ ] All evidence captured in a proof file at `/mnt/projects/cis/enforcement/mwl-proof-v2/RESULTS/build_proof_$(date +%Y%m%d).txt`

---

## Key Principles for Claude

1. **Eric is not a coder.** Every instruction must be a copy-paste command or a short series of commands. No "write a script that..." — Claude writes the script, Eric places it.

2. **Evidence over claims.** After every step, capture the command output. The proof file is the evidence that the build succeeded. No "trust me it worked."

3. **The container is the future.** After this build, all CIS development happens inside the container. The host is only for launching the container and reading results. Treat the container as the permanent environment, not a test.

4. **If something breaks, stop and diagnose.** Don't patch around failures. The enforcement walls must be proven working before any CIS work begins inside the container.

5. **The managed config is the contract.** Every enforcement surface (plugins, hooks, model pin, context length) is pinned in `/etc/hermes/config.yaml`. The worker reads it but cannot write it. If a feature isn't pinned there, the worker can disable it.

---

## Reference Files (For Claude's Context)

These are the files Claude should read before building:

| File | Why |
|---|---|
| `docs/DEV-PIVOT-17_ENFORCEMENT_ARCHITECTURE.md` | Architecture decisions |
| `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` | Full enforcement spec, acceptance tests §7 |
| `enforcement/mwl-proof-v2/Dockerfile` | Current Dockerfile (Step 4 may update) |
| `enforcement/mwl-proof-v2/managed-config.yaml` | Current managed config (Step 1 fixes context_length) |
| `enforcement/mwl-proof-v2/standing_container_block_proof.txt` | Proof the POC wall worked |
| `enforcement/mwl-proof-v2/run_v7.txt` | Full POC run log — shows what was tested |
| `AGENTS.md` | Current state, architecture, active decisions |
| `PROJECT_CONTEXT_PACK_UPLOAD/HCP_11_OPERATIONAL_STATE.md` | (if generated) Operational state snapshot |
