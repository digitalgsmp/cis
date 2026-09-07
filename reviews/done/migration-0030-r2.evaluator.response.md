# Advisor review — migration-0030-r2

- packet: `reviews/pending/migration-0030-r2.md`
- advisor: evaluator on port 8650, no tools
- run tag: migration-0030-r2 @ 2026-09-07T10:58:19-05:00
- at: 2026-09-07T11:03:14
- prompt_tokens: 3778
- completion_tokens: 2307
- total_tokens: 6085
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

The migration fails to establish that **ON DELETE CASCADE behavior is preserved** in build_plan_dependencies. Check 9 verifies the 25 rows resolve to valid node IDs, but never tests that deleting a node cascades to delete its dependencies. A migration that preserved the rows but lost the CASCADE clause would pass all eleven checks.

The verification also fails to establish that **index definitions are correct**, not merely that indexes with the expected names exist. Check 6 confirms idx_bpn_project_status and idx_bpn_project_sequence are present, but doesn't verify their column order or composition. Indexes on (status, project_id) instead of (project_id, status) would pass check 6 while being wrong.

Results that satisfy verification while still being wrong:

1. **Dependencies resolve but don't cascade**: All 25 build_plan_dependencies rows point to valid nodes (check 9 passes), but the ON DELETE CASCADE clause was somehow lost. Deleting a node would leave orphaned dependencies instead of removing them.

2. **Indexes exist with wrong definitions**: Both named indexes are present (check 6 passes), but one or both have reversed column order or different columns entirely, degrading query performance or breaking index-based lookups.

3. **Non-project_id columns corrupted during copy**: The INSERT...SELECT explicitly lists columns, but the verification never checks that created_at and updated_at weren't swapped, or that other columns weren't corrupted. As long as project_id is lowercased and counts match, checks 1-11 pass.

4. **CHECK constraint on status lost**: The status column has a CHECK constraint limiting it to six values. The verification doesn't test that invalid status values are rejected. All existing data happens to be valid, so no check fails, but future inserts with invalid status would succeed.

The revision-2 checks address the three specific objections from revision 1: dependency resolution (check 9), DEFAULT behavior (check 10), and workflow_run_id FK (check 11). Each check answers its objection directly, not merely its wording.

However, Qwen's observation about index definitions and column corruption remains unaddressed. The mitigation is that both are written explicitly in the migration, but inspection is not verification. Check 6 confirms index existence by name; it does not compare definitions. If that is insufficient, a check comparing pragma_index_info output against expected column lists would close the gap.
