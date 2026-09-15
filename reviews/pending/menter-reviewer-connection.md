# Connect Menter to its pipeline reviewers (implementation review stage)

VERSION 5 — 2026-09-13. Folded dual-reviewer findings (both APPROVE/RIGHT_WORK,
2026-09-13). Status: READY_TO_BUILD. Additions since V4:
- **Spine helper replaced, not patched** — `check_eric_gate_approval` (returns
  bool) → `query_eric_gate_approval_for_run` (returns dict with `decision`).
- **Menter completion trigger named** — `menter_closeout.py` is invoked by the
  sandbox run's completion hook, not "someone."
- **`card_scope` migration + AGENTS.md Menter-map update** are explicit build steps.

Eric directive (verbatim, this Telegram session 2026-09-13): "we are not doing the
adrenaline 016 again... do not use adr 016 again just build until a thing works."
The ADR process is retired as enforcement — the dual-reviewer loop is the
enforcement now. No work item waits on ADR-SEED-016 or §14 evidence.

GOAL_ALIGNMENT: seed intent 3 (checks and balances) + seed intent 1 (models
verify each other's work because they have different training data and blind
spots). This card closes the produce→check gap at the IMPLEMENTATION stage, the
mirror of what the advisor loop already does at the CARD stage.

## Problem

The pipeline dead-ends at proposal approval. `reviewer_closeout.py` routes
`CONSENSUS_REACHED → ERIC_APPROVAL_GATE`, and nothing after that gate dispatches
Menter. There is no path from "Menter finished building" → "pipeline reviewers
review the build" → "Eric notified."

Evidence (verified by both reviewers 2026-09-13):
- `dispatch_log` has ever only contained `target_agent` values `hermes-r1`
  (reviewer) and `hermes-v4pro` (drafter). No Menter, no review2. `eric_approved`
  is 0 on every row.
- `reviewer_closeout.py` routes `CONSENSUS_REACHED` and `ESCALATE` to
  `ERIC_APPROVAL_GATE`, then stops. `lifecycle_events` has zero
  `ERIC_APPROVAL_GATE` transitions — the state is a dead end.
- `runtime/mcp_bridge/tools.py:handle_dispatch_implementer` calls
  `bash tools/pipeline/pipeline_dispatch.sh <run_id>` (bare positional), but
  `pipeline_dispatch.sh` only accepts `--proposal <file>` and rejects unknown
  args with "Unknown arg". Plus a second bug: it reads `.get("approved")` while
  the helper returns `decision` (value `APPROVE`) — the check can never pass.
- No `menter_closeout.py` or implementation-review dispatch exists in
  `tools/pipeline/`.
- `reviewer_reconcile.py` REVIEWERS config is stale (qwen→8002 llama-server,
  glm→openrouter.ai; nothing points to the live 8643/8647 gateways).

This was previously claimed complete. It is not.

## Requirement

After Eric approves a proposal (ERIC_APPROVAL_GATE), the approved directive is
dispatched to Menter (sandboxed Claude Code); when Menter finishes, its build
evidence is routed to BOTH pipeline reviewers (review1 8643 + review2 8647) — not
the advisor reviewers (8649/8650) — reconciled, and the verdict is pushed to Eric.
The reviewers are the code check: they assess the build against deterministic
evidence. Each transition is a spine row, not a blocked process (1.21 "row, not a
process").

## Mechanism

R1. Menter dispatch (fix the broken contract + replace the spine helper). After
    an `eric_gate_approvals` row with `decision = 'APPROVE'` exists for a workflow
    run, create a `dispatch_log` row with `target_agent = 'menter'`,
    `eric_approved = 1`, lifecycle `ERIC_APPROVAL_GATE → MENTER_BUILDING`.
    Replace `spine.check_eric_gate_approval(run_id)` (returns a bool, can never
    distinguish APPROVE from absence) with
    `spine.query_eric_gate_approval_for_run(run_id)` returning `dict(row)` with a
    `decision` field — and update the handler to read `decision == 'APPROVE'`,
    NOT `approved`. Also fix the dispatch call so it matches the real script
    contract (no bare positional run_id). Target Menter = sandboxed Claude Code
    (the kernel-sandboxed coder), not the 8646 gateway.

R2. Menter closeout (new `tools/pipeline/menter_closeout.py`). When Menter
    reports completion — triggered by the sandbox run's COMPLETION HOOK (the
    `run_claude_sandbox.sh` process exit, not a manual call or cron) — write
    `MENTER_BUILDING → MENTER_COMPLETE` and store build evidence (git diff,
    test/build output, artifact paths, patch handle) into
    `workflow_run_artifacts`. Menter's self-report is NOT truth; the evidence
    handle is what gets reviewed (ADR-SEED-002).

R3. Implementation review dispatch (new). On MENTER_COMPLETE, create TWO
    dispatches — `target_agent = 'review1'` (8643) and `target_agent = 'review2'`
    (8647) — carrying the card's DONE-WHEN plus the build-evidence handle, NOT the
    proposal text. Reviewers assess the BUILD against deterministic evidence AND
    check the code (this absorbs Verify's former job). Two reviewers of different
    lineage (Qwen + GLM) = the cross-lineage check.

R4. Reconcile + closeout on build evidence. Reuse `reviewer_reconcile.py` /
    `reviewer_closeout.py` semantics, extended to two-reviewer implementation
    review. Route: both `CONSENSUS_REACHED` → APPLY; `OBJECTIONS` → return dispatch
    to Menter (`REVISE_REQUESTED`); `ESCALATE` → Eric. Repoint the stale REVIEWERS
    config to the live 8643/8647 gateways.

R5. Notify Eric. On APPLY-READY (and on ESCALATE / BLOCK), push a phone message
    via the existing container notify path (`reply_consumer.py`, already live in
    the container) with the verdict + evidence handle. No terminal required.

R6. Deterministic apply gate (the sole writer to the repo). Menter's sandbox
    mounts the repo READ-ONLY (kernel wall) and writes its output as a PATCH into
    its single writable folder. Nothing in the pipeline may write the repo except
    a root-owned, deterministic apply gate that runs in the control plane (the
    same trust root as /opt/cis-control). The gate is CODE, not an LLM: it applies
    the patch into the repo only when both conditions are already recorded as
    spine rows —
      (a) CONSENSUS_REACHED from BOTH review1 (8643) and review2 (8647);
      (b) the diff touches ONLY files declared in the card's scope
          (`workflow_runs.card_scope`).
    No spine rows → no write. A model cannot argue with it or persuade it, because
    it is not a model; it is a gate that checks rows and refuses otherwise. This
    removes any human/agent from standing in the middle of the apply step.

    Concretely the gate must: (1) run as root or a privileged non-worker uid;
    (2) be the ONLY process with write access to the repo (all agent gateways run
    as worker with the repo read-only); (3) read the patch from Menter's writable
    folder; (4) validate both conditions before applying; (5) refuse and emit a
    BLOCK event otherwise; (6) leave a spine row recording the apply (applied_at,
    run_id, diff scope, gate hash); (7) enforce condition (b) against the
    `card_scope` field — add `card_scope TEXT` to `workflow_runs` (schema
    migration) and persist the card's declared file scope at dispatch time.
    Without this field, condition (b) is unenforceable.

    NOTE 1 — LIVE HOLE today: the pipeline container mounts the repo read-write
    and the agent gateways run as worker, so as-built an agent COULD write the
    repo. R6 closes that by making the repo read-only to every agent and making
    the apply gate the sole writer. This IS the container-isolation work — no
    separate ADR-gated node; do it here.

    NOTE 2 — this card does NOT wait on ADR-SEED-016 / §14 evidence. The
    dual-reviewer loop is the enforcement. Build the gate until the write-attempt
    test passes; if filesystem isolation is imperfect, fix it — do not defer.

## Decisions

D1. The pipeline reviewers are review1 (8643, Qwen) and review2 (8647, GLM), NOT
    the advisor reviewers (8649/8650). Advisor reviewers review CARDS; pipeline
    reviewers review IMPLEMENTATION and check the code. Two reviewers of different
    lineage = the cross-lineage check.

D2. Menter self-report is not truth (ADR-SEED-002). The review packet carries a
    deterministic-evidence handle, not Menter's prose claim of success.

D3. Every transition is a spine row (lifecycle_events + dispatch_log), never a
    long-running blocked process — matching 1.21.

D4. Menter = sandboxed Claude Code (kernel-sandboxed coder). AGENTS.md's stale
    8646 mapping is corrected in this same build.

D5. Verify (8648) is retired. Code-checking is the reviewers' job. There is no
    third LLM check; the deterministic apply gate is the final enforcement, and
    it is code, not a model.

D6. The apply gate is deterministic code, not an LLM, and it is the SOLE writer
    to the repo. Repo is read-only to every agent; only the root-owned apply gate
    writes, and only after (a) dual-review CONSENSUS_REACHED and (b)
    diff-within-card-scope are both recorded as spine rows. Trust is enforced by
    filesystem ownership + row checks, never by an agent's self-report.

D7. Enforcement is the dual-reviewer loop, not the ADR process. ADRs were put in
    place before reviewers existed; the reviewers are the check-and-balance now.
    No work item is gated on ADR-SEED-016 or §14 evidence. Build until it works;
    if it does not, fix it — do not defer.

## Open questions (resolve at implement time, files win)

O1. `reviewer_reconcile.py` REVIEWERS config is stale (glm→openrouter,
    qwen→8002). Implementer must repoint to the live 8643/8647 gateways or
    reconciliation hits the wrong models. (R4 covers this.)

## DONE-WHEN

- After an Eric Gate APPROVE (decision = 'APPROVE'), a `dispatch_log` row to
  `target_agent='menter'` is created with `eric_approved=1` and the dispatch path
  fires without the argument-contract error or the `approved` vs `decision` bug.
- The spine helper is `query_eric_gate_approval_for_run` (returns dict with
  `decision`), NOT `check_eric_gate_approval` (bool).
- `menter_closeout.py` is triggered by the sandbox run's completion hook.
- `workflow_runs.card_scope` exists (migration applied to the existing 17+ rows)
  and AGENTS.md maps Menter → sandboxed Claude Code (not 8646).
- Menter completion writes a `MENTER_COMPLETE` lifecycle event and stores build
  evidence in `workflow_run_artifacts`.
- MENTER_COMPLETE creates dispatches to BOTH review1 (8643) and review2 (8647).
- The two reviewers return FINAL_JSON; reconcile routes CONSENSUS/OBJECTIONS/
  ESCALATE correctly; OBJECTIONS returns a revise dispatch to Menter.
- The reviewers' review includes code-checking (the former Verify job).
- Eric receives a phone notification with the verdict + evidence handle.
- The full chain (approve → build → review → apply → notify) is exercised once
  end-to-end on a real card, with raw spine/DB output as evidence.

## R6 ACCEPTANCE (deterministic apply gate)

- The repo is read-only to every agent process (worker uid) — verified by a
  write attempt from a gateway that is rejected with "Read-only file system."
- The apply gate is the only writer: root-owned, not editable by worker, and a
  patch is NOT applied when either (a) dual-review CONSENSUS or (b) scope check
  is missing — verified by feeding it an unverified patch and confirming it BLOCKs
  without writing.
- A verified patch IS applied, and the repo gains the declared files with a
  spine row recording applied_at + run_id + diff scope + gate hash.
- `workflow_runs.card_scope` exists and is populated at dispatch time.
