# CIS-AUDIT-001B — Coverage Addendum

**Date:** 2026-05-24
**Parent report:** `/mnt/projects/cis/docs/CIS_CURRENT_STATE_AUDIT_2026-05-24.md`

---

## Coverage Checklist

### 1. Proxmox/storage/snapshot risk
- **Covered:** YES
- **Where:** Section 2, "Immediate Risks / Blockers"
- **Evidence:** No qemu-guest-agent installed. VM on raw ext4 virtio partitions. /mnt/models at 91%.
- **Gap:** Underlying Proxmox storage type (LVM-thin, ZFS, directory?) not confirmed from inside VM. Need Proxmox host access to determine.
- **Next action:** Install qemu-guest-agent, test snapshot from Proxmox host. If still blocked, check storage type.

### 2. Runtime/service/autostart state
- **Covered:** YES
- **Where:** Section 3, "Current Runtime Map"
- **Evidence:** All 7 services verified running, all enabled in default.target.wants. Post-reboot recovery confirmed.
- **Gap:** None.
- **Next action:** None needed at this time.

### 3. Active app/file structure
- **Covered:** YES
- **Where:** Section 4, "Current File/App Map"
- **Evidence:** Runtime directory mapped, UI pages listed, API blueprints enumerated.
- **Gap:** None.
- **Next action:** None.

### 4. Legacy/duplicate/generated/backup file clutter
- **Covered:** YES
- **Where:** Section 4 under "Legacy/experimental files in runtime"
- **Evidence:** 50+ Python files in runtime/ with unclear dependency chains. 8 zero-byte .db files scattered. ui_components/, ui_mockups/ pre-React artifacts. _archive directories at multiple levels.
- **Gap:** No dependency analysis of which legacy files are still imported vs truly dead.
- **Next action:** Before distribution/packaging, run import analysis to identify dead files. Do NOT delete yet.

### 5. Database split and schema conflicts
- **Covered:** PARTIAL — upgraded from "dual" to "triple" in this addendum
- **Where:** Section 5, "Current Database/Schema Map" — originally reported dual split. **CORRECTION BELOW.**
- **Evidence of TRIPLE split (new finding):**

| Database | Path | Size | Tables | Purpose |
|----------|------|------|--------|---------|
| cis_memory.db | /mnt/projects/cis/memory/ | 40MB | 30+ | Legacy: collab, spines, knowledge, tasks, models, captures, live_sessions |
| cis_app.db | /mnt/projects/cis/memory/ | 2MB | 9 | App layer: ideas, projects, assets, schedule, domains, users, permissions |
| cis_memory.db | /mnt/projects/cis/runtime/db/ | 200KB | 6 | Advisor Chat: threads, messages, reconciliations, external_reviews, idea_drafts, agent_instances |

- **Schema conflicts:**
  - `idea_drafts` (runtime DB) vs `ideas` (cis_app.db) — different tables, different schemas, different databases
  - `projects` in cis_app.db (33 rows, mostly LMS courses) vs tasks in cis_memory.db referencing `PROJECT__CIS__BUILD__V1` — different project ID formats
  - No cross-database foreign keys exist anywhere
  - `assets` in cis_app.db (254 rows) are LMS video lessons — not general DAM assets
  - `idea_drafts` has 3 rows pending promotion, `ideas` has 6 rows (2 promoted, 4 captured)

- **Gap:** The original report called this a "dual database" split. It is a TRIPLE split. The cis_app.db was missed because it uses a different filename pattern.
- **Next action:** Database unification must address THREE databases, not two. The cis_app.db has the most mature app-layer schema (ideas, projects, assets with proper FK patterns).

### 6. Ideas / idea_drafts / projects / tasks relationship
- **Covered:** PARTIAL — now fully mapped
- **Where:** Section 5 gaps + this addendum
- **Evidence of current state:**
  - `ideas` (cis_app.db, 6 rows): User-facing ideas with status (captured/promoted), domain, description, tags
  - `idea_drafts` (runtime DB, 3 rows): AI-structured deliberation output with domain classification, open questions, source thread/message IDs
  - `projects` (cis_app.db, 33 rows): 2 actual projects (CIS Kernel v1 + SWA case mgmt), 31 LMS courses mis-stored as projects
  - `tasks` (cis_memory.db, 35 rows): All reference `PROJECT__CIS__BUILD__V1`, all status "open", no cross-DB linkage
  - No promotion path exists between idea_drafts (runtime DB) and ideas (cis_app.db) or projects (cis_app.db)
  - IdeasPage.jsx has a "promote" button that navigates to /projects?source=idea_id — this is a URL-parameter handoff, not a database promotion
- **Gap:** The three databases prevent any structured workflow. An idea_draft from Advisor Chat cannot be promoted without manual cross-DB operations.
- **Next action:** This is the core of Pass 5. Establish a single ideas→projects pipeline in the unified database.

### 7. Advisor Chat current functionality
- **Covered:** YES
- **Where:** Sections 3, 5, 7
- **Evidence:** All 4 agents verified (PRIME_OK, V4PRO_OK, R1_OK, QWEN_OK). Direct, Parallel/Deliberate, Reconcile, Execute modes all functional. Streaming for Prime and V4-Pro. External review capture endpoint exists (0 rows).
- **Gap:** External review capture has no data — manual paste workflow only. Live Claude/ChatGPT API routing deferred.
- **Next action:** Deferred per architecture decision. Not blocking Pass 5.

### 8. Advisor Chat UX/layout/visibility issues
- **Covered:** YES (identified as design friction, not bugs)
- **Where:** HHR-UI-006 in scratchpad
- **Evidence:** Eric reported Prime in bottom-left corner not ideal for first-engagement. Single-monitor and mobile usability are concerns. 2×2 grid layout reflects agent roles, not engagement flow.
- **Gap:** No UX review performed beyond Eric's observations. No mobile responsiveness analysis.
- **Next action:** Defer to consolidated UX pass. Not blocking Pass 5.

### 9. Project-management workflow
- **Covered:** YES — now fully audited
- **Where:** This addendum (items 5-6)
- **Evidence:**
  - Ideas → Projects promotion: URL-parameter handoff only (IdeasPage.jsx line 161-162)
  - Projects exist in cis_app.db with proper schema (name, description, domain, status, phases, owner, team, created/updated/target dates)
  - 31 of 33 projects are LMS courses — the "projects" table is being used as an LMS course registry as well as a project tracker
  - Tasks (cis_memory.db) have project_id field but reference different project ID format
  - No milestones, no Gantt, no dependency tracking
  - Schedule (cis_app.db): 0 schedule_slots — the table exists but was never populated
  - ProjectDetail.jsx (171 lines) shows basic project info with "slots" count but minimal functionality
- **Gap:** Projects exist but are not connected to tasks, schedule, DAM, knowledge, or advisor threads.
- **Next action:** Pass 5 scope: build the connection layer between projects and other entities.

### 10. Roadmap / issue capture / prioritization mechanism
- **Covered:** YES — now fully audited
- **Where:** This addendum
- **Evidence of what exists:**
  - `collab_next_actions` (cis_memory.db, 6 rows): Priority-ordered action items with status, related_task
  - `collab_open_questions` (cis_memory.db, 8 rows): Numbered questions with status
  - `collab_decisions` (cis_memory.db, 12 rows): Dated decisions
  - `tasks` (cis_memory.db, 35 rows): All "open", all for one project
  - `execution_jobs` (cis_memory.db, 16 rows): Queued jobs with priority, retries
  - `live_sessions` (cis_memory.db, 36 rows): Old problem/solution tracking
  - ReviewQueue page (ReviewQueue.jsx, 173 lines): Approve/reject for ingest items — NOT a bug tracker
  - No table for: bugs, features, roadmap items, blockers, or deferred UX issues
- **Gap:** No unified issue/roadmap capture mechanism. The pieces exist (tasks, next_actions, open_questions) but no single view or categorization system.
- **Next action:** Design a unified issue/roadmap table in the unified database. Not in Pass 5 scope — defer to Pass 6 or standalone UX pass.

### 11. Navigation separation between standalone tools and workflow systems
- **Covered:** YES
- **Where:** Section 6
- **Evidence:** 11 flat nav items mixing categories. No visual hierarchy.
- **Gap:** No regrouping proposal made.
- **Next action:** Defer to consolidated UX pass.

### 12. Schedule/calendar vs project milestones
- **Covered:** YES — now fully audited
- **Where:** This addendum (item 9)
- **Evidence:** `schedule_slots` table exists in cis_app.db with proper schema (name, start, end, duration, category, project_id, status, notes) but has 0 rows. `projects` table has target_date field but no milestone sub-table.
- **Gap:** Schedule infrastructure exists but is unused. No milestone concept at all.
- **Next action:** Pass 6 scope. Requires projects to be functioning first.

### 13. DAM relationship to Projects
- **Covered:** YES — now fully audited
- **Where:** This addendum (items 5-6)
- **Evidence:** `assets` table in cis_app.db has `project_id` TEXT column. 254 assets exist, all are LMS course video lessons. No general-purpose DAM assets. No asset types beyond "video." DamPage.jsx (173 lines) shows filterable asset list with create/edit/delete.
- **Gap:** Assets are de facto LMS content, not a general DAM. The table schema supports general DAM but the data is all LMS lessons.
- **Next action:** Decide whether to keep LMS content in the assets table or create a separate LMS lessons table. Not blocking Pass 5.

### 14. DAM relationship to Knowledge Base
- **Covered:** YES
- **Where:** Sections 5, 7
- **Evidence:** No relationship exists. Assets (cis_app.db) and knowledge_spines/spine_nodes (cis_memory.db) are in different databases with no cross-reference columns.
- **Gap:** Complete.
- **Next action:** Defer to Pass 6.

### 15. Learn/LMS relationship to Knowledge Base and VDB
- **Covered:** YES — now fully audited
- **Where:** This addendum
- **Evidence:**
  - LearningPage.jsx (310 lines): Full LMS UI with course browser, search, scan, index, schedule-study functions
  - Backend: `lms_api.py` — courses, search (ChromaDB-powered), scan (filesystem), index (ChromaDB), suggest, schedule
  - LMS data stored as projects + assets in cis_app.db (31 courses as projects, 254 lessons as assets)
  - ChromaDB at /mnt/projects/cis/memory/chromadb/ (17MB) used for LMS search
  - knowledge_spines (1,536 rows) and spine_nodes (8,142 rows) exist in cis_memory.db — these are from the extraction pipeline, NOT from LMS
  - No connection between LMS courses and knowledge spines
- **Gap:** LMS and knowledge spine systems evolved separately. They share ChromaDB as a search backend but have no cross-referencing. LMS courses are not connected to knowledge spines, and knowledge spines don't reference LMS content.
- **Next action:** Decide whether LMS courses should be a subset of the knowledge spine system or a parallel system. Defer to Pass 6.

### 16. Knowledge/VDB current state
- **Covered:** YES
- **Where:** Sections 5, 8
- **Evidence:** ChromaDB at /mnt/projects/cis/memory/chromadb/ (17MB, 1 collection). 14,770 memory_records in cis_memory.db. 1,536 knowledge_spines with 8,142 spine_nodes. Hybrid FTS5 + ChromaDB in unified memory system.
- **Gap:** Knowledge is indexed but not surfaced in project context. No "while working on project X, here's what you already know" functionality.
- **Next action:** Defer to Pass 6.

### 17. Moonlight/Sunshine enablement
- **Covered:** NO — not covered in original report. Now audited.
- **Evidence:**
  - Sunshine installed: `/usr/bin/sunshine` v2025.924.154138
  - Configuration at `~/.config/sunshine/` (sunshine.conf, apps.json, credentials)
  - No systemd service for Sunshine (not in user or system scope)
  - No process running, no port listening
  - Moonlight is the client-side app — not relevant on the server
  - Sunshine is a game-streaming host (Moonlight server). Installed but dormant.
- **Gap:** Not integrated with CIS. No CIS service depends on it. Could be repurposed for remote desktop/streaming access to CIS but currently unused.
- **Next action:** If remote access to CIS desktop is needed, enable Sunshine as a systemd service. Otherwise, it's dormant infrastructure. Not blocking anything.

### 18. Hardcoded absolute paths
- **Covered:** YES
- **Where:** Section 8, "Local-Only Coupling Points"
- **Evidence:** 20+ instances across 10+ files. Mapped with severity levels.
- **Gap:** Complete count would require scanning all 50+ runtime Python files.
- **Next action:** Before distribution: replace with env vars or config. Not blocking Pass 5.

### 19. Local-only infrastructure coupling
- **Covered:** YES
- **Where:** Section 8
- **Evidence:** Mapped all coupling categories with severity.
- **Gap:** None significant.
- **Next action:** Documented. No immediate action.

### 20. Docker/distributable readiness
- **Covered:** YES
- **Where:** Section 9, "Portability/Distribution Gaps"
- **Evidence:** 8 blocking items identified.
- **Gap:** No Docker Compose or containerization exists yet.
- **Next action:** Not in Pass 5 scope. After database unification and path abstraction.

### 21. Private Studio OS vs Public/Reputation Track separation
- **Covered:** YES
- **Where:** Section 9 under "Separation strategy"
- **Evidence:** Identified two layers. Private = Hermes profiles, local Qwen, Proxmox, file watchers. Extractable = Flask + React app, DB schema, deliberation pipeline.
- **Gap:** No formal separation yet — everything is intermingled.
- **Next action:** After database unification and path abstraction, begin extracting the portable layer.

### 22. Self-contained project apps/products possibility
- **Covered:** PARTIAL
- **Where:** Strategic framing section (top of original report)
- **Evidence:** The concept was framed but no specific candidates were evaluated against this criteria.
- **Gap:** The Advisor Chat deliberation pipeline could become a self-contained app if the agent backends were configurable. CIS itself is too large to be a single self-contained app but individual pages (DAM browser, LMS viewer, spine explorer) could be extracted.
- **Next action:** Defer until after database unification and path abstraction.

### 23. CIS framework/template possibility
- **Covered:** PARTIAL
- **Where:** Strategic framing section
- **Evidence:** Concept was framed but no template structure defined.
- **Gap:** A CIS framework would need: unified database schema, abstracted paths, configurable agent backends, documentation. None exist yet.
- **Next action:** After database unification, design the schema as a standalone template. Not in Pass 5 scope.

### 24. Public extraction candidates beyond Advisor Chat
- **Covered:** PARTIAL — named 3 candidates but could enumerate more
- **Where:** Section 10
- **Evidence:** Advisor Chat (top candidate), CIS Schema (after Pass 5-6), Knowledge Spines.
- **Additional candidates now identified:**
  4. **LMS/Learning Hub** — Course browser with ChromaDB search, filesystem scan, indexing. Already functional (LearningPage.jsx, 310 lines; lms_api.py). Coupled to cis_app.db for course/asset storage.
  5. **DAM Browser** — Filterable asset library with type classification. Coupled to cis_app.db.
  6. **Spine Explorer** — Interactive knowledge graph viewer (iframe embedding React Flow at /ui/). Coupled to cis_memory.db for spines/nodes.
- **Gap:** Original report only listed 3 candidates.
- **Next action:** LMS and DAM are strong extraction candidates because they're self-contained pages with clear APIs. Document after database unification.

### 25. Whether Pass 5 should proceed, be reframed, or pause
- **Covered:** YES
- **Where:** Executive Summary + Section 12
- **Evidence:** Recommendation: PROCEED with reframing to "Project Scaffolding." Top risk: Proxmox snapshots. Top decision: database unification.
- **Gap:** Recommendation accounted for dual-DB split. With triple-DB split now confirmed, the unification decision is even more critical.
- **Next action:** Original recommendation STANDS but with increased urgency: database unification must address three databases, not two.

---

## Items Not Covered or Only Partially Covered

| # | Item | Status | Reason |
|---|------|--------|--------|
| 5 | Database split | UPGRADED | Originally reported as dual. Now confirmed as TRIPLE split (cis_memory.db + cis_app.db + runtime/db/cis_memory.db) |
| 10 | Roadmap/issue capture | NOW COVERED | Audited in this addendum — no unified mechanism exists |
| 12 | Schedule vs milestones | NOW COVERED | Audited — table exists (0 rows), no milestone concept |
| 15 | Learn/LMS vs VDB | NOW COVERED | Audited — LMS and knowledge spines are separate systems sharing ChromaDB |
| 17 | Moonlight/Sunshine | NOW COVERED | Sunshine installed but dormant, no CIS integration |
| 22 | Self-contained apps | PARTIAL | Concept framed, no candidates evaluated |
| 23 | Framework/template | PARTIAL | Concept framed, no structure defined |
| 24 | Extraction candidates | UPGRADED | 3 additional candidates identified (LMS, DAM, Spine Explorer) |

---

## Updated Recommendation

The original recommendation STANDS: Pass 5 should proceed, reframed as "Project Scaffolding." However, with the triple-database split now confirmed, the unification decision is more urgent than originally reported.

**Revised severity:**
- Proxmox snapshots: BLOCKING (unchanged)
- Triple database split: BLOCKING for Pass 5 schema work (upgraded from HIGH)
- 8 zero-byte stale .db files: MEDIUM (unchanged)

**Addendum file:** `/mnt/projects/cis/docs/CIS_CURRENT_STATE_AUDIT_2026-05-24_ADDENDUM.md`
