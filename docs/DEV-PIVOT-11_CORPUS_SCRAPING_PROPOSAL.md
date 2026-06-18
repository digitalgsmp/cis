# Proposal: Corpus Scraping & Intent Extraction for Build Plan Foundation

**Author:** hermes-r1 (Reviewer), per Eric's direction
**Date:** 2026-06-18
**Status:** DRAFT
**Purpose:** Identify and catalog all source material containing Eric's verbatim intent, then produce a build plan based on Eric's actual words — not enterprise dev assumptions from training data.

---

## 0. Core Finding: Legacy Files ≠ Session Files

The session files capture recent development iteration. The **legacy files in `/mnt/archive/`** are the foundation — Eric's original project definitions, creative infrastructure, and idea knowledge base. These files predate Hermes and contain the vision that sessions have been orbiting. Extraction must prioritize legacy files; sessions supplement.

## 1. Corpus Inventory

### 1.1 Live Storage

| Location | Size | Contents |
|---|---|---|
| `/mnt/projects/cis/` | ~250GB partition | CIS project: 65 docs, 364MB spine DB, pipeline scripts, UI, HCP exports |
| `/mnt/archive/` | 9.1TB (8TB used) | WIAS domain directories, CIS backups, business docs, client files |
| `/mnt/cache/` | 111.8GB | SSD cache |
| `/mnt/models/` | 232.9GB | AI models |
| `/mnt/models2/` | 232.4GB | AI models (secondary) |

### 1.2 Hermes Session Files

| Profile | Path | Count | Size |
|---|---|---|---|
| Prime (V4 Pro) | `~/.hermes/sessions/` | 4 `.jsonl` files | 409MB |
| R1 (Reviewer) | `~/.hermes-r1/sessions/` | 2 `.jsonl` files | 104MB |
| Qwen | `~/.hermes-qwen/sessions/` | 0 | — |
| V4 Implementer | `~/.hermes-v4impl/sessions/` | 3 `.jsonl` files | unknown |

Each `.jsonl` file contains turn-by-turn conversation records (role: user/assistant/tool). Eric's messages are tagged `role: "user"`.

### 1.3 CIS Database (cis_memory.db, 364MB)

Relevant tables for intent extraction:

| Table | What it holds |
|---|---|
| `project_decisions` | ADR records, decision text |
| `open_questions` | Unresolved questions, many in Eric's framing |
| `next_actions` | Build direction, next steps |
| `build_plan_nodes` | Current build state |
| `workflow_runs` | Pipeline run history with topics |
| `deliberation_rounds` | Drafter/Reviewer exchange history |
| `lifecycle_events` | State transitions |
| `session_closeouts` | Session close records with generated context |

### 1.4 Archive Structure — WIAS Development Files

**Location:** `/mnt/archive/WIAS/`

| Directory | Contents | Relevance |
|---|---|---|
| `0admin/` | WIAS Project Manager.xlsx (705KB), WIAS Project App.xlsx (187KB), WIAS Project Manager v1 (746KB) | **PRIMARY** — WIAS project definition spreadsheets |
| `1life/` | Life domain: 1space, 2mind, 3body | Life management structure |
| `2production/` | Production pipeline: 1word, 2image, 3action, 4sound, 5web, 6products | WIAS creative production workflow |
| `3ideabank/` | Idea definitions + ideas (A-Z catalog) | Creative ideas to be developed through WIAS/CIS |
| `WIAS/` | WIAS Project App.xlsx (187KB), WIAS Project Manager.xlsx (705KB), WIASProjects.xlsx (748KB) | Duplicate/versioned spreadsheets |

### 1.5 CIS Plain Language Build Files

**Location:** `/mnt/projects/cis/`

| File | Size | Description |
|---|---|---|
| `docs/architecture_atlas/original_CISChats/CIS_Canonical_Build_Sequence_Plain_Language.md` | 35KB / 399 lines | Original plain language build roadmap — Phases PD through 2, factory analogy, every beam and pipe named |
| `cis_kernel/extraction/functional_intents/cis_plain_language_build_roadmap_extraction_analysis.md` | — | Extraction analysis of the roadmap |
| `cis_kernel/identity/intent.md` | 13 bytes | Stub file |

### 1.6 SWA Development Files

**Location:** `/mnt/projects/swa/social_work_ai/`

| Component | Contents | Relevance |
|---|---|---|
| `SOCIAL_WORK_AI_SOURCE_TOPOLOGY.md` | 388 lines, 4,985 files cataloged | Full SWA file inventory |
| `01_CORE/` | 20+ chat transcripts and dev docs | Core SWA development — AI setup, Docker, workflow |
| `03_CLINICAL/` | Clinical module files | Clinical domain code |
| `04_DATA/` | Data module files | Data processing |
| `swa_kernel/` | Full kernel: build, design, extraction, identity, polish, release, research, source | SWA project structure — 8 subsystems |
| `triage_master_list.csv` | 1.6MB | Triage/classification master list |
| `swa_email_export/` | Full Gmail export (All Mail, INBOX, Sent, Folders) | SWA-related email correspondence |
| `swa_audit/` | candidates, logs, manifests, reports | Audit framework |

### 1.7 Priority Extraction Targets (Corrected)

**Tier 1 — Must extract first:**
1. **CIS Plain Language Build Roadmap** — 399 lines of Eric's vision in plain language. This is the canonical build sequence.
2. **WIAS Project Manager spreadsheets** (3 versions, 700KB+ each) — Original WIAS feature/requirement definitions
3. **SWA Source Topology + kernel** — Full project structure, 4,985 files mapped
4. **SWA chat transcripts** (584 files in `01_CORE/`) — Eric's SWA development conversations

**Tier 2 — High value:**
5. WIAS production pipeline structure (1word through 6products) — Creative workflow design
6. SWA triage_master_list.csv (1.6MB) — Classification data
7. SWA email export — Eric's SWA correspondence
8. Idea Bank A-Z — Creative projects to be developed through WIAS/CIS

**Tier 3 — Supplemental:**
9. Hermes session files (~513MB) — Recent development iteration
10. CIS spine (364MB) — Decisions, questions, build state

### 1.5 CIS Documentation

65 docs in `/mnt/projects/cis/docs/` including build plans, tier specifications, architecture documents, proposals.

---

## 2. Extraction Strategy

### Phase A: Surface Eric's Verbatim Words

**Source 1 — Hermes Session Files**

All `.jsonl` files across all profiles. Extract every message where `role == "user"`. Filter to messages containing CIS/SWA/WIAS domain keywords. Preserve full message text, source session ID, timestamp, and profile.

```bash
# Per-session extraction pattern
cat session.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    msg = json.loads(line)
    if msg.get('role') == 'user':
        print(json.dumps({'content': msg['content'], 'ts': msg.get('timestamp')}))
"
```

**Source 2 — Archive Files**

Recursively scan `/mnt/archive/` for text documents (.md, .txt, .json, .yaml, .pdf, .docx). For PDFs/DOCX, extract text via `marker-pdf` or similar. Filter for Eric-authored content (file metadata, directory context, first-person voice).

**Source 3 — CIS Spine**

Query `project_decisions`, `open_questions`, `next_actions`, and `workflow_runs.topic` for Eric-framed content. The `project_decisions` table in particular contains verbatim Eric quotes preserved as "Seed Intent" (AGENTS.md §12).

**Source 4 — CIS Docs**

Scan all 65 docs in `/mnt/projects/cis/docs/` for sections quoting Eric directly, requirement statements, and feature descriptions.

### Phase B: Categorize by Project

Tag each extracted intent fragment by project domain:

| Project | Keywords |
|---|---|
| **CIS** | pipeline, agent, deliberation, Eric Gate, spine, SQLite, review, orchestration, gateway, profile, role, router |
| **SWA** | schedule, field-work, appointment, calendar, time, dispatch, mobile, field, worker |
| **WIAS** | word, image, action, sound, creative, art, music, video, design, generate, compose, render, studio |
| **Mixed** | References multiple domains |
| **Unknown** | No clear domain signal |

### Phase C: Populate Wishlist

Each extracted intent fragment becomes a row in a `wishlist` table:

```sql
CREATE TABLE IF NOT EXISTS wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    source_file TEXT,
    source_line INTEGER,
    source_timestamp TEXT,
    project TEXT CHECK(project IN ('CIS','SWA','WIAS','MIXED','UNKNOWN')),
    category TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected','merged','duplicate')),
    eric_verbatim TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    approved_at TEXT,
    notes TEXT
);
```

### Phase D: Eric Review

Present the wishlist in a simple UI. Eric approves, rejects, merges duplicates, or assigns priority. This is the existing intake path from PROPOSAL_GOVERNANCE_RESET.md §7 — the one thing everyone agrees should be built first.

### Phase E: Build Plan Generation

Approved wishlist items → `build_plan_nodes` rows. Dependencies inferred from domain and category. Three separate build plans generated — one per project.

---

## 3. Files and Databases to Catalog

### 3.1 Databases Identified

| Database | Path | Size | Schema Known? |
|---|---|---|---|
| CIS Spine | `/mnt/projects/cis/data/cis_memory.db` | 364MB | Yes (36 tables) |
| Kanban | `/mnt/projects/cis/data/kanban.db` | 232KB | Unknown |
| Hermes SQLite | `~/.hermes/sessions/hermes_state.db` | Unknown | Unknown |
| Hermes R1 SQLite | `~/.hermes-r1/sessions/hermes_state.db` | Unknown | Unknown |

### 3.2 Key Files for Build Planning

| File | Purpose |
|---|---|
| `AGENTS.md` | Current build state, active decisions |
| `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` | Existing build order |
| `config/hcp_static.yaml` | HCP narrative source |
| `config/agents_static.yaml` | AGENTS.md narrative source |
| `runtime/api/orchestration.py` | Pipeline state machine |
| `runtime/orchestrator.py` | Deliberation engine |
| `tools/closeout.sh` | Session closeout |
| `tools/export/generate_all.py` | Context regeneration |

### 3.3 Archive Files Needing Assessment

All `.tar.gz` backups may contain older versions of session files, databases, and Eric's earlier conversations. These are valuable for intent that predates current session files.

---

## 4. VM and Storage Assessment Framework

Before building three separate projects, assess:

1. **Storage allocation** — Does each project need its own partition? Current layout:
   - `/mnt/projects` (250GB): CIS + could host SWA and WIAS repos
   - `/mnt/archive` (9.1TB): Long-term storage, backups, media assets
   - `/mnt/cache` (111.8GB): Fast scratch space
   - `/mnt/models` + `/mnt/models2` (~465GB): AI model storage

2. **Isolation model** — Per ADR-SEED-010: each CIS-managed project gets its own git repo and project root. SWA and WIAS should follow same pattern.

3. **Shared infrastructure** — Hermes profiles, gateway, Flask/React stack. CIS provides agentic backend. SWA and WIAS are separate applications using CIS as their engine.

4. **Database strategy** — Per-project spines or shared spine with project_id filtering? Resolution needed before build begins.

---

## 5. Immediate Next Action

**Evidence-gathering spike.** Before any build plan, before any code:

1. Extract all Eric-authored messages from Hermes session files (Prime + R1 + V4Impl)
2. Scan archive domain directories for Eric-authored docs
3. Query CIS spine for Eric-framed decisions, questions, next actions
4. Compile into a single `eric_intent_corpus.json` with source provenance
5. Present for Eric review — "is this what you meant?"

**Duration estimate:** 30-60 minutes of agent work (automated grep + extraction).

**Output:** A structured corpus of Eric's actual words, categorized by project domain, with source provenance. This becomes the foundation for three build plans — not enterprise dev strategy, not training-data assumptions. Eric's words.
