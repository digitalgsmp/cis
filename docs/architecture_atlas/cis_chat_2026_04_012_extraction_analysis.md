# CIS Chat 2026-04 012 — Extraction Analysis

Source file: `CIS_Chat_2026-04_012.md`  
Extraction mode: Implementation-grade architectural topology extraction  
Primary theme: Pre-intelligence capture infrastructure, session continuity, project-aware intake, dashboard UX, and discovery of missing data-capture gates before intelligence extraction.

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Session Close Is Not Merely a Log Event — It Is a Continuity Transport Layer

- **Architectural Significance**  
  The session close process was corrected from a passive vault write into an active continuity transport mechanism. The handoff file became the object that carries operational memory into the next chat/session. This shifted session close from “save a record” to “prepare the next runtime context.”

- **Affected Layers**  
  - Governance Layer
  - Application Surface / Dashboard
  - Execution Layer
  - Project Object Layer
  - Memory / Continuity Layer

- **Dependency Impact**  
  The handoff now depends on:
  - active project identity
  - dashboard session close POST payload
  - `cis_dashboard.py` Step 7
  - project folder write access
  - timestamped filename generation
  - embedded handoff protocol content

- **Build Impact**  
  Session close cannot be considered complete unless the handoff is written both to the vault and to the active project folder. This adds a second write target to the close sequence.

- **Runtime Impact**  
  Session close now produces a portable project-local continuity artifact. The next chat can be started from the active project folder without navigating the vault.

---

## Discovery Name: Active Project Context Must Travel Through Session Close and Intake

- **Architectural Significance**  
  Project identity is not optional metadata. It is required for both handoff generation and source intake. Without `project_id`, session artifacts and ingested sources become disconnected from the project object.

- **Affected Layers**  
  - Project Object
  - Dashboard Application Layer
  - Intake Pipeline
  - Source Manifest
  - Knowledge Record lineage

- **Dependency Impact**  
  The dashboard frontend must send `project_id` to backend routes. The backend must pass it into runtime scripts. `cis_intake.py` already supported `--project`, but the dashboard was not sending it.

- **Build Impact**  
  Intake and session close routes required wiring changes:
  - HTML session close POST body sends `project_id`
  - HTML intake POST body sends `project_id`
  - Python `/api/intake` route passes `--project` to `cis_intake.py`

- **Runtime Impact**  
  Newly ingested sources now write `"project_id": "PROJECT__CIS__BUILD__V1"` into the manifest when the active project is selected.

---

## Discovery Name: Handoff File Naming Requires Timestamp Granularity

- **Architectural Significance**  
  Date-only handoff names fail when multiple sessions happen in one day. Timestamp naming is required for version-safe continuity.

- **Affected Layers**  
  - Governance
  - Session Close Protocol
  - Runtime Script Layer
  - File Storage / Project Container

- **Dependency Impact**  
  The handoff filename now depends on a UTC timestamp, not only a calendar date.

- **Build Impact**  
  The filename pattern changed to:

  `CIS_Handoff_YYYY-MM-DD_HHMM.md`

- **Runtime Impact**  
  Multiple handoffs can exist on the same day without overwriting or ambiguity.

---

## Discovery Name: Session Close Protocol Should Be Embedded, Not Generated Separately

- **Architectural Significance**  
  The Session Close Protocol was reclassified as stable boilerplate that should live inside the generated handoff content. This reduces the number of files required to start the next chat.

- **Affected Layers**  
  - Governance
  - Handoff Template / Close Sequence
  - Chat Continuity Workflow

- **Dependency Impact**  
  The protocol no longer needs to be regenerated per session. The generated handoff must include a duty/protocol block.

- **Build Impact**  
  The handoff content is constructed inline in `cis_dashboard.py`, not through an external template file.

- **Runtime Impact**  
  One generated file can carry session facts and the instructions for how the next agent should use them.

---

## Discovery Name: Notes Field Requires a Governance Definition

- **Architectural Significance**  
  The `Notes` field was identified as inconsistent because it lacked a contract. It became a structured capture area for context that does not fit focus, completed work, or next steps.

- **Affected Layers**  
  - Governance
  - Session Close
  - Memory / Continuity
  - Dashboard Form Model

- **Dependency Impact**  
  Notes content depends on qualifying criteria:
  - pending decisions
  - warnings / gotchas
  - partially built work
  - deferred context

- **Build Impact**  
  Notes should be a textarea, not a single-line input, and should not be filler.

- **Runtime Impact**  
  Session close output becomes more reliable as a transfer mechanism for unresolved context.

---

## Discovery Name: The Dashboard Requires a Server-Side Archive Browser

- **Architectural Significance**  
  Manual path entry was a usability blocker for intake. The user could browse files visually but had to copy paths manually. Browser-native file input cannot reliably expose server filesystem paths, so the correct solution is a server-side directory browser rooted at `/mnt/archive`.

- **Affected Layers**  
  - Application Layer
  - Intake Pipeline
  - Archive Interface
  - Operator Usability

- **Dependency Impact**  
  The dashboard requires:
  - `/api/browse` endpoint
  - a file tree UI
  - ingestable file filtering
  - path-fill behavior into the intake field

- **Build Impact**  
  Intake UI expanded from a text field to a navigable archive selector.

- **Runtime Impact**  
  The operator can select source files from `/mnt/archive` without manually copying paths.

---

## Discovery Name: Intelligence Work Cannot Begin Safely Without Capture Infrastructure

- **Architectural Significance**  
  The conversation identified that intelligence extraction should not begin yet because critical data capture paths were missing. This converted “start intelligence” into “first complete pre-intelligence capture gates.”

- **Affected Layers**  
  - Intelligence Layer
  - Router / Model Orchestration
  - Governance
  - Application Surface
  - Review / Promotion
  - Database / Memory

- **Dependency Impact**  
  Before intelligence extraction, the system needs:
  - decision logging form
  - extraction run logging table
  - review/promotion UI
  - prompt version tracking plan
  - processing profile override path

- **Build Impact**  
  The next build order changes: decision logging, run logging, and review UI precede first meaningful extraction.

- **Runtime Impact**  
  Extraction runs must be auditable, associated with decisions, and promotable through human review.

---

## Discovery Name: Post-Commit Work Creates an Uncaptured Continuity Gap

- **Architectural Significance**  
  The user identified that work continued after the session had been closed and committed. This created a new class of continuity failure: post-commit work that is real but not captured in handoff, DB, git, or logs.

- **Affected Layers**  
  - Governance
  - Session Close
  - Memory / Continuity
  - Handoff Protocol
  - Start-of-session Protocol

- **Dependency Impact**  
  The next session must accept a `POST-COMMIT ADDENDUM` as an input object and record it before any new work proceeds.

- **Build Impact**  
  A new session-opening rule is required: if a post-commit addendum exists, record it to all necessary endpoints first.

- **Runtime Impact**  
  Prevents undocumented work from falling outside the session lifecycle.

---

# 2. TOPOLOGY MUTATIONS

## New Layers

### 2.1 Continuity Transport Sub-layer

A new practical sub-layer emerged between Governance, Session Close, and Project Object:

`session work → close fields → handoff content → vault + active project folder → next chat startup`

This sub-layer is responsible for transporting context, not just storing it.

### 2.2 Capture Infrastructure Layer Before Intelligence

The system discovered that Phase 1 Intelligence Extraction needs a capture-precondition layer:

`decision capture → run capture → review/promotion capture → extraction`

This layer prevents intelligence outputs from becoming untraceable.

### 2.3 Server-Side Archive Selection Bridge

The Application Layer gained a bridge to `/mnt/archive`:

`dashboard browse UI → /api/browse → server filesystem listing → selected path → intake field`

This is not intelligence yet. It is an operator-access bridge into the archive.

### 2.4 Post-Commit Addendum State

A new governance state emerged:

`session closed → work continues → post-commit addendum required → next session records addendum`

This is a lifecycle mutation in the session protocol.

---

## Split Layers

### 2.5 Handoff Template vs Handoff Runtime

The session clarified that there is no external template mechanism. The “template” lives as inline runtime content in `cis_dashboard.py`.

Split:
- conceptual template = desired handoff structure
- runtime implementation = f-string inside dashboard backend

### 2.6 System Log vs ADRs

The conversation separated two institutional memory channels:

- system log = what happened operationally
- ADRs = what was decided architecturally and why

This separation is critical for future knowledge-base formation.

---

## Runtime Bridges

- Session Close POST body → backend `api_session_close`
- Session Close backend → vault handoff path
- Session Close backend → active project folder handoff path
- Intake POST body → backend `/api/intake`
- Backend `/api/intake` → `cis_intake.py --project`
- Browse UI → `/api/browse`
- Source selection → intake path field

---

## Orchestration Changes

The workflow changed from:

`close session → write handoff to vault`

to:

`close session → write log/DB/vault/git → write handoff to vault → write handoff to active project folder → verify project folder artifact`

The intake workflow changed from:

`manual path entry → intake source`

to:

`browse archive → select source → auto-fill path → intake source with active project_id`

---

## Governance Expansion

New governance rules emerged:

- handoff filenames must be timestamped
- active project folder must receive the handoff
- handoff must contain protocol boilerplate
- Notes field must be meaningful or blank
- source intake must carry `project_id`
- post-commit work requires an addendum
- ADRs must capture architecture decisions, not merely system actions

---

## Object-Model Mutations

### Handoff Object

The handoff object now contains:
- timestamped filename
- session focus
- completed work
- next steps
- notes
- sync status
- protocol/duty block
- project-local copy

### Source Manifest

The source manifest now requires `project_id` when intake happens from an active project.

### Post-Commit Addendum

New proposed object:
- date/time
- additional completed work
- additional decisions
- required next-session actions
- recording requirement

---

## Workflow / Execution Separation

The session repeatedly exposed that conceptual workflow is not enough. The dashboard implementation required exact runtime wiring:

- frontend POST fields
- backend argument passing
- command-line script flags
- filesystem write paths
- verification commands

This reinforces the prior architectural distinction:

`workflow = what should happen`  
`execution = what file/command/state/output proves it happened`

---

## Project-Container Evolution

The active project folder became the operational handoff site, not just a creative project container. It now stores:

- project JSON
- timestamped handoff files
- future source-linked session continuity artifacts

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisites

### 3.1 Handoff Project Write Requires Frontend Project ID

The backend cannot write to the active project folder unless the frontend sends `project_id` during close.

### 3.2 Intake Project Association Requires Full Chain Wiring

`cis_intake.py` already supported `--project`, but the pipeline was not project-aware until all three links were wired:

`HTML POST → Python route → cis_intake.py --project → manifest.json`

### 3.3 Usability Requires Server-Side File Browsing

Native browser file selection cannot solve `/mnt/archive` path selection. The dashboard needs a server-side listing API.

### 3.4 Intelligence Requires Data-Capture Preconditions

Before extraction, the system must capture:
- decisions
- run metadata
- review/promotions
- prompt versions
- processing profile overrides

### 3.5 Verification Requires Small Output Units

Batch terminal checks caused truncated copied output. The user requires visible verification, so verification commands should be run in small groups or one at a time.

---

## Sequencing Constraints

1. Finish session close continuity before intelligence.
2. Wire active project into intake before extraction.
3. Add archive browser before regular archive ingestion.
4. Add decision logging before more architecture decisions accumulate.
5. Add run logging before intelligence extraction.
6. Add review/promotion UI before trusted knowledge formation.
7. Add post-commit addendum handling before allowing sessions to close cleanly while work continues.

---

## Circular Dependencies

### 3.6 Application Layer Earlier Than Expected

The system originally treated the Application Layer as later. This session shows that minimal operator-facing application surfaces are needed early to make execution usable:

- session close form
- pipeline panel
- browse button
- future decision logging form
- future review/promotion panel

This is not full app development; it is an execution control surface.

### 3.7 Governance Requires UI to Be Followed Reliably

Manual ADR insertion is possible, but unreliable. Governance quality now depends on dashboard capture forms.

---

## Unstable Dependencies

- External handoff template file: considered but rejected for now.
- `sqlite3` command-line availability: missing on the VM during verification.
- Existing pre-fix source manifests: may lack `project_id` and require patching.
- Context-window limit: external chat UI limit creates session boundary risk.

---

## Runtime Blockers

- No decision logging form.
- No extraction run logging table.
- No dashboard trigger for `cis_review.py`.
- No prompt version tracking.
- No dashboard override for processing profile.
- Existing test source `image__img1783__001` is not meaningful for first real extraction.

---

## Orchestration Bottlenecks

- Session close can be bypassed by continuing work post-commit.
- Handoff generation is inline in Python, so formatting errors can break runtime if pasted incorrectly.
- User verification breaks down if outputs are batched and visually truncated.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## Commands / Runtime Actions Extracted

### 4.1 Find Dashboard Runtime Files

```bash
find /mnt/projects/cis -name "*.py" -o -name "*.js" -o -name "*.html" | grep -v __pycache__ | sort
```

Purpose: locate runtime scripts controlling dashboard behavior.

### 4.2 Replace Dashboard Files

```bash
cp cis_dashboard.py /mnt/projects/cis/runtime/cis_dashboard.py
cp cis_dashboard.html /mnt/projects/cis/runtime/cis_dashboard.html
```

Purpose: deploy full-file replacements for dashboard backend and frontend.

### 4.3 Start Dashboard

```bash
python3 /mnt/projects/cis/runtime/cis_dashboard.py
```

Purpose: verify dashboard restarts cleanly.

### 4.4 Verify Project-Aware Intake

```bash
cat /mnt/projects/cis/ingest/processing/image__img1783__001/manifest.json | grep project_id
```

Expected output:

```json
"project_id": "PROJECT__CIS__BUILD__V1",
```

### 4.5 Verify Project Handoff Artifact

```bash
ls /mnt/projects/cis/projects/PROJECT__CIS__BUILD__V1/
```

Expected result includes:

```text
CIS_Handoff_2026-04-18_0740.md
project__cis__build__v1.json
```

### 4.6 Verify Runtime Sync / Git Commit

```bash
cd /mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1 && git log --oneline -3
```

Purpose: verify session close commit landed.

---

## States

### Session Close States

- open
- close fields filled
- close submitted
- DB logged
- ADRs regenerated
- records synced
- runtime synced
- system log updated
- handoff written to vault
- handoff written to project folder
- git committed/pushed
- verified

### Source Intake States

- path selected
- intake submitted
- source container created
- manifest written
- project_id assigned
- ready for classify/preprocess/extract/normalize

### Post-Commit State

- session already committed
- additional work performed
- addendum required
- next session must ingest addendum first

---

## Transitions

### Handoff Transition

`session close form submit → handoff content generated → timestamped file created → vault write → active project write → sync status returned`

### Intake Transition

`browse file → selected file path → POST /api/intake with project_id → backend command with --project → manifest writes project_id`

### Verification Transition

`system claims success → user runs exact command → output inspected → status accepted`

---

## Runtime Contracts

### Handoff Filename Contract

Pattern:

`CIS_Handoff_YYYY-MM-DD_HHMM.md`

Requirements:
- UTC timestamp
- supports multiple sessions per day
- same file written to vault and active project folder

### Handoff Content Contract

Must include:
- protocol/duty block
- session focus
- completed work
- next steps
- notes
- sync status
- next-session startup instructions

### Notes Field Contract

Valid Notes content includes:
- pending decisions
- gotchas/warnings
- partially built work
- deferred context

Invalid Notes content:
- filler
- redundant completed work
- content already captured in next steps

### Intake Project Contract

Every dashboard-triggered intake must pass active `project_id` through to the source manifest.

---

## Validation Behavior

### Session Close Validation

Pass requires all eight close steps to report green:

- session logged to database
- ADRs regenerated
- knowledge records synced
- projects folder synced
- runtime scripts synced
- system log updated
- handoff written to vault
- handoff written to project folder
- git committed and pushed

### Intake Validation

Pass requires manifest grep to show non-null project_id matching active project.

### UI Validation

Pass requires visual confirmation:
- RUN CIS-START button is solid blue
- session sections are visually separated
- completed/next steps textareas expandable
- Notes is textarea
- Browse button opens file tree

---

## Pass / Fail Structures

### Pass

- dashboard restarts
- file browser selects source
- intake creates manifest
- manifest contains project_id
- session close writes handoff to active project folder
- git commit reflects session focus

### Fail

- Python indentation error in `cis_dashboard.py`
- frontend does not send `project_id`
- project folder missing handoff
- intake manifest has null project_id
- verification output too truncated for user confidence

---

## Retry / Escalation Logic

- If dashboard Python breaks, replace complete file and run syntax check.
- If session close skips project folder write, inspect frontend POST body for `project_id`.
- If intake manifest lacks project_id, verify HTML POST → backend route → `cis_intake.py --project` chain.
- If terminal output is unclear, rerun checks one at a time.
- If work continues after commit, create post-commit addendum and force next session to ingest it first.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

### Human Authority

The user’s requirement for visible verification overrides assistant assumptions. “No error shown” is not sufficient if output is truncated or incomplete.

### ADR Authority

ADRs are the canonical place for decisions about how the system is built and why.

### System Log Authority

System log records operational actions and session close results.

### Handoff Authority

Handoff carries immediate cross-session continuity, including context that may not yet be fully recorded elsewhere.

---

## Review States

### Decisions

- proposed
- needs ADR
- logged in decisions table
- regenerated into ADRs.md
- available to future sessions

### Intelligence Outputs

Not yet fully implemented, but the session clarified required states:

- draft
- needs review
- checked
- approved
- locked

### Post-Commit Addendum

- addendum drafted
- pending next-session ingestion
- recorded to endpoints
- superseded by official session record

---

## Promotion Logic

- Runtime facts can enter system log automatically.
- Architectural decisions require ADR capture.
- Intelligence outputs cannot become trusted knowledge until reviewed/promoted.
- Post-commit work cannot become canon until explicitly recorded next session.

---

## Rejection Paths

- Handoff external template file rejected for current stage; inline f-string retained.
- Session Close Protocol auto-generation rejected; embed stable protocol block inside handoff instead.
- Manual path entry rejected as insufficient for operator usability.
- Starting intelligence extraction immediately rejected because capture infrastructure gaps remain.

---

## Trust Enforcement

Trust now requires:
- artifact exists in expected location
- manifest contains correct project_id
- git commit exists
- logs show session close
- ADRs capture decisions
- user-visible verification output is readable

---

## Hallucination Controls

The session does not focus on model hallucination directly, but it identifies prerequisite controls:

- run logging table
- prompt version tracking
- validation result capture
- review/promotion UI
- decision logging

These are required before extraction outputs can be trusted.

---

## Provenance Enforcement

New provenance chains:

### Session Provenance

`session work → handoff file → project folder → next chat`

### Intake Provenance

`archive file path → source manifest → project_id → future knowledge record`

### Decision Provenance

`conversation decision → ADR candidate → decisions table → ADRs.md`

### Post-Commit Provenance

`work after commit → addendum → next session ingestion → DB/log/ADR updates`

---

## Validation Contracts

- No handoff is complete unless written to active project folder.
- No project-aware intake is valid unless manifest contains correct project_id.
- No intelligence extraction should proceed without run logging and review path.
- No post-commit work is complete until addendum is ingested next session.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

The file reinforces that knowledge formation is not just extraction. It requires capture of the build process itself:

- decisions become ADR knowledge
- runtime actions become system log knowledge
- source intake becomes manifest knowledge
- extraction runs must become run-log knowledge
- reviewed records become reusable knowledge

---

## Retrieval Structure

Future retrieval depends on capturing:

- source path
- project_id
- manifest metadata
- model used
- prompt version
- validation result
- review state
- decision history

Without these, retrieval cannot distinguish trusted knowledge from raw output.

---

## Indexing Implications

The dashboard and DB must eventually index:

- handoffs by timestamp and project
- decisions by ADR ID / date / topic
- extraction runs by source_id / model / prompt version
- knowledge records by project_id / status
- review actions by record_id / reviewer / promotion state

---

## Normalization Rules

The session implies normalization rules for several objects:

### Handoff

Normalized fields:
- focus
- completed
- next_steps
- notes
- sync_status
- timestamp
- project_id

### Decision

Normalized fields:
- decision title
- rationale
- affected layer
- date/time
- status

### Run Log

Required future normalized fields:
- task type
- model used
- prompt version
- source_id
- output path
- validation result
- escalation count
- runtime metrics

---

## Ontology / Spine Implications

The knowledge spine must include system-building knowledge, not only creative reference knowledge.

New knowledge categories implied:

- build_decision
- session_handoff
- runtime_action
- extraction_run
- review_event
- continuity_gap
- operator_verification_requirement

---

## Chunking Logic

Handoffs and post-commit addenda should be chunked by operational section:

- focus
- completed work
- next steps
- notes
- decisions to log
- required next actions

This allows future retrieval to surface precise continuity context.

---

## Reinforcement Behavior

The user’s correction that truncated outputs are not sufficient becomes an operator reinforcement signal:

- assistant/system should not batch verification commands when user needs complete visibility
- future dashboard should prefer explicit status displays over assumed success
- verification outputs should be human-readable and complete

---

## Project Linkage

All source materials and handoff artifacts must attach to active project context.

Implication:

`project_id` becomes required for pipeline intake from the dashboard.

---

## Stabilization Loops

- Session close improvements stabilize continuity.
- Project-aware intake stabilizes provenance.
- File browser stabilizes operator access to archive.
- Decision logging will stabilize architecture memory.
- Run logging will stabilize intelligence auditability.
- Review UI will stabilize trusted knowledge formation.

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

The dashboard is evolving into an operator-facing workbench rather than a passive dashboard.

Minimum required workbench areas now include:

- Session Panel
- Pipeline / Intake Panel
- File Browser
- Decision Logging Panel
- Run Logging / Intelligence Audit Panel
- Review / Promotion Panel

---

## Interface Panels

### Existing / Updated

#### Session Panel

Requirements:
- run cis-start
- close session and commit
- expandable fields
- notes textarea
- visible section separation
- active project context passed to close

#### Pipeline Panel

Requirements:
- intake path field
- Browse button
- file tree rooted at `/mnt/archive`
- ingestable file filtering
- active project passed to intake

### Required Next

#### Decision Logging Panel

Must write decisions into the DB decisions table so ADRs.md can regenerate.

#### Run Logging Panel / Backend

Must capture each intelligence run with model, prompt, source, validation, escalation, runtime metrics.

#### Review / Promotion Panel

Must expose `cis_review.py` or equivalent review/promotion action without terminal dependency.

---

## Operator Actions

New / revised operator actions:

- browse archive
- select source file
- run intake
- verify manifest project_id
- close session
- verify handoff in project folder
- create post-commit addendum if work continues
- log decisions before starting intelligence

---

## Runtime Visibility Needs

The user explicitly requires visible verification. Therefore the Application Layer should eventually display:

- active project_id
- last ingested source_id
- manifest project linkage
- session close output status
- handoff file path
- run logging status
- review status
- decision logging status

---

## Workflow Exposure

The dashboard must expose not only actions but their state:

`intake selected → source created → project linked → ready for extraction`

`session close submitted → DB logged → files synced → handoff written → git pushed`

---

## Project-Centered Interaction

The project becomes the anchor for:

- handoff storage
- source intake
- future knowledge records
- future run logs
- future review states

---

## Application / Runtime Bridges

Required bridges:

- `SessionPanel` → `/api/session/close`
- `PipelinePanel` → `/api/intake`
- `FileBrowser` → `/api/browse`
- future `DecisionPanel` → `/api/decision/log`
- future `RunLog` → DB run logging backend
- future `ReviewPanel` → `cis_review.py`

---

# 8. FEEDBACK LOOP DISCOVERIES

## Reinforcement Loops

### 8.1 Verification Loop

`system says success → user asks to verify → command output checked → incomplete visibility rejected → verification method corrected`

### 8.2 Usability Loop

`manual path entry friction → user asks for browser button → browser limitation identified → server-side browser built`

### 8.3 Session Continuity Loop

`manual handoff placement → user identifies convenience issue → project folder write added → session close verified`

---

## Correction Loops

### 8.4 Code Delivery Correction

`assistant gives unindented code → user pastes → Python breaks → assistant acknowledges fault → full-file replacement required`

Implication: for code edits, deliver full files or clearly scoped patches with indentation preserved.

### 8.5 Terminal Verification Correction

`batched checks → output appears truncated → user rejects trust-based validation → commands should be split`

---

## Governance Loops

### 8.6 ADR Gap Loop

`work completed → session close says ADRs regenerated → user questions missing ADRs → decision capture gap identified → decision logging form becomes required`

### 8.7 Post-Commit Gap Loop

`session committed → more work continues → no capture path → post-commit addendum introduced`

---

## Retrieval-Improvement Loops

Future retrieval quality depends on logging:

- decisions
- run metadata
- prompt versions
- validation outcomes
- review/promotions

This session identifies these as necessary before intelligence extraction.

---

## Archive-Learning Loops

`archive file selected → intake creates manifest → manifest links project → future extraction creates record → review promotes knowledge → teacher/librarian can reuse`

---

## Continuity / Memory Loops

`session close → handoff → next session start → continuation` now expands to:

`session close → handoff → post-commit addendum if needed → next session records addendum → continuation`

---

## Project-Output Feedback Loops

The active project folder is not only a storage destination; it becomes a continuity surface that feeds the next session.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridges

- Decision logging route from dashboard to DB.
- Extraction run logging route from pipeline to DB.
- Review/promotion route from dashboard to `cis_review.py`.
- Prompt version tracking from prompts to records/runs.
- Processing profile override from dashboard to manifest.
- Post-commit addendum ingestion route.

---

## Undefined Objects

### Extraction Run Record

Needs schema.

Required fields:
- run_id
- source_id
- project_id
- task_type
- model_used
- prompt_version
- processing_profile
- processing_plan
- input_path
- output_path
- validation_result
- escalation_count
- runtime_metrics
- created_at
- status

### Decision Record UI Object

Needs dashboard form fields:
- title
- decision
- rationale
- affected layers
- date/time
- status
- related session

### Post-Commit Addendum Object

Needs formal schema:
- originating session
- closed handoff reference
- additional completed work
- additional decisions
- required next-session actions
- recording status

---

## Unstable Schemas

- Handoff schema exists inline but not as external documented schema.
- Notes field criteria are defined verbally but should be locked into dashboard placeholder/help text and documentation.
- Run logging schema not yet implemented.
- Review/promotion UI state schema not yet implemented.

---

## Unresolved Orchestration

- How run logging attaches to each pipeline step.
- How review UI finds draft records.
- How post-commit addendum is detected and forced at next session open.
- Whether prompt versions are file hashes, version strings, or DB records.

---

## Unresolved Routing

- No LLM/model connected to dashboard yet.
- Classify, Preprocess, Extract, Normalize beyond intake do not yet function meaningfully without intelligence runtime.
- No dashboard logic for model selection or routing.

---

## Missing Governance

- ADR decisions from this session remain unlogged.
- Decision logging form not built.
- Post-commit addendum handling not embedded in formal session open protocol.
- No rule yet preventing work after close without addendum.

---

## Missing Validation Layers

- No extraction validation UI.
- No run validation record.
- No prompt version validation.
- No review-state promotion UI.
- No completeness rule for verification outputs.

---

## Unresolved Application Surfaces

- Decision Logging Panel
- Intelligence Run Log Panel
- Review / Promotion Panel
- Processing Profile Override UI
- Prompt Version Viewer
- Post-Commit Addendum Intake Panel

---

## Unresolved Storage Rules

- Where post-commit addenda live.
- Whether addenda are stored in active project folder, vault, DB, or all three.
- How historical handoff files are indexed.
- Whether decision logs should attach to project records or global ADRs only.

---

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

Before first real intelligence extraction:

1. Log six pending ADRs from this session.
2. Build decision logging form.
3. Add extraction run logging table.
4. Wire run logging into pipeline steps.
5. Build review/promotion UI.
6. Decide minimal prompt version tracking method.
7. Add or defer processing profile override with explicit gap note.

---

## Blocked Layers

### Intelligence Layer

Blocked from meaningful production use by missing run logging and review/promotion.

### Knowledge Layer

Blocked from trusted knowledge formation until review/promotion UI exists.

### Governance Layer

Partially blocked by lack of decision logging form.

### Application Layer

Must expand minimally to support capture, not full app polish.

---

## Sequencing Implications

Recommended immediate sequence:

1. Start next session with handoff + post-commit addendum.
2. Record addendum to required endpoints.
3. Insert/log six pending ADRs.
4. Build decision logging form.
5. Build extraction run logging table.
6. Wire run logging into pipeline.
7. Build review/promotion UI.
8. Select meaningful archive source.
9. Run first intelligence extraction.
10. Review and promote or reject first record.

---

## Runtime-First Requirements

- All new dashboard features must write to stable backend objects.
- Every runtime step must have visible verification.
- Full-file replacements are safer than partial unindented code snippets for non-coder operation.

---

## Governance-First Requirements

- Decisions must be captured before further architecture work.
- Post-commit addendum must become official protocol.
- Notes field contract should be locked in documentation or UI help.

---

## Execution-First Requirements

- UI controls must call runtime scripts reliably.
- Each script call must update an object or log.
- Pipeline steps must not appear functional unless their backend capability is connected.

---

## Application Dependencies

The dashboard now depends on:

- active project state
- project folder existence
- `/mnt/archive` availability
- `/api/browse`
- `/api/intake`
- `/api/session/close`
- DB decisions table
- future run logging schema

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object: Handoff File

- **Purpose**  
  Carries session state, protocol, completed work, next steps, notes, and sync status into the next chat.

- **Lifecycle**  
  generated at session close → written to vault → written to active project folder → attached to next chat → used as continuity source

- **Authority Source**  
  Dashboard session close fields + runtime close sequence.

- **Related Objects**  
  Session Log, Project, ADRs, System Log, Post-Commit Addendum.

- **States**  
  generated, written_to_vault, written_to_project, verified, used_in_next_session

- **Storage Implications**  
  Stored in vault Phase_PD folder and active project root.

---

## Object: Session Close Protocol Block

- **Purpose**  
  Defines next-agent duty and handoff usage inside the handoff itself.

- **Lifecycle**  
  stable boilerplate → embedded in handoff → updated only when protocol changes

- **Authority Source**  
  Governance / Session Close design.

- **Related Objects**  
  Handoff File, Session Close Form, Post-Commit Addendum.

- **States**  
  embedded, current, revised

- **Storage Implications**  
  Inline inside handoff generation string, not a separate generated file.

---

## Object: Notes Field

- **Purpose**  
  Captures pending decisions, warnings, gotchas, partial work, or deferred context.

- **Lifecycle**  
  filled during session close → written into handoff → reviewed next session

- **Authority Source**  
  User / governance definition.

- **Related Objects**  
  Handoff File, Session Log, ADR candidates, Post-Commit Addendum.

- **States**  
  empty, populated, reviewed, actioned

- **Storage Implications**  
  Stored in handoff content; may later map to session_log notes field.

---

## Object: Active Project

- **Purpose**  
  Anchors session close artifacts and source intake.

- **Lifecycle**  
  selected in dashboard → used by session close and intake → receives handoff/source linkage

- **Authority Source**  
  Dashboard project state.

- **Related Objects**  
  Handoff File, Source Manifest, Project JSON, Knowledge Records.

- **States**  
  selected, active, written_to, source_attached

- **Storage Implications**  
  Project root receives timestamped handoff files and links to ingested sources.

---

## Object: Source Manifest

- **Purpose**  
  Records source identity, processing state, and project association for intake.

- **Lifecycle**  
  source selected → intake run → manifest created → project_id written → pipeline steps proceed

- **Authority Source**  
  `cis_intake.py` plus dashboard intake POST.

- **Related Objects**  
  Source, Project, Knowledge Record, Processing Profile.

- **States**  
  created, project_linked, ready_for_processing, preprocessed, extracted, normalized

- **Storage Implications**  
  Stored under `/mnt/projects/cis/ingest/processing/<source_id>/manifest.json`.

---

## Object: Archive Browser Selection

- **Purpose**  
  Lets the operator select a source path from `/mnt/archive` through the dashboard.

- **Lifecycle**  
  browse opened → directory listed → file selected → intake path populated

- **Authority Source**  
  `/api/browse` endpoint and dashboard UI.

- **Related Objects**  
  Source Path, Intake Form, Source Manifest.

- **States**  
  browsing, selected, path_filled, ingested

- **Storage Implications**  
  Does not create storage itself; feeds path to intake.

---

## Object: Decision / ADR Candidate

- **Purpose**  
  Captures architecture decisions requiring preservation.

- **Lifecycle**  
  decision made → ADR candidate identified → logged in decisions table → ADRs.md regenerated

- **Authority Source**  
  User/system architecture discussion.

- **Related Objects**  
  ADRs.md, decisions table, session log, handoff.

- **States**  
  proposed, pending_log, logged, regenerated, canonical

- **Storage Implications**  
  Needs DB form; currently pending for six session decisions.

---

## Object: Extraction Run Log

- **Purpose**  
  Audits each intelligence extraction run.

- **Lifecycle**  
  pipeline run starts → model/task metadata captured → validation result saved → run becomes auditable

- **Authority Source**  
  Router / Intelligence pipeline.

- **Related Objects**  
  Source Manifest, Model, Prompt, Knowledge Record, Validation Result.

- **States**  
  pending_schema, not_built, required_before_extraction

- **Storage Implications**  
  Needs DB table and pipeline integration.

---

## Object: Review / Promotion Event

- **Purpose**  
  Moves generated knowledge from draft toward trusted use.

- **Lifecycle**  
  record generated → review triggered → user approves/rejects/edits → status updated

- **Authority Source**  
  Human review via `cis_review.py` / future UI.

- **Related Objects**  
  Knowledge Record, Source Manifest, Run Log, Project.

- **States**  
  draft, checked, approved, rejected, locked

- **Storage Implications**  
  Requires dashboard trigger and persistent review state.

---

## Object: Post-Commit Addendum

- **Purpose**  
  Captures work done after a session close/commit.

- **Lifecycle**  
  session closed → work continues → addendum created → next session records addendum first

- **Authority Source**  
  User-identified continuity gap.

- **Related Objects**  
  Handoff File, Session Log, ADRs, System Log.

- **States**  
  created, pending_ingestion, recorded, closed

- **Storage Implications**  
  Needs formal storage and ingestion protocol.

---

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did NOT exist before?

This file establishes that CIS cannot move into Intelligence Extraction merely because the execution layer and dashboard exist. The system must first complete a capture-and-continuity layer that preserves decisions, run metadata, project associations, review states, and post-session work.

The major new understanding is:

> **Intelligence extraction is not the next isolated technical step; it is dependent on capture infrastructure that makes extraction auditable, project-linked, reviewable, and recoverable across sessions.**

The session produced several concrete topology shifts:

1. **Session close became a continuity transport layer.**  
   Handoffs are no longer only vault records. They are timestamped, project-local startup artifacts for the next chat.

2. **The active project became mandatory runtime context.**  
   Both session handoff and source intake must carry `project_id`.

3. **The dashboard became an early execution control surface.**  
   Minimal application-layer surfaces are required before the full Application Layer because the operator needs clickable, visible control over intake and continuity.

4. **The archive browser became a required intake bridge.**  
   The system cannot rely on manual path entry if it is meant to support real archive-driven ingestion.

5. **Decision capture became a blocker, not polish.**  
   ADR logging is necessary because CIS is also building a coding/build knowledge base from its own construction.

6. **Run logging and review/promotion became preconditions for intelligence.**  
   Without run logs, prompt versions, validation results, and review UI, intelligence outputs cannot be audited or trusted.

7. **Post-commit work became a new governance gap.**  
   The user’s actual working pattern includes continuing after close/commit. CIS must support this through post-commit addenda.

8. **Verification must be visible and granular.**  
   The user cannot rely on implied success. The system must provide readable, complete validation outputs.

The build plan therefore changes from:

`dashboard ready → intelligence extraction`

into:

`dashboard ready → decision logging → run logging → review/promotion UI → prompt/version awareness → intelligence extraction`

This is a major architectural correction. The file reveals that the missing layer is not more model capability. The missing layer is **capture, verification, and promotion infrastructure** that allows intelligence work to become trustworthy system knowledge.
