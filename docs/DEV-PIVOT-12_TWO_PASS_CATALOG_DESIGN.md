# Two-Pass Cataloging & Indexing Design

**Author:** hermes-r1 (Reviewer) + hermes-qwen (Second Reviewer), per Eric's direction
**Date:** 2026-06-18
**Status:** DRAFT — awaiting Eric Gate
**Design:** Two sequential passes — flat extraction first, structural graph second. Each pass produces reusable output the next pass consumes.

---

## Pass 1: Flat Catalog — Eric's Words, Per-Project, Immediately Usable

**Goal:** Extract every verbatim Eric statement about CIS and SWA (including WIASW workflow resources) into a flat, searchable catalog. Produce per-project build plans from Eric's actual words. No graph theory. No dependency inference. Just Eric's words, categorized, ready to read.

**Design principle:** Pass 1 preserves work that doesn't have to be figured out again. Every extracted fragment has source provenance. Nothing is summarized. Nothing is inferred.

### 1.1 Extraction Pipeline

```
Source files → Text extraction → Eric-filter → Domain tagging → Catalog DB
```

**Step 1: File Discovery**

Walk source directories for two projects, catalog every file with metadata:

| Project | Root | File types |
|---|---|---|---|
| CIS | `/mnt/projects/cis/` | .md, .yaml, .py, .json, .db |
| SWA | `/mnt/projects/swa/` | .md, .py, .csv, .json, .txt |
| SWA/WIASW | `/mnt/archive/WIAS/` | .xlsx, .xlsb, .md, .csv (WIASW workflow resources used by SWA) |
| Sessions | `~/.hermes*/sessions/` | .jsonl |
| Archive | `/mnt/archive/` | .md, .txt, .xlsx, .mmap |

Output: `catalog/file_inventory.json` — one record per file with path, size, type, project tag.

**Step 2: Text Extraction**

| File type | Extraction method |
|---|---|
| `.xlsx`, `.xlsb` | `openpyxl` — read every sheet, extract every cell value |
| `.jsonl` (sessions) | Parse line by line, extract `role: "user"` messages |
| `.md`, `.txt`, `.yaml` | Read directly |
| `.db` (SQLite) | Query schema + row samples via `sqlite3` |
| `.mmap` (mindmap) | Parse XML structure, extract node text |

Output: `catalog/extracted_text/` — one `.txt` file per source, mirroring source path.

**Step 3: Eric-Filter**

Tag every text fragment by speaker:

| Tag | Rule |
|---|---|
| `eric_verbatim` | Session `role: "user"`, or file in Eric's personal directories, or first-person voice in docs |
| `eric_framing` | Document structured by Eric (spreadsheet headers, section titles, ADR topic lines) |
| `system_generated` | LLM output, auto-generated content, spine rows |
| `unknown` | Can't determine |

Output: `catalog/eric_corpus.jsonl` — one JSON object per fragment with source file, line number, timestamp, speaker tag, raw text.

**Step 4: Domain Tagging**

Keyword-based + manual review. Each fragment tagged with one or more:

| Domain | Keywords |
|---|---|
| `cis` | pipeline, agent, deliberation, Eric Gate, spine, orchestrator, gateway, profile, role, router, SQLite |
| `swa` | social work, clinical, case management, scheduling, field, appointment, client, assessment, DAP, UTAB |
| `wias` | word, image, action, sound, web, creative, production, animation, film, music, design, render, studio |
| `shared` | infrastructure, storage, VM, model, Hermes, docker, database |

Output: Same `eric_corpus.jsonl`, now with `domain` field populated.

**Step 5: Catalog Database**

SQLite table — flat, no graph:

```sql
CREATE TABLE eric_catalog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    source_line INTEGER,
    source_timestamp TEXT,
    project TEXT NOT NULL CHECK(project IN ('CIS','SWA','SHARED','UNKNOWN')),
    domain TEXT NOT NULL,
    speaker TEXT NOT NULL CHECK(speaker IN ('eric_verbatim','eric_framing','system_generated','unknown')),
    raw_text TEXT NOT NULL,
    category TEXT,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'unevaluated' CHECK(status IN ('unevaluated','wishlist','rejected','duplicate','approved')),
    wishlist_id INTEGER REFERENCES wishlist(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_eric_catalog_project ON eric_catalog(project);
CREATE INDEX idx_eric_catalog_domain ON eric_catalog(domain);
CREATE INDEX idx_eric_catalog_speaker ON eric_catalog(speaker);
CREATE VIRTUAL TABLE eric_catalog_fts USING fts5(raw_text, content=eric_catalog, content_rowid=id);
```

### 1.2 Per-Project Build Plans

From the flat catalog, generate two build plans plus shared infrastructure:

**CIS Build Plan:** Filter `project = 'CIS'`. Source: Plain Language Roadmap (§Phases PD-2) + Hermes sessions + spine decisions. Output: ordered build phases.

**SWA Build Plan:** Filter `project = 'SWA'`. Source: SWA kernel structure + chat transcripts + triage_master_list.csv. Output: clinical modules, data pipeline, guardrail system. Includes WIASW workflow resources extracted from `/mnt/archive/WIAS/` project manager spreadsheets (creative production workflow, domain tools).

**Shared Infrastructure:** Filter `project = 'SHARED'`. Output: VM/storage allocation, Hermes gateway config, Docker setup. Referenced by both project plans.

### 1.3 Pass 1 Outputs

```
catalog/
├── file_inventory.json          # Every file discovered
├── extracted_text/              # Raw text from every parseable file
├── eric_corpus.jsonl            # All Eric fragments, tagged
├── eric_catalog.db              # SQLite catalog with FTS5 search
├── build_plans/
│   ├── cis_build_plan.md        # From Eric's CIS words
│   ├── swa_build_plan.md        # From Eric's SWA words
│   │   └── swa_wiasw_resources.md # WIASW workflow resources (part of SWA)
│   └── shared_infrastructure.md # Cross-project infrastructure
└── wishlist.db                  # Wishlist items extracted from catalog
```

### 1.4 Pass 1 Tools

```
tools/catalog/
├── discover_files.py     # Walk directories, produce file_inventory.json
├── extract_text.py       # Parse each file type, produce extracted_text/
├── filter_eric.py        # Tag speaker, produce eric_corpus.jsonl
├── tag_domains.py        # Keyword-based domain tagging
├── build_catalog_db.py   # Populate eric_catalog.db
├── search_catalog.py     # FTS5 search + domain filter CLI
└── generate_build_plan.py # Per-project build plan from catalog queries
```

---

## Pass 2: Knowledge Graph — Structural Dependencies, Unified Build Order

**Goal:** Consume Pass 1 outputs. Build a knowledge graph connecting files, requirements, decisions, and build tasks across both projects. Produce a unified dependency graph showing what must be built before what, across projects.

**Design principle:** Pass 2 discovers what Pass 1 couldn't — that a SWA guardrail depends on a CIS gate script, that a SWA rendering pipeline (WIASW workflow) needs a model from shared infrastructure, that a decision in one project contradicts a requirement in another.

### 2.1 Node Types

| Node type | Source | Example |
|---|---|---|
| `file` | file_inventory.json | `WIAS Project Manager.xlsx` |
| `requirement` | eric_corpus.jsonl (eric_verbatim) | "I need a system that remembers across sessions" |
| `decision` | eric_catalog where category='decision' | ADR-SEED-010: project isolation model |
| `build_task` | Pass 1 build plans | "Build intake pipeline" |
| `dependency` | Inferred from text | SWA guardrail → CIS gate script |
| `contradiction` | Cross-reference | "SWA needs real-time rendering" vs "model runs on CPU only" |
| `infrastructure` | Shared infra plan | VM storage allocation, Docker config |

### 2.2 Edge Types

| Edge | Meaning |
|---|---|
| `CONTAINS` | File contains requirement |
| `DEPENDS_ON` | Task B cannot start before task A |
| `REFERENCES` | Decision references requirement |
| `CONTRADICTS` | Two statements conflict |
| `IMPLEMENTS` | Build task implements requirement |
| `VERSION_OF` | File is a version of another file |
| `RUNS_ON` | Software runs on infrastructure |

### 2.3 Graph Construction

**Phase 1: Node extraction**

Scan Pass 1 catalog. For each entry:
- Files → `file` nodes with metadata
- Eric verbatim fragments → `requirement` nodes with source link
- Spine decisions → `decision` nodes
- Build plan phases → `build_task` nodes
- Infrastructure references → `infrastructure` nodes

**Phase 2: Edge inference**

Three inference strategies:

| Strategy | Method |
|---|---|
| **Direct reference** | Parse text for explicit references: "see ADR-SEED-010", "uses the CIS gate script", "depends on Docker setup" |
| **Domain overlap** | Two requirements tagged with same domain subset → potential dependency |
| **Version chain** | Same filename, different versions → VERSION_OF edge |

**Phase 3: Contradiction detection**

Cross-reference requirements across projects. Flag pairs where:
- Same concept described differently in two files
- One project requires capability another project's decisions block
- Timeline conflicts

**Phase 4: Unified build order**

Topological sort of the dependency graph. Nodes with no unfulfilled dependencies → ready to build. Output: ordered build sequence across both projects.

### 2.4 Graph Storage

NetworkX graph serialized to JSON + visualized as HTML:

```python
import networkx as nx
G = nx.DiGraph()
G.add_node("cis_intake", type="build_task", project="CIS")
G.add_node("swa_guardrail", type="build_task", project="SWA")
G.add_edge("swa_guardrail", "cis_intake", type="DEPENDS_ON")
```

Output formats:
- `catalog/knowledge_graph.json` — Full NetworkX node-link data
- `catalog/knowledge_graph.html` — Interactive D3.js visualization
- `catalog/unified_build_order.md` — Topologically sorted build sequence
- `catalog/contradictions.md` — Flagged conflicts for Eric review

### 2.5 Pass 2 Tools

```
tools/catalog/
├── build_graph.py        # Construct knowledge graph from Pass 1 outputs
├── infer_edges.py        # Direct reference + domain overlap inference
├── detect_contradictions.py  # Cross-reference requirement pairs
├── topological_sort.py   # Unified build order from dependency graph
└── visualize_graph.py    # D3.js HTML visualization
```

### 2.6 Pass 2 Outputs

```
catalog/
├── knowledge_graph.json       # Full graph data
├── knowledge_graph.html       # Interactive visualization
├── unified_build_order.md     # Cross-project build sequence
└── contradictions.md          # Conflicts needing Eric resolution
```

---

## 3. Pass Sequencing

```
Pass 1                           Pass 2
───────                          ───────
Discover files                   Read file_inventory.json
Extract text                     ─
Filter Eric's words              Read eric_corpus.jsonl
Tag domains                      Read domain tags
Build flat catalog DB            ─
Generate per-project plans       Read build plans
                                 Construct knowledge graph
                                 Infer edges
                                 Detect contradictions
                                 Generate unified build order
```

Pass 1 can begin immediately. Pass 2 begins when Pass 1 completes — it consumes Pass 1 outputs, never raw files.

**Pass 1 delivers:** Eric can search his own words, see per-project build plans, immediately useful.

**Pass 2 delivers:** Cross-project dependency map, conflict detection, unified build order — work that builds on Pass 1 and doesn't have to be re-figured out.

---

## 4. Eric's Review Points

After Pass 1 completes, Eric reviews:

1. **Per-project build plans** — Does this match what you intended?
2. **Domain tags** — Any fragments miscategorized?
3. **Missing sources** — Any file or conversation you know exists but isn't in the catalog?

After Pass 2 completes, Eric reviews:

4. **Unified build order** — Does the sequencing make sense?
5. **Contradictions** — Which conflicts are real vs artifacts of version history?
6. **Knowledge graph** — Missing dependencies?

---

## 5. Storage & VM Assessment (Separate Task)

Before either pass executes, assess:

1. **Catalog storage location** — `/mnt/cache/catalog/` (111.8GB SSD, fast) or `/mnt/archive/catalog/` (9.1TB HDD, durable)?
2. **Database location** — `cis_memory.db` already at 364MB. New catalog adds ~50-100MB. Separate DB or new tables in existing spine?
3. **Backup strategy** — Pass 1 outputs are derived (can regenerate). Back up the source files, not the catalog.

Assessment deferred to separate proposal per Eric's instruction: "the VM and storage will be assessed and prioritized for the build of the two projects (CIS and SWA)."
