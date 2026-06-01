# CIS Current-State Architecture Audit — May 24, 2026

**Audit:** CIS-AUDIT-001
**Status:** COMPLETE (read-only)
**Purpose:** Determine whether Pass 5 (Project Promotion) should proceed, be reframed, or be paused.

---

## 1. Executive Summary

CIS has evolved rapidly from a Flask dashboard experiment into a functional multi-model deliberation and creative production system. Advisor Chat is the most mature subsystem — a four-panel deliberation pipeline (Prime → R1 → V4-Pro → external escalation → reconciliation → Qwen execution) with verified backend routing, streaming, structured output parsing, and external review capture.

However, the system rests on infrastructure with no snapshot/backup safety net, two unconnected databases, 50+ runtime Python files with significant legacy cruft, and hardcoded paths that couple every component to Eric's specific Proxmox VM. The navigation bar mixes tool categories, project management, knowledge, and execution endpoints without hierarchy.

**Verdict:** Pass 5 can proceed, but only after the Proxmox snapshot risk is resolved and a schema unification decision is made. Reframe Pass 5 as "Project Scaffolding" rather than "Project Promotion" — build the project table and basic linking before wiring the full promotion pipeline.

---

## 2. Immediate Risks / Blockers

### 🔴 BLOCKING: Proxmox snapshots blocked — no backup safety net

**Evidence:**
- VM runs on virtio raw ext4 partitions (vda2, vdb, vdc, vdd, vde, vdf)
- `qemu-guest-agent` is NOT installed (`dpkg -l | grep qemu-guest` returns nothing)
- Without guest agent, Proxmox cannot freeze filesystems for consistent snapshots
- Root disk at 71% (139G free of 491G)
- `/mnt/models` at 91% (21G free of 229G) — near capacity

**Impact:** If the VM fails or storage corrupts, all CIS development since the last manual backup is lost. There is no rollback capability. Any further feature work accumulates risk on an un-snapshotable foundation.

**Recommended next action:** Install `qemu-guest-agent`, verify Proxmox can snapshot, take a snapshot before any Pass 5 work begins. If the underlying Proxmox storage type (directory-based?) doesn't support snapshots even with the agent, consider migrating the VM disk to LVM-thin or ZFS storage. This outranks all feature work.

### 🟡 HIGH: Dual-database architecture with no connection

**Evidence:**
- `/mnt/projects/cis/memory/cis_memory.db` (40MB, 30 tables) — used by `connection.py` / `config.py` for collab, projects, tasks, models, spines, drafts, decisions, captures, execution_jobs, live_sessions, manifests, etc.
- `/mnt/projects/cis/runtime/db/cis_memory.db` (200KB, 6 tables) — used by advisor.py, reconciliation.py, advisor_external.py, idea_drafts.py for advisor_threads, advisor_messages, advisor_reconciliations, advisor_external_reviews, idea_drafts, agent_instances
- `idea_drafts` exists in BOTH databases with different schemas (runtime: 7 columns, legacy: absent from the legacy DB)
- Advisor Chat cannot reference collab rounds, projects, tasks, or knowledge spines
- Projects cannot reference advisor threads or reconciliations

**Impact:** Pass 5 cannot wire idea_drafts to projects without deciding which database owns the relationship. All cross-domain queries (e.g., "show all advisor deliberations for project X") are impossible today.

### 🟡 MEDIUM: 8 zero-byte stale .db files confuse tooling

Locations: `/mnt/projects/cis/cis_memory.db`, `/mnt/projects/cis/cis_app.db`, `/mnt/projects/cis/runtime/cis.db`, `/mnt/projects/cis/runtime/cis_memory.db`, `/mnt/projects/cis/runtime/cis_live.db`, `/mnt/projects/cis/runtime/memory/cis_memory.db`, `/mnt/projects/cis/runtime/memory/hermes_memory.db`, `/mnt/projects/cis/memory/_archive/cis.db`

---

## 3. Current Runtime Map

| Service | Port | Process | Status | Autostart |
|---------|------|---------|--------|-----------|
| cis-flask | 5000 | app.py (pid 1508) | running | enabled |
| hermes-gateway (Prime/V4-Pro) | 8642 | gateway run (pid 11260) | running | enabled |
| hermes-gateway-r1 (R1) | 8643 | gateway run (pid 11322) | running | enabled |
| hermes-gateway-qwen (Worker) | 8644 | gateway run (pid 1516) | running | enabled |
| llama-server-qwen | 8002 | llama-server (pid 11372) | running, ctx 32768 | enabled |
| hermes-dashboard | — | TUI (pid 1519) | running | enabled |
| hermes-mcp-proxy | 8888 | mcp-proxy (pid 3779) | running | enabled |
| ollama | 11434 | ollama serve (pid 1498) | running | system-level |

All services confirmed surviving reboot after HHR-FIX-003 (May 24).

**Agent instances (runtime DB):**
| name | role | model | gateway |
|------|------|-------|---------|
| hermes-prime | coordinator | deepseek-v4-flash | :8642 |
| hermes-r1 | senior-advisor | deepseek-reasoner | :8643 |
| hermes-qwen | worker | qwen3-vl-30b (local) | :8644 |
| hermes-v4pro | deep-analyst | deepseek-v4-pro | :8642 |

---

## 4. Current File/App Map

### Active runtime: `/mnt/projects/cis/runtime/`

**Frontend (React/Vite):**
- `ui/src/App.jsx` — router, 11 nav items, topbar
- `ui/src/pages/AdvisorChat.jsx` (1096 lines) — 4-panel deliberation UI
- `ui/src/pages/ChatConsole.jsx` — collab round chat
- `ui/src/pages/IdeasPage.jsx` (521 lines)
- `ui/src/pages/ProjectsPage.jsx` (194 lines)
- `ui/src/pages/SchedulePage.jsx` (195 lines)
- `ui/src/pages/DamPage.jsx` (173 lines)
- `ui/src/pages/LearningPage.jsx` (310 lines)
- `ui/src/pages/InfraPage.jsx` — infra subpages (CollabTracker, Hardware, Models, Services, Software, Storage)

**Backend (Flask):**
- `app.py` — 26 registered blueprints
- 30+ API files in `api/`

**Active API blueprints (advisor chat system):**
- `api/advisor.py` — Direct/Parallel chat, streaming, execute directive
- `api/reconciliation.py` — Reconcile synthesis from R1+V4-Pro+external reviews
- `api/advisor_external.py` — External review CRUD, escalation prompts
- `api/idea_drafts.py` — AI-suggested domain classification, Structure This

**Active API blueprints (collab/project infrastructure):**
- `api/collab.py` — collab_status, activity, agents, decisions, open_questions, next_actions
- `api/collab_rounds.py` — 7-step advisor round wizard, send-to-hermes, capture-exchange, final directives, handoff
- `api/app_api.py` — ideas, projects, assets, schedule, domains (REST CRUD)
- `api/projects.py` — legacy project routes

**Active API blueprints (knowledge/DAM/LMS):**
- `api/spines_api.py` — knowledge spine browsing
- `api/ingest_spines.py` — spine ingestion pipeline
- `api/lms_api.py` — LMS courses, search, scan, index, suggest, schedule
- `api/captures.py` — capture CRUD
- `api/models.py` — model inventory

**Legacy/experimental files in runtime (50+ files):**
- `cis_db.py` (28KB), `cis_verify.py` (69KB), `cis_ingest.py` (28KB), `cis_lms.py` (28KB), `cis_lms_log.md` (671KB), `extractor.py` (16KB), `hermes_chat.py` (13KB), `librarian.py` (15KB), `primer_update_v3.py` (18KB), `cis_review.py` (15KB), and 30+ more
- `_archive/` directory with further legacy files
- `ui_components/`, `ui_mockups/` — pre-React experimental UI

### Database files:

| Path | Size | Used By | Status |
|------|------|---------|--------|
| `/mnt/projects/cis/memory/cis_memory.db` | 40MB | connection.py, collab, projects, tasks, spines, models, drafts, decisions, captures, live_sessions, manifests, execution_jobs, extraction_runs | ACTIVE — legacy main DB |
| `/mnt/projects/cis/runtime/db/cis_memory.db` | 200KB | advisor.py, reconciliation.py, advisor_external.py, idea_drafts.py | ACTIVE — advisor chat DB |
| 8 other .db files | 0 bytes | nothing | STALE — zero-byte artifacts |

### ChromaDB:
- `/mnt/projects/cis/memory/chromadb/` — 17MB, 1 collection
- Connected to unified memory system (FTS5 + ChromaDB hybrid)
- 14,770 memory_records in legacy DB, 864 memory_sessions

---

## 5. Current Database/Schema Map

### Legacy DB (`memory/cis_memory.db`) — 30 tables:

| Table | Rows | Purpose |
|-------|------|---------|
| knowledge_spines | 1,536 | Knowledge spine records (domains/subjects) |
| spine_nodes | 8,142 | Individual nodes within spine trees |
| memory_records | 14,770 | Unified memory records (hybrid FTS5+VDB) |
| memory_sessions | 864 | Session metadata for memory records |
| live_sessions | 36 | Old live-collab sessions |
| live_rounds | 53 | Old live-collab rounds (gemini/claude/chatgpt) |
| collab_rounds | 29 | Advisor round wizard rounds |
| collab_session_imports | 11 | Imported Hermes session logs |
| collab_session_messages | 268 | Raw messages from imports |
| collab_activity | 66 | Activity log entries |
| collab_exchanges | 25 | Captured advisor exchanges |
| collab_final_directives | 6 | Final directive documents |
| collab_decisions | 12 | Structured project decisions |
| collab_open_questions | 8 | Structured open questions |
| collab_next_actions | 6 | Structured next actions |
| collab_agents | 5 | Collab agent definitions |
| collab_status | 1 | Current project status row |
| collab_files_changed | 0 | (empty — never populated) |
| decisions | 50 | General decisions |
| tasks | 35 | Task records |
| captures | 35 | Captured observations |
| drafts | 7 | Staged draft intake (ADR-048) |
| models | 12 | Model inventory |
| execution_jobs | 16 | Execution queue jobs (ADR-045) |
| extraction_runs | 2 | Extraction pipeline runs |
| insights | 1 | Insight records |
| session_log | 50 | Session log entries |
| manifests | 6 | Manifest records |
| corrections | 3 | Correction records |
| memory_archive_files | 0 | (empty) |
| segments | 0 | (empty — video segmentation) |
| schema_versions | 1 | Schema version tracking |
| migration_log | 1 | Migration tracking |

### Runtime DB (`runtime/db/cis_memory.db`) — 6 tables:

| Table | Rows | Purpose |
|-------|------|---------|
| advisor_messages | 267 | All advisor chat messages (user+assistant) |
| advisor_threads | 9 | Advisor chat threads |
| advisor_reconciliations | 2 | Reconciliation synthesis records |
| advisor_external_reviews | 0 | External (Claude/ChatGPT) review captures |
| idea_drafts | 3 | AI-structured idea drafts from deliberation |
| agent_instances | 4 | Gateway agent definitions |

### Missing relationships (gaps):
- advisor_threads ↔ collab_rounds: `round_id` FK column exists but round 9 was created for testing, no real linkage
- advisor_messages ↔ projects: no project_id column
- idea_drafts ↔ projects: no promotion path
- idea_drafts ↔ ideas (in app_api): different databases, different schemas
- knowledge_spines ↔ projects: spine records have no project association
- memory_records ↔ advisor_threads: no linkage
- captures ↔ projects: `project_id` TEXT column exists, unknown if populated
- tasks ↔ projects: `project_id` TEXT column exists
- DAM/assets: handled by app_api.py against legacy DB, but `asset` table not found in schema dump — may use file-based storage

---

## 6. Current Feature/Navigation Map

**Navigation bar (App.jsx):** Ideas, Projects, Schedule, DAM, Learn, Review, Ingestion, Map, Infra, Chat, Advisor Chat

**Category analysis:**

| Category | Nav Items | Status |
|----------|-----------|--------|
| Creative tools | Advisor Chat, Chat | MATURE — fully functional |
| Project management | Ideas, Projects, Schedule | PARTIAL — pages exist, backend routes exist, no cross-linking |
| Asset management | DAM | PARTIAL — page exists (173 lines), backend routes in app_api.py |
| Knowledge/Learning | Learn, Map, Ingestion, Review | SCAFFOLD — pages exist, some backend (spines, LMS), no project integration |
| Infrastructure | Infra | FUNCTIONAL — CollabTracker, Hardware, Models, Services, Software, Storage subpages |

**Mixed categories in single nav bar:** The 11 nav items combine execution tools (Chat, Advisor Chat), project management (Ideas, Projects, Schedule), knowledge (Learn, Map), intake (Ingestion, Review), assets (DAM), and infrastructure (Infra). There is no visual hierarchy separating "tools I use right now" from "things I manage over time."

---

## 7. Workflow Gaps

**Intended flow (from Eric's directive):**
1. Start with Prime chat to talk through an idea
2. Refer to R1 for deep reasoning
3. Refer to V4-Pro for deep analysis
4. Escalate to Claude/ChatGPT if confidence is low
5. Structure the idea
6. Promote into a project
7. Attach research, references, DAM assets, code, models, tutorials, outputs
8. Connect project work to reusable knowledge and future learning

**Current state:**

| Step | Status | Gap |
|------|--------|-----|
| 1-3 (Deliberation) | ✅ COMPLETE | Direct + Parallel + Reconcile modes all verified |
| 4 (External escalation) | ⚠️ PARTIAL | External review capture endpoint exists, but 0 rows. Manual paste workflow only — no live API routing. |
| 5 (Structure idea) | ✅ COMPLETE | Phase 4 Auto-Structure with idea_drafts table and domain classification |
| 6 (Promote to project) | ❌ MISSING | No promotion path. idea_drafts → projects pathway does not exist. This IS Pass 5. |
| 7 (Attach assets/knowledge) | ❌ MISSING | No cross-referencing. Projects don't link to DAM assets, knowledge spines, or advisor threads. |
| 8 (Reusable knowledge) | ❌ MISSING | knowledge_spines and spine_nodes (8,142 nodes) exist but are not queryable from project context. No "show me relevant tutorials for this project" functionality. |

---

## 8. Local-Only Coupling Points

Every component that would need abstraction for portability:

| Coupling | Location | Severity |
|----------|----------|----------|
| Absolute paths `/mnt/projects/cis/` | Every API file, app.py, config.py, collab_rounds.py, systemd services | CRITICAL — 20+ hardcoded paths |
| Absolute paths `/mnt/archive/` | app.py, app_api.py | HIGH |
| Absolute paths `/home/eric/` | collab_rounds.py (session imports, handoff text), cis-flask.env | HIGH |
| Localhost ports (8642, 8643, 8644, 8002) | advisor.py, collab_rounds.py, advisor_external.py | HIGH — would need env vars or config |
| API_SERVER_KEY in cis-flask.env | /home/eric/.config/cis-flask.env | HIGH — secret management |
| DEEPSEEK_R1_KEY in cis-flask.env | /home/eric/.config/cis-flask.env | HIGH |
| Hermes gateway profiles (~/.hermes, ~/.hermes-r1, ~/.hermes-qwen) | systemd service files, advisor.py env_path | HIGH — multi-profile architecture |
| RTX 4090 / GPU assumption | llama-server-qwen.service (--n-gpu-layers -1 = full offload) | MEDIUM — Qwen could run CPU-only with different flags |
| systemd user services | 12 service files in ~/.config/systemd/user/ | MEDIUM — Docker Compose would replace this |
| Proxmox VM / virtio disks | vda, vdb, vdc, vdd, vde, vdf block devices | LOW — only relevant if whole VM is distributed |
| chroma.sqlite3 at fixed path | /mnt/projects/cis/memory/chromadb/ | MEDIUM — path in unified memory config |

---

## 9. Portability/Distribution Gaps

### What blocks a Docker deployment today:
1. **Dual database architecture** — which DB gets mounted where?
2. **Hardcoded absolute paths** — 20+ instances across 10+ files
3. **Multi-gateway profile architecture** — three Hermes instances with separate HOME dirs would need container orchestration
4. **Local model dependency** — Qwen on port 8002 requires GPU or CPU llama.cpp setup
5. **API keys in env files** — no secrets management abstraction
6. **systemd assumptions** — 12 service files, no Docker Compose equivalent
7. **File watchers** — cis_download_watcher.py, incoming_watcher.py, watcher.py all assume local filesystem

### What blocks another person from running CIS:
All of the above, plus:
- Hermes Agent installation required (not pip-installable for external users)
- DeepSeek API key required for Prime, R1, V4-Pro
- Multi-profile Hermes setup undocumented for external use
- No setup script, no requirements.txt audit, no environment bootstrap
- 50+ legacy Python files in runtime/ with unclear dependency chains

### Separation strategy:
CIS naturally splits into two layers:
1. **Private Studio OS** — Eric's personal infrastructure (Hermes profiles, local Qwen, Proxmox VM, file watchers, systemd services, specific file paths). This stays on the VM.
2. **Extractable CIS App** — The Flask + React application, database schema, API blueprints, deliberation pipeline, project management, and UI. This could be packaged.

---

## 10. Public Extraction Candidates

### Candidate 1: Advisor Chat Deliberation Pipeline ⭐ TOP CANDIDATE

**Component:** Prime → R1 → V4-Pro → external escalation → reconciliation → Worker execution

**Why it has value:** A structured, multi-model deliberation system with parallel compare, reconciliation synthesis, divergence mapping, and gated execution. This is novel — most AI tools are single-model chat. This is a deliberation harness.

**Current coupling:**
- Hardcoded gateway URLs (127.0.0.1:8642/8643/8644)
- API keys embedded in env file paths
- Agent definitions hardcoded in agent_instances table
- Qwen worker assumes local llama.cpp server
- Database path hardcoded

**What would need abstraction:**
- Agent registry → config file or env vars instead of SQLite table
- Gateway URLs → configurable endpoints
- Worker backend → pluggable (local llama, remote API, Docker container)
- DB path → env var or config

**Extraction form:** Reference implementation + case study + blog post. Not a standalone app (depends on multiple LLM backends). Could become a template for others building multi-model deliberation systems.

### Candidate 2: CIS Schema + Project Management

**Component:** Ideas → Structure → Promote → Project → Tasks → Schedule → DAM

**Why it has value:** Creative project management with AI-assisted structuring. Bridges the gap between "chat about an idea" and "structured project with assets and schedule."

**Current coupling:** Dual DB, no cross-linking, pre-Pass-5

**Extraction form:** Framework/template after Pass 5-6 completion.

### Candidate 3: Knowledge Spine System

**Component:** knowledge_spines + spine_nodes (1,536 spines, 8,142 nodes) — hierarchical knowledge trees with domain classification

**Why it has value:** A structured alternative to flat vector search. Hierarchical knowledge with parent/child relationships for tutorial content and reference material.

**Current coupling:** Legacy DB only, no project integration

**Extraction form:** Standalone library or reference implementation.

---

## 11. Architecture Decisions Needed Before Pass 5

1. **Database unification:** Merge runtime DB into legacy DB, or promote runtime DB to primary and migrate legacy tables? The advisor chat system (runtime DB) is the active development surface, but the legacy DB holds 30 tables of accumulated data.

2. **`idea_drafts` ownership:** Which DB owns the canonical idea_drafts table? Currently two different schemas exist. Pass 5 promotion needs a single source of truth.

3. **Project table design:** What columns does a "project" need to bridge idea_drafts, advisor_threads, knowledge_spines, DAM assets, schedule slots, and tasks? Design this before coding promotion.

4. **Nav hierarchy:** Should the 11 nav items be regrouped into logical sections before Pass 5, or after? Eric's layout concern (Prime in bottom-left) is part of a larger UX question.

5. **Proxmox snapshot resolution:** Must happen before any Pass 5 database or schema changes. Cannot risk development on an un-snapshotable VM.

---

## 12. Recommended Next Three Actions

1. **Install qemu-guest-agent and take a Proxmox snapshot** — this is the single highest-priority action. All feature work is unsafe until this is resolved.

2. **Decide database unification strategy** — merge runtime DB into legacy DB or vice versa. This decision gates all Pass 5 schema work.

3. **Reframe Pass 5 as "Project Scaffolding"** — build the project table in the unified database, create the idea_draft → project promotion path, and add basic project detail view. Defer full DAM/knowledge/schedule wiring to Pass 6.

---

## Report Metadata

- **Report file:** `/mnt/projects/cis/docs/CIS_CURRENT_STATE_AUDIT_2026-05-24.md`
- **Pass 5 recommendation:** PROCEED (reframed as Project Scaffolding, not full Project Promotion)
- **Top immediate risk:** Proxmox snapshots blocked — no backup/rollback capability
- **Top architecture decision needed:** Database unification (dual DB → single DB)
- **Top public extraction candidate:** Advisor Chat Deliberation Pipeline (multi-model deliberation harness)
