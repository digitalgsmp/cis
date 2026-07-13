# CIS Workbench UI — Design Spec

**Status:** SPEC — for pipeline processing or direct build
**Date:** 2026-07-13
**Source:** Eric's vision (verbatim from X_ documents + session transcripts)
**Theme:** WIASW — "What I Am Seeing When"

---

## 1. What This Is NOT

This is NOT the pipeline observation dashboard (that's the System tab).
This is NOT the deliberation viewer (that's the Pipeline tab).
This is NOT the health checker (that's the enforcement audit).

This IS the **workbench** — the surface where Eric works with Brain to develop ideas
and watches them materialize into components in real-time.

From X_10_Application Stream:
> "Not a portfolio site. Not a project manager. Not a chat interface.
> It is: a studio operating system interface."
> "Instead of opening 10 tools, searching folders, remembering where things are —
> you interact with one system that knows your work."

From the session history (2026-07-09):
> "You are not configuring a control plane so you can do engineering in it.
> You are configuring it so a group of expert models can do the engineering
> through the pipeline, with you steering by intention."

From Eric's memory (persistent):
> "Eric's CIS UI vision: conversational chat with Brain (explains idea → Brain
> searches KB → enriches intent → kicks off pipeline). Live observation feed of
> all phases with a backchannel chat — Eric interjects thoughts at any point
> WITHOUT stopping the flow. NOT checkpoints, NOT micromanagement. Pipeline runs
> continuously, absorbs his input as steering signals."

---

## 2. The Holy Grail Layout

Eric described it directly:
> "the holy grail would be ok we have idea figured out. im in a chat with brain
> on the left side of the screen and on the right side i am seeing the desired
> component or functionality constructed."

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOP BAR: Project breadcrumb trail                                  │
│  CIS → Enforcement Audit → SEEA Spec → Phase 1: Registry            │
├──────────────────────────────┬──────────────────────────────────────┤
│                              │                                      │
│   LEFT PANEL (40%)           │   RIGHT PANEL (60%)                   │
│                              │                                      │
│   Brain Chat                 │   Live Construction View              │
│                              │                                      │
│   ┌──────────────────────┐   │   ┌────────────────────────────────┐  │
│   │ Eric: I want the      │   │   │  [Component being built]       │  │
│   │ enforcement registry  │   │   │                                │  │
│   │ to live in the spine  │   │   │  enforcement_checks table      │  │
│   │ not in code           │   │   │  ┌─────────────────────────┐   │  │
│   └──────────────────────┘   │   │  │ CREATE TABLE enforcemen │   │  │
│                              │   │  │   (id TEXT PRIMARY KEY,  │   │  │
│   ┌──────────────────────┐   │   │  │    name TEXT NOT NULL,   │   │  │
│   │ Brain: That makes     │   │   │  │    category TEXT,        │   │  │
│   │ sense. I found 3      │   │   │  │    check_type TEXT, ...  │   │  │
│   │ relevant ADRs in the  │   │   │  └─────────────────────────┘   │  │
│   │ KB: ADR-015, ADR-016, │   │   │                                │  │
│   │ and ADR-002...         │   │   │  Migration 0026               │  │
│   └──────────────────────┘   │   │  + enforcement_checks table     │  │
│                              │   │  + FTS5 index                   │  │
│   ┌──────────────────────┐   │   │  + seed 14 existing checks      │  │
│   │ [input box]          │   │   │                                │  │
│   │ Message Brain...     │   │   │  Status: BUILDING (Menter)     │  │
│   └──────────────────────┘   │   │  ─────────────────────────────  │  │
│                              │   │  Reviewer1: PASS ✓              │  │
│   [Brain is thinking...]     │   │  Reviewer2: PASS ✓              │  │
│                              │   │  Verifier: CHECKING...          │  │
│                              │   └────────────────────────────────┘  │
│                              │                                      │
│                              │   [Backchannel: type a thought...]   │
├──────────────────────────────┴──────────────────────────────────────┤
│  BOTTOM BAR: Active runs | Phase status | Enforcement: INTACT      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 Top Bar — Project Breadcrumb Trail

From X_08_Workflow Stream §2.3:
> "Each stage of the workflow produces outputs that live in predictable locations."
> "Workflow becomes visible on disk."

From Eric's request:
> "a breadcrumb like trail for each part of the project"

The breadcrumb shows the **development path** — not just the current location,
but how we got here. Each crumb is a decision point:

```
CIS → Enforcement → SEEA Spec → Phase 1: Registry → Migration 0026
```

Clicking a crumb shows:
- What was decided at that point
- Why (the intent that drove it)
- What it produced (the artifact)
- When it happened

This is the **provenance trail** — every piece of the project has a history
you can trace back to the original idea.

**Data source:** `workflow_runs` + `deliberation_rounds` + `session_handoffs` tables
in the spine. Each breadcrumb links to the run that produced it.

### 3.2 Left Panel — Brain Chat (40%)

From X_00_OPERATOR_MODEL:
> "AI operates in the following sequence:
> 1. Wait (understand intent)
> 2. Suggest (next steps)
> 3. Organize (structure thoughts)
> 4. Challenge (identify gaps)
> 5. Fill gaps (provide knowledge)
> 6. Automate (execute tasks)"

This is a **conversation**, not a form submission. Eric talks with Brain about an idea.
Brain:
- Searches the KB for relevant context (ADRs, past decisions, existing work)
- Enriches the intent with what it finds
- Suggests how to break the idea into buildable components
- Challenges gaps in the thinking
- When the idea is ready, kicks it to the pipeline

**Key behaviors:**
- Stream responses (don't wait for full completion before showing text)
- Show when Brain is searching the KB (status indicator)
- Show what Brain found in the KB (expandable references)
- Eric can steer mid-conversation ("actually, I want it in the spine, not in code")
- When Brain kicks to pipeline, the right panel starts showing construction
- No "submit" button — the conversation flows naturally until Eric says "build it"

**Backend:** Existing `/api/relay/brain/chat` endpoint (already built and working)

### 3.3 Right Panel — Live Construction View (60%)

This is the **holy grail**. Eric described it:
> "on the right side I am seeing the desired component or functionality constructed"

When Brain kicks an idea to the pipeline, the right panel shows:
1. **What's being built** — the component name, spec, target file
2. **The actual artifact** — code, migration SQL, UI component, config file —
   rendered live as Menter writes it
3. **Review status** — Reviewer1 and Reviewer2 pass/fail as they complete
4. **Verification** — Verifier's deterministic evidence checks
5. **The finished product** — when verification passes, the completed artifact
   is shown in its final form

**This is not a log viewer.** It's a construction viewer.
Think of it like watching a 3D printer: you see the object being built layer by layer.

**What gets shown depends on the artifact type:**
- Code files → syntax-highlighted source, updating in real-time
- SQL migrations → table schema with column definitions
- UI components → rendered preview (if React component, show it live)
- Config files → structured YAML/JSON, diff against previous version
- Documentation → rendered markdown

**Key behaviors:**
- Auto-scrolls as content arrives (but pauses if Eric scrolls up)
- Shows diff markers (+/-) for changes
- Phase indicators on the left edge: Draft → Review → Implement → Verify
- Each phase's output is collapsible (Eric can focus on what he cares about)
- When complete, a "View final artifact" button opens the file in full

**Backend:** Needs a new WebSocket or SSE endpoint for live content streaming.
Existing `/api/relay/<run_id>/feed` provides polling-based updates but doesn't
stream content in real-time. Could use Server-Sent Events on Flask.

### 3.4 Backchannel (Bottom of Right Panel)

From session history (2026-07-10):
> "Interject a thought (backchannel — doesn't stop the pipeline)..."

From Eric's memory:
> "Eric interjects thoughts at any point WITHOUT stopping the flow.
> NOT checkpoints, NOT micromanagement.
> Pipeline runs continuously, absorbs his input as steering signals."

The backchannel is a **persistent input box** at the bottom of the right panel.
Eric can type a thought at any time. It gets injected into the pipeline as a
steering signal — the next phase sees it as context.

**Key behaviors:**
- Always available (not disabled during pipeline runs)
- Messages are marked as "consumed" when a phase reads them
- Eric can see which phase consumed his input
- Does NOT pause the pipeline (unlike Eric Gate which is a hard stop)
- Styled distinctly from Brain chat (warning color accent, not primary)

**Backend:** Existing `/api/relay/<run_id>/interject` and
`/api/relay/<run_id>/interjections` endpoints (already built)

### 3.5 Bottom Bar — Status Strip

Thin status bar showing:
- Active run count
- Current phase of the active run
- Enforcement audit status (INTACT/BREACHED badge)
- Timestamp of last completed phase

---

## 4. The Workflow ON TOP of the Pipeline

Eric is clear about this distinction:
> "I am not talking about the pipeline, I am talking about the workflow
> that runs on top of the pipeline."

The pipeline is the engine: Brain → Draft → Review → Menter → Verify.
The workflow is what Eric experiences: idea → conversation → construction → result.

From X_08_Workflow Stream:
> "Workflow is not software. Workflow is how work moves."
> "human-directed, intelligence-assisted"

The workbench UI exposes this workflow:

```
Eric has idea
  ↓
Eric chats with Brain (left panel)
  ↓
Brain searches KB, enriches intent, suggests approach
  ↓
Eric refines, Brain adjusts
  ↓
Eric says "build it" (or Brain proposes it)
  ↓
Right panel activates — pipeline starts
  ↓
Draft phase → spec appears on right
  ↓
Review phase → pass/fail indicators
  ↓
Menter phase → artifact constructed live on right
  ↓
Eric can interject thoughts via backchannel at ANY point
  ↓
Verify phase → deterministic evidence shown
  ↓
Complete — breadcrumb trail updated, artifact visible
  ↓
Eric starts next conversation about next component
```

The pipeline runs *underneath*. Eric doesn't see "INTAKE → BRAIN_PHASE →
DRAFT_PHASE → PROPOSAL_REVIEW → ERIC_GATE..." He sees a conversation
that becomes a construction that becomes a finished thing.

---

## 5. Relationship to X_ Documents

### X_00_OPERATOR_MODEL → Left Panel (Brain Chat)
- "AI operates: Wait → Suggest → Organize → Challenge → Fill gaps → Automate"
- "AI is helpful when aligned with user intent. AI is intrusive when acting without alignment."
- The Brain chat IS this sequence — Brain waits for Eric's intent, suggests next steps,
  organizes his thoughts, challenges gaps, fills with KB knowledge, then automates by
  kicking to pipeline.

### X_08_WORKFLOW_STREAM → Right Panel (Construction View)
- "Idea → Intake → Project → Research → Reference → Outline → Concept → Boards →
   Production → Output → Distribution → Archive"
- The construction view shows the "Production → Output" stages happening live.
- "Workflow becomes visible on disk" → the construction view makes work visible on screen.

### X_10_APPLICATION_STREAM → Overall Layout
- "Not a portfolio site. Not a project manager. Not a chat interface.
   It is a studio operating system interface."
- "One place where everything connects."
- The split-pane layout IS this: conversation on one side, construction on the other,
  breadcrumb connecting everything to its history.
- "The primary entry point of the application is the project." → The breadcrumb trail
  anchors everything to the project.

### X_CIS_WORKFLOW_EXECUTION_SPEC → The Pipeline Underneath
- "The Execution Layer does not require a database first, a web app, a control surface.
   It requires deterministic inputs, deterministic outputs, stable folder/state rules."
- The pipeline IS the execution layer. The workbench sits ON TOP of it, exposing
  the workflow to Eric without him needing to see the execution mechanics.

---

## 6. Technical Architecture

### Frontend
- React 19 + Vite (existing stack)
- New component: `Workbench.jsx` (replaces or sits alongside existing tabs)
- Sub-components:
  - `BrainChatPanel.jsx` (left)
  - `ConstructionView.jsx` (right)
  - `BreadcrumbTrail.jsx` (top bar)
  - `BackchannelInput.jsx` (bottom of right)
  - `StatusStrip.jsx` (bottom bar)

### Backend — New Endpoints Needed

1. **`GET /api/relay/workbench/breadcrumb/<project_id>`**
   - Returns the development path for the current project
   - Joins workflow_runs + deliberation_rounds to build the trail
   - Each crumb: { run_id, phase, intent, artifact_path, timestamp, status }

2. **`GET /api/relay/workbench/artifact/<run_id>`**
   - Returns the current state of the artifact being built
   - For code: the file content (or diff from previous version)
   - For SQL: the migration content
   - For UI: the component source + rendered preview
   - Streams via Server-Sent Events for real-time updates

3. **`GET /api/relay/workbench/construction/<run_id>/stream`**
   - SSE endpoint that pushes artifact updates as they happen
   - Each event: { phase, content_type, content, timestamp }
   - Closes when run completes

4. **Existing endpoints (already built):**
   - `POST /api/relay/brain/chat` — Brain chat (working)
   - `GET /api/relay/brain/history/<session>` — Chat history (working)
   - `POST /api/relay/<run_id>/interject` — Backchannel (built, needs testing)
   - `GET /api/relay/<run_id>/interjections` — Backchannel history (built, needs testing)
   - `GET /api/relay/<run_id>/feed` — Polling feed (built, needs testing)
   - `GET /api/relay/<run_id>` — Run status (working)

### Spine Tables (existing, no new schema needed)
- `workflow_runs` — run_id, intent, status, created_at
- `deliberation_rounds` — per-phase outputs, reviewer signals
- `session_handoffs` — breadcrumb trail data source

---

## 7. Phasing

### Phase 1: Split-Pane Shell (visual only, no live pipeline)
- Build Workbench.jsx with split-pane layout
- Left panel: Brain chat (already works)
- Right panel: placeholder showing "Waiting for Brain to dispatch..."
- Top bar: breadcrumb (read from workflow_runs)
- Bottom bar: status strip
- This is immediately usable as a conversation interface

### Phase 2: Construction View (polling-based)
- Right panel shows pipeline run progress when Brain kicks to pipeline
- Poll `GET /api/relay/<run_id>` every 2 seconds
- Show phase indicators: Draft → Review → Menter → Verify
- Show artifact content when Menter completes (read file from disk)
- Show review pass/fail when reviewers complete
- Show verification evidence when Verify completes

### Phase 3: Live Construction (SSE streaming)
- Replace polling with Server-Sent Events
- Stream Menter's output as it writes (file content updates)
- Real-time diff markers as code changes
- This is the "holy grail" moment — watching the thing being built

### Phase 4: Backchannel Integration
- Wire up the backchannel input
- Show interjection history
- Show which phase consumed each interjection
- Test with a live pipeline run

### Phase 5: Breadcrumb Provenance
- Click any breadcrumb crumb → see the full decision history
- Show the intent that drove each decision
- Show the KB references Brain used
- Show the artifact produced
- This makes the development trail permanent and navigable

---

## 8. What Eric Sees (User Story)

1. Eric opens the workbench. Left panel shows Brain chat. Right panel is empty
   with "Start a conversation with Brain about what you want to build."

2. Eric types: "I want the enforcement audit registry to live in the spine, not in code."

3. Brain responds in the left panel: "Good idea. I found ADR-015 and ADR-016 in the KB.
   They define the containment model. The current 14 checks are hardcoded in
   container_app.py. Moving them to a spine table would make them data-driven.
   Should each check store its check_type, parameters, and evidence template?"

4. Eric: "Yes, and the Verify role should be able to propose new checks."

5. Brain: "That works. I'll draft a spec for a spine migration + audit engine refactor.
   Want me to kick it to the pipeline?"

6. Eric: "Build it."

7. Right panel activates. Breadcrumb updates: "CIS → Enforcement → Audit Registry → Build"
   The spec appears. Review indicators light up. Menter starts writing the migration SQL
   — Eric watches the CREATE TABLE statement appear on screen.

8. Eric thinks of something. He types in the backchannel: "Add a fail_count column
   so we can track which checks fail most." The message appears in the backchannel
   history. A moment later, the phase indicator shows "Backchannel consumed by: Menter"
   and the migration adds `fail_count INTEGER DEFAULT 0`.

9. Verifier runs. Evidence appears: "Migration 0026 applied. 14 checks seeded.
   SELECT COUNT(*) FROM enforcement_checks → 14. PASS."

10. The construction is complete. The breadcrumb shows the full trail. Eric starts
    a new conversation about the next component.

---

## 9. Key Principles (from X_ documents)

1. **Object-first** (X_10 §Final): "The application is object-first. It must not be
   designed primarily around files or folders." The workbench is organized around
   the *idea* and the *artifact*, not the file path.

2. **Project as primary interface** (X_10 §4.1): "The primary entry point of the
   application is the project." The breadcrumb anchors everything to the project.

3. **Workflow is adaptive** (X_08 §2.4): "Workflow is adaptive, not fixed." The
   workbench supports pausing, rescoping, redirecting — the backchannel enables
   steering without stopping.

4. **Human-directed, intelligence-assisted** (X_08 §1.1): Eric directs, Brain assists.
   The left panel is the direction, the right panel is the assistance.

5. **Execution before application** (X_CIS_WORKFLOW_EXECUTION_SPEC): The pipeline
   (execution layer) is already built. The workbench (application layer) exposes it.
   Don't rebuild the engine — build the steering wheel.
