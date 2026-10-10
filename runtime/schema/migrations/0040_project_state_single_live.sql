-- 0040_project_state_single_live.sql
-- Database-enforced single-valued authority for project_state.
-- Authority: existing project_state schema (0002_project_state.sql),
--            ADR-XDEV-001 (external_dev_checkpoint acceptance authority),
--            ADR-PIPE-006 (pipeline_roadmap sequencing authority),
--            dev_continuity_events revision 152 (the measured defect).
--
-- WHAT IT DOES. One partial UNIQUE index, so the DATABASE — not caller
-- discipline — refuses a second live row for a key whose authority
-- contract requires exactly one current record. It holds against any
-- writer, including a direct sqlite3 INSERT that bypasses
-- runtime/db/state_authority.set_state entirely. That is the point:
-- revision 152 demonstrated a forged external_dev_checkpoint row claiming
-- REMOTE_VERIFIED being accepted with no trigger and no check, leaving two
-- live acceptance rows for newest-wins readers to serve.
--
-- WHY AN INDEX AND NOT A TRIGGER OR A CHECK. The uniqueness being enforced
-- is exactly "one row per key among the live ones", which is what a partial
-- unique index states declaratively. A trigger would re-implement the same
-- predicate in procedural form and could be dropped independently of the
-- table; a CHECK cannot see other rows at all. Nothing about the existing
-- contract changes: no column is added, no column is made NOT NULL, no row
-- is modified, and superseded_by stays nullable (104 historical rows carry
-- superseded_at with superseded_by NULL and remain valid history).
--
-- THE KEY LIST IS DELIBERATELY EXPLICIT. It must stay identical to the
-- single-valued entries of KEY_CARDINALITY in runtime/db/state_authority.py;
-- runtime/tests/test_state_authority.py asserts that the two agree, so a key
-- declared in one place and not the other fails a test rather than drifting
-- into a silent gap. Keys NOT listed here are not constrained: a key whose
-- authority contract legitimately allows several live records must not be
-- forced into single-valued semantics by this index.
--
-- ───────────────────────────────────────────────────────────────────────────
-- PRECONDITION — CHECKED BY THE INSTALLER, NOT BY THE READER OF THIS FILE.
-- ───────────────────────────────────────────────────────────────────────────
-- CREATE UNIQUE INDEX fails if the data already violates it, and SQLite's
-- own failure message names neither the key nor the rows. So the supported
-- installer asks the question first:
--
--   runtime/db/state_authority.install_single_live_index(conn)
--     — called by runtime/db/database.init_db() on every open. It checks
--       sqlite_master for this index (absent => install, present => return,
--       so it is idempotent), verifies the key list below still equals the
--       single-valued entries of KEY_CARDINALITY, and then checks every
--       such key for duplicate live rows. Duplicates raise
--       DuplicateLiveRowsError NAMING THE KEYS AND ROW IDS, with nothing
--       written: no row superseded, no winner selected, no superseded_by
--       backfilled. A migration that resolved its own precondition by
--       picking a survivor would be the defect, not the fix.
--
-- The equivalent by hand, expected to return no rows:
--
--   SELECT key, COUNT(*) AS live
--     FROM project_state
--    WHERE superseded_at IS NULL
--      AND key IN (/* the key list below */)
--    GROUP BY key HAVING COUNT(*) > 1;
--
-- or, table-wide and including supersession-chain integrity:
--
--   python3 -m db.state_authority --integrity      # from runtime/, exit 0 required
--
-- IF IT REFUSES, the remediation is an architect action and is not
-- automatic: decide which record is current, supersede the others through
-- state_authority.set_state so superseded_at and superseded_by are both
-- set, then reopen the database.
--
-- HISTORY, because this header previously read as a standing blocker. When
-- this file was written, project_state.next_action carried two live rows,
-- 161 and 166, and applying it to data/cis_memory.db would have failed.
-- That conflict was resolved by authority decision, this index now exists
-- on the production spine, and the installer above therefore returns
-- already_present there and applies nothing. Where the index is NOT yet
-- installed, single-valued enforcement comes from the sanctioned writer
-- alone and direct database mutation is DETECTED rather than prevented, by
-- state_authority.resolve_current and tools/gates/gate_build_state_coherence.py.
--
-- The same DDL is inlined in runtime/schema/spine_schema.sql so a fresh
-- database is born with it; the two key lists and KEY_CARDINALITY are
-- asserted equal by runtime/tests/test_state_authority.py.

CREATE UNIQUE INDEX IF NOT EXISTS idx_project_state_one_live_per_single_valued_key
    ON project_state(key)
 WHERE superseded_at IS NULL
   AND key IN (
        'build_phase',
        'completed_tier',
        'current_direction',
        'current_queue_item',
        'devpivot_index',
        'enforcement_container',
        'enforcement_status',
        'external_dev_checkpoint',
        'gateway_status_qwen',
        'last_export_run_id',
        'last_verified_closeout_tier',
        'next_action',
        'next_tier',
        'pipeline_roadmap',
        'pipeline_stability_verified',
        'queue_projection_observation'
   );
