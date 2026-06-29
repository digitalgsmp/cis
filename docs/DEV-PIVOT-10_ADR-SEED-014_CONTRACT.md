     1|# ADR-SEED-014 — Temporary Draft Initiation Contract Before Router/Tier 7R
     2|
     3|**Status:** REVIEWED (r1 objections resolved, pending Eric Gate approval)
     4|**ADR ID:** ADR-SEED-014
     5|**Date proposed:** 2026-06-14
     6|**Date reviewed:** 2026-06-15
     7|**Reviewed by:** V4 Reviewer (r1, port 8643) — 5 objections raised, all resolved
     8|**Proposed by:** V4 Reviewer (r1, port 8643) — see Provenance Note below
     9|**Supersedes:** None
    10|**Superseded by:** None (temporary bridge, superseded by Tier 7R Router when built)
    11|
    12|---
    13|
    14|## Provenance Note
    15|
    16|This ADR was initially drafted during a Reviewer-profile session (r1, port 8643)
    17|while the operator was diagnosing a role-boundary failure (BLK-SEED-005: gateway
    18|service auto-overwrite causing profile misbinding). The ADR's architecture emerged
    19|through iterative discovery against live schema evidence, with external advisor
    20|audit (ChatGPT, Claude) across multiple rounds.
    21|
    22|Eric explicitly waives the Drafter/Reviewer provenance defect for ADR-SEED-014 only.
    23|Reason: the ADR was challenged by the same r1 instance after role identity was
    24|confirmed, material defects were caught (false "transition demonstrated" claim,
    25|incorrect FK direction, missing idempotency, missing git-state policy), and all
    26|objections were resolved. Restarting from scratch on port 8645 would add friction
    27|without improving the underlying decision.
    28|
    29|This waiver does not create precedent. Future ADR/spec drafting must originate from
    30|V4 Drafter (port 8645) and be independently challenged by r1 (port 8643) before
    31|Eric Gate approval, per the established Drafter→Reviewer→Eric Gate pipeline.
    32|
    33|---
    34|
    35|## Decision
    36|
    37|Until the Router / Tier 7R initiation path is fully built, CIS will use a temporary
    38|manual TRIAGE contract for how a Drafter session begins:
    39|
    40|1. **Eric states the initiating intent** in plain language. Eric's stated intent is
    41|   sufficient authorization to open the temporary manual TRIAGE workflow_run. No
    42|   separate pre-draft approval step is required. The recorded intent text is
    43|   authoritative and must be preserved for Reviewer comparison against the Drafter
    44|   proposal. Eric Gate remains later in the pipeline for implementation approval.
    45|
    46|2. **A minimal initiation shim creates both identities.** A script
    47|   (`tools/pipeline/drafter_start.py`) accepts Eric's intent as input and creates:
    48|   - A `workflow_run_id` following the existing `run-<hex>` convention
    49|   - A `proposal_id` following the existing UUID convention
    50|   - The link between them (via `workflow_run_id` columns on `lifecycle_events`
    51|     and `dispatch_log` — see Design Choice 1 below)
    52|   - Idempotency: if Eric's intent text hashes to an already-active workflow_run,
    53|     returns the existing IDs instead of creating duplicates
    54|
    55|   This is the only path for creating a Drafter workflow run until Tier 7R Router exists.
    56|   `drafter_start.py` does not classify, route, or interpret the intent.
    57|
    58|3. **The Drafter receives both IDs plus a spine-derived session briefing** (via
    59|   `drafter_session_init.py`, defined in the Tier 11C specification). The Drafter
    60|   may draft the proposal from Eric's intent, current spine state, active decisions,
    61|   active blockers, and the approved build order.
    62|
    63|4. **The Drafter may not invent or materially alter the initiating goal.** If the
    64|   Drafter identifies a gap in the intent, it may flag it for Eric but must not
    65|   rewrite the goal to fill the gap.
    66|
    67|5. **External advisors may frame options, critique, or analyze**, but they may not:
    68|   - Author the authoritative proposal content
    69|   - Create the initiating intent
    70|   - Create the workflow_run or proposal
    71|   - Write FINAL_JSON blocks
    72|   - Insert lifecycle_events or dispatch records
    73|
    74|   The advisor-framing-not-authoring boundary is primarily a governance convention.
    75|   It is not fully technically enforceable — a motivated Drafter could paste
    76|   advisor-authored text verbatim and no automated gate would catch it. The
    77|   following minimum mechanisms provide partial enforcement:
    78|
    79|   - `drafter_start.py` records Eric's exact intent text in `workflow_runs.topic`
    80|     as the authoritative initiating source.
    81|   - `drafter_closeout.py` logs a hash of the Drafter output.
    82|   - The Reviewer is instructed to compare the Drafter proposal against Eric's
    83|     recorded intent and challenge material drift.
    84|   - Eric Gate remains as the final human reconciliation point.
    85|
    86|   Full automated "advisor similarity detection" is not required for Tier 11C.
    87|   Clause 5's primary enforcement is the existing triangulated review model:
    88|   Drafter authors, Reviewer challenges, Eric reconciles.
    89|
    90|6. **Reviewer challenge begins only after Drafter emits a valid FINAL_JSON** with
    91|   `role: "drafter"` and `status: "PROPOSAL_READY"`.
    92|
    93|---
    94|
    95|## Deliberated Design Choices
    96|
    97|### Choice 1: Proposal identity vs. workflow identity
    98|
    99|**Fact:** The existing code (`runtime/api/orchestration.py:119`, `runtime/api/advisor.py:1250`)
   100|already uses separate namespaces:
   101|- `proposal_id` = UUID, used in `lifecycle_events`, `dispatch_log`, `dispatch_events`
   102|- `workflow_run_id` = `run-<hex>`, used in `workflow_runs`
   103|
   104|There is currently no column joining them. The Flask API creates both in the same
   105|call but the link exists only in the HTTP response, not in the database.
   106|
   107|**Options considered:**
   108|
   109|- Option A: Collapse them (`proposal_id = workflow_run_id`).
   110|  Rejected. Would create semantic collision — `run-<hex>` values in columns designed
   111|  for UUIDs. Creates future migration cleanup when the Flask API resumes writing UUIDs.
   112|
   113|- Option B: Separate identities with no recorded link.
   114|  Rejected. Session-coincidence is not a link — `drafter_session_init.py` and
   115|  `drafter_closeout.py` cannot answer "what workflow_run does this lifecycle belong to?"
   116|
   117|- **Option C (chosen): Separate identities with explicit recorded links on the many side.**
   118|  One workflow run produces many lifecycle events and many dispatches. The link
   119|  belongs on the many side: `workflow_run_id` on `lifecycle_events` and `dispatch_log`.
   120|  Two nullable TEXT columns. No FK required (proposals table doesn't exist yet per
   121|  migration 0011 comment, and `proposal_id` remains the lifecycle primary key).
   122|
   123|**Decision:** Honor the existing separate-identity architecture. Add nullable
   124|`workflow_run_id` columns to the two many-side tables. The migration is:
   125|```sql
   126|ALTER TABLE lifecycle_events ADD COLUMN workflow_run_id TEXT;
   127|ALTER TABLE dispatch_log ADD COLUMN workflow_run_id TEXT;
   128|```
   129|
   130|`drafter_start.py` creates the workflow_run_id and proposal_id, then writes
   131|`workflow_run_id` into each lifecycle event and dispatch row it creates.
   132|Downstream scripts query lifecycle directly by workflow_run_id, or join:
   133|`SELECT * FROM lifecycle_events WHERE workflow_run_id = ?`.
   134|`proposal_id` remains the lifecycle primary identifier — `workflow_run_id`
   135|is a denormalized join key for convenience.
   136|
   137|### Choice 2: Lifecycle events as canonical state machine (no new column on workflow_runs)
   138|
   139|**Fact:** `lifecycle_events` exists (migration 0011) but contains zero rows. The state
   140|machine is enforced in code by `transition_state()` which validates against
   141|`ALLOWED_TRANSITIONS` before writing. The table has never been operationally exercised.
   142|
   143|**Decision:** `lifecycle_events` is the canonical draft/review state machine.
   144|`workflow_runs.status` remains coarse-grained (COMPLETE/PENDING/ERROR) and is not
   145|used for intermediate draft/review transitions. No `draft_status` column is added.
   146|
   147|**Required states (from the existing ALLOWED_TRANSITIONS in orchestration.py):**
   148|
   149|| Transition | Meaning |
   150||---|---|
   151|| IDLE → ROUTING | Intent received, routing begins |
   152|| ROUTING → DRAFTING | Drafter session active |
   153|| DRAFTING → DRAFT_READY | Proposal complete, FINAL_JSON validated |
   154|| DRAFT_READY → REVIEW_PENDING | Dispatch created, awaiting Reviewer |
   155|
   156|These state names are not invented — they are the existing constants from
   157|`runtime/api/orchestration.py` lines 21-71.
   158|
   159|### Choice 3: Write through the existing state machine, not raw SQL
   160|
   161|**Decision:** `drafter_start.py` and `drafter_closeout.py` must write lifecycle
   162|events through `transition_state()` (or a validated CLI-safe wrapper) rather than
   163|inserting rows directly. This ensures the ALLOWED_TRANSITIONS validator is the
   164|single enforcement point, preventing the state machine from forking into two writers
   165|with different rules.
   166|
   167|**Verification required before Tier 11C implementation:** Tier 11C must verify
   168|whether `transition_state()` (`runtime/api/orchestration.py:138`) is safely
   169|callable from a terminal script without importing the full Flask application
   170|context. If it requires Flask context, Tier 11C must provide one of:
   171|- A small CLI-safe wrapper that exposes the same validation
   172|- A shared validation helper extracted from `orchestration.py` into a standalone module
   173|- Explicit replication of the validation logic (least preferred)
   174|
   175|State-transition rules must not be duplicated in two places. One validator, one
   176|source of truth, callable from both Flask and terminal contexts.
   177|
   178|The existing `transition_state()` function (`orchestration.py:138`) accepts:
   179|```python
   180|transition_state(proposal_id, session_id, from_state, to_state,
   181|                 initiated_by, gate_type=None, dispatch_ref=None,
   182|                 evidence_ref=None, reviewer_message_id=None,
   183|                 directive_hash=None, eric_approved=0,
   184|                 eric_bypass=0, revision_count=0, notes=None, db=None)
   185|```
   186|
   187|### Choice 4: Eric's stated intent as sufficient authorization
   188|
   189|**Decision:** Eric stating the intent is sufficient to open the temporary manual
   190|TRIAGE workflow_run. No separate pre-draft approval step is required. Adding one
   191|would recreate the friction Tier 11C is designed to remove.
   192|
   193|The authority boundary is preserved by:
   194|- `drafter_start.py` recording Eric's exact intent text as the authoritative source
   195|- The Drafter being prohibited from materially altering it (clause 4)
   196|- The Reviewer challenging any drift between intent and proposal (clause 6)
   197|- Eric Gate remaining as the later implementation approval gate (not collapsed into initiation)
   198|
   199|### Choice 5: Git-state policy for session init and closeout
   200|
   201|**Decision:** Three-phase git-state handling:
   202|
   203|| Phase | Script | Policy |
   204||---|---|---|
   205|| Initiation | `drafter_start.py` | Warns on dirty tracked files and untracked files. Does not refuse. Records git HEAD for provenance. |
   206|| Session start | `drafter_session_init.py` | Warns on dirty/untracked state. Does not refuse. Reports git HEAD and dirty file list in briefing. |
   207|| Closeout | `drafter_closeout.py` | **Refuses** closeout if untracked files exist. Warns on dirty tracked files. Closeout is the enforcement point. |
   208|
   209|This keeps initiation permissive (the operator may have intentionally open work)
   210|while making closeout strict (no uncommitted artifacts escape the session).
   211|Human cleanup of untracked files is required before closeout can proceed.
   212|
   213|---
   214|
   215|## Rationale
   216|
   217|### Why this is needed now
   218|
   219|The designed CIS pipeline (TRIAGE → Router → Orchestrator → Drafter) assumes Router
   220|creates workflow_runs. But Tier 7 (Router) is deferred. The current operational path
   221|is Eric opening terminal sessions manually. Without this contract:
   222|
   223|- Drafter sessions begin through implicit context and manual paste.
   224|- No authoritative record exists for how a draft began.
   225|- The `lifecycle_events` table exists but has never been exercised — the state machine
   226|  is structural, not operational.
   227|- External advisors have no explicit boundary.
   228|- `proposal_id` and `workflow_run_id` are created in the Flask API but not joinable
   229|  in the database.
   230|
   231|### Why the boundary clause matters
   232|
   233|Evidence from this session: External advisors (ChatGPT, Claude) provided substantive
   234|framing before the Drafter began drafting this ADR. Clause 5 codifies: advisors
   235|critique and frame, but the Drafter authors. Without this clause, the line between
   236|"advisor framed options" and "advisor authored the proposal skeleton" is invisible.
   237|
   238|### Why separate identities with a recorded link
   239|
   240|The existing code already chose separate namespaces. Collapsing them for the
   241|temporary bridge would create semantic collision (mixed ID formats in lifecycle_events)
   242|that becomes cleanup debt when the Flask API resumes. Adding nullable
   243|`workflow_run_id` columns to the two many-side tables is the least invasive way to
   244|make the link queryable without forking from the intended architecture.
   245|
   246|### Why temporary
   247|
   248|This contract is a bridge to Tier 7R Router. When the Router is built, it replaces
   249|`drafter_start.py`. This ADR will be superseded. It must not expand into full router
   250|implementation, intent classification, project promotion, or generalized workflow
   251|automation.
   252|
   253|---
   254|
   255|## Schema Change Required
   256|
   257|Migration for Tier 11C prerequisite (new file: `runtime/schema/migrations/0012_workflow_run_link.sql`):
   258|
   259|```sql
   260|-- Migration 0012: Add workflow_run_id to lifecycle and dispatch tables
   261|-- Prerequisite for ADR-SEED-014 (Temporary Draft Initiation Contract)
   262|-- Links the lifecycle state machine back to the durable workflow run.
   263|-- One workflow_run → many lifecycle_events, many dispatch_log rows.
   264|-- FK deferred — proposals and dispatches are independent namespaces per
   265|-- migration 0011 comment ("no proposals table exists yet").
   266|
   267|ALTER TABLE lifecycle_events ADD COLUMN workflow_run_id TEXT;
   268|ALTER TABLE dispatch_log ADD COLUMN workflow_run_id TEXT;
   269|```
   270|
   271|This is additive only. No existing rows modified. No existing queries break.
   272|`proposal_id` remains the primary lifecycle identifier. `workflow_run_id` is
   273|a denormalized join key for query convenience.
   274|
   275|---
   276|
   277|## Implementation Consequence for Tier 11C
   278|
   279|1. Tier 11C must include migration 0012 as a prerequisite (add `workflow_run_id`
   280|   to `lifecycle_events` and `dispatch_log`).
   281|
   282|2. Tier 11C must verify `transition_state()` terminal callability and provide a
   283|   CLI-safe wrapper if needed (see Choice 3).
   284|
   285|3. The Tier 11C state sequence becomes:
   286|
   287|   ```
   288|   Eric states intent
   289|        ↓
   290|   drafter_start.py:
   291|     - Hashes Eric's intent text for idempotency check
   292|     - If existing active run found, returns existing IDs (no duplicate)
   293|     - Creates workflow_run_id (run-<hex>)
   294|     - Creates proposal_id (UUID)
   295|     - Writes lifecycle events via transition_state(): IDLE → ROUTING → DRAFTING
   296|       (each with workflow_run_id set)
   297|     - Records Eric's exact intent in workflow_runs.topic
   298|     - Records git HEAD
   299|     - Warns on dirty/untracked git state
   300|        ↓
   301|   drafter_session_init.py briefs from workflow_run (spine + git state)
   302|   Warns on dirty/untracked state
   303|        ↓
   304|   Drafter produces proposal + FINAL_JSON
   305|        ↓
   306|   drafter_closeout.py:
   307|     - Refuses if untracked files exist
   308|     - Validates FINAL_JSON (role=drafter, status=PROPOSAL_READY)
   309|     - Logs hash of Drafter output
   310|     - Writes lifecycle event: DRAFTING → DRAFT_READY
   311|     - Creates dispatch_log row (REVIEW_PENDING → r1, port 8643)
   312|     - Writes lifecycle event: DRAFT_READY → REVIEW_PENDING
   313|        ↓
   314|   Reviewer receives dispatch (r1, port 8643)
   315|   Reviewer compares proposal against Eric's recorded intent
   316|   ```
   317|
   318|4. Idempotency: `drafter_start.py` hashes Eric's intent text and checks for an
   319|   existing workflow_run with the same topic. If found and still active (not
   320|   COMPLETE/ERROR/ESCALATE), returns the existing `workflow_run_id` and
   321|   `proposal_id` instead of creating duplicates.
   322|
   323|5. All lifecycle writes go through `transition_state()` (or its CLI-safe wrapper)
   324|   using existing ALLOWED_TRANSITIONS state names.
   325|
   326|6. The phrase "workflow run is in a Drafter-closeable state" is redefined as:
   327|   the most recent `lifecycle_events.to_state` for this `workflow_run_id` is
   328|   `DRAFTING`, and no `DRAFT_READY` event already exists (idempotency protection).
   329|
   330|7. Git-state enforcement: `drafter_start.py` warns, `drafter_session_init.py`
   331|   warns, `drafter_closeout.py` refuses if untracked files exist.
   332|
   333|---
   334|
   335|## Evidence
   336|
   337|### Fact 1: No ADR covers draft initiation
   338|13 ADRs exist (SEED-001 through SEED-013, plus T44-001). None define how a Drafter
   339|workflow_run is created.
   340|
   341|### Fact 2: Workflow_run creation exists only in Flask API layer
   342|`runtime/api/advisor.py:1250` — `_create_workflow_run()` is API-bound. Terminal
   343|Drafter sessions have no equivalent path.
   344|
   345|### Fact 3: proposal_id and workflow_run_id are separate identities in existing code
   346|`orchestration.py:119`: `generate_proposal_id()` returns `str(uuid.uuid4())`
   347|`advisor.py:1250`: `_create_workflow_run()` returns `f"run-{uuid.uuid4().hex[:13]}"`
   348|No column in any Tier 11B table stores the link between them.
   349|
   350|### Fact 4: Lifecycle events table exists but is empty (0 rows)
   351|`migration 0011_lifecycle_dispatch.sql` created the schema. The state machine
   352|(`ALLOWED_TRANSITIONS` in `orchestration.py:21-71`) is enforced in code but has
   353|never been exercised with real data. No demonstration of DRAFT_READY → REVIEW_PENDING
   354|has occurred.
   355|
   356|### Fact 5: ALLOWED_TRANSITIONS already defines the needed states
   357|All required states exist in the code: ROUTING, DRAFTING, DRAFT_READY, REVIEW_PENDING.
   358|No new state names need to be invented.
   359|
   360|### Fact 6: No column exists to join proposal_id to workflow_run_id (on either side)
   361|Full schema audit of lifecycle_events, dispatch_log, dispatch_events, workflow_runs,
   362|workflow_run_artifacts, and workflow_run_legacy_links confirmed zero columns
   363|bridging the two identities. The Flask API creates both IDs in the same call but
   364|the link exists only in the HTTP response, not in the database.
   365|
   366|Migration 0012 adds `workflow_run_id` to the many-side tables (`lifecycle_events`,
   367|`dispatch_log`) so downstream queries can filter lifecycle and dispatch state by
   368|workflow run without a join through proposal_id.
   369|
   370|---
   371|
   372|## Boundary
   373|
   374|This is a temporary bridge, not the final Router/Tier 7R design. It must not expand into:
   375|- Full router implementation
   376|- Intent classification or topic routing
   377|- Project promotion (Pass 5)
   378|- Generalized workflow automation
   379|- Multi-project initiation
   380|- Schedule/field-use work (SWA)
   381|
   382|When Tier 7R Router is built, `drafter_start.py` is retired, the `workflow_run_id`
   383|link columns become the standard join path, and this ADR is marked SUPERSEDED.
   384|
   385|---
   386|
   387|## Resolved Reviewer Objections
   388|
   389|The following objections were raised by V4 Reviewer (r1, port 8643) on 2026-06-15
   390|and resolved in this revision:
   391|
   392|| # | Objection | Resolution |
   393||---|---|---|
   394|| 1 | ADR authored by Reviewer profile, not Drafter | Eric waived for ADR-SEED-014 only (see Provenance Note). Future ADRs: Drafter authors first. |
   395|| 2 | Advisor boundary clause has no enforcement mechanism | Stated as governance convention with minimum mechanisms: intent recording, output hashing, Reviewer comparison. No overbuilt similarity detection. |
   396|| 3 | `transition_state()` import chain unspecified for terminal scripts | Tier 11C must verify terminal callability. Provide CLI-safe wrapper if Flask context required. One validator, callable from both contexts. |
   397|| 4 | No idempotency protection for `drafter_start.py` | Added topic-hash dedup. Duplicate intents return existing IDs instead of creating duplicates. |
   398|| 5 | Missing git-state policy for session init vs closeout | Three-phase policy added (Choice 5): start warns, session init warns, closeout refuses untracked files. |
   399|
   400|Risk assessment: **LOW** after revisions. Architecture is sound. All structural
   401|decisions are resolved. Implementation risks are limited to `transition_state()`
   402|terminal callability (verification gated before Tier 11C build) and the advisor
   403|boundary (governance convention, not technical enforcement).
   404|
   405|---
   406|
   407|## Session Update — 2026-06-27
   408|
   409|This document's topic (ADR-SEED-014 contract) was not directly advanced this session.
   410|The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
   411|abstraction layer (5 endpoints including human-readable status), intent alignment
   412|pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
   413|full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
   414|Commit: 9c921e2. All 17 DEV-PIVOT files carry session footers. HCP regenerated at HEAD.
   415|