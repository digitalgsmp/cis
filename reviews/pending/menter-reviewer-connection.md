# Connect Menter to its pipeline reviewers (implementation review stage)

VERSION 1 — queue item to be assigned (follows 3.31).

GOAL_ALIGNMENT: seed intent 3 (checks and balances) + seed intent 1 (models
verify each other's work because they have different training data and blind
spots). This card closes the produce→check gap at the IMPLEMENTATION stage, the
mirror of what the advisor loop already does at the CARD stage.

## Problem

The pipeline dead-ends at proposal approval. `reviewer_closeout.py` routes
`CONSENSUS_REACHED → ERIC_APPROVAL_GATE`, and nothing after that gate dispatches
Menter. There is no path from "Menter finished building" → "pipeline reviewers
review the build" → "Eric notified."

Evidence (verified 2026-09-12):
- `dispatch_log` has ever only contained `target_agent` values `hermes-r1`
  (reviewer) and `hermes-v4pro` (drafter). No Menter (8646), no review2 (8647),
  no Verify (8648).
- `reviewer_pickup.py` claims dispatches for `hermes-r1` (8643) only — a single
  reviewer, for PROPOSAL review.
- `reviewer_closeout.py` routes `CONSENSUS_REACHED` and `ESCALATE` to
  `ERIC_APPROVAL_GATE`, then stops. No successor state.
- `runtime/mcp_bridge/tools.py:handle_dispatch_implementer` calls
  `bash tools/pipeline/pipeline_dispatch.sh <run_id>`, but
  `pipeline_dispatch.sh` parses `--proposal <file>` and rejects a bare positional
  arg ("Unknown arg"). The dispatch-to-Menter path is broken at the call contract.
- No `menter_closeout.py`, no verify-stage script, no implementation-review
  dispatch exists in `tools/pipeline/`.

This was previously claimed complete. It is not.

## Requirement

After Eric approves a proposal (ERIC_APPROVAL_GATE), the approved directive is
dispatched to Menter; when Menter finishes, its build evidence is routed to BOTH
pipeline reviewers (review1 8643 + review2 8647) — not the advisor reviewers
(8649/8650) — reconciled, verified against deterministic evidence (ADR-SEED-002),
and the verdict is pushed to Eric. Each transition is a spine row, not a blocked
process, matching the 1.21 "row, not a process" principle.

## Mechanism

R1. Menter dispatch (fix the broken contract). After an `eric_gate_approvals`
    APPROVE row exists for a workflow run, create a `dispatch_log` row with
    `target_agent = 'menter'`, `target_endpoint = 'http://127.0.0.1:8646'`,
    `eric_approved = 1`, lifecycle state `ERIC_APPROVAL_GATE → MENTER_BUILDING`.
    Fix `handle_dispatch_implementer` so its call into the dispatch path matches
    the actual script argument contract (or route through a real `menter_start.py`
    instead of the pre-execution-oversight script, which is for a different job).

R2. Menter closeout (new `tools/pipeline/menter_closeout.py`). When Menter
    reports completion, write `MENTER_BUILDING → MENTER_COMPLETE` lifecycle event
    and store the build evidence (git diff, test/build output, artifact paths)
    into `workflow_run_artifacts`. Menter's self-report is NOT accepted as truth;
    the evidence handle is what gets reviewed (ADR-SEED-002).

R3. Implementation review dispatch (new). On MENTER_COMPLETE, create TWO
    dispatches — `target_agent = 'review1'` (8643) and `target_agent = 'review2'`
    (8647) — carrying the card's DONE-WHEN plus the build-evidence handle, NOT the
    proposal text. This is a distinct packet from the advisor card-review packet:
    reviewers assess the BUILD against deterministic evidence, not the design.

R4. Reconcile + closeout on build evidence. Reuse `reviewer_reconcile.py` /
    `reviewer_closeout.py` semantics, extended to a two-reviewer
    (review1 + review2) implementation review. Route: both `CONSENSUS_REACHED` →
    VERIFY; `OBJECTIONS` → return dispatch to Menter (`REVISE_REQUESTED`);
    `ESCALATE` → Eric.

R5. Verify (new `tools/pipeline/verify_closeout.py`). The Verify agent (8648)
    independently checks the deterministic evidence (git diff, test output, DB
    query, endpoint response, service health — ADR-SEED-002 accepted evidence)
    and emits PASS/FAIL. PASS → ERIC_NOTIFY; FAIL → return dispatch to Menter.

R6. Notify Eric. On ERIC_NOTIFY (and on ESCALATE / BLOCK), push a phone message
    via the container notify path (the TG2 mechanism) with the verdict + evidence
    handle. No terminal required to see the result.

## Decisions

D1. The pipeline reviewers are review1 (8643) and review2 (8647), NOT the advisor
    reviewers (8649/8650). Advisor reviewers review CARDS; pipeline reviewers
    review IMPLEMENTATION. Two reviewers of different lineage, per the
    dual-reviewer rule.

D2. Menter self-report is not truth (ADR-SEED-002). The review packet carries a
    deterministic-evidence handle, not Menter's prose claim of success.

D3. Every transition is a spine row (lifecycle_events + dispatch_log), never a
    long-running blocked process — matching 1.21.

## Open questions (resolve at implement time, files win)

O1. Menter identity: AGENTS.md maps Menter → `hermes-v4impl` (8646,
    deepseek-v4-pro); the newer lineage map says Menter = Claude (sandboxed coder).
    The card is identity-agnostic; the implementer must verify which is live in
    the container and target it.
O2. Lineage: review2 (8647) and Verify (8648) are both GLM 5.2 per AGENTS.md —
    a same-lineage review→verify boundary. Confirm whether this violates the
    cross-lineage rule and, if so, which model Verify should be.
O3. `reviewer_reconcile.py` REVIEWERS config is stale (glm→openrouter, not the
    local 8647 gateway; qwen→8002 llama-server, not 8643). Implementer must
    repoint it to the live gateways or the reconciliation will hit the wrong
    models.

## DONE-WHEN

- After an Eric Gate APPROVE, a `dispatch_log` row to `target_agent='menter'`
  is created with `eric_approved=1` and the dispatch path fires without the
  argument-contract error.
- Menter completion writes a `MENTER_COMPLETE` lifecycle event and stores build
  evidence in `workflow_run_artifacts`.
- MENTER_COMPLETE creates dispatches to BOTH review1 (8643) and review2 (8647).
- The two reviewers return FINAL_JSON; reconcile routes CONSENSUS/OBJECTIONS/
  ESCALATE correctly; OBJECTIONS returns a revise dispatch to Menter.
- Verify (8648) independently checks the evidence and emits PASS/FAIL.
- Eric receives a phone notification with the verdict + evidence handle.
- The full chain (approve → build → review → verify → notify) is exercised once
  end-to-end on a real card, with raw spine/DB output as evidence.
