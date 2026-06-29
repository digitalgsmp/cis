# Two-Pass Cataloging & Indexing — Implementation Specification v1.0

## Eric Gate Status: PENDING_APPROVAL

This document converts the approved DESIGN_TWO_PASS_CATALOGING_AND_INDEXING.md into an actionable implementation specification. It defines exact file paths, tool interfaces, test strategy, and acceptance criteria. No code shall be written under this document alone. Implementation proceeds only after Eric Gate approval.

**Author:** Hermes V4 Drafter (deepseek-v4-pro)
**Date:** 2026-06-18
**Status:** DRAFT — awaiting Eric Gate review
**Run ID:** run-d99af34b845c
**HERMES_HOME:** /home/eric/.hermes-v4pro
**Role:** Drafter (port 8645)
**Source Design:** docs/DESIGN_TWO_PASS_CATALOGING_AND_INDEXING.md (reviewer consensus: R1 + Qwen agree, Eric approved)

---

## 1. Purpose

Convert the two-pass cataloging design into an implementable specification. Pass 1 extracts every verbatim Eric statement into a flat, searchable catalog with per-project build plans. Pass 2 consumes Pass 1 outputs and constructs a cross-project knowledge graph with dependency mapping, contradiction detection, and a unified build order.

Design principle (verbatim from design): "Pass 1 preserves work that doesn't have to be figured out again. Every extracted fragment has source provenance. Nothing is summarized. Nothing is inferred."

---

## 2. Data Scope

### 2.1 SHALL be touched

- `tools/catalog/` — new directory: 12 Python tools (7 Pass 1, 5 Pass 2)
- `/mnt/cache/catalog/` — catalog storage root on fast SSD (111.8GB available)
- `catalog/eric_catalog.db` — new standalone SQLite database with FTS5
- `catalog/file_inventory.json` — discovered file manifest
- `catalog/extracted_text/` — raw text output directory
- `catalog/eric_corpus.jsonl` — tagged Eric fragments
- `catalog/build_plans/` — per-project build plans
- `catalog/knowledge_graph.json` — NetworkX serialized graph
- `catalog/knowledge_graph.html` — D3.js interactive visualization
- `catalog/unified_build_order.md` — topologically sorted build sequence
- `catalog/contradictions.md` — flagged cross-project conflicts
- `tests/test_catalog/` — new test directory

### 2.2 SHALL NOT be touched

- `cis_memory.db` spine schema (catalog uses standalone DB, not new tables in spine)
- Hermes Agent core source
- NeMo Guardrails configuration
- Existing gate scripts (catalog gates are new, not replacements)
- ChromaDB collections
- Archive or backup paths
- `runtime/ui/` (no UI component in this tier)
- `runtime/api/` (catalog is CLI-driven, no API endpoints)

### 2.3 Storage Decision

Per design §5: Eric instructed "the VM and storage will be assessed and prioritized for the build of the three separate projects." This spec defers the storage location decision to Eric but recommends:

- Catalog root: `/mnt/cache/catalog/` (111.8GB SSD — fast reads for search and graph operations)
- Catalog DB: `/mnt/cache/catalog/eric_catalog.db` (new standalone DB, ~50-100MB estimated)
- Rationale: Keeps catalog separate from spine. Catalog is derived data, reproducible. If SSD space becomes tight, migrate to `/mnt/archive/catalog/` (9.1TB HDD).

---

## 3. Out of Scope

- Storage/VM capacity assessment (deferred per Eric's instruction, design §5)
- Catalog backup strategy (derived data; backup source files, not catalog)
- UI for catalog search (CLI-only in this tier; UI deferred)
- Catalog integration with ChromaDB VDB (separate tier)
- Automated re-extraction on source file change (watch-based or cron-based refresh deferred)
- Multi-language extraction (English-only; Chinese/other fragments stored as-is)
- Telegram/Discord catalog query interface
- Any modification to source files during extraction (read-only pass)

---

## 4. Architecture

```
Source Directories               Pass 1 Pipeline                    Pass 2 Pipeline
─────────────────               ──────────────                    ──────────────
/mnt/projects/cis/               discover_files.py
/mnt/archive/WIAS/                     │
/mnt/projects/swa/                     ▼
~/.hermes*/sessions/            extract_text.py
/mnt/archive/                         │
                                      ▼
                               filter_eric.py
                                      │
                                      ▼
                               tag_domains.py
                                      │
                                      ▼
                               build_catalog_db.py ────► eric_catalog.db
                                      │
                                      ▼
                               generate_build_plan.py ──► build_plans/*.md
                                                            │
                                                            ▼
                                                     build_graph.py ────► knowledge_graph.json
                                                            │
                                                            ▼
                                                     infer_edges.py
                                                            │
                                                            ▼
                                                     detect_contradictions.py ──► contradictions.md
                                                            │
                                                            ▼
                                                     topological_sort.py ──► unified_build_order.md
                                                            │
                                                            ▼
                                                     visualize_graph.py ──► knowledge_graph.html
```

Pass 1 can begin immediately. Pass 2 begins only after Pass 1 completes. Pass 2 consumes Pass 1 outputs exclusively — it never reads raw source files.

---

## 5. Pass 1: Flat Catalog Tools

All tools live under `tools/catalog/`. Each tool is a standalone Python script with argparse CLI, writes its output to the filesystem, and prints a summary to stdout. Exit code 0 on success, non-zero on failure.

### 5.1 discover_files.py

```
usage: discover_files.py [-h] [--output OUTPUT] [--roots ROOTS [ROOTS ...]]

Walk root directories, catalog every file with metadata.
Produces: catalog/file_inventory.json

Input:  Hardcoded root list (see design §1.1 Step 1), overridable via --roots
Output: JSON array of {path, name, size_bytes, extension, project, discovered_at}

Logic:
  for each root:
    os.walk(root)
    skip .git/, __pycache__/, node_modules/, .venv/, *.pyc
    stat each file
    assign project tag: CIS, SWA, HERMES_SESSIONS, or ARCHIVE
    write record

Exit codes: 0 = success, 1 = no files found, 2 = root directory missing
```

### 5.2 extract_text.py

```
usage: extract_text.py [-h] [--inventory INVENTORY] [--output-dir OUTPUT_DIR]

Parse each file from file_inventory.json, extract text by type.
Produces: catalog/extracted_text/<relative_path>.txt

Input:  catalog/file_inventory.json
Output: One .txt file per parseable source, mirroring relative path structure

Type handlers:
  .xlsx, .xlsb  → openpyxl: read every sheet, cell value joined with \n
  .jsonl        → json.loads per line, extract role=="user" messages
  .md, .txt, .yaml, .py, .csv, .json → read directly (utf-8)
  .db (SQLite)  → sqlite3: .schema + SELECT * FROM <table> LIMIT 100 per table
  .mmap (XMind) → xml.etree: parse XML, extract topic title attributes recursively

Unparseable types (.png, .mp4, .bin, etc.) → logged and skipped
Empty files → logged and skipped
Encoding errors → logged, file skipped with error note

Exit codes: 0 = success, 1 = inventory file missing, 2 = all files failed
```

### 5.3 filter_eric.py

```
usage: filter_eric.py [-h] [--text-dir TEXT_DIR] [--output OUTPUT]

Tag every text fragment by speaker.
Produces: catalog/eric_corpus.jsonl

Input:  catalog/extracted_text/ directory
Output: JSONL, one object per fragment

Fragment boundaries: double newline (\n\n) for .md/.txt; per-cell for .xlsx;
                     per-message for .jsonl; per-node for .mmap

Speaker tagging rules (applied in order, first match wins):
  eric_verbatim:
    - Session file AND role == "user"
    - File path under /home/eric/ (personal directories)
    - First-person voice regex: /\b(I need|I want|I am|I'm|my|I think|let me|I have}\b/
  eric_framing:
    - Spreadsheet column headers (row 1 of .xlsx)
    - Document section headers matching Eric's naming patterns
    - ADR topic lines: /^\[ADR-/
  system_generated:
    - Session file AND role != "user"
    - File under runtime/generated/ or docs/generated/
    - LLM output markers: "Hermes V4", "Assistant:", "FINAL_DIRECTIVE"
  unknown:
    - All remaining fragments

Exit codes: 0 = success, 1 = text directory missing
```

### 5.4 tag_domains.py

```
usage: tag_domains.py [-h] [--corpus CORPUS] [--output OUTPUT]

Keyword-based domain tagging on Eric corpus.
Produces: catalog/eric_corpus.jsonl (same file, adds domain field)

Input:  catalog/eric_corpus.jsonl
Output: Same file, each record now with "domain" field

Domain keywords (case-insensitive, substring match):

  cis:      pipeline, agent, deliberation, Eric Gate, spine, orchestrator,
            gateway, profile, role, router, SQLite, HERMES_HOME, workflow_run,
            ADR-SEED, build_plan, gate_runner, delegation

  swa:      social work, clinical, case management, scheduling, field,
            appointment, client, assessment, DAP, UTAB, intake, triage,
            guardrail, referral, caseload

  wias:     word, image, action, sound, web, creative, production, animation,
            film, music, design, render, studio, CG, VFX, compositing

  shared:   infrastructure, storage, VM, model, Docker, backup, archive,
            Proxmox, wander, creative-vm, passthrough

Tag assignment: union of all matching domains — a fragment can have multiple domains.
No match → domain = [] (empty array)

Exit codes: 0 = success, 1 = corpus file missing
```

### 5.5 build_catalog_db.py

```
usage: build_catalog_db.py [-h] [--corpus CORPUS] [--db DB]

Populate eric_catalog.db with FTS5 search.
Produces: catalog/eric_catalog.db

Input:  catalog/eric_corpus.jsonl
Output: SQLite database with eric_catalog table + eric_catalog_fts FTS5 virtual table

Schema (from design §1.1 Step 5):
  CREATE TABLE eric_catalog ( ... )  -- see design doc lines 79-93
  CREATE INDEX idx_eric_catalog_project ON eric_catalog(project);
  CREATE INDEX idx_eric_catalog_domain ON eric_catalog(domain);
  CREATE INDEX idx_eric_catalog_speaker ON eric_catalog(speaker);
  CREATE VIRTUAL TABLE eric_catalog_fts USING fts5(raw_text, content=eric_catalog, content_rowid=id);

Population: INSERT each JSONL record into eric_catalog
  - domain stored as comma-separated string (SQLite has no array type)
  - project derived from source path (prefix match on roots)
  - raw_text = full fragment text, no truncation

Exit codes: 0 = success, 1 = corpus file missing, 2 = DB write error
```

### 5.6 search_catalog.py

```
usage: search_catalog.py [-h] [--db DB] [--query QUERY] [--domain DOMAIN]
                         [--project PROJECT] [--speaker SPEAKER] [--limit LIMIT]
                         [--format {text,json}]

FTS5 search with domain/project/speaker filters.
Reads from catalog/eric_catalog.db

Options:
  --query     FTS5 search string (required, supports boolean: AND/OR/NOT)
  --domain    Filter: cis, swa, wias, shared (comma-separated OK)
  --project   Filter: CIS, SWA, SHARED, UNKNOWN
  --speaker   Filter: eric_verbatim, eric_framing, system_generated, unknown
  --limit     Max results (default: 20)
  --format    text (default, readable) or json (machine-parseable)

Query: SELECT * FROM eric_catalog WHERE eric_catalog_fts MATCH ? [AND domain LIKE ? ...]
       ORDER BY rank LIMIT ?

Exit codes: 0 = success, 1 = query syntax error, 2 = no matches
```

### 5.7 generate_build_plan.py

```
usage: generate_build_plan.py [-h] [--db DB] [--project PROJECT] [--output-dir OUTPUT_DIR]

Generate per-project build plan from catalog queries.
Produces: catalog/build_plans/{cis,swa,shared_infrastructure}.md

Input:  catalog/eric_catalog.db
Output: Markdown build plan documents

Per-project queries:
  CIS:    SELECT raw_text FROM eric_catalog WHERE project='CIS' AND speaker IN ('eric_verbatim','eric_framing') ORDER BY source_timestamp
  SWA:    SELECT raw_text FROM eric_catalog WHERE project='SWA' AND speaker IN ('eric_verbatim','eric_framing') ORDER BY source_timestamp
  SHARED: SELECT raw_text FROM eric_catalog WHERE project='SHARED' AND speaker IN ('eric_verbatim','eric_framing') ORDER BY source_timestamp

Output format: Each build plan is a markdown file with:
  # {Project} Build Plan — From Eric's Words
  **Generated:** {timestamp}
  **Source:** Eric catalog, {N} fragments
  ---
  ## Phase 1: ...
  (verbatim fragments grouped by topic, ordered by timestamp)
  Each fragment: > {raw_text} — {source_file}:{line}, {timestamp}

Exit codes: 0 = success, 1 = DB missing, 2 = no fragments found for project
```

---

## 6. Pass 2: Knowledge Graph Tools

All tools live under `tools/catalog/`. Each consumes Pass 1 outputs exclusively.

### 6.1 build_graph.py

```
usage: build_graph.py [-h] [--inventory INVENTORY] [--corpus CORPUS]
                      [--build-plans-dir BUILD_PLANS_DIR] [--output OUTPUT]

Construct knowledge graph from Pass 1 outputs.
Produces: catalog/knowledge_graph.json

Input:  catalog/file_inventory.json, catalog/eric_corpus.jsonl, catalog/build_plans/
Output: NetworkX DiGraph serialized as node-link JSON

Node types extracted:
  - file:          from file_inventory.json, id = relative path
  - requirement:   from eric_corpus.jsonl where speaker == "eric_verbatim", id = source:line
  - decision:      from eric_corpus.jsonl where raw_text matches ADR-SEED pattern
  - build_task:    from build_plans/*.md, each ## Phase heading
  - infrastructure: from tags where domain includes "shared"

Node attributes: {id, type, project, label (truncated first 80 chars of raw_text), source}

Exit codes: 0 = success, 1 = input file missing
```

### 6.2 infer_edges.py

```
usage: infer_edges.py [-h] [--graph GRAPH] [--output OUTPUT]

Infer edges from direct references and domain overlap.
Produces: catalog/knowledge_graph.json (augments in-place)

Input:  catalog/knowledge_graph.json
Output: Same file, now with edges added

Three inference strategies:

1. Direct reference (regex scan on requirement raw_text):
   - "see ADR-SEED-XXX" → REFERENCES edge to decision node
   - "uses {tool_or_file_path}" → DEPENDS_ON edge to file/build_task node
   - "depends on", "requires", "needs {X} before {Y}" → DEPENDS_ON edge
   - "builds on", "consumes", "reads from" → DEPENDS_ON edge

2. Domain overlap (co-occurrence scoring):
   - Two requirements sharing ≥2 domain tags → potential DEPENDS_ON (weaker)
   - Requirements in different projects sharing same domain → cross-project edge

3. Version chain (filename pattern):
   - Same basename with version suffix (_v2, .bak, .old) → VERSION_OF edge

Edge types per design §2.2: CONTAINS, DEPENDS_ON, REFERENCES, CONTRADICTS,
                           IMPLEMENTS, VERSION_OF, RUNS_ON

Exit codes: 0 = success, 1 = graph file missing
```

### 6.3 detect_contradictions.py

```
usage: detect_contradictions.py [-h] [--graph GRAPH] [--output OUTPUT]

Cross-reference requirement pairs for contradictions.
Produces: catalog/contradictions.md

Input:  catalog/knowledge_graph.json
Output: Markdown report of flagged conflicts

Detection heuristics:
  1. Same concept described differently in two files
     → Compare requirement nodes with overlapping domain tags
     → Flag if raw_text contains opposing keywords (must/can't, always/never,
       required/optional for same subject)

  2. Cross-project capability conflict
     → Requirement in Project A demands capability X
     → Decision in Project B blocks or limits capability X
     → Flag as contradiction

  3. Timeline conflicts
     → Requirement mentions "Phase 1" while dependency references "Phase 3"
     → Flag ordering conflict

Output format:
  # Contradictions — Eric Review Required
  ## Contradiction #{N}: {type}
  - **Statement A:** > {raw_text} — {source}:{line}
  - **Statement B:** > {raw_text} — {source}:{line}
  - **Conflict:** {description}

Exit codes: 0 = success, 1 = graph file missing, 2 = contradictions found (non-zero for CI gating)
```

### 6.4 topological_sort.py

```
usage: topological_sort.py [-h] [--graph GRAPH] [--output OUTPUT]

Topological sort of dependency graph.
Produces: catalog/unified_build_order.md

Input:  catalog/knowledge_graph.json
Output: Markdown build order document

Algorithm:
  1. Load NetworkX DiGraph from JSON
  2. Identify nodes with in-degree 0 (no dependencies) → Tier 1
  3. Remove Tier 1 nodes, repeat → Tier 2, Tier 3, ...
  4. Handle cycles: detect strongly connected components, report as BLOCKED

Output format:
  # Unified Build Order
  **Generated:** {timestamp}
  **Nodes:** {N} | **Edges:** {M} | **Tiers:** {T}
  ---
  ## Tier 1 — No Dependencies
  - [CIS] {task label} — {source}
  - [SWA] {task label} — {source}
  ## Tier 2 — Depends on Tier 1
  ...

Exit codes: 0 = success, 1 = graph file missing, 2 = cycle detected (blocked)
```

### 6.5 visualize_graph.py

```
usage: visualize_graph.py [-h] [--graph GRAPH] [--output OUTPUT]

Generate interactive D3.js visualization of knowledge graph.
Produces: catalog/knowledge_graph.html

Input:  catalog/knowledge_graph.json
Output: Self-contained HTML file with embedded D3.js (CDN-loaded, no local deps)

Visualization:
  - Force-directed layout (d3-force)
  - Node color by project: CIS=blue, SWA=green, SHARED=gray
  - Node shape by type: file=square, requirement=circle, decision=diamond,
    build_task=triangle, infrastructure=hexagon
  - Edge color by type: DEPENDS_ON=red, REFERENCES=blue, CONTAINS=gray,
    CONTRADICTS=orange-dashed, IMPLEMENTS=green, VERSION_OF=purple-dotted
  - Hover: show node label + source
  - Click: highlight connected subgraph
  - Legend: node type + edge type key

Exit codes: 0 = success, 1 = graph file missing
```

---

## 7. Files to Create

```
tools/catalog/
├── __init__.py                    # Empty, makes catalog a package
├── discover_files.py              # Pass 1, Step 1
├── extract_text.py                # Pass 1, Step 2
├── filter_eric.py                 # Pass 1, Step 3
├── tag_domains.py                 # Pass 1, Step 4
├── build_catalog_db.py            # Pass 1, Step 5
├── search_catalog.py              # Pass 1, Step 6
├── generate_build_plan.py         # Pass 1, Step 7
├── build_graph.py                 # Pass 2, Phase 1
├── infer_edges.py                 # Pass 2, Phase 2
├── detect_contradictions.py       # Pass 2, Phase 3
├── topological_sort.py            # Pass 2, Phase 4
└── visualize_graph.py             # Pass 2, Output

tests/test_catalog/
├── __init__.py
├── test_discover_files.py
├── test_extract_text.py
├── test_filter_eric.py
├── test_tag_domains.py
├── test_build_catalog_db.py
├── test_search_catalog.py
├── test_generate_build_plan.py
├── test_build_graph.py
├── test_infer_edges.py
├── test_detect_contradictions.py
├── test_topological_sort.py
├── test_visualize_graph.py
└── fixtures/
    ├── sample_session.jsonl
    ├── sample_spreadsheet.xlsx
    └── sample_mindmap.mmap

catalog/                           # Created at runtime by tools
├── file_inventory.json
├── extracted_text/
├── eric_corpus.jsonl
├── eric_catalog.db
├── build_plans/
│   ├── cis_build_plan.md
│   ├── swa_build_plan.md
│   ├── wias_build_plan.md
│   └── shared_infrastructure.md
├── knowledge_graph.json
├── knowledge_graph.html
├── unified_build_order.md
└── contradictions.md
```

---

## 8. Files to Modify

None. This is a new capability tier. No existing files are modified.

---

## 9. Python Dependencies

Required (check if already in CIS venv):
- `openpyxl` — .xlsx/.xlsb parsing (likely installed, verify)
- `networkx` — graph construction and topological sort
- `pytest` — test framework (already installed per Tier 10 spec)

New (add to requirements):
- None. All dependencies are standard library or likely already installed.

Verification command: `/home/eric/.hermes/hermes-agent/venv/bin/python -c "import openpyxl, networkx, pytest, xml.etree.ElementTree, json, sqlite3, argparse"`

---

## 10. Test Strategy

### 10.1 Unit Tests (minimum 3 per tool)

Each tool gets test coverage for:
1. Happy path — valid input produces expected output
2. Missing input — handles absent files gracefully (correct exit code)
3. Edge case — empty input, malformed input, encoding errors

Fixture files:
- `sample_session.jsonl` — 5 messages, 2 Eric verbatim, 3 system
- `sample_spreadsheet.xlsx` — 2 sheets, 50 rows of mixed data
- `sample_mindmap.mmap` — XMind XML with 3-level topic hierarchy

### 10.2 Integration Test

Single script `tests/test_catalog/test_integration.py` that runs:
1. `discover_files.py --roots tests/test_catalog/fixtures/` → verify inventory
2. `extract_text.py` → verify extracted text files
3. `filter_eric.py` → verify speaker tags on known fixtures
4. `tag_domains.py` → verify domain tags
5. `build_catalog_db.py` → verify FTS5 search returns expected results
6. `search_catalog.py --query "Eric"` → verify output
7. `generate_build_plan.py --project CIS` → verify build plan structure

Pass 2 integration test:
1. `build_graph.py` → verify node count and types
2. `infer_edges.py` → verify edges created for test data
3. `detect_contradictions.py` → verify zero contradictions on clean fixtures
4. `topological_sort.py` → verify no cycles, correct tier assignment
5. `visualize_graph.py` → verify HTML file created and contains D3.js reference

### 10.3 Test Target

Minimum 80% line coverage per tool. Pass 1 tools: ≥21 tests. Pass 2 tools: ≥15 tests. Integration: 2 test scripts. Total: ≥38 tests.

---

## 11. Verification Gates

### Gate 1: Tool Existence
```bash
test -f tools/catalog/discover_files.py && echo PASS || echo FAIL
test -f tools/catalog/extract_text.py && echo PASS || echo FAIL
# ... all 12 tools
```

### Gate 2: Import Check
```bash
# Each tool must import without error
python -c "import sys; sys.path.insert(0, '.'); from tools.catalog import discover_files"
# ... all 12 tools
```

### Gate 3: Test Suite
```bash
pytest tests/test_catalog/ -v --tb=short
```
Required: All tests pass, ≥38 tests discovered.

### Gate 4: Pass 1 Dry Run (fixtures only)
```bash
python tools/catalog/discover_files.py --roots tests/test_catalog/fixtures/ --output /tmp/catalog_test/file_inventory.json
python tools/catalog/extract_text.py --inventory /tmp/catalog_test/file_inventory.json --output-dir /tmp/catalog_test/extracted_text/
python tools/catalog/filter_eric.py --text-dir /tmp/catalog_test/extracted_text/ --output /tmp/catalog_test/eric_corpus.jsonl
python tools/catalog/tag_domains.py --corpus /tmp/catalog_test/eric_corpus.jsonl
python tools/catalog/build_catalog_db.py --corpus /tmp/catalog_test/eric_corpus.jsonl --db /tmp/catalog_test/eric_catalog.db
python tools/catalog/search_catalog.py --db /tmp/catalog_test/eric_catalog.db --query "test" --format json
python tools/catalog/generate_build_plan.py --db /tmp/catalog_test/eric_catalog.db --project CIS --output-dir /tmp/catalog_test/build_plans/
```
Required: All exit codes 0.

### Gate 5: Pass 2 Dry Run (fixtures only)
```bash
python tools/catalog/build_graph.py --inventory /tmp/catalog_test/file_inventory.json --corpus /tmp/catalog_test/eric_corpus.jsonl --build-plans-dir /tmp/catalog_test/build_plans/ --output /tmp/catalog_test/knowledge_graph.json
python tools/catalog/infer_edges.py --graph /tmp/catalog_test/knowledge_graph.json
python tools/catalog/detect_contradictions.py --graph /tmp/catalog_test/knowledge_graph.json --output /tmp/catalog_test/contradictions.md
python tools/catalog/topological_sort.py --graph /tmp/catalog_test/knowledge_graph.json --output /tmp/catalog_test/unified_build_order.md
python tools/catalog/visualize_graph.py --graph /tmp/catalog_test/knowledge_graph.json --output /tmp/catalog_test/knowledge_graph.html
```
Required: All exit codes 0.

### Gate 6: Dependency Verification
```bash
/home/eric/.hermes/hermes-agent/venv/bin/python -c "import openpyxl, networkx; print('openpyxl:', openpyxl.__version__); print('networkx:', networkx.__version__)"
```
Required: Both import with version number, no errors.

---

## 12. Implementation Order

1. Create `tools/catalog/__init__.py` and directory structure
2. Deploy test fixtures (`tests/test_catalog/fixtures/`)
3. Implement Pass 1 tools in order: discover → extract → filter → tag → build_db → search → generate_plan
4. Write tests after each tool (TDD: write test, see it fail, implement, see it pass)
5. Implement Pass 2 tools in order: build_graph → infer_edges → detect_contradictions → topological_sort → visualize
6. Write Pass 2 tests after each tool
7. Run full Gate 1-6 verification
8. Submit for Eric Gate approval

Estimated effort: Pass 1 (7 tools, 21+ tests) ~2-3 cycles. Pass 2 (5 tools, 15+ tests) ~2 cycles. Total ~4-5 implementation cycles.

---

## 13. Evidence-Backed Acceptance

Per ADR-SEED-002 (Verification Hardening Rule): implementer self-report is not sufficient. Acceptance requires:

1. `git diff --stat` showing only new files under `tools/catalog/` and `tests/test_catalog/`
2. Full `pytest tests/test_catalog/ -v` output with all tests passing
3. Gate 4 output: Pass 1 dry run with all exit codes 0
4. Gate 5 output: Pass 2 dry run with all exit codes 0
5. Gate 6 output: dependency versions confirmed
6. `find tools/catalog/ -name '*.py' | wc -l` = 13 (12 tools + __init__.py)
7. `find tests/test_catalog/ -name '*.py' | wc -l` ≥ 15 (including fixtures)

---

## 14. Eric Review Points

After implementation, Eric reviews:
1. Pass 1 outputs on fixtures — do the speaker tags look right?
2. Pass 1 outputs on fixtures — do the domain tags match intent?
3. Dry run on fixtures — does every tool complete without error?
4. Build plan format — is the per-project output readable and useful?
5. Pass 2 outputs — does the knowledge graph visualization load in a browser?
6. Pass 2 outputs — do contradictions.md and unified_build_order.md make sense?

Full catalog run against real source directories happens ONLY after Eric Gate approval. Fixture-based dry run is the gate check.

---

### Summary

Converts approved DESIGN_TWO_PASS_CATALOGING_AND_INDEXING.md into 12 standalone Python CLI tools (7 Pass 1, 5 Pass 2) under `tools/catalog/`, with ~38+ pytest tests. Pass 1 extracts verbatim Eric statements from 5 source roots into a flat FTS5-searchable catalog with per-project build plans. Pass 2 consumes Pass 1 outputs to build a NetworkX knowledge graph with dependency inference, contradiction detection, and a unified cross-project build order. Catalog lives at `/mnt/cache/catalog/` in a standalone database — no spine schema changes. Six verification gates validate tool existence, imports, test pass, and fixture-based dry runs. No existing files modified. No UI built. Storage assessment deferred per Eric's instruction.

### Recommendation

APPROVE for implementation. The design has dual-reviewer consensus (R1 + Qwen) and Eric's explicit approval. The implementation follows the two-pass design exactly: flat extraction first, structural graph second, with clear pass boundaries and reusable outputs.

---

## Session Update — 2026-06-27: IMPLEMENTED (WITH APPROACH CHANGE)

The core goals of this implementation spec have been achieved, though the method changed:

**What was built instead of two-pass:**
- Session format: raw conversations ingested directly into `knowledge_messages`
- 287,589 messages from 12 sources — FTS5 + ChromaDB (9.3GB)
- `cis_search_knowledge` MCP tool: dual search (keyword + semantic) in one call
- Intent alignment pipeline compares new proposals against all 287K messages

**Why the change:** Eric's sessions ARE the catalog. Raw words → ChromaDB semantic
search is superior to extracting→categorizing→tagging→querying. The two-pass design
would have required a 25-hour tagging pass that Eric explicitly rejected. The session
format approach achieves the same outcome (Eric's words are searchable by meaning)
with zero manual categorization.

See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for full session handoff.
Commit: 70e73bd.
