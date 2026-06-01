# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Phase 0 Execution Layer became operator-facing instead of purely headless

- **Architectural Significance**
  - The session begins with “Phase 0 — Execution Layer (PROVEN)” and a build queue that turns runtime proof into usable dashboard operations.
  - The Execution Layer is no longer only commands/scripts; it now requires application-facing controls for ADR logging, pipeline status, extraction logging, and CIS Live coordination.
  - This invalidates the prior assumption that the operator could remain comfortable with command-only workflow during Phase 0/Phase 1.

- **Affected Layers**
  - Execution Layer
  - Application Layer
  - Governance Layer
  - Intelligence Layer
  - Knowledge Layer

- **Dependency Impact**
  - Dashboard routes become required runtime bridges, not optional convenience UI.
  - `cis_dashboard.py` and `cis_dashboard.html` become operational surfaces for governance, pipeline control, and live coordination.
  - Database tables become required for persistent operator-visible state.

- **Build Impact**
  - Application surface work must begin earlier than the original “late Phase 5” framing, but only as an operator console tied to live execution needs.
  - Dashboard work must remain scoped to execution support, not full product UI.

- **Runtime Impact**
  - Operator actions such as logging ADRs, triggering pipeline stages, recording extraction runs, and coordinating model feedback must be routed through visible buttons, forms, and status messages.
  - Missing feedback states are now runtime defects, not UI polish issues.

---

## Discovery Name: DAM emerged as the unaffiliated knowledge layer

- **Architectural Significance**
  - CIS now has two knowledge affiliation modes:
    - **Affiliated**: `project_id` set; record exists as a project asset.
    - **Unaffiliated**: `project_id` null; record exists in the DAM.
  - The DAM is not a separate system; it is a filtered application view of the same knowledge base.
  - This invalidates the assumption that all ingested material must immediately belong to a project.

- **Affected Layers**
  - Knowledge Layer
  - Application Layer
  - Project Object Layer
  - Review/Promotion Layer

- **Dependency Impact**
  - Knowledge records must support nullable `project_id`.
  - Application navigation eventually requires a distinct DAM section separate from project-scoped Knowledge.
  - Review logic must support linking, promotion, and demotion.

- **Build Impact**
  - Build sequence must add DAM as a Phase 5 surface, but not as a standalone stream yet.
  - The Architecture Map and Application Stream require explicit DAM references to prevent future drift.

- **Runtime Impact**
  - Ingested items can start as unaffiliated assets.
  - Assets may be linked to a project, promoted into a standalone project, or demoted back to unaffiliated/DAM status.

---

## Discovery Name: Every ingested item is an asset by default, with project potential

- **Architectural Significance**
  - Ingestion does not automatically create a project.
  - Ingested material becomes a source, then a reviewed knowledge record, then an asset.
  - The review surface becomes the decision point where an item remains an asset, links to a project, or becomes a project seed.

- **Affected Layers**
  - Intake Layer
  - Pipeline Layer
  - Knowledge Layer
  - Project Layer
  - Application Layer

- **Dependency Impact**
  - Review screen must include `Promote to Project` capability in addition to metadata review.
  - Project creation can be seeded from a `knowledge_record`.

- **Build Impact**
  - Project creation logic must support source-derived project initialization.
  - Source list/pipeline page must distinguish raw source state from knowledge/project state.

- **Runtime Impact**
  - Source lifecycle becomes:
    - archive/raw file → intake → source container + manifest → extraction/normalization → knowledge record → reviewed asset → optional project seed.

---

## Discovery Name: Review surface became the human validation workbench

- **Architectural Significance**
  - The user reframed visual review as essential for visual designers: after image intake and AI description, the operator must visually inspect the image and correct metadata.
  - The review page is no longer an abstract governance concept; it is a concrete operator surface with image-left / editable-fields-right layout.

- **Affected Layers**
  - Governance Layer
  - Knowledge Layer
  - Application Layer
  - Intelligence Layer

- **Dependency Impact**
  - AI-produced descriptions remain draft until human correction.
  - Editable fields include title, summary, scene_description, mood_style, tags, knowledge_category, subject, status, uncertainty.
  - The Review surface must write back to canonical JSON or the appropriate record store.

- **Build Impact**
  - Review/promotion UI becomes required before knowledge can be trusted at scale.
  - Image display and metadata correction must be built before a full DAM.

- **Runtime Impact**
  - Human correction becomes an explicit pipeline action.
  - The review page becomes the interface for `draft → checked → approved` movement and for project/DAM affiliation decisions.

---

## Discovery Name: Pipeline source list must become paginated and project-aware

- **Architectural Significance**
  - Pipeline was discovered to be a single-source operator tool requiring typed `source_id`.
  - This breaks archive-scale usability.
  - Pipeline must evolve into a queue/list interface with pagination, status visibility, and review routing.

- **Affected Layers**
  - Pipeline Layer
  - Application Layer
  - Source Manifest Layer

- **Dependency Impact**
  - `/mnt/projects/cis/ingest/processing/` becomes the source list backing store until a DB-backed source registry exists.
  - Source list must filter by active project by default, with unaffiliated/DAM visibility as a parallel path.

- **Build Impact**
  - Build must add source list, pagination, and pipeline/review buttons.
  - Intake success must auto-populate the source ID and refresh the pipeline list.

- **Runtime Impact**
  - Operator must not need to remember or type source IDs manually once intake has occurred.
  - Pipeline page becomes a queue, not a single command panel.

---

## Discovery Name: Extraction run logging became its own runtime object

- **Architectural Significance**
  - Extraction runs require durable tracking independent of the knowledge record.
  - A new `extraction_runs` table was created to capture source_id, record_id, model_used, extraction_type, status, duration_seconds, error, project_id, created_at, completed_at.

- **Affected Layers**
  - Execution Layer
  - Intelligence Layer
  - Application Layer
  - Audit/Observability Layer

- **Dependency Impact**
  - Pipeline extract step must log to `extraction_runs`.
  - Dashboard must surface extraction history below the pipeline track.
  - Model failure, runtime duration, and error messages become auditable.

- **Build Impact**
  - New API routes are required:
    - `GET /api/extraction_runs`
    - `POST /api/extraction_runs`
  - Frontend state must include run history and not break when no runs exist.

- **Runtime Impact**
  - Extract is no longer a black-box step.
  - Failed model loads, dependency errors, OOM failures, and successful inference attempts can be tracked over time.

---

## Discovery Name: 32B model execution is constrained by runtime environment, not just model availability

- **Architectural Significance**
  - Qwen2.5-VL-32B loading is possible but inference can fail due to VRAM headroom.
  - GUI overhead, model loading mode, processor pixel count, token budget, Python environment, and dependency resolution all become runtime constraints.

- **Affected Layers**
  - Intelligence Layer
  - Execution Layer
  - Infrastructure Layer
  - Router/Model Registry Layer

- **Dependency Impact**
  - `cis_extract.py` must use the correct Python environment explicitly: `/home/eric/gpu-test/bin/python3`.
  - `qwen_vl_utils` must exist in the active environment.
  - `BitsAndBytesConfig(load_in_4bit=True)` must replace direct `load_in_4bit=True` usage.
  - `max_pixels` and `max_new_tokens` must be tunable runtime controls.

- **Build Impact**
  - Model execution settings need to become configurable and logged, not hardcoded.
  - Router must account for hardware constraints and GUI VRAM usage.

- **Runtime Impact**
  - “Model installed” is insufficient; “model can infer under current UI/GPU conditions” becomes the actual validation standard.

---

## Discovery Name: CIS_LIVE became a cross-model coordination object

- **Architectural Significance**
  - CIS_LIVE is a new operational object for near-real-time collaboration across Claude, ChatGPT, and Gemini.
  - The system must reduce the user’s role as manual copy/paste middleware.
  - It evolved from freeform scratchpad to structured multi-round session object.

- **Affected Layers**
  - Application Layer
  - Knowledge Layer
  - Governance/Memory Layer
  - Human Middleware Reduction Layer

- **Dependency Impact**
  - Requires `live_sessions` and `live_rounds` tables.
  - Requires GitHub raw URL sync or future LXC read-only public endpoint.
  - Requires push serialization from DB → `CIS_LIVE.md` → public read surface.

- **Build Impact**
  - Live panel requires session list, active session, thread, round form, consolidated response field, optional attribution, push, copy URL, resolve, and promote-to-knowledge behavior.

- **Runtime Impact**
  - Operator uses GitHub/raw URL as “meeting point.”
  - Models read the same shared file; the human consolidates responses and pushes updates.
  - On resolution, the session can become a `capture` record with `capture_type=solution`.

---

## Discovery Name: Consolidated response workflow supersedes rigid per-model fields

- **Architectural Significance**
  - Per-model fields were initially valued for attribution, but they slowed the actual collaborative rhythm.
  - The revised workflow uses a fast consolidated response field, with optional attribution collapsed by default.

- **Affected Layers**
  - Application Layer
  - Knowledge Capture Layer
  - Human Workflow Layer

- **Dependency Impact**
  - `live_rounds` must include `consolidated` plus optional `gemini`, `claude`, and `chatgpt` fields.
  - GitHub export should prioritize readable consolidated thread output.
  - DB retains individual attribution only when operator chooses to provide it.

- **Build Impact**
  - UI must be optimized around rhythm:
    - Your Message
    - Consolidated Responses
    - Optional attribution
    - Add Round
    - Push

- **Runtime Impact**
  - Normal round: write message → paste consolidated responses → Add Round → Push.
  - High-value round: optionally expand attribution to preserve who said what.

---

## Discovery Name: Public CIS_LIVE serving needs an isolated LXC boundary

- **Architectural Significance**
  - GitHub raw URL introduces possible latency and push-state confusion.
  - Direct serving from the machine is desirable but unsafe if exposing the main dashboard.
  - A read-only LXC container becomes the secure boundary for external model reads.

- **Affected Layers**
  - Infrastructure Layer
  - Application Layer
  - Security Boundary Layer
  - Cross-Model Coordination Layer

- **Dependency Impact**
  - Requires Proxmox LXC, read-only bind mount of `CIS_LIVE.md`, minimal Flask or nginx, and router port forwarding.
  - Container must not access DB, dashboard, archive, or runtime scripts.

- **Build Impact**
  - Future build can create a minimal public endpoint:
    - Internet → Router Port 80/443 → LXC → read-only `/data/CIS_LIVE.md`.

- **Runtime Impact**
  - Models read live file directly without GitHub CDN delay.
  - Human remains write/post bridge.
  - Security blast radius is isolated to disposable LXC.

---

# 2. TOPOLOGY MUTATIONS

## New Layers

### DAM / Unaffiliated Knowledge Surface

- Introduced as an application-layer surface over the knowledge base.
- Not a separate storage system.
- Defined by `project_id = null`.
- Acts as the holding layer for useful material not yet attached to a project.

### CIS_LIVE Coordination Layer

- A new fast coordination layer between human operator and external models.
- Stores sessions and rounds in DB.
- Serializes to public/shared markdown.
- Later may be served from isolated LXC.

### Extraction Observability Layer

- `extraction_runs` table creates a runtime history of extract attempts.
- Surfaces model performance, duration, and failures.

### Review/Validation Workbench Surface

- Human-facing review page becomes required for trust promotion.
- Image preview and editable metadata fields define a concrete review pattern.

---

## Split Layers

### Knowledge split into Affiliated vs Unaffiliated Modes

- Affiliated: linked to project.
- Unaffiliated: DAM/floating.
- Same schema, same pipeline, different application surface.

### Pipeline split into Intake Queue vs Knowledge Review

- Pipeline is for sources and processing states.
- Review/Knowledge is for records after extraction/normalization.
- Previous blending of source and knowledge object caused confusion.

### Live Coordination split into Communication vs Knowledge Capture

- Push to GitHub / public URL = communication function.
- Mark Resolved / Promote = knowledge capture function.
- These actions must remain separate.

---

## Runtime Bridges

- `/api/intake` bridges dashboard intake form to `cis_intake.py`.
- `/api/pipeline/<action>` bridges dashboard buttons to classify/preprocess/extract/normalize scripts.
- `/api/decisions` bridges dashboard ADR form to `decisions` table.
- `/api/extraction_runs` bridges extraction execution to audit history.
- `/api/live/*` bridges Live UI to DB, markdown serialization, GitHub push.
- Future LXC bridge exposes read-only `CIS_LIVE.md` to external models.

---

## Orchestration Changes

- Initial extraction was deferred because prerequisite governance addendum ADRs had to be logged first.
- Build queue became explicit:
  1. Log ADR-013–ADR-018.
  2. Build decision logging form.
  3. Build extraction run logging table.
  4. Build review/promotion UI.
  5. Begin intelligence extraction.
- Pipeline actions remain manual button-driven, but now need observability and feedback.

---

## Governance Expansion

- ADR-019 locks DAM as unaffiliated knowledge layer.
- ADR-020 locks review page as human validation surface.
- ADR logging form removes manual SQL as governance bottleneck.
- “Nothing to commit” must not appear as “git not configured”; UI messages now constitute governance clarity.

---

## Object-Model Mutations

- Source gains clearer distinction from Knowledge Record.
- Knowledge Record gains affiliation mode.
- Asset becomes default interpretation of ingested material after review.
- Project can be created from an asset/knowledge record.
- Live Session and Live Round emerge as new persistent objects.
- Extraction Run emerges as an audit object.
- DAM record is not a new schema object but a knowledge record with `project_id = null`.

---

## Workflow/Execution Separation

- Workflow says: intake → classify → preprocess → extract → normalize → review.
- Execution now requires:
  - explicit script paths,
  - correct Python environment,
  - runtime feedback,
  - DB logging,
  - source status checking,
  - UI state reset,
  - error display,
  - audit trail.

---

## Project-Container Evolution

- Project remains primary production container.
- Ingested source is not automatically a project.
- Ingested source may become:
  - project asset,
  - DAM asset,
  - standalone project seed.
- Demotion allows project assets to return to DAM without deletion.

---

# 3. DEPENDENCY DISCOVERIES

## Hidden Prerequisites

- ADR-013–ADR-018 had to be logged before build work continued.
- Decision logging form was required before further ADR capture to avoid repeated manual SQL.
- `qwen_vl_utils` dependency had to exist in the actual runtime Python environment, not merely somewhere on disk.
- `BitsAndBytesConfig` was required for compatible 4-bit model loading.
- Live push correctness depended on serialization from DB, vault copy, Git commit, and raw GitHub freshness.
- `live_rounds` needed schema migration to add `consolidated` before the revised UI could function.
- Source review cannot happen meaningfully until source image and editable fields are exposed together.

## Sequencing Constraints

- Intake must create source container and manifest before pipeline actions.
- Classification must precede preprocessing.
- Preprocessing must precede extraction.
- Extraction must precede normalization.
- Normalization must precede review.
- Review must precede approval/trusted retrieval.
- Add Round must precede Push if the new round is expected to appear in GitHub output.
- Push must occur after DB write, not before.

## Circular Dependencies

- Application surface depends on execution logic, but execution usability depends on minimal application surface.
- Knowledge base depends on human review, but human review requires an application view of image + metadata.
- Cross-model coordination reduces human middleware, but still requires the human as the write bridge.

## Unstable Dependencies

- GitHub raw URL may appear stale if push does not actually commit changed serialized content.
- Dashboard monolith is fragile; single JavaScript error can break the Pipeline page.
- Runtime Python environment detection is unstable when shebang/system Python conflicts with virtual environment.
- Model inference depends on VRAM headroom and GUI process load.

## Runtime Blockers

- No visible intake feedback after clicking Intake.
- Pipeline buttons initially gave poor feedback and source list was missing.
- `runs is not defined` broke Pipeline page.
- `table live_rounds has no column named consolidated` blocked Add Round.
- Misleading Git status messages obscured whether push succeeded.
- Qwen32B failed inference due to dependency/environment and later VRAM constraints.

## Orchestration Bottlenecks

- Human remains the cross-model POST mechanism.
- Operator still must paste model responses into CIS Live.
- GitHub sync adds possible coordination friction.
- No stable review/promotion UI yet.
- Source list and pagination not built yet.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## Commands

### Intake

```bash
python3 /mnt/projects/cis/runtime/cis_intake.py \
  /mnt/projects/cis/ingest/incoming/Weird_War_Tales_cover.jpg \
  --project PROJECT__CIS__BUILD__V1
```

Observed output:

- `INTAKE START`
- `FILE COPIED`
- `MANIFEST CREATED`
- `INTAKE COMPLETE`
- `Source ID: image__weird_war_tales_cover__002`
- status = `arrived`

### Classification

```bash
python3 /mnt/projects/cis/runtime/cis_classify.py image__weird_war_tales_cover__002
```

Observed results:

- type = image
- status = classified
- passes = `['vision']`
- model = `qwen2.5-vl-32b`

### Preprocess

```bash
python3 /mnt/projects/cis/runtime/cis_preprocess.py image__weird_war_tales_cover__002
```

Observed results:

- status = preprocessed
- files = 1
- extracted file = `/mnt/projects/cis/ingest/processing/image__weird_war_tales_cover__002/extracted/Weird_War_Tales_cover.jpg`

### Extract

Initial dashboard call failed silently/fast. Manual command required:

```bash
PYTORCH_ALLOC_CONF=expandable_segments:True \
/home/eric/gpu-test/bin/python3 \
/mnt/projects/cis/runtime/cis_extract.py \
image__weird_war_tales_cover__002
```

### Model Configuration Patch

Required replacement:

```python
from transformers import BitsAndBytesConfig
bnb_config = BitsAndBytesConfig(load_in_4bit=True)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto"
)
```

### Proposed VRAM Stability Patch

```python
image_inputs, video_inputs = process_vision_info(messages, max_pixels=512*28*28)
...
generated_ids = model.generate(
    **inputs,
    max_new_tokens=512,
    do_sample=False
)
```

---

## States

### Source/Pipeline States

- arrived
- classified
- preprocessed
- extracted
- normalized
- reviewed / draft handled downstream

### Knowledge Review States

- draft
- checked
- approved
- locked
- deprecated

### Knowledge Affiliation States

- affiliated (`project_id` set)
- unaffiliated / DAM (`project_id` null)

### Live Session States

- open
- resolved

### Extraction Run States

- pending
- success
- failed
- partial

### ADR States

- locked
- proposed
- superseded

---

## Transitions

### Source Pipeline

```text
arrived → classified → preprocessed → extracted → normalized → draft knowledge_record
```

### Knowledge Trust

```text
draft → checked → approved → locked
```

### DAM / Project Affiliation

```text
unaffiliated DAM record → linked to existing project → affiliated asset
unaffiliated DAM record → promoted to standalone project → project seed + affiliated asset
affiliated asset → demoted → unaffiliated DAM record
```

### Live Coordination

```text
create live_session → add live_round → push serialized file → models read → add next round → repeat → resolve → save solution capture
```

---

## Runtime Contracts

- Intake must return visible source ID and status.
- Pipeline must expose current source status before allowing next steps.
- Extract must log run metadata to `extraction_runs`.
- Add Round must write DB row before Push.
- Push must serialize DB state to `CIS_LIVE.md` before git commit/push.
- Resolve must write solution to `captures` table.
- Review must not promote automatically without human action.

---

## Orchestration Logic

- Pipeline panel currently runs manual operator-controlled stages.
- Live panel runs manual multi-model coordination rounds.
- Decision panel writes ADRs to DB and displays sorted decision list.
- Extraction run logging records extract results but does not yet orchestrate retries.
- Future LXC serves only read-only live file to external models.

---

## Validation Behavior

- Intake success must show assigned source_id.
- Pipeline page must not render undefined state variables.
- DB schema must match frontend payload fields.
- Git push messages must distinguish:
  - successful push,
  - nothing new to push,
  - git not configured,
  - actual git error.
- Model execution must validate dependencies, environment, quantization config, VRAM headroom.

---

## Pass/Fail Structures

### Pipeline Step PASS

- command succeeds
- stdout displayed
- status updated
- manifest reloaded
- run logged if extraction

### Pipeline Step FAIL

- stderr shown
- status not falsely advanced
- run logged with failed status if extraction

### Git Push PASS

- serialized content written
- vault copy updated
- git commit/push completes or no-change case reported accurately
- raw URL displayed

### Git Push FAIL

- error message shown
- no false success state

---

## Retry/Escalation Logic

- Qwen extract failure path requires:
  - dependency check,
  - correct interpreter,
  - BitsAndBytesConfig patch,
  - pixel/token reduction,
  - GPU process check.
- UI failure path requires:
  - console error inspection,
  - state injection fix,
  - schema migration.
- Git push failure path requires:
  - compare DB serialized output,
  - compare local `CIS_LIVE.md` and vault `CIS_LIVE.md`,
  - check git status,
  - check raw URL.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## Authority Structures

- ADR table is canonical for decisions.
- Human remains final authority for review, promotion, and correction.
- AI output remains proposal/draft until human validation.
- CIS Live captures model collaboration but human selects final solution.

## Review States

- Review page becomes primary human surface for draft record validation.
- Review state belongs to the knowledge record, not the source manifest.
- Pipeline state and review state must remain distinct.

## Promotion Logic

- Record promotion:
  - draft → checked → approved → locked.
- DAM promotion:
  - DAM record → linked project asset.
  - DAM record → standalone project seed.
- Live session promotion:
  - resolved collaboration → `captures` solution record.

## Rejection Paths

- Failed extraction → error in `extraction_runs`; not trusted knowledge.
- Inadequate model output → human correction or rerun.
- Asset no longer useful in project → demote to DAM, not delete.
- Live session not resolved → stays open; not knowledge capture.

## Trust Enforcement

- Decision logging form prevents governance records from existing only in chat.
- Review page prevents model metadata from becoming trusted automatically.
- DAM demotion prevents loss of valuable material while preserving project integrity.
- CIS Live resolution form prevents transient brainstorming from becoming knowledge without explicit solution capture.

## Hallucination Controls

- Human image review addresses model inability to identify visual language correctly.
- Comic illustration requires ambiguity-aware extraction standards.
- Model output must be editable before promotion.

## Provenance Enforcement

- `extraction_runs` logs model, source, status, duration, project.
- `live_rounds` preserves round number, message, consolidated responses, optional model attribution.
- GitHub raw file is communication surface, DB is authoritative collaboration record.

## Validation Contracts

- ADR form validates required fields before DB insert.
- Add Round validates save before thread update.
- Live schema migration required for `consolidated` field.
- Review/promotion UI must enforce same rules as `cis_review.py`.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## Knowledge Formation Logic

- Raw file is not knowledge.
- Source is not knowledge.
- Knowledge begins after extraction/normalization creates a structured record.
- Human review turns draft record into usable/trusted knowledge.
- CIS Live resolved sessions produce solution captures, adding operational lessons to the knowledge base.

## Retrieval Structure

- Approved/locked knowledge records should feed retrieval.
- DAM records should become searchable unaffiliated assets.
- Live solution captures become searchable problem/solution knowledge.
- Extraction runs provide operational diagnostics but are not direct retrieval content unless summarized into captures/insights.

## Indexing Implications

- Knowledge index must include project affiliation state.
- DAM view filters `project_id IS NULL`.
- Project knowledge filters `project_id = active_project`.
- Live captures may need tags and project_id to support future retrieval.

## Normalization Rules

- AI descriptions must be normalized into fields before review.
- Live collaboration must be normalized into topic/problem/solution/model/tags before capture.
- Source lineage must be preserved from archive/incoming path through source_id to knowledge record.

## Ontology/Spine Implications

- Asset becomes a core object category between knowledge record and project.
- DAM becomes the unaffiliated asset pool.
- Review is the trust spine between AI output and knowledge reuse.
- CIS Live adds “solution capture” as a knowledge category for system-building knowledge.

## Chunking Logic

- Live sessions are round-based chunks.
- Each round contains:
  - user message,
  - consolidated responses,
  - optional model-specific responses.
- GitHub export chunks by session and round.
- Future retrieval can chunk problem/solution separately from raw brainstorming.

## Reinforcement Behavior

- Human corrections in review page improve future metadata quality.
- Live resolved sessions capture which model/approach worked.
- DEMOTION from project back to DAM is a relevance correction signal.
- Extraction failures become model/runtime improvement signals.

## Project Linkage

- Intake can assign `project_id`.
- Unaffiliated intake leaves `project_id` null.
- Knowledge record may later attach to project.
- Live solution captures should be linked to CIS project context when relevant.

## Stabilization Loops

- ADR form stabilizes governance.
- Review page stabilizes knowledge records.
- Extraction run log stabilizes intelligence runtime debugging.
- CIS Live stabilizes cross-model collaboration.

---

# 7. APPLICATION-LAYER IMPLICATIONS

## Workbench Requirements

- Dashboard must provide enough operator surface to make execution usable.
- Minimal application surfaces are justified when they reduce critical operator bottlenecks.
- Full application remains deferred, but early operator console is required.

## Interface Panels

### Existing / Built or Partially Built

- System panel
- Session panel
- Tasks panel
- Pipeline panel
- Knowledge panel
- ADRs / Decisions panel
- Live panel

### Required / Emergent

- Review page
- Source list/pipeline queue
- DAM view
- Extraction run history panel
- Public Live endpoint status panel

## Operator Actions

- Ingest source.
- Check source status.
- Run classify/preprocess/extract/normalize.
- Log ADR.
- Add live session.
- Add round.
- Push to GitHub.
- Copy URL.
- Resolve session.
- Save solution capture.
- Review image + metadata.
- Link/promote/demote asset.

## Runtime Visibility Needs

- Intake success/failure must be visible.
- Source ID must be surfaced immediately.
- Pipeline status must be visible.
- Extraction run history must be visible.
- Git push status must distinguish no-change vs error.
- Live panel must show saved rounds and session status.

## Workflow Exposure

- Pipeline must expose source lifecycle.
- Review must expose knowledge trust lifecycle.
- DAM must expose unaffiliated asset lifecycle.
- Live must expose model collaboration lifecycle.

## Project-Centered Interaction

- Active project remains default context.
- Sources ingested under project become affiliated.
- Unaffiliated intake becomes DAM material.
- Project context must not hide unaffiliated assets from system-level view.

## Application/Runtime Bridges

- Dashboard routes must be treated as runtime bridges.
- Buttons/forms must trigger scripts or DB writes.
- UI feedback must reflect runtime state, not cosmetic assumptions.
- Future app must expose a runtime that already works.

---

# 8. FEEDBACK LOOP DISCOVERIES

## Reinforcement Loops

- AI proposes metadata → human corrects → corrected record becomes authoritative.
- Model collaboration → human consolidates → Live session evolves → resolved solution captured.
- DAM asset linked/demoted → relevance signal modifies project/asset relationship.

## Correction Loops

- UI bug → console/error → code patch → retest.
- Extraction failure → environment/config check → patch → rerun.
- Git push mismatch → inspect DB/local/vault/raw URL → patch messaging/serialization.

## Governance Loops

- Conversation decision → ADR form → decisions table → sorted dashboard list.
- Emergent DAM concept → ADR-019 → documentation addition.
- Review surface concept → ADR-020 → future contract alignment.

## Retrieval-Improvement Loops

- Reviewed/approved records improve retrieval quality.
- DAM grows searchable pool of unaffiliated assets.
- Live solution captures create searchable operational memory.

## Archive-Learning Loops

- Archive source → intake → classification → extraction → review → knowledge/DAM/project asset.
- Unaffiliated material can later become project-relevant.

## Continuity/Memory Loops

- CIS Live reduces cross-model context loss.
- GitHub raw file / future LXC endpoint provides shared context surface.
- Session close still needed for durable handoff, but Live handles rapid mid-session coordination.

## Project-Output Feedback Loops

- Project assets can be demoted to DAM when they stop working.
- DAM assets can seed future projects.
- Visual review improves how image references become reusable production knowledge.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## Missing Runtime Bridges

- Pipeline source list and pagination are not yet built.
- Intake success does not yet fully auto-refresh pipeline queue.
- Review page is scoped but not implemented.
- DAM nav/surface is defined but not implemented.
- LXC public endpoint is specified but not built.

## Undefined Objects

- Asset object is conceptually defined but may not have its own schema/table.
- DAM record is defined as nullable project knowledge record, but UI filters and operations are not built.
- Project promotion from asset lacks implementation contract.
- Demotion operation lacks command/API/UI.
- Live capture solution schema currently maps to `captures`, but richer solution schema may be needed later.

## Unstable Schemas

- `live_rounds` required post-hoc `consolidated` column migration.
- `extraction_runs` exists but may need schema evolution for prompt version, config, pixel budget, token budget, GPU memory.
- `captures` may be too generic for long-term solution knowledge.

## Unresolved Orchestration

- Pipeline still relies on manual stage clicking.
- Extract button may fail if environment mismatch persists.
- Git push workflow can mislead if no new commit occurs.
- Multiple Live sessions can be open; active session/push selection must remain clear.

## Unresolved Routing

- 32B extraction settings not yet locked into model profile/config.
- Router does not automatically downgrade/escalate based on VRAM failure.
- GitHub vs LXC live serving not decided as final path.

## Missing Governance

- DAM documentation needed in current authoritative docs.
- ADR-020 review page must align with Review States Contract.
- Live solution capture should likely become a formal record category or intake path.

## Missing Validation Layers

- No automatic check that GitHub raw file reflects latest DB state.
- No validation that Live push wrote all sessions/rounds correctly.
- No validation that review edits preserve schema.
- No validation that extraction run logging covers dashboard and manual extract paths equally.

## Unresolved Application Surfaces

- Review page.
- DAM page.
- Source list queue.
- Extraction run history UX.
- LXC live status/URL display.
- Live split layout: thread left, fixed round form right remains proposed.

## Unresolved Storage Rules

- Whether Live sessions should remain in `cis_memory.db` long term or migrate into canonical knowledge records.
- Whether solution captures should produce markdown mirrors.
- How DAM records map into physical folder structure when `project_id` is null.
- How promoted project seeds preserve source/record lineage.

---

# 10. BUILD-PLAN IMPLICATIONS

## Foundational Prerequisites

1. ADR logging form must remain stable.
2. DB schema migrations must be versioned and repeatable.
3. Pipeline source status must be visible before extraction scaling.
4. Review surface must exist before trusted knowledge scaling.
5. Model runtime config must be stabilized before repeated extraction.
6. CIS Live push/serialization must be reliable before relying on it for cross-model work.

## Blocked Layers

- Knowledge scaling is blocked by review/promotion UI.
- DAM usability is blocked by source/record list and unaffiliated filtering.
- Agent use is blocked by approved knowledge and retrieval readiness.
- Public model coordination is blocked by either stable GitHub sync or LXC endpoint.

## Sequencing Implications

### Immediate

1. Fix Live push no-change/stale serialization feedback.
2. Implement split Live layout if usability remains a blocker.
3. Stabilize Qwen extraction config.
4. Implement Review page for image sources.
5. Implement source list/pagination.

### Near-Term

6. Add DAM view.
7. Add promote/demote controls.
8. Add extraction config logging.
9. Add LXC read-only public endpoint.

### Later

10. Build full asset/project promotion workflow.
11. Build retrieval over reviewed records.
12. Integrate agents with DAM/project knowledge.

## Runtime-First Requirements

- Every button must produce visible success/failure state.
- Every DB write must be reflected in UI state.
- Every push/export must be verifiable.
- Every model run must be logged.

## Governance-First Requirements

- ADRs must be logged through UI, not manual SQL.
- Review/promotion must require human action.
- DAM promotion/demotion must preserve lineage.
- Live resolved sessions must be explicitly captured, not assumed knowledge.

## Execution-First Requirements

- Scripts must be callable by dashboard routes.
- Correct environment must be enforced per script.
- Schema migrations must precede UI usage.
- Error messages must identify real failure conditions.

## Application Dependencies

- Application surfaces must be built only where they reduce proven operator bottlenecks.
- Dashboard monolith risk needs future modularization.
- UI design must prioritize visual readability, persistent action controls, and low scroll friction.

---

# 11. EXTRACTED CANONICAL OBJECTS

## Source

- **Purpose**: Raw ingested material in processing container.
- **Lifecycle**: archive/incoming → intake → source container → pipeline states → knowledge record.
- **Authority Source**: Source manifest and filesystem.
- **Related Objects**: Manifest, processing profile, extraction run, knowledge record, project.
- **States**: arrived, classified, preprocessed, extracted, normalized.
- **Storage Implications**: `/mnt/projects/cis/ingest/processing/<source_id>/`.

## Source Manifest

- **Purpose**: Tracks intake metadata and processing status.
- **Lifecycle**: created at intake; updated by pipeline stages.
- **Authority Source**: `cis_intake.py` and pipeline scripts.
- **Related Objects**: Source, processing_profile, processing_plan, project_id.
- **States**: mirrors source/pipeline state.
- **Storage Implications**: Stored inside source container.

## Processing Profile

- **Purpose**: Determines extraction path and model routing.
- **Lifecycle**: assigned at intake, confirmed/updated at classify.
- **Authority Source**: Classification logic / manifest.
- **Related Objects**: Source manifest, extraction run, model registry.
- **States**: image/reference/document/video/audio/idea profile variants.
- **Storage Implications**: Manifest field.

## Knowledge Record

- **Purpose**: Canonical structured knowledge output.
- **Lifecycle**: produced after normalize; reviewed; promoted/demoted; retrieved.
- **Authority Source**: Extraction + normalization + human review.
- **Related Objects**: Source, project, asset, DAM, review state, retrieval chunks.
- **States**: draft, checked, approved, locked, deprecated.
- **Storage Implications**: JSON canonical record + markdown mirror in knowledge records.

## Asset

- **Purpose**: Reviewed knowledge record usable in production.
- **Lifecycle**: knowledge record → asset linked to project or DAM.
- **Authority Source**: Human review/labeling.
- **Related Objects**: Project, DAM, knowledge record.
- **States**: affiliated, unaffiliated, promoted, demoted.
- **Storage Implications**: Same knowledge record; project affiliation determined by `project_id`.

## DAM Record

- **Purpose**: Unaffiliated knowledge asset.
- **Lifecycle**: unaffiliated intake/review → DAM → linked/promoted or retained.
- **Authority Source**: `project_id = null` plus review state.
- **Related Objects**: Knowledge record, project, asset.
- **States**: unaffiliated, linked, promoted, demoted.
- **Storage Implications**: Same record storage; surfaced through DAM view.

## Project

- **Purpose**: Persistent container for creative work.
- **Lifecycle**: created independently or seeded from asset; receives assets; evolves through WIAS.
- **Authority Source**: Human/operator decision.
- **Related Objects**: Sources, assets, knowledge records, Live sessions, tasks.
- **States**: active/open/paused/archived; project-specific status not fully specified in transcript.
- **Storage Implications**: Project folders + DB project_id references.

## Review Page / Review Surface

- **Purpose**: Human validation surface for visual/knowledge records.
- **Lifecycle**: source/record selected → image displayed → fields edited → saved → promoted/demoted/approved.
- **Authority Source**: Human operator.
- **Related Objects**: Knowledge record, asset, DAM, project.
- **States**: editing, saved, checked, approved; not fully implemented.
- **Storage Implications**: Writes back to record JSON/DB fields.

## Decision / ADR

- **Purpose**: Canonical governance decision.
- **Lifecycle**: proposed/logged → displayed/sorted → locked/superseded.
- **Authority Source**: Decisions table.
- **Related Objects**: Dashboard ADR panel, documentation updates.
- **States**: locked, proposed, superseded.
- **Storage Implications**: `decisions` table in `cis_memory.db`.

## Extraction Run

- **Purpose**: Audit record for model extraction attempt.
- **Lifecycle**: extract initiated → run logged → success/failure displayed.
- **Authority Source**: Pipeline extract route/manual logging.
- **Related Objects**: Source, model, project, knowledge record.
- **States**: pending, success, failed, partial.
- **Storage Implications**: `extraction_runs` table.

## CIS Live Session

- **Purpose**: Cross-model problem-solving session.
- **Lifecycle**: create problem → add rounds → push → resolve → capture.
- **Authority Source**: Operator through Live panel.
- **Related Objects**: Live rounds, captures, GitHub raw file, project.
- **States**: open, resolved.
- **Storage Implications**: `live_sessions` table; serialized to `CIS_LIVE.md`.

## CIS Live Round

- **Purpose**: One cycle of user prompt + model responses.
- **Lifecycle**: compose → add round → DB row → serialize/push.
- **Authority Source**: Operator.
- **Related Objects**: Live session, consolidated response, model attributions.
- **States**: saved; no separate state defined.
- **Storage Implications**: `live_rounds` table with `your_message`, `consolidated`, optional model fields.

## Consolidated Response

- **Purpose**: Fast combined model feedback capture.
- **Lifecycle**: paste model outputs → store as round field → push to shared file.
- **Authority Source**: Human consolidation.
- **Related Objects**: Live round, optional model fields.
- **States**: present/empty.
- **Storage Implications**: `live_rounds.consolidated`.

## Model Attribution Fields

- **Purpose**: Optional precise record of Gemini/Claude/ChatGPT responses.
- **Lifecycle**: collapsed by default; filled when attribution matters.
- **Authority Source**: Human paste.
- **Related Objects**: Live round, solution capture.
- **States**: optional.
- **Storage Implications**: `live_rounds.gemini`, `live_rounds.claude`, `live_rounds.chatgpt`.

## Solution Capture

- **Purpose**: Convert resolved Live session into knowledge base entry.
- **Lifecycle**: resolve → fill solution/decided_by → write capture.
- **Authority Source**: Human operator.
- **Related Objects**: Live session, captures table, tags.
- **States**: captured.
- **Storage Implications**: `captures` table with `capture_type=solution`.

## CIS_LIVE.md

- **Purpose**: Shared external-readable coordination file.
- **Lifecycle**: serialized from DB → local write → vault copy → git push → raw URL / future LXC read.
- **Authority Source**: Live DB serialization.
- **Related Objects**: Live sessions, GitHub repo, future LXC endpoint.
- **States**: local, pushed, stale, public.
- **Storage Implications**: `/mnt/projects/cis/CIS_LIVE.md` and vault copy.

## LXC Public Endpoint

- **Purpose**: Secure direct public read endpoint for `CIS_LIVE.md`.
- **Lifecycle**: create container → bind mount file read-only → serve GET → models read.
- **Authority Source**: Proxmox/container config.
- **Related Objects**: CIS_LIVE.md, router port forwarding, external models.
- **States**: not built; proposed.
- **Storage Implications**: read-only bind mount only; no DB/archive/dashboard access.

---

# 12. ARCHITECTURAL DELTA SUMMARY

After this file, CIS is understood less as a future application and more as an already-emerging operator-facing runtime whose application surfaces must appear wherever human bottlenecks block execution.

The major new understanding is:

1. **Execution proof is insufficient without operator feedback.** A command can work, but if the dashboard does not show success, source_id, status, or error, the system is not usable.

2. **The Application Layer can appear early as an operator console without violating build discipline.** ADR logging, Pipeline controls, Extraction Run history, and CIS Live are not “full app” features; they are execution-support surfaces.

3. **The DAM is the unaffiliated knowledge layer.** It is not a separate product. It is the same knowledge base filtered by missing project affiliation, with promotion and demotion paths.

4. **Every ingested item is an asset by default, not automatically a project.** Review determines whether it stays a project asset, becomes a DAM record, or seeds a standalone project.

5. **Review is the trust conversion point.** AI extraction produces proposals. Human visual inspection and metadata correction convert proposals into trusted knowledge.

6. **Cross-model collaboration is now a system object.** CIS Live creates a structured record of multi-model problem-solving, reducing but not eliminating human middleware.

7. **The human remains the write bridge.** External models can read GitHub/LXC shared state, but the operator still posts responses into CIS Live. The system must minimize this burden without exposing unsafe write access.

8. **Runtime diagnostics need their own records.** Extraction attempts, model failures, and configuration changes must be logged separately from knowledge output.

9. **Hardware constraints are architectural constraints.** Qwen32B is not simply a model choice; it forces runtime configuration, VRAM budgeting, UI/GUI awareness, and fallback routing.

10. **Build order shifts toward usability gates.** Before scaling intelligence extraction or knowledge formation, CIS must stabilize the interfaces that allow the operator to see, review, correct, and trust what happened.

The topology that emerges is:

```text
Archive / Incoming Source
  → Intake
  → Source Container + Manifest
  → Pipeline Queue
  → Classify
  → Preprocess
  → Extract
  → Extraction Run Log
  → Normalize
  → Draft Knowledge Record
  → Review Surface
      → Project Asset
      → DAM Asset
      → Promoted Project
      → Demoted Asset
  → Retrieval / Teacher / Librarian later
```

Parallel governance and collaboration topology:

```text
Conversation / Runtime Discovery
  → ADR Form
  → decisions table
  → documented system rule

Problem / Model Collaboration
  → CIS Live Session
  → Live Rounds
  → GitHub or LXC shared read surface
  → Resolved Solution Capture
  → Knowledge Base
```

This file therefore records a mutation from “CIS as designed architecture” to “CIS as operator-mediated runtime system with emerging application surfaces, governance capture, DAM semantics, review gates, extraction observability, and cross-model coordination.”
