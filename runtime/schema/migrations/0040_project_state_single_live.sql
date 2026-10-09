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
-- PRECONDITION — NOT SATISFIED ON THE PRODUCTION SPINE AS OF 2026-10-09.
-- ───────────────────────────────────────────────────────────────────────────
-- CREATE UNIQUE INDEX fails if the data already violates it. On
-- data/cis_memory.db, project_state.next_action has TWO live rows, 161 and
-- 166, so this migration WILL FAIL on production until an authority
-- decision supersedes one of them. That is correct behaviour, not a
-- blocker to work around: a migration that silently picked a winner would
-- be the defect this card exists to remove. Selecting between 161 and 166
-- is phase authority (see project_state row 163) and is explicitly outside
-- the scope of the card that wrote this file.
--
-- Run this before applying, and expect it to return no rows:
--
--   SELECT key, COUNT(*) AS live
--     FROM project_state
--    WHERE superseded_at IS NULL
--      AND key IN (/* the key list below */)
--    GROUP BY key HAVING COUNT(*) > 1;
--
-- or equivalently:
--
--   python3 -m db.state_authority --integrity      # from runtime/, exit 0 required
--
-- REMEDIATION REQUIRED BEFORE APPLYING (architect action, not automatic):
--   1. Decide which of next_action 161 / 166 is current.
--   2. Record the decision and supersede the other row through the
--      sanctioned writer, so superseded_at and superseded_by are both set.
--   3. Re-run the precondition query; it must return no rows.
--   4. Apply this file.
--
-- Until step 4, single-valued enforcement on production comes from the
-- sanctioned writer and is DETECTED (not prevented) for direct database
-- mutation, by state_authority.resolve_current and by
-- tools/gates/gate_build_state_coherence.py.

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
