# CIS — Phase PD.5 Operational Governance Layer Contract
## Version: 1.1 — READY FOR L1 VERIFICATION
## Status: L3 PASS (minor corrections applied) — PENDING L1/L2
## Authority: Loop 4 correction — real execution revealed missing substrate layer
## L3 Auditor: ChatGPT architectural review — PASS WITH MINOR CORRECTIONS
## Canonical path: /mnt/projects/cis/docs/contracts/CIS_PD5_Operational_Governance_Contract_v1.md

---

## 1. Constitutional Basis

The CIS Canonical Build Sequence (Loop 4, Living Document Rule) explicitly permits roadmap
versioning when real execution reveals structural gaps. This contract records one such
correction.

Phase PD.5 is not a replacement phase. It is a missing substrate layer discovered through
fifteen sessions of real execution. It is inserted between Phase PD and Phase 0 in the
canonical dependency graph:

```
Phase PD → Phase PD.5 → Phase 0 → Phase 1 → ...
```

The canonical roadmap destination is unchanged:
intelligence extraction → knowledge formation → WIAS workflow → agents → application layer.

PD.5 exists so that destination can be reached without the build environment collapsing
under orchestration complexity, runtime entropy, or operator overload.

---

## 2. Why PD.5 Exists

The original roadmap correctly identified dependency order and constitutional constraints.
What it underestimated was the size of the hidden substrate required to safely execute
the roadmap itself.

Real execution revealed recurring failure patterns:

- Terminal commands becoming normalized workflow
- Desktop launcher spawning duplicate Flask and vLLM processes
- Runtime service state becoming invisible to the operator
- Failed processes leaving silent zombie instances
- Dashboard buttons triggering unmanaged direct script execution
- Frontend monolith causing fragile, expensive breakage
- Session boundaries creating context drift and reconstruction labor
- Files existing in multiple locations without authority designation
- Architectural decisions made in conversation before capture in DB
- Verification requiring too much manual operator orchestration
- Operator acting as scheduler, retry manager, and process tracker

These are not application feature gaps. They are build-environment stabilization failures.

The missing layer is named: Operator and Runtime Governance Infrastructure.

---

## 3. Scope Definition

### 3.1 What PD.5 Covers

PD.5 governs six infrastructure areas:

1. Runtime Service Ownership
2. Execution Queue Ownership (ADR-045)
3. Filesystem Governance (ADR-046)
4. Verification Governance
5. Operator Abstraction
6. Operator Surface Audit

Each area is defined in Section 6.

### 3.2 What PD.5 Does NOT Cover

PD.5 explicitly excludes:

- Frontend redesign or visual overhaul
- New intelligence extraction features
- Retrieval system upgrades
- Agent expansion of any kind
- Swarm or multi-agent orchestration
- Replacing Flask as the application server
- Replacing SQLite as the memory layer
- Production deployment architecture
- Full application-layer feature work
- Any schema work beyond execution_jobs and execution state machine
- Automation beyond execution governance boundaries

Violation of this boundary restarts the scope creep cycle PD.5 was built to prevent.

---

## 4. Governing Principles

### 4.1 Single Operator Action

A non-coder operator must be able to:

- Click one desktop launcher
- Observe runtime state in the dashboard
- Start required runtime services from the dashboard
- Run Verify Contract from the dashboard
- Observe job state and verification results
- Close a session from the dashboard

without terminal interaction. Terminal use during PD.5 is classified as:

- unavoidable one-time setup
- temporary diagnostic
- operator abstraction gap requiring a dashboard fix
- missing queue or service ownership requiring implementation

Any terminal step that recurs more than once becomes a dashboard or service ownership
implementation target.

### 4.2 No Unmanaged Execution

Once ADR-045 is active, no operator surface may directly spawn unmanaged runtime execution.

All runtime execution flows through declared ownership paths:
Operator button → Execution Queue → Single Worker → Runtime Scripts → Verification → Registry

Direct script invocation from API routes is a violation of this principle after ADR-045 locks.

### 4.3 Authoritative State Over Optimistic UI

The dashboard must never display:
- running
- verified
- complete
- healthy

unless authoritative backend confirmation exists. UI state reflects system reality.
Optimistic display is a governance failure.

### 4.4 Operational Truth Surfaces

The operator must be able to determine actual system state without inspecting terminal
processes directly. The following must be visible from the dashboard:

- Flask service status (running / stopped, PID, port)
- vLLM Slot 1 status (running / stopped, port, model loaded)
- Active execution jobs (state, job type, elapsed time)
- Last verification result (L1/L2 verdict, timestamp)
- Open CIS Live sessions (count, topic)
- Next required action (derived from system state, not human memory)

### 4.5 Runtime Service Ownership vs Execution Ownership

These are distinct layers and must not be conflated.

**Runtime Service Ownership** governs:
Flask lifecycle, vLLM lifecycle, launcher behavior, ports, logs, uptime, service health.
A healthy Flask process does not imply healthy execution governance.

**Execution Ownership** governs:
Jobs, queue, worker authority, retries, resumability, verification execution, stale jobs,
orchestration legality.
The queue may be operational while runtime services are degraded — each layer reports
its own state independently.

### 4.6 Resumability Over Concurrency

PD.5 prioritizes resumability and recoverability over concurrency and speed.

Single queue. Single worker. Single GPU ownership path.

Concurrent execution is deferred. PD.5 assumes single-worker serialized execution.
This is aligned with hardware constraints (one RTX 4090) and the canonical roadmap's
sequential build discipline.

### 4.7 Recovery Semantics

The system must handle:

- Interrupted jobs (Flask restart while job running)
- Stale jobs (worker died without completion)
- Crash recovery (process exit without state cleanup)
- Partial verification runs (L1 passed, L2 crashed mid-run)

Recovery behavior is defined by the execution state machine. No job disappears silently.

### 4.8 Session Continuity as Infrastructure

Session continuity is infrastructure, not convenience.

All PD.5 work reduces reconstruction burden between sessions.
Handoff content, Next Required Action, verification state, and open job state must be
derivable from authoritative system sources, not human memory alone.

### 4.9 Implementation Discipline

PD.5 implementation prioritizes, in order:

1. Authority clarity
2. Deterministic behavior
3. Visibility
4. Resumability
5. Governance integrity

before convenience, expansion, or optimization.

### 4.10 Authority Hierarchy

When sources of truth conflict, this hierarchy governs:

1. Locked contracts and locked ADRs supersede conversational reasoning
2. Runtime execution state supersedes cached UI state
3. Database execution state (execution_jobs) supersedes session memory or operator assumption
4. config.py is path authority — all file path references derive from it
5. CIS_FILE_MAP.md governs filesystem authority classification
6. Dashboard surfaces are reflections of authoritative backend state, not independent authority sources

No lower authority may override a higher authority. Conflicts surface as blockers,
not silent resolutions.

### 4.11 Human Override Authority

The operator retains final authority over promotion, cancellation, approval, and session
closure decisions.

System recommendations, next-action guidance, and queue suggestions are advisory unless
explicitly locked by a governance rule in a locked contract or ADR.

The human-led constitutional principle from the canonical roadmap is preserved without
exception throughout PD.5.

### 4.12 Append-Only Log Protection

Execution logs are append-only operational records.

Logs may be superseded by a new log file or archived to a historical path.
Logs may not be silently rewritten, truncated, or modified in place.

This protects auditability across sessions and enables accurate recovery semantics.

### 4.13 Session Close Semantics

Session close is a continuity capture action, not a completion declaration.

Closing a session means:
- Open job state is captured
- Open CIS Live sessions are noted
- Unresolved verification state is recorded
- Next required action is derived from system state
- Handoff is produced

Closing a session does not mean:
- All work is complete
- All jobs succeeded
- The phase is done
- The build target is reached

The operator must not treat close as completion. The system must not imply it.

---

## 5. Execution State Machine

All execution jobs pass through this legal state graph:

```
queued
  └── claimed
        └── running
              ├── succeeded
              ├── failed
              ├── stale (heartbeat timeout)
              └── needs_human_review
queued → cancelled (operator cancel before claim)
```

State transition rules:
- A job may only move forward through the graph above
- No job may move from failed or succeeded back to queued without explicit re-enqueue
- Stale detection fires when a claimed job has no heartbeat for a defined interval
- needs_human_review is set by the worker when output is ambiguous, not by the operator

**Worker Authority Rule:**
The worker is the sole authority permitted to transition execution job states after claim.

No API route, operator button, or external script may mutate job state once a job is
claimed by the worker. State mutations from any other source after claim are a governance
violation. This rule protects execution integrity and prevents race conditions between
operator intent and worker execution.

---

## 6. PD.5 Implementation Areas

### 6.1 Runtime Service Ownership

**Authority files:**
- `/mnt/projects/cis/runtime/cis_launcher.sh` (NEW — canonical launcher)
- `cis_vllm_slot1.sh` (MODIFY — add port pre-check)
- Desktop `.desktop` launcher file (MODIFY — point to cis_launcher.sh)
- `api/operator.py` (MODIFY — add Flask status route)
- `cis_dashboard.html` (MODIFY — surface Flask status in Operator section)

**Required behavior:**

cis_launcher.sh must:
- Check if Flask is already running on port 5000 before starting
- Check if vLLM is already running on port 8001 before starting
- If service is already running, open browser only
- If service is not running, start it once, log PID and startup to known log path
- Never spawn a second instance of either service

cis_vllm_slot1.sh must:
- Check port 8001 before attempting startup
- Exit cleanly if port is bound
- Never leave a zombie EngineCore process on failure

Dashboard Operator section must show:
- Flask: UP/DOWN with port
- Slot 1: UP/DOWN with model name
- Both statuses polled from authoritative backend routes, not assumed

**Completion gate:** Clicking the desktop launcher twice produces one Flask instance
and one browser window. No terminal required.

---

### 6.2 Execution Queue Ownership — ADR-045

**Authority files:**
- `db/execution_jobs.py` (NEW — schema, enqueue, claim, complete, fail, stale detection)
- `runtime/cis_worker.py` (NEW — single-worker execution loop)
- `api/operator.py` (MODIFY — verify_contract route becomes enqueue-only)
- `db/connection.py` (MODIFY — ensure_tables includes execution_jobs)
- `cis_dashboard.html` (MODIFY — Verify Contract button shows job ID and live state)

**execution_jobs schema (minimum required fields):**

```
id               INTEGER PRIMARY KEY
job_type         TEXT NOT NULL
payload          TEXT (JSON)
status           TEXT NOT NULL DEFAULT 'queued'
enqueued_at      TEXT
claimed_at       TEXT
started_at       TEXT
completed_at     TEXT
last_heartbeat   TEXT
worker_id        TEXT
result           TEXT (JSON)
error            TEXT
log              TEXT (append-only)
retry_count      INTEGER DEFAULT 0
```

**Worker behavior:**
- Polls execution_jobs WHERE status='queued' ORDER BY enqueued_at ASC LIMIT 1
- Claims job (status='claimed', worker_id, claimed_at)
- Executes job payload
- Writes heartbeat at defined interval
- On completion: status='succeeded', result written
- On failure: status='failed', error written
- Stale detection: separate process or Flask background thread checks for
  claimed jobs with no heartbeat beyond defined timeout

**ADR-045 must be drafted and locked before implementation begins.**

**Completion gate:** Clicking Verify Contract in the dashboard enqueues a job,
returns a job ID, and the operator can observe the job moving through states
until L1/L2 results appear. No terminal required.

---

### 6.3 Filesystem Governance — ADR-046

**Authority files:**
- `CIS_FILE_MAP.md` (EXISTING — becomes ADR-046 seed document)
- `config.py` (AUDIT — all paths verified against FILE_MAP before ADR-046 locks)

**Required authority labels:**

Every file in the runtime must be classified as one of:
- ACTIVE — canonical authority, in active use
- MIRROR — copy of an ACTIVE file, not authoritative
- ARCHIVE — historical, intentionally preserved, not in active use
- LEGACY — superseded, not yet removed, no longer authoritative
- TRANSITIONAL — temporary state, must resolve to another label
- DEPRECATED — scheduled for removal

**Required governance rules:**
- `runtime/` is canonical runtime authority
- Vault is MIRROR, not source
- `config.py` is path authority — all other path references derive from it
- No file may exist in both `runtime/` root and `runtime/api/` without explicit authority designation
- Duplicate runtime copies must be labeled LEGACY or removed

**ADR-046 deferred until ADR-045 is operational.**

**Completion gate:** Every file in `/mnt/projects/cis/runtime/` has an authority label
in CIS_FILE_MAP.md. No duplicate authority exists.

---

### 6.4 Verification Governance

**Authority files:**
- `api/operator.py` (MODIFY — verify_contract enqueues; does not execute directly)
- `cis_verify_semantic.py` (MODIFY — reduce max_tokens from 1024 to 768 to resolve
  4096 context ceiling; remove temperature=0.0 parameter before any model migration)
- `cis_verify.py` (NO CHANGE — called by worker, not API route)
- `cis_dashboard.html` (MODIFY — verification results displayed from job result field)

**Verification chain authority:**
- L1 (deterministic) — owned by cis_verify.py, executed by worker
- L2 (semantic) — owned by cis_verify_semantic.py, executed by worker, gated on Slot 1 health
- L3 (external audit) — owned by ChatGPT architectural review, required for contracts,
  schemas, ADRs, and major governance documents

**Completion gate:** L1 and L2 for CIS_Execution_Layer_Contract_v1.md complete
through the queue-backed operator button. Results visible in dashboard without
terminal inspection.

---

### 6.5 Operator Abstraction

**Authority files:**
- `api/operator.py` (MODIFY — next_action route reads live system state)
- `cis_dashboard.html` (MODIFY — Next Required Action tile shows authoritative state)

**Next Required Action priority logic (implemented in next_action route):**

1. Any job in `failed` or `needs_human_review` → surface immediately
2. Any job in `running` or `claimed` → show progress and estimated state
3. Slot 1 DOWN with L2 work pending → prompt start via dashboard button
4. Open CIS Live sessions → prompt resolution by count and topic
5. No active blockers → read next steps from reorientation file

**Completion gate:** Next Required Action tile reflects actual system state,
not static text from a file read. Operator does not need to remember what to do next.

---

### 6.6 Operator Surface Audit

**Purpose:**
Existing dashboard forms were built as data capture surfaces.
PD.5 reclassifies them as operational truth and continuity surfaces.
That is a structural reframe requiring audit before further expansion.

**Classification rule:**
All existing major forms are classified TRANSITIONAL until audited against
the governance model defined in this contract.

**Minimum audit requirement per form:**

Each form must be evaluated against:
- What authority source should it eventually read from?
- Does it currently create false sense of completion?
- What is the minimum correction required before Phase 1 resumes?
- Does it rely on human memory where system state could be derived?

**Form audit targets:**

**Session Close Form**
Current state: manual summary entry
PD.5 target: guided continuity checkpoint that verifies open jobs, open CIS Live sessions,
unresolved verification FAILs, and uncommitted changes before allowing close
Minimum correction: add pre-close state check that surfaces blockers

**Handoff**
Current state: generated text artifact from human-supplied fields
PD.5 target: state-derived continuity packet assembled from DB, job state, open Live sessions,
and verification log — human approves and annotates, does not reconstruct
Minimum correction: identify which fields can be auto-populated from authoritative sources

**ADR Form**
Current state: basic decision entry with title and description
PD.5 target: architectural decision workflow with scope, authority, supersedes/superseded-by,
verification requirement, affected files, and implementation status fields
Minimum correction: add affected_files and verification_required fields

**Session Form**
Current state: basic lifecycle form (start/close)
PD.5 target: session as governed work container with focus, active build target,
open jobs, unresolved risks, and close gates
Minimum correction: add open job count and open Live session count to session start view

**Note:** Full form redesign is NOT a PD.5 requirement.
Minimum blocking corrections only. Full redesign deferred to Phase 0 scaling work.

---

## 7. Non-Goals (Explicit Scope Boundary)

The following must not be built during PD.5 under any circumstances:

- New extraction pipeline features
- Knowledge record schema changes
- Retrieval or embedding work
- Agent capability expansion
- Frontend component redesign beyond operator section stabilization
- Additional operator buttons beyond current four
- New dashboard panels or sections
- Flask replacement
- SQLite replacement
- Production deployment infrastructure
- Multi-worker execution
- Concurrent queue processing
- Full form redesign

If a build decision would add capability beyond PD.5 scope, it is deferred to the
appropriate phase and logged as an ADR direction or open question.

---

## 8. PD.5 Implementation Sequence

Work must proceed in this order. No step begins before its predecessor is complete.

```
1.  Fix cis_verify_semantic.py token budget (max_tokens 1024 → 768, remove temperature param)
2.  Build cis_launcher.sh — idempotent Flask + browser open
3.  Fix cis_vllm_slot1.sh — port pre-check before startup
4.  Update desktop launcher to call cis_launcher.sh
5.  Add Flask status route to api/operator.py
6.  Surface Flask + Slot 1 status in dashboard Operator section
7.  Draft and lock ADR-045
8.  Build db/execution_jobs.py — schema and job lifecycle functions
9.  Build runtime/cis_worker.py — single-worker poll loop
10. Refactor verify_contract route to enqueue only
11. Validate queue-backed L1 through operator button
12. Validate queue-backed L2 through operator button (first full ADR-044 + ADR-045 test)
13. Upgrade next_action route to live system state query
14. Audit existing forms against PD.5 governance model
15. Apply minimum blocking corrections to forms
16. Draft ADR-046 from CIS_FILE_MAP.md
17. Apply authority labels to runtime/ filesystem
```

Steps 1–6 constitute Runtime Service Ownership stabilization.
Steps 7–12 constitute Execution Queue Ownership (ADR-045).
Steps 13–15 constitute Operator Abstraction and Surface Audit.
Steps 16–17 constitute Filesystem Governance groundwork (ADR-046).

---

## 9. PD.5 Exit Criteria

PD.5 is complete when ALL of the following are true:

**Runtime Service Ownership**
- [ ] Desktop launcher is idempotent — clicking twice produces one Flask instance
- [ ] Flask status visible in dashboard without terminal
- [ ] Slot 1 start/health visible and idempotent from dashboard
- [ ] vLLM zombie process prevention confirmed (port pre-check in startup script)
- [ ] Flask and vLLM logs written to known paths

**Execution Governance**
- [ ] ADR-045 locked
- [ ] execution_jobs table operational in cis_memory.db
- [ ] Single-worker loop running and processing jobs
- [ ] Verify Contract route enqueues work only — no direct script execution
- [ ] L1 verification runs queue-backed and result visible in dashboard
- [ ] L2 verification runs queue-backed and result visible in dashboard
- [ ] Stale job detection operational
- [ ] Job state visible in dashboard Operator section

**Operator Abstraction**
- [ ] Next Required Action tile reflects live system state
- [ ] Operator does not need terminal to determine what to do next
- [ ] All four operator buttons function without terminal fallback

**Filesystem Governance**
- [ ] ADR-046 drafted (lock deferred to post-ADR-045)
- [ ] All files in runtime/ have authority labels in CIS_FILE_MAP.md
- [ ] No duplicate authority exists between runtime/ root and subdirectories

**Operator Surface Audit**
- [ ] All major forms classified TRANSITIONAL with audit notes
- [ ] Minimum blocking corrections applied to Session Close and Session Start forms
- [ ] Handoff auto-population fields identified

**Continuity**
- [ ] Open CIS Live sessions #021, #022, #023, #024 resolved or formally accounted for
- [ ] Reorientation file and Project Primer updated to reflect PD.5 insertion
- [ ] Canonical Build Sequence updated to show PD → PD.5 → Phase 0

**Operator Independence Gate (Constitutional)**
A non-coder operator can, without terminal interaction:
- Click one desktop launcher and open CIS
- Observe Flask and Slot 1 runtime state
- Start Slot 1 from the dashboard
- Run Verify Contract from the dashboard
- Observe job progress and verification results
- Close the session with state-derived continuity information

This gate must pass before Phase 0 scaling work resumes.

---

## 10. Verification Requirements

**L1 — Deterministic (pre-lock)**
- All files listed in Section 6 exist at canonical paths
- Launcher script contains port pre-check logic
- execution_jobs table schema matches Section 6.2 field list
- Worker script contains single-job poll loop
- verify_contract route calls enqueue function, not run_script directly
- next_action route contains live state priority logic
- cis_verify_semantic.py max_tokens is 768 or less

**L2 — Semantic (post-implementation)**
- Worker correctly transitions jobs through legal state graph
- Stale detection fires on heartbeat timeout
- Launcher does not spawn duplicate processes
- Dashboard operator section reflects backend authority state, not assumptions
- Recovery behavior handles interrupted jobs without silent loss

**L3 — External Audit (required before lock)**
Architectural review must confirm:
- PD.5 preserves canonical roadmap dependency order
- PD.5 does not introduce scope that belongs to Phase 0 or later
- Runtime ownership and execution ownership are cleanly separated
- Exit criteria are measurable and not circular
- Non-goals section prevents known scope creep vectors
- Operator Surface Audit does not accidentally trigger full form redesign
- Contract is consistent with ADR-043, ADR-044, and ADR-045 direction

---

## 11. Relationship to Existing ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-033 | Verification layer — PD.5 routes verification through queue, does not bypass |
| ADR-034 | Three-role verification chain — PD.5 implements queue-backed execution of this chain |
| ADR-040 | L3 audit mandatory — PD.5 requires L3 before lock |
| ADR-041 | Artifact registry — queue-backed verification still writes to registry |
| ADR-043 | Execution layer contract — PD.5 execution queue is subordinate to this authority |
| ADR-044 | Operator Abstraction Layer — PD.5 operationalizes ADR-044's enqueue intent |
| ADR-045 | Execution Queue Ownership — drafted and locked during PD.5 Step 7 |
| ADR-046 | Filesystem Governance — groundwork during PD.5, lock deferred post-ADR-045 |

---

## 12. Roadmap Insertion

The canonical dependency graph insertion is recorded here as a reference marker.
The canonical roadmap documents are NOT fully rewritten until PD.5 is operational
and validated. This prevents prematurely hard-baking details that may require one
further refinement pass after real execution.

**Insertion note (reference only — canonical docs updated post-PD.5 validation):**

Previous:
```
Phase PD → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
```

Corrected:
```
Phase PD → Phase PD.5 → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
```

PD.5 does not replace any phase. It makes Phase 0 scaling possible without
repeated derailment from build environment failures.

The canonical roadmap destination is unchanged.

**Canonical roadmap revision action:** Deferred to post-PD.5 validation.
At that point: add PD.5 insertion note to CIS_Canonical_Build_Sequence.md and
CIS_Plain_Language_Build_Roadmap.md as a versioned Loop 4 correction.

---

## Artifact Identity

```
artifact_id:   contract__CIS_PD5_Operational_Governance_Contract_v1__20260429__001
artifact_type: contract
artifact_name: CIS_PD5_Operational_Governance_Contract_v1
artifact_path: /mnt/projects/cis/docs/contracts/CIS_PD5_Operational_Governance_Contract_v1.md
status:        PENDING L1/L2 — L3 PASS — LOCKED FOR VERIFICATION
version:       1.1
session_id:    20260429
builder:       claude-sonnet-4-6
l3_auditor:    ChatGPT architectural review
l3_verdict:    PASS WITH MINOR CORRECTIONS (all corrections applied in v1.1)
```

---

*This document requires L1 deterministic verification and L2 semantic verification
before lock. L3 external audit is complete (PASS). Deploy to VM canonical contracts
path, run cis_verify.py, then cis_verify_semantic.py through the operator queue.*
