# PRE-FLIGHT REVIEW — migration 0030, REVISION 2. Still NOT run.

**You are reviewing a MIGRATION that has never executed.** Nothing below has
touched the database.

Answer exactly this:

1. **What would this migration fail to establish?**
2. **What result would satisfy its verification while still being wrong?**

---

## What changed in revision 2, and what did not

**No executable SQL changed. Revision 2 is a verification change only.**

Verified, not asserted — comments stripped from both revisions and the remaining
statements hashed:

```
executable statements: 12, none incomplete
executable SQL sha256 rev1: a4dbf0712cda5e85
executable SQL sha256 rev2: a4dbf0712cda5e85
executable SQL unchanged: True
```

That matters to your answer. If the migration itself is wrong, revision 2 has not
touched it, and adding checks to a wrong migration only makes the wrongness
better-observed. Say so if that is the case.

## The revision-1 review, and what was done about it

Revision 1 was reviewed on 2026-09-07 by Qwen (evaluator, 8650). GLM (advisor,
8649) failed to answer — `agent_incomplete` after four gateway continuation
attempts — so **revision 1 was seen by one lineage, not two.**

Qwen judged seven earlier findings addressed and raised three new ones. Each is
quoted below with the check now added. Judge whether the check answers the
objection or only its wording.

### Objection 1 → check 9

> "The migration fails to verify that `build_plan_dependencies` rows still
> reference valid node IDs. The verification checks count=25 but never confirms
> those 25 rows point to existing `build_plan_nodes.id` values. A migration that
> preserved the count while corrupting the references would pass."

```sql
-- 9. THE 25 DEPENDENCY ROWS RESOLVE — not merely count 25.
SELECT count(*) FROM build_plan_dependencies d
  JOIN build_plan_nodes n1 ON d.node_id       = n1.id
  JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id;      -- expect 25

SELECT count(*) FROM build_plan_dependencies d
  LEFT JOIN build_plan_nodes n1 ON d.node_id       = n1.id
  LEFT JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id
 WHERE n1.id IS NULL OR n2.id IS NULL;                      -- expect 0
```

### Objection 2 → check 10

> "The verification also fails to test that the DEFAULT actually works in
> practice. Step 3 checks `pragma_table_info` shows `'cis'` as the default, but
> never executes `INSERT INTO build_plan_nodes (node_label, tier, sequence)
> VALUES (...)` to confirm the default is applied."

```sql
-- 10. THE DEFAULT APPLIES IN PRACTICE. Rolled back, so the probe leaves nothing.
BEGIN;
  INSERT INTO build_plan_nodes (node_label, tier, sequence)
         VALUES ('default-probe', 'T', 997);
  SELECT project_id FROM build_plan_nodes WHERE node_label = 'default-probe';
                                                    -- expect 'cis'
ROLLBACK;
```

Check 3 (pragma) is **kept, not replaced**. 3 reads the declaration; 10 reads the
behaviour. A default declared and not applied passes 3 and fails 10.

### Objection 3 → check 11

> "The `workflow_run_id` foreign key is declared in the new table schema but the
> verification never tests it. Step 5 only probes the `project_id` FK. If the
> `workflow_runs` table doesn't exist or the FK was somehow lost, verification
> would still pass."

```sql
-- 11. THE workflow_run_id FK IS REAL, probed the same way project_id is.
INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, workflow_run_id)
       VALUES ('cis', 'fk-probe-wr', 'T', 996, 'run-does-not-exist');
                                      -- expect FOREIGN KEY constraint failed
```

### One thing Qwen raised that has NO check, stated rather than hidden

Qwen also listed, as things that could pass while wrong:

> "Corrupted non-`project_id` columns during `INSERT...SELECT` (e.g., swapped
> `created_at` and `updated_at`)"
> "Recreated indexes with different definitions (e.g., ... different column order)"

Neither has a dedicated check. The mitigation is that both column lists are
written out in full in the migration and both indexes are recreated with explicit
`CREATE INDEX` statements — inspection, not verification. **If you think that is
insufficient, say so.** Check 6 confirms the indexes exist by name; it does not
compare their definitions.

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
  idx_bpn_project_sequence   ON build_plan_nodes(project_id, sequence)
  idx_bpn_project_status     ON build_plan_nodes(project_id, status)
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

Qwen endorsed this reasoning in revision 1:

> "The reasoning is correct. With `foreign_keys=OFF`, the `DROP TABLE` doesn't
> cascade. With `legacy_alter_table=ON`, the `RENAME` doesn't rewrite child
> references."

**You are not bound by that.** It is the load-bearing decision in the file and it
has been endorsed by one model. If it is wrong, say so.

## THE MIGRATION UNDER REVIEW — unchanged from revision 1

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

## THE VERIFICATION — all eleven checks, run after, with foreign_keys ON

```sql
-- 1. row counts, both tables
SELECT count(*) FROM build_plan_nodes;               -- expect 30
SELECT count(*) FROM build_plan_dependencies;        -- expect 25

-- 2. the case fix
SELECT project_id, count(*) FROM build_plan_nodes GROUP BY 1;   -- expect [('cis',30)]

-- 3. the DEFAULT as DECLARED
SELECT name, "notnull", dflt_value FROM pragma_table_info('build_plan_nodes')
 WHERE name='project_id';                            -- expect dflt_value = 'cis'

-- 4. BOTH foreign keys present
SELECT "table", "from", "to" FROM pragma_foreign_key_list('build_plan_nodes');
                                     -- expect projects/project_id/id
                                     --    AND workflow_runs/workflow_run_id/id

-- 5. the project_id FK is real, not merely declared
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

-- 9. NEW — the 25 dependency rows RESOLVE, not merely count 25
SELECT count(*) FROM build_plan_dependencies d
  JOIN build_plan_nodes n1 ON d.node_id       = n1.id
  JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id;         -- expect 25
SELECT count(*) FROM build_plan_dependencies d
  LEFT JOIN build_plan_nodes n1 ON d.node_id       = n1.id
  LEFT JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id
 WHERE n1.id IS NULL OR n2.id IS NULL;                         -- expect 0

-- 10. NEW — the DEFAULT applies in practice
BEGIN;
  INSERT INTO build_plan_nodes (node_label, tier, sequence)
         VALUES ('default-probe','T',997);
  SELECT project_id FROM build_plan_nodes WHERE node_label='default-probe';
                                                     -- expect 'cis'
ROLLBACK;

-- 11. NEW — the workflow_run_id FK is real
INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, workflow_run_id)
       VALUES ('cis','fk-probe-wr','T',996,'run-does-not-exist');
                                     -- expect FOREIGN KEY constraint failed
```

## What you are NOT being asked

Not whether 3.6 is worth fixing. Not whether COLLATE NOCASE should stay.

Only: **would this migration and its eleven checks prove what they claim, and
what could pass every check above while still being wrong?**
