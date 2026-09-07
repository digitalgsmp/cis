# Advisor review — fix-3.6-preflight-qwen

- packet: `reviews/pending/fix-3.6-preflight-qwen.md`
- advisor: evaluator on port 8650, no tools
- run tag: fix-3.6-preflight-qwen @ 2026-09-07T09:21:26-05:00
- at: 2026-09-07T09:22:29
- prompt_tokens: 1497
- completion_tokens: 1355
- total_tokens: 2852
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

**1. What would this card fail to establish?**

The card would fail to establish that a FOREIGN KEY constraint to `projects(id)` actually exists in the rebuilt table. The migration template shows the column definition but omits the `REFERENCES projects(id)` clause. The plain join returning 30 rows proves the values match, not that referential integrity is enforced. Future inserts with non-existent `project_id` values would succeed.

It would also fail to establish that dependent schema objects (indexes, triggers, views referencing `build_plan_nodes`) are preserved through the drop-and-rename, or that the backup is actually restorable.

**2. What result would satisfy its EXPECT while still being wrong?**

All five verification queries could pass while the table lacks a FOREIGN KEY constraint entirely. The join returns 30 rows because `'cis' = 'cis'`, `foreign_key_check` returns empty because there is no foreign key to check, and integrity is fine. But the stated intent — "Make build_plan_nodes.project_id join to projects.id" — implies referential enforcement, which the EXPECT doesn't actually verify. A subsequent `INSERT INTO build_plan_nodes (project_id, ...) VALUES ('nonexistent', ...)` would succeed, violating the intent while all EXPECT conditions remain satisfied.

Additionally, if the original table had indexes or triggers beyond the `UNIQUE(project_id, node_label)` shown, they would be silently dropped, and the EXPECT wouldn't catch their absence.
