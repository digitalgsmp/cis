# CIS-PASS5-PLANNING-001 — Project Scaffolding & Database Unification Decision Gate

**Date:** 2026-05-24
**Status:** PLANNING — no implementation authorized

---

## 1. Executive Recommendation

**Pass 5 should proceed with `memory/cis_app.db` as the canonical app database.** The Advisor Chat runtime DB should remain separate with a lightweight link field added to `idea_drafts` pointing into the app DB. No migration of Advisor Chat data into the app DB at this stage. The legacy `memory/cis_memory.db` should be treated as archive/reference — queried but never written by new Pass 5 code.

The existing `projects` table in `cis_app.db` is structurally sound but semantically mixed: 31 of 33 projects are LMS courses. A `type` field already exists and is populated — the scaffolding is present but needs hardening with a CHECK constraint to prevent future conflation.

**Implementation gate:** Do not implement until Eric approves. Local + Google Drive backups confirmed. Proxmox snapshot risk remains open.

---

## 2. Canonical Database Recommendation

**Recommendation:** `memory/cis_app.db` becomes the canonical app database.

### Rationale

| Criterion | cis_app.db | runtime/db/cis_memory.db | memory/cis_memory.db |
|-----------|-----------|--------------------------|---------------------|
| Has ideas table | ✅ (6 rows) | ❌ | ❌ |
| Has projects table | ✅ (33 rows) | ❌ | ❌ |
| Has assets table | ✅ (254 rows) | ❌ | ❌ |
| Has schedule table | ✅ (0 rows — ready) | ❌ | ❌ |
| Has domains table | ✅ (5 rows) | ❌ | ❌ |
| Has users/permissions | ✅ | ❌ | ❌ |
| Has advisor data | ❌ | ✅ | ❌ |
| Has knowledge spines | ❌ | ❌ | ✅ (1,536 spines) |
| Active app endpoints use it | ✅ (app_api.py → cis_db.py) | ✅ (advisor.py) | ✅ (collab, spines, tasks) |

cis_app.db is the only database that holds the complete app-layer domain: ideas → projects → assets → schedule → domains → users. It is the natural home for project scaffolding.

### Risks

- **Advisor Chat data stays separate:** `idea_drafts` in the runtime DB cannot have a SQL foreign key into `cis_app.db` projects. Mitigation: use a TEXT `promoted_project_id` column in `idea_drafts` that stores the project ID string from cis_app.db. Enforce referential integrity in application code, not SQLite.
- **Legacy DB stays legacy:** The 40MB cis_memory.db has knowledge spines (1,536), spine nodes (8,142), collab rounds (29), and tasks (35). These are NOT migrating now. New code reads from it but never writes to it for Pass 5.

---

## 3. Database Boundary Map

```
┌─────────────────────────────────────────────────────────┐
│                   CIS Application                        │
│                                                         │
│  ┌──────────────────────┐    ┌──────────────────────┐   │
│  │  cis_app.db (2MB)    │    │ runtime/db/          │   │
│  │  CANONICAL APP DB    │    │ cis_memory.db (200K) │   │
│  │                      │    │ ADVISOR CHAT ONLY    │   │
│  │  ideas (6)           │    │                      │   │
│  │  projects (33)       │◄───│  idea_drafts (3)     │   │
│  │  assets (254)        │link│  advisor_threads (9) │   │
│  │  schedule_slots (0)  │    │  advisor_messages    │   │
│  │  domains (5)         │    │    (267)             │   │
│  │  users (0)           │    │  reconciliations (2) │   │
│  │  permissions (0)     │    │  external_reviews(0) │   │
│  │  idea_attachments(4) │    │  agent_instances (4) │   │
│  └──────────────────────┘    └──────────────────────┘   │
│           │                                             │
│           │  reads only (Pass 6+)                       │
│           ▼                                             │
│  ┌──────────────────────┐                               │
│  │ cis_memory.db (40MB) │                               │
│  │ LEGACY / ARCHIVE     │                               │
│  │                      │                               │
│  │  knowledge_spines    │                               │
│  │  spine_nodes         │                               │
│  │  collab_rounds (29)  │                               │
│  │  tasks (35)          │                               │
│  │  models (12)         │                               │
│  │  memory_records      │                               │
│  │  (14,770)            │                               │
│  │  ... 20+ more tables │                               │
│  └──────────────────────┘                               │
│                                                         │
│  ChromaDB: /mnt/projects/cis/memory/chromadb/ (17MB)    │
└─────────────────────────────────────────────────────────┘

Link direction: idea_drafts.promoted_project_id → projects.id
(application-level, not SQL FK — cross-database)
```

---

## 4. idea_drafts Conflict Summary

### Only one `idea_drafts` table exists

| Property | Runtime DB | cis_app.db |
|----------|-----------|------------|
| Table exists? | ✅ `idea_drafts` | ❌ (has `ideas`, different table) |
| Schema | 16 columns: id, title, summary, intent, domain, domain_source, open_questions, suggested_next_step, source_thread_id, source_message_ids, input_scope, structuring_agent, structuring_model, status, created_at, updated_at | N/A |
| Rows | 3 | N/A |
| Status values | `reviewing` (2), `dismissed` (1) | N/A |
| Source | All 3 from thread #4 (052226_test001) | N/A |

### The `ideas` table in cis_app.db is a different concept

| Property | cis_app.db `ideas` |
|----------|-------------------|
| Schema | 18 columns: id, name, link, date, description, context, domain, category, medium, story_type, user_level, tags, status, owner_id, created, updated, content, file_path |
| Rows | 6 |
| Status values | `promoted` (3), `captured` (3) |
| Source | User-entered via Ideas page, not structured from Advisor Chat |

### Conflict resolution

These are NOT duplicate tables — they are parallel systems. `idea_drafts` is the AI-structured deliberation output. `ideas` is the user-curated idea bank. They serve different purposes and should NOT be merged.

**Recommendation:** Keep both. Add `promoted_project_id TEXT` to `idea_drafts` for the link to `cis_app.db.projects`. When a draft promotes, create a project in `cis_app.db` and write its ID back to the draft. The `ideas` table in cis_app.db can also link to projects via existing `source_idea_id` on the projects table.

---

## 5. Existing Projects/Assets Breakdown

### Projects — by `type` field

The `type` column already exists and is populated:

| type | Count | Examples |
|------|-------|----------|
| `course` | 31 | Blender courses, digital painting, Nuke, DaVinci Resolve, Cascadeur |
| `infrastructure / system` | 2 | CIS Kernel v1, Social Work App |
| `new creation` | 1 | Catch This Falling Star — Song Animation |

### Projects — by `domain` field

| domain | Count |
|--------|-------|
| image | 26 |
| action | 4 |
| creative | 1 |
| socialcare | 1 |
| technical | 1 |

### Projects — by `status`

| status | Count |
|--------|-------|
| initiated | 32 |
| active | 1 |

### Real vs. LMS breakdown

| Category | Count | ID pattern |
|----------|-------|------------|
| LMS courses | 31 | `course_*` |
| Real projects | 3 | `proj_*` |
| — CIS Kernel v1 | 1 | `proj_20260515T221108.840507` |
| — Catch This Falling Star | 1 | `proj_20260516T173903.084579` |
| — Social Work App | 1 | `proj_20260518T174629.620886` |

### Assets — by `type`

| type | Count |
|------|-------|
| video | 162 |
| learning | 71 |
| resource | 12 |
| reference | 9 |

### Assets — project linkage

| Metric | Value |
|--------|-------|
| Total assets | 254 |
| Assets with non-empty `project_id` | 254 (100%) |
| Assets linked to course-type projects | 254 (100%) |
| Assets linked to real projects | 0 |
| Foreign key constraint | ❌ No SQL FK — `project_id` is TEXT with no REFERENCES clause |

**Critical finding:** All 254 assets are LMS video lessons linked to course-type projects. Zero assets belong to the three real projects (CIS Kernel, Falling Star, SWA). This confirms the LMS conflation: the assets table is de facto an LMS lessons table.

### Candidate project type mapping

| Candidate type | Maps to existing? | Evidence |
|---------------|-------------------|----------|
| creative project | ✅ `new creation` | Catch This Falling Star |
| CIS development task | ✅ `infrastructure / system` | CIS Kernel v1 |
| course/LMS item | ✅ `course` | 31 courses |
| product/app | ✅ `infrastructure / system` | Social Work App |
| infrastructure task | ✅ `infrastructure / system` | CIS Kernel v1 |

The `type` field already distinguishes the five categories but the values are ad-hoc strings. Recommending a CHECK constraint with a controlled vocabulary.

---

## 6. Minimal Project Scaffold Recommendation

### What exists and is usable

The `projects` table in `cis_app.db` already has the right structure:

```sql
projects (
    id, name, owner, owner_id, start_date, due_date,
    level, type, goal, domain, description,
    source_idea_id,      -- already links to ideas!
    status, progress,
    linked_research,     -- JSON array, reserved for DAM
    linked_references,   -- JSON array, reserved for KB
    linked_learning,     -- JSON array, reserved for Learn/LMS
    linked_templates,    -- JSON array
    linked_checklists,   -- JSON array
    schedule_slots,      -- JSON array, reserved for Schedule
    created, updated
)
```

### What Pass 5 needs to add

**Minimal — no schema migration, only data hardening:**

1. **Add `promoted_project_id TEXT` to `idea_drafts`** (runtime DB) — links a draft to its promoted project in cis_app.db. This is the cross-DB bridge.

2. **Harden the `type` field with controlled values** — add application-level validation (not a SQL CHECK yet, to avoid migration risk on existing data). Recognized types:
   - `creative` — creative production project (song, film, artwork, poem)
   - `development` — CIS/SWA development task
   - `course` — LMS learning item
   - `product` — distributable app/product
   - `infrastructure` — system config, deployment, maintenance

   Existing values map: `new creation` → `creative`, `infrastructure / system` → `development` or `infrastructure` (Eric decides), `course` → `course` (no change).

3. **Add `draft_source TEXT` to `projects`** — stores which system created the project: `advisor_chat`, `ideas_page`, `lms_scan`, `manual`. This preserves provenance without requiring cross-DB joins.

### What NOT to add in Pass 5

- DAM asset tables (use existing `assets` table, add real project assets later)
- Knowledge base tables (query legacy DB in Pass 6)
- Schedule/milestone sub-tables (use existing `schedule_slots`)
- Issue/task tracking (use existing `tasks` in legacy DB, bridge in Pass 6)
- Full LMS/course redesign (separate project — Pass 6+)

---

## 7. Promotion Path Recommendation

### Flow

```
Advisor Chat discussion
  → Phase 4 Auto-Structure → idea_draft (status: structured)
  → Human review → idea_draft (status: reviewed)
  → Promote action → project created in cis_app.db
  → idea_draft.promoted_project_id = project.id
  → idea_draft status → promoted
  → project.status → initiated
```

### Promotion method: **COPY + LINK**

- **Copy** the draft's title, summary, domain, and intent into the project's name, description, domain, and goal fields
- **Link** via `idea_drafts.promoted_project_id` → `projects.id` and `projects.draft_source = 'advisor_chat'`
- **Do not move or delete** the draft — it remains as an audit trail of the deliberation
- **Do not archive** the draft automatically — archiving is a separate human decision

### Status lifecycle

| Status | Set on | Meaning |
|--------|--------|---------|
| `structured` | Auto-Structure completes | AI has extracted a draft from deliberation |
| `reviewed` | Human clicks "Review Complete" | Draft has been reviewed and is ready for promotion |
| `promoted` | Human clicks "Promote to Project" | A project has been created from this draft |
| `dismissed` | Human clicks "Dismiss" | Draft was considered and rejected — kept for audit |
| *(project side)* | | |
| `initiated` | Project created from draft | Scaffold exists, no work started |
| `active` | Human sets | Work in progress |
| `completed` | Human sets | Project finished |
| `archived` | Human sets | Retained for reference |
| `deferred` | Human sets | Not now, maybe later |

---

## 8. Risks and Non-Goals

### Risks

1. **LMS conflation:** The current `assets` table is 100% LMS content. If Pass 5 adds creative project assets without a `project_type` filter, the DAM page will show blender tutorials alongside song lyrics. Mitigation: filter assets by project type in the UI, not by creating a separate assets table.

2. **Cross-DB referential integrity:** `idea_drafts.promoted_project_id` cannot be a SQL FK. If a project is deleted in cis_app.db, the draft's link becomes dangling. Mitigation: application-level validation on project delete — check for backlinks.

3. **Type field inconsistency:** The existing `type` field has ad-hoc values (`new creation`, `infrastructure / system`, `course`). Until Eric approves a controlled vocabulary, new promotion code should write consistent values but not retroactively change the 33 existing rows.

4. **Proxmox snapshots:** Still the top infrastructure risk. Any schema change, even adding one column, should wait for explicit Eric approval after snapshot resolution.

### Non-Goals (explicitly deferred)

- Full DAM redesign
- Knowledge base integration (Pass 6)
- LMS/course separation from projects (Pass 6)
- Schedule/milestone engine (Pass 6)
- Issue/roadmap tracker (Pass 6)
- Docker/distribution packaging
- UI layout redesign
- Nav hierarchy reorganization

---

## 9. Decisions Eric Must Make Before Implementation

| # | Decision | Options | Impact |
|---|----------|---------|--------|
| D1 | Approve `cis_app.db` as canonical app DB? | Yes / No / Different DB | Gates all Pass 5 work |
| D2 | Approve controlled `type` vocabulary? | `creative`, `development`, `course`, `product`, `infrastructure` — or Eric's preferred terms | Prevents semantic conflation |
| D3 | What to do with existing project `type` values? | (a) Retroactively normalize all 33 to new vocabulary, (b) Normalize only new projects going forward, (c) Leave all as-is | (b) is recommended — safest |
| D4 | Approve promotion method? | COPY + LINK (recommended) / MOVE / COPY + ARCHIVE | Affects audit trail |
| D5 | Approve `draft_source` field on projects? | Yes / No | Preserves provenance |
| D6 | Proxmox snapshot fixed? | Required before schema changes | Safety gate |

---

## 10. Recommended Next Step

1. Eric reviews this report and the ChatGPT/Claude feedback
2. Eric makes decisions D1–D6
3. Proxmox snapshot resolved (or explicit risk acceptance)
4. Pass 5 implementation begins: add `promoted_project_id` to `idea_drafts`, add `draft_source` to `projects`, build promotion endpoint, wire UI button
5. Defer all LMS/course separation to Pass 6

---

## Return Summary

- **Report file:** `/mnt/projects/cis/docs/CIS_PASS5_PLANNING_2026-05-24.md`
- **Recommended canonical DB:** `memory/cis_app.db`
- **Recommended Pass 5 scope:** Project Scaffolding — add cross-DB link column, promotion endpoint, type vocabulary hardening. No migration. No LMS separation yet.
- **Implementation wait for Proxmox snapshot?** YES — schema changes should wait. Planning is complete.
- **Current backup sufficient for planning?** YES — local + Google Drive both verified.
- **Projects semantically mixed with LMS?** YES — 31 of 33 are courses. The `type` field already distinguishes them but values are ad-hoc.
- **Assets link to projects?** YES — `project_id` TEXT field exists, all 254 assets linked to course-type projects. No SQL FK constraint. Zero assets linked to real projects. This is a de facto LMS lessons table, not a general-purpose DAM.
