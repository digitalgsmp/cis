# CIS Canonical Build Sequence Plain Language — Extraction Analysis

Source file: `CIS_Canonical_Build_Sequence_Plain_Language.md`

Extraction mode: implementation-grade architectural topology extraction  
Purpose: derive topology-ready build intelligence, dependency structure, runtime implications, governance gates, canonical objects, state machines, execution contracts, and application-layer consequences.

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery 1 — CIS Build Order Is Now Canonicalized as a Phase-Gated Construction Sequence

- **Discovery Name:** Canonical Build Sequence: PD → 0 → 1 → 2 → 3 → 4 → 5
- **Architectural Significance:** The roadmap converts CIS from a conceptual layered system into a physically ordered build system. Each phase establishes a prerequisite layer that later phases depend on.
- **Affected Layers:** Governance, Execution Layer, Intelligence Layer, Knowledge Layer, Workflow Layer, Agent Layer, Application Layer.
- **Dependency Impact:** Later system layers are not independent. Retrieval depends on records. Agents depend on approved/retrievable knowledge. Application depends on commands and runtime objects. Automation depends on manually validated execution.
- **Build Impact:** Prevents premature UI, agent, retrieval, or database work. Establishes a strict proof-before-expansion rule.
- **Runtime Impact:** Runtime behavior must be validated phase by phase. Each phase ends with an operational completion test, not a conceptual milestone.

## Discovery 2 — Pre-Development Harness Is a Required System Layer Before Execution

- **Discovery Name:** Phase PD — Pre-Development Harness
- **Architectural Significance:** CIS requires a context-loading and decision-preservation layer before implementation begins. This creates a system memory substrate that supports continuity across AI sessions and collaborators.
- **Affected Layers:** Governance, Memory, Collaboration, Documentation, AI Role Routing.
- **Dependency Impact:** Execution work depends on persistent decisions, role assignments, skill documents, and a harness coordinator.
- **Build Impact:** The first build layer is not the execution pipeline itself. The first build layer is the institutional-memory harness that prevents context reset.
- **Runtime Impact:** A session can load memory, skill docs, role assignments, and locked rules automatically before any work begins.

## Discovery 3 — Execution Layer Is the Load-Bearing Foundation

- **Discovery Name:** Phase 0 — Execution Layer as Load-Bearing Structure
- **Architectural Significance:** The Execution Layer is the first operational layer. It converts architecture into enforceable object schemas, commands, states, validation, logs, and storage rules.
- **Affected Layers:** Runtime, Workflow, Knowledge, Application, Agent prerequisites.
- **Dependency Impact:** Nothing above Phase 0 can be trusted until objects, commands, validation, state transitions, and naming/storage conventions are enforceable.
- **Build Impact:** The system must build command-line/runtime behavior before app UI.
- **Runtime Impact:** A file can move from raw arrival to draft knowledge record through explicit commands and state changes.

## Discovery 4 — CIS Uses a Five-Stage Knowledge Formation Path

- **Discovery Name:** Raw File → System Reading → Structured Description → Human Review → Knowledge Record
- **Architectural Significance:** The document defines the universal transformation path that all later architecture supports.
- **Affected Layers:** Intake, Intelligence, Governance, Knowledge Formation, Review, Retrieval.
- **Dependency Impact:** Knowledge does not begin at storage. It begins only after structured description and human review.
- **Build Impact:** Every phase exists to make the five stages reliable, repeatable, and scalable across 10TB of source material.
- **Runtime Impact:** Raw files remain raw material until processed, reviewed, and saved as knowledge records.

## Discovery 5 — Core Runtime Commands Are Now Named and Sequenced

- **Discovery Name:** CIS Core Command Set
- **Architectural Significance:** The roadmap defines actual command entry points: `cis intake`, `cis classify`, `cis preprocess`, `cis extract`, `cis normalize`, `cis review`, and `cis project init`.
- **Affected Layers:** Execution Layer, Workflow Layer, Application Layer, Human Operator Layer.
- **Dependency Impact:** Future UI buttons call these commands. Agents advise around these commands but do not replace them.
- **Build Impact:** Command implementation is a prerequisite to Phase 5 Application Layer.
- **Runtime Impact:** The system becomes executable without a GUI and testable by coworker-use criteria.

## Discovery 6 — Validation Is Embedded in Every Runtime Command

- **Discovery Name:** Command-Level Validation Gates
- **Architectural Significance:** Validation is not a separate later layer. It is built into each command before state advancement.
- **Affected Layers:** Execution, Governance, Knowledge Trust, Review.
- **Dependency Impact:** State transitions depend on valid outputs. Invalid outputs stop, log failure, and mark `needs_review`.
- **Build Impact:** Each script must include pass/fail logic from the beginning.
- **Runtime Impact:** Bad outputs cannot silently contaminate the knowledge base.

## Discovery 7 — Real Archive Material Is the System Calibration Mechanism

- **Discovery Name:** First Real Archive Run as Schema Calibration
- **Architectural Significance:** The 10TB archive is not merely content. It is the reality test that mutates schemas, scripts, processing profiles, and validation rules.
- **Affected Layers:** Intake, Execution, Discovery, Knowledge, Processing Profiles, Validation.
- **Dependency Impact:** Phase 1 cannot begin until Phase 0 is tested on real archive files and breaks are captured.
- **Build Impact:** Test material must not be clean hypothetical samples. The archive must reveal missing profiles and hidden edge cases.
- **Runtime Impact:** Failures feed back into schemas and scripts before scaling.

## Discovery 8 — Intelligence Extraction Requires a Three-Pass Model

- **Discovery Name:** Extraction → Constraint Enforcement → Normalization
- **Architectural Significance:** The Intelligence Layer is not a single model call. It is a multi-pass pipeline combining OCR, vision, cleanup, and schema normalization.
- **Affected Layers:** Intelligence, Knowledge Formation, Validation, Routing.
- **Dependency Impact:** `cis extract` must expand into staged extraction. `cis normalize` depends on merged, cleaned outputs.
- **Build Impact:** Merge logic and constraint enforcement must be implemented before retrieval quality can be trusted.
- **Runtime Impact:** Records contain text signal, visual signal, and normalized structured fields.

## Discovery 9 — Merge Layer Becomes a Distinct Runtime Object/Script

- **Discovery Name:** `merge_record.py`
- **Architectural Significance:** The merge of Tesseract OCR and InternVL visual outputs is elevated from implicit human synthesis to a repeatable script.
- **Affected Layers:** Intelligence, Knowledge Record Assembly, Field Authority, Validation.
- **Dependency Impact:** The final knowledge record depends on merge logic respecting field authority: source-derived text overrides model description; user corrections override all.
- **Build Impact:** Merge script is a required Phase 1 component.
- **Runtime Impact:** Multi-signal extraction becomes consistent and repeatable.

## Discovery 10 — Intelligence Router Is a Decision Layer, Not a Model

- **Discovery Name:** `route_task.py`
- **Architectural Significance:** Model selection is pulled out into explicit routing logic based on task type, processing profile, local capacity, quality need, and escalation conditions.
- **Affected Layers:** Intelligence Routing, Cost Control, Model Registry, Extraction, Frontier Escalation.
- **Dependency Impact:** Models are interchangeable execution units. The router decides which tool/model handles each job.
- **Build Impact:** Routing must be logged so model outcomes can be compared.
- **Runtime Impact:** Easy tasks avoid unnecessary frontier/API use; hard tasks escalate intentionally.

## Discovery 11 — Human Correction Becomes a Structured Learning Signal

- **Discovery Name:** `corrections_log.json`
- **Architectural Significance:** Human edits are no longer isolated corrections. They become a system-learning corpus for improving prompts, validation rules, and extraction behavior.
- **Affected Layers:** Reinforcement, Governance, Review, Intelligence, Knowledge Quality.
- **Dependency Impact:** Future model behavior depends on logged correction patterns.
- **Build Impact:** Correction logging must be implemented alongside review, not after review.
- **Runtime Impact:** The system improves from batch to batch through correction-pattern accumulation.

## Discovery 12 — Knowledge Formation Requires Review, Promotion, Retrieval Text, and Vector Indexing

- **Discovery Name:** Phase 2 — Knowledge Formation and Retrieval
- **Architectural Significance:** Knowledge is formalized as a trust-managed object that moves from draft to checked to approved to locked. Approved records gain retrieval text and vector embeddings.
- **Affected Layers:** Knowledge, Retrieval, Governance, Agent Prerequisites.
- **Dependency Impact:** Retrieval depends on approved records and normalized retrieval text. Agents depend on retrieval.
- **Build Impact:** Vector index must not be built before approved records exist.
- **Runtime Impact:** Search becomes semantic rather than keyword-only.

## Discovery 13 — Production Outputs Re-Enter the Knowledge System

- **Discovery Name:** `cis archive_output`
- **Architectural Significance:** CIS knowledge grows from both archive material and active project outputs.
- **Affected Layers:** Workflow, Knowledge, Feedback Loops, Project System.
- **Dependency Impact:** Project outputs become new sources and re-enter intake/extraction/review.
- **Build Impact:** Production feedback path is required for CIS to improve through use.
- **Runtime Impact:** Techniques, renders, written pieces, and discoveries become reusable knowledge.

## Discovery 14 — Project Object Becomes a Runtime-Tracked Production Container

- **Discovery Name:** Phase 3 — Workflow System / Project Management Scripts
- **Architectural Significance:** Project is no longer a folder. It becomes a tracked object with stage, linked sources, approved records, outputs, and status.
- **Affected Layers:** Workflow, Application, Knowledge Linkage, WIAS Routing.
- **Dependency Impact:** WIAS stage routing depends on project state.
- **Build Impact:** Project scripts must expand beyond initialization to status, attachment, and stage updates.
- **Runtime Impact:** Project context can control retrieval, tool relevance, and production-stage behavior.

## Discovery 15 — AI Inference on Projects Is Advisory, Not Authoritative

- **Discovery Name:** Project AI Inference Fields
- **Architectural Significance:** CIS adds AI-generated fields for inferred constraints, required skills, risk flags, and effort estimate, but explicitly labels them as proposals.
- **Affected Layers:** Intelligence, Workflow, Human Authority, Governance.
- **Dependency Impact:** Project intelligence depends on project description, intended output type, active stage, and linked knowledge.
- **Build Impact:** Advisory fields require mutability and authority separation.
- **Runtime Impact:** The system can warn and assist without making decisions automatically.

## Discovery 16 — WIAS Routing Becomes a Configurable Operational Mechanism

- **Discovery Name:** `wias_routing.json`
- **Architectural Significance:** WIAS stages map to relevant tools, templates, processing profiles, retrieval categories, and expected outputs.
- **Affected Layers:** Workflow, Tools, Knowledge Retrieval, Application.
- **Dependency Impact:** Stage changes alter what the system surfaces.
- **Build Impact:** WIAS routing config is required before workflow can become operational.
- **Runtime Impact:** Story-first workflow becomes executable rather than descriptive.

## Discovery 17 — Agents Are Prompt-Configured Roles Grounded in Approved Records

- **Discovery Name:** Phase 4 — Bounded Agents
- **Architectural Significance:** Agents are not autonomous workers or new systems. They are structured prompt roles that operate over approved knowledge through commands.
- **Affected Layers:** Agent Layer, Retrieval, Governance, Human Authority.
- **Dependency Impact:** Librarian depends on vector index and approved records. Researcher depends on Librarian results. Teacher depends on approved learning/tutorial records.
- **Build Impact:** Agents cannot be built before Phase 2 retrieval and Phase 3 project context.
- **Runtime Impact:** Agents advise; humans decide and execute.

## Discovery 18 — Application Layer Is a Control Surface Over Existing Commands

- **Discovery Name:** Phase 5 — Workbench Interface Over Runtime
- **Architectural Significance:** The app does not create system behavior. It exposes commands, objects, states, review actions, retrieval, project dashboard, and DAM views.
- **Affected Layers:** Application, Execution, Knowledge, Workflow, Agents.
- **Dependency Impact:** Application depends on working commands, existing objects, retrieval index, agents, and project dashboard.
- **Build Impact:** No interface before commands work.
- **Runtime Impact:** Coworker can operate CIS through browser without terminal knowledge.

## Discovery 19 — DAM View Solves Unaffiliated Knowledge Routing

- **Discovery Name:** DAM View for Unaffiliated Knowledge
- **Architectural Significance:** Not all useful material belongs to a project at intake. The DAM is a filtered view of knowledge records where `project_id` is empty.
- **Affected Layers:** Application, Knowledge, Project Linkage, Asset Management.
- **Dependency Impact:** DAM requires the same knowledge schema, review process, and retrieval system as project-linked records.
- **Build Impact:** Application must support promotion, linking, and demotion between project context and DAM.
- **Runtime Impact:** Useful but unaffiliated material remains processed, searchable, and reusable.

---

# 2. TOPOLOGY MUTATIONS

## Mutation 1 — Pre-Development Harness Added Before Execution Layer

The build topology now begins with Phase PD, not Phase 0. This adds a pre-execution governance/memory layer that contains:

- SQLite session memory
- Obsidian vault
- skill documents
- ADRs
- model role assignments
- Harness Coordinator

This is a new upstream layer that prevents context loss and decision drift before runtime implementation begins.

## Mutation 2 — Execution Layer Split into Six Subsystems

Phase 0 decomposes Execution Layer into:

1. schema documents
2. state transition rules
3. command set
4. validation layer
5. real archive run
6. folder/naming enforcement

This changes Execution Layer from a conceptual “runtime bridge” into a multi-part operational substrate.

## Mutation 3 — Intake Pipeline Gains Enforced Object-State Progression

Raw material is no longer allowed to move freely into knowledge. It must pass:

source file → manifest → classified source → preprocessed source → extracted output → normalized draft record → reviewed/promoted record.

This introduces a stateful runtime chain.

## Mutation 4 — Intelligence Layer Gains Internal Pass Structure

The Intelligence Layer is split into:

- OCR/text extraction
- visual extraction
- constraint enforcement
- merge/normalization
- routing
- model comparison
- correction logging

This mutation prevents treating model output as final.

## Mutation 5 — Knowledge Layer Gains Review + Retrieval Substructure

Knowledge Formation is now:

- draft record
- checked record
- approved record
- locked record
- retrieval text
- vector index
- production feedback ingestion

This creates a trust ladder and retrieval layer inside Knowledge Formation.

## Mutation 6 — Workflow Layer Becomes Project-State Routing

Workflow is no longer a general idea-to-output path. It now depends on:

- project scripts
- stage updates
- project attachment
- project status
- AI advisory fields
- WIAS routing config
- full pipeline trial

The Project Object becomes the state-bearing workflow container.

## Mutation 7 — Agent Layer Becomes Retrieval-Grounded and Non-Executing

Agents are constrained to:

- search approved records
- synthesize retrieved records
- teach from validated records
- produce proposals only

Agents do not execute commands, change records, or promote knowledge.

## Mutation 8 — Application Layer Becomes a Runtime Surface, Not a System Origin

The application is explicitly downstream of the command/runtime system. It surfaces:

- Project Panel
- Source Panel
- Structure Panel
- Review Panel
- Knowledge Output Panel
- Search/Retrieval Interface
- Project Dashboard
- DAM View

This prevents premature dashboard development.

## Mutation 9 — DAM Introduces Unaffiliated Knowledge State

The topology now includes knowledge records that are:

- processed
- reviewed
- searchable
- not project-linked

This requires project linking/demotion logic and a first-class unaffiliated asset pool.

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisites

- Session memory must exist before reliable multi-session implementation.
- Skill documents must exist before AI/human task delegation.
- ADRs must be locked before multiple model/collaborator routing.
- Source manifest schema must exist before intake command.
- Project object schema must exist before project workflow.
- Knowledge record schema must exist before extraction output.
- Processing profile schema must exist before classification/preprocessing.
- Review states must exist before records can be trusted.
- Command set must exist before application buttons.
- Validation logic must exist before knowledge scaling.
- Real archive test must occur before Phase 1 expansion.
- Merge layer must exist before retrieval-quality records.
- Approved records must exist before vector index.
- Vector index must exist before Librarian agent.
- Librarian retrieval must exist before Researcher synthesis.
- Approved tutorial/learning records must exist before Teacher agent.
- Project objects and WIAS routing must exist before workflow operationalization.
- Runtime commands must work before application surface.

## Sequencing Constraints

1. PD must precede Phase 0 because context and role rules govern implementation.
2. Phase 0 must precede Phase 1 because extraction requires objects, states, commands, and storage.
3. Phase 1 must precede Phase 2 because knowledge retrieval requires merged records.
4. Phase 2 must precede Phase 3 because project workflows need retrievable approved records.
5. Phase 3 must precede Phase 4 because agents need project context and workflow state.
6. Phase 4 must precede Phase 5 because the app needs functioning agents to expose agent controls.
7. Phase 5 must not precede commands, because UI is only a surface over existing runtime behavior.

## Circular Dependencies Identified

- Application desire depends on Execution Layer, but operator usability pressures push toward early UI. The document resolves this by building commands first and UI later.
- Knowledge retrieval depends on approved records, but approved records depend on human review, which later benefits from UI. The document resolves this with command-based review first, interface review later.
- Agent usefulness depends on knowledge quality, but knowledge quality improves through agent-assisted use. The document resolves this by delaying agents until approved records and retrieval exist.

## Unstable Dependencies

- Qwen3-VL-32B becomes primary only if benchmark comparison proves superiority over InternVL.
- ChromaDB is likely but not locked as the vector database.
- Flask or Streamlit is likely but not locked as the interface framework.
- Frontier API use is conditional and task-dependent.
- Processing profiles are expected to mutate after the first real archive run.

## Runtime Blockers

- No valid schema → no command implementation.
- No state transitions → invalid object movement.
- No validation → bad records contaminate knowledge.
- No merge layer → OCR/visual outputs remain fragmented.
- No approved records → vector retrieval cannot be meaningful.
- No retrieval index → agents cannot ground outputs.
- No project object → WIAS routing cannot apply context.
- No commands → application has nothing real to call.

## Orchestration Bottlenecks

- The first real archive run will expose missing profiles and validation failures.
- Human review remains required for trust promotion.
- Correction logging must be structured enough to improve future prompts/rules.
- Vector index quality depends on retrieval_text quality.
- Agent quality depends on record quality, not model size alone.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## Commands Extracted

### `cis intake <path>`

- **Input:** file path
- **Process:** creates source manifest; sets status to `arrived`; moves file into `/mnt/projects/cis/ingest/incoming/`
- **Output:** source manifest and source container
- **State Transition:** none/raw → arrived
- **Validation:** path must exist; file must be accepted as source material

### `cis classify <source_id>`

- **Input:** source ID
- **Process:** reads file/source manifest; assigns processing profile
- **Output:** updated manifest with processing profile
- **State Transition:** arrived → classified
- **Validation:** processing profile must be assigned

### `cis preprocess <source_id>`

- **Input:** classified source ID
- **Process:** extracts raw ingredients:
  - PDF → pages + embedded text
  - video → sampled frames + audio transcript
  - image → visual-analysis-ready image
- **Output:** staged intermediates
- **State Transition:** classified → preprocessed
- **Validation:** required preprocessing outputs must exist

### `cis extract <source_id>`

- **Input:** preprocessed source ID
- **Process:** runs OCR/visual extraction using routing/profile rules
- **Output:** raw extraction outputs; rough draft knowledge record
- **State Transition:** preprocessed → extracted
- **Validation:** extraction outputs must exist and contain required signals or uncertainty flags

### `cis normalize <source_id>`

- **Input:** extracted source ID
- **Process:** merges OCR and visual outputs; applies schema; checks required fields
- **Output:** canonical draft knowledge record JSON + markdown mirror
- **State Transition:** extracted → draft
- **Validation:** required fields present; no unsupported claims; uncertainty noted

### `cis review <record_id>`

- **Input:** draft knowledge record ID
- **Process:** opens record for human review; captures approve/reject/edit decisions
- **Output:** updated record state and correction data
- **State Transition:** draft → checked OR rejected/rework
- **Validation:** human decision required for promotion beyond draft/check

### `cis project init`

- **Input:** project name/type/initial stage
- **Process:** creates project object and project folder structure
- **Output:** project object and disk structure
- **State Transition:** none → initiated/active project
- **Validation:** project must have required schema fields

### `cis promote <record_id>`

- **Input:** checked record ID
- **Process:** moves checked record to approved status when human confidence is established
- **Output:** approved knowledge record
- **State Transition:** checked → approved
- **Validation:** record must already be checked

### `cis archive_output <project_id> <file_path>`

- **Input:** project ID + output file path
- **Process:** feeds project output back into intake as new source with project-origin metadata
- **Output:** new source object linked to originating project
- **State Transition:** output → source intake path
- **Validation:** project ID and file path must exist

### `cis project stage <project_id> <stage>`

- **Input:** project ID + WIAS stage
- **Process:** updates active stage
- **Output:** stage-updated project object
- **State Transition:** project active stage changes
- **Validation:** stage must be one of Word/Image/Action/Sound/Web

### `cis project attach <project_id> <source_id>`

- **Input:** project ID + source/record ID
- **Process:** links source or knowledge record to project
- **Output:** updated project linkage
- **State Transition:** unlinked/linked object → project-linked object
- **Validation:** both objects must exist

### `cis project status <project_id>`

- **Input:** project ID
- **Process:** prints project status, stage, attached sources, approved records, outputs
- **Output:** project status summary
- **State Transition:** none
- **Validation:** project must exist

## Runtime Contracts

- No command advances state unless required output exists.
- Every object has a documented state history.
- Every state movement must be legal under transition rules.
- Validation failure logs the reason and halts advancement.
- Raw outputs must not enter knowledge as trusted records.
- Draft records are not approved knowledge.
- Approved/locked records are retrievable and agent-usable.

## Pass/Fail Structures

### Pass Conditions

- required fields present
- schema valid
- source linkage preserved
- project linkage captured when applicable
- uncertainty present when needed
- output written to correct folder
- state updated
- action logged

### Failure Conditions

- missing required fields
- unsupported/invented claims
- hallucinated text
- empty uncertainty where ambiguity exists
- broken schema
- malformed file/folder naming
- missing output artifact
- illegal state jump

## Retry / Escalation Logic

- If validation fails: log failure and mark `needs_review` or stop for rework.
- If model output is weak: constraint pass flags invalid portions.
- If local model insufficient: router may escalate to higher-capability model/frontier API.
- If all extraction attempts fail: record/source requires human review.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

- Human review is required for trust promotion.
- Human corrections override system-generated fields.
- Source-derived text overrides model-generated descriptions.
- AI advisory project fields do not make decisions.
- Agents advise only; humans execute and decide.
- ADRs lock architectural decisions.
- Role assignments constrain model responsibilities.

## Review States

- draft — generated but untrusted
- checked — human has reviewed record
- approved — trusted enough for search/agent use
- locked — stable and protected from casual change
- deprecated — retained but no longer preferred
- needs_review — failed validation or requires human judgment
- rejected — unusable or returned for rework

## Promotion Logic

- `cis review` moves draft to checked or rework/rejected.
- `cis promote` moves checked to approved.
- Locked records require explicit versioning before change.
- Approved/locked records become retrieval and agent substrate.

## Rejection Paths

- failed validation → stop + log + needs_review
- hallucination detected → flag/remove during constraint pass
- missing profile → update schema/profile definitions
- bad extraction → rerun/escalate/review
- incorrect project link → edit/link/demote to DAM

## Trust Enforcement

- Nothing becomes knowledge because a model generated it.
- Nothing becomes approved until reviewed.
- Records must pass schema and validation checks.
- Agents are denied authority to write/promote/execute.
- UI is denied authority to create hidden behavior; it only calls commands.

## Hallucination Controls

- Constraint enforcement pass removes or flags unsupported claims.
- Validation checks unsupported/invented information.
- Human review compares draft record against original source.
- Corrections log captures hallucination-removal events.

## Provenance Enforcement

- Source manifest records origin and processing plan.
- Record stores source, model/tool used, project linkage, status, and trust level.
- Routing script logs model used for every record.
- Corrections log records human edits and correction types.
- Output archive command tags project origin.

## Validation Contracts

- Every command contains validation logic.
- `cis normalize` validates required fields and uncertainty.
- `cis review` captures human decision.
- `build_index.py` indexes only approved records.
- Agents operate only on approved/locked records.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

Knowledge formation follows:

raw source → source manifest → preprocessing → extraction → normalization → draft knowledge record → human review → checked/approved/locked record → retrieval/indexing → reuse.

Knowledge is not raw storage. It is structured, reviewed, searchable, reusable meaning.

## Retrieval Structure

- `retrieval_text` is generated only for approved records.
- Retrieval text is a cleaned, compressed 2–4 sentence searchable field.
- Vector index reads approved records and embeds retrieval text.
- Search retrieves semantically similar records, not exact keyword matches only.
- Results carry record ID, category, tags, and project link.

## Indexing Implications

- Vector index depends on approved records.
- `build_index.py` converts retrieval text to embeddings.
- ChromaDB or equivalent lightweight vector store is likely.
- Index entries include metadata for filtering.
- Agent retrieval depends on this index.

## Normalization Rules

- OCR and visual outputs must be merged into one coherent record.
- Text directly extracted from source has higher authority than visual model narrative.
- User correction has highest authority.
- Records must conform exactly to knowledge record schema.
- Retrieval text is not raw extraction; it is normalized search text.

## Ontology / Spine Implications

The knowledge spine is organized around:

- source identity
- source type
- project link
- knowledge category
- WIAS stage relevance
- tags
- review state
- retrieval text
- trust status

## Chunking Logic

The document does not specify detailed chunking beyond vector indexing of retrieval_text. Implication: chunking should initially operate at record level, then later split retrieval_text or source units when record volume/detail requires it.

## Reinforcement Behavior

- Corrections log stores before/after edits.
- Correction types include hallucination removal, category fix, tag change, uncertainty addition.
- Correction patterns update prompts and validation rules.
- Record quality should improve from batch to batch.

## Project Linkage

- Records can be project-linked at intake.
- Project outputs re-enter knowledge with project origin.
- Some records remain unaffiliated and appear in DAM.
- DAM records can later be promoted/linked to projects.
- Linked records can be demoted back to DAM by clearing project link.

## Stabilization Loops

- real archive run stabilizes schemas and processing profiles
- correction logs stabilize prompts and validation
- review/promote stabilizes trusted knowledge
- retrieval quality stabilizes through retrieval_text improvement
- production feedback stabilizes project-derived knowledge

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

The first application must expose the runtime system through panels:

1. Project Panel
2. Source Panel
3. Structure Panel
4. Review Panel
5. Knowledge Output Panel
6. Search/Retrieval Interface
7. Project Dashboard
8. DAM View

The app must call existing commands, not invent separate behavior.

## Interface Panels

### Project Panel

- list active projects
- show current WIAS stage
- show status
- create new project

### Source Panel

- file drop zone
- calls `cis intake`
- shows file type
- shows detected processing profile
- shows current runtime state

### Structure Panel

- displays extraction output
- editable proposed fields
- title/category/tags/summary/visual description
- makes model proposals visible

### Review Panel

- approve
- reject
- edit fields
- capture `cis review` decision
- update record state on screen

### Knowledge Output Panel

- show final saved knowledge record
- confirm project link
- confirm status
- expose JSON/markdown record state

### Search/Retrieval Interface

- search vector index
- display matching approved records
- show title/category/source/snippet/status
- send selected record to active agent

### Project Dashboard

- show linked sources
- approved records
- current WIAS stage
- AI constraints/risks
- timeline of record creation/approval

### DAM View

- display all records with no project affiliation
- provide promote/link actions
- allow demotion back from project to DAM

## Operator Actions

- ingest file
- assign/confirm project
- inspect extracted structure
- edit proposed fields
- approve/reject record
- search knowledge
- ask agent
- link/promote/demote DAM records
- view project state

## Runtime Visibility Needs

The app must display:

- source status
- processing profile
- record state
- validation outcome
- project link
- review status
- search status
- agent grounding source

## Workflow Exposure

The UI should make visible:

source → manifest → preprocessing → extraction → normalization → review → knowledge → retrieval → project use.

## Project-Centered Interaction

All modules attach to project context when a project is active. DAM handles material without a project.

## Application/Runtime Bridges

- UI drop zone → `cis intake`
- UI review buttons → `cis review`
- UI promote action → `cis promote`
- UI project creation → `cis project init`
- UI project stage selection → `cis project stage`
- UI link action → `cis project attach`
- UI search → vector index query
- UI agent prompt → `cis ask librarian/researcher/teacher`

---

# 8. FEEDBACK LOOP DISCOVERIES

## Loop 1 — Archive Reality → Schema/Profile Mutation

real archive file → Phase 0 command run → failure/breakage → missing profile/validation/schema discovered → schemas/scripts updated → next run improves.

## Loop 2 — Production Output → Knowledge Growth

project output → `cis archive_output` → intake/extraction/review → project-origin knowledge record → future reuse.

## Loop 3 — Human Correction → Model/Validation Improvement

model output → human correction → `corrections_log.json` → prompt/validation update → fewer repeated errors.

## Loop 4 — Review/Promotion → Retrieval Trust

draft record → human review → checked/approved/locked → retrieval priority → agent-usable knowledge.

## Loop 5 — Retrieval → Agent Use → Production Assistance

approved records → vector index → Librarian retrieval → Researcher synthesis → Teacher guidance → production output.

## Loop 6 — Project Stage → WIAS Routing → Contextual Surfacing

project active stage → `wias_routing.json` → relevant tools/templates/knowledge categories surfaced → workflow proceeds.

## Loop 7 — DAM → Project Promotion/Demotion

unaffiliated record → DAM → promoted/linked to project OR demoted from project → record remains searchable and reusable.

## Loop 8 — Session Memory → Continuity → Better Execution

locked decisions/roles/skill docs → Harness Coordinator loads context → session starts aligned → implementation avoids drift.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridges

- Exact schema files are described but not authored in this document.
- Exact command implementations do not yet exist.
- Exact validation rule library is not specified in code-level detail.
- Exact state transition table is described conceptually but not enumerated as a machine-readable map.
- Exact UI-to-command API bridge is implied but not defined.

## Undefined Objects

- `source_id` generation rules
- `record_id` generation rules
- `project_id` generation rules
- processing profile schema details
- review event object
- correction event object
- routing task object
- embedding/index object
- DAM record view/filter object

## Unstable Schemas

- Knowledge record fields are conceptually defined but need final locked schema.
- Source manifest fields are conceptually defined but need final locked schema.
- Project object fields are conceptually defined but need final locked schema.
- Processing profile fields must adapt after real archive test.
- Review states need exact transition permissions.

## Unresolved Orchestration

- Whether commands are standalone scripts, CLI subcommands, or Python package entry points remains unspecified.
- Queue behavior for batch processing is not defined.
- Failure retry count is not defined.
- Logging format is not fully specified.
- Model runtime invocation details are not defined.

## Unresolved Routing

- Router task classification rules are implied but not fully formalized.
- Local/frontier/API escalation thresholds are not specified.
- Qwen3-VL-32B adoption criteria require benchmark design.
- Cost-control rules are not expressed as runtime policy.

## Missing Governance

- Who can promote to approved/locked is not specified.
- ADR storage and naming convention are not specified here.
- Human review interface/format before app is not specified.
- Locked record versioning behavior is implied but not operationally specified.

## Missing Validation Layers

- Hallucination detector criteria require exact patterns.
- Unsupported claims detection needs source-comparison strategy.
- Uncertainty-field requirements need field-level rules.
- Schema validation likely requires JSON Schema/Pydantic but not specified.

## Unresolved Application Surfaces

- App framework not locked: Flask or Streamlit only suggested.
- DAM UX details not fully specified.
- Agent handoff from search result to active agent is implied but not specified.
- Project dashboard data model and timeline object are undefined.

## Unresolved Storage Rules

- Final disk paths are shown for core structure, but database/index paths are not specified.
- Where SQLite session memory lives is not specified.
- Where Obsidian vault lives is not specified.
- Where vector index files live is not specified.
- Where correction logs live is not specified.

---

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

1. Lock PD memory/skill/role infrastructure.
2. Author schema documents before code.
3. Implement state transition rules.
4. Implement command set.
5. Embed validation in each command.
6. Lock folder/naming convention.
7. Run real archive files through Phase 0.
8. Update schemas/profiles from real failures.

## Blocked Layers

- Retrieval blocked until approved knowledge records exist.
- Agents blocked until retrieval and approved records exist.
- Application blocked until commands work.
- Automation blocked until manual version validated.
- Database blocked until object schemas stable.

## Sequencing Implications

### Phase PD

Build memory and governance harness first.

### Phase 0

Build runtime objects and commands. Prove one real file can become a valid draft record.

### Phase 1

Upgrade extraction into multi-pass OCR + vision + merge + routing + correction logging.

### Phase 2

Build review/promotion, retrieval_text, vector index, production feedback.

### Phase 3

Build project management scripts, WIAS routing, project AI inference, full pipeline project test.

### Phase 4

Build Librarian, Researcher, Teacher as grounded prompt/command roles.

### Phase 5

Build local browser interface over existing commands and records.

## Runtime-First Requirements

- Commands must work without UI.
- State transitions must be enforced.
- Outputs must be valid before state changes.
- Logs must capture actions and failures.
- Real archive files must drive refinement.

## Governance-First Requirements

- Decisions must persist.
- Model roles must be constrained.
- Human authority must remain final.
- Promotion must require review.
- Agents cannot execute, write, or promote.

## Execution-First Requirements

- Object schemas precede database.
- Runtime commands precede app.
- Manual validation precedes automation.
- Record generation precedes retrieval.
- Retrieval precedes agents.

## Application Dependencies

The app depends on:

- `cis intake`
- `cis review`
- `cis promote`
- `cis project init`
- `cis project stage`
- `cis project attach`
- vector index query
- approved knowledge records
- project status data
- DAM filter logic
- agent command interface

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object 1 — Source Manifest

- **Purpose:** Intake control object created when a file enters CIS.
- **Lifecycle:** created at intake → classified → preprocessing plan assigned → tracks runtime state → links to downstream records.
- **Authority Source:** system-generated from source file and processing rules.
- **Related Objects:** Source, Processing Profile, Project Object, Knowledge Record, Logs.
- **States:** arrived, classified, preprocessed, extracted, normalized/draft-linked, needs_review.
- **Storage Implications:** stored in source container, likely `manifest.json`.

## Object 2 — Source

- **Purpose:** Raw material entering the system.
- **Lifecycle:** raw arrival → moved to incoming/source folder → processed into extraction units → remains preserved.
- **Authority Source:** source-authoritative; original file is never replaced by interpretation.
- **Related Objects:** Manifest, Processing Profile, Preprocessed Outputs, Knowledge Records.
- **States:** arrived, classified, preprocessed, extracted, failed/needs_review.
- **Storage Implications:** stored in `source/` inside source container.

## Object 3 — Project Object

- **Purpose:** Master container for creative work and context.
- **Lifecycle:** initialized → active → stage changes → sources attached → records approved → outputs archived → paused/archived.
- **Authority Source:** human/system hybrid; human controls project meaning and direction; system tracks state.
- **Related Objects:** Sources, Knowledge Records, WIAS Routing, Outputs, Agents, Dashboard.
- **States:** initiated, active, paused, archived; plus active WIAS stages.
- **Storage Implications:** project folder under `/mnt/projects/cis/projects/` plus project object metadata.

## Object 4 — Knowledge Record

- **Purpose:** Canonical structured output of extraction and review.
- **Lifecycle:** rough draft → normalized draft → reviewed/checked → approved → locked/deprecated/versioned.
- **Authority Source:** source-derived + system-generated + human-corrected; human corrections highest authority.
- **Related Objects:** Source Manifest, Source, Project Object, Retrieval Text, Vector Index, Agents, DAM.
- **States:** draft, checked, approved, locked, deprecated, rejected, needs_review.
- **Storage Implications:** JSON canonical + markdown mirror in source record folder.

## Object 5 — Processing Profile

- **Purpose:** Defines how a file type/source class should be handled.
- **Lifecycle:** assigned during classify → used in preprocess/extract/router → refined after archive failures.
- **Authority Source:** system/governance specification, updated by real archive evidence.
- **Related Objects:** Source Manifest, Router, Extraction Pipeline.
- **States:** assigned, missing, revised.
- **Storage Implications:** likely config file/profile registry.

## Object 6 — Review State

- **Purpose:** Trust and lifecycle marker for knowledge records.
- **Lifecycle:** draft → checked → approved → locked/deprecated.
- **Authority Source:** governance and human review.
- **Related Objects:** Knowledge Record, Retrieval Index, Agents.
- **States:** draft, checked, approved, locked, deprecated, rejected, needs_review.
- **Storage Implications:** field inside record and/or review log.

## Object 7 — Skill Document

- **Purpose:** Defines capability contracts: input, output, pass/fail, role behavior.
- **Lifecycle:** authored in PD → loaded by Harness Coordinator → used by humans/AI roles.
- **Authority Source:** governance/ADR system.
- **Related Objects:** Role Assignments, Agents, Harness Coordinator.
- **States:** draft, locked, revised.
- **Storage Implications:** stored in text/Obsidian/system docs.

## Object 8 — ADR

- **Purpose:** Locked architectural decision record.
- **Lifecycle:** decision captured → locked → loaded into session memory → prevents relitigation.
- **Authority Source:** human-approved governance.
- **Related Objects:** SQLite Memory, Obsidian Vault, Harness Coordinator.
- **States:** proposed, locked, superseded.
- **Storage Implications:** stored in memory database and human-readable vault.

## Object 9 — Harness Coordinator

- **Purpose:** Loads memory, skill documents, role assignments, and locked rules at session start.
- **Lifecycle:** run at session start → loads context → prepares role-specific working state.
- **Authority Source:** system governance scripts.
- **Related Objects:** SQLite, Obsidian, Skill Documents, ADRs, Role Assignments.
- **States:** not run, loaded, failed.
- **Storage Implications:** Python script and configuration files.

## Object 10 — Extraction Output

- **Purpose:** Raw model/tool output generated by OCR and visual extraction.
- **Lifecycle:** generated during extraction → cleaned by constraint pass → merged by normalization.
- **Authority Source:** model/tool output; not trusted as final.
- **Related Objects:** Tesseract Output, InternVL Output, Merge Layer, Knowledge Record.
- **States:** raw, flagged, cleaned, merged.
- **Storage Implications:** stored in `extracted/` or equivalent raw-output folder.

## Object 11 — Merge Record

- **Purpose:** Structured result of merging OCR and visual outputs into schema-conforming record.
- **Lifecycle:** created by `merge_record.py` → validated → becomes draft knowledge record.
- **Authority Source:** merge script plus field authority rules.
- **Related Objects:** OCR Output, Visual Output, Knowledge Record.
- **States:** assembled, validated, failed.
- **Storage Implications:** output to records folder as JSON + markdown.

## Object 12 — Router Task

- **Purpose:** Defines task type and model/tool routing decision.
- **Lifecycle:** task created → model selected → execution logged → output evaluated/escalated.
- **Authority Source:** route_task.py and processing profile.
- **Related Objects:** Processing Profile, Model Registry, Extraction Output, Logs.
- **States:** classified, routed, executed, escalated, completed, failed.
- **Storage Implications:** logs must record model/tool used.

## Object 13 — Correction Log Entry

- **Purpose:** Records human correction as reinforcement data.
- **Lifecycle:** generated during review → accumulated → analyzed for prompt/validation updates.
- **Authority Source:** human review action.
- **Related Objects:** Knowledge Record, Review Event, Prompt Rules, Validation Rules.
- **States:** logged, aggregated, applied.
- **Storage Implications:** stored in `corrections_log.json`.

## Object 14 — Retrieval Text

- **Purpose:** Search-optimized compressed representation of approved record content.
- **Lifecycle:** generated during approval → embedded into vector index → updated on record revision.
- **Authority Source:** normalized system output, approved by trust pipeline.
- **Related Objects:** Knowledge Record, Vector Index, Search Interface, Librarian.
- **States:** absent, generated, indexed, stale.
- **Storage Implications:** field in knowledge record and source for embedding.

## Object 15 — Vector Index Entry

- **Purpose:** Semantic-search representation of approved retrieval text.
- **Lifecycle:** generated by `build_index.py` → queried by search/agents → rebuilt when records change.
- **Authority Source:** approved knowledge records and embedding model.
- **Related Objects:** Knowledge Record, Retrieval Text, Librarian Agent.
- **States:** indexed, stale, rebuilt.
- **Storage Implications:** stored in ChromaDB or equivalent local vector database.

## Object 16 — Production Output Source

- **Purpose:** Creative output reintroduced as source material.
- **Lifecycle:** output created → `cis archive_output` → intake/extraction/review → knowledge record.
- **Authority Source:** project production artifact.
- **Related Objects:** Project Object, Source Manifest, Knowledge Record.
- **States:** output, archived_as_source, processed, approved.
- **Storage Implications:** stored as source with project-origin metadata.

## Object 17 — WIAS Routing Config

- **Purpose:** Maps production stages to tools, templates, processing profiles, knowledge categories, and outputs.
- **Lifecycle:** created in Phase 3 → read when project stage changes → refined through use.
- **Authority Source:** workflow/governance configuration.
- **Related Objects:** Project Object, Tools, Knowledge Records, Workflow Stage.
- **States:** configured, active, revised.
- **Storage Implications:** `wias_routing.json`.

## Object 18 — Librarian Agent

- **Purpose:** Retrieve approved/locked records relevant to query/project.
- **Lifecycle:** called via `cis ask librarian` → searches vector index → returns grounded results.
- **Authority Source:** approved knowledge records and agent skill document.
- **Related Objects:** Vector Index, Knowledge Records, Project Context.
- **States:** inactive, queried, returned results.
- **Storage Implications:** prompt/skill document plus logs.

## Object 19 — Researcher Agent

- **Purpose:** Synthesize retrieved records into project-relevant structured summaries.
- **Lifecycle:** called after retrieval → reads records → produces proposal/gap analysis.
- **Authority Source:** retrieved approved records plus role constraints.
- **Related Objects:** Librarian Results, Project Object, Knowledge Records.
- **States:** inactive, synthesizing, proposal output.
- **Storage Implications:** prompt/skill document plus logs.

## Object 20 — Teacher Agent

- **Purpose:** Guide user through application of approved learning/tutorial records.
- **Lifecycle:** called with task/tutorial context → generates grounded steps → human applies.
- **Authority Source:** approved tutorial/learning records.
- **Related Objects:** Knowledge Records, Project Stage, User Task.
- **States:** inactive, teaching session, proposal output.
- **Storage Implications:** prompt/skill document plus logs.

## Object 21 — Workbench Interface

- **Purpose:** Browser-based control surface over runtime commands and knowledge objects.
- **Lifecycle:** launched locally → user ingests/reviews/searches/asks agents → calls commands.
- **Authority Source:** existing runtime commands and records.
- **Related Objects:** Project, Source, Knowledge Record, Vector Index, Agents, DAM.
- **States:** active session, command running, review pending, output saved.
- **Storage Implications:** local web app code; no independent source of truth.

## Object 22 — DAM Record View

- **Purpose:** Filtered application view of records without project affiliation.
- **Lifecycle:** record has null project → appears in DAM → linked/promoted to project or remains unaffiliated → may be demoted back.
- **Authority Source:** knowledge record project linkage state.
- **Related Objects:** Knowledge Record, Project Object, Application Interface.
- **States:** unaffiliated, linked, promoted, demoted.
- **Storage Implications:** no separate storage; filtered view over knowledge base.

---

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did NOT exist before?

This file converts CIS from a layered architectural vision into a canonical, phase-gated implementation sequence.

The major delta is that CIS now has a clear answer to:

- what is built first
- why it must be built first
- what each phase physically creates
- what each phase unlocks
- what is explicitly forbidden before its prerequisites exist
- how a coworker can eventually operate the system without needing the architect present

The most important new understanding is:

**CIS becomes real only when the documentation is transformed into executable objects, commands, state transitions, validation rules, review gates, and feedback loops.**

Before this file, the system had architecture, workflow logic, object concepts, and application aspirations. After this file, the system has a buildable chronology:

1. First preserve memory and roles.
2. Then define schemas and executable commands.
3. Then run real archive material through those commands.
4. Then build multi-pass intelligence extraction.
5. Then form approved searchable knowledge.
6. Then connect knowledge to projects and WIAS workflow.
7. Then introduce bounded agents grounded in approved records.
8. Then build the application as a control surface over the already-working runtime.

The file also clarifies the central implementation principle:

**The application is not the system. The application is only the visible control room over a factory that must already run.**

It introduces a practical division between:

- runtime engine: commands, schemas, states, validation, logs
- knowledge warehouse: approved records, retrieval text, vector index
- production scheduler: project object, WIAS routing, project attachments
- specialized workers: Librarian, Researcher, Teacher
- control room: Workbench UI, Project Dashboard, DAM view

The strongest topology correction is that CIS is not built by jumping to agents or UI. It is built by making one file travel through a governed path from raw material to draft knowledge record, then improving that path until it becomes reliable enough to scale.

The most important new canonical chain is:

**raw file → source manifest → processing profile → preprocessing → OCR/vision extraction → constraint enforcement → merge/normalization → draft knowledge record → human review → approved record → retrieval text → vector index → agent use → project output → archive_output feedback → new knowledge.**

The deepest build-plan implication is:

**Every later layer is blocked until its substrate exists.**

- No database before schemas stabilize.
- No retrieval before records exist.
- No agents before approved knowledge exists.
- No interface before commands work.
- No automation before manual validation succeeds.

This file therefore provides the missing implementation-grade bridge between CIS architecture and CIS construction.
