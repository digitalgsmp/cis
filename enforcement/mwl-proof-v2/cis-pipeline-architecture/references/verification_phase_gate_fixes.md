# Verification Phase Gate Fixes (2026-07-11, commit 8ef52eb)

After the external gate timing fix (commit 563ee22) resolved all 5 phases'
timing races, the verification phase still had 5 blocking issues that
prevented the pipeline from completing through Menter → Verify.

## Problem Summary

Test run `run-269b1220fcaf0135-1783780815` reached all 7 phases with
CONSENSUS_REACHED signals but final status was ESCALATED. Gate outcomes
showed 5 FAIL results in the verify phase:

```
ext_gate_service_health      | verify | FAIL | ADVISORY | port 8642 unreachable
ext_gate_endpoint            | verify | FAIL | ADVISORY | endpoint doesn't contain 'ok'
ext_gate_build_state_coherence | verify | FAIL | ADVISORY | Traceback: No module 'yaml'
ext_gate_eric_approval       | verify | FAIL | BLOCK    | Run result is 'PENDING', expected 'CONSENSUS_REACHED'
ext_gate_eric_approval_present | verify | FAIL | BLOCK  | eric_approved_at is null
```

## Root Causes and Fixes

### 1. gate_service_health.sh — wrong port (ADVISORY)

**Root cause**: `PHASE_GATE_MAP` in `guardrails.py` hardcoded args `["8642", "ok"]`.
Port 8642 is the retired prime gateway. The container API runs on port 5000.

**Fix**: Changed to `["5000", "ok"]` in `guardrails.py` line 1233.

### 2. gate_endpoint.sh — wrong URL path (ADVISORY)

**Root cause**: `PHASE_GATE_MAP` hardcoded URL `http://localhost:5000/health`.
The container API serves health at `/api/health`, not `/health`.

**Fix**: Changed to `http://localhost:5000/api/health`. Also added a `/health`
route alias in `runtime/container_app.py` so the gate_service_health.sh
default path `/health` works:
```python
@app.route("/health")
def health_alias():
    return health()
```

### 3. gate_build_state_coherence.py — missing pyyaml (ADVISORY)

**Root cause**: Gate scripts run with system Python (`#!/usr/bin/env python3`),
not the Hermes venv Python. The Hermes venv had pyyaml installed (`pip install
flask httpx pyyaml`), but system Python did not. The `apt-get install
python3-yaml` package didn't work for the `nikolaik/python-nodejs:python3.11-nodejs20`
base image.

**Fix**: Added `RUN pip3 install pyyaml` as a separate Dockerfile layer.
This also fixes `generate_all.py` and `generate_agents_md.py` which import yaml.

### 4. gate_eric_approval.py — workflow_runs.result still PENDING (BLOCK)

**Root cause**: The verification phase set `workflow_runs.result` in the
PASS/FAIL branch AFTER external gates fired. But `gate_eric_approval.py`
(BLOCK mode) checks `result == 'CONSENSUS_REACHED'` during external gates.
Result was still PENDING.

**Fix**: Moved the `workflow_runs.result` UPDATE to BEFORE
`run_external_gates()` in the verification phase:
```python
# Set workflow_runs.result BEFORE external gates fire
if status == "PASS":
    self.conn.execute(
        "UPDATE workflow_runs SET result = 'CONSENSUS_REACHED', "
        "completed_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), run_id)
    )
else:
    self.conn.execute(
        "UPDATE workflow_runs SET result = 'VERIFY_FAILED', "
        "completed_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), run_id)
    )
self.conn.commit()
# NOW run external gates
ext_report = run_external_gates(...)
```

Also removed the duplicate UPDATE from the PASS/FAIL branches below
(was setting it twice — once before ext gates, once after).

### 5. gate_eric_approval_present.sh — eric_approved_at null (BLOCK)

**Root cause**: The gate approval endpoint (`POST /api/relay/<run_id>/gate`
in `runtime/api/relay.py`) wrote to `eric_gate_approvals` table and updated
`workflow_runs.status` but never set `workflow_runs.eric_approved_at`.
The `gate_eric_approval_present.sh` gate checks this column is non-null.

**Fix**: Added `eric_approved_at = ?` to the UPDATE statement in the
approval endpoint:
```python
conn.execute(
    "UPDATE workflow_runs SET status = 'PATTERN_CATALOG', "
    "eric_approved_at = ? WHERE id = ?",
    (now, run_id),
)
```

### 6. gate_eric_approval.py — placeholder data handling (BLOCK)

**Root cause**: `gate_eric_approval.py` has 6 checks. Checks 3 (briefing
integrity), 4 (goal trace), and 6 (export agreement) require a full Eric
Gate provenance system not yet built. The gate approval endpoint inserts
placeholder data: `briefing_json='{}'`, `goal_reference_id=0`,
`briefing_hash=directive_hash`. These checks FAIL on placeholder data.

**Fix**: Added early-return skips in checks 3 and 4 when placeholder data
detected:
```python
if briefing_json in ("", "{}"):
    print("[3] SKIP: Briefing JSON is placeholder")
    return

if goal_id in (0, None):
    print("[4] SKIP: Goal reference is placeholder")
    return
```

Check 5 (drift state) passes because `'{}'` has `open_count=0`.
Check 6 (export agreement) was also failing because `generate_all.py`
crashed on missing pyyaml — fixed by fix #3 above.

**SUPERSEDED (2026-07-11):** The SKIP logic in fix #6 was replaced by
a full provenance capture system. The approval endpoint now builds real
goal_references, decision_trails, and briefing JSON at approval time.
Checks 3 and 4 now FAIL (not SKIP) if provenance is missing.
See `references/eric_gate_provenance_system.md`.

## Verification

After all fixes, test run `run-269b1220fcaf0135-1783783226` reached
all 7 phases through Menter and Verify. Code Review (Menter) escalated
due to model behavior (Menter didn't emit CHUNK_READY FINAL_JSON) —
this is a model behavior issue, not a pipeline bug. The pipeline
correctly detects and escalates on contract violation.

## Key Pattern

The `workflow_runs.result` / `eric_approved_at` fix follows the same
"set DB state BEFORE gates that check it" pattern as the external gate
timing fix. The general rule: any DB column that a gate checks must be
written BEFORE `run_external_gates()` fires. This applies to:
- `deliberation_rounds` columns (written by `_complete_round()`)
- `workflow_runs.result` (written by the verification phase)
- `workflow_runs.eric_approved_at` (written by the gate approval endpoint)
