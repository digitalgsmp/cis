# Foundation Hardening — Component 3.5 Design
## Build-Plan Spine Authority

**Status:** REVISED — incorporating ChatGPT audit (8 findings)
**Author:** Hermes V4 Implementer (deepseek-v4-pro)
**Date:** 2026-06-11
**Revision:** 2 — ChatGPT audit findings applied
**Depends on:** Component 1 (provenance schema), Component 2 (escalation protocol)
**Coordinates with:** Component 3 (Eric Gate redesign — 3.5 can implement in parallel, does not gate on 3)
**Blocks:** Component 4 (Router Expansion), Component 5 (Tier Retrofit Assessment)
**Target migration:** `runtime/schema/migrations/0011_build_plan_spine.sql` (NOT YET CREATED — design only)
**Spine impact:** 2 new tables, 0 existing data modified

---

## 1. Purpose

Component 3.5 eliminates the three-source next-action split that currently exists in CIS:

| Source | Current Role | Problem |
|---|---|---|
| `next_actions` table | Primary authority (generator trusts it) | Exhausted — 12 rows, all COMPLETE, zero PENDING. Generator produces "(No pending actions)." |
| `project_state` table | Key-value cache (`next_tier`, `next_action`, `build_phase`) | Correct but ignored by `generate_hcp.py` for next-action rendering. |
| `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` | Human-readable dependency graph | Not machine-readable. Not queried by any code. Drifts from spine. |

These three sources answer "what's next" differently. Component 3.5 replaces them with a single machine-readable authority: `build_plan_nodes` + `build_plan_dependencies`.

### Why This Must Precede Component 4 and Component 5

**Component 3 already admits the gap.** Finding #5 from the Component 3 ChatGPT audit (line 258 of `CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`):

> "Component 3 verifies the declared goal trace from `goal_references`. It cannot fully verify whether a tier is globally blocked or out of order because the dependency graph is not yet machine-readable."

Component 3.5 closes this gap by making the dependency graph machine-readable before Component 4 and Component 5 consume it.

**Component 4 needs a deterministic project-position query.** The Router Expansion design requires surfacing "current project position in plain language" at session start. Without a build-plan spine, this position must be scraped from prose or inferred from `project_state` key-value pairs. With the spine, it is a single SQL query.

**Component 5's output should be the graph itself.** The Tier Retrofit Assessment is designed to audit tiers 0-7 for production-readiness gaps and produce a remediation list. Without a build-plan spine, that remediation list is another markdown document that drifts. With the spine, Component 5 populates `build_plan_nodes` rows for every tier and marks gaps as `DEFERRED` — the graph IS the remediation list.

**The Future Build-Plan Spine Requirement explicitly calls for this.** From `docs/CIS_FUTURE_BUILD_PLAN_SPINE_REQUIREMENT.md`:

> "The build plan itself needs to become a first-class database object. Future CIS-managed projects should not rely on prose documents alone to determine sequence, completion, dependencies, or next action."
>
> "Session startup should eventually derive exact_next_action from this database-backed build plan, not from prose docs or stale next_actions rows."

Component 3.5 is the implementation of that requirement — scoped to the build plan only, not the full prose-to-structure pipeline.

---

## 2. Build Order Placement

```
Component 1 — Provenance and Lifecycle Base Schema ✅ IMPLEMENTED
Component 2 — Escalation Advisor Integration Protocol ✅ IMPLEMENTED
Component 3 — Eric Gate Redesign (design revised, implementing now)
  → Component 3.5 — Build-Plan Spine Authority (THIS DOCUMENT)
Component 4 — Router Expansion (gated on 3.5)
Component 5 — Tier Retrofit Assessment (gated on 3.5 + 4)
```

Component 3.5 depends on Component 1 (for the `workflow_runs` FK pattern and `goal_references.dependency_node` column) and Component 2 (for the escalation state to influence BLOCKED status decisions). It does not depend on Component 3's implementation — the schema is independent. It can be implemented in parallel with Component 3's remaining phases.

---

## 3. Schema

### 3.1 `build_plan_nodes`

One row per unit of work. A node is a tier, a sub-tier, a phase, a feature, or any discrete build-plan item.

**Pre-migration verification required:** `workflow_runs.id` is `TEXT` in the existing spine (confirmed: `CREATE TABLE workflow_runs (id TEXT PRIMARY KEY, ...)`). The `workflow_run_id` column in this table is therefore `TEXT`, not `INTEGER`. This is the same FK type-mismatch issue corrected in Component 1 revisions — verify before migration.

```sql
CREATE TABLE build_plan_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL DEFAULT 'CIS',
    -- Namespace. 'CIS' for infrastructure, 'SWA' for social worker app,
    -- 'AE-PROMO' for a creative project. Required from the start.

    node_label      TEXT NOT NULL,
    -- Human-readable label. Must be unique within project_id.
    -- Example: "Tier 7.5 — Archive Import + FTS5"
    -- Example: "SWA Phase 1 — Client deadline dashboard"

    tier            TEXT NOT NULL,
    -- Tier identifier. Free text for flexibility across project types.
    -- CIS convention: "5", "7.5", "8"
    -- Non-CIS convention: "SWA-1", "AE-Promo", "Phase-2"

    sequence        INTEGER NOT NULL,
    -- Order within project_id. Lower number = earlier in build order.
    -- Does not enforce execution order (dependencies do that).
    -- Used for display ordering in generators and UI.

    status          TEXT NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN (
                        'PENDING',       -- Ready to work, all HARD dependencies met
                        'IN_PROGRESS',   -- Actively being worked
                        'COMPLETE',      -- Done, verified by gates
                        'BLOCKED',       -- Cannot proceed: unmet dependency or external blocker
                        'DEFERRED',      -- Intentionally postponed (not a gap)
                        'PROPOSED'       -- Drafted but not yet approved (future Drafter path)
                    )),

    blocked_reason  TEXT,
    -- Required when status = 'BLOCKED'. Free text describing why the node
    -- cannot proceed. Provides immediate visibility without requiring a
    -- JOIN to active_blockers. Future enhancement: FK to active_blockers.id.
    -- Example: "Gated on Tier 7 Router Reclassification (placeholder)"

    required_role   TEXT,
    -- The CIS role responsible for this node.
    -- Values: 'Drafter', 'Reviewer', 'Implementer', 'Router', 'Eric'
    -- NULL means no role assignment (informational nodes, parent groupings).

    allowed_mode    TEXT,
    -- What kind of work this node permits.
    -- Values: 'specification', 'implementation', 'verification'
    -- NULL means not yet determined.

    workflow_run_id TEXT REFERENCES workflow_runs(id),
    -- The pipeline run that completed or advanced this node.
    -- NULL until a run is associated.
    -- TYPE IS TEXT (not INTEGER) because workflow_runs.id is TEXT PRIMARY KEY.

    evidence_path   TEXT,
    -- Path or reference to the verification artifact proving completion.
    -- Example: 'tools/gates/gate_db_state.py output', 'git diff <hash>'

    commit_hash     TEXT,
    -- Git commit that delivered this node.

    completed_at    TEXT,
    -- ISO-8601 timestamp when status changed to COMPLETE.

    approved_at     TEXT,
    -- ISO-8601 timestamp when Eric approved this node (if applicable).

    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    -- ISO-8601 timestamp when this node was first inserted.

    updated_at      TEXT DEFAULT (datetime('now')),
    -- ISO-8601 timestamp of last status change.

    UNIQUE(project_id, node_label)
);
```

### 3.2 `build_plan_dependencies`

Foreign-key relationships between nodes. Replaces the text-based `depends_on` column in the legacy `next_actions` table.

```sql
CREATE TABLE build_plan_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         INTEGER NOT NULL REFERENCES build_plan_nodes(id) ON DELETE CASCADE,
    depends_on_id   INTEGER NOT NULL REFERENCES build_plan_nodes(id) ON DELETE CASCADE,
    dependency_type TEXT NOT NULL DEFAULT 'HARD'
                    CHECK (dependency_type IN ('HARD', 'SOFT')),
    -- HARD: node cannot start until depends_on_id is COMPLETE.
    -- SOFT: node should ideally wait but can proceed with Eric approval.

    UNIQUE(node_id, depends_on_id),
    CHECK(node_id != depends_on_id)
);
```

### 3.3 Indexes

```sql
CREATE INDEX idx_bpn_project_status ON build_plan_nodes(project_id, status);
CREATE INDEX idx_bpn_project_sequence ON build_plan_nodes(project_id, sequence);
CREATE INDEX idx_bpd_node ON build_plan_dependencies(node_id);
CREATE INDEX idx_bpd_depends ON build_plan_dependencies(depends_on_id);
```

### 3.4 Total DDL

Two tables, 4 indexes. 0 existing rows modified. 0 existing tables altered. Appends to the spine, does not rewrite it.

---

## 4. Lifecycle and Status Rules

### 4.1 State Transitions

```
PROPOSED → PENDING → IN_PROGRESS → COMPLETE
                ↓          ↓
             BLOCKED    DEFERRED
```

| From | To | Condition |
|---|---|---|
| — | PROPOSED | Drafter inserts a proposed work item (future — not in Component 3.5 scope) |
| PROPOSED | PENDING | Eric Gate approves the proposal |
| PENDING | IN_PROGRESS | Work begins. Only one IN_PROGRESS node per project at a time (convention, not enforced by CHECK). |
| IN_PROGRESS | COMPLETE | All verification gates pass. Evidence exists. |
| PENDING | BLOCKED | A HARD dependency is not COMPLETE, or an external blocker is recorded in `active_blockers`. |
| PENDING | DEFERRED | Eric explicitly defers. Must include a reason recorded elsewhere (decision_trails or project_decisions). |
| BLOCKED | PENDING | All HARD dependencies become COMPLETE and no active blockers remain. Auto-promoted by `promote_unblocked()`. |
| DEFERRED | PENDING | Eric un-defers. |

### 4.2 Write Functions (Enforced Transitions)

Direct UPDATE of `status` is prohibited. All status changes must go through named functions in `runtime/db/build_plan.py`. Each function enforces the transition rules above.

```python
def create_node(db_path, project_id, node_label, tier, sequence,
                required_role=None, allowed_mode=None, status='PENDING'):
    """Insert a new build_plan_nodes row. Returns node id."""

def start_node(db_path, node_id):
    """PENDING → IN_PROGRESS. Fails if node has unmet HARD dependencies."""

def block_node(db_path, node_id, reason):
    """PENDING → BLOCKED. Sets blocked_reason. Fails if reason is empty."""

def defer_node(db_path, node_id, reason):
    """PENDING → DEFERRED. Records reason in decision_trails."""

def complete_node(db_path, node_id, evidence_path=None,
                  commit_hash=None, workflow_run_id=None):
    """IN_PROGRESS → COMPLETE. Records evidence and commit.
    Then calls promote_unblocked() automatically."""

def promote_unblocked(db_path, project_id='CIS'):
    """For every BLOCKED node in the given project whose HARD dependencies
    are all COMPLETE, set status to PENDING. Returns count of promoted nodes."""
```

Called:
- `promote_unblocked()` — automatically when `complete_node()` fires. Manually via `python3 tools/build_plan/promote_unblocked.py`. By Component 5's retrofit audit before generating the remediation list.
- All other functions — called by gate scripts, seed scripts, or Eric Gate approval flow. Never by raw SQL.

### 4.3 Dependency Satisfaction and Eligibility

**Dependency satisfaction rule:** A node's HARD dependencies are satisfied when every row in `build_plan_dependencies` where `node_id = this node` and `dependency_type = 'HARD'` references a `build_plan_nodes` row with `status = 'COMPLETE'`.

**Eligibility rule:** A node is eligible for work when:
- `status = 'PENDING'`, AND
- All HARD dependencies are satisfied (per the rule above), AND
- No active blocker references this node.

SOFT dependencies are informational only — they do not block but surface as warnings.

**Next safe action:** The lowest-sequence eligible PENDING node. The generator queries eligible nodes, not all PENDING nodes. If any PENDING node has unmet HARD dependencies, it is skipped — the next eligible node is shown instead. A gate (G4b) verifies that no PENDING node has unmet HARD dependencies, catching incorrectly marked nodes.<｜end▁of▁thinking｜>

---

## 5. Relationship to Existing Tables

### 5.1 `next_actions` (legacy)

| Before Component 3.5 | After Component 3.5 |
|---|---|
| Primary authority for next-action rendering in `generate_hcp.py` | Derived/generated view. Populated from `build_plan_nodes WHERE status='PENDING' AND project_id='CIS'`. |
| 12 seeded NA-SEED-* rows, all COMPLETE | Preserved as historical record. No new rows inserted into `next_actions` after generator switchover. |
| `depends_on` is a space-separated TEXT column | Replaced by `build_plan_dependencies` foreign keys. |

The legacy `next_actions` table is not dropped, not altered, and not blocked from reads. It remains queryable for historical context. The 12 NA-SEED-* rows continue to render in the "Approved build order" section of HCP_05. New actionable work items are inserted only into `build_plan_nodes`.

### 5.2 `project_state` (cache)

| Key | Before Component 3.5 | After Component 3.5 |
|---|---|---|
| `next_tier` | Manually set during tier completion | Generated from `build_plan_nodes` — the tier of the lowest-sequence PENDING node. |
| `next_action` | Manually set during tier completion | Generated from `build_plan_nodes` — the `node_label` of the lowest-sequence PENDING node. |
| `build_phase` | Manually set | Generated summary of current phase from the build graph. |
| `completed_tier` | Manually set | Continues to be set by gate scripts (deterministic evidence). Used for cross-verification with build-plan graph. |

`project_state` becomes a cache, not an authority. Gate scripts continue to write `completed_tier` and `build_phase` as they do today. If the cache and the build graph disagree, the build graph wins.

### 5.2.1 `sync_project_state_from_build_plan()`

A required function in `runtime/db/build_plan.py` that writes cached `project_state` values from the build graph.

```python
def sync_project_state_from_build_plan(db_path, project_id='CIS'):
    """
    Reads build_plan_nodes for the given project_id.
    Writes/updates project_state rows:
      - next_tier: tier of lowest-sequence eligible PENDING node
      - next_action: node_label of lowest-sequence eligible PENDING node
      - build_phase: "{highest COMPLETE node_label}. {next PENDING node_label}."
    Supersedes previous project_state rows (does not UPDATE in place).
    """
```

Called:
- After any `complete_node()` call.
- After any `promote_unblocked()` call that changes status.
- By `generate_all.py` before running the generators (ensures cache is current).
- Manually: `python3 tools/build_plan/sync_project_state.py [--project-id CIS]`.

**Acceptance test:** After seeding the CIS graph, run `sync_project_state_from_build_plan()`. Then `SELECT value FROM project_state WHERE key='next_action' AND superseded_at IS NULL` must match the `node_label` of the lowest-sequence eligible PENDING node in `build_plan_nodes`.<｜end▁of▁thinking｜>

### 5.3 `goal_references` (Component 1)

The `goal_references.dependency_node` column, designed in Component 1, is the bridge between workflow runs and build-plan nodes. Example:

```
build_plan_nodes table:
  id=14, node_label="Tier 7.5 — Archive Import + FTS5", project_id="CIS"

goal_references table:
  workflow_run_id=5, dependency_node="Tier 7.5 — Archive Import + FTS5"
```

This allows the Eric Gate (Component 3) to verify that a workflow run's declared goal matches a known build-plan node. The Eric Gate does not need to query `build_plan_nodes` directly — it queries `goal_references.dependency_node` and the build-plan spine verifies the node exists and is not blocked.

### 5.4 `workflow_runs` (unchanged)

No changes to `workflow_runs`. The FK `build_plan_nodes.workflow_run_id → workflow_runs.id` is optional — a node can exist without a workflow run (for planning/pending nodes), and a workflow run can exist without closing a node (for deliberation-only runs).

---

## 6. `project_id` Behavior

### 6.1 Required from the start

Every `build_plan_nodes` row requires a `project_id`. The DEFAULT is `'CIS'` for backward compatibility with the single-project present, but `project_id` is a NOT NULL column — every insert must name the project it belongs to.

### 6.2 Multi-project isolation

Projects are isolated by `project_id`. Queries filter by `WHERE project_id = ?`. The generator (`generate_hcp.py`, `generate_agents_md.py`) queries only `project_id = 'CIS'` until Component 4 adds project-aware context selection.

### 6.3 Non-CIS projects

A second project initializes with:
```
INSERT INTO build_plan_nodes (project_id, node_label, tier, sequence, status, created_at)
VALUES ('SWA', 'SWA Phase 1 — Client deadline dashboard', 'SWA-1', 1, 'PENDING', datetime('now'));
```

Same structure. Same `promote_unblocked()`. Same gate scripts. The generator ignores `project_id != 'CIS'` until Component 4 expands to multi-project context. This is guaranteed by the generator query: `WHERE project_id = 'CIS'`.

### 6.4 The `project_id` is the landing pad

The Router Expansion file (`docs/Routining the quick advisor.txt`) describes prompts like "find where I described how the social worker app should work." Under Component 4, the router will determine the project from the prompt and create work items with the correct `project_id`. `build_plan_nodes.project_id` is the column those items land in.

---

## 7. HCP / AGENTS.md Export Behavior

### 7.1 `generate_hcp.py` — HCP_05 Next Actions section

**Current behavior (broken):**
```python
pending = [a for a in actions if a["status"] == "PENDING"]
if pending:
    na = pending[0]
else:
    lines.append("(No pending actions)")
```

**Target behavior (after Component 3.5 Phase 3):**
```python
# Query build_plan_nodes for the lowest-sequence ELIGIBLE PENDING node.
# "Eligible" means status='PENDING' AND all HARD dependencies are COMPLETE.
node = conn.execute(
    """SELECT bpn.node_label, bpn.tier, bpn.status
       FROM build_plan_nodes bpn
       WHERE bpn.project_id = 'CIS'
         AND bpn.status = 'PENDING'
         AND bpn.id NOT IN (
             SELECT bpd.node_id FROM build_plan_dependencies bpd
             JOIN build_plan_nodes dep ON bpd.depends_on_id = dep.id
             WHERE bpd.dependency_type = 'HARD'
               AND dep.status != 'COMPLETE'
         )
       ORDER BY bpn.sequence LIMIT 1"""
).fetchone()

if node:
    lines.append(f"**{node['node_label']}** (Tier {node['tier']})")
elif ps_next := build_state.get("next_action"):
    # Temporary fallback — remove after one regeneration cycle
    lines.append(f"**{ps_next}** (Source: project_state — build-plan spine empty)")
else:
    lines.append("(No pending actions — both build-plan spine and project_state are empty)")
```

The eligibility subquery excludes any PENDING node that has at least one HARD dependency whose target is not COMPLETE. This prevents incorrectly-marked PENDING nodes from appearing as the next safe action. A separate gate (G4b) verifies that no PENDING node has unmet HARD dependencies — catching the condition early.

### 7.2 `generate_hcp.py` — HCP_05 Approved Build Order table

Currently renders all `next_actions` rows. After switchover, renders all `build_plan_nodes` rows for `project_id='CIS'` — including COMPLETE, PENDING, and BLOCKED — in `sequence` order. The legacy NA-SEED-* rows from `next_actions` are appended after the build-plan nodes for historical completeness.

### 7.3 `generate_agents_md.py` — Build Phase line

Currently reads `project_state.build_phase`. After Component 3.5:
- `project_state.build_phase` is generated from the build graph (highest-sequence COMPLETE node's `node_label`, plus next PENDING node's `node_label`).
- The generator continues to read `project_state.build_phase` — unchanged query, but the value it reads is now spine-derived.

### 7.4 `generate_agents_md.py` — Do Not Start list

Currently hardcoded in `config/agents_static.yaml`. After Component 3.5, the Do Not Start list can be generated from `build_plan_nodes WHERE status = 'BLOCKED' AND project_id = 'CIS'`. This is a future improvement, not required for Component 3.5 initial delivery.

---

## 8. Component 4 Consumption

Component 4 (Router Expansion) gains one deterministic data source:

**Session start project position.** The Router, on session start, queries:
```sql
SELECT node_label, status, tier
FROM build_plan_nodes
WHERE project_id = 'CIS' AND status IN ('PENDING', 'IN_PROGRESS')
ORDER BY sequence;
```

This replaces prose-scraping or `project_state` inference. The Router presents:
- Current tier/phase
- Next pending action
- Any IN_PROGRESS work
- Blocked items with their blocker dependencies

All from one query. No markdown parsing. No key-value interpretation.

---

## 9. Component 5 Retrofit Behavior

Component 5 (Tier Retrofit Assessment) is redesigned around the build-plan spine:

**Without Component 3.5:** Component 5 reads code, gates, and docs. Produces a remediation markdown list. That list goes stale like all other prose.

**With Component 3.5:** Component 5 becomes a two-phase operation:

Phase A — Populate the graph:
- For every tier 0-7 from `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md`, insert a `build_plan_nodes` row.
- Set `status = 'COMPLETE'` if the tier's gate suite passes.
- Set `status = 'DEFERRED'` if a gap exists and Eric defers it.
- Set `status = 'BLOCKED'` if a HARD dependency prevents completion.
- Insert `build_plan_dependencies` rows from the dependency graph.

Phase B — The remediation list IS the graph:
- The set of non-COMPLETE nodes IS the gap report.
- `SELECT * FROM build_plan_nodes WHERE project_id='CIS' AND status IN ('BLOCKED', 'DEFERRED') ORDER BY sequence` produces the remediation list.
- Each row already carries its dependencies — the graph itself answers "what blocks this."
- The output is machine-readable, queryable, and stays current when nodes are completed.

Component 5's deliverable changes from "a markdown document" to "a populated and verified build-plan spine for tiers 0-7."

---

## 10. Migration / Backfill Plan

Four phases. Each phase is independently committable and verifiable.

### Phase 1 — Schema Only (commit 1)

- Migration file: `runtime/schema/migrations/0011_build_plan_spine.sql`
- Creates `build_plan_nodes` and `build_plan_dependencies` tables.
- Creates 4 indexes.
- No data inserted.
- No generator changes.
- `gate_db_state.py` extended to verify both tables exist and are empty (pre-seed).

Acceptance: Tables exist. `gate_db_state.py build_plan_nodes count 0` passes.

### Phase 2 — Seed CIS Graph (commit 2)

- Script: `tools/build_plan/seed_build_plan.py`
- Reads `docs/CIS_DEPENDENCY_GRAPH_BUILD_PLAN.md` and/or a structured config (`config/build_plan_tiers.yaml`).
- Inserts one `build_plan_nodes` row per tier/sub-tier (Tier 0 through Tier 10, plus sub-tiers 5.1-5.7, 6.x, 7.1, 7.5a, 7.5b).
- Sets status based on current evidence:
  - Tiers 0-6: COMPLETE (verified by gate scripts and git log)
  - Tier 7: BLOCKED (placeholder per build plan: "Do not design implementation until Tier 6 is verified stable")
  - Tier 7.1: COMPLETE (Router Reclassification implemented at 8a8c99f)
  - Tier 7.5a: COMPLETE (Corpus audit complete)
  - Tier 7.5b: COMPLETE (Clean Subset Import + FTS5 complete)
  - Tier 8: BLOCKED (gated on Tier 7 + pipeline stable per build plan)
  - Tier 9: BLOCKED (gated on Tier 8)
  - Tier 10: BLOCKED (gated on Tier 9)
- Inserts `build_plan_dependencies` rows per the dependency graph.
- Idempotent — skips nodes that already exist (matched on `project_id` + `node_label`).

Acceptance: At least 20 nodes for `project_id='CIS'`. Dependencies exist. `gate_db_state.py` confirms `build_plan_nodes` count meets minimum.

### Phase 3 — Generator Switchover (commit 3)

- Patch `generate_hcp.py`: next-action query → `build_plan_nodes` (with `project_state.next_action` fallback for one cycle).
- Patch `generate_hcp.py`: build-order table → `build_plan_nodes` UNION `next_actions` (legacy).
- `generate_agents_md.py`: no change (still reads `project_state.build_phase` — which is now generated from the graph).
- Regenerate all HCP files and AGENTS.md.
- Verify `gate_export_agreement.sh` still passes.
- Verify HCP_05 now shows a PENDING node from the build graph, not "(No pending actions)."

Acceptance: HCP_05 shows non-empty next action. `gate_export_agreement.sh` passes. All 12 NA-SEED-* rows still visible in build-order table.

### Phase 4 — Deprecate next_actions Authority (commit 4, optional / can be deferred)

- `next_actions` remains queryable for historical read.
- New PENDING rows are inserted only into `build_plan_nodes`.
- `seed_build_queue.py` (if built from Approach B) writes to `build_plan_nodes`, not `next_actions`.
- Generator fallback to `project_state.next_action` removed after one regeneration cycle confirms the build-plan spine is stable.

Acceptance: Generator queries only `build_plan_nodes`. No fallback path. `next_actions` table unchanged — readable but not written.

---

## 11. Acceptance Gates

| # | Gate | Verification |
|---|---|---|
| G1 | Schema exists | `sqlite3 data/cis_memory.db ".schema build_plan_nodes"` returns DDL |
| G2 | Seed complete | `SELECT COUNT(*) FROM build_plan_nodes WHERE project_id='CIS'` >= 20 |
| G3 | Dependencies exist | `SELECT COUNT(*) FROM build_plan_dependencies` > 0 |
| G4 | Generator reads graph | HCP_05 "Next Safe Action" section shows a `build_plan_nodes` entry, not "(No pending actions)" |
| G4b | No PENDING nodes with unmet HARD dependencies | Query: `SELECT bpn.node_label FROM build_plan_nodes bpn JOIN build_plan_dependencies bpd ON bpd.node_id = bpn.id JOIN build_plan_nodes dep ON bpd.depends_on_id = dep.id WHERE bpn.status = 'PENDING' AND bpd.dependency_type = 'HARD' AND dep.status != 'COMPLETE'` must return 0 rows |
| G5 | Legacy rows preserved | All 12 NA-SEED-* entries visible in HCP_05 build-order table |
| G6 | Export agreement | `gate_export_agreement.sh` exits 0 |
| G7 | promote_unblocked works | Mark a dependency COMPLETE → its dependent auto-promotes from BLOCKED to PENDING |
| G8 | Non-CIS isolation | Insert a node with `project_id='SWA'` → generator ignores it (CIS-only query) → manually query confirms it exists and is separable |
| G9 | No existing data modified | `SELECT COUNT(*) FROM next_actions` = 12 (unchanged). `SELECT COUNT(*) FROM project_state` unchanged. `SELECT COUNT(*) FROM workflow_runs` = 5 (unchanged). |
| G10a | Rollback Phase 1–2 | Drop `build_plan_nodes` and `build_plan_dependencies` → generators unchanged → pre-3.5 behavior restored → no data loss. |
| G10b | Rollback Phase 3 | Revert generator commit first (restore `next_actions` query) → HCP output matches pre-3.5 → then optionally drop new tables. |
| G10c | Rollback Phase 4 | Restore previous generator behavior from git (commit before Phase 3 switchover) → HCP output matches pre-3.5. New tables remain but are not queried — no data loss. |
| G11 | sync_project_state accuracy | `SELECT value FROM project_state WHERE key='next_action' AND superseded_at IS NULL` matches `SELECT node_label FROM build_plan_nodes WHERE project_id='CIS' AND status='PENDING' AND <eligible> ORDER BY sequence LIMIT 1` |

---

## 12. Non-Goals (Explicitly Out of Scope)

Component 3.5 does NOT:

- Implement Router Expansion (Component 4)
- Implement Tier Retrofit Assessment (Component 5)
- Import archives or build FTS5 search (Tier 7.5)
- Build MCP Bridge (Tier 8)
- Build Chroma/VDB (Tier 9)
- Build CIS UI or custom display views (Tier 10)
- Implement SWA, Micro1, or any non-CIS project
- Auto-generate `build_plan_nodes` from Drafter output (future — Component 4+)
- Add a UI for editing the build plan (future — Tier 10)
- Replace the markdown build plan document (it remains the human-readable reference; the spine is the machine-readable authority)
- Migrate existing `next_actions` rows into `build_plan_nodes` (the 12 NA-SEED-* rows stay in `next_actions` as historical record)
- Solve the full prose-to-structure pipeline from `CIS_FUTURE_BUILD_PLAN_SPINE_REQUIREMENT.md` (that is a post-Component 5 concern)

---

## 13. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Generator switchover breaks HCP rendering | Low | Medium — HCP packets go to ChatGPT/Claude with wrong next action | Phased rollout: Phase 3 includes `project_state.next_action` fallback for one cycle. If the graph query fails, the fallback catches it. |
| Seed script produces wrong dependency graph | Medium | Low — wrong BLOCKED/PENDING status but no data loss | Seed is idempotent. Rerun with corrected config. Status can be manually overridden per node. |
| Two sources of truth during Phase 3 transition | Medium | Low — temporary, one regeneration cycle | Phase 4 removes the fallback. The transition window is explicitly bounded. |
| `project_id` proliferation without governance | Low | Medium — non-CIS projects could be created without Eric approval | `project_id` is a TEXT column with no CHECK constraint on values. Governance is enforced by the insert path (Component 4 Router), not by the schema. Manual inserts are possible but detectable via `gate_db_state.py`. |
| Component 5's redesign around the graph is not what Eric wants | Low | High — Component 5 is the retrofit audit, getting its output format wrong is costly | This design document must be approved by Eric and audited by ChatGPT before implementation. Component 5's redesign is stated here as intent — the actual Component 5 design doc will specify the exact behavior. |

---

## 14. Open Questions

| ID | Question | Proposed Answer |
|---|---|---|
| OQ-C35-001 | Should `build_plan_nodes` track "who inserted this node" (Drafter, Eric, seed script)? | Defer. Not required for Component 3.5. Can be added as a `created_by` column if needed in Component 4. |
| OQ-C35-002 | Should BLOCKED nodes carry a `blocked_reason` TEXT column? | RESOLVED — `blocked_reason TEXT` column added in Revision 2 per audit finding #4. Required when setting status='BLOCKED' via `block_node()`. Future: FK to `active_blockers.id`. |
| OQ-C35-003 | Should COMPLETE nodes be verified by a gate script before status changes to COMPLETE? | Yes — this is the existing verification-hardening rule. Component 3.5 does not change the rule. The `complete_node()` function should require an evidence hash or gate output before setting status to COMPLETE. This is a Component 5 concern (retrofit gates), not a Component 3.5 concern (schema only). |
| OQ-C35-004 | Should `build_plan_dependencies` support cross-project dependencies (CIS node depends on SWA node)? | No. Cross-project dependencies are a Component 4+ concern. The CHECK constraint `node_id != depends_on_id` is sufficient for single-project graphs. Cross-project would require relaxing the FK to allow NULL or adding a separate table. |

---

## 15. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-06-11 | Hermes V4 Implementer | Initial design document |
| 2026-06-11 | Hermes V4 Implementer | Revision 2 — ChatGPT audit: (1) FK type corrected to TEXT, (2) DEFAULT timestamps added, (3) write functions defined, (4) blocked_reason column added, (5) sync_project_state_from_build_plan() specified, (6) eligibility rule in generator query, (7) phase-specific rollback gates, (8) dependency wording clarified |
