# WIASW BUILD GUIDE — How the app works, recovered from your own workbook
**Claude Fable 5 — 2026-07-19**
**Sources: `data/drive_imports/architecture_atlas_prompt_WIAS Project Manager (version 1).xlsb.xlsx` (all 47 sheets read) · `docs/_archive/.../X_00A WORKING METHOD` · `X_00_OPERATOR_MODEL.md` · your verbatim spine messages**

---

## PART 1 — THE ANSWER: how a user does work in WIASW

You said you can't figure out how you imagined a user working in the application. You did imagine it — it's in the workbook, and here is the recovered loop. The key that unblurs everything:

**The core loop of WIASW is the brain BETWEEN work sessions** — it remembers where every project is, hands you what the current step needs, schedules the block, and records what happened. The creative work itself happens in Blender, Resolve, ComfyUI, a DAW, a notebook. The X_-prefixed docs blurred because models kept restating this loop as abstract "Streams," "Workbenches," and "Execution Layers" — design-process documents mistaken for the product. The workbook never blurred: it is object-first and complete. (Part 4 below covers the second half of your vision — the app *driving* those external tools. That layer is real, but it bolts onto the loop; it doesn't replace it.)

### The loop (recovered from your own sheets)

**1. Capture an idea (2 minutes, any time).**
Your `ideas definition` sheet is the form: idea name, link, date, description, context/backstory, category (Word/Image/Action/Sound/Web), medium, story type. Your Operator Model: *"Ideas are not fully formed at inception."* Capture is fast and judgment-free — a parking lot, not a commitment.

**2. Promote an idea to a project (when you're ready).**
Your `projects` sheet: pick the **project goal** — your `project goal` sheet lists exactly what a goal can be: script, book, drawing, painting, storyboard, animatic, 2d animation, 3d animation, film, music production... This is your 2026-04-17 insight verbatim: *"each stage of WIAS can be an end goal, script painting, comic, animation, short or long form."* The goal defines where the pipeline STOPS for this project.

**3. The app generates the step chain.**
Your `status` sheet is not a status dropdown — **it is the production pipeline in order**: idea link → create project → research → reference → general outline → treatment → outline-to-script → write script → concept art → storyboard → 2d animatic → environments → characters → animate → composite → vfx → 3d previz → model → sculpt → texture → ... A project's chain runs from `create project` to its goal and no further. A drawing project has a short chain; a film has a long one. **Progress = position in chain**, which answers the question you said you always need answered: *"I always want to know how far am I from the end."*

**4. Open the current step — everything it needs is attached.**
This is what your support sheets are FOR: `checklists` (per medium genre), `templates` (per genre folder), `software` (mapped to status/steps in your software sheet), `learn folders` (per category + step + software), `research` and `reference` (per project). The step page shows: the checklist, the templates, the software for this step, your learning links for that software, and this project's research/references. One screen, then you go work.

**5. The calendar schedules the block.**
Your `life schedule` / `7 day schedule` sheets: time blocks assigned to a project step, software training, or artform theory — work, learning, and life in one calendar, exactly Intention 11: *"a life management and task schedule to incorporate the full life and creative projects management in a single calendar and UI."* Today's view = which project, which step, which block.

**6. Close the block: mark done or not, jot one line, the chain advances or doesn't.**
The Operator Model's memory rules (retain project state, past decisions, detect drift, remind of required actions) are satisfied by this habit plus the data model — no AI needed for the core loop.

That's the core app: **Idea shelf → Project chains → Step page → One calendar.** Four screens.

### Where the LLM goes in the brain layer (one feature at a time)

Your Operator Model's AI sequence — Wait → Suggest → Organize → Challenge → Fill gaps → Automate — maps onto the loop:
- **Organize**: paste a rough idea, the model fills the idea form for your review (card W-6).
- **Suggest**: on a step page, "what should this block focus on" from the checklist + session notes.
- **Challenge / Fill gaps**: "what am I missing before I leave this step."
- **Automate**: the production actions in Part 4 — last in the sequence, exactly as you wrote in April. The sequence is a leash: a feature may not automate what it hasn't first suggested and organized.

---

## PART 2 — THE CORE CARD STACK (v0.1, feed through the same gates as SWA)

Same rules as FABLE_RECOMMENDATION_REPORT.md: one card per run, evidence decides, docs-only diff fails. Build in `/workspace/wiasw-app` (add the writable mount, same as swa-app). Port 8091 so SWA and WIASW run side by side.

```
CARD W-1: Database derived from the workbook
SOURCE: Intention 11; workbook at data/drive_imports/architecture_atlas_prompt_WIAS
Project Manager (version 1).xlsb.xlsx
INTENT (Eric, verbatim): "The WIASW spreadsheet is the source schema — CIS should derive
its data model from this workbook, not invent one from scratch."
BUILD: A script import_workbook.py that reads the workbook and creates wiasw.db with
tables: ideas, projects, steps, project_steps, checklists, templates, learning, research,
reference, software, equipment — columns named from the sheet headers verbatim (typos
included). Seed lookups verbatim: the 6 categories, the full status list IN ORDER (with
sort_order), goals, mediums, all genre lists. Emit mapping_report.txt: sheet → table →
columns.
DONE WHEN:
  - Eric reads mapping_report.txt and recognizes his own workbook
  - the status order in the db matches the sheet order exactly
EVIDENCE:
  - cd /workspace/wiasw-app && python3 import_workbook.py
  - sqlite3 wiasw.db "SELECT count(*) FROM steps;" | grep -qv "^0$"
  - sqlite3 wiasw.db "SELECT name FROM steps ORDER BY sort_order LIMIT 1;" | grep -qi "idea"
NOT IN THIS CARD: no UI, no renaming Eric's terms, no "improving" the schema, no
normalization passes, no user accounts.
```

```
CARD W-2: Idea shelf
SOURCE: ideas definition sheet; X_00_OPERATOR_MODEL.md
INTENT (Eric, verbatim source doc): "Ideas are not fully formed at inception."
BUILD: Flask app at /workspace/wiasw-app/app.py on port 8091. Page /ideas: a fast
capture form matching the ideas definition sheet (name, link, description, context,
category dropdown, medium dropdown, story type dropdown) and the list of captured
ideas newest-first.
DONE WHEN:
  - Eric captures a real idea in under a minute and sees it in the list after restart
EVIDENCE:
  - cd /workspace/wiasw-app && (python3 app.py &) && sleep 3
  - curl -sf -X POST http://localhost:8091/ideas -d "idea_name=test idea&category=word&description=x"
  - pkill -f "app.py"; (python3 app.py &); sleep 3; curl -sf http://localhost:8091/ideas | grep -q "test idea"
NOT IN THIS CARD: no projects yet, no calendar, no LLM, no styling, no search.
```

```
CARD W-3: Promote to project → generated step chain
SOURCE: projects sheet, project goal sheet, status sheet; message from 2026-04-17
INTENT (Eric, verbatim): "each stage of WIAS can be an end goal, script painting, comic,
animation, short or long form, series etc... In this scenario I always want to know how
far am I from the end."
BUILD: A Promote button on an idea: pick project goal (from goals table) and project
type (minor/major). The app creates the project and its project_steps chain — every
step from "create project" through the step matching the goal, in workbook order. Page
/project/<id> shows the chain, current step highlighted, and "Step N of M — X% to
<goal>" at the top. A Done button on the current step advances the chain.
DONE WHEN:
  - Eric promotes an idea with goal "drawing" and sees a short chain; another with goal
    "2d animation" gets a longer one
  - the top of each project page answers "how far am I from the end" at a glance
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/ideas/1/promote -d "goal=drawing&type=minor"
  - curl -sf http://localhost:8091/project/1 | grep -qi "of "
NOT IN THIS CARD: no step attachments yet, no calendar, no branching/merging, no
hand-editing chains.
```

```
CARD W-4: Step page with attachments
SOURCE: checklists, templates, software, learn folders, research, reference sheets
INTENT (Eric, verbatim): WIASW includes "training knowledge, asset management for
creative projects" attached to the work.
BUILD: The current step on /project/<id> links to /project/<id>/step: that step's
checklist items (checkable, saved), templates for the project's medium/genre, software
mapped to this step, learning links for that software/category, and the project's
research and reference lists with an add-link form for each.
DONE WHEN:
  - Eric opens a real project's current step, sees checklist + templates + software +
    learning + research on one page, adds one research link, and it persists
EVIDENCE:
  - curl -sf -X POST "http://localhost:8091/project/1/research" -d "name=ref&url=http://x"
  - curl -sf http://localhost:8091/project/1/step | grep -q "ref"
NOT IN THIS CARD: no file uploads (links only), no DAM ingestion, no thumbnails, no
LLM suggestions.
```

```
CARD W-5: The single calendar
SOURCE: life schedule / 7 day schedule sheets; Intention 11
INTENT (Eric, verbatim): "a life management and task schedule to incorporate the full
life and creative projects management in a single calendar and UI."
BUILD: Page /week: a 7-day grid of time blocks. A block is: project+step, software
training, artform theory, or life (from schedule category). Add/edit blocks with
start/end times. Page / (home) becomes Today: today's blocks in order, each linking to
its project step page.
DONE WHEN:
  - Eric schedules a real week and starts his day from the Today page
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/blocks -d "day=2026-07-20&start=09:00&end=11:00&category=project&project_id=1"
  - curl -sf http://localhost:8091/week | grep -q "09:00"
NOT IN THIS CARD: no external calendar sync, no notifications, no recurring blocks, no
drag-and-drop.
```

```
CARD W-6: Idea intake assist (first LLM feature)
SOURCE: X_00_OPERATOR_MODEL.md AI sequence
INTENT (Eric, verbatim source doc): "AI operates in the following sequence: 1. Wait
(understand intent) 2. Suggest (next steps) 3. Organize (structure thoughts)"
BUILD: On /ideas, a paste box: Eric pastes rough idea text, clicks Organize, the app
calls the DeepSeek API and fills the capture form fields (name, description, context,
category, medium, story type) as an editable draft. Never auto-saved — Eric reviews
and saves.
DONE WHEN:
  - Eric pastes a messy paragraph, clicks Organize, gets a filled form he edits and saves
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/ideas/organize -d "text=a short film about a lighthouse keeper who collects storms" | grep -qi "category"
NOT IN THIS CARD: no chat, no step suggestions, no automation, no model picker.
```

---

## PART 3 — WHAT TO DO WITH THE X_ FILES

Keep them archived; stop mining them for the app. Ranked honestly:
- **Load-bearing (already used above):** the workbook itself, `X_00_OPERATOR_MODEL.md`, `X_00A WORKING METHOD`. The Operator Model survives as two product rules: the AI-sequence leash, and "structure must be adaptive" (chains are generated, but Done is always manual).
- **Historical only:** the Stream docs (X_05–X_11), MASTER_ARCHITECTURE_MAP, RUNTIME_SPEC, ROUTER SPEC, the Workbench docs. They describe an 8-layer system *around* the loop — the blur you noticed. Nothing in the four screens needs them. If a future card genuinely needs one, the card will name it.

---

## PART 4 — PRODUCTION ACTIONS: the app driving the creative tools

This is the second half of your vision, in your words this session: after *"the brain work was done setting up a project... the programs could be opened, templates saved to a folder, even concepts turned into 3d animations, videos or music."* Correct instinct, and people are doing all of it. Here is the shape that makes it buildable by cards instead of becoming another abstraction.

### The architecture: Recipes attached to steps

A **recipe** is a small script the app can run for a step. Every recipe has the same contract:

```
recipe:
  step it belongs to        (e.g. "concept art", "create project", "2d animatic")
  inputs                    (fields from YOUR objects: idea description, genre, references,
                             the script text, storyboard images...)
  tool it drives            (filesystem, ComfyUI API, headless Blender, ffmpeg, Resolve API)
  outputs                   (files written into the project's asset folders, every one
                             registered in the assets table with project + step + date)
  evidence                  (a command that proves the output exists — same gate as everything)
```

The LLM's only job inside a recipe is filling creative parameters (a prompt from the idea description + genre, a shot list from the script). The tool execution is deterministic script, not model improvisation — same principle as card_gate: **models fill fields; scripts do actions.** Outputs are always drafts filed into the project, never auto-advanced steps. That keeps your Operator Model's leash: the recipe automates the setup and the first draft; you do the creative pass in the tool.

### Why this works with what you already run

- **Filesystem** — no AI needed. Folder scaffolds and template copies are plain scripts.
- **ComfyUI** — has an HTTP API: a workflow saved as JSON can be POSTed with new prompt text and returns images/video. This is the industry-standard way apps drive image/video generation, and it's exactly a recipe: workflow JSON = the deterministic part, prompt = the LLM-filled part.
- **Blender** (`/mnt/projects/blender`) — runs headless: `blender --background --python script.py`. A recipe can build a scene from a template (camera, lighting, imported storyboard planes) and save a .blend the artist opens.
- **ffmpeg** — assembles storyboard frames + durations into an animatic video. Pure script.
- **DaVinci Resolve** (`/mnt/projects/resolve`) — has a Python scripting API: recipes can create a project, make bins, import the animatic and assets.
- **Houdini/Unreal** (`/mnt/projects/houdini`, `/mnt/projects/unreal`) — both scriptable (hython, Unreal Python) — later recipes, same contract.
- **Music** — hardest locally; start with the brain side (lyric/structure drafts via LLM) and leave audio generation as a future recipe slot rather than a blocker.

### The production card stack (build AFTER W-1..W-6 are live)

```
CARD W-7: Project scaffold recipe (no AI — the proof of the recipe system)
INTENT (Eric, verbatim, this session): "the programs could be opened, templates saved
to a folder"
BUILD: A "Set up project" action on /project/<id>: creates the project's folder tree
on disk (one folder per step in its chain, plus assets/), copies the templates for its
medium/genre into the right step folders, and registers every copied file in the assets
table. The step page shows an "Open folder" path for the current step.
DONE WHEN:
  - Eric clicks Set up on a real project and finds the folder tree with templates inside
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/project/1/scaffold
  - ls /workspace/wiasw-app/projects/1/ | grep -qi assets
  - sqlite3 wiasw.db "SELECT count(*) FROM assets WHERE project_id=1;" | grep -qv "^0$"
NOT IN THIS CARD: no external tools yet, no generation, no file watching.
```

```
CARD W-8: Concept art recipe (ComfyUI)
INTENT (Eric, verbatim, this session): "even concepts turned into 3d animations, videos
or music" — starting with the concept-art step, images first.
BUILD: On the "design concept art" step page, a Generate action: the app builds a prompt
from the idea description + medium + genre (LLM fills it, Eric can edit the prompt before
running), POSTs it to the ComfyUI API with a fixed workflow JSON stored in the repo, and
files returned images into the project's concept-art folder + assets table. The step page
shows the generated images.
DONE WHEN:
  - Eric clicks Generate on a real project, edits the suggested prompt, and sees new
    concept images on the step page and in the project folder
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/project/1/step/generate | grep -qi "queued\|image"
  - ls /workspace/wiasw-app/projects/1/concept_art/ | grep -qi ".png\|.jpg"
NOT IN THIS CARD: no video yet, no model training, no workflow editor — ONE fixed
workflow JSON, swappable by replacing the file.
```

```
CARD W-9: Animatic recipe (ffmpeg)
INTENT: the "create 2d animatic" step from Eric's own status sheet.
BUILD: On the animatic step page: Eric orders the storyboard images (from the project's
storyboard folder) and gives each a duration in seconds. A Build Animatic action runs
ffmpeg to produce animatic.mp4 in the project folder, registered as an asset, playable
on the step page.
DONE WHEN:
  - Eric builds an animatic from real boards and plays it in the browser
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/project/1/animatic
  - ls /workspace/wiasw-app/projects/1/ | grep -q animatic.mp4
NOT IN THIS CARD: no audio track yet, no transitions, no timeline UI beyond order+duration.
```

```
CARD W-10: Blender scene bootstrap recipe
INTENT (Eric, verbatim, this session): "concepts turned into 3d animations" — the setup
half: a ready scene, not a finished animation.
BUILD: On the "3d previz" step page, a Create Scene action: runs blender --background
--python with a repo-stored script that builds a .blend from a template — camera,
lighting rig, storyboard images imported as reference planes — saved into the project
folder and registered as an asset. The step page shows the file path to open.
DONE WHEN:
  - Eric clicks Create Scene, opens the .blend in Blender, and finds his boards and a
    working camera already in it
EVIDENCE:
  - curl -sf -X POST http://localhost:8091/project/1/blender_scene
  - ls /workspace/wiasw-app/projects/1/previz/ | grep -q ".blend"
NOT IN THIS CARD: no animation generation, no rendering, no Houdini/Unreal, no asset
library management.
```

**Sequencing rule for Part 4:** W-7 first, always — it proves the recipe contract with zero AI and zero external dependencies. Each later recipe adds exactly one tool. If a recipe card fails its evidence twice, the step keeps its manual path (open the folder, work in the tool) and the recipe goes back in the queue — production actions are accelerators on top of a working loop, never prerequisites for it. That's the difference between this plan and the X_ docs: the loop ships first, the magic bolts on one card at a time.

**Order of operations overall:** SWA bills first (cards in FABLE_RECOMMENDATION_REPORT.md). WIASW starts at W-1 after SWA-6 is live. Recipes start at W-7 after the loop is lived-in for at least a week of real blocks. Both apps share the same method, the same gates, and the same container — which is the proof CIS was for.
