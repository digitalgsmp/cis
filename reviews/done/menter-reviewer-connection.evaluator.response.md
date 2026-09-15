# Advisor review — menter-reviewer-connection

- packet: `reviews/pending/menter-reviewer-connection.md`
- advisor: evaluator on port 8650
- run tag: menter-reviewer-connection @ 2026-09-13T12:27:59-05:00
- at: 2026-09-13T12:34:35
- prompt_tokens: 774563
- completion_tokens: 7570
- total_tokens: 782133
- token source: gateway response usage
- model turns: (see gateway agent.log for the per-turn tool-use breakdown)
- finish_reason: stop

---

FRAME: RIGHT_WORK

The pipeline genuinely dead-endsafter Eric gate approval. Here is the evidence, claim by claim:

DEAD-END CONFIRMED

dispatch_log has 3 rows total: hermes-r1 (eric_approved=0, 2 rows) and hermes-v4pro (eric_approved=0, 1 row). Zero rows with eric_approved=1. Zero rows targeting "menter". The pipeline has never dispatched an implementer after approval.

lifecycle_events has zero ERIC_APPROVAL_GATE transitions. States seen: ROUTING(9), DRAFTING(9), REVIEW_PENDING(2), DRAFT_READY(2), REVISE_REQUESTED(1), REVIEW_COMPLETE(1), REVIEWING(1). Nothing ever reaches the gate.

Meanwhile eric_gate_approvals has 27 APPROVE + 2 VETO decisions, and 17 workflow_runs have eric_approved_at populated. Eric IS approving work, but nothing fires afterward. The approval is recorded but orphaned.

reviewer_closeout.py routes CONSENSUS_REACHED and ESCALATE to ERIC_APPROVAL_GATE and stops. There is no code path from "Eric approved" to "Menter builds" to "reviewers review the build" to "Eric notified of verdict."

LATENT BUGS CONFIRMED

handle_dispatch_implementer at tools.py:834 calls:
  ["bash", "tools/pipeline/pipeline_dispatch.sh", run_id]

pipeline_dispatch.sh only accepts --proposal <file>. Any other positional arg hits the catch-all case and exits with code 2 ("Unknown arg"). So even if the eric-gate check passed, the subprocess would fail immediately.

Additionally, handle_dispatch_implementer reads spine.check_eric_gate_approval(run_id) which returns the decision value (the string "APPROVE"), and the handler tests if not approved. The string "APPROVE" is truthy so this particular check works by accident, but the naming is misleading and fragile.

MISSING FILES CONFIRMED

menter_closeout.py does not exist in tools/pipeline/. The directory contains: drafter_closeout.py, drafter_session_init.py, drafter_start.py, measure_intent.py, pipeline_dispatch.sh, reviewer_closeout.py, reviewer_pickup.py, reviewer_reconcile.py, reviewer_session_init.py, staleness_check.py. No menter anything.

workflow_runs has no card_scope column. 18 columns: id, topic, result, requires_eric_review, max_rounds, max_consecutive_revisions, rounds_completed, final_objections_json, created_at, completed_at, status, route, updated_at, eric_approved_at, intent, directive_hash, project_id, parent_run_id.

STALE CONFIG CONFIRMED

reviewer_reconcile.py REVIEWERS dict points to:
- r1: http://127.0.0.1:8643 (correct gateway)
- qwen: http://127.0.0.1:8002 (local llama-server, not the 8647 gateway)
- glm: https://openrouter.ai (cloud API)
- deepseek-r1: https://api.deepseek.com (cloud API)

Nothing references the 8647 implementation-review gateway. The reconciler was built for the CARD-stage proposal review, not implementation review.

AGENTS.md maps "Implementer" to port 8646 but the proposal says Menter is sandboxed Claude Code, not an 8646 process. This mapping is stale.

WHAT THE PROPOSAL GETS RIGHT

The proposal correctly identifies:
1. The pipeline dead-end is real and empirically measurable.
2. The missing menter_closeout.py is the gap — no script exists to capture Menter's build output and route it to reviewers.
3. The card_scope column is needed on workflow_runs to bound what reviewers check.
4. The dispatch_log argument contract is broken (bare positional vs --proposal).
5. The REVIEWERS config in reviewer_reconcile.py doesn't serve implementation review (wrong gateways).
6. The R6 acceptance criteria (repo read-only to workers, apply gate root-owned, dual-review CONSENSUS required before patch) are sound security constraints.

WHAT I COULD NOT VERIFY

reply_consumer.py: I searched runtime/mcp_bridge for it and got no results. If it exists, it's not in that directory. The proposal says it's "live in the container" — I could not confirm this from the repo tree.

The exact contents of spine.check_eric_gate_approval: the function is at spine.py:278 but I could not read past the file header due to truncation. I can confirm the function exists and is called, but cannot verify its exact return type without reading that section.

WHAT IS MISSING FROM THE PROPOSAL

No mention of how Menter's sandbox actually communicates completion. The proposal assumes a menter_closeout.py will be called, but doesn't specify who calls it (cron? process exit hook? Eric manually?). The drafter pipeline has drafter_closeout.py called by the Hermes agent loop; Menter needs an equivalent trigger.

No migration script for adding card_scope to workflow_runs. The column doesn't exist yet and 17+ runs are already in the table.

No plan for updating AGENTS.md to reflect Menter = sandboxed Claude Code instead of port 8646.

BOTTOM LINE

This is the right work at the right time. The dead-end is real, measurable, and blocks every approved proposal from ever being built. The infrastructure (reviewer gateways, eric_gate_approvals, dispatch_log) exists but isn't wired together past the approval point. The proposal correctly identifies all the gaps and latent bugs. The missing pieces (Menter completion trigger, migration, AGENTS.md update) are small additions to the build scope.
