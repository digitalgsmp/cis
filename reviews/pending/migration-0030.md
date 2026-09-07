# PRE-FLIGHT REVIEW — migration 0030 has NOT been run

**You are reviewing a MIGRATION that has never executed.** Nothing below has
touched the database.

Answer exactly this:

1. **What would this migration fail to establish?**
2. **What result would satisfy its verification while still being wrong?**

---

## Why a previous version of this card was rejected

An earlier draft was reviewed on 2026-09-07 by two lineages and found defective
on **seven** counts. This version was written against those findings. State
plainly if any remain unfixed, and do not credit a fix you cannot see in the SQL.

Prior findings, for reference:
- backup step was pseudo-code producing nothing
- the DEFAULT was never verified — the migration's own central claim
- the new table's column list was elided
- UNIQUE was claimed but unchecked
- migration number 0021 was assumed free
- no FOREIGN KEY on project_id, so `foreign_key_check` was vacuous evidence
- indexes silently dropped by the rebuild

---

## Measured state, all verified 2026-09-07

```
build_plan_nodes.project_id : [('CIS', 30)]
projects.id                 : [('cis',), ('swa',)]
plain join                  : 0 of 30
join COLLATE NOCASE         : 30

pragma foreign_key_list(build_plan_nodes):
  (0, 0, 'workflow_runs', 'workflow_run_id', 'id', 'NO ACTION', 'NO ACTION', 'NONE')
  -> project_id has NO foreign key

pragma foreign_key_list(build_plan_dependencies):
  build_plan_dependencies.depends_on_id -> build_plan_nodes.id  ON DELETE CASCADE
  build_plan_dependencies.node_id       -> build_plan_nodes.id  ON DELETE CASCADE
  build_plan_dependencies rows: 25

pragma index_list(build_plan_nodes):
  idx_bpn_project_sequence   CREATE INDEX ... ON build_plan_nodes(project_id, sequence)
  idx_bpn_project_status     CREATE INDEX ... ON build_plan_nodes(project_id, status)
  sqlite_autoindex_build_plan_nodes_1  (implicit, from UNIQUE)

SQLite version: 3.45.1
Writers of build_plan_nodes in production code: NONE
  (only tests/mcp_bridge/test_security.py:51 and tests/mcp_bridge/test_spine.py:148)
Migration numbers in use: 0001-0029, plus a duplicate 0011. 0021 is TAKEN
  (0021_corpus_entries.sql). This file is therefore 0030.
```

## build_plan_nodes, complete DDL as it stands today

```sql
CREATE TABLE build_plan_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'CIS',
    node_label      TEXT NOT NULL,
    tier            TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','IN_PROGRESS','COMPLETE',
                                      'BLOCKED','DEFERRED','PROPOSED')),
    blocked_reason  TEXT,
    required_role   TEXT,
    allowed_mode    TEXT,
    workflow_run_id TEXT REFERENCES workflow_runs(id),
    evidence_path   TEXT,
    commit_hash     TEXT,
    completed_at    TEXT,
    approved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, node_label)
)
```

## The deliberate departure from precedent

Migration 0020 rebuilt a table with: `ALTER TABLE x RENAME TO x_old` → create →
`INSERT..SELECT` → `DROP TABLE x_old`. **0030 does not follow that shape.**

0020's table had nothing referencing it. `build_plan_nodes` has 25
`build_plan_dependencies` rows pointing at it through two `ON DELETE CASCADE`
edges. Under 0020's shape those rows are destroyed two ways: with
`foreign_keys=ON` the `DROP` cascades; with `foreign_keys=OFF`, SQLite 3.45.1
rewrites child references during `ALTER TABLE .. RENAME` (default since 3.25),
repointing `build_plan_dependencies` at the `_old` table before it is dropped.

0030 therefore sets **both** `foreign_keys=OFF` and `legacy_alter_table=ON`,
creates `_new`, drops the original, and renames.

**Evaluate that reasoning. If it is wrong, say so — it is the load-bearing
decision in the file.**

## THE MIGRATION UNDER REVIEW

```sql
PRAGMA foreign_keys = OFF;
PRAGMA legacy_alter_table = ON;

BEGIN;

CREATE TABLE build_plan_nodes_new (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'cis' REFERENCES projects(id),
    node_label      TEXT NOT NULL,
    tier            TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING','IN_PROGRESS','COMPLETE',
                                      'BLOCKED','DEFERRED','PROPOSED')),
    blocked_reason  TEXT,
    required_role   TEXT,
    allowed_mode    TEXT,
    workflow_run_id TEXT REFERENCES workflow_runs(id),
    evidence_path   TEXT,
    commit_hash     TEXT,
    completed_at    TEXT,
    approved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(project_id, node_label)
);

INSERT INTO build_plan_nodes_new
    (id, project_id, node_label, tier, sequence, status,
     blocked_reason, required_role, allowed_mode, workflow_run_id,
     evidence_path, commit_hash, completed_at, approved_at,
     created_at, updated_at)
SELECT
     id, lower(project_id), node_label, tier, sequence, status,
     blocked_reason, required_role, allowed_mode, workflow_run_id,
     evidence_path, commit_hash, completed_at, approved_at,
     created_at, updated_at
FROM build_plan_nodes;

DROP TABLE build_plan_nodes;
ALTER TABLE build_plan_nodes_new RENAME TO build_plan_nodes;

CREATE INDEX idx_bpn_project_status   ON build_plan_nodes(project_id, status);
CREATE INDEX idx_bpn_project_sequence ON build_plan_nodes(project_id, sequence);

COMMIT;

PRAGMA legacy_alter_table = OFF;
PRAGMA foreign_keys = ON;
```

## THE BACKUP — a real command, run before the migration

```bash
sqlite3 /mnt/projects/cis/data/cis_memory.db \
  ".dump build_plan_nodes build_plan_dependencies" \
  > data/backups/build_plan_nodes_$(date -u +%Y%m%dT%H%M%SZ).sql
test -s data/backups/build_plan_nodes_*.sql || { echo "BACKUP EMPTY — STOP"; exit 1; }
```

## THE VERIFICATION — every claim a command that can fail

```sql
-- 1. row counts, both tables
SELECT count(*) FROM build_plan_nodes;               -- expect 30
SELECT count(*) FROM build_plan_dependencies;        -- expect 25  (the cascade test)

-- 2. the case fix
SELECT project_id, count(*) FROM build_plan_nodes GROUP BY 1;   -- expect [('cis',30)]

-- 3. the DEFAULT — the migration's central claim
SELECT name, "notnull", dflt_value FROM pragma_table_info('build_plan_nodes')
 WHERE name='project_id';                            -- expect dflt_value = 'cis'

-- 4. BOTH foreign keys present
SELECT "table", "from", "to" FROM pragma_foreign_key_list('build_plan_nodes');
                                     -- expect projects/project_id/id
                                     --    AND workflow_runs/workflow_run_id/id

-- 5. the FK is real, not merely declared
INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence)
       VALUES ('nonexistent','fk-probe','T',999);    -- expect FOREIGN KEY constraint failed

-- 6. both named indexes present
SELECT name FROM pragma_index_list('build_plan_nodes') ORDER BY name;
                                     -- expect idx_bpn_project_sequence,
                                     --        idx_bpn_project_status, sqlite_autoindex...

-- 7. UNIQUE still enforced
INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence)
       SELECT project_id, node_label, tier, 998 FROM build_plan_nodes LIMIT 1;
                                     -- expect UNIQUE constraint failed

-- 8. integrity
PRAGMA foreign_key_check;                            -- expect empty
PRAGMA integrity_check;                              -- expect ok
```

## What you are NOT being asked

Not whether 3.6 is worth fixing. Not whether COLLATE NOCASE should stay.
Only: **would this migration and its verification prove what they claim, and what
could pass every check above while still being wrong?**
