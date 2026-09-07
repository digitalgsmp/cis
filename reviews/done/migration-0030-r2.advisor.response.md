# Advisor review — migration-0030-r2

- packet: `reviews/pending/migration-0030-r2.md`
- advisor: advisor on port 8649, no tools
- run tag: migration-0030-r2 @ 2026-09-07T10:58:19-05:00
- at: 2026-09-07T11:02:00
- prompt_tokens: 3626
- completion_tokens: 11393
- total_tokens: 15019
- token source: gateway response usage
- model turns: 1 (single-turn: the advisor has no tools, so there is nothing to iterate on)
- finish_reason: stop

---

## 1. What this migration fails to establish

The migration SQL itself is sound. The foreign_keys=OFF + legacy_alter_table=ON approach correctly preserves the 25 dependency rows: the DROP cannot cascade (foreign_keys off), and the dependencies reference the table name `build_plan_nodes`, which is re-established by the RENAME with the same id values copied through. I agree with Qwen's endorsement. The data copy, lowercasing, default change, and FK addition are all correctly specified in the executable SQL.

What it fails to establish is verification coverage, not migration logic. Six things survive the migration unverified:

a. Index definitions. Check 6 confirms index names exist. It does not confirm their column composition or ordering. `idx_bpn_project_sequence` could be recreated as `(sequence, project_id)` and check 6 would pass. The packet acknowledges this.

b. Non-project_id column values. No check inspects any individual value of created_at, updated_at, blocked_reason, required_role, allowed_mode, evidence_path, commit_hash, completed_at, approved_at, tier, sequence, status, or node_label. The explicit column lists in the INSERT and SELECT make a column-order mismatch a matter of inspection, not verification. The packet acknowledges this for created_at/updated_at. It is equally true for every other non-id, non-project_id column.

c. NOT NULL constraints. No check inserts an explicit NULL into any NOT NULL column to confirm enforcement. Check 10 omits project_id and relies on the default, which would apply 'cis' whether or NOT NULL is present. If NOT NULL were accidentally dropped from project_id, all 11 checks would pass.

d. The CHECK constraint on status. No check inserts an invalid status value. If the CHECK were dropped, all 11 checks would pass.

e. AUTOINCREMENT on id. No check confirms AUTOINCREMENT is preserved. If it were dropped (leaving plain INTEGER PRIMARY KEY), all 11 checks would pass. The behavioral difference only manifests on future inserts after row deletion.

f. The collation of the project_id FK match. The packet does not provide the declared collation of projects.id or build_plan_nodes.project_id. This matters: if projects.id has COLLATE NOCASE, the new FK would accept 'CIS' as matching 'cis', which would undermine the intent of lowercasing. The migration lowercases existing data and sets the default to 'cis', but the FK collation determines whether future 'CIS' inserts are also accepted. This information is missing from the packet and I need it to assess whether the FK enforces what the migration intends.

## 2. What result would satisfy verification while still being wrong

The most concrete wrong-but-passing scenarios:

Scenario A: Swapped created_at and updated_at. If the SELECT list had `updated_at, created_at` in the final two positions instead of `created_at, updated_at`, every row would have those two columns exchanged. Checks 1 through 11 all pass: row counts are 30/25, project_id is lowercased, the default, both FKs, both indexes by name, UNIQUE, integrity, dependency resolution, the default probe, and the workflow_run_id FK probe are all unaffected by timestamp values being in the wrong columns.

Scenario B: Wrong index column order. If `CREATE INDEX idx_bpn_project_sequence ON build_plan_nodes(sequence, project_id)` were substituted for the correct definition, check 6 passes (the name exists), and no other check inspects index definitions.

Scenario C: NOT NULL dropped from project_id. If the new table were created with `project_id TEXT DEFAULT 'cis' REFERENCES projects(id)` (no NOT NULL), check 10 would still return 'cis' (the default applies), check 5 would still fail with FK error (the value 'nonexistent' violates the FK before NOT NULL is relevant), and no check inserts an explicit NULL to test the constraint.

Scenario D: CHECK dropped from status. If the CHECK constraint on status were omitted from the new table, all 11 checks pass. No check inserts an out-of-range status value.

Scenario E: AUTOINCREMENT dropped. If the new table declared `id INTEGER PRIMARY KEY` without AUTOINCREMENT, all 11 checks pass. The difference only appears when rows are deleted and new rows are inserted later, potentially reusing ids that build_plan_dependencies rows still reference.

The checks added in revision 2 (9, 10, 11) correctly answer the three objections raised in revision 1. Check 9 does verify referential integrity, not merely count. Check 10 does test the default in practice. Check 11 does probe the workflow_run_id FK. These are genuine improvements. But revision 2 added no check for the two items Qwen raised that have no dedicated check (swapped columns, index definitions), and it added no checks for NOT NULL, CHECK, or AUTOINCREMENT preservation. The migration is right; the verification does not yet prove everything it claims to prove.
