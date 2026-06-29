     1|# Verifier Registry — Specification v1.0
     2|
     3|## Status: DRAFT
     4|
     5|**Author:** Hermes V4 Reviewer (deepseek-v4-pro)
     6|**Date:** 2026-06-14
     7|**Scope:** Ground-truth-checkable facts that verifiers guess wrong
     8|
     9|---
    10|
    11|## 1. Purpose
    12|
    13|The Verifier Registry solves a specific failure mode: verifiers using wrong paths,
    14|table names, or column names produce false findings that block the pipeline. It
    15|replaces "the verifier remembers" with "the verifier queries a validated source."
    16|
    17|The registry is a lookup, not a spec. It answers "where is X" and "what is X called,"
    18|not "is X correct" or "is X sufficient."
    19|
    20|### 1.1 What it prevents
    21|
    22|| Failure | Session example | Fix |
    23||---------|----------------|-----|
    24|| Wrong directory path | `ls gates/` instead of `ls tools/gates/` | Registry declares `GATE_DIR`, verifier uses it |
    25|| Wrong table name | Spec references `decisions`, table is `project_decisions` | Registry declares table names, validated against `.tables` |
    26|| Wrong column name | Spec says `content`, column is `content_text` | Registry declares column names, validated against `PRAGMA table_info` |
    27|| Wrong endpoint path | Verifier curls wrong URL | Registry declares endpoint routes, validated against `app.py` |
    28|
    29|---
    30|
    31|## 2. Design
    32|
    33|### 2.1 Core rule: validated against ground truth
    34|
    35|Every registry entry must be checkable against the live system. The registry is
    36|not a hand-maintained wishlist — it is a cache of verified facts.
    37|
    38|An entry consists of:
    39|
    40|| Field | Description |
    41||-------|-------------|
    42|| `key` | What the verifier asks for (e.g., `GATE_DIR`) |
    43|| `value` | The fact (e.g., `tools/gates/`) |
    44|| `validation_command` | Shell command that confirms the fact is true now |
    45|| `validation_expected` | What the command should output if the fact is current |
    46|| `last_validated` | ISO timestamp of last successful validation |
    47|| `valid` | `true` if last validation passed, `false` if stale/broken |
    48|
    49|### 2.2 Registry location
    50|
    51|```
    52|runtime/config/verifier_registry.yaml
    53|```
    54|
    55|Single file. One source of truth. No parallel copies.
    56|
    57|### 2.3 Scope: what belongs
    58|
    59|Only facts that meet ALL three criteria:
    60|
    61|1. **Has a single correct answer** — the fact can be right or wrong, not interpreted
    62|2. **Checkable against ground truth** — a command exists that proves the fact
    63|3. **A verifier has gotten wrong in practice** — prevents bloat
    64|
    65|Current scope (from this session's failures):
    66|
    67|| Category | Example keys |
    68||----------|-------------|
    69|| Directory paths | `GATE_DIR`, `MIGRATION_DIR`, `UI_PAGES_DIR`, `UI_COMPONENTS_DIR` |
    70|| Table names | `DB_TABLES` (full list from `.tables`), specific table names |
    71|| Column names | Per-table column lists from `PRAGMA table_info` |
    72|| Endpoint routes | Key API routes and their expected HTTP methods |
    73|
    74|### 2.4 Scope: what does NOT belong
    75|
    76|- Gate pass/fail criteria ("is this gate sufficient?")
    77|- Code quality judgments ("is this function well-named?")
    78|- Version numbers (use `git rev-parse HEAD` instead)
    79|- Anything that requires interpretation
    80|
    81|---
    82|
    83|## 3. Implementation
    84|
    85|### 3.1 Registry YAML format
    86|
    87|```yaml
    88|# Verifier Registry — validated facts for verification scripts
    89|# Regenerate: python3 tools/regenerate_verifier_registry.py
    90|# Last validated: 2026-06-14T18:00:00Z
    91|
    92|facts:
    93|  - key: GATE_DIR
    94|    value: tools/gates/
    95|    description: "Directory containing verification gate scripts"
    96|    validation_command: "test -d tools/gates/ && echo 'EXISTS'"
    97|    validation_expected: "EXISTS"
    98|    last_validated: "2026-06-14T18:00:00Z"
    99|    valid: true
   100|
   101|  - key: DB_TABLES
   102|    value:
   103|      - active_blockers
   104|      - build_plan_nodes
   105|      - eric_gate_approvals
   106|      - goal_references
   107|      - workflow_runs
   108|      - deliberation_rounds
   109|      - dam_extracted_text
   110|      # ... complete list from .tables
   111|    description: "All tables in cis_memory.db"
   112|    validation_command: "sqlite3 data/cis_memory.db '.tables'"
   113|    validation_expected: null  # checked by structural comparison
   114|    last_validated: "2026-06-14T18:00:00Z"
   115|    valid: true
   116|
   117|  - key: TABLE_COLUMNS_eric_gate_approvals
   118|    value:
   119|      - id
   120|      - workflow_run_id
   121|      - decision
   122|      - decided_at
   123|      - decided_by
   124|      - goal_reference_id
   125|      - briefing_hash
   126|      - briefing_json
   127|      - drift_snapshot_json
   128|      - decision_trail_snapshot_json
   129|      - is_current
   130|      - supersedes_approval_id
   131|      - rationale
   132|      - created_at
   133|    description: "Columns in eric_gate_approvals"
   134|    validation_command: "sqlite3 data/cis_memory.db 'SELECT name FROM pragma_table_info(\"eric_gate_approvals\") ORDER BY cid'"
   135|    validation_expected: null
   136|    last_validated: "2026-06-14T18:00:00Z"
   137|    valid: true
   138|
   139|  - key: API_ROUTES_GET
   140|    value:
   141|      - /api/pipeline/status
   142|      - /api/pipeline/runs
   143|      - /api/pipeline/eric-gate
   144|      - /api/dashboard/full
   145|    description: "Key GET API endpoints"
   146|    validation_command: "grep -h '@.*\.route\|@.*\.get' runtime/api/*.py | grep -oP '(?<=[\"\\x27])/api/[^\"\\x27]+' | sort -u"
   147|    validation_expected: null
   148|    last_validated: "2026-06-14T18:00:00Z"
   149|    valid: true
   150|
   151|  - key: UI_PAGE_ROUTES
   152|    value:
   153|      - /
   154|      - /ideas
   155|      - /projects
   156|      - /schedule
   157|      - /dam
   158|      - /learn
   159|      - /review
   160|      - /ingest
   161|      - /spines
   162|      - /infra
   163|      - /chat
   164|      - /advisor-chat
   165|      - /pipeline
   166|      - /eric-gate
   167|      - /archive/search
   168|      - /archive/sessions
   169|      - /decisions
   170|    description: "All 18 routed React page paths"
   171|    validation_command: "grep -oP '(?<=path=\")/[^\"]+' runtime/ui/src/App.jsx"
   172|    validation_expected: null
   173|    last_validated: "2026-06-14T18:00:00Z"
   174|    valid: true
   175|```
   176|
   177|### 3.2 Validation script
   178|
   179|`tools/validate_verifier_registry.py` — runs every `validation_command` against
   180|the live system, compares output to `validation_expected`, sets `valid` and
   181|`last_validated` for each entry.
   182|
   183|A verifier that queries the registry gets facts that were checked against the
   184|live system, not facts someone typed once.
   185|
   186|### 3.3 Verifier usage
   187|
   188|```bash
   189|# Instead of: ls gates/ | grep 11a
   190|# Use:
   191|source tools/gates/_gate_common.sh  # loads GATE_DIR from registry
   192|ls "$GATE_DIR"/gate_11a_*.sh
   193|
   194|# Instead of: sqlite3 data/cis_memory.db ".schema decisions"
   195|# Use: query registry for TABLE_COLUMNS_project_decisions
   196|```
   197|
   198|### 3.4 Regeneration
   199|
   200|The registry is regenerated by `tools/regenerate_verifier_registry.py`, which:
   201|1. Runs every validation command
   202|2. Writes the current ground truth into `value`
   203|3. Sets `valid: true` / `valid: false` and `last_validated`
   204|4. Commits the updated registry if `--commit` flag is passed
   205|
   206|The registry is kept in git. Stale entries show `valid: false` with the
   207|timestamp of the last successful validation, so a verifier can decide whether
   208|to trust the entry or re-validate.
   209|
   210|---
   211|
   212|## 4. Acceptance Criteria
   213|
   214|| # | Test | Verification |
   215||---|------|-------------|
   216|| V1 | Registry exists at `runtime/config/verifier_registry.yaml` | File exists |
   217|| V2 | All entries pass validation | `python3 tools/validate_verifier_registry.py` exits 0 |
   218|| V3 | Registry covers gate path, table names, column names, endpoint routes | Count entries per category |
   219|| V4 | No judgment entries (opinions, assessments, "is X correct") | Grep for prohibited patterns |
   220|| V5 | `_gate_common.sh` sources registry for GATE_DIR | Gates use `$GATE_DIR` not hardcoded paths |
   221|| V6 | Validation script detects a stale entry | Change `GATE_DIR` value, run validation, `valid: false` |
   222|| V7 | Regeneration script updates entries from live system | Run regenerate, verify values match ground truth |
   223|
   224|---
   225|
   226|## 5. Out of Scope
   227|
   228|- Replacing gate scripts with registry entries
   229|- Encoding pass/fail criteria in the registry
   230|- Auto-fixing stale entries (the verifier reads `valid: false` and decides)
   231|- Replacing ADR-SEED-002 (self-report is never truth) — the registry is a
   232|  supporting tool for verification, not a replacement for independent checking
   233|
   234|---
   235|
   236|*End of Verifier Registry Specification v1.0*
   237|*Status: DRAFT — awaiting Reviewer review*
   238|
   239|---
   240|
   241|## Session Update — 2026-06-27
   242|
   243|This document's topic (verifier registry) was not directly advanced this session.
   244|The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
   245|abstraction layer (5 endpoints including human-readable status), intent alignment
   246|pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
   247|full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
   248|Commit: 9c921e2. All 17 DEV-PIVOT files carry session footers. HCP regenerated at HEAD.
   249|