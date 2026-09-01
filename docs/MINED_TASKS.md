# MINED TASKS — not on the build list

**PROVISIONAL.** P3's 4,479 keyword rows remain unadjudicated. This file will change when they are worked; tasks may be added and evidence counts may rise.

**Complete:** P1 (acknowledged-but-unresolved), P2 (reasoning that implies a task), P4 (the filesystem, by content not filename), P6 (targeted re-mine of the productive sources). Every candidate in those four passes carries a recorded verdict.

## What each pass contributed

| pass | queued | TASK verdicts | what it reached |
|---|---|---|---|
| P1 acknowledged | 567 | 16 | documents that state a problem in the words a taxonomy would use |
| P2 reasoning | 862 | 22 | exchanges where a problem was reasoned through and nobody wrote a task |
| P3 keyword | 11,722 | 12 | exact markers and identifiers semantic search cannot reach — 4,479 still pending |
| P4 filesystem | 874 | 22 | 1,885 .md files read by content, filenames ignored — including the container's own skill library |
| P6 targeted | 1,170 | 16 | a second semantic pass in the corpus's own register, aimed at the seam P2 opened |

Scope is recorded per task. CONTAINER means the finding was verified against the pipeline in production. VM_ONLY means it describes the older VM pipeline. UNDETERMINED names the check that would settle it.

---


# CONTAINER


## gate-mechanics

### Build the verification snapshot and provenance gaps

Execution snapshot and git snapshot isolation are both recorded as verified gaps never built; the gate approval endpoint inserts with no provenance system; after a session-gap recovery the agent has no record of what it did during the gap.

- **Raised:** 5 times, 2026-07-13 to 2026-08-24
- **Sources:** fs:enforcement
- **Scope:** CONTAINER — all four documents are the container's own skill library describing its verification phase; 15815 still needs verify-snapshot-gap.md read in full
- **Candidates:** 15782,15784,15723,15720,15815

**Strongest excerpt** — `enforcement/mwl-proof-v2/cis-pipeline-architecture/references/session_recovery_technique.md`

> may continue after the gap but the agent has no memory of what it did during the gap.

### Give the pipeline a stop button and validate its input

The relay blueprint exposes eight routes and none cancels a run; grep for 'cancel' returns 0. pipeline_relay.py accepts the intent string with no validation, so a malformed intent enters the pipeline and is caught only downstream.

- **Raised:** 2 times, 2026-07-08 to 2026-07-08
- **Sources:** fs:cis_kernel
- **Scope:** CONTAINER — runtime/api/relay.py is the blueprint container_app.py registers at line 27; no _validate_intent in runtime/abstraction/pipeline_relay.py
- **Candidates:** 15439,15418

**Strongest excerpt** — `cis_kernel/extraction/functional_intents/relay_extraction_analysis.md`

> ## 9. UNRESOLVED GAPS + MISSING LAYERS ### Missing Runtime Bridges: 1. **No WebSocket/SSE**: No real-time status updates; requires polling 2. **No Cancellation**: No endpoint to stop a running pipeline 3. **No Retry Logic**: Failed background threads are not retried 4. **No Timeout**: No maximum execution time for background threads ### Undefined Objects: 1. **`PipelineRelay`**: Imported but not defined in this file; external dependency 2. **`eric_gate_approvals` table**: Referenced but not created; assumes pre-existing schema 3. **`workflow_runs.directive_hash`**: Column assumed to exist; no 

### Override plane and fail-mode policy before any blocking gate is trusted

The v2.0 deadlock came from a clearance token the gate itself could prevent you from writing. Build and prove an out-of-band override first; state fail-open vs fail-closed per mode.

- **Raised:** 2 times, 2026-06-27 to 2026-08-29
- **Sources:** cis_docs, claude_export
- **Scope:** CONTAINER — the .GATE_DISABLED override plane is repo-level and applies to both pipelines
- **Candidates:** 1462,508

**Strongest excerpt** — `claude_export`

> Here's where today broke, and it's three specific design errors, each fixable: **Error 1 — the gate's "pass" condition depended on a fragile, stateful token.** Today's hook checked for a `/tmp/cis_gate_clearance` file written by `gate_runner.sh`, 30-minute TTL. That's the deadlock engine: the hook blocks writes, but granting clearance *requires writing the token*, and writing got blocked, and now nothing can ever clear. A deterministic gate must never depend on state that the gate itself can prevent you from creating. The clearance mechanism was a second moving part that could — and did — jam.

### The reviewed diff must contain the deliverable

A code review ran against a diff that omitted the new file entirely while L1 confirmed it on disk, and reviewers evaluated proposal text that did not match the applied patch.

- **Raised:** 2 times, 2026-08-29 to 2026-08-29
- **Sources:** hermes_glm-reviewer, pipeline_code_review
- **Scope:** CONTAINER — the source rows are pipeline_code_review, i.e. container runs
- **Candidates:** 783,786

**Strongest excerpt** — `hermes_glm-reviewer`

> [asked] ## L1 UNIVERSAL CHECK RESULTS ## L1: File Exists ✗ runtime/abstraction/pipeline_relay.py MISSING ## CHUNK DIFF ```diff diff --git a/PROJECT_CONTEXT_PACK_UPLOAD/HCP_10_DEV_PIVOT_STATUS.md b/PROJECT_CONTEXT_PACK_UPLOAD/HC... These are two completely different descriptions of the same behavior. The applied diff (chunk diff) correctly identifies the no-op. The proposal incorrectly describes functional exclusion. This means either the implementer ignored the proposal and wrote correct text, or there are two conflicting versions in circulation. The review is evaluating a proposal that doesn'


## pipeline-defect

### Keep test data out of canonical state

A test transition wrote proposal_id='test-lifecycle-001' into live lifecycle_events and left it.

- **Raised:** 1 times, 2026-08-29 to 2026-08-29
- **Sources:** claude_export
- **Scope:** CONTAINER — lifecycle_events is the shared spine
- **Candidates:** 1360

**Strongest excerpt** — `claude_export`

> The test transition writes a row with `proposal_id='test-lifecycle-001'` into your live spine and leaves it there. That's test data in the canonical state table. Either have the test clean up after itself (delete the test row after verifying), or use a clearly-marked test value and confirm it won't be picked up by anything that reads `lifecycle_events` later. A stray test transition sitting in the lifecycle log is the kind of thing that confuses a future verifier — "why is there a DRAFT_READY for a proposal that doesn't exist."


## review-independence

### Make review independence verifiable, not assumed

Nothing checks that a reviewer searched before delivering a verdict; a revision carries no objection-to-resolution mapping; an empty or ambiguous reviewer response is consumed as a review; and Eric has no guaranteed second opinion. NOTE: the model-sharing half of this is FALSE in the container.

- **Raised:** 5 times, 2026-06-27 to 2026-08-29
- **Sources:** cis_docs, hermes_glm-reviewer, hermes_glm-verifier, hermes_prime
- **Scope:** CONTAINER — container review1 is qwen/qwen3.7-max and review2 is z-ai/glm-5.2 against draft deepseek-v4-pro — three lineages, so model-sharing does not apply; the independence CHECKS are still absent
- **Candidates:** 166,976,13826,14972,3563

**Strongest excerpt** — `hermes_prime`

> [asked] look through the session log for yesterday where we realized that the advisor chat is just pretending to have different roles and all are running the same model because the config files are not completely setup. **May 25, 12:12 AM** — session `api-a7bc10d5b6371553` Dug deeper and confirmed: Prime and V4-Pro Advisor are the *same model* `deepseek-v4-pro` — the only difference is `reasoning_effort`, which is set identically everywhere. All three configs are copies of the original. The core finding is captured in `/mnt/projects/cis/runtime/docs/BRAINSTORMING_TODO.md`. Let me pull the actu


# UNDETERMINED


## continuity-and-record

### Settle the glossary-collision and inheritance-index schemas

Unresolved glossary term collisions block cross-layer operations with no collision-to-runtime bridge; the inheritance index has no machine-readable schema and neither session-initialization nor query-routing consumes it.

- **Raised:** 2 times, 2026-05-13 to 2026-05-13
- **Sources:** fs:cis_kernel
- **Scope:** UNDETERMINED — would be settled by checking whether any container phase reads the glossary or the index
- **Candidates:** 15023,15024

**Strongest excerpt** — `cis_kernel/extraction/functional_intents/15_inheritance_index_extraction_analysis.md`

> | Machine-readable format | Schema definition | Future (not yet defined) | # 9. UNRESOLVED GAPS + MISSING LAYERS | Index → Automated inheritance routing | Machine-readable format not yet defined | Future | | Index → Session initialization | Not yet implemented | Future | | Index → Query routing engine | Not yet implemented | Future | | Machine-readable index schema | Format for automated routing | Not defined | | Index addition request | Object for submitting additions | Not defined | | Authority classification record | Object for tracking classification history | Not defined | | Machine-reada

### Close the system-learning loop

Corrections are logged but never fed back into the extraction model, so the review work produces no improvement.

- **Raised:** 1 times, 2026-06-27 to 2026-06-27
- **Sources:** cis_kernel
- **Scope:** UNDETERMINED — would be settled by establishing whether the container's pattern catalog consumes correction history
- **Candidates:** 5162

**Strongest excerpt** — `cis_kernel`

> - **Loop 3 — System Learning**: Human corrections at review → corrections table → training data for extraction model → improved extraction quality. This loop is designed but not implemented — corrections are logged but not fed back into the model. ### Correction Loops - **Review Correction Loop**: Human reviews draft record → corrects errors → corrected record becomes authoritative → corrections logged to DB → available for analysis. This is operational. - **Session Close Correction Loop**: Session close produces handoff → post-close work discovered → addendum written → next session receives a

### Define the capability taxonomy and criticality criteria

Without one, the primary-plus-fallback requirement cannot be enforced.

- **Raised:** 1 times, 2026-08-29 to 2026-08-29
- **Sources:** cis_kernel
- **Scope:** UNDETERMINED — no capability_taxonomy, CapabilityClaim or capability_registry anywhere under runtime/ — absent from both pipelines
- **Candidates:** 79

**Strongest excerpt** — `cis_kernel`

> ### Object 1: "Capability" - **Description**: What constitutes a "critical capability" is undefined - **Impact**: Cannot enforce primary + fallback requirement without capability definition - **Required**: Capability taxonomy, criticality criteria, mapping to tools ### Object

### Resolve the memory seed failure

seed_memory.py failed with 'database or disk is full' across roughly a thousand extraction files; whether the seed completed or is still short was never recorded.

- **Raised:** 1 times, 2026-08-29 to 2026-08-29
- **Sources:** hermes_prime
- **Scope:** UNDETERMINED — the seed target and its current completeness were never established
- **Candidates:** 3513

**Strongest excerpt** — `hermes_prime`

> [asked] [IMPORTANT: Background process proc_00d2558b5b2e completed (exit code 0). Command: cd /mnt/projects/cis/runtime && python3 scripts/seed_memory.py 2>&1 Output: 518/1536] top_level_extraction_analysis.md... ✗ database or d... ✗ database or disk is full [1530/1536] utab_system_assessment_extraction_analysis.md... ✗ database or disk is full [1531/1536] utab_todo_extraction_analysis.md... ✗ database or disk is full [1532/1536] vendor_extraction_analysis.md... ✗ database or disk is full [1533/1536] we_will_be_starting_from_scratch_so_extraction_analysis... ✗ database or disk is full [1534/15


## operator-load

### Automate the ADR-048 intake and handoff package

The record calls the manual transfer of structured content the largest remaining automation gap and it is still done by hand. The Downloads watcher runtime model and draft storage format were never settled; cis_build_handoff_package.py and cis_download_watcher.py were never built; a dropped return-dispatch pickup deadlocks the run.

- **Raised:** 4 times, 2026-05-13 to 2026-08-02
- **Sources:** fs:cards, fs:cis_kernel
- **Scope:** UNDETERMINED — the ADR-048 staging path is VM-side, but whether the container pipeline's own intake replaces the need is not established
- **Candidates:** 15019,15020,15017,14994

**Strongest excerpt** — `cis_kernel/extraction/functional_intents/08_open_questions_extraction_analysis.md`

> - **Architectural Significance**: The Downloads watcher's runtime model (daemon vs Flask-started) is unresolved, creating a process architecture gap ## Discovery 2: Draft Storage Format Unresolved - **Architectural Significance**: Dashboard modularization approach (React vs Flask partials vs lightweight JS) is unresolved - **Architectural Significance**: Formal zone classification (ACTIVE, MIRROR, ARCHIVE, LEGACY, TRANSITIONAL, DEPRECATED) for ADR-047 is unresolved - **Runtime Impact**: Without classification, filesystem becomes ungoverned; retention and migration policies cannot be enforced -


# VM_ONLY


## continuity-and-record

### Record the decision rationale that was never written down

The file-size limit has no explanatory note; the build plan still depends on a spec cited as containing factual errors and no longer on disk; the 640-line spec has no risk register.

- **Raised:** 3 times, 2026-06-27 to 2026-08-29
- **Sources:** cis_docs, claude_code
- **Scope:** VM_ONLY — project_decisions is not read or written in the container path
- **Candidates:** 161,147,152

**Strongest excerpt** — `claude_code`

> [user] again another best practice question, I dont know why there is a limit in the first place. [assistant] Fair question, and I shouldn't guess at your own reasoning — let me check whether the rule's origin is recorded anywhere. [assistant] Nothing recorded — both commits that touched the file have no explanatory notes, so the reason wasn't written down anywhere. What follows is my reading as a general practice, not something I recovered from your project.

### Implement knowledge-record backlinks

The designed backlink syntax for knowledge-record markdown was never implemented in cis_normalize.py.

- **Raised:** 1 times, 2026-06-27 to 2026-06-27
- **Sources:** cis_docs
- **Scope:** VM_ONLY — cis_normalize.py is VM ingestion tooling, not in the container path
- **Candidates:** 5158

**Strongest excerpt** — `cis_docs`

> The backlink syntax for knowledge record MD files was designed but not implemented in `cis_normalize.py`.


## gate-mechanics

### Close the gate bypass and generalise enforcement

The write-block was proven on one file and never generalised to the 16 failure modes. The pre_tool_call hook bypass describes the VM only.

- **Raised:** 2 times, 2026-06-27 to 2026-08-29
- **Sources:** claude_export, hermes_v4pro
- **Scope:** VM_ONLY — no pre_tool_call configured in any /home/worker/.hermes-*/config.yaml; the container constrains agents by image and mount
- **Candidates:** 13418,14719

**Strongest excerpt** — `claude_export`

> this is great news, but it proves we can stop a file from being writen to. can we enforce all of these? The 16 failure modes: 2.1 Trust Failures (3) 1. Self-reported completion without evidence 2. Hallucinated claims masquerading as facts 3. Rubber-stamp reviews 2.2 Knowledge Failures (3) 4. Training-data staleness 5. Context amnesia across sessions 6. Version drift in static configs 2.3 Process Failures (6) 7. Scope creep by implementer 8. Constraint bypass through placeholder data 9. Pipeline bypass (agents calling scripts directly) 10. Role confusion 11. Silent gate failures 12. Concurrency


## operator-load

### Finish or retire the VM operator surfaces

Pipeline source list and pagination, intake auto-refresh, the Review page, the DAM nav surface and the LXC public endpoint are specified and unbuilt; the Intel sidebar tabs are decorative placeholders; the dashboard cannot track long-running subprocess work; creating a CIS Live session does not auto-populate the sidebar so rounds can be logged against the wrong session; cis_review.py was built with no contract.

- **Raised:** 5 times, 2026-04-24 to 2026-06-27
- **Sources:** cis_docs, fs:cis_kernel, fs:docs
- **Scope:** VM_ONLY — all are VM dashboard surfaces; container_app.py registers only relay_bp plus health/UI
- **Candidates:** 5138,15527,15230,5153,15551

**Strongest excerpt** — `cis_kernel/extraction/functional_intents/cis_dashboard_monolith_20260420_extraction_analysis.md`

> - (Other states not defined in this file) - Record IDs: Not specified (filesystem-based) - Knowledge categories: Not defined in this file - Records are created but no mechanism to feed outputs back into project refinement # 9. UNRESOLVED GAPS + MISSING LAYERS - **Issue:** Dashboard calls pipeline scripts via subprocess but has no mechanism to track long-running processes - **Issue:** Extraction uses GPU (`PYTORCH_ALLOC_CONF`) but dashboard has no GPU monitoring - **Issue:** `session_log` table is referenced but not defined in `ensure_tables()` - **Issue:** Manifest file structure is assumed bu

### Remove Eric from the relay roles he still fills by hand

Human router, human triage clerk, human reviewer selector and human schema reconciler. The reviewer-implementer challenge loop halts on him; the Implementer-to-Verifier loop has no owner; the manual instruction template has no automation; escalation needs a snapshot-and-switch with an acknowledgement signal rather than a prompt-optimisation step.

- **Raised:** 5 times, 2026-06-27 to 2026-08-29
- **Sources:** cis_docs, claude_export, hermes_glm-reviewer, hermes_prime
- **Scope:** VM_ONLY — the four relay roles and the escalation path are the VM-era manual workflow
- **Candidates:** 14561,541,1169,127,3552

**Strongest excerpt** — `hermes_prime`

> [asked] let me explain it better first. Prime said it was going to look into the issue to send a better prompt to R1, that's where it looks like its working. the bigger issue I think is the way the excalation happened. Prime ask... Second, the feedback failure. During that 7 minutes, there was no "R1 has been notified, it's working" signal. So you were in a void — joined a new thread, asked "are you there?", and R1 either never received it (connection was already dead) or couldn't deliver it back. Either way, you got silence. The root failure: escalation was treated as a task to optimize rathe

### Secure the operator surfaces before any field exposure

Flask has no app-level login and Phase 0 (backup safety net) is deferred with backup integrity unverified; /ui/schedule was blocked on an authentication review that never happened, and the page carries client, work and personal obligations.

- **Raised:** 2 times, 2026-06-01 to 2026-08-29
- **Sources:** fs:cis_kernel, hermes_prime
- **Scope:** VM_ONLY — the Flask dashboard and its login surface run on the VM
- **Candidates:** 15004,3620

**Strongest excerpt** — `cis_kernel/build/CIS_SCRATCHPAD.md`

> **Purpose:** Brain dump and partial todo list for the CIS build conversation ## 2026-05-26 — Schedule/Todo Page Rebuild - Conditional form fields per item_type (appointment shows time dropdowns, deadline requires due_date, attention_item has no due/scheduled) **Purpose:** Extend the Schedule/Todo page into a field-work evidence capture system that helps Eric keep up with daily work obligations, progress notes, billing documentation, and mileage tracking. - Flask has no app-level login * Phase 0: DEFERRED — Proxmox/backup safety net. Google Drive backup integrity unverified; Eric accepted risk.


## pipeline-defect

### Build the ADR-045 execution queue and run logging

execution_jobs schema, queue worker and operator queue routing are all recorded as not built, and the Router Spec's required extraction run-logging table does not exist.

- **Raised:** 2 times, 2026-04-26 to 2026-04-29
- **Sources:** fs:docs
- **Scope:** VM_ONLY — no execution_jobs or runs table in the spine; the queue is VM-era design
- **Candidates:** 15570,15625

**Strongest excerpt** — `docs/claude_chat_transcripts/2026-04-18_Phase 1 intelligence extraction priorities.md`

> **Is template functionality built?** No. There's no mechanism to read a template file. The handoff content is assembled inline in the Python function. **Decided but not yet built:** - The existing image__weird_war_tales_cover__001 has no project_id in its manifest (pre-fix) — if used, project_id will need to be patched manually into that manifest The Router Spec requires every extraction run to record: task type, model used, prompt version, input source, output, validation result, escalation count, runtime metrics. There is no `runs` table in the DB and no mechanism capturing this. Without it,

### Fix the construction-view data contract and its missing handlers

F3 mismatch — topic vs intent, rounds vs phases, no latest_output — makes the view non-functional, and the UI gate action handlers the directive assumes exist were never confirmed.

- **Raised:** 2 times, 2026-08-29 to 2026-08-29
- **Sources:** claude_export, pipeline_intent_review
- **Scope:** VM_ONLY — VM dashboard; container_app.py serves only static /ui/
- **Candidates:** 724,838

**Strongest excerpt** — `pipeline_intent_review`

> Brain's review has a fatal structural flaw: its two most critical findings (F1, F2) are **fabricated**. Brain claimed "full-text search for 'brain/chat', 'brain/start', 'brain/history' across the entire `/workspace/cis/runtime` directory returns zero results" and used this to declare the component non-functional. The endpoints exist. The search was either executed incorrectly or the results were misinterpreted. The irony is that Brain correctly identified the REAL critical issue — F3 (data contract mismatch) — which independently makes the construction view non-functional. The component IS bro

### Add pagination to the capped list endpoints

runtime/api/extraction_runs.py:27,32 and captures.py:23,28 hardcode LIMIT 50 with no paging.

- **Raised:** 1 times, 2026-08-29 to 2026-08-29
- **Sources:** cis_kernel
- **Scope:** VM_ONLY — neither blueprint is registered in container_app.py
- **Candidates:** 809

**Strongest excerpt** — `cis_kernel`

> ## Sequencing Constraint: Task Execution Must Check Approval Status - **Dependency**: Task execution engine must verify `status != 'pending'` or `approval_required=0` before running - **Impact**: Without this check, tasks could execute before human approval - **Build Order**: Task runner must be updated to respect approval gating ## Unstable Dependency: Hardcoded Limit of 50 - **Dependency**: No pagination, filtering, or search - **Impact**: If approval queue exceeds 50, items are invisible; potential for missed approvals - **Build Order**: Pagination should be added before production deployme

### Group parallel advisor rounds reliably

advisor_messages needs a nullable batch_id; thread_id plus timestamp proximity cannot separate interleaved parallel rounds.

- **Raised:** 1 times, 2026-08-29 to 2026-08-29
- **Sources:** hermes_prime
- **Scope:** VM_ONLY — advisor_messages is referenced nowhere in the container path
- **Candidates:** 1402

**Strongest excerpt** — `hermes_prime`

> [asked] Phase 3 — Reconcile Mode: Planning Directive This is a planning document only. No code is to be written until the spec is approved by Eric and reviewed by ChatGPT. What Phase 3 must produce: A Reconcile Mode that takes t... **No. Not without a schema addition.** The only grouping mechanism is `thread_id` + timestamp proximity. A Direct Mode message could be interleaved between the user save and the three assistant saves, or between parallel rounds in the same thread. **Smallest schema-safe option:** Add a nullable `batch_id TEXT` column to `advisor_messages`. The parallel endpoint gene

### Lock the video preprocessing decisions

Whisper model size and the segment-level video source_unit schema must be decided before video preprocessing is built.

- **Raised:** 1 times, 2026-06-27 to 2026-06-27
- **Sources:** cis_docs
- **Scope:** VM_ONLY — video preprocessing is the VM creative-ingestion path
- **Candidates:** 5149

**Strongest excerpt** — `cis_docs`

> 5. What was left unresolved Whisper model size was not decided or locked. The choice between medium and large affects transcription quality and processing time. This must be decided before video preprocessing is implemented. The video source_unit schema — segment-level with timestamp_start and timestamp_end fields — was described but not written as a schema file or locked as an ADR. Video preprocessing in cis_preprocess.py was identified as the next build target but was not implemented. The session ended before this work could begin. The Phase 0 archive run — 10 files from real archive materia

### Retire the legacy inline relay in app.py

PIPELINE_RUNS, portal_pipeline_start and portal_pipeline_status are still at app.py:824-917, duplicating api/relay.py, with only a TODO at line 22. app.py now declares itself reference-only, so the question is whether the file retires wholesale.

- **Raised:** 1 times, 2026-08-29 to 2026-08-29
- **Sources:** hermes_brainstorm
- **Scope:** VM_ONLY — app.py is not the container entry point; container_app.py is
- **Candidates:** 3337

**Strongest excerpt** — `hermes_brainstorm`

> [asked] [PRE-DISCOVERY RESULTS — review before proceeding] ## Knowledge Base (Search error: fts5: syntax error near "/") [END PRE-DISCOVERY — now produce your output] Eric's intent: Add a TODO comment to the top of runtime/ap... 2. Legacy ad-hoc pipeline: embedded **inline** in `app.py` at lines 794-917 — an in-memory `PIPELINE_RUNS` dict plus `portal_pipeline_start` and `portal_pipeline_status` routes. Shells out to `drafter_start.py` + `pipeline_dispatch.sh` as subprocesses. No persistence, no circuit breaker, no crash recovery. This is ~125 lines of duplicate/overlapping relay logic that wa

### Settle model routing and the benchmark protocol

Intelligent routing between local and frontier models is unimplemented, the benchmark protocol is not operationalised, and the Qwen3-VL-32B FP8 test path is unsettled.

- **Raised:** 1 times, 2026-06-27 to 2026-06-27
- **Sources:** cis_docs
- **Scope:** VM_ONLY — routing between local and frontier models is the VM ingestion concern; the container uses fixed per-role model config
- **Candidates:** 5141

**Strongest excerpt** — `cis_docs`

> - Intelligent routing between local and frontier models not implemented. - Model benchmark protocol needs operationalization. - Qwen3-VL-32B FP8 test path remains a future task. - Frontier API escalation remains conditional and unbuilt.


## review-independence

### Make inter-agent review traffic first-class and readable

The Drafter can call the Reviewer with no stored response and no message id, claim approval, self-repair a failed auth without surfacing it, and disable the chat input so Eric cannot abort. dispatch_log holds only a hash and 500 characters of the proposal the Reviewer must challenge.

- **Raised:** 3 times, 2026-08-29 to 2026-08-29
- **Sources:** claude_export, hermes_r1
- **Scope:** VM_ONLY — dispatch_log is absent from runtime/abstraction/ and container_app.py
- **Candidates:** 13859,13468,14616

**Strongest excerpt** — `claude_export`

> - Drafter initiates calls to Reviewer without Eric's knowledge or consent. The result appears as Drafter narration, not Reviewer output. - Drafter claims Reviewer approved a proposal. No stored Reviewer response, no message ID, no verifiable evidence. - When a lateral call fails (auth/API rejection), Drafter attempts self-repair — searching for or substituting API keys — without surfacing the failure to Eric. - During agentic actions, the global chat input is disabled. Eric cannot abort, redirect, or interrupt. - There is no lifecycle state record. There is no way to determine whether a propos

