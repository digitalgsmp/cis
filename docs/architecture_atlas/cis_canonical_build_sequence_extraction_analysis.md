# CIS Canonical Build Sequence — Extraction Analysis

Source document: `CIS_Canonical_Build_Sequence.md`  
Extraction mode: Implementation-grade architectural topology extraction  
Purpose: Build-plan, topology atlas, dependency map, runtime diagram, governance diagram, and application-sequencing input

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Build Order Is Dependency-Forced, Not Preference-Based

- **Architectural Significance:** The CIS build sequence is not a flexible roadmap. It is a forced dependency graph governed by stream order, execution-layer maturity, and feedback-loop activation.
- **Affected Layers:** Intelligence, Knowledge, Workflow, Agents, Application, Governance, Execution.
- **Dependency Impact:** Intelligence must precede Knowledge; Knowledge must precede Workflow; Workflow must precede Agents; Agents must precede Application. The Execution Layer underpins all higher layers.
- **Build Impact:** The system cannot skip ahead to Application or Agents without invalidating downstream behavior.
- **Runtime Impact:** Runtime must enforce prerequisite completion before dependent actions become available.

## Discovery Name: Phase PD Is a Required Pre-Development Harness

- **Architectural Significance:** A new layer exists before implementation: the harness that stabilizes memory, skills, protocols, and AI-session coordination.
- **Affected Layers:** Governance, Documentation Loop, Memory, Skill Contracts, AI Role Coordination.
- **Dependency Impact:** Phase 0 depends on Phase PD. Capability development cannot begin until session context can be reconstructed reliably.
- **Build Impact:** Memory and protocol infrastructure become build prerequisites, not supporting documentation.
- **Runtime Impact:** Session-start behavior must load memory, skill documents, role protocols, and context before execution.

## Discovery Name: Execution Layer Is the Primary Current Blocker

- **Architectural Significance:** The headless runtime is missing as a unified system. Existing shell scripts and manual steps are insufficient.
- **Affected Layers:** Workflow, Intelligence, Knowledge, Application, Agents.
- **Dependency Impact:** Every layer above Intelligence depends on a deterministic execution layer.
- **Build Impact:** Phase 0 becomes the immediate build priority.
- **Runtime Impact:** CIS requires commands, state transitions, validation, logging, and object contracts before UI or automation.

## Discovery Name: Feedback Loops Are Architectural Determinants

- **Architectural Significance:** Four loops define CIS identity rather than acting as optional future features.
- **Affected Layers:** Intake, Workflow, Knowledge, Reinforcement, Documentation, Application.
- **Dependency Impact:** Loops activate in sequence: Documentation Loop in Phase PD; Material and System Learning Loops around Phase 1; Workflow Loop in Phases 2–3.
- **Build Impact:** Build order must intentionally activate loops, not retrofit them later.
- **Runtime Impact:** Runtime must capture signals from source intake, user correction, production use, and documentation updates.

## Discovery Name: Application Layer Is Exposure, Not Creation

- **Architectural Significance:** The application layer must not be built to make CIS exist. It exposes a system that already works.
- **Affected Layers:** Application, Execution, Knowledge, Agents, Workflow.
- **Dependency Impact:** App depends on stable runtime, dense knowledge, operational agents, and observable feedback loops.
- **Build Impact:** Application development is deferred until Phase 5.
- **Runtime Impact:** UI buttons must call existing runtime operations instead of inventing system behavior.

## Discovery Name: DAM Emerges as an Unaffiliated Knowledge Surface

- **Architectural Significance:** The DAM is not separate from the Knowledge Layer. It is the unaffiliated view of the same knowledge base.
- **Affected Layers:** Knowledge, Application, Project System, Asset Management.
- **Dependency Impact:** DAM requires knowledge records with nullable `project_id`, link/promote/demote paths, and project affiliation rules.
- **Build Impact:** The Application Layer must support both project-scoped and unaffiliated knowledge views.
- **Runtime Impact:** Records can move between unaffiliated DAM state and project-affiliated asset state without data loss.

---

# 2. TOPOLOGY MUTATIONS

## New Layers

- **Phase PD / Pre-Development Harness:** A prerequisite meta-layer that stabilizes memory, skills, protocols, and coordinator behavior before implementation.
- **Harness Coordinator:** A session-start coordinator that loads correct memory, skills, and role protocols.
- **Execution Layer Foundation:** A headless runtime layer between conceptual workflow and application UI.
- **DAM Surface:** A knowledge-base navigation mode for unaffiliated records.

## Split Layers

- **Workflow vs Execution:** Workflow defines what should happen; Execution defines what command runs, what state changes, and what output validates.
- **Application vs Runtime:** Application exposes; runtime performs.
- **Knowledge vs Raw Archive:** Raw archive material is not knowledge until processed into approved or reviewable `knowledge_record` objects.
- **Agents vs Intelligence:** Agents are structured user-facing role behaviors; Intelligence provides extraction, routing, reasoning, and transformation.

## Runtime Bridges

- Source Manifest bridges raw material to processing.
- Processing Profile bridges source type to extraction behavior.
- Processing Plan bridges routing to command execution.
- `knowledge_record` bridges extraction to knowledge retention.
- Project Object bridges knowledge to workflow.
- DAM View bridges unaffiliated records to project promotion.

## Orchestration Changes

- Orchestration is no longer implied by workflow text.
- Commands become state-transition operators.
- Validation becomes a required runtime gate.
- Real archive trials become schema-normalization triggers.

## Governance Expansion

- Contract-first discipline governs schema before code.
- AI role contracts are formalized across Gemini, Claude, ChatGPT, and Local Qwen.
- Human approval is required for promotion.
- Field authority and mutability rules govern record modification.

## Object-Model Mutations

- Canonical objects become implementation prerequisites:
  - Source Manifest
  - Project Object
  - `knowledge_record`
  - Processing Profile
  - Processing Plan
  - Review State
  - DAM Record / Unaffiliated Knowledge Record

## Workflow / Execution Separation

- Workflow remains the creative movement map.
- Execution becomes the enforceable runtime contract.
- Application can only surface execution once execution exists.

## Project-Container Evolution

- Project remains the workflow anchor.
- Project consumes records, produces outputs, and feeds knowledge back into the system.
- Project affiliation is mutable for knowledge records; records can be promoted to projects or demoted back to DAM.

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisites

- Phase PD must precede all build work.
- Memory and skill contracts must exist before session-stable implementation.
- Execution Layer must exist before Workflow, Agents, and Application can become operational.
- Object schemas must be locked before commands are built.
- State graphs must exist before commands become meaningful.
- Real archive testing must occur before object model normalization.
- Merge Layer must exist before reliable knowledge formation.
- Approved records must exist before agents can operate safely.
- Dense retrieval must exist before Teacher and Librarian become useful.

## Sequencing Constraints

1. Phase PD → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5.
2. Schema → state graph → command → validation → archive trial → normalization.
3. Intake → OCR/visual extraction → merge → structured record → review → retrieval.
4. Project object → WIAS stage inference → source linking → production output → knowledge return.
5. Librarian → Researcher → Teacher → Producer/Orchestrator.

## Circular Dependencies

- Application feels necessary for usability, but it depends on runtime stability; minimal workbench can only emerge after runtime works.
- Knowledge is needed by Workflow, but Knowledge is created through Intelligence and refined through Workflow use.
- Agents need Knowledge and Workflow, but agent use will later improve both.
- Documentation defines build behavior, but real behavior updates documentation.

## Unstable Dependencies

- Model quality is not stable until benchmarked against real archive material.
- Processing profiles are provisional until archive heterogeneity reveals missing cases.
- Schemas are locked before code, but normalized after real runs.
- Retrieval quality depends on record quality and review state density.

## Runtime Blockers

- Unified execution layer absent.
- Merge layer absent.
- Intelligent routing not yet implemented.
- Vector retrieval not yet implemented.
- Application cannot exist as a reliable control surface yet.
- Agents cannot operate on raw or unapproved files.

## Orchestration Bottlenecks

- Human currently remains the transport layer across AI sessions unless Phase PD resolves memory/context loading.
- Manual script use remains fragile until commands are standardized.
- Record quality remains inconsistent until merge and validation are unified.
- Knowledge cannot scale until processing and review states are enforceable.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## Commands

Required minimal command set:

- `cis intake <path>`
  - Creates source manifest.
  - Moves source to `arrived` state.

- `cis classify <source_id>`
  - Assigns processing profile.
  - Moves source to `classified`.

- `cis preprocess <source_id>`
  - Extracts text, pages, images, metadata.
  - Moves source to `preprocessed`.

- `cis extract <source_id>`
  - Runs intelligence extraction.
  - Produces draft `knowledge_record`.

- `cis review <record_id>`
  - Human review entry point.
  - Supports approve, reject, edit, check, lock, deprecate.

- `cis project init`
  - Creates Project Object.
  - Sets initial status and WIAS stage inference.

## States

### Source States

- arrived
- classified
- preprocessed
- extracted
- normalized
- draft
- reviewed
- approved
- rejected

### Project States

- initiated
- active
- paused
- archived

### Record States

- draft
- checked
- approved
- locked
- deprecated

### Failure / Review States

- needs_review
- rejected
- retry_required
- validation_failed

## Transitions

- A command is a validated state transition.
- No object may move outside its allowed state graph.
- Every transition must be logged.
- Promotion requires human review.
- Failure blocks downstream use.

## Runtime Contracts

Each command requires:

- required inputs
- required outputs
- allowed failure conditions
- explicit state change
- log entry
- validation result

## Orchestration Logic

1. Receive input or trigger.
2. Create or load canonical object.
3. Determine current state.
4. Execute allowed command.
5. Validate output.
6. Update state if valid.
7. Flag failure if invalid.
8. Log all actions.

## Validation Behavior

Invalid if:

- required fields are missing
- unsupported claims are present
- schema is broken
- uncertainty is omitted where ambiguity exists
- hallucination indicators appear
- output is too short or incomplete
- processing profile mismatch occurs

## Pass / Fail Structures

- PASS: output exists, schema validates, state updates, log entry created.
- FAIL: no knowledge storage, reason logged, state moves to `needs_review` or `retry_required`.

## Retry / Escalation Logic

- Retry with same profile when failure is procedural.
- Escalate model tier when failure is quality-related.
- Send to human review when failure persists or ambiguity cannot be resolved.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

- Human authority is final for promotion.
- AI proposes only.
- User-authoritative fields override system-generated fields.
- Source-authoritative fields override interpretation.
- System fields fill gaps but remain regenerable.

## Review States

- `draft`: fresh system output.
- `checked`: basic human sanity check complete.
- `approved`: accepted for workflow use.
- `locked`: stable, high trust, no silent overwrite.
- `deprecated`: retained but not preferred.

## Promotion Logic

- Intelligence may create draft records only.
- Draft records do not become truth.
- Human review promotes records.
- Approved and locked records influence future structure and retrieval.

## Rejection Paths

- Validation failure → needs_review.
- Hallucination → reject or retry after cleanup.
- Unsupported claim → reject or mark uncertainty.
- Schema failure → retry or repair.
- Low-confidence output → review before storage.

## Trust Enforcement

- Retrieval priority depends on review state.
- Agents may operate only on validated knowledge records.
- Draft records are low-trust and cannot define system truth.

## Hallucination Controls

- Schema validation.
- Required uncertainty fields.
- Source lineage.
- Model provenance.
- Human review.
- Escalation only after local failure.

## Provenance Enforcement

Every record or command log must track:

- source path
- source unit
- model used
- processing profile
- prompt or command version
- timestamp
- validation result
- state transition

## Validation Contracts

Validation is non-optional. Outputs that fail validation cannot enter the Knowledge Layer as approved system knowledge.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

- Knowledge is generated by Intelligence.
- Raw materials are not knowledge.
- `knowledge_record` is the atomic unit.
- Human review determines trust level.
- Approved records influence future structure.

## Retrieval Structure

- Retrieval indexes `retrieval_text`, not raw files.
- Chunks point back to `record_id`.
- Metadata includes category, subject, tags, project_id, source_unit, model_used, version.
- Retrieval ranking considers review state.

## Indexing Implications

- Vector index is built only after normalized approved records exist.
- Draft records may be searchable at low priority but should not steer agents as truth.
- Locked records receive highest retrieval priority.

## Normalization Rules

Records normalize into workbook/application views:

- Research
- Reference
- Learning
- Template
- Checklist
- Asset / DAM record

The full JSON remains canonical.

## Ontology / Spine Implications

- Knowledge spine emerges from processed records.
- Categories stabilize through repeated correction and approval.
- DAM and project views are two surfaces over the same record base.

## Chunking Logic

- Chunk `retrieval_text`.
- Preserve record_id.
- Preserve source_unit.
- Preserve project context.
- Preserve model and version metadata.

## Reinforcement Behavior

- Model output → human/system review → accept/reject/correct → pattern memory → improved future proposals.
- Only approved records can teach the system.
- Rejected patterns are tracked to reduce repeated failure.

## Project Linkage

- Affiliated records carry project_id.
- Unaffiliated records carry null project_id and surface in DAM.
- DAM records can be linked to a project or promoted into a standalone project.
- Affiliated records can be demoted back to DAM without data loss.

## Stabilization Loops

- Material Loop stabilizes intake.
- System Learning Loop stabilizes extraction quality.
- Workflow Loop stabilizes project use.
- Documentation Loop stabilizes build rules.

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

First application surface must be a knowledge-building workbench, not a dashboard.

Required panels:

1. Project Panel
2. Source Panel
3. Structure Panel
4. Review Panel
5. Knowledge Output Panel

## Interface Panels

### Project Panel

- create project
- view project state
- attach materials
- show WIAS stages

### Source Panel

- preview source
- show extracted signals
- display detected type and confidence

### Structure Panel

- show proposed fields
- show tags
- show relationships
- expose uncertain/missing structure

### Review Panel

- approve
- reject
- edit
- mark uncertainty
- promote/demote trust state

### Knowledge Output Panel

- display structured record
- show project linkage
- show reuse readiness

## Operator Actions

- ingest source
- classify source
- trigger processing
- review records
- approve or reject records
- link DAM record to project
- promote DAM record to standalone project
- demote affiliated record back to DAM

## Runtime Visibility Needs

- current source state
- current record state
- validation results
- model used
- retry/escalation status
- source-to-record lineage
- project linkage

## Workflow Exposure

The interface must expose, not invent:

- source intake
- processing status
- review state
- knowledge record output
- WIAS stage progress
- feedback-loop signals

## Project-Centered Interaction

- Project is primary entry point.
- Knowledge, workflow, agents, and outputs attach to active project.
- DAM exists for materials not yet project-affiliated.

## Application / Runtime Bridges

- UI button → existing command.
- UI record → canonical JSON object.
- UI status → runtime state.
- UI validation result → validation log.

---

# 8. FEEDBACK LOOP DISCOVERIES

## Material Loop

Source material → intake → extraction → structure proposal → review → knowledge object → retrieval/reuse → better future intake.

- Activates when intake commands exist and extraction produces draft records.
- Requires review and promotion path.
- Becomes visible when records influence later intake.

## Workflow Loop

Project need → source selection → processing → output → production use → archive return.

- Activates when production outputs return to the Knowledge Layer.
- Requires project linkage and WIAS stage context.
- Makes CIS improve through creative work, not only archive intake.

## System Learning Loop

Model output → correction → accepted structure → better future proposals.

- Activates when corrections are tracked.
- Requires approved outputs as precedent.
- Rejected patterns must also be remembered.

## Documentation Loop

Real behavior → design insight → doc update → new build rule → new behavior.

- Activates in Phase PD.
- Requires memory, skill docs, ADRs, and role protocols.
- Prevents session fragmentation.

## Retrieval-Improvement Loop

Approved record density → better retrieval → better project support → better outputs → more approved records.

## Archive-Learning Loop

Archive heterogeneity → profile gaps → processing profile updates → better routing → cleaner records.

## Continuity / Memory Loop

Session behavior → stored decisions → context loading → improved continuity → fewer reconstruction burdens.

## Project-Output Feedback Loop

Creative output → archived project knowledge → future reference / template / learning record → improved production.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridges

- Unified headless execution layer.
- Command dispatcher.
- State-transition engine.
- Validation engine.
- Source-to-record lineage tracker.
- UI-to-runtime bridge.

## Undefined Objects

- Final source manifest schema still needs implementation locking.
- Processing plan object needs detailed executable fields.
- DAM record state may need a formal schema field or mode flag.
- Harness Coordinator object/contract needs definition.
- Skill document contract object needs formal representation.

## Unstable Schemas

- Processing profiles remain provisional until archive trials.
- Knowledge record fields may require normalization after real material.
- WIAS stage metadata may need expansion based on project use.
- Agent input/output contracts remain dependent on Phase 2–3 outputs.

## Unresolved Orchestration

- No unified command runner yet.
- No runtime queue or job state described in this roadmap.
- No automatic escalation manager implemented.
- No documented retry policy implementation beyond conceptual rules.

## Unresolved Routing

- Intelligent routing between local and frontier models not implemented.
- Model benchmark protocol needs operationalization.
- Qwen3-VL-32B FP8 test path remains a future task.
- Frontier API escalation remains conditional and unbuilt.

## Missing Governance

- Promotion UI/process not implemented.
- Review audit trail not yet operational.
- Human approval checkpoint needs runtime representation.
- Contract-first enforcement across docs and code needs tooling.

## Missing Validation Layers

- Schema validation engine.
- Hallucination detection heuristics.
- Required uncertainty checks.
- Retrieval-readiness validator.
- State-transition validator.

## Unresolved Application Surfaces

- Workbench not built.
- DAM view not built.
- Agent interface not built.
- Project-centered control surface not built.
- Feedback loops not yet observable in UI.

## Unresolved Storage Rules

- DB vs filesystem remains staged: filesystem first, database later.
- Record family storage must be enforced.
- Version retention and current-version selection need runtime implementation.
- DAM demotion/promotion storage effects need strict contract.

---

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

1. Complete Phase PD harness.
2. Lock canonical schemas.
3. Define state graphs.
4. Build core command set.
5. Implement validation layer.
6. Run real archive trial.
7. Normalize object model from real results.

## Blocked Layers

- Intelligence scaling blocked by missing execution foundation.
- Knowledge retrieval blocked by incomplete merge/normalization.
- Workflow system blocked by insufficient retrieval and project linkage.
- Agents blocked by lack of validated knowledge and workflow context.
- Application blocked by absence of stable runtime and agents.

## Sequencing Implications

Build sequence must remain:

1. Phase PD — Harness
2. Phase 0 — Execution Layer Foundation
3. Phase 1 — Intelligence Extraction Pipeline
4. Phase 2 — Knowledge Formation and Retrieval
5. Phase 3 — Workflow System
6. Phase 4 — Bounded Agents
7. Phase 5 — Application Layer

## Runtime-First Requirements

- Commands before UI.
- State transitions before automation.
- Validation before knowledge promotion.
- Filesystem objects before database.
- Real archive trial before schema normalization.

## Governance-First Requirements

- Human approval gates.
- Field authority rules.
- Review states.
- Versioning rules.
- No silent overwrite.
- Contract-first schema locking.

## Execution-First Requirements

- Source manifest creation.
- Processing profile assignment.
- Preprocessing outputs.
- Extraction outputs.
- Merge outputs.
- Validation outputs.
- State/log outputs.

## Application Dependencies

Application requires:

- stable command layer
- stable object schema
- stable state model
- stable knowledge records
- retrieval system
- validated agents
- visible feedback loops

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object: Source Manifest

- **Purpose:** Controls ingestion behavior and source identity before extraction.
- **Lifecycle:** created at intake → classified → preprocessing plan assigned → updated through processing.
- **Authority Source:** source-authoritative and system-authoritative.
- **Related Objects:** Source, Processing Profile, Processing Plan, Project Object, knowledge_record.
- **States:** arrived, classified, preprocessed, extracted, normalized.
- **Storage Implications:** Must exist before extraction; stored in source container metadata.

## Object: Project Object

- **Purpose:** Persistent container for workflow, knowledge, tasks, outputs, and context.
- **Lifecycle:** initiated → active → paused → archived.
- **Authority Source:** user-authoritative for project intent and direction; system-authoritative for inferred constraints.
- **Related Objects:** Sources, knowledge_records, WIAS stages, assets, agents, outputs.
- **States:** initiated, active, paused, archived.
- **Storage Implications:** Project metadata must support linked records, sources, stages, outputs, and DAM affiliations.

## Object: knowledge_record

- **Purpose:** Atomic canonical knowledge unit produced by extraction and review.
- **Lifecycle:** draft → checked → approved → locked or deprecated; versioned over time.
- **Authority Source:** source, system, and user authority combined under mutability rules.
- **Related Objects:** Source Manifest, Project Object, Retrieval Chunk, DAM View, Agent Context.
- **States:** draft, checked, approved, locked, deprecated.
- **Storage Implications:** JSON canonical; markdown mirror; record family folder; no loose files; version-safe storage.

## Object: Processing Profile

- **Purpose:** Defines how a source type is handled.
- **Lifecycle:** assigned during classification; refined after archive trials.
- **Authority Source:** system-authoritative contract.
- **Related Objects:** Source Manifest, Processing Plan, Router, Command Set.
- **States:** provisional, active, revised.
- **Storage Implications:** Must be inspectable and reusable; should not be guessed per file.

## Object: Processing Plan

- **Purpose:** Defines execution steps for a given processing profile.
- **Lifecycle:** loaded during preprocessing/extraction; updated based on failures.
- **Authority Source:** system/governance contract.
- **Related Objects:** Commands, Router, Validation Layer.
- **States:** planned, running, completed, failed.
- **Storage Implications:** Should be logged with execution outputs.

## Object: Review State

- **Purpose:** Governs trust, retrieval priority, and promotion path.
- **Lifecycle:** draft → checked → approved → locked / deprecated.
- **Authority Source:** human-governed, system-enforced.
- **Related Objects:** knowledge_record, Retrieval Index, Agents.
- **States:** draft, checked, approved, locked, deprecated.
- **Storage Implications:** Must be stored on every record and used in retrieval ranking.

## Object: Retrieval Chunk

- **Purpose:** Embeddable/searchable unit derived from `retrieval_text`.
- **Lifecycle:** generated after normalization; re-generated on new record version.
- **Authority Source:** derived from canonical knowledge_record.
- **Related Objects:** knowledge_record, Vector Index, Retrieval System.
- **States:** current, superseded.
- **Storage Implications:** Must retain record_id, chunk_id, metadata, model_used, version.

## Object: DAM Record / Unaffiliated Knowledge Record

- **Purpose:** Represents knowledge material not attached to a project.
- **Lifecycle:** unaffiliated → linked to project OR promoted to standalone project; may be demoted from project back to DAM.
- **Authority Source:** review-stage human/system decision.
- **Related Objects:** knowledge_record, Project Object, Application DAM View.
- **States:** unaffiliated, affiliated, promoted, demoted.
- **Storage Implications:** `project_id = null` indicates DAM visibility; demotion must not delete data.

## Object: Harness Coordinator

- **Purpose:** Loads correct memory, skills, and protocols at AI-session start.
- **Lifecycle:** invoked at session start; validates context readiness.
- **Authority Source:** Phase PD governance.
- **Related Objects:** SQLite Memory, Obsidian Shell, Skill Documents, ADRs, Role Protocols.
- **States:** unloaded, loading, ready, failed.
- **Storage Implications:** Requires machine-readable context pointers and session-start logs.

## Object: Skill Document

- **Purpose:** Two-tier contract document defining capability behavior, inputs, outputs, and validation.
- **Lifecycle:** drafted → reviewed → locked → loaded by coordinator.
- **Authority Source:** contract-first governance.
- **Related Objects:** Harness Coordinator, Execution Commands, Streams, ADRs.
- **States:** draft, locked, superseded.
- **Storage Implications:** Header/full split required for progressive disclosure.

## Object: AI Role Protocol

- **Purpose:** Defines scope and output expectations for model roles.
- **Lifecycle:** locked in Phase PD; invoked per session/task.
- **Authority Source:** ADRs and protocol layer.
- **Related Objects:** Gemini, Claude, ChatGPT, Local Qwen, Harness Coordinator.
- **States:** active, revised, deprecated.
- **Storage Implications:** Must be loadable and auditable across sessions.

---

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did NOT exist before?

This file turns CIS from a broad architectural system into a forced implementation sequence.

The most important new understanding is that CIS cannot be built by choosing the most visible or desirable layer first. The build sequence is determined by prerequisite dependencies, execution-layer maturity, and feedback-loop activation. The Application Layer, despite being the most tangible control surface, cannot safely precede the headless runtime that gives it stable behavior.

The file also makes Phase PD explicit as a required pre-development harness. This is a major topology mutation. Before this roadmap, the system could be understood as beginning with execution or intelligence activation. After this roadmap, it begins with memory, skill contracts, role protocols, and a coordinator that prevents AI-session fragmentation. Documentation continuity becomes part of runtime readiness.

The Execution Layer is confirmed as the current primary blocker. It is not a UI, not a database, and not a finished application. It is the layer that converts workflow intent into deterministic commands, state transitions, validation, logging, and canonical object movement. This reframes the next build target: not “build the app,” but “make the workflow enforceable.”

The roadmap clarifies that schemas must be locked before code, but normalized after real archive use. This resolves the tension between contract-first design and discovery-driven structure. CIS requires a minimal backbone before execution, but the archive is allowed to reshape the object model after real processing exposes missing profiles, fields, and validation needs.

The four feedback loops are elevated from conceptual descriptions into build-order determinants:

- Documentation Loop starts immediately in Phase PD.
- Material Loop starts when intake and extraction produce draft records.
- System Learning Loop starts when corrections are tracked and approved patterns influence future proposals.
- Workflow Loop starts when project outputs return to the Knowledge Layer.

This means CIS is not built as a static architecture. It is built as a loop-activating system.

The document also introduces a more precise Application Layer target: first a knowledge-building workbench, then a broader project-centered control surface. It adds the DAM as an unaffiliated knowledge surface, giving non-project material a permanent home and a promotion/demotion path without data loss.

In build-plan terms, the new operational truth is:

Phase PD must stabilize session memory and contracts.  
Phase 0 must implement the headless execution runtime.  
Phase 1 must stabilize extraction, merge, routing, and reinforcement.  
Phase 2 must produce reviewed, retrieval-ready knowledge.  
Phase 3 must close the project/workflow loop.  
Phase 4 may then introduce bounded agents.  
Phase 5 may then expose the system through application surfaces.

The architectural delta is therefore:

CIS is no longer only a layered creative intelligence architecture.  
It is now a governed, dependency-forced, feedback-loop-activated runtime build sequence whose immediate blocker is the Execution Layer Foundation.
