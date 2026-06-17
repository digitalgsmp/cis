# Tier 11D — Reviewer #1 (r1:8643) Feedback
Date: 2026-06-16 | Reviewer: hermes-r1 (port 8643)

## Verdict: BLOCKED — REVISE_SPEC (2 critical, 5 moderate, 3 minor)

### Critical Objections

**O1 — deliberation_rounds column names are fictional (CRITICAL)**
Spec §6.2 step 14 references columns that don't exist:
- `workflow_run_id` → actual: `run_id`
- `reviewer_status` → actual: `reviewer_signal`
- `reviewer_feedback_hash` → DOES NOT EXIST
- `drafter_proposal_hash` → DOES NOT EXIST  
- `completed_at` → DOES NOT EXIST
All 5 INSERT/UPDATE statements in step 14 will fail. Also: `reviewer_signal` is NOT NULL with no default, so "open round" detection via IS NULL won't work.

**O2 — Max-rounds override is dead code (CRITICAL)**
Step 12 sets override flag + prints warning, but step 15 recomputes verdict from original `status`:
```python
verdict = 'ERIC_APPROVAL_GATE' if status in ('CONSENSUS_REACHED', 'ESCALATE') else 'REVISE_REQUESTED'
```
When `status == 'OBJECTIONS'` and max rounds exceeded, step 12 says "route to ERIC_APPROVAL_GATE" but step 15 routes to `REVISE_REQUESTED` and creates return dispatch anyway.

### Moderate Objections

**O3** — Eric Gate endpoint path wrong: `/api/eric-gate/approve` → actual: `/api/pipeline/eric-gate`
**O4** — §2 verification queries non-existent `ALLOWED_TRANSITIONS_LOOKUP` table
**O5** — Step 17 raw SQL UPDATE skips `complete_dispatch()`, missing `dispatch_events` row
**O6** — §7 gate narrative says "≥6 events" but there are 7 events (should be ≥7)
**O7** — Full proposal text unavailable to Reviewer from spine (500-char summary only)

### Minor Objections

**O8** — session_id resolution simplified vs 11C's three-tier pattern
**O10** — Scope-creep grep missing "classifier" keyword parity with 11C gate

### Required Revisions (R1-R8)
R1: Rewrite all deliberation_rounds SQL against actual schema
R2: Fix max-rounds override → actually force escalation
R3: Correct Eric Gate path
R4: Replace ALLOWED_TRANSITIONS_LOOKUP with real check
R5: Use complete_dispatch() or add dispatch_events INSERT
R6: "≥6" → "≥7" in gate narrative
R7: Three-tier session_id in reviewer_pickup.py
R8: Add "classifier" to scope-creep grep
