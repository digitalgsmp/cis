# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Phase PD Becomes a Real Pre-Development Harness, Not a Conceptual Planning Phase

- **Architectural Significance**
  - Phase PD is clarified as the infrastructure layer that lets CIS accumulate instead of resetting across sessions.
  - It contains the persistent memory layer, human-readable vault, role/skill documents, protocols, and harness coordinator.
  - It is not creative production and not the CIS application itself. It is the scaffolding required before CIS can be built reliably.

- **Affected Layers**
  - Governance Layer
  - Memory / Continuity Layer
  - Documentation Loop
  - Platform Infrastructure
  - Future Application Layer

- **Dependency Impact**
  - All later phases depend on Phase PD because every later build action requires persistent decisions, session continuity, and locked contracts.
  - The file invalidates any build order that begins with the application surface, agents, or raw pipeline commands before persistent memory exists.

- **Build Impact**
  - Build begins with `/mnt/projects/cis/memory/cis_memory.db`, `cis_log.py`, `cis_harness.py`, Obsidian/GitHub sync, ADR recording, and role skill documents.
  - The build sequence is split into:
    - **Track 1 — Platform Infrastructure**
    - **Track 2 — CIS Build**

- **Runtime Impact**
  - Session start becomes an explicit runtime ritual through `cis-start`.
  - Session memory becomes queryable through SQLite instead of dependent on chat history.
  - ADRs and session logs become runtime-readable system state.

---

## Discovery Name: CIS Build Order Must Be Split from Platform Infrastructure Build Order

- **Architectural Significance**
  - The transcript corrects a major conceptual conflation: building CIS and building the infrastructure that hosts CIS are two different missions.
  - Platform Infrastructure is the factory site, utilities, storage layout, runtime environment, persistent memory, and operational tooling.
  - CIS is the creative studio system running on top: intake, extraction, knowledge records, review, retrieval, agents, and workbench.

- **Affected Layers**
  - Infrastructure Layer
  - Execution Layer
  - Governance Layer
  - Application Layer
  - Tool Layer

- **Dependency Impact**
  - CIS cannot be stable without a stable platform substrate.
  - Model storage, cache storage, mounted archive access, runtime environment activation, and persistent memory precede execution-layer scripts.

- **Build Impact**
  - Hardware/storage work becomes part of Phase PD infrastructure, not a side task.
  - `/mnt/models`, `/mnt/cache`, `/mnt/projects`, `/mnt/archive`, and `/mnt/projects/cis` become named infrastructure surfaces.

- **Runtime Impact**
  - Runtime execution is no longer abstract. It is tied to real mount points, real Python environments, real model paths, and real shell aliases.

---

## Discovery Name: Model Quality Is a Foundational System Gate

- **Architectural Significance**
  - CIS usefulness depends on the quality of generated knowledge records.
  - The 32B model pivot is not a tool preference; it is a viability condition for the entire system.
  - Smaller visual models were deemed unacceptable because they produced hallucinated, weak, or unusable descriptions.

- **Affected Layers**
  - Intelligence Layer
  - Knowledge Layer
  - Governance Layer
  - Execution Layer
  - Routing Layer

- **Dependency Impact**
  - Extraction infrastructure must be built around the model quality threshold, not around whichever model is easiest to run.
  - Runtime selection becomes a governance decision, not a convenience decision.

- **Build Impact**
  - Qwen2.5-VL-32B becomes the primary extraction model.
  - Runtime implementation must support quantized 32B inference on RTX 4090.
  - Infrastructure must support `/mnt/models/huggingface`, `/home/eric/gpu-test`, `bitsandbytes`, `transformers`, and a VRAM-fragmentation mitigation flag.

- **Runtime Impact**
  - Full bfloat16 Qwen2.5-VL-32B cannot load on RTX 4090.
  - FP8 attempt is insufficient.
  - 4-bit bitsandbytes via transformers succeeds.
  - `cis_extract.py` must run with `PYTORCH_ALLOC_CONF=expandable_segments:True` and the correct environment path.

---

## Discovery Name: Phase 0 Execution Layer Moves from Missing Blocker to Proven Pipeline

- **Architectural Significance**
  - The execution layer was initially identified as the primary blocker for application development.
  - By the end of the transcript, Phase 0 is proven through five concrete commands.
  - CIS crosses from architectural documentation into executable pipeline behavior.

- **Affected Layers**
  - Execution Layer
  - Workflow Layer
  - Knowledge Layer
  - Governance Layer
  - Application Layer

- **Dependency Impact**
  - Application, retrieval, and agent layers are no longer blocked by the total absence of a pipeline, but remain blocked by missing review and validation completion.
  - `cis_review.py` becomes the next required bridge.

- **Build Impact**
  - Five scripts are created and tested:
    - `cis_intake.py`
    - `cis_classify.py`
    - `cis_preprocess.py`
    - `cis_extract.py`
    - `cis_normalize.py`
  - A real archive source moves through intake to canonical record output.

- **Runtime Impact**
  - Runtime path becomes:
    - source file
    - manifest
    - classification
    - preprocessing
    - extraction
    - normalization
    - knowledge record JSON
    - markdown mirror
    - draft review state

---

## Discovery Name: Source Manifest Becomes the Intake Control Object

- **Architectural Significance**
  - The manifest is promoted from metadata to the control object for every source.
  - No processing step should run without a valid manifest.
  - Source identity, file hash, state history, and project linkage must live before extraction begins.

- **Affected Layers**
  - Intake Layer
  - Execution Layer
  - Governance Layer
  - Knowledge Layer

- **Dependency Impact**
  - `cis_intake.py` becomes the first runtime command because it creates the manifest.
  - State transitions depend on manifest existence.

- **Build Impact**
  - Every ingested source receives a processing folder and manifest before any model work occurs.
  - Manifest validation becomes a prerequisite for downstream commands.

- **Runtime Impact**
  - Source state begins at `arrived`.
  - Manifest records SHA256 hash, source identity, source ID, and status history.

---

## Discovery Name: Persistent Memory Moves from Chat Dependency to Local SQLite Object

- **Architectural Significance**
  - Architectural memory is no longer dependent on frontier-model chat history.
  - SQLite becomes the machine-queryable continuity layer.
  - Obsidian remains the readable shell.

- **Affected Layers**
  - Governance Layer
  - Memory Layer
  - Documentation Layer
  - Harness Coordinator

- **Dependency Impact**
  - Future sessions depend on `cis-start` and database state rather than transcript recall.
  - ADRs, session logs, corrections, and schema versions become queryable objects.

- **Build Impact**
  - `/mnt/projects/cis/memory/cis_memory.db` is created.
  - Tables created:
    - `decisions`
    - `session_log`
    - `corrections`
    - `schema_versions`
  - `cis_log.py` becomes the write interface.
  - `cis_harness.py` becomes the session context loader.

- **Runtime Impact**
  - `cis-log` records decisions, sessions, and corrections.
  - `cis-start` prints phase, last session, decisions, storage map, runtime status, and project tree.

---

## Discovery Name: Storage Architecture Becomes a Governance Requirement

- **Architectural Significance**
  - Storage is not incidental infrastructure; it directly affects model viability and system reliability.
  - Model weights, cache, project files, and archive materials must not compete with the OS disk.

- **Affected Layers**
  - Infrastructure Layer
  - Runtime Layer
  - Intelligence Layer
  - Knowledge Layer

- **Dependency Impact**
  - Model inference cannot be scaled until storage is separated.
  - Archive-driven development requires stable `/mnt/archive` access.

- **Build Impact**
  - Drives are assigned canonical purposes:
    - `/` = OS and installed software
    - `/mnt/projects` = CIS project files
    - `/mnt/models` = model weights and runtimes
    - `/mnt/cache` = system/cache files
    - `/mnt/archive` = source archive

- **Runtime Impact**
  - Environment variables:
    - `HF_HOME=/mnt/models/huggingface`
    - `OLLAMA_MODELS=/mnt/models/ollama`
  - Cache symlink:
    - `~/.cache -> /mnt/cache/.cache`

---

## Discovery Name: Human-Readable Documentation and Machine Memory Must Mirror Each Other

- **Architectural Significance**
  - Obsidian and SQLite are not redundant; they serve different authority surfaces.
  - SQLite stores machine-queryable memory.
  - Obsidian/GitHub stores human-readable canonical documentation.

- **Affected Layers**
  - Governance Layer
  - Memory Layer
  - Documentation Loop
  - Application Layer

- **Dependency Impact**
  - Decisions must be recorded both in database and readable docs.
  - Git sync becomes a continuity mechanism.

- **Build Impact**
  - Obsidian vault is extended rather than recreated.
  - GitHub credentialing and sync become part of Phase PD infrastructure.

- **Runtime Impact**
  - Git/Obsidian backup protects the human-readable side.
  - `cis-log` protects the machine-queryable side.

---

## Discovery Name: Ambiguity-Aware Extraction Becomes Required for Illustrated Sources

- **Architectural Significance**
  - Comic and illustrated source extraction cannot behave like plain document OCR.
  - Ambiguity is not a defect; it must be explicitly represented.
  - Extraction outputs must avoid unsupported identity claims and source-confident hallucinations.

- **Affected Layers**
  - Intelligence Layer
  - Knowledge Layer
  - Governance Layer
  - Review Layer

- **Dependency Impact**
  - Visual extraction standards must include uncertainty, confidence notes, and human review before trust promotion.
  - Review and correction mechanisms become mandatory, not optional.

- **Build Impact**
  - ADR-011 locks ambiguity-aware extraction standards.
  - Corrections are logged to the database.

- **Runtime Impact**
  - Records remain draft until reviewed.
  - `confidence_notes` and correction logging become part of record governance.

---

# 2. TOPOLOGY MUTATIONS

## New Layers

### Phase PD / Pre-Development Harness Layer
- Newly clarified as a real system layer before Phase 0.
- Contains:
  - SQLite memory database
  - Obsidian vault
  - GitHub backup
  - ADRs
  - `cis-log`
  - `cis-start`
  - future skill documents
  - future protocols
- Function: maintain continuity, decisions, and session state before runtime execution begins.

### Platform Infrastructure Track
- Split from CIS application development.
- Contains:
  - Proxmox host
  - Ubuntu creative VM
  - storage mounts
  - model runtimes
  - environment variables
  - cache/model relocation
  - terminal/Obsidian/Git integration

### Execution Layer / Phase 0
- Moves from missing bridge to proven pipeline.
- Concrete commands created:
  - intake
  - classify
  - preprocess
  - extract
  - normalize
- Still missing review completion.

## Split Layers

### Infrastructure vs CIS Build
- Before: roadmap conflated hosting infrastructure and CIS system construction.
- After: two-track architecture:
  - Track 1 — Platform Infrastructure
  - Track 2 — CIS Build

### Runtime vs Application
- Runtime is script/manifest/state/record behavior.
- Application is the future visible control surface.
- Application must expose runtime; it must not invent runtime behavior.

### Human-Readable Memory vs Machine-Queryable Memory
- Obsidian = readable shell.
- SQLite = operational memory.
- GitHub = backup/sync substrate.

## Runtime Bridges

### `cis-start`
- Bridges session context, ADRs, storage map, runtime paths, and current phase.
- Reduces chat-history dependency.

### `cis-log`
- Bridges human decisions and database state.
- Logs decisions, sessions, and corrections.

### Environment Variables
- `HF_HOME` bridges HuggingFace cache/model loading to `/mnt/models/huggingface`.
- `OLLAMA_MODELS` bridges Ollama to `/mnt/models/ollama`.

### Processing Commands
- `cis_intake.py` bridges raw file arrival to manifest object.
- `cis_classify.py` bridges manifest to processing profile.
- `cis_preprocess.py` bridges source file to model-ready input.
- `cis_extract.py` bridges source unit to model-generated raw extraction.
- `cis_normalize.py` bridges raw extraction to canonical `knowledge_record`.

## Orchestration Changes

- Orchestration is not yet a full service.
- Orchestration is currently command-line sequence and operator-guided execution.
- The five command pipeline establishes the minimum orchestration skeleton.
- Future automation must wrap these commands rather than bypassing them.

## Governance Expansion

- ADRs expand from documentation into runtime memory entries.
- Model choice, runtime choice, storage layout, schema status, and execution proof become locked decisions.
- Corrections become first-class memory events.

## Object-Model Mutations

- Source Manifest becomes the control object.
- `knowledge_record` becomes proven as canonical output.
- Session Log becomes a system object.
- ADR becomes both documentation object and database object.
- Correction becomes a traceable object.

## Workflow / Execution Separation

- Workflow remains what should happen.
- Execution becomes what command runs, what file appears, what state changes, and what output is valid.
- Phase 0 proves that execution can exist without a full application UI.

## Project-Container Evolution

- `/mnt/projects/cis` becomes the active system root.
- Existing folders shift from exploratory placeholders into canonical surfaces:
  - `docs/`
  - `ingest/`
  - `knowledge/`
  - `logs/`
  - `projects/`
  - `runtime/`
  - `memory/`

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisites

### Storage Separation Before Model Work
- 32B model work is blocked if model weights remain in `~/.cache` or system disk.
- `/mnt/models` and `/mnt/cache` must exist before reliable extraction.

### Persistent Memory Before Phase 0 Expansion
- Without `cis_memory.db`, ADRs, sessions, and corrections remain trapped in chat.
- Phase PD must precede durable Phase 0 work.

### Runtime Environment Before Extraction Script
- `cis_extract.py` requires:
  - Qwen2.5-VL-32B 4-bit runtime
  - `transformers + bitsandbytes`
  - correct GPU environment
  - `PYTORCH_ALLOC_CONF=expandable_segments:True`

### Manifest Before Any Processing
- Every command after intake depends on manifest existence.
- No file can move directly from raw source to extraction without manifest identity.

### Real Archive Trial Before Schema Confidence
- The system cannot validate schema behavior using abstract examples.
- Real archive material exposes ambiguity, model limitations, naming needs, and record quality issues.

## Sequencing Constraints

1. Stabilize storage and runtime.
2. Create persistent memory.
3. Lock ADRs.
4. Create harness coordinator.
5. Transition to Phase 0.
6. Build intake.
7. Build classification.
8. Build preprocessing.
9. Build extraction.
10. Build normalization.
11. Build review.
12. Only then build retrieval, agents, and application surface.

## Circular Dependencies

### App vs Runtime
- The user wants a workbench because command line is burdensome.
- But the app must expose existing runtime behavior.
- Therefore the minimal runtime must exist before the app, while the app remains necessary to reduce human middleware later.

### Model Quality vs Pipeline Build
- Pipeline is useless if records are low quality.
- But the model cannot be integrated reliably until pipeline paths and storage are stable.
- Resolution: restore/validate model runtime in Phase PD, then build Phase 0 pipeline around it.

### Documentation vs Execution
- Docs define contracts.
- Execution proves or mutates contracts.
- Corrections must feed back to docs through ADRs and session logs.

## Unstable Dependencies

- vLLM was initially treated as runtime, later superseded by transformers + bitsandbytes for 32B inference.
- ADR-002 and ADR-009 conflict unless ADR-009 is treated as superseding ADR-002 for extraction.
- `cis_harness.py` required updating to reflect the runtime change.
- Obsidian Git sync depended on GitHub credential storage.

## Runtime Blockers

- System disk at 86% usage blocked model deployment.
- Qwen2.5-VL-32B full bfloat16 weights exceed RTX 4090 VRAM.
- FP8 on-the-fly quantization failed with OOM.
- Model weights were hidden in HuggingFace cache until relocated.
- `~/.cache` symlink had to be corrected.
- Archive NTFS mount caused temporary terminal/df hang risk.

## Orchestration Bottlenecks

- Human copy/paste remains a major execution bottleneck.
- Commands are manually run in terminal.
- Session close still requires manual logging.
- `cis_review.py` is not yet complete.
- Dashboard/workbench does not yet exist to surface review, correction, or state transitions.

# 4. EXECUTION-LAYER IMPLICATIONS

## Commands Extracted

### Phase PD Commands

- `cis-log`
  - Alias for `python3 /mnt/projects/cis/memory/cis_log.py`
  - Logs decisions, sessions, and corrections.

- `cis-start`
  - Alias for `python3 /mnt/projects/cis/memory/cis_harness.py`
  - Loads session context.

### Phase 0 Commands

- `cis_intake.py`
  - Input: source file path.
  - Action: create source folder, copy source, create manifest, compute hash.
  - Output: `manifest.json` with `status = arrived`.

- `cis_classify.py`
  - Input: source manifest.
  - Action: confirm source type and processing profile.
  - Output: manifest update with classification and processing state.

- `cis_preprocess.py`
  - Input: classified source.
  - Action: prepare source for extraction.
  - Output: preprocessing artifacts and `status = preprocessed`.

- `cis_extract.py`
  - Input: preprocessed source.
  - Action: run Qwen2.5-VL-32B 4-bit extraction.
  - Required runtime:
    - `/home/eric/gpu-test/bin/python3`
    - `PYTORCH_ALLOC_CONF=expandable_segments:True`
  - Output: raw extraction text.

- `cis_normalize.py`
  - Input: raw extraction.
  - Action: parse to canonical `knowledge_record`.
  - Output: JSON record and markdown mirror.

- `cis_review.py`
  - Planned / missing next command.
  - Required to review, correct, approve, reject, or promote records.

## States and Transitions

### Source / Manifest Runtime States

- `arrived`
- `classified`
- `preprocessed`
- `extracted`
- `normalized`
- `draft`
- `reviewed`
- `approved`
- `rejected`

### Proven Transition

`raw file → manifest/status arrived → classified → preprocessed → extracted → normalized → knowledge_record/status draft`

### Missing Transition

`draft → reviewed → approved/locked/deprecated`

## Runtime Contracts

### Intake Contract
- No source can be processed without manifest.
- Manifest must include source identity and hash.
- Source must be copied into processing folder.

### Extraction Contract
- Extraction must use validated 32B model path.
- Extraction must run in the correct Python environment.
- Extraction must account for VRAM constraints.
- Extraction must produce raw output that can be normalized.

### Normalization Contract
- Output must conform to `knowledge_record v1`.
- JSON is canonical.
- Markdown is mirror.
- Status remains draft until review.

### Memory Contract
- Session and ADR changes must be logged through `cis-log`.
- Context is loaded through `cis-start`.

## Orchestration Logic

Current orchestration is sequential and operator-driven:

1. Operator runs command.
2. Command reads current object state.
3. Command writes next artifact.
4. Command updates state.
5. Operator verifies.
6. Operator logs decision/session/correction.

Future orchestration should convert this sequence into queued jobs, dashboard buttons, or workbench actions without changing the underlying state rules.

## Validation Behavior

### Existing Validation
- Manual verification of output files.
- Manual inspection of JSON and markdown record.
- ADR locking after successful proof.
- Corrections logged manually.

### Required Validation
- Required field validation.
- Schema validation.
- Hallucination/unsupported claim checks.
- Confidence/uncertainty validation.
- Source-path validity checks.
- Review-state validation.

## Pass / Fail Structures

### Pass
- Output exists.
- Output matches required structure.
- State advances.
- Session/decision logged.

### Fail
- Missing required fields.
- Runtime OOM.
- Model hallucination.
- Ambiguous visual content presented as certainty.
- Script syntax/paste failure.
- Wrong environment.
- Broken mount, missing path, or wrong model location.

## Retry / Escalation Logic

- Runtime fail → adjust environment / GPU flag / model quantization.
- Output quality fail → correct prompt / apply ambiguity rules / human correction.
- Schema fail → revise normalizer.
- Human uncertainty → keep draft, mark for review.
- Repeated command friction → convert to wrapper script or future UI route.

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

### Human Authority
- Human validates model quality.
- Human decides whether records are useful.
- Human locks ADRs.
- Human controls build direction.
- Human determines whether a model result is acceptable enough to build on.

### System Authority
- SQLite records decisions and sessions.
- Manifest controls source state.
- `knowledge_record` controls canonical knowledge output.
- Harness coordinator controls session-start context.

### Source Authority
- Source files and hashes ground extraction.
- Source path and source identity must not be silently overwritten.

## Review States

- Draft state exists and is proven.
- Review state path remains incomplete.
- `cis_review.py` is required to govern:
  - correction
  - approval
  - rejection
  - promotion
  - deprecation

## Promotion Logic

Current promotion gate is manual and not yet encoded.

Required future path:

`draft → reviewed → approved → locked`

Rejected or uncertain records should remain retained but not trusted for retrieval or agent use.

## Rejection Paths

A record or output must be rejected/returned when:

- model output is hallucinated
- model output is too generic
- source identity is wrong
- required fields are absent
- ambiguity is not expressed
- schema is invalid
- runtime environment is wrong

## Trust Enforcement

Trust is not assigned because a model generated output.
Trust is assigned after review, correction, and approval.

This transcript turns trust from a philosophical rule into a build requirement because corrections are logged and draft records remain unpromoted.

## Hallucination Controls

- Smaller models were rejected because they hallucinated or produced unusable outputs.
- Comic illustration requires ambiguity-aware extraction.
- Extraction should not make unsupported claims about identity, artist, issue metadata, or visual certainty.

## Provenance Enforcement

- Manifest stores source identity and hash.
- Records store source path, source type, source unit, model used, and status.
- ADRs store rationale for architectural decisions.
- Session logs store context for what changed.

## Validation Contracts

- `knowledge_record v1` governs output schema.
- ADRs govern runtime and build decisions.
- Storage map governs path responsibilities.
- Manifest governs intake lifecycle.
- Corrections table governs record improvement history.

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

Knowledge is formed only after raw material passes through:

`source → manifest → preprocessing → extraction → normalization → draft knowledge_record`

Raw archive files are not knowledge.
Model output is not knowledge by itself.
A normalized canonical record is the first knowledge-layer object.

## Retrieval Structure

Retrieval depends on records, not raw files.
The transcript proves a record can be generated and stored in:

`/mnt/projects/cis/knowledge/records/IMAGE__WEIRD_WAR_TALES_COVER__001/`

Records must contain retrieval-ready fields, including summary and retrieval text.

## Indexing Implications

Indexing remains future work but is now unblocked by the existence of canonical records.
Required next structures:

- record registry
- retrieval chunks
- metadata index
- vector index
- approved-only retrieval priority

## Normalization Rules

`cis_normalize.py` is the first normalizer.
It must convert raw extraction into:

- canonical JSON
- markdown mirror
- draft status
- stable record identity

Normalization is where field authority and hallucination controls must be enforced.

## Ontology / Spine Implications

The knowledge spine begins with:

- `knowledge_category`
- `subject`
- `tags`
- `active_stages`
- `source_type`
- `model_used`
- `status`

Future ontology must account for:

- illustrated references
- comics
- visual ambiguity
- tutorial segments
- archive folders
- project-linked knowledge

## Chunking Logic

Chunking is not yet implemented.
Required future chunking logic:

- one record can produce retrieval chunks
- chunks must retain `record_id`
- visual records may need scene/layout/mood chunks
- video records must include timestamps
- only reviewed/approved chunks should influence high-trust retrieval

## Reinforcement Behavior

Corrections are logged to the database.
This turns correction from chat feedback into system memory.
Future extraction should use correction history to improve prompts, normalizer behavior, and review surfaces.

## Project Linkage

Project linkage is structurally present but not yet fully used.
Records should eventually attach to:

- `project_id`
- `project_title`
- active WIAS stages
- project output type
- related references/research/learning

## Stabilization Loops

The transcript demonstrates a stabilization loop:

1. Test model.
2. Reject weak outputs.
3. Select quality model.
4. Fix storage/runtime.
5. Generate record.
6. Log corrections.
7. Lock ADR.
8. Update documentation and harness.

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

The future workbench must expose the runtime pipeline that now exists:

- source intake
- manifest display
- classification state
- preprocessing status
- extraction run
- normalized record preview
- review/correction panel
- promotion controls
- session/ADR status

## Interface Panels

The topology image aligns with required panels:

### Intake / Discovery Panel
- upload/select file
- assign source type
- create manifest
- show source hash and status

### Runtime Status Panel
- show current state
- show command progress
- show model/environment used
- show errors

### Knowledge Record Panel
- show JSON fields in readable form
- show markdown mirror
- show source linkage
- show confidence notes

### Review Panel
- edit fields
- log correction
- approve/reject
- promote record

### Governance Panel
- show ADRs
- show current phase
- show last session
- show unresolved gaps

### Tool / Runtime Panel
- show model path
- show active environment
- show storage health

## Operator Actions

The operator should be able to:

- add source
- run intake
- classify source
- run preprocessing
- run extraction
- normalize output
- review/correct record
- approve/reject record
- log session close
- commit docs

## Runtime Visibility Needs

The transcript reveals a strong need for visibility into:

- storage mount status
- environment variables
- model runtime availability
- extraction model choice
- current phase
- ADR list
- source state
- record state

`cis-start` is a CLI version of the future dashboard status panel.

## Workflow Exposure

The application must not merely show folders.
It must expose workflow state:

- arrived
- classified
- preprocessed
- extracted
- normalized
- draft
- reviewed
- approved

## Project-Centered Interaction

Although the transcript focuses on source/record infrastructure, the application must eventually attach all record behavior to projects.
The project remains the primary interface object, but Phase 0 proves the source-to-record subpipeline first.

## Application / Runtime Bridges

Future app buttons should call existing commands rather than reimplementing logic:

- Intake button → `cis_intake.py`
- Classify button → `cis_classify.py`
- Preprocess button → `cis_preprocess.py`
- Extract button → `cis_extract.py`
- Normalize button → `cis_normalize.py`
- Review button → `cis_review.py`
- Session start → `cis-start`
- Decision/session/correction logging → `cis-log`

# 8. FEEDBACK LOOP DISCOVERIES

## Reinforcement Loop

Model output is evaluated by human judgment.
Corrections are recorded.
Accepted patterns become future system precedent.

Current implementation:

`model output → human correction → cis-log correction → ADR/session memory → future prompt/runtime improvement`

## Correction Loop

Corrections are no longer informal chat comments.
They become rows in the `corrections` table.
Future review UI must make this automatic.

## Governance Loop

Build discoveries become ADRs.
ADRs update harness state.
Harness state guides the next session.

`runtime discovery → ADR → database → cis-start → next build behavior`

## Retrieval-Improvement Loop

Not implemented yet, but structurally implied:

`approved records → retrieval index → agent/teacher output → user feedback → record correction → better retrieval`

## Archive-Learning Loop

Real archive material reveals schema and extraction needs.
This invalidates upfront-only schema design.

`archive source → pipeline failure/success → schema/runtime correction → ADR → improved pipeline`

## Continuity / Memory Loop

`session work → cis-log session → cis-start context → next session starts with continuity`

This loop directly reduces reliance on platform chat memory.

## Project-Output Feedback Loop

Not directly executed in this file, but build-order logic preserves it:

`project output → knowledge record → future retrieval/teacher support → improved project execution`

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridges

- `cis_review.py` not yet completed.
- No wrapper for session-close logging.
- No automated Git/Obsidian/database synchronization between SQLite ADRs and markdown ADRs.
- No queue/worker layer for long-running extraction.
- No dashboard/workbench button layer.

## Undefined or Partially Defined Objects

- Review object / review event.
- Correction object has database form but no UI form.
- Retrieval chunk object.
- Model run object.
- Extraction job object.
- Processing profile object in the local runtime.
- Project object not yet active in this transcript's pipeline.

## Unstable Schemas

- Existing `knowledge_v1.json` predecessor schema is less complete than locked schema.
- ADR markdown and SQLite ADRs can diverge.
- `record_001.json` naming appears in Phase 0 proof while earlier examples use `record.json`; naming needs enforcement.
- `source_name` handling remains a known weak point from earlier record examples.

## Unresolved Orchestration

- Command sequence is manual.
- No command dispatcher exists.
- No dependency checker prevents out-of-order commands.
- No job queue.
- No retry manager.

## Unresolved Routing

- Model routing is hard-coded around Qwen2.5-VL-32B for quality.
- No router decides local vs frontier vs fallback.
- No automatic downgrade/upgrade logic.
- vLLM vs transformers runtime conflict needs formal supersession.

## Missing Governance

- Review/promotion governance not encoded.
- Schema validation not enforced systematically.
- ADR supersession not formalized.
- Session-close automation missing.
- Human middleware remains high.

## Missing Validation Layers

- JSON schema validator.
- Required-field checker.
- Source-path checker.
- Unsupported-claim checker.
- Confidence/uncertainty checker.
- Review-state validator.

## Unresolved Application Surfaces

- No Workbench UI.
- No Review Panel.
- No runtime dashboard.
- No model status indicator.
- No record browser.
- No project linkage UI.

## Unresolved Storage Rules

- Archive drive is NTFS and high-usage; long-term archive ingestion stability remains a risk.
- Model drive has limited headroom after Qwen weights and runtimes.
- Git-backed Obsidian vault and CIS runtime docs need ongoing synchronization discipline.

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

Completed or proven in this file:

- Drive-purposed storage architecture.
- `/mnt/projects/cis` active root.
- `/mnt/models` for model weights and runtime.
- `/mnt/cache` for cache.
- `/mnt/archive` for source material.
- `HF_HOME` and `OLLAMA_MODELS` set.
- SQLite memory database.
- `cis-log`.
- `cis-start`.
- ADRs 001–012.
- Phase 0 command pipeline.
- First knowledge record generated from real archive material.

## Blocked Layers

### Phase 1 / Intelligence Extraction Refinement
Blocked by:
- missing review command
- missing validation automation
- unstable runtime routing
- need for repeatable extraction standards

### Knowledge Retrieval
Blocked by:
- lack of reviewed/approved records
- missing chunking/indexing
- missing retrieval database/vector store

### Agents
Blocked by:
- insufficient approved knowledge
- no retrieval layer
- no project context layer
- no agent skill documents completed

### Application
Blocked by:
- missing review system
- missing runtime state API
- no queue/worker layer
- no stable database mirror of records beyond file/SQLite memory

## Sequencing Implications

Immediate next build order:

1. Complete `cis_review.py`.
2. Create schema validation for `knowledge_record`.
3. Add command aliases or wrapper.
4. Automate session-close logging.
5. Resolve ADR-002 vs ADR-009 runtime supersession.
6. Build retrieval-ready index from approved/draft records.
7. Add minimal review/workbench surface.
8. Only then begin agent roles.

## Runtime-First Requirements

- Runtime commands must remain source of truth.
- Future UI calls runtime commands.
- Long-running model calls need queue/status behavior.

## Governance-First Requirements

- ADRs must be locked for every system-changing discovery.
- Corrections must be logged at review time.
- Human approval remains required for promotion.

## Execution-First Requirements

- Each command must define:
  - input
  - output
  - required prior state
  - next state
  - failure behavior

## Application Dependencies

The application can begin only after:

- review path exists
- state transitions are reliable
- records can be listed and opened
- corrections can be applied
- runtime status can be surfaced

# 11. EXTRACTED CANONICAL OBJECTS

## Object: Source

- **Purpose**
  - Raw material entering the system.
- **Lifecycle**
  - selected → ingested → copied to processing folder → manifest created.
- **Authority Source**
  - original file and hash.
- **Related Objects**
  - Source Manifest, Processing Folder, Knowledge Record, Project.
- **States**
  - raw / arrived.
- **Storage Implications**
  - stored in source/processing folder under `/mnt/projects/cis/ingest` or related record structure.

---

## Object: Source Manifest

- **Purpose**
  - Control object for all source intake and processing.
- **Lifecycle**
  - created by `cis_intake.py`; updated by classify/preprocess/extract/normalize/review.
- **Authority Source**
  - system-generated, grounded in source file hash.
- **Related Objects**
  - Source, Processing Profile, Extraction Output, Knowledge Record.
- **States**
  - arrived, classified, preprocessed, extracted, normalized, draft/review path.
- **Storage Implications**
  - `manifest.json` in processing/source folder.

---

## Object: Processing Profile

- **Purpose**
  - Determines path: text, vision, or hybrid.
- **Lifecycle**
  - assigned/confirmed during classification.
- **Authority Source**
  - system classification plus human override.
- **Related Objects**
  - Source Manifest, Extraction Command, Processing Plan.
- **States**
  - proposed, confirmed, overridden.
- **Storage Implications**
  - stored in manifest and future runtime schema.

---

## Object: Extraction Runtime

- **Purpose**
  - Executes model inference for record generation.
- **Lifecycle**
  - configured in Phase PD; invoked by `cis_extract.py`.
- **Authority Source**
  - ADRs and runtime tests.
- **Related Objects**
  - Model, Environment, Extraction Output, ADR.
- **States**
  - available, failed, superseded, active.
- **Storage Implications**
  - `/home/eric/gpu-test` for successful transformers/bitsandbytes runtime; `/mnt/models` for model weights.

---

## Object: Model

- **Purpose**
  - Provides visual/multimodal interpretation.
- **Lifecycle**
  - tested → accepted/rejected → assigned to extraction role.
- **Authority Source**
  - model benchmark results and ADRs.
- **Related Objects**
  - Runtime, Extraction Output, Knowledge Record, ADR.
- **States**
  - rejected, fallback, primary, superseded.
- **Storage Implications**
  - weights stored under `/mnt/models/huggingface`.

---

## Object: Knowledge Record

- **Purpose**
  - Canonical CIS knowledge output.
- **Lifecycle**
  - generated by normalization → draft → reviewed → approved/locked/deprecated.
- **Authority Source**
  - source file + model extraction + human correction.
- **Related Objects**
  - Source, Manifest, Project, Correction, Retrieval Chunk.
- **States**
  - draft, reviewed, approved, locked, rejected/deprecated.
- **Storage Implications**
  - JSON canonical and markdown mirror under `/mnt/projects/cis/knowledge/records/...`.

---

## Object: ADR

- **Purpose**
  - Locks architectural decisions.
- **Lifecycle**
  - discovered → logged → locked → displayed in harness → mirrored to docs.
- **Authority Source**
  - human/system decision based on runtime evidence.
- **Related Objects**
  - Session Log, Harness, Obsidian Docs, Governance Layer.
- **States**
  - proposed, locked, superseded.
- **Storage Implications**
  - SQLite `decisions` table and markdown ADR document.

---

## Object: Session Log

- **Purpose**
  - Preserves session continuity and next steps.
- **Lifecycle**
  - logged at session close or milestone.
- **Authority Source**
  - operator-guided session summary.
- **Related Objects**
  - Harness, ADR, Build Phase.
- **States**
  - recorded.
- **Storage Implications**
  - SQLite `session_log` table.

---

## Object: Correction

- **Purpose**
  - Records human/system correction of generated record fields.
- **Lifecycle**
  - identified during review → logged → influences future standards.
- **Authority Source**
  - human correction.
- **Related Objects**
  - Knowledge Record, Review State, Reinforcement Loop.
- **States**
  - logged; future applied pattern.
- **Storage Implications**
  - SQLite `corrections` table.

---

## Object: Harness Coordinator

- **Purpose**
  - Loads operational context at session start.
- **Lifecycle**
  - executed through `cis-start`.
- **Authority Source**
  - SQLite memory and fixed runtime map.
- **Related Objects**
  - ADRs, Session Logs, Storage Map, Runtime Config.
- **States**
  - active, outdated, updated.
- **Storage Implications**
  - `/mnt/projects/cis/memory/cis_harness.py`.

---

## Object: Obsidian Vault

- **Purpose**
  - Human-readable continuity and documentation shell.
- **Lifecycle**
  - edited → committed → pushed to GitHub.
- **Authority Source**
  - human-readable canonical docs.
- **Related Objects**
  - ADRs, Build Sequence, GitHub Remote, SQLite Memory.
- **States**
  - local, committed, pushed, out-of-sync.
- **Storage Implications**
  - `/mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1`.

---

## Object: Project

- **Purpose**
  - Primary future container for workflow, knowledge, outputs, and execution context.
- **Lifecycle**
  - initiated → active → production → output → archived.
- **Authority Source**
  - user creative intent.
- **Related Objects**
  - Source, Knowledge Records, References, Research, Outputs.
- **States**
  - not fully activated in this transcript.
- **Storage Implications**
  - `/mnt/projects/cis/projects`; future workbench primary object.

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did not exist before?

After this file, CIS is no longer only a documented architecture or conceptual studio operating system. It has crossed into a partially executable local infrastructure with a proven Phase 0 source-to-record pipeline.

The major architectural delta is that the build sequence becomes grounded in real machine constraints, real storage layout, real model performance, and real command behavior. The system is no longer merely defined by layers; it is defined by executable contracts.

The new understanding is:

1. **Phase PD is not optional planning.**  
   It is the continuity infrastructure that prevents CIS from depending on chat memory. SQLite, Obsidian, GitHub, ADRs, and the harness coordinator are required before reliable CIS development.

2. **Infrastructure and CIS are separate missions.**  
   Storage, model runtime, VM setup, and environment variables are platform infrastructure. Intake, extraction, normalization, review, records, retrieval, agents, and workbench are CIS.

3. **Model quality is a system viability gate.**  
   The system cannot be built around weak visual extraction. Qwen2.5-VL-32B becomes foundational because usable knowledge records are the basis of everything downstream.

4. **Hardware constraints mutate the intelligence layer.**  
   The RTX 4090 cannot load full 32B bfloat16 weights. The architecture must use 4-bit quantization through transformers + bitsandbytes, with runtime flags to prevent VRAM fragmentation.

5. **The source manifest becomes the first operational control object.**  
   Intake is not file copying. Intake is manifest creation, identity assignment, hash recording, and state initiation.

6. **The execution layer is proven through commands.**  
   Five scripts move a real file from raw source to canonical knowledge record: intake, classify, preprocess, extract, normalize.

7. **The knowledge layer now has a real atom.**  
   The canonical `knowledge_record` is no longer theoretical. A real record was produced and stored as JSON and markdown mirror.

8. **Governance becomes runtime memory.**  
   ADRs, session logs, corrections, schemas, and current phase are now stored in SQLite and exposed by `cis-start`.

9. **The review layer is the next bottleneck.**  
   Phase 0 is proven up to draft record creation. Trust promotion still requires `cis_review.py`, validation rules, and review UI/workbench exposure.

10. **Application development is closer but still gated.**  
   The future application can now be designed as a surface over actual runtime commands, not abstract desired behavior. But it must wait until review, validation, and state exposure are stable.

## Net Delta

Before this file:

- CIS had architecture, build-order logic, and prototype records.
- Execution was still mostly conceptual or exploratory.
- Persistent memory was desired but not built.
- Infrastructure and CIS build phases were conflated.

After this file:

- Platform storage is purpose-assigned and stable.
- Model runtime constraints are known and governed.
- SQLite memory exists.
- `cis-log` and `cis-start` exist.
- ADRs are locked in machine memory.
- Phase 0 command pipeline exists.
- A real archive item can produce a draft canonical record.
- The next architectural bottleneck is explicit: review, validation, correction, and promotion.

## Topology-Map Translation

For topology diagramming, this file adds or confirms these nodes:

- Phase PD Harness
- SQLite Memory DB
- Obsidian Vault
- GitHub Sync
- ADR Store
- Session Log
- Corrections Store
- Harness Coordinator / `cis-start`
- Logging Interface / `cis-log`
- Storage Map
- Model Store
- Cache Store
- Archive Store
- Qwen2.5-VL-32B Runtime
- Transformers + BitsAndBytes Runtime
- Source Manifest
- Intake Command
- Classify Command
- Preprocess Command
- Extract Command
- Normalize Command
- Draft Knowledge Record
- Missing Review Command
- Future Workbench Review Surface

For dependency diagramming, this file establishes this critical chain:

`storage architecture → model runtime viability → persistent memory → ADR governance → harness coordinator → source manifest → phase 0 commands → draft knowledge_record → review/promotion gap → retrieval/agents/application`

