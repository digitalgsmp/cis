# CIS_Chat_2026-04_008 — Extraction Analysis

Source file: `CIS_Chat_2026-04_008.md`  
Extraction mode: implementation-grade architectural topology extraction  
Output purpose: topology atlas / dependency map / runtime build-plan merge input  
Reference image: `example_CIS_Chat_2026-04_004_topo03.png`

---

# 1. CORE ARCHITECTURAL DISCOVERIES

## Discovery Name: Monolithic Dashboard Split into Modular Backend Runtime

- **Architectural Significance**
  - CIS application moved from a fragile two-file pattern into a modular Flask backend structure.
  - The previous backend `cis_dashboard-2.py` / `cis_dashboard.py` model was identified as a scalability risk because routes, helpers, database logic, and startup behavior were contained in one large file.
  - The new structure creates an explicit runtime backend topology:
    - `app.py` = entry point / Flask initialization / blueprint registration
    - `config.py` = path and constants authority
    - `api/*` = domain-specific route modules
    - `db/*` = database connection and CIS_LIVE serialization
    - `utils/*` = reusable helpers and project utilities

- **Affected Layers**
  - Application Layer
  - Execution Layer
  - Runtime Layer
  - Governance / Continuity Layer

- **Dependency Impact**
  - Frontend development is now dependent on a stable modular backend contract rather than a monolithic Python file.
  - CIS_LIVE and dashboard panels depend on `api/live.py`, `db/live_db.py`, and `cis_dashboard.html` alignment.
  - Deployment depends on file placement in `/mnt/projects/cis/runtime/` and correct `app.py` startup.

- **Build Impact**
  - Backend refactor must precede deeper frontend redesign.
  - `app.py` becomes the canonical launch target.
  - Future API expansion should add domain modules rather than expanding a monolith.

- **Runtime Impact**
  - Runtime starts via:
    - `python3 /mnt/projects/cis/runtime/app.py`
  - Dashboard serves through Flask at:
    - `http://127.0.0.1:5000`
    - `http://192.168.1.15:5000`
  - Desktop launcher must point to `app.py`, not the archived monolith.

---

## Discovery Name: CIS_LIVE Becomes a Runtime Collaboration Tool, Not a Static Note

- **Architectural Significance**
  - CIS_LIVE evolved from a markdown status file into an active multi-frontier-model coordination surface.
  - Its purpose is to allow Claude, Gemini, and ChatGPT to participate in a structured reasoning loop during development.
  - CIS_LIVE is prioritized because frontier model collaboration is being used to bootstrap weaker local intelligence capability.

- **Affected Layers**
  - Intelligence Layer
  - Application Layer
  - Execution Layer
  - Knowledge / Memory Layer
  - Governance Layer

- **Dependency Impact**
  - Local development depends on manual frontier model response collection until auto-fetch exists.
  - CIS_LIVE depends on:
    - session object
    - round object
    - model attribution fields
    - markdown serialization
    - push-to-live deployment path
  - Frontier reasoning output must be written into a durable shared artifact before it can inform downstream development.

- **Build Impact**
  - The Live panel becomes a priority application surface.
  - `api/live.py` and `db/live_db.py` become critical backend modules.
  - UI must support a simple 3–4 step operator sequence rather than a loose form.

- **Runtime Impact**
  - User creates a problem session.
  - User writes a question.
  - System saves the question and pushes it to the live site.
  - Frontier models read the shared CIS_LIVE context and respond.
  - User pastes responses into attribution fields.
  - System logs the round and pushes the updated thread.

---

## Discovery Name: Application Surface Must Reduce Cognitive Load, Not Merely Expose Features

- **Architectural Significance**
  - A functional dashboard can still fail if the operator cannot remember the order of actions.
  - The Live panel exposed a usability gap: buttons existed, but their labels and placement did not encode the runtime sequence.
  - The application surface must make workflow order visible.

- **Affected Layers**
  - Application Layer
  - Operator Model
  - Execution Layer
  - Automation Reduction Layer

- **Dependency Impact**
  - UI design now depends on explicit action sequencing.
  - Runtime action labels must distinguish between:
    - saving a question
    - pushing to live site
    - logging responses
    - pushing updated thread
  - A button that only pushes existing DB state is insufficient if the new question is not yet saved.

- **Build Impact**
  - CIS_LIVE UI must be redesigned around a numbered sequence.
  - “Push” must become semantically split into `Save Question + Push` and `Log Responses + Push`.
  - The problem form belongs in a dedicated right-sidebar tab, not buried at the bottom of the thread.

- **Runtime Impact**
  - Step 2 now must save a partial round before pushing.
  - Step 4 must update/log responses and push again.
  - Models see the current question before responses exist.

---

## Discovery Name: Stream Deck Layout Becomes the Control-Surface Pattern

- **Architectural Significance**
  - The main dashboard is no longer just a vertical sidebar plus content panel.
  - It evolves into a three-zone control surface:
    - left: Stream Deck-style operator controls
    - center: active workspace / project panel / Live thread
    - right: Intelligence sidebar
  - This is a concrete UI manifestation of CIS as a studio operating system.

- **Affected Layers**
  - Application Layer
  - Workflow Layer
  - Intelligence Layer
  - Tool Layer

- **Dependency Impact**
  - Dashboard navigation depends on grouped operator actions rather than only icon tabs.
  - Tool availability and screen space must be balanced through collapsible panels.
  - Smaller displays require collapse behavior as a first-class UI state.

- **Build Impact**
  - The left column must be collapsible between full Stream Deck view and compact icon strip.
  - The right Intelligence sidebar must be independently collapsible.
  - Existing working panels remain intact while the shell evolves around them.

- **Runtime Impact**
  - Operator can access navigation, pipeline actions, knowledge actions, WIAS filters, and session controls from a persistent left control surface.
  - Operator can collapse control zones when screen space is constrained.

---

## Discovery Name: Cloudflare / Proxmox / LXC Static Site Path Becomes Runtime Distribution Bridge

- **Architectural Significance**
  - CIS_LIVE distribution is not a GitHub raw URL problem.
  - The actual deployment path is:
    - Ubuntu VM writes `CIS_LIVE.md`
    - SCP to Proxmox host `/mnt/cis-live/CIS_LIVE.md`
    - bind mount into LXC 101 at `/data/CIS_LIVE.md`
    - Flask static service exposes root URL at `creative-intelligence-system.com`
  - This creates a concrete remote-read bridge for frontier model collaboration.

- **Affected Layers**
  - Runtime Layer
  - Application Layer
  - Infrastructure Layer
  - Intelligence Layer

- **Dependency Impact**
  - Live site update depends on SSH/SCP key validity.
  - Cloudflare tunnel does not run on the Ubuntu VM; it is served through a separate Proxmox/LXC route.
  - The public URL root, not `/CIS_LIVE.md`, is the canonical readable endpoint.

- **Build Impact**
  - `api/live.py` push logic must perform local write, Git push, and SCP to Proxmox.
  - `db/live_db.py` / URL logic must copy the correct public root URL.
  - UI must label the URL as the Live Site URL rather than GitHub raw.

- **Runtime Impact**
  - Successful push status means live site updated through SCP.
  - GitHub push may succeed while live-site SCP fails; these states must be distinguishable.

---

## Discovery Name: Frontend Monolith Is Now a Recognized Runtime Risk

- **Architectural Significance**
  - The backend refactor solved one monolith, but `cis_dashboard.html` remains a large single-file frontend.
  - The transcript identifies that frontend modularization is possible using native JavaScript modules while retaining CDN React / no build step.

- **Affected Layers**
  - Application Layer
  - Build / Maintainability Layer
  - Operator Continuity Layer

- **Dependency Impact**
  - UI expansion depends on either careful single-file patching or eventual modularization.
  - Complex components such as Live panel, Stream Deck, and Intelligence Sidebar increase fragility if kept in one file.

- **Build Impact**
  - Frontend modularization should follow functional stabilization of CIS_LIVE.
  - Proposed modules:
    - `frontend/index.html`
    - `frontend/api.js`
    - `frontend/router.js`
    - `frontend/components/*`
    - `frontend/panels/*`

- **Runtime Impact**
  - Until modularized, one syntax error can break the full UI.
  - UI patches should be incremental and verified through browser refresh.

---

# 2. TOPOLOGY MUTATIONS

## 2.1 Backend Runtime Topology Mutation

Previous topology:

```text
cis_dashboard.py / cis_dashboard-2.py
    contains paths + helpers + DB + routes + app startup
```

New topology:

```text
/mnt/projects/cis/runtime/
├── app.py
├── config.py
├── api/
│   ├── system.py
│   ├── projects.py
│   ├── session.py
│   ├── tasks.py
│   ├── pipeline.py
│   ├── records.py
│   ├── captures.py
│   ├── decisions.py
│   ├── extraction_runs.py
│   └── live.py
├── db/
│   ├── connection.py
│   └── live_db.py
└── utils/
    ├── helpers.py
    └── project_helpers.py
```

Topology mutation:

```text
Monolith
→ Modular Flask runtime
→ Domain-specific API surfaces
→ Stable backend contract for frontend redesign
```

---

## 2.2 Application Surface Mutation

Previous topology:

```text
vertical sidebar → full-width panel
```

New topology:

```text
collapsible Stream Deck control surface
→ central workspace
→ collapsible Intelligence sidebar
```

Sub-structure:

```text
Left Control Surface
├── Navigate keys
├── Pipeline keys
├── Knowledge keys
├── WIAS keys
└── Session keys

Center Workspace
├── Dashboard panels
├── Project views
├── Live thread
└── Records / Pipeline / Decisions views

Right Intelligence Sidebar
├── LOCAL tab
├── REMOTE tab
├── AGENT tab
└── LIVE / problem form tab
```

---

## 2.3 CIS_LIVE Runtime Bridge Mutation

Previous assumption:

```text
CIS_LIVE.md pushed to GitHub raw URL
```

Corrected runtime bridge:

```text
Dashboard Live panel
→ api/live.py
→ live_db.py serialization
→ local CIS_LIVE.md
→ git commit/push
→ SCP to Proxmox /mnt/cis-live/CIS_LIVE.md
→ LXC bind mount /data/CIS_LIVE.md
→ Flask static root
→ https://creative-intelligence-system.com
```

Topology mutation:

```text
local-only markdown
→ public live reasoning document
→ multi-model context distribution bridge
```

---

## 2.4 CIS_LIVE Workflow Mutation

Previous workflow ambiguity:

```text
type question → push? → paste responses? → log? → push?
```

New explicit sequence:

```text
1. Type question
2. Save Question + Push
3. Copy URL / send to frontier models
4. Paste model responses
5. Log Responses + Push
6. Repeat next round
```

Critical mutation:

- A question must exist as a saved partial round before it can be pushed.
- Responses are later attached to that round or logged into the latest round.
- Push cannot only serialize already-complete rounds.

---

## 2.5 Governance / Memory Mutation

The deployment process introduced a housekeeping layer:

```text
cis_deploy.sh
→ create archive + mockup folders
→ unzip backend
→ archive old monolith
→ move UI mockups
→ append memory additions
→ copy memory additions to vault
→ verify expected file structure
→ syntax-check app.py
→ git commit/push
```

This mutates deployment from manual file copying into a governed housekeeping operation.

---

# 3. DEPENDENCY DISCOVERIES

## 3.1 Hidden Prerequisite: Backend Contract Before Frontend Redesign

- Frontend redesign is unsafe until backend endpoints and runtime file structure are stable.
- `app.py` and blueprint modules must exist before UI wiring.
- Live panel integration depends on `api/live.py` and `db/live_db.py` being present.

## 3.2 Hidden Prerequisite: Deployment Housekeeping Before Continued Development

- User was lost because generated artifacts, mockups, old monoliths, and new backend files coexisted in the runtime directory.
- Development cannot proceed reliably until runtime folder is cleaned and verified.

## 3.3 Hidden Prerequisite: Live Site Push Must Save Unsaved UI State

- The push operation cannot only serialize database state.
- If the question is typed in UI but not yet saved, the live site cannot show it.
- Step 2 must persist a partial round first.

## 3.4 Hidden Prerequisite: Public URL Target Must Match Real Serving Topology

- GitHub raw URL and Cloudflare URL are separate surfaces.
- `/CIS_LIVE.md` path returning 404 did not mean CIS_LIVE failed; root route served the live file.
- Public live URL must be root if Flask LXC service only serves `/`.

## 3.5 Hidden Prerequisite: Operator Memory Is Not Enough

- User could not remember previous ADR/memory capture operations.
- Session reorientation document emerged as a continuity object.
- The dashboard must reduce mental load by encoding sequence into UI.

## 3.6 Hidden Prerequisite: Desktop Launcher Must Track Runtime Refactor

- Old desktop button launched `cis_dashboard.py`.
- Refactored runtime requires launcher update to `app.py`.
- Launchers are part of runtime topology, not cosmetic extras.

## 3.7 Sequencing Constraint: CIS_LIVE First, Broader App Later

- CIS_LIVE was prioritized to coordinate frontier models for local intelligence buildout.
- Broader Stream Deck / dashboard work should not obscure the Live proof loop.

## 3.8 Circular Dependency Exposed: Need Frontier Models to Build Local Intelligence

- Local intelligence is the intended future capability.
- But frontier manual collaboration is needed to reason through local intelligence implementation.
- CIS_LIVE becomes the bridge resolving this circular dependency.

## 3.9 Runtime Blocker: Cloudflared Not Running on Ubuntu VM

- Debugging initially assumed Cloudflare tunnel lived on the VM.
- No `cloudflared` process, service, binary, or config existed on the VM.
- Actual path used Proxmox/LXC, requiring SCP rather than local tunnel reconfiguration.

## 3.10 Orchestration Bottleneck: Human Copy/Paste Between Model Tabs

- Manual paste is currently the realistic path.
- Auto-fetch from model share URLs was discussed but rejected as not currently reliable.
- This remains a human-middleware bottleneck until API or browser automation exists.

# 4. EXECUTION-LAYER IMPLICATIONS

## 4.1 Commands

### Launch Runtime

```bash
python3 /mnt/projects/cis/runtime/app.py
```

### Desktop Launcher Target

```desktop
Exec=gnome-terminal -- bash -c "if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then echo 'CIS Dashboard already running. Opening browser...'; xdg-open http://127.0.0.1:5000; else python3 /mnt/projects/cis/runtime/app.py & until curl -s http://127.0.0.1:5000 >/dev/null; do sleep 1; done; xdg-open http://127.0.0.1:5000; fi; exec bash"
```

### Deploy / Housekeeping

```bash
cd /mnt/projects/cis/runtime
bash cis_deploy.sh
```

### Manual SCP Test

```bash
echo "# test" > /tmp/test.md
scp -i ~/.ssh/cis_proxmox /tmp/test.md root@192.168.1.200:/mnt/cis-live/CIS_LIVE.md
```

---

## 4.2 Runtime States

### Backend Deployment States

```text
monolith_present
→ backend_zip_present
→ extracted
→ old_monolith_archived
→ modules_verified
→ syntax_checked
→ git_committed
→ runtime_ready
```

### Dashboard Runtime States

```text
not_running
→ port_check
→ app_started
→ flask_ready
→ browser_opened
→ api_routes_responding
```

### CIS_LIVE Session States

```text
no_session
→ session_created
→ question_drafted
→ question_saved_partial_round
→ live_site_pushed
→ models_responding
→ responses_pasted
→ responses_logged
→ updated_live_site_pushed
→ resolved
→ captured_to_knowledge / memory
```

### Cloudflare / Live Site States

```text
local_markdown_written
→ git_commit_attempted
→ github_pushed
→ scp_attempted
→ proxmox_file_updated
→ lxc_static_file_visible
→ public_url_current
```

Failure states:

```text
git_success_scp_fail
scp_fail
wrong_url_target
root_serves_file_but_path_404
```

---

## 4.3 Transitions

### CIS_LIVE Step 2 Transition

```text
question_text_in_ui
→ save partial round to DB
→ serialize CIS_LIVE.md
→ push to live site
→ copy URL for models
```

### CIS_LIVE Step 4 Transition

```text
model_responses_in_ui
→ attach/log responses
→ serialize updated thread
→ push to live site
→ models can read updated context
```

### Dashboard Layout Transition

```text
old_sidebar_open
→ Stream Deck expanded
→ Stream Deck collapsed
→ Intelligence sidebar open
→ Intelligence sidebar collapsed
```

---

## 4.4 Runtime Contracts

### Modular Backend Contract

- `app.py` must register all route modules.
- `config.py` owns paths and constants.
- API route code belongs in `api/*`.
- Database behavior belongs in `db/*`.
- Shared utilities belong in `utils/*`.

### Live Push Contract

A Live push must:

1. serialize current CIS_LIVE session state to markdown
2. write local output
3. commit / push to GitHub when applicable
4. SCP the markdown file to Proxmox
5. report whether live site update succeeded

### UI Sequence Contract

The operator-facing Live workflow must enforce:

```text
Question before responses.
Save before push.
Push before asking frontier models to respond.
Paste responses before log.
Log before updated push.
```

---

## 4.5 Validation Behavior

### Deployment Validation

- Verify required backend files exist.
- Syntax-check `app.py`.
- Confirm Flask route responses return 200.
- Confirm project, records, decisions, and live sessions load.

### Live Site Validation

- Confirm public URL returns content.
- Confirm root route serves file if `/CIS_LIVE.md` is not routed.
- Confirm SCP updates `/mnt/cis-live/CIS_LIVE.md`.
- Confirm GitHub push and live-site push are separately reported.

### UI Validation

- Confirm Stream Deck expanded and collapsed states work.
- Confirm Intelligence sidebar tabs render LOCAL / REMOTE / AGENT / LIVE.
- Confirm question form no longer duplicates in center bottom after moving to right sidebar.
- Confirm Step 2 updates CIS_LIVE before responses are entered.

---

## 4.6 Pass / Fail Structures

### Deployment PASS

```text
19/19 modular backend files verified
app.py syntax OK
Git commit pushed
Dashboard reachable at localhost:5000
API routes respond 200
```

### Deployment FAIL

```text
missing app.py
missing api/db/utils folders
old launcher still points to cis_dashboard.py
syntax check fails
port 5000 occupied by wrong process
```

### CIS_LIVE PASS

```text
question saved as partial round
live site shows current question
responses logged with model attribution
updated live site shows full thread
root URL readable by frontier models
```

### CIS_LIVE FAIL

```text
question exists only in UI state
push serializes old DB state only
copy URL points to GitHub raw instead of live site
SCP fails silently
user cannot identify next step
```

---

## 4.7 Retry / Escalation Logic

- If browser does not open automatically, manually open `http://127.0.0.1:5000`.
- If launcher opens old dashboard, update `.desktop` file to `app.py`.
- If live URL shows 404 at `/CIS_LIVE.md`, test root URL.
- If root URL shows old test text, inspect serving topology and SCP target.
- If SCP fails, verify SSH key and Proxmox path.
- If UI sequence confuses operator, simplify to numbered steps and relabel buttons.

# 5. GOVERNANCE + VALIDATION IMPLICATIONS

## 5.1 Authority Structures

### Human Authority

- Human decides whether CIS_LIVE flow is usable.
- Human identifies operator confusion as a system defect.
- Human controls final acceptance of UI sequence and build priority.

### Runtime Authority

- `app.py` is runtime entry authority.
- `config.py` is path/config authority.
- `api/live.py` is Live behavior authority.
- `db/live_db.py` is Live serialization / URL authority.

### Deployment Authority

- `cis_deploy.sh` becomes a temporary but important deployment authority for housekeeping.
- Git commit verifies deployment as recorded state.

---

## 5.2 Review States

### UI / Runtime Review States

```text
mockup
→ integrated
→ visually confirmed
→ functionally tested
→ operator-confusing
→ revised
→ operator-usable
```

### CIS_LIVE Round Review States

```text
question_draft
→ question_pushed
→ awaiting_model_responses
→ responses_collected
→ responses_logged
→ thread_pushed
→ resolved
```

### Deployment Review States

```text
unverified_files
→ file_structure_verified
→ syntax_verified
→ runtime_verified
→ committed
```

---

## 5.3 Promotion Logic

- Mockups are not promoted until wired to API endpoints.
- A UI layout is not promoted until operator confirms actual usability.
- CIS_LIVE thread content becomes useful only after it is pushed to the public live context.
- Memory additions should be appended to logs / vault before being treated as durable.

---

## 5.4 Rejection Paths

- Reject GitHub raw URL as Live URL when actual collaboration surface is Cloudflare root.
- Reject hidden bottom forms when operator must scroll to paste responses.
- Reject duplicated problem forms when sidebar tab owns the form.
- Reject push buttons that do not save unsaved question state.
- Reject frontend expansion if it breaks operator sequence or increases cognitive load.

---

## 5.5 Trust Enforcement

- Live site push must show whether SCP succeeded.
- Empty rounds should be skipped in serialization.
- Session numbering should stabilize Live thread readability.
- UI must distinguish between “question pushed” and “responses logged.”

---

## 5.6 Hallucination / Drift Controls

- Reorientation document prevents loss of application build context.
- Housekeeping script archives old files to prevent runtime ambiguity.
- Git commit creates durable trace after deployment.
- Explicit file structure prevents conceptual drift back into monolith.

---

## 5.7 Provenance Enforcement

CIS_LIVE records must preserve:

- session title
- round number
- user question
- model attribution
- response content
- resolved status
- live push path
- commit / deployment trace when available

---

## 5.8 Validation Contracts

Minimum validation needed after each patch:

```text
replace file
refresh browser
verify visual behavior
verify API behavior if backend changed
restart Flask if backend changed
push test if Live path changed
```

# 6. KNOWLEDGE-LAYER IMPLICATIONS

## 6.1 Knowledge Formation Logic

This transcript does not primarily build archive-derived knowledge records. It creates a reasoning-capture and development-support pathway.

New knowledge formation logic:

```text
frontier model discussion
→ CIS_LIVE session / rounds
→ resolved decision or implementation insight
→ memory additions / vault update / possible ADR
→ future local intelligence build guidance
```

## 6.2 Retrieval Structure

- CIS_LIVE sessions require retrieval by:
  - session title
  - session number
  - problem topic
  - model response source
  - resolved status
  - date
- Session numbering improves scanning and future retrieval.

## 6.3 Indexing Implications

Future indexing should treat CIS_LIVE as a structured object, not only markdown.

Required index fields:

- `live_session_id`
- `session_number`
- `title`
- `status`
- `round_count`
- `models_involved`
- `resolved_summary`
- `public_url`
- `created_at`
- `updated_at`

## 6.4 Normalization Rules

CIS_LIVE outputs should normalize into multiple downstream object types depending on content:

- ADR candidate
- session insight
- implementation task
- bug / conflict record
- reorientation update
- runtime decision
- knowledge record candidate

## 6.5 Ontology / Spine Implications

CIS_LIVE sits between Intelligence and Governance:

```text
Remote frontier reasoning
→ Live session object
→ resolved insight
→ governance / memory / task / ADR object
```

It is not a final knowledge record by default. It is a staging and reasoning surface.

## 6.6 Chunking Logic

CIS_LIVE markdown should chunk by:

- session
- round
- model response
- resolution

Avoid chunking across model attribution boundaries because model source matters.

## 6.7 Reinforcement Behavior

- User identifies clumsy sequence.
- UI is revised to encode steps.
- Future operator behavior improves because sequence is visible.
- Accepted UI sequence becomes precedent for other CIS workflows.

## 6.8 Project Linkage

CIS_LIVE sessions should link to:

- active project (`PROJECT__CIS__BUILD__V1`)
- current build target
- relevant runtime module
- associated ADR / memory record when promoted

## 6.9 Stabilization Loops

```text
operator uses Live panel
→ friction appears
→ UI sequence revised
→ push logic fixed
→ operator retests
→ accepted behavior stabilizes
```

# 7. APPLICATION-LAYER IMPLICATIONS

## 7.1 Workbench Requirements

The dashboard must support:

- modular backend runtime access
- Stream Deck-style operator controls
- central workspace panels
- Intelligence sidebar
- CIS_LIVE problem form
- session thread reading
- model attribution fields
- push-to-live controls
- live URL copy
- collapsible layout zones

## 7.2 Interface Panels

Extracted panel set:

### Left Stream Deck

- Navigate
- Pipeline
- Knowledge
- WIAS
- Session

### Center Workspace

- System
- Session
- Tasks
- Pipeline
- Knowledge
- Insights
- ADRs / Decisions
- Live thread

### Right Intelligence Sidebar

- LOCAL
- REMOTE
- AGENT
- LIVE / problem form

## 7.3 Operator Actions

Critical operator actions:

- launch dashboard without terminal
- create/open Live session
- type problem/question
- save question as partial round
- push to live site
- copy public URL
- paste model responses
- log responses
- push updated thread
- resolve session
- collapse side panels

## 7.4 Runtime Visibility Needs

The UI must expose:

- whether dashboard is running
- whether app.py is active
- whether live site push succeeded
- whether Git push succeeded separately
- whether SCP succeeded
- which Live session is active
- which round is next
- whether form content is saved or only local UI state

## 7.5 Workflow Exposure

CIS_LIVE workflow must be displayed as a numbered sequence:

```text
① Type question
② Save Question + Push
③ Paste model responses
④ Log Responses + Push
```

## 7.6 Project-Centered Interaction

CIS_LIVE is used in the context of CIS application development and local intelligence activation. It should eventually attach to project context automatically.

## 7.7 Application / Runtime Bridges

Bridges exposed by this transcript:

- Dashboard UI → Flask API
- Flask API → SQLite / JSON / markdown serialization
- Live panel → CIS_LIVE.md
- Runtime VM → Proxmox host via SCP
- Proxmox host → LXC bind mount
- LXC Flask static service → Cloudflare public URL
- Desktop launcher → `app.py`

# 8. FEEDBACK LOOP DISCOVERIES

## 8.1 Reinforcement Loop: UI Friction → UI Redesign

```text
operator confused by sequence
→ articulates failed mental model
→ assistant extracts real workflow
→ UI relabeled and restructured
→ workflow becomes executable
```

## 8.2 Correction Loop: Wrong URL → Correct Runtime Bridge

```text
GitHub raw URL assumed
→ operator rejects URL
→ Cloudflare target investigated
→ tunnel location corrected
→ SCP bridge implemented
→ root URL accepted
```

## 8.3 Governance Loop: Runtime Folder Confusion → Deploy Script

```text
mixed runtime files
→ user lost
→ housekeeping plan
→ deploy script
→ verified modular files
→ git commit
→ runtime stabilized
```

## 8.4 Retrieval-Improvement Loop: Session Numbering

```text
un-numbered sessions difficult to read
→ numbering added
→ session list / markdown improves scanability
```

## 8.5 Continuity / Memory Loop: Reorientation Document

```text
user cannot remember where work left off
→ reorientation doc created
→ future session start burden reduced
```

## 8.6 Project-Output Feedback Loop

CIS_LIVE outputs are not final creative outputs, but they produce implementation insights. These should feed:

- memory additions
- ADR candidates
- task list updates
- dashboard UX changes
- local intelligence build plan

## 8.7 Archive-Learning Loop Not Primary Here

Archive-learning remains background context. This transcript is about application runtime and collaborative intelligence tooling, not direct 10TB archive ingestion.

# 9. UNRESOLVED GAPS + MISSING LAYERS

## 9.1 Missing Runtime Bridge: Frontend Modularization

- Backend modularization is complete.
- Frontend remains monolithic.
- Need modular frontend plan after CIS_LIVE stabilizes.

## 9.2 Missing Runtime Bridge: Live Panel Form State Update Semantics

- Step 2 must save partial round.
- Step 4 must attach/log responses to correct round.
- Need verification that implementation updates the intended existing round rather than creating duplicate rounds.

## 9.3 Missing Object: CIS_LIVE Round Lifecycle Object

Current implied fields:

- round_id
- session_id
- round_number
- question
- pushed_question_at
- gemini_response
- claude_response
- chatgpt_response
- responses_logged_at
- pushed_responses_at
- status

This object should be formally defined.

## 9.4 Missing Object: Live Push Record

Needed to distinguish:

- local write success
- GitHub push success
- SCP success
- public URL verified

## 9.5 Missing Governance: Promotion from CIS_LIVE to ADR / Memory / Task

- CIS_LIVE captures reasoning.
- It does not yet define the governed path for turning a resolved Live session into an ADR, session insight, task, or memory update.

## 9.6 Missing Validation Layer: Public URL Verification

- Push reports success based on SCP.
- Future improvement should GET the public URL and verify content hash or timestamp.

## 9.7 Missing Application Surface: Real Model Status

- Intelligence sidebar model data is static.
- Need `/api/intel/status` or equivalent to report actual local model runtime state.

## 9.8 Missing Application Surface: Pipeline Deck Actions

- Stream Deck Pipeline keys exist visually but are placeholders.
- Intake / Classify / Extract / Normalize keys must call actual API endpoints.

## 9.9 Missing Application Surface: Knowledge Deck Filters

- Knowledge keys exist visually but are not wired.
- Records / Search / Review / Approve need real behavior.

## 9.10 Missing Application Surface: WIAS Filters

- WIAS keys are present but undefined.
- Need decision: filter current project records, switch domain workspace, or trigger WIAS-specific workflows.

## 9.11 Unresolved Storage Rule: Location of CIS_LIVE Canonical Source

Multiple copies exist:

- local runtime output
- vault copy
- GitHub copy
- Proxmox `/mnt/cis-live/CIS_LIVE.md`
- LXC bind-mounted `/data/CIS_LIVE.md`

Need canonical source-of-truth rule.

## 9.12 Unresolved Orchestration: Auto-Fetch from Model Share URLs

- Discussed but deferred.
- Manual paste remains current implementation.

## 9.13 Unresolved Continuity Gap: Changes Need Automatic Capture

- User notes that past system had tools replacing redundant manual tasks.
- Current transcript still includes manual updates and patch replacement cycles.
- Needs stronger governed draft intake / session close flow.

## 9.14 Unresolved Deployment Gap: Manual File Replacement from Chat

- Assistant generated updated files for user to place on server.
- This remains a manual bridge.
- Future solution: direct patch script or staged draft/code ingestion mechanism.

# 10. BUILD-PLAN IMPLICATIONS

## 10.1 Foundational Prerequisites

1. Stable modular backend runtime.
2. Desktop launcher points to `app.py`.
3. CIS_LIVE push path works end-to-end.
4. Live panel sequence is operator-usable.
5. Runtime folder housekeeping complete.

## 10.2 Blocked Layers

### Blocked: Broader Frontend Modularization

Reason:
- CIS_LIVE flow must stabilize first.
- Current UI monolith still works but is fragile.

### Blocked: Real Intelligence Sidebar Status

Reason:
- Requires backend status endpoint and process detection.

### Blocked: Automated Frontier Response Fetching

Reason:
- Major frontier platforms do not provide reliable public-response fetch behavior.

### Blocked: Live-to-Governance Promotion

Reason:
- Needs ADR / memory / task staging mechanism.

## 10.3 Sequencing Implications

Correct near-term order:

```text
1. Verify CIS_LIVE step sequence works.
2. Verify live site updates after Save Question + Push.
3. Verify Log Responses + Push updates same session correctly.
4. Remove duplicated form from center workspace.
5. Confirm right-sidebar LIVE tab is sole input surface.
6. Define CIS_LIVE Round Lifecycle Object.
7. Add Live Push Record / public verification.
8. Wire Stream Deck pipeline actions.
9. Plan frontend modularization.
```

## 10.4 Runtime-First Requirements

- Push behavior must work before UI polish.
- Live public URL must be correct before model collaboration is trusted.
- Desktop launcher must start correct backend.

## 10.5 Governance-First Requirements

- Deployment changes must be committed.
- Runtime files must not scatter across old/new locations.
- Memory additions and future feature decisions must be captured durably.

## 10.6 Execution-First Requirements

- Every button must map to a concrete state transition.
- “Push” is not a single concept; it must specify what is saved and where.
- UI cannot rely on operator remembering hidden state.

## 10.7 Application Dependencies

- Stream Deck controls depend on existing panel routing.
- Intelligence sidebar depends on active panel awareness.
- LIVE tab depends on session/round API endpoints.
- Live site copy button depends on canonical public URL rule.

# 11. EXTRACTED CANONICAL OBJECTS

## 11.1 Modular Backend Runtime

- **Purpose**
  - Replace monolithic backend with domain-separated runtime modules.
- **Lifecycle**
  - designed → generated → zipped → deployed → verified → committed → launched
- **Authority Source**
  - runtime file structure in `/mnt/projects/cis/runtime/`
- **Related Objects**
  - `app.py`, `config.py`, `api/*`, `db/*`, `utils/*`
- **States**
  - pending / extracted / verified / active / archived
- **Storage Implications**
  - backend modules live directly under runtime root after extraction.

## 11.2 `app.py`

- **Purpose**
  - Flask application entry point and blueprint registrar.
- **Lifecycle**
  - generated → syntax checked → launched → desktop launcher target
- **Authority Source**
  - modular backend package
- **Related Objects**
  - all `api` blueprints, `cis_dashboard.html`
- **States**
  - missing / present / syntax-valid / running
- **Storage Implications**
  - `/mnt/projects/cis/runtime/app.py`

## 11.3 API Route Module

- **Purpose**
  - Domain-specific backend route container.
- **Lifecycle**
  - created → registered by app.py → called by frontend → extended as domain grows
- **Authority Source**
  - modular backend contract
- **Related Objects**
  - `api/system.py`, `api/projects.py`, `api/live.py`, etc.
- **States**
  - present / registered / responding / failing
- **Storage Implications**
  - `/mnt/projects/cis/runtime/api/`

## 11.4 CIS_LIVE Session

- **Purpose**
  - Container for a multi-model problem-solving conversation.
- **Lifecycle**
  - created → active → rounds added → resolved → serialized / pushed
- **Authority Source**
  - Live panel / `api/live.py`
- **Related Objects**
  - rounds, model responses, resolution, CIS_LIVE.md
- **States**
  - open / active / resolved / pushed
- **Storage Implications**
  - DB-backed session state; markdown mirror in CIS_LIVE.md.

## 11.5 CIS_LIVE Round

- **Purpose**
  - Unit of question + attributed model responses.
- **Lifecycle**
  - question drafted → question saved → question pushed → responses pasted → responses logged → updated push
- **Authority Source**
  - Live sidebar form
- **Related Objects**
  - Live session, Gemini response, Claude response, ChatGPT response
- **States**
  - draft / question_pushed / awaiting_responses / responses_logged / pushed
- **Storage Implications**
  - Requires DB row and markdown serialization.

## 11.6 Model Attribution Field

- **Purpose**
  - Preserve which frontier model produced each response.
- **Lifecycle**
  - empty → pasted → logged → serialized
- **Authority Source**
  - human paste action
- **Related Objects**
  - CIS_LIVE Round, Remote Intelligence tab
- **States**
  - empty / filled / logged
- **Storage Implications**
  - Must not merge model responses without attribution.

## 11.7 Live Push Record

- **Purpose**
  - Track whether CIS_LIVE.md reached local, GitHub, and live public surfaces.
- **Lifecycle**
  - push initiated → local write → git push → SCP → public visible
- **Authority Source**
  - `api/live.py`
- **Related Objects**
  - CIS_LIVE.md, Proxmox file, public URL
- **States**
  - pending / local_written / git_pushed / scp_success / scp_failed / public_verified
- **Storage Implications**
  - Should be logged for debugging and trust.

## 11.8 Stream Deck Control Surface

- **Purpose**
  - Persistent operator control zone for dashboard navigation and actions.
- **Lifecycle**
  - mockup → integrated → expanded/collapsed → wired actions
- **Authority Source**
  - Application UI shell
- **Related Objects**
  - panels, pipeline actions, knowledge actions, WIAS filters
- **States**
  - expanded / collapsed / active key selected
- **Storage Implications**
  - frontend component; future modularization target.

## 11.9 Intelligence Sidebar

- **Purpose**
  - Surface local, remote, agent, and Live input contexts.
- **Lifecycle**
  - added → tabs rendered → LIVE form moved into it → future real status endpoint
- **Authority Source**
  - dashboard UI
- **Related Objects**
  - local models, remote models, agents, CIS_LIVE form
- **States**
  - open / collapsed / LOCAL / REMOTE / AGENT / LIVE
- **Storage Implications**
  - frontend component; eventual backend status integration.

## 11.10 Desktop Launcher

- **Purpose**
  - Operator-facing app start without terminal.
- **Lifecycle**
  - old monolith target → rewritten to app.py → executable
- **Authority Source**
  - `~/Desktop/CIS_Dashboard.desktop`
- **Related Objects**
  - Flask runtime, browser, port 5000
- **States**
  - points_to_old_monolith / points_to_app_py / executable / tested
- **Storage Implications**
  - Desktop file must be kept in sync with runtime entry point.

## 11.11 Reorientation Document

- **Purpose**
  - Preserve current application build state and next actions across sessions.
- **Lifecycle**
  - generated → copied to vault → referenced in future starts
- **Authority Source**
  - session continuity process
- **Related Objects**
  - memory additions, runtime deployment, CIS_LIVE priority
- **States**
  - draft / copied / current / stale
- **Storage Implications**
  - belongs in Obsidian vault / CIS docs.

## 11.12 Memory Additions

- **Purpose**
  - Capture future features and decisions from the session.
- **Lifecycle**
  - generated → appended to system_log → copied to vault → committed
- **Authority Source**
  - session close / deployment housekeeping
- **Related Objects**
  - Cloudflare tunnel, auto-fetch, QR code, remote field access
- **States**
  - proposed / appended / committed
- **Storage Implications**
  - should not remain only in chat.

# 12. ARCHITECTURAL DELTA SUMMARY

## What new understanding of CIS exists after this file that did not exist before?

After this file, CIS is no longer only an architecture for ingestion, knowledge, and tools. It has crossed into a concrete operator-facing application runtime with a modular backend, a working dashboard shell, a three-zone control-surface UI, and an active multi-model reasoning workflow.

The largest delta is that CIS_LIVE becomes a critical implementation bridge between frontier intelligence and local intelligence development. It is not just a markdown log. It is a live public context object, a manual multi-model orchestration surface, and a temporary substitute for a more advanced router/orchestrator. Its runtime path through Ubuntu VM, Proxmox, LXC, Flask, and Cloudflare makes it a real distributed system component.

The second major delta is that UI design is now recognized as execution architecture. The user’s confusion about the order of Live actions is not treated as a training issue; it is treated as a system defect. This changes the application requirement from “provide buttons” to “encode the runtime sequence into the interface.” Buttons must correspond to state transitions. Labels must expose whether data has been saved, pushed, logged, or only typed into local UI state.

The third major delta is that backend modularization is complete enough to serve as a stable contract for further application development. `app.py`, route modules, database modules, and utility modules replace the previous monolith. The frontend remains a known monolith risk, but the runtime backend is now structurally ready for panel-by-panel expansion.

The fourth major delta is that the intended CIS application interface became much more concrete. The Stream Deck control surface, central workspace, and right Intelligence sidebar translate prior abstract ideas—project-centered workflow, intelligence tiers, agents, WIAS, and tools—into visible application zones. The dashboard is becoming the practical control surface of the CIS studio system.

The fifth major delta is that remote access is no longer just a future concept. The Cloudflare/Proxmox/LXC bridge exposes CIS_LIVE to frontier models and potentially to the user in the field. This introduces a new category of application requirement: local runtime actions that generate externally readable state.

The unresolved architectural lesson is that the human remains a middleware layer in several places: copying model responses, replacing generated files, remembering operation order, and promoting live insights into durable governance objects. The next build-plan pressure therefore points toward staged intake, Live-to-governance promotion, frontend modularization, and stronger runtime verification of public outputs.

---

# TOPOLOGY-READY NODE LIST

## Primary Nodes

- Modular Backend Runtime
- `app.py`
- `config.py`
- API Route Modules
- Database Modules
- Utility Modules
- `cis_dashboard.html`
- Stream Deck Control Surface
- Central Workspace
- Intelligence Sidebar
- CIS_LIVE Panel
- CIS_LIVE Session
- CIS_LIVE Round
- Model Attribution Fields
- Live Push Record
- CIS_LIVE.md
- GitHub Repository
- Proxmox Host
- LXC 101 Static Server
- Cloudflare Public URL
- Desktop Launcher
- Reorientation Document
- Memory Additions

## Primary Edges

```text
Desktop Launcher → app.py
app.py → API modules
API modules → DB / runtime files
Dashboard UI → API modules
Live Sidebar Form → api/live.py
api/live.py → live_db.py
live_db.py → CIS_LIVE.md
CIS_LIVE.md → GitHub
CIS_LIVE.md → SCP → Proxmox /mnt/cis-live
Proxmox /mnt/cis-live → LXC /data
LXC Flask static route → creative-intelligence-system.com
creative-intelligence-system.com → Frontier Models read context
Frontier responses → Human paste → CIS_LIVE Round
Resolved Live session → Memory / ADR / Task candidate
```

## Primary Feedback Loops

```text
Operator confusion → UI sequence redesign → lower cognitive load
Wrong URL → runtime path discovery → SCP bridge correction
Monolith risk → backend modularization → stable API contract
Live session outputs → implementation insight → CIS build improvements
Public context push → frontier model responses → local intelligence development
```

