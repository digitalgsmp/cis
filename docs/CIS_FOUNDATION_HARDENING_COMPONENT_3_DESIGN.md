# CIS Foundation Hardening — Component 3 Design

## Eric Gate Redesign — Revision 2

**Document:** `docs/CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`
**Phase:** Foundation Hardening
**Component:** 3 — Eric Gate Redesign
**Status:** REVISED — incorporating ChatGPT audit (14 findings) + Eric reconciliation
**Author:** Claude (draft) → ChatGPT (audit, BLOCKED 14 findings) → v4impl (revision, ChatGPT-role drafter)
**Eric reconciliation:** All 14 audit findings ACCEPTED. Design revised accordingly.
**Authority:** Eric final approval required before implementation
**Implementation authority:** V4 Implementer only after FINAL_DIRECTIVE

---

## Changelog — Revision 2

| # | Finding | Change |
|---|---------|--------|
| 1 | goal_reference_id type mismatch | Changed TEXT → INTEGER to match goal_references.id |
| 2 | VETO/RETURN_TO_DRAFT briefing requirement unclear | Added explicit rule: all decisions require same full briefing |
| 3 | gate_db_state.py may fail on new table | Added post-migration verification test (Test 19) |
| 4 | 13 preconditions not fully covered by tests | Added Setter Precondition Tests group (Tests 10-18) |
| 5 | Blocked/out-of-order tier unverifiable | Downgraded to "verify declared goal trace only"; limitation documented |
| 6 | rejection_rationale join path unspecified | Added explicit JOIN through decision_trails (Section 4.4.3) |
| 7 | Hash canonicalization insufficient | Added 9 canonicalization rules (Section 5) |
| 8 | Multiple approval rows create ambiguity | Added is_current column + unique current-row index (Section 3.2) |
| 9 | Missing test fixture artifact | Added tools/eric_gate/seed_test_fixture.py (Section 13) |
| 10 | Missing status reader artifact | Added tools/eric_gate/show_status.py (Section 13) |
| 11 | Migration idempotency unstated | Added explicit migration policy (Section 3.4) |
| 12 | Export visibility unstated | Defined AGENTS.md/HCP export rules (Section 14) |
| 13 | No FINAL_DIRECTIVE enforcement point | Added gate_final_directive_allowed.py (Section 15) |
| 14 | Escalation-state check unspecified | Defined explicit SQL over Component 2 tables (Section 6.5, precondition 10) |

---

## 1. Purpose

Component 3 replaces the current placeholder Eric approval mechanism with a provenance-gated human approval checkpoint.

Current state:

* `workflow_runs.eric_approved_at` exists as a nullable `TEXT` column.
* No deterministic approval setter exists.
* No mandatory Eric Gate briefing exists.
* Closeout correctly fails while approval remains unset.
* Approval is not yet tied to what Eric saw, what goal the action advances, what objections were resolved, or what drift indicators were active.

Target state:

Eric must see a deterministic four-section briefing before approval. Eric may approve, veto, or return the run to draft. The decision must be recorded in the SQLite spine with timestamp, goal reference, briefing hash, drift snapshot, and decision rationale. VETO and RETURN_TO_DRAFT require the same full briefing payload as APPROVE — the only difference is they do not set `workflow_runs.eric_approved_at`.

The approval timestamp in `workflow_runs.eric_approved_at` remains as a compatibility/status field, but it is not sufficient as the source of truth.

---

## 2. Design Principle

Approval is valid only if CIS can prove:

1. Which workflow run Eric approved.
2. What exact briefing Eric saw.
3. Which project goal and dependency graph node the action advanced.
4. What decision trail led to the proposal.
5. What drift indicators and objections existed at the approval moment.
6. Whether Eric approved, vetoed, or returned the work to draft.

If any of those cannot be proven, the Eric Gate must fail closed.

---

## 3. New Schema

### 3.1 Migration File

Create:

`runtime/schema/migrations/0010_eric_gate_approvals.sql`

### 3.2 Table: `eric_gate_approvals`

```sql
CREATE TABLE IF NOT EXISTS eric_gate_approvals (
    id TEXT PRIMARY KEY,

    workflow_run_id TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (
        decision IN ('APPROVE', 'VETO', 'RETURN_TO_DRAFT')
    ),

    decided_at TEXT NOT NULL,
    decided_by TEXT NOT NULL DEFAULT 'Eric',

    -- CHANGED in Revision 2: INTEGER to match goal_references.id
    goal_reference_id INTEGER NOT NULL,

    briefing_hash TEXT NOT NULL,
    briefing_json TEXT NOT NULL,

    drift_snapshot_json TEXT NOT NULL,
    decision_trail_snapshot_json TEXT NOT NULL,

    -- ADDED in Revision 2: current-decision handling for multiple rows (VETO → RETURN → APPROVE)
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    supersedes_approval_id TEXT,

    rationale TEXT,

    created_at TEXT NOT NULL,

    FOREIGN KEY (workflow_run_id)
        REFERENCES workflow_runs(id),

    FOREIGN KEY (goal_reference_id)
        REFERENCES goal_references(id),

    FOREIGN KEY (supersedes_approval_id)
        REFERENCES eric_gate_approvals(id)
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_eric_gate_approvals_workflow_run_id
    ON eric_gate_approvals(workflow_run_id);

CREATE INDEX IF NOT EXISTS idx_eric_gate_approvals_goal_reference_id
    ON eric_gate_approvals(goal_reference_id);

-- Only one current decision per workflow run
CREATE UNIQUE INDEX IF NOT EXISTS idx_eric_gate_one_current_decision
    ON eric_gate_approvals(workflow_run_id)
    WHERE is_current = 1;
```

### 3.3 Workflow Runs Compatibility Field

Continue using:

```sql
workflow_runs.eric_approved_at
```

Rules:

* Set `workflow_runs.eric_approved_at` only when `decision = 'APPROVE'` and `is_current = 1`.
* Leave `workflow_runs.eric_approved_at` NULL when `decision = 'VETO'`.
* Leave `workflow_runs.eric_approved_at` NULL when `decision = 'RETURN_TO_DRAFT'`.
* Never treat `eric_approved_at` alone as proof of approval.
* The closeout gate must select the current `eric_gate_approvals` row where `is_current = 1`, not any historical row.

### 3.4 Migration Policy

* Migration is idempotent — uses `CREATE TABLE IF NOT EXISTS`.
* Migration does not backfill approvals into existing `workflow_runs` rows.
* Migration does not mutate existing `workflow_runs` rows.
* Existing `workflow_runs.eric_approved_at` values, if any, are legacy and not automatically trusted.
* Legacy approvals require either explicit backfill with full provenance or gate exclusion.
* `gate_db_state.py` must be updated (or verified tolerant) after migration to include `eric_gate_approvals` in its expected schema.

---

## 4. Briefing Builder

### 4.1 File Path

Create:

`tools/eric_gate/build_briefing.py`

### 4.2 Input

Required argument:

```bash
python3 tools/eric_gate/build_briefing.py --workflow-run-id <RUN_ID>
```

Optional output modes:

```bash
--json          # print canonical JSON to stdout
--markdown      # print markdown-formatted briefing to stdout
--write         # write to runtime/eric_gate/briefings/<RUN_ID>.json
```

### 4.3 Output

The builder produces one canonical JSON object:

```json
{
  "briefing_schema_version": "1.0.0",
  "workflow_run_id": "...",
  "generated_at": "...",
  "source_fingerprint": {
    "git_head": "<full 40-char SHA>",
    "workflow_run_updated_at": "...",
    "latest_deliberation_round_id": "...",
    "latest_drift_indicator_id": "...",
    "goal_reference_id": 1
  },
  "briefing": {
    "action_summary": {
      "plain_language_summary": "...",
      "files_expected_to_change": [],
      "reversibility": "REVERSIBLE"
    },
    "goal_trace": {
      "project_goal": "...",
      "goal_reference_id": 1,
      "dependency_graph_node": "...",
      "tier_advanced": "...",
      "why_this_action_closes_or_advances_node": "..."
    },
    "decision_trail": {
      "problem": "...",
      "deliberation_path": [],
      "key_objections": [],
      "resolution_summary": "..."
    },
    "drift_indicators": {
      "open_drift_count": 0,
      "blocking_drift": [],
      "warnings": [],
      "flags": {
        "temporary_dependency_without_retirement_trigger": false,
        "diverges_from_dependency_graph": false,
        "objection_dismissed_without_resolution": false,
        "component_patched_more_than_once_without_root_cause_fix": false
      }
    },
    "approved_file_manifest": {
      "status": "NOT_YET_IMPLEMENTED",
      "files": [],
      "enforcement": "PENDING_OQ_SEED_005"
    }
  }
}
```

### 4.4 Four Required Briefing Sections

The builder must assemble these four sections from spine data.

#### Section 1 — Action Summary

Purpose: One plain-language paragraph explaining what will change, why, whether it is reversible, and what files or systems are expected to change.

Sources: `workflow_runs`, `next_actions`, `decision_trails`. Future: Approved File Manifest when OQ-SEED-005 is resolved.

Fail conditions: no action summary can be assembled; action is not tied to one workflow run; reversibility is absent or unknown without explicit warning.

#### Section 2 — Goal Trace

Purpose: Show how the action connects to defined project goal, dependency graph node, tier/component advanced, and why this action is allowed now.

Sources: `goal_references`, `workflow_runs`, project decisions, build-order records.

**Limitation (Revision 2):** Component 3 verifies the declared goal trace from `goal_references` (goal_label, dependency_node, tier_advanced, advancement_type). It cannot fully verify whether a tier is globally blocked or out of order because the dependency graph is not yet machine-readable. Full blocked/out-of-order tier verification is deferred until dependency graph data is represented in queryable form (future infrastructure). The gate will flag if no `goal_references` row exists or if tier/node is absent, but will not assert global build-order validity beyond what the spine records.

Fail conditions: no `goal_references` row exists; no dependency graph or tier reference exists; goal trace is manually invented instead of spine-derived.

#### Section 3 — Decision Trail

Purpose: Condense the path from problem to proposal — original problem, deliberation rounds, key objections, how objections were resolved, why proposal reached Eric Gate.

Sources: `decision_trails`, `deliberation_rounds`, `rejection_rationale` (joined through `decision_trails`), `workflow_runs.final_objections_json`.

**Rejection rationale join path (Revision 2):**

```sql
SELECT rr.id, rr.rejected_option_label, rr.rejected_option_summary,
       rr.rejection_reason, rr.rejection_detail, rr.rejected_by
FROM rejection_rationale rr
JOIN decision_trails dt ON rr.decision_trail_id = dt.id
WHERE dt.workflow_run_id = ?
  AND rr.workflow_run_id = dt.workflow_run_id   -- consistency check
ORDER BY dt.trail_sequence, rr.id;
```

Fail conditions: workflow has no deliberation history; final objections remain unresolved; objection is dismissed without recorded rationale; decision trail cannot show why consensus was reached.

#### Section 4 — Drift Indicators

Purpose: Surface automatic risk flags before Eric approval.

Required flags:

1. temporary dependency with no retirement trigger
2. action diverges from dependency graph
3. objection dismissed without resolution
4. component patched more than once without root cause fix

Sources: `drift_indicators`, `active_blockers`, `open_questions`, `rejection_rationale` (via decision_trails join), `decision_trails`, `workflow_runs`, git/file history where available.

Fail conditions: open blocking drift exists; unresolved mandatory escalation exists; repeated patching is detected without root-cause resolution; drift section is omitted entirely.

---

## 5. Briefing Hash — Canonicalization Rules

The briefing builder must compute a deterministic SHA256 hash over the canonical JSON payload.

Canonicalization rules (Revision 2):

1. JSON serialized with `sort_keys=True, separators=(",", ":")`.
2. All IDs serialized as their true schema type (INTEGER stays integer, TEXT stays string).
3. All timestamps normalized to UTC ISO-8601 format: `YYYY-MM-DDTHH:MM:SSZ` (no sub-second precision, no timezone variants).
4. All SQL row collections ordered by deterministic `ORDER BY` clauses.
5. Missing optional fields represented as `null` consistently (never omit a known field).
6. Empty collections represented as `[]`, never `null` and never omitted.
7. Unicode normalized to NFC (`unicodedata.normalize("NFC", text)`).
8. Git HEAD uses full 40-character SHA, never short hash.
9. Hash includes `briefing_schema_version` field to detect schema changes.
10. `generated_at` timestamp is EXCLUDED from hash computation to allow staleness detection separately from content matching.
11. User-authored `rationale` text is NOT included in briefing hash (rationale is post-decision, not pre-decision).

Example:

```python
import hashlib, json, unicodedata

def canonicalize(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False)
    return unicodedata.normalize("NFC", raw)

def compute_briefing_hash(payload):
    # Exclude volatile fields
    hash_payload = {k: v for k, v in payload.items()
                    if k not in ("generated_at", "rationale")}
    canonical = canonicalize(hash_payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

---

## 6. Approval Setter

### 6.1 File Path

Create:

`tools/eric_gate/record_decision.py`

### 6.2 Approval Command

```bash
python3 tools/eric_gate/record_decision.py \
  --workflow-run-id <RUN_ID> \
  --decision APPROVE \
  --briefing-hash <HASH> \
  --goal-reference-id <GOAL_REFERENCE_ID> \
  --rationale "<ERIC_NOTE>"
```

### 6.3 Veto Command

```bash
python3 tools/eric_gate/record_decision.py \
  --workflow-run-id <RUN_ID> \
  --decision VETO \
  --briefing-hash <HASH> \
  --goal-reference-id <GOAL_REFERENCE_ID> \
  --rationale "<ERIC_NOTE>"
```

### 6.4 Return-to-Draft Command

```bash
python3 tools/eric_gate/record_decision.py \
  --workflow-run-id <RUN_ID> \
  --decision RETURN_TO_DRAFT \
  --briefing-hash <HASH> \
  --goal-reference-id <GOAL_REFERENCE_ID> \
  --rationale "<ERIC_NOTE>"
```

### 6.5 Setter Preconditions

All decision types (APPROVE, VETO, RETURN_TO_DRAFT) require the same full briefing payload, goal reference, drift snapshot, and decision trail snapshot. The only difference is whether `workflow_runs.eric_approved_at` is set.

The setter must verify all 13 preconditions before any write. If any precondition fails, the setter exits non-zero and writes nothing.

1. Workflow run exists — `SELECT id FROM workflow_runs WHERE id = ?` returns a row.
2. Workflow run result is `CONSENSUS_REACHED` — `workflow_runs.result = 'CONSENSUS_REACHED'`.
3. Workflow run requires Eric review — `workflow_runs.requires_eric_review = 1` unless an explicit exemption is recorded (exemption mechanism deferred, not in Component 3 scope).
4. Briefing can be rebuilt from current spine state — calling `build_briefing.py --workflow-run-id <RUN_ID>` succeeds with exit code 0.
5. Rebuilt briefing hash equals supplied briefing hash — match computed from canonical rebuild.
6. Supplied goal reference exists and belongs to this workflow run or approved project context — `goal_references` row must have matching `workflow_run_id` or be an approved project-level goal.
7. All four briefing sections are present — action_summary, goal_trace, decision_trail, drift_indicators all non-null with required content.
8. No open blocking drift indicator exists — `SELECT COUNT(*) FROM drift_indicators WHERE workflow_run_id = ? AND status IN ('RAISED', 'ACKNOWLEDGED', 'ESCALATED')` returns 0.
9. No unresolved final objection exists — `workflow_runs.final_objections_json` either NULL, empty array, or all objections marked resolved.
10. No mandatory escalation remains unreconciled — escalation check via Component 2 tables (see Section 6.7).
11. No prior current approval exists — `SELECT COUNT(*) FROM eric_gate_approvals WHERE workflow_run_id = ? AND is_current = 1 AND decision = 'APPROVE'` returns 0 unless `--supersede` flag is passed.
12. Git HEAD matches briefing source fingerprint — `git rev-parse HEAD` full SHA equals `source_fingerprint.git_head` from the briefing.
13. Decision is one of `APPROVE`, `VETO`, or `RETURN_TO_DRAFT` — enum check.

### 6.6 Setter Write Behavior

All writes for a single decision must execute in a single SQLite transaction. If the transaction fails at any point, the entire decision is rolled back and no partial state is written.

For `APPROVE`:

* Begin transaction.
* If a prior current row exists (VETO or RETURN_TO_DRAFT), set its `is_current = 0` and set `supersedes_approval_id` on the new row to reference the superseded row ID.
* Insert row into `eric_gate_approvals` with `is_current = 1`.
* Set `workflow_runs.eric_approved_at = decided_at`.
* Update `workflow_runs.updated_at`.
* Commit transaction.
* Do not generate FINAL_DIRECTIVE automatically.

For `VETO`:

* Begin transaction.
* If a prior current row exists, set its `is_current = 0` and set `supersedes_approval_id` on the new row.
* Insert row into `eric_gate_approvals` with `is_current = 1`.
* Leave `workflow_runs.eric_approved_at` NULL.
* Record rationale.
* Commit transaction.
* Leave workflow run status unchanged; rely on approval table for decision history.

For `RETURN_TO_DRAFT`:

* Begin transaction.
* If a prior current row exists, set its `is_current = 0` and set `supersedes_approval_id` on the new row.
* Insert row into `eric_gate_approvals` with `is_current = 1`.
* Leave `workflow_runs.eric_approved_at` NULL.
* Record rationale.
* Commit transaction.
* Leave workflow run status unchanged; rely on approval table for decision history.

### 6.7 Escalation-State Check Integration

Precondition 10 requires verification that no mandatory escalation remains unreconciled. This check uses Component 2 escalation tables.

If Component 2 escalation tables exist in the schema, query:

```sql
SELECT COUNT(*) FROM advisor_escalations
WHERE workflow_run_id = ?
  AND trigger_class = 'MANDATORY'
  AND status NOT IN ('RECONCILED', 'CANCELLED_BY_ERIC', 'ABANDONED', 'SUPERSEDED');
```

Actual Component 2 schema confirmed: `advisor_escalations` table has `trigger_class` (not `escalation_type`) with values `DISCRETIONARY`/`MANDATORY`, and `status` with values `OPEN`/`PACKET_BUILT`/`TRANSMITTED`/`RESPONSES_COMPLETE`/`RECONCILED`/`ABANDONED`/`SUPERSEDED`/`CANCELLED_BY_ERIC`. This SQL uses the correct column names and excludes all four terminal states.

If Component 2 tables do not yet exist, the check is a no-op with a warning logged. The check becomes active when escalation tables are available.

---

## 7. Closeout Gate Modification

### 7.1 File Path

Create:

`tools/gates/gate_eric_approval.py`

Then add it to:

`tools/gates/gate_runner.sh`

and, if closeout-specific gates are chained separately:

`tools/closeout.sh`

### 7.2 Gate Purpose

The closeout gate must verify that an approved workflow run has valid approval provenance, not merely that `workflow_runs.eric_approved_at IS NOT NULL`.

### 7.3 Required Gate Checks

The gate must verify:

#### Check 1 — Valid workflow run

* `workflow_runs.id` exists.
* `workflow_runs.result = 'CONSENSUS_REACHED'`.
* Run is not in `ERROR`.
* Run is not superseded, abandoned, or cancelled.

#### Check 2 — Matching current approval row

Select the current Eric Gate decision row:

```sql
SELECT * FROM eric_gate_approvals
WHERE workflow_run_id = ?
  AND is_current = 1
ORDER BY decided_at DESC, created_at DESC, id DESC
LIMIT 1;
```

Then verify:

* Row exists.
* `decision = 'APPROVE'`.
* `workflow_runs.eric_approved_at = eric_gate_approvals.decided_at`.
* `decided_by = 'Eric'`.
* `is_current = 1`.

Prior VETO or RETURN_TO_DRAFT rows with `is_current = 0` must not cause the gate to fail.

#### Check 3 — Briefing integrity

* `briefing_json` is valid JSON.
* All four sections exist: action summary, goal trace, decision trail, drift indicators.
* Stored `briefing_hash` matches recomputed hash over canonical JSON.
* Rebuilt current briefing hash matches stored hash — unless the run has moved to a later valid state (e.g. post-implementation), in which case approval was valid at the time of decision.

#### Check 4 — Goal trace integrity

* `goal_reference_id` exists in `goal_references`.
* `goal_label` is not empty.
* `dependency_node` or `tier_advanced` is present.
* Limitation: global build-order validity is not asserted (deferred per Section 4.4.2).

#### Check 5 — Drift and objection state

* No open blocking drift indicators exist for the run at approval time (verified from `drift_snapshot_json`).
* No unresolved final objections exist in snapshot.
* No objection is dismissed without rationale.
* No mandatory escalation remains unreconciled.
* Repeated patching flag is either false or has root-cause resolution recorded.

#### Check 6 — Export agreement

* Approval state is visible to generated context.
* `tools/export/generate_all.py` succeeds.
* `tools/gates/gate_export_agreement.sh` passes.
* Generated HCP files and AGENTS.md match manifest.

### 7.4 Failure Rule

Any missing, stale, contradictory, or unverifiable approval provenance must fail the gate.

The gate must never pass solely because `eric_approved_at` is non-null.

---

## 8. Approved File Manifest Interaction

OQ-SEED-005 remains open. Component 3 must not fully solve Approved File Manifest enforcement.

The Eric Gate briefing reserves a field for implementation scope:

```json
"approved_file_manifest": {
  "status": "NOT_YET_IMPLEMENTED",
  "files": [],
  "enforcement": "PENDING_OQ_SEED_005"
}
```

Until OQ-SEED-005 is resolved:

* The briefing may warn that file-scope enforcement is pending.
* The setter must not pretend file-manifest enforcement exists.
* The closeout gate must not require manifest enforcement yet.

---

## 9. Closeout Trigger Interaction

OQ-SEED-004 remains open. Component 3 must not redesign closeout triggering.

Component 3 only adds approval validation into the existing gate/closeout pipeline.

* Do not change whether closeout is state-write triggered, gate-gated, or externally pulsed.
* Add Eric approval verification as a deterministic gate.
* Preserve current closeout pipeline behavior unless the gate fails.

---

## 10. Acceptance Tests

### Group A — Briefing Completeness Tests (Fail-Closed)

#### Test 1 — Missing briefing fails closed

Setup: Create or select workflow run with `CONSENSUS_REACHED`. Do not generate briefing.

```bash
python3 tools/eric_gate/record_decision.py --workflow-run-id <RUN_ID> --decision APPROVE
```

Expected: exits non-zero; no `eric_gate_approvals` row inserted; `workflow_runs.eric_approved_at` remains NULL.

#### Test 2 — Missing action summary fails closed

Setup: Generate malformed briefing without `action_summary` section.

Expected: setter exits non-zero; approval not recorded.

#### Test 3 — Missing goal trace fails closed

Setup: Generate briefing without `goal_trace` or without valid `goal_reference_id`.

Expected: setter exits non-zero; approval not recorded.

#### Test 4 — Missing decision trail fails closed

Setup: Generate briefing without `decision_trail`. Or use workflow run with no deliberation history.

Expected: setter exits non-zero; approval not recorded.

#### Test 5 — Open drift blocks approval

Setup: Add open blocking drift indicator (`status = 'RAISED'`) for run.

Expected: setter exits non-zero; failure message identifies blocking drift; approval not recorded.

#### Test 6 — Stale briefing hash blocks approval

Setup: Generate valid briefing. Add a new deliberation round, drift indicator, or goal reference change. Attempt approval with old hash.

Expected: setter exits non-zero; stale briefing/hash mismatch reported; approval not recorded.

#### Test 7 — Wrong-run briefing blocks approval

Setup: Generate briefing for run A. Attempt to approve run B with run A hash.

Expected: setter exits non-zero; approval not recorded for either run.

#### Test 8 — Veto records rationale but not approval timestamp

Setup: Generate valid briefing. Record decision `VETO`.

Expected: row inserted into `eric_gate_approvals` with `decision = 'VETO'`, `is_current = 1`; rationale non-empty; `workflow_runs.eric_approved_at` remains NULL; closeout gate does not treat run as approved.

#### Test 9 — Valid approval passes and closeout gate verifies provenance

Setup: Generate valid briefing. No open drift. Valid goal reference. Valid decision trail. Record decision `APPROVE`.

Expected: row inserted into `eric_gate_approvals` with `decision = 'APPROVE'`, `is_current = 1`; `workflow_runs.eric_approved_at` set; briefing hash recomputes correctly; `gate_eric_approval.py` passes; full gate runner passes if all other existing gates pass.

### Group B — Setter Precondition Tests (Revision 2)

#### Test 10 — Non-consensus run blocked

Setup: Create workflow run with result `ESCALATE` or `ERROR`.

```bash
python3 tools/eric_gate/record_decision.py \
  --workflow-run-id <NON_CONSENSUS_RUN> \
  --decision APPROVE \
  --briefing-hash <VALID_HASH> \
  --goal-reference-id <ID>
```

Expected: setter exits non-zero; error message states run result is not `CONSENSUS_REACHED`.

#### Test 11 — Missing workflow run blocked

Setup: Use a run ID that does not exist in `workflow_runs`.

Expected: setter exits non-zero; error message states workflow run not found.

#### Test 12 — Cross-run goal reference blocked

Setup: Goal reference belongs to run A. Attempt to approve run B using run A's goal reference.

Expected: setter exits non-zero; error message states goal reference does not belong to this workflow run.

#### Test 13 — Duplicate current approval blocked

Setup: Run already has an `eric_gate_approvals` row with `decision = 'APPROVE'` and `is_current = 1`. Attempt second approval without `--supersede`.

Expected: setter exits non-zero; error message states prior current approval exists.

#### Test 14 — Unreconciled escalation blocked

Setup: Add unreconciled mandatory escalation row linked to the workflow run (if Component 2 escalation tables exist).

Expected: setter exits non-zero; error message identifies unreconciled escalation.

#### Test 15 — Invalid decision enum blocked

Setup:

```bash
python3 tools/eric_gate/record_decision.py \
  --workflow-run-id <RUN_ID> \
  --decision INVALID_VALUE \
  --briefing-hash <HASH> \
  --goal-reference-id <ID>
```

Expected: setter exits non-zero; error message states invalid decision value.

#### Test 16 — Git HEAD mismatch blocked

Setup: Generate briefing at HEAD A. Change git HEAD (e.g., new commit). Attempt approval with old hash.

Expected: setter exits non-zero; error message states git HEAD mismatch.

#### Test 17 — Malformed briefing JSON blocked

Setup: Supply briefing hash computed from valid JSON, but store corrupted JSON in briefing file.

Expected: setter exits non-zero; error message states briefing JSON cannot be parsed or hash mismatch.

#### Test 18 — VETO → APPROVE history handled correctly

Setup:
1. Record `VETO` for run (is_current=1).
2. Record `APPROVE` for run (is_current=1, supersedes VETO row).

Expected:
* VETO row has `is_current = 0`.
* APPROVE row has `is_current = 1`, `supersedes_approval_id` = VETO row ID.
* `workflow_runs.eric_approved_at` is set.
* Closeout gate selects APPROVE row (is_current=1), not VETO row.
* `tools/eric_gate/show_status.py --workflow-run-id <RUN_ID>` shows full decision history.

### Group C — Post-Migration Verification Test (Revision 2)

#### Test 19 — gate_db_state.py passes after migration

Setup: Apply migration 0010. Then run existing DB state gate.

```bash
cd /mnt/projects/cis && python3 tools/gates/gate_db_state.py
```

Expected: PASS. `eric_gate_approvals` recognized as valid table. No schema mismatch errors.

---

## 11. VETO and RETURN_TO_DRAFT Briefing Requirement

**Explicit rule (Revision 2):** VETO and RETURN_TO_DRAFT require the same valid four-section briefing payload as APPROVE. The only difference is that VETO and RETURN_TO_DRAFT do not set `workflow_runs.eric_approved_at`.

Rationale: Eric cannot make an informed veto or return-to-draft decision without seeing the same provenance data. The schema enforces this via NOT NULL constraints on `briefing_json`, `drift_snapshot_json`, and `decision_trail_snapshot_json` for all decision types.

---

## 12. Files to Create or Modify

### Create

* `docs/CIS_FOUNDATION_HARDENING_COMPONENT_3_DESIGN.md`
* `runtime/schema/migrations/0010_eric_gate_approvals.sql`
* `tools/eric_gate/build_briefing.py`
* `tools/eric_gate/record_decision.py`
* `tools/eric_gate/show_status.py`
* `tools/eric_gate/seed_test_fixture.py`
* `tools/gates/gate_eric_approval.py`
* `tools/gates/gate_final_directive_allowed.py`
* `tests/test_eric_gate.py` (acceptance test suite, runs against temp DB copy)

### Modify

* `runtime/schema/spine_schema.sql` — add eric_gate_approvals table definition
* `runtime/db/database.py` — add write/read methods for eric_gate_approvals
* `tools/gates/gate_db_state.py` — update expected schema table list
* `tools/gates/gate_runner.sh` — add gate_eric_approval.py to gate chain
* `tools/closeout.sh` — add gate_eric_approval.py if closeout gates are separately chained

### Conditional Modifications

* `tools/export/generate_hcp.py` — add approval provenance summary per Section 14
* `tools/export/generate_agents_md.py` — add compact Eric Gate status per Section 14

### Do Not Modify Unless Separately Approved

* Router behavior
* Escalation packet protocol
* OQ-SEED-005 file manifest enforcement
* OQ-SEED-004 closeout trigger design
* Tier 8 MCP planning
* VDB/Chroma work
* UI redesign

---

## 13. New Artifact Descriptions (Revision 2)

### 13.1 tools/eric_gate/show_status.py

Purpose: Read-only inspection tool. Shows current approval state and full decision history for a workflow run.

```bash
python3 tools/eric_gate/show_status.py --workflow-run-id <RUN_ID>
```

Output: current decision (APPROVE/VETO/RETURN_TO_DRAFT), decided_at, goal reference, briefing hash, decision history table with all rows ordered by decided_at, is_current flag, closeout validity check (PASS/FAIL with reason).

### 13.2 tools/eric_gate/seed_test_fixture.py

Purpose: Create isolated test workflow runs with controlled properties for acceptance testing. Uses a temporary SQLite copy or `--db-path` argument to avoid mutating the live spine.

```bash
python3 tools/eric_gate/seed_test_fixture.py \
  --db-path /tmp/test_cis.db \
  --scenario <SCENARIO_NAME>
```

Scenarios: `consensus_reached`, `no_deliberation`, `with_drift`, `with_escalation`, `approved`, `vetoed`, `veto_then_approve`, `stale_briefing`.

### 13.3 tests/test_eric_gate.py

Purpose: Python test module that runs the full 19-test acceptance suite against a temporary SQLite database. Uses seed_test_fixture.py for setup, then exercises build_briefing.py, record_decision.py, gate_eric_approval.py, and show_status.py. All tests use `--db-path /tmp/test_eric_gate.db`.

---

## 14. Export Visibility (Revision 2)

### AGENTS.md (Hermes-native context)

Compact Eric Gate status block added:

```
## Eric Gate Status
- Workflow run: <RUN_ID>
- Status: APPROVED / VETOED / RETURNED_TO_DRAFT / PENDING
- Decided at: <timestamp> / Not yet decided
- Goal: <goal_label>
```

Does NOT include `briefing_json`, drift snapshot, or full decision trail.

### HCP (external advisor context)

Richer approval provenance summary added to HCP_07 (Recent Handoff) or HCP_06 (Protocol):

```
## Eric Gate Approval Status
- Decision: APPROVE / VETO / RETURN_TO_DRAFT
- Decided at: <timestamp>
- Goal reference: <goal_label> → <dependency_node>
- Drift state at approval: <open_drift_count> open, <blocking_count> blocking
- Briefing hash: <sha256>
- Decision trail summary: <one paragraph>
```

Includes decision, goal trace, drift summary, and briefing hash. Does NOT include full `briefing_json`.

---

## 15. FINAL_DIRECTIVE Enforcement (Revision 2)

### 15.1 File Path

Create:

`tools/gates/gate_final_directive_allowed.py`

### 15.2 Purpose

No FINAL_DIRECTIVE may be emitted for a workflow run unless Eric approval provenance passes verification.

### 15.3 Behavior

```bash
python3 tools/gates/gate_final_directive_allowed.py --workflow-run-id <RUN_ID>
```

The gate verifies:

1. `gate_eric_approval.py --workflow-run-id <RUN_ID>` passes (all 6 checks).
2. Workflow run has a current APPROVE decision in `eric_gate_approvals`.
3. No newer VETO or RETURN_TO_DRAFT has superseded the APPROVE.

If any check fails, exits non-zero and blocks FINAL_DIRECTIVE generation.

### 15.4 Integration Points

* Called by the FINAL_DIRECTIVE generator before emitting output.
* Called by the V4 Implementer routing layer before accepting a directive.
* Called by closeout before writing implementation evidence.

---

## 16. Implementation Boundary

This document is a design draft only.

It is not a FINAL_DIRECTIVE.

V4 Implementer must not implement from this document until:

1. ChatGPT audits this revised draft.
2. Eric reconciles audit findings.
3. Eric approves final design.
4. Eric issues an explicit FINAL_DIRECTIVE.

---

## 17. Final Recommendation

Component 3 should be implemented as a provenance gate, not a timestamp setter.

The approval setter should fail closed unless the system can prove the exact briefing Eric saw, the workflow run it belonged to, the goal it advanced, the decision trail behind it, and the drift state at the moment of approval.

`workflow_runs.eric_approved_at` may remain as a compatibility field, but approval truth must live in `eric_gate_approvals` with `is_current = 1`.

Multiple Eric Gate decisions (VETO → RETURN_TO_DRAFT → APPROVE) are supported through the `is_current` flag and `supersedes_approval_id` field. The closeout gate selects only the current row.

---

## Appendix A — ChatGPT Audit Summary (2026-06-11)

Status: BLOCKED (14 findings). All findings ACCEPTED by Eric and addressed in this Revision 2.

| # | Finding | Resolution |
|---|---------|------------|
| 1 | goal_reference_id type mismatch | Changed to INTEGER (Section 3.2) |
| 2 | VETO/RETURN briefing requirement unclear | Explicit rule added (Section 11) |
| 3 | gate_db_state.py update needed | Test 19 added |
| 4 | 13 preconditions not fully tested | Tests 10-18 added (Group B) |
| 5 | Blocked tier unverifiable | Downgraded claim + limitation documented (Section 4.4.2) |
| 6 | rejection_rationale join path | Exact SQL added (Section 4.4.3) |
| 7 | Hash canonicalization insufficient | 11 canonicalization rules (Section 5) |
| 8 | Multiple row ambiguity | is_current + unique index (Section 3.2, Section 7.3 Check 2) |
| 9 | Missing test fixture | seed_test_fixture.py (Section 13.2) |
| 10 | Missing status reader | show_status.py (Section 13.1) |
| 11 | Migration idempotency | Migration policy (Section 3.4) |
| 12 | Export visibility | AGENTS.md + HCP rules (Section 14) |
| 13 | No FINAL_DIRECTIVE enforcement | gate_final_directive_allowed.py (Section 15) |
| 14 | Escalation check unspecified | SQL over Component 2 tables (Section 6.7) |

---

*End of Revision 2. Awaiting ChatGPT audit and Eric approval before implementation.*
