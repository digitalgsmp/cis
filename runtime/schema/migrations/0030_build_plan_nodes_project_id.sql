-- Migration 0030: build_plan_nodes.project_id — case, DEFAULT, and a real FK.
--
-- THREE DEFECTS, ONE REBUILD:
--   1. 30 rows hold 'CIS'; projects.id holds 'cis'. A plain join returns 0 of 30.
--      relay.py:1058 papers over it with COLLATE NOCASE.
--   2. The column DEFAULT is 'CIS' — the wrong side. An UPDATE alone is reverted
--      by the next default insert, and SQLite cannot ALTER a column default.
--   3. project_id has NO foreign key to projects(id). pragma foreign_key_list
--      returns only workflow_run_id -> workflow_runs. So `foreign_key_check`
--      passing has never been evidence about project_id at all.
--
-- NUMBERED 0030, NOT 0021. 0021_corpus_entries.sql already exists; migrations
-- run to 0029. (The directory already carries one collision — two files share
-- 0011_ — so this is not hypothetical.)
--
-- 0020's RENAME SHAPE IS DELIBERATELY NOT FOLLOWED, AND THIS IS THE LOAD-BEARING
-- DECISION IN THIS FILE.
--   0020 does: ALTER TABLE x RENAME TO x_old; CREATE x; INSERT..SELECT; DROP x_old.
--   That is safe for deliberation_rounds, which nothing references.
--   build_plan_dependencies holds 25 rows and points at build_plan_nodes(id)
--   TWICE, both ON DELETE CASCADE:
--       build_plan_dependencies.node_id       -> build_plan_nodes.id  ON DELETE CASCADE
--       build_plan_dependencies.depends_on_id -> build_plan_nodes.id  ON DELETE CASCADE
--   Under 0020's shape those 25 rows are lost two different ways:
--     - with foreign_keys=ON, DROP TABLE x_old cascades and deletes them;
--     - with foreign_keys=OFF, SQLite 3.45.1 rewrites child references during
--       ALTER TABLE .. RENAME (default since 3.25), silently repointing
--       build_plan_dependencies at build_plan_nodes_old, which is then dropped.
--   PRAGMA legacy_alter_table=ON suppresses the reference rewriting, and
--   foreign_keys=OFF suppresses the cascade. Both are required. Neither alone
--   is sufficient.
--
-- The two named indexes are recreated explicitly. A rebuild drops them silently:
--   idx_bpn_project_status    ON build_plan_nodes(project_id, status)
--   idx_bpn_project_sequence  ON build_plan_nodes(project_id, sequence)
--
-- RUN 2026-09-07 against data/cis_memory.db. Exit 0, all 15 checks below
-- passing, counts 30 and 25 unchanged, project_id now [('cis', 30)].
-- (This line read "NOT RUN ... has never executed" until it was run. Left
-- unchanged it would have shipped a false claim about the file's own state.)

PRAGMA foreign_keys = OFF;
PRAGMA legacy_alter_table = ON;

BEGIN;

-- New table: identical to the original except project_id's DEFAULT and its FK.
-- Every column is written out, in original order (pragma table_info cid 0-15).
CREATE TABLE build_plan_nodes_new (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'cis' REFERENCES projects(id),
    node_label      TEXT NOT NULL,
    tier            TEXT NOT NULL,
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN (
                        'PENDING', 'IN_PROGRESS', 'COMPLETE',
                        'BLOCKED', 'DEFERRED', 'PROPOSED'
                    )),
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

-- Both column lists written out. An implicit INSERT..SELECT is how column-order
-- drift corrupts data silently.
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

-- Recreate the two named indexes. The UNIQUE autoindex comes back with the
-- constraint; these do not.
CREATE INDEX idx_bpn_project_status
    ON build_plan_nodes(project_id, status);
CREATE INDEX idx_bpn_project_sequence
    ON build_plan_nodes(project_id, sequence);

COMMIT;

PRAGMA legacy_alter_table = OFF;
PRAGMA foreign_keys = ON;

-- ===========================================================================
-- VERIFICATION — run AFTER the migration, with foreign_keys ON.
-- Every check is a command that can fail. Revision 2 adds checks 9, 10 and 11
-- after a pre-flight review by Qwen (evaluator, 8650) on 2026-09-07 found the
-- first eight insufficient. Its objections, and what each new check answers:
--
--   9  "the verification checks count=25 but never confirms those 25 rows point
--       to existing build_plan_nodes.id values. A migration that preserved the
--       count while corrupting the references would pass."
--  10  "fails to test that the DEFAULT actually works in practice ... never
--       executes an INSERT to confirm the default is applied."  Check 3 reads
--       the DECLARATION; check 10 reads the BEHAVIOUR. They are not the same
--       check and 10 does not replace 3.
--  11  "the workflow_run_id foreign key is declared ... but the verification
--       never tests it. Step 5 only probes the project_id FK."
-- ===========================================================================
--
-- BACKUP FIRST — a real command, and it fails loudly if it produces nothing:
--   sqlite3 data/cis_memory.db ".dump build_plan_nodes build_plan_dependencies" \
--     > data/backups/build_plan_nodes_$(date -u +%Y%m%dT%H%M%SZ).sql
--   test -s data/backups/build_plan_nodes_*.sql || { echo "BACKUP EMPTY — STOP"; exit 1; }
--
-- 1. row counts, both tables
--   SELECT count(*) FROM build_plan_nodes;              -- expect 30
--   SELECT count(*) FROM build_plan_dependencies;       -- expect 25
--
-- 2. the case fix
--   SELECT project_id, count(*) FROM build_plan_nodes GROUP BY 1;
--                                                       -- expect [('cis', 30)]
--
-- 3. the DEFAULT as DECLARED
--   SELECT name, dflt_value FROM pragma_table_info('build_plan_nodes')
--    WHERE name = 'project_id';                         -- expect 'cis'
--
-- 4. BOTH foreign keys present
--   SELECT "table", "from", "to" FROM pragma_foreign_key_list('build_plan_nodes');
--                       -- expect projects/project_id/id
--                       --    AND workflow_runs/workflow_run_id/id
--
-- 5. the project_id FK is real, not merely declared
--   INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence)
--          VALUES ('nonexistent', 'fk-probe', 'T', 999);
--                                        -- expect FOREIGN KEY constraint failed
--
-- 6. both named indexes present
--   SELECT name FROM pragma_index_list('build_plan_nodes') ORDER BY name;
--             -- expect idx_bpn_project_sequence, idx_bpn_project_status,
--             --        sqlite_autoindex_build_plan_nodes_1
--
-- 7. UNIQUE still enforced
--   INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence)
--          SELECT project_id, node_label, tier, 998 FROM build_plan_nodes LIMIT 1;
--                                              -- expect UNIQUE constraint failed
--
-- 8. integrity
--   PRAGMA foreign_key_check;                           -- expect empty
--   PRAGMA integrity_check;                             -- expect ok
--
-- 9. THE 25 DEPENDENCY ROWS RESOLVE — not merely count 25.
--    Both edges are checked. The second query is the one that matters: it counts
--    rows whose references DO NOT resolve, and the only acceptable answer is 0.
--   SELECT count(*) FROM build_plan_dependencies d
--     JOIN build_plan_nodes n1 ON d.node_id       = n1.id
--     JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id;      -- expect 25
--
--   SELECT count(*) FROM build_plan_dependencies d
--     LEFT JOIN build_plan_nodes n1 ON d.node_id       = n1.id
--     LEFT JOIN build_plan_nodes n2 ON d.depends_on_id = n2.id
--    WHERE n1.id IS NULL OR n2.id IS NULL;                      -- expect 0
--
-- 10. THE DEFAULT APPLIES IN PRACTICE. Wrapped in a transaction and rolled back,
--     so the probe leaves nothing behind. Check 3 proves the declaration; this
--     proves the behaviour. A default that is declared and not applied passes 3
--     and fails 10, which is exactly the case being guarded.
--   BEGIN;
--     INSERT INTO build_plan_nodes (node_label, tier, sequence)
--            VALUES ('default-probe', 'T', 997);
--     SELECT project_id FROM build_plan_nodes WHERE node_label = 'default-probe';
--                                                       -- expect 'cis'
--   ROLLBACK;
--
-- 11. THE workflow_run_id FK IS REAL, probed the same way project_id is.
--     It is carried over rather than added, which is precisely why it could be
--     lost in a rebuild without any other check noticing.
--   INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, workflow_run_id)
--          VALUES ('cis', 'fk-probe-wr', 'T', 996, 'run-does-not-exist');
--                                        -- expect FOREIGN KEY constraint failed
--
-- --- revision 3 -------------------------------------------------------------
-- Checks 12-15 close the findings from the revision-2 dual review (GLM on 8649,
-- Qwen on 8650, same packet hash 4419478f6a20df0d). Both endorsed the SQL; both
-- said the verification did not yet prove what it claimed. Executable SQL is
-- unchanged again — revisions 2 and 3 are verification only.
--
-- 12 was Qwen's alone and is the most serious of the seven. GLM did not raise it.
-- 14 and 15 were GLM's; 13 was raised by both.
--
-- 12. THE CASCADE STILL FIRES. Check 9 proves the 25 rows RESOLVE. It does not
--     prove that deleting a node still removes them. The whole reason 0030
--     departs from 0020's shape is to protect these rows FROM the cascade — so
--     confirming the cascade survived is not optional. Rolled back.
--   BEGIN;
--     SELECT count(*) FROM build_plan_dependencies;             -- 25
--     DELETE FROM build_plan_nodes
--      WHERE id = (SELECT node_id FROM build_plan_dependencies ORDER BY id LIMIT 1);
--     SELECT count(*) FROM build_plan_dependencies;             -- expect < 25
--   ROLLBACK;
--   (requires foreign_keys=ON; with it OFF this check silently proves nothing)
--
-- 13. INDEX DEFINITIONS MATCH, not merely the names. Check 6 passes if an index
--     called idx_bpn_project_sequence exists on (sequence, project_id).
--   SELECT name FROM pragma_index_info('idx_bpn_project_status')   ORDER BY seqno;
--                                              -- expect project_id, then status
--   SELECT name FROM pragma_index_info('idx_bpn_project_sequence') ORDER BY seqno;
--                                              -- expect project_id, then sequence
--
-- 14. NOT NULL ON project_id IS ENFORCED. Check 10 omits the column and gets
--     'cis' from the DEFAULT whether or not NOT NULL survived, so 10 cannot see
--     this. Only an explicit NULL can.
--   INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence)
--          VALUES (NULL, 'null-probe', 'T', 995);
--                                        -- expect NOT NULL constraint failed
--
-- 15. THE status CHECK CONSTRAINT IS ENFORCED. All 30 existing rows hold valid
--     values, so no other check would notice the constraint going missing.
--   INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, status)
--          VALUES ('cis', 'check-probe', 'T', 994, 'BOGUS');
--                                        -- expect CHECK constraint failed
--
-- KNOWN UNCOVERED, RECORDED RATHER THAN TESTED:
--   AUTOINCREMENT on id. GLM raised it in the revision-2 review: if the rebuild
--   dropped AUTOINCREMENT, all fifteen checks still pass, and the difference only
--   appears later — deleted ids get reused, and build_plan_dependencies rows may
--   still point at them. Testing it needs a delete-then-insert probe across a
--   transaction boundary, which is more machinery than the rest of this block.
--   It is declared in the CREATE TABLE above and left to inspection. This line
--   exists so the gap is a recorded decision rather than an oversight.
-- ===========================================================================
