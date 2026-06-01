# architecture_atlas_prompt_wias_project_manager_version_1_xlsb — Extraction Analysis

Source document: `architecture_atlas_prompt_WIAS Project Manager (version 1).xlsb.xlsx`  
Extraction mode: implementation-grade architectural topology extraction  
Reference image: `example_CIS_Chat_2026-04_004_topo03.png`  

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Workbook as Analogue Application Data Model

- **Architectural Significance**  
  The workbook is not only a tracker or schedule. It is an early application schema for CIS. It already contains object tables, classification lists, project status states, production schedules, software/tool mappings, research/reference/learning records, templates, checklists, genre taxonomies, and user-level metadata.
- **Affected Layers**
  - Project Object Layer
  - Workflow Layer
  - Knowledge Layer
  - Application Layer
  - Execution Layer
- **Dependency Impact**
  CIS application design should not invent its object model from scratch. It must derive the first project-management and knowledge-management schema from this workbook.
- **Build Impact**
  Build order changes from “design UI first” to “normalize workbook entities into canonical objects first.”
- **Runtime Impact**
  Runtime objects should be instantiated from workbook-derived entities: `Project`, `Idea`, `Research`, `Reference`, `Learning`, `Template`, `Checklist`, `Status`, `Schedule Slot`, `Software`, `Genre`, and `Medium`.

---

## Discovery Name: Project Object Already Exists as Persistent Container

- **Architectural Significance**  
  The `projects` sheet defines a project as a persistent relational container with fields for project identity, idea linkage, user level, project type, project goal, research, reference, status, checklists, templates, and learning.
- **Affected Layers**
  - Project Object Layer
  - Workflow Layer
  - Application Layer
  - Knowledge Layer
- **Dependency Impact**
  All downstream system objects should attach to `project id` rather than floating as independent files or notes.
- **Build Impact**
  The first CIS data model should implement the project container before building advanced workflow automation.
- **Runtime Impact**
  Runtime actions must preserve project linkage when ingesting research, reference, learning, checklist, and template records.

Workbook fields observed:
- `project id`
- `project name`
- `creation date`
- `idea name`
- `user level`
- `project type`
- `project goal`
- `research`
- `reference`
- `status`
- `checklists`
- `templates`
- `learning`

---

## Discovery Name: Idea → Project Conversion Is Already Modeled

- **Architectural Significance**  
  The `ideas definition` sheet contains early-stage idea fields: name, link, original date, description, context, category, category medium, and story type. The `Projects Form` sheet then provides a structured intake surface for converting those ideas into projects.
- **Affected Layers**
  - Intake Layer
  - Project Initiation Layer
  - Application Layer
  - Workflow Layer
- **Dependency Impact**
  CIS must implement an idea-intake state before project creation.
- **Build Impact**
  Project creation should depend on minimal validated idea fields rather than arbitrary project folder creation.
- **Runtime Impact**
  Intake should produce a draft `Idea` object. Promotion to `Project` should create a `Project` object with linked source idea metadata.

Observed idea fields:
- `idea name`
- `idea link`
- `idea original date`
- `idea description`
- `idea context`
- `catagory`
- `catagory medium`
- `story type`

---

## Discovery Name: WIAS Is Encoded as Schedule Categories and Production Domains

- **Architectural Significance**  
  The workbook encodes Word/Web, Image, Action, and Sound as schedule categories and creative production lanes. This confirms that WIAS began as an operational scheduling/workflow system, not only as a conceptual taxonomy.
- **Affected Layers**
  - Workflow Layer
  - Schedule Layer
  - Application Layer
  - Tool Layer
- **Dependency Impact**
  Each WIAS domain must support status states, tools, training, theory, skill practice, and templates.
- **Build Impact**
  The application should expose WIAS as project-stage panels, not only folders.
- **Runtime Impact**
  Schedule slots and workflow states should map to active WIAS stages.

Observed WIAS categories:
- `word / web`
- `image`
- `action`
- `sound`
- `non-digital product`
- `wildcard`

---

## Discovery Name: Status Sheet Defines Workflow State Vocabulary

- **Architectural Significance**  
  The `status` sheet contains the clearest early workflow state list. It spans idea/project formation, research, reference, outlining, writing, 2D, 3D, editing, sound, publishing, learning, and completion.
- **Affected Layers**
  - Workflow Layer
  - Execution Layer
  - Project State Machine
  - Checklist Layer
- **Dependency Impact**
  Workflow execution must map these statuses into normalized state transitions.
- **Build Impact**
  A status normalization pass is required before implementation.
- **Runtime Impact**
  Project status must become a controlled field with allowed transitions rather than free text.

Observed status/state vocabulary includes:
- `idea link`
- `create project`
- `research`
- `reference`
- `general outline`
- `treatment`
- `outline to script`
- `write script`
- `design concept art`
- `storyboard`
- `create 2d animatic`
- `animate 2d`
- `3d previz`
- `create 3d enviroment`
- `sculpt 3d model`
- `texture 3d model`
- `animate 3d`
- `create 3d motion graphics`
- `create 3d rendering`
- `create 3d game`
- `create vfx`
- `edit film`
- `colorgrade film`
- `create ar`
- `create vr`
- `music production`
- `sound design`
- `stream/record content`
- `create web post`
- `create learning course`
- `complete`

---

## Discovery Name: Schedule Is a Repeating Production Operating System

- **Architectural Significance**  
  The `7 day schedule` and `72 production schedule` sheets encode production time as repeatable slots with schedule id, week count, day count, duration, category, project step, software, start/end date, start/end time, software training, artform theory, skill practice, and templates.
- **Affected Layers**
  - Workflow Layer
  - Application Layer
  - Execution Planning
  - Operator Model
- **Dependency Impact**
  CIS must support time-blocked creative workflow execution, not only project records.
- **Build Impact**
  The Workbench should eventually include a schedule/work queue panel.
- **Runtime Impact**
  Workflow execution may be triggered by active schedule slot context.

Observed schedule fields:
- `schedule id`
- `week count`
- `day count`
- `day name`
- `duration`
- `schedule catagory`
- `project step`
- `software`
- `start date`
- `start time`
- `end date`
- `end time`
- `software training`
- `artform theory`
- `skill practice`
- `templates`

---

## Discovery Name: Tool Selection Is Workflow-Stage Dependent

- **Architectural Significance**  
  Tools are mapped to project steps rather than treated as the system center. Example mappings include Final Draft for writing, Clip Studio/Photoshop for concept work, Unreal/Blender/Houdini/Resolve for production, and Studio One/Native Instruments/Toontrack/Spectrasonics for sound.
- **Affected Layers**
  - Tool Layer
  - Workflow Layer
  - Application Layer
  - Intelligence Guidance Layer
- **Dependency Impact**
  Tool invocation should be stage-aware and project-aware.
- **Build Impact**
  Tool launcher should attach tools to WIAS stage context.
- **Runtime Impact**
  Runtime should not merely launch tools; it should launch tools with project context, expected output, and storage target.

---

## Discovery Name: Research, Reference, Learning, Templates, and Checklists Are Separate Object Classes

- **Architectural Significance**  
  The workbook separates source/knowledge/support entities into distinct sheets. These are early canonical object candidates.
- **Affected Layers**
  - Knowledge Layer
  - Application Layer
  - Agent Layer
  - Project Object Layer
- **Dependency Impact**
  Knowledge cannot be modeled as a single generic note table. CIS needs typed knowledge/support entities.
- **Build Impact**
  Implement a canonical `knowledge_record` plus normalized views for `Research`, `Reference`, `Learning`, `Template`, and `Checklist`.
- **Runtime Impact**
  Each object type needs lifecycle, authority, project linkage, and review state.

Observed object tables:
- `research`
- `reference`
- `learning`
- `templates`
- `checklists`

---

## Discovery Name: Genre and Medium Taxonomies Are Already Deeply Enumerated

- **Architectural Significance**  
  The workbook includes medium and genre lists across poetry, fiction, nonfiction, scripts, song lyrics, drawing, painting, 2D animation, 3D animation, 3D game, film, music production, sound design, and learning type.
- **Affected Layers**
  - Ontology/Knowledge Spine
  - Project Classification
  - Retrieval Layer
  - Application Filters
- **Dependency Impact**
  The taxonomy should become an ontology spine, not remain disconnected sheet tabs.
- **Build Impact**
  Taxonomies should be normalized into lookup tables before UI build.
- **Runtime Impact**
  Project classification, reference retrieval, and Teacher/Librarian agents should use this taxonomy.

---

## Discovery Name: User Level Is a Project Calibration Field

- **Architectural Significance**  
  The workbook includes `user level` and project records contain user-level values. This indicates that workflow guidance was meant to adapt to skill level.
- **Affected Layers**
  - Intelligence Layer
  - Teacher Agent
  - Workflow Layer
  - Application Layer
- **Dependency Impact**
  Teacher outputs should be calibrated to user level.
- **Build Impact**
  User level should become an application/user profile field and a project-specific override.
- **Runtime Impact**
  AI evaluation should consider skill level when estimating difficulty, risk, templates, and next actions.

---

# 2. TOPOLOGY MUTATIONS

## Workbook → Application Schema Mutation

The workbook should be reclassified as a prototype application database. Its sheets represent:
- object tables
- lookup tables
- workflow state vocabularies
- schedule systems
- tool registries
- taxonomy registries
- intake forms
- relational project links

## Flat Sheets → Object Graph

The topology mutates from spreadsheet tabs into a graph:

`Idea`  
→ promoted into `Project`  
→ links to `Research`  
→ links to `Reference`  
→ links to `Learning`  
→ links to `Template`  
→ links to `Checklist`  
→ advances through `Status`  
→ scheduled through `Schedule Slot`  
→ executed with `Software`  
→ classified by `Medium / Genre / Project Goal`.

## Schedule → Workflow Execution Bridge

The `7 day schedule` and `72 production schedule` are not just calendar layouts. They act as execution bridges between:
- time
- production step
- WIAS category
- tool/software
- training/theory/practice support
- templates

## Project Form → Intake/Application Surface

The `Projects Form` sheet indicates an early visual interface:
- owner
- user level
- idea name
- creation date
- start/due date
- project name
- project type
- project goal
- research/reference
- status/checklists
- templates/learning

This mutates into the first Project Intake panel of CIS.

## Taxonomy Sheets → Knowledge Spine

Genre, medium, project goal, project category, learning type, equipment type, and product type sheets become controlled vocabulary nodes for:
- classification
- retrieval
- filters
- recommendations
- project scaffolding
- agent routing

## Tools Sheet → Tool Registry

The `software` sheet becomes an early tool registry:
- developer/vendor
- software name
- URL
- category
- associated status/steps
- templates
- checklists

This mutates into a canonical `Tool` object or `Tool Registry`.

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisite: Normalize Workbook Entities Before Building the App

The workbook already contains operational structure, but field names are inconsistent and some values are duplicated or misspelled. A normalization pass is required before implementation.

Examples:
- `catagory` should normalize to `category`
- `enviroment` should normalize to `environment`
- `2D Animation` / `2d animation` variants should collapse
- `sound ` includes trailing space
- `general outline ` includes trailing space
- status values differ between sheets

## Hidden Prerequisite: Project Object Must Precede Knowledge Attachment

Research, reference, learning, templates, and checklists are all linked to project names/IDs. Knowledge ingestion must therefore either:
1. attach to an existing project, or
2. enter as global knowledge with later project linkage.

## Hidden Prerequisite: Status Vocabulary Must Become a State Machine

The status sheet lists states, but not allowed transitions. The execution layer requires:
- allowed starting states
- next allowed states
- branch rules
- completion states
- reset/rework states
- rejected/blocked states

## Hidden Prerequisite: Schedule Slots Need Runtime Semantics

Schedule rows contain time blocks, categories, steps, and tools, but no runtime state. A schedule slot needs:
- planned
- active
- completed
- skipped
- moved
- blocked
- reviewed

## Hidden Prerequisite: Knowledge Object Types Need Shared Canonical Layer

Research, reference, learning, templates, and checklists are separate sheets. For implementation, they should be normalized under a shared `knowledge_record` / `support_record` model while retaining type-specific views.

## Hidden Prerequisite: Tool Registry Needs Capability Mapping

The software sheet lists tools but does not fully define:
- capability
- input/output formats
- supported WIAS stage
- launch command
- project folder target
- required templates
- fallback tools

## Runtime Blocker: Workbook Contains Data But No Validation Gates

The workbook contains fields but no explicit validation logic. CIS must add:
- required field checks
- type checks
- controlled vocabulary checks
- relationship checks
- project linkage checks
- duplicate checks
- status transition checks

## Orchestration Bottleneck: Manual Relational Linking

Research/reference/learning/templates/checklists are linked manually in the workbook. Application build must automate or assist relationship creation.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## Required Runtime Contract: Idea Intake

### Input
- idea name
- idea link
- original date
- description
- context
- category
- category medium
- story type

### Process
1. create `idea_id`
2. validate required idea fields
3. classify WIAS category
4. capture source link/upload if present
5. set status = `draft_idea`
6. prepare for project promotion

### Output
- `Idea` object

### State Transition
`captured` → `classified` → `project_candidate`

---

## Required Runtime Contract: Project Creation

### Input
- idea reference
- owner
- user level
- start date
- due date
- project name
- project type/scope
- project goal
- initial status
- optional research/reference/template/learning links

### Process
1. create `project_id`
2. link source `idea_id`
3. assign `project_goal`
4. assign `project_type`
5. assign `user_level`
6. initialize relation arrays:
   - `research_ids`
   - `reference_ids`
   - `learning_ids`
   - `template_ids`
   - `checklist_ids`
7. infer active WIAS stages from goal/status
8. set status = `create project` or `initiated`

### Output
- canonical `Project` object

### State Transition
`project_candidate` → `initiated` → `active`

---

## Required Runtime Contract: Research Attachment

### Input
- research name
- research type
- research URL
- uploaded file
- research category
- project id/name

### Process
1. create `research_id`
2. capture source URL/file
3. classify category
4. link to project
5. store as draft research record
6. validate source exists or URL present

### Output
- `Research` normalized view
- canonical `knowledge_record` if processed

### State Transition
`arrived` → `classified` → `draft`

---

## Required Runtime Contract: Reference Attachment

### Input
- reference type
- reference name
- reference URL
- uploaded file
- reference category
- project id/name

### Process
1. create `reference_id`
2. classify source
3. attach to project
4. assign category/tags
5. prepare for visual/text extraction if source exists
6. set review state

### Output
- `Reference` normalized view
- optional `knowledge_record`

---

## Required Runtime Contract: Learning Attachment

### Input
- learning name
- learning type
- learning URL
- category
- project link if relevant

### Process
1. create `learning_id`
2. capture source identity
3. classify learning type
4. link to project or global knowledge
5. prepare for Teacher agent use

### Output
- `Learning` record
- optional `knowledge_record`

---

## Required Runtime Contract: Schedule Slot Execution

### Input
- schedule id
- week/day/hour
- schedule category
- project step
- software
- training/theory/practice/template fields

### Process
1. identify active project context
2. map project step to workflow state
3. map software to tool registry
4. load attached templates/checklists
5. mark slot active
6. record output or skipped/blocked result

### Output
- `Execution Session`
- schedule state update
- project status update if completed

### State Transition
`planned` → `active` → `completed | skipped | blocked | moved`

---

## Required Runtime Contract: Checklist Binding

### Input
- checklist name
- checklist items
- status/stage association
- genre/medium folder association

### Process
1. select checklist based on project status and medium/genre
2. attach to project
3. track item completion
4. block promotion if required checklist items incomplete

### Output
- `ChecklistInstance`

---

## Required Runtime Contract: Template Binding

### Input
- template id
- template name
- template URL/location
- status association
- genre/medium association

### Process
1. select template based on project stage/status
2. attach to project
3. expose to tool/workflow step
4. log use

### Output
- `TemplateInstance` or project-level `template_ids`

---

## Pass/Fail Structures

### Pass Conditions
- required fields present
- controlled vocabulary values valid
- linked object exists
- project id valid
- status value normalized
- source URL/file captured when required
- schedule slot has mapped project step and tool

### Fail Conditions
- missing project id for project-bound object
- unknown status
- unknown project goal
- orphaned research/reference/learning record
- duplicate object id
- source file missing
- software name not registered
- schedule slot with no executable step

### Retry/Escalation Logic
- auto-normalize known spelling/trailing-space variants
- route unknown category/status to human review
- mark orphaned objects as `needs_linkage`
- mark source errors as `needs_source`
- mark ambiguous taxonomy as `needs_classification`

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

### Source-Authoritative
- source file name
- source URL
- original idea link
- upload file path
- original creation date

### User-Authoritative
- project name
- project goal
- project type/scope
- user level
- accepted status
- selected templates/checklists
- final creative decisions

### System-Authoritative
- generated ids
- normalized categories
- derived WIAS stages
- timestamps
- validation status
- relationship indexes

## Required Review States

For workbook-derived records:
- `draft`
- `checked`
- `approved`
- `locked`
- `deprecated`

For runtime execution:
- `planned`
- `active`
- `completed`
- `blocked`
- `skipped`
- `needs_review`

For source intake:
- `arrived`
- `classified`
- `preprocessed`
- `extracted`
- `normalized`
- `draft`
- `reviewed`
- `approved`
- `rejected`

## Promotion Logic

Workbook data should not enter canonical CIS knowledge automatically. It should move through:
1. import
2. normalization
3. validation
4. human/system review
5. approved canonical object creation

## Rejection Paths

Reject or return records when:
- object has no valid id
- relationship points to missing project
- category/status not recognized
- required source metadata missing
- uploaded path broken
- duplicate ids or duplicate canonical names exist
- field is too ambiguous to normalize safely

## Trust Enforcement

- Raw spreadsheet rows are not yet canonical objects.
- Canonical objects require validated schema.
- User-approved corrections override system interpretations.
- System-generated links are draft until reviewed.
- No workbook-derived taxonomy should become locked until duplicate/misspelled variants are resolved.

## Provenance Enforcement

Every imported object should store:
- source workbook filename
- source sheet name
- source row number
- imported_at
- importer version
- normalization version
- review status

## Validation Contracts

Minimum validation checks:
- `project_id` required for project rows
- `idea_name` or `idea_id` required for idea-linked project rows
- `status` must map to normalized allowed status
- `project_goal` must map to allowed project goal
- `research/reference/learning/template/checklist` links must point to real object ids or be marked unresolved
- `software` must map to registered tool
- schedule category must map to WIAS domain or approved non-WIAS category

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

The workbook shows the earliest version of a knowledge system:
- research records
- reference records
- learning records
- templates
- checklists
- software registry
- genre/medium taxonomies

These should be treated as structured but unnormalized knowledge seeds.

## Retrieval Structure

Retrieval should index:
- project name/id
- project goal
- status
- medium/category
- genre
- linked research/reference/learning
- software/tool
- template/checklist associations

## Indexing Implications

The workbook should become multiple indexes:
- project index
- idea index
- source index
- research index
- reference index
- learning index
- template index
- checklist index
- schedule index
- tool index
- taxonomy index

## Normalization Rules

Normalize:
- spelling variants
- casing variants
- trailing spaces
- plural/singular labels
- category names
- workflow statuses
- WIAS stage names
- tool names/vendor names

Do not normalize away:
- original user labels
- source sheet lineage
- source row lineage
- project-specific context
- working titles
- creative intent fields

## Ontology/Spine Implications

The workbook supplies a first ontology spine:

`Domain / Schedule Category`  
→ `Medium`  
→ `Artform`  
→ `Genre`  
→ `Project Goal`  
→ `Workflow Status`  
→ `Tool`  
→ `Template / Checklist`  
→ `Research / Reference / Learning`.

## Chunking Logic

When imported into retrieval:
- project records should chunk by field groups
- research/reference/learning records should chunk by object
- taxonomy sheets should chunk by category list
- schedule records should chunk by week/day/hour or by project step
- software registry should chunk by tool/capability group

## Reinforcement Behavior

User corrections should update:
- status normalization map
- taxonomy synonym map
- tool alias map
- project-goal-to-WIAS mapping
- checklist/template recommendations
- genre/category merge rules

## Project Linkage

All knowledge objects should support:
- global mode
- project-linked mode
- project-generated mode

This preserves the workbook’s design where project fields hold linked research/reference/learning/template/checklist values.

## Stabilization Loops

Repeated use should stabilize:
- common project pathways
- common statuses for each medium
- preferred tools per workflow stage
- frequent templates/checklists
- useful learning records
- high-value references/research

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

The workbook implies a minimum CIS Workbench with:

### Project Panel
- list projects
- create/edit project
- show project status
- attach idea
- attach research/reference/learning/templates/checklists

### Idea Intake Panel
- capture idea name/link/date/description/context
- classify category/medium/story type
- promote to project

### Research/Reference/Learning Panel
- add source URL/upload
- classify type/category
- link to project
- show processing state

### Workflow Status Panel
- show normalized status
- display checklist for current state
- display templates for current state
- allow status transition

### Schedule Panel
- show 7-day or 72-slot production schedule
- connect time slots to WIAS categories and tools
- log completed output

### Taxonomy Panel
- view/edit controlled vocabularies
- merge duplicate labels
- approve canonical terms

### Tool Registry Panel
- view tools by stage/category
- launch/open tool context
- show related templates/checklists

### Review Panel
- detect missing fields
- approve/reject normalized objects
- correct category/status/tool mapping

## Interface Panels Derived Directly From Workbook Sheets

| Workbook Sheet | Application Surface |
|---|---|
| `Projects Form` | Project intake/edit panel |
| `projects` | Project database/table |
| `ideas definition` | Idea capture/intake panel |
| `research` | Research/source panel |
| `reference` | Reference/source panel |
| `learning` | Learning/source panel |
| `templates` | Template library panel |
| `checklists` | Checklist library/promotion panel |
| `status` | Workflow status/state panel |
| `7 day schedule` | Weekly execution scheduler |
| `72 production schedule` | Extended production scheduler |
| `software` | Tool registry/launcher |
| genre sheets | Ontology/taxonomy manager |

## Operator Actions

Required operator actions:
- create idea
- promote idea to project
- attach source material
- classify category/medium/genre
- select project goal
- select status
- attach checklist/template
- start schedule slot
- mark output complete
- approve/reject normalized object
- merge duplicate taxonomy values

## Runtime Visibility Needs

The application must show:
- current project status
- missing required fields
- linked/unlinked knowledge objects
- active WIAS stage
- current schedule slot
- current checklist completion
- current tool/template recommendation
- failed validation messages
- unresolved source links

## Project-Centered Interaction

The project is the central application object:
- all work links to project
- all sources can be attached to project
- schedule slots should be project-aware
- knowledge reuse should be project-aware
- tool launch should be project-stage aware

## Application/Runtime Bridges

The Workbench should not only display workbook data. It should trigger:
- normalization
- validation
- source ingestion
- project creation
- status transition
- checklist instantiation
- template binding
- schedule execution logging

---

# 8. FEEDBACK LOOP DISCOVERIES

## Reinforcement Loop: Spreadsheet Use → Schema Refinement

Manual workbook usage reveals which fields matter. The system should preserve this as a feedback source:
manual field creation → repeated use → canonical object field.

## Correction Loop: User Fixes → Normalization Maps

Spelling variants, category drift, and duplicate statuses should become correction rules:
user correction → synonym map → future auto-normalization.

## Governance Loop: Validation Failure → Schema Update

If many records fail validation due to a missing field, the schema may need to be updated rather than forcing data into the old shape.

## Retrieval-Improvement Loop: Project Use → Knowledge Priority

Knowledge records attached to active projects should receive higher retrieval priority than unused records.

## Archive-Learning Loop: Source Attachment → Object Creation

Research/reference/learning rows prove that source capture must become a structured intake process:
source enters → classified → linked → processed → reusable.

## Continuity/Memory Loop: Project Status → Next Action

Status fields allow the system to remember where work stopped and recommend the next step.

## Project-Output Feedback Loop

Completed status, output stages, templates, and checklists should feed back into future project scaffolding:
project completion → reusable template/checklist/process pattern.

## Schedule Feedback Loop

Schedule execution should capture:
- planned vs completed
- skipped/blocked slots
- effective tools
- time estimates
- recurring bottlenecks

This becomes planning intelligence.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridge: Workbook Row → Canonical Object Importer

No mechanism yet converts spreadsheet rows into canonical CIS objects while preserving source lineage.

Required:
- workbook importer
- sheet-to-object mapper
- row lineage tracker
- normalization engine
- validation report

## Missing Object: Schedule Slot

The schedule sheets imply a formal object that does not yet exist.

Required fields:
- `schedule_slot_id`
- `week_count`
- `day_count`
- `day_name`
- `duration`
- `schedule_category`
- `project_step`
- `software`
- `start_date`
- `start_time`
- `end_date`
- `end_time`
- `status`
- `project_id`
- `output_ids`

## Missing Object: Tool Registry Entry

The `software` sheet needs conversion into a canonical object:
- `tool_id`
- `developer`
- `tool_name`
- `tool_url`
- `category`
- `supported_statuses`
- `supported_wias_stages`
- `templates`
- `checklists`
- `launch_command`
- `fallback_tools`

## Missing Object: Checklist Instance

The workbook has checklist templates, but projects need checklist instances.

## Missing Object: Template Instance

The workbook has templates, but project/runtime needs applied template instances.

## Missing Object: Taxonomy Term

All category/genre/medium sheets should become governed taxonomy objects with:
- canonical label
- aliases
- parent category
- related terms
- source sheet
- review state

## Missing Schema: Allowed Project Status Transitions

Status exists as a list but not a state machine.

## Missing Schema: Project Goal → WIAS Stage Mapping

Project goals imply WIAS stages, but the mapping is not formalized.

## Missing Governance: Duplicate and Typo Handling

There are visible spelling/casing/trailing-space inconsistencies. Governance needs:
- canonical term enforcement
- alias/synonym table
- pending term review

## Missing Validation Layer: Relationship Integrity

Project records reference research/reference/learning/template/checklist values, but there is no enforcement of valid linked IDs.

## Missing Application Surface: Taxonomy Merge/Correction

The operator needs a way to merge terms, correct spellings, and approve canonical labels.

## Missing Storage Rule: Workbook-to-CIS Migration Destination

The document does not define where imported workbook-derived objects should live in CIS storage.

Recommended:
`/mnt/projects/cis/application_seed/wias_project_manager_import/`
or
`/mnt/projects/cis/knowledge/records/spreadsheet__wias_project_manager__001/`

## Missing Routing: Imported Source vs Knowledge Source

Spreadsheet rows are structured source data, but it is unresolved whether they become:
- canonical knowledge records
- application seed objects
- migration fixtures
- lookup tables
- all of the above

## Missing Review/Promotion Path for Imported Workbook Data

Imported workbook objects should not automatically become locked. They should enter `draft_imported` or `needs_normalization`.

---

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

1. Define workbook import target schema.
2. Normalize field names and labels.
3. Create object mapping table.
4. Create taxonomy normalization map.
5. Define project/status state machine.
6. Define relationship validation rules.
7. Define schedule-slot object.
8. Define tool registry object.
9. Define checklist/template instancing.
10. Define import review workflow.

## Blocked Layers

### Application Layer
Blocked until workbook entities are normalized into object schemas.

### Workflow Execution Layer
Blocked until statuses become state transitions and schedule slots become runtime objects.

### Knowledge Layer
Blocked until research/reference/learning/templates/checklists are normalized into canonical `knowledge_record` or associated object views.

### Agent Layer
Blocked until project-linked knowledge records and controlled taxonomy exist.

### Tool Launcher
Blocked until software registry is normalized into tool-capability mapping.

## Sequencing Implications

Recommended order:

1. **Workbook Extraction / Migration Spec**
   - define sheet-to-object mappings
   - preserve lineage

2. **Canonical Object Schema v1**
   - Project
   - Idea
   - Research
   - Reference
   - Learning
   - Template
   - Checklist
   - Status
   - Schedule Slot
   - Tool Registry Entry
   - Taxonomy Term

3. **Normalization Dictionary**
   - statuses
   - WIAS categories
   - project goals
   - media/genres
   - tool names

4. **Validation Engine**
   - required fields
   - allowed values
   - relationship integrity
   - duplicate checks

5. **Import Review Workbench**
   - approve/correct imported rows
   - merge labels
   - resolve broken links

6. **Project-Centered Workbench v1**
   - project table
   - idea intake
   - source attachment
   - status/checklist/template panel

7. **Schedule Runtime**
   - active slot
   - task context
   - completion logging

8. **Knowledge/Agent Integration**
   - Teacher/Librarian use only approved project-linked records.

## Runtime-First Requirements

The minimum runtime must support:
- object creation
- object validation
- object state update
- relationship linking
- lineage logging
- import review status

## Governance-First Requirements

The workbook should be treated as historical source data. Every imported value needs:
- source sheet
- source row
- normalized field
- original value
- canonical value
- review state

## Execution-First Requirements

Before app UI:
- implement `import_workbook`
- implement `normalize_terms`
- implement `validate_objects`
- implement `create_project`
- implement `attach_knowledge`
- implement `advance_status`
- implement `instantiate_checklist`
- implement `instantiate_template`

## Application Dependencies

The first application surface depends on:
- Project object schema
- Idea intake schema
- Status/state schema
- Knowledge/support object schema
- Tool registry schema
- Taxonomy lookup schema
- Validation messages

---

# 11. EXTRACTED CANONICAL OBJECTS

## Object: Idea

- **Purpose**  
  Capture raw or early creative concepts before project formation.
- **Lifecycle**  
  `captured` → `classified` → `project_candidate` → `promoted_to_project` | `archived`
- **Authority Source**  
  User-authoritative for concept/description/context. Source-authoritative for original link/date.
- **Related Objects**
  - Project
  - Taxonomy Term
  - Story Type
- **States**
  - draft
  - classified
  - promoted
  - archived
- **Storage Implications**
  Store as canonical JSON with source workbook lineage if imported.

Observed fields:
- idea name
- idea link
- idea original date
- idea description
- idea context
- category
- category medium
- story type

---

## Object: Project

- **Purpose**  
  Persistent container for all work, knowledge, assets, workflow state, and outputs.
- **Lifecycle**  
  `initiated` → `active` → `paused` → `completed` → `archived`
- **Authority Source**  
  User-authoritative for name, goal, type, and final direction. System-authoritative for id and timestamps.
- **Related Objects**
  - Idea
  - Research
  - Reference
  - Learning
  - Template
  - Checklist
  - Schedule Slot
  - Tool
  - Status
- **States**
  - initiated
  - active
  - blocked
  - paused
  - complete
  - archived
- **Storage Implications**
  Project should act as the root object for relationship indexes and application display.

Observed fields:
- project id
- project name
- creation date
- idea name
- user level
- project type
- project goal
- research
- reference
- status
- checklists
- templates
- learning

---

## Object: Project Intake Form

- **Purpose**  
  Operator-facing form for turning idea/context into a project.
- **Lifecycle**  
  `blank` → `partially_filled` → `validated` → `project_created`
- **Authority Source**  
  User input.
- **Related Objects**
  - Idea
  - Project
  - User
  - Research
  - Reference
  - Checklist
  - Template
  - Learning
- **States**
  - draft
  - ready
  - submitted
  - rejected
- **Storage Implications**
  Should become an application form, not canonical storage itself.

Observed form fields:
- project id
- owner
- user level
- start date
- due date
- idea name
- idea creation date
- project name
- project type
- project goal
- research
- reference
- status
- checklists
- templates
- learning

---

## Object: Research

- **Purpose**  
  Store informational source material linked to project development.
- **Lifecycle**  
  `arrived` → `classified` → `processed` → `draft` → `approved`
- **Authority Source**  
  Source-authoritative for URL/upload. User/system-authoritative for category.
- **Related Objects**
  - Project
  - Knowledge Record
  - Source Manifest
- **States**
  - draft
  - checked
  - approved
  - rejected
- **Storage Implications**
  Normalize into `knowledge_record` view with `knowledge_category = research`.

Observed fields:
- research ID
- research name
- research type
- research url
- research upload
- research category
- project name

---

## Object: Reference

- **Purpose**  
  Store aesthetic, visual, conceptual, or production references.
- **Lifecycle**  
  `arrived` → `classified` → `processed` → `draft` → `approved`
- **Authority Source**  
  Source-authoritative for file/URL. User-authoritative for creative relevance.
- **Related Objects**
  - Project
  - Knowledge Record
  - Taxonomy Term
- **States**
  - draft
  - checked
  - approved
  - rejected
- **Storage Implications**
  Normalize into `knowledge_record` view with `knowledge_category = reference`.

Observed fields:
- reference ID
- reference type
- reference name
- reference url
- reference upload
- reference category
- project name

---

## Object: Learning

- **Purpose**  
  Store tutorials, courses, and instructional references usable by Teacher agent.
- **Lifecycle**  
  `captured` → `classified` → `processed` → `approved` → `reused`
- **Authority Source**  
  Source-authoritative for URL/source. User/system-authoritative for relevance and category.
- **Related Objects**
  - Project
  - Teacher Agent
  - Tool
  - Knowledge Record
- **States**
  - draft
  - checked
  - approved
  - deprecated
- **Storage Implications**
  Normalize into `knowledge_record` view with `knowledge_category = learning`.

Observed fields:
- learning id
- learning name
- learning type
- learning url
- category

---

## Object: Checklist

- **Purpose**  
  Store repeatable process steps for workflow/status execution.
- **Lifecycle**  
  `template_defined` → `instantiated_for_project` → `in_progress` → `completed`
- **Authority Source**  
  User-authoritative for checklist content; system-authoritative for instantiation.
- **Related Objects**
  - Project
  - Status
  - Template
  - Medium/Genre
- **States**
  - template
  - active
  - completed
  - obsolete
- **Storage Implications**
  Separate `ChecklistTemplate` from `ChecklistInstance`.

Observed fields:
- checklist id
- checklist name
- checklists
- genre template folder
- medium genre checklists

---

## Object: Template

- **Purpose**  
  Provide reusable execution scaffolds tied to status, medium, genre, or tool.
- **Lifecycle**  
  `defined` → `attached` → `used` → `updated` → `deprecated`
- **Authority Source**  
  User-authoritative for template choice and meaning.
- **Related Objects**
  - Project
  - Status
  - Checklist
  - Tool
  - Knowledge Record
- **States**
  - draft
  - approved
  - active
  - deprecated
- **Storage Implications**
  Separate canonical template record from project-specific template instance.

Observed fields:
- template id
- template name
- template url
- status
- genre template folder
- medium genre checklists

---

## Object: Status

- **Purpose**  
  Define workflow state vocabulary and stage-level progress.
- **Lifecycle**  
  `defined` → `normalized` → `mapped_to_transition` → `used`
- **Authority Source**  
  User/system governance.
- **Related Objects**
  - Project
  - Checklist
  - Template
  - Schedule Slot
  - Tool
- **States**
  - active term
  - alias
  - deprecated term
- **Storage Implications**
  Store as controlled vocabulary plus transition graph.

---

## Object: Schedule Slot

- **Purpose**  
  Represent time-boxed planned or active production work.
- **Lifecycle**  
  `planned` → `active` → `completed | skipped | blocked | moved`
- **Authority Source**  
  User-authoritative for plan. System-authoritative for execution logs.
- **Related Objects**
  - Project
  - Status
  - Tool
  - Template
  - Checklist
- **States**
  - planned
  - active
  - completed
  - skipped
  - blocked
  - moved
- **Storage Implications**
  Requires a runtime table/object separate from calendar display.

Observed fields:
- schedule id
- week count
- day count
- day name
- duration
- schedule category
- project step
- software
- start/end date
- start/end time
- software training
- artform theory
- skill practice
- templates

---

## Object: Tool / Software Registry Entry

- **Purpose**  
  Store tool identity, vendor, URL, category, status/stage association, and execution support.
- **Lifecycle**  
  `registered` → `validated` → `active` → `deprecated`
- **Authority Source**  
  Source/user for tool identity. System for launch/configuration.
- **Related Objects**
  - Project
  - Schedule Slot
  - Template
  - Checklist
  - Workflow Status
- **States**
  - candidate
  - installed
  - validated
  - active
  - deprecated
- **Storage Implications**
  Needs mapping to installed local paths/launch commands later.

Observed fields:
- status
- category
- software developer
- software name
- software url
- status/steps
- templates
- checklists

---

## Object: Taxonomy Term

- **Purpose**  
  Store controlled vocabulary for project classification, genres, media, learning types, equipment types, product types, and categories.
- **Lifecycle**  
  `discovered` → `normalized` → `approved` → `merged | deprecated`
- **Authority Source**  
  Governance/user review.
- **Related Objects**
  - Project
  - Idea
  - Knowledge Record
  - Tool
  - Schedule Slot
- **States**
  - draft
  - approved
  - alias
  - deprecated
- **Storage Implications**
  Requires canonical label plus aliases and source sheet lineage.

---

## Object: Project Goal

- **Purpose**  
  Define intended output type and production target.
- **Lifecycle**  
  `selected` → `mapped_to_stage` → `executed` → `completed`
- **Authority Source**  
  User-authoritative.
- **Related Objects**
  - Project
  - Status
  - WIAS Stage
  - Template
  - Checklist
- **States**
  - active
  - alias
  - deprecated
- **Storage Implications**
  Should become controlled vocabulary with WIAS mapping.

Observed values include:
- script
- book
- drawing
- painting
- storyboard
- animatic
- previz
- 2d animation
- 3d animation
- 3d environment
- 3d sculpture
- 3d model
- 3d texture
- 3d game
- vfx
- 3d motion graphics
- 3d rendering
- full length film
- short film
- film editing
- film colorgrade
- augmented reality
- virtual reality
- music production
- sound design
- post online
- stream
- learndash course
- product

---

## Object: User Level

- **Purpose**  
  Calibrate project guidance, learning recommendations, and execution complexity.
- **Lifecycle**  
  `defined` → `assigned` → `used_for_guidance`
- **Authority Source**  
  User-authoritative.
- **Related Objects**
  - Project
  - Learning
  - Teacher Agent
  - Workflow Guidance
- **States**
  - beginner
  - intermediate
  - advanced
- **Storage Implications**
  Store globally and allow project-level override.

---

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did NOT exist before?

The workbook proves that CIS did not begin as abstract architecture. It began as an analogue operating system for creative production.

The most important new understanding is:

**The WIAS Project Manager workbook is an early CIS application and data model disguised as a spreadsheet.**

It already contains the seeds of:
- project objects
- idea intake
- project promotion
- workflow statuses
- WIAS scheduling
- tool-to-stage mapping
- research/reference/learning linkage
- template/checklist support
- taxonomy and genre classification
- user-level calibration
- schedule-based execution
- application form surfaces

The workbook changes the CIS build plan in a concrete way:

1. **Application schema should be derived from the workbook.**  
   The workbook contains the operator’s original project logic and should drive object modeling.

2. **The Project Object is confirmed as the central persistent container.**  
   Research, reference, learning, templates, checklists, status, and schedule all attach to the project.

3. **WIAS is operational, not only conceptual.**  
   It appears as schedule categories, production stages, tool mappings, and workflow steps.

4. **Status vocabulary must become a formal state machine.**  
   The workbook provides the vocabulary but not the enforcement.

5. **The Application Layer can start as a normalized Workbench for workbook-derived objects.**  
   This is not premature UI. It is the interface required to migrate analogue CIS into executable CIS.

6. **The Execution Layer must bridge schedule, status, tools, and project objects.**  
   Schedule sheets show how work is meant to move through time, but runtime state and validation must be added.

7. **Knowledge records should normalize from existing Research, Reference, Learning, Template, and Checklist sheets.**  
   These are not random fields; they are early typed knowledge/support objects.

8. **The ontology spine already exists in fragmented form.**  
   Genre, medium, project goal, learning type, and category sheets provide the first controlled vocabularies.

9. **A migration/import governance layer is required.**  
   The workbook is valuable but inconsistent. It must be imported through validation, normalization, lineage tracking, and review.

10. **The first build target should be a workbook-to-CIS object migration spec.**  
    Before complex agents or polished UI, CIS needs to translate this analogue system into canonical runtime objects.

## Topology-Ready Summary

### Primary Nodes
- Idea
- Project
- Project Intake Form
- Research
- Reference
- Learning
- Template
- Checklist
- Status
- Schedule Slot
- Tool Registry Entry
- Taxonomy Term
- Project Goal
- User Level

### Primary Edges
- Idea → Project
- Project → Research
- Project → Reference
- Project → Learning
- Project → Template
- Project → Checklist
- Project → Status
- Project → Schedule Slot
- Schedule Slot → Tool
- Status → Checklist
- Status → Template
- Project Goal → WIAS Stage
- Medium/Genre → Project Classification
- Learning → Teacher Agent
- Reference/Research → Librarian Agent
- Tool → Workflow Stage

### Primary State Machines
- Idea lifecycle
- Project lifecycle
- Source/knowledge lifecycle
- Schedule slot lifecycle
- Status workflow transition
- Taxonomy normalization lifecycle
- Template/checklist instantiation lifecycle

### Primary Governance Gates
- Import validation
- Field normalization
- Controlled vocabulary validation
- Relationship integrity validation
- Project linkage validation
- Human review/promotion
- Canonical object approval

### Primary Build Sequence
1. Extract workbook schema.
2. Map sheets to canonical objects.
3. Normalize field names and terms.
4. Build validation rules.
5. Import workbook rows as draft objects.
6. Review and approve canonical terms.
7. Implement project-centered Workbench.
8. Add schedule/runtime execution.
9. Connect knowledge retrieval.
10. Add Teacher/Librarian support.

---

# APPENDIX A — SHEET-TO-OBJECT MAP

| Sheet | Extracted Role | Canonical Object / Surface |
|---|---|---|
| `ideas definition` | idea capture | Idea |
| `Projects Form` | project intake UI | Project Intake Form |
| `projects` | project database | Project |
| `research` | research records | Research / knowledge_record |
| `reference` | reference records | Reference / knowledge_record |
| `learning` | learning records | Learning / knowledge_record |
| `templates` | reusable structures | Template |
| `checklists` | process checklists | Checklist |
| `status` | workflow states | Status / State Machine |
| `7 day schedule` | weekly execution slots | Schedule Slot |
| `72 production schedule` | extended production slots | Schedule Slot / Production Plan |
| `schedule and definitions` | lookup/control map | Taxonomy + Workflow Definitions |
| `software` | tool registry | Tool Registry Entry |
| `project goal` | output vocabulary | Project Goal |
| `project Scope` | scope vocabulary | Project Scope |
| `project catagory` | project category vocabulary | Taxonomy Term |
| genre sheets | genre vocabulary | Taxonomy Term |
| `learning type` | learning taxonomy | Taxonomy Term |
| `equipment type` | equipment taxonomy | Taxonomy Term |

---

# APPENDIX B — IMPLEMENTATION-GRADE NODE LIST

```yaml
nodes:
  - id: idea
    type: canonical_object
    layer: intake
  - id: project
    type: canonical_object
    layer: project_container
  - id: project_intake_form
    type: application_surface
    layer: application
  - id: research
    type: knowledge_view
    layer: knowledge
  - id: reference
    type: knowledge_view
    layer: knowledge
  - id: learning
    type: knowledge_view
    layer: knowledge
  - id: template
    type: support_object
    layer: workflow
  - id: checklist
    type: support_object
    layer: workflow
  - id: status
    type: workflow_state
    layer: workflow_execution
  - id: schedule_slot
    type: runtime_object
    layer: workflow_execution
  - id: tool_registry_entry
    type: capability_object
    layer: tool
  - id: taxonomy_term
    type: ontology_object
    layer: knowledge_spine
  - id: project_goal
    type: classification_object
    layer: project
  - id: user_level
    type: calibration_object
    layer: intelligence_guidance
```

---

# APPENDIX C — IMPLEMENTATION-GRADE EDGE LIST

```yaml
edges:
  - from: idea
    to: project
    relationship: promoted_into
  - from: project
    to: research
    relationship: links_to
  - from: project
    to: reference
    relationship: links_to
  - from: project
    to: learning
    relationship: links_to
  - from: project
    to: template
    relationship: uses
  - from: project
    to: checklist
    relationship: uses
  - from: project
    to: status
    relationship: has_current_state
  - from: project
    to: schedule_slot
    relationship: executed_through
  - from: schedule_slot
    to: tool_registry_entry
    relationship: invokes
  - from: status
    to: checklist
    relationship: requires
  - from: status
    to: template
    relationship: suggests
  - from: project_goal
    to: status
    relationship: determines_possible_workflow
  - from: project_goal
    to: taxonomy_term
    relationship: classified_by
  - from: learning
    to: tool_registry_entry
    relationship: teaches
  - from: reference
    to: taxonomy_term
    relationship: tagged_by
  - from: research
    to: taxonomy_term
    relationship: categorized_by
```

---

# APPENDIX D — TOPOLOGY PANEL RECOMMENDATION

Based on the reference image, this workbook should become its own topology panel titled:

## WIAS Workbook → CIS Application Seed Topology

Recommended panel sections:
1. **Idea Intake**
2. **Project Creation**
3. **Project Object**
4. **Knowledge Attachments**
5. **Workflow Status Engine**
6. **Schedule Execution Engine**
7. **Tool Registry**
8. **Taxonomy / Knowledge Spine**
9. **Template + Checklist Support**
10. **Import Governance + Validation**
11. **Application Workbench Surface**
12. **Feedback / Reinforcement Loop**

