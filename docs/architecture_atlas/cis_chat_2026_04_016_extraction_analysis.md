# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name
Contract Artifacts Are Distinct From ADRs, Schemas, and Runtime Implementations

### Architectural Significance
The transcript exposes a major governance correction: CIS had been treating several artifact types as interchangeable even though they serve different roles. ADRs record decisions. JSON schemas define structure. Runtime code proves behavior. Contract documents define field authority, mutability, state transition rules, validation rules, and implementation constraints. The session establishes that none of these artifacts can substitute for the others.

The previous assumption was that schemas in `/mnt/projects/cis/runtime/schemas/` and locked ADRs could function as contracts. That assumption was invalidated. A schema can say which fields exist, but it cannot define the authority model, transition law, rejection behavior, lifecycle requirements, or implementation responsibility.

### Affected Layers
- Governance Layer
- Execution Layer
- Knowledge Layer
- Intake / Discovery Layer
- Application Layer
- Documentation / Memory Layer

### Dependency Impact
This introduces a new dependency: implementation must be checked against the contract register before new build work proceeds. Future pipeline code must depend on formally governed contracts, not inferred runtime behavior.

The dependency chain becomes:

`ADR decision → contract specification → schema/runtime implementation → verification → build continuation`

### Build Impact
The build sequence changes. The session rejects proceeding directly to `cis_spine_intake.py` until contract existence and contract status are audited. It creates the need for a `CIS_CONTRACT_REGISTER.md` or equivalent governing registry.

### Runtime Impact
Runtime behavior can no longer be accepted merely because code produces outputs. Runtime behavior must be traceable to an explicit contract. Existing runtime objects may require verification against their governing contract after the fact.

---

## Discovery Name
Session Memory Failure Is a Build-Blocking Architectural Problem

### Architectural Significance
The session identifies that CIS has a meta-level memory problem: the build process itself is losing architectural reasoning between sessions. Handoffs and ADRs capture outcomes but not the reasoning, failures, incorrect assumptions, scope pivots, and emotional/operational friction that shaped those outcomes.

This reframes transcript processing from an optional archival task into a prerequisite for reliable continued development.

### Affected Layers
- Governance Layer
- Knowledge Layer
- Intelligence Layer
- Application Layer
- Feedback / Evolution Loop
- Session Close / Handoff System

### Dependency Impact
The build now depends on a persistent institutional memory layer that can ingest and extract insight from chat transcripts. Before this session, transcript processing was considered possibly unnecessary because ADRs and handoffs were believed to capture enough signal. This assumption was explicitly invalidated.

### Build Impact
The build priority changes from `cis_spine_intake.py` and contract writing to session logging capability. The user explicitly prioritizes the session logging capability because the same context-loss problem keeps forcing hours of architectural archaeology.

### Runtime Impact
CIS needs a runtime or semi-runtime path for transcript-derived insight records. The immediate version is manual: export transcripts, run model-based extraction, write `SESSION_INSIGHT_RECORD_*` files. Future versions require automated or staged intake so that session reasoning becomes durable system knowledge.

---

## Discovery Name
`knowledge_v1.json` Was a Pre-Scope-Expansion Artifact and Had to Be Replaced

### Architectural Significance
The transcript identifies `knowledge_v1.json` as out of sync with the actual pipeline output, the expanded architecture, and the real record structure. The existing schema used older fields such as `knowledge_type`, `text_extract`, `visual_summary`, `mood_style_tags`, `structural_notes`, `example_uses`, `ingestion_method`, and `confidence_notes`. The actual pipeline output used `knowledge_category`, `summary`, `visible_text`, `scene_description`, `layout_description`, `mood_style`, `uncertainty`, `retrieval_text`, `source_origin`, `model_used`, `version`, and `is_current`.

### Affected Layers
- Knowledge Layer
- Intelligence Layer
- Schema Governance
- Runtime Extraction Pipeline
- Review / Promotion Layer

### Dependency Impact
Any process producing or consuming knowledge records is blocked by schema drift until the canonical schema is corrected. `cis_spine_intake.py` and any future spine anchoring workflow depend on current `knowledge_v1.json` because `anchor_node_id` must exist on future knowledge records.

### Build Impact
The session replaced the old schema with a corrected structure derived from actual current pipeline output and ADR-032 requirements. Test records were cleared because they were Phase 0 exit proofs rather than production data.

### Runtime Impact
The corrected `knowledge_v1.json` becomes the new runtime contract target for future extraction records. Existing records from proof runs were removed to avoid polluting production tests.

---

## Discovery Name
The Build Plan Is Non-Linear Because System Understanding Emerges Through Use

### Architectural Significance
The transcript validates that the original linear build plan could not accurately predict implementation order because major system realizations emerged only through interaction with real files, runtime failures, project memory gaps, and operator friction. This is not treated as failure of discipline but as a property of the system: CIS is discovered through use.

### Affected Layers
- Workflow Layer
- Governance Layer
- Application Layer
- Knowledge Formation Layer
- Feedback Loop

### Dependency Impact
Build sequencing becomes conditional rather than strictly linear. Contracts may not exist before implementation in cases where the feature was not yet conceptually stable. However, once the need for a contract becomes visible, work must stop and formalize it before further dependent development.

### Build Impact
The session introduces a governance principle: the user chooses when the build plan is deviated from. AI assistance must not silently reclassify missing artifacts as “bureaucratic detours.”

### Runtime Impact
Runtime state must preserve not only current phase but also why build order changed. Otherwise future sessions repeat the same disagreements about whether a deviation was intentional, accidental, or overdue.

---

## Discovery Name
Resolved CIS Live Sessions Are Not Exportable Institutional Artifacts

### Architectural Significance
The transcript exposes a gap in CIS Live: resolved sessions live in SQLite and the dashboard, but they do not automatically produce a portable markdown artifact. The user had to paste resolved session content manually to recover the reasoning behind ADR-031 and ADR-032.

### Affected Layers
- CIS Live
- Session Memory
- Governance Layer
- Application Layer
- Knowledge Layer

### Dependency Impact
Future handoffs and architectural extractions depend on resolved sessions being exportable. Without export, resolved CIS Live sessions cannot be dragged into future model sessions and cannot be processed through the same transcript insight pipeline.

### Build Impact
This introduces a future feature requirement: “export resolved session as markdown.” It also strengthens the need for session insight records and daily flush logic.

### Runtime Impact
Resolved sessions need a lifecycle path:

`live session → resolved session → exported markdown → insight extraction → knowledge / governance record`

---

## Discovery Name
Transcript Extraction Requires Its Own Deterministic Contract

### Architectural Significance
The user rejected vague or handoff-like transcript summaries and required a deterministic extraction contract before processing the session archive. This produced `CIS Session Transcript Extraction Contract v1`, defining a fixed seven-section output structure for every transcript.

### Affected Layers
- Knowledge Layer
- Intelligence Layer
- Governance Layer
- Feedback Loop
- Session Logging System

### Dependency Impact
Transcript processing now depends on a contract. The extraction process cannot vary by model mood or chat context. Every transcript must be evaluated against the same institutional memory criteria.

### Build Impact
The contract itself becomes a reusable processing profile for chat transcript ingestion. It also demonstrates the broader rule: model outputs intended for CIS must be contract-bound.

### Runtime Impact
Future transcript extraction can be made into a formal pipeline:

`raw transcript → transcript extraction contract → SESSION_INSIGHT_RECORD → review → retained institutional memory`

---

# 2. TOPOLOGY MUTATIONS

## Mutation: Governance Layer Expands From ADR Storage to Contract Governance

The Governance Layer mutates from a decision log into a multi-artifact authority system. The session identifies at least four governance artifact classes:

- ADRs: decision authority
- Contract specs: implementation law
- JSON schemas: structural templates
- Runtime code / DB state: operational implementation

The transcript clarifies that ADRs are binding but incomplete. Contracts must be derived from ADRs and must state the rules that code is allowed to enforce.

## Mutation: Documentation Layer Becomes an Active Memory Layer

Documentation is no longer passive recordkeeping. It becomes part of system runtime continuity. Session transcripts, insight records, handoffs, ADRs, and reorientation documents form a memory topology that must be kept synchronized.

New memory chain:

`chat transcript → insight record → reorientation update → contract/register update → future build context`

## Mutation: Knowledge Layer Gains Institutional Memory Objects

The Knowledge Layer is no longer only about external creative/source material. It must also retain CIS’s own build reasoning as institutional memory.

New knowledge object class implied:

`session_insight_record`

This object is distinct from ADRs and handoffs. It stores why understanding changed, what failed, what was assumed, and what remains unresolved.

## Mutation: Build Pipeline Gains Meta-Extraction Loop

The system gains a second extraction pipeline operating on its own development transcripts.

Original knowledge pipeline:

`source material → intake → extraction → knowledge_record`

New meta-pipeline:

`build transcript → institutional extraction → session_insight_record → governance / reorientation / knowledge update`

## Mutation: Workflow/Execution Separation Becomes Stronger

The session reinforces that workflow descriptions are insufficient unless they become execution contracts. The Workflow Stream says what should happen. The Execution Layer says what exact artifact appears, which command runs, what state changes, and what counts as valid output.

## Mutation: Application Layer Debt Becomes Governance-Relevant

The frontend monolith, previously treated as deferred technical debt, becomes part of the topology risk map because a single syntax error can break the entire dashboard. The dashboard is a critical governance surface for decisions, Live sessions, review, and future transcript workflows.

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisite: Contract Register Before Further Contract Writing

The user identifies that writing individual missing contracts without a complete register risks producing contracts that do not match ADRs, schemas, or database reality. A contract register must come before additional contract drafting.

Dependency chain:

`ADR database audit → schema audit → runtime artifact audit → contract register → missing contracts → implementation verification`

## Hidden Prerequisite: Transcript Archive Before Reliable Reorientation

The session reveals that the reorientation document is stale because prior session reasoning was never systematically extracted. Updating reorientation directly without processing transcripts would only preserve a partial understanding.

Dependency chain:

`transcripts → insight extraction → institutional memory → reorientation update`

## Hidden Prerequisite: Schema Verification Before Pipeline Expansion

`knowledge_v1.json` drifted from actual records. The transcript shows that schema files must be compared against real outputs before dependent scripts are built.

Dependency chain:

`actual record output → schema correction → downstream script design`

## Sequencing Constraint: `cis_spine_intake.py` Depends on Spine Contracts and Correct Knowledge Schema

The original next step was to build `cis_spine_intake.py`. The session establishes that this work depends on:

- source manifest rules
- processing profile rules
- review state rules
- knowledge_spine contract
- spine_node contract
- corrected knowledge_v1 schema with `anchor_node_id`

## Sequencing Constraint: PySceneDetect Depends on Spine Anchoring

PySceneDetect was deprioritized because scene detection cannot usefully produce segment records until spines exist to anchor segments. Scene detection becomes downstream of knowledge_spine ingestion, not a standalone Phase 1 opener.

## Runtime Blocker: `runtime/manifests/` Exists but Has No Defined Role

The empty `runtime/manifests/` folder is identified as a structural ambiguity. It should not silently remain as an implied runtime destination. It requires classification as canonical, deprecated, or reserved.

## Runtime Blocker: DB May Reference Deleted Test Records

The session clears all test records and ingest content. This is acceptable because they were proof outputs, but the transcript notes that DB references to deleted paths may now be broken and should be checked before further ingestion.

## Orchestration Bottleneck: Human Is Still Performing Transcript Transport

The process requires the user to export chats, drag files, ask for extraction, and later save the outputs. This creates the same operator-as-API pattern that CIS is meant to eliminate.

# 4. EXECUTION-LAYER IMPLICATIONS

## Command / Process Implications

The transcript contains or implies the following execution commands and checks:

- `find /mnt/projects/cis -name "*contract*" -o -name "*manifest*" -o -name "*profile*" | grep -v __pycache__`
- `sqlite3 /mnt/projects/cis/memory/cis_memory.db "SELECT id, title, status FROM decisions ORDER BY id;"`
- `cat /mnt/projects/cis/runtime/schemas/knowledge_v1.json`
- `cat /mnt/projects/cis/runtime/schemas/knowledge_spine_v1.json`
- `cat /mnt/projects/cis/runtime/schemas/spine_node_v1.json`
- `sqlite3 /mnt/projects/cis/memory/cis_memory.db ".schema"`
- `rm -rf /mnt/projects/cis/knowledge/records/*/`
- `rm -rf /mnt/projects/cis/ingest/processing/*/`
- `rm -rf /mnt/projects/cis/ingest/completed/*/`
- `rm -rf /mnt/projects/cis/ingest/incoming/*`
- `rm -rf /mnt/projects/cis/ingest/legacy/*/`
- `mkdir -p /mnt/projects/cis/docs/claude_chat_transcripts`
- `mkdir -p /mnt/projects/cis/docs/claude_chat_transcripts/insights`

These commands show that the session was not conceptual only. It actively audited filesystem state, database state, schema state, and cleared runtime proof data.

## State Implications

New or clarified states:

### Source / Intake States
- arrived
- classified
- preprocessed
- extracted
- normalized
- draft
- reviewed
- approved
- rejected

### Knowledge Record Review States
- draft
- checked
- approved
- locked
- deprecated

### knowledge_spine States
- ingested
- parsed
- reviewed
- approved
- rejected

### spine_node States
- generated
- reviewed
- approved
- merged
- deprecated

### Transcript Processing States Implied
- exported
- ingested
- extracted
- reviewed
- saved as insight record
- integrated into reorientation/governance

## Transition Implications

### Contract Transition
`decision exists in ADR → contract spec written → schema verified → implementation verified`

### Knowledge Record Transition
`pipeline output → draft → human review → checked/approved/locked or deprecated`

### Transcript Insight Transition
`raw transcript → model extraction → SESSION_INSIGHT_RECORD → saved to insights folder → used to update persistent system memory`

## Runtime Contracts

The transcript implies the following runtime contracts:

1. No build proceeds from stale reorientation without audit.
2. No dependent script is built from code-inferred behavior when a contract is missing.
3. No schema is accepted if it does not match actual record output and current architecture.
4. No transcript insight extraction is accepted if it only duplicates a handoff summary.
5. No partial reading of long transcripts is acceptable when the task is institutional memory recovery.

## Validation Behavior

The session introduces validation requirements for transcript processing:

- Full file must be read, not sampled.
- Duplicates must be identified and skipped.
- Partial reads must be disclosed.
- Extracted insight must include failures, assumptions, direction changes, and unresolved tensions.
- Handoff-like summaries are insufficient.

## Retry / Escalation Logic

When transcript extraction failed to capture nuance, the user rejected it and required a contract. When a transcript was partially read, the extraction had to be redone. This creates a feedback pattern:

`weak extraction → user rejection → contract refinement → redo extraction → supplemental extraction when missed lines discovered`

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

The session establishes a hierarchy of authority:

1. User authority controls deviation from build plan.
2. Contract-first rule governs implementation discipline.
3. ADR database records locked decisions.
4. Contract specs translate ADRs into implementation law.
5. Schemas are structural templates, not full governance.
6. Runtime code must be verified against contracts.
7. Handoff artifacts are lower-authority continuity aids.

## Review States

The session reinforces that review states are not optional UI labels. They control trust, retrieval priority, and whether an object can be used as knowledge.

## Promotion Logic

For knowledge records, promotion is human-governed. For transcript insight records, an equivalent review path is implied but not yet formalized. The system must eventually decide whether session insight records enter knowledge automatically or require approval.

## Rejection Paths

Rejected or weak outputs include:

- Handoff-like transcript summaries
- Incomplete extraction of long transcript files
- Contract claims unsupported by filesystem/DB evidence
- Schema files inconsistent with actual output records
- AI claims that memory is “saved” without deterministic persistence

## Trust Enforcement

Trust cannot depend on AI reassurance. The session repeatedly demands evidence: filesystem listing, DB queries, schema reads, line counts, and full transcript review. This strengthens empirical verification as a governance norm.

## Hallucination Controls

The transcript establishes that claims about existing files, contracts, or memory state must be verified against disk and DB. The AI must not infer that artifacts exist because they were discussed.

## Provenance Enforcement

Session insight records require source filename, approximate date, sequence position, and output location. This provenance structure is essential for later ingestion into knowledge.

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

The Knowledge Layer must now process two categories of material:

1. External source material: tutorials, images, PDFs, documents, videos, archive sources.
2. Internal development material: chat transcripts, Live sessions, ADR reasoning, build failures, contract decisions.

This creates a reflexive knowledge system: CIS must preserve the knowledge generated while building CIS.

## Retrieval Structure

Session insight records should become retrievable by:

- session date
- transcript file
- ADR references
- architectural theme
- unresolved gap
- object affected
- phase affected
- scope mutation

## Indexing Implications

A future index should include:

- `SESSION_INSIGHT_RECORD_*` files
- ADRs referenced
- contracts affected
- schemas affected
- runtime files affected
- unresolved tasks
- assumptions requiring future verification

## Normalization Rules

Session insight records need a normalized schema separate from `knowledge_record`. The current contract defines seven prose sections, but application use will require metadata fields such as:

- source_file
- date
- session_sequence
- related_adrs
- affected_layers
- affected_objects
- unresolved_items
- scope_changes
- assumptions
- output_path

## Ontology / Spine Implications

The transcript reinforces `knowledge_spine` as a hierarchy for domain knowledge, but the session insight archive may need its own spine:

`CIS Build Memory → Contracts → Schemas → Runtime → Application → Governance → Infrastructure → Transcripts`

## Chunking Logic

Transcript extraction cannot rely on arbitrary chunk sampling. For long transcripts, the pipeline must track line ranges and identify unread portions. Supplemental extraction must be merged into the original insight record.

## Reinforcement Behavior

The user’s corrections to extraction quality function as reinforcement signals:

- “This is no better than a handoff” → extraction quality failure.
- “Write a contract first” → deterministic process requirement.
- “You read only 600 of 5532 lines” → completeness failure.
- “Which other files were only partially looked through?” → audit requirement.

These corrections should be retained as model/process improvement data.

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

The transcript implies several application surfaces:

### Contract Register Surface
- View all expected contracts
- Show governing ADR
- Show schema status
- Show spec doc status
- Show implementation verification status
- Show blockers before build continuation

### Transcript Intake Surface
- Upload or point to transcript files
- Detect duplicates
- Track line counts / completeness
- Apply transcript extraction contract
- Produce insight records
- Mark extraction status

### Session Insight Browser
- Browse `SESSION_INSIGHT_RECORD_*` files
- Search by unresolved issue, ADR, object, layer, or phase
- Promote insight into reorientation, ADR, contract, or task

### Resolved CIS Live Export Surface
- Export resolved Live sessions as markdown
- Attach session metadata
- Send to transcript extraction path

### Schema / Runtime Audit Surface
- Compare schema files to real output records
- Flag drift
- Link drift to required contract updates

## Interface Panels

The application now needs or implies:

- Governance panel
- Contract register panel
- Transcript insight panel
- Runtime audit panel
- Memory integration panel
- Reorientation update panel

## Operator Actions

The operator currently must:

- Export transcripts manually
- Upload/drag transcripts into model chats
- Ask for extraction
- Check whether extraction was complete
- Save generated records
- Manually update memory/reorientation

These actions are targets for automation reduction.

## Runtime Visibility Needs

The application must expose:

- Which session transcript files have been processed
- Which were duplicates
- Which were partially read
- Which insight records exist
- Which insight records have been integrated into system memory
- Which contracts are missing or unverified
- Which schemas are stale

## Application / Runtime Bridge

The application should not just display transcript insights. It should write them into the persistent knowledge/governance system using a governed intake path.

# 8. FEEDBACK LOOP DISCOVERIES

## Loop: Contract Failure → User Challenge → Governance Correction

The user challenges the claim that contracts are a bureaucratic detour. That challenge corrects the governance model and reasserts contract-first discipline.

## Loop: Runtime Evidence → Schema Correction

The actual `IMAGE__XMEN_001__001/record_001.json` output reveals schema drift. Runtime output becomes evidence for schema correction.

## Loop: Session Archaeology → Memory System Priority

The session spends so much time reconstructing prior decisions that the activity itself proves the need for transcript-derived institutional memory.

## Loop: Weak Transcript Summary → Extraction Contract

A weak summary triggers the creation of the deterministic transcript extraction contract.

## Loop: Partial Transcript Review → Completeness Audit

The user identifies that only 600 of 5532 lines were read. This forces a full re-read and establishes a completeness audit requirement.

## Loop: Transcript Insights → Future Reorientation

The extracted insight records are intended to update reorientation and reduce future archaeology.

## Loop: AI Overclaiming → Evidence-Based Guardrail

Repeated AI uncertainty or overclaiming creates a stronger rule: verify against disk, DB, schema, and transcript content before asserting state.

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridge

No automated bridge exists from exported transcript to saved `SESSION_INSIGHT_RECORD`. The user remains the manual transport layer.

## Undefined Objects

### `session_insight_record`
The transcript produces these as files, but no canonical schema or lifecycle is defined.

### `contract_register`
The need is identified, but the artifact is not finalized in this transcript.

### `resolved_live_session_export`
The need is identified, but no object or export format is defined.

## Unstable Schemas

### `knowledge_v1.json`
Corrected during the session, but further verification is needed against expanded LIFE/CREATION scope and future spine anchoring.

### `source_manifest`
Operational but lacking formal schema/spec at this point in the transcript.

### `segment`
DB table exists but schema/spec status is incomplete at this point in the transcript.

## Unresolved Orchestration

No pipeline exists for:

`transcript folder → detect unprocessed transcripts → extract insight → save insight → update memory/reorientation`

## Unresolved Routing

The session discusses whether local models, frontier models, or chat interfaces should process transcripts. The immediate approach uses frontier chat manually, but no durable routing decision is fully implemented.

## Missing Governance

The transcript extraction contract exists, but it needs:

- verification status
- storage location
- authority level
- relationship to ADRs/contracts
- update rules

## Missing Validation Layers

Needed validators:

- transcript completeness validator
- duplicate transcript detector
- insight record schema validator
- citation/provenance validator
- integration status validator

## Unresolved Application Surfaces

No dashboard surface exists for:

- contract register
- transcript intake
- insight record review
- resolved session export
- reorientation update workflow

## Unresolved Storage Rules

The insight folder path is identified as:

`/mnt/projects/cis/docs/claude_chat_transcripts/insights`

But the canonical relationship between this folder, Obsidian vault, knowledge records, and ADR/reorientation updates remains unresolved.

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

Before further Phase 1 build work, the following must be stabilized:

1. Contract register
2. Missing contract specs or explicit deferral reasons
3. Corrected `knowledge_v1.json`
4. Transcript insight extraction process
5. Reorientation update based on extracted insights
6. Check for DB references to deleted test records
7. Clarify `runtime/manifests/` role

## Blocked Layers

### Spine Ingestion
Blocked by contract clarity and corrected schema state.

### Segmentation / PySceneDetect
Blocked by knowledge_spine availability and segmentation policy.

### Knowledge Retrieval
Blocked by stable knowledge records and spine anchoring.

### Application Growth
Blocked by frontend monolith risk and lack of transcript/governance surfaces.

## Sequencing Implications

Updated sequence implied by this file:

1. Correct stale schema(s).
2. Clear proof/test data.
3. Build or formalize contract register.
4. Process available transcripts into session insight records.
5. Update reorientation / institutional memory.
6. Verify contract gaps against ADRs and runtime state.
7. Resume Phase 1 build (`cis_spine_intake.py`).
8. Ingest first spine.
9. Then install/test PySceneDetect and write segmentation policy.

## Runtime-First Requirements

All future build steps require evidence from actual runtime state. Assumptions about file existence or contract status are not acceptable.

## Governance-First Requirements

The user must be able to see and approve deviations from the build plan. Silent reprioritization by the AI is not acceptable.

## Execution-First Requirements

Transcript extraction must become executable, repeatable, and auditable. It cannot remain a one-off chat activity.

## Application Dependencies

A future application surface must reduce the operator burden created by transcript exporting, contract auditing, and artifact saving.

# 11. EXTRACTED CANONICAL OBJECTS

## Object: Source Manifest

### Purpose
Control object for every intake source. Records source identity, file path, hash, project link, status, processing profile, timestamps, and state history.

### Lifecycle
`created before processing → updated through intake states → governs downstream processing`

### Authority Source
ADR-007; operational `manifest.json` files; future contract spec required.

### Related Objects
- Source
- Processing Profile
- Processing Plan
- Knowledge Record
- Project

### States
- arrived
- classified
- preprocessed
- extracted
- normalized
- draft
- reviewed
- approved
- rejected

### Storage Implications
Stored in each source container. At this point in the transcript, source manifest is operational but lacks a formal standalone spec/schema file.

---

## Object: Processing Profile

### Purpose
Determines how a source is processed.

### Lifecycle
`assigned during classification → read during preprocessing/extraction → governs extraction route`

### Authority Source
Architecture specs and ADR-derived rules; standalone contract missing at this point.

### Related Objects
- Source Manifest
- Processing Plan
- Extraction Path
- Model Router

### States
Not itself stateful, but governs state transitions in source processing.

### Storage Implications
Needs formal profile definitions for image, document, multimodal, tutorial video, audio lesson, idea note, and spine source profiles.

---

## Object: Review State

### Purpose
Controls trust and promotion of knowledge records.

### Lifecycle
`draft → checked → approved → locked`, with `deprecated` as retained but non-preferred.

### Authority Source
ADR-005, ADR-021, architecture map; standalone contract missing at this point.

### Related Objects
- Knowledge Record
- Review UI
- cis_review.py
- Human Validation Surface

### States
- draft
- checked
- approved
- locked
- deprecated

### Storage Implications
Must exist on canonical JSON knowledge records and be reflected in markdown mirrors / UI.

---

## Object: Knowledge Record

### Purpose
Canonical structured output from extraction.

### Lifecycle
`model extraction → structured assembly → draft → review → approved/locked/deprecated → versioned over time`

### Authority Source
ADR-005, corrected `knowledge_v1.json`, actual pipeline output.

### Related Objects
- Source Manifest
- Project
- Knowledge Spine
- Spine Node
- Review State
- Markdown Mirror

### States
- draft
- checked
- approved
- locked
- deprecated

### Storage Implications
File-based, not DB-based. Stored as JSON + markdown. Must include `anchor_node_id` going forward.

---

## Object: Knowledge Spine

### Purpose
Authoritative domain taxonomy that anchors knowledge records.

### Lifecycle
`ingested → parsed → reviewed → approved → rejected`

### Authority Source
ADR-032; `knowledge_spine_v1.json`; future contract/spec needed.

### Related Objects
- Spine Node
- Knowledge Record
- Segment
- Domain Taxonomy

### States
- ingested
- parsed
- reviewed
- approved
- rejected

### Storage Implications
DB operational state plus schema file. Approved spines are required before records/segments can be anchored.

---

## Object: Spine Node

### Purpose
Hierarchical node within a knowledge spine.

### Lifecycle
`generated → reviewed → approved → merged/deprecated`

### Authority Source
ADR-032; `spine_node_v1.json`; future contract/spec needed.

### Related Objects
- Knowledge Spine
- Knowledge Record
- Segment
- Obsidian Node MD

### States
- generated
- reviewed
- approved
- merged
- deprecated

### Storage Implications
Deprecated nodes require re-anchoring of linked records before those records can be approved.

---

## Object: Segment

### Purpose
Canonical execution object for video and other subdivided sources.

### Lifecycle
`source unit → scene/segment detection → segment object → extraction unit → knowledge record(s)`

### Authority Source
ADR-031; segment DB table; segmentation policy pending ADR-033 at this point.

### Related Objects
- Source
- Knowledge Record
- Knowledge Spine
- Spine Node
- PySceneDetect

### States
Not fully formalized in this transcript. Implied states include detected, reviewed, extracted, anchored, approved/rejected.

### Storage Implications
Operational DB table exists; schema/spec contract incomplete at this point.

---

## Object: Session Insight Record

### Purpose
Captures institutional memory from raw chat transcripts: goals, failures, direction changes, decisions, unresolved tensions, assumptions, and scope changes.

### Lifecycle
`raw transcript → extraction contract applied → insight record generated → saved → later integrated into memory/reorientation/knowledge`

### Authority Source
`CIS Session Transcript Extraction Contract v1`; user correction and acceptance.

### Related Objects
- Transcript
- Handoff
- ADR
- Reorientation Document
- Knowledge Record
- Contract Register

### States
Not yet formalized. Implied states: extracted, reviewed, saved, integrated.

### Storage Implications
Stored in `/mnt/projects/cis/docs/claude_chat_transcripts/insights/` using `SESSION_INSIGHT_RECORD_YYYY-MM-DD_NNN.md` naming.

---

## Object: Contract Register

### Purpose
Inventory of all contracts required by the build plan, governing ADRs, schema status, spec document status, and implementation verification status.

### Lifecycle
`created → populated from ADR/schema/runtime audit → updated as contracts are written/verified`

### Authority Source
User-requested governance correction; ADR database; schema folder; runtime audit.

### Related Objects
- ADR
- Contract Spec
- Schema File
- Runtime Script
- Verification Result

### States
Not formalized. Implied: missing, drafted, verified, locked, superseded.

### Storage Implications
Needs canonical location, likely `/mnt/projects/cis/docs/contracts/CIS_CONTRACT_REGISTER.md` or equivalent.

---

## Object: Resolved CIS Live Session Export

### Purpose
Portable artifact generated from resolved CIS Live sessions so they can be reviewed, dragged into future chats, and processed through the transcript insight pipeline.

### Lifecycle
`live session → resolved session → exported markdown → transcript/intelligence processing`

### Authority Source
Gap discovered in this transcript.

### Related Objects
- CIS Live Session
- SQLite DB
- Handoff
- Session Insight Record

### States
Not formalized.

### Storage Implications
No canonical storage path exists yet.

# 12. ARCHITECTURAL DELTA SUMMARY

After this file, CIS gains a new understanding of itself as a system whose build process must be governed with the same rigor as the application it is creating.

The primary delta is that CIS’s institutional memory failure becomes visible as an architectural blocker, not a documentation inconvenience. The system cannot continue depending on ADRs and handoffs alone because those artifacts do not preserve enough reasoning. Transcript-derived session insight records become a required memory layer.

The second delta is that contract governance becomes clearer. ADRs, schemas, specs, and runtime code are no longer allowed to blur together. ADRs record decisions. Contract specs define rules. Schemas define structure. Runtime code implements behavior. The missing bridge is the contract register that shows which expected contracts exist, which are missing, and which implementations were built without the contract-first discipline.

The third delta is that `knowledge_v1.json` is corrected from an obsolete pre-scope-expansion schema to the current runtime-aligned knowledge record schema, including `anchor_node_id` for future spine anchoring.

The fourth delta is that transcript processing itself becomes a governed knowledge formation workflow. The user rejects handoff-like summaries, requires a deterministic extraction contract, demands full-file review, and identifies partial reading as a contract failure. That establishes the quality bar for any future intelligence-mediated ingestion of CIS’s own build history.

The fifth delta is that the build sequence changes. Before this file, the next logical step appeared to be Phase 1 pipeline work: `cis_spine_intake.py`, first spine ingest, PySceneDetect, ADR-033. After this file, the build must address institutional memory, contract register clarity, schema correction, and transcript insight extraction before resuming pipeline expansion.

The new understanding is:

CIS is not only a creative production system. It is also a governed memory-and-execution system whose own development process must be captured, verified, and made reusable. If its build reasoning is not retained, the system repeatedly loses context and recreates drift. Therefore, transcript extraction, contract governance, and institutional memory are not side tasks. They are architectural infrastructure.
