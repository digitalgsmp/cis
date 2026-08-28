# Eric Gate Provenance System (2026-07-11)

## Problem

`gate_eric_approval.py` has 6 checks that verify approval provenance:
1. Valid workflow run (result = CONSENSUS_REACHED)
2. Matching approval row (decision = APPROVE, eric_approved_at matches)
3. Briefing integrity (valid JSON, 4 sections, hash matches)
4. Goal trace integrity (goal_reference exists, has label + advancement type)
5. Drift state (no blocking drift at approval time)
6. Export agreement (generate_all.py runs, gate_export_agreement.sh passes)

The approval endpoint (`POST /api/relay/<run_id>/gate` in `runtime/api/relay.py`)
was storing placeholders: `goal_reference_id=0`, `briefing_json='{}'`,
`briefing_hash=directive_hash`, `drift_snapshot_json='{}'`.

Checks 3 and 4 were made to SKIP on placeholder data — but Eric corrected:
"provenance is very important to access to the knowledge base can you fix
it instead of skipping."

## The Fix: Build Real Provenance at Approval Time

The approval endpoint now builds 3 provenance artifacts before writing
the `eric_gate_approvals` row:

### 1. goal_references Row

Created from the run's topic/intent. Links the approval to a goal.

```python
# Check for existing goal_reference, create if missing
existing_goal = conn.execute(
    "SELECT id FROM goal_references WHERE workflow_run_id = ? LIMIT 1",
    (run_id,)).fetchone()
if existing_goal:
    goal_ref_id = existing_goal[0]
else:
    cur = conn.execute(
        "INSERT INTO goal_references "
        "(workflow_run_id, goal_label, dependency_node, tier_advanced, "
        "advancement_type, authored_by) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, topic[:200], "", "", "PIPELINE_RUN", "ERIC_GATE"),
    )
    goal_ref_id = cur.lastrowid
```

**CHECK constraints (migration 0027):**
- `advancement_type` must be one of: CLOSES_NODE, ADVANCES_TIER,
  RESOLVES_BLOCKER, RESOLVES_OPEN_QUESTION, ESTABLISHES_PREREQUISITE,
  **PIPELINE_RUN** (added by migration 0027)
- `authored_by` must be one of: DRAFTER, REVIEWER, ERIC_GATE, ROUTER, CLOSEOUT
- `dependency_node` is NOT NULL — use empty string, not NULL

### 2. decision_trails Row

Created from deliberation rounds. Captures the full round-by-round history.

```python
rounds = conn.execute(
    "SELECT round_number, drafter_role, reviewer_signal "
    "FROM deliberation_rounds WHERE run_id = ? ORDER BY round_number",
    (run_id,)).fetchall()

cur = conn.execute(
    "INSERT INTO decision_trails "
    "(workflow_run_id, trail_sequence, problem_statement, "
    "research_summary, draft_summary, review_summary, "
    "proposed_action, round_count, consensus_signal, "
    "eric_decision, eric_decision_note, eric_decided_at, authored_by) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (run_id, 1, run["topic"],
     brain_summary, draft_summary, review_summary,
     directive[:500], len(rounds), consensus_signal,
     decision, rationale, now, "ROUTER"),
)
trail_id = cur.lastrowid
```

**CHECK constraints:**
- `authored_by` must be one of: DRAFTER, REVIEWER, CLOSEOUT, ROUTER
  (note: NO ERIC_GATE here, unlike goal_references)
- `UNIQUE(workflow_run_id, trail_sequence)`

### 3. Briefing JSON with Hash

4 required sections: action_summary, goal_trace, decision_trail, drift_indicators.

```python
briefing = {
    "briefing": {
        "action_summary": f"Eric {decision.lower()}d run {run_id}...",
        "goal_trace": {
            "goal_reference_id": goal_ref_id,
            "goal_label": goal_label,
            ...
        },
        "decision_trail": {
            "trail_id": trail_id,
            "round_count": round_count,
            "consensus_signal": consensus_signal,
            "rounds": round_summaries,
        },
        "drift_indicators": drift_snapshot,
    },
    "generated_at": now,
    "rationale": rationale,
}

# Hash excludes generated_at, rationale, briefing_hash
hash_payload = {k: v for k, v in briefing.items()
               if k not in ("generated_at", "rationale", "briefing_hash")}
canonical = unicodedata.normalize("NFC", json.dumps(
    hash_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
briefing_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

### 4. Drift Snapshot

Captured from `drift_indicators` table at approval time:

```python
drift_rows = conn.execute(
    "SELECT id, indicator_type, description, status, detected_by "
    "FROM drift_indicators WHERE workflow_run_id = ?",
    (run_id,)).fetchall()
open_drift = [d for d in drift_rows
              if d[3] in ("RAISED", "ACKNOWLEDGED", "ESCALATED")]
drift_snapshot = {
    "open_drift_count": len(open_drift),
    "blocking_drift": [...],
    "all_drift_count": len(drift_rows),
}
```

### 5. Final INSERT with Full Provenance

```python
conn.execute(
    "INSERT INTO eric_gate_approvals "
    "(workflow_run_id, decision, rationale, decided_at, "
    "goal_reference_id, briefing_hash, briefing_json, "
    "drift_snapshot_json, decision_trail_snapshot_json, "
    "is_current, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
    (run_id, decision, rationale, now,
     goal_ref_id, briefing_hash, briefing_json,
     drift_snapshot_json, trail_snapshot_json, now),
)
```

## Gate Updates

`gate_eric_approval.py` checks 3 and 4 now FAIL instead of SKIP:
- Check 3: `if not briefing_json or briefing_json in ("", "{}"): fail(3, ...)`
- Check 4: `if not goal_id or goal_id == 0: fail(4, ...)`

Check 4 also accepts `advancement_type` as a third option alongside
`dependency_node` and `tier_advanced` (pipeline runs aren't tied to
build plan nodes).

## SQLite CHECK Constraint Gotchas

When inserting into CIS spine tables, CHECK constraints on enum columns
will silently reject invalid values. Always check the schema first:

```bash
sqlite3 data/cis_memory.db ".schema goal_references"
sqlite3 data/cis_memory.db ".schema decision_trails"
```

Migration 0027 added `PIPELINE_RUN` to the `advancement_type` CHECK.
SQLite doesn't support `ALTER TABLE ... ALTER CHECK` — the migration
recreates the table (backup → drop → recreate → restore → drop backup).

## Files Modified

- `runtime/api/relay.py` — provenance capture in `relay_gate()` function
- `enforcement/mwl-proof-v2/gates/gate_eric_approval.py` — removed SKIP, added FAIL
- `tools/gates/gate_eric_approval.py` — copy of the above
- `runtime/schema/migrations/0027_add_pipeline_run_advancement_type.sql` — new migration

## Supersedes

The SKIP logic in `references/verification_phase_gate_fixes.md` fix #6
is now superseded by this provenance capture system.
