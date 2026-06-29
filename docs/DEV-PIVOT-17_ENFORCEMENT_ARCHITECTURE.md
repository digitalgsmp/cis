     1|# DEV-PIVOT-17: Enforcement Architecture — Process Isolation
     2|
     3|**Date:** 2026-06-19
     4|**Status:** DECIDED (architecture) / NEXT: draft implementation spec for review
     5|**Supersedes:** DEV-PIVOT-02/03 hook-token approach (deadlocked, retired)
     6|
     7|## The Core Realization
     8|
     9|The 16 failure modes are LLM *behavior* failures, not future CIS app features.
    10|The goal is a runtime obligation system: the model cannot answer from training
    11|data when the task needs current/external truth, and cannot act outside the
    12|declared intent of the task. Prompt/SOUL/skills/profile instructions are
    13|insufficient — the constrained agent can ignore, reinterpret, or mutate them.
    14|Enforcement must be deterministic and live OUTSIDE the constrained agent.
    15|
    16|The inventory/catalog task is the proving ground: if Hermes can't be constrained
    17|on a read-only inventory, it can't be constrained on a UI build or refactor.
    18|Prove the primitive on the smallest task; it generalizes.
    19|
    20|## The Architecture (settled)
    21|
    22|Three-layer process isolation. CIS is the control plane OVER Hermes. Hermes is a
    23|replaceable worker backend, not the authority.
    24|
    25|1. **CIS control plane** — owns task contracts, policy checker, task templates,
    26|   frozen contracts, gates, review state, release decisions. Lives at
    27|   `/opt/cis-control/`, root-owned, mounted READ-ONLY into the worker container.
    28|   The constrained agent can read but never write it.
    29|
    30|2. **Hermes worker** — executes inside a Docker container. Reads context +
    31|   contract, uses tools, produces output. Cannot alter its own permissions.
    32|   Cannot launch Docker (eric not in docker group; control plane launches
    33|   containers).
    34|
    35|3. **Workspace** — `/mnt/cache/catalog/<run_id>/` is the ONLY writable mount.
    36|   Source roots (/mnt/archive, /mnt/projects/cis, /mnt/projects/swa) mount
    37|   read-only.
    38|
    39|Two enforcement walls, not one:
    40|- **Docker/kernel** — physically refuses writes to source/control paths.
    41|- **CIS policy hook** (pre_tool_call) — blocks wrong tools, wrong paths, missing
    42|  evidence, missing review. The hook is the policy brain; Docker is the
    43|  filesystem wall.
    44|
    45|## Trust Root (load-bearing)
    46|
    47|- The constrained agent CANNOT author or edit its own contract.
    48|- Valid contract authors: Claude API proposal → deterministic local compiler
    49|  validates against a fixed template → freezes contract JSON + hash. Or Eric
    50|  directly. Or a prior approved DB row.
    51|- The compiler REJECTS any proposal that widens paths/tools beyond the template.
    52|  Claude fills descriptive fields only (labels, intent summary, risk notes).
    53|  Paths, tools, deny-list are hardcoded in the template — Claude cannot expand
    54|  them.
    55|- Claude API is the adversarial reviewer of the candidate output. The hook does
    56|  NOT judge answer quality; the reviewer does. Reviewer is never the constrained
    57|  agent. The hook alone does not solve the 16 — the reviewer is required for
    58|  quality.
    59|- Override plane (`.GATE_DISABLED`) checked FIRST by the hook, testable from
    60|  bare shell, built and tested BEFORE the hook is trusted. This prevents the
    61|  v2.0 deadlock (a gate openable only from inside the locked room).
    62|
    63|## Verified Premise
    64|
    65|Docker 29.6.0 installed. Container with `/mnt/projects/cis` mounted read-only
    66|refused a write: "Read-only file system", exit 1. No breach file created on host.
    67|Kernel containment confirmed. eric not in docker group — Docker launch requires
    68|root/control-plane orchestration (this is a security feature: worker cannot
    69|remount to escape).
    70|
    71|## SOUL/Skills Split (going forward)
    72|
    73|- **Procedural knowledge** (what tool to run, file paths, project structure) →
    74|  stays in agent context / skills. Agent may patch these for procedural learning.
    75|- **Enforcement rules** (evidence required, write boundaries, completion claims)
    76|  → move to the external policy layer. Agent may NOT patch enforcement policy,
    77|  hook code, task templates, or active contracts.
    78|
    79|## Next Action
    80|
    81|Draft `docs/TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md` as a PROPOSAL ONLY.
    82|Do not implement. Do not create /opt/cis-control. Do not modify hooks, Docker
    83|settings, DB schema, or live enforcement files. Draft routes through review
    84|(Claude audit + ChatGPT audit + Eric approval) before any file lands in
    85|/opt/cis-control.
    86|
    87|## Parked Items
    88|
    89|- Doc-sync failure: no session-to-spine write path; project_state only tracks
    90|  build_phase; DEV-PIVOT files have no generator. See
    91|  DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md. Design task: make DB the source of truth,
    92|  generate HCP + DEV-PIVOT advisor packets from spine. Front-of-queue next
    93|  session.
    94|- gate_runner increment hardening (((X++)) || true) — cosmetic.
    95|- gate_7 exit-contract honesty (skip counts as pass) — minor.
    96|- Dead API key in git history (f0a78f...) — dead, no action.
    97|- DEV-PIVOT-02 row-count drift — wrong in one historical doc.
    98|
    99|## Closed This Session
   100|
   101|- Spine-gate audit complete, findings verified by raw evidence.
   102|- gate_runner.sh honest banner (PASSED/SKIPPED/FAILED counts) — fixed, verified.
   103|- Hardcoded key swapped to env var (CIS_R1_API_KEY in gitignored runtime.env) —
   104|  fixed, verified.
   105|- Dead spine.db (0 bytes) confirmed a decoy, not a live fault — no action needed.
   106|
   107|---
   108|
   109|## Session Update — 2026-06-27
   110|
   111|This document's topic (enforcement architecture — process isolation) was not directly
   112|advanced this session. The major work completed: knowledge base ingestion (287K messages,
   113|FTS5 + ChromaDB), abstraction layer (5 endpoints including human-readable status),
   114|intent alignment pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10**
   115|for the full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
   116|Commit: 9c921e2. All 17 DEV-PIVOT files carry session footers. HCP regenerated at HEAD.
   117|