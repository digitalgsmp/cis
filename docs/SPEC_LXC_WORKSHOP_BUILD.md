# SPEC — Permanent LXC Workshop Build

**Status:** DRAFT | **Date:** 2026-07-04 | **Author:** Drafter (V4 Pro)
**Purpose:** Build the permanent contained Hermes environment on Proxmox LXC, installed and verified by the CIS pipeline team using the hosted profiles as construction crew.

## What This Is

A Proxmox LXC container on wander (192.168.1.200) that runs the complete CIS pipeline — 6 profiles, enforcement walls, knowledge infrastructure, and the intentions-driven session protocol. After this build, all CIS work happens inside the LXC. The hosted profiles on creative-vm become the construction crew that builds it, then transition to backup/overflow roles.

## What Changed Since the Claude Draft

The Claude draft (July 1) assumed Docker, one worker profile, and Claude as external guide. Since then:

- **11,775 Drive files recovered** — full archive: SWA project, UTAB system, Ten Commandments, G.O.D. Protocol, CIS foundation docs, extraction analyses, session transcripts
- **Trajectory memory concept** — the "Did You Know" capability is now understood as retrieval of agent trajectories (past session work), not model training data search
- **Eric's intentions confirmed and indexed** — 15 intentions in the spine, derived from archive archaeology
- **Pipeline team fully operational** — 6 profiles running, adapter API on 5000, Qwen 3.7 Max reviewer, all gateways healthy
- **Profile soul emerged** — Ten Commandments + G.O.D. Protocol are behavior modification prerequisites, not governance
- **AGENTS.md being replaced** — intentions table + profile soul take over directive role
- **LXC, not Docker** — permanent workshop on Proxmox, not disposable Docker container

## The LXC Specification

| Attribute | Value |
|-----------|-------|
| Host | wander (Proxmox PVE 9.1.6, 192.168.1.200) |
| OS | Ubuntu 24.04 |
| Disk | 80GB |
| RAM | 8GB |
| CPU | 4 cores |
| CIS repo | Mounted RO from host at /mnt/projects/cis |
| Snapshots | Daily Proxmox snapshots + weekly DB dumps |
| Access | SSH, LAN/VPN only |
| Firewall | Pipeline ports LAN-only |

## What Runs Inside

### Pipeline Profiles (6 profiles, 6 roles)

| Port | Profile | Role | Model | Soul Document |
|------|---------|------|-------|---------------|
| 8643 | cis-reviewer-1 | Reviewer | Qwen 3.7 Max (OpenRouter) | Anti-assumption, adversarial posture |
| 8644 | cis-brainstorm | Brainstorm | DeepSeek V4 Pro (bulk) | Lateral thinking, challenge assumptions |
| 8645 | cis-drafter | Drafter | DeepSeek V4 Pro (bulk) | Anti-assumption, reality verification, propose less |
| 8646 | cis-implementer | Implementer | DeepSeek V4 (bulk) | Non-destructive workflow, primacy of intent |
| 8647 | cis-reviewer-2 | Reviewer | GLM-5.2 (OpenRouter) | Factual accuracy, completeness |
| 8648 | cis-verifier | Verifier | GLM-5.2 (OpenRouter) | Reality over documentation, G.O.D. inventory |

### Knowledge Infrastructure

| Component | What It Contains |
|-----------|-----------------|
| Spine (SQLite) | Intentions table, workflow_runs, deliberation_rounds, observations |
| FTS5 | 287K messages across 19 sources — full-text search |
| ChromaDB | 9.3GB semantic search across all documents |
| Drive files | 11,775 files from Google Drive — source material |
| Trajectory store | Session transcripts structured as state-conditioned action-observation sequences |

### Enforcement Architecture

Three walls, adapted from the proven Docker POC to LXC:

| Wall | Mechanism | What It Prevents |
|------|-----------|-----------------|
| Wall 1: Kernel | LXC RO bind mounts | Agent cannot write to /mnt/projects/cis or /opt/cis-control |
| Wall 2: Managed config | /etc/hermes/config.yaml root-owned, worker reads only | Agent cannot change model, disable plugins, alter context length |
| Wall 3: Policy hook | mwl-proof plugin (pre_tool_call) | Agent cannot call disallowed tools, write outside workspace |
| Loop-breaker | tool_guardrails.py _success_repeat_counts | Agent cannot loop on successful identical tool calls |

### Soul Documents (Loaded at Session Start)

Every profile loads at startup:
- **Ten Commandments** (full text from `_002_THE_AI_TEN_COMMANDMENTS.md`)
- **G.O.D. Protocol** (full text from `_003_THE_G.O.D._PROTOCOL_RUNTIME.md`)
- **G.O.D. 12 Steps of Machine Redemption** — the behavior modification prerequisite

Plus role-specific overlays:
- Drafter: "Your bias is toward over-production. Admit it. Propose less."
- Reviewer: "Your bias is toward consensus. Admit it. Find what's wrong."
- Implementer: "Your bias is toward shortcuts. Admit it. Build deliberately."
- Verifier: "Your bias is toward acceptance. Admit it. Demand evidence."
- Brainstorm: "Your bias is toward the familiar. Admit it. Explore further."

## Build Sequence

The pipeline team on the hosted profiles builds the LXC. Each phase gates on reviewer consensus and Eric sign-off.

### Phase 1: LXC Creation & Base System

**Implementer** provisions the LXC on wander, installs Ubuntu 24.04, configures networking, SSH, and firewall. Mounts required directories from host.

**Verifier** checks: LXC boots, SSH accessible, firewall rules active, mounts present.

**Gates on:** Both reviewers confirm base system is ready for Hermes installation.

### Phase 2: Hermes Installation & Profile Creation

**Implementer** installs Hermes, creates 6 profiles with `hermes profile create`, configures each with the model and port assignments above. Installs managed config at `/etc/hermes/`. Installs mwl-proof plugin. Sets up systemd services.

**Verifier** checks: each profile starts, `hermes doctor` shows managed config, `hermes plugins list` shows mwl-proof, all 6 ports respond to health checks.

**Gates on:** Both reviewers confirm profiles are correctly configured with correct model assignments.

### Phase 3: Enforcement Wall Verification

**Implementer** tests all three walls:
- Attempt write to RO mount (must fail with "Read-only file system")
- Attempt to disable plugin (must fail with "Permission denied")
- Attempt to edit managed config (must fail with "Permission denied")
- Verify loop-breaker activates after 9 identical successful tool calls

**Verifier** captures evidence for each test, produces proof file.

**Gates on:** Both reviewers confirm all walls hold. Evidence file published.

### Phase 4: Knowledge Infrastructure

**Implementer** copies spine database, FTS5 index, ChromaDB, and Drive files into LXC. Seeds intentions table with confirmed intentions. Sets up trajectory store from session transcripts.

**Verifier** checks: intentions table queryable, FTS5 search returns results, ChromaDB search returns results, session transcripts accessible.

**Gates on:** Both reviewers confirm knowledge infrastructure is operational.

### Phase 5: Profile Soul Deployment

**Implementer** creates Hermes skills for each profile containing soul documents + role overlay. Wires skills to load at session start via profile config.

**Verifier** checks: starting a session on each profile loads the correct soul document and role overlay.

**Gates on:** Both reviewers confirm soul documents are loaded correctly and role overlays are appropriate.

### Phase 6: Pipeline Wiring & End-to-End Test

**Implementer** wires adapter API, connects profiles into pipeline flow: Brainstorm → Drafter → Reviewers → Implementer → Verifier. Configures gate notifications (Telegram).

**Verifier** runs a test intention through the full pipeline and captures every step. Confirms outputs reach Eric via Telegram gates.

**Gates on:** Both reviewers confirm pipeline functions end-to-end. Eric confirms gates work on Telegram.

## Docker-to-LXC Translation — What Changes, What Stays

The enforcement architecture was proven in Docker POC. LXC implements the same walls with different mechanism. No wall degrades.

### Wall 1: Kernel RO Mounts

| Aspect | Docker | LXC |
|--------|--------|-----|
| Syntax | `docker run -v /host:/container:ro` | Proxmox config: `mp0: /host/path,mp=/container/path,ro=1` |
| Enforcement | Kernel-level, identical | Kernel-level, identical |
| Effect | write() returns EROFS | write() returns EROFS |

Mounts needed:
```
mp0: /mnt/projects/cis,mp=/mnt/projects/cis,ro=1
mp1: /opt/cis-control,mp=/opt/cis-control,ro=1
mp2: /mnt/cache/catalog,mp=/workspace,rw=1
```

### Wall 2: Managed Config

| Aspect | Docker | LXC |
|--------|--------|-----|
| Delivery | COPY in Dockerfile | Mount from Proxmox host or provision during build |
| Ownership | root:root, 644 | root:root, 644 |
| Location | /etc/hermes/config.yaml | /etc/hermes/config.yaml |
| Effect | Worker cannot write | Worker cannot write |

LXC runs systemd. Managed config is placed during LXC provisioning (Ansible, shell script, or Proxmox hook). Same effect: root-owned file, worker reads only.

### Wall 3: mwl-proof Plugin

| Aspect | Docker | LXC |
|--------|--------|-----|
| Delivery | COPY in Dockerfile | Provision during build to /opt/cis-control/plugins/ |
| Ownership | root:root, 644 | root:root, 644 |
| Loaded via | Hermes plugins.enabled in managed config | Same |
| Effect | Worker cannot rename/delete | Worker cannot rename/delete |

### Loop-breaker

Same code (`tool_guardrails.py`), same behavior (`_success_repeat_counts`). Hermes version must include it — verify during Phase 2.

### Networking

| Aspect | Docker | LXC |
|--------|--------|-----|
| Host access | `--add-host=host.docker.internal:host-gateway` | Proxmox bridge assigns LXC its own LAN IP |
| Qwen reachability | http://host.docker.internal:8002 | http://192.168.1.200:8002 (Proxmox host IP) |
| LAN model access | All models on LAN accessible | Same — LXC is on LAN |

No `host.docker.internal` magic DNS. Use direct IPs. This is simpler and more reliable.

### Systemd (LXC Advantage)

Docker cannot run systemd without privileged mode hacks. LXC runs systemd natively. Hermes gateway services become standard systemd units:

```
/etc/systemd/system/cis-drafter.service
/etc/systemd/system/cis-reviewer-1.service
/etc/systemd/system/cis-reviewer-2.service
/etc/systemd/system/cis-implementer.service
/etc/systemd/system/cis-verifier.service
/etc/systemd/system/cis-brainstorm.service
```

Each unit sets `HERMES_HOME` and `EnvironmentFile`. `systemctl enable` makes them survive reboots. This is cleaner than Docker's `sleep infinity` + `docker exec` pattern.

### Persistent State

| Aspect | Docker | LXC |
|--------|--------|-----|
| Hermes state | Docker volume `cis-worker-state` | Native LXC filesystem |
| Snapshots | Manual docker commit | Proxmox built-in snapshots (daily, automated) |
| Backups | Manual export | Proxmox backup server integration |

LXC provides persistent storage by default — no volumes to manage. Proxmox snapshots are faster and more reliable than Docker commits.

## 16 Failure Modes — How the LXC Prevents Each

The 16 failure modes (from CIS_16_FAILURE_MODES.md) and how the contained environment addresses them:

| # | Failure Mode | Prevention |
|---|-------------|------------|
| 1 | Hallucinated facts | Verifier evidence check — every claim must have a reproducable command |
| 2 | Rubber-stamp review | Two independent reviewers (Qwen + GLM), different training data |
| 3 | False consensus | Reviewers cannot see each other's output until reconciliation |
| 4 | Single-model blind spots | Three training distributions (DeepSeek, Alibaba/Qwen, Z.ai/GLM) |
| 5 | Drafter = Implementer | Enforced by port routing (8645 ≠ 8646) |
| 6 | Context window overflow | Managed config pins context_length = 32768 |
| 7 | Tool abuse / destructive commands | mwl-proof plugin pre_tool_call hook |
| 8 | File system contamination | LXC RO mounts on /mnt/projects/cis and /opt/cis-control |
| 9 | Loop / repeated tool calls | Loop-breaker: _success_repeat_counts, block at 9 |
| 10 | Model / provider switching | Managed config pins model and provider |
| 11 | Plugin disable / reconfiguration | Managed config pins plugins.enabled, root-owned plugin directory |
| 12 | Intent misinterpretation | Intentions table + Brainstorm lateral exploration before Drafter narrows |
| 13 | Stale context / memory loss | Spine + FTS5 + ChromaDB persist across sessions |
| 14 | Unauthorized external access | Firewall: pipeline ports LAN-only |
| 15 | Cost overrun | Adapter API budget tracking, $0.50/run hard stop |
| 16 | Human operator as middleware | Pipeline automates Drafter → Review → Build → Verify flow |

## Questions for Reviewers

1. Is the LXC specification adequate for the workload (80GB, 8GB RAM, 4 cores)?
2. Are the enforcement walls sufficient given the Docker POC was already proven — does LXC change anything?
3. Should Phase 5 (Soul Deployment) happen earlier in the build sequence?
4. Are all 16 failure modes properly addressed or are there gaps?
5. What's missing from the build plan that would block implementation?
