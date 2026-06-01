# CIS Chat 2026-04 002 — Extraction Analysis

Source file: `CIS_Chat_2026-04_002.md`  
Extraction mode: implementation-grade architectural topology extraction  
Output filename: `cis_chat_2026_04_002_extraction_analysis.md`

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery 1 — Segment Becomes a Canonical Execution Object

**Discovery Name**  
Segment as canonical execution object for video-based extraction.

**Architectural Significance**  
The transcript begins with Phase 1 opening around video segmentation. The initial architectural move is to define `Segment` as the video equivalent of the Phase 0 single-image extraction unit. This shifts video ingestion away from treating a complete video as one source unit and toward a processable intermediate object.

**Affected Layers**
- Execution Layer
- Intelligence Layer
- Knowledge Layer
- Workflow Layer
- Runtime schema layer
- Storage / database layer

**Dependency Impact**
- Requires a `segments` table.
- Requires `source_unit_id` linkage.
- Requires segment state tracking.
- Requires extraction runs to accept `Segment` as an input.
- Requires video processing to produce segment files before extraction.
- Later becomes dependent on `anchor_node_id` after the knowledge spine model emerges.

**Build Impact**
- Introduces a new schema and database migration.
- Changes batch extraction from file-list processing to segment-queue processing.
- Requires segmentation method selection before video extraction can scale.

**Runtime Impact**
- Segment objects move through states such as pending, extracted, reviewed, approved.
- Segment objects become runtime targets for extraction.
- Segments carry temporal metadata, file paths, and eventually knowledge-spine anchoring.

---

## Discovery 2 — Scene Detection Alone Is Insufficient

**Discovery Name**  
PySceneDetect is useful but not sufficient as the sole segmentation method.

**Architectural Significance**  
The user identifies a failure case: static-camera tutorial videos may not produce scene cuts, resulting in one long segment. This exposes a hidden assumption in the segmentation design: visual scene change does not equal instructional concept change.

**Affected Layers**
- Execution Layer
- Intelligence Layer
- Workflow Layer
- Knowledge Formation Layer

**Dependency Impact**
- Segmentation requires a policy, not only a tool.
- PySceneDetect must be combined with transcript-aware logic and duration fallback.
- Video segmentation must evaluate instructional density and concept boundaries.

**Build Impact**
- ADR-031 cannot remain limited to scene detection.
- A later ADR-033 is required to define segmentation policy.
- Video extraction cannot scale until the segmentation policy is validated.

**Runtime Impact**
- Long segments must be detected and split.
- Segment validation must include usefulness of knowledge records.
- Failed or overly broad segments trigger fallback or review.

---

## Discovery 3 — Transcript-Assisted Segmentation Becomes Required for Tutorials

**Discovery Name**  
Tutorial segmentation must use transcript concept transitions.

**Architectural Significance**  
Analysis of Blender tutorial transcripts reveals that tutorials are structured by instructional topic blocks, not visual cuts. Spoken transitions, chapter markers, and concept changes become more important than scene boundaries.

**Affected Layers**
- Intelligence Layer
- Execution Layer
- Knowledge Layer
- Routing Layer
- Future Teacher Agent behavior

**Dependency Impact**
- Requires transcript availability or transcript generation.
- Requires text parsing before segmentation.
- Requires concept-transition detection.
- Requires a fallback when transcripts are unavailable.

**Build Impact**
- Adds transcript parsing as a pre-segmentation step.
- Requires segmentation strategy options:
  - duration cap
  - transcript-assisted segmentation
  - hybrid duration + transcript marker segmentation
- Prevents PySceneDetect-only implementation from being production-grade.

**Runtime Impact**
- Source units may be split by topic markers.
- Segments become instructional units rather than visual units.
- Retrieval becomes more granular and useful.

---

## Discovery 4 — Anchor Documents Must Precede Tutorial Ingestion

**Discovery Name**  
Anchor documents must be ingested before source material for structured tutorial domains.

**Architectural Significance**  
The user identifies that Blender tutorials should not be interpreted in isolation. A manual, official documentation set, or structured outline should first establish the conceptual map of the tool. Tutorial transcripts and videos should then be mapped against that anchor.

**Affected Layers**
- Knowledge Layer
- Intelligence Layer
- Execution Layer
- Application Layer
- Retrieval Layer
- Agent Layer

**Dependency Impact**
- Requires a new object type: `knowledge_spine`.
- Requires a new object type: `spine_node`.
- Requires `anchor_node_id` linkage from knowledge records and segments.
- Requires anchor mapping before segmentation.
- Requires domain-specific documentation intake.

**Build Impact**
- Adds a new prerequisite before tutorial extraction.
- Turns spine ingestion into an early Phase 1 requirement.
- Changes the order of implementation: spine first, segmentation second, extraction third.

**Runtime Impact**
- Tutorial sources map to known tool concepts.
- Segments are cut at concept boundaries.
- Knowledge records accumulate under stable conceptual nodes.

---

## Discovery 5 — Knowledge Records Are Concept Contributions, Not Flat Extraction Outputs

**Discovery Name**  
Knowledge records become contributions to ontology nodes.

**Architectural Significance**  
The transcript changes the meaning of a `knowledge_record`. A record is no longer simply the output of extracting one source unit. It is a structured contribution attached to an anchor concept in a domain spine.

**Affected Layers**
- Knowledge Layer
- Retrieval Layer
- Intelligence Layer
- Application Layer
- Obsidian / human-readable documentation layer

**Dependency Impact**
- Requires every approved record to carry `anchor_node_id`.
- Requires records to be positioned in a hierarchy before trusted promotion.
- Requires an unanchored state for early or unresolved records.

**Build Impact**
- `knowledge_v1.json` schema is updated with `anchor_node_id`.
- Markdown record writer must eventually include backlink syntax.
- Review gates must prevent unanchored records from reaching approved state.

**Runtime Impact**
- Records aggregate under spine nodes.
- Multiple sources deepen one concept node.
- Retrieval becomes concept-based rather than file-based.

---

## Discovery 6 — CIS Scope Expands from Creative Production to LIFE + CREATION

**Discovery Name**  
CIS becomes the container for LIFE and CREATION.

**Architectural Significance**  
Review of the WIAS Project Manager spreadsheet confirms that the original analogue system was not only creative production. It was a life and creation management system. The top-level architecture becomes:

- LIFE: Home, Body, Mind
- CREATION: Word, Image, Action, Sound, Web

WIAS becomes the historical name for CREATION only.

**Affected Layers**
- Master Architecture
- Operator Model
- Project Object
- Knowledge Spine Taxonomy
- Workflow Layer
- Application Layer
- Schedule Layer

**Dependency Impact**
- Universal project schema must support both life and creative domains.
- Knowledge spines must support all eight sub-domains.
- Build sequence must defer LIFE implementation while preserving architectural compatibility.

**Build Impact**
- ADR-032 locks the domain taxonomy.
- Project schema becomes universal.
- Future application must not hard-code only WIAS.

**Runtime Impact**
- Every project resolves into a domain/sub-domain.
- Fitness, home management, learning, and creative production can share the same project mechanics.
- CREATION is built first; LIFE is designed now but deferred.

---

## Discovery 7 — SQLite and JSON/MD Serve Different System Roles

**Discovery Name**  
Dual storage architecture clarified.

**Architectural Significance**  
The transcript discovers that there is no `knowledge_records` database table. The dashboard is reading JSON files from disk. The system is not inconsistent; it is dual-mode by design.

**Affected Layers**
- Storage Layer
- Knowledge Layer
- Runtime Layer
- Application Layer
- Obsidian Integration Layer

**Dependency Impact**
- SQLite stores operational state.
- JSON files store machine-readable knowledge records.
- Markdown files store human-readable vault mirrors.
- `anchor_node_id` must be added to the JSON schema, not to a nonexistent DB table.

**Build Impact**
- Avoids creating an unnecessary `knowledge_records` DB table.
- Updates `knowledge_v1.json` instead.
- Adds `knowledge_spines`, `spine_nodes`, and `segments` to SQLite as operational objects.

**Runtime Impact**
- DB manages execution state and relationships.
- Files remain the canonical knowledge content.
- Obsidian remains the human-readable knowledge surface.

---

## Discovery 8 — Contract-First Discipline Was Incomplete

**Discovery Name**  
Missing contract files discovered.

**Architectural Significance**  
The user expects multiple contracts to exist because the build roadmaps required them. Searching the project reveals that only `knowledge_v1.json` exists as a schema contract. Source manifest, processing profile, and review-state contracts had been described but not written as standalone files.

**Affected Layers**
- Governance Layer
- Runtime Layer
- Execution Layer
- Documentation Layer

**Dependency Impact**
- Phase 0 contracts must be written before Phase 1 exits.
- Spine ingestion pipeline depends on missing contract definitions.
- Build roadmap alignment requires schema artifacts to exist on disk, not only in chat.

**Build Impact**
- Adds task to write missing Phase 0 contract documents.
- Prevents future “assumed contract” drift.
- Changes next-session order: contracts before scripts.

**Runtime Impact**
- Runtime cannot fully enforce undocumented contracts.
- Future scripts must reference schema files explicitly.

---

## Discovery 9 — Obsidian Backlinks Become a Human-Readable Topology Layer

**Discovery Name**  
Obsidian backlinks and graph view become a required output format.

**Architectural Significance**  
The user identifies that backlinks would make the Obsidian graph useful for connecting ideas. The assistant connects this to spine nodes and knowledge records. Markdown output must include backlinks to spine nodes and domain structures.

**Affected Layers**
- Knowledge Layer
- Application / Human Interface Layer
- Obsidian Vault Layer
- Documentation Automation Layer

**Dependency Impact**
- `cis_spine_intake.py` must generate spine node Markdown files.
- Knowledge record Markdown writer must include backlink syntax based on `anchor_node_id`.
- The graph depends on structured spine-node files existing in the vault.

**Build Impact**
- Adds task: write Obsidian backlinks and spine node MD files.
- Turns graph visualization into a functional topology surface.
- Connects human-readable documentation to machine-readable ontology.

**Runtime Impact**
- Records cluster around concepts in Obsidian graph view.
- Spine nodes cluster under sub-domains.
- Human users can visually navigate CIS knowledge topology.

---

# 2. TOPOLOGY MUTATIONS

## Mutation 1 — Segmentation Layer Splits from Extraction Layer

Before this transcript, video extraction was implicitly:

```text
video → extraction
```

Then it became:

```text
video → segment → extraction
```

After deeper analysis, it becomes:

```text
video/transcript → concept mapping → anchored segment → extraction
```

This creates a distinct segmentation object layer.

---

## Mutation 2 — Knowledge Spine Layer Inserted Before Segmentation

The major topology mutation is the insertion of a knowledge-spine layer before segmentation:

```text
Anchor Document
→ knowledge_spine
→ spine_nodes
→ source-to-spine mapping
→ concept-based segmentation
→ anchored extraction
```

This means segmentation is no longer a purely media-processing stage. It becomes ontology-driven.

---

## Mutation 3 — WIAS Reclassified Under CREATION

WIAS was previously treated as the top-level creative system. The transcript reclassifies it as the CREATION branch of CIS.

New taxonomy:

```text
CIS
├── LIFE
│   ├── Home
│   ├── Body
│   └── Mind
└── CREATION
    ├── Word
    ├── Image
    ├── Action
    ├── Sound
    └── Web
```

---

## Mutation 4 — Project Object Becomes Universal Across Domains

The project object mutates from creative-production container into universal life/creation container.

A project can now be:
- Blender animation
- fitness training program
- home management system
- music production
- writing project
- software learning path
- body/mind/home routine

The topology becomes project-centered across all domains.

---

## Mutation 5 — Knowledge Record Becomes Spine-Anchored

The `knowledge_record` mutates from isolated record to anchored ontology contribution.

Before:

```text
record_001.json
```

After:

```text
record_001.json
→ anchor_node_id
→ spine_node
→ knowledge_spine
→ domain taxonomy
```

---

## Mutation 6 — Database Role Clarified

The storage topology mutates into a clear dual system:

```text
SQLite DB
→ operational state
→ decisions
→ sessions
→ tasks
→ spines
→ nodes
→ segments

Filesystem JSON/MD
→ knowledge record content
→ human-readable mirror
→ Obsidian vault
```

---

## Mutation 7 — Obsidian Becomes Graph Surface

Obsidian is no longer just a note viewer. It becomes a human-readable visualization of CIS knowledge topology through backlinks:

```text
Knowledge Record MD
→ [[Spine Node]]
→ [[Subject]]
→ [[Sub-domain]]
→ [[Domain]]
```

---

## Mutation 8 — Roadmap Discipline Reinterpreted

The sequential roadmap was designed to avoid scope creep. The transcript mutates this rule:

- arbitrary branches remain forbidden
- load-bearing discoveries must not be deferred
- placeholders are dangerous when they hide core dependencies

This changes governance behavior.

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisite 1 — A Domain Spine Must Exist Before Useful Tutorial Segmentation

The transcript discovers that tutorial segmentation cannot be valid unless the system knows the domain structure first.

Dependency chain:

```text
Anchor documentation
→ knowledge_spine
→ spine_nodes
→ transcript-to-node mapping
→ concept-aware segmentation
→ useful knowledge records
```

---

## Hidden Prerequisite 2 — Transcript Parsing Must Precede Tutorial Video Segmentation

Static-camera tutorials do not produce meaningful scene cuts.

Dependency:

```text
transcript
→ topic transition detection
→ concept mapping
→ segmentation boundaries
```

---

## Hidden Prerequisite 3 — `anchor_node_id` Must Exist Before Knowledge Promotion

Records without an anchor may exist in draft or unanchored state, but cannot become approved.

Dependency:

```text
knowledge_record
→ anchor_node_id
→ spine_node exists
→ spine approved
→ record promotion allowed
```

---

## Hidden Prerequisite 4 — Spine Schema Must Exist Before Migration and Scripts

Contract-first discipline requires the schema to exist before code.

Dependency:

```text
schema contract
→ migration
→ ensure_tables
→ pipeline script
```

---

## Hidden Prerequisite 5 — Phase 0 Contracts Must Be Written Before Phase 1 Completion

Missing contracts discovered:
- source manifest
- processing profile
- review states

These must exist before Phase 1 can be considered stable.

---

## Hidden Prerequisite 6 — Obsidian Graph Requires Spine Node Markdown Files

Backlinks are only useful if target files exist.

Dependency:

```text
spine_node
→ spine_node.md
→ record backlink
→ Obsidian graph edge
```

---

## Hidden Prerequisite 7 — Storage Role Must Be Clarified Before Schema Changes

The failed attempt to alter `knowledge_records` exposed that the table does not exist.

Dependency clarification:

```text
knowledge content schema → JSON file
operational runtime schema → SQLite table
```

---

## Hidden Prerequisite 8 — Live Session UI Needs Decision Capture Mode

The user notices that the Live session interface is not ideal for capturing architectural decisions that emerge mid-conversation.

Dependency:

```text
architectural insight
→ round capture format
→ session continuity
→ governance memory
```

---

## Sequencing Constraints

Corrected sequence at session close:

1. Write missing Phase 0 contracts.
2. Build `cis_spine_intake.py`.
3. Ingest first spine, likely Blender documentation.
4. Install and test PySceneDetect after a spine exists.
5. Write ADR-033 for segmentation policy.
6. Update reorientation documentation.

---

## Circular Dependency Avoided

A potential circular dependency was identified:

```text
Need segmentation to extract tutorials
Need spine to segment tutorials usefully
Need anchor docs to build spine
```

Resolution:

```text
Build spine from anchor docs first.
Then segment source tutorials against the spine.
```

---

## Runtime Blockers

- No `knowledge_records` DB table exists.
- Missing Phase 0 contracts are not yet formalized.
- Spine ingestion script does not yet exist.
- PySceneDetect is not useful until concept anchoring exists.
- `2_CIS_REORIENTATION.md` still reflects Phase 0 architecture.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## New Execution Objects

### Segment

Runtime object for video source units.

Required fields discussed:
- `segment_id`
- `source_unit_id`
- `project_id`
- `segment_index`
- `start_time`
- `end_time`
- `segmentation_method`
- `scene_score`
- `anchor_node_id`
- `file_path`
- `file_format`
- `status`
- `extraction_run_id`
- `created_at`
- `updated_at`

States:
```text
pending → extracted → reviewed → approved
```

---

### knowledge_spine

Operational object stored in SQLite.

Required fields:
- `spine_id`
- `domain`
- `sub_domain`
- `subject`
- `source_type`
- `file_path`
- `node_count`
- `status`
- `ingested_at`
- `updated_at`

States:
```text
ingested → parsed → reviewed → approved
```

---

### spine_node

Operational concept node.

Required fields:
- `node_id`
- `spine_id`
- `parent_node_id`
- `title`
- `depth`
- `path`
- `status`
- `created_at`

States:
```text
generated → reviewed → approved → merged / deprecated
```

---

## Spine Ingestion Pipeline

The transcript defines a five-step pipeline.

### Step 1 — Intake

Input:
- manual
- textbook
- taxonomy
- methodology document
- software documentation
- chapter list
- markdown outline
- HTML documentation

Action:
- register source as `knowledge_spine`
- assign domain and sub-domain
- assign subject
- assign source type
- set state to `ingested`

Output:
- `knowledge_spines` row

---

### Step 2 — Parse

Action:
- extract headings, sections, hierarchy, or structured nodes

Possible parse tools:
- PDF / EPUB heading extraction
- Markdown heading parser
- HTML heading parser
- structured JSON parser
- manual taxonomy input
- chapter list parser

Output:
- flat list of potential nodes with parent-child relationships

State transition:
```text
ingested → parsed
```

---

### Step 3 — Node Generation

Action:
- each structural element becomes a `spine_node`

Output:
- `spine_nodes` rows
- node paths such as:
```text
Blender > Transform > Scale > Axis Constraint
```

State:
```text
generated
```

---

### Step 4 — Human Review

Human actions:
- inspect node tree
- merge nodes
- rename nodes
- reorder nodes
- correct hierarchy

State transition:
```text
parsed → reviewed
```

---

### Step 5 — Approval

Action:
- approve the spine for downstream use

State transition:
```text
reviewed → approved
```

Runtime rule:
- only approved spines can anchor segmentation and knowledge records.

---

## Segment Runtime Flow

```text
source video
→ source_unit
→ segmentation method
→ segment objects
→ anchor_node_id mapping
→ extraction run
→ knowledge record JSON/MD
→ review
→ promotion
```

---

## Runtime Validation Rules

### Segment Validation
Fail or mark for review if:
- missing time range
- missing source unit
- missing file path
- segment duration exceeds allowed threshold without fallback processing
- segment has no anchor where anchor is required
- extraction output is too broad or unfocused

---

### Spine Validation
Fail or hold if:
- missing domain
- missing sub-domain
- missing subject
- empty node tree
- unreviewed node tree
- invalid taxonomy values
- duplicate or malformed nodes
- no human review

---

### Record Validation
Fail or prevent promotion if:
- required schema fields missing
- unsupported claims present
- no `anchor_node_id` where spine exists
- source linkage missing
- uncertainty omitted when ambiguity exists
- raw model output not normalized

---

## Commands / Runtime Actions Identified

Commands or scripts mentioned or implied:
- `migrate_phase1_schemas.py`
- `ensure_phase1_tables(conn)`
- `cis_spine_intake.py` (planned)
- PySceneDetect smoke test
- schema file writes to `/mnt/projects/cis/runtime/schemas/`
- Git sync of handoff / vault updates

---

## Execution Constraint

The system cannot rely on scripts alone unless they reference schema authority.

Every table and pipeline script must reference:
- schema file
- ADR number
- version

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Governance Discovery 1 — Load-Bearing Branches Must Not Be Treated as Scope Creep

The user explicitly identifies that conservative sequencing can hide core functionality if every branch is deferred. The transcript distinguishes:

- arbitrary rabbit holes
- architectural discoveries that expose missing prerequisites

Rule emerging:

```text
If a branch exposes a hidden dependency required for the system to function, it is not scope creep.
```

---

## Governance Discovery 2 — ADR-031 Requires Amendment

ADR-031 initially centered scene detection. The transcript identifies that segmentation policy must include:
- scene detection
- duration fallback
- transcript-assisted option
- concept-map segmentation
- quality gate

This is deferred to ADR-033.

---

## Governance Discovery 3 — ADR-032 Locks Domain Taxonomy and Spine Model

ADR-032 establishes:
- LIFE and CREATION top-level domains
- WIAS as CREATION only
- universal project schema
- `knowledge_spine` as first-class object
- `spine_node` as atomic concept object
- `anchor_node_id` as knowledge-record linkage
- CREATION built first, LIFE deferred

---

## Governance Discovery 4 — Schema Contracts Must Be Real Files

The user asks where the schema doc is stored and how it maintains alignment. This reveals that chat-only schema definitions are not governance artifacts.

Rule:

```text
A contract exists only when it is written to disk, referenced by ADRs/scripts, and version controlled.
```

---

## Governance Discovery 5 — Live Session Round Type Is Inadequate

The user notices the Live session round interface was designed for Q&A, not emergent architectural decision capture.

Required governance mutation:
- add round types
- support decision/insight/scope-change capture
- separate architectural notes from model-response rounds

---

## Governance Discovery 6 — Human Review Is Required Before Spine Approval

Spines are authoritative. Therefore:
- generated node trees cannot be trusted automatically
- human review is required
- approval makes spine available for downstream anchoring

---

## Promotion Logic

### Spine Promotion
```text
ingested → parsed → reviewed → approved
```

### Spine Node Promotion
```text
generated → reviewed → approved
```

### Knowledge Record Promotion
```text
draft → checked/reviewed → approved → locked
```

Additional rule:
- unanchored records cannot reach approved status where a relevant spine exists.

---

## Rejection Paths

### For Segments
- too long
- too broad
- no anchor
- low extraction quality
- segmentation method failed
- transcript mapping failed

### For Spines
- malformed hierarchy
- missing subject
- duplicate taxonomy
- poor parse
- unsupported source type

### For Knowledge Records
- no source linkage
- no anchor
- unsupported claims
- schema failure
- excessive generality
- missing uncertainty

---

## Trust Enforcement

Trust is enforced by:
- schema files
- ADRs
- human review
- status states
- anchored records
- version control
- operational DB state
- JSON/MD record mirrors

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Changes

Before:
```text
raw source → extraction → knowledge record
```

After:
```text
domain anchor → spine → nodes → source mapping → extraction → anchored record
```

---

## Knowledge Records Become Accumulative

Multiple records can attach to the same spine node:

```text
Blender Manual: Scale
Tutorial 1: Scale basics
Tutorial 2: Axis constraints
Transcript segment: Scale shortcut
User note: common issue
```

All deepen the same concept node.

---

## Knowledge Is Domain-Positioned

Every knowledge record should eventually locate itself within:

```text
CIS
→ LIFE / CREATION
→ sub_domain
→ subject
→ spine_node
→ record
```

---

## Retrieval Structure

Retrieval should use:
- domain
- sub-domain
- subject
- spine path
- anchor node
- related records
- project links
- status / review state

---

## Indexing Implications

A future `KNOWLEDGE_INDEX.md` or equivalent should render:
- spines
- nodes
- records
- backlinks
- status
- project links

This can support:
- human navigation
- agent navigation
- Obsidian graph
- no-vector baseline retrieval

---

## Normalization Rules

Knowledge content remains in JSON/MD records. Operational metadata lives in DB tables.

This means:
- `knowledge_v1.json` is schema authority for knowledge content
- `knowledge_spine_v1.json` is schema authority for spines
- `spine_node_v1.json` is schema authority for nodes

---

## Ontology / Spine Implications

Spines are shared domain infrastructure, not project-specific. A Blender spine can be used by many projects.

This creates:
```text
domain infrastructure
→ reusable concept graph
→ project-specific knowledge attachment
```

---

## Chunking Logic

Video/tutorial content should be chunked by:
- concept transition
- transcript markers
- anchor-node mapping
- duration threshold fallback
- scene detection only where visually meaningful

---

## Reinforcement Behavior

User corrections to spine nodes and record anchoring become system learning signals:
- merged nodes
- renamed concepts
- corrected paths
- rejected anchors
- recurring patterns

These can improve future spine mapping.

---

## Project Linkage

Every knowledge record may support:
- global domain knowledge
- project-specific application
- multiple project links
- reusable learning assets

---

## Stabilization Loop

```text
source enters
→ system proposes structure
→ human corrects
→ spine stabilizes
→ future mapping improves
→ retrieval improves
→ production support improves
```

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Required Workbench Functions

The transcript implies the future application must expose:

### Spine Management Panel
- create spine
- select domain / sub-domain
- ingest anchor source
- review node tree
- approve spine
- merge or deprecate nodes

### Source Mapping Panel
- display transcript/source
- show detected concepts
- map concepts to spine nodes
- flag unmapped regions

### Segmentation Panel
- show visual scene cuts
- show transcript topic boundaries
- show concept boundaries
- allow review of segment-to-node mapping

### Knowledge Record Panel
- show JSON/MD output
- show anchor node
- show related records at same node
- approve / reject / edit

### Obsidian Graph / Backlink Panel
- show node MD files
- show record backlinks
- preview graph readiness

---

## Runtime Visibility Needs

The app must reveal:
- spine status
- node status
- segment status
- record anchoring status
- unanchored records
- records blocked from promotion
- missing contracts
- schema version

---

## Operator Actions

The user must be able to:
- approve a spine
- edit node hierarchy
- merge nodes
- reject weak mappings
- anchor or re-anchor records
- mark uncertainty
- approve knowledge promotion
- generate or refresh Obsidian backlinks

---

## Application / Runtime Bridges

The interface must call or expose:
- `cis_spine_intake.py`
- segment generation
- transcript mapping
- record writing
- backlink writer
- status update functions
- schema validation
- task logging
- Live session decision capture

---

## Project-Centered Interaction

Because every domain resolves into a project, the application must allow:
- project creation across LIFE and CREATION
- attaching spines and knowledge to projects
- using global spines within project contexts
- linking project work back to spine nodes

---

## Human Interface Implication

The Obsidian vault is not a side artifact. It is part of the human-readable application surface.

---

# 8. FEEDBACK LOOP DISCOVERIES

## Loop 1 — Spine Formation Loop

```text
anchor document
→ parse
→ node tree
→ human review
→ approved spine
→ future source mapping
```

---

## Loop 2 — Source-to-Spine Mapping Loop

```text
tutorial/source
→ transcript analysis
→ concept detection
→ spine-node mapping
→ segment generation
→ review
→ correction
```

---

## Loop 3 — Knowledge Accumulation Loop

```text
multiple sources
→ same anchor node
→ records accumulate
→ concept deepens
→ Teacher/Librarian improves
```

---

## Loop 4 — Correction / Reinforcement Loop

```text
system proposes
→ human corrects
→ node merge/rename/re-anchor
→ system stores pattern
→ future proposals improve
```

---

## Loop 5 — Governance Loop

```text
architectural discovery
→ Live round
→ ADR
→ schema file
→ migration/script
→ handoff update
→ Git sync
```

---

## Loop 6 — Obsidian Human-Readability Loop

```text
knowledge record
→ markdown mirror
→ backlinks
→ Obsidian graph
→ human navigation
→ insight discovery
→ further correction
```

---

## Loop 7 — Session Memory Automation Loop

The Karpathy transcript discussion introduces a future loop:

```text
session ends
→ summary/handoff generated
→ daily log
→ flush to wiki/knowledge records
→ regenerate index
→ Git sync
```

This is not implemented but is identified as highly relevant.

---

## Loop 8 — Build Roadmap Correction Loop

```text
planned roadmap
→ real build exposes hidden requirement
→ roadmap corrected
→ handoff updated
→ next session starts from corrected order
```

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Gap 1 — Missing Phase 0 Contract Documents

Missing as standalone files:
- source manifest contract
- processing profile contract
- review state contract

Impact:
- scripts may rely on assumptions
- runtime enforcement incomplete
- future contributors cannot verify contracts

---

## Gap 2 — `cis_spine_intake.py` Does Not Exist

This is the next critical implementation object.

It must:
- ingest anchor document
- parse structure
- generate nodes
- create spine records
- write node Markdown files
- support review state
- prepare approved spine for mapping

---

## Gap 3 — Spine Node Markdown Writer Not Yet Built

Required for Obsidian graph functionality.

Must produce:
- one Markdown file per spine node
- backlink hierarchy
- list of attached records
- domain/sub-domain links

---

## Gap 4 — Knowledge Record Markdown Writer Needs Backlinks

Required additions:
- links to anchor node
- links to subject
- links to domain and sub-domain
- related record links
- perhaps status / schema metadata

---

## Gap 5 — Transcript-to-Spine Mapping Not Defined

Still required:
- concept detection strategy
- timestamp mapping
- confidence scores
- unmapped concept handling
- human correction path

---

## Gap 6 — Segmentation Policy Not Locked

ADR-033 is required.

Must define:
- scene detection role
- duration fallback
- transcript-assisted mode
- concept-map segmentation
- minimum/maximum segment duration
- overlap rules
- quality gates

---

## Gap 7 — PySceneDetect Not Yet Installed / Tested

Deferred until after spine exists.

Important correction:
- PySceneDetect test without a spine is no longer meaningful.

---

## Gap 8 — Live Session Input Model Inadequate

Needs:
- round type field
- architectural decision capture mode
- insight capture mode
- correction mode
- implementation log mode

---

## Gap 9 — Reorientation Document Outdated

`2_CIS_REORIENTATION.md` still reflects Phase 0 architecture and must be updated to include:
- segments
- spines
- nodes
- LIFE/CREATION taxonomy
- dual storage clarification
- corrected build sequence

---

## Gap 10 — Knowledge Index Not Built

Needed:
- `KNOWLEDGE_INDEX.md`
- spine-based listing
- record links
- domain/sub-domain grouping
- status indicators

---

## Gap 11 — Schema Versioning Underdeveloped

Existing schemas are flat JSON.

Need:
- schema version tracking
- relationship to migrations
- field authority rules
- mutability rules
- validation enforcement

---

## Gap 12 — Source Unit Table Status Unclear

Initial schema discussion referenced `source_units`, but the actual database table state was not fully resolved in the extraction.

This remains a potential structural gap.

---

# 10. BUILD-PLAN IMPLICATIONS

## Corrected Build Sequence

The transcript ends by correcting the next-session order:

```text
1. Write missing Phase 0 contracts
2. Build cis_spine_intake.py
3. Ingest first spine, likely Blender documentation
4. Install and test PySceneDetect
5. Write ADR-033 segmentation policy
6. Update 2_CIS_REORIENTATION.md
```

---

## Foundational Prerequisites

Before video/tutorial extraction can scale:
- schema contracts must exist
- spine ingestion must work
- at least one approved domain spine must exist
- transcript mapping must be designed
- segmentation policy must be locked

---

## Blocked Layers

### Video Extraction
Blocked by:
- no approved spine
- no segmentation policy
- no transcript mapping

### Teacher Agent
Blocked by:
- validated knowledge records
- spine-node organization
- retrieval/index structure

### Librarian Agent
Blocked by:
- spine-based knowledge map
- record anchoring
- approved records

### Application Layer
Blocked by:
- execution contracts
- spine ingestion pipeline
- review state model
- source/record visibility

---

## Runtime-First Requirements

The runtime must support:
- spine table
- node table
- segment table
- schema files
- `ensure_phase1_tables()`
- record schema update with `anchor_node_id`

These were partially implemented in the transcript.

---

## Governance-First Requirements

Required before further build:
- ADR-033
- missing Phase 0 contracts
- reorientation update
- task for Live session round type improvement

---

## Execution-First Requirements

The next executable pipeline is not PySceneDetect. It is:

```text
anchor document → spine ingestion → node generation → review → approved spine
```

---

## Application Dependencies

Future interface must expose:
- spine creation/review
- source mapping
- segment-to-node mapping
- record anchoring
- unanchored blockers
- Obsidian graph readiness

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object 1 — Segment

**Purpose**  
A discrete video extraction unit.

**Lifecycle**
```text
pending → extracted → reviewed → approved
```

**Authority Source**
- system-generated by segmentation pipeline
- human-reviewed before approval
- later governed by ADR-033 segmentation policy

**Related Objects**
- source_unit
- project
- extraction_run
- spine_node
- knowledge_record

**States**
- pending
- extracted
- reviewed
- approved

**Storage Implications**
- stored in SQLite `segments`
- includes path to segment file
- includes `anchor_node_id` when mapped

---

## Object 2 — knowledge_spine

**Purpose**  
Authoritative knowledge structure for a domain, sub-domain, subject, tool, methodology, or production step.

**Lifecycle**
```text
ingested → parsed → reviewed → approved
```

**Authority Source**
- anchor document
- user domain assignment
- human review
- ADR-032

**Related Objects**
- spine_node
- knowledge_record
- segment
- domain taxonomy
- Obsidian node files

**States**
- ingested
- parsed
- reviewed
- approved
- rejected / deprecated in future

**Storage Implications**
- stored in SQLite `knowledge_spines`
- schema file: `knowledge_spine_v1.json`
- does not store extracted knowledge content
- shared across projects

---

## Object 3 — spine_node

**Purpose**  
Atomic concept position inside a knowledge spine.

**Lifecycle**
```text
generated → reviewed → approved → merged / deprecated
```

**Authority Source**
- parsed anchor document
- human review and correction
- approved spine hierarchy

**Related Objects**
- knowledge_spine
- segment
- knowledge_record
- Obsidian Markdown node
- backlinks

**States**
- generated
- reviewed
- approved
- merged
- deprecated

**Storage Implications**
- stored in SQLite `spine_nodes`
- schema file: `spine_node_v1.json`
- must eventually produce MD file for graph view

---

## Object 4 — anchor_node_id

**Purpose**  
Link between a knowledge record or segment and its concept location in the spine.

**Lifecycle**
- empty / unanchored at draft
- assigned during mapping or review
- required for approval where spine exists
- retained unless human re-anchors

**Authority Source**
- system mapping proposal
- human confirmation
- approved spine node

**Related Objects**
- spine_node
- knowledge_record
- segment

**States**
- null / unanchored
- proposed
- confirmed
- stale / requires re-anchor if node deprecated

**Storage Implications**
- added to `knowledge_v1.json`
- exists in `segments` DB table
- not added to nonexistent `knowledge_records` table

---

## Object 5 — Domain Taxonomy

**Purpose**  
Top-level organizational structure for CIS.

**Lifecycle**
- locked by ADR-032
- CREATION built first
- LIFE deferred but architecturally present

**Authority Source**
- WIAS Project Manager spreadsheet
- user clarification
- ADR-032

**Related Objects**
- projects
- knowledge_spines
- application modules
- schedules
- retrieval hierarchy

**States**
- defined
- partially implemented
- expanded over time

**Storage Implications**
- likely controlled through schema / config
- must constrain spine domain and sub_domain values

---

## Object 6 — Knowledge Record JSON

**Purpose**  
Machine-readable canonical knowledge content.

**Lifecycle**
```text
created → draft → reviewed → approved → locked/deprecated
```

**Authority Source**
- extraction pipeline
- user correction
- source material
- schema `knowledge_v1.json`

**Related Objects**
- MD mirror
- spine_node
- project
- source
- extraction run

**States**
- draft
- reviewed
- approved
- locked
- deprecated

**Storage Implications**
- stored as JSON file under records directory
- not stored as DB table
- updated schema includes `anchor_node_id`

---

## Object 7 — Knowledge Record Markdown Mirror

**Purpose**  
Human-readable Obsidian version of knowledge record.

**Lifecycle**
- generated from JSON
- updated when record changes
- enriched with backlinks

**Authority Source**
- JSON record
- MD writer
- Obsidian vault conventions

**Related Objects**
- JSON record
- spine_node MD files
- Obsidian graph

**States**
- generated
- stale
- refreshed

**Storage Implications**
- stored in vault
- should include backlinks for graph topology

---

## Object 8 — Live Session Round

**Purpose**  
Capture session-level decisions, insights, corrections, and development notes.

**Lifecycle**
- created during session
- resolved in handoff
- synced to vault / Git

**Authority Source**
- user / assistant during live architecture work

**Related Objects**
- ADR
- tasks
- handoff
- session log

**States**
- open
- consolidated
- resolved

**Storage Implications**
- SQLite operational state
- needs round type improvement

---

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did not exist before?

This transcript introduces a major architectural redefinition of CIS.

Before this file, CIS was primarily understood as:

```text
a story-first creative production infrastructure
with intake, extraction, workflow, knowledge records, and tools
```

After this file, CIS is understood as:

```text
a LIFE + CREATION operating system
where every project is organized through domain-specific knowledge spines,
where source material is mapped to authoritative concept structures before extraction,
and where knowledge accumulates at spine nodes across sources over time.
```

The most important new understanding is:

```text
Ontology must precede extraction.
```

A source should not be processed merely because it exists. It should be processed into a known or emerging conceptual structure.

The transcript proves that:
- segmentation cannot be tool-first
- extraction cannot be source-first
- retrieval cannot be flat
- knowledge records cannot remain orphaned
- PySceneDetect cannot be the architectural center
- manual documentation must become schema-governed runtime contracts
- Obsidian can serve as a human-readable topology layer
- LIFE domains must remain architecturally present even if deferred in build order

The system therefore mutates from:

```text
intake → extraction → record
```

into:

```text
domain → spine → node → source mapping → segment → extraction → anchored record → backlink graph → retrieval / teaching / reuse
```

This transcript also exposes a major governance correction:

```text
The roadmap must prevent arbitrary drift, but must not suppress load-bearing discoveries.
```

The build plan must therefore allow architectural recursion when a hidden prerequisite is discovered.

The dominant architectural delta is the appearance of the Knowledge Spine as the missing bridge between:
- raw archive material
- tutorial transcripts
- segmentation
- knowledge records
- retrieval
- Obsidian graph view
- future Teacher/Librarian agents
- application-layer workbench surfaces

This file is therefore a critical topology mutation record and should be treated as a foundational CIS architecture artifact.

---

# TOPOLOGY-READY NODE LIST

## Primary Nodes
- CIS
- LIFE
- CREATION
- Home
- Body
- Mind
- Word
- Image
- Action
- Sound
- Web
- Project Object
- Anchor Document
- knowledge_spine
- spine_node
- Segment
- Transcript
- Concept Map
- knowledge_record JSON
- knowledge_record MD
- Obsidian Graph
- SQLite Operational DB
- Live Session
- ADR
- Handoff
- PySceneDetect
- cis_spine_intake.py

---

# TOPOLOGY-READY EDGE LIST

```text
CIS → LIFE
CIS → CREATION
LIFE → Home
LIFE → Body
LIFE → Mind
CREATION → Word
CREATION → Image
CREATION → Action
CREATION → Sound
CREATION → Web

Project → Domain/Sub-domain
Project → Source Material
Project → Knowledge Records

Anchor Document → knowledge_spine
knowledge_spine → spine_node
spine_node → anchor_node_id
anchor_node_id → Segment
anchor_node_id → knowledge_record JSON
knowledge_record JSON → knowledge_record MD
knowledge_record MD → Obsidian Backlinks
Obsidian Backlinks → Obsidian Graph

Transcript → Concept Detection
Concept Detection → Spine Mapping
Spine Mapping → Segment Boundaries
Segment Boundaries → Segment
Segment → Extraction Run
Extraction Run → knowledge_record JSON

SQLite DB → operational state
Filesystem → JSON/MD knowledge content

Live Session → Round
Round → ADR
ADR → Schema
Schema → Migration
Migration → Runtime Table
Runtime Table → Application Surface

Handoff → Git Sync
Git Sync → Continuity
```

---

# BUILD-PLAN WARNING FLAGS

## Warning 1
Do not build video segmentation before spine ingestion.

## Warning 2
Do not treat PySceneDetect as the primary intelligence method.

## Warning 3
Do not promote unanchored knowledge records where a relevant spine exists.

## Warning 4
Do not assume contracts exist unless files exist on disk.

## Warning 5
Do not split LIFE out of CIS architecturally, even if LIFE implementation is deferred.

## Warning 6
Do not let JSON/MD knowledge records drift from SQLite operational objects.

## Warning 7
Do not build the application layer without exposing spine review and anchoring status.

---

# FINAL BUILD-ORDER EXTRACTION

## Immediate Next Build Order

1. Write missing Phase 0 contracts:
   - source manifest
   - processing profile
   - review states

2. Build `cis_spine_intake.py`.

3. Ingest first approved spine:
   - likely Blender documentation
   - generate `knowledge_spines`
   - generate `spine_nodes`
   - generate spine node MD files

4. Design transcript-to-spine mapping.

5. Then test PySceneDetect against a video.

6. Write ADR-033:
   - scene detection
   - duration fallback
   - transcript-assisted segmentation
   - concept-map segmentation
   - quality gates

7. Update reorientation document.

8. Update knowledge record MD writer with Obsidian backlinks.

9. Generate initial `KNOWLEDGE_INDEX.md`.

---

# END OF EXTRACTION
