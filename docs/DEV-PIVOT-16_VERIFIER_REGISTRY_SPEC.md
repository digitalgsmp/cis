# Verifier Registry — Specification v1.0

## Status: DRAFT

**Author:** Hermes V4 Reviewer (deepseek-v4-pro)
**Date:** 2026-06-14
**Scope:** Ground-truth-checkable facts that verifiers guess wrong

---

## 1. Purpose

The Verifier Registry solves a specific failure mode: verifiers using wrong paths,
table names, or column names produce false findings that block the pipeline. It
replaces "the verifier remembers" with "the verifier queries a validated source."

The registry is a lookup, not a spec. It answers "where is X" and "what is X called,"
not "is X correct" or "is X sufficient."

### 1.1 What it prevents

| Failure | Session example | Fix |
|---------|----------------|-----|
| Wrong directory path | `ls gates/` instead of `ls tools/gates/` | Registry declares `GATE_DIR`, verifier uses it |
| Wrong table name | Spec references `decisions`, table is `project_decisions` | Registry declares table names, validated against `.tables` |
| Wrong column name | Spec says `content`, column is `content_text` | Registry declares column names, validated against `PRAGMA table_info` |
| Wrong endpoint path | Verifier curls wrong URL | Registry declares endpoint routes, validated against `app.py` |

---

## 2. Design

### 2.1 Core rule: validated against ground truth

Every registry entry must be checkable against the live system. The registry is
not a hand-maintained wishlist — it is a cache of verified facts.

An entry consists of:

| Field | Description |
|-------|-------------|
| `key` | What the verifier asks for (e.g., `GATE_DIR`) |
| `value` | The fact (e.g., `tools/gates/`) |
| `validation_command` | Shell command that confirms the fact is true now |
| `validation_expected` | What the command should output if the fact is current |
| `last_validated` | ISO timestamp of last successful validation |
| `valid` | `true` if last validation passed, `false` if stale/broken |

### 2.2 Registry location

```
runtime/config/verifier_registry.yaml
```

Single file. One source of truth. No parallel copies.

### 2.3 Scope: what belongs

Only facts that meet ALL three criteria:

1. **Has a single correct answer** — the fact can be right or wrong, not interpreted
2. **Checkable against ground truth** — a command exists that proves the fact
3. **A verifier has gotten wrong in practice** — prevents bloat

Current scope (from this session's failures):

| Category | Example keys |
|----------|-------------|
| Directory paths | `GATE_DIR`, `MIGRATION_DIR`, `UI_PAGES_DIR`, `UI_COMPONENTS_DIR` |
| Table names | `DB_TABLES` (full list from `.tables`), specific table names |
| Column names | Per-table column lists from `PRAGMA table_info` |
| Endpoint routes | Key API routes and their expected HTTP methods |

### 2.4 Scope: what does NOT belong

- Gate pass/fail criteria ("is this gate sufficient?")
- Code quality judgments ("is this function well-named?")
- Version numbers (use `git rev-parse HEAD` instead)
- Anything that requires interpretation

---

## 3. Implementation

### 3.1 Registry YAML format

```yaml
# Verifier Registry — validated facts for verification scripts
# Regenerate: python3 tools/regenerate_verifier_registry.py
# Last validated: 2026-06-14T18:00:00Z

facts:
  - key: GATE_DIR
    value: tools/gates/
    description: "Directory containing verification gate scripts"
    validation_command: "test -d tools/gates/ && echo 'EXISTS'"
    validation_expected: "EXISTS"
    last_validated: "2026-06-14T18:00:00Z"
    valid: true

  - key: DB_TABLES
    value:
      - active_blockers
      - build_plan_nodes
      - eric_gate_approvals
      - goal_references
      - workflow_runs
      - deliberation_rounds
      - dam_extracted_text
      # ... complete list from .tables
    description: "All tables in cis_memory.db"
    validation_command: "sqlite3 data/cis_memory.db '.tables'"
    validation_expected: null  # checked by structural comparison
    last_validated: "2026-06-14T18:00:00Z"
    valid: true

  - key: TABLE_COLUMNS_eric_gate_approvals
    value:
      - id
      - workflow_run_id
      - decision
      - decided_at
      - decided_by
      - goal_reference_id
      - briefing_hash
      - briefing_json
      - drift_snapshot_json
      - decision_trail_snapshot_json
      - is_current
      - supersedes_approval_id
      - rationale
      - created_at
    description: "Columns in eric_gate_approvals"
    validation_command: "sqlite3 data/cis_memory.db 'SELECT name FROM pragma_table_info(\"eric_gate_approvals\") ORDER BY cid'"
    validation_expected: null
    last_validated: "2026-06-14T18:00:00Z"
    valid: true

  - key: API_ROUTES_GET
    value:
      - /api/pipeline/status
      - /api/pipeline/runs
      - /api/pipeline/eric-gate
      - /api/dashboard/full
    description: "Key GET API endpoints"
    validation_command: "grep -h '@.*\.route\|@.*\.get' runtime/api/*.py | grep -oP '(?<=[\"\\x27])/api/[^\"\\x27]+' | sort -u"
    validation_expected: null
    last_validated: "2026-06-14T18:00:00Z"
    valid: true

  - key: UI_PAGE_ROUTES
    value:
      - /
      - /ideas
      - /projects
      - /schedule
      - /dam
      - /learn
      - /review
      - /ingest
      - /spines
      - /infra
      - /chat
      - /advisor-chat
      - /pipeline
      - /eric-gate
      - /archive/search
      - /archive/sessions
      - /decisions
    description: "All 18 routed React page paths"
    validation_command: "grep -oP '(?<=path=\")/[^\"]+' runtime/ui/src/App.jsx"
    validation_expected: null
    last_validated: "2026-06-14T18:00:00Z"
    valid: true
```

### 3.2 Validation script

`tools/validate_verifier_registry.py` — runs every `validation_command` against
the live system, compares output to `validation_expected`, sets `valid` and
`last_validated` for each entry.

A verifier that queries the registry gets facts that were checked against the
live system, not facts someone typed once.

### 3.3 Verifier usage

```bash
# Instead of: ls gates/ | grep 11a
# Use:
source tools/gates/_gate_common.sh  # loads GATE_DIR from registry
ls "$GATE_DIR"/gate_11a_*.sh

# Instead of: sqlite3 data/cis_memory.db ".schema decisions"
# Use: query registry for TABLE_COLUMNS_project_decisions
```

### 3.4 Regeneration

The registry is regenerated by `tools/regenerate_verifier_registry.py`, which:
1. Runs every validation command
2. Writes the current ground truth into `value`
3. Sets `valid: true` / `valid: false` and `last_validated`
4. Commits the updated registry if `--commit` flag is passed

The registry is kept in git. Stale entries show `valid: false` with the
timestamp of the last successful validation, so a verifier can decide whether
to trust the entry or re-validate.

---

## 4. Acceptance Criteria

| # | Test | Verification |
|---|------|-------------|
| V1 | Registry exists at `runtime/config/verifier_registry.yaml` | File exists |
| V2 | All entries pass validation | `python3 tools/validate_verifier_registry.py` exits 0 |
| V3 | Registry covers gate path, table names, column names, endpoint routes | Count entries per category |
| V4 | No judgment entries (opinions, assessments, "is X correct") | Grep for prohibited patterns |
| V5 | `_gate_common.sh` sources registry for GATE_DIR | Gates use `$GATE_DIR` not hardcoded paths |
| V6 | Validation script detects a stale entry | Change `GATE_DIR` value, run validation, `valid: false` |
| V7 | Regeneration script updates entries from live system | Run regenerate, verify values match ground truth |

---

## 5. Out of Scope

- Replacing gate scripts with registry entries
- Encoding pass/fail criteria in the registry
- Auto-fixing stale entries (the verifier reads `valid: false` and decides)
- Replacing ADR-SEED-002 (self-report is never truth) — the registry is a
  supporting tool for verification, not a replacement for independent checking

---

*End of Verifier Registry Specification v1.0*
*Status: DRAFT — awaiting Reviewer review*

---

## Session Update — 2026-06-27

This document's topic (verifier registry) was not directly advanced this session.
The major work completed: knowledge base ingestion (287K messages, FTS5 + ChromaDB),
abstraction layer (5 endpoints including human-readable status), intent alignment
pipeline, and roadmap. See **DEV-PIVOT-05 §10** and **DEV-PIVOT-06 §10** for the
full session handoff (gateway status, Eric's feedback, Phase 1 next steps).
Commit: 70e73bd.
