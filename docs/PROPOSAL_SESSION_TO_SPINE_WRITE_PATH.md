# Proposal: Session-to-Spine Write Path

**Status:** PROPOSAL — for Claude audit, ChatGPT audit, then Eric approval
**Date:** 2026-06-19 (revised 2026-06-19 for D6 idempotency after audit)
**Ref:** DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md
**Constraint:** Zero new tables, zero migration run, zero /opt/cis-control, works on current schema

## Summary

Extend the existing `project_state` key convention with two new keys (`current_direction`, `devpivot_index`) and add a generator fallback clause so `next_actions` feeds Section 6/Next Actions when `build_plan_nodes` has no PENDING rows. Record DEV-PIVOT-17 as `ADR-SEED-015` in `project_decisions` and queue the next action as `NA-SEED-013` in `next_actions`. No new tables, no new columns, no migration. Same tables that already track `build_phase`, 14 ADR-SEED decisions, and 13 next action lifecycle rows. All writes use idempotent collision guards (INSERT OR IGNORE) and project_state writes supersede prior rows via inline UPDATE-then-INSERT SQL (canonical sequence in Idempotency Contract §A). The `supersede_project_state()` helper (`runtime/db/database.py:300`) exists but is NOT used for this task and is NOT modified — see §A for why (it lacks the id-exclusion guard and would zero the active row if called after insert).

## Root Cause (restated)

Five causes from DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md:

1. No automated session-to-spine write path — decisions stay in transcripts
2. `project_state` schema only tracks `build_phase` — no key for direction or architecture state
3. Section 6 (Next Actions) depends solely on `build_plan_nodes WHERE status IN ('PENDING','IN_PROGRESS')` — empty when all nodes are COMPLETE/DEFERRED
4. DEV-PIVOT docs are hand-maintained with no generator
5. Handoff files are outside the generation pipeline

This proposal fixes causes 1-3 directly. Cause 4 (DEV-PIVOT generation) gets a foundational index; full template rendering is Phase 2. Cause 5 dissolves once 1-3 are fixed: handoff files become generated from spine state.

## Design (one recommendation)

### 1. Where a session decision is recorded

**Table:** `project_decisions` (exists, no changes needed)

DEV-PIVOT-17 becomes `ADR-SEED-015`:

```sql
-- NOTE: This block illustrates the row CONTENT only. Executable writes must use INSERT OR IGNORE
-- per Idempotency Contract §B.
INSERT INTO project_decisions (id, label, decision, reason, status, decided_at)
VALUES (
  'ADR-SEED-015',
  'Enforcement architecture: three-layer process isolation',
  'CIS enforces Hermes via root-owned /opt/cis-control mounted read-only into Docker worker. Worker writes only to /mnt/cache/catalog/<run_id>/. Two enforcement walls: kernel (Docker RO mount) + policy hook (pre_tool_call). Trust root: constrained agent cannot author its own contract. Override plane (.GATE_DISABLED) built/tested before hook is trusted. See DEV-PIVOT-17 for full text.',
  '16 failure modes are LLM behavior failures, not future app features. Prompt/SOUL instructions insufficient — enforcement must be deterministic and live outside the constrained agent. Inventory/catalog is the proving ground.',
  'DECIDED',
  '2026-06-19T07:00:00Z'
);
```

Convention: All architecture decisions use `ADR-SEED-NNN` IDs (matches existing pattern). The `decision` column carries the one-paragraph summary. The `reason` column carries the "why now." Full deliberation history lives in `decision_trails` (existing table, joined on `workflow_run_id`). The full DEV-PIVOT-17 markdown text is referenced (file path) but not denormalized into the DB — the DB carries the decision *summary*; the document carries the full reasoned text.

### 2. What records current architecture direction

**Table:** `project_state` (exists, uses existing `superseded_by` chain)

New key `current_direction`:

```sql
-- NOTE: This block illustrates the row CONTENT only. Do not execute this as the write sequence.
-- For executable/idempotent project_state writes, use the canonical UPDATE-then-INSERT sequence
-- in Idempotency Contract §A.
INSERT INTO project_state (key, value, source, created_at)
VALUES (
  'current_direction',
  'ADR-SEED-015 — three-layer process isolation. CIS control plane over Hermes worker. Docker container with RO mounts. /opt/cis-control root-owned. Next: draft enforcement primitive spec.',
  'manual',
  '2026-06-19T07:00:00Z'
);
```

When a later decision supersedes this direction, the old row gets `superseded_at` set and the new row's `superseded_by` points back to it. This is the EXACT same temporal versioning pattern already used by `build_phase`, `completed_tier`, `next_tier`, and `next_action` keys. The generators already query `project_state WHERE superseded_at IS NULL` — no query change needed for this key.

### 3. How the next action enters the DB when no build_plan_nodes are PENDING

**Table:** `next_actions` (exists, no changes)

Current state: 13 `next_actions` rows, all COMPLETE. Generators query this table already (HCP_05 build order list) but NOT for the single "current next action" line.

Add one row:

```sql
-- NOTE: This block illustrates the row CONTENT only. Executable writes must use INSERT OR IGNORE
-- per Idempotency Contract §C.
INSERT INTO next_actions (id, tier, description, status, depends_on, created_at)
VALUES (
  'NA-SEED-013',
  'enforcement',
  'Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md as proposal only. Route through Claude audit + ChatGPT audit + Eric approval before any /opt/cis-control file lands.',
  'PENDING',
  'ADR-SEED-015',
  '2026-06-19T07:00:00Z'
);
```

The `depends_on` field references `ADR-SEED-015` — the architecture decision must exist before the spec can be drafted (already true). The `tier` field uses `'enforcement'` rather than a numeric tier since this work lives outside the Tier 1-11 build plan.

### 4. Generator query changes

**generate_agents_md.py — two changes:**

Change A: Section 1 (Build Phase) — append direction after build_phase line:
```python
# After line 114:
direction = build_state.get("current_direction", "")
if direction:
    lines.append(f"Direction: {direction}")
```
Result in AGENTS.md Section 1:
```
Tier 11D COMPLETE. ...
Direction: ADR-SEED-015 — three-layer process isolation. CIS control plane over Hermes...
```

Change B: Section 6 (Next Actions) — fallback to next_actions:
```python
# Current query (line 51-56):
actions = conn.execute(
    """SELECT node_label AS id, tier, node_label AS description, status
       FROM build_plan_nodes
       WHERE project_id='CIS' AND status IN ('PENDING','IN_PROGRESS')
       ORDER BY sequence"""
).fetchall()

# Add fallback (after the fetch, before the render):
if not actions:
    actions = conn.execute(
        """SELECT id, tier, description, status
           FROM next_actions
           WHERE status IN ('PENDING','IN_PROGRESS')
           ORDER BY created_at"""
    ).fetchall()
```

Result in AGENTS.md Section 6 (before fix = empty, after fix):
```
## 6. Next Actions
- [NA-SEED-013] (Tier enforcement) Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md...
```

**generate_hcp.py — two changes:**

Change C: HCP_01 (render_hcp_01) — add direction context after build_phase line:
```python
# After "Status: {status_line}" line (line 240):
direction = build_state.get("current_direction", "")
if direction:
    lines.append(f"Direction: {direction}")
```

Change D: HCP_05 (render_hcp_05) — fallback in "Current Next Action" section:
```python
# Current logic (lines 713-731):
in_progress = [n for n in build_plan_nodes if n["status"] == "IN_PROGRESS"]
eligible = [n for n in build_plan_nodes if n["status"] == "PENDING" and ...]
if in_progress:
    lines.append(f"**{node['node_label']}** (IN PROGRESS)")
elif eligible:
    lines.append(f"**{node['node_label']}**")
else:
    lines.append("(No eligible PENDING node in build plan.)")

# Add fallback to next_actions (in the else block):
else:
    na_pending = [a for a in actions if a["status"] in ("PENDING", "IN_PROGRESS")]
    if na_pending:
        na = na_pending[0]
        lines.append(f"**{na['id']}**: {na['description']}")
    else:
        lines.append("(No eligible PENDING node in build plan.)")
```

Change E: HCP_07 (render_hcp_07) — same fallback pattern for "Exact Next Action" section (lines 950-958).

**generate_hcp.py already reads `project_decisions`** (HCP_03): ADR-SEED-015 appears automatically in the decisions table with no code change. HCP_03 renders ALL `project_decisions` rows regardless of status.

### 5. How DEV-PIVOT advisor records are generated from the spine

**Phase 1 (this proposal): Index only.** Add `project_state` key `devpivot_index`:

```sql
-- NOTE: This block illustrates the row CONTENT only. Do not execute this as the write sequence.
-- For executable/idempotent project_state writes, use the canonical UPDATE-then-INSERT sequence
-- in Idempotency Contract §A.
INSERT INTO project_state (key, value, source, created_at)
VALUES (
  'devpivot_index',
  'DEV-PIVOT-01,DEV-PIVOT-02,DEV-PIVOT-03,DEV-PIVOT-04,DEV-PIVOT-05,DEV-PIVOT-06,DEV-PIVOT-07,DEV-PIVOT-08,DEV-PIVOT-09,DEV-PIVOT-10,DEV-PIVOT-11,DEV-PIVOT-12,DEV-PIVOT-13,DEV-PIVOT-14,DEV-PIVOT-15,DEV-PIVOT-16,DEV-PIVOT-17',
  'manual',
  '2026-06-19T07:00:00Z'
);
```

Generators read this key to know which DEV-PIVOT files exist. Currently they're hand-maintained — the index tells the system "these records exist, here's where to find them." When a new DEV-PIVOT is created, append to the index.

**Phase 2 (future, out of scope): Template-based generation.** Each DEV-PIVOT maps to a `decision_trails` row (via `workflow_run_id`). A `generate_devpivot.py` script reads `decision_trails.proposed_action` + `project_decisions.decision` + `decision_trails.problem_statement` and renders a DEV-PIVOT markdown file from a template. The `devpivot_index` key feeds the generation loop. This is deferred — Phase 1 is sufficient to close the doc-sync gap.

### Idempotency Contract (D6)

Every DB write in this proposal is safe to re-run. If the write script runs twice (operator error, pipeline retry, subshell re-entry), the second execution is a no-op — it neither errors nor duplicates state.

**A. project_state writes — supersede BEFORE insert (canonical sequence)**

`project_state` uses append-only semantics with a `superseded_at` / `superseded_by` chain. A direct INSERT without superseding the prior active row would leave TWO rows with `superseded_at IS NULL` for the same key — the generators would see both and pick the wrong one (or the newer one, depending on query).

**Do NOT use `supersede_project_state()` for this task.** The helper at `runtime/db/database.py:300` supersedes rows `WHERE key=? AND superseded_at IS NULL` with no `id` exclusion. Calling it AFTER inserting the new row (passing the new row id) would supersede the new row too, leaving zero active rows. This task uses inline SQL instead, and does NOT modify or call `database.py` helpers.

Canonical write sequence for each project_state key — **UPDATE (supersede) first, then INSERT**:

```sql
-- 1. Supersede any prior active row FIRST (0 rows affected for a brand-new key)
UPDATE project_state SET superseded_at = datetime('now')
WHERE key = 'current_direction' AND superseded_at IS NULL;

-- 2. Insert the new active row (superseded_at defaults NULL = active)
INSERT INTO project_state (key, value, source, created_at)
VALUES ('current_direction', 'ADR-SEED-015 — three-layer...', 'manual', '2026-06-19T07:00:00Z');
```

Why supersede-first, not insert-first: superseding before the insert means there is nothing to exclude — the new row is inserted AFTER the clear, so no `id != <new_row_id>` guard is needed and the self-supersession trap is structurally impossible. Insert-first requires an `id !=` guard to avoid superseding the row just written; supersede-first removes that fragility entirely.

Idempotency guarantee: If the script runs twice, run 2 supersedes the row run 1 inserted, then inserts a fresh active row. Exactly one active row per key at all times. The generators read `WHERE superseded_at IS NULL AND id = (SELECT MAX(id)...)` — highest-id unsuperseded row, which is the most recent write. No duplicate active state, no stale pointer, no zero-active-row window (run the UPDATE and INSERT in one transaction; if the INSERT fails, the transaction rolls back and the prior row stays active).

**B. project_decisions — INSERT OR IGNORE**

`project_decisions.id` is TEXT PRIMARY KEY. A bare `INSERT INTO project_decisions VALUES (...)` on a duplicate id would fail with `UNIQUE constraint failed`. Use `INSERT OR IGNORE`:

```sql
INSERT OR IGNORE INTO project_decisions (id, label, decision, reason, status, decided_at)
VALUES ('ADR-SEED-015', ...);
```

Second run: no-op. The row is already there; the second INSERT is silently ignored. No error, no duplicate.

**C. next_actions — INSERT OR IGNORE**

`next_actions.id` is TEXT PRIMARY KEY. Same pattern:

```sql
INSERT OR IGNORE INTO next_actions (id, tier, description, status, depends_on, created_at)
VALUES ('NA-SEED-013', ...);
```

Second run: no-op.

**D. Fallback rendering — deterministic ORDER BY**

The fallback query in the generators uses `ORDER BY created_at`:

```sql
SELECT id, tier, description, status FROM next_actions
WHERE status IN ('PENDING','IN_PROGRESS')
ORDER BY created_at
```

When multiple PENDING next_actions exist: oldest (by creation time) is selected first. This is monotonic and deterministic — re-running the generator produces identical output. If a newer action should take priority, change its status to IN_PROGRESS (which sorts first in the Python fallback filter).

**E. devpivot_index — same supersede pattern as A**

Follows the same canonical UPDATE-then-INSERT sequence as §A (supersede the prior active `devpivot_index` row first, then insert the new list). Does NOT call `supersede_project_state()`. When DEV-PIVOT-18 is created, supersede the old index row and insert the new list.

### Audit Evidence (read-only verification run 2026-06-19)

```
# Schemas match proposal claims:
project_decisions.id        TEXT PRIMARY KEY       → INSERT OR IGNORE works
project_decisions.superseded_by  TEXT               → chaining pointer
project_state.superseded_at      TEXT               → NULL = active
project_state.superseded_by      INTEGER FK → id   → temporal chain
next_actions.id              TEXT PRIMARY KEY       → INSERT OR IGNORE works
next_actions.tier            TEXT                   → 'enforcement' is valid
next_actions.depends_on      TEXT                   → 'ADR-SEED-015' fits

# Existing helpers (runtime/db/database.py):
supersede_project_state()    line 300               → known; NOT used, NOT modified (inline SQL instead — lacks id-exclusion guard)
insert_project_state()       line 273               → known; NOT used, NOT modified (inline SQL instead)
insert_project_decision()    line 224               → known; NOT used, NOT modified (inline INSERT OR IGNORE instead)
# Do NOT alter database.py helper functions as part of this task.

# Generator filter confirmed:
generate_agents_md.py:39-41  project_decisions WHERE status != 'SUPERSEDED' AND id LIKE 'ADR-SEED-%'
generate_hcp.py:118          project_decisions ORDER BY decided_at DESC  (ALL rows, no filter)
generate_agents_md.py:51-56  build_plan_nodes WHERE status IN ('PENDING','IN_PROGRESS')
generate_hcp.py:126          next_actions ORDER BY tier, id (already used for build order)

# Off-by-one confirmed (noted, not fixed):
AGENTS.md says "25/27 COMPLETE, 2 DEFERRED" → actual spine: 24 COMPLETE, 3 DEFERRED = 27 total
This is a pre-existing drift in AGENTS.md build_phase string, not caused by this proposal.
It resolves when the build_phase key is next superseded with an accurate count.

# NA-SEED-013 available:
max NA-SEED numeric = 012. NA-SEED-013 does not exist.
```

### Execution Evidence Requirement

Approval does not accept agent attestation that writes landed. The executor must capture raw output from these exact commands, run AFTER the DB writes and AFTER the generator export:

**DB write verification:**
```bash
sqlite3 data/cis_memory.db "SELECT id, status FROM project_decisions WHERE id='ADR-SEED-015';"
sqlite3 data/cis_memory.db "SELECT key, value FROM project_state WHERE key='current_direction' AND superseded_at IS NULL;"
sqlite3 data/cis_memory.db "SELECT id, status FROM next_actions WHERE id='NA-SEED-013';"
```

**Generator output verification (post-export greps):**
```bash
grep "Direction:" AGENTS.md | head -1                          # §1: direction present
grep "ADR-SEED-015" AGENTS.md | head -1                         # §4: decision renders
grep "NA-SEED-013" AGENTS.md                                    # §6: next action renders
grep "ADR-SEED-015" PROJECT_CONTEXT_PACK_UPLOAD/HCP_03_DECISIONS_LOG.md | head -1  # HCP_03
grep "NA-SEED-013" PROJECT_CONTEXT_PACK_UPLOAD/HCP_05_NEXT_ACTIONS.md | head -1     # HCP_05
```

Each grep must return at least one line matching the "After" block in §First Test Case below. "Confirmed present" or "verified" without raw output is insufficient — the whole doc-sync failure exists because formatted success reports masked broken state. Raw output, matched against the expected lines, or the gap is not closed.

**Self-supersession check:** After the write, confirm exactly one active row for each key:

```bash
sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM project_state WHERE key='current_direction' AND superseded_at IS NULL;"
sqlite3 data/cis_memory.db "SELECT COUNT(*) FROM project_state WHERE key='devpivot_index' AND superseded_at IS NULL;"
```

Both must return `1`. For `current_direction` (new key): the UPDATE affects 0 rows on first run, the INSERT lands one active row. For `devpivot_index`: same. Run the UPDATE and INSERT in a single transaction — if the INSERT fails, the transaction rolls back and no active row is lost. If either returns 0, the transaction did not commit — re-run the §A sequence (supersede-first makes re-runs safe).

### State After This Closes

- Spine authoritative for current direction + next action.
- Next export reflects DEV-PIVOT-17. Doc-sync gap closed for this decision class.
- Generator edits in — future generator writes route through the control plane once it exists (N4 precedent).
- Tradeoff: generator edits leave a verification tail until the run proves render. The evidence step above closes it.

## First Test Case: DEV-PIVOT-17 in the Spine

### Before (current state)

```
$ sqlite3 data/cis_memory.db "SELECT key, value FROM project_state WHERE key='current_direction' AND superseded_at IS NULL;"
(no rows)

$ sqlite3 data/cis_memory.db "SELECT id, status FROM next_actions WHERE status IN ('PENDING','IN_PROGRESS');"
(no rows — all 13 are COMPLETE)

$ grep "## 6. Next Actions" AGENTS.md -A 1
## 6. Next Actions
(empty — zero content)

$ sqlite3 data/cis_memory.db "SELECT id, label FROM project_decisions WHERE id='ADR-SEED-015';"
(no rows)
```

AGENTS.md generated output for Section 1: `Tier 11D COMPLETE. ...` — no mention of enforcement architecture.
AGENTS.md generated output for Section 6: EMPTY.
HCP_05 "Current Next Action": `(No eligible PENDING node in build plan.)`

### After (proposed fix applied)

Dev writes (proposal approval → Eric or Hermes runs these, safe to re-run). Run as a single transaction so a mid-script failure rolls back rather than leaving partial state:

```sql
BEGIN;

-- 1. Record the decision (idempotent via PRIMARY KEY)
INSERT OR IGNORE INTO project_decisions (id, label, decision, reason, status, decided_at)
VALUES ('ADR-SEED-015', 'Enforcement architecture: three-layer process isolation',
        'CIS enforces Hermes via root-owned /opt/cis-control...',
        '16 failure modes are LLM behavior failures...', 'DECIDED', '2026-06-19T07:00:00Z');

-- 2. Current direction (canonical: supersede FIRST, then insert — §A)
UPDATE project_state SET superseded_at = datetime('now')
WHERE key = 'current_direction' AND superseded_at IS NULL;
INSERT INTO project_state (key, value, source, created_at)
VALUES ('current_direction', 'ADR-SEED-015 — three-layer process isolation...', 'manual', '2026-06-19T07:00:00Z');

-- 3. Queue the next action (idempotent via PRIMARY KEY)
INSERT OR IGNORE INTO next_actions (id, tier, description, status, depends_on, created_at)
VALUES ('NA-SEED-013', 'enforcement',
        'Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md as proposal only. Route through Claude audit + ChatGPT audit + Eric approval before any /opt/cis-control file lands.',
        'PENDING', 'ADR-SEED-015', '2026-06-19T07:00:00Z');

-- 4. Index DEV-PIVOT files (canonical: supersede FIRST, then insert — §A)
UPDATE project_state SET superseded_at = datetime('now')
WHERE key = 'devpivot_index' AND superseded_at IS NULL;
INSERT INTO project_state (key, value, source, created_at)
VALUES ('devpivot_index', 'DEV-PIVOT-01,DEV-PIVOT-02,...,DEV-PIVOT-17', 'manual', '2026-06-19T07:00:00Z');

COMMIT;
```


Generator output after fix:

```
AGENTS.md Section 1:
Tier 11D COMPLETE. ...
Direction: ADR-SEED-015 — three-layer process isolation...

AGENTS.md Section 4:
- [ADR-SEED-015] Enforcement architecture: three-layer process isolation: CIS enforces Hermes via...

AGENTS.md Section 6:
- [NA-SEED-013] (Tier enforcement) Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md...

HCP_03 decisions table:
| 2026-06-19 | [ADR-SEED-015] Enforcement architecture: three-layer process isolation: CIS... | ... | DECIDED | spine record |

HCP_05 Current Next Action:
**NA-SEED-013**: Draft TASK_CONTRACT_ENFORCEMENT_PRIMITIVE_V1.md as proposal only...
```

## Why This Doesn't Need the Enforcement Primitive

Cause 4 (chicken-and-egg): "we're building the primitive because the system can't be trusted; but we need the system to record the decision to build the primitive."

This fix runs on the CURRENT system with no trust dependency:

- `project_state` already works — used for 30+ build_phase rows across Tier 6-11D
- `project_decisions` already works — 14 ADR-SEED rows, all verified
- `next_actions` already works — 13 rows, all tracked through their lifecycle
- The generators already query all three tables — they just don't use them for the right things
- The SQL writes are deterministic INSERT statements — no agent judgment, no policy parsing, no hook needed

The only trust question is "who writes the INSERT" — and the answer is the same as today: Eric (via Hermes under Eric's direction) or Closeout (deterministic script). No enforcement primitive needed to write a row to a table that already has 30+ rows.

## Rejected Alternatives

- **New `session_decisions` table**: Duplicates `project_decisions` + `decision_trails` functionality. Same data in two places diverges.
- **Extend `build_plan_nodes` with `PROPOSED` status for enforcement work**: Mixes infrastructure build nodes with design decisions. The `build_plan_nodes` table tracks the dependency graph build plan — enforcement primitive work isn't a build-plan node. Using `PROPOSED` here pollutes the dependency resolver.
- **JSON blob in `project_state` for all session state**: Unqueryable by generators. Defeats the purpose of a structured spine.
- **Use `decision_trails` as the only decision store**: `decision_trails` is scoped to workflow runs. ADR-SEED decisions are project-level, not run-scoped. `project_decisions` is the correct project-level table.
- **Manual handoff file pattern indefinitely**: DISCOVERY_BRIEF already proved this fails — handoff files drift from spine state, generators don't read them.

## Authorship Rule

This proposal was drafted by Hermes (v4pro Drafter profile). Per DEV-PIVOT-17 trust root: Hermes proposing its own constraint architecture is acceptable for a PROPOSAL. The proposal routes through:

1. Claude audit (reads DISCOVERY_BRIEF + spine schema + generator source)
2. ChatGPT audit (same inputs, independent review)
3. Eric approval

No DB writes, no generator edits, no /opt/cis-control files are created until Eric approves. The INSERT statements above are illustrative — not executed.

---

**Next step:** Attach this file + DISCOVERY_BRIEF_DOC_SYNC_FAILURE.md + spine schema + generator source to Claude for audit.
