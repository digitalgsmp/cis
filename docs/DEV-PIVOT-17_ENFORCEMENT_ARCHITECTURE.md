# DEV-PIVOT-17: Enforcement Architecture — Process Isolation

**Date:** 2026-06-19
**Status:** DECIDED (architecture) / NEXT: draft implementation spec for review
**Supersedes:** DEV-PIVOT-02/03 hook-token approach (deadlocked, retired)

## The Core Realization

The 16 failure modes are LLM *behavior* failures, not future CIS app features.
The goal is a runtime obligation system: the model cannot answer from training
data when the task needs current/external truth, and cannot act outside the
declared intent of the task. Prompt/SOUL/skills/profile instructions are
insufficient — the constrained agent can ignore, reinterpret, or mutate them.
Enforcement must be deterministic and live OUTSIDE the constrained agent.

The inventory/catalog task is the proving ground: if Hermes can't be constrained
on a read-only inventory, it can't be constrained on a UI build or refactor.
Prove the primitive on the smallest task; it generalizes.

## The Architecture (settled)

Three-layer process isolation. CIS is the control plane OVER Hermes. Hermes is a
replaceable worker backend, not the authority.

1. **CIS control plane** — owns task contracts, policy checker, task templates,
   frozen contracts, gates, review state, release decisions. Lives at
   `/opt/cis-control/`, root-owned, mounted READ-ONLY into the worker container.
   The constrained agent can read but never write it.

2. **Hermes worker** — executes inside a Docker container. Reads context +
   contract, uses tools, produces output. Cannot alter its own permissions.
   Cannot launch Docker (eric not in docker group; control plane launches
   containers).

3. **Workspace** — `/mnt/cache/catalog/<run_id>/` is the ONLY writable mount.
   Source roots (/mnt/archive, /mnt/projects/cis, /mnt/projects/swa) mount
   read-only.

Two enforcement walls, not one:
- **Docker/kernel** — physically refuses writes to source/control paths.
- **CIS policy hook** (pre_tool_call) — blocks wrong tools, wrong paths, missing
  evidence, missing review. The hook is the policy brain; Docker is the
  filesystem wall.

## Trust Root (load-bearing)

- The constrained agent CANNOT author or edit its own contract.
- Valid contract authors: Claude API proposal → deterministic local compiler
  validates against a fixed template → freezes contract JSON + hash. Or Eric
  directly. Or a prior approved DB row.
- The compiler REJECTS any proposal that widens paths/tools beyond the template.
  Claude fills descriptive fields only (labels, intent summary, risk notes).
  Paths, tools, deny-list are hardcoded in the template — Claude cannot expand
  them.
- Claude API is the adversarial reviewer of the candidate output. The hook does
  NOT judge answer quality; the reviewer does. Reviewer is never the constrained
  agent. The hook alone does not solve the 16 — the reviewer is required for
  quality.
- Override plane (`.GATE_DISABLED`) checked FIRST by the hook, testable from
  bare shell, built and tested BEFORE the hook is trusted. This prevents the
  v2.0 deadlock (a gate openable only from inside the locked room).

## Verified Premise

Docker 29.6.0 installed. Container with `/mnt/projects/cis` mounted read-only
refused a write: "Read-only file system", exit 1. No breach file created on host.
Kernel containment confirmed. eric not in docker group — Docker launch requires
root/control-plane orchestration (this is a security feature: worker cannot
remount to escape).

## SOUL/Skills Split (going forward)

- **Procedural knowledge** (what tool to run, file paths, project structure) →
  stays in agent context / skills. Agent may patch these for procedural learning.
- **Enforcement rules** (evidence required, write boundaries, completion claims)
  → move to the external policy layer. Agent may NOT patch enforcement policy,
  hook code, task templates, or active contracts.

## Next Action

Draft `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` as a PROPOSAL ONLY.
Do not implement. Do not create /opt/cis-control. Do not modify hooks, Docker
settings, DB schema, or live enforcement files. Draft routes through review
(Claude audit + ChatGPT audit + Eric approval) before any file lands in
/opt/cis-control.

## Parked Items

- Doc-sync failure: no session-to-spine write path; project_state only tracks
  build_phase; DEV-PIVOT files have no generator. See
  DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md. Design task: make DB the source of truth,
  generate HCP + DEV-PIVOT advisor packets from spine. Front-of-queue next
  session.
- gate_runner increment hardening (((X++)) || true) — cosmetic.
- gate_7 exit-contract honesty (skip counts as pass) — minor.
- Dead API key in git history (f0a78f...) — dead, no action.
- DEV-PIVOT-02 row-count drift — wrong in one historical doc.

## Closed This Session

- Spine-gate audit complete, findings verified by raw evidence.
- gate_runner.sh honest banner (PASSED/SKIPPED/FAILED counts) — fixed, verified.
- Hardcoded key swapped to env var (CIS_R1_API_KEY in gitignored runtime.env) —
  fixed, verified.
- Dead spine.db (0 bytes) confirmed a decoy, not a live fault — no action needed.
