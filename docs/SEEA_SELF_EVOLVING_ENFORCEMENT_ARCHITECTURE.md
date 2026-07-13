# Self-Evolving Enforcement Architecture (SEEA)

**Status:** SPEC — awaiting pipeline processing
**Author:** Eric (intent) + GLM Verifier (draft)
**Date:** 2026-07-13
**References:** ADR-SEED-015, ADR-SEED-016, AGENTS.md §10 (Verification Hardening Rule)

---

## 1. Problem Statement

The current enforcement audit (14 static checks) was built reactively — I mounted the
docker socket into the container, Eric caught it, and the audit was created to prevent
recurrence. This pattern is backwards. The system should catch its own failures and
evolve its own defenses, not wait for Eric to spot containment breaks.

The enforcement layer needs to become self-evolving: every breach attempt, whether caught
by a gate or by a human, should produce a new deterministic check that prevents that class
of failure from recurring. The audit checklist grows from real attacks, not from
a developer guessing what to check.

## 2. Dual Hermes Installation Strategy

Two distinct Hermes installations serve different purposes:

### Host Hermes (The Root Coder)
- **Location:** /home/eric/.hermes-* (host-side systemd services on 864x)
- **Role:** Development, infrastructure work, building and modifying the container itself
- **Containment:** NONE — runs as eric, has full system access, docker group, sudo
- **Trust model:** Trusted for development work. NOT trusted to run pipeline agents.
  Cannot verify its own output (per ADR-SEED-002).
- **What it does:**
  - Writes and modifies code in /mnt/projects/cis
  - Builds Docker images, manages containers
  - Rebuilds and restarts the container
  - Hosts the fallback gateway services
  - Does NOT run inside the enforcement model
- **What it must NOT do:**
  - Run pipeline agent roles (Brain, Drafter, Reviewer, Implementer, Verifier)
  - Make claims about its own compliance
  - Be trusted as a verification authority

### Container Hermes (The Pipeline)
- **Location:** /home/worker/.hermes-* inside cis-pipeline container
- **Role:** Multi-agent pipeline execution (Brain → Draft → Review → Menter → Verify)
- **Containment:** FULL — non-root worker, no docker socket, sealed enforcement surfaces,
  managed config, hook consent baked into image env
- **Trust model:** Constrained. Cannot author its own contract. Enforcement is external
  (root-owned files, kernel-level RO mounts, policy hooks). Per ADR-SEED-015:
  three-layer process isolation.
- **What it does:**
  - Runs pipeline agent roles in isolation
  - Processes intents through the review chain
  - Produces verified work products backed by deterministic evidence
- **What it must NOT do:**
  - Access the host filesystem outside mounted volumes
  - Modify its own enforcement configuration
  - Access docker, sudo, or any privilege escalation path
  - Break out of the container

### Boundary Between Them

The boundary is unidirectional: Host → Container.

Host can:
- Read container logs (docker logs, /tmp/cis-logs/)
- Restart the container (sg docker -c "docker restart cis-pipeline")
- Modify code in /mnt/projects/cis (appears at /workspace/cis in container)
- Rebuild the image and recreate the container

Host cannot:
- Trust container agent output without deterministic verification (ADR-SEED-002)
- Inject unverified commands into running pipeline agents
- Override enforcement from inside the container

Container cannot:
- Reach back to the host
- Modify its own containment surfaces
- Access docker, sudo, or host processes

## 3. Self-Evolving Enforcement Audit

### 3.1 Current State

14 static checks hardcoded in container_app.py at /api/relay/system/security.
Checks are:
1. Worker is non-root
2. No docker socket mounted
3. Worker not in docker group
4. Managed config sealed (root-owned, worker RO)
5-10. Plugin sealed for all 6 profiles
11. Gate scripts sealed (root-owned, worker RO)
12. Hook consent baked (HERMES_ACCEPT_HOOKS=1)
13. Managed scope baked (HERMES_MANAGED_DIR=/etc/hermes)
14. Entrypoint worker cannot modify

### 3.2 Target Architecture

```
┌─────────────────────────────────────────────────────┐
│           enforcement_audit_registry.json           │
│  (SQLite table in spine, or JSON file in repo)      │
│                                                     │
│  Each entry:                                        │
│  {                                                  │
│    "id": "CHK-001",                                 │
│    "name": "Worker is non-root",                    │
│    "category": "identity",                          │
│    "check_type": "uid_not_zero",                    │
│    "check_fn": "os.getuid() != 0",                 │
│    "added_date": "2026-07-13",                      │
│    "added_by": "initial_seed",                      │
│    "trigger": "ADR-SEED-015 baseline requirement",   │
│    "evidence_template": "UID={uid} ({username})",   │
│    "severity": "critical",                          │
│    "last_failed": null,                             │
│    "fail_count": 0                                  │
│  }                                                  │
│                                                     │
│  New entries added when:                            │
│  1. A gate catches a new violation type            │
│  2. A human (Eric) reports a containment concern    │
│  3. A breach attempt is logged in any pipeline run  │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│        Enforcement Audit Engine (Python)             │
│  - Reads registry                                  │
│  - Executes each check_type against live state      │
│  - Collects raw evidence (uid, mode, writable)     │
│  - Returns structured JSON                         │
│  - Logs failures to spine for pattern analysis      │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│        System Dashboard (React)                      │
│  - Shows CONTAINMENT INTACT/BREACHED badge          │
│  - Lists all checks with PASS/FAIL + evidence      │
│  - Highlights new checks (added since last view)    │
│  - Shows failure history for recurring issues       │
└─────────────────────────────────────────────────────┘
```

### 3.3 Check Categories

- **identity** — Who is the worker? (UID, groups, non-root)
- **isolation** — What can the worker reach? (docker socket, host network, host PID)
- **sealing** — What can the worker modify? (config, plugins, gates, entrypoint)
- **consent** — What enforcement is active? (hooks, managed scope, guardrails)
- **boundary** — What mounts exist? (read-only enforcement surfaces)
- **gate_runtime** — Are gates actually executing? (gate runner active, hooks firing)
- **provenance** — Is the audit itself trustworthy? (audit code is root-owned)

### 3.4 Evolution Triggers

The audit registry grows when:

1. **Gate violation logging:** When container_gate_runner.py blocks an action,
   it logs the violation type. A new check is created to detect the precondition
   that allowed the attempt.

2. **Human escalation:** When Eric reports a containment concern (like the docker
   socket incident), a new check is added to the registry with `added_by: "human_escalation"`
   and the trigger description preserved.

3. **Breach attempt analysis:** When a pipeline run logs an out-of-bounds action,
   the post-run analysis identifies what enforcement surface was targeted and
   creates a check for that surface.

4. **Periodic review:** The Verify role in the pipeline can propose new checks
   based on reviewing the current registry and identifying gaps.

### 3.5 Registry Storage

The audit registry should live in the SQLite spine, not in code. This allows:
- The pipeline to add checks without code changes
- A history of when checks were added and why
- Failure tracking for pattern analysis
- The Verify role to review and propose additions

New spine table:
```sql
CREATE TABLE enforcement_checks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    check_type TEXT NOT NULL,
    check_params TEXT,  -- JSON: parameters for the check function
    added_date TEXT NOT NULL,
    added_by TEXT NOT NULL,  -- "initial_seed", "human_escalation", "gate_violation", "verify_review"
    trigger_desc TEXT,
    severity TEXT DEFAULT 'high',  -- critical, high, medium, low
    last_checked TEXT,
    last_failed TEXT,
    fail_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1
);
```

### 3.6 Check Execution

The audit engine is a dispatcher: it reads `check_type` from the registry and
calls the corresponding Python function. Each function returns `(passed: bool, evidence: str)`.

Built-in check types (extensible):
- `uid_not_zero` — worker is not root
- `file_not_exists` — path does not exist (e.g., docker socket)
- `worker_not_in_group` — worker is not in named group
- `file_root_owned` — file is owned by UID 0
- `file_not_writable` — worker cannot write to path
- `env_equals` — environment variable matches expected value
- `env_is_set` — environment variable is set
- `dir_not_writable` — directory is not writable by worker
- `no_suid_binaries` — no SUID binaries in enforcement paths
- `mount_is_readonly` — mount point is read-only (check /proc/mounts)

New check types can be added by the Host Hermes (root coder) since they require
code changes. The registry entries (what to check) can be added by the pipeline.

## 4. Host-Container Build Strategy

### 4.1 Host Hermes (Root Coder) Responsibilities

The host Hermes is the development environment. It:
- Builds and maintains the container image
- Writes all code in /mnt/projects/cis
- Manages Docker infrastructure
- Has full system access — intentionally unruly
- Does NOT run pipeline agents
- Does NOT make enforcement claims about itself

Build cycle:
1. Host Hermes writes/modifies code
2. Host Hermes rebuilds image: `sg docker -c "docker build -t cis-hermes:pipeline -f ..."`
3. Host Hermes recreates container: `run_container.sh stop && run_container.sh -d`
4. Host Hermes verifies enforcement audit passes: `curl localhost:5000/api/relay/system/security`
5. If audit fails, host Hermes fixes the issue before proceeding

### 4.2 Container Hermes (Pipeline) Responsibilities

The container Hermes runs the multi-agent pipeline. It:
- Processes intents through Brain → Draft → Review → Menter → Verify
- Is constrained by sealed enforcement surfaces
- Cannot modify its own containment
- Produces verified work products with deterministic evidence
- Can propose new enforcement checks (adds to registry)
- Cannot approve its own checks (host must review)

### 4.3 The Split

The split is clean:
- **Host does the coding.** All filesystem changes, Docker operations, infrastructure.
- **Container does the verification.** All pipeline roles, review, gate execution.

The host is trusted to write code because Eric trusts the host Hermes
(it's him, working through the agent). The container is NOT trusted
to write code — it's constrained to review and verify.

This means:
- New enforcement checks are *proposed* by the container (pipeline)
- New enforcement check *code* is *written* by the host (root coder)
- The registry entries are *added* by the container
- The check functions that execute them are *written and compiled* by the host

## 5. Implementation Phasing

### Phase 1: Externalize the Registry (NOW)
- Move the 14 hardcoded checks from container_app.py into the SQLite spine
- Audit engine reads from spine and dispatches to check functions
- No behavior change — same 14 checks, just data-driven

### Phase 2: Gate Violation → Check Creation
- When container_gate_runner.py blocks an action, it logs to a new spine table
- Post-run analysis proposes a new enforcement_check entry
- Verify role reviews and the entry is added to the registry
- The check function must already exist in the engine (host writes it)

### Phase 3: Human Escalation Path
- Eric reports a concern (like docker socket)
- A new check entry is created with `added_by: "human_escalation"`
- The trigger description is preserved verbatim (Eric's words)
- The check runs immediately on next audit cycle

### Phase 4: Audit Self-Review
- The Verify role periodically reviews the enforcement_checks table
- Identifies gaps (surfaces that have no checks)
- Proposes new checks to close gaps
- Host Hermes implements the check functions

### Phase 5: Failure Pattern Analysis
- Track which checks fail and how often
- Identify systematic issues (e.g., container recreation keeps breaking seals)
- Alert Eric when a check that previously passed starts failing
- The system learns its own failure modes

## 6. What This Is NOT

- This is NOT the container auditing itself. The audit code runs inside the container
  but checks external surfaces (root-owned files, env vars, mount state). The worker
  cannot modify the audit code (it's in the repo, which is writable, but changes only
  take effect after container restart — and the host controls restarts).

- This is NOT trust-based. Every check produces raw evidence. PASS means the
  filesystem state matches the expected state. No agent opinion is involved.

- This is NOT static. The registry grows. New attacks produce new checks.
  The defense surface evolves with the threat surface.

- This is NOT a replacement for the gate runner. The gates prevent actions in
  real-time. The audit proves the gates are in a position to function
  (sealed, root-owned, worker can't disable them). They're complementary.
