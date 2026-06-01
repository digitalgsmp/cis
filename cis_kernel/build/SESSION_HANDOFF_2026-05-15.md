# Session Handoff — May 14-15, 2026

## Current State

The React Flow UI is running at `http://127.0.0.1:5000/ui/` (or double-click **CIS React Flow** desktop icon). Vite + React project at `/mnt/projects/cis/runtime/ui/`. Node creation works — you can add nodes with label, narrative, and status, and they save to the drafts database. Flask serves the compiled bundle. The old kernel workbench is still at `/workbench`.

The SOUL.md persona file has been written at `~/.hermes/SOUL.md` — it defines the operating principles: propose before executing, seek best solutions not easiest, absorb corrections permanently, preserve everything, think in systems not tasks.

## What Was Built This Session

- [x] Single-click desktop button for CIS Workbench
- [x] Session Record page with breadcrumb trail, infrastructure status, scratchpad, decisions
- [x] Upload → Vision Model auto-describe pipeline (upload server at port 9000, watcher as systemd service)
- [x] Mermaid flowchart in Map tab (now superseded by React Flow)
- [x] React Flow UI foundation — Vite + npm + CDN-free compiled bundle
- [x] Node creation form with status picker, saves to drafts DB
- [x] Interactive feature toggles: background pattern, minimap, snap-to-grid, animated edges
- [x] SOUL.md persona file

## Open Branches / Next Tasks

These are listed in rough priority — nothing is locked, rearrange as needed.

### 1. Align React Flow to CIS Documentation and Database
The React Flow graph currently has hardcoded nodes. It needs to read from and write to the CIS database (maps table, nodes/edges stored as JSON, status changes updating drafts). The graph should reflect the same state the system knows about.

### 2. Rebuild the UI Around React Flow
The kernel workbench (`/workbench`) is still the old inline-HTML pattern. Either integrate React Flow into it or rebuild the whole UI with React Flow as the foundation. The nav tabs (Ideas, Session, Project, Research, Build Plan, Management, Knowledge, Agents) would become React panels beside or within the graph.

### 3. Open Source Calendar
A calendar view in the UI where React Flow nodes can become events. Drag a node onto the calendar → it creates a time-blocked event. Todo items bridge between the graph and the calendar. Look at FullCalendar (MIT licensed, open source) or similar. Calendar should integrate with project scheduling.

### 4. Add "Work" Domain to CIS — SWA Under Work
The home-body-mind concept expands to home-body-mind-work. The SWA (Social Work AI) project lives under the Work domain. This affects the map structure — SWA gets its own React Flow map under the Work category. The WIAS scheduling concept (Word/Image/Action/Sound for creative production) may have an equivalent for work/life domains.

### 5. Web Search Functionality
SearXNG was the stubborn choice against paywalled search APIs. It needs to be resolved — either get SearXNG running, find a free-tier search API that works, or establish a different approach to web research. This has been blocking the extraction indexing research.

### 6. Proton Email & Calendar Integration
Proton Mail Bridge is already running (IMAP 1143, SMTP 1025 for eshelton@communitycounselingmadison.com). SWA project could use Proton Calendar for client scheduling. Need to explore Proton's API or bridge capabilities.

### 7. Real-Time Knowledge Base Updates
Instead of creating session transcript files that need extraction later, wire Hermes session logs directly into the knowledge base. Decisions, corrections, and insights captured during conversation should go straight to the knowledge store.

### 8. Index CIS and SWA Extraction Files
1,508 extraction files (444 CIS + 1,064 SWA) contain accumulated solutions from months of exploratory development. They need to be indexed (vectorized) so the content can be searched and used. The indexed information should also seed React Flow charts that define the build plans for both projects.

## Key Files

| Path | Purpose |
|------|---------|
| `/mnt/projects/cis/runtime/ui/` | React Flow Vite project |
| `/mnt/projects/cis/runtime/ui/src/App.jsx` | Main React Flow app |
| `/mnt/projects/cis/runtime/app.py` | Flask backend |
| `/home/eric/.hermes/SOUL.md` | Agent persona (loaded every message) |
| `/home/eric/incoming/upload_server.py` | Upload server (port 9000) |
| `/home/eric/incoming/incoming_watcher.py` | Vision model watcher (systemd service) |
| `/mnt/projects/cis/cis_kernel/build/CIS_SCRATCHPAD.md` | Running scratchpad from this session |
| `/mnt/projects/cis/cis_kernel/extraction/functional_intents/` | 444 CIS extraction files |
| `/mnt/projects/social_work_ai/swa_kernel/extraction/functional_intents/` | 1,092 SWA extraction files |
| `/mnt/projects/cis/memory/cis_memory.db` | Main CIS database (19 tables) |

## Infrastructure Running

- **Flask** on port 5000 (serves API + React Flow)
- **Vision model** (Qwen3-VL-30B-A3B) on port 8002 via llama-server
- **Upload server** on port 9000
- **Incoming watcher** (systemd) — watches for new images, auto-describes via vision model
- **Proton Bridge** — IMAP 1143, SMTP 1025
- **Hermes gateway** — connects CLI and Telegram
