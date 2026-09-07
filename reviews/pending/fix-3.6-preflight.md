# PRE-FLIGHT CARD REVIEW — this card has NOT been executed

**You are reviewing an INSTRUCTION, not a result. Nothing below has run yet.**

Answer exactly this, and nothing else:

1. **What would this card fail to establish?**
2. **What result would satisfy its EXPECT while still being wrong?**

Do not review the queue item's merit. Review whether this card, as written,
would prove what it claims to prove.

---

## Background: queue item 3.6, as recorded

> `projects.id` is `'cis'`, `build_plan_nodes.project_id` is `'CIS'`.
> A plain join returns 0 of 30 rows; `relay.py:1058` papers over it with
> COLLATE NOCASE.

Scope was corrected on 2026-09-07 in both directions:

- **Wider:** the two schemas disagree *by default* —
  `build_plan_nodes.project_id TEXT NOT NULL DEFAULT 'CIS'` against
  `workflow_runs.project_id TEXT DEFAULT 'cis'`. An `UPDATE` that lowercases the
  30 rows is reverted by the next default insert, and **SQLite cannot `ALTER` a
  column default** — changing it requires a table rebuild.
- **Narrower:** `corpus_entries.project_tag` is OUT of scope. Checked: it is
  `project_tag TEXT DEFAULT 'CIS'` with comment `-- CIS, SWA, WIAS`, **no
  `REFERENCES projects`** — a free-text tag, not a foreign key, with an FTS5
  shadow. It does not join to `projects.id` and does not need to.

Measured state:

```
projects.id                   : [('cis',), ('swa',)]
build_plan_nodes.project_id   : [('CIS',)]
node count                    : 30
join rows (plain)             : 0
join rows (COLLATE NOCASE)    : 30
```

There is a precedent for the rebuild: `runtime/schema/migrations/0020_deliberation_rounds_signal_check.sql`
already rebuilt a table to widen a CHECK.

---

## THE CARD UNDER REVIEW

```
CARD: FIX-3.6-01
INTENT: Make build_plan_nodes.project_id join to projects.id. One migration.
Back up the table first. No pipeline runs. No commit.

STEP 1 — backup
  python3.12 -c "dump deliberation of build_plan_nodes to
  data/backups/build_plan_nodes_<ts>.sql"

STEP 2 — write runtime/schema/migrations/0021_build_plan_nodes_project_id.sql
  Following 0020's shape:
    PRAGMA foreign_keys=OFF;
    BEGIN;
    CREATE TABLE build_plan_nodes_new (
        ... identical to current, except:
        project_id TEXT NOT NULL DEFAULT 'cis',
        ...
        UNIQUE(project_id, node_label)
    );
    INSERT INTO build_plan_nodes_new
      SELECT id, lower(project_id), node_label, tier, sequence, status,
             blocked_reason, required_role, allowed_mode, workflow_run_id,
             evidence_path, commit_hash, completed_at, approved_at,
             created_at, updated_at
      FROM build_plan_nodes;
    DROP TABLE build_plan_nodes;
    ALTER TABLE build_plan_nodes_new RENAME TO build_plan_nodes;
    COMMIT;
    PRAGMA foreign_keys=ON;

STEP 3 — apply it
  sqlite3 data/cis_memory.db < runtime/schema/migrations/0021_*.sql

VERIFY:
  select count(*) from build_plan_nodes;                          -- expect 30
  select distinct project_id from build_plan_nodes;               -- expect cis
  select count(*) from build_plan_nodes b
    join projects p on b.project_id = p.id;                       -- expect 30
  pragma foreign_key_check;                                       -- expect empty
  pragma integrity_check;                                         -- expect ok

EXPECT: 30 rows, project_id 'cis', the plain join returns 30, foreign_key_check
empty, integrity ok.
```

---

## What you are NOT being asked

Not whether 3.6 is worth fixing. Not whether COLLATE NOCASE should stay.
Only: **would this card, run exactly as written, prove what its EXPECT claims —
and what could pass that EXPECT while still being wrong?**
