# CIS Build Scenarios: Strategic Approaches to Finally Building This App

**Author:** Hermes Agent (DeepSeek analysis of 200+ extraction files)
**Date:** 2026-05-14
**For:** Eric (Utgar) — to review after getting back from outside

---

## Background: Why 5 Weeks Of Claude/ChatGPT Failed

The existing extraction files document 5+ weeks of failed attempts. The root causes are:

1. **Scope Confusion** — Claude and ChatGPT kept trying to build the full vision (stream architecture, workbenches, sovereign inference) instead of the next concrete thing
2. **AI Proposing → No One Committing** — Every session ended with architectural insight but zero code committed to runtime
3. **Governance Over Execution** — The architecture demands contract-first, but that turned into infinite schema planning without implementation
4. **Context Thrash** — Each new chat lost all context, re-discovered the same architecture, and died before delivering

The core problem is not complexity — it's **sequence discipline**. The system is already 80% of the way there. The remaining gap is narrow and specific.

---

## What Currently Exists (Working)

- **Flask backend** at `/mnt/projects/cis/runtime/app.py` with 15 API blueprints
- **SQLite DB** at `/mnt/projects/cis/memory/cis_memory.db` with `drafts`, `execution_jobs`, `captures`, `decisions`, `insights`, `models` tables
- **Queue worker** at `queue_worker.py` — single-threaded FIFO, polls `execution_jobs` for `verify_contract` and `run_l2`
- **Dashboard** at `cis_dashboard.html` (~3194 lines, React-without-JSX via `React.createElement`)
- **API/drafts** — ADR-048 Phase 1: `/api/drafts/stage`, `/api/drafts/<id>/action` (approve/reject/supersede/commit), DraftIntakePanel in UI
- **Primer update executor** `primer_update_v3.py` with governance controls
- **Verification layer** — L1 (cis_verify.py), L2 (cis_verify_semantic.py via vLLM Slot 1)
- **Intake CLI** `cis_intake.py` — moves files through incoming → processing → completed
- **Conflict register** `cis_conflict_append.py`
- **Download watcher** `cis_download_watcher.py` (partially built)

## What Is Blocked / Broken

- **`verify_contract` flag mismatch bug** — blocks ADR-045 full closure
- **Queue worker unverified** on VM (was developed in different env)
- **ADR-048 Phase 2** (downloads watcher automation) blocked until Phase 1 verified
- **Frontend monolith** — 3194 line HTML file, no fault isolation
- **vLLM Slot 1** requires manual start each session
- **Filesystem drift** — legacy files, namespace collisions
- **15 SESSION_INSIGHT_RECORDs** identified but not ingested
- **Human-as-transport-layer** — all AI content flows through manual copy-paste

---

## The Critical Insight

The system is much closer to operational than it looks. The current state says:
> "ADR-048 Phase 1 is built (drafts table, API endpoints, dashboard panel). But Phase 2 is blocked."

The truth is: **ADR-048 Phase 1 was never actually completed and verified.** The code exists but was never deployed, tested, and locked. The extraction files document intent and architecture but the runtime has never received the commit.

Every build scenario must start from the same first step: **get the working code into the runtime, fix the blocker bugs, and verify it actually runs.**

---

# SCENARIO A: "Intake First" — Close ADR-048, Then Everything

**Focus:** The human-is-the-API problem. Solve intake, then all other content flow unlocks.

**Time estimate:** 1-2 sessions (current session tools, not Claude)

### Phase A1 — Fix & Close ADR-045 (prerequisite, 1 session)
1. Fix `verify_contract` flag mismatch in `queue_worker.py` (the bug that prevents reliable verification)
2. Deploy verified `queue_worker.py` to VM runtime
3. Run `cis_test_queue.py` to confirm FIFO behavior and cold start recovery
4. Mark ADR-045 as LOCKED with verification evidence

### Phase A2 — Verify & Lock ADR-048 Phase 1 (1 session)
1. Ensure `drafts` table exists (check schema — it does in the DB but verify columns match `api/drafts.py`)
2. Test `/api/drafts/stage` end-to-end via curl
3. Test approve → commit → canonical record creation pipeline
4. Test supersession and rejection paths
5. Confirm DraftIntakePanel renders and actions work in dashboard
6. Mark ADR-048 Phase 1 COMPLETE

### Phase A3 — ADR-048 Phase 2: Downloads Watcher (1 session)
1. Fix `cis_download_watcher.py` — ensure it detects new files in Downloads, creates draft via API, and moves to `inbox/platform_drafts/`
2. Wire the watcher into systemd as a persistent service (or have the Flask app auto-start it)
3. Test end-to-end: download a file → watcher picks it up → draft appears in dashboard → human approves → committed to canonical

### Phase A4 — Ingest 15 SESSION_INSIGHT_RECORDs (2 sessions)
1. Use the now-working intake pipeline to ingest the 15 identified insight records
2. Each record becomes a draft → human reviews → committed to knowledge layer
3. Knowledge base is now populated with real data for the first time

### Phase A5 — CIS Build-Plan Reconstruction (1 session)
1. With ingested data and working intake, reconstruct the authoritative build plan from current state
2. Determine what app features to prioritize next

### What This Unlocks
- No more manual copy-paste for any AI content
- Knowledge layer gets real data
- Downstream development decisions are grounded in actual operational data

### Risk
- If ADR-045 has deeper bugs not surfaced by the extraction files, this stalls
- The "verify_contract flag mismatch" may be more complex than described

---

# SCENARIO B: "Governance & Memory First" — Lock the Foundation

**Focus:** Constitutional integrity. Get governance, memory, and primer infrastructure bulletproof.

**Time estimate:** 2-3 sessions

### Phase B1 — Primer/Memory Audit (1 session)
1. Verify `primer_update_v3.py` works end-to-end (preview, two-phase atomic apply, process lock)
2. Verify `--approved-by` and `--architect` provenance tracking works
3. Run primer drift detection across all 16 primer files
4. Fix any primer contradictions found

### Phase B2 — Conflict Register as Active Governance (1 session)
1. `cis_conflict_append.py` exists — ensure it's wired into session close workflow
2. Create conflict resolution workflow: log → escalate → resolve → close
3. Enforce: session cannot close with unresolved conflicts

### Phase B3 — Session Close Automation (1 session)
1. Verify GET `/api/session/verification-status` works
2. Verify Dashboard SessionPanel auto-populates Field 5 (Verification Status)
3. Verify POST `/api/session/close` writes verification_status
4. Close loop: session → verification → memory → continuity

### Phase B4 — vLLM Slot 1 Daemonization (1/2 session)
1. Create systemd service for vLLM Slot 1 (`cis_vllm_slot1.sh`)
2. Ensure port 8002 healthcheck in `cis_slot1_healthcheck.py`
3. L2 semantic verification is now always available

### What This Unlocks
- Constitutional integrity: primer drift never goes unnoticed
- Session continuity: clean close/verify/reopen cycle
- L2 verification always online
- Foundation for cross-session validation

### Risk
- This doesn't directly solve the human-transport problem — you still copy-paste
- Governance without intake throughput can feel like bureaucracy without output

---

# SCENARIO C: "Execution Layer First" — Ship A Working Queue

**Focus:** Getting the queue worker running reliably, then expanding what it can do.

**Time estimate:** 1-2 sessions

### Phase C1 — Debug & Stabilize Queue Worker (1 session)
1. Find and fix the `verify_contract` flag mismatch (the blocker bug)
2. Deploy to VM, confirm no stale-code reload issue
3. Add a `run_intake` job type: queue worker can now process content ingestion
4. Add a `run_normalize` job type
5. Verify all job types: `verify_contract`, `run_l2`, `run_intake`, `run_normalize`

### Phase C2 — Queue Dashboard Expansion (1 session)
1. In the Dashboard, add job queue depth visualization
2. Add job history with results/errors
3. Add manual job submission (paste JSON, pick job type, submit)
4. This gives you a "supervisor console" for the entire execution layer

### Phase C3 — Wire Intake Into Queue (1 session)
1. `/api/drafts/stage` enqueues a `run_intake` job instead of processing inline
2. Queue worker processes the intake job
3. Dashboard shows intake job progress

### Phase C4 — Cross-Session Continuity via Queue (1 session)
1. Queue state must survive process death (already partially done — cold start recovery)
2. Verify state recovery: kill Flask, restart, running jobs reset to queued
3. Add queue persistence verification

### What This Unlocks
- Execution is fully queue-backed, reliable, observable
- Everything the system does goes through a governed FIFO pipeline
- Admins can see, manage, and reroute work from the dashboard

### Risk
- Skips the intake pipeline that users actually feel — you still copy-paste content
- Deep queue debugging is unsexy and may feel like polishing wheels instead of driving

---

# SCENARIO D: "User-Facing App First" — Dashboard Modular Refactor

**Focus:** The frontend is a 3200-line monolith. Modernize it so new features can ship.

**Time estimate:** 2-3 sessions

### Phase D1 — Assess Monolith Structure (1 session)
1. Audit the 3194 lines of `cis_dashboard.html`
2. Identify panel boundaries: Operator, DraftIntake, Session, Tasks, Models, Queue, etc.
3. Each panel is already a JavaScript function — the boundaries exist but are in one file

### Phase D2 — Split Into Separate Files (1 session)
1. Extract each panel into its own `.js` / `.html` partial
2. Flask serves the main shell; panels are lazy-loaded via `<script>` tags or fetch
3. Fault isolation: one broken panel can't bring down the entire UI

### Phase D3 — Add Draft Management View (1 session)
1. The DraftIntakePanel exists but is basic — expand it:
   - Sort/filter drafts by type, zone, status, source_model
   - Preview payload inline with syntax highlighting
   - Batch approve/reject
   - Show commit history per draft

### What This Unlocks
- You can ship UI changes without fear of breaking everything
- Draft management becomes the primary operator surface
- Foundation for Discovery/Intake/General workbenches from Phase 5 of the original plan

### Risk
- Pure frontend work; no backend throughput gains
- Doesn't fix any of the queue/intake blockers
- If the monolith refactor introduces bugs, you lose the only working UI

---

# SCENARIO E: "Spike — Build A Minimal Viable Product"

**Focus:** Forget governance perfection. Build the smallest thing that gives you value.

**Time estimate:** 1 session

### The Minimum Viable CIS

This ignores phases, ADRs, and constitutional governance for one session only. The goal is a single workflow you can actually run:

1. **Python script** that reads a JSON file from a known location
2. **Validates** the JSON against a schema
3. **Stages** it into the drafts table
4. **Dashboard** shows the draft
5. **One click** approves it into canonical storage
6. **Records** are queryable via API

That's it. No queues, no workers, no state machines. This is what ADR-048 Phase 1 was supposed to be — just verify it works.

### Why This Matters
The entire project has been over-designed. The 5 weeks of failed sessions prove that governance-first architecture without a working feedback loop is a trap. A working MVP gives you:

- Actual data to reason about
- A real feedback loop
- Motivation to build the next layer
- Proof that the architecture works

### How This Differs From What Already Exists
The code already exists for this. The difference is: **no one has ever run it end-to-end and verified it works.** The extraction files analyze transcripts, not runtime behavior.

---

# Priority Recommendation

Based on analysis of 200+ extraction files and the actual runtime codebase:

## Immediate Priority: Scenario A (Intake First)

Why:
1. ADR-045 is described as "locked/full implemented" in the extractions but has a known unverified bug — this must be resolved before anything else
2. ADR-048 Phase 1 code exists but was never deployed and verified — this is the shortest path to a working system
3. Fixing the intake pipeline unlocks every downstream capability (ingestion, build-plan reconstruction, app development)
4. The project has been "pre-draft" for too long — the fastest path to momentum is getting a working intake

## Suggested Two-Session Sprint

### Session 1 — Fix and Verify
1. Fix `verify_contract` flag mismatch in `queue_worker.py`
2. Verify queue worker on VM runtime
3. Run `cis_test_queue.py`
4. Verify drafts table schema matches `api/drafts.py` expectations
5. Test `/api/drafts/stage` and action routes via curl
6. Test DraftIntakePanel in Dashboard

### Session 2 — Complete and Lock
1. Fix any issues found in Session 1
2. End-to-end test: generate content → stage → approve → commit → query
3. Mark ADR-048 Phase 1 as VERIFIED COMPLETE
4. Decide: Phase 2 (downloads watcher) or ingestion of insight records next?

## Why NOT The Other Scenarios (For Now)

- **Scenario B (Governance First):** Governance without data flow is empty ceremony. You need working intake first.
- **Scenario C (Execution Layer):** The queue is close enough to working — don't polish it until you have something to queue.
- **Scenario D (Dashboard Refactor):** Pure cosmetic risk without throughput gain. Do this after intake works.
- **Scenario E (MVP Spike):** Tempting, but the MVP code already exists. The problem is verification, not building more code.

---

## Key Files Summary For Build Work

| File | Purpose | Status |
|------|---------|--------|
| `/mnt/projects/cis/runtime/api/drafts.py` | ADR-048 Phase 1 — draft staging and action routes | BUILT, UNVERIFIED |
| `/mnt/projects/cis/runtime/queue_worker.py` | ADR-045 — single-threaded FIFO queue worker | BUGGY (flag mismatch) |
| `/mnt/projects/cis/runtime/cis_dashboard.html` | Frontend (3194 lines, React) | OPERATIONAL, MONOLITHIC |
| `/mnt/projects/cis/runtime/cis_download_watcher.py` | ADR-048 Phase 2 — filesystem watcher | BUILT, UNVERIFIED |
| `/mnt/projects/cis/runtime/cis_intake.py` | CLI intake tool (incoming→process→complete) | OPERATIONAL |
| `/mnt/projects/cis/runtime/cis_verify.py` | L1 deterministic verification | OPERATIONAL |
| `/mnt/projects/cis/runtime/cis_verify_semantic.py` | L2 semantic verification (via vLLM) | OPERATIONAL |
| `/mnt/projects/cis/runtime/primer_update_v3.py` | Primer update executor with governance | OPERATIONAL |
| `/mnt/projects/cis/runtime/cis_conflict_append.py` | Conflict register CLI | OPERATIONAL |
| `/mnt/projects/cis/runtime/cis_vllm_slot1.sh` | vLLM Slot 1 startup script | MANUAL START REQUIRED |
| `/mnt/projects/cis/memory/cis_memory.db` | SQLite database with 19 tables | OPERATIONAL |
| `/mnt/projects/cis/runtime/cis_test_queue.py` | Queue test harness | BUILT |

---

## Decision Point For You

When you get back, the key question is:

**Do you want me to start fixing and verifying the existing code (Scenario A — intake first), or do you want a different angle?**

The extraction files consistently point to the same bottleneck: the human copy-paste transport layer. Fix that and everything else accelerates. Leave it unfixed and nothing changes regardless of how much governance or architecture you design.
