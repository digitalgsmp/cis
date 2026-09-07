# Advisor review — fix-3.6-preflight

- packet: `reviews/pending/fix-3.6-preflight.md`
- advisor: advisor on port 8649, no tools
- run tag: fix-3.6-preflight @ 2026-09-07T09:06:37-05:00
- at: 2026-09-07T09:07:26
- prompt_tokens: 1406
- completion_tokens: 2253
- total_tokens: 3659
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

## 1. What would this card fail to establish?

**The backup is non-functional.** STEP 1 is pseudo-code — `python3.12 -c "dump deliberation of build_plan_nodes to data/backups/build_plan_nodes_<ts>.sql"` is not valid Python and would produce no backup. The card says "back up the table first" but nothing in the card verifies a backup file exists before STEP 3 runs.

**The column DEFAULT is never verified.** This is the core of the fix. The background explicitly frames the problem as "the next default insert reverts the lowercase." The VERIFY checks that existing rows are `'cis'` (which the `lower()` in INSERT handles), but nothing checks `PRAGMA table_info(build_plan_nodes)` to confirm the default is actually `'cis'` and not `'CIS'`. The EXPECT is blind to the exact thing the migration exists to change.

**The new table schema is elided.** The CREATE TABLE contains `... identical to current, except:` — the actual column list is absent. The INSERT...SELECT provides an explicit 14-column order, but there is no way to confirm the new table's column order matches it. If they diverge, data is silently inserted into wrong columns.

**The UNIQUE(project_id, node_label) constraint is claimed but never verified.** No VERIFY query checks for its presence.

**No check that other tables referencing build_plan_nodes survive the rebuild.** `PRAGMA foreign_key_check` runs with FKs re-enabled, which is good, but the card never enumerates which tables reference `build_plan_nodes` or confirms their row counts are unchanged.

**No check that 0020 was the last applied migration** or that 0021 doesn't collide with an existing file.

## 2. What result would satisfy its EXPECT while still being wrong?

**DEFAULT 'CIS' (uppercase) in the rebuilt table.** The INSERT uses `lower(project_id)`, so all 30 existing rows become `'cis'`. `distinct project_id` returns `cis`. The join returns 30. foreign_key_check is empty. integrity_check is ok. Every EXPECT passes — but the next default insert reintroduces `'CIS'`, recreating the original bug. The card's central claim — that it fixes the default — is untested.

**Column-order misalignment.** If the new table's column order differs from the SELECT list (e.g., `tier` and `node_label` swapped), the 14 values land in wrong columns. Count is 30, `project_id` is `'cis'` (it's first in both), the join returns 30, integrity_check passes. But `node_label` and `tier` data are silently corrupted.

**Missing UNIQUE constraint.** If the constraint is accidentally omitted from the CREATE TABLE, every EXPECT still passes. The card claims to enforce it but never checks.

**No backup, no rollback path.** EXPECT passes, but if a downstream problem is discovered, there is no `.sql` dump to restore from, because STEP 1 produced nothing.

**workflow_runs still broken.** The background identifies `workflow_runs.project_id TEXT DEFAULT 'cis'` as part of the disagreement, but the card touches only `build_plan_nodes`. All five VERIFY queries pass while `workflow_runs` retains any uppercase values it may hold. The card doesn't claim to fix `workflow_runs`, but the EXPECT gives no signal that the wider problem persists.
