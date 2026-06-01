# CIS Chat 2026-04 013 — Extraction Analysis

Source file: `CIS_Chat_2026-04_013.md`  
Extraction mode: Implementation-grade architectural topology extraction  
Primary delta: Phase 1 application/runtime bridge emergence, session-close synchronization, project-object formalization, dashboard-as-operator-surface, and human-middleware exposure.

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Handoff Is Not Documentation; It Is a Runtime Continuity Object

- **Architectural Significance**: The session handoff became a live continuity object that must be generated, synchronized, versioned, and passed forward through a governed session-close process. The handoff is no longer a manually written note; it is a product of runtime state, database entries, git state, synced records, and session protocol.
- **Affected Layers**: Governance Layer, Execution Layer, Application Layer, Memory/Continuity Layer.
- **Dependency Impact**: Introduces dependency between `session_log`, `ADRs.md`, `knowledge_records`, `projects`, `runtime_scripts`, `system_log.md`, generated handoff markdown, and git push.
- **Build Impact**: Session close must be wired before dashboard work can be trusted. Any dashboard action that updates state must be included in close synchronization.
- **Runtime Impact**: One session-close action must produce an aligned system state. If any target is omitted, the next session starts from partial truth.

### Critical analysis

- **Invalidated assumption**: A handoff document alone is enough to start the next session.
- **Introduced dependency**: Handoff validity depends on DB state, synced files, generated docs, and git status.
- **Layer affected**: Governance, Runtime, Application.
- **Build order change**: Session-close wiring becomes a prerequisite for further dashboard expansion.
- **New system object required**: Session Close Protocol.
- **Governance rule required**: Close fields must be generated only when the human signals actual session end.
- **Runtime state required**: `session_closed`, sync result list, git result.
- **Review/promotion path required**: Handoff content must be checked against latest session state before use.
- **Feedback loop created**: Failed/stale handoff → protocol correction → future close improvement.
- **Hidden bottleneck exposed**: Human copy/paste timing controls institutional memory quality.

---

## Discovery Name: CIS Build Must Become Its Own First Project Object

- **Architectural Significance**: The system pipeline was previously proven with loose sources, but it had not been exercised as a project-centered system. This invalidated the assumption that a working pipeline equals a valid CIS workflow.
- **Affected Layers**: Project Object Layer, Workflow Layer, Knowledge Layer, Application Layer.
- **Dependency Impact**: Dashboard panels require an active `project_id`; knowledge records require project linkage; WIAS stages require project context.
- **Build Impact**: `PROJECT__CIS__BUILD__V1` must exist before dashboard development can properly test project-scoped views.
- **Runtime Impact**: Records processed during system construction must link back to the CIS build project rather than remaining loose source artifacts.

### Critical analysis

- **Invalidated assumption**: Dashboard can be built against system-wide state without project context.
- **Introduced dependency**: Dashboard views depend on a formal project object and project-scoped record linkage.
- **Layer affected**: Application, Workflow, Knowledge.
- **Build order change**: Project object creation precedes reliable dashboard expansion.
- **New system object required**: `PROJECT__CIS__BUILD__V1`.
- **Governance rule required**: CIS infrastructure/application build is itself a WEB-domain project.
- **Runtime state required**: project status, active WIAS stages, production phases.
- **Review/promotion path required**: Existing records must be re-linked or reprocessed under the project.
- **Feedback loop created**: Dashboard reveals missing project context → project schema refined.
- **Hidden bottleneck exposed**: Loose records cannot support project-centered application behavior.

---

## Discovery Name: cis_review.py Became the First Human Review Execution Contract

- **Architectural Significance**: `cis_review.py` operationalized review as a command-level human validation step. It loads draft records, presents corrections, applies accepted changes, updates record and manifest status, writes a markdown mirror, and logs the review.
- **Affected Layers**: Execution Layer, Review/Promotion Layer, Knowledge Layer, Governance Layer.
- **Dependency Impact**: Depends on source manifest path, knowledge record folder structure, corrections table, session_log schema, and valid status transitions.
- **Build Impact**: Review functionality must exist before trusted knowledge promotion and before dashboard review controls.
- **Runtime Impact**: Human review becomes an explicit state transition rather than an informal editing activity.

### Critical analysis

- **Invalidated assumption**: Generated knowledge can move forward without a formal review command.
- **Introduced dependency**: Knowledge trust depends on review execution and DB logging.
- **Layer affected**: Knowledge, Execution, Governance.
- **Build order change**: Review command precedes knowledge promotion UI.
- **New system object required**: Review session/action entry.
- **Governance rule required**: Accepted corrections update records; corrections table remains history/source input.
- **Runtime state required**: draft → checked; manifest → checked.
- **Review/promotion path required**: approve/reject/edit per correction.
- **Feedback loop created**: corrections table → human review → record update → session_log.
- **Hidden bottleneck exposed**: Incorrect filesystem assumptions broke the first review command until real paths were discovered.

---

## Discovery Name: Runtime Scripts Were Outside Version Control

- **Architectural Significance**: The working execution layer (`memory/`, `runtime/`) was not recoverable through git, even though it contained the application’s operational scripts.
- **Affected Layers**: Execution Layer, Governance Layer, Version Control Layer, Continuity Layer.
- **Dependency Impact**: Runtime integrity depends on syncing scripts into the git-tracked vault under `runtime_scripts/`.
- **Build Impact**: Version-control coverage became a prerequisite before continuing dashboard/application work.
- **Runtime Impact**: Loss or overwrite of `cis_log.py`, `cis_review.py`, or pipeline scripts would break the system without rollback.

### Critical analysis

- **Invalidated assumption**: GitHub backup covered everything vital.
- **Introduced dependency**: Session close must sync runtime scripts into the vault before commit.
- **Layer affected**: Governance, Runtime.
- **Build order change**: Version-control closure precedes dashboard expansion.
- **New system object required**: `runtime_scripts/` mirror in the vault.
- **Governance rule required**: Generated artifacts such as `.db` and `__pycache__` are excluded.
- **Runtime state required**: synced vs unsynced runtime scripts.
- **Review/promotion path required**: Runtime changes must be committed after test.
- **Feedback loop created**: Overwrite risk → git mirror → session-close sync rule.
- **Hidden bottleneck exposed**: The execution layer existed outside the institutional record.

---

## Discovery Name: Dashboard Is an Operator Companion, Not Just a Status Viewer

- **Architectural Significance**: The dashboard’s role mutated from displaying system state to guiding non-coder creative operators through session start, active work, capture, task execution, and close.
- **Affected Layers**: Application Layer, Operator Model, Execution Layer, Workflow Layer.
- **Dependency Impact**: Requires task table, project launcher, URL-scoped project workspace, capture button, session panel, and execution endpoints.
- **Build Impact**: Application work must prioritize operator cognitive relief over developer-style dashboards.
- **Runtime Impact**: The dashboard becomes a control surface for session rituals and eventually for orchestrator/librarian handoff.

### Critical analysis

- **Invalidated assumption**: A minimal dashboard can be a generic admin view.
- **Introduced dependency**: Dashboard UI must reflect project context and operator phase.
- **Layer affected**: Application, Workflow, Governance.
- **Build order change**: Project selection architecture must be settled before DAM/project management panels.
- **New system object required**: Task queue entries and capture records.
- **Governance rule required**: Dashboard actions must not bypass human authority.
- **Runtime state required**: selected project, active panel, task status, session state.
- **Review/promotion path required**: Some UI actions need approval gates.
- **Feedback loop created**: User confusion using dashboard → UI/UX tasks added → dashboard evolves.
- **Hidden bottleneck exposed**: Creative users cannot be expected to hold roadmap, schema, and developer tasks in memory.

---

## Discovery Name: Project Launcher and URL Routing Became Required Architecture

- **Architectural Significance**: Multi-project use invalidated the single active project assumption. The correct application structure became a project launcher with project-scoped routes.
- **Affected Layers**: Application Layer, Project Object Layer, DAM Future Layer, Project Management Future Layer.
- **Dependency Impact**: DAM, tasks, knowledge records, pipeline steps, and session actions must be scoped by `project_id`.
- **Build Impact**: URL routing must be built before adding DAM and project management panels.
- **Runtime Impact**: Browser routes become a project-context boundary: `/project/<project_id>/...`.

### Critical analysis

- **Invalidated assumption**: A top-bar project switcher is sufficient.
- **Introduced dependency**: Every panel must resolve project context from the route.
- **Layer affected**: Application.
- **Build order change**: Rebuild dashboard foundation before adding more panels.
- **New system object required**: Project card / project workspace route.
- **Governance rule required**: Project context must be explicit, not implicit.
- **Runtime state required**: selected project id in URL.
- **Review/promotion path required**: Not direct, but project-scoped review surfaces inherit it.
- **Feedback loop created**: DAM/project management expectations → project routing correction.
- **Hidden bottleneck exposed**: Scaling from one to many projects breaks global dashboard assumptions.

---

## Discovery Name: WIAS Progress Is a Universal Production Signal, Not Only Output Taxonomy

- **Architectural Significance**: WIAS was clarified as a universal production sequence: Word = planning/concept, Image = visual/aesthetic language, Action = execution/interaction/motion, Sound = final resonance/polish, Web = distribution/social/public life.
- **Affected Layers**: Workflow Layer, Application Layer, Project Progress Model.
- **Dependency Impact**: Progress visualization must represent WIAS depth across every project, including code/application projects.
- **Build Impact**: The dashboard progress component must be WIAS-aware rather than generic percent complete.
- **Runtime Impact**: Project progress display uses WIAS stage depth indicators rather than a single linear bar.

### Critical analysis

- **Invalidated assumption**: WIAS stages are only media categories or output endpoints.
- **Introduced dependency**: Project objects need `active_stages` and eventually `stage_progress`.
- **Layer affected**: Workflow, Application.
- **Build order change**: Progress model must be defined before project management panel.
- **New system object required**: WIAS stage-progress field.
- **Governance rule required**: All projects can be interpreted through WIAS, with different depth by stage.
- **Runtime state required**: stage depth/active/completed signals.
- **Review/promotion path required**: Stage outputs eventually need validation/acceptance.
- **Feedback loop created**: User meaning of WIAS → dashboard model correction.
- **Hidden bottleneck exposed**: A generic progress bar cannot represent creative development.

---

## Discovery Name: Task Table Became a Pre-Intelligence Orchestration Substitute

- **Architectural Significance**: Before orchestrator/librarian agents exist, the dashboard task table becomes the visible roadmap and operator guidance layer.
- **Affected Layers**: Application Layer, Workflow Layer, Future Agent Layer.
- **Dependency Impact**: Tasks must be stored in the DB with project, phase, priority, status, command, and created timestamp.
- **Build Impact**: Task seeding becomes a required step to prevent roadmap loss.
- **Runtime Impact**: Task count and priority strips become operator-facing progress indicators.

### Critical analysis

- **Invalidated assumption**: The human can remember the roadmap or reconstruct it from chats.
- **Introduced dependency**: Build agenda depends on DB-backed task records.
- **Layer affected**: Application, Agent future.
- **Build order change**: Task panel must be populated before further ad hoc work.
- **New system object required**: Task.
- **Governance rule required**: Tasks should be generated from known gaps and session handoff context.
- **Runtime state required**: open/completed task status.
- **Review/promotion path required**: Task completion must be human-confirmed or command-verified.
- **Feedback loop created**: Session discoveries → task entries → future build execution.
- **Hidden bottleneck exposed**: Cognitive load is architectural debt.

---

## Discovery Name: Session Close Must Synchronize Multiple Stores Atomically Enough for Continuity

- **Architectural Significance**: CIS state was distributed across SQLite DB, markdown docs, knowledge JSON, runtime scripts, project JSON, system logs, generated handoff, and git. Manual synchronization created continuity risk.
- **Affected Layers**: Execution Layer, Governance Layer, Application Layer, Continuity Layer.
- **Dependency Impact**: Session close must perform an ordered sync sequence and display pass/fail results.
- **Build Impact**: Session-close endpoint becomes a core runtime bridge.
- **Runtime Impact**: Dashboard session close executes the system’s continuity contract.

### Critical analysis

- **Invalidated assumption**: Session close can be a simple DB log plus git commit.
- **Introduced dependency**: State validity depends on all stores being updated together.
- **Layer affected**: Governance, Runtime, Application.
- **Build order change**: Close synchronization must precede reliance on dashboard-generated handoffs.
- **New system object required**: Sync result / step log.
- **Governance rule required**: Session cannot be considered clean if sync steps fail.
- **Runtime state required**: step-by-step sync status.
- **Review/promotion path required**: Handoff should be reviewed before use.
- **Feedback loop created**: Failed sync/stale handoff → protocol and backend correction.
- **Hidden bottleneck exposed**: Manual sync and stale generated files create institutional memory drift.

---

## Discovery Name: Protocol Timing Is Part of Governance

- **Architectural Significance**: The timing of when the AI generates close fields became a governance issue. If fields are generated before the session actually ends, the handoff becomes stale even if the mechanism works.
- **Affected Layers**: Governance Layer, Human Authority Layer, Continuity Layer.
- **Dependency Impact**: AI must generate close fields once at true session end, and regenerate them if more work happens.
- **Build Impact**: `CIS_Session_Close_Protocol.md` becomes mandatory handoff package material.
- **Runtime Impact**: The dashboard can only be as accurate as the close fields supplied to it until automated orchestration exists.

### Critical analysis

- **Invalidated assumption**: Paste-ready close fields can be supplied proactively after any major accomplishment.
- **Introduced dependency**: Handoff accuracy depends on a timing rule and AI compliance.
- **Layer affected**: Governance, Operator Model.
- **Build order change**: Protocol must be created before session close is considered reliable.
- **New system object required**: Session Close Protocol.
- **Governance rule required**: Claude must not generate close fields until the human signals final close.
- **Runtime state required**: ready-to-close vs mid-session.
- **Review/promotion path required**: Final close fields supersede any earlier fields.
- **Feedback loop created**: Stale handoff → protocol rule → improved future handoffs.
- **Hidden bottleneck exposed**: AI itself can become a source of continuity drift without protocol.

---

# 2. TOPOLOGY MUTATIONS

## 2.1 New Layers

### Session Continuity Synchronization Layer

A new implicit layer emerged between Governance and Application. It coordinates session logging, ADR regeneration, runtime script syncing, knowledge/project syncing, handoff generation, system log writing, and git push. This layer is not a creative workflow layer; it is the continuity bridge that prevents institutional memory drift.

### Operator Companion Layer

The dashboard mutated from a passive status interface into an operator companion. It supports:

- project selection
- project-scoped workspaces
- session start and close
- task queue guidance
- capture of observations/insights
- WIAS progress display
- future execution buttons

### Pre-Intelligence Orchestration Layer

Before agents exist, the task table and dashboard session panel function as a human-facing orchestration substitute. This layer will later be partially absorbed by Orchestrator, Librarian, Teacher, and other agent roles.

---

## 2.2 Split Layers

### Session Handoff split into:

1. **Session Close Protocol** — standing behavioral rule and handoff package specification.
2. **Generated Handoff Document** — session-specific output generated by dashboard close.
3. **cis-start Output** — runtime state verification used at next session start.

### Review split into:

1. **CLI Review** — `cis_review.py` command for terminal-based review.
2. **Dashboard Review Surface** — future application interface for same review state transitions.
3. **Corrections Table** — input history source, not direct canonical record mutation.

### Dashboard split into:

1. Project Launcher
2. Project Workspace
3. Project-Scoped Panels
4. Session Panel
5. Tasks Panel
6. Capture Flyout
7. Future DAM / Project Management Panels

---

## 2.3 Runtime Bridges

### New Bridges

- `cis-log decision` → DB decisions table → regenerated `ADRs.md`.
- `cis-log insight` → insights table → future Insights panel.
- `cis_review.py` → record JSON + manifest + markdown mirror + session_log.
- Dashboard Session Close → DB + markdown + synced folders + git.
- Project Launcher route → selected `project_id` → scoped dashboard panels.
- Task table → dashboard roadmap → future orchestrator input.

### Still Missing Bridges

- Dashboard decision form → decisions table → ADR generation.
- Dashboard review trigger → `cis_review.py` execution.
- Pipeline intake → active project link.
- Knowledge panel → status promotion.
- Logs viewer → pipeline log files.
- Automated handoff package builder.

---

## 2.4 Orchestration Changes

- Manual terminal-driven session close shifted toward dashboard-driven close.
- Dashboard began to own session rituals.
- Task queue became the pre-agent orchestration surface.
- Application backend became responsible for syncing runtime artifacts to vault before git commit.
- The session close endpoint now functions as a mini-orchestrator.

---

## 2.5 Governance Expansion

New governance requirements:

- Close fields generated only at actual session end.
- Handoff package must include: `cis-start` output, generated handoff file, and Session Close Protocol.
- ADR regeneration must sort logically by ADR number, with superseded entries last.
- Runtime scripts and knowledge records must not remain outside version control.
- The dashboard must not imply a start action at close through misleading UI state.

---

## 2.6 Object-Model Mutations

New or strengthened objects:

- `PROJECT__CIS__BUILD__V1`
- Task record
- Insight record/table
- Capture record
- Session Close Protocol
- Sync step result
- Project route/workspace
- WIAS progress data
- system_log entry
- Handoff package

---

## 2.7 Workflow/Execution Separation

The session clarifies that workflow descriptions are insufficient unless paired with executable dashboard actions. The application must expose execution, not merely describe steps. Session close is the first major example: it moved from “run these commands” to “one button runs the sequence.”

---

## 2.8 Project-Container Evolution

CIS itself became a project container. This shifts the system from “we are building CIS” as an external activity to “CIS development is a formal project inside CIS.” That move allows the application to be tested against its own architecture.

---

# 3. DEPENDENCY DISCOVERIES

## 3.1 Hidden Prerequisites

- Dashboard needs a formal project object before meaningful project-scoped UI exists.
- `cis_review.py` needs correct source manifest paths and record file conventions before review can run.
- Session close needs runtime script syncing before git can be trusted.
- Handoff generation needs current close fields, not earlier drafted fields.
- ADR regeneration needs logical sort, not insertion order.
- Task panel needs seeded tasks before it can reduce operator memory burden.
- Future DAM/project management require URL-based project routing.

---

## 3.2 Sequencing Constraints

1. Resolve handoff gaps.
2. Build `cis_review.py` contract and command.
3. Add `cis-log insight` and insights table.
4. Bring runtime scripts under version control.
5. Bring knowledge records under version control.
6. Create formal CIS build project object.
7. Link existing records to project.
8. Build dashboard backend/frontend.
9. Rebuild dashboard around project launcher + routes.
10. Seed task table.
11. Wire session close to sync all critical stores.
12. Create Session Close Protocol.
13. Fix handoff/ADR ordering/protocol timing.

---

## 3.3 Circular Dependencies

### Dashboard vs Execution Layer

- Dashboard is needed to reduce terminal burden.
- But dashboard actions depend on stable execution commands.
- Resolution: expose existing commands first, then expand into richer UI.

### Handoff vs Protocol

- Handoff tells the next session what to do.
- Protocol tells the current assistant how to generate the handoff.
- Resolution: protocol becomes mandatory handoff package component.

### Knowledge Records vs Project Object

- Dashboard needs project-linked knowledge records.
- First record existed before the first formal project.
- Resolution: re-link record to `PROJECT__CIS__BUILD__V1`.

---

## 3.4 Unstable Dependencies

- Running dashboard server may not reflect the latest file on disk unless restarted.
- Close fields depend on user paste discipline until automated field generation exists.
- Handoff filename by date can overwrite or obscure multiple closes in one day.
- `ADRs.md` can drift from DB unless regenerated.
- `system_log.md` exists but pipeline-wide logging is deferred.

---

## 3.5 Runtime Blockers

- Missing `created_at` field caused DB log failure in `cis_review.py`.
- `sqlite3` CLI not installed; Python sqlite fallback required.
- Manifest path mismatch blocked review until real path discovered.
- Flask/Node/npm missing; Flask was installed, React served by CDN.
- Desktop launcher did not fully block multiple terminal/browser instances.
- Handoff content became stale due to close fields generated too early.

---

## 3.6 Orchestration Bottlenecks

- Human still mediates AI-generated close text into dashboard fields.
- Human still knows when to regenerate fields unless protocol is followed.
- Task creation still partly terminal-seeded.
- Dashboard does not yet write ADRs, review records, or promote knowledge.
- Some session actions are wired; others remain manual or deferred.

---

# 4. EXECUTION-LAYER IMPLICATIONS

## 4.1 Commands Extracted

### Review

```bash
python3 /mnt/projects/cis/runtime/cis_review.py IMAGE__WEIRD_WAR_TALES_COVER__001
```

Behavior:

- resolves record dir
- resolves manifest path
- loads draft record(s)
- loads corrections table entries
- presents corrections
- allows approve/skip/edit
- writes updated record JSON
- regenerates markdown mirror
- updates manifest
- logs session entry

### Insight

```bash
cis-log insight <category> <title> <observation> [--source <record_id>]
```

Behavior:

- creates insights table if missing
- writes insight record
- allows later `cis-log show insights`

### Runtime script sync

```bash
cp -r /mnt/projects/cis/memory/. /mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1/runtime_scripts/memory/
cp -r /mnt/projects/cis/runtime/. /mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1/runtime_scripts/runtime/
```

Later absorbed into dashboard session close.

### Session close dashboard endpoint

Runtime sequence:

1. Write session record to DB.
2. Regenerate `ADRs.md` from decisions table.
3. Sync knowledge records to vault.
4. Sync projects folder to vault.
5. Sync runtime scripts to vault.
6. Append `system_log.md` session entry.
7. Write handoff markdown.
8. Git add/commit/push.

### Task seeding

Creates DB tasks with:

- title
- description
- command
- phase
- project_id
- priority
- status
- created_at

---

## 4.2 States Extracted

### Knowledge record review states

- draft
- checked
- approved
- locked
- deprecated

Active transition demonstrated:

```text
draft → checked
```

### Manifest/source states observed

- arrived
- classified
- preprocessed
- extracted
- draft
- checked

### Session states

- session started
- active work
- close fields drafted
- session close submitted
- sync steps complete
- session closed/locked

### Task states

- open
- completed
- future: executable/running/failed likely needed

### Project states

- active
- future: initiated, paused, archived

---

## 4.3 Transitions

### Review transition

```text
source_id input
→ record + manifest resolved
→ corrections displayed
→ accepted corrections written
→ record status draft → checked
→ manifest status checked
→ session_log entry
```

### Dashboard close transition

```text
session close fields supplied
→ DB session insert
→ docs regenerated
→ records/projects/runtime mirrored
→ system log appended
→ handoff written
→ git committed/pushed
→ close button locked
```

### Project selection transition

```text
launcher grid
→ project card click
→ /project/<project_id>
→ project-scoped panels
```

### Task roadmap transition

```text
conversation gap / known backlog
→ task DB insert
→ dashboard task list
→ future execution/completion
```

---

## 4.4 Runtime Contracts

### cis_review.py contract

- Input: `source_id`
- Output: updated record JSON + markdown mirror + updated manifest
- DB reads: corrections table
- DB writes: session_log
- Required path reality: manifest at `/mnt/projects/cis/ingest/processing/<lowercase_source_id>/manifest.json`

### Session close contract

- Input: focus, completed, next steps, optional notes
- Output: DB session entry, synced files, regenerated ADRs, system log entry, handoff markdown, git commit/push
- Must display step-by-step success/failure
- Must disable after success to prevent duplicate close

### Dashboard project route contract

- Launcher route `/`
- Workspace route `/project/<project_id>`
- Panel routes `/project/<project_id>/<panel>`
- Every project panel must resolve `project_id`

---

## 4.5 Orchestration Logic

Current orchestration is hybrid:

- Human chooses action.
- ChatGPT/Claude supplies code/text fields.
- Dashboard executes some actions.
- DB tracks tasks/decisions/sessions/insights.
- Git preserves mirrored outputs.

Future target:

- Orchestrator populates tasks.
- Librarian accesses project-linked knowledge.
- Teacher uses validated records.
- Dashboard becomes monitor/override surface.

---

## 4.6 Validation Behavior

Validated in session:

- `cis_review.py` resolves paths and handles no-draft state without traceback.
- `cis-log insight` creates table and logs insight.
- Runtime scripts are committed.
- Knowledge records and projects are mirrored into vault.
- Session close shows eight pass steps.
- `system_log.md` created and appended.
- Handoff file exists but content quality depends on supplied fields.
- ADR ordering bug identified and sort logic validated.

---

## 4.7 Pass/Fail Structures

### PASS conditions

- Path resolved.
- Record found.
- DB write includes all required fields.
- Git commit/push succeeds.
- All sync steps show green check.
- Task count visible in dashboard.
- Project route opens correct workspace.

### FAIL conditions

- Manifest path mismatch.
- Missing DB column insert value.
- Dashboard server not restarted after code replacement.
- Git has nothing to commit after duplicate close.
- Handoff content stale or mislabeled.
- `ADRs.md` generated in insertion order.

---

## 4.8 Retry/Escalation Logic

- On path mismatch: inspect real filesystem paths, regenerate full script rather than forcing user to patch manually.
- On DB schema mismatch: query SQLite schema with Python fallback.
- On outdated dashboard behavior: check file contents and running server version.
- On stale handoff: regenerate close fields at true session end.
- On duplicate close: disable close button after success.

---

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## 5.1 Authority Structures

### Human authority

- Human validates corrections.
- Human decides session is ending.
- Human approves dashboard task direction.
- Human controls whether WIAS meaning is correct.

### System authority

- DB stores sessions, decisions, corrections, insights, tasks.
- `ADRs.md` is regenerated from decisions table.
- Project JSON anchors application context.
- Runtime scripts are version-controlled mirrors.

### AI assistant authority

- AI supplies implementation code and session close field content.
- AI must follow Session Close Protocol.
- AI must not generate close fields too early.

---

## 5.2 Review States

Review state became operational through `cis_review.py`:

```text
draft → checked
```

Future states remain:

```text
checked → approved → locked
```

Dashboard review surface is still missing.

---

## 5.3 Promotion Logic

- Draft records can become checked after human sanity review.
- Checked records should be promotable from dashboard in future.
- Automated systems must not promote to approved/locked.
- Locked records require versioning for correction.

---

## 5.4 Rejection Paths

- `cis_review.py` supports reject path in design.
- Failed validation can mark records as needing review.
- Future dashboard needs reject/deprecate actions.
- Handoff content can be considered invalid if stale and must be regenerated.

---

## 5.5 Trust Enforcement

- Knowledge records must be project-linked and review-state tagged.
- Handoff must reflect latest session state.
- ADR supersession must be visible and ordered correctly.
- Runtime scripts must be recoverable through git.
- Session close cannot rely on memory or terminal-only commands.

---

## 5.6 Hallucination Controls

Emergent controls:

- Corrections table provides human override mechanism.
- Review command writes accepted corrections only.
- Handoff protocol prevents AI-generated fields from becoming stale truth.
- Session Close Protocol documents AI responsibility.

---

## 5.7 Provenance Enforcement

- Records are linked to `project_id` and `project_title`.
- Handoff generated by dashboard stored in vault.
- `system_log.md` records session close actions.
- Git commits record runtime and document sync state.
- `cis-log insight` captures insight provenance by optional source record.

---

## 5.8 Validation Contracts

New validation demands:

- Dashboard close must verify all sync targets exist.
- ADR sort must parse decision number, not insertion ID.
- Runtime server version must be restarted after file replacement.
- Session close fields must be final, not interim.
- Handoff package requirements must be explicit.

---

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## 6.1 Knowledge Formation Logic

The session confirms that knowledge formation is not complete until records are:

1. extracted
2. normalized
3. reviewed
4. linked to project
5. mirrored/versioned
6. available to dashboard/future agents

The Weird War Tales record moved from loose source artifact toward project-linked checked knowledge.

---

## 6.2 Retrieval Structure

Retrieval depends on:

- project linkage
- record status
- canonical JSON
- markdown mirror
- future vector index
- task roadmap for adding retrieval later

The vector index remains a future task.

---

## 6.3 Indexing Implications

- `knowledge_records/` must be synced to vault.
- Record families need deterministic storage.
- Unexpected folders inside knowledge records root were noticed and may require cleanup/governance.
- Future indexes/embeddings should not become accidental unmanaged folders.

---

## 6.4 Normalization Rules

- Full JSON remains canonical.
- Markdown mirror exists for human readability.
- Project fields (`project_id`, `project_title`) must be injected into records when linked.
- Review updates status but do not necessarily create new content versions.

---

## 6.5 Ontology/Spine Implications

The session reinforces an emerging spine:

```text
Project → Source → Manifest → Knowledge Record → Review State → Task / Insight / Handoff
```

Dashboard project routing makes this spine visible.

---

## 6.6 Chunking Logic

Chunking/vector retrieval remains unresolved. However, the task table now contains a future vector index/retrieval item, meaning retrieval expansion is acknowledged but not yet implemented.

---

## 6.7 Reinforcement Behavior

Reinforcement appears in three forms:

- Human corrections applied to records.
- User feedback about dashboard confusion generates tasks.
- Handoff failures update protocol.

Accepted outcomes become future operating rules.

---

## 6.8 Project Linkage

Project linkage is now mandatory for meaningful dashboard context. Existing records must be linked, and future pipeline intake must automatically associate sources with the active project.

---

## 6.9 Stabilization Loops

- Review command stabilizes records.
- Task table stabilizes roadmap.
- Session close stabilizes continuity.
- ADR regeneration stabilizes decisions.
- Protocol stabilizes assistant behavior.

---

# 7. APPLICATION-LAYER IMPLICATIONS

## 7.1 Workbench Requirements

The dashboard must evolve into a workbench that supports:

- project launcher
- project workspace
- source/pipeline panel
- knowledge panel
- task panel
- session start/close panel
- capture flyout
- future review controls
- future decision logging
- future DAM/project management

---

## 7.2 Interface Panels

### Built or emerging

- System Overview / Project Overview
- Project Launcher
- Pipeline
- Knowledge Base
- Tasks
- Insights/Capture
- Session

### Required next

- Decision logging / ADR panel
- Review trigger panel/control
- Record promotion controls
- Log viewer
- Markdown mirror viewer
- DAM panel
- Project management panel

---

## 7.3 Operator Actions

The dashboard must let a creative non-coder:

- start session (`cis-start` button)
- select project
- see current WIAS progress
- view tasks in priority order
- capture insight/correction/observation
- run known commands by button
- close session and sync all data stores
- eventually log decisions and review records

---

## 7.4 Runtime Visibility Needs

The session exposed needs for:

- visible sync step log
- visible DB updates
- visible git status
- visible handoff file path/content
- visible task count
- visible dashboard server/runtime version state
- visible logs panel

---

## 7.5 Workflow Exposure

The dashboard should not only show data; it must expose the workflow sequence:

```text
Session Start → Project Selection → Active Work → Capture/Tasks/Pipeline → Review → Session Close → Handoff
```

---

## 7.6 Project-Centered Interaction

The application must open into a project launcher and route into project-scoped workspaces. Every panel must inherit project context from the route. This prepares the app for DAM and project management.

---

## 7.7 Application/Runtime Bridges

Current bridges:

- Flask backend serves project data.
- React frontend renders project/task/session views.
- Dashboard session close executes backend sync.
- Dashboard reads DB-backed task list.

Missing bridges:

- Dashboard → decision logging.
- Dashboard → review command.
- Dashboard → active project pipeline intake.
- Dashboard → knowledge promotion.
- Dashboard → logs.
- Dashboard → handoff package builder.

---

# 8. FEEDBACK LOOP DISCOVERIES

## 8.1 Reinforcement Loops

```text
AI/system output → human detects issue → task/protocol/code update → future session improves
```

Examples:

- Stale handoff → Session Close Protocol update.
- Dashboard confusion → session panel UI tasks.
- Missing version control → runtime_scripts mirror.

---

## 8.2 Correction Loops

```text
corrections table → cis_review.py → accepted corrections → record JSON → manifest/session log
```

This is the first explicit correction-to-knowledge loop.

---

## 8.3 Governance Loops

```text
DB decisions → ADRs.md regeneration → handoff/dashboard display → discrepancy found → ordering rule fixed
```

Governance becomes executable and self-correcting.

---

## 8.4 Retrieval-Improvement Loops

Not yet implemented, but task roadmap includes vector index and retrieval. Project-linked checked records are prerequisites.

---

## 8.5 Archive-Learning Loops

The real source record exposed path assumptions and review requirements. Future archive processing must let real materials reveal schema/runtime gaps.

---

## 8.6 Continuity/Memory Loops

```text
session work → DB + docs + system_log + handoff + git → next session cis-start + handoff package
```

This loop moved from manual to dashboard-assisted.

---

## 8.7 Project-Output Feedback Loops

CIS build outputs—scripts, dashboard files, protocols, project objects—are now treated as project artifacts that feed the system back into itself.

---

# 9. UNRESOLVED GAPS + MISSING LAYERS

## 9.1 Missing Runtime Bridges

- Dashboard decision logging form.
- Dashboard trigger for `cis_review.py`.
- Dashboard pipeline source → active project auto-link.
- Knowledge panel promotion controls.
- Markdown mirror viewer.
- Pipeline log viewer.
- Session start output updating dashboard state.
- Handoff package builder with required attachments.

---

## 9.2 Undefined Objects

- Capture record schema remains minimal and provisional.
- Stage progress schema not fully stabilized.
- Handoff package object not yet formalized.
- Sync result object not formalized.
- Project thumbnail object/location not defined.
- DAM asset object not defined.
- Project management milestone object not defined.

---

## 9.3 Unstable Schemas

- Tasks table exists but may need status expansion.
- Insights/capture schema minimal; future categories unknown.
- Session close fields depend on free text.
- `system_log.md` format is provisional.
- Handoff filename by date risks collision.
- Knowledge record root contains unexpected folders; storage schema needs cleanup.

---

## 9.4 Unresolved Orchestration

- Dashboard actions are not yet queued through a formal execution queue.
- Known commands execute or are planned ad hoc.
- Orchestrator role does not yet populate tasks.
- No automatic session summary generation exists.
- No automatic detection of “work continued after close fields generated” exists.

---

## 9.5 Unresolved Routing

- Pipeline intake does not inherit selected project.
- Model/intelligence routing not active in dashboard.
- Task execution routing is command-string based, not governed job-based.
- Start/close session actions are visually confusing in UI.

---

## 9.6 Missing Governance

- Dashboard-generated ADRs not yet implemented.
- ADRs.md regeneration must be verified after sort patch.
- Session Close Protocol must be included in handoff package.
- STATE/MEMORY regeneration was identified but deferred.
- Pipeline-wide system_log writing deferred.

---

## 9.7 Missing Validation Layers

- Session close should validate current backend version or server restart status.
- Handoff content should strip pasted labels.
- Session close should warn if content appears stale.
- Dashboard should verify git has committed actual updated runtime scripts.
- Task completion should have validation criteria.

---

## 9.8 Unresolved Application Surfaces

- Decision/ADR panel.
- Review panel.
- Log viewer.
- DAM.
- Project management.
- Project thumbnails.
- Expandable session close fields.
- Clear start/close session separation.

---

## 9.9 Unresolved Storage Rules

- Whether `/mnt/projects/cis/logs/system_log.md` is canonical or mirrored into vault.
- Whether DB snapshots should ever be versioned.
- How to manage multiple same-day handoffs.
- How to keep runtime canonical code and vault mirrors from drifting.
- How to clean unexpected knowledge_records subfolders.

---

# 10. BUILD-PLAN IMPLICATIONS

## 10.1 Foundational Prerequisites

Before further dashboard expansion:

1. Confirm session close uses latest backend.
2. Fix close-field label stripping.
3. Confirm ADR sort in generated `ADRs.md`.
4. Confirm Session Close Protocol is in handoff package.
5. Add UI tasks for session panel clarity.

---

## 10.2 Blocked Layers

### Blocked until dashboard actions are wired

- Decision/ADR governance through GUI.
- Review/promotion through GUI.
- Pipeline-as-project workflow.
- Log observability.

### Blocked until project context is enforced

- DAM.
- Project management.
- Teacher/Librarian reuse.
- Project-specific retrieval.

---

## 10.3 Sequencing Implications

Recommended next build order:

1. Fix session panel UX and close-field handling.
2. Add dashboard decision logging.
3. Auto-update ADRs through dashboard decision logging.
4. Add review trigger to pipeline/knowledge panel.
5. Wire pipeline source intake to active project.
6. Add record promotion buttons.
7. Add log viewer.
8. Add markdown mirror viewer.
9. Add handoff package builder.
10. Begin retrieval/vector indexing.

---

## 10.4 Runtime-First Requirements

- Dashboard must execute the same commands that terminal workflows previously used.
- Runtime scripts must remain canonical or mirrored reliably.
- Session close must not leave unsynced state outside git.
- Start/close rituals must be operator-safe.

---

## 10.5 Governance-First Requirements

- Decisions must enter DB and regenerate ADRs.
- Handoff must reflect final session state only.
- Protocol must govern assistant behavior.
- Human approval gates remain intact for review/promotion.

---

## 10.6 Execution-First Requirements

- Existing commands should be surfaced before inventing new UI abstractions.
- Known terminal steps should become dashboard actions.
- Task panel should prioritize friction-reduction and continuity-risk tasks.

---

## 10.7 Application Dependencies

- Flask + React CDN foundation chosen to avoid rebuild.
- URL routing chosen for project-scoped future panels.
- Project launcher chosen as first screen.
- Dashboard monolith may later require modularization.

---

# 11. EXTRACTED CANONICAL OBJECTS

## 11.1 Project Object: `PROJECT__CIS__BUILD__V1`

- **Purpose**: Formal container for CIS infrastructure/application build as the first CIS project.
- **Lifecycle**: created → active → future completed/archived.
- **Authority source**: Project JSON; user confirmed WEB domain.
- **Related objects**: knowledge records, tasks, runtime scripts, dashboard panels, session handoffs.
- **States**: active; WIAS stage `web` active; future stage progress.
- **Storage implications**: `/mnt/projects/cis/projects/PROJECT__CIS__BUILD__V1/`, mirrored to vault `projects/`.

---

## 11.2 Knowledge Record

- **Purpose**: Canonical structured knowledge output.
- **Lifecycle**: draft → checked → approved → locked / deprecated.
- **Authority source**: canonical JSON; markdown mirror for human reading.
- **Related objects**: source manifest, corrections, project, review actions.
- **States**: draft/checked observed; approved/locked/deprecated future.
- **Storage implications**: `/mnt/projects/cis/knowledge/records/<record_family>/`, mirrored to vault `knowledge_records/`.

---

## 11.3 Source Manifest

- **Purpose**: Intake and processing control object for a source.
- **Lifecycle**: arrived → classified → preprocessed → extracted → draft/checked.
- **Authority source**: manifest JSON.
- **Related objects**: source file, record JSON, review command.
- **States**: observed multiple status entries; status handling needs clarification.
- **Storage implications**: actual path discovered as `/mnt/projects/cis/ingest/processing/<lowercase_source_id>/manifest.json`.

---

## 11.4 Correction

- **Purpose**: Logged human or system correction against a record field.
- **Lifecycle**: logged → reviewed → accepted/skipped/edited → applied to record if accepted.
- **Authority source**: corrections table; human approval.
- **Related objects**: knowledge record, `cis_review.py`.
- **States**: pending/accepted/skipped/edited implied.
- **Storage implications**: SQLite `corrections` table.

---

## 11.5 Insight

- **Purpose**: Captures architectural or operational observations.
- **Lifecycle**: captured → stored → future review/use.
- **Authority source**: `cis-log insight` and future dashboard capture.
- **Related objects**: optional source record, tasks, handoff.
- **States**: no mature review states yet.
- **Storage implications**: SQLite `insights` table auto-created by `cis_log.py`.

---

## 11.6 Task

- **Purpose**: Operator-facing pre-intelligence roadmap item.
- **Lifecycle**: open → completed; future running/failed/blocked likely needed.
- **Authority source**: DB task table; seeded from known gaps and session context.
- **Related objects**: project, phase, command, dashboard task panel.
- **States**: open/completed.
- **Storage implications**: SQLite `tasks` table with project linkage.

---

## 11.7 Session Log Entry

- **Purpose**: Structured record of completed session activity.
- **Lifecycle**: inserted at review or session close.
- **Authority source**: SQLite `session_log`.
- **Related objects**: handoff, system_log, git commit.
- **States**: append-only.
- **Storage implications**: requires `created_at` field.

---

## 11.8 Decision / ADR Entry

- **Purpose**: Architecture decision record stored in DB and represented in `ADRs.md`.
- **Lifecycle**: logged → regenerated into markdown → future superseded if needed.
- **Authority source**: decisions table; `ADRs.md` derived.
- **Related objects**: handoff, dashboard ADR panel future.
- **States**: locked; superseded marker required.
- **Storage implications**: SQLite decisions table + generated vault markdown.

---

## 11.9 Session Close Protocol

- **Purpose**: Governs assistant duty and timing for session close fields and handoff package.
- **Lifecycle**: created → revised → attached to handoff package.
- **Authority source**: markdown protocol document.
- **Related objects**: handoff, cis-start output, dashboard close fields.
- **States**: v1/v1.1 implied.
- **Storage implications**: vault Phase_PD and runtime copy.

---

## 11.10 Handoff Document

- **Purpose**: Session-specific continuity artifact.
- **Lifecycle**: generated at close → attached to next session → superseded by next handoff.
- **Authority source**: dashboard session close output.
- **Related objects**: session_log, system_log, git commit, protocol.
- **States**: current/stale; date-based naming collision unresolved.
- **Storage implications**: `/mnt/projects/cis/docs/CIS_Creative_Intelligence_System_v1/Phase_PD/CIS_Handoff_<date>.md`.

---

## 11.11 system_log.md Entry

- **Purpose**: Append-only operational action log.
- **Lifecycle**: action occurs → entry appended.
- **Authority source**: runtime logging.
- **Related objects**: session close, future pipeline steps.
- **States**: append-only.
- **Storage implications**: `/mnt/projects/cis/logs/system_log.md`; pipeline-wide logging deferred.

---

## 11.12 Runtime Script Mirror

- **Purpose**: Git-tracked backup of execution layer scripts.
- **Lifecycle**: runtime script changes → sync to vault mirror → git commit.
- **Authority source**: canonical runtime files, mirrored for version control.
- **Related objects**: dashboard, pipeline commands, memory scripts.
- **States**: synced/unsynced.
- **Storage implications**: `runtime_scripts/memory/` and `runtime_scripts/runtime/` in vault.

---

# 12. ARCHITECTURAL DELTA SUMMARY

After this file, CIS is no longer only a validated execution pipeline plus conceptual application plan. It becomes an early operator-facing system with a real project object, project-scoped dashboard architecture, review command, insight capture mechanism, task-roadmap database, runtime script versioning, session-close synchronization, system log initiation, and explicit session-close protocol.

The most important new understanding is:

**CIS continuity is itself a runtime workflow.**

The system can fail even when individual commands work if handoff, DB, markdown docs, runtime scripts, project records, knowledge records, and git are not synchronized together. The session exposed that the Application Layer cannot simply sit on top of the system; it must actively coordinate the system’s continuity rituals.

The second major understanding is:

**CIS must build itself as its first valid project.**

The application cannot be tested against loose sources or abstract states. It needs a project container, project-linked records, project-scoped routes, WIAS progress, and task context. This converts the CIS build from external development activity into a formal WEB-domain CIS project.

The third major understanding is:

**The human is still the API at session boundaries.**

Even with a working dashboard close button, stale handoff content occurred because close fields were generated too early. This means automation is not only about commands; it is about removing cognitive timing burdens. The Session Close Protocol emerged to govern that gap until future orchestrator behavior can generate and validate session close content automatically.

The fourth major understanding is:

**The dashboard is becoming a producer/operator companion.**

Its role is not merely to display state. It must reduce cognitive load for a creative operator by presenting the current project, the roadmap, the next action, capture tools, runtime controls, and session start/close rituals. The task panel is the pre-intelligence orchestration bridge; later, agents will populate and operate through the same surface.

The fifth major understanding is:

**Project routing is foundational to all future application panels.**

DAM, project management, knowledge retrieval, review, and workflow panels must all be scoped to a selected project. The correct application foundation is a launcher plus URL-routed project workspace, not a single global dashboard.

The practical build consequence is:

**Before expanding into richer creative features, CIS must finish wiring the immediate operator-continuity surfaces: session close correctness, decision/ADR logging, review execution from dashboard, pipeline-project linkage, record promotion, log visibility, and handoff package clarity.**

---

## Topology-Ready Node/Edge Sketch

```text
User / Operator
  → Dashboard Project Launcher
    → Project Workspace (/project/<project_id>)
      → Session Panel
        → cis-start output
        → Session Close Endpoint
          → session_log DB
          → decisions DB → ADRs.md
          → knowledge records sync
          → projects sync
          → runtime_scripts sync
          → system_log.md
          → handoff markdown
          → git commit/push
      → Tasks Panel
        → tasks DB
        → future executable commands
      → Capture Flyout
        → insights/captures DB
      → Pipeline Panel
        → intake/classify/preprocess/extract/normalize scripts
        → future active project linkage
      → Knowledge Panel
        → knowledge_record JSON
        → review state
        → future promotion controls
      → Future DAM / Project Management
        → project-scoped assets/tasks/milestones

cis_review.py
  → source manifest
  → draft knowledge_record
  → corrections DB
  → human review
  → record JSON update
  → markdown mirror
  → manifest checked
  → session_log

CIS Build Project
  → PROJECT__CIS__BUILD__V1
  → active stage: WEB
  → linked Weird War Tales record
  → seeded tasks
  → dashboard as first project surface
```
