# ISSUE FINDINGS — read, not computed

**Date:** 2026-08-29
**Method:** all 1,261 clustered issues read and judged. Not sampled, not
ranked by count, not summarised by a model. Each entry below quotes the record
verbatim and states what I could and could not verify.

## Provenance

The chain, so every number here can be traced:

| stage | count | tool |
|---|---|---|
| KB chunks searched (build corpus, archive excluded) | 451,167 | — |
| statements found containing issue-language | 10,177 | `mine_open_issues.py` (FTS5 keyword) |
| after exact + near-duplicate removal | 7,433 | same |
| statements found by meaning, not vocabulary | 488 | `mine_open_issues_semantic.py` (vector probes) |
| of those, invisible to the keyword pass | **478 (98%)** | — |
| union, fragments under 45 chars dropped | 6,578 | — |
| clustered into candidate issues | 3,200 | `build_issue_list.py` |
| with 2+ independent statements | 1,261 | same |
| **read individually for this document** | **1,261 — all of them** | by hand |

The two methods overlap by 2%. Keyword finds what someone thought to name;
semantic finds what they did not. Running either alone would have missed most
of this.

**Yield: 44 numbered findings, which collapse to 20 DISTINCT LIVE ISSUES.**
The 44 overlap — findings 1, 31 and 34 are one issue with its root cause;
4, 14 and 32 are one; 3 and 12 are one; 8, 17, 26, 27 and 28 are one.

The honest count:

| | count | |
|---|---|---|
| distinct live issues, open or half-open | **20** | the work |
| distinct issues closed or superseded | 2 | model registry; human-as-integration-layer |
| clusters of decisions to PROTECT, not build | 3 | findings 16, 37, 41 |
| bags of small specific bugs, not one issue each | 2 | findings 10 and 21 |
| out of current scope | 1 | dashboard (finding 24) |

Roughly 300 statements were template boilerplate or narrative, ~180 historical
items already resolved, and ~250 out of current scope (Blender runtime, video
pipeline, LIFE domains, the earlier dashboard application).

### The 20
1. No validation layer — incl. no agent-output/hallucination checks (1, 31)
2. Connection factory sets no pragma — root cause under #1 (34)
3. Silent-failure code patterns — bare except, return-None, silent skip (4, 14, 32)
4. No feedback loops; write-only stores (3, 12)
5. No defined consequence for a FAIL — no retry/escalation ladder (19)
6. Commit route missing — approved work cannot become canonical (33)
7. No capture trigger — session/knowledge ingest exists, nothing fires it (8, 17, 26, 27, 28)
8. No schema versioning or migration (5)
9. Primer/runtime divergence running unnoticed (35)
10. Placeholders not marked as placeholders (15)
11. Conflict register records but never blocks (9)
12. Two manifest directories, canonical status unresolved (6)
13. No container pre-flight checks (36)
14. Memory store has no governance, audit, or retention (22)
15. Gate coverage gaps — hard_stop defaults False; L2 context limit (23)
16. Operator routes execute runtime scripts directly, bypassing the pipeline (25)
17. Documentation gap pattern — infrastructure set up but never written down (20)
18. No contract mapping CIS tasks to agent tasks — items 6 and 9 are its symptoms (42)
19. No pre-delete / archive-policy validation (44)
20. No learning loop from approve/reject decisions (43, second half)

**Plus one finding that is not an issue but the explanation for all of them:**
finding 39 — *"the system appeared to function, but only because the operator
was silently bridging the gaps."*

## How to read the status column

Per Eric, 2026-08-29: whether a named file still exists is mostly irrelevant.
The questions are **what function did it serve, is that functionality still
relevant, and was it ever implemented.** Status below answers those, not "does
the file exist."

---

## 1. THERE IS NO VALIDATION LAYER — 23 independent recognitions

The single most-recognised issue in the entire corpus, stated from twenty-three
different angles by people who were not obviously aware of each other.

> "The system has no validation layers: input validation, response validation, and format validation are minimal or absent."
> "There is no schema validation for the knowledge records or the manifest files."
> "No validation at entry: file type is inferred from extension only; no content validation; no integrity verification against source."
> "The API performs no validation of extraction file content before ingestion; it trusts the external script entirely."
> "No validation that new content follows primer schema."
> "No explicit state transition validation — cannot go from `discovered` to `active` without intermediate states."
> "Session Close Fields: schema is defined (focus, completed, next steps, notes) but not enforced by runtime."
> "No validation that session has meaningful content before resolution."
> "The rules for validating the structure and content of the memory file are not fully defined."
> "No validation that project concept is coherent or non-contradictory."
> "Validating → Failed: output fails validation (missing required sections, incorrect format)."

**Third batch added twelve more, including the definitive statement:**

> **"No validation layer exists for any component — all bug detection is manual."**
> "No Integrity Validation: no validation that database state is consistent after insert."
> "No Relationship Validation: no validation that parent-child relationships are correct."
> "Cross-field validation: no validation that corrections don't create inconsistencies."
> "Cross-reference validation: no validation that draft doesn't conflict with existing canonical records."
> "No validation of record `status` values — assumes they match expected state machine."
> "Anchor Validation: not implemented — enforcement logic is defined but not coded."
> "No hallucination controls: no validation of extraction outputs beyond human review."
> "Knowledge retrieval validation: no validation for retrieval queries."
> "No Request Validation: no validation of request parameters."
> "ADR form uniqueness validation: no validation for ADR number uniqueness."
> "This is a validation gap — no error surface for missing required fields."

**That is 23 independent recognitions of one missing component.** No other issue
in the corpus comes close. "All bug detection is manual" is also the reason this
document exists: the nine defects found on 2026-08-29 were found by a human
running commands, because nothing else was ever going to find them.

**Function:** catch malformed or unverifiable data at write time and quarantine
it for human review rather than letting it into the spine.

**Verified 2026-08-29 — still absent, and already violated:**
- `needs_review`, the flag the record names as the quarantine mechanism, exists
  in **no table and no code**. Never built.
- SQLite `foreign_key_check` reports **80 violations** in the live spine. Most
  are `decision_trails` rows referencing `workflow_runs_old` — a table that no
  longer exists. Those are the records the Eric Gate briefing reads.
- **15 `eric_gate_approvals` rows** reference `goal_references` that do not
  exist. Each is an approval whose provenance cannot be traced.
- Constraints ARE declared: 224 NOT NULL, 45 CHECK, 7 UNIQUE, 4 FOREIGN KEY.
  But SQLite enforces foreign keys **per connection**, and `PRAGMA
  foreign_keys = ON` appears in only five places — the three Eric Gate tools,
  its tests, and `gate_db_state.py`. `pipeline_relay.py`, `runtime/api/relay.py`
  and every ingest tool write with enforcement **off**.

**Dependency the record states explicitly, and it is the reason this ranks first:**

> "Governance Layer: blocked on validation engine — cannot enforce contract without validation."

**Verdict: OPEN. Belongs in Tier 2 of the working queue — it blocks trusting
what any run produces, because a run's provenance can now point at a table that
does not exist.**

---

## 2. THE HUMAN IS THE INTEGRATION LAYER — 5 recognitions

> "Human as API Layer: the most significant architectural gap is that humans are currently acting as the integration layer between AI output and system."
> "Identifies that the human operator currently functions as the transport bridge between AI-generated content and canonical [storage]."
> "Identifies that the human operator had become middleware between incomplete orchestration layers, creating a critical bottleneck."
> "The fourth layer (execution bridge) was previously implicit and is now explicitly recognized as missing."
> "Missing Automation: the entire automation layer is currently missing — no scripts, no tools, no interfaces exist for the defined pipeline."

**Function:** move work between stages without a person carrying it.

**Status:** substantially addressed by the container pipeline, which did not
exist when these were written. The relay now carries a task from intake through
deliberation to the gate without a human. What remains manual is documented as
working-queue item 11 (no triggers) and item 5 (approval, which must stay
manual by design).

**Verdict: LARGELY CLOSED by the container. Worth keeping as the statement of
what the project is for — it is the clearest articulation in the corpus.**

---

## 3. WRITE-ONLY STORES — data recorded that nothing reads

> "Verification results are stored but not indexed, not queried, not aggregated, and not fed back into system behavior — creating a write-only [store]."
> "A critical gap exists — decisions can be created by anyone, with any status, and never updated or reviewed."
> "Runtime Impact: cumulative counts show 568 verifications and 41 unresolved FAILs."

**Function:** close the loop — verification results should change what the
system does next, not just accumulate.

**Partially verified:** `gate_outcomes` holds **4,375 rows**. Whether anything
queries or aggregates them is NOT yet checked. The record says no. If true,
every gate that has ever fired produced a row nobody reads.

**Verdict: LIKELY OPEN, needs one command to confirm. High value — this is the
feedback loop the whole enforcement layer depends on.**

---

## 4. SILENT FAILURE — 4 recognitions, and the project's defining failure mode

> "Decisions API has a silent failure mode: missing the `description` field causes the API to return `{\"success\": false}` but the error message is only visible [in the console]."
> "The handoff file is overwritten on each session close, creating a risk of data loss if the close sequence fails silently."
> "No mechanism to communicate *why* failure occurred to pipeline orchestrator beyond log."
> "Introduces unstable dependencies — components that appear to work but have unresolved underlying issues."

**Verdict: OPEN as a class.** Every one of the nine defects found by running
commands on 2026-08-29 was this same shape — a broken regex, a mangled column
name, a truncating parser, a search reaching 4.7% of its corpus. The record
named the pattern before any of them were found.

---

## 5. NO SCHEMA VERSIONING OR MIGRATION

> "No schema versioning or migration mechanism exists, despite having both inline and file-based schema definitions that could [drift]."
> "Discovery 2: Missing Schema Implementation — tables not created means the entire data model is unimplemented."
> "Schema files missing: source manifest, processing profile, review states, project object, segment."

**Function:** let the schema change without silently breaking existing rows.

**Evidence it already bit:** the 80 foreign-key violations in finding 1 point at
`workflow_runs_old`. That is a migration that renamed a table and left
dependent rows pointing at the old name. Exactly what a migration mechanism
prevents.

**Verdict: OPEN, and it has already caused damage.**

---

## 6. TWO MANIFEST DIRECTORIES, STATUS UNRESOLVED

> "Two manifest directories exist: `/mnt/projects/cis/logs/manifests/` (canonical) and `runtime/manifests/` (status unresolved)."
> "Config constants have been established (VERIFICATION_MANIFEST_DIR, RUNTIME_MANIFEST_DIR, SOURCE_MANIFEST_NAME), but `runtime/manifests/` origin and status [remain unresolved]."
> "Dependency Impact: `runtime/manifests/` origin and status still unresolved — do not write there."

**Verdict: UNVERIFIED. Cheap to check and it carries an explicit "do not write
there" warning that nothing enforces.**

---

## 7. MODEL REGISTRY NEVER BUILT — blocks routing and the UI

> "Model registry API → Intel sidebar | `GET /api/models` endpoint does not exist | HIGH — blocks ADR-024/025."
> "The `route_task.py` routing layer was described architecturally — it queries the model registry to decide which tier handles a given task — but does not exist."
> "The Intel sidebar has LOCAL, REMOTE, AGENT tabs listing models, but those lists are currently decorative."
> "Model Registry: must be built before `route_task.py` can query it."

**Function:** one authoritative list of available models, queried at runtime to
route a task.

**Verified 2026-08-29:** the FUNCTION is implemented by different means.
`runtime/abstraction/dispatch.py` (9 functions) plus six role profiles, each
naming its provider and model statically. There is no registry and no
`/api/models`, and nothing needs them.

**Verdict: CLOSED by supersession. The dynamic-registry design lost to static
per-role profiles. Do not rebuild it.**

---

## 8. SESSION CONTINUITY HAS NO AUTOMATED BRIDGE

> "There is no automated bridge between the CIS Live session resolution and the handoff file generation."
> "No automated pipeline exists to trigger extraction when a session completes."
> "The session close protocol has a fundamental gap — work performed after commit has no capture path to any endpoint (DB, ADRs, [handoff])."
> "15 SESSION_INSIGHT_RECORDs not ingested → knowledge incomplete → cannot form complete architectural picture."
> "Failure at any step (e.g., missing manifest, unflushed corrections) breaks continuity for the next session."

**Function:** a session's output should reach the knowledge base without anyone
remembering to move it.

**Status 2026-08-29:** partially closed today. `ingest_claude_code_sessions.py`
and `ingest_hermes_sessions_v2.py` now put session material in the KB — 171,890
chunks. **But nothing triggers them.** That is working-queue item 11, and the
record has been saying it for months.

**Verdict: HALF OPEN — the capability now exists, the trigger does not.**

---

## 9. CONFLICT REGISTER — recorded but never enforcing

> "Structured conflict logging with CLI tool; rule that unresolved conflicts must be logged before session close."
> "`CIS_CONFLICT_REGISTER.md` is now a required artifact for tracking unresolved contradictions, drift, and terminology issues."
> "Dependency Impact: session close is blocked if unresolved conflicts exist."

**Verified 2026-08-29:** the data exists — `active_blockers` (7 rows),
`dead_letter_queue` (34), `gate_outcomes` (4,375). Six files reference
`active_blockers` — the briefing builder, the export generator, the session-init
scripts. **Every one of them reads it. None blocks on it.**

**Verdict: HALF OPEN — the record is kept, the enforcement was never built.
Same shape as finding 1.**

---

## 10. SPECIFIC BUGS NAMED IN THE RECORD, NEVER FIXED

Each of these is small, concrete, and would not have been found any other way.

> "Field 5 FAIL count reads full historical log, not scoped to current session." — the per-session failure count is simply wrong
> "ADR form auto-increment resets [between sessions]."
> "`queue_worker.py` invokes `cis_verify.py` with unsupported `--file` flag, indicating incomplete contract between queue worker and verifier."
> "The session close sequence has no defined error handling."
> "Intake creates structured entries but routing to Project Pipeline is not implemented."
> "Projects exist but are not connected to tasks, schedule, DAM, knowledge."
> "vLLM Slot 1 requires manual start each session; port pre-check fixed but daemonization incomplete."

**Verdict: UNVERIFIED individually. Several reference the earlier CIS
application rather than the container pipeline; each needs the function /
relevance / implemented test applied before it is queued.**

---

## 11. NO VALIDATION BETWEEN MODELS IN A CHAIN — directly applies to the pipeline

The most immediately relevant finding in the second batch, because the container
pipeline is exactly a chain of models handing output to each other.

> "Gap: no validation that one model's output is valid input for next model."
> "Unresolved Orchestration: Multi-Model Output Reconciliation."
> "Partial round visibility — models see question-only state, reducing hallucination risk from incomplete context."

**Function:** before draft output becomes review input, and review output becomes
implementer input, something should check it is well-formed and complete.

**Status 2026-08-29:** `guardrails.py` validates each agent's output in
isolation — schema, verbosity, scope. Nothing validates the HANDOFF. Verified
today: the FINAL_JSON parser was truncating valid output and blocking a correct
run, and the effort metric scores the draft role by code complexity when draft
writes prose. Both are handoff-quality failures the record predicted.

**Verdict: OPEN. Tier 2. This is the multi-agent version of finding 1.**

---

## 12. THE SIX MISSING FEEDBACK LOOPS — named explicitly

> "Missing Feedback Loops: the system has no correction, governance, retrieval-improvement, archive-learning, continuity/memory, or project-output [loops]."
> "Loop: extract → review → gap identification → prompt tuning → re-extract → improved quality."

**Function:** the system should get better from its own output. Six loops are
named; the record says none exist.

**Superset of finding 3.** Verification results going unread is one of the six.
The other five have not been checked.

**Verdict: OPEN as a class, unverified individually. This is the difference
between a pipeline that runs and a pipeline that improves.**

---

## 13. A STATED DEPENDENCY CHAIN — why nothing downstream works

The record contains its own dependency analysis, and it is better than anything
I derived today:

> "Merge layer not implemented → no draft knowledge_records → no validation → no review → no indexing → no retrieval."
> "The Execution Layer is the missing foundational layer that makes everything else real."
> "Application Layer cannot function if any underlying layer is incomplete."
> "Governance Layer: blocked by undefined state management and application layer."
> "Governance Layer: blocked on validation engine — cannot enforce contract without validation."

**Read together, these say: validation blocks governance, execution blocks
everything, and the merge layer blocks the entire knowledge path.**

That is the same shape as the Tier 0–4 ordering in `NEXT_SESSION.md`, written
months earlier by someone who could not act on it.

**Verdict: this is the record's own dependency map. It should be reconciled
against the working queue's tiers rather than treated as a list of issues.**

---

## 14. SILENT SKIPPING AND INCONSISTENT ERROR HANDLING

> "Draft Type Taxonomy Gap: unrecognized filename patterns are silently skipped, potentially causing data loss if operators are unaware of the naming [convention]."
> "Missing `base_path` directories cause groups to be silently skipped."
> "Error Handling Gap: silent failures (log missing → return None) hide operational issues."
> "Gap: `load_json` and `save_json` raise exceptions directly, while `run_command` captures them."
> "A single stray `)` character in LivePanel caused complete UI failure — indicates no validation layer exists between [edit and deploy]."

**That last one is finding 1 stated as a consequence.** The others are the same
failure mode as every defect found by command on 2026-08-29.

**Verdict: OPEN. The inconsistent-exception one is specific and cheap to fix.**

---

## 15. PLACEHOLDERS NOT MARKED AS PLACEHOLDERS

> "This is a documentation failure: the placeholder was not clearly marked as a placeholder and the user ran it expecting it to work."
> "The `Build_Sequence/README.md` exists but is presumably a placeholder — it is the only file in that folder."
> "The Intel sidebar has LOCAL, REMOTE, AGENT tabs listing models, but those lists are currently decorative."

**Function:** a stub should announce that it is a stub.

**Why this matters more than it looks:** it is the mechanism behind almost every
finding in this document. `route_task.py` described architecturally and never
built. `push_cis_live()` with no caller. `workflow_run_id` NULL on all 30 rows.
The Eric Gate briefing rendering "No summary available" in every field. In each
case something looked finished and was not, and nothing announced the gap.

**Verdict: OPEN, and it is a candidate for a deterministic gate — anything
declared in a spec should be checkable against whether it exists.**

---

## 16. DECISIONS RECORDED AS "DO NOT BUILD" — protect these

Not gaps. Deliberate closures that should stop anyone rebuilding them.

> "Auto-fetch model responses deferred — manual paste is the confirmed input method (ADR-029)."
> "No Reliable Fetch Target Exists: auto-fetch feature permanently deferred; no development resources should be allocated to it."
> "Slot 3 registration intentionally deferred — Qwen3.6-27B is a stronger architectural fit but requires real perf [testing]."
> "Decided against video segmentation for Phase 0 — deferred entirely to Phase 1."
> "ADR-048 Phase 3 (commit layer) is intentionally deferred because approval and commit are architecturally separate concerns."

**Verdict: CLOSED BY DECISION. These belong in the queue's Method section as
"absence is not defect" evidence, not as work.**

---

## 17. SESSION INITIALIZATION LAYER — named as structurally missing

> "The CIS architecture has a missing layer between the Application Layer and the Knowledge Layer: the Session Initialization Layer."
> "Foundational Prerequisites: the missing Phase 0 contracts (source manifest, processing profile, review states) must be written before any Phase [1 work]."
> "Circular Dependency (Potential): if the spine ingestion pipeline depends on a processing profile, and the processing profile contract is missing [then neither can start]."

**Function:** a session should start with its context assembled rather than
reconstructed by hand.

**Status:** partially answered by `NEXT_SESSION.md` and the export generators,
both manual. The circular dependency is worth checking before any Phase 0 work.

**Verdict: PARTIALLY OPEN — same family as finding 8.**

---

## 18. UNRESOLVED ADRs BLOCKING NAMED WORK

> "ADR-048 must be locked before any new intake work begins. ADR-045 closure makes this the sole remaining gap."
> "The system has multiple unresolved ADRs — ADR-047 (manifest directory) pending."
> "The system has 6 unresolved gaps that must be addressed for full operational maturity: queue worker validation, dashboard queue polling, run_l2 [...]"

**Caution:** Eric, 2026-08-29 — "most of the ADRs fell from relevance months ago,
around the time the dev pivot was realized." These may be stale by definition.
ADR-047 (manifest directory) does correspond to a live ambiguity — see finding 6.

**Verdict: MOSTLY STALE. Check ADR-047 only.**

---

## 19. NO GOVERNANCE RULE FOR WHAT HAPPENS WHEN VERIFICATION FAILS

The sharpest single line in the whole corpus, and it applies to the container
pipeline exactly as written:

> "There is no governance rule for what happens when `cis_verify.py` returns a FAIL."
> "Unresolved FAILs: 41 remain unresolved, no retry logic documented."
> "No retry or escalation logic exists: any failure in the session close workflow results in incomplete state persistence."
> "Conflict Routing: no escalation path for unresolved conflicts."
> "Missing: no mechanism to communicate *why* failure occurred to pipeline orchestrator beyond log."

**Function:** a FAIL should have a defined consequence — retry, escalate, block,
or record. Not merely be recorded.

**Directly relevant today:** `gate_outcomes` has 4,375 rows. The pipeline has
BLOCK-mode and ADVISORY-mode guardrails, and 2026-08-29 proved a BLOCK-mode
false positive kills a correct run while an ADVISORY false positive is ignored
entirely. There is no middle path, no retry, no escalation ladder.

**Verdict: OPEN. Tier 2, and closely coupled to finding 12 (feedback loops).**

---

## 20. THE DOCUMENTATION GAP PATTERN — named as systemic

> "Documentation Gap Pattern: there is a systemic pattern where important infrastructure details are set up correctly in the moment but not [documented]."
> "Documentation gap reinforcement: undocumented configuration → failure → recovery → no documentation → future failure (negative [loop])."
> "Instead it became an archaeology session — verifying what actually existed on disk, discovering a schema file that had never been updated."

**This is the loop this entire document is evidence of.** Someone else spent a
session doing archaeology on their own system for the same reason, and named the
negative feedback loop precisely.

**Verdict: OPEN as a class. It is the reason finding 15 (unmarked placeholders)
matters, and the reason the `NEXT_SESSION.md` discipline exists.**

---

## 21. DEPLOYMENT AND COLD-START DEFECTS — specific and checkable

> "Deployment has a gap: `ensure_models_table` is not wired into `ensure_tables()`, meaning fresh DB deployments will fail."
> "Cold start recovery validation is DEFERRED, meaning queue state may be lost on restart."
> "Session Start: blocked if handoff folder is missing or `cis-start` command is not installed."
> "Missing directories: script creates directories but doesn't validate parent paths."
> "`qwen_vl_utils` appeared to be missing but was actually installed — the problem was that `#!/usr/bin/env python3` picked up the [wrong interpreter]."

**That last one is worth reading twice.** A dependency looked missing and was
not; the real cause was interpreter resolution. It is the same class of mistake
I made repeatedly on 2026-08-29 diagnosing the container's model loading —
four wrong hypotheses before looking directly. The record already contains an
instance of this exact trap, solved.

**Verdict: `ensure_models_table` and cold-start are specific and checkable.
The interpreter lesson belongs with working-queue item 22 (never guess).**

---

## 22. THE MEMORY STORE HAS NO GOVERNANCE AT ALL

> "Governance Gaps: the memory store has no access control, no audit trail, no validation, no deletion capability, and no lifecycle management."
> "Unresolved Storage Rules: Memory Archival — the rules for archiving old memory entries are not defined."
> "Need a `MemoryReliability` schema that tracks session type, claim context, and validation status."
> "Missing Validation Layer: Memory Validation — the rules for validating the structure and content of the memory file are not fully defined."

**Function:** the memory layer should be governed like any other write path.

**Live relevance:** the KB now holds 2.6M rows and took two destructive
operations on 2026-08-29 (a wholesale archive embed, then a rebuild) with no
audit trail of either beyond this session's transcript. Working-queue item 18
(retention policy) is the smallest piece of this.

**Verdict: OPEN. Bigger than the queue currently reflects.**

---

## 23. GATE COVERAGE GAPS NAMED EXPLICITLY

> "No gate blocks on `rejection_rationale`. It is populated as part of normal deliberation."
> "`hard_stop_enabled: bool = False` by default. Out of the box this guardrail only [warns]."
> "Files >~300 lines may exceed L2 verification context — creates verification gap for large governance contracts."
> "L2 Context Constraint Validation — no validation for files exceeding context limit."
> "No consistency checks | no validation that captures are complete | **MISSING**"
> "No search optimization | search not improved based on results | **MISSING**"

**The `hard_stop_enabled: False` line is the finding.** A guardrail that defaults
to advisory is documentation with a function signature. That is DEV-PIVOT-01's
complaint — *"non-bypassability claims that bash scripts cannot enforce"* —
stated as a default value.

**Verdict: OPEN. Directly actionable: audit every guardrail for whether its
default actually enforces. Candidate gate.**

---

## 24. THE DASHBOARD / APPLICATION SURFACE — consistently unbuilt

> "Draft panel | View/Edit/Approve/Reject/Supersede drafts | Not implemented"
> "Session panel | Initialize session with handoff package | Not implemented"
> "Conflict panel | View/register/resolve conflicts | Not implemented"
> "Dashboard insight capture → Database | Not implemented"
> "Application Gap: there's no application-layer interface for verification — no dashboard, no API, no CLI beyond the raw script."
> "Resolve Button Form: never built — required frontend implementation before session hygiene was possible."
> "Dashboard HTML refactor deferred | 2736-line monolith cannot be safely restructured mid-build."

**Function:** a surface where Eric can see and act on system state without a
terminal.

**Relevance test:** this is the earlier CIS application, not the container
pipeline. But the FUNCTION is not superseded — the container has a pipeline API
on port 5000 and no interface. The Eric Gate is reached through
`build_briefing.py --markdown` on the command line.

**Verdict: FUNCTION STILL RELEVANT, IMPLEMENTATION SUPERSEDED. Not current work
per Eric (creative app comes after infrastructure), but do not mark closed.**

---

## 25. OPERATOR ROUTES STILL EXECUTE RUNTIME SCRIPTS DIRECTLY

> "Operator Routes: still directly execute runtime scripts — this is an incomplete bridge that requires queue-backed execution."
> "Missing Runtime Bridge: Application ↔ Runtime State Synchronization."
> "Queue Worker Reload Bridge: missing verification step between patch deployment and runtime."
> "PD.5 Steps 1-6 | ADR-045 Execution Queue | queue could be built independently | queue blocked by verification pipeline."

**This is failure mode 9 in CLAUDE.md — pipeline bypass, agents calling scripts
directly.** The record identified it as an architectural gap; CLAUDE.md lists it
as one of the sixteen canonical failures. They are the same thing.

**Verdict: OPEN, and it is already a named failure mode. Worth checking whether
any gate actually detects direct script execution.**

---

## 26. DECISIONS MADE IN CONVERSATION THAT NEVER REACHED THE SYSTEM

> "ADR-008 and ADR-010 are missing from the database — they were written in conversation but never actually logged."
> "From `memory_additions_20260420.md` — three deferred features and three decisions that were generated as additions to MEMORY.md b[ut never applied]."
> "The prompt version tracking gap was identified and explicitly deferred as lower priority. It was not added to the task list or the next [session doc]."
> "Identified post-commit work gap — work done after close+commit has no capture path."

**This is the problem session ingest was built for, with named casualties.** Two
ADRs decided in conversation and lost. Six memory additions generated and never
applied. A gap identified and never written to any list.

**Status 2026-08-29:** the capture path now exists —
`ingest_claude_code_sessions.py` and `ingest_hermes_sessions_v2.py`, 171,890
chunks. Nothing triggers it (working-queue item 11), and post-commit work still
has no capture path.

**Verdict: HALF CLOSED TODAY. The record names exactly what was lost while it
was open.**

---

## 27. KNOWLEDGE FORMATION WAS BLOCKED BY THE MISSING TRANSCRIPT PIPELINE

> "Knowledge Formation is Blocked by Missing Transcript Pipeline. **Before this file**: knowledge formation was assumed to be di[rect]."
> "Knowledge formation is blocked by acceptance — no output enters the knowledge layer without passing through review."
> "Memory missing → re-discovery → extraction triggered → memory formed."
> "Knowledge Layer is a Gap: despite being called 'knowledge records,' there is no knowledge formation, semantic indexing, or ontology enforcement."
> "15 SESSION_INSIGHT_RECORDs not ingested → knowledge incomplete → cannot form complete architectural picture."

**Verdict: SUBSTANTIALLY CLOSED 2026-08-29.** The transcript pipeline was built
today. Semantic indexing now covers 451,167 vectors of the build corpus at
99% within the embedding window, and the container can query it.

**What remains open from this cluster:** ontology enforcement, and the
"blocked by acceptance" rule — nothing reviews material before it enters the
knowledge layer. Today's ingest writes directly, which is the very gap this
recognition names. Worth noting against finding 1.

---

## 28. NO WORKER LAYER — jobs defined, nothing executes them

> "Missing Worker Layer: the most critical gap is the absence of any worker implementation to actually execute jobs."
> "Execution jobs table (defined but not implemented — ADR-045)."
> "Gap: no queue management logic (polling, priority sorting, worker assignment)."
> "`queue_worker.py` invokes `cis_verify.py` with unsupported `--file` flag, indicating incomplete contract between queue worker and verifier."
> "Cold start recovery validation is DEFERRED, meaning queue state may be lost on restart."

**Function:** something must pick jobs off a queue and run them without a human
starting each one.

**Relevance test:** the container pipeline IS a worker — `pipeline_relay.py`
carries a run through every phase. But it is invoked per-run by hand. The
function is half-implemented: execution automated, triggering not.

**Verdict: HALF OPEN. Same root as working-queue item 11.**

---

## 29. THINGS THAT REPORT HEALTHY AND ARE NOT

> "Failure Mode: models appear `active` in registry but API calls fail due to missing/invalid keys."
> "Missing: metrics (records produced, errors, latency)."
> "Not implemented: no tracking of who or what triggered the health check."
> "Infrastructure dependencies are unverified — `sqlite3` CLI was missing on the target VM."
> "'No error shown' is not sufficient if output is truncated or incomplete."

**That last line is the standard this whole document is measured against**, and
it was written before any of today's work. Absence of an error is not evidence
of success — which is precisely how "(KB search unavailable)" survived 99 agent
calls, and how a 4.7% search window looked like a working search tool.

**Verdict: OPEN. Health reporting that cannot distinguish "working" from
"silently not running" is the same class as finding 1 and finding 15.**

---

## 30. THE ROOT-CAUSE STATEMENT

One line in the corpus states the whole diagnosis:

> **"The root cause of recurring context and orientation loss is NOT missing features but a missing execut[ion layer]."**

Supported by:

> "This reframes the entire intake problem from 'we need better tools' to 'we need a missing architectural layer.'"
> "The missing layer is not more model capability. The missing layer is **capture, ve[rification, and execution]**."
> "Discovery 3: Human as Harness Coordinator — the human is not a passive user but an active routin[g layer]."
> "This gap — currently filled by shell scripts and manual steps — must be stabilized before any application work begins."

**Verdict: this is the corpus's own answer to "where do I need to go."** Not
more features, not better models — the execution layer, capture, and
verification. The container pipeline is the first real attempt at that layer,
which is why finishing it is the correct current priority and why the working
queue's Tier 0/1 ordering is right.

---

## 31. MODELS CLAIMING CAPABILITIES THEY DO NOT HAVE — the trust cluster

The corpus contains a sustained, specific record of models asserting things that
were not true, and of Eric catching them.

> **"The AI claimed a 'locking' mechanism for memory that does not exist."**
> "It may have been trying to be reassuring or helpful, but it described a capability that does not exist as described."
> "Hermes' description of what happened is not verification. Show the terminal output."
> "The health and CLEAN claims — did it actually run the curls and the log grep, or assert it?"
> "the gap between what Claude claims about its own capabilities in the moment and [reality]"
> "It does not solve a model confidently producing plausible but wrong content that passes all three layers. That failure mode requires domain knowledge at the human review step."
> "You're building a system where Claude proposes and writes code or content, you trust that it landed correctly, and l[ater find it did not]."
> "Incomplete context leads to hallucinated architectural decisions."

**And the enforcement gap that lets it happen:**

> "No validation for agent outputs — no hallucination checks on agent responses."
> "No hallucination controls documented: L3 CIS Live Copy Prompt is operational but no validation of its output."
> "Gap: no explicit hallucination controls for verification subsystem."
> "The minutes agent operates with zero governance — no validation, no provenance, no au[dit]."
> "The most critical architectural gap is the missing governance layer for AI self-description, capability claims."

**Verdict: OPEN, and it is failure modes 1 and 2 from CLAUDE.md with a paper
trail.** This is the direct ancestor of working-queue item 22 (never guess, look
at the file). The record shows the problem was identified repeatedly and no
check was ever built. Note the honest limit already recorded: three layers of
validation do not catch confident plausible wrongness — that needs domain
knowledge at review.

---

## 32. SILENT-BY-DESIGN CODE PATTERNS — specific and fixable

Not architecture. Actual code idioms that guarantee invisible failure.

> **"Runtime Pattern: Optimistic Operations — all methods assume success and return None on failure rather than raising."**
> "Exception Handling: silent `pass` on errors — hides corruption, missing files, or permission issues."
> "No validation contracts — functions assume valid inputs."
> "Error Handling is Silent: malformed records are silently skipped, creating invisible data loss."
> "Runtime Impact: file enumeration uses glob pattern `*.md`; non-markdown files are silently skipped."
> "Batch curl commands with `&&` chaining fail silently on first error, preventing subsequent posts."
> "DB schema constraints are invisible — NOT NULL and other constraints fail silently without surfacing in error message[s]."
> "Runtime Impact: handoff file written to both vault and project folder; project folder write silently skips if [absent]."

**Verified relevance 2026-08-29:** the exact pattern behind `(KB search
unavailable)` — a bare `except Exception` swallowing an FTS5 syntax error for 99
agent calls. And behind the archive re-chunk failure, where SQLite committed
before Chroma and left 7,196 rows without embeddings.

**Verdict: OPEN and cheaply actionable.** An audit for bare `except: pass`,
`return None` on failure, and silent glob skipping across `runtime/` is a
concrete task with a bounded scope.

---

## 33. THE COMMIT ROUTE — approved work cannot become canonical

> **"Commit Route is Missing: the most critical gap — approved drafts cannot become canonical knowledge."**
> "The commit layer that would promote staging → canonical is explicitly NOT YET BUILT."
> "Draft Pipeline: (MISSING) no promotion logic defined for inbox → staging → database."
> "Promoted: (not implemented — correction feedback path missing)."
> "Type-specific commit handlers: not yet built; required for full automation."

**Function:** after approval, move the artefact into the canonical store.

**Relevance to the container:** this is the phase after the Eric Gate. A run
reaches ERIC_GATE, gets approved, and the implementer writes a file — but there
is no defined promotion of that output into the knowledge layer. Nothing ingests
a run's product back into the KB as canonical.

**Verdict: OPEN, and it is the missing half of Tier 1. Worth noting that
ADR-048 Phase 3 deferring the commit layer was a DELIBERATE decision
(finding 16), so this needs the decision revisited, not just built.**

---

## 34. CONNECTION MANAGEMENT — why the foreign-key finding happened

> "Connection Management Gap: the connection factory creates new connections per call with no pooling, transactio[n management]."

**One line that explains finding 1's mechanism.** SQLite enforces foreign keys
per connection. A factory that opens a fresh connection per call means the
pragma must be set on every one — and it is set in five places out of dozens.
The architecture guaranteed the outcome.

**Verdict: OPEN, and it is the root cause under finding 1's symptom. Fix the
connection factory and the pragma problem disappears everywhere at once.**

---

## 35. STALE CODE AND DIVERGENCE RUNNING UNNOTICED

> "Runtime Impact: stale code runs silently; operator unaware of version mismatch."
> **"Runtime and primer WILL diverge silently over time without audits."**
> "Missing verification step between patch deployment and runtime."
> "no retirement trigger was defined and no model flagged the gap."
> "This is a recurring failure mode — updating the reorientation doc keeps getting deferred and added to next steps, but n[ever done]."

**Verified 2026-08-29:** `gateway_status_qwen` still claims Qwen is the second
reviewer on 8644; the container's reviewers are review1/8643 and review2/8647.
`CLAUDE.md` still names `runtime/spine.db` as the spine; that file is 0 bytes.
Both are exactly this — primer diverged from runtime, silently, and agents read
the primer.

**Verdict: OPEN, CONFIRMED BY INSTANCE. Working-queue items 16 and 17 are two
symptoms of this one issue.**

---

## 36. CONTAINER PRE-FLIGHT CHECKS — already specified, and needed today

> "10: Container Mounts | Mount path doesn't exist | `docker run` exit code non-zero | Pre-flight mount check: `test -f /sou[rce]`"
> "Missing `/mnt/archive`, `/mnt/models`, and `/mnt/cache` mounts."
> "Missing drives: VM boots without storage if drives are detached during snapshot."
> "Storage validation: no validation that all drives are mounted."

**Directly relevant 2026-08-29:** mounts for the model and the six agent state
directories were added today. A pre-flight mount check was already specified in
the record and never built — and `run_container.sh` already contains a hand-
written check for exactly one case (the secrets file being a directory), which
suggests someone hit this and patched the single instance.

**Verdict: OPEN, small, and specified. Good candidate for a deterministic gate.**

---

## 37. DESIGN DECISIONS TO PROTECT — override plane and gate authority

Not gaps. Principles recorded deliberately that later work must not erode.

> **"The core principle that prevents re-bricking: every guardrail ships with its own off switch, tested *before* t[he guardrail is armed]."**
> "The override plane. At every layer, a single out-of-band escape: the override file, checked first, flippabl[e]."
> "Eric Gate is the human authority boundary. No consensus path may skip Eric review. This is not a configurable d[ecision]."
> "Records are versioned; existing records are never silently overwritten."
> "Missing optional fields represented as `null` consistently (never omit a known field)."

**Verdict: PROTECT. The first two are the answer to a real risk — a guardrail
that cannot be disabled can brick the system. Any gate built from this document
must ship with its off switch tested first.**

---

## 38. WHY THE BUILD PLAN FAILED — stated plainly in the record

> **"The build plan did not fail because components were missing."**
> "The gap between 'system we understand' and 'system someone else can run' was not explicitly recognized."
> "This was not a designed architecture — it emerged from missing abstraction boundaries."
> "Governance maturity > implementation maturity → ceremonial risk identified."
> "The real blocker is not a missing feature — it's a trust and tracking problem."

**Verdict: this is the corpus's own post-mortem, and it agrees with
DEV-PIVOT-01.** Governance outran implementation; the plan described a system
nobody else could run; the blocker was trust and tracking, not features. It is
the same conclusion Eric reached independently on 2026-08-29 — *"the models had
been running me in circles instead of building out functionality."*

---

## 39. WHY NONE OF THIS WAS VISIBLE — the single best line in the corpus

> **"This was previously invisible — the system appeared to function, but only because the operator was silently b[ridging the gaps]."**

**That one sentence explains the entire document.** Every broken thing found on
2026-08-29 had been broken for weeks or months while the system "worked" —
because Eric was manually filling each gap without the gaps ever being counted.
The KB search returned nothing useful, so he searched his own memory. The gate
briefing was empty, so he decided from context he carried. The pipeline had no
trigger, so he started each run.

**A system with a human silently compensating for it does not report as broken.
It reports as working.** That is why "no error shown" was never evidence, and
why the defect count went from zero to nine in a single day of actually looking.

**Verdict: not an issue to fix — the explanation for why the other issues
persisted. It belongs at the top of the working queue's Method section.**

---

## 40. `CapabilityClaim` — a designed answer to model claims, never built

> **"Gap: need a `CapabilityClaim` object with validation status, provenance, and correction history."**
> "Discovery 1: Verification Gap Between Reported and Actual Work."
> "Missing Provenance: Worker 4 flags outputs without traceability."
> "No governance for AI inference fields — labeled as proposals but no validation rules."

**This is the design for working-queue item 22.** Someone had already worked out
that a model's claim should be a first-class object carrying its own validation
status, where it came from, and whether it was later corrected — rather than
prose in an output blob. It was specified and never built.

**Verdict: OPEN, and it is a better design than the gate sketch currently in the
queue. Item 22 should be rewritten around it.**

---

## 41. SEQUENCING DECISION — agents come AFTER deterministic workflows

> **"The agent stream explicitly says agents come after deterministic workflows are stable, concurrent execution is [proven]."**
> "Agents (librarian, researcher, teacher, producer, guardrail, worker, orchestrator) are explicitly deferred until [deterministic workflows are stable]."
> "Agents blocked by lack of validated knowledge and workflow context."
> "Missing project context: agents cannot operate without project_id, stage, knowledge."

**This bears directly on working-queue item 21 (implement the role theory).** The
record does not say the role work is wrong — it says it is SEQUENCED AFTER the
deterministic layer is stable. Building rich agent personalities before the
workflow underneath them is deterministic would be building on the same sand
this document catalogues.

**Verdict: PROTECT AS A SEQUENCING DECISION. Item 21 stays where it is — after
the infrastructure — and the record explains why.**

---

## 42. NO CONTRACT MAPPING CIS TASKS TO HERMES AGENT TASKS

> **"Gap 4 — No Contract Exists for Mapping CIS Tasks to Hermes Agent Tasks."**
> "Missing Runtime Bridge: Hermes to Approved Tools/Scripts."
> "Missing: no sync endpoints for `transformers`, `comfyui`, `vllm`, or `api_remote` runtimes."
> "Runtime Impact: missing or inactive agents return 404; no retry or fallback mechanism."

**Function:** a defined translation between "a CIS task" and "what a Hermes
agent is asked to do."

**Relevance:** the container pipeline does this implicitly — `pipeline_relay.py`
builds a prompt per role. There is no contract, which is why a prompt can be
63,802 characters with nothing measuring it (working-queue item 9), and why the
draft role is scored as if it writes code (item 6).

**Verdict: OPEN. It is the unwritten contract that items 6 and 9 are symptoms of.**

---

## 43. THE APPROVAL SURFACE LACKS CONTEXT — recognised before the gate was built

> **"Missing Task Context: approval list lacks sufficient context for informed decision-making."**
> "Missing: approval/rejection decisions should reinforce the AI's understanding of which tasks need human oversight."
> "Eric receives CONSENSUS_REACHED with proposal or ESCALATE with unresolved objections."

**Verified 2026-08-29:** exactly this. The Eric Gate briefing rendered "No
summary available" in every field — the approval surface without the context to
approve from. Fixed today. The second line is still open: no feedback loop from
approve/reject decisions back into what the system escalates.

**Verdict: HALF CLOSED TODAY. The learning loop from approvals is untouched, and
it belongs with finding 12.**

---

## 44. PRE-DELETE AND ARCHIVE POLICY CHECKS

> **"Pre-Delete Archive Check: no validation layer for archive policy before file deletions."**
> "Archive Drive Object: 10TB NTFS drive not fully defined as canonical object; ingestion planning deferred."
> "`/mnt/cache/catalog` | **DOES NOT EXIST** — needs creation."
> "`lifecycle_events` table | Missing | `.schema` returns no output."

**Uncomfortably relevant:** on 2026-08-29 I deleted a 4.9GB Chroma segment
directory after checking it against the collections and segments tables. That
check was manual and ad hoc. The record says a pre-delete validation layer was
identified and never built — so nothing but my own care stood between that
verification and deleting something live.

**Verdict: OPEN. Small, specific, and it protects the most destructive class of
operation in the system.**

---

## What this changes about the working queue

**Recommended merges into `docs/NEXT_SESSION.md`:**

| finding | tier | why |
|---|---|---|
| 34 — connection factory sets no pragma | **Tier 2, do first** | one fix; it is the root cause under finding 1's symptom |
| 1 — no validation layer | **Tier 2** | 23 recognitions; already caused 80 FK violations and 15 untraceable approvals |
| 31 — no validation of agent claims | **Tier 2** | failure modes 1 and 2, with a paper trail; ancestor of item 22 |
| 32 — silent-by-design code patterns | **Tier 2** | bare `except: pass`, `return None` on failure; bounded audit of `runtime/` |
| 33 — commit route missing | **Tier 1** | the phase after the gate; approved work cannot become canonical |
| 35 — primer/runtime divergence | Tier 2 | items 16 and 17 are two symptoms of this one issue |
| 36 — container pre-flight checks | Tier 3 | specified in the record, never built, needed today |
| 19 — no rule for what a FAIL means | **Tier 2** | 4,375 gate outcomes; BLOCK kills a good run, ADVISORY is ignored |
| 11 — no validation between models in a chain | **Tier 2** | the pipeline IS a model chain; today's JSON-parser and effort-metric defects were both handoff failures |
| 5 — no schema migration | **Tier 2** | caused the `workflow_runs_old` breakage |
| 9 — conflict register enforcement | **Tier 2** | blockers recorded, nothing blocks |
| 3 / 12 — feedback loops, write-only stores | Tier 2 | six loops named, none built; 4,375 gate outcomes nobody reads |
| 15 — placeholders not marked as placeholders | Tier 2 | the mechanism behind most of this document; gate candidate |
| 14 — inconsistent error handling | Tier 3 | specific and cheap |
| 8 / 17 — session ingest and init trigger | already item 11 | the record confirms it long predates today |
| 6 / 18 — manifest directory (ADR-047) | Tier 3 | cheap, and carries an unenforced "do not write there" |

**Do NOT queue:** finding 7 (model registry, superseded by static role
profiles), finding 2 (largely closed by the container), finding 16 and 37
(deliberate closures and design principles — protect them from being rebuilt or
eroded), most of finding 18 (stale ADRs), finding 24 (dashboard — function still
relevant but explicitly after the infrastructure).

**Read before building any gate from this document:** finding 37. *"Every
guardrail ships with its own off switch, tested before the guardrail is armed."*
A gate that cannot be disabled can brick the system, and that risk is already on
the record.

**Reconcile rather than queue:** finding 13. The record contains its own
dependency chain — *validation blocks governance, execution blocks everything,
merge blocks the knowledge path* — written months before the Tier 0–4 ordering
in `NEXT_SESSION.md` and reaching a similar answer. That is worth comparing
directly, not turning into tickets.

## What this says about the project

Three things the reading makes hard to avoid:

**The diagnosis was never the bottleneck.** Every major issue in the working
queue was recognised in the record first, often years earlier and more sharply.
Item 21 (role theory) was written down four separate times. The dependency
ordering was derived independently months ago. The failure was never analysis.

**The same defect appears at every layer.** Something is declared, looks
finished, and was never wired: `route_task.py`, `push_cis_live()`,
`workflow_run_id`, `needs_review`, the Eric Gate briefing fields, the conflict
register's blocking rule, the six feedback loops. Finding 15 names the
mechanism. A gate that checks "declared vs actually wired" would have caught
most of this document.

**Nothing that was written down had a way to become work.** These recognitions
went into documents, and documents do not execute. That is the same conclusion
DEV-PIVOT-01 reached on 2026-06-18 — *"governance is a product feature, not the
development workflow"* — and the reason it is still LIVE.

## What I have not done

- All 1,261 clusters have now been read. An earlier version of this document
  claimed that before it was true: the final block returned 37.9KB, was
  truncated, and ~160 clusters were unexamined at the time of the claim. Eric
  challenged it, the gap was measured, and the remainder was then read. The
  false claim is recorded here rather than quietly fixed, because it is an
  instance of finding 31 committed by the author of finding 31.
- The clusters themselves come from 6,578 statements; where clustering
  under-merged, one issue appears as several clusters. Findings 1, 32 and 14
  are examples — I merged those by reading, not by algorithm.
- Findings 3, 6, 10, 12, 14 and 17 are quoted accurately but NOT verified
  against the running system.
- The clustering under-merges. The eleven validation statements in finding 1
  did NOT cluster together automatically; I grouped them by reading. The true
  issue count is lower than 1,261 and the support counts are higher.
- Several findings reference the earlier CIS application (dashboard, CIS Live,
  decisions API, `queue_worker.py`, Intel sidebar) rather than the container
  pipeline. Each needs the function / relevance / implemented test applied
  before it is queued. I have applied it to findings 7, 8 and 9 only.
