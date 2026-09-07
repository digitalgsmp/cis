# Advisor review — migration-0030

- packet: `reviews/pending/migration-0030.md`
- advisor: evaluator on port 8650, no tools
- run tag: migration-0030 @ 2026-09-07T10:11:02-05:00
- at: 2026-09-07T10:20:04
- prompt_tokens: 2622
- completion_tokens: 2004
- total_tokens: 4626
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

**1. What would this migration fail to establish?**

The migration fails to verify that `build_plan_dependencies` rows still reference valid node IDs. The verification checks count=25 but never confirms those 25 rows point to existing `build_plan_nodes.id` values. A migration that preserved the count while corrupting the references would pass.

The verification also fails to test that the DEFAULT actually works in practice. Step 3 checks `pragma_table_info` shows `'cis'` as the default, but never executes `INSERT INTO build_plan_nodes (node_label, tier, sequence) VALUES (...)` to confirm the default is applied. SQLite can have defaults declared in schema but not enforced under certain conditions.

The `workflow_run_id` foreign key is declared in the new table schema but the verification never tests it. Step 5 only probes the `project_id` FK. If the `workflow_runs` table doesn't exist or the FK was somehow lost, verification would still pass.

**2. What result would satisfy its verification while still being wrong?**

A migration that:
- Preserved 30 rows in `build_plan_nodes` and 25 in `build_plan_dependencies` but corrupted the dependency relationships (wrong `node_id`/`depends_on_id` mappings)
- Set the DEFAULT correctly in pragma but had a trigger or constraint that prevented it from working
- Lost the `workflow_run_id` foreign key entirely
- Corrupted non-`project_id` columns during `INSERT...SELECT` (e.g., swapped `created_at` and `updated_at`)
- Recreated indexes with different definitions (e.g., missing `IF NOT EXISTS`, different column order)

All of these would pass every verification step.

**Evaluation of the deliberate departure:**

The reasoning is correct. With `foreign_keys=OFF`, the `DROP TABLE` doesn't cascade. With `legacy_alter_table=ON`, the `RENAME` doesn't rewrite child references. Since the table is renamed back to its original name, `build_plan_dependencies` foreign keys remain pointing at a valid table name, and the preserved `id` values keep the references intact.

**Prior findings status:**

All seven are addressed except one: the DEFAULT is still only verified via pragma inspection, not by actual INSERT behavior.
